-- Migration: Add daily_takeout_revenue table for tracking per-store daily takeout data
-- Date: 2026-01-06
-- Description: Stores daily takeout revenue extracted from Input/daily_report/takeout_report/ Excel files

-- Create the daily takeout revenue table
CREATE TABLE IF NOT EXISTS daily_takeout_revenue (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id),
    date DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, date)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_daily_takeout_revenue_store_date
    ON daily_takeout_revenue(store_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_takeout_revenue_date
    ON daily_takeout_revenue(date);

-- Add comment for documentation
COMMENT ON TABLE daily_takeout_revenue IS 'Daily takeout revenue per store, extracted from SAP export files';
COMMENT ON COLUMN daily_takeout_revenue.amount IS 'Takeout revenue amount in local currency (positive value)';
