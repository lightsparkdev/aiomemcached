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
