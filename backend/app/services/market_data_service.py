"""
Market Data Service for fetching options chains, stock prices, earnings, and VIX data.

Uses multiple data sources with fallback:
  - Primary: Tradier API (free with brokerage account)
  - Fallback: yfinance (free, less reliable)
  - VIX/Macro: FRED API (free)

All methods are async with Redis caching.
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.redis import cache

logger = logging.getLogger(__name__)

# Cache key prefixes
CACHE_PREFIX_CHAIN = "mkt:chain"
CACHE_PREFIX_QUOTE = "mkt:quote"
CACHE_PREFIX_HISTORY = "mkt:history"
CACHE_PREFIX_EARNINGS = "mkt:earnings"
CACHE_PREFIX_VIX = "mkt:vix"


class MarketDataService:
    """Fetches and caches external market data from multiple providers."""

    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.close()

    # ─── Stock Quotes ────────────────────────────────────────────────

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock quote. Tries Tradier first, falls back to yfinance."""
        cache_key = f"{CACHE_PREFIX_QUOTE}:{symbol.upper()}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        quote = await self._tradier_get_quote(symbol)
        if not quote:
            quote = await self._yfinance_get_quote(symbol)

        if quote:
            await cache.set(cache_key, quote, ttl=settings.CACHE_TTL_MARKET_DATA)
        return quote

    async def get_stock_quotes_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get quotes for multiple symbols concurrently."""
        tasks = [self.get_stock_quote(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        quotes = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, dict):
                quotes[symbol.upper()] = result
            else:
                logger.warning(f"Failed to fetch quote for {symbol}: {result}")
        return quotes

    # ─── Options Chains ──────────────────────────────────────────────

    async def get_options_chain(
        self,
        symbol: str,
        expiration: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get options chain for a symbol. Returns calls and puts with Greeks."""
        cache_key = f"{CACHE_PREFIX_CHAIN}:{symbol.upper()}:{expiration or 'all'}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        chain = await self._tradier_get_options_chain(symbol, expiration)
        if not chain:
            chain = await self._yfinance_get_options_chain(symbol, expiration)

        if chain:
            await cache.set(cache_key, chain, ttl=settings.CACHE_TTL_MARKET_DATA)
        return chain

    async def get_options_expirations(self, symbol: str) -> List[str]:
        """Get available expiration dates for a symbol."""
        cache_key = f"{CACHE_PREFIX_CHAIN}:{symbol.upper()}:expirations"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        expirations = await self._tradier_get_expirations(symbol)
        if not expirations:
            expirations = await self._yfinance_get_expirations(symbol)

        if expirations:
            await cache.set(cache_key, expirations, ttl=settings.CACHE_TTL_MARKET_DATA)
        return expirations or []

    # ─── Historical Data ─────────────────────────────────────────────

    async def get_historical_prices(
        self,
        symbol: str,
        days: int = 252
    ) -> List[Dict[str, Any]]:
        """Get historical daily OHLCV data for volatility calculations."""
        cache_key = f"{CACHE_PREFIX_HISTORY}:{symbol.upper()}:{days}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        history = await self._tradier_get_history(symbol, days)
        if not history:
            history = await self._yfinance_get_history(symbol, days)

        if history:
            await cache.set(cache_key, history, ttl=settings.CACHE_TTL_SIGNALS)
        return history or []

    # ─── VIX & Market Data ───────────────────────────────────────────

    async def get_vix(self) -> Optional[Dict[str, Any]]:
        """Get current VIX level and related data."""
        cache_key = CACHE_PREFIX_VIX
        cached = await cache.get(cache_key)
        if cached:
            return cached

        vix = await self.get_stock_quote("VIX")
        if not vix:
            vix = await self._yfinance_get_quote("^VIX")

        if vix:
            await cache.set(cache_key, vix, ttl=settings.CACHE_TTL_MARKET_DATA)
        return vix

    # ─── Earnings Calendar ───────────────────────────────────────────

    async def get_earnings_calendar(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get upcoming earnings dates for symbols."""
        cache_key = f"{CACHE_PREFIX_EARNINGS}:{','.join(sorted(symbols)) if symbols else 'all'}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        earnings = await self._tradier_get_calendar(symbols)
        if not earnings:
            earnings = await self._yfinance_get_earnings(symbols)

        if earnings:
            await cache.set(cache_key, earnings, ttl=settings.CACHE_TTL_INSIGHTS)
        return earnings or []

    # ─── Tradier API Methods ─────────────────────────────────────────

    async def _tradier_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make authenticated request to Tradier API."""
        if not settings.TRADIER_API_KEY:
            return None

        client = await self._get_client()
        url = f"{settings.TRADIER_BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {settings.TRADIER_API_KEY}",
            "Accept": "application/json",
        }

        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"Tradier API error {e.response.status_code} for {endpoint}: {e}")
            return None
        except Exception as e:
            logger.error(f"Tradier request failed for {endpoint}: {e}")
            return None

    async def _tradier_get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock quote from Tradier."""
        data = await self._tradier_request("markets/quotes", {"symbols": symbol})
        if not data:
            return None

        try:
            quotes = data.get("quotes", {})
            quote = quotes.get("quote", {})
            if isinstance(quote, list):
                quote = quote[0] if quote else {}

            return {
                "symbol": quote.get("symbol", symbol),
                "last": quote.get("last"),
                "change": quote.get("change"),
                "change_pct": quote.get("change_percentage"),
                "volume": quote.get("volume"),
                "open": quote.get("open"),
                "high": quote.get("high"),
                "low": quote.get("low"),
                "close": quote.get("close"),
                "bid": quote.get("bid"),
                "ask": quote.get("ask"),
                "source": "tradier",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error parsing Tradier quote for {symbol}: {e}")
            return None

    async def _tradier_get_options_chain(
        self,
        symbol: str,
        expiration: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get options chain from Tradier."""
        params = {"symbol": symbol, "greeks": "true"}
        if expiration:
            params["expiration"] = expiration

        data = await self._tradier_request("markets/options/chains", params)
        if not data:
            return None

        try:
            options = data.get("options", {})
            option_list = options.get("option", [])
            if not isinstance(option_list, list):
                option_list = [option_list] if option_list else []

            calls = []
            puts = []
            for opt in option_list:
                greeks = opt.get("greeks", {}) or {}
                parsed = {
                    "symbol": opt.get("symbol"),
                    "underlying": opt.get("underlying"),
                    "strike": float(opt.get("strike", 0)),
                    "expiration_date": opt.get("expiration_date"),
                    "option_type": opt.get("option_type"),
                    "bid": opt.get("bid"),
                    "ask": opt.get("ask"),
                    "last": opt.get("last"),
                    "volume": opt.get("volume", 0),
                    "open_interest": opt.get("open_interest", 0),
                    "implied_volatility": greeks.get("mid_iv"),
                    "delta": greeks.get("delta"),
                    "gamma": greeks.get("gamma"),
                    "theta": greeks.get("theta"),
                    "vega": greeks.get("vega"),
                    "rho": greeks.get("rho"),
                }
                if opt.get("option_type") == "call":
                    calls.append(parsed)
                else:
                    puts.append(parsed)

            return {
                "symbol": symbol,
                "expiration": expiration,
                "calls": calls,
                "puts": puts,
                "source": "tradier",
            }
        except Exception as e:
            logger.error(f"Error parsing Tradier options chain for {symbol}: {e}")
            return None

    async def _tradier_get_expirations(self, symbol: str) -> Optional[List[str]]:
        """Get available expiration dates from Tradier."""
        data = await self._tradier_request(
            "markets/options/expirations",
            {"symbol": symbol}
        )
        if not data:
            return None

        try:
            expirations = data.get("expirations", {})
            dates = expirations.get("date", [])
            if isinstance(dates, str):
                dates = [dates]
            return dates
        except Exception as e:
            logger.error(f"Error parsing Tradier expirations for {symbol}: {e}")
            return None

    async def _tradier_get_history(
        self,
        symbol: str,
        days: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical prices from Tradier."""
        start = (date.today() - timedelta(days=days)).isoformat()
        data = await self._tradier_request(
            "markets/history",
            {"symbol": symbol, "interval": "daily", "start": start}
        )
        if not data:
            return None

        try:
            history = data.get("history", {})
            day_data = history.get("day", [])
            if not isinstance(day_data, list):
                day_data = [day_data] if day_data else []

            return [
                {
                    "date": d.get("date"),
                    "open": d.get("open"),
                    "high": d.get("high"),
                    "low": d.get("low"),
                    "close": d.get("close"),
                    "volume": d.get("volume"),
                }
                for d in day_data
            ]
        except Exception as e:
            logger.error(f"Error parsing Tradier history for {symbol}: {e}")
            return None

    async def _tradier_get_calendar(
        self,
        symbols: Optional[List[str]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Get earnings calendar from Tradier."""
        data = await self._tradier_request("markets/calendar")
        if not data:
            return None

        try:
            calendar = data.get("calendar", {})
            days = calendar.get("days", {}).get("day", [])
            if not isinstance(days, list):
                days = [days] if days else []

            earnings = []
            for day in days:
                events = day.get("premarket", {}).get("event", [])
                if not isinstance(events, list):
                    events = [events] if events else []
                for event in events:
                    if event.get("event_type") == "earnings":
                        entry = {
                            "symbol": event.get("ticker"),
                            "date": day.get("date"),
                            "time": "pre_market",
                        }
                        if not symbols or entry["symbol"] in symbols:
                            earnings.append(entry)
            return earnings
        except Exception as e:
            logger.error(f"Error parsing Tradier calendar: {e}")
            return None

    # ─── yfinance Fallback Methods ───────────────────────────────────

    async def _yfinance_get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock quote using yfinance (fallback)."""
        try:
            import yfinance as yf
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)
            info = await loop.run_in_executor(None, lambda: ticker.fast_info)

            return {
                "symbol": symbol.upper().replace("^", ""),
                "last": getattr(info, "last_price", None),
                "change": None,
                "change_pct": None,
                "volume": getattr(info, "last_volume", None),
                "open": getattr(info, "open", None),
                "high": getattr(info, "day_high", None),
                "low": getattr(info, "day_low", None),
                "close": getattr(info, "previous_close", None),
                "bid": None,
                "ask": None,
                "source": "yfinance",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning(f"yfinance quote failed for {symbol}: {e}")
            return None

    async def _yfinance_get_options_chain(
        self,
        symbol: str,
        expiration: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get options chain using yfinance (fallback)."""
        try:
            import yfinance as yf
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)

            if not expiration:
                expirations = await loop.run_in_executor(None, lambda: ticker.options)
                if not expirations:
                    return None
                expiration = expirations[0]

            chain = await loop.run_in_executor(
                None, lambda: ticker.option_chain(expiration)
            )

            def parse_df(df, option_type):
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "symbol": row.get("contractSymbol", ""),
                        "underlying": symbol,
                        "strike": float(row.get("strike", 0)),
                        "expiration_date": expiration,
                        "option_type": option_type,
                        "bid": row.get("bid"),
                        "ask": row.get("ask"),
                        "last": row.get("lastPrice"),
                        "volume": int(row.get("volume", 0) or 0),
                        "open_interest": int(row.get("openInterest", 0) or 0),
                        "implied_volatility": row.get("impliedVolatility"),
                        "delta": None,
                        "gamma": None,
                        "theta": None,
                        "vega": None,
                        "rho": None,
                    })
                return records

            return {
                "symbol": symbol,
                "expiration": expiration,
                "calls": parse_df(chain.calls, "call"),
                "puts": parse_df(chain.puts, "put"),
                "source": "yfinance",
            }
        except Exception as e:
            logger.warning(f"yfinance options chain failed for {symbol}: {e}")
            return None

    async def _yfinance_get_expirations(self, symbol: str) -> Optional[List[str]]:
        """Get expiration dates using yfinance (fallback)."""
        try:
            import yfinance as yf
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)
            expirations = await loop.run_in_executor(None, lambda: ticker.options)
            return list(expirations) if expirations else None
        except Exception as e:
            logger.warning(f"yfinance expirations failed for {symbol}: {e}")
            return None

    async def _yfinance_get_history(
        self,
        symbol: str,
        days: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get historical prices using yfinance (fallback)."""
        try:
            import yfinance as yf
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)
            period = "1y" if days <= 252 else "2y"
            df = await loop.run_in_executor(
                None, lambda: ticker.history(period=period)
            )
            if df is None or df.empty:
                return None

            return [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
                for idx, row in df.iterrows()
            ]
        except Exception as e:
            logger.warning(f"yfinance history failed for {symbol}: {e}")
            return None

    async def _yfinance_get_earnings(
        self,
        symbols: Optional[List[str]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Get earnings calendar using yfinance (fallback)."""
        try:
            import yfinance as yf
            loop = asyncio.get_event_loop()
            targets = symbols or settings.INSIGHTS_DEFAULT_WATCHLIST.split(",")
            earnings = []

            for symbol in targets:
                try:
                    ticker = yf.Ticker(symbol.strip())
                    cal = await loop.run_in_executor(None, lambda t=ticker: t.calendar)
                    if cal is not None and not (hasattr(cal, 'empty') and cal.empty):
                        earnings_date = None
                        if isinstance(cal, dict):
                            earnings_date = cal.get("Earnings Date")
                        if earnings_date:
                            if isinstance(earnings_date, list):
                                earnings_date = earnings_date[0]
                            earnings.append({
                                "symbol": symbol.strip(),
                                "date": str(earnings_date)[:10],
                                "time": "unknown",
                            })
                except Exception:
                    continue

            return earnings if earnings else None
        except Exception as e:
            logger.warning(f"yfinance earnings failed: {e}")
            return None
