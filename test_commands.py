import asyncio
from io import BytesIO

import pytest
from unittest import mock

from aiomemcached.exceptions import ClientException, ValidationException


async def assert_raise_with_mocked_execute_raw_cmd(
    client, server_response: bytes, exception, func, *args, **kwargs
):
    response = BytesIO()
    response.write(server_response)
    response.seek(0)

    with mock.patch.object(client, '_execute_raw_cmd') as patched:
        patched.return_value = response
        with pytest.raises(exception):
            await func(*args, **kwargs)


@pytest.mark.asyncio
async def test_close(client):
    await client.close()
    assert client._pool.size() == 0


@pytest.mark.asyncio
async def test_get_set(client):
    key, value = b'test:key:get_set', b'1'
    default = b'default'
    exptime = 1

    await client.set(key, value)

    result = await client.get(key)
    assert result == value

    result = await client.get(b'not:' + key, default=default)
    assert result == default

    result = await client.get(b'not:' + key)
    assert result is None

    # set param expire ---
    await client.set(key, value, exptime=exptime)
    result = await client.get(key)
    assert result == value

    await asyncio.sleep(1.1)

    result = await client.get(key)
    assert result is None

    # set param errors ---
    with pytest.raises(ValidationException):
        await client.set(key, value, exptime=-1)

    with pytest.raises(ValidationException):
        await client.set(key, value, flags=-1)


@pytest.mark.asyncio
async def test_gets_set_cas(client):
    key, value_1, value_2 = b'test:key:gets_set_cas', b'1', b'2'
    default = b'default'
    await client.set(key, value_1)

    # basic function ---
    result_value, result_cas = await client.gets(key)
    assert result_value == value_1
    assert isinstance(result_cas, int)

    result_value, result_cas = await client.gets(
        b'not:' + key, default=default
    )
    assert result_value == default
    assert result_cas is None

    result_value, result_cas = await client.gets(b'not:' + key)
    assert result_value is None
    assert result_cas is None

    # cas ---
    await client.set(key, value_1)
    result_value, cas = await client.gets(key)

    stored = await client.cas(key, value_2, cas + 1)
    assert stored is False
    result_value, result_cas = await client.gets(key)
    assert result_value == value_1
    assert result_cas == cas

    stored = await client.cas(key, value_2, cas)
    assert stored is True
    result_value, result_cas = await client.gets(key)
    assert result_value == value_2
    assert isinstance(result_cas, int)


@pytest.mark.asyncio
async def test_get_many_set(client):
    key_1, value_1 = b'test:key:get_many_set_1', b'1'
    key_2, value_2 = b'test:key:get_many_set_2', b'2'
    await client.set(key_1, value_1)
    await client.set(key_2, value_2)

    keys = [key_1, key_2]
    result = await client.get_many(keys)
    result[key_1] = value_1
    result[key_2] = value_2

    keys = [b'not' + key_1, key_2]
    result = await client.get_many(keys)
    assert key_1 not in result  # TODO default ??!!

    keys = []
    result = await client.get_many(keys)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_gets_many_set(client):
    key_1, value_1 = b'test:key:gets_many_set_1', b'1'
    key_2, value_2 = b'test:key:gets_many_set_2', b'2'
    await client.set(key_1, value_1)
    await client.set(key_2, value_2)

    keys = [key_1, key_2]
    result_value, result_cas = await client.gets_many(keys)
    assert result_value[key_1] == value_1
    assert result_value[key_2] == value_2
    # assert isinstance(result_cas[key_1], int) # TODO!!!
    # assert isinstance(result_cas[key_2], int)


@pytest.mark.asyncio
async def test_multi_get(client):
    key1, value1 = b'test:key:multi_get:1', b'1'
    key2, value2 = b'test:key:multi_get:2', b'2'
    await client.set(key1, value1)
    await client.set(key2, value2)
    test_value = await client.multi_get(key1, key2)
    assert test_value == (value1, value2)

    test_value = await client.multi_get(b'not' + key1, key2)
    assert test_value == (None, value2)
    test_value = await client.multi_get()
    assert test_value == ()


@pytest.mark.asyncio
async def test_add(client):
    key, value = b'test:key:add', b'1'
    await client.set(key, value)

    test_value = await client.add(key, b'2')
    assert not test_value

    test_value = await client.add(b'not:' + key, b'2')
    assert test_value

    test_value = await client.get(b'not:' + key)
    assert test_value == b'2'


@pytest.mark.asyncio
async def test_replace(client):
    key, value = b'test:key:replace', b'1'
    await client.set(key, value)

    test_value = await client.replace(key, b'2')
    assert test_value
    # make sure value exists
    test_value = await client.get(key)
    assert test_value == b'2'

    test_value = await client.replace(b'not:' + key, b'3')
    assert not test_value
    # make sure value exists
    test_value = await client.get(b'not:' + key)
    assert test_value is None


