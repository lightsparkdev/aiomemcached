AioMemcached
============

A pure-Python(3.7+) asyncio memcached client, fork from aiomcache.

.. image:: https://travis-ci.org/rexzhang/aiomemcached.svg?branch=master
    :target: https://travis-ci.org/rexzhang/aiomemcached
.. image:: https://img.shields.io/coveralls/rexzhang/aiomemcached.svg?branch=master
    :target: https://coveralls.io/github/rexzhang/aiomemcached?branch=master
.. image:: https://img.shields.io/pypi/v/aiomemcached.svg
    :target: https://pypi.org/project/aiomemcached/
.. image:: https://img.shields.io/pypi/pyversions/aiomemcached.svg
    :target: https://pypi.org/project/aiomemcached/
.. image:: https://img.shields.io/pypi/dm/aiomemcached.svg
    :target: https://pypi.org/project/aiomemcached/

Install
-------

.. code-block:: shell

    pip install -U aiomemcached

Usage
-----

A simple example.

.. code:: python

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

pytest
------

.. code-block:: shell

    python -m pytest --cov=. --cov-report html
