import asyncio

import aiomemcached


async def base_command():
    client = aiomemcached.Client()

    print("client.version() =>", await client.version())

    print("\ninit key and value:")
    k1, k2, v1, v2 = b"k1", b"k2", b"1", b"v2"
    print("k1, k2, v1, v2 = b'k1', b'k2', b'1', b'2'")
    keys = [k1, k2]
    print("keys = [k1, k2]")

    print("\nget and set key:")
    print("client.set(k1, v1) =>", await client.set(k1, v1))
    print("client.get(k1) =>", await client.get(k1))
    print("client.set(k2, v2) =>", await client.set(k2, v2))
    print("client.get(k2) =>", await client.get(k2))

    print("\nincr and decr value:")
    print("client.incr(k1) =>", await client.incr(k1))
    print("client.decr(k1) =>", await client.decr(k1))

    print("\nget multi key:")
    print("client.get_many(keys) =>", await client.get_many(keys))
    print("client.gets_many(keys) =>", await client.gets_many(keys))
    print("client.set(k2, v2) =>", await client.set(k2, v2))
    print("client.gets_many(keys) =>", await client.gets_many(keys))

    print("\ndelete key:")
    print("client.delete(k1) =>", await client.delete(k1))
    print("client.gets_many(keys) =>", await client.gets_many(keys))

    print("\nappend value to key:")
    print("client.append(k2, b'append') =>", await client.append(k2, b"append"))
    print("client.get(k2) =>", await client.get(k2))

    print("flush memcached:")
    print("client.flush_all() =>", await client.flush_all())
    print("client.get_many(keys) =>", await client.get_many(keys))

    return


if __name__ == "__main__":
    asyncio.run(base_command())
