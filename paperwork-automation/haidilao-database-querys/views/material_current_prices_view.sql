-- Material Current Prices View Query
-- Shows material number, name, and current active prices for each store
-- Created for Haidilao material price analysis

-- ==================================================
-- BASIC QUERY: All materials with current prices
-- ==================================================

-- All materials with their current active prices across all stores
SELECT 
    m.material_number,
    m.name as material_name,
    s.name as store_name,
    s.id as store_id,
    mph.price as current_price,
    mph.currency,
    mph.effective_date,
    mph.created_at as price_updated_at
FROM material m
INNER JOIN material_price_history mph ON m.id = mph.material_id
INNER JOIN store s ON mph.store_id = s.id
WHERE mph.is_active = TRUE
ORDER BY m.material_number, s.id;

-- ==================================================
-- ALTERNATIVE QUERIES FOR SPECIFIC USE CASES
-- ==================================================

-- Query 1: Materials with prices for a specific store (Store 1)
/*
SELECT 
    m.material_number,
    m.name as material_name,
    mph.price as current_price,
    mph.currency,
    mph.effective_date
FROM material m
INNER JOIN material_price_history mph ON m.id = mph.material_id
WHERE mph.store_id = 1 
  AND mph.is_active = TRUE
ORDER BY m.material_number;
*/

-- Query 2: Materials with price comparison across all stores (pivoted view)
/*
SELECT 
    m.material_number,
    m.name as material_name,
    MAX(CASE WHEN mph.store_id = 1 THEN mph.price END) as store_1_price,
    MAX(CASE WHEN mph.store_id = 2 THEN mph.price END) as store_2_price,
    MAX(CASE WHEN mph.store_id = 3 THEN mph.price END) as store_3_price,
    MAX(CASE WHEN mph.store_id = 4 THEN mph.price END) as store_4_price,
    MAX(CASE WHEN mph.store_id = 5 THEN mph.price END) as store_5_price,
    MAX(CASE WHEN mph.store_id = 6 THEN mph.price END) as store_6_price,
    MAX(CASE WHEN mph.store_id = 7 THEN mph.price END) as store_7_price
FROM material m
LEFT JOIN material_price_history mph ON m.id = mph.material_id AND mph.is_active = TRUE
LEFT JOIN store s ON mph.store_id = s.id
GROUP BY m.material_number, m.name
ORDER BY m.material_number;
*/

-- Query 3: Materials without current pricing (missing prices)
/*
SELECT 
    m.material_number,
    m.name as material_name,
    m.material_type_id,
    COUNT(mph.id) as stores_with_pricing
FROM material m
LEFT JOIN material_price_history mph ON m.id = mph.material_id AND mph.is_active = TRUE
GROUP BY m.material_number, m.name, m.material_type_id
HAVING COUNT(mph.id) = 0
ORDER BY m.material_number;
*/

-- Query 4: Price statistics across stores for each material
/*
SELECT 
    m.material_number,
    m.name as material_name,
    COUNT(mph.price) as stores_count,
    MIN(mph.price) as min_price,
    MAX(mph.price) as max_price,
    AVG(mph.price) as avg_price,
    STDDEV(mph.price) as price_variance
FROM material m
INNER JOIN material_price_history mph ON m.id = mph.material_id
WHERE mph.is_active = TRUE
GROUP BY m.material_number, m.name
HAVING COUNT(mph.price) > 1  -- Only materials with prices in multiple stores
ORDER BY price_variance DESC;
*/

-- Query 5: Recently updated prices (last 30 days)
/*
SELECT 
    m.material_number,
    m.name as material_name,
    s.name as store_name,
    mph.price as current_price,
    mph.currency,
    mph.effective_date,
    mph.created_at as price_updated_at
FROM material m
INNER JOIN material_price_history mph ON m.id = mph.material_id
INNER JOIN store s ON mph.store_id = s.id
WHERE mph.is_active = TRUE
  AND mph.created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY mph.created_at DESC;
*/

-- ==================================================
-- CREATE VIEW FOR EASY ACCESS
-- ==================================================

-- Uncomment to create a permanent view for this query
/*
CREATE OR REPLACE VIEW v_material_current_prices AS
SELECT 
    m.material_number,
    m.name as material_name,
    s.name as store_name,
    s.id as store_id,
    mph.price as current_price,
    mph.currency,
    mph.effective_date,
    mph.created_at as price_updated_at
FROM material m
INNER JOIN material_price_history mph ON m.id = mph.material_id
INNER JOIN store s ON mph.store_id = s.id
WHERE mph.is_active = TRUE;

-- Usage: SELECT * FROM v_material_current_prices ORDER BY material_number, store_id;
*/

-- ==================================================
-- USAGE EXAMPLES
-- ==================================================

-- Example 1: Find specific material across all stores
-- SELECT * FROM v_material_current_prices WHERE material_number = '4000360';

-- Example 2: Find all materials for Store 1
-- SELECT * FROM v_material_current_prices WHERE store_id = 1;

-- Example 3: Find materials with prices above $10
-- SELECT * FROM v_material_current_prices WHERE current_price > 10.00;

-- Example 4: Count materials by store
-- SELECT store_name, COUNT(*) as material_count FROM v_material_current_prices GROUP BY store_name; 