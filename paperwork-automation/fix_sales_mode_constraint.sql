-- Fix dish_monthly_sale unique constraint to include sales_mode
-- This allows storing separate records for 堂食 (dine-in) and 外卖 (takeout) sales modes

-- Drop the existing unique constraint that doesn't include sales_mode
ALTER TABLE dish_monthly_sale DROP CONSTRAINT dish_monthly_sale_dish_id_store_id_year_month_key;

-- Add new unique constraint that includes sales_mode
ALTER TABLE dish_monthly_sale ADD CONSTRAINT dish_monthly_sale_dish_id_store_id_year_month_sales_mode_key 
    UNIQUE (dish_id, store_id, year, month, sales_mode);

-- Create index for better performance
CREATE INDEX idx_dish_monthly_sale_sales_mode ON dish_monthly_sale (sales_mode);

-- Verify the constraint was added correctly
SELECT constraint_name, column_name 
FROM information_schema.key_column_usage 
WHERE table_name = 'dish_monthly_sale' 
AND constraint_name LIKE '%sales_mode%'
ORDER BY constraint_name, ordinal_position;