@pytest.mark.asyncio
async def test_append(client):
    key, value = b'test:key:append', b'1'
    await client.set(key, value)

    test_value = await client.append(key, b'2')
    assert test_value

    # make sure value exists
    test_value = await client.get(key)
    assert test_value == b'12'

    test_value = await client.append(b'not:' + key, b'3')
    assert not test_value
    # make sure value exists
    test_value = await client.get(b'not:' + key)
    assert test_value is None


@pytest.mark.asyncio
async def test_prepend(client):
    key, value = b'test:key:prepend', b'1'
    await client.set(key, value)

    test_value = await client.prepend(key, b'2')
    assert test_value

    # make sure value exists
    test_value = await client.get(key)
    assert test_value == b'21'

    test_value = await client.prepend(b'not:' + key, b'3')
    assert not test_value
    # make sure value exists
    test_value = await client.get(b'not:' + key)
    assert test_value is None


@pytest.mark.asyncio
async def test_delete(client):
    key, value = b'test:key:delete', b'value'
    await client.set(key, value)

    # make sure value exists
    test_value = await client.get(key)
    assert test_value == value

    is_deleted = await client.delete(key)
    assert is_deleted
    # make sure value does not exists
    test_value = await client.get(key)
    assert test_value is None

    # await _assert_raise_with_mocked_execute_raw_cmd(
    #     client, b'SERVER_ERROR error\r\n', ClientException,
    #     client.delete, b'not:' + key
    # )

    # delete key not exists
    is_deleted = await client.delete(b'not:key')
    assert not is_deleted


@pytest.mark.asyncio
async def test_incr_decr(client):
    # incr ---
    key, value = b'test:key:incr:1', b'1'
    await client.set(key, value)

    test_value = await client.incr(key, 2)
    assert test_value == 3

    # make sure value exists
    test_value = await client.get(key)
    assert test_value == b'3'

    # incr error ---
    key, value = b'test:key:incr:2', b'string'
    await client.set(key, value)

    with pytest.raises(ClientException):
        await client.incr(key, 2)

    with pytest.raises(ClientException):
        await client.incr(key, 3.14)

    # decr ---
    key, value = b'test:key:decr:1', b'17'
    await client.set(key, value)

    test_value = await client.decr(key, 2)
    assert test_value == 15

    test_value = await client.get(key)
    assert test_value == b'15'

    test_value = await client.decr(key, 1000)
    assert test_value == 0

    # decr ---
    key, value = b'test:key:decr:2', b'string'
    await client.set(key, value)

    with pytest.raises(ClientException):
        await client.decr(key, 2)

    with pytest.raises(ClientException):
        await client.decr(key, 3.14)

    # common --
    key, value = b'test:key:incr_decr:1', b'1'
    await client.set(key, value)
    await client.incr(key, increment=1)
    await client.decr(key, decrement=1)

    with pytest.raises(ValidationException):
        await client.incr(key, value=-1)

    await assert_raise_with_mocked_execute_raw_cmd(
        client, b'NOT_FOUND\r\n', ClientException,
        client.incr, b'not:' + key
    )


@pytest.mark.asyncio
async def test_touch(client):
    key, value = b'test:key:touch:1', b'17'
    await client.set(key, value)

    test_value = await client.touch(key, 1)
    assert test_value

    test_value = await client.get(key)
    assert test_value == value

    await asyncio.sleep(1.1)

    test_value = await client.get(key)
    assert test_value is None

    test_value = await client.touch(b'not:' + key, 1)
    assert not test_value

    # await _do_mock_execute_raw_cmd(
    #     client, b'SERVER_ERROR error\r\n', ClientException,
    #     client.touch, b'not:' + key, 1
    # )


@pytest.mark.asyncio
async def test_stats(client):
    stats = await client.stats()
    assert b'pid' in stats


@pytest.mark.asyncio
async def test_version(client):
    version = await client.version()
    stats = await client.stats()
    assert version == stats[b'version']

    await assert_raise_with_mocked_execute_raw_cmd(
        client, b'SERVER_ERROR error\r\n', ClientException,
        client.version
    )


@pytest.mark.asyncio
async def test_flush_all(client):
    key, value = b'test:key:flush_all', b'flush_all_value'
    await client.set(key, value)
    # make sure value exists
    test_value = await client.get(key)
    assert test_value == value
    # flush data
    await client.flush_all()
    # make sure value does not exists
    test_value = await client.get(key)
    assert test_value is None

    await assert_raise_with_mocked_execute_raw_cmd(
        client, b'SERVER_ERROR error\r\n', ClientException,
        client.flush_all
    )
