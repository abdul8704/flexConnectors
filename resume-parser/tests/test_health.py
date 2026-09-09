from fastapi.testclient import TestClient

from app.main import create_app


class FakeDatabase:
    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        pass


def test_health_check() -> None:
    response = TestClient(create_app(database=FakeDatabase())).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"success": True, "status": "healthy"}
