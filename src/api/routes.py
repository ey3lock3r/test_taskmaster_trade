from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from src.config import settings
from src.utils.security import create_access_token, create_refresh_token, verify_token
from src.utils.logger import logger
from src.utils.redis_utils import add_jti_to_blacklist # Import add_jti_to_blacklist
from fastapi_limiter.depends import RateLimiter # Added for rate limiting
from src.constants import ( # Import constants
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND,
    USERNAME_ALREADY_REGISTERED, EMAIL_ALREADY_REGISTERED, INCORRECT_CREDENTIALS,
    BEARER_TOKEN_REQUIRED, INVALID_OR_INACTIVE_REFRESH_TOKEN, INVALID_TOKEN_TYPE,
    INVALID_TOKEN_PAYLOAD, USER_NOT_FOUND, COULD_NOT_VALIDATE_REFRESH_TOKEN,
    ACTIVE_SESSION_NOT_FOUND, SESSION_NOT_FOUND_OR_UNAUTHORIZED, BOT_INSTANCE_NOT_FOUND
)

from src.database import get_session
from src.models.user import User
from src.models.session import Session as DBSession
from src.models.brokerage_connection import BrokerageConnection
from src.models.bot_instance import BotInstance
from src.models.bot_status import BotStatus
from src.models.trade_order import TradeOrder
from src.models.position import Position
from src.models.broker import Broker # Import Broker model
from src.services.bot_service import BotService
from src.services.broker_service import BrokerService # New import
from src.utils.security import get_current_user
from src.schemas import UserCreate, UserResponse, Token, LoginRequest, BrokerageConnectionCreate, BrokerageConnectionResponse, BotInstanceCreate, BotInstanceResponse, BotStatusResponse, TradeOrderResponse, PositionResponse
from fastapi.security import OAuth2PasswordBearer # Removed unused OAuth2PasswordRequestForm, HTTPBearer

router = APIRouter()

def get_bearer_token(request: Request) -> str:
    """
    Extracts the bearer token from the Authorization header.

    Args:
        request (Request): The incoming FastAPI request.

    Returns:
        str: The extracted bearer token.

    Raises:
        HTTPException: If the Authorization header is missing or malformed.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Bearer token missing or malformed in Authorization header.")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=BEARER_TOKEN_REQUIRED)
    return auth_header.split(" ")[1]

@router.post("/register", response_model=UserResponse, status_code=HTTP_201_CREATED, dependencies=[Depends(RateLimiter(times=9, seconds=60))])
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    """
    Registers a new user.

    Args:
        user (UserCreate): The user registration data.
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        UserResponse: The created user's response model.

    Raises:
        HTTPException: If username or email is already registered.
    """
    logger.info(f"Attempting to register new user: {user.username}")
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if db_user:
        logger.warning(f"Registration failed: Username '{user.username}' already registered.")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=USERNAME_ALREADY_REGISTERED)
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if db_user:
        logger.warning(f"Registration failed: Email '{user.email}' already registered.")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=EMAIL_ALREADY_REGISTERED)
    
    new_user = User(username=user.username, email=user.email)
    new_user.set_password(user.password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    logger.info(f"User '{new_user.username}' registered successfully with ID: {new_user.id}")
    return new_user

@router.post("/token", response_model=Token, dependencies=[Depends(RateLimiter(times=9, seconds=60))])
def login_for_access_token(form_data: LoginRequest, session: Session = Depends(get_session)):
    """
    Authenticates a user and returns access and refresh tokens.

    Args:
        form_data (LoginRequest): The user's login credentials.
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        Token: Access and refresh tokens.

    Raises:
        HTTPException: If authentication fails.
    """
    logger.info(f"Attempting login for email: {form_data.email}")
    user = session.exec(select(User).where(User.email == form_data.email)).first()
    if not user or not user.check_password(form_data.password):
        logger.warning(f"Login failed for email '{form_data.email}': Incorrect credentials.")
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=INCORRECT_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)}, expires_delta=access_token_expires
    )
 
    new_refresh_token = create_refresh_token(data={"sub": user.username, "user_id": str(user.id)})
    db_session = DBSession(
        user_id=user.id,
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_at=datetime.now(timezone.utc) + access_token_expires
    )
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    logger.info(f"User '{user.username}' logged in successfully. Session created.")
    
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh_token}

@router.get("/users/me/", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retrieves the current authenticated user's information.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Returns:
        UserResponse: The current user's response model.
    """
    return current_user

