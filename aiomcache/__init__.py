"""memcached client, based on mixpanel's memcache_client library

Usage example::

    import aiomcache
    mc = aiomcache.Client("127.0.0.1", 11211, timeout=1, connect_timeout=5)
    yield from mc.set("some_key", "Some value")
    value = yield from mc.get("some_key")
    yield from mc.delete("another_key")
"""

from .client import Client
from .exceptions import ClientException, ValidationException

__all__ = ('Client', 'ClientException', 'ValidationException')

__name__ = 'aiomemcached'
__version__ = '0.6.0'

__author__ = 'Nikolay Kim'
__author_email__ = 'fafhrd91@gmail.com'
__maintainer__ = ', '.join((
    'Nikolay Kim <fafhrd91@gmail.com>',
    'Andrew Svetlov <andrew.svetlov@gmail.com>',
    'Rex Zhang <rex.zhang@gmail.com',
))
__licence__ = 'BSD'

__description__ = 'A pure python asyncio memcached client,' \
                  ' fork from aiomcache.'
__project_url__ = 'https://github.com/rexzhang/aiomemcached'
