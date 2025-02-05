import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient


from trading_execution_system.db.settings import Base
from trading_execution_system.main import app
import trading_execution_system.db.settings as db_settings


# use in-memory db for tests
_DB = os.environ["DATABASE_URL"] = "sqlite:///:memory:"

engine = create_engine(_DB, connect_args={"check_same_thread": False})

connection = engine.connect()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)

Base.metadata.create_all(bind=connection)

db_settings.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="function", autouse=True)
def recreate_db():
    """drop and recreate the tables before each test run"""
    Base.metadata.drop_all(bind=connection)
    Base.metadata.create_all(bind=connection)
    yield


@pytest.fixture(scope="session")
def client():
    """create a FastApi test client"""
    with TestClient(app) as c:
        yield c
