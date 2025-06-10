import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, timezone
import sys
import redis.asyncio as redis
from redis.exceptions import ConnectionError
from src.utils.redis_utils import initialize_redis, close_redis_connection, add_jti_to_blacklist, is_jti_blacklisted, redis_client

@pytest.fixture(autouse=True)
def mock_redis_client():
    """Mocks the global redis_client and redis.from_url for each test."""
    with patch('src.utils.redis_utils.redis_client', new_callable=AsyncMock) as mock_global_client, \
         patch('src.utils.redis_utils.redis.from_url', return_value=mock_global_client) as mock_from_url:
        yield mock_global_client

@pytest.mark.asyncio
async def test_initialize_redis_success(mock_redis_client):
    """Test successful Redis client initialization."""
    mock_redis_client.ping.return_value = True
    client = await initialize_redis()
    assert client is not None
    mock_redis_client.ping.assert_called_once()

@pytest.mark.asyncio
async def test_initialize_redis_connection_error(mock_redis_client):
    """Test Redis client initialization failure due to connection error."""
    mock_redis_client.ping.side_effect = ConnectionError("Connection failed")
    with pytest.raises(ConnectionError):
        await initialize_redis()
    assert mock_redis_client.ping.call_count == 5

@pytest.mark.asyncio
async def test_close_redis_connection(mock_redis_client):
    """Test closing the Redis client connection."""
    # Simulate an initialized client by setting the mock
    with patch('src.utils.redis_utils.redis_client', mock_redis_client):
        await close_redis_connection()
        mock_redis_client.close.assert_called_once()

@pytest.mark.asyncio
async def test_add_jti_to_blacklist_success(mock_redis_client):
    """Test adding a JTI to the blacklist successfully."""
    mock_redis_client.setex.return_value = True
    jti = "test_jti"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    await add_jti_to_blacklist(jti, expires_at)
    mock_redis_client.setex.assert_called_once_with(f"blacklist:{jti}", int((expires_at - datetime.now(timezone.utc)).total_seconds()), "blacklisted")

@pytest.mark.asyncio
async def test_add_jti_to_blacklist_already_expired(mock_redis_client):
    """Test adding an already expired JTI to the blacklist."""
    jti = "expired_jti"
    expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    await add_jti_to_blacklist(jti, expires_at)
    mock_redis_client.setex.assert_not_called()

@pytest.mark.asyncio
async def test_add_jti_to_blacklist_no_redis_client():
    """Test adding JTI to blacklist when Redis client is not initialized."""
    with patch('src.utils.redis_utils.redis_client', None):
        jti = "test_jti"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await add_jti_to_blacklist(jti, expires_at)
        # No assertion on mock_redis_client.setex as it's None

@pytest.mark.asyncio
async def test_is_jti_blacklisted_true(mock_redis_client):
    """Test checking if a JTI is blacklisted (returns True)."""
    mock_redis_client.exists.return_value = 1 # Redis returns 1 for existence
    jti = "blacklisted_jti"
    result = await is_jti_blacklisted(jti)
    assert result is True
    mock_redis_client.exists.assert_called_once_with(f"blacklist:{jti}")

@pytest.mark.asyncio
async def test_is_jti_blacklisted_false(mock_redis_client):
    """Test checking if a JTI is blacklisted (returns False)."""
    mock_redis_client.exists.return_value = 0
    jti = "non_blacklisted_jti"
    result = await is_jti_blacklisted(jti)
    assert result is False
    mock_redis_client.exists.assert_called_once_with(f"blacklist:{jti}")

@pytest.mark.asyncio
async def test_is_jti_blacklisted_no_redis_client():
    """Test checking JTI blacklist when Redis client is not initialized."""
    with patch('src.utils.redis_utils.redis_client', None):
        jti = "test_jti"
        result = await is_jti_blacklisted(jti)
        assert result is False
        # No assertion on mock_redis_client.exists as it's None