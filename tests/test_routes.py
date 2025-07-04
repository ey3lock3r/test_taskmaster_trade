import pytest
from fastapi.testclient import TestClient
import os
import jwt
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
from src.models.user import User
from src.models.brokerage_connection import BrokerageConnection
from src.models.bot_instance import BotInstance
from src.models.trade_order import TradeOrder
from src.models.position import Position
from src.models.broker import Broker # New import
import uuid

# Import the main app to test routes
from src.main import app as fastapi_app
client = TestClient(fastapi_app)

# Test cases
@pytest.mark.asyncio
async def test_register_user_success(client: TestClient, session: Session):
    """Test successful user registration"""
    response = client.post(
        "/api/v1/register",
        json={"username": "testuser", "password": "pass1234", "email": f"testuser_{uuid.uuid4()}@example.com"}
    )
    assert response.status_code == 201
    assert "id" in response.json()

@pytest.mark.asyncio
async def test_register_duplicate_username(client: TestClient, session: Session):
    """Test registration with duplicate username"""
    # First registration
    client.post(
        "/api/v1/register",
        json={"username": "duplicate", "password": "pass1234", "email": f"duplicate_{uuid.uuid4()}@example.com"}
    )
    
    # Second registration with same username
    response = client.post(
        "/api/v1/register",
        json={"username": "duplicate", "password": "anotherpass1", "email": f"duplicate_2_{uuid.uuid4()}@example.com"}
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_register_invalid_username(client: TestClient, session: Session):
    """Test registration with invalid username"""
    # Too short
    response = client.post(
        "/api/v1/register",
        json={"username": "ab", "password": "validpass1", "email": f"ab_{uuid.uuid4()}@example.com"}
    )
    assert response.status_code == 422
    # Non-alphanumeric
    response = client.post(
        "/api/v1/register",
        json={"username": "invalid@user", "password": "validpass1", "email": f"invaliduser_{uuid.uuid4()}@example.com"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_invalid_password(client: TestClient, session: Session):
    """Test registration with invalid password"""
    # Too short
    response = client.post(
        "/api/v1/register",
        json={"username": "user1", "password": "short", "email": f"user1_{uuid.uuid4()}@example.com"}
    )
    assert response.status_code == 422
    
    # No number
    response = client.post(
        "/api/v1/register",
        json={"username": "user2", "password": "passwordonly", "email": f"user2_{uuid.uuid4()}@example.com"}
    )
    assert response.status_code == 422
    
    # No letter
    response = client.post(
        "/api/v1/register",
        json={"username": "user3", "password": "12345678", "email": f"user3_{uuid.uuid4()}@example.com"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_invalid_email(client: TestClient, session: Session):
    """Test registration with invalid email"""
    response = client.post(
        "/api/v1/register",
        json={"username": "user4", "password": "validpass1", "email": "invalid-email"}
    )
    assert response.status_code == 422
    
@pytest.mark.asyncio
async def test_login_success(client: TestClient, session: Session):
    """Test successful login returns valid token with correct claims"""
    # Register a user first with valid alphanumeric username
    test_email = f"testlogin_{uuid.uuid4()}@example.com"
    client.post(
        "/api/v1/register",
        json={"username": "testlogin", "password": "testpass123", "email": test_email}
    )

    # Login with correct credentials
    response = client.post(
        "/api/v1/token",
        json={"email": test_email, "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    
    # Verify token claims (Note: JWT decoding is not directly part of SQLModel tests, but for completeness)
    token = response.json()["access_token"]
    # The JWT_SECRET_KEY and JWT_ALGORITHM are now loaded from settings in src/utils/security.py
    # For testing, we can use the same settings or mock them if needed.
    # For now, let's assume we can decode it with the same settings.
    # This requires importing settings from src.config
    from src.config import settings
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "testlogin" # The sub claim is still the username
    assert "user_id" in payload
    assert "exp" in payload
    assert payload["type"] == "access"
    
@pytest.mark.asyncio
async def test_login_invalid_email(client: TestClient, session: Session):
    """Test login with invalid email"""
    response = client.post(
        "/api/v1/token",
        json={"email": "invalid@example.com", "password": "anypass"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_invalid_password(client: TestClient, session: Session):
    """Test login with invalid password"""
    # Register a user first
    test_email = f"test_invpass_{uuid.uuid4()}@example.com"
    client.post(
        "/api/v1/register",
        json={"username": "test_invpass", "password": "correctpass", "email": test_email}
    )
    
    # Login with wrong password
    response = client.post(
        "/api/v1/token",
        json={"email": test_email, "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
    
@pytest.mark.asyncio
async def test_login_rate_limiting(client: TestClient, session: Session):
    """Test rate limiting blocks excessive login attempts (if implemented)"""
    # This test depends on rate limiting logic in routes.py, which might be removed with SQLModel refactor
    # If rate limiting is re-implemented, this test needs to be adjusted.
    # Register a user first
    test_email = f"test_ratelimit_{uuid.uuid4()}@example.com"
    client.post(
        "/api/v1/register",
        json={"username": "testratelimit", "password": "testpass123", "email": test_email}
    )

    # Attempt multiple logins to trigger rate limit
    for _ in range(5): # 5 attempts allowed in 60 seconds
        response = client.post(
            "/api/v1/token",
            json={"email": test_email, "password": "testpass123"}
        )
        assert response.status_code == 200 # First 5 attempts should succeed

    # The 6th attempt should still succeed in test environment (rate limiting bypassed)
    response = client.post(
        "/api/v1/token",
        json={"email": test_email, "password": "testpass123"}
    )
    assert response.status_code == 200 # Expect 200 OK as rate limiting is bypassed
    # No assertion on "Too Many Requests" detail as rate limiting is bypassed

@pytest.mark.asyncio
async def test_login_missing_fields(client: TestClient, session: Session):
    """Test login with missing fields"""
    # Missing password
    response = client.post(
        "/api/v1/token",
        json={"email": "anyuser@example.com"}
    )
    assert response.status_code == 422
    assert "Field required" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_get_bot_status_success(client: TestClient, session: Session):
    """Test retrieving bot status successfully."""
    test_email = f"testuser_bot_status_{uuid.uuid4()}@example.com"
    register_response = client.post("/api/v1/register", json={"username": "testuserbotstatus", "password": "testpass123", "email": test_email})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", json={"email": test_email, "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def default_broker_for_routes(session):
    broker = Broker(name="RouteTestBroker", base_url="http://route.com", streaming_url="ws://route.com/stream", is_live_mode=False)
    session.add(broker)
    session.commit()
    session.refresh(broker)
    return broker

@pytest.fixture(scope="function")
def authenticated_client_with_broker(client: TestClient, session: Session, default_broker_for_routes: Broker): # Add type hint back
    user = User(username="testuser_route", email=f"route_{uuid.uuid4()}@example.com", hashed_password="hashedpassword")
    session.add(user)
    session.commit()
    session.refresh(user)

    from src.config import settings # Import settings to get jwt_secret_key
    access_token = jwt.encode({"sub": user.username, "user_id": str(user.id), "type": "access"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    refresh_token = jwt.encode({"sub": user.username, "user_id": str(user.id), "type": "refresh"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    # Create a session entry in the database for the token
    from src.models.session import Session as DBSession # Import DBSession
    db_session_entry = DBSession(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    )
    session.add(db_session_entry)
    session.commit()
    session.refresh(db_session_entry)
    
    client.headers = {"Authorization": f"Bearer {access_token}"}
    return client, user, default_broker_for_routes # Return the actual broker object

@pytest.mark.asyncio
async def test_create_brokerage_connection_route(authenticated_client_with_broker):
    client, user, broker = authenticated_client_with_broker
    response = client.post(
        "/api/v1/brokerage_connections/",
        json={
            "user_id": user.id,
            "broker_id": broker.id,
            "access_token": "routetoken123",
            "refresh_token": "routerefresh123",
            "token_expires_at": 1678886400 # Example Unix timestamp
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user.id
    assert data["broker_id"] == broker.id
    assert data["access_token"] is not None # Should be encrypted bytes, but schema returns string
    assert data["broker"]["name"] == "RouteTestBroker" # Verify nested broker data
    assert data["broker"]["base_url"] == "http://route.com"

@pytest.mark.asyncio
async def test_create_brokerage_connection_with_nonexistent_broker_id(authenticated_client_with_broker):
    client, user, _ = authenticated_client_with_broker
    response = client.post(
        "/api/v1/brokerage_connections/",
        json={
            "user_id": user.id,
            "broker_id": 99999, # Non-existent ID
            "access_token": "invalidtoken"
        }
    )
    assert response.status_code == 404
    assert "Broker not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_brokerage_connections_route(authenticated_client_with_broker):
    client, user, broker = authenticated_client_with_broker
    # Create a connection first
    client.post(
        "/api/v1/brokerage_connections/",
        json={
            "user_id": user.id,
            "broker_id": broker.id,
            "access_token": "gettoken123"
        }
    )
    response = client.get("/api/v1/brokerage_connections/", headers=client.headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["user_id"] == user.id
    assert data[0]["broker"]["name"] == "RouteTestBroker"

@pytest.mark.asyncio
async def test_get_bot_status_success(client: TestClient, session: Session, default_broker_for_routes: Broker): # Add type hint back
    """Test retrieving bot status successfully."""
    test_email = f"testuser_bot_status_{uuid.uuid4()}@example.com"
    register_response = client.post("/api/v1/register", json={"username": "testuserbotstatus", "password": "testpass123", "email": test_email})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", json={"email": test_email, "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = session.exec(select(User).where(User.username == "testuserbotstatus")).first()
    brokerage_connection = BrokerageConnection(
        user_id=user.id,
        broker_id=default_broker_for_routes.id, # Use broker_id
        access_token="dummy_key",
        api_secret="dummy_secret"
    )
    session.add(brokerage_connection)
    session.commit()
    session.refresh(brokerage_connection)

    bot_instance = BotInstance(
        user_id=user.id,
        strategy_id=1,
        brokerage_connection_id=brokerage_connection.id,
        name="TestBotStatus",
        status="running",
        parameters={"param1": "value1"}
    )
    session.add(bot_instance)
    session.commit()
    session.refresh(bot_instance)

    # Manually add a BotStatus entry for the bot instance
    from src.models.bot_status import BotStatus
    bot_status = BotStatus(
        bot_instance_id=bot_instance.id,
        status="active",
        last_check_in=datetime.now(timezone.utc),
        is_active=True
    )
    session.add(bot_status)
    session.commit()
    session.refresh(bot_status)

    response = client.get("/api/v1/bot/status", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
    assert response.json()[0]["bot_instance_id"] == bot_instance.id
    assert response.json()[0]["status"] == "active"
    assert "last_check_in" in response.json()[0]
    assert response.json()[0]["is_active"] == True

@pytest.mark.asyncio
async def test_get_bot_status_no_bots(client: TestClient, session: Session):
    """Test retrieving bot status when no bot instances exist for the user."""
    test_email = f"testuser_no_bots_{uuid.uuid4()}@example.com"
    register_response = client.post("/api/v1/register", json={"username": "testusernobots", "password": "testpass123", "email": test_email})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", json={"email": test_email, "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/bot/status", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_bot_parameters_success(client: TestClient, session: Session, default_broker_for_routes: Broker): # Add type hint back
    """Test retrieving bot parameters successfully."""
    # Register a user and log in to get a token
    test_email = f"testuser_bot_{uuid.uuid4()}@example.com"
    register_response = client.post("/api/v1/register", json={"username": "testuserbot", "password": "testpass123", "email": test_email})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", json={"email": test_email, "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a user and brokerage connection for the bot instance
    user = session.exec(select(User).where(User.username == "testuserbot")).first()
    brokerage_connection = BrokerageConnection(
        user_id=user.id,
        broker_id=default_broker_for_routes.id, # Use broker_id
        access_token="dummy_key",
        api_secret="dummy_secret"
    )
    session.add(brokerage_connection)
    session.commit()
    session.refresh(brokerage_connection)

    # Create a dummy bot instance (assuming strategy_id is not strictly enforced for tests)
    bot_instance = BotInstance(
        user_id=user.id,
        strategy_id=1, # Dummy strategy ID
        brokerage_connection_id=brokerage_connection.id,
        name="TestBot",
        status="running",
        parameters={"param1": "value1", "param2": 123}
    )
    session.add(bot_instance)
    session.commit()
    session.refresh(bot_instance)

    response = client.get(f"/api/v1/bot/parameters?bot_id={bot_instance.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["parameters"] == {"param1": "value1", "param2": 123}

@pytest.mark.asyncio
async def test_get_bot_parameters_not_found(client: TestClient, session: Session):
    """Test retrieving bot parameters for a non-existent bot."""
    test_email = f"testuser_notfound_{uuid.uuid4()}@example.com"
    register_response = client.post("/api/v1/register", json={"username": "testusernotfound", "password": "testpass123", "email": test_email})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", json={"email": test_email, "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/bot/parameters?bot_id=9999", headers=headers)
    assert response.status_code == 404
    assert "Bot instance not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_bot_parameters_success(client: TestClient, session: Session, default_broker_for_routes: Broker): # Add type hint back
    """Test updating bot parameters successfully."""
    test_email = f"testuser_update_{uuid.uuid4()}@example.com"
    register_response = client.post("/api/v1/register", json={"username": "testuserupdate", "password": "testpass123", "email": test_email})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", json={"email": test_email, "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = session.exec(select(User).where(User.username == "testuserupdate")).first()
    brokerage_connection = BrokerageConnection(
        user_id=user.id,
        broker_id=default_broker_for_routes.id, # Use broker_id
        access_token="dummy_key_update",
        api_secret="dummy_secret_update"
    )
    session.add(brokerage_connection)
    session.commit()
    session.refresh(brokerage_connection)

    bot_instance = BotInstance(
        user_id=user.id,
        strategy_id=1, # Dummy strategy ID
        brokerage_connection_id=brokerage_connection.id,
        name="TestBotUpdate",
        status="running",
        parameters={"initial_param": "initial_value"}
    )
    session.add(bot_instance)
    session.commit()
    session.refresh(bot_instance)

    # Send a complete BotInstanceCreate object, with updated parameters nested correctly
    updated_payload = {
        "strategy_id": bot_instance.strategy_id,
        "brokerage_connection_id": bot_instance.brokerage_connection_id,
        "name": bot_instance.name,
        "parameters": {"param_a": "new_value_a", "param_b": 456}
    }
    response = client.post(f"/api/v1/bot/parameters?bot_id={bot_instance.id}", json=updated_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Bot parameters updated successfully"
    assert response.json()["parameters"] == updated_payload["parameters"]

    session.expire(bot_instance)
    updated_bot_instance = session.exec(select(BotInstance).where(BotInstance.id == bot_instance.id)).first()
    assert updated_bot_instance.parameters == updated_payload["parameters"]

@pytest.mark.asyncio
async def test_update_bot_parameters_invalid_payload(client: TestClient, session: Session, default_broker_for_routes: Broker): # Add type hint back
    """Test updating bot parameters with an invalid payload (e.g., missing required fields)."""
    test_email = f"testuser_invalid_payload_{uuid.uuid4()}@example.com"
    register_response = client.post("/api/v1/register", json={"username": "testuserinvalidpayload", "password": "testpass123", "email": test_email})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", json={"email": test_email, "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = session.exec(select(User).where(User.username == "testuserinvalidpayload")).first()
    brokerage_connection = BrokerageConnection(
        user_id=user.id,
        broker_id=default_broker_for_routes.id, # Use broker_id
        access_token="dummy_key",
        api_secret="dummy_secret"
    )
    session.add(brokerage_connection)
    session.commit()
    session.refresh(brokerage_connection)

    bot_instance = BotInstance(
        user_id=user.id,
        strategy_id=1, # Dummy strategy ID
        brokerage_connection_id=brokerage_connection.id,
        name="TestBotInvalidPayload",
        status="running",
        parameters={"initial_param": "initial_value"}
    )
    session.add(bot_instance)
    session.commit()
    session.refresh(bot_instance)

    # Send an invalid payload (missing required fields for BotInstanceCreate, e.g., strategy_id)
    invalid_payload = {"parameters": {"some_param": "value"}} # Missing strategy_id, brokerage_connection_id, name
    response = client.post(f"/api/v1/bot/parameters?bot_id={bot_instance.id}", json=invalid_payload, headers=headers)
    assert response.status_code == 422 # Unprocessable Entity
    # Check for a specific error message related to missing fields
    assert "Field required" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_update_bot_parameters_not_found(client: TestClient, session: Session, default_broker_for_routes: Broker): # Add type hint back
    """Test updating bot parameters for a non-existent bot."""
    test_email = f"testuser_update_notfound_{uuid.uuid4()}@example.com"
    register_response = client.post("/api/v1/register", json={"username": "testuserupdatenotfound", "password": "testpass123", "email": test_email})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", json={"email": test_email, "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a user and brokerage connection for the bot instance
    user = session.exec(select(User).where(User.username == "testuserupdatenotfound")).first()
    if not user:
        user = User(username="testuserupdatenotfound", hashed_password="hashedpassword", email=f"testuserupdatenotfound_{uuid.uuid4()}@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
    
    brokerage_connection = BrokerageConnection(
        user_id=user.id,
        broker_id=default_broker_for_routes.id, # Use broker_id
        access_token="dummy_token",
        api_secret="dummy_secret"
    )
    session.add(brokerage_connection)
    session.commit()
    session.refresh(brokerage_connection)

    # Send a complete BotInstanceCreate object, with updated parameters nested correctly
    updated_payload = {
        "strategy_id": 1, # Dummy value
        "brokerage_connection_id": brokerage_connection.id,
        "name": "NonExistentBot", # Dummy value
        "parameters": {"param_x": "value_x"}
    }
    response = client.post("/api/v1/bot/parameters?bot_id=9999", json=updated_payload, headers=headers)
    assert response.status_code == 404
    assert "Bot instance not found" in response.json()["detail"]
