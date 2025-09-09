"""
Configuration settings for Cryptocurrency Price Tracker API.
"""

import os
from typing import Dict, Any

class Settings:
    """Application settings."""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./crypto_prices.db")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Cache Configuration
    CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "30"))  # seconds
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # Exchange API Keys (optional)
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    COINBASE_API_KEY: str = os.getenv("COINBASE_API_KEY", "")
    KRAKEN_API_KEY: str = os.getenv("KRAKEN_API_KEY", "")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_exchange_config(cls) -> Dict[str, Any]:
        """Get exchange configuration with API keys."""
        return {
            "binance": {
                "api_key": cls.BINANCE_API_KEY,
                "base_url": "https://api.binance.com/api/v3",
                "rate_limit": 1200  # requests per minute
            },
            "coinbase": {
                "api_key": cls.COINBASE_API_KEY,
                "base_url": "https://api.coinbase.com/v2",
                "rate_limit": 10000  # requests per hour
            },
            "kraken": {
                "api_key": cls.KRAKEN_API_KEY,
                "base_url": "https://api.kraken.com/0/public",
                "rate_limit": 60  # requests per minute
            }
        }

# Global settings instance
settings = Settings()
