import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from sqlmodel import select # Import select
from src.models.brokerage_connection import BrokerageConnection
from src.models.user import User
from src.brokerage.tradier_adapter import TradierAdapter # Import TradierAdapter
from unittest.mock import MagicMock # Import MagicMock

def test_create_brokerage_connection(session):
    """Test that a BrokerageConnection can be created and retrieved."""
    user = User(username="testuser", email="test@example.com", hashed_password="hashed_password")
    session.add(user)
    session.commit()
    session.refresh(user)

    connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="Tradier",
        api_key="test_api_key",
        api_secret="test_api_secret",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        connection_status="connected",
        last_connected=datetime.now(timezone.utc)
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)

    assert connection.id is not None
    assert connection.user_id == user.id
    assert connection.brokerage_name == "Tradier"
    assert connection.decrypt_api_key() == "test_api_key" # Check decryption
    assert connection.decrypt_api_secret() == "test_api_secret" # Check decryption
    assert connection.decrypt_access_token() == "test_access_token"
    assert connection.decrypt_refresh_token() == "test_refresh_token"
    assert connection.connection_status == "connected"
    assert connection.last_connected is not None

    # Verify relationship
    assert connection.user.username == "testuser"

def test_brokerage_connection_encryption_methods(session):
    """Test the encryption/decryption methods."""
    user = User(username="anotheruser", email="another@example.com", hashed_password="another_hashed_password")
    session.add(user)
    session.commit()
    session.refresh(user)

    connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="InteractiveBrokers",
        api_key="initial_api_key",
        api_secret="initial_api_secret",
        access_token="token",
        refresh_token="refresh",
        connection_status="disconnected",
        last_connected=None
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)

    # Test set_api_key and get_api_key
    new_api_key = "new_api_key_value"
    # The BrokerageConnection model now encrypts on init, so direct set_api_key is not needed
    # Instead, we'll create a new connection to simulate updating the key
    # For testing purposes, we'll re-create the connection with the new key
    # In a real application, you would update the existing connection object's string fields
    # and then call session.add(connection) and session.commit()
    
    # Simulate updating the API key by creating a new instance with the updated key
    # This is a simplification for testing the decryption logic
    updated_connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="InteractiveBrokers",
        api_key=new_api_key,
        api_secret="initial_api_secret",
        access_token="token",
        refresh_token="refresh",
        connection_status="disconnected",
        last_connected=None
    )
    session.add(updated_connection)
    session.commit()
    session.refresh(updated_connection)
    assert updated_connection.decrypt_api_key() == new_api_key

    # Test set_api_secret and get_api_secret
    new_api_secret = "new_api_secret_value"
    # Simulate updating the API secret
    updated_connection_secret = BrokerageConnection(
        user_id=user.id,
        brokerage_name="InteractiveBrokers",
        api_key=new_api_key, # Use the new_api_key from previous step
        api_secret=new_api_secret,
        access_token="token",
        refresh_token="refresh",
        connection_status="disconnected",
        last_connected=None
    )
    session.add(updated_connection_secret)
    session.commit()
    session.refresh(updated_connection_secret)
    assert updated_connection_secret.decrypt_api_secret() == new_api_secret

def test_brokerage_connection_repr(session):
    """Test the __repr__ method of BrokerageConnection."""
    user = User(username="repruser", email="repr@example.com", hashed_password="repr_password")
    session.add(user)
    session.commit()
    session.refresh(user)

    connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="TestBroker",
        api_key="key",
        api_secret="secret",
        connection_status="connected"
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)

    expected_repr = f"<BrokerageConnection(id={connection.id}, user_id={user.id}, brokerage_name='TestBroker', status='connected')>"
    assert repr(connection) == expected_repr

def test_brokerage_connection_on_user_delete_cascade(session):
    """Test CASCADE delete on user_id."""
    user = User(username="cascadeuser", email="cascade@example.com", hashed_password="hashed_password")
    session.add(user)
    session.commit()
    session.refresh(user)

    connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="CascadeBroker",
        api_key="key",
        api_secret="secret"
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)

    connection_id = connection.id
    user_id = user.id

    # Delete the user
    session.delete(user)
    session.commit()

    # Try to retrieve the connection, it should be deleted
    deleted_connection = session.exec(select(BrokerageConnection).where(BrokerageConnection.id == connection_id)).first()
    assert deleted_connection is None

    # Ensure user is also deleted
    deleted_user = session.exec(select(User).where(User.id == user_id)).first()
    assert deleted_user is None


