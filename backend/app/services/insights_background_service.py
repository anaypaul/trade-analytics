"""
Insights Background Service

Handles periodic market data sync and signal calculation for the
Daily Options Insights engine. Runs as scheduled jobs via APScheduler.

Jobs:
  - Volatility scan: refreshes IVR/IVP for watchlist (every 15 min, market hours)
  - Market regime: updates VIX + regime classification (every 5 min, market hours)
  - Daily insights generation: produces trade setups based on signals
"""

import logging
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.redis import cache
from app.core.database import get_db
from app.core.security import DEMO_USER_ID
from app.models.daily_insight import DailyInsight
from app.models.market_signal import MarketSignal
from app.models.user_watchlist import UserWatchlist
from app.services.market_data_service import MarketDataService
from app.services.volatility_service import VolatilityService

logger = logging.getLogger(__name__)


class InsightsBackgroundService:
    """Orchestrates background jobs for the insights engine."""

    def __init__(self):
        self.market_data = MarketDataService()
        self.vol_service = VolatilityService(self.market_data)

    async def run_market_regime_update(self) -> Dict[str, Any]:
        """
        Fetch VIX and classify current market regime.
        Stores result as a MarketSignal for the API to serve.
        """
        try:
            vix_data = await self.market_data.get_vix()
            if not vix_data:
                return {"success": False, "message": "Failed to fetch VIX data"}

            vix_level = vix_data.get("price", 0)

            # Classify regime based on VIX thresholds
            if vix_level < 15:
                regime = "low_vol"
            elif vix_level < 20:
                regime = "normal"
            elif vix_level < 25:
                regime = "elevated"
            elif vix_level < 30:
                regime = "high"
            else:
                regime = "extreme"

            # Position sizing recommendation based on VIX
            if vix_level < 20:
                position_pct = 100
            elif vix_level < 25:
                position_pct = 75
            elif vix_level < 30:
                position_pct = 50
            else:
                position_pct = 25

            signal_data = {
                "vix_level": vix_level,
                "vix_change": vix_data.get("change", 0),
                "vix_change_pct": vix_data.get("change_pct", 0),
                "regime": regime,
                "position_size_pct": position_pct,
                "spy_price": vix_data.get("spy_price"),
            }

            # Store in Redis for fast API access
            await cache.set("insights:market_regime", signal_data, ttl=600)

            # Persist to DB
            async for db in get_db():
                signal = MarketSignal(
                    signal_type="market_regime",
                    symbol=None,
                    value=vix_level,
                    regime=regime,
                    data=signal_data,
                    signal_timestamp=datetime.utcnow(),
                )
                db.add(signal)
                await db.commit()

            logger.info(f"Market regime updated: {regime} (VIX={vix_level:.1f})")
            return {"success": True, "regime": regime, "vix": vix_level}

        except Exception as e:
            logger.error(f"Market regime update failed: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    async def run_volatility_scan(self) -> Dict[str, Any]:
        """
        Scan watchlist symbols for IVR/IVP and cache results.
        """
        try:
            symbols = await self._get_scan_symbols()
            if not symbols:
                return {"success": True, "scanned": 0, "message": "No symbols to scan"}

            snapshots = await self.vol_service.get_volatility_scanner(symbols)

            # Cache the full scan result for the API
            await cache.set("insights:vol_scanner", snapshots, ttl=settings.CACHE_TTL_SIGNALS)

            # Store individual symbol signals in DB
            async for db in get_db():
                for snap in snapshots:
                    signal = MarketSignal(
                        signal_type="volatility_snapshot",
                        symbol=snap["symbol"],
                        value=snap.get("iv_rank"),
                        regime=snap.get("strategy_recommendation", {}).get("action"),
                        data=snap,
                        signal_timestamp=datetime.utcnow(),
                    )
                    db.add(signal)
                await db.commit()

            logger.info(f"Volatility scan completed: {len(snapshots)}/{len(symbols)} symbols")
            return {"success": True, "scanned": len(snapshots), "total": len(symbols)}

        except Exception as e:
            logger.error(f"Volatility scan failed: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    async def run_daily_insights_generation(self) -> Dict[str, Any]:
        """
        Generate daily trade insights based on latest signals.
        Combines volatility data with market regime to produce actionable setups.
        """
        try:
            # Get latest scan data
            snapshots = await cache.get("insights:vol_scanner")
            regime_data = await cache.get("insights:market_regime")

            if not snapshots:
                return {"success": False, "message": "No volatility data available"}

            regime = regime_data.get("regime", "normal") if regime_data else "normal"
            insights_created = 0

            async for db in get_db():
                for snap in snapshots:
                    insight = self._generate_insight_from_snapshot(snap, regime)
                    if insight:
                        db.add(insight)
                        insights_created += 1

                if insights_created > 0:
                    await db.commit()

            logger.info(f"Generated {insights_created} daily insights")
            return {"success": True, "insights_created": insights_created}

        except Exception as e:
            logger.error(f"Insights generation failed: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    # ─── Helpers ──────────────────────────────────────────────────

    async def _get_scan_symbols(self) -> List[str]:
        """Get symbols to scan: user watchlist + default watchlist."""
        symbols = set()

        # Default watchlist
        defaults = settings.INSIGHTS_DEFAULT_WATCHLIST.split(",")
        symbols.update(s.strip().upper() for s in defaults if s.strip())

        # User watchlist from DB
        try:
            async for db in get_db():
                from sqlalchemy import select
                result = await db.execute(
                    select(UserWatchlist.symbol).where(
                        UserWatchlist.user_id == DEMO_USER_ID
                    )
                )
                user_symbols = result.scalars().all()
                symbols.update(s.upper() for s in user_symbols)
        except Exception as e:
            logger.warning(f"Failed to load user watchlist: {e}")

        return list(symbols)

    # TODO(human): Implement the insight generation logic
    def _generate_insight_from_snapshot(
        self,
        snapshot: Dict[str, Any],
        market_regime: str,
    ) -> Optional[DailyInsight]:
        """
        Generate a DailyInsight from a volatility snapshot.

        Decides whether a symbol's current volatility state warrants
        a trade setup recommendation, and if so, what kind.
        Returns a DailyInsight model instance, or None to skip.
        """
        pass
