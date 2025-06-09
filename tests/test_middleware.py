import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone # Import timezone
import jwt

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# from src.main import app # Will get app from conftest client fixture
from sqlalchemy.orm import Session as SQLAlchemySession # Import for type hinting
from src.models.user import User, pwd_context # Import pwd_context
from src.utils.security import create_access_token # Remove hash_password
# from src.database import get_db # Will use db_session from conftest

# Create test client - remove global client, will use fixture
# client = TestClient(app)

# Create test user
@pytest.fixture(scope="function") # Changed scope to function
def test_user(session: SQLAlchemySession): # Use session fixture
    db = session # Use the injected test session
    username = f"testuser_{datetime.now().timestamp()}"
    password = "testpass123"
    hashed = pwd_context.hash(password) # Use pwd_context for hashing
    print("Creating test user")
    
    # Create test user
    test_email = f"{username}@example.com"
    user_instance = User(
        username=username,
        email=test_email,
        hashed_password=hashed,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user_instance)
    db.commit()
    db.refresh(user_instance) # Ensure all attributes are loaded, including ID
    
    # Yield data needed for tests, including the user ID and email for potential re-fetching
    yield {"username": username, "password": password, "id": user_instance.id, "email": test_email}
    
    # No explicit cleanup here, db_session fixture handles it
    pass

def test_missing_authorization_header(client: TestClient, test_user): # Add client fixture
    """Test access without authorization token"""
    response = client.get("/api/v1/protected")
    assert response.status_code == 401
    assert response.json()['detail'] == "Missing or invalid authorization token"

def test_invalid_token_format(client: TestClient, test_user): # Add client fixture
    """Test invalid token format"""
    response = client.get("/api/v1/protected", headers={"Authorization": "InvalidFormat"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid authorization token"

def test_invalid_token(client: TestClient, test_user): # Add client fixture
    """Test invalid token signature"""
    invalid_token = jwt.encode({"sub": test_user["username"]}, "wrong_secret", algorithm="HS256")
    response = client.get("/api/v1/protected", headers={"Authorization": f"Bearer {invalid_token}"})
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"

def test_expired_token(client: TestClient, test_user): # Add client fixture
    """Test expired token handling"""
    # Create expired token
    expiration = timedelta(minutes=-1)
    expired_token = create_access_token(data={"sub": test_user["username"]}, expires_delta=expiration)
    
    response = client.get("/api/v1/protected", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"

def test_valid_authentication(client: TestClient, test_user): # Add client fixture
    """Test successful authentication flow"""
    # Register user (already done by test_user fixture)
    # Perform login to create a session and get a valid token
    login_response = client.post(
        "/api/v1/token",
        json={"email": test_user["email"], "password": test_user["password"]}
    )
    assert login_response.status_code == 200
    valid_token = login_response.json()["access_token"]
    
    response = client.get("/api/v1/protected", headers={"Authorization": f"Bearer {valid_token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Protected content"  # Correct response from route

def test_exempt_routes(client: TestClient): # Add client fixture
    """Test that exempt routes don't require authentication"""
    # Send POST with password but no username/email to trigger the model validator
    response = client.post("/api/v1/token", json={"password": "testpass123"})
    assert response.status_code == 422  # Now bypasses middleware but fails at route validation
    assert "Either username or email must be provided" in response.json()["detail"][0]["msg"]