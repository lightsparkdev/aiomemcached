# AioMemcached

![GitHub](https://img.shields.io/github/license/rexzhang/aiomemcached)
![Pytest Workflow Status](https://github.com/rexzhang/aiomemcached/actions/workflows/check-pytest.yml/badge.svg)
[![codecov](https://codecov.io/gh/rexzhang/aiomemcached/branch/main/graph/badge.svg?token=UCO9BUNU6C)](https://codecov.io/gh/rexzhang/aiomemcached)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![](https://img.shields.io/pypi/v/aiomemcached.svg)](https://pypi.org/project/aiomemcached/)
[![](https://img.shields.io/pypi/pyversions/aiomemcached.svg)](https://pypi.org/project/aiomemcached/)
[![](https://img.shields.io/pypi/dm/aiomemcached.svg)](https://pypi.org/project/aiomemcached/)

A pure-Python(3.7+) zero-depend asyncio memcached client, fork from [aiomcache](https://pypi.org/project/aiomcache/).

| | people | 
--- | ---
Author | Nikolay Kim <fafhrd91@gmail.com>
Maintainer | Rex Zhang <rex.zhang@gmail.com>
Contributions | Andrew Svetlov <andrew.svetlov@gmail.com>

## Install

```shell
pip install -U AioMemcached
```

## Usage

### Base command examples

Code

```python
import asyncio

import aiomemcached


async def base_command():
    client = aiomemcached.Client()

    print('client.version() =>', await client.version())

    print('\ninit key and value:')
    k1, k2, v1, v2 = b'k1', b'k2', b'1', b'v2'
    print("k1, k2, v1, v2 = b'k1', b'k2', b'1', b'2'")
    keys = [k1, k2]
    print("keys = [k1, k2]")

    print('\nget and set key:')
    print('client.set(k1, v1) =>', await client.set(k1, v1))
    print('client.get(k1) =>', await client.get(k1))
    print('client.set(k2, v2) =>', await client.set(k2, v2))
    print('client.get(k2) =>', await client.get(k2))

    print('\nincr and decr value:')
    print('client.incr(k1) =>', await client.incr(k1))
    print('client.decr(k1) =>', await client.decr(k1))

    print('\nget multi key:')
    print('client.get_many(keys) =>', await client.get_many(keys))
    print('client.gets_many(keys) =>', await client.gets_many(keys))
    print('client.set(k2, v2) =>', await client.set(k2, v2))
    print('client.gets_many(keys) =>', await client.gets_many(keys))

    print('\ndelete key:')
    print('client.delete(k1) =>', await client.delete(k1))
    print('client.gets_many(keys) =>', await client.gets_many(keys))

    print('\nappend value to key:')
    print("client.append(k2, b'append') =>",
          await client.append(k2, b'append'))
    print('client.get(k2) =>', await client.get(k2))

    print('flush memcached:')
    print('client.flush_all() =>', await client.flush_all())
    print('client.get_many(keys) =>', await client.get_many(keys))

    return


if __name__ == '__main__':
    asyncio.run(base_command())
```

Output

```
client.version() => b'1.6.9'

init key and value:
k1, k2, v1, v2 = b'k1', b'k2', b'1', b'2'
keys = [k1, k2]

get and set key:
client.set(k1, v1) => True
client.get(k1) => (b'1', {'flags': 0, 'cas': None})
client.set(k2, v2) => True
client.get(k2) => (b'v2', {'flags': 0, 'cas': None})

incr and decr value:
client.incr(k1) => 2
client.decr(k1) => 1

get multi key:
client.get_many(keys) => ({b'k1': b'1', b'k2': b'v2'}, {b'k1': {'flags': 0, 'cas': None}, b'k2': {'flags': 0, 'cas': None}})
client.gets_many(keys) => ({b'k1': b'1', b'k2': b'v2'}, {b'k1': {'flags': 0, 'cas': 168}, b'k2': {'flags': 0, 'cas': 166}})
client.set(k2, v2) => True
client.gets_many(keys) => ({b'k1': b'1', b'k2': b'v2'}, {b'k1': {'flags': 0, 'cas': 168}, b'k2': {'flags': 0, 'cas': 169}})

delete key:
client.delete(k1) => True
client.gets_many(keys) => ({b'k2': b'v2'}, {b'k2': {'flags': 0, 'cas': 169}})

append value to key:
client.append(k2, b'append') => True
client.get(k2) => (b'v2append', {'flags': 0, 'cas': None})
flush memcached:
client.flush_all() => True
client.get_many(keys) => ({}, {})

```
## Development

Coverage Report

```shell
python -m pytest --cov=. --cov-report html
```
