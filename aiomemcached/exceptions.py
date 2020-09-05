__all__ = [
    'ClientException',

    'ValidationException',
    'TimeoutException',
    'ResponseException',
]


class ClientException(Exception):
    """Base Exception for AioMemCached"""
    pass


class ValidationException(ClientException):
    pass


class TimeoutException(ClientException):
    pass


class ResponseException(ClientException):
    def __init__(self, raw_cmd, response):
        super().__init__('Memcached::[{}] response is not expected:{}'.format(
            raw_cmd, response
        ))
