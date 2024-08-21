class BaseCustomException(Exception):
    code = 1001
    message = "Unknown error."
    detail = None

    def __init__(self, detail=None):
        self.detail = detail


class SampleException(BaseCustomException):
    code = 1101
    message = "The Sample is unprocessable."
