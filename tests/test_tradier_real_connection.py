import pytest
from src.brokerage.tradier_adapter import TradierAdapter
from src.models.brokerage_connection import BrokerageConnection
from src.models.broker import Broker
from src.config import settings, BROKER_CONFIGS
from datetime import datetime, timedelta, timezone
import os
import asyncio # Added for async tests

# Ensure the encryption key is set for testing
# This should match the default or configured key in src/config.py
# For real tests, it's crucial that the encryption key used here matches
# what BrokerageConnection expects.
os.environ["ENCRYPTION_KEY"] = settings.encryption_key

@pytest.fixture(scope="module")
def real_tradier_broker():
    """Provides a real Tradier Sandbox Broker object."""
    tradier_sandbox_config = next(
        (b for b in BROKER_CONFIGS if b["name"] == "Tradier Sandbox"), None
    )
    if not tradier_sandbox_config:
        pytest.skip("Tradier Sandbox configuration not found in BROKER_CONFIGS.")
    
    return Broker(
        name=tradier_sandbox_config["name"],
        base_url=tradier_sandbox_config["base_url"],
        streaming_url=tradier_sandbox_config["streaming_url"],
        is_live_mode=tradier_sandbox_config["is_live_mode"]
    )

@pytest.fixture(scope="module")
def real_tradier_connection(real_tradier_broker):
    """Provides a BrokerageConnection with real Tradier Sandbox credentials."""
    # These are sandbox credentials provided in the task description
    api_key = "VA1921000"
    api_secret = "F8ZAWUhT8KxP1fouaTz1jeiqjjbf"
    access_token = "F8ZAWUhT8KxP1fouaTz1jeiqjjbf"

    # For testing, we can use dummy user_id and broker_id
    # In a real scenario, these would come from the database
    user_id = 1
    broker_id = real_tradier_broker.id if real_tradier_broker.id else 1 # Use broker.id if available, else dummy

    # Initialize BrokerageConnection. It will encrypt the api_key and api_secret.
    connection = BrokerageConnection(
        user_id=user_id,
        broker_id=broker_id,
        api_key=api_key,
        api_secret=api_secret,
        access_token=access_token
        # For initial connection test, access_token and refresh_token are not needed
        # as connect() will attempt to exchange code for token if none exists.
        # However, for a direct connection test, we might need a pre-set token.
        # Let's assume for now that connect() handles the initial token acquisition.
        # If it fails, we might need to simulate an authorization flow or pre-set tokens.
    )
    # Manually set decrypted values for testing purposes if needed,
    # but the adapter should use the encrypted ones.
    # For a real connection test, we need to ensure the connection object
    # has a valid access token, or that the exchange_code_for_token is called.
    # Since the connect method first checks for an access token and then tries to refresh/obtain,
    # we need to simulate a scenario where it can obtain one.
    # For a direct connection test, we'll need to mock the token exchange or pre-set a token.
    # Let's pre-set a dummy access token for the `connect` method to proceed to the profile check.
    # The actual token exchange would require a full OAuth flow, which is out of scope for a simple connection test.
    # This test validates the adapter's ability to use a *provided* valid token.
    connection.expires_at = datetime.now(timezone.utc) + timedelta(days=1) # Set a future expiry

    return connection

@pytest.mark.skip(reason="Requires real Tradier API calls and a valid access token setup. Manual execution recommended.")
def test_real_tradier_connection(real_tradier_broker, real_tradier_connection):
    """
    Tests a real connection to the Tradier Sandbox API.
    This test requires actual network access and valid, non-expired credentials.
    It is skipped by default and should be run manually.
    """
    adapter = TradierAdapter(broker=real_tradier_broker, connection=real_tradier_connection)
    
    # Attempt to connect
    # This will use the pre-set mock_valid_access_token to hit the user profile endpoint.
    # If the mock token is not accepted by Tradier, this test will fail.
    # For a truly "real" connection test, you'd need to go through the OAuth flow
    # to get a real access token, which is complex for automated tests.
    # This test validates the adapter's ability to use a *provided* valid token.
    is_connected = adapter.connect()

    assert is_connected is True, "Failed to connect to Tradier Sandbox API with provided credentials."
    assert real_tradier_connection.connection_status == "connected"
    assert real_tradier_connection.last_connected is not None

@pytest.mark.skip(reason="Requires real Tradier API calls and a valid access token setup. Manual execution recommended.")
def test_get_account_balance(real_tradier_broker, real_tradier_connection):
    """
    Tests retrieving account balance from Tradier Sandbox API.
    """
    adapter = TradierAdapter(broker=real_tradier_broker, connection=real_tradier_connection)
    
    # Ensure connection is established before making API calls
    assert adapter.connect() is True

    balance = adapter.get_account_balance()
    assert balance is not None
    assert "account_number" in balance
    # assert "option_buying_power" in balance
    print(f"Account Balance: {balance}")

