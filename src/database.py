import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
from src.config import settings
from src.utils.logger import logger # Import the logger

load_dotenv()

DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    logger.info("Attempting to create database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables creation process completed.")

def get_session():
    with Session(engine) as session:
        yield session