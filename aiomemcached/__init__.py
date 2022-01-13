"""memcached client, based on mixpanel's memcache_client library

Usage example::

    import asyncio
    import aiomemcached


    async def example():
        c = aiomemcached.Client()
        await c.set(b"some_key", b"Some value")
        value = await c.get(b"some_key")
        print(value)
        values = await c.multi_get(b"some_key", b"other_key")
        print(values)
        await c.delete(b"another_key")


    asyncio.run(example())
"""

from .client import Client
from .exceptions import (
    ClientException,
    ValidationException,
    ResponseException,
    ConnectException,
    TimeoutException,
)

__all__ = (
    "Client",
    "ClientException",
    "ValidationException",
    "ResponseException",
    "ConnectException",
    "TimeoutException",
)

__name__ = "AioMemcached"
__version__ = "0.8.3"

__author__ = "Nikolay Kim"
__author_email__ = "fafhrd91@gmail.com"
__maintainer__ = "Rex Zhang <rex.zhang@gmail.com>"
__contributions__ = [
    "Nikolay Kim <fafhrd91@gmail.com>",
    "Andrew Svetlov <andrew.svetlov@gmail.com>",
    "Rex Zhang <rex.zhang@gmail.com>",
]

__licence__ = "BSD"

__description__ = (
    "A pure-Python(3.7+) asyncio memcached client," " fork from aiomcache. "
)
__project_url__ = "https://github.com/rexzhang/aiomemcached"
