-- =============================================================
-- Stocky — Supabase Schema
-- Paste this into Supabase Studio → SQL Editor and run it.
-- Idempotent: all statements use IF NOT EXISTS / CREATE TYPE … IF NOT EXISTS.
-- =============================================================

-- ---------------------
-- 1. Custom ENUM types
-- ---------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'conditiontype') THEN
        CREATE TYPE conditiontype AS ENUM ('ABOVE', 'BELOW', 'EQUAL');
    END IF;
END
$$;

-- ---------------------
-- 2. stocks
-- ---------------------
CREATE TABLE IF NOT EXISTS stocks (
    id          SERIAL PRIMARY KEY,
    symbol      VARCHAR(15)  NOT NULL,
    name        VARCHAR(255) NOT NULL,
    exchange    VARCHAR(50)  NOT NULL,
    sector      VARCHAR(100),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ,
    CONSTRAINT uq_stocks_symbol UNIQUE (symbol)
);

CREATE INDEX IF NOT EXISTS idx_stocks_symbol   ON stocks (symbol);
CREATE INDEX IF NOT EXISTS idx_stocks_exchange ON stocks (exchange);

-- ---------------------
-- 3. holdings
-- ---------------------
CREATE TABLE IF NOT EXISTS holdings (
    id            SERIAL PRIMARY KEY,
    symbol        VARCHAR(15)    NOT NULL,
    name          VARCHAR(255)   NOT NULL,
    shares        DOUBLE PRECISION NOT NULL,
    avg_cost      DOUBLE PRECISION NOT NULL,
    total_cost    DOUBLE PRECISION NOT NULL,
    purchase_date DATE           NOT NULL,
    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ,
    CONSTRAINT uq_holdings_symbol UNIQUE (symbol)
);

CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON holdings (symbol);

-- ---------------------
-- 4. alerts
-- ---------------------
CREATE TABLE IF NOT EXISTS alerts (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(15)    NOT NULL,
    condition_type  conditiontype  NOT NULL,
    target_price    NUMERIC(12, 4) NOT NULL,
    is_active       BOOLEAN        NOT NULL DEFAULT TRUE,
    last_triggered  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_ticker          ON alerts (ticker);
CREATE INDEX IF NOT EXISTS idx_alerts_is_active       ON alerts (is_active);
CREATE INDEX IF NOT EXISTS idx_alerts_ticker_is_active ON alerts (ticker, is_active);

-- ---------------------
-- 5. watchlist_lists
-- ---------------------
CREATE TABLE IF NOT EXISTS watchlist_lists (
    id         SERIAL      PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    position   INTEGER      NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_watchlist_lists_position ON watchlist_lists (position);

-- ---------------------
-- 6. watchlist_items
-- ---------------------
CREATE TABLE IF NOT EXISTS watchlist_items (
    id           SERIAL      PRIMARY KEY,
    watchlist_id INTEGER     NOT NULL
        REFERENCES watchlist_lists (id) ON DELETE CASCADE,
    symbol       VARCHAR(15)  NOT NULL,
    name         VARCHAR(255) NOT NULL,
    exchange     VARCHAR(50)  NOT NULL,
    sector       VARCHAR(100),
    position     INTEGER      NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ,
    CONSTRAINT uq_watchlist_item UNIQUE (watchlist_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_items_watchlist_id ON watchlist_items (watchlist_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_symbol       ON watchlist_items (symbol);
