import sys
import os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["JWT_SECRET_KEY"] = "test_secret_key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["TESTING"] = "True" # Set TESTING environment variable for conditional logic

import pytest
import pytest_asyncio # Import pytest_asyncio
from fastapi import Request # Import Request
from fastapi.responses import JSONResponse, Response # Import JSONResponse and Response
from fastapi.testclient import TestClient
from src.models.session import Session as SessionModel # Explicitly import SessionModel
from sqlmodel import create_engine, Session, SQLModel
from src.main import create_app
from src.database import get_session
from dotenv import load_dotenv
import src.models # Import all models to ensure they are registered with SQLModel.metadata
import asyncio
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from src.utils.redis_utils import redis_client, initialize_redis, close_redis_connection
from unittest.mock import AsyncMock, patch

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

@pytest_asyncio.fixture(name="client")
async def client_fixture(session: Session):
    test_engine = session.bind

    def get_session_override():
        with Session(test_engine) as session:
            yield session
    
    app = create_app(db_engine=test_engine)
    app.dependency_overrides[get_session] = get_session_override
    
    # Create a mock Redis client for FastAPILimiter.redis
    mock_redis_client_for_limiter = AsyncMock()
    mock_redis_client_for_limiter.script_load.return_value = "mock_sha"

    # Create a mock Redis client for FastAPILimiter.redis
    mock_redis_client_for_limiter = AsyncMock()
    mock_redis_client_for_limiter.script_load.return_value = "mock_sha"

    # Create mock identifier and callback functions
    async def mock_identifier(request: Request):
        return "mock_identifier"

    async def mock_http_callback(request: Request, response: Response, pexpire: int):
        # Return a dummy successful response to bypass rate limiting in tests
        return None

    # Patch FastAPILimiter.redis, FastAPILimiter.init, FastAPILimiter.identifier, and FastAPILimiter.http_callback
    with patch("fastapi_limiter.FastAPILimiter.redis", new=mock_redis_client_for_limiter), \
         patch("fastapi_limiter.FastAPILimiter.init", new_callable=AsyncMock), \
         patch("fastapi_limiter.FastAPILimiter.identifier", new=mock_identifier), \
         patch("fastapi_limiter.FastAPILimiter.http_callback", new=mock_http_callback):
        yield TestClient(app)
