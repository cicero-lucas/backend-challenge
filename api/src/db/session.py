from typing import Generator
from sqlalchemy.engine import Connection
from .engine import engine


def get_db() -> Generator[Connection, None, None]:
    with engine.connect() as conn:
        yield conn
