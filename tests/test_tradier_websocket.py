import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.brokerage.tradier_websocket import TradierWebSocketClient
from src.config import settings

@pytest.fixture
def mock_websocket_connection():
    """Mocks a websockets.WebSocketClientProtocol instance."""
    mock_ws = AsyncMock()
    mock_ws.recv.side_effect = [
        json.dumps({"msg": "connected"}),
        json.dumps({"msg": "auth", "data": {"status": "ok"}}),
        json.dumps({"msg": "quote", "data": {"symbol": "SPY", "last": 400.0}}),
        json.dumps({"msg": "option", "data": {"symbol": "AAPL", "strike": 150, "option_type": "call"}}),
        asyncio.CancelledError # To stop the listen loop
    ]
    return mock_ws

@pytest.fixture(autouse=True)
def mock_websockets_connect(mock_websocket_connection):
    """Mocks websockets.connect."""
    with patch('src.brokerage.tradier_websocket.websockets.connect', new_callable=AsyncMock) as mock_connect:
        mock_connect.return_value = mock_websocket_connection
        yield mock_connect

@pytest.fixture(autouse=True)
def mock_redis_client_fixture():
    """Mocks the global redis_client for each test."""
    with patch('src.brokerage.tradier_websocket.redis_client', new_callable=AsyncMock) as mock_client:
        yield mock_client

@pytest.fixture(autouse=True)
def mock_logger():
    """Mocks the logger to prevent actual logging during tests."""
    with patch('src.brokerage.tradier_websocket.logger') as mock_log:
        yield mock_log

@pytest.mark.asyncio
async def test_connect_success(mock_websockets_connect, mock_websocket_connection, mock_logger):
    """Test successful WebSocket connection and authentication."""
    client = TradierWebSocketClient(access_token="test_token")
    await client.connect()

    mock_websockets_connect.assert_called_once_with(settings.tradier_websocket_url)
    assert client.is_connected is True
    mock_websocket_connection.send.assert_any_call(json.dumps({"jsonrpc": "2.0", "msg": "auth", "data": {"access_token": "test_token"}}))
    mock_logger.info.assert_any_call("Tradier WebSocket connected.")
    mock_logger.info.assert_any_call("Sent authentication message to Tradier WebSocket.")
    assert client.ping_task is not None
    assert not client.ping_task.done() # Ping task should be running

@pytest.mark.asyncio
async def test_disconnect(mock_websocket_connection, mock_logger):
    """Test WebSocket disconnection."""
    client = TradierWebSocketClient(access_token="test_token")
    client.connection = mock_websocket_connection
    client.is_connected = True
    client.ping_task = asyncio.create_task(asyncio.sleep(100)) # Simulate running ping task

    await client.disconnect()

    mock_websocket_connection.close.assert_called_once()
    assert client.is_connected is False
    assert client.ping_task.done() # Ping task should be cancelled
    mock_logger.info.assert_called_with("Tradier WebSocket disconnected.")

@pytest.mark.asyncio
async def test_send_message(mock_websocket_connection):
    """Test sending a message when connected."""
    client = TradierWebSocketClient(access_token="test_token")
    client.connection = mock_websocket_connection
    client.is_connected = True
    test_message = {"type": "test", "data": "hello"}
    await client.send_message(test_message)
    mock_websocket_connection.send.assert_called_once_with(json.dumps(test_message))

@pytest.mark.asyncio
async def test_send_message_not_connected(mock_websocket_connection, mock_logger):
    """Test sending a message when not connected."""
    client = TradierWebSocketClient(access_token="test_token")
    client.connection = None
    client.is_connected = False
    test_message = {"type": "test", "data": "hello"}
    await client.send_message(test_message)
    mock_websocket_connection.send.assert_not_called()
    mock_logger.warning.assert_called_with("WebSocket not connected. Cannot send message.")

