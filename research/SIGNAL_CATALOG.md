# Options Market Signal Catalog
## Comprehensive Signal Inventory for Daily Options Trading

*Research compiled: 2026-02-21*

---

## Table of Contents
1. [Signal Inventory](#1-signal-inventory)
2. [Priority Ranking](#2-priority-ranking)
3. [Data Requirements](#3-data-requirements)
4. [Feature Translation](#4-feature-translation)
5. [Daily Action Items Framework](#5-daily-action-items-framework)
6. [Alert Criteria](#6-alert-criteria)
7. [Screening Templates](#7-screening-templates)

---

## 1. Signal Inventory

### Category A: Unusual Options Activity (UOA)

#### A1. Volume vs Open Interest Ratio
- **Description**: Identifies options contracts trading at significantly higher volume relative to their open interest, suggesting new informed positioning.
- **Calculation**: `UOA_Ratio = Daily_Volume / Open_Interest`. Flag when ratio > 2.0 (aggressive) or > 1.5 (moderate).
- **Predictive Value**: HIGH — Academic research (Jiang & Strong, SSRN #3618427) confirms UOA has significant predictive power for underlying stock returns. However, media-covered UOA shows overreaction followed by reversal.
- **Key Nuance**: Filter for orders >$50K premium to exclude retail noise. Short-dated OTM contracts (expiry <35 days, >10% OTM) carry strongest signal.
- **Edge Duration**: 1-5 trading days for directional signals.

#### A2. Sweep Detection
- **Description**: Large orders split across multiple exchanges to fill quickly, indicating urgency from institutional/informed traders.
- **Calculation**: Detect when a single order fills across 3+ exchanges within seconds, total premium >$100K.
- **Predictive Value**: HIGH — Sweeps at the ask (buying) or at the bid (selling) signal directional conviction. Multi-exchange execution suggests urgency over price optimization.
- **Key Filters**: Premium >$100K, filled at ask (bullish) or bid (bearish), <35 DTE for conviction.

#### A3. Block Trade Identification
- **Description**: Large single-exchange fills (100+ contracts) negotiated off-screen, typically institutional activity.
- **Calculation**: Single fills of 100+ contracts at a single price point, premium >$250K.
- **Predictive Value**: MEDIUM-HIGH — Blocks are more likely hedges than sweeps but still indicate significant positioning. Cross-reference with dark pool activity for confirmation.

#### A4. Repeat Unusual Activity
- **Description**: Multiple unusual options trades on the same ticker within a short window, building a pattern of informed accumulation.
- **Calculation**: 3+ separate UOA signals on the same ticker within 2 trading days, with consistent directional bias.
- **Predictive Value**: HIGH — Repeat activity is the strongest UOA signal. Single occurrences can be hedges; patterns indicate conviction.

---

### Category B: Implied Volatility Signals

#### B1. IV Rank (IVR)
- **Description**: Where current IV sits relative to its 52-week high/low range. The primary strategy selection tool.
- **Calculation**: `IVR = (Current_IV - 52wk_Low_IV) / (52wk_High_IV - 52wk_Low_IV) * 100`
- **Predictive Value**: HIGH — TastyTrade research shows selling premium when IVR > 50 yields significantly higher win rates. IV is mean-reverting, making extreme IVR values actionable.
- **Strategy Mapping**:
  - IVR > 50: Sell premium (iron condors, strangles, credit spreads)
  - IVR < 30: Buy premium (long calls/puts, debit spreads)
  - IVR 30-50: Neutral zone, use directional signals for strategy selection

#### B2. IV Percentile (IVP)
- **Description**: Percentage of trading days in the past year where IV was below the current level.
- **Calculation**: `IVP = (Days_Below_Current_IV / 252) * 100`
- **Predictive Value**: HIGH — More robust than IVR because it accounts for distribution shape, not just range extremes. IVP > 60 = options are expensive historically.
- **Usage**: IVP is preferred over IVR for identifying mean-reversion opportunities because it's less distorted by single-day spikes.

#### B3. IV Skew (Put/Call)
- **Description**: Difference in implied volatility between OTM puts and OTM calls. Steep skew = high demand for downside protection.
- **Calculation**: `Skew = IV(25-delta put) - IV(25-delta call)`. Track percentile of skew vs 30/60/90 day history.
- **Predictive Value**: MEDIUM — Skew flattening signals complacency (potential risk ahead). Skew steepening before events signals hedging demand. Useful for timing, less useful for direction.
- **Trading Signal**: When skew is at extremes (>90th or <10th percentile), mean reversion trades on the skew itself can be profitable.

#### B4. IV Term Structure
- **Description**: How IV varies across expiration dates. Normal = upward sloping. Inverted = near-term IV higher than long-term.
- **Calculation**: Compare 30-day IV vs 60-day vs 90-day IV. Inverted = 30-day > 60-day by >5%.
- **Predictive Value**: MEDIUM-HIGH — Inverted term structure before earnings/events is normal. Inverted term structure without a known catalyst is a strong signal of anticipated volatility.
- **Trading Signal**: Calendar spreads profit from term structure normalization. Sell near-term, buy far-term when term structure is inverted.

#### B5. HV vs IV Divergence
- **Description**: Gap between realized (historical) volatility and implied volatility. When IV >> HV, options are overpriced relative to actual movement.
- **Calculation**: `Divergence = IV_30 - HV_30`. Track Z-score of divergence.
- **Predictive Value**: MEDIUM-HIGH — IV > HV by >1 standard deviation = strong sell premium signal. HV > IV (rare) = potential buying opportunity or breakout signal.

#### B6. IV Crush Detection
- **Description**: Rapid IV collapse after binary events (earnings, FDA decisions, etc.).
- **Calculation**: Compare pre-event IV to post-event IV. Typical crush is 30-60% of IV value.
- **Predictive Value**: HIGH for timing — IV crush is the most predictable event in options. Pre-earnings IV almost always exceeds post-earnings realized move. Selling premium before events captures this edge.
- **Key Data**: Historical IV crush magnitude by ticker enables accurate premium selling sizing.

---

### Category C: Options Flow Analysis

#### C1. Put/Call Ratio (Equity)
- **Description**: Ratio of put volume to call volume on individual equities.
- **Calculation**: `PCR = Total_Put_Volume / Total_Call_Volume` (daily or intraday)
- **Predictive Value**: MEDIUM — Extreme readings are contrarian indicators. PCR > 1.5 = extreme bearishness (often a bottom). PCR < 0.5 = extreme bullishness (potential top). Most useful on indexes (SPX, VIX) rather than individual stocks.
- **Key Nuance**: Must distinguish between speculative puts (directional bets) and hedging puts (portfolio protection). Context matters enormously.

#### C2. Net Premium Analysis
- **Description**: Aggregate dollar flow into calls vs puts, weighted by premium size.
- **Calculation**: `Net_Premium = SUM(Call_Premium_at_Ask) - SUM(Put_Premium_at_Ask)`. Positive = bullish flow, negative = bearish flow.
- **Predictive Value**: HIGH — Dollar-weighted flow is more meaningful than volume because it captures conviction level. Rank tickers by bullish and bearish premium to identify where capital is flowing.
- **Smart Money Filter**: Only count trades >$50K premium to filter retail noise.

#### C3. Smart Money vs Retail Flow Detection
- **Description**: Separate institutional/informed flow from retail activity based on order characteristics.
- **Calculation**: Multi-factor scoring:
  - Order size: >100 contracts or >$50K premium (+1 institutional)
  - Execution: At ask (aggressive buy) or at bid (aggressive sell) (+1 conviction)
  - Expiry: <35 DTE and >10% OTM (+1 speculative/informed)
  - Multi-leg: Complex spreads (+1 institutional)
  - Exchange: PHLX/CBOE blocks (+1 institutional)
- **Predictive Value**: MEDIUM-HIGH — Smart money flow direction has been shown to lead price by 1-3 days. Most effective when smart money and retail diverge.

#### C4. Dark Pool + Options Confluence
- **Description**: Combined signal when dark pool block trades align with options flow direction.
- **Calculation**: Dark pool buy blocks + rising call volume = strong bullish confirmation. Dark pool sell blocks + rising put volume = strong bearish confirmation.
- **Predictive Value**: HIGH when both align — The confluence of institutional equity positioning (dark pools) with options positioning provides the strongest directional signal.
- **Data Requirement**: Requires dark pool/ATS trade reporting data (FINRA).

---

### Category D: Market Structure / Dealer Positioning Signals

#### D1. Gamma Exposure (GEX)
- **Description**: Aggregate net gamma of all open options positions, reflecting how dealers must hedge price changes.
- **Calculation**: `GEX = Σ(OI × Contract_Multiplier × Gamma × Spot_Price² / 100)` for all strikes. Net GEX = Call GEX - Put GEX.
- **Predictive Value**: HIGH for regime identification —
  - **Positive GEX**: Dealers sell rallies, buy dips → suppressed volatility, mean-reverting, range-bound. Ideal for selling premium.
  - **Negative GEX**: Dealers buy rallies, sell dips → amplified volatility, trending. Ideal for directional trades.
- **Key Levels**: Zero Gamma line = transition point. Large GEX concentration at specific strikes = "magnetic" price levels.
- **Implementation Priority**: CRITICAL — This is the single most important market structure signal.

#### D2. Delta Hedging Flow Estimation
- **Description**: Estimated dollar value of equity that dealers must buy/sell to maintain delta-neutral positions.
- **Calculation**: Aggregate dealer delta exposure by strike, estimate hedging flow needed for 1% move in underlying.
- **Predictive Value**: MEDIUM-HIGH — Large estimated hedging flows at specific price levels create support/resistance. When GEX is high, hedging flows dampen moves; when GEX is negative, they amplify.

#### D3. Vanna Flow (Volatility-Driven Hedging)
- **Description**: How dealer hedging changes when implied volatility shifts. Vanna = ∂Δ/∂IV.
- **Calculation**: `Vanna_Exposure = Σ(OI × Vanna × Contract_Multiplier)`. Track sign and magnitude.
- **Predictive Value**: HIGH around vol regime shifts — Post-event IV collapses trigger massive vanna-driven flows. When IV drops after events, dealers unwind delta hedges, often causing mechanical rallies unrelated to fundamentals.
- **Trading Signal**: After earnings/FOMC when IV crushes, expect vanna-driven buying pressure. Position for the mechanical bounce.

#### D4. Charm Flow (Time-Driven Hedging)
- **Description**: How dealer hedging changes as time passes. Charm = ∂Δ/∂t.
- **Calculation**: `Charm_Exposure = Σ(OI × Charm × Contract_Multiplier)`. Strongest near expiration.
- **Predictive Value**: MEDIUM-HIGH near expiration — As OTM options decay, dealers reduce hedges. Near expiration (especially Friday), charm flows create predictable drifts. Combined with vanna after events, creates powerful mechanical price movement.
- **Implementation**: Most impactful for same-week and 0DTE trading.

#### D5. Max Pain Level
- **Description**: Strike price where the maximum number of options (calls + puts) expire worthless.
- **Calculation**: For each strike, calculate total intrinsic value of all calls and puts. Max Pain = strike with minimum total intrinsic value.
- **Predictive Value**: LOW-MEDIUM — Academic research ("No Max Pain, No Max Gain") found 0.4% weekly returns from max-pain-based strategies, but only effective for small-cap, illiquid stocks. NOT effective for large-cap or index options (SPY, QQQ).
- **Implementation Priority**: LOW — Include as reference level but do not build core strategies around it.

#### D6. Options Expiration Pin Risk
- **Description**: Tendency for stock prices to gravitate toward strikes with highest open interest near expiration.
- **Calculation**: Identify strikes with highest combined call + put OI for upcoming expiration. Track OI concentration vs spot price.
- **Predictive Value**: MEDIUM on expiration days — "Pinning" effect is strongest on monthly OpEx (3rd Friday) for stocks with concentrated OI. Effect diminishes for weekly expirations.

---

### Category E: Technical Analysis for Options Entry

#### E1. VWAP (Volume-Weighted Average Price)
- **Description**: The average price weighted by volume throughout the day. Key institutional reference level.
- **Calculation**: `VWAP = Σ(Price × Volume) / Σ(Volume)` — cumulative, resets daily.
- **Predictive Value**: HIGH for intraday entries — Price above VWAP = bullish trend. Price below VWAP = bearish. Crosses are entry signals. Best used 30+ minutes after open when VWAP stabilizes.
- **Options Application**:
  - Price crossing above VWAP → Buy calls or sell puts (0.20-0.30 delta)
  - Price crossing below VWAP → Buy puts or sell calls (0.20-0.30 delta)
  - VWAP as stop-loss reference for options positions

#### E2. Key Strike Level Support/Resistance
- **Description**: Strike prices with high open interest act as support/resistance due to dealer hedging.
- **Calculation**: Overlay OI by strike on price chart. High call OI strikes = resistance. High put OI strikes = support.
- **Predictive Value**: MEDIUM-HIGH — Particularly effective when combined with GEX analysis. "Gamma walls" at high-OI strikes create mechanical support/resistance.

#### E3. RSI with Options Timing
- **Description**: Relative Strength Index overbought/oversold conditions combined with options entry signals.
- **Calculation**: Standard 14-period RSI. Oversold (<30) + above VWAP = strong call entry. Overbought (>70) + below VWAP = strong put entry.
- **Predictive Value**: MEDIUM — Most effective as confirmation signal, not standalone. Combine with volatility signals for optimal entry.

#### E4. Volume Profile Analysis
- **Description**: Distribution of trading volume at different price levels, identifying high-volume nodes (HVN) and low-volume nodes (LVN).
- **Calculation**: Aggregate volume by price over selected period. HVN = support/resistance. LVN = areas of fast price movement.
- **Predictive Value**: MEDIUM — HVN areas often correspond to options strikes with high OI, creating confluence signals.

---

### Category F: Macro & Event-Driven Signals

#### F1. Earnings IV Pattern
- **Description**: Predictable IV behavior around earnings announcements — IV builds pre-earnings and crushes post-earnings.
- **Calculation**: Track IV at -30, -14, -7, -1, +1 days around earnings. Calculate average IV crush magnitude per ticker historically.
- **Predictive Value**: VERY HIGH for IV direction — IV crush is the most predictable pattern in options. Historical crush data by ticker enables precise premium selling sizing.
- **Trading Signal**: Sell strangles/iron condors 7-14 days before earnings when IVR > 50. Close or let expire after earnings for IV crush profit.

#### F2. FOMC / Fed Meeting Volatility Pattern
- **Description**: Predictable volatility behavior around Federal Reserve meetings — VIX typically elevated pre-meeting, drops post-announcement.
- **Calculation**: Track VIX behavior in 5-day window around FOMC dates historically.
- **Predictive Value**: HIGH for volatility timing — The "FOMC drift" (rally after announcement) is well-documented. Pre-FOMC skew steepening creates opportunities.
- **Trading Signal**: Sell SPX strangles morning of FOMC day. Expect IV crush after 2 PM ET announcement.

#### F3. Sector Rotation Signals
- **Description**: Relative performance shifts between sectors indicating capital flow rotation.
- **Calculation**: Compare sector ETF relative strength (XLK, XLF, XLE, XLV, etc.) over 5, 20, 60 day periods. Rising sectors get call flow; declining sectors get put flow.
- **Predictive Value**: MEDIUM — Useful for identifying which sectors to focus options strategies on. Options on sector ETFs provide beta exposure with reduced single-stock risk.

#### F4. Correlation Breakdown
- **Description**: When normally correlated assets diverge, it signals potential reversion or fundamental regime change.
- **Calculation**: Rolling correlation between asset pairs (SPY/QQQ, VIX/SPX, sector pairs). Flag when correlation drops below -1 standard deviation.
- **Predictive Value**: MEDIUM — Divergences often precede volatility. A VIX/SPX divergence (VIX rising while SPX rises) is a warning signal.

#### F5. Economic Calendar Impact
- **Description**: Scheduled economic releases (CPI, NFP, GDP, etc.) create predictable volatility windows.
- **Calculation**: Map all major economic events. Track historical IV behavior and realized moves around each event type.
- **Predictive Value**: HIGH for timing — Known events allow pre-positioning. Sell premium before low-impact events. Buy protection before high-impact events.

---

### Category G: 0DTE / Same-Day Signals

#### G1. Pre-Market GEX Analysis
- **Description**: Gamma Exposure levels calculated before market open to set daily framework.
- **Calculation**: Calculate GEX from previous close OI data. Identify positive/negative gamma regime and key levels.
- **Predictive Value**: HIGH for daily framework — Pre-market GEX is the single most important data point for 0DTE traders. Determines whether to expect range-bound or trending behavior.

#### G2. Intraday Gamma Flip Detection
- **Description**: When intraday price action crosses the zero-gamma level, regime shifts from dampening to amplifying (or vice versa).
- **Calculation**: Monitor price vs pre-calculated zero-gamma level. Alert on crossover.
- **Predictive Value**: HIGH — Crossing from positive to negative gamma regime often triggers sharp directional moves. Key for 0DTE timing.

#### G3. 0DTE OI Buildup
- **Description**: New positions being built in same-day expiration contracts, indicating intraday directional bets.
- **Calculation**: Track intraday volume vs OI for 0DTE contracts. Volume >> OI means new positions being established.
- **Predictive Value**: MEDIUM-HIGH — New 0DTE positioning can signal expected intraday direction. Heavy call building = bullish intraday expectation.

---

## 2. Priority Ranking

### Tier 1: Must-Have (Highest Edge, Implement First)

| Rank | Signal | Edge Type | Win Rate Impact | Implementation Effort |
|------|--------|-----------|----------------|----------------------|
| 1 | **GEX (D1)** | Regime identification | Defines market behavior for the day | Medium (OI data needed) |
| 2 | **IV Rank/Percentile (B1/B2)** | Strategy selection | +15-20% win rate when IVR > 50 | Low (historical IV data) |
| 3 | **IV Crush / Earnings Pattern (F1)** | Event timing | Most predictable pattern in options | Low (earnings calendar + IV history) |
| 4 | **Net Premium Flow (C2)** | Directional | Identifies institutional conviction | Medium (real-time flow data) |
| 5 | **Sweep Detection (A2)** | Urgency signal | Leads price by 1-3 days | Medium (multi-exchange data) |

### Tier 2: High Value (Strong Edge, Implement Second)

| Rank | Signal | Edge Type | Win Rate Impact | Implementation Effort |
|------|--------|-----------|----------------|----------------------|
| 6 | **Vanna/Charm Flow (D3/D4)** | Mechanical flow | Explains post-event rallies | High (Greeks calculation) |
| 7 | **IV Skew & Term Structure (B3/B4)** | Volatility structure | Identifies mispriced options | Medium (options chain data) |
| 8 | **HV vs IV Divergence (B5)** | Premium direction | Strong sell-premium signal | Low (HV + IV data) |
| 9 | **VWAP Entry Timing (E1)** | Entry optimization | Improves fills 5-10% | Low (standard indicator) |
| 10 | **UOA Volume/OI Ratio (A1)** | Informed activity | Predictive for 1-5 day moves | Medium (real-time volume) |

### Tier 3: Good-to-Have (Moderate Edge, Implement Third)

| Rank | Signal | Edge Type | Win Rate Impact | Implementation Effort |
|------|--------|-----------|----------------|----------------------|
| 11 | **Smart Money Flow (C3)** | Institutional tracking | Useful for confirmation | High (complex scoring) |
| 12 | **Put/Call Ratio (C1)** | Sentiment | Contrarian at extremes | Low (aggregate data) |
| 13 | **FOMC Pattern (F2)** | Event calendar | High predictability, low frequency | Low (calendar-based) |
| 14 | **Key Strike Levels (E2)** | Support/Resistance | GEX derivative, good visualization | Medium (OI by strike) |
| 15 | **Sector Rotation (F3)** | Sector selection | Helps target best sectors | Low (ETF performance) |

### Tier 4: Nice-to-Have (Lower Edge, Implement Last)

| Rank | Signal | Edge Type | Win Rate Impact | Implementation Effort |
|------|--------|-----------|----------------|----------------------|
| 16 | **Dark Pool Confluence (C4)** | Institutional confirmation | Strong when combined, rare | High (ATS data) |
| 17 | **RSI Confirmation (E3)** | Entry timing | Mild improvement as add-on | Low (standard indicator) |
| 18 | **0DTE GEX (G1-G3)** | Intraday | Requires advanced infrastructure | Very High (real-time) |
| 19 | **Max Pain (D5)** | Reference level | Weak for large-cap; informational only | Low (OI calculation) |
| 20 | **Volume Profile (E4)** | Price structure | Helpful but not options-specific | Medium |

---

## 3. Data Requirements

### Real-Time Data (Streaming/WebSocket)

| Data Type | Source Options | Cost Range | Signals Enabled |
|-----------|---------------|------------|-----------------|
| Options quotes (bid/ask/last) | OPRA via Databento, Polygon.io, Tradier | $199-$1500/mo | All IV signals, real-time flow |
| Options volume/OI | OPRA, CBOE DataShop | $199-$1500/mo | GEX, UOA, max pain, heatmaps |
| Options flow (time & sales) | Unusual Whales API, FlowAlgo, Quant Data | $30-$100/mo | Sweeps, blocks, net premium |
| Stock quotes | Polygon.io, Alpaca, IEX Cloud | $0-$99/mo | VWAP, technicals, correlation |
| Dark pool prints | Quant Data, FlowAlgo | $30-$100/mo | Dark pool confluence |

### End-of-Day (EOD) Data

| Data Type | Source Options | Cost Range | Signals Enabled |
|-----------|---------------|------------|-----------------|
| Historical IV by ticker | iVolatility, Quandl/Nasdaq Data Link | $50-$300/mo | IVR, IVP, IV history |
| Historical OI | CBOE DataShop | $50-$200/mo | GEX historical, OI trends |
| Earnings calendar | Earnings Whispers, Financial Modeling Prep | $0-$50/mo | Earnings IV patterns |
| Economic calendar | Trading Economics, FRED API | Free-$30/mo | Event-driven signals |
| Greeks (by strike) | Options chain APIs (Tradier, Polygon) | Included in options quotes | Vanna, Charm, GEX calculation |

### Derived/Calculated Data (Built In-House)

| Calculation | Input Required | Complexity | Storage |
|-------------|----------------|------------|---------|
| GEX by strike | OI + Greeks + Spot price | Medium | Daily snapshot + intraday |
| IV Rank / Percentile | 252 days of IV history | Low | Per-ticker daily |
| Net premium flow | Options time & sales | Medium | Real-time aggregation |
| Vanna/Charm exposure | OI + Greeks | Medium-High | Daily snapshot |
| UOA scoring | Volume, OI, premium, execution | Medium | Real-time per-contract |
| Skew percentile | 90+ days of skew history | Low | Per-ticker daily |

### Recommended Data Stack (Minimum Viable)

**Tier 1 — MVP ($250-$500/mo)**:
- Tradier API ($0/mo for market data with brokerage account) — options chains, quotes, Greeks
- Polygon.io ($99/mo starter) — real-time stock data, historical
- Unusual Whales ($30/mo) or Quant Data ($30/mo) — options flow data
- Free APIs: FRED (economic calendar), earnings whisper scraping

**Tier 2 — Growth ($500-$1,500/mo)**:
- Databento Standard ($199/mo) — OPRA-level options data
- iVolatility ($200/mo) — professional IV analytics
- FlowAlgo ($100/mo) — dark pool + options flow
- Additional storage/compute for real-time calculations

---

## 4. Feature Translation

### Feature 1: Daily Market Regime Dashboard
**Signals Used**: GEX (D1), IV Rank (B1), Put/Call Ratio (C1)

**User-Facing Feature**:
- Morning dashboard showing today's market regime: "Range-Bound" (positive GEX) or "Trending" (negative GEX)
- Color-coded regime indicator (green = sell premium, orange = directional)
- Key levels: zero-gamma level, high-GEX strikes, support/resistance from OI
- Strategy recommendation based on regime + IV environment

**UI Components**:
- Regime badge: "Positive Gamma — Expect Mean Reversion"
- Key levels chart overlay
- Suggested strategy type for the day

---

### Feature 2: Volatility Scanner
**Signals Used**: IVR (B1), IVP (B2), HV-IV Divergence (B5), IV Crush (B6)

**User-Facing Feature**:
- Table of all watchlist tickers with: IVR, IVP, HV/IV ratio, days to next earnings
- Sort/filter by IVR > 50 (sell premium candidates), IVR < 20 (buy premium candidates)
- Historical IV crush data for upcoming earnings
- Visual IV term structure graph per ticker

**UI Components**:
- Sortable table with color-coded IV metrics
- Sparkline charts for 30-day IV trend
- Earnings countdown with expected IV crush magnitude
- "Premium Selling Opportunities" and "Premium Buying Opportunities" tabs

---

### Feature 3: Options Flow Feed
**Signals Used**: Sweeps (A2), Blocks (A3), Net Premium (C2), Smart Money (C3)

**User-Facing Feature**:
- Real-time feed of significant options trades (>$50K premium)
- Classified as: Sweep (urgent), Block (institutional), or Unusual (volume/OI)
- Color-coded: Green (bullish flow), Red (bearish flow)
- Aggregate net premium by ticker and by market
- "Repeat Activity" flag when same ticker appears 3+ times

**UI Components**:
- Scrolling flow feed with filters (min premium, ticker, direction)
- Ticker heatmap showing net premium (bullish/bearish)
- Top 10 tickers by bullish/bearish flow
- Time-series chart of aggregate market flow (calls vs puts)

---

### Feature 4: Open Interest Heatmap
**Signals Used**: OI by Strike (E2), Max Pain (D5), GEX Levels (D1)

**User-Facing Feature**:
- 2D heatmap: X-axis = strike prices, Y-axis = expiration dates
- Color intensity = OI concentration
- Overlay: current price, max pain, zero-gamma level, high-GEX strikes
- Click any cell to see call/put OI breakdown and net GEX at that strike

**UI Components**:
- Interactive heatmap (Recharts or D3.js)
- Price overlay with key levels
- Expiration selector
- Call/Put toggle

---

### Feature 5: Earnings Volatility Analyzer
**Signals Used**: IV Crush (B6), Earnings Pattern (F1), Term Structure (B4)

**User-Facing Feature**:
- Calendar view of upcoming earnings with IV metrics
- Per-ticker: historical IV crush %, expected move vs actual move, best strategy historically
- "Earnings Play Recommendations" — iron condors when expected move < historical, straddles when expected move > historical
- Post-earnings analysis: did IV crush as expected?

**UI Components**:
- Earnings calendar with IV overlay
- Historical earnings move chart (expected vs actual)
- Strategy recommendation cards
- Post-earnings scorecard

---

### Feature 6: Smart Signal Alerts
**Signals Used**: All — combined scoring

**User-Facing Feature**:
- Push/in-app alerts when multiple signals align on a ticker
- Alert types:
  - "Institutional Activity": Sweep + block + repeat UOA
  - "Premium Selling Setup": IVR > 60 + positive GEX regime + no near-term events
  - "Earnings Play": 7 days to earnings + elevated IV + historical crush data
  - "Regime Change": GEX flip from positive to negative (or vice versa)
  - "Unusual Activity": 3+ UOA signals with consistent direction

**UI Components**:
- Alert feed with priority levels (High/Medium/Low)
- Alert history with outcome tracking
- Custom alert builder (user-defined criteria)
- Email/push notification preferences

---

### Feature 7: Daily Trade Planner
**Signals Used**: Framework combining all signals (see Section 5)

**User-Facing Feature**:
- Morning brief: market regime, key levels, events today, top opportunities
- Afternoon review: how signals performed, P&L attribution to signals
- Trade journal integration: log trades against signals that triggered them
- Weekly performance review: which signals generated edge, win rates by signal

**UI Components**:
- Morning brief card (auto-generated)
- Trade entry form with signal tagging
- Performance dashboard with signal attribution
- Historical win rate by signal type

---

### Feature 8: Strategy Screener
**Signals Used**: IVR (B1), GEX (D1), UOA (A1-A4), Technical (E1-E4)

**User-Facing Feature**:
- Pre-built screener templates (see Section 7)
- Custom screener builder with all signal criteria
- Results sorted by "Signal Score" — weighted combination of aligned signals
- One-click analysis: see detailed signal breakdown for any ticker

**UI Components**:
- Template selector with preview
- Custom filter builder (drag-and-drop or form)
- Results table with signal score breakdown
- Quick-analysis modal per ticker

---

## 5. Daily Action Items Framework

### Pre-Market Routine (8:00 - 9:30 AM ET)

#### Step 1: Market Regime Assessment
- [ ] Check overnight GEX calculation → Determine positive/negative gamma regime
- [ ] Review VIX level and term structure → Identify volatility environment
- [ ] Check overnight futures → Assess pre-market direction
- **Output**: "Today is a [Range-Bound/Trending] day with [High/Medium/Low] volatility"

#### Step 2: Event Calendar Review
- [ ] Check economic calendar for today's releases (CPI, NFP, FOMC, etc.)
- [ ] Check earnings calendar for pre/post market reports
- [ ] Identify any ticker-specific events (FDA, product launches, etc.)
- **Output**: List of tickers/events to watch with expected impact level

#### Step 3: Overnight Flow Analysis
- [ ] Review after-hours and pre-market options flow for unusual activity
- [ ] Check dark pool prints from previous session
- [ ] Scan for repeat UOA patterns from yesterday
- **Output**: "Top 5 tickers with unusual overnight activity"

#### Step 4: Volatility Scan
- [ ] Run IVR/IVP screener on watchlist
- [ ] Identify premium selling candidates (IVR > 50, no near-term events)
- [ ] Identify premium buying candidates (IVR < 20, catalyst expected)
- **Output**: "Today's premium selling/buying candidates"

### Market Open (9:30 - 10:30 AM ET)

#### Step 5: Opening Flow Monitoring
- [ ] Monitor first-hour flow for sweeps and blocks
- [ ] Watch for GEX level crossovers
- [ ] Track VWAP development for watchlist tickers
- **Note**: Avoid trading first 15 minutes — spreads wide, signals noisy

#### Step 6: Entry Execution
- [ ] Execute planned trades from pre-market analysis after 10:00 AM
- [ ] Confirm entries align with VWAP direction
- [ ] Set defined risk parameters (stop-loss at VWAP or key strike)
- **Output**: Executed trades with signal attribution

### Midday Monitoring (10:30 AM - 2:00 PM ET)

#### Step 7: Position Management
- [ ] Monitor active positions against key levels
- [ ] Check for GEX regime changes
- [ ] Watch for new significant flow signals
- [ ] Adjust stops if trend extends

### Power Hour (3:00 - 4:00 PM ET)

#### Step 8: End-of-Day Actions
- [ ] Review positions for overnight hold decisions
- [ ] Check charm flow implications for next-day expiration
- [ ] Identify new positions from afternoon flow signals
- [ ] Log all trades with signal tags for performance tracking

### Post-Market Review (After 4:00 PM ET)

#### Step 9: Daily Scorecard
- [ ] Record P&L by position
- [ ] Score each signal that triggered trades: correct/incorrect
- [ ] Update rolling signal performance metrics
- [ ] Identify lessons learned and adjust approach
- **Output**: Daily trade journal entry with signal attribution

---

## 6. Alert Criteria

### Critical Alerts (Immediate Notification)

| Alert | Criteria | Action |
|-------|----------|--------|
| **GEX Regime Flip** | Zero-gamma level crossed intraday | Reassess all positions; regime changed |
| **Multi-Signal Convergence** | 3+ Tier 1 signals align on same ticker | Review for potential trade entry |
| **IV Spike** | Ticker IV jumps >20% intraday without known catalyst | Investigate — potential informed activity |
| **Massive Sweep** | Single sweep >$1M premium | Immediate review — major institutional bet |

### High Priority Alerts (Within 15 Minutes)

| Alert | Criteria | Action |
|-------|----------|--------|
| **Premium Selling Setup** | IVR > 60 + positive GEX + no events within 7 days | Review for iron condor/strangle entry |
| **Earnings IV Setup** | 7 days to earnings + IVR > 50 + historical crush data available | Review earnings play recommendation |
| **Repeat UOA** | Same ticker flagged 3+ times in 2 days, consistent direction | Review for directional trade |
| **Skew Extreme** | Put/call skew > 90th percentile or < 10th percentile | Review for skew reversion trade |

### Standard Alerts (Daily Summary)

| Alert | Criteria | Action |
|-------|----------|--------|
| **Watchlist IV Changes** | Any watchlist ticker IVR changes >10 points | Update strategy assessment |
| **Position Greeks Update** | Material delta/gamma shift in held positions | Review position management |
| **Upcoming Earnings** | Watchlist ticker has earnings within 14 days | Begin pre-earnings analysis |
| **Event Calendar** | Major economic event within 48 hours | Review portfolio hedging |

### Alert Scoring System

Each alert receives a composite score (0-100) based on:
- **Signal Tier**: Tier 1 signals weighted 3x, Tier 2 weighted 2x, Tier 3 weighted 1x
- **Signal Convergence**: Each additional aligned signal adds 15 points
- **Recency**: Fresh signals (< 1 hour) weighted higher than stale signals
- **Historical Accuracy**: Signals with >60% historical hit rate get bonus weighting
- **Volume Confirmation**: Unusually high volume adds 10 points

Alerts with score >70 = Critical, 50-70 = High, 30-50 = Standard, <30 = Informational

---

## 7. Screening Templates

### Template 1: "Premium Selling Paradise"
**Goal**: Find the best stocks to sell premium on today
```
Filters:
  IVR > 50
  IVP > 60
  No earnings within 14 days
  GEX Regime = Positive (market-wide)
  Bid-Ask Spread < $0.30
  Options Volume > 1,000 contracts/day
  Market Cap > $5B (liquidity)

Sort by: IVR descending
Strategy: Iron Condors, Strangles, Credit Spreads at 1 SD
DTE: 30-45 days
Management: Close at 50% profit or 21 DTE, whichever first
```

### Template 2: "Earnings IV Crusher"
**Goal**: Capitalize on predictable IV collapse around earnings
```
Filters:
  Earnings within 7-14 days
  IVR > 40
  Historical IV Crush > 25% (average of last 4 quarters)
  Expected Move > Historical Average Actual Move
  Options Volume > 500 contracts/day
  Bid-Ask Spread < $0.50

Sort by: Expected IV Crush descending
Strategy: Iron Condors or Strangles at 1 SD wings
DTE: Use first expiration after earnings
Management: Close immediately after earnings (next morning)
```

### Template 3: "Smart Money Follow"
**Goal**: Identify and follow significant informed options flow
```
Filters:
  Sweep OR Block in last 24 hours
  Premium > $100K
  Filled at Ask (bullish) or at Bid (bearish)
  DTE < 35 days
  OTM > 5%
  Volume/OI Ratio > 2.0
  No earnings within 3 days (avoid hedging noise)

Sort by: Premium descending
Strategy: Follow direction with defined-risk spreads
DTE: Match or exceed the sweep/block expiry
Management: Trail stop at 50% of premium paid
```

### Template 4: "Volatility Mean Reversion"
**Goal**: Exploit extreme IV levels that are likely to revert
```
Filters:
  IVR > 80 OR IVR < 15
  HV/IV Ratio > 1.3 (IV overpriced) OR < 0.7 (IV underpriced)
  No known catalyst within 14 days
  Skew percentile > 80th or < 20th (additional confirmation)
  Options Volume > 500 contracts/day

Sort by: |HV/IV Divergence| descending
Strategy:
  - IV High: Sell strangles/iron condors
  - IV Low: Buy straddles/strangles (rare)
DTE: 30-45 days for selling, 45-60 days for buying
Management: Close at 25% profit (selling) or 100% profit (buying)
```

### Template 5: "Daily 0DTE Scanner"
**Goal**: Find setups for same-day expiration trades
```
Pre-Conditions:
  GEX Regime = Negative (trending day expected)
  VIX > 15 (enough premium to trade)
  No major economic releases in next 2 hours

Filters:
  SPX/SPY/QQQ/IWM only (liquidity requirement)
  0DTE contracts available
  Bid-Ask Spread < $0.15
  Delta between 0.15 - 0.40 for entries

Signals to Watch:
  Intraday VWAP cross direction
  GEX level proximity
  Real-time put/call volume ratio

Strategy: Iron butterflies or vertical spreads on 0DTE
Management: Strict stop-loss at 100% of premium. Close by 3:30 PM.
```

### Template 6: "Post-Event Vanna Bounce"
**Goal**: Capitalize on mechanical vanna-driven rallies after events
```
Pre-Conditions:
  Major event just occurred (earnings, FOMC, CPI)
  IV crushed > 15% from pre-event levels

Filters:
  IV drop > 15% in last 24 hours
  Positive vanna exposure (dealers will buy on IV drop)
  Price near or above VWAP
  No follow-up events within 48 hours

Strategy:
  - Buy short-dated calls (5-10 DTE) on the mechanical bounce
  - OR sell put credit spreads expecting upward drift
DTE: 5-10 days
Management: Quick profit target (50-100%), tight stop
```

### Template 7: "Sector Rotation Play"
**Goal**: Target options on sectors showing relative strength or weakness
```
Filters:
  Sector ETF 5-day relative performance vs SPY > +2% or < -2%
  Sector IVR > 30 (enough premium to trade)
  Options Volume > 2,000 contracts/day

Leading Sectors (RS > +2%):
  Strategy: Bull call spreads or short put spreads

Lagging Sectors (RS < -2%):
  Strategy: Bear put spreads or short call spreads

DTE: 21-30 days
Management: Close at 50% profit
```

---

## Appendix A: Signal Interaction Matrix

Signals work best when combined. This matrix shows which signal combinations create the strongest edges:

| Signal Combo | Strength | Description |
|-------------|----------|-------------|
| GEX + IVR | Very Strong | Regime tells you HOW to trade, IVR tells you WHAT to trade |
| Sweep + Repeat UOA | Very Strong | Institutional urgency + persistence = highest conviction |
| IV Crush + Earnings Calendar | Very Strong | Most predictable pattern in options |
| Vanna + Event | Strong | Mechanical bounce after IV collapse |
| Net Premium + Dark Pool | Strong | Two independent institutional signals aligning |
| VWAP + RSI | Moderate | Entry timing optimization |
| Put/Call Ratio + Skew | Moderate | Double sentiment confirmation |
| Max Pain + OI Heatmap | Weak | Informational, not strongly predictive for large-cap |

## Appendix B: Signal False Positive Mitigation

| Signal | Common False Positive | Mitigation |
|--------|----------------------|------------|
| UOA (sweeps/blocks) | Hedging activity, not directional | Filter for no offsetting trades. Ignore if near earnings. |
| IV Rank > 50 | Elevated due to known upcoming event | Check event calendar. If event-driven, switch to earnings template. |
| Put/Call Ratio extreme | Index options used for portfolio hedging | Use equity-only P/C ratio, not total. |
| GEX positive | Can persist for weeks without mean reversion | Combine with other signals. GEX alone is regime, not timing. |
| Dark pool prints | Delayed reporting creates stale signals | Cross-reference with options flow for time confirmation. |

## Appendix C: Recommended Implementation Phases

### Phase 1 (MVP — Weeks 1-3)
1. IV Rank / IV Percentile scanner per ticker
2. Basic GEX calculation (positive/negative regime indicator)
3. Earnings calendar with IV crush history
4. Screening Template #1 (Premium Selling Paradise)

### Phase 2 (Core — Weeks 4-6)
5. Options flow feed (sweeps, blocks, UOA)
6. Net premium analysis by ticker
7. OI heatmap visualization
8. Screening Templates #2 and #3
9. Basic alert system (GEX flip, IV spike, UOA)

### Phase 3 (Advanced — Weeks 7-10)
10. Vanna/Charm flow calculations
11. IV skew and term structure analysis
12. Smart money flow scoring
13. Full alert system with scoring
14. Screening Templates #4-#7
15. Daily Trade Planner (morning brief, scorecard)

### Phase 4 (Pro — Weeks 11+)
16. 0DTE-specific features
17. Dark pool integration
18. Signal performance tracking and attribution
19. Custom screener builder
20. ML-based signal scoring (historical backtesting)

---

*End of Signal Catalog*
