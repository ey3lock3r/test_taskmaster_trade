import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from .api.routes import router as api_router
from .api.middleware import AuthMiddleware
from src.database import create_db_and_tables, get_session, engine
from src.models.bot_instance import BotInstance
from src.services.bot_service import BotService
from sqlmodel import SQLModel # Import SQLModel

# Load environment variables from .env file
load_dotenv()

import logging
from contextlib import asynccontextmanager
 
# Configure logging for the application
logging.basicConfig(level=logging.WARNING) # Set default logging level to WARNING
# logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR) # Deactivate SQLAlchemy engine logs
logger = logging.getLogger(__name__)

def create_app(db_engine=None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Context manager for application startup and shutdown events.
        Creates database tables on startup.
        """
        if not db_engine: # Only create tables if a specific engine is not provided (i.e., not in a test environment)
            logger.info("Creating tables on application startup...")
            create_db_and_tables()
            logger.info("Tables created.")
            # Initialize bot status in the database if it doesn't exist
            with next(get_session()) as db:
                bot_service = BotService(db)
                bot_service.get_bot_status() # This will create the record if it doesn't exist
                
                # Load bot parameters
                try:
                    bot_instance = db.query(BotInstance).first()
                    if bot_instance and bot_instance.parameters:
                        logger.info(f"Loaded bot parameters: {bot_instance.parameters}")
                    else:
                        logger.info("No bot parameters found or bot instance not initialized.")
                except Exception as e:
                    logger.error(f"Error loading bot parameters on startup: {e}")
        else:
            logger.info("Skipping table creation on application startup (test environment detected).")
        yield
        logger.info("Shutting down application...")
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
    app.add_middleware(AuthMiddleware, exclude_paths=["/api/v1/token", "/api/v1/register"], db_engine=db_engine or engine)
    
    return app
 
app = create_app()
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)