import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.model.base import BaseModel as Base
from src.models import User, Session, BrokerageConnection, BotInstance, StrategyDefinition, StrategyParameter, TradeOrder, Position, MarketDataCache_OptionChain
from src.config import settings
from datetime import datetime, timedelta, timezone
from src.utils.encryption import generate_key # Import generate_key

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def engine():
    return create_engine(DATABASE_URL)

@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

def test_user_creation(db_session):
    user = User(username="testuser", hashed_password="hashedpassword", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
    assert user.username == "testuser"

def test_user_unique_username(db_session):
    user1 = User(username="uniqueuser", hashed_password="hashedpassword1")
    user2 = User(username="uniqueuser", hashed_password="hashedpassword2")
    db_session.add(user1)
    db_session.commit()
    with pytest.raises(Exception): # Expecting IntegrityError or similar
        db_session.add(user2)
        db_session.commit()

def test_user_unique_email(db_session):
    user1 = User(username="userA", hashed_password="hpA", email="email@example.com")
    user2 = User(username="userB", hashed_password="hpB", email="email@example.com")
    db_session.add(user1)
    db_session.commit()
    with pytest.raises(Exception): # Expecting IntegrityError or similar
        db_session.add(user2)
        db_session.commit()

def test_session_creation(db_session):
    user = User(username="sessionuser", hashed_password="hp")
    db_session.add(user)
    db_session.commit()
    session = Session(user_id=user.id, access_token="someaccesstoken", refresh_token="somerefreshtoken", expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db_session.add(session)
    db_session.commit()
    assert session.session_id is not None
    assert session.user.username == "sessionuser"

def test_brokerage_connection_creation(db_session):
    user = User(username="brokeruser", hashed_password="hp")
    db_session.add(user)
    db_session.commit()
    # Generate a valid Fernet key for testing
    test_encryption_key = generate_key()
    # Temporarily override the settings.encryption_key for this test
    original_encryption_key = settings.encryption_key
    settings.encryption_key = test_encryption_key

    conn = BrokerageConnection(user_id=user.id, brokerage_name="Tradier", api_key="test_api_key", api_secret="test_api_secret")
    db_session.add(conn)
    db_session.commit()

    # Assert that the tokens are encrypted (i.e., they are bytes and not the original string)
    assert isinstance(conn.api_key, bytes)
    assert isinstance(conn.api_secret, bytes)
    assert conn.decrypt_api_key() == "test_api_key"
    assert conn.decrypt_api_secret() == "test_api_secret"

    # Restore the original encryption key
    settings.encryption_key = original_encryption_key
    db_session.add(conn)
    db_session.commit()
    assert conn.id is not None
    assert conn.user.username == "brokeruser"

def test_bot_instance_creation(db_session):
    user = User(username="botuser", hashed_password="hp")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    strategy = StrategyDefinition(name="TestStrategy", file_path="test.py", class_name="TestStrategyClass", created_by=user.id)
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    # Generate a valid Fernet key for testing
    test_encryption_key = generate_key()
    # Temporarily override the settings.encryption_key for this test
    original_encryption_key = settings.encryption_key
    settings.encryption_key = test_encryption_key

    conn = BrokerageConnection(user_id=user.id, brokerage_name="Tradier", api_key="test_api_key", api_secret="test_api_secret")
    db_session.add(conn)
    db_session.commit()
    db_session.refresh(conn)

    # Restore the original encryption key
    settings.encryption_key = original_encryption_key
    
    bot = BotInstance(user_id=user.id, strategy_id=strategy.id, brokerage_connection_id=conn.id, name="MyBot", status="running")
    db_session.add(bot)
    db_session.commit()
    db_session.refresh(bot)
    assert bot.id is not None
    assert bot.user.username == "botuser"
    assert bot.brokerage_connection.brokerage_name == "Tradier"
    assert bot.strategy.name == "TestStrategy"

def test_strategy_definition_creation(db_session):
    user = User(username="strategyuser", hashed_password="hp")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    strategy = StrategyDefinition(name="PMCC", file_path="pmcc.py", class_name="PMCCStrategy", created_by=user.id)
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    assert strategy.id is not None
    assert strategy.name == "PMCC"
    assert strategy.created_user.username == "strategyuser"

def test_strategy_parameters_pmcc_creation(db_session):
    user = User(username="pmccuser", hashed_password="hp")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    strategy = StrategyDefinition(name="PMCC_Params", file_path="pmcc.py", class_name="PMCCStrategy", created_by=user.id)
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    strategy_params = [
        StrategyParameter(strategy_definition_id=strategy.id, name="delta_threshold", value="0.7"),
        StrategyParameter(strategy_definition_id=strategy.id, name="days_to_expiration_long", value="365"),
        StrategyParameter(strategy_definition_id=strategy.id, name="days_to_expiration_short", value="30"),
        StrategyParameter(strategy_definition_id=strategy.id, name="profit_target_percentage", value="0.1"),
        StrategyParameter(strategy_definition_id=strategy.id, name="stop_loss_percentage", value="0.05"),
    ]
    db_session.add_all(strategy_params)
    db_session.commit()
    for param in strategy_params:
        db_session.refresh(param)

    retrieved_params = db_session.query(StrategyParameter).filter_by(strategy_definition_id=strategy.id).all()
    assert len(retrieved_params) == 5
    param_names = {p.name for p in retrieved_params}
    assert "delta_threshold" in param_names
    assert "days_to_expiration_long" in param_names
    assert "days_to_expiration_short" in param_names
    assert "profit_target_percentage" in param_names
    assert "stop_loss_percentage" in param_names
    assert retrieved_params[0].id is not None
    assert retrieved_params[0].strategy_definition.name == "PMCC_Params"

def test_trade_order_creation(db_session):
    user = User(username="orderuser", hashed_password="hp")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    strategy = StrategyDefinition(name="OrderStrategy", file_path="order.py", class_name="OrderStrategyClass", created_by=user.id)
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    # Generate a valid Fernet key for testing
    test_encryption_key = generate_key()
    # Temporarily override the settings.encryption_key for this test
    original_encryption_key = settings.encryption_key
    settings.encryption_key = test_encryption_key

    conn = BrokerageConnection(user_id=user.id, brokerage_name="Tradier", api_key="test_api_key", api_secret="test_api_secret")
    db_session.add(conn)
    db_session.commit()
    db_session.refresh(conn)

    # Restore the original encryption key
    settings.encryption_key = original_encryption_key
    
    bot = BotInstance(user_id=user.id, strategy_id=strategy.id, brokerage_connection_id=conn.id, name="OrderBot", status="running")
    db_session.add(bot)
    db_session.commit()
    db_session.refresh(bot)

    order = TradeOrder(bot_instance_id=bot.id, symbol="SPY", order_type="market", quantity=10, status="pending")
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    assert order.id is not None
    assert order.bot_instance.name == "OrderBot"

def test_position_creation(db_session):
    user = User(username="positionuser", hashed_password="hp")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    strategy = StrategyDefinition(name="PositionStrategy", file_path="position.py", class_name="PositionStrategyClass", created_by=user.id)
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    # Generate a valid Fernet key for testing
    test_encryption_key = generate_key()
    # Temporarily override the settings.encryption_key for this test
    original_encryption_key = settings.encryption_key
    settings.encryption_key = test_encryption_key

    conn = BrokerageConnection(user_id=user.id, brokerage_name="Tradier", api_key="test_api_key", api_secret="test_api_secret")
    db_session.add(conn)
    db_session.commit()
    db_session.refresh(conn)

    # Restore the original encryption key
    settings.encryption_key = original_encryption_key
    
    bot = BotInstance(user_id=user.id, strategy_id=strategy.id, brokerage_connection_id=conn.id, name="PositionBot", status="running")
    db_session.add(bot)
    db_session.commit()
    db_session.refresh(bot)

    position = Position(bot_instance_id=bot.id, symbol="AAPL", quantity=5, average_cost=150.0)
    db_session.add(position)
    db_session.commit()
    db_session.refresh(position)
    assert position.id is not None
    assert position.bot_instance.name == "PositionBot"

def test_market_data_cache_option_chain_creation(db_session):
    option_data = MarketDataCache_OptionChain(
        symbol="GOOG",
        expiration_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
        strike_price=100.0,
        option_type="call",
        bid=5.0,
        ask=5.5,
        implied_volatility=0.2,
        delta=0.5,
        gamma=0.05,
        theta=-0.01,
        vega=0.1,
        open_interest=1000,
        volume=500
    )
    db_session.add(option_data)
    db_session.commit()
    assert option_data.id is not None
    assert option_data.symbol == "GOOG"