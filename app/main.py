import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.containers import Container
from app.infrastructure.http import sample_controller
from app.infrastructure.http.chat import chat_controller
from app.infrastructure.http.exceptions import api_exception_handler
from app.settings import settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.container.config = settings
    application.container.init_resources()
    print(f"Server started...")
    yield
    application.container.shutdown_resources()
    print(f"Server shutdown...")


def set_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def set_routers(app: FastAPI) -> None:
    app.include_router(chat_controller.router)
    app.include_router(sample_controller.router)


def set_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, api_exception_handler)


def create_app():
    title = "AI Agent API"
    version = "v1"
    tags_metadata = [
        {
            "name": "AI Agent API",
            "description": "AI 에이전트",
        },
    ]

    description = f"""
## 제공 기능 🚀
* 세션 발급
* Q&A 이력 조회
* 채팅 (stream)

"""

    application = FastAPI(
        lifespan=lifespan,
        title=title,
        version=version,
        docs_url="/api/docs",
        openapi_url="" if settings.stage == "prod" else "/api/openapi.json",
        description=description,
        openapi_tags=tags_metadata,
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            # "docExpansion": "none",
        },
    )

    set_cors(application)
    set_routers(application)
    set_exception_handlers(application)

    application.container = Container()

    return application


app = create_app()
