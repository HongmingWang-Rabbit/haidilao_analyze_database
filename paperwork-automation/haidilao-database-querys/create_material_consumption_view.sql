-- View to calculate actual material consumption (usage minus inventory)
-- This represents the true material consumed during the period

DROP VIEW IF EXISTS material_consumption_by_month CASCADE;

CREATE VIEW material_consumption_by_month AS
SELECT 
    m.store_id,
    s.name as store_name,
    m.id as material_id,
    m.material_number,
    m.name as material_name,
    m.unit,
    mt.name as material_type,
    mct.name as material_child_type,
    COALESCE(mmu.year, ic.year) as year,
    COALESCE(mmu.month, ic.month) as month,
    COALESCE(mmu.material_used, 0) as material_used,
    COALESCE(ic.counted_quantity, 0) as ending_inventory,
    -- Actual consumption = Used - Ending Inventory (cannot be negative)
    GREATEST(
        COALESCE(mmu.material_used, 0) - COALESCE(ic.counted_quantity, 0), 
        0
    ) as actual_consumption,
    -- Consumption rate (percentage of material used that was consumed)
    CASE 
        WHEN COALESCE(mmu.material_used, 0) > 0 
        THEN (GREATEST(COALESCE(mmu.material_used, 0) - COALESCE(ic.counted_quantity, 0), 0) / mmu.material_used * 100)
        ELSE 0
    END as consumption_rate,
    mph.price as unit_price,
    -- Cost of consumed materials
    GREATEST(
        COALESCE(mmu.material_used, 0) - COALESCE(ic.counted_quantity, 0), 
        0
    ) * COALESCE(mph.price, 0) as consumption_cost,
    -- Value of ending inventory
    COALESCE(ic.counted_quantity, 0) * COALESCE(mph.price, 0) as inventory_value
FROM material m
JOIN store s ON s.id = m.store_id
LEFT JOIN material_type mt ON mt.id = m.material_type_id
LEFT JOIN material_child_type mct ON mct.id = m.material_child_type_id
LEFT JOIN material_monthly_usage mmu ON 
    mmu.material_id = m.id 
FULL OUTER JOIN inventory_count ic ON 
    ic.material_id = m.id
    AND ic.year = mmu.year
    AND ic.month = mmu.month
    AND ic.store_id = mmu.store_id
LEFT JOIN material_price_history mph ON 
    mph.material_id = m.id 
    AND mph.store_id = m.store_id
    AND mph.effective_year = COALESCE(mmu.year, ic.year)
    AND mph.effective_month = COALESCE(mmu.month, ic.month)
    AND mph.is_active = true
WHERE m.is_active = true
    AND (mmu.material_used > 0 OR ic.counted_quantity > 0)
ORDER BY m.store_id, year DESC, month DESC, actual_consumption DESC;

-- Create summary view by store and month
DROP VIEW IF EXISTS material_consumption_summary CASCADE;

CREATE VIEW material_consumption_summary AS
SELECT 
    store_id,
    store_name,
    year,
    month,
    COUNT(DISTINCT material_id) as material_count,
    SUM(material_used) as total_used,
    SUM(ending_inventory) as total_inventory,
    SUM(actual_consumption) as total_consumed,
    AVG(consumption_rate) as avg_consumption_rate,
    SUM(consumption_cost) as total_consumption_cost,
    SUM(inventory_value) as total_inventory_value
FROM material_consumption_by_month
GROUP BY store_id, store_name, year, month
ORDER BY year DESC, month DESC, store_id;

-- Create view for high-value consumption items
DROP VIEW IF EXISTS high_value_consumption CASCADE;

CREATE VIEW high_value_consumption AS
SELECT 
    store_name,
    material_number,
    material_name,
    unit,
    material_type,
    year,
    month,
    material_used,
    ending_inventory,
    actual_consumption,
    unit_price,
    consumption_cost,
    inventory_value
FROM material_consumption_by_month
WHERE consumption_cost > 100  -- Materials with consumption cost > $100
ORDER BY consumption_cost DESC;

-- Grant permissions
GRANT SELECT ON material_consumption_by_month TO hongming;
GRANT SELECT ON material_consumption_summary TO hongming;
GRANT SELECT ON high_value_consumption TO hongming;

-- Add comments
COMMENT ON VIEW material_consumption_by_month IS 'Actual material consumption calculated as usage minus ending inventory';
COMMENT ON VIEW material_consumption_summary IS 'Monthly summary of material consumption by store';
COMMENT ON VIEW high_value_consumption IS 'High-value material consumption items (>$100)';

-- Sample queries:

-- 1. Get material consumption for a specific store and month
-- SELECT * FROM material_consumption_by_month
-- WHERE store_id = 1 AND year = 2025 AND month = 7
-- ORDER BY actual_consumption DESC;

-- 2. Get summary for all stores
-- SELECT * FROM material_consumption_summary
-- WHERE year = 2025;

-- 3. Find materials with high inventory relative to usage
-- SELECT store_name, material_name, material_used, ending_inventory,
--        CASE WHEN material_used > 0 
--             THEN ROUND((ending_inventory / material_used * 100)::numeric, 2) 
--             ELSE 0 END as inventory_percentage
-- FROM material_consumption_by_month
-- WHERE year = 2025 AND month = 7
--   AND ending_inventory > material_used * 0.5  -- Inventory > 50% of usage
-- ORDER BY inventory_percentage DESC;