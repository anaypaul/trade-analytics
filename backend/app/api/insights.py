"""
Insights API router — daily trade recommendations, volatility scanner,
market regime, watchlist, and signal performance endpoints.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.daily_insight import DailyInsight
from app.models.user_watchlist import UserWatchlist
from app.services.market_data_service import MarketDataService
from app.services.volatility_service import VolatilityService

router = APIRouter(prefix="/insights", tags=["insights"])


def get_market_data_service() -> MarketDataService:
    """Dependency to get MarketDataService instance."""
    return MarketDataService()


def get_volatility_service() -> VolatilityService:
    """Dependency to get VolatilityService instance."""
    mds = MarketDataService()
    return VolatilityService(mds)


# ─── Daily Insights ──────────────────────────────────────────────────


@router.get("/daily")
async def get_daily_insights(
    limit: int = Query(default=20, ge=1, le=100),
    insight_type: Optional[str] = Query(default=None),
    min_score: Optional[int] = Query(default=None, ge=0, le=100),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get today's insights for the current user, sorted by priority and score."""
    query = (
        select(DailyInsight)
        .where(
            and_(
                DailyInsight.user_id == current_user_id,
                DailyInsight.is_dismissed == False,
            )
        )
        .order_by(DailyInsight.priority, DailyInsight.signal_score.desc())
        .limit(limit)
    )

    if insight_type:
        query = query.where(DailyInsight.insight_type == insight_type)
    if min_score is not None:
        query = query.where(DailyInsight.signal_score >= min_score)

    result = await db.execute(query)
    insights = result.scalars().all()

    return {
        "success": True,
        "data": [_serialize_insight(i) for i in insights],
        "count": len(insights),
    }


