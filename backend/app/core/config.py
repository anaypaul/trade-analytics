"""
Application configuration settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Trading Analytics"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # Robinhood
    ROBINHOOD_USERNAME: Optional[str] = None
    ROBINHOOD_PASSWORD: Optional[str] = None
    
    # Cache settings
    CACHE_TTL_POSITIONS: int = 300  # 5 minutes
    CACHE_TTL_ORDERS: int = 3600   # 1 hour
    CACHE_TTL_ANALYSIS: int = 1800  # 30 minutes
    
    # WebSocket
    WS_MAX_CONNECTIONS: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # API limits
    MAX_POSITIONS_PER_REQUEST: int = 1000
    MAX_ORDERS_PER_REQUEST: int = 500

    # Market Data APIs (Insights Feature)
    TRADIER_API_KEY: Optional[str] = None
    TRADIER_BASE_URL: str = "https://api.tradier.com/v1"
    POLYGON_API_KEY: Optional[str] = None
    UNUSUAL_WHALES_API_KEY: Optional[str] = None

    # TastyTrade API (pre-calculated IVR, IVP, IV index)
    TASTYTRADE_USERNAME: Optional[str] = None
    TASTYTRADE_PASSWORD: Optional[str] = None
    TASTYTRADE_API_URL: str = "https://api.tastyworks.com"

    # Insights Configuration
    CACHE_TTL_MARKET_DATA: int = 300  # 5 minutes
    CACHE_TTL_SIGNALS: int = 900  # 15 minutes
    CACHE_TTL_INSIGHTS: int = 3600  # 1 hour
    INSIGHTS_DEFAULT_WATCHLIST: str = "SPY,QQQ,IWM,AAPL,TSLA,NVDA,AMZN,META,MSFT,GOOGL"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()