from fastapi.testclient import TestClient


def test_create_user_success(client: TestClient, seed_role):
    role_id = seed_role("editor")
    payload = {"name": "Alice", "email": "alice@example.com", "role_id": role_id}
    response = client.post("/users/", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["role_id"] == role_id


def test_create_user_auto_password(client: TestClient, seed_role):
    role_id = seed_role("viewer")
    payload = {"name": "Bob", "email": "bob@example.com", "role_id": role_id}
    response = client.post("/users/", json=payload)
    assert response.status_code == 201


def test_create_user_invalid_role(client: TestClient):
    payload = {"name": "Ghost", "email": "ghost@example.com", "role_id": 9999}
    response = client.post("/users/", json=payload)
    assert response.status_code == 404


def test_create_user_invalid_email(client: TestClient, seed_role):
    role_id = seed_role()
    payload = {"name": "Bad", "email": "not-an-email", "role_id": role_id}
    response = client.post("/users/", json=payload)
    assert response.status_code == 422


def test_create_user_missing_required_fields(client: TestClient):
    response = client.post("/users/", json={"name": "Incomplete"})
    assert response.status_code == 422
