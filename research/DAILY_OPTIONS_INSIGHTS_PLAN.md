# Daily Options Insights — Comprehensive Feature Plan

*Synthesized from 4-agent research team | 2026-02-21*

---

## Executive Summary

Build a **Daily Options Insights Engine** that transforms raw trading data into actionable daily trade recommendations. The system combines market regime detection (GEX), volatility analytics (IV Rank/Percentile), institutional flow tracking, and automated screening to deliver a morning briefing with prioritized trade setups.

**Target**: 0.15-0.25% daily return (40-80% annually) — aggressive but achievable with disciplined risk management. Note: 1% daily (1,200% annually) exceeds what top hedge funds achieve and would require unsustainable risk.

**Estimated Build**: 10-12 weeks across 4 phases.

---

## 1. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL DATA SOURCES                       │
├─────────────┬──────────────┬──────────────┬────────────────────┤
│ Tradier API │ Polygon.io   │ Unusual      │ FRED / Earnings    │
│ (free)      │ ($99/mo)     │ Whales ($35) │ Calendar (free)    │
│ Options     │ Stock data   │ Flow data    │ Events & macro     │
│ chains +    │ + historical │ Sweeps,      │ CPI, FOMC,         │
│ Greeks      │              │ blocks, UOA  │ earnings dates     │
└──────┬──────┴──────┬───────┴──────┬───────┴────────┬───────────┘
       │             │              │                │
       ▼             ▼              ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│              MarketDataService (NEW)                             │
│  Async fetcher + Redis cache (1-5 min TTL)                      │
│  Rate limiting, error handling, multi-source fallback            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐  ┌────────────────┐  ┌────────────────────┐
│ SignalEngine │  │ VolatilityCalc │  │ FlowAnalyzer       │
│ GEX, regime  │  │ IVR, IVP, HV   │  │ Sweeps, blocks,    │
│ detection    │  │ skew, term str │  │ net premium, UOA   │
└──────┬───────┘  └────────┬───────┘  └────────┬───────────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    InsightsEngine (NEW)                          │
│  Combines signals → generates daily insights + trade recs       │
│  Alert scoring (0-100), screening templates, risk checks        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
            ┌──────────┐  ┌──────────────┐
            │ PostgreSQL│  │ Redis Cache  │
            │ New tables│  │ Real-time    │
            │ insights, │  │ signals,     │
            │ signals,  │  │ regime state │
            │ alerts    │  │              │
            └──────┬───┘  └──────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│              InsightsAPI Router (NEW)                            │
