============
AioMemcached
============

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

A pure-Python(3.7+) asyncio memcached client, fork from aiomcache.

============= =========================================
Author        Nikolay Kim <fafhrd91@gmail.com>
Maintainer    Rex Zhang <rex.zhang@gmail.com>
Contributions Andrew Svetlov <andrew.svetlov@gmail.com>
============= =========================================

Install
=======

.. code-block:: shell

    pip install -U AioMemcached

Usage
=====

Base command examples
---------------------

Code

.. code:: python

    import asyncio

    import aiomemcached

    KEY_1, KEY_2 = b'k1', b'k2'
    VALUE_1, VALUE_2 = b'1', b'v2'


    async def base_command():
        client = aiomemcached.Client()

        print('--- version() ---')
        print(await client.version())

        print()

        print('--- set(KEY1, VALUE_1), get(KEY_1) ---')
        await client.set(KEY_1, VALUE_1)
        value, info = await client.get(KEY_1)
        print(value, info)

        print('--- after incr(KEY_1), get(KEY_1) ---')
        await client.incr(KEY_1)
        value, info = await client.get(KEY_1)
        print(value, info)

        print('--- after decr(KEY_1), get(KEY_1) ---')
        await client.decr(KEY_1)
        value, info = await client.get(KEY_1)
        print(value, info)

        print('--- gets(KEY_1) ---')
        value, info = await client.gets(KEY_1)
        print(value, info)

        print()
        keys = [KEY_1, KEY_2]

        print('--- get_many() ---')
        values, info = await client.get_many(keys)
        print(values, info)

        print('--- gets_many() ---')
        values, info = await client.gets_many(keys)
        print(values, info)

        print('--- after set(KEY2, VALUE_2), gets_many() ---')
        await client.set(KEY_2, VALUE_2)
        values, info = await client.gets_many(keys)
        print(values, info)

        print('--- after delete(KEY_1), gets_many() ---')
        await client.delete(KEY_1)
        value, info = await client.gets_many(keys)
        print(value, info)

        print()

        print('--- set(KEY2, VALUE_2), get(KEY_2) ---')
        await client.set(KEY_2, VALUE_2)
        value, info = await client.get(KEY_2)
        print(value, info)

        print('--- after append(KEY_2, b"append"), get(KEY_2) ---')
        await client.append(KEY_2, b'append')
        value, info = await client.get(KEY_2)
        print(value, info)

        print('--- after flush_all(), get_many() ---')
        await client.flush_all()
        values, info = await client.get_many(keys)
        print(values, info)

        return


    if __name__ == '__main__':
        asyncio.run(base_command())

Output

.. code:: shell

    --- version() ---
    b'1.6.6'

    --- set(KEY1, VALUE_1), get(KEY_1) ---
    b'1' {'flags': 0, 'cas': None}
    --- after incr(KEY_1), get(KEY_1) ---
    b'2' {'flags': 0, 'cas': None}
    --- after decr(KEY_1), get(KEY_1) ---
    b'1' {'flags': 0, 'cas': None}
    --- gets(KEY_1) ---
    b'1' {'flags': 0, 'cas': 11248}

    --- get_many() ---
    {b'k1': b'1'} {b'k1': {'flags': 0, 'cas': None}}
    --- gets_many() ---
    {b'k1': b'1'} {b'k1': {'flags': 0, 'cas': 11248}}
    --- after set(KEY2, VALUE_2), gets_many() ---
    {b'k2': b'v2', b'k1': b'1'} {b'k2': {'flags': 0, 'cas': 11249}, b'k1': {'flags': 0, 'cas': 11248}}
    --- after delete(KEY_1), gets_many() ---
    {b'k2': b'v2'} {b'k2': {'flags': 0, 'cas': 11249}}

    --- set(KEY2, VALUE_2), get(KEY_2) ---
    b'v2' {'flags': 0, 'cas': None}
    --- after append(KEY_2, b"append"), get(KEY_2) ---
    b'v2append' {'flags': 0, 'cas': None}
    --- after flush_all(), get_many() ---
    {} {}

Development
===========

Coverage Report

.. code-block:: shell

    python -m pytest --cov=. --cov-report html
