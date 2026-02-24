"""
User watchlist model for targeted scanning and alerts
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class UserWatchlist(Base):
    """User-configurable watchlist for targeted scanning"""
    __tablename__ = "user_watchlist"

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
    symbol = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)

    # Alert preferences
    alert_on_ivr_above = Column(Integer, default=50)
    alert_on_flow = Column(Boolean, default=True)

    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")


# Indexes
Index("idx_user_watchlist_user_symbol", UserWatchlist.user_id, UserWatchlist.symbol, unique=True)