@router.post("/logout", status_code=HTTP_200_OK)
def logout(request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Logs out the current user by invalidating their session.

    Args:
        request (Request): The incoming FastAPI request.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException: If no active session is found for the provided token.
    """
    logger.info(f"Attempting logout for user: {current_user.username}")
    # Extract the access token from the Authorization header
    access_token = get_bearer_token(request)

    # Invalidate the current session
    db_session = session.exec(select(DBSession).where(
        DBSession.user_id == current_user.id,
        DBSession.access_token == access_token,
        DBSession.is_active == True
    )).first()

    if db_session:
        db_session.is_active = False
        db_session.logged_out_at = datetime.now(timezone.utc)
        session.add(db_session)
        session.commit()
        session.refresh(db_session)
        logger.info(f"User '{current_user.username}' successfully logged out. Session ID: {db_session.session_id}")
        return {"message": "Successfully logged out"}
    logger.warning(f"Logout failed for user '{current_user.username}': Active session not found for provided token.")
    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=ACTIVE_SESSION_NOT_FOUND)

@router.post("/refresh", response_model=Token, dependencies=[Depends(RateLimiter(times=9, seconds=60))])
async def refresh_access_token(request: Request, session: Session = Depends(get_session)):
    """
    Refreshes an expired access token using a valid refresh token.

    Args:
        request (Request): The incoming FastAPI request containing the refresh token.
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        Token: A new access token and refresh token.

    Raises:
        HTTPException: If the refresh token is invalid, inactive, or expired.
    """
    logger.info("Attempting to refresh access token.")
    refresh_token = get_bearer_token(request)
    # logger.debug("Refresh endpoint received refresh token (masked).") # Removed for security

    db_session = session.exec(select(DBSession).where(
        DBSession.refresh_token == refresh_token,
        DBSession.is_active == True
    )).first()

    if not db_session:
        logger.warning("Refresh token failed: Active session not found for provided refresh token (masked).")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=INVALID_OR_INACTIVE_REFRESH_TOKEN)
    
    # logger.debug(f"Found active session for refresh token (masked). Session ID: {db_session.session_id}") # Removed for security

    # Check if the refresh token itself has expired (optional, but good practice)
    # Assuming refresh tokens also have an expiration managed by the JWT payload or session.expires_at
    # For now, we rely on the session.expires_at which is tied to the access token's life.
    # If refresh tokens had their own distinct, longer expiry, that check would go here.

    # Verify the refresh token payload
    try:
        payload = await verify_token(refresh_token)
        # logger.debug(f"Refresh token payload: {payload}") # Removed for security
        if payload.get("type") != "refresh":
            logger.warning("Refresh token failed: Invalid token type in payload.")
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN_TYPE)
        
        user_id = payload.get("user_id")
        username = payload.get("sub")
        if not user_id or not username:
            logger.warning("Refresh token failed: Missing user_id or sub in token payload.")
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN_PAYLOAD)

        # Ensure the user exists
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            logger.warning(f"Refresh token failed: User with ID {user_id} not found.")
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=USER_NOT_FOUND)

    except HTTPException:
        raise # Re-raise existing HTTPExceptions
    except Exception as e:
        logger.error(f"Refresh token verification failed: {e}", exc_info=True)
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=COULD_NOT_VALIDATE_REFRESH_TOKEN)

    # Generate new access and refresh tokens
    access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
    new_access_token = create_access_token(
        data={"sub": username, "user_id": str(user_id)}, expires_delta=access_token_expires
    )
    # Invalidate the old refresh token by setting the current session to inactive
    # and creating a new session for the new tokens.
    # This prevents replay attacks of the old refresh token.
    db_session.is_active = False
    db_session.logged_out_at = datetime.now(timezone.utc)
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    logger.info(f"Old session {db_session.session_id} invalidated for user: {username}.")

    # Blacklist the old refresh token's JTI
    old_refresh_token_payload = await verify_token(refresh_token)
    old_jti = old_refresh_token_payload.get("jti")
    if old_jti:
        # Use the expiration of the old refresh token for the blacklist TTL
        # If the refresh token itself doesn't have an 'exp', use a reasonable default or the session's expiry
        old_refresh_token_expiry = datetime.fromtimestamp(old_refresh_token_payload["exp"], tz=timezone.utc)
        await add_jti_to_blacklist(old_jti, old_refresh_token_expiry)
    else:
        logger.warning(f"Old refresh token for user {username} did not contain a JTI. Cannot blacklist.")

    # Generate new access and refresh tokens
    new_access_token = create_access_token(
        data={"sub": username, "user_id": str(user_id)}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": username, "user_id": str(user_id)})

    # Create a new session record for the new tokens
    new_db_session = DBSession(
        user_id=user.id,
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_at=datetime.now(timezone.utc) + access_token_expires,
        last_activity=datetime.now(timezone.utc),
        is_active=True
    )
    session.add(new_db_session)
    session.commit()
    session.refresh(new_db_session)
    logger.info(f"Access token refreshed successfully for user: {username}. New session ID: {new_db_session.session_id}")

    return {"access_token": new_access_token, "token_type": "bearer", "refresh_token": new_refresh_token}

@router.get("/user/sessions", response_model=List[dict])
def get_user_sessions(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Retrieves all sessions for the current authenticated user.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        List[dict]: A list of user sessions.
    """
    user_sessions = session.exec(select(DBSession).where(DBSession.user_id == current_user.id)).all()
    
    # Convert to a list of dictionaries, including the session_id
    return [{"id": s.session_id, "is_active": s.is_active, "expires_at": s.expires_at, "last_activity": s.last_activity} for s in user_sessions]

@router.delete("/user/sessions/{session_id}", status_code=HTTP_200_OK)
def terminate_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Terminates a specific user session by setting it to inactive.

    Args:
        session_id (str): The ID of the session to terminate.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException: If the session is not found or not authorized for the current user.
    """
    db_session = session.exec(select(DBSession).where(
        DBSession.session_id == session_id,
        DBSession.user_id == current_user.id
    )).first()

    if not db_session:
        logger.warning(f"Session termination failed for session ID '{session_id}': Not found or unauthorized.")
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=SESSION_NOT_FOUND_OR_UNAUTHORIZED)

    db_session.is_active = False
    db_session.logged_out_at = datetime.now(timezone.utc)
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    logger.info(f"Session {session_id} terminated successfully for user: {current_user.username}")
    
    return {"message": f"Session {session_id} terminated successfully"}

@router.post("/brokerage_connections", response_model=BrokerageConnectionResponse, status_code=HTTP_201_CREATED)
def create_brokerage_connection(
    connection: BrokerageConnectionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Creates a new brokerage connection for the current user.

    Args:
        connection (BrokerageConnectionCreate): The brokerage connection data.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        BrokerageConnectionResponse: The created brokerage connection.

    Raises:
        HTTPException: If the specified broker_id does not exist.
    """
    logger.info(f"Attempting to create brokerage connection for user: {current_user.username}")

    # Verify that the broker_id exists
    broker_service = BrokerService(session)
    broker = broker_service.get_broker_by_id(connection.broker_id) # Use get_broker_by_id
    if not broker:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )

    db_connection = BrokerageConnection(
        user_id=current_user.id,
        broker_id=connection.broker_id,
        api_key=connection.api_key,
        api_secret=connection.api_secret,
        access_token=connection.access_token,
        refresh_token=connection.refresh_token,
        expires_at=datetime.fromtimestamp(connection.token_expires_at, tz=timezone.utc) if connection.token_expires_at else None
    )
    session.add(db_connection)
    session.commit()
    session.refresh(db_connection)
    logger.info(f"Brokerage connection for broker ID '{connection.broker_id}' created for user {current_user.username}.")
    return db_connection

