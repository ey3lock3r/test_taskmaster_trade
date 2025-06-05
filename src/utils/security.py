import bcrypt
import jwt
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import uuid
import bcrypt
import jwt
import os
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from sqlmodel import Session, select
from src.config import settings
from src.models.user import User
from src.utils.encryption import EncryptionUtil
from src.database import get_session # Add this import

load_dotenv()

# JWT configuration
JWT_SECRET_KEY = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expiration_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.jwt_refresh_expiration_days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

# Initialize EncryptionUtil
encryption_util = EncryptionUtil(key=settings.encryption_key)

def hash_password(password: str) -> str:
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")
    if not hashed or not isinstance(hashed, str):
        raise ValueError("Hashed password must be a non-empty string")
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token() -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if "type" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    print("get_current_user: Started.")
    from src.models.session import Session as DBSession # Import DBSession here
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        print(f"get_current_user: Token payload: {payload}")
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        token_type: str = payload.get("type") # Get token type
        if username is None or user_id is None or token_type != "access": # Validate token type
            print("get_current_user: Invalid username, user_id, or token_type in payload.")
            raise credentials_exception
        print(f"get_current_user: Payload validated. User ID: {user_id}, Username: {username}")
    except HTTPException as e:
        print(f"get_current_user: HTTPException during token verification: {e.detail}")
        raise credentials_exception
    except Exception as e:
        print(f"get_current_user: Unexpected error during token verification: {e}")
        raise credentials_exception
    
    # Check if the session exists and is valid
    print(f"get_current_user: Checking session for token: {token[:10]}...")
    db_session = session.exec(
        select(DBSession).where(
            DBSession.access_token == token,
            DBSession.is_active == True, # Ensure session is active
            DBSession.expires_at >= datetime.now(timezone.utc),
            DBSession.logged_out_at == None # Ensure session is not logged out
        )
    ).first()
    print(f"get_current_user: db_session found: {db_session is not None}")
    if db_session:
        print(f"get_current_user: db_session is_active: {db_session.is_active}, logged_out_at: {db_session.logged_out_at}, expires_at: {db_session.expires_at}")

    if db_session is None:
        print("get_current_user: db_session is None, raising credentials_exception.")
        raise credentials_exception

    print(f"get_current_user: Fetching user with ID: {user_id}")
    user = session.exec(select(User).where(User.id == int(user_id))).first()
    if user is None:
        print("get_current_user: User not found, raising credentials_exception.")
        raise credentials_exception
    
    # Update last_activity for the session
    print("get_current_user: Updating session last_activity.")
    db_session.last_activity = datetime.now(timezone.utc)
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    print("get_current_user: Session last_activity updated. Returning user.")

    return user