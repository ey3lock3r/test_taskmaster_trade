import sys
import os
from datetime import datetime, timedelta, timezone
import sys
import os
from datetime import datetime, timedelta, timezone
import json
import subprocess # Import subprocess

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, create_engine, select
from src.models.user import User
from src.models.session import Session as DBSession
from src.config import settings
from src.utils.security import hash_password, create_access_token, create_refresh_token

# Ensure the database URL is set for testing
settings.database_url = "sqlite:///./algotrader.db" # Or use .env.test if configured
engine = create_engine(settings.database_url, echo=False)

def setup_test_user(username_prefix: str = "testuser", email_prefix: str = "test", password: str = "password123"):
    """
    Sets up a test user and an active session in the database.
    Returns the user ID and access token.
    """
    # Reset the database before setting up the user
    reset_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'reset_db.py'))
    try:
        subprocess.run([sys.executable, reset_script_path], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error resetting database: {e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)

    random_suffix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f"{username_prefix}_{random_suffix}"
    email = f"{email_prefix}_{random_suffix}@example.com"

    with Session(engine) as session:
        # Create user
        hashed_pw = hash_password(password)
        user = User(username=username, email=email, hashed_password=hashed_pw)
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create session
        access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": str(user.id)}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token()

        db_session = DBSession(
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + access_token_expires
        )
        session.add(db_session)
        session.commit()
        session.refresh(db_session)
        
        return {"user_id": user.id, "access_token": access_token}

if __name__ == "__main__":
    try:
        result = setup_test_user()
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)