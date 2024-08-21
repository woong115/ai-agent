import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.settings import Settings


@pytest.fixture(scope="session")
def settings():
    settings = Settings()
    yield settings


@pytest.fixture(scope="session")
def app():
    application = create_app()
    yield application


@pytest_asyncio.fixture
async def integration_test_client(settings):
    """해당 fixture는 통합테스트를 위한 클라이언트입니다.
    make up된 실제 로컬 api 컨테이너에 요청하여 테스트하기 때문에 모든 컨테이너가 up되어 있어야 합니다.
    또한 해당 클라이언트를 사용하여 테스트할때는 watchfiles 작동을 방지하기 위해",
    테스트 실행 이후에 코드를 변경해서는 안됩니다.
    또한 디버깅 모드도 불가합니다."""
    async with AsyncClient(base_url=settings.self_host, timeout=30.0) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def test_client(app, settings):
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
            yield test_client