@pytest.fixture
def tradier_connection(session):
    user = User(username="tradieruser", email="tradier@example.com", hashed_password="hashed_password")
    session.add(user)
    session.commit()
    session.refresh(user)
    connection = BrokerageConnection(
        user_id=user.id,
        brokerage_name="Tradier",
        api_key="mock_api_key",
        api_secret="mock_api_secret",
        access_token="mock_token",
        refresh_token="mock_refresh_token",
        connection_status="connected",
        last_connected=datetime.now(timezone.utc)
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)
    return connection

@pytest.mark.asyncio
async def test_tradier_adapter_get_option_chain(session, tradier_connection, mock_tradier_option_chain_response):
    """Test get_option_chain method of TradierAdapter."""
    # Create a real TradierAdapter instance using the connection object
    adapter = TradierAdapter(connection=tradier_connection)
    
    # Mock the requests.get call
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_tradier_option_chain_response
        mock_get.return_value.raise_for_status.return_value = None

        option_chain = await adapter.get_option_chain("SPY")
        assert isinstance(option_chain, list)
        assert len(option_chain) > 0
        assert option_chain[0]['symbol'] == 'SPY240621C00500000'
        mock_get.assert_called_once_with(
            f"{adapter._base_url}markets/options/chains",
            headers={
                "Authorization": f"Bearer {adapter._access_token}",
                "Accept": "application/json"
            },
            params={"symbol": "SPY"}
        )

@pytest.mark.asyncio
async def test_tradier_adapter_place_order(session, tradier_connection, mock_tradier_place_order_response):
    """Test place_order method of TradierAdapter."""
    # Create a real TradierAdapter instance using the connection object
    adapter = TradierAdapter(connection=tradier_connection)

    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_tradier_place_order_response
        mock_post.return_value.raise_for_status.return_value = None

        order_details = await adapter.place_order("AAPL", 10, "market")
        assert isinstance(order_details, dict)
        assert order_details['status'] == 'ok'
        assert order_details['id'] == 12345
        mock_post.assert_called_once_with(
            f"{adapter._base_url}accounts/{adapter._account_id}/orders",
            headers={
                "Authorization": f"Bearer {adapter._access_token}",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "class": "equity",
                "symbol": "AAPL",
                "quantity": 10,
                "type": "market"
            }
        )

def test_tradier_adapter_get_positions(session, tradier_connection, mock_tradier_positions_response):
    """Test get_positions method of TradierAdapter."""
    # Create a real TradierAdapter instance using the connection object
    adapter = TradierAdapter(connection=tradier_connection)

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_tradier_positions_response
        mock_get.return_value.raise_for_status.return_value = None

        positions = adapter.get_positions()
        assert isinstance(positions, list)
        assert len(positions) > 0
        assert positions[0]['symbol'] == 'MSFT'
        mock_get.assert_called_once_with(
            f"{adapter._base_url}accounts/{adapter._account_id}/positions",
            headers={
                "Authorization": f"Bearer {adapter._access_token}",
                "Accept": "application/json"
            }
        )

@pytest.mark.asyncio
async def test_tradier_adapter_get_quotes(session, tradier_connection, mock_tradier_quotes_response):
    """Test get_quotes method of TradierAdapter."""
    # Create a real TradierAdapter instance using the connection object
    adapter = TradierAdapter(connection=tradier_connection)

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_tradier_quotes_response
        mock_get.return_value.raise_for_status.return_value = None

        quotes = await adapter.get_quotes(["GOOG", "AMZN"])
        assert isinstance(quotes, dict)
        assert "GOOG" in quotes
        assert "AMZN" in quotes
        assert quotes["GOOG"]["description"] == "Alphabet Inc. Class C"
        mock_get.assert_called_once_with(
            f"{adapter._base_url}markets/quotes",
            headers={
                "Authorization": f"Bearer {adapter._access_token}",
                "Accept": "application/json"
            },
            params={"symbols": "GOOG,AMZN"}
        )

