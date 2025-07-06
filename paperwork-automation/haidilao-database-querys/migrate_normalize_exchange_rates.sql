-- Migration: Normalize Monthly Exchange Rates
-- This script moves monthly_CAD_USD_rate from store_monthly_target to a new month_static_data table
-- Author: Haidilao Database Migration
-- Date: 2025-01-01

-- ========================================
-- STEP 1: Create month_static_data table
-- ========================================

CREATE TABLE IF NOT EXISTS month_static_data (
    id SERIAL PRIMARY KEY,
    month DATE NOT NULL UNIQUE,                    -- Monthly date (first day of month)
    cad_usd_rate NUMERIC(8, 4) NOT NULL,          -- Monthly CAD/USD exchange rate
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_month_first_day CHECK (EXTRACT(DAY FROM month) = 1)
);

-- Add indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_month_static_data_month ON month_static_data(month);

-- Add trigger for updated_at timestamp
CREATE TRIGGER update_month_static_data_updated_at 
    BEFORE UPDATE ON month_static_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- STEP 2: Migrate existing exchange rate data
-- ========================================

-- Extract unique month and exchange rate combinations from store_monthly_target
INSERT INTO month_static_data (month, cad_usd_rate)
SELECT DISTINCT 
    month,
    monthly_CAD_USD_rate
FROM store_monthly_target 
WHERE monthly_CAD_USD_rate IS NOT NULL
ON CONFLICT (month) DO UPDATE SET
    cad_usd_rate = EXCLUDED.cad_usd_rate,
    updated_at = CURRENT_TIMESTAMP;

-- ========================================
-- STEP 3: Remove redundant column from store_monthly_target
-- ========================================

-- Remove the monthly_CAD_USD_rate column from store_monthly_target
ALTER TABLE store_monthly_target 
DROP COLUMN IF EXISTS monthly_CAD_USD_rate;

-- ========================================
-- VERIFICATION QUERIES
-- ========================================

-- Verify migration completed successfully
DO $$
DECLARE
    month_static_count INTEGER;
    store_target_has_rate BOOLEAN;
BEGIN
    -- Check if month_static_data has records
    SELECT COUNT(*) INTO month_static_count FROM month_static_data;
    
    -- Check if monthly_CAD_USD_rate column still exists in store_monthly_target
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'store_monthly_target' 
        AND column_name = 'monthly_cad_usd_rate'
    ) INTO store_target_has_rate;
    
    -- Print results
    RAISE NOTICE 'Migration Status:';
    RAISE NOTICE '- month_static_data records: %', month_static_count;
    RAISE NOTICE '- store_monthly_target still has rate column: %', store_target_has_rate;
    
    IF month_static_count > 0 AND NOT store_target_has_rate THEN
        RAISE NOTICE 'Migration completed successfully!';
    ELSE
        RAISE WARNING 'Migration may not have completed properly';
    END IF;
END
$$; 