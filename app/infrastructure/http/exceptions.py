from fastapi import status
from fastapi.responses import ORJSONResponse

from app.application.exceptions import BaseCustomException, SampleException


class APIError(Exception):
    status_code: int
    code: int
    message: str
    detail: str = None

    def __init__(self, message=None, detail: str = None):
        if message:
            self.message = message
        self.detail = detail

    @classmethod
    def to_spec(cls):
        return {
            "content": {
                "application/json": {
                    "example": {
                        "status_code": cls.status_code,
                        "code": cls.code,
                        "message": cls.message,
                        "detail": cls.detail if cls.detail else "...",
                    }
                }
            }
        }


class InternalServerError(APIError):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: int = 1001
    message: str = "Internal Server Error"
    detail: str = "An error occurred on the server."


class UnauthorizedError(APIError):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    code: int = 1002
    message: str = "Unauthorized Error"


class ForbiddenError(APIError):
    status_code: int = status.HTTP_403_FORBIDDEN
    code: int = 1003
    message: str = "Forbidden Error"


class BadRequestError(APIError):
    status_code: int = status.HTTP_400_BAD_REQUEST
    code: int = 1004
    message: str = "Bad Request Error"


class NotFoundError(APIError):
    status_code: int = status.HTTP_404_NOT_FOUND
    code: int = 1005
    message: str = "Not Found Error"


HTTP_400_BAD_REQUEST_LIST = (SampleException,)  # 해당 에러가 내려오면 404로 처리한다.


def api_exception_handler(request, exc):
    if isinstance(exc, BaseCustomException):
        if type(exc) in HTTP_400_BAD_REQUEST_LIST:
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        content = {
            "status": status_code,
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        }
    elif isinstance(exc, APIError):
        status_code = exc.status_code
        content = {
            "status": status_code,
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
        }
    else:
        status_code = InternalServerError.status_code
        content = {
            "status": status_code,
            "code": InternalServerError.code,
            "message": InternalServerError.message,
            "detail": InternalServerError.detail,
        }

    return ORJSONResponse(
        headers={"Access-Control-Allow-Origin": "*"},
        status_code=status_code,
        content=content,
    )
