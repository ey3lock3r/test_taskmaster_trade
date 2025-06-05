import sys
import os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["JWT_SECRET_KEY"] = "test_secret_key"
os.environ["JWT_ALGORITHM"] = "HS256"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel
from src.main import create_app
from src.database import get_session
from dotenv import load_dotenv

if os.path.exists(".env.test"):
    load_dotenv(".env.test")
else:
    load_dotenv()

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///./test.db", echo=False, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine) # Create tables for the test database
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine) # Drop tables after tests

@pytest.fixture(name="client")
def client_fixture(session: Session):
    # Use the engine from the session fixture to create new sessions for overrides
    test_engine = session.bind

    def get_session_override():
        with Session(test_engine) as session:
            yield session
    
    app = create_app(db_engine=test_engine) # Pass the test_engine to create_app
    app.dependency_overrides[get_session] = get_session_override
    
    with TestClient(app) as client:
        yield client