@router.post("/insights/{insight_id}/dismiss")
async def dismiss_insight(
    insight_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an insight so it no longer appears in the daily feed."""
    result = await db.execute(
        select(DailyInsight).where(
            and_(
                DailyInsight.id == insight_id,
                DailyInsight.user_id == current_user_id,
            )
        )
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    insight.is_dismissed = True
    await db.commit()
    return {"success": True, "message": "Insight dismissed"}


@router.post("/insights/{insight_id}/acted")
async def mark_insight_acted(
    insight_id: uuid.UUID,
    outcome_pnl: Optional[float] = Query(default=None),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Mark an insight as acted upon, optionally with outcome P&L."""
    result = await db.execute(
        select(DailyInsight).where(
            and_(
                DailyInsight.id == insight_id,
                DailyInsight.user_id == current_user_id,
            )
        )
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    insight.is_acted_upon = True
    if outcome_pnl is not None:
        insight.outcome_pnl = outcome_pnl
    await db.commit()
    return {"success": True, "message": "Insight marked as acted upon"}


# ─── Market Overview ─────────────────────────────────────────────────


@router.get("/market/regime")
async def get_market_regime(
    mds: MarketDataService = Depends(get_market_data_service),
):
    """Get current market regime: GEX-based + VIX level + strategy recommendation."""
    vix_data = await mds.get_vix()
    spy_quote = await mds.get_stock_quote("SPY")

    vix_level = vix_data.get("last") if vix_data else None
    spy_price = spy_quote.get("last") if spy_quote else None

    # Determine regime from VIX (GEX calculation requires OI data — Phase 2)
    if vix_level is not None:
        if vix_level < 15:
            regime = "low_vol"
            regime_label = "Low Volatility — Sell Premium"
            position_size_pct = 100
        elif vix_level < 20:
            regime = "normal"
            regime_label = "Normal — Full Size Positions"
            position_size_pct = 100
        elif vix_level < 25:
            regime = "elevated"
            regime_label = "Elevated Vol — Reduce to 75%"
            position_size_pct = 75
        elif vix_level < 30:
            regime = "high"
            regime_label = "High Vol — Reduce to 50%"
            position_size_pct = 50
        else:
            regime = "extreme"
            regime_label = "Extreme Vol — 25% or Pause"
            position_size_pct = 25
    else:
        regime = "unknown"
        regime_label = "Unable to determine — data unavailable"
        position_size_pct = 50

    return {
        "success": True,
        "data": {
            "regime": regime,
            "regime_label": regime_label,
            "vix": vix_level,
            "spy_price": spy_price,
            "position_size_pct": position_size_pct,
            "gex_regime": None,  # Phase 2: calculated from OI data
            "zero_gamma_level": None,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


# ─── Volatility Scanner ─────────────────────────────────────────────


@router.get("/volatility/scanner")
async def volatility_scanner(
    symbols: Optional[str] = Query(
        default=None,
        description="Comma-separated symbols to scan. Defaults to watchlist."
    ),
    min_ivr: Optional[float] = Query(default=None, ge=0, le=100),
    max_ivr: Optional[float] = Query(default=None, ge=0, le=100),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    vol_service: VolatilityService = Depends(get_volatility_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Scan symbols for volatility metrics (IVR, IVP, HV, strategy recommendations).
    Sorted by IV Rank descending — top results are best premium-selling candidates.
    """
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
    else:
        # Use user's watchlist or defaults
        result = await db.execute(
            select(UserWatchlist.symbol).where(
                UserWatchlist.user_id == current_user_id
            )
        )
        watchlist_symbols = [row[0] for row in result.all()]
        symbol_list = watchlist_symbols or settings.INSIGHTS_DEFAULT_WATCHLIST.split(",")

    snapshots = await vol_service.get_volatility_scanner(symbol_list)

    # Apply IVR filters
    if min_ivr is not None:
        snapshots = [s for s in snapshots if (s.get("iv_rank") or 0) >= min_ivr]
    if max_ivr is not None:
        snapshots = [s for s in snapshots if (s.get("iv_rank") or 100) <= max_ivr]

    return {
        "success": True,
        "data": snapshots,
        "count": len(snapshots),
        "filters_applied": {
            "symbols": symbol_list,
            "min_ivr": min_ivr,
            "max_ivr": max_ivr,
        },
    }


@router.get("/volatility/{symbol}")
async def get_symbol_volatility(
    symbol: str,
    vol_service: VolatilityService = Depends(get_volatility_service),
):
    """Get detailed volatility analysis for a single symbol."""
    snapshot = await vol_service.get_volatility_snapshot(symbol)
    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail=f"Volatility data unavailable for {symbol}",
        )

    return {"success": True, "data": snapshot}


# ─── Watchlist ───────────────────────────────────────────────────────


@router.get("/watchlist")
async def get_watchlist(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get user's watchlist."""
    result = await db.execute(
        select(UserWatchlist)
        .where(UserWatchlist.user_id == current_user_id)
        .order_by(UserWatchlist.added_at.desc())
    )
    items = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": str(item.id),
                "symbol": item.symbol,
                "notes": item.notes,
                "alert_on_ivr_above": item.alert_on_ivr_above,
                "alert_on_flow": item.alert_on_flow,
                "added_at": item.added_at.isoformat() if item.added_at else None,
            }
            for item in items
        ],
        "count": len(items),
    }


@router.post("/watchlist")
async def add_to_watchlist(
    symbol: str = Query(..., min_length=1, max_length=20),
    notes: Optional[str] = Query(default=None),
    alert_on_ivr_above: int = Query(default=50, ge=0, le=100),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add a symbol to the user's watchlist."""
    symbol = symbol.upper().strip()

    # Check for duplicate
    existing = await db.execute(
        select(UserWatchlist).where(
            and_(
                UserWatchlist.user_id == current_user_id,
                UserWatchlist.symbol == symbol,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"{symbol} is already in your watchlist",
        )

    item = UserWatchlist(
        user_id=current_user_id,
        symbol=symbol,
        notes=notes,
        alert_on_ivr_above=alert_on_ivr_above,
    )
    db.add(item)
    await db.commit()

    return {
        "success": True,
        "message": f"{symbol} added to watchlist",
        "data": {"id": str(item.id), "symbol": symbol},
    }


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Remove a symbol from the user's watchlist."""
    result = await db.execute(
        delete(UserWatchlist).where(
            and_(
                UserWatchlist.user_id == current_user_id,
                UserWatchlist.symbol == symbol.upper(),
            )
        )
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"{symbol} not found in watchlist")

    return {"success": True, "message": f"{symbol} removed from watchlist"}


# ─── Earnings ────────────────────────────────────────────────────────


@router.get("/earnings")
async def get_earnings_calendar(
    symbols: Optional[str] = Query(default=None),
    mds: MarketDataService = Depends(get_market_data_service),
):
    """Get upcoming earnings dates for symbols."""
    symbol_list = (
        [s.strip().upper() for s in symbols.split(",")]
        if symbols
        else None
    )
    earnings = await mds.get_earnings_calendar(symbol_list)

    return {
        "success": True,
        "data": earnings,
        "count": len(earnings),
    }


# ─── Helpers ─────────────────────────────────────────────────────────


def _serialize_insight(insight: DailyInsight) -> Dict[str, Any]:
    """Serialize a DailyInsight model to dict."""
    return {
        "id": str(insight.id),
        "insight_type": insight.insight_type,
        "priority": insight.priority,
        "signal_score": insight.signal_score,
        "title": insight.title,
        "description": insight.description,
        "action_items": insight.action_items,
        "related_symbol": insight.related_symbol,
        "strategy_type": insight.strategy_type,
        "signals_triggered": insight.signals_triggered,
        "screening_template": insight.screening_template,
        "is_acted_upon": insight.is_acted_upon,
        "outcome_pnl": float(insight.outcome_pnl) if insight.outcome_pnl else None,
        "valid_from": insight.valid_from.isoformat() if insight.valid_from else None,
        "expires_at": insight.expires_at.isoformat() if insight.expires_at else None,
        "created_at": insight.created_at.isoformat() if insight.created_at else None,
    }


# Import settings for default watchlist
from app.core.config import settings
