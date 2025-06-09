import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.brokerage.tradier_adapter import TradierAdapter
from src.models.brokerage_connection import BrokerageConnection
import json

@pytest.fixture
def mock_connection():
    """Mocks a BrokerageConnection object."""
    conn = MagicMock(spec=BrokerageConnection)
    conn.decrypt_access_token.return_value = "mock_access_token"
    conn.decrypt_refresh_token.return_value = "mock_refresh_token"
    return conn

@pytest.fixture(autouse=True)
def mock_redis_client_fixture():
    """Mocks the global redis_client for each test."""
    with patch('src.brokerage.tradier_adapter.redis_client', new_callable=AsyncMock) as mock_client:
        yield mock_client

@pytest.fixture(autouse=True)
def mock_requests():
    """Mocks the requests library."""
    with patch('src.brokerage.tradier_adapter.requests') as mock_req:
        yield mock_req

@pytest.mark.asyncio
async def test_get_option_chain_from_cache(mock_redis_client_fixture, mock_requests, mock_connection):
    """Test get_option_chain retrieves data from Redis cache."""
    adapter = TradierAdapter(connection=mock_connection)
    symbol = "AAPL"
    cached_data = [{"strike": 150, "type": "call"}]
    mock_redis_client_fixture.get.return_value = json.dumps(cached_data)

    result = await adapter.get_option_chain(symbol)

    mock_redis_client_fixture.get.assert_called_once_with(f"option_chain:{symbol}")
    mock_requests.get.assert_not_called() # Should not call API if cached
    assert result == cached_data

@pytest.mark.asyncio
async def test_get_option_chain_from_api_and_cache(mock_redis_client_fixture, mock_requests, mock_connection):
    """Test get_option_chain retrieves data from API and caches it."""
    adapter = TradierAdapter(connection=mock_connection)
    symbol = "GOOG"
    api_data = {"options": {"option": [{"strike": 100, "type": "put"}]}}
    
    mock_redis_client_fixture.get.return_value = None # No cached data
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = api_data
    mock_requests.get.return_value = mock_resp

    result = await adapter.get_option_chain(symbol)

    mock_redis_client_fixture.get.assert_called_once_with(f"option_chain:{symbol}")
    mock_requests.get.assert_called_once()
    mock_redis_client_fixture.setex.assert_called_once_with(f"option_chain:{symbol}", 3600, json.dumps(api_data['options']['option']))
    assert result == api_data['options']['option']

@pytest.mark.asyncio
async def test_get_quotes_from_cache(mock_redis_client_fixture, mock_requests, mock_connection):
    """Test get_quotes retrieves data from Redis cache."""
    adapter = TradierAdapter(connection=mock_connection)
    symbols = ["MSFT", "AMZN"]
    cached_data = {"MSFT": {"last": 200}, "AMZN": {"last": 3000}}
    mock_redis_client_fixture.get.return_value = json.dumps(cached_data)

    result = await adapter.get_quotes(symbols)

    mock_redis_client_fixture.get.assert_called_once_with(f"quotes:{','.join(symbols)}")
    mock_requests.get.assert_not_called() # Should not call API if cached
    assert result == cached_data

@pytest.mark.asyncio
async def test_get_quotes_from_api_and_cache(mock_redis_client_fixture, mock_requests, mock_connection):
    """Test get_quotes retrieves data from API and caches it."""
    adapter = TradierAdapter(connection=mock_connection)
    symbols = ["TSLA"]
    api_data = {"quotes": {"quote": [{"symbol": "TSLA", "last": 700}]}}
    
    mock_redis_client_fixture.get.return_value = None # No cached data
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = api_data
    mock_requests.get.return_value = mock_resp

    result = await adapter.get_quotes(symbols)

    mock_redis_client_fixture.get.assert_called_once_with(f"quotes:{','.join(symbols)}")
    mock_requests.get.assert_called_once()
    mock_redis_client_fixture.setex.assert_called_once_with(f"quotes:{','.join(symbols)}", 300, json.dumps({"TSLA": {"symbol": "TSLA", "last": 700}}))
    assert result == {"TSLA": {"symbol": "TSLA", "last": 700}}

@pytest.mark.asyncio
async def test_get_option_chain_no_redis_client(mock_redis_client_fixture, mock_requests, mock_connection):
    """Test get_option_chain when redis_client is None (no caching)."""
    with patch('src.brokerage.tradier_adapter.redis_client', None):
        adapter = TradierAdapter(connection=mock_connection)
        symbol = "MSFT"
        api_data = {"options": {"option": [{"strike": 250, "type": "call"}]}}
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = api_data
        mock_requests.get.return_value = mock_resp

        result = await adapter.get_option_chain(symbol)

        mock_requests.get.assert_called_once()
        mock_redis_client_fixture.get.assert_not_called()
        mock_redis_client_fixture.setex.assert_not_called()
        assert result == api_data['options']['option']

@pytest.mark.asyncio
async def test_get_quotes_no_redis_client(mock_redis_client_fixture, mock_requests, mock_connection):
    """Test get_quotes when redis_client is None (no caching)."""
    with patch('src.brokerage.tradier_adapter.redis_client', None):
        adapter = TradierAdapter(connection=mock_connection)
        symbols = ["NFLX"]
        api_data = {"quotes": {"quote": [{"symbol": "NFLX", "last": 500}]}}
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = api_data
        mock_requests.get.return_value = mock_resp

        result = await adapter.get_quotes(symbols)

        mock_requests.get.assert_called_once()
        mock_redis_client_fixture.get.assert_not_called()
        mock_redis_client_fixture.setex.assert_not_called()
        assert result == {"NFLX": {"symbol": "NFLX", "last": 500}}