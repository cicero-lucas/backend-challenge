import bcrypt
from fastapi.testclient import TestClient
from sqlalchemy.engine import Connection
from src.db.tables import users


def test_create_user_success(client: TestClient, seed_role):
    role_id = seed_role("editor")
    payload = {"name": "Alice", "email": "alice@example.com", "role_id": role_id}
    response = client.post("/users/", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["role_id"] == role_id


def test_create_user_password_is_hashed(client: TestClient, seed_role, db_conn: Connection):
    role_id = seed_role("admin")
    payload = {"name": "Charlie", "email": "charlie@example.com", "role_id": role_id, "password": "mysecret"}
    response = client.post("/users/", json=payload)
    assert response.status_code == 201
    assert response.json()["password"] == "mysecret"

    row = db_conn.execute(users.select().where(users.c.email == "charlie@example.com")).fetchone()
    assert bcrypt.checkpw(b"mysecret", row.password.encode())


def test_create_user_auto_password(client: TestClient, seed_role):
    role_id = seed_role("viewer")
    payload = {"name": "Bob", "email": "bob@example.com", "role_id": role_id}
    response = client.post("/users/", json=payload)
    assert response.status_code == 201
    assert response.json()["password"]  # senha gerada não é vazia


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
