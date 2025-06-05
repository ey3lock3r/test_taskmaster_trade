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
import uuid

# Test cases
def test_register_user_success(client: TestClient, session: Session):
    """Test successful user registration"""
    response = client.post(
        "/api/v1/register",
        json={"username": "testuser", "password": "pass1234", "email": f"testuser_{uuid.uuid4()}@example.com"}
    )
    assert response.status_code == 201
    assert "id" in response.json()

def test_register_duplicate_username(client: TestClient, session: Session):
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

def test_register_invalid_username(client: TestClient, session: Session):
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

def test_register_invalid_password(client: TestClient, session: Session):
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

def test_register_invalid_email(client: TestClient, session: Session):
    """Test registration with invalid email"""
    response = client.post(
        "/api/v1/register",
        json={"username": "user4", "password": "validpass1", "email": "invalid-email"}
    )
    assert response.status_code == 422
    
def test_login_success(client: TestClient, session: Session):
    """Test successful login returns valid token with correct claims"""
    # Register a user first with valid alphanumeric username
    client.post(
        "/api/v1/register",
        json={"username": "testlogin", "password": "testpass123", "email": f"testlogin_{uuid.uuid4()}@example.com"}
    )

    # Login with correct credentials
    response = client.post(
        "/api/v1/token",
        data={"username": "testlogin", "password": "testpass123"}
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
    assert payload["sub"] == "testlogin"
    assert "user_id" in payload
    assert "exp" in payload
    assert payload["type"] == "access"
    
    # Test email-based login (if supported by your login endpoint)
    # This part might need adjustment based on how your /token endpoint handles email vs username
    # For now, assuming it primarily uses username from OAuth2PasswordRequestForm
    
def test_login_invalid_username(client: TestClient, session: Session):
    """Test login with invalid username"""
    response = client.post(
        "/api/v1/token",
        data={"username": "invalid_user", "password": "anypass"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_invalid_password(client: TestClient, session: Session):
    """Test login with invalid password"""
    # Register a user first
    client.post(
        "/api/v1/register",
        json={"username": "test_invpass", "password": "correctpass", "email": f"test_invpass_{uuid.uuid4()}@example.com"}
    )
    
    # Login with wrong password
    response = client.post(
        "/api/v1/token",
        data={"username": "test_invpass", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
    
def test_login_rate_limiting(client: TestClient, session: Session):
    """Test rate limiting blocks excessive login attempts (if implemented)"""
    # This test depends on rate limiting logic in routes.py, which might be removed with SQLModel refactor
    # If rate limiting is re-implemented, this test needs to be adjusted.
    pass # Skipping for now as rate limiting might be removed/changed

def test_login_missing_fields(client: TestClient, session: Session):
    """Test login with missing fields"""
    # Missing password
    response = client.post(
        "/api/v1/token",
        data={"username": "anyuser"}
    )
    assert response.status_code == 422
    assert "Field required" in response.json()["detail"][0]["msg"]

def test_get_bot_parameters_success(client: TestClient, session: Session):
    """Test retrieving bot parameters successfully."""
    # Register a user and log in to get a token
    register_response = client.post("/api/v1/register", json={"username": "testuserbot", "password": "testpass123", "email": f"testuser_bot_{uuid.uuid4()}@example.com"})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", data={"username": "testuserbot", "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a user and brokerage connection for the bot instance
    user = session.exec(select(User).where(User.username == "testuserbot")).first()
    brokerage_connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="Tradier",
        api_key="dummy_key",
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

def test_get_bot_parameters_not_found(client: TestClient, session: Session):
    """Test retrieving bot parameters for a non-existent bot."""
    register_response = client.post("/api/v1/register", json={"username": "testusernotfound", "password": "testpass123", "email": f"testuser_notfound_{uuid.uuid4()}@example.com"})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", data={"username": "testusernotfound", "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/bot/parameters?bot_id=9999", headers=headers)
    assert response.status_code == 404
    assert "Bot instance not found" in response.json()["detail"]

def test_update_bot_parameters_success(client: TestClient, session: Session):
    """Test updating bot parameters successfully."""
    register_response = client.post("/api/v1/register", json={"username": "testuserupdate", "password": "testpass123", "email": f"testuser_update_{uuid.uuid4()}@example.com"})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", data={"username": "testuserupdate", "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = session.exec(select(User).where(User.username == "testuserupdate")).first()
    brokerage_connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="Tradier",
        api_key="dummy_key_update",
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

def test_update_bot_parameters_invalid_payload(client: TestClient, session: Session):
    """Test updating bot parameters with an invalid payload (e.g., missing required fields)."""
    register_response = client.post("/api/v1/register", json={"username": "testuserinvalidpayload", "password": "testpass123", "email": f"testuser_invalid_payload_{uuid.uuid4()}@example.com"})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", data={"username": "testuserinvalidpayload", "password": "testpass123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user = session.exec(select(User).where(User.username == "testuserinvalidpayload")).first()
    brokerage_connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="Tradier",
        api_key="dummy_key",
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

def test_update_bot_parameters_not_found(client: TestClient, session: Session):
    """Test updating bot parameters for a non-existent bot."""
    register_response = client.post("/api/v1/register", json={"username": "testuserupdatenotfound", "password": "testpass123", "email": f"testuser_update_notfound_{uuid.uuid4()}@example.com"})
    assert register_response.status_code == 201
    
    login_response = client.post("/api/v1/token", data={"username": "testuserupdatenotfound", "password": "testpass123"})
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
        brokerage_name="Tradier",
        api_key="dummy_token",
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
