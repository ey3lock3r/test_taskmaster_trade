# Configure test database before importing application code
import pytest
import uuid
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import time
from sqlalchemy.orm import Session as SQLAlchemySession, sessionmaker
from sqlmodel import Session, select, delete

from src.models.user import User, pwd_context # Import pwd_context
from src.models.session import Session as SessionModel # Alias the model to avoid conflict with sqlmodel.Session
from src.utils.security import create_access_token, create_refresh_token
from src.utils.redis_utils import add_jti_to_blacklist # Import add_jti_to_blacklist


# Setup logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
        
@pytest.fixture(scope="function") # Changed scope to function
def test_user(session: Session):
    db = session
    username = f"testuser_session_{uuid.uuid4()}" # Use UUID for robust uniqueness
    password = "testpassword"
    hashed = pwd_context.hash(password) # Use pwd_context for hashing
    
    # Create test user
    user = User(username=username, email=f"{username}@example.com", hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create an initial session for the user to avoid foreign key constraint issues
    try:
        # Generate a refresh token
        refresh_token = create_refresh_token(data={"sub": user.username, "user_id": str(user.id)})
        new_session_record = SessionModel(
            user_id=user.id,
            access_token="initial_token",
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            last_activity=datetime.now(timezone.utc),
            is_active=True
        )
        db.add(new_session_record)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to create initial session: {str(e)}")
        raise
    
    yield {"username": username, "password": password, "user": user}
    
    # Explicitly delete the user and any associated sessions created by this fixture
    # This is crucial because session is module-scoped, and rollback won't clear committed data
    try:
        # Delete sessions associated with the user first to avoid foreign key constraints
        db.exec(delete(SessionModel).where(SessionModel.user_id == user.id))
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error during test_user cleanup: {e}")

@pytest.fixture(scope="function")
def valid_token(test_user, client): # Renamed client_fixture to client
    # Create a valid session by logging in
    response = client.post( # Changed client_fixture to client
        "/api/v1/token",
        json={"email": test_user["user"].email, "password": test_user["password"]}
    )
    assert response.status_code == 200
    return response.json().get("access_token")

def test_session_creation_on_login(test_user, valid_token, session, client): # Renamed client_fixture to client
    # Verify session is created on successful login
    response = client.post( # Changed client_fixture to client
        "/api/v1/token",
        json={"email": test_user["user"].email, "password": test_user["password"]}
    )
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert token is not None
    
    # Verify session exists in database for this token
    db = session
    session = db.exec(select(SessionModel).where(SessionModel.access_token == token)).first()
    assert session is not None
    assert session.is_active is True

def test_session_timeout(test_user, session, client): # Renamed client_fixture to client
    # Test session expiration after inactivity
    # Create a session with a short expiration in the future
    db = session
    # Generate real JWT tokens with short expiration
    access_token = create_access_token(
        data={"sub": test_user["username"], "user_id": str(test_user["user"].id)},
        expires_delta=timedelta(seconds=5)
    )
    refresh_token = create_refresh_token(data={"sub": test_user["username"], "user_id": str(test_user["user"].id)})

    # Create session in database
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=5)
    new_session_record = SessionModel(
        user_id=test_user["user"].id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        last_activity=datetime.now(timezone.utc),
        is_active=True
    )
    db.add(new_session_record)
    db.commit()
    db.refresh(new_session_record)

    # Verify session exists
    assert new_session_record is not None

    # Use the token immediately - should work
    response = client.get( # Changed client_fixture to client
        "/api/v1/users/me/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200 # First request should succeed
    
    # Wait for token to expire
    time.sleep(6) # Increased sleep to ensure token expiration
    
    # Explicitly expire the session in the database to ensure it's seen as expired
    new_session_record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(new_session_record) # Add the modified object back to the session
    db.commit()
    db.refresh(new_session_record) # Refresh the session object to get latest state
    
    # Try to use expired token
    response = client.get( # Changed client_fixture to client
        "/api/v1/users/me/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert "expired" in response.json().get("detail", "")

def test_access_profile_with_valid_token(valid_token, client):
    """Test accessing /api/v1/users/me/ with a valid token."""
    response = client.get(
        "/api/v1/users/me/",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] is not None

def test_token_renewal(test_user, session, client): # Renamed client_fixture to client
    # Verify token renewal process
    # First login to get refresh token
    # Get refresh token from login
    login_response = client.post( # Changed client_fixture to client
        "/api/v1/token",
        json={"email": test_user["user"].email, "password": test_user["password"]}
    )
    refresh_token = login_response.json().get("refresh_token")
    print(f"DEBUG: Test received refresh token: {refresh_token}")

    # Ensure session exists for refresh token
    db = session
    session_record = db.exec(select(SessionModel).where(SessionModel.refresh_token == refresh_token)).first()
    if not session_record:
        pytest.fail("Session not found for refresh token")
    print(f"DEBUG: Test found session record for refresh token: {session_record.session_id}")
    
    # Request token renewal
    response = client.post( # Changed client_fixture to client
        "/api/v1/refresh", # Corrected endpoint path
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert response.status_code == 200
    new_token = response.json().get("access_token")
    assert new_token is not None
    
    # Verify new token works
    response = client.get( # Changed client_fixture to client
        "/api/v1/users/me/",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    assert response.status_code == 200

def test_logout_terminates_session(test_user, valid_token, session, client):
    # First verify session is active
    db = session
    session_record = db.exec(select(SessionModel).where(
        SessionModel.user_id == test_user["user"].id,
        SessionModel.access_token == valid_token,
        SessionModel.is_active == True
    )).first()
    if not session_record:
        pytest.fail("Active session not found")
    assert session_record.is_active is True
    
    # Logout
    response = client.post(
        "/api/v1/logout",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    
    # Verify session is terminated
    db.refresh(session_record) # Refresh the session object to get latest state
    assert session_record.is_active is False
    assert session_record.logged_out_at is not None
    
    # Verify token no longer works
    response = client.get(
        "/api/v1/users/me/",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 401

def test_logging_on_successful_login(test_user, client, caplog):
    """Test that appropriate log messages are generated on successful user login."""
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/token",
            json={"email": test_user["user"].email, "password": test_user["password"]}
        )
        assert response.status_code == 200
        
        # Check for specific log messages
        assert any(f"Attempting login for email: {test_user['user'].email}" in record.message for record in caplog.records)
        assert any(f"User '{test_user['user'].username}' logged in successfully. Session created." in record.message for record in caplog.records)

def test_view_active_sessions(test_user, valid_token, session, client): # Renamed client_fixture to client
    # Verify session viewing functionality
    # Create multiple sessions
    # Create sessions by logging in multiple times
    login1 = client.post( # Changed client_fixture to client
        "/api/v1/token",
        json={"email": test_user["user"].email, "password": test_user["password"]}
    )
    token1 = login1.json().get("access_token")
    
    login2 = client.post( # Changed client_fixture to client
        "/api/v1/token",
        json={"email": test_user["user"].email, "password": test_user["password"]}
    )
    token2 = login2.json().get("access_token")
    
    # Get active sessions
    response = client.get( # Changed client_fixture to client
        "/api/v1/user/sessions",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    # Verify we got at least 2 sessions
    sessions = response.json()
    assert len(sessions) >= 2
    # Should have at least 3 sessions (including the valid_token session)
    assert len(sessions) >= 3
    
    # Get session IDs from the database for the generated tokens
    db = session
    session_valid_token = db.exec(select(SessionModel).where(SessionModel.access_token == valid_token)).first()
    session_token1 = db.exec(select(SessionModel).where(SessionModel.access_token == token1)).first()
    session_token2 = db.exec(select(SessionModel).where(SessionModel.access_token == token2)).first()
    
    # Extract session IDs
    session_ids_from_db = []
    if session_valid_token:
        session_ids_from_db.append(session_valid_token.session_id)
    if session_token1:
        session_ids_from_db.append(session_token1.session_id)
    if session_token2:
        session_ids_from_db.append(session_token2.session_id)
        
    # Extract IDs from the API response
    session_ids_from_api = [s["id"] for s in sessions]
    
    # Verify that the session IDs from the database are present in the API response
    for session_id in session_ids_from_db:
        assert session_id in session_ids_from_api

def test_terminate_session(test_user, valid_token, session, client): # Renamed client_fixture to client
    # Test session termination capability
    # Create another session to terminate
    # Create session by logging in
    login_response = client.post( # Changed client_fixture to client
        "/api/v1/token",
        json={"email": test_user["user"].email, "password": test_user["password"]}
    )
    other_token = login_response.json().get("access_token")
    refresh_token = login_response.json().get("refresh_token")
    
    # Get session for the new token using access token
    db = session
    session_to_terminate = db.exec(select(SessionModel).where(
        SessionModel.access_token == other_token,
        SessionModel.is_active == True
    )).first()
    if not session_to_terminate:
        pytest.fail("Session not found for new token")
    
    # Get session ID to terminate using refresh token
    # Get session by access token again for termination
    db = session
    session_to_terminate = db.exec(select(SessionModel).where(
        SessionModel.access_token == other_token,
        SessionModel.is_active == True
    )).first()
    if not session_to_terminate:
        pytest.fail("Session not found for termination")
    
    # Terminate the session
    response = client.delete(
        f"/api/v1/user/sessions/{session_to_terminate.session_id}", # Corrected to session_id
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    
    # Verify session is terminated
    db.refresh(session_to_terminate) # Refresh the session object to get latest state
    assert session_to_terminate.is_active is False

    # Explicitly commit to ensure changes are visible
    session.commit()
    
    # Expire all objects in the session to force a reload from the database
    session.expire_all()

    # Import create_app to create a new client instance with the test database
    from src.main import create_app
    new_client = TestClient(create_app(db_engine=session.bind))
    
    # Verify token no longer works with the new client instance
    response = new_client.get(
        "/api/v1/users/me/",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    # Expecting 401 Unauthorized as the session should be terminated
    assert response.status_code == 401