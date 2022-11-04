__all__ = [
    "ClientException",
    "ValidationException",
    "ResponseException",
    "ConnectException",
    "TimeoutException",
]


class ClientException(Exception):
    """Base Exception for AioMemCached"""

    pass


class ValidationException(ClientException):
    pass


class ResponseException(ClientException):
    def __init__(self, raw_cmd, response, ext_message=None):
        message = "Memcached::[{}] response is not expected:{}{}".format(
            raw_cmd, "{}, ".format(ext_message) if ext_message else "", response
        )
        super().__init__(message)


class ConnectException(ClientException, ConnectionError):
    pass


class TimeoutException(ConnectException, TimeoutError):
    pass
