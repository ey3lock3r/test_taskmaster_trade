from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import secrets # Import secrets module
from typing import List # Import List for type hinting
# from src.utils.logger import logger # Import the custom logger

class Settings(BaseSettings):
    """Application configuration settings."""
    
    app_name: str = "AlgoTraderPy"
    debug: bool = False
    testing: bool = False # Added for test environment detection
    log_level: str = "INFO" # New setting for logging level
    database_url: str = "sqlite:///./algotrader.db"
    tradier_api_key: str = "" # This might be a developer key, not user access token
    tradier_client_id: str = "" # Added for Tradier OAuth 2.0
    tradier_client_secret: str = "" # Added for Tradier OAuth 2.0
    tradier_base_url: str = "https://sandbox.tradier.com/v1/" # Default to sandbox URL
    tradier_websocket_url: str = "wss://ws.tradier.com/v1/websocket" # Default to sandbox WebSocket URL
    tradier_account_id: str = ""

    # Redis Settings
    redis_url: str = "redis://localhost:6379/0" # Default Redis URL

    # PMCC Strategy Parameters
    pmcc_target_delta: float = 0.75
    pmcc_min_dte_long: int = 90
    pmcc_max_dte_long: int = 730
    pmcc_min_delta_short: float = 0.2
    pmcc_max_delta_short: float = 0.4
    pmcc_max_dte_short: int = 45
    pmcc_max_net_debit: float = 500.0
    pmcc_risk_free_rate: float = 0.05

    # JWT Settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    jwt_refresh_expiration_days: int = 7

    # CORS Settings
    allowed_origins: List[str] = ["http://localhost:3000"] # Default to frontend development URL

    # API Keys for external services (if applicable)
    perplexity_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    
    # Encryption Key
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "QTj1rf50KEAeygc0dw512gM8X6ACumCWXowRHES64eE=") # Provide a default key for testing

    model_config = SettingsConfigDict(env_file=".env", extra="ignore") # Configure model settings

    def __post_init__(self):
        """Perform validation after settings are loaded."""
        # Import logger here to avoid circular dependency
        from src.utils.logger import logger
        self._check_jwt_secret_key_strength(logger)

    def _check_jwt_secret_key_strength(self, logger):
        """
        Checks if the JWT_SECRET_KEY is strong enough.
        Logs a critical warning if it's weak or missing.
        """
        min_length = 32  # Recommended minimum length for HS256
        if not self.jwt_secret_key:
            logger.critical("JWT_SECRET_KEY is not set. Please set a strong secret key in your .env file.")
            # Optionally generate a strong key if not in production
            if not self.testing and not self.debug:
                logger.critical("For production, a strong, unique JWT_SECRET_KEY is mandatory. Exiting.")
                exit(1)
            else:
                generated_key = secrets.token_urlsafe(min_length)
                logger.warning(f"Generating a temporary JWT_SECRET_KEY for development/testing: {generated_key}")
                self.jwt_secret_key = generated_key
        elif len(self.jwt_secret_key) < min_length:
            logger.critical(f"JWT_SECRET_KEY is too short ({len(self.jwt_secret_key)} chars). "
                            f"It should be at least {min_length} characters for security. "
                            "Please generate a stronger key.")
            if not self.testing and not self.debug:
                logger.critical("For production, a strong, unique JWT_SECRET_KEY is mandatory. Exiting.")
                exit(1)
        # Add more complexity checks if desired (e.g., entropy, character types)
        # For simplicity, we'll stick to length for now.

BROKER_CONFIGS = [
    {
        "name": "Tradier Sandbox",
        "base_url": "https://sandbox.tradier.com",
        "streaming_url": "wss://ws.tradier.com", # New field
        "is_live_mode": False # Sandbox mode
    },
    {
        "name": "Tradier",
        "base_url": "https://api.tradier.com",
        "streaming_url": "wss://ws.tradier.com", # New field
        "is_live_mode": True # Live mode
    },
    # Add other brokers as needed
]

settings = Settings()