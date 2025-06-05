from src.utils.security import verify_token
from fastapi import Request, HTTPException, status
from fastapi.middleware import Middleware
from typing import Callable, List, Optional, Any # Import Any
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from src.models.session import Session as SessionModel # Alias the model
from src.models.user import User
from src.database import get_session # Use get_session from SQLModel
import logging

logger = logging.getLogger(__name__)

SESSION_TIMEOUT_MINUTES = 30

class AuthMiddleware:
    def __init__(
        self,
        app: Callable,
        exclude_paths: Optional[List[str]] = None,
        db_engine: Any = None # Add db_engine parameter
    ):
        self.app = app
        self.exclude_paths = exclude_paths if exclude_paths is not None else []
        self.exempt_routes = ["/api/v1/token", "/api/v1/register", "/api/v1/login", "/api/v1/health", "/api/v1/refresh"] + self.exclude_paths
        self.db_engine = db_engine # Store the engine
        
    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        print(f"AuthMiddleware: Incoming request to path: {request.url.path}")
        
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            print(f"AuthMiddleware: Token found: {token[:10]}...") # Print first 10 chars of token

        if request.url.path not in self.exempt_routes:
            print(f"AuthMiddleware: Path {request.url.path} is NOT exempt.")
            if not token:
                print("AuthMiddleware: No token found for non-exempt path, returning 401.")
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Missing or invalid authorization token"}
                )
                await response(scope, receive, send)
                return
            
            session: Session = Session(self.db_engine) # Use the injected db_engine
            print("AuthMiddleware: Database session created.")
            
            try:
                logger.debug(f"AuthMiddleware: Processing request for path: {request.url.path}, token: {token}")
                payload = verify_token(token)
                logger.debug(f"AuthMiddleware: Token verified, payload type: {payload.get('type')}")
                print(f"AuthMiddleware: Token payload: {payload}")
                
                is_refresh_endpoint = request.url.path == "/api/v1/refresh"

                if is_refresh_endpoint and payload.get("type") != "refresh":
                    logger.debug("AuthMiddleware: Invalid refresh token type, raising 401.")
                    print("AuthMiddleware: Invalid refresh token type, returning 401.")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token type")
                elif not is_refresh_endpoint and payload.get("type") != "access":
                    logger.debug("AuthMiddleware: Invalid access token type, raising 401.")
                    print("AuthMiddleware: Invalid access token type, returning 401.")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token type")

                if is_refresh_endpoint:
                    session_record = session.exec(select(SessionModel).where(SessionModel.refresh_token == token, SessionModel.is_active == True)).first()
                else:
                    session_record = session.exec(select(SessionModel).where(SessionModel.access_token == token, SessionModel.is_active == True)).first()
                
                if not session_record:
                    logger.debug("AuthMiddleware: Session not found, raising 401.")
                    print("AuthMiddleware: Session record NOT found in DB, returning 401.")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

                session.refresh(session_record)
                print(f"AuthMiddleware: Session record found. ID: {session_record.session_id}, Is Active: {session_record.is_active}, Expires At: {session_record.expires_at}")
                
                if not session_record.is_active:
                    logger.debug("AuthMiddleware: Session found but is inactive after refresh, raising 401.")
                    print("AuthMiddleware: Session is inactive, returning 401.")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is inactive")

                logger.debug(f"AuthMiddleware: Session found. ID: {session_record.session_id}, Is Active: {session_record.is_active}, Expires At: {session_record.expires_at}")
                    
                if session_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                    logger.debug("AuthMiddleware: Session expired, setting inactive and raising 401.")
                    print("AuthMiddleware: Session expired, setting inactive and returning 401.")
                    session_record.is_active = False
                    session.add(session_record)
                    session.commit()
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
                    
                if datetime.now(timezone.utc) - session_record.last_activity.replace(tzinfo=timezone.utc) > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                    logger.debug("AuthMiddleware: Session timeout due to inactivity, setting inactive and raising 401.")
                    print("AuthMiddleware: Session timeout due to inactivity, setting inactive and returning 401.")
                    session_record.is_active = False
                    session.add(session_record)
                    session.commit()
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session timeout due to inactivity")
                    
                session_record.last_activity = datetime.now(timezone.utc)
                session.add(session_record)
                session.commit()
                logger.debug("AuthMiddleware: Session last activity updated.")
                print("AuthMiddleware: Session last activity updated.")
                
                user = session.exec(select(User).where(User.id == session_record.user_id)).first()
                if not user:
                    logger.debug("AuthMiddleware: User not found for session, raising 401.")
                    print("AuthMiddleware: User not found for session, returning 401.")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
                    
                request.state.user = user
                logger.debug(f"AuthMiddleware: User {user.username} authenticated.")
                print(f"AuthMiddleware: User {user.username} authenticated. Passing request to app.")
                
            except HTTPException as e:
                logger.debug(f"AuthMiddleware: Caught HTTPException: {e.detail} with status {e.status_code}.")
                print(f"AuthMiddleware: Caught HTTPException: {e.detail} with status {e.status_code}. Returning JSONResponse.")
                response = JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
                await response(scope, receive, send)
                return
            except Exception as e:
                logging.exception(f"Unhandled exception in AuthMiddleware: {e}")
                print(f"AuthMiddleware: Unhandled exception: {e}. Returning 500.")
                response = JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": f"Authentication error: {str(e)}"}
                )
                await response(scope, receive, send)
                return
            finally:
                session.close() # Ensure session is closed
                print("AuthMiddleware: Database session closed.")
        else:
            print(f"AuthMiddleware: Path {request.url.path} is EXEMPT. Passing request to app.")
        
        await self.app(scope, receive, send)