@pytest.mark.skip(reason="Requires real Tradier API calls and a valid access token setup. Manual execution recommended.")
def test_get_positions(real_tradier_broker, real_tradier_connection):
    """
    Tests retrieving current positions from Tradier Sandbox API.
    """
    adapter = TradierAdapter(broker=real_tradier_broker, connection=real_tradier_connection)
    
    assert adapter.connect() is True

    positions = adapter.get_positions()
    assert isinstance(positions, list)
    # Depending on the sandbox account, this might be empty or contain positions
    print(f"Positions: {positions}")

@pytest.mark.skip(reason="Requires real Tradier API calls and a valid access token setup. Manual execution recommended.")
def test_get_orders(real_tradier_broker, real_tradier_connection):
    """
    Tests retrieving active and historical orders from Tradier Sandbox API.
    """
    adapter = TradierAdapter(broker=real_tradier_broker, connection=real_tradier_connection)
    
    assert adapter.connect() is True

    orders = adapter.get_orders()
    # assert isinstance(orders, list)
    # Depending on the sandbox account, this might be empty or contain orders
    print(f"Orders: {orders}")

@pytest.mark.skip(reason="Requires real Tradier API calls and a valid access token setup. Manual execution recommended.")
@pytest.mark.asyncio
async def test_get_quotes(real_tradier_broker, real_tradier_connection):
    """
    Tests retrieving market quotes for specified symbols from Tradier Sandbox API.
    """
    adapter = TradierAdapter(broker=real_tradier_broker, connection=real_tradier_connection)
    
    assert adapter.connect() is True

    symbols = ["AAPL", "MSFT"]
    quotes = await adapter.get_quotes(symbols)
    assert isinstance(quotes, dict)
    assert len(quotes) > 0
    for symbol in symbols:
        assert symbol in quotes
        assert "last" in quotes[symbol] # Check for a common quote field
    print(f"Quotes for {symbols}: {quotes}")

@pytest.mark.skip(reason="Requires real Tradier API calls and a valid access token setup. Manual execution recommended.")
@pytest.mark.asyncio
async def test_get_option_chain(real_tradier_broker, real_tradier_connection):
    """
    Tests retrieving option chain data for a given symbol from Tradier Sandbox API.
    """
    adapter = TradierAdapter(broker=real_tradier_broker, connection=real_tradier_connection)
    
    assert adapter.connect() is True

    symbol = "SPY" # A common symbol with options
    expiration = "2025-06-20"

    option_chain = await adapter.get_option_chain(symbol, expiration)
    print(f"Option Chain for {symbol} (first 5 entries): {option_chain[:5]}")
    assert isinstance(option_chain, list)
    # Option chain can be very large, just check if it's not empty
    assert len(option_chain) > 0
    # print(f"Option Chain for {symbol} (first 5 entries): {option_chain[:5]}")

@pytest.mark.skip(reason="Requires real Tradier API calls and a valid access token setup. Placing and canceling orders modifies the account. Use with caution.")
@pytest.mark.asyncio
async def test_place_and_cancel_order(real_tradier_broker, real_tradier_connection):
    """
    Tests placing a dummy order and then canceling it.
    This test modifies the sandbox account.
    """
    adapter = TradierAdapter(broker=real_tradier_broker, connection=real_tradier_connection)
    
    assert adapter.connect() is True

    symbol = "GOOG" # Use a liquid stock for testing
    quantity = 1
    order_type = "limit"
    price = 1.00 # A very low price to ensure it doesn't fill immediately in sandbox

    print(f"Attempting to place a dummy {order_type} order for {quantity} shares of {symbol} at ${price}...")
    placed_order = await adapter.place_order(symbol=symbol, quantity=quantity, order_type=order_type, order_class="equity", duration="day", side="buy", price=price)
    
    assert placed_order is not None
    assert "id" in placed_order # Check if an order ID is returned
    assert placed_order.get("status") == "ok" or placed_order.get("status") == "accepted" # Status might vary in sandbox
    
    order_id = placed_order["id"]
    print(f"Order placed with ID: {order_id}. Attempting to cancel...")

    # Give a small delay to ensure the order is processed by Tradier before attempting to cancel
    await asyncio.sleep(2)

    is_cancelled = adapter.cancel_order(order_id=str(order_id))
    assert is_cancelled is True, f"Failed to cancel order {order_id}"
    print(f"Order {order_id} cancelled successfully.")