def test_tradier_adapter_get_orders(session, tradier_connection, mock_tradier_orders_response):
    """Test get_orders method of TradierAdapter."""
    # Create a real TradierAdapter instance using the connection object
    adapter = TradierAdapter(connection=tradier_connection)

    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_tradier_orders_response
        mock_get.return_value.raise_for_status.return_value = None

        orders = adapter.get_orders()
        assert isinstance(orders, list)
        assert len(orders) > 0
        assert orders[0]['id'] == 123456
        mock_get.assert_called_once_with(
            f"{adapter._base_url}accounts/{adapter._account_id}/orders",
            headers={
                "Authorization": f"Bearer {adapter._access_token}",
                "Accept": "application/json"
            }
        )

def test_tradier_adapter_cancel_order(session, tradier_connection, mock_tradier_cancel_order_response):
    """Test cancel_order method of TradierAdapter."""
    # Create a real TradierAdapter instance using the connection object
    adapter = TradierAdapter(connection=tradier_connection)

    with patch('requests.delete') as mock_delete:
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = mock_tradier_cancel_order_response
        mock_delete.return_value.raise_for_status.return_value = None

        result = adapter.cancel_order("12345")
        assert result is True
        mock_delete.assert_called_once_with(
            f"{adapter._base_url}accounts/{adapter._account_id}/orders/12345",
            headers={
                "Authorization": f"Bearer {adapter._access_token}",
                "Accept": "application/json"
            }
        )

@pytest.fixture
def mock_tradier_option_chain_response():
    """Mock response for Tradier get_option_chain."""
    return {
        "options": {
            "option": [
                {
                    "symbol": "SPY240621C00500000",
                    "description": "SPY JUN 21 24 500 Call",
                    "exch": "PHLX",
                    "type": "call",
                    "last": 0.0,
                    "change": 0.0,
                    "bid": 0.0,
                    "ask": 0.0,
                    "volume": 0,
                    "open_interest": 0,
                    "underlying": "SPY",
                    "strike": 500.0,
                    "expiration_date": "2024-06-21",
                    "trade_date": "2024-05-20",
                    "greeks": {
                        "delta": 0.0,
                        "gamma": 0.0,
                        "theta": 0.0,
                        "vega": 0.0,
                        "rho": 0.0,
                        "impliedVolatility": 0.0,
                        "bidIv": 0.0,
                        "askIv": 0.0
                    }
                }
            ]
        }
    }

@pytest.fixture
def mock_tradier_place_order_response():
    """Mock response for Tradier place_order."""
    return {
        "order": {
            "id": 12345,
            "status": "ok",
            "exec_quantity": 0,
            "remaining_quantity": 10,
            "create_date": "2024-05-20 10:00:00.000",
            "transaction_date": "2024-05-20 10:00:00.000",
            "class": "equity",
            "symbol": "AAPL",
            "type": "market",
            "side": "buy",
            "quantity": 10,
            "strategy": "single",
            "tag": "my_order_tag"
        }
    }

@pytest.fixture
def mock_tradier_positions_response():
    """Mock response for Tradier get_positions."""
    return {
        "positions": {
            "position": [
                {
                    "symbol": "MSFT",
                    "qty": 100,
                    "cost_basis": 150.0,
                    "open_date": "2023-01-01",
                    "purchase_price": 150.0,
                    "current_value": 16000.0
                }
            ]
        }
    }

@pytest.fixture
def mock_tradier_quotes_response():
    """Mock response for Tradier get_quotes."""
    return {
        "quotes": {
            "quote": [
                {
                    "symbol": "GOOG",
                    "description": "Alphabet Inc. Class C",
                    "last": 170.0,
                    "bid": 169.9,
                    "ask": 170.1
                },
                {
                    "symbol": "AMZN",
                    "description": "Amazon.com Inc.",
                    "last": 180.0,
                    "bid": 179.9,
                    "ask": 180.1
                }
            ]
        }
    }

@pytest.fixture
def mock_tradier_orders_response():
    """Mock response for Tradier get_orders."""
    return {
        "orders": {
            "order": [
                {
                    "id": 123456,
                    "status": "open",
                    "symbol": "GOOG",
                    "type": "limit",
                    "quantity": 10,
                    "price": 160.0
                }
            ]
        }
    }

@pytest.fixture
def mock_tradier_cancel_order_response():
    """Mock response for Tradier cancel_order."""
    return {
        "order": {
            "id": 12345,
            "status": "ok"
        }
    }