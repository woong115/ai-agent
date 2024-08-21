from app.application.exceptions import SampleException


class SampleService:
    def __init__(self): ...

    def exception_sample(self, detail: str):
        raise SampleException(detail)
