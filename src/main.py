import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional # Import Optional
from .api.routes import router as api_router
from .api.middleware import AuthMiddleware
from src.database import create_db_and_tables, get_session, engine
from src.models.bot_instance import BotInstance
from src.services.bot_service import BotService
from src.services.broker_service import BrokerService # New import
from sqlmodel import SQLModel, Session # Import Session
from src.config import settings
from fastapi_limiter import FastAPILimiter # Import FastAPILimiter
from src.utils.redis_utils import redis_client, initialize_redis, close_redis_connection # Import Redis utilities
from src.brokerage.tradier_websocket import TradierWebSocketClient # Import TradierWebSocketClient
from src.models.brokerage_connection import BrokerageConnection # Import BrokerageConnection

# Load environment variables from .env file
load_dotenv()

from contextlib import asynccontextmanager
from src.utils.logger import logger, setup_logging # Import setup_logging


def create_app(db_engine=None):
    """
    Factory function to create and configure the FastAPI application.

    Args:
        db_engine: Optional SQLAlchemy engine for database connection.
                   If not provided, a default engine will be used.
                   This is primarily used for dependency injection in testing.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Context manager for application startup and shutdown events.
        Creates database tables on startup, initializes Redis, and connects to Tradier WebSocket.
        """
        global redis_client
        global tradier_ws_client # Declare global for WebSocket client

        if not db_engine: # Only create tables if a specific engine is not provided (i.e., not in a test environment)
            # Tables are now managed by Alembic migrations, so no need to call create_db_and_tables() here.
            # logger.info("Creating tables on application startup...")
            # create_db_and_tables()
            # logger.info("Tables created.")
            logger.info("Database schema managed by Alembic. Skipping create_db_and_tables().")
        else:
            logger.info("Skipping table creation on application startup (test environment detected).")
        
        # Re-configure logger with settings.log_level after settings are loaded
        setup_logging(settings.log_level)

        # Initialize Redis client and ensure it's available for FastAPILimiter
        initialized_redis_client = await initialize_redis()
        
        if initialized_redis_client:
            await FastAPILimiter.init(initialized_redis_client)
            logger.info("FastAPI-Limiter initialized with a valid Redis client.")
        else:
            # This case should ideally be caught by initialize_redis raising an exception,
            # but as a fallback, log a critical error if client is still None.
            logger.critical("Redis client is None after initialization. FastAPILimiter not initialized. Rate limiting will not be active.")
        
        # Initialize brokers
        with Session(db_engine or engine) as session:
            broker_service = BrokerService(session)
            broker_service.initialize_brokers()
            logger.info("Brokers initialized successfully.")

        # Initialize and connect to Tradier WebSocket
        with Session(db_engine or engine) as session: # This session is for Tradier WebSocket, not broker initialization
            # For simplicity, get the first brokerage connection. In a real app, this would be user-specific.
            connection = session.query(BrokerageConnection).first()
            if connection and connection.access_token and connection.broker:
                # Pass the streaming_url from the associated Broker model
                tradier_ws_client = TradierWebSocketClient(
                    access_token=connection.decrypt_access_token(),
                    websocket_url=connection.broker.streaming_url # Use streaming_url from Broker
                )
                await tradier_ws_client.connect()
                if tradier_ws_client.is_connected:
                    # Subscribe to quotes and options for a few symbols
                    await tradier_ws_client.subscribe(symbols=["SPY", "AAPL"], channels=["quote", "option"])
                    # Start listening in a background task
                    import asyncio # Ensure asyncio is imported if not already
                    asyncio.create_task(tradier_ws_client.listen_for_messages())
                    logger.info("Tradier WebSocket client initialized and listening.")
                else:
                    logger.warning("Tradier WebSocket client failed to connect.")
            else:
                logger.warning("No brokerage connection found, access token missing, or broker not associated for Tradier WebSocket.")
            
        logger.info("Application lifespan context entered.")
        yield
        logger.info("Shutting down application...")
        if tradier_ws_client and tradier_ws_client.is_connected:
            await tradier_ws_client.disconnect() # Close Tradier WebSocket connection
        await close_redis_connection() # Close Redis connection
        # No specific shutdown logic for tables needed here as they are managed by test fixtures
        
    app = FastAPI(title="AlgoTraderPy", lifespan=lifespan)
    
    # Add exception handler for HTTPException
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    app.include_router(api_router, prefix="/api/v1")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,  # Use configured origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    app.add_middleware(AuthMiddleware, exclude_paths=["/api/v1/token", "/api/v1/register", "/api/v1/test"], db_engine=db_engine or engine)
    
    # Initialize FastAPI-Limiter within the lifespan context
    # The @app.on_event("startup") decorator is deprecated in favor of lifespan
    # await FastAPILimiter.init(redis_client) # This is now handled in lifespan
    # logger.info("FastAPI-Limiter initialized.")

    return app
 
tradier_ws_client: Optional[TradierWebSocketClient] = None # Global WebSocket client instance

app = create_app()
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)