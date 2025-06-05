from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from src.config import settings
from src.utils.security import create_access_token, create_refresh_token

from src.database import get_session
from src.models.user import User
from src.models.session import Session as DBSession
from src.models.brokerage_connection import BrokerageConnection
from src.models.bot_instance import BotInstance
from src.models.bot_status import BotStatus
from src.models.trade_order import TradeOrder
from src.models.position import Position
from src.services.bot_service import BotService
from src.utils.security import get_current_user
from src.schemas import UserCreate, UserResponse, Token, LoginRequest, BrokerageConnectionCreate, BrokerageConnectionResponse, BotInstanceCreate, BotInstanceResponse, BotStatusResponse, TradeOrderResponse, PositionResponse
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, OAuth2PasswordBearer

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = User(username=user.username, email=user.email)
    new_user.set_password(user.password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": str(user.id)}, expires_delta=access_token_expires
    )

    new_refresh_token = create_refresh_token()
    db_session = DBSession(
        user_id=user.id,
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_at=datetime.now(timezone.utc) + access_token_expires
    )
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    print(f"DEBUG: Stored refresh token in DB: {new_refresh_token}")
    
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": new_refresh_token}

@router.get("/users/me/", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Extract the access token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    
    access_token = auth_header.split(" ")[1]

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
        return {"message": "Successfully logged out"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active session not found")

@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str = Depends(OAuth2PasswordBearer(tokenUrl="token")), # Get refresh token from header
    session: Session = Depends(get_session)
):
    print(f"DEBUG: Refresh endpoint received token: {refresh_token}")
    # Find the session associated with the refresh token
    db_session = session.exec(select(DBSession).where(
        DBSession.refresh_token == refresh_token,
        DBSession.is_active == True
    )).first()

    if not db_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Generate a new access token
    new_access_token_expires = timedelta(minutes=settings.jwt_expiration_minutes)
    new_access_token = create_access_token(
        data={"sub": db_session.user.username, "user_id": str(db_session.user.id)},
        expires_delta=new_access_token_expires
    )

    # Update the existing session with the new access token and expiration
    db_session.access_token = new_access_token
    db_session.expires_at = datetime.now(timezone.utc) + new_access_token_expires
    db_session.last_activity = datetime.now(timezone.utc)
    session.add(db_session)
    session.commit()
    session.refresh(db_session)

    return {"access_token": new_access_token, "token_type": "bearer"}

@router.get("/user/sessions", response_model=List[dict])
def get_user_sessions(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    user_sessions = session.exec(select(DBSession).where(DBSession.user_id == current_user.id)).all()
    
    # Convert to a list of dictionaries, including the session_id
    return [{"id": s.session_id, "is_active": s.is_active, "expires_at": s.expires_at, "last_activity": s.last_activity} for s in user_sessions]

@router.delete("/user/sessions/{session_id}", status_code=status.HTTP_200_OK)
def terminate_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    db_session = session.exec(select(DBSession).where(
        DBSession.session_id == session_id,
        DBSession.user_id == current_user.id
    )).first()

    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or not authorized")

    db_session.is_active = False
    db_session.logged_out_at = datetime.now(timezone.utc)
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    
    return {"message": f"Session {session_id} terminated successfully"}

@router.post("/brokerage_connections/", response_model=BrokerageConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_brokerage_connection(
    connection: BrokerageConnectionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    db_connection = BrokerageConnection(
        user_id=current_user.id,
        brokerage_name=connection.brokerage_name,
        api_key=connection.api_key,
        api_secret=connection.api_secret,
        account_id=connection.account_id
    )
    session.add(db_connection)
    session.commit()
    session.refresh(db_connection)
    return db_connection

@router.get("/brokerage_connections/", response_model=List[BrokerageConnectionResponse])
def get_brokerage_connections(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return session.exec(select(BrokerageConnection).where(BrokerageConnection.user_id == current_user.id)).all()

@router.post("/bot_instances/", response_model=BotInstanceResponse, status_code=status.HTTP_201_CREATED)
def create_bot_instance(
    bot_instance: BotInstanceCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
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
    return db_bot_instance

@router.get("/bot_instances/", response_model=List[BotInstanceResponse])
def get_bot_instances(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    return session.exec(select(BotInstance).where(BotInstance.user_id == current_user.id)).all()

@router.get("/bot_status/", response_model=BotStatusResponse)
def get_bot_status(session: Session = Depends(get_session)):
    bot_service = BotService(session)
    status = bot_service.get_bot_status()
    return status

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
    try:
        bot_instance = session.exec(
            select(BotInstance).where(
                BotInstance.id == bot_id,
                BotInstance.user_id == current_user.id
            )
        ).first()

        if not bot_instance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot instance not found")
        
        return {"parameters": bot_instance.parameters}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.post("/bot/parameters", response_model=dict)
def update_bot_parameters(
    bot_id: int = Query(..., description="ID of the bot instance"),
    *, # Add this to make subsequent arguments keyword-only
    updated_parameters: BotInstanceCreate, # Use BotInstanceCreate for the request body
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    try:
        bot_instance = session.exec(
            select(BotInstance).where(
                BotInstance.id == bot_id,
                BotInstance.user_id == current_user.id
            )
        ).first()

        if not bot_instance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot instance not found")
        
        # Update only the parameters field from the request body
        bot_instance.parameters = updated_parameters.parameters
        session.add(bot_instance)
        session.commit()
        session.refresh(bot_instance)
        
        return {"message": "Bot parameters updated successfully", "parameters": bot_instance.parameters}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.get("/protected")
def protected_route():
    return {"message": "Protected content"}
