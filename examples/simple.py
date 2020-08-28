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
