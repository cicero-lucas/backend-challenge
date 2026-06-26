from fastapi.testclient import TestClient


def test_get_role_success(client: TestClient, seed_role):
    role_id = seed_role("admin")
    response = client.get(f"/roles/{role_id}")
    assert response.status_code == 200
    assert response.json() == {"id": role_id, "description": "admin"}


def test_get_role_not_found(client: TestClient):
    response = client.get("/roles/9999")
    assert response.status_code == 404
