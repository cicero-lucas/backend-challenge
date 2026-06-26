import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from src.main import app
from src.db.session import get_db
from src.db.tables import metadata, roles

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL)
    metadata.create_all(engine)
    yield engine
    metadata.drop_all(engine)


@pytest.fixture()
def db_conn(db_engine) -> Connection:
    with db_engine.connect() as conn:
        yield conn
        conn.rollback()


@pytest.fixture()
def client(db_conn: Connection) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_conn
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_role(db_conn: Connection):
    def _factory(description: str = "admin") -> int:
        result = db_conn.execute(roles.insert().values(description=description))
        db_conn.commit()
        return result.inserted_primary_key[0]
    return _factory
