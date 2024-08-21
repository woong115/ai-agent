import pytest


@pytest.mark.asyncio
async def test_session(test_client):
    response = await test_client.post("/api/chat/session")
    assert response.status_code == 201
    session_id = response.json()["session_id"]
    assert session_id
