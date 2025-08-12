-- schema.sql
--
-- This script sets up the database schema for the market data storage system.
-- It is designed for PostgreSQL with the TimescaleDB extension.
--
-- To set up the database:
-- 1. Ensure you have PostgreSQL and the TimescaleDB extension installed.
-- 2. Create a new database (e.g., 'market_data').
-- 3. Connect to your new database (e.g., using `psql -d market_data`).
-- 4. Run `CREATE EXTENSION IF NOT EXISTS timescaledb;`
-- 5. Run the contents of this file.

-- Table to store metadata for each symbol
CREATE TABLE IF NOT EXISTS symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    asset_type VARCHAR(50), -- e.g., 'Stock', 'Crypto', 'Forex', 'Commodity'
    exchange VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table to store 1-minute OHLCV data
CREATE TABLE IF NOT EXISTS ohlcv_1m (
    symbol_id INTEGER NOT NULL,
    "time" TIMESTAMPTZ NOT NULL,
    "open" DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    "close" DOUBLE PRECISION,
    volume BIGINT,
    FOREIGN KEY (symbol_id) REFERENCES symbols (id) ON DELETE CASCADE,
    PRIMARY KEY (symbol_id, "time")
);

-- Convert the ohlcv_1m table into a TimescaleDB hypertable, partitioned by time.
-- This is the core of TimescaleDB's performance benefits for time-series data.
-- It automatically partitions the data by time, making queries much faster.
-- The `if_not_exists => TRUE` argument prevents an error if the command is run again.
SELECT create_hypertable('ohlcv_1m', 'time', if_not_exists => TRUE);

-- Create indexes for faster queries
-- Index on the 'symbols' table for quick lookup by symbol name.
CREATE INDEX IF NOT EXISTS idx_symbol_name ON symbols(symbol);

-- TimescaleDB automatically creates an index on the time column of hypertables.
-- A composite index on (symbol_id, time) is already created by the PRIMARY KEY constraint.
-- This index is highly efficient for the most common query: fetching data for a specific symbol
-- within a specific time range.

-- Optional: Create a function to automatically update the 'updated_at' timestamp
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Optional: Attach the trigger to the 'symbols' table
-- This trigger will fire whenever a row in the 'symbols' table is updated.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'set_timestamp' AND tgrelid = 'symbols'::regclass
    ) THEN
        CREATE TRIGGER set_timestamp
        BEFORE UPDATE ON symbols
        FOR EACH ROW
        EXECUTE PROCEDURE trigger_set_timestamp();
    END IF;
END;
$$;

-- Idempotent insert/upsert function for OHLCV data.
-- This ensures that we don't insert duplicate data points.
-- The function is not strictly needed if using INSERT ... ON CONFLICT,
-- but can be useful for more complex logic. For now, we will rely on
-- the application-level logic using `ON CONFLICT (symbol_id, "time") DO NOTHING`.

-- End of schema setup.
-- Version: 1.0
-- Author: Jules, AI Software Engineer
