"""
Signal performance model for tracking historical signal accuracy
"""

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class SignalPerformance(Base):
    """Track how each signal performs over time for continuous improvement"""
    __tablename__ = "signal_performance"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    signal_type = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=True)
    signal_direction = Column(String(10), nullable=True)  # bullish, bearish, neutral
    signal_value = Column(Numeric(precision=16, scale=6), nullable=True)

    # Outcome
    entry_price = Column(Numeric(precision=12, scale=4), nullable=True)
    exit_price = Column(Numeric(precision=12, scale=4), nullable=True)
    pnl = Column(Numeric(precision=12, scale=2), nullable=True)
    pnl_percent = Column(Numeric(precision=8, scale=4), nullable=True)
    holding_period_hours = Column(Integer, nullable=True)
    outcome = Column(String(10), nullable=True)  # win, loss, scratch

    # Context
    market_regime = Column(String(20), nullable=True)  # GEX regime when signal fired
    vix_at_signal = Column(Numeric(precision=8, scale=4), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Indexes
Index("idx_signal_perf_type", SignalPerformance.signal_type, SignalPerformance.created_at.desc())
Index("idx_signal_perf_symbol", SignalPerformance.symbol, SignalPerformance.signal_type, SignalPerformance.created_at.desc())
Index("idx_signal_perf_outcome", SignalPerformance.signal_type, SignalPerformance.outcome)
