-- Reset SQL for dish-material related tables only
-- This script clears dish, material, and related tables while preserving stores and other data

-- Disable foreign key checks temporarily (if needed)
SET session_replication_role = replica;

-- Clear dish-material relationship tables first (due to foreign keys)
DELETE FROM dish_material;
DELETE FROM dish_monthly_sale;
DELETE FROM dish_price_history;

-- Clear material-related tables
DELETE FROM material_price_history;
DELETE FROM material;

-- Clear dish-related tables
DELETE FROM dish;
DELETE FROM dish_child_type;
DELETE FROM dish_type;

-- Re-enable foreign key checks
SET session_replication_role = DEFAULT;

-- Reset sequences (if using auto-increment IDs)
SELECT setval(pg_get_serial_sequence('dish_type', 'id'), 1, false);
SELECT setval(pg_get_serial_sequence('dish_child_type', 'id'), 1, false);
SELECT setval(pg_get_serial_sequence('dish', 'id'), 1, false);
SELECT setval(pg_get_serial_sequence('material', 'id'), 1, false);

-- Show cleanup results
SELECT 
    'dish_type' as table_name, COUNT(*) as remaining_records FROM dish_type
UNION ALL
SELECT 
    'dish_child_type' as table_name, COUNT(*) as remaining_records FROM dish_child_type
UNION ALL
SELECT 
    'dish' as table_name, COUNT(*) as remaining_records FROM dish
UNION ALL
SELECT 
    'material' as table_name, COUNT(*) as remaining_records FROM material
UNION ALL
SELECT 
    'dish_material' as table_name, COUNT(*) as remaining_records FROM dish_material
UNION ALL
SELECT 
    'dish_price_history' as table_name, COUNT(*) as remaining_records FROM dish_price_history
UNION ALL
SELECT 
    'dish_monthly_sale' as table_name, COUNT(*) as remaining_records FROM dish_monthly_sale
UNION ALL
SELECT 
    'material_price_history' as table_name, COUNT(*) as remaining_records FROM material_price_history;

PRINT 'Dish-material related tables have been reset successfully!';
PRINT 'Store data and other non-dish-material tables remain intact.';