@pytest.mark.asyncio
async def test_subscribe(mock_websocket_connection, mock_logger):
    """Test subscribing to channels."""
    client = TradierWebSocketClient(access_token="test_token")
    client.connection = mock_websocket_connection
    client.is_connected = True
    symbols = ["SPY", "AAPL"]
    channels = ["quote", "trade"]
    await client.subscribe(symbols, channels)
    expected_message = {
        "jsonrpc": "2.0",
        "msg": "subscribe",
        "data": {
            "symbols": "SPY,AAPL",
            "channels": "quote,trade"
        }
    }
    mock_websocket_connection.send.assert_called_once_with(json.dumps(expected_message))
    mock_logger.info.assert_called_with(f"Subscribed to {channels} for symbols: {symbols}")

@pytest.mark.asyncio
async def test_listen_for_messages_and_update_redis(mock_websocket_connection, mock_redis_client_fixture, mock_logger):
    """Test listening for messages and updating Redis cache."""
    client = TradierWebSocketClient(access_token="test_token")
    client.connection = mock_websocket_connection
    client.is_connected = True

    # Run listen_for_messages in a background task
    listen_task = asyncio.create_task(client.listen_for_messages())

    # Allow some time for messages to be processed
    await asyncio.sleep(0.1) 

    # Verify Redis updates for quote
    mock_redis_client_fixture.set.assert_any_call("quotes:SPY", json.dumps({"symbol": "SPY", "last": 400.0}))
    mock_logger.debug.assert_any_call("Updated quote for SPY in Redis.")

    # Verify Redis updates for option
    expected_option_key = "option_chain_contract:AAPL:150:call:None" # Expiration date is None in mock
    mock_redis_client_fixture.set.assert_any_call(expected_option_key, json.dumps({"symbol": "AAPL", "strike": 150, "option_type": "call"}))
    mock_logger.debug.assert_any_call("Updated option contract for AAPL in Redis.")

    # Ensure the listen task eventually stops due to CancelledError
    listen_task.cancel()
    try:
        await listen_task
    except asyncio.CancelledError:
        pass
    assert client.is_connected is False

@pytest.mark.asyncio
async def test_handle_auth_success(mock_logger):
    """Test handling of successful authentication message."""
    client = TradierWebSocketClient(access_token="test_token")
    await client._handle_message({"msg": "auth", "data": {"status": "ok"}})
    mock_logger.info.assert_called_with("Tradier WebSocket authentication successful.")

@pytest.mark.asyncio
async def test_handle_auth_failure(mock_logger):
    """Test handling of failed authentication message."""
    client = TradierWebSocketClient(access_token="test_token")
    await client._handle_message({"msg": "auth", "data": {"status": "error", "error": "Invalid token"}})
    mock_logger.error.assert_called_with("Tradier WebSocket authentication failed: Invalid token")

@pytest.mark.asyncio
async def test_handle_error_message(mock_logger):
    """Test handling of error message."""
    client = TradierWebSocketClient(access_token="test_token")
    await client._handle_message({"msg": "error", "data": {"error": "Rate limit exceeded"}})
    mock_logger.error.assert_called_with("Tradier WebSocket error: Rate limit exceeded")

@pytest.mark.asyncio
async def test_ping_task_sends_ping(mock_websocket_connection, mock_logger):
    """Test that the ping task sends ping messages."""
    client = TradierWebSocketClient(access_token="test_token")
    client.connection = mock_websocket_connection
    client.is_connected = True
    
    # Start ping task and let it run briefly
    ping_task = asyncio.create_task(client._send_ping())
    await asyncio.sleep(0.01) # Allow time for first ping
    ping_task.cancel()
    try:
        await ping_task
    except asyncio.CancelledError:
        pass

    mock_websocket_connection.send.assert_called_once_with(json.dumps({"jsonrpc": "2.0", "msg": "ping"}))
    # The debug log for "Received ping" is in _handle_message, not _send_ping.
    # We are testing _send_ping, so we only assert on the send call.