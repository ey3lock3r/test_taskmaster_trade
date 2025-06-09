import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import create_db_and_tables, engine
from sqlmodel import SQLModel, Session
from src.models.user import User
from src.models.session import Session as DBSession
from src.models.brokerage_connection import BrokerageConnection
from src.models.bot_instance import BotInstance
from src.models.bot_status import BotStatus
from src.models.trade_order import TradeOrder
from src.models.position import Position
from src.models.strategy_definition import StrategyDefinition
from src.models.strategy_parameters import StrategyParameter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    logger.info("Attempting to drop all tables...")
    try:
        # Drop all tables
        SQLModel.metadata.drop_all(engine)
        logger.info("All tables dropped successfully.")
    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        # If tables don't exist, drop_all might raise an error, but we want to proceed
        pass

    logger.info("Attempting to create all tables...")
    try:
        # Create all tables
        create_db_and_tables()
        logger.info("All tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        sys.exit(1) # Exit if table creation fails

if __name__ == "__main__":
    reset_database()