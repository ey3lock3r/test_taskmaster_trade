from pydantic_settings import BaseSettings, SettingsConfigDict # Import SettingsConfigDict
import os

class Settings(BaseSettings):
    """Application configuration settings."""
    
    app_name: str = "AlgoTraderPy"
    debug: bool = False
    testing: bool = False # Added for test environment detection
    database_url: str = "sqlite:///./algotrader.db"
    tradier_api_key: str = "" # This might be a developer key, not user access token
    tradier_client_id: str = "" # Added for Tradier OAuth 2.0
    tradier_client_secret: str = "" # Added for Tradier OAuth 2.0
    tradier_base_url: str = "https://sandbox.tradier.com/v1/" # Default to sandbox URL
    tradier_account_id: str = ""

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

    # API Keys for external services (if applicable)
    perplexity_api_key: str = ""
    google_api_key: str = ""
    openrouter_api_key: str = ""
    
    # Encryption Key
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "QTj1rf50KEAeygc0dw512gM8X6ACumCWXowRHES64eE=") # Provide a default key for testing

    model_config = SettingsConfigDict(env_file=".env", extra="ignore") # Configure model settings

settings = Settings()