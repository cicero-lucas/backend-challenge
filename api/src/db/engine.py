import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/shipay",
)

engine: Engine = create_engine(DATABASE_URL)
