-- Daily Options Insights Feature Tables
-- Adds tables for insights engine: daily_insights, market_signals, signal_performance, user_watchlist

-- Table: daily_insights
-- Stores generated trade recommendations and alerts per user
CREATE TABLE IF NOT EXISTS daily_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Insight Classification
    insight_type VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 3,
    signal_score INTEGER,

    -- Content
    title VARCHAR(200) NOT NULL,
    description TEXT,
    action_items JSONB,

    -- Context
    related_symbol VARCHAR(20),
    related_position_id UUID,
    strategy_type VARCHAR(50),

    -- Signal Attribution
    signals_triggered JSONB,
    screening_template VARCHAR(50),

    -- Metadata
    metadata JSONB,

    -- Tracking
    is_dismissed BOOLEAN NOT NULL DEFAULT FALSE,
    is_acted_upon BOOLEAN NOT NULL DEFAULT FALSE,
    outcome_pnl NUMERIC(12,2),

    -- Timing
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_insights_user_priority
    ON daily_insights (user_id, priority, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_daily_insights_user_type
    ON daily_insights (user_id, insight_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_daily_insights_symbol
    ON daily_insights (related_symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_daily_insights_active
    ON daily_insights (user_id, is_dismissed, expires_at)
    WHERE is_dismissed = FALSE;
CREATE INDEX IF NOT EXISTS idx_daily_insights_score
    ON daily_insights (user_id, signal_score DESC, created_at DESC);


-- Table: market_signals
-- Cached market-wide signals shared across all users
CREATE TABLE IF NOT EXISTS market_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Signal Identity
    signal_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),

    -- Signal Data
    value NUMERIC(16,6),
    regime VARCHAR(20),
    data JSONB NOT NULL,

    -- Timing
    signal_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_market_signals_type_symbol_time
    ON market_signals (signal_type, symbol, signal_timestamp);
CREATE INDEX IF NOT EXISTS idx_market_signals_type_time
    ON market_signals (signal_type, signal_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_signals_symbol_type
    ON market_signals (symbol, signal_type, signal_timestamp DESC);


-- Table: signal_performance
-- Track historical signal accuracy for continuous improvement
CREATE TABLE IF NOT EXISTS signal_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    signal_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),
    signal_direction VARCHAR(10),
    signal_value NUMERIC(16,6),

    -- Outcome
    entry_price NUMERIC(12,4),
    exit_price NUMERIC(12,4),
    pnl NUMERIC(12,2),
    pnl_percent NUMERIC(8,4),
    holding_period_hours INTEGER,
    outcome VARCHAR(10),

    -- Context
    market_regime VARCHAR(20),
    vix_at_signal NUMERIC(8,4),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signal_perf_type
    ON signal_performance (signal_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signal_perf_symbol
    ON signal_performance (symbol, signal_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_signal_perf_outcome
    ON signal_performance (signal_type, outcome);


-- Table: user_watchlist
-- User-configurable watchlist for targeted scanning
CREATE TABLE IF NOT EXISTS user_watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    notes TEXT,

    -- Alert preferences
    alert_on_ivr_above INTEGER DEFAULT 50,
    alert_on_flow BOOLEAN DEFAULT TRUE,

    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_watchlist_user_symbol
    ON user_watchlist (user_id, symbol);


-- Migration notes:
-- 1. daily_insights: Core table for the insights engine output
--    - Partitioned queries by user_id + priority for the daily briefing
--    - signal_score enables ranking across insight types
--    - is_dismissed/is_acted_upon + outcome_pnl enable signal performance tracking
--
-- 2. market_signals: Shared signal cache (not per-user)
--    - Deduplication via unique index on (signal_type, symbol, signal_timestamp)
--    - expires_at enables automatic cleanup of stale signals
--
-- 3. signal_performance: Historical tracking for signal accuracy
--    - Feeds back into signal scoring weights over time
--    - market_regime context helps identify regime-dependent signal behavior
--
-- 4. user_watchlist: Simple watchlist with alert preferences
--    - Unique constraint on (user_id, symbol) prevents duplicates
--    - alert_on_ivr_above configurable per-symbol threshold
