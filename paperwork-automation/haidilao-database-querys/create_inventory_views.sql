-- View to check inventory counts with material names and details
-- This view makes it easy to query inventory data with readable material information

-- Drop view if exists
DROP VIEW IF EXISTS inventory_count_with_materials CASCADE;

-- Create comprehensive inventory view
CREATE VIEW inventory_count_with_materials AS
SELECT 
    ic.id,
    ic.year,
    ic.month,
    ic.store_id,
    s.name as store_name,
    ic.material_id,
    m.material_number,
    m.name as material_name,
    m.description as material_description,
    m.unit,
    mt.name as material_type,
    mct.name as material_child_type,
    ic.counted_quantity,
    ic.created_at,
    ic.created_by
FROM inventory_count ic
JOIN material m ON m.id = ic.material_id
JOIN store s ON s.id = ic.store_id
LEFT JOIN material_type mt ON mt.id = m.material_type_id
LEFT JOIN material_child_type mct ON mct.id = m.material_child_type_id
ORDER BY ic.year DESC, ic.month DESC, s.id, m.name;

-- Create a summary view for quick overview
DROP VIEW IF EXISTS inventory_summary_by_month CASCADE;

CREATE VIEW inventory_summary_by_month AS
SELECT 
    ic.year,
    ic.month,
    ic.store_id,
    s.name as store_name,
    COUNT(DISTINCT ic.material_id) as material_count,
    SUM(ic.counted_quantity) as total_quantity,
    MIN(ic.created_at) as first_entry,
    MAX(ic.created_at) as last_entry
FROM inventory_count ic
JOIN store s ON s.id = ic.store_id
GROUP BY ic.year, ic.month, ic.store_id, s.name
ORDER BY ic.year DESC, ic.month DESC, ic.store_id;

-- Create a view to find materials with significant quantity changes
DROP VIEW IF EXISTS inventory_quantity_changes CASCADE;

CREATE VIEW inventory_quantity_changes AS
WITH monthly_inventory AS (
    SELECT 
        ic.store_id,
        ic.material_id,
        m.material_number,
        m.name as material_name,
        m.unit,
        ic.year,
        ic.month,
        ic.counted_quantity,
        LAG(ic.counted_quantity) OVER (
            PARTITION BY ic.store_id, ic.material_id 
            ORDER BY ic.year, ic.month
        ) as previous_quantity
    FROM inventory_count ic
    JOIN material m ON m.id = ic.material_id
)
SELECT 
    store_id,
    s.name as store_name,
    material_id,
    material_number,
    material_name,
    unit,
    year,
    month,
    counted_quantity,
    previous_quantity,
    counted_quantity - COALESCE(previous_quantity, 0) as quantity_change,
    CASE 
        WHEN previous_quantity IS NULL OR previous_quantity = 0 THEN NULL
        ELSE ROUND(((counted_quantity - previous_quantity) / previous_quantity * 100)::numeric, 2)
    END as percentage_change
FROM monthly_inventory mi
JOIN store s ON s.id = mi.store_id
WHERE previous_quantity IS NOT NULL
ORDER BY store_id, year DESC, month DESC, ABS(counted_quantity - COALESCE(previous_quantity, 0)) DESC;

-- Create a view for materials missing from inventory
DROP VIEW IF EXISTS materials_not_in_inventory CASCADE;

CREATE VIEW materials_not_in_inventory AS
SELECT 
    m.store_id,
    s.name as store_name,
    m.id as material_id,
    m.material_number,
    m.name as material_name,
    m.unit,
    mt.name as material_type,
    mct.name as material_child_type
FROM material m
JOIN store s ON s.id = m.store_id
LEFT JOIN material_type mt ON mt.id = m.material_type_id
LEFT JOIN material_child_type mct ON mct.id = m.material_child_type_id
WHERE NOT EXISTS (
    SELECT 1 
    FROM inventory_count ic 
    WHERE ic.material_id = m.id
)
AND m.is_active = true
ORDER BY m.store_id, m.name;

-- Grant permissions (adjust user as needed)
GRANT SELECT ON inventory_count_with_materials TO hongming;
GRANT SELECT ON inventory_summary_by_month TO hongming;
GRANT SELECT ON inventory_quantity_changes TO hongming;
GRANT SELECT ON materials_not_in_inventory TO hongming;

-- Add comments for documentation
COMMENT ON VIEW inventory_count_with_materials IS 'Complete inventory counts with material details and store names';
COMMENT ON VIEW inventory_summary_by_month IS 'Monthly summary of inventory counts by store';
COMMENT ON VIEW inventory_quantity_changes IS 'Month-over-month inventory quantity changes';
COMMENT ON VIEW materials_not_in_inventory IS 'Active materials that have never been counted in inventory';

-- Example queries to use these views:

-- 1. Check all inventory for a specific month
-- SELECT * FROM inventory_count_with_materials 
-- WHERE year = 2025 AND month = 7 AND store_id = 1
-- ORDER BY material_name;

-- 2. Get summary for all stores
-- SELECT * FROM inventory_summary_by_month
-- WHERE year = 2025;

-- 3. Find materials with big changes
-- SELECT * FROM inventory_quantity_changes
-- WHERE year = 2025 AND month = 7
-- AND ABS(percentage_change) > 50;

-- 4. Find materials never counted
-- SELECT * FROM materials_not_in_inventory
-- WHERE store_id = 1;

-- 5. Search for specific material by name
-- SELECT * FROM inventory_count_with_materials
-- WHERE material_name ILIKE '%beef%'
-- ORDER BY year DESC, month DESC;