from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.application.chat.chat_service import ChatService
from app.containers import Container
from app.infrastructure.http.chat.chat_dto import (
    CreateSessionIdResponse,
    GenerateChatStreamRequest,
    GetChatHistoriesResponse,
)
from app.infrastructure.http.exceptions import InternalServerError

router = APIRouter(
    prefix="/api/chat",
    tags=["AI Agent API"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: InternalServerError.to_spec(),
    },
)


async def get_x_chat_session_id(request: Request) -> str:
    session_id = request.headers.get("x-chat-session-id")
    if session_id:
        try:  # uuid 형식이 맞는지 검증
            UUID(session_id, version=4)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session id",
            )
    return session_id


SessionIdProvider = Annotated[str, Depends(get_x_chat_session_id)]


@router.post(
    "/session",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateSessionIdResponse,
)
@inject
async def create_chat_session(
    session_id: SessionIdProvider,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
):
    if not session_id:
        session_id = chat_service.create_session_id()

    return CreateSessionIdResponse(session_id=session_id)


@router.get(
    "/histories",
    status_code=status.HTTP_200_OK,
    response_model=GetChatHistoriesResponse,
)
@inject
async def get_chat_histories(
    session_id: SessionIdProvider,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
):
    histories = []
    if session_id:
        histories = await chat_service.get_chat_histories(session_id)

    return GetChatHistoriesResponse(histories=histories)


@router.post(
    "",
    status_code=status.HTTP_200_OK,
)
@inject
async def stream_chat(
    session_id: SessionIdProvider,
    body: GenerateChatStreamRequest,
    chat_service: ChatService = Depends(Provide[Container.chat_service]),
):
    stream_iter = await chat_service.get_chat_stream(session_id, body.question)

    return StreamingResponse(stream_iter, media_type="text/event-stream")
