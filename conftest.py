import pytest

import aiomemcached

DEFAULT_CLIENT_PARAMS = dict(host="localhost", port=11211)


# mcache_server_option = None
#
#
# def pytest_addoption(parser):
#     parser.addoption(
#         '--memcached', help='Memcached server')
#
#
# @pytest.fixture(scope='session')
# def unused_port():
#     def f():
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.bind(('127.0.0.1', 0))
#             return s.getsockname()[1]
#     return f
#
#
# def pytest_runtest_setup(item):
#     global mcache_server_option
#     mcache_server_option = item.config.getoption('--memcached')
#
#
# def pytest_ignore_collect(path, config):
#     if 'test_py35' in str(path):
#         if sys.version_info < (3, 5, 0):
#             return True
#
#
# @pytest.fixture(scope='session')
# def session_id():
#     '''Unique session identifier, random string.'''
#     return str(uuid.uuid4())
#
#
# @pytest.fixture(scope='session')
# def docker():
#     return docker_mod.from_env()
#
#
# def mcache_server_actual(host, port='11211'):
#     port = int(port)
#     container = {
#         'host': host,
#         'port': port,
#     }
#     container['mcache_params'] = container.copy()
#     return container
#
#
# @contextlib.contextmanager
# def mcache_server_docker(unused_port, docker, session_id):
#     docker.images.pull('memcached:alpine')
#     container = docker.containers.run(
#         image='memcached:alpine',
#         name='memcached-test-server-{}'.format(session_id),
#         ports={'11211/tcp': None},
#         detach=True,
#     )
#     try:
#         print("Run memcached server")
#         container.start()
#         container.reload()
#         host = container.attrs['NetworkSettings']['IPAddress']
#         # host = container.attrs['NetworkSettings']['Ports']['11211/tcp'][0]['HostIp']
#         port = int(container.attrs['NetworkSettings']['Ports']['11211/tcp'][0]['HostPort'])
#         mcache_params = dict(host=host, port=port)
#         delay = 0.001
#         print("Ping memcached server on {}:{}".format(host, port))
#         for i in range(10):
#             try:
#                 conn = memcache.Client(
#                     ['{host}:{port}'.format_map(mcache_params)])
#                 conn.get_stats()
#                 break
#             except Exception:
#                 time.sleep(delay)
#                 delay *= 2
#         else:
#             pytest.fail("Cannot start memcached")
#         ret = {'Id': container.id}
#         ret['host'] = host
#         ret['port'] = port
#         ret['mcache_params'] = mcache_params
#         time.sleep(0.1)
#         print("Memcached config: {}".format(ret))
#         yield ret
#     finally:
#         container.kill()
#         container.remove()
#
#
# @pytest.fixture(scope='session')
# def mcache_server(unused_port, docker, session_id):
#     if not mcache_server_option:
#         with mcache_server_docker(unused_port, docker, session_id) as ret:
#             return ret
#     else:
#         mcache_params = mcache_server_option.split(':')
#         return mcache_server_actual(*mcache_params)
#
#
@pytest.fixture
# def mcache_params(mcache_server):
def mcache_params():
    # return dict(**mcache_server['mcache_params'])
    return DEFAULT_CLIENT_PARAMS


@pytest.fixture
async def client():
    client = aiomemcached.Client(**DEFAULT_CLIENT_PARAMS)
    yield client
    await client.close()
