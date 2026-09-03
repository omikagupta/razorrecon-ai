import os

os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg2://razorrecon:razorrecon@127.0.0.1:5432/razorrecon"
)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import reconciliation  # noqa: F401


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()