│  /api/v1/insights/*                                             │
│  daily, alerts, opportunities, screener, market-overview        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Frontend: InsightsTab (NEW)                         │
│  Daily Trade Planner | Volatility Scanner | Flow Feed           │
│  OI Heatmap | Earnings Analyzer | Smart Alerts | Screener       │
└─────────────────────────────────────────────────────────────────┘
```

### Integration with Existing Codebase

| Existing Component | How Insights Plugs In |
|---|---|
| `RobinhoodService` | Provides current positions, orders, portfolio Greeks — insights engine reads this data, does NOT add new RH API calls |
| `options_orders` table | Historical trade data feeds P&L attribution and signal performance tracking |
| `options_positions` table | Current holdings feed position alerts, theta decay warnings, roll recommendations |
| `BackgroundScheduler` | New jobs added alongside existing 15-min sync and 30-min rolled options processing |
| `RedisCache` | New cache keys for signals, regime state, and real-time flow data |
| `frontend/dashboard/page.tsx` | New `'insights'` tab added to `TabType` union |

---

## 2. Data Stack & Costs

### Recommended Data Sources (MVP: ~$134/month)

| Source | Cost | Data Provided | Priority |
|--------|------|---------------|----------|
| **Tradier API** | Free (with brokerage acct) | Options chains, real-time quotes, Greeks, execution | Must-have |
| **Polygon.io Starter** | $99/mo | Stock prices, historical data, news, 5 calls/min | Must-have |
| **Unusual Whales** | $35/mo | Options flow, sweeps, blocks, dark pool, UOA | Must-have |
| **FRED API** | Free | Economic calendar, macro data | Must-have |
| **yfinance** | Free | Earnings calendar, basic data (dev/fallback only) | Nice-to-have |
| **Alpha Vantage** | Free | Technical indicators (25/day) | Nice-to-have |

### Open Source Libraries (All Free)

| Library | Purpose |
|---------|---------|
| `py_vollib_vectorized` | Fast Greeks & IV calculation (vectorized numpy) |
| `QuantLib-Python` | Volatility surfaces, advanced options pricing |
| `pandas` + `numpy` | Signal calculations, data processing |
| `scipy.stats` | Statistical analysis (z-scores, percentiles) |
| `ta` or `pandas_ta` | Technical indicators (RSI, VWAP, moving averages) |

### Growth Path ($500-1,500/mo when ready)

| Source | Cost | Unlocks |
|--------|------|---------|
| Databento Standard | $199/mo | OPRA-level options data, nanosecond timestamps |
| iVolatility | $200/mo | Professional IV analytics, volatility surface |
| Alpaca Markets | Free | Additional execution, MCP server for AI integration |

---

## 3. Database Schema (New Tables)

### Table: `daily_insights`
Primary storage for generated trade recommendations and alerts.

```sql
CREATE TABLE daily_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Insight Classification
    insight_type VARCHAR(50) NOT NULL,  -- 'morning_brief', 'trade_setup', 'position_alert',
                                        -- 'earnings_play', 'flow_alert', 'regime_change',
                                        -- 'roll_recommendation', 'risk_warning'
    priority INTEGER NOT NULL DEFAULT 3, -- 1=critical, 2=high, 3=medium, 4=low
    signal_score INTEGER,                -- 0-100 composite score

    -- Content
    title VARCHAR(200) NOT NULL,
    description TEXT,
    action_items JSONB,                  -- [{action: "sell put spread", details: {...}}]

    -- Context
    related_symbol VARCHAR(20),
    related_position_id UUID,
    strategy_type VARCHAR(50),           -- 'credit_spread', 'iron_condor', 'straddle', etc.

    -- Signal Attribution
    signals_triggered JSONB,             -- [{signal: "IVR", value: 72, tier: 1}, ...]
    screening_template VARCHAR(50),      -- Which template generated this insight

    -- Metadata
    metadata JSONB,                      -- Flexible: strike, expiry, delta, expected_return, etc.

    -- Tracking
    is_dismissed BOOLEAN DEFAULT FALSE,
    is_acted_upon BOOLEAN DEFAULT FALSE,
    outcome_pnl NUMERIC(12,2),           -- Actual P&L if acted upon (for signal performance)

    -- Timing
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    CONSTRAINT idx_insights_user_date UNIQUE (user_id, insight_type, related_symbol, created_at)
);

CREATE INDEX idx_daily_insights_user_priority ON daily_insights(user_id, priority, created_at DESC);
CREATE INDEX idx_daily_insights_user_type ON daily_insights(user_id, insight_type, created_at DESC);
CREATE INDEX idx_daily_insights_symbol ON daily_insights(related_symbol, created_at DESC);
CREATE INDEX idx_daily_insights_active ON daily_insights(user_id, is_dismissed, expires_at)
    WHERE is_dismissed = FALSE;
```

### Table: `market_signals`
Cached market-wide signals shared across all users.

```sql
CREATE TABLE market_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Signal Identity
    signal_type VARCHAR(50) NOT NULL,    -- 'gex_regime', 'vix_level', 'sector_rotation',
                                         -- 'market_flow', 'economic_event'
    symbol VARCHAR(20),                  -- NULL for market-wide, ticker for stock-specific

    -- Signal Data
    value NUMERIC(16,6),                 -- Numeric value (GEX, IVR, etc.)
    regime VARCHAR(20),                  -- 'positive', 'negative', 'neutral'
    data JSONB NOT NULL,                 -- Full signal data

    -- Timing
    signal_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Deduplication
    CONSTRAINT uq_signal_type_symbol_time UNIQUE (signal_type, symbol, signal_timestamp)
);

CREATE INDEX idx_market_signals_type ON market_signals(signal_type, signal_timestamp DESC);
CREATE INDEX idx_market_signals_symbol ON market_signals(symbol, signal_type, signal_timestamp DESC);
CREATE INDEX idx_market_signals_active ON market_signals(expires_at) WHERE expires_at > NOW();
```

### Table: `signal_performance`
Track how each signal performs over time for continuous improvement.

```sql
CREATE TABLE signal_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    signal_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),
    signal_direction VARCHAR(10),        -- 'bullish', 'bearish', 'neutral'
    signal_value NUMERIC(16,6),

    -- Outcome
    entry_price NUMERIC(12,4),
    exit_price NUMERIC(12,4),
    pnl NUMERIC(12,2),
    pnl_percent NUMERIC(8,4),
    holding_period_hours INTEGER,
    outcome VARCHAR(10),                 -- 'win', 'loss', 'scratch'

    -- Context
    market_regime VARCHAR(20),           -- GEX regime when signal fired
    vix_at_signal NUMERIC(8,4),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_signal_perf_type ON signal_performance(signal_type, created_at DESC);
```

### Table: `user_watchlist`
User-configurable watchlist for targeted scanning.

```sql
CREATE TABLE user_watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    alert_on_ivr_above INTEGER DEFAULT 50,
    alert_on_flow BOOLEAN DEFAULT TRUE,

    CONSTRAINT uq_user_watchlist UNIQUE (user_id, symbol)
);
```

---

## 4. Backend Services (New)

### Service 1: `MarketDataService`

**File**: `backend/app/services/market_data_service.py`

**Responsibilities**:
- Fetch and cache external market data (Tradier, Polygon, UW)
- Rate limiting per provider
- Multi-source fallback (if Tradier fails, try Polygon)
- Normalize data formats across providers

**Key Methods**:
```
get_options_chain(symbol) → OptionsChain
get_stock_price(symbol) → StockQuote
get_historical_prices(symbol, days) → List[OHLCV]
get_earnings_calendar(symbols) → List[EarningsEvent]
get_vix() → VIXData
get_options_flow(symbol?) → List[FlowEntry]  (via Unusual Whales)
get_economic_calendar() → List[EconomicEvent]
```

### Service 2: `VolatilityService`

**File**: `backend/app/services/volatility_service.py`

**Responsibilities**:
- Calculate IV Rank, IV Percentile per ticker
- Calculate Historical Volatility (HV)
- Detect IV skew and term structure anomalies
- Track IV crush patterns around earnings

**Key Methods**:
```
calculate_ivr(symbol) → {ivr, ivp, current_iv, high_52w, low_52w}
calculate_hv(symbol, period=30) → float
get_iv_skew(symbol) → {skew, percentile, put_iv, call_iv}
get_term_structure(symbol) → List[{dte, iv}]
get_earnings_iv_history(symbol) → List[{date, pre_iv, post_iv, crush_pct}]
```

### Service 3: `SignalEngine`

**File**: `backend/app/services/signal_engine.py`

**Responsibilities**:
- Calculate GEX from options chain data
- Detect market regime (positive/negative gamma)
- Calculate net premium flow
- Score and rank signals
- Detect sweep/block/UOA patterns

**Key Methods**:
```
calculate_gex(symbol) → {net_gex, regime, zero_gamma_level, key_levels}
detect_unusual_activity(symbol) → List[UOASignal]
calculate_net_premium(symbol) → {net_premium, direction, magnitude}
get_market_regime() → {regime, vix, gex, confidence}
score_signals(symbol) → {score: 0-100, signals: List[Signal]}
```

### Service 4: `InsightsEngine`

**File**: `backend/app/services/insights_engine.py`

**Responsibilities**:
- Combine all signals into actionable insights
- Generate daily morning briefing
- Run screening templates
- Create trade recommendations with risk parameters
- Track signal performance over time

**Key Methods**:
```
generate_morning_brief(user_id) → MorningBrief
generate_trade_setups(user_id, template?) → List[TradeSetup]
analyze_position_risks(user_id) → List[PositionAlert]
get_roll_recommendations(user_id) → List[RollRecommendation]
get_earnings_plays() → List[EarningsPlay]
run_screener(criteria) → List[ScreenerResult]
record_outcome(insight_id, outcome) → void
get_signal_performance(days=30) → SignalPerformanceReport
```

### Background Jobs (New)

| Job | Schedule | Purpose |
|-----|----------|---------|
| `market_data_sync` | Every 5 min (market hours) | Fetch prices, options chains for watchlist |
| `signal_calculation` | Every 15 min (market hours) | Calculate GEX, IVR, flow signals |
| `morning_insights` | 8:00 AM ET (weekdays) | Generate daily briefing + trade setups |
| `position_monitor` | Every 30 min (market hours) | Check position alerts, theta decay, expiry warnings |
| `earnings_scan` | 6:00 AM ET (weekdays) | Scan for earnings within 14 days, calculate IV patterns |
| `signal_performance` | 4:30 PM ET (weekdays) | Record daily signal outcomes for performance tracking |
| `eod_cleanup` | 5:00 PM ET (weekdays) | Expire stale signals, archive old insights |

---

## 5. API Endpoints (New)

### Insights Router: `/api/v1/insights`

```
# Daily Briefing
GET  /daily                    → Today's insights (morning brief + active setups)
GET  /daily/history?days=7     → Past insights with outcomes

# Trade Setups & Opportunities
GET  /opportunities            → Current screened opportunities (all templates)
GET  /opportunities/screener   → Custom screener with query params
POST /opportunities/screener   → Custom screener with complex criteria body

# Position Management
GET  /alerts                   → Active position alerts (expiry, risk, roll recs)
GET  /theta-report             → Daily theta decay analysis for all positions
GET  /roll-recommendations     → Roll suggestions for expiring positions

# Market Overview
GET  /market/regime            → Current GEX regime + key levels
GET  /market/vix               → VIX + term structure
GET  /market/flow              → Aggregate market flow (bullish/bearish)
GET  /market/sectors           → Sector rotation heatmap data
GET  /market/events            → Economic + earnings calendar

# Volatility Scanner
GET  /volatility/scanner       → IVR/IVP table for watchlist
GET  /volatility/{symbol}      → Detailed vol analysis for one ticker
GET  /volatility/earnings      → Upcoming earnings with IV crush data

# Flow Feed
GET  /flow/live                → Recent significant options flow
GET  /flow/{symbol}            → Flow for specific ticker
GET  /flow/summary             → Net premium by ticker (top bullish/bearish)

# Interaction
POST /insights/{id}/dismiss    → Dismiss an insight
POST /insights/{id}/acted      → Mark as acted upon (with entry details)
PUT  /insights/{id}/outcome    → Record outcome P&L

# Watchlist
GET  /watchlist                → User watchlist
POST /watchlist                → Add symbol to watchlist
DELETE /watchlist/{symbol}     → Remove from watchlist

# Signal Performance
GET  /performance              → Signal performance dashboard data
GET  /performance/{signal}     → Specific signal historical accuracy
```

---

## 6. Frontend Components (New)

### Component Tree

```
frontend/src/components/insights/
├── InsightsTab.tsx                    # Main container (tab in dashboard)
├── MorningBrief/
│   ├── MorningBriefCard.tsx          # Daily summary card
│   ├── MarketRegimeIndicator.tsx     # GEX regime badge (green/orange/red)
│   └── DailyChecklist.tsx            # 9-step daily workflow checklist
├── TradeSetups/
│   ├── TradeSetupList.tsx            # List of today's recommended trades
│   ├── TradeSetupCard.tsx            # Individual trade with signals, entry/exit
│   └── SignalBadge.tsx               # Signal pill (IVR: 72, GEX: +)
├── VolatilityScanner/
│   ├── VolatilityScannerTable.tsx    # IVR/IVP sortable table
│   ├── IVSparkline.tsx              # 30-day IV trend mini chart
│   └── EarningsCountdown.tsx         # Days to earnings + expected crush
├── FlowFeed/
│   ├── FlowFeedList.tsx             # Scrolling flow entries
│   ├── FlowEntry.tsx                # Single sweep/block/UOA entry
│   ├── NetPremiumChart.tsx          # Bullish vs bearish flow chart
│   └── TopFlowTickers.tsx           # Top 10 by flow
├── MarketOverview/
│   ├── VIXGauge.tsx                 # VIX level + term structure
│   ├── SectorHeatmap.tsx            # Sector rotation visual
│   └── EventCalendar.tsx            # Upcoming events timeline
├── PositionAlerts/
│   ├── AlertList.tsx                # Active alerts for held positions
│   ├── ThetaDecayReport.tsx         # Daily theta bleed analysis
│   └── RollRecommendation.tsx       # Roll suggestion card
├── Screener/
│   ├── ScreenerTemplates.tsx        # 7 pre-built templates
│   ├── ScreenerResults.tsx          # Results table with signal scores
│   └── CustomScreenerBuilder.tsx    # Advanced filter builder
├── Performance/
│   ├── SignalPerformanceDash.tsx    # Signal accuracy over time
│   └── DailyScorecard.tsx          # Today's P&L vs target
└── shared/
    ├── InsightCard.tsx              # Reusable insight/alert card
    ├── SignalScoreMeter.tsx         # 0-100 score visualization
    └── StrategyBadge.tsx            # Strategy type pill
```

### Key UI Patterns

**Morning Brief Card**: Shows at top of insights tab every morning with regime, key events, top 3 setups.

**Trade Setup Card**: Each trade recommendation includes:
- Signal score (0-100) with breakdown
- Specific strategy (e.g., "Sell AAPL 45 DTE Iron Condor")
- Entry criteria (IVR, delta, strikes)
- Risk parameters (max loss, position size as % of account)
- Exit rules (50% profit target, stop loss)
- Signals that triggered it (badges)

**Screener Templates**: 7 pre-built scanners from the signal catalog:
1. Premium Selling Paradise
2. Earnings IV Crusher
3. Smart Money Follow
4. Volatility Mean Reversion
5. Daily 0DTE Scanner
6. Post-Event Vanna Bounce
7. Sector Rotation Play

---

## 7. Strategy & Risk Framework (Built Into System)

### Position Sizing Rules (Enforced by InsightsEngine)

Every trade recommendation includes calculated position size:

| Rule | Limit |
|------|-------|
| Per-trade risk | Max 1-2% of account |
| Per-strategy daily risk | Max 5% of account |
| Total portfolio risk | Max 15% at any time |
| VIX < 20 | 100% normal size |
| VIX 20-25 | 75% size |
| VIX 25-30 | 50% size |
| VIX > 30 | 25% size or pause |

### Daily Stop-Loss Cascade (Monitored by position_monitor job)

| Daily P&L | System Action |
|-----------|---------------|
| -1% | Alert: "Tighten all stops" |
| -2% | Alert: "Close all 0DTE positions" |
| -3% | Alert: "Close 50% of all positions" |
| -5% | Critical: "Full halt recommended" |

### Strategy Mix (Default Allocation)

| Strategy | Target Allocation | Screening Template |
|----------|-------------------|-------------------|
| 0DTE SPX Credit Spreads | 25% | Daily 0DTE Scanner |
| 45 DTE Premium Selling | 30% | Premium Selling Paradise |
| Wheel Strategy | 25% | (Manual selection) |
| Earnings Vol Crush | 10% | Earnings IV Crusher |
| VIX Tail Hedge | 5% | (Systematic monthly) |
| Cash Reserve | 5% | — |

---

## 8. Daily Action Items System

### How It Works

Every weekday morning at 8:00 AM ET, the `morning_insights` job generates a personalized briefing:

```
┌─────────────────────────────────────────────────┐
│  DAILY TRADE PLANNER — Monday, Feb 23 2026      │
├─────────────────────────────────────────────────┤
│                                                  │
│  MARKET REGIME: Positive Gamma (Range-Bound)     │
│  VIX: 17.3 | GEX: +$2.1B | Zero Gamma: 5,820   │
│  Strategy: SELL PREMIUM                          │
│                                                  │
│  TODAY'S EVENTS:                                 │
│  • 10:00 AM — Existing Home Sales (Low Impact)   │
│  • AAPL earnings after close (High Impact)       │
│                                                  │
│  TOP TRADE SETUPS:                               │
│                                                  │
│  1. [Score: 87] TSLA Iron Condor                 │
│     IVR: 73 | 45 DTE | Positive GEX regime      │
│     Sell 280/275 put / 350/355 call              │
│     Max risk: $500 | Target: $250 (50%)          │
│                                                  │
│  2. [Score: 74] AAPL Earnings Straddle Sell       │
│     IVR: 68 | Earnings today | Hist crush: 42%   │
│     Sell 235 straddle, Feb 28 expiry             │
│     Max risk: $800 | Target: $400                │
│                                                  │
│  3. [Score: 65] SPX 0DTE Put Credit Spread       │
│     Positive GEX | Tue (best day) | VIX < 20    │
│     Sell 5780/5775 put spread                    │
│     Max risk: $250 | Target: $125                │
│                                                  │
│  POSITION ALERTS:                                │
│  ⚠ NVDA 130 Call — expires in 3 days, -$45      │
│  ⚠ AMZN put spread — at 50% profit, close?     │
│                                                  │
│  DAILY CHECKLIST:                                │
│  □ Review regime + key levels                    │
│  □ Check overnight flow for watchlist            │
│  □ Execute setups after 10:00 AM                 │
│  □ Monitor positions at midday                   │
│  □ Close 0DTE by 3:30 PM                        │
│  □ Log trades + score signals at EOD             │
└─────────────────────────────────────────────────┘
```

### Action Item Categories

1. **Trade Setups** — Specific trades with entry/exit/risk (auto-generated from screeners)
2. **Position Alerts** — Warnings for existing positions (expiry, profit target hit, risk)
3. **Roll Recommendations** — When to roll existing positions
4. **Risk Warnings** — Portfolio-level risk alerts (VIX spike, drawdown cascade)
5. **Regime Changes** — GEX flips, IV environment shifts
6. **Earnings Plays** — Upcoming earnings with IV analysis
7. **Flow Alerts** — Institutional activity on watchlist tickers

---

## 9. Phased Implementation Roadmap

### Phase 1: Foundation + Volatility Scanner (Weeks 1-3)

**Goal**: Get external data flowing and deliver the first actionable feature.

| Week | Backend | Frontend | Deliverable |
|------|---------|----------|-------------|
| 1 | MarketDataService (Tradier + yfinance), new DB tables + migrations, env config | InsightsTab shell, add tab to dashboard | Data pipeline working |
| 2 | VolatilityService (IVR, IVP, HV), background job for IV calculations | VolatilityScannerTable, IVSparkline | Volatility scanner live |
| 3 | Basic GEX calculation, earnings calendar integration | MarketRegimeIndicator, EarningsCountdown, MorningBriefCard (basic) | Market regime + earnings awareness |

**Data Sources Needed**: Tradier API (free), yfinance (free), FRED (free)
**Cost**: $0/month

### Phase 2: Insights Engine + Flow (Weeks 4-6)

**Goal**: Generate daily trade recommendations and track institutional flow.

| Week | Backend | Frontend | Deliverable |
|------|---------|----------|-------------|
| 4 | InsightsEngine core, morning_insights job, trade setup generation | TradeSetupList, TradeSetupCard, SignalBadge | Daily trade recommendations |
| 5 | Unusual Whales integration, flow parsing, sweep/block detection | FlowFeedList, FlowEntry, NetPremiumChart | Live options flow feed |
| 6 | Screening templates (#1-#3), position alerts, theta decay report | ScreenerTemplates, AlertList, ThetaDecayReport | Screening + position management |

**Data Sources Added**: Unusual Whales API ($35/mo)
**Cost**: $35/month

### Phase 3: Advanced Signals + Polish (Weeks 7-9)

**Goal**: Add advanced signals, performance tracking, and remaining screeners.

| Week | Backend | Frontend | Deliverable |
|------|---------|----------|-------------|
| 7 | Polygon.io integration, real-time stock data, VWAP calculations | MarketOverview (VIX, sectors, events), TopFlowTickers | Market overview dashboard |
| 8 | Signal performance tracking, outcome recording, alert scoring system | SignalPerformanceDash, DailyScorecard, signal_performance API | Performance analytics |
| 9 | Remaining screener templates (#4-#7), IV skew/term structure, roll recommendations | CustomScreenerBuilder, RollRecommendation, VolatilityScanner detail views | Full screening suite |

**Data Sources Added**: Polygon.io ($99/mo)
**Cost**: $134/month total

### Phase 4: Pro Features + Optimization (Weeks 10-12)

**Goal**: 0DTE features, smart alerts, ML scoring, mobile optimization.

| Week | Backend | Frontend | Deliverable |
|------|---------|----------|-------------|
| 10 | Vanna/Charm flow calculations, 0DTE-specific signals, smart alert engine | DailyChecklist, smart alert UI, notification preferences | Vanna/Charm + smart alerts |
| 11 | Signal convergence detection, ML-based signal scoring (XGBoost on historical data) | OI Heatmap (D3.js/Recharts), SignalScoreMeter | OI heatmap + ML scoring |
| 12 | End-to-end testing, performance optimization, documentation | Mobile responsiveness, accessibility, final polish | Production-ready |

---

## 10. Environment Configuration (New)

### Backend `.env` additions

```
# Market Data APIs
TRADIER_API_KEY=your_tradier_api_key
TRADIER_SANDBOX=true
POLYGON_API_KEY=your_polygon_api_key
UNUSUAL_WHALES_API_KEY=your_uw_api_key
ALPHA_VANTAGE_API_KEY=your_av_api_key

# Insights Configuration
INSIGHTS_MARKET_OPEN_HOUR=9       # ET
INSIGHTS_MARKET_CLOSE_HOUR=16     # ET
INSIGHTS_MORNING_BRIEF_HOUR=8     # ET
INSIGHTS_GEX_REFRESH_MINUTES=15
INSIGHTS_FLOW_REFRESH_MINUTES=5
INSIGHTS_DEFAULT_WATCHLIST=SPY,QQQ,IWM,AAPL,TSLA,NVDA,AMZN,META,MSFT,GOOGL
```

### New pip dependencies

```
py_vollib_vectorized>=0.1.0
QuantLib>=1.31
pandas_ta>=0.3.14
httpx>=0.27.0            # Async HTTP client for external APIs
apscheduler>=3.10.0      # Already installed, but verify version
```

### New npm dependencies

```
d3>=7.0.0                # For OI heatmap visualization
@tanstack/react-query    # Already in package.json, wire up for insights
date-fns                 # Date formatting for market hours/events
```

---

## 11. Risk Disclaimer & Realistic Expectations

### What This System Is

- **A decision-support tool** that surfaces high-probability trade setups based on quantitative signals
- **A risk management framework** that enforces position sizing and stop-loss discipline
- **A learning system** that tracks which signals work and improves over time

### What This System Is NOT

- **NOT a guaranteed profit machine** — all options trading involves risk of total loss
- **NOT a replacement for judgment** — signals are probabilistic, not deterministic
- **NOT capable of 1% daily returns sustainably** — recalibrate to 0.15-0.25% daily (40-80% annually)

### Realistic Performance Benchmarks

| Metric | Conservative | Aggressive |
|--------|-------------|------------|
| Annual return target | 25-40% | 50-80% |
| Daily return target | 0.10-0.16% | 0.20-0.30% |
| Expected win rate | 65-75% | 60-70% |
| Max drawdown tolerance | 10-15% | 15-25% |
| Sharpe ratio | 1.0-1.5 | 0.8-1.2 |

---

## 12. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Morning brief delivered by | 8:30 AM ET | Job execution log |
| Trade setups generated daily | 3-5 per day | Insights count |
| Signal accuracy (Tier 1) | >60% correct direction | Signal performance table |
| User acts on insights | >30% of generated | is_acted_upon tracking |
| Positive P&L attribution | >50% of acted insights | outcome_pnl tracking |
| System uptime during market hours | >99.5% | Health check monitoring |
| Data freshness | <5 min for prices, <15 min for signals | Cache TTL monitoring |

---

*End of Comprehensive Feature Plan*
*Synthesized from: Financial Expert (tools/APIs), Hedge Fund Strategist (strategies/risk), Engineering Lead (codebase/architecture), Technical PM (signals/features)*
