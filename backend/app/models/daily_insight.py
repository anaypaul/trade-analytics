"""
Daily insights model for storing generated trade recommendations and alerts
"""

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class DailyInsight(Base):
    """Generated trade recommendation or alert for a user"""
    __tablename__ = "daily_insights"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Insight Classification
    insight_type = Column(String(50), nullable=False)  # morning_brief, trade_setup, position_alert, etc.
    priority = Column(Integer, nullable=False, default=3)  # 1=critical, 2=high, 3=medium, 4=low
    signal_score = Column(Integer, nullable=True)  # 0-100 composite score

    # Content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    action_items = Column(JSONB, nullable=True)  # [{action: "sell put spread", details: {...}}]

    # Context
    related_symbol = Column(String(20), nullable=True)
    related_position_id = Column(UUID(as_uuid=True), nullable=True)
    strategy_type = Column(String(50), nullable=True)  # credit_spread, iron_condor, straddle, etc.

    # Signal Attribution
    signals_triggered = Column(JSONB, nullable=True)  # [{signal: "IVR", value: 72, tier: 1}, ...]
    screening_template = Column(String(50), nullable=True)  # Which template generated this

    # Metadata
    metadata_json = Column("metadata", JSONB, nullable=True)  # Flexible: strike, expiry, delta, etc.

    # Tracking
    is_dismissed = Column(Boolean, default=False, nullable=False)
    is_acted_upon = Column(Boolean, default=False, nullable=False)
    outcome_pnl = Column(Numeric(precision=12, scale=2), nullable=True)  # Actual P&L if acted upon

    # Timing
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")


# Indexes for efficient queries
Index("idx_daily_insights_user_priority", DailyInsight.user_id, DailyInsight.priority, DailyInsight.created_at.desc())
Index("idx_daily_insights_user_type", DailyInsight.user_id, DailyInsight.insight_type, DailyInsight.created_at.desc())
Index("idx_daily_insights_symbol", DailyInsight.related_symbol, DailyInsight.created_at.desc())
Index("idx_daily_insights_active", DailyInsight.user_id, DailyInsight.is_dismissed, DailyInsight.expires_at)
Index("idx_daily_insights_score", DailyInsight.user_id, DailyInsight.signal_score.desc(), DailyInsight.created_at.desc())
