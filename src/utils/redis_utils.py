import redis.asyncio as redis
from typing import Optional
from datetime import datetime, timezone
from src.config import settings
from src.utils.logger import logger

redis_client: Optional[redis.Redis] = None

import asyncio

async def initialize_redis(retries: int = 5, delay: int = 2) -> redis.Redis:
    """
    Initializes the global Redis client and returns it.
    Includes retry logic to wait for Redis server to become available.
    """
    global redis_client
    for i in range(retries):
        logger.info(f"Attempt {i+1}/{retries}: Connecting to Redis at {settings.redis_url}...")
        try:
            redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
            await redis_client.ping()
            logger.info("Successfully connected to Redis.")
            return redis_client
        except redis.ConnectionError as e:
            logger.warning(f"Could not connect to Redis: {e}. Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    logger.critical(f"Failed to connect to Redis after {retries} attempts. Ensure Redis server is running.")
    raise redis.ConnectionError(f"Failed to connect to Redis after {retries} attempts.")

async def close_redis_connection():
    """Closes the global Redis client connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed.")

async def add_jti_to_blacklist(jti: str, expires_at: datetime):
    """Adds a JTI to the Redis blacklist."""
    if redis_client:
        ttl = (expires_at - datetime.now(timezone.utc)).total_seconds()
        if ttl > 0:
            await redis_client.setex(f"blacklist:{jti}", int(ttl), "blacklisted")
            logger.info(f"JTI {jti} added to blacklist with TTL {int(ttl)}s.")
        else:
            logger.warning(f"JTI {jti} not added to blacklist: Token already expired.")
    else:
        logger.error("Redis client not initialized. Cannot blacklist JTI.")

async def is_jti_blacklisted(jti: str) -> bool:
    """Checks if a JTI is in the Redis blacklist."""
    if redis_client:
        is_blacklisted = await redis_client.exists(f"blacklist:{jti}")
        if is_blacklisted:
            logger.warning(f"JTI {jti} found in blacklist.")
        return bool(is_blacklisted)
    else:
        logger.error("Redis client not initialized. Cannot check JTI blacklist.")
        return False