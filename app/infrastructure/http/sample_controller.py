from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.sample_service import SampleService
from app.containers import Container
from app.infrastructure.http.exceptions import BadRequestError

router = APIRouter(prefix="/api/sample", tags=["Sample API"])


@router.post(
    "/raise",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: BadRequestError.to_spec(),
    },
)
@inject
async def raise_sample_exception(
    sample_service: SampleService = Depends(Provide[Container.sample_service]),
):
    sample_service.exception_sample("This is detail message.")

    return {}
