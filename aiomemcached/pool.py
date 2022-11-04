import asyncio
from asyncio.streams import StreamReader, StreamWriter
from collections import deque

from .constants import DEFAULT_POOL_MAXSIZE, DEFAULT_POOL_MINSIZE, DEFAULT_TIMEOUT
from .exceptions import ConnectException

__all__ = ["MemcachedPool", "MemcachedConnection"]


class MemcachedConnection:
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.in_use = False
        self.reader = reader
        self.writer = writer

    async def close(self):
        self.reader.feed_eof()
        self.writer.close()


class MemcachedPool:
    def __init__(
        self,
        host: str,
        port: int,
        minsize: int = DEFAULT_POOL_MINSIZE,
        maxsize: int = DEFAULT_POOL_MAXSIZE,
        connect_timeout: int = DEFAULT_TIMEOUT,
    ):
        self._host = host
        self._port = port
        self._connect_timeout = connect_timeout

        self._pool = deque()
        self._pool_minsize = minsize
        self._pool_maxsize = maxsize
        self._pool_lock = asyncio.Lock()

    def size(self) -> int:
        return len(self._pool)

    async def _create_new_connection(self) -> MemcachedConnection:
        while self.size() >= self._pool_maxsize:
            await asyncio.sleep(1)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._connect_timeout,
            )
        except (ConnectionError, TimeoutError, OSError) as e:
            raise ConnectException(e)

        return MemcachedConnection(reader, writer)

    async def acquire(self) -> MemcachedConnection:
        """Acquires a not in used connection from pool.
        Creates new connection if needed.
        """
        try:
            conn = self._pool[0]
            if conn.in_use:
                raise IndexError

            conn.in_use = True
            self._pool.rotate(-1)
            return conn

        except IndexError:
            pass

        conn = await self._create_new_connection()
        conn.in_use = True
        self._pool.append(conn)
        return conn

    async def release(self, conn: MemcachedConnection) -> None:
        """Returns used connection back into pool.
        When pool size > minsize the connection will be dropped.
        """
        await self._pool_lock.acquire()
        try:
            if conn not in self._pool:
                return

            if self.size() > self._pool_minsize:
                await conn.close()
                self._pool.remove(conn)

            else:
                conn.in_use = False

        finally:
            self._pool_lock.release()

    async def dispose(self, conn: MemcachedConnection) -> None:
        """Closes and disposes of the connection."""
        if conn in self._pool:
            self._pool.remove(conn)

        try:
            await conn.close()
        except ConnectionError:
            pass

    async def clear(self) -> None:
        """Clear pool connections.
        Close and remove all free connections.
        """
        while self._pool:
            conn = self._pool.pop()
            await conn.close()
