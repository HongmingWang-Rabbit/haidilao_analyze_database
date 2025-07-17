-- Migration script to add sales_mode column to dish_monthly_sale table
-- This addresses the issue where different sales modes (堂食/外卖) are being overwritten

BEGIN;

-- Step 1: Add sales_mode column to dish_monthly_sale table
ALTER TABLE dish_monthly_sale 
ADD COLUMN sales_mode VARCHAR(10) DEFAULT '堂食' CHECK (sales_mode IN ('堂食', '外卖'));

-- Step 2: Update the comment for the table
COMMENT ON COLUMN dish_monthly_sale.sales_mode IS '销售模式: 堂食 (dine-in) or 外卖 (takeout)';

-- Step 3: Drop the old unique constraint
ALTER TABLE dish_monthly_sale 
DROP CONSTRAINT dish_monthly_sale_dish_id_store_id_month_year_key;

-- Step 4: Create new unique constraint including sales_mode
ALTER TABLE dish_monthly_sale 
ADD CONSTRAINT dish_monthly_sale_dish_id_store_id_month_year_sales_mode_key 
UNIQUE(dish_id, store_id, month, year, sales_mode);

-- Step 5: Create index for sales_mode queries
CREATE INDEX idx_dish_monthly_sale_sales_mode ON dish_monthly_sale(sales_mode);

-- Step 6: Create composite index for common queries
CREATE INDEX idx_dish_monthly_sale_dish_store_date_mode ON dish_monthly_sale(dish_id, store_id, year, month, sales_mode);

COMMIT;

-- Display the updated table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'dish_monthly_sale' 
ORDER BY ordinal_position; 