@router.post("/brokerage_connections/test", status_code=status.HTTP_200_OK)
def test_brokerage_connection(
    connection_data: BrokerageConnectionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Tests a brokerage connection without persisting it to the database.
    TODO Implement broker connection test

    Args:
        connection_data (BrokerageConnectionCreate): The brokerage connection data to test.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        dict: A confirmation message if the test is successful.

    Raises:
        HTTPException: If the connection test fails or broker is not found.
    """
    logger.info(f"Attempting to test brokerage connection for user: {current_user.username}")

    broker_service = BrokerService(session)
    broker = broker_service.get_broker_by_id(connection_data.broker_id)
    if not broker:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Broker not found"
        )

    # Here you would integrate with the actual broker's API to test the credentials.
    # For now, we'll simulate a successful test.
    # In a real scenario, this would involve calling a method on broker_service
    # that attempts to authenticate with the broker using the provided credentials.
    try:
        # Example: broker_service.test_connection(broker, connection_data.api_key, connection_data.api_secret)
        logger.info(f"Simulating successful connection test for broker ID '{connection_data.broker_id}'.")
        return {"message": "Connection test successful!"}
    except Exception as e:
        logger.error(f"Connection test failed for broker ID '{connection_data.broker_id}': {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {e}"
        )

@router.delete("/brokerage_connections/{connection_id}", status_code=status.HTTP_200_OK)
def delete_brokerage_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Deletes a brokerage connection for the current user.

    Args:
        connection_id (int): The ID of the brokerage connection to delete.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException: If the connection is not found or not authorized for the current user.
    """
    logger.info(f"Attempting to delete brokerage connection ID '{connection_id}' for user: {current_user.username}")

    db_connection = session.exec(select(BrokerageConnection).where(
        BrokerageConnection.id == connection_id,
        BrokerageConnection.user_id == current_user.id
    )).first()

    if not db_connection:
        logger.warning(f"Brokerage connection deletion failed for ID '{connection_id}': Not found or unauthorized.")
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Brokerage connection not found or unauthorized"
        )

    session.delete(db_connection)
    session.commit()
    logger.info(f"Brokerage connection ID '{connection_id}' deleted successfully for user: {current_user.username}")
    return {"message": f"Brokerage connection {connection_id} deleted successfully"}


@router.get("/brokers", response_model=List[Broker])
def get_all_brokers_route(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retrieves all available brokers from the database.

    Args:
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        List[Broker]: A list of all available brokers.
    """
    broker_service = BrokerService(session)
    return broker_service.get_all_brokers()

@router.get("/brokerage_connections", response_model=List[BrokerageConnectionResponse])
def get_brokerage_connections(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retrieves all brokerage connections for the current user.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        List[BrokerageConnectionResponse]: A list of brokerage connections.
    """
    return session.exec(select(BrokerageConnection).where(BrokerageConnection.user_id == current_user.id)).all()

@router.post("/bot_instances/", response_model=BotInstanceResponse, status_code=HTTP_201_CREATED)
def create_bot_instance(
    bot_instance: BotInstanceCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Creates a new bot instance for the current user.

    Args:
        bot_instance (BotInstanceCreate): The bot instance data.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        BotInstanceResponse: The created bot instance.
    """
    logger.info(f"Attempting to create bot instance '{bot_instance.name}' for user: {current_user.username}")
    db_bot_instance = BotInstance(
        user_id=current_user.id,
        strategy_id=bot_instance.strategy_id,
        brokerage_connection_id=bot_instance.brokerage_connection_id,
        name=bot_instance.name,
        parameters=bot_instance.parameters
    )
    session.add(db_bot_instance)
    session.commit()
    session.refresh(db_bot_instance)
    logger.info(f"Bot instance '{db_bot_instance.name}' (ID: {db_bot_instance.id}) created for user {current_user.username}.")
    return db_bot_instance

@router.get("/bot_instances/", response_model=List[BotInstanceResponse])
def get_bot_instances(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retrieves all bot instances for the current user.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        List[BotInstanceResponse]: A list of bot instances.
    """
    return session.exec(select(BotInstance).where(BotInstance.user_id == current_user.id)).all()

@router.get("/bot/status", response_model=List[BotStatusResponse])
def get_bot_status(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Retrieves the latest status for all bot instances belonging to the current user.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        List[BotStatusResponse]: A list of bot statuses.
    """
    bot_instances = session.exec(
        select(BotInstance).where(BotInstance.user_id == current_user.id)
    ).all()
    
    # Ensure that the bot_statuses list is initialized before the loop
    bot_statuses = []

    for bot_instance in bot_instances:
        latest_status = session.exec(
            select(BotStatus)
            .where(BotStatus.bot_instance_id == bot_instance.id)
            .order_by(BotStatus.last_check_in.desc())
        ).first()
        
        if latest_status:
            bot_statuses.append(latest_status)
        else:
            # If no status found, return a default/inactive status
            bot_statuses.append(BotStatus(
                id=None, # Or a placeholder ID if schema allows
                bot_instance_id=bot_instance.id,
                status="inactive",
                last_check_in=datetime.now(timezone.utc),
                is_active=False,
                error_message=None # Explicitly set error_message to None for inactive bots
            ))
    return bot_statuses

@router.get("/trading/orders", response_model=List[TradeOrderResponse])
def get_trade_orders(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    bot_instance_id: Optional[int] = Query(None, description="Filter by bot instance ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    start_date: Optional[datetime] = Query(None, description="Filter by executed_at from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter by executed_at up to this date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Retrieves trade orders for the current user, with optional filtering.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).
        bot_instance_id (Optional[int], optional): Filter by bot instance ID. Defaults to Query(None, description="Filter by bot instance ID").
        symbol (Optional[str], optional): Filter by symbol. Defaults to Query(None, description="Filter by symbol").
        status (Optional[str], optional): Filter by order status. Defaults to Query(None, description="Filter by order status").
        start_date (Optional[datetime], optional): Filter by executed_at from this date. Defaults to Query(None, description="Filter by executed_at from this date").
        end_date (Optional[datetime], optional): Filter by executed_at up to this date. Defaults to Query(None, description="Filter by executed_at up to this date").
        limit (int, optional): Maximum number of results to return. Defaults to Query(100, ge=1, le=1000, description="Maximum number of results to return").
        offset (int, optional): Number of results to skip. Defaults to Query(0, ge=0, description="Number of results to skip").

    Returns:
        List[TradeOrderResponse]: A list of trade orders.
    """
    query = select(TradeOrder).join(BotInstance).where(BotInstance.user_id == current_user.id)

    if bot_instance_id:
        query = query.where(TradeOrder.bot_instance_id == bot_instance_id)
    if symbol:
        query = query.where(TradeOrder.symbol == symbol)
    if status:
        query = query.where(TradeOrder.status == status)
    if start_date:
        query = query.where(TradeOrder.executed_at >= start_date)
    if end_date:
        query = query.where(TradeOrder.executed_at <= end_date)

    query = query.offset(offset).limit(limit)
    trade_orders = session.exec(query).all()
    return trade_orders

@router.get("/trading/positions", response_model=List[PositionResponse])
def get_positions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    bot_instance_id: Optional[int] = Query(None, description="Filter by bot instance ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Retrieves current positions for the current user, with optional filtering.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).
        bot_instance_id (Optional[int], optional): Filter by bot instance ID. Defaults to Query(None, description="Filter by bot instance ID").
        symbol (Optional[str], optional): Filter by symbol. Defaults to Query(None, description="Filter by symbol").

    Returns:
        List[PositionResponse]: A list of positions.
    """
    query = select(Position).join(BotInstance).where(BotInstance.user_id == current_user.id)

    if bot_instance_id:
        query = query.where(Position.bot_instance_id == bot_instance_id)
    if symbol:
        query = query.where(Position.symbol == symbol)
    
    positions = session.exec(query).all()
    return positions

@router.get("/bot/parameters", response_model=dict)
def get_bot_parameters(
    bot_id: int = Query(..., description="ID of the bot instance"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retrieves parameters for a specific bot instance.

    Args:
        bot_id (int): The ID of the bot instance.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        dict: A dictionary containing the bot's parameters.

    Raises:
        HTTPException: If the bot instance is not found or not authorized.
    """
    bot_instance = session.exec(
        select(BotInstance).where(
            BotInstance.id == bot_id,
            BotInstance.user_id == current_user.id
        )
    ).first()

    if not bot_instance:
        logger.warning(f"Get bot parameters failed: Bot instance with ID {bot_id} not found for user {current_user.username}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot instance not found")
    
    logger.info(f"Retrieved parameters for bot instance ID {bot_id}.")
    return {"parameters": bot_instance.parameters}

@router.post("/bot/parameters", response_model=dict)
def update_bot_parameters(
    bot_id: int = Query(..., description="ID of the bot instance"),
    *, # Add this to make subsequent arguments keyword-only
    updated_parameters: BotInstanceCreate, # Use BotInstanceCreate for the request body
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Updates parameters for a specific bot instance.

    Args:
        bot_id (int): The ID of the bot instance.
        updated_parameters (BotInstanceCreate): The updated parameters for the bot.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        session (Session, optional): Database session. Defaults to Depends(get_session).

    Returns:
        dict: A confirmation message and the updated parameters.

    Raises:
        HTTPException: If the bot instance is not found or not authorized.
    """
    bot_instance = session.exec(
        select(BotInstance).where(
            BotInstance.id == bot_id,
            BotInstance.user_id == current_user.id
        )
    ).first()

    logger.info(f"Attempting to update parameters for bot instance ID: {bot_id}")
    if not bot_instance:
        logger.warning(f"Update bot parameters failed: Bot instance with ID {bot_id} not found for user {current_user.username}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot instance not found")
    
    # Update only the parameters field from the request body
    bot_instance.parameters = updated_parameters.parameters
    session.add(bot_instance)
    session.commit()
    session.refresh(bot_instance)
    
    logger.info(f"Parameters updated successfully for bot instance ID {bot_id}.")
    return {"message": "Bot parameters updated successfully", "parameters": bot_instance.parameters}

@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    """
    A protected route example that requires authentication.

    Args:
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Returns:
        dict: A protected content message.
    """
    return {"message": "Protected content"}
