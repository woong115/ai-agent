import pytest


@pytest.mark.asyncio
async def test_session(integration_test_client):
    response = await integration_test_client.post("/api/sample/raise")

    print(response.json())
    assert response.status_code == 400
    status = response.json()["status"]
    assert status == 400
    code = response.json()["code"]
    assert code == 1101
    message = response.json()["message"]
    assert message == "The Sample is unprocessable."
    detail = response.json()["detail"]
    assert detail == "This is detail message."
