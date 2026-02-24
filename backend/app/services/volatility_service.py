"""
Volatility Service for IV Rank, IV Percentile, Historical Volatility,
and volatility-based strategy recommendations.

Architecture: TastyTrade API (primary) → Local calculation (fallback)

TastyTrade provides pre-calculated IVR, IVP, and IV index for free,
eliminating the need to compute these from raw options chains.
Local calculation uses HV-proxy for IVR/IVP when TastyTrade is unavailable.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.redis import cache
from app.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

CACHE_PREFIX_VOL = "vol"


class VolatilityService:
    """Calculates IV Rank, IV Percentile, HV, and volatility signals per ticker."""

    def __init__(self, market_data: MarketDataService):
        self.market_data = market_data
        self._tt_session_token: Optional[str] = None
        self._tt_token_expiry: Optional[datetime] = None

    # ─── Public API ───────────────────────────────────────────────

    async def get_volatility_snapshot(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get complete volatility snapshot for a symbol.
        Tries TastyTrade first for pre-calculated metrics, falls back to local calc.
        """
        cache_key = f"{CACHE_PREFIX_VOL}:snapshot:{symbol.upper()}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # Try TastyTrade first (pre-calculated IVR/IVP/IV)
        snapshot = await self._tastytrade_snapshot(symbol)

        if snapshot is None:
            # Fallback: compute locally from options chain + price history
            snapshot = await self._local_snapshot(symbol)

        if snapshot is None:
            return None

        await cache.set(cache_key, snapshot, ttl=settings.CACHE_TTL_SIGNALS)
        return snapshot

    async def get_volatility_scanner(
        self,
        symbols: List[str]
    ) -> List[Dict[str, Any]]:
        """Run volatility scanner across multiple symbols. Returns sorted by IVR."""
        import asyncio
        tasks = [self.get_volatility_snapshot(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        snapshots = []
        for result in results:
            if isinstance(result, dict):
                snapshots.append(result)

        snapshots.sort(key=lambda x: x.get("iv_rank") or 0, reverse=True)
        return snapshots

    # ─── TastyTrade Integration ───────────────────────────────────

    async def _tastytrade_snapshot(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch pre-calculated IV metrics from TastyTrade API."""
        if not settings.TASTYTRADE_USERNAME or not settings.TASTYTRADE_PASSWORD:
            return None

        try:
            token = await self._get_tt_session_token()
            if not token:
                return None

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.TASTYTRADE_API_URL}/market-metrics",
                    params={"symbols": symbol.upper()},
                    headers={"Authorization": token},
                )
                resp.raise_for_status()
                data = resp.json()

            items = data.get("data", {}).get("items", [])
            if not items:
                return None

            metrics = items[0]

            current_iv = metrics.get("implied-volatility-index")
            ivr = metrics.get("implied-volatility-rank")
            ivp = metrics.get("implied-volatility-percentile")
            hv_30 = metrics.get("historical-volatility-30-day")
            hv_60 = metrics.get("historical-volatility-60-day")
            iv_30 = metrics.get("implied-volatility-30-day")

            if current_iv is None:
                return None

            hv_iv_ratio = round(hv_30 / current_iv, 4) if hv_30 and current_iv > 0 else None
            divergence = round(current_iv - hv_30, 4) if hv_30 else None

            # IVR/IVP from TastyTrade are 0-1 decimals, convert to 0-100 scale
            ivr_pct = round(ivr * 100, 2) if ivr is not None else None
            ivp_pct = round(ivp * 100, 2) if ivp is not None else None

            strategy_rec = self._recommend_strategy(ivr_pct, ivp_pct, hv_iv_ratio)

            return {
                "symbol": symbol.upper(),
                "current_iv": round(current_iv, 4),
                "iv_30d": round(iv_30, 4) if iv_30 else None,
                "iv_rank": ivr_pct,
                "iv_percentile": ivp_pct,
                "hv_30": round(hv_30, 4) if hv_30 else None,
                "hv_60": round(hv_60, 4) if hv_60 else None,
                "hv_iv_ratio": hv_iv_ratio,
                "hv_iv_divergence": divergence,
                "strategy_recommendation": strategy_rec,
                "data_source": "tastytrade",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except httpx.HTTPStatusError as e:
            logger.warning(f"TastyTrade API error for {symbol}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.warning(f"TastyTrade fetch failed for {symbol}: {e}")
            return None

    async def _get_tt_session_token(self) -> Optional[str]:
        """Authenticate with TastyTrade and return session token. Caches token."""
        if (
            self._tt_session_token
            and self._tt_token_expiry
            and datetime.utcnow() < self._tt_token_expiry
        ):
            return self._tt_session_token

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{settings.TASTYTRADE_API_URL}/sessions",
                    json={
                        "login": settings.TASTYTRADE_USERNAME,
                        "password": settings.TASTYTRADE_PASSWORD,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            self._tt_session_token = data["data"]["session-token"]
            # Tokens last 24h; refresh at 23h to avoid edge cases
            self._tt_token_expiry = datetime.utcnow() + timedelta(hours=23)
            return self._tt_session_token

        except Exception as e:
            logger.error(f"TastyTrade auth failed: {e}")
            self._tt_session_token = None
            self._tt_token_expiry = None
            return None

    # ─── Local Fallback Calculation ───────────────────────────────

    async def _local_snapshot(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Compute volatility snapshot locally from options chain + price history."""
        chain = await self.market_data.get_options_chain(symbol)
        history = await self.market_data.get_historical_prices(symbol, days=365)

        if not chain or not history:
            logger.warning(f"Insufficient data for local vol snapshot: {symbol}")
            return None

        current_iv = self._extract_atm_iv(chain)
        if current_iv is None:
            return None

        iv_history = self._build_iv_history(history)
        hv_30 = self.calculate_historical_volatility(history, period=30)
        hv_60 = self.calculate_historical_volatility(history, period=60)

        ivr = self.calculate_iv_rank(current_iv, iv_history)
        ivp = self.calculate_iv_percentile(current_iv, iv_history)

        hv_iv_ratio = round(hv_30 / current_iv, 4) if current_iv > 0 and hv_30 else None
        divergence = round(current_iv - hv_30, 4) if hv_30 else None

        strategy_rec = self._recommend_strategy(ivr, ivp, hv_iv_ratio)

        return {
            "symbol": symbol.upper(),
            "current_iv": round(current_iv, 4),
            "iv_30d": None,
            "iv_rank": round(ivr, 2) if ivr is not None else None,
            "iv_percentile": round(ivp, 2) if ivp is not None else None,
            "hv_30": round(hv_30, 4) if hv_30 else None,
            "hv_60": round(hv_60, 4) if hv_60 else None,
            "hv_iv_ratio": hv_iv_ratio,
            "hv_iv_divergence": divergence,
            "strategy_recommendation": strategy_rec,
            "data_source": "local",
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ─── Core Calculations ───────────────────────────────────────

    @staticmethod
    def calculate_iv_rank(
        current_iv: float,
        iv_history: List[float]
    ) -> Optional[float]:
        """
        IV Rank: where current IV sits in its 52-week range.
        IVR = (Current_IV - 52wk_Low) / (52wk_High - 52wk_Low) * 100

        IVR > 50 = options are expensive -> sell premium
        IVR < 30 = options are cheap -> buy premium
        """
        if not iv_history or len(iv_history) < 20:
            return None

        iv_high = max(iv_history)
        iv_low = min(iv_history)

        if iv_high == iv_low:
            return 50.0

        ivr = (current_iv - iv_low) / (iv_high - iv_low) * 100
        return max(0.0, min(100.0, ivr))

    @staticmethod
    def calculate_iv_percentile(
        current_iv: float,
        iv_history: List[float]
    ) -> Optional[float]:
        """
        IV Percentile: % of trading days where IV was BELOW current level.
        More robust than IVR -- not distorted by single-day spikes.

        IVP > 60 = options are historically expensive
        IVP < 30 = options are historically cheap
        """
        if not iv_history or len(iv_history) < 20:
            return None

        days_below = sum(1 for iv in iv_history if iv < current_iv)
        return (days_below / len(iv_history)) * 100

    @staticmethod
    def calculate_historical_volatility(
        price_history: List[Dict[str, Any]],
        period: int = 30
    ) -> Optional[float]:
        """
        Historical (Realized) Volatility using close-to-close log returns.
        Annualized: HV = stdev(daily_returns) * sqrt(252)
        """
        if not price_history or len(price_history) < period + 1:
            return None

        recent = price_history[-period - 1:]
        closes = [d["close"] for d in recent if d.get("close")]

        if len(closes) < period + 1:
            return None

        log_returns = []
        for i in range(1, len(closes)):
            if closes[i] > 0 and closes[i - 1] > 0:
                log_returns.append(math.log(closes[i] / closes[i - 1]))

        if len(log_returns) < 5:
            return None

        mean = sum(log_returns) / len(log_returns)
        variance = sum((r - mean) ** 2 for r in log_returns) / (len(log_returns) - 1)
        daily_vol = math.sqrt(variance)
        annualized = daily_vol * math.sqrt(252)

        return annualized

    # ─── Helper Methods ──────────────────────────────────────────

    @staticmethod
    def _extract_atm_iv(chain: Dict[str, Any]) -> Optional[float]:
        """
        Extract at-the-money implied volatility from options chain.

        Strategy: Find the strike closest to the underlying price, then average
        the call and put IV at that strike for a cleaner ATM IV estimate.
        If only one side has data, use that.
        """
        calls = chain.get("calls", [])
        puts = chain.get("puts", [])
        underlying_price = chain.get("underlying_price")

        all_options = calls + puts
        if not all_options:
            return None

        # If we have the underlying price, find the closest strike
        if underlying_price and underlying_price > 0:
            # Build a map of strike -> {call_iv, put_iv}
            strike_ivs: Dict[float, Dict[str, float]] = {}
            for opt in calls:
                strike = opt.get("strike")
                iv = opt.get("implied_volatility")
                if strike and iv and iv > 0:
                    strike_ivs.setdefault(strike, {})["call"] = iv
            for opt in puts:
                strike = opt.get("strike")
                iv = opt.get("implied_volatility")
                if strike and iv and iv > 0:
                    strike_ivs.setdefault(strike, {})["put"] = iv

            if not strike_ivs:
                return None

            # Find the strike closest to underlying price
            atm_strike = min(strike_ivs.keys(), key=lambda s: abs(s - underlying_price))
            atm_data = strike_ivs[atm_strike]

            # Average call and put IV at ATM strike
            ivs = [v for v in atm_data.values()]
            return sum(ivs) / len(ivs)

        # No underlying price: use volume-weighted average of near-ATM options
        options_with_iv = [
            o for o in all_options
            if o.get("implied_volatility") and o["implied_volatility"] > 0
        ]
        if not options_with_iv:
            return None

        # Sort by volume (higher volume = more representative of ATM)
        options_with_iv.sort(key=lambda o: o.get("volume", 0), reverse=True)
        top = options_with_iv[:4]
        return sum(o["implied_volatility"] for o in top) / len(top)

    @staticmethod
    def _build_iv_history(price_history: List[Dict[str, Any]]) -> List[float]:
        """
        Build approximate IV history from historical price data using rolling HV.

        Since free-tier APIs don't provide historical IV, we use rolling 30-day
        HV as a proxy. For production accuracy, use ORATS or iVolatility.
        """
        if len(price_history) < 60:
            return []

        iv_proxy = []
        for i in range(30, len(price_history)):
            window = price_history[i - 30:i]
            hv = VolatilityService.calculate_historical_volatility(window, period=29)
            if hv is not None:
                iv_proxy.append(hv)

        return iv_proxy

    @staticmethod
    def _recommend_strategy(
        ivr: Optional[float],
        ivp: Optional[float],
        hv_iv_ratio: Optional[float]
    ) -> Dict[str, Any]:
        """Recommend strategy based on volatility signals."""
        if ivr is None:
            return {"action": "insufficient_data", "confidence": "low"}

        if ivr >= 50:
            action = "sell_premium"
            strategies = ["iron_condor", "strangle", "credit_spread"]
            confidence = "high" if ivr >= 70 else "medium"
        elif ivr <= 20:
            action = "buy_premium"
            strategies = ["long_straddle", "debit_spread", "long_call_put"]
            confidence = "medium"
        else:
            action = "neutral"
            strategies = ["directional_spread", "calendar_spread"]
            confidence = "low"

        # Boost confidence if HV/IV divergence confirms
        if hv_iv_ratio is not None:
            if action == "sell_premium" and hv_iv_ratio < 0.8:
                confidence = "high"
            elif action == "buy_premium" and hv_iv_ratio > 1.2:
                confidence = "high"

        return {
            "action": action,
            "strategies": strategies,
            "confidence": confidence,
            "rationale": f"IVR: {ivr:.0f}, IVP: {ivp:.0f}" if ivp else f"IVR: {ivr:.0f}",
        }
