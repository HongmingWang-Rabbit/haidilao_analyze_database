-- ========================================
-- COMBO TABLES MIGRATION SCRIPT
-- ========================================
-- This script adds combo support to the existing database
-- without affecting any existing data.
--
-- Usage: Run this script on the production database to add:
-- - combo table
-- - monthly_combo_dish_sale table
-- - related indexes and triggers
--
-- Generated: 2025-07-03
-- ========================================

-- Check if tables already exist before creating
DO $$
BEGIN
    -- Create combo table if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'combo') THEN
        CREATE TABLE combo (
            id SERIAL PRIMARY KEY,
            combo_code VARCHAR NOT NULL UNIQUE, -- 套餐编码 (e.g., "3010184", "1000000303")
            name VARCHAR NOT NULL,              -- 套餐名称 (e.g., "儿童套餐", "超值单人套餐")
            description VARCHAR,                -- 描述
            is_active BOOLEAN DEFAULT TRUE,     -- 是否活跃
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        RAISE NOTICE 'Created combo table';
    ELSE
        RAISE NOTICE 'Combo table already exists, skipping creation';
    END IF;

    -- Create monthly_combo_dish_sale table if it doesn't exist
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'monthly_combo_dish_sale') THEN
        CREATE TABLE monthly_combo_dish_sale (
            id SERIAL PRIMARY KEY,
            combo_id INTEGER REFERENCES combo(id), -- 外键：套餐
            dish_id INTEGER REFERENCES dish(id), -- 外键：菜品
            store_id INTEGER REFERENCES store(id), -- 外键：门店
            month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12), -- 月份 (1-12)
            year INTEGER NOT NULL CHECK (year >= 2020), -- 年份
            sale_amount NUMERIC(12, 4) DEFAULT 0, -- 销售数量 (出品数量 - 退菜数量)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(combo_id, dish_id, store_id, month, year) -- 同一套餐同一菜品同一门店同一月只能有一条记录
        );
        
        RAISE NOTICE 'Created monthly_combo_dish_sale table';
    ELSE
        RAISE NOTICE 'Monthly_combo_dish_sale table already exists, skipping creation';
    END IF;
END
$$;

-- ========================================
-- ADD INDEXES FOR PERFORMANCE
-- ========================================

-- Combo indexes
DO $$
BEGIN
    -- Check if index exists before creating
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_combo_code') THEN
        CREATE INDEX idx_combo_code ON combo(combo_code);
        RAISE NOTICE 'Created index: idx_combo_code';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_combo_active') THEN
        CREATE INDEX idx_combo_active ON combo(is_active);
        RAISE NOTICE 'Created index: idx_combo_active';
    END IF;

    -- Monthly combo dish sale indexes
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_monthly_combo_dish_sale_combo_dish_store_date') THEN
        CREATE INDEX idx_monthly_combo_dish_sale_combo_dish_store_date ON monthly_combo_dish_sale(combo_id, dish_id, store_id, year, month);
        RAISE NOTICE 'Created index: idx_monthly_combo_dish_sale_combo_dish_store_date';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_monthly_combo_dish_sale_dish_store_date') THEN
        CREATE INDEX idx_monthly_combo_dish_sale_dish_store_date ON monthly_combo_dish_sale(dish_id, store_id, year, month);
        RAISE NOTICE 'Created index: idx_monthly_combo_dish_sale_dish_store_date';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_monthly_combo_dish_sale_store_date') THEN
        CREATE INDEX idx_monthly_combo_dish_sale_store_date ON monthly_combo_dish_sale(store_id, year, month);
        RAISE NOTICE 'Created index: idx_monthly_combo_dish_sale_store_date';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_monthly_combo_dish_sale_date') THEN
        CREATE INDEX idx_monthly_combo_dish_sale_date ON monthly_combo_dish_sale(year, month);
        RAISE NOTICE 'Created index: idx_monthly_combo_dish_sale_date';
    END IF;
END
$$;

-- ========================================
-- ADD TRIGGERS FOR UPDATED_AT
-- ========================================

-- Ensure the update_updated_at_column function exists
DO $$
BEGIN
    -- Check if the trigger function exists
    IF NOT EXISTS (SELECT FROM pg_proc WHERE proname = 'update_updated_at_column') THEN
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $trigger$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $trigger$ LANGUAGE plpgsql;
        
        RAISE NOTICE 'Created update_updated_at_column function';
    END IF;
END
$$;

-- Add triggers for combo tables
DO $$
BEGIN
    -- Combo table trigger
    IF NOT EXISTS (SELECT FROM information_schema.triggers WHERE trigger_name = 'update_combo_updated_at') THEN
        CREATE TRIGGER update_combo_updated_at 
            BEFORE UPDATE ON combo
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        RAISE NOTICE 'Created trigger: update_combo_updated_at';
    END IF;

    -- Monthly combo dish sale table trigger
    IF NOT EXISTS (SELECT FROM information_schema.triggers WHERE trigger_name = 'update_monthly_combo_dish_sale_updated_at') THEN
        CREATE TRIGGER update_monthly_combo_dish_sale_updated_at 
            BEFORE UPDATE ON monthly_combo_dish_sale
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        RAISE NOTICE 'Created trigger: update_monthly_combo_dish_sale_updated_at';
    END IF;
END
$$;

-- ========================================
-- MIGRATION COMPLETE
-- ========================================

-- Display summary
DO $$
DECLARE
    combo_count INTEGER;
    combo_sales_count INTEGER;
BEGIN
    -- Count existing records
    SELECT COUNT(*) INTO combo_count FROM combo;
    SELECT COUNT(*) INTO combo_sales_count FROM monthly_combo_dish_sale;
    
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'COMBO TABLES MIGRATION COMPLETED';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created/verified:';
    RAISE NOTICE '  ✓ combo (% records)', combo_count;
    RAISE NOTICE '  ✓ monthly_combo_dish_sale (% records)', combo_sales_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes created/verified: 6';
    RAISE NOTICE 'Triggers created/verified: 2';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Extract combo data: python scripts/extract_combo_monthly_sales.py [file] --direct-db';
    RAISE NOTICE '2. Generate reports: The monthly material reports will now include combo usage';
    RAISE NOTICE '';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '========================================';
END
$$; 