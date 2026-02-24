"""
Market signals model for cached market-wide signals shared across all users
"""

from sqlalchemy import Column, String, DateTime, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class MarketSignal(Base):
    """Cached market-wide signal (GEX regime, VIX, sector rotation, etc.)"""
    __tablename__ = "market_signals"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Signal Identity
    signal_type = Column(String(50), nullable=False)  # gex_regime, vix_level, sector_rotation, etc.
    symbol = Column(String(20), nullable=True)  # NULL for market-wide, ticker for stock-specific

    # Signal Data
    value = Column(Numeric(precision=16, scale=6), nullable=True)  # Numeric value (GEX, IVR, etc.)
    regime = Column(String(20), nullable=True)  # positive, negative, neutral
    data = Column(JSONB, nullable=False)  # Full signal data

    # Timing
    signal_timestamp = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Indexes for efficient queries
Index("idx_market_signals_type_time", MarketSignal.signal_type, MarketSignal.signal_timestamp.desc())
Index("idx_market_signals_symbol_type", MarketSignal.symbol, MarketSignal.signal_type, MarketSignal.signal_timestamp.desc())
Index("idx_market_signals_type_symbol_time", MarketSignal.signal_type, MarketSignal.symbol, MarketSignal.signal_timestamp, unique=True)
