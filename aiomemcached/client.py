import re
import functools
import asyncio
import warnings
from io import BytesIO
from typing import List, Dict, Optional

from .constants import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DEFAULT_POOL_MINSIZE,
    DEFAULT_POOL_MAXSIZE,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_KEY_LENGTH,
    DEFAULT_MAX_VALUE_LENGTH,
    STORED,
    NOT_STORED,
    EXISTS,
    NOT_FOUND,
    DELETED,
    TOUCHED,
    END,
    VERSION,
    OK,
)
from .pool import MemcachedPool, MemcachedConnection
from .exceptions import (
    ValidationException,
    ResponseException,
    ConnectException,
    TimeoutException,
)

"""
Ref:
- https://github.com/memcached/memcached/blob/master/doc/protocol.txt
- https://dzone.com/refcardz/getting-started-with-memcached
"""

__all__ = ["Client"]

# key supports ascii sans space and control chars
# \x21 is !, right after space, and \x7e is -, right before DEL
# also 1 <= len <= 250 as per the spec
_VALIDATE_KEY_RE = re.compile(b"^[^\x00-\x20\x7f]{1,%d}$" % DEFAULT_MAX_KEY_LENGTH)

# URI: memcached://localhost:11211
_URI_RE = re.compile(
    r"^memcached://(?P<host>[.a-z0-9_-]+|[0-9]+.[0-9]+.[0-9]+.[0-9]+)"
    r"(:(?P<port>[0-9]+))?"
)


def acquire(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        conn = await self._pool.acquire()
        try:
            return await func(self, conn, *args, **kwargs)

        finally:
            await self._pool.release(conn)

    return wrapper


class Client(object):
    def __init__(
        self,
        uri: str = None,
        host: str = DEFAULT_SERVER_HOST,
        port: int = DEFAULT_SERVER_PORT,
        pool_minsize: int = DEFAULT_POOL_MINSIZE,
        pool_maxsize: int = DEFAULT_POOL_MAXSIZE,
        timeout: int = DEFAULT_TIMEOUT,
        value_length: int = DEFAULT_MAX_VALUE_LENGTH,
    ):
        if uri is None:
            self._host = host
            self._port = port

        else:
            self._host, self._port = self.uri_parser(uri)

        self._timeout = timeout
        self._value_length = value_length
        self._pool = MemcachedPool(
            host=self._host, port=self._port, minsize=pool_minsize, maxsize=pool_maxsize
        )

    @staticmethod
    def uri_parser(uri: str) -> (str, int):
        m = re.match(_URI_RE, uri.lower())

        try:
            host = m.group("host")

            port = m.group("port")
            if port is None:
                port = DEFAULT_SERVER_PORT

            else:
                port = int(port)

        except AttributeError:
            raise ValidationException("URI:{} parser failed!".format(uri))

        return host, port

    @staticmethod
    def validate_key(key: bytes) -> None:
        """A key (arbitrary string up to 250 bytes in length.
        No space or newlines for ASCII mode)
        """
        if not isinstance(key, bytes):  # TODO maybe remove in next version?
            raise ValidationException("key must be bytes:{}".format(key))

        m = _VALIDATE_KEY_RE.match(key)
        if not m or len(m.group(0)) != len(key):
            raise ValidationException(
                "A key (arbitrary string up to 250 bytes in length. "
                "No space or newlines for ASCII mode):{}".format(key)
            )

        return

    def validate_value(self, value: bytes):
        if len(value) > self._value_length:
            raise ValidationException(
                "A value up to {} bytes in length.".format(len(value))
            )

    async def close(self):
        """Closes the sockets if its open."""
        await self._pool.clear()

    @acquire
    async def _execute_raw_cmd(
        self,
        conn: MemcachedConnection,
        cmd: bytes,
        one_line_response: bool = False,
        end_symbols: List[bytes] = None,
    ) -> BytesIO:
        """
        skip end_symbols if one_line_response is True
        """
        if end_symbols is None:
            end_symbols = list()

        conn.writer.write(cmd)

        response_stream = BytesIO()
        while True:
            try:
                line = await asyncio.wait_for(
                    conn.reader.readline(), timeout=self._timeout
                )
            except ConnectionError as e:
                raise ConnectException(e)
            except asyncio.TimeoutError as e:
                raise TimeoutException(e)  # TODO test

            response_stream.write(line)

            if one_line_response:
                break
            if line in end_symbols:
                break

        response_stream.seek(0)
        return response_stream

    async def _storage_command(
        self,
        cmd: bytes,
        key: bytes,
        value: bytes,
        flags: int = 0,
        exptime: int = 0,
        cas: int = None,
    ) -> bool:
        """
        Storage commands
        ----------------

        First, the client sends a command line which looks like this:

        <command name> <key> <flags> <exptime> <bytes> [noreply]\r\n
        cas <key> <flags> <exptime> <bytes> <cas unique> [noreply]\r\n

        - <command name> is "set", "add", "replace", "append" or "prepend"

          "set" means "store this data".

          "add" means "store this data, but only if the server *doesn't* already
          hold data for this key".

          "replace" means "store this data, but only if the server *does*
          already hold data for this key".

          "append" means "add this data to an existing key after existing data".

          "prepend" means "add this data to an existing key before existing data".

          The append and prepend commands do not accept flags or exptime.
          They update existing data portions, and ignore new flag and exptime
          settings.

          "cas" is a check and set operation which means "store this data but
          only if no one else has updated since I last fetched it."

        - <key> is the key under which the client asks to store the data

        - <flags> is an arbitrary 16-bit unsigned integer (written out in
          decimal) that the server stores along with the data and sends back
          when the item is retrieved. Clients may use this as a bit field to
          store data-specific information; this field is opaque to the server.
          Note that in memcached 1.2.1 and higher, flags may be 32-bits, instead
          of 16, but you might want to restrict yourself to 16 bits for
          compatibility with older versions.

        - <exptime> is expiration time. If it's 0, the item never expires
          (although it may be deleted from the cache to make place for other
          items). If it's non-zero (either Unix time or offset in seconds from
          current time), it is guaranteed that clients will not be able to
          retrieve this item after the expiration time arrives (measured by
          server time). If a negative value is given the item is immediately
          expired.

        - <bytes> is the number of bytes in the data block to follow, *not*
          including the delimiting \r\n. <bytes> may be zero (in which case
          it's followed by an empty data block).

        - <cas unique> is a unique 64-bit value of an existing entry.
          Clients should use the value returned from the "gets" command
          when issuing "cas" updates.

        - "noreply" optional parameter instructs the server to not send the
          reply.  NOTE: if the request line is malformed, the server can't
          parse "noreply" option reliably.  In this case it may send the error
          to the client, and not reading it on the client side will break
          things.  Client should construct only valid requests.

        After this line, the client sends the data block:

        <data block>\r\n

        - <data block> is a chunk of arbitrary 8-bit data of length <bytes>
          from the previous line.

        After sending the command line and the data block the client awaits
        the reply, which may be:

        - "STORED\r\n", to indicate success.

        - "NOT_STORED\r\n" to indicate the data was not stored, but not
        because of an error. This normally means that the
        condition for an "add" or a "replace" command wasn't met.

        - "EXISTS\r\n" to indicate that the item you are trying to store with
        a "cas" command has been modified since you last fetched it.

        - "NOT_FOUND\r\n" to indicate that the item you are trying to store
        with a "cas" command did not exist.
        """
        # validate key, value
        self.validate_key(key)
        self.validate_value(value)

        if flags < 0 or exptime < 0:
            raise ValidationException(
                "flags:[{}] and exptime:[{}] must be unsigned integer"
                "".format(flags, exptime)
            )

        if cas:
            raw_cmd = b"cas %b %d %d %d %d\r\n%b\r\n" % (
                key,
                flags,
                exptime,
                len(value),
                cas,
                value,
            )
        else:
            raw_cmd = b"%b %b %d %d %d\r\n%b\r\n" % (
                cmd,
                key,
                flags,
                exptime,
                len(value),
                value,
            )

        response_stream = await self._execute_raw_cmd(
            cmd=raw_cmd, one_line_response=True
        )
        response = response_stream.readline()
        if response == STORED:
            return True

        elif response in (NOT_STORED, EXISTS, NOT_FOUND):
            # TODO raise with status , depend option raise_exp?
            return False

        raise ResponseException(raw_cmd, response_stream.getvalue())

    async def set(
        self, key: bytes, value: bytes, flags: int = 0, exptime: int = 0
    ) -> bool:
        """ "set" means "store this data"."""
        return await self._storage_command(
            cmd=b"set", key=key, value=value, flags=flags, exptime=exptime
        )

    async def add(
        self, key: bytes, value: bytes, flags: int = 0, exptime: int = 0
    ) -> bool:
        """
        "add" means "store this data, but only if the server *doesn't* already
        hold data for this key".
        """
        return await self._storage_command(
            cmd=b"add", key=key, value=value, flags=flags, exptime=exptime
        )

    async def replace(
        self, key: bytes, value: bytes, flags: int = 0, exptime: int = 0
    ) -> bool:
        """
        "replace" means "store this data, but only if the server *does*
        already hold data for this key".
        """
        return await self._storage_command(
            cmd=b"replace", key=key, value=value, flags=flags, exptime=exptime
        )

    async def append(
        self, key: bytes, value: bytes, flags: int = 0, exptime: int = 0
    ) -> bool:
        """
        "append" means "add this data to an existing key after existing data".
        """
        return await self._storage_command(
            cmd=b"append", key=key, value=value, flags=flags, exptime=exptime
        )

    async def prepend(
        self, key: bytes, value: bytes, flags: int = 0, exptime: int = 0
    ) -> bool:
        """ "prepend" means
        "add this data to an existing key before existing data".
        """
        return await self._storage_command(
            cmd=b"prepend", key=key, value=value, flags=flags, exptime=exptime
        )

    async def cas(
        self, key: bytes, value: bytes, cas: int, flags: int = 0, exptime: int = 0
    ) -> bool:
        """
        "cas" is a check and set operation which means "store this data but
        only if no one else has updated since I last fetched it."
        """
        return await self._storage_command(
            cmd=b"cas", key=key, value=value, flags=flags, exptime=exptime, cas=cas
        )

    async def _retrieval_command(
        self, keys: List[bytes], with_cas: bool = False
    ) -> (Dict[bytes, bytes], Dict[bytes, Dict[bytes, Optional[int]]]):
        """
        Retrieval command:
        ------------------

        The retrieval commands "get" and "gets" operate like this:

        get <key>*\r\n
        gets <key>*\r\n

        - <key>* means one or more key strings separated by whitespace.

        After this command, the client expects zero or more items, each of
        which is received as a text line followed by a data block. After all
        the items have been transmitted, the server sends the string

        "END\r\n"

        to indicate the end of response.

        Each item sent by the server looks like this:

        VALUE <key> <flags> <bytes> [<cas unique>]\r\n
        <data block>\r\n

        - <key> is the key for the item being sent

        - <flags> is the flags value set by the storage command

        - <bytes> is the length of the data block to follow, *not* including
          its delimiting \r\n

        - <cas unique> is a unique 64-bit integer that uniquely identifies
          this specific item.

        - <data block> is the data for this item.

        If some of the keys appearing in a retrieval request are not sent back
        by the server in the item list this means that the server does not
        hold items with such keys (because they were never stored, or stored
        but deleted to make space for more items, or expired, or explicitly
        deleted by a client).
        """
        # validate keys
        [self.validate_key(key) for key in keys]

        cmd_format = b"gets %b\r\n" if with_cas else b"get %b\r\n"
        raw_cmd = cmd_format % b" ".join(keys)

        response_stream = await self._execute_raw_cmd(
            cmd=raw_cmd,
            end_symbols=[
                END,
            ],
        )

        values = {}
        info = {}
        # values = {
        #     key: data,
        #     ...
        # }
        # info = {
        #     key: {
        #         'flags': flags,
        #         'cas': cas,
        #     },
        #     ...
        # }

        line = response_stream.readline()
        while line != b"" and line != END:
            terms = line.split()

            try:
                if terms[0] != b"VALUE":
                    raise ResponseException(raw_cmd, response_stream.getvalue())

                key = terms[1]
                if key in values:
                    raise ResponseException(
                        raw_cmd,
                        response_stream.getvalue(),
                        ext_message="Duplicate results from server",
                    )

                flags = int(terms[2])
                cas = int(terms[4]) if with_cas else None
                data_len = int(terms[3])

                data = response_stream.read(data_len + 2).rstrip(b"\r\n")
                if len(data) != data_len:
                    raise ValueError

            except ValueError:
                raise ResponseException(raw_cmd, response_stream.getvalue())

            values[key] = data
            info[key] = {
                "flags": flags,
                "cas": cas,
            }

            line = response_stream.readline()

        if len(values) > len(keys):
            raise ResponseException(
                raw_cmd,
                response_stream.readline(),
                ext_message="received too many responses",
            )
        return values, info

    async def get(
        self, key: bytes, default: bytes = None
    ) -> (bytes, Dict[bytes, Optional[int]]):
        """Gets a single value from the server."""
        keys = [
            key,
        ]
        values, info = await self._retrieval_command(keys)

        return values.get(key, default), info.get(key, dict())

    async def gets(
        self, key: bytes, default: bytes = None
    ) -> (bytes, Dict[bytes, Optional[int]]):
        """Gets a single value from the server together with the cas token."""
        keys = [
            key,
        ]
        values, info = await self._retrieval_command(keys, with_cas=True)
        return values.get(key, default), info.get(key, dict())

    async def get_many(
        self, keys: List[bytes]
    ) -> (  # TODO default?!
        Dict[bytes, bytes],
        Dict[bytes, Dict[bytes, Optional[int]]],
    ):
        """Takes a list of keys and returns a list of values."""
        # check keys
        if len(keys) == 0:
            return dict(), dict()

        keys = list(set(keys))  # ignore duplicate keys error

        values, info = await self._retrieval_command(keys)
        return values, info

    async def gets_many(
        self, keys: List[bytes]
    ) -> (Dict[bytes, bytes], Dict[bytes, Dict[bytes, Optional[int]]]):
        """Takes a list of keys and returns a list of values
        together with the cas token.
        """
        # check keys
        if len(keys) == 0:
            return dict(), dict()

        keys = list(set(keys))  # ignore duplicate keys error

        values, info = await self._retrieval_command(keys, with_cas=True)
        return values, info

    async def multi_get(self, *args):
        """shadow for get_multi, DeprecationWarning"""
        warnings.warn(
            "multi_get is deprecated since AioMemcached 0.8, "
            "and scheduled for removal in AioMemcached 0.9 .)",
            DeprecationWarning,
        )
        keys = [arg for arg in args]
        values, _ = await self.get_many(keys)
        return tuple(values.get(key) for key in keys)

    async def delete(self, key: bytes) -> bool:
        """
        Deletion
        --------

        The command "delete" allows for explicit deletion of items:

        delete <key> [noreply]\r\n

        - <key> is the key of the item the client wishes the server to delete

        - "noreply" optional parameter instructs the server to not send the
          reply.  See the note in Storage commands regarding malformed
          requests.

        The response line to this command can be one of:

        - "DELETED\r\n" to indicate success

        - "NOT_FOUND\r\n" to indicate that the item with this key was not
          found.

        See the "flush_all" command below for immediate invalidation
        of all existing items.
        """
        # validate key
        self.validate_key(key)

        raw_cmd = b"delete %b\r\n" % key
        response_stream = await self._execute_raw_cmd(
            cmd=raw_cmd, one_line_response=True
        )
        response = response_stream.readline()
        if response == DELETED:
            return True

        elif response == NOT_FOUND:
            # TODO raise with status , depend option raise_exp?
            return False

        raise ResponseException(raw_cmd, response_stream.getvalue())

    async def _incr_decr(self, cmd: bytes, key: bytes, value: int) -> Optional[int]:
        """
        Increment/Decrement
        -------------------

        Commands "incr" and "decr" are used to change data for some item
        in-place, incrementing or decrementing it. The data for the item is
        treated as decimal representation of a 64-bit unsigned integer.  If
        the current data value does not conform to such a representation, the
        incr/decr commands return an error (memcached <= 1.2.6 treated the
        bogus value as if it were 0, leading to confusion). Also, the item
        must already exist for incr/decr to work; these commands won't pretend
        that a non-existent key exists with value 0; instead, they will fail.

        The client sends the command line:

        incr <key> <value> [noreply]\r\n

        or

        decr <key> <value> [noreply]\r\n

        - <key> is the key of the item the client wishes to change

        - <value> is the amount by which the client wants to increase/decrease
        the item. It is a decimal representation of a 64-bit unsigned integer.

        - "noreply" optional parameter instructs the server to not send the
          reply.  See the note in Storage commands regarding malformed
          requests.

        The response will be one of:

        - "NOT_FOUND\r\n" to indicate the item with this value was not found

        - <value>\r\n , where <value> is the new value of the item's data,
          after the increment/decrement operation was carried out.

        Note that underflow in the "decr" command is caught: if a client tries
        to decrease the value below 0, the new value will be 0.  Overflow in
        the "incr" command will wrap around the 64 bit mark.

        Note also that decrementing a number such that it loses length isn't
        guaranteed to decrement its returned length.  The number MAY be
        space-padded at the end, but this is purely an implementation
        optimization, so you also shouldn't rely on that.
        """
        # validate key
        self.validate_key(key)

        if value < 0 or not isinstance(value, int):
            raise ValidationException(
                "value:[{}]  must be unsigned integer".format(value)
            )

        raw_cmd = b"%b %b %d\r\n" % (cmd, key, value)
        response_stream = await self._execute_raw_cmd(
            cmd=raw_cmd, one_line_response=True
        )
        response = response_stream.readline()

        try:
            if response == NOT_FOUND:
                # TODO raise with status , depend option raise_exp?
                return None

            new_value = int(response)

        except ValueError:
            raise ResponseException(raw_cmd, response_stream.getvalue())

        return new_value

    async def incr(
        self, key: bytes, value: int = 1, increment: int = None
    ) -> Optional[int]:
        if increment:
            warnings.warn(
                "incr() param increment is deprecated since AioMemcached 0.8, "
                "and scheduled for removal in AioMemcached 0.9 .)",
                DeprecationWarning,
            )
            value = increment
        return await self._incr_decr(cmd=b"incr", key=key, value=value)

    async def decr(
        self, key: bytes, value: int = 1, decrement: int = None
    ) -> Optional[int]:
        if decrement:
            warnings.warn(
                "incr() param increment is deprecated since AioMemcached 0.8, "
                "and scheduled for removal in AioMemcached 0.9 .)",
                DeprecationWarning,
            )
            value = decrement
        return await self._incr_decr(cmd=b"decr", key=key, value=value)

    async def touch(self, key: bytes, exptime: int) -> bool:
        """
        Touch
        -----

        The "touch" command is used to update the expiration time of an existing item
        without fetching it.

        touch <key> <exptime> [noreply]\r\n

        - <key> is the key of the item the client wishes the server to touch

        - <exptime> is expiration time. Works the same as with the update commands
          (set/add/etc). This replaces the existing expiration time. If an existing
          item were to expire in 10 seconds, but then was touched with an
          expiration time of "20", the item would then expire in 20 seconds.

        - "noreply" optional parameter instructs the server to not send the
          reply.  See the note in Storage commands regarding malformed
          requests.

        The response line to this command can be one of:

        - "TOUCHED\r\n" to indicate success

        - "NOT_FOUND\r\n" to indicate that the item with this key was not
          found.
        """
        # validate key
        self.validate_key(key)

        raw_cmd = b"touch %b %d\r\n" % (key, exptime)
        response_stream = await self._execute_raw_cmd(
            cmd=raw_cmd, one_line_response=True
        )
        response = response_stream.readline()

        if response == TOUCHED:
            return True

        elif response == NOT_FOUND:
            # TODO raise with status , depend option raise_exp?
            return False

        raise ResponseException(raw_cmd, response_stream.getvalue())

    async def stats(self, args: bytes = None) -> dict:
        """
        Statistics
        ----------

        The command "stats" is used to query the server about statistics it
        maintains and other internal data. It has two forms. Without
        arguments:

        stats\r\n

        it causes the server to output general-purpose statistics and
        settings, documented below.  In the other form it has some arguments:

        stats <args>\r\n

        Depending on <args>, various internal data is sent by the server. The
        kinds of arguments and the data sent are not documented in this version
        of the protocol, and are subject to change for the convenience of
        memcache developers.
        """
        if args is None:
            args = b""

        raw_cmd = b"stats %b\r\n" % args
        response_stream = await self._execute_raw_cmd(
            cmd=raw_cmd,
            end_symbols=[
                END,
            ],
        )

        result = {}
        line = response_stream.readline()
        while line != END:
            terms = line.split()

            if len(terms) == 2 and terms[0] == b"STAT":
                result[terms[1]] = None
            elif len(terms) == 3 and terms[0] == b"STAT":
                result[terms[1]] = terms[2]
            elif len(terms) >= 3 and terms[0] == b"STAT":
                result[terms[1]] = b" ".join(terms[2:])
            else:
                raise ResponseException(raw_cmd, response_stream.getvalue())

            line = response_stream.readline()

        return result

    async def version(self) -> bytes:
        """
        "version" is a command with no arguments:

        version\r\n

        In response, the server sends

        "VERSION <version>\r\n", where <version> is the version string for the
        server.

        "verbosity" is a command with a numeric argument. It always succeeds,
        and the server sends "OK\r\n" in response (unless "noreply" is given
        as the last parameter). Its effect is to set the verbosity level of
        the logging output.
        """
        raw_cmd = b"version\r\n"
        response_stream = await self._execute_raw_cmd(
            cmd=raw_cmd, one_line_response=True
        )
        response = response_stream.readline()

        if not response.startswith(VERSION):
            raise ResponseException(raw_cmd, response_stream.getvalue())

        versions = response.rstrip(b"\r\n").split(maxsplit=1)
        return versions[1]

    async def flush_all(self) -> bool:
        """Its effect is to invalidate all existing items immediately

        "flush_all" is a command with an optional numeric argument. It always
        succeeds, and the server sends "OK\r\n" in response (unless "noreply"
        is given as the last parameter). Its effect is to invalidate all
        existing items immediately (by default) or after the expiration
        specified.  After invalidation none of the items will be returned in
        response to a retrieval command (unless it's stored again under the
        same key *after* flush_all has invalidated the items). flush_all
        doesn't actually free all the memory taken up by existing items; that
        will happen gradually as new items are stored. The most precise
        definition of what flush_all does is the following: it causes all
        items whose update time is earlier than the time at which flush_all
        was set to be executed to be ignored for retrieval purposes.
        """
        raw_cmd = b"flush_all\r\n"
        response_stream = await self._execute_raw_cmd(
            cmd=raw_cmd, one_line_response=True
        )
        response = response_stream.readline()

        if not response.startswith(OK):
            raise ResponseException(raw_cmd, response_stream.getvalue())

        return True
