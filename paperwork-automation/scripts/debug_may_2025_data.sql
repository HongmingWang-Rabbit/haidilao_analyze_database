-- Debug May 2025 Data for Gross Margin Report
-- Run with: psql -U hongming -d haidilao-paperwork -f scripts/debug_may_2025_data.sql

\echo '=== DEBUG MAY 2025 DATA FOR GROSS MARGIN REPORT ==='
\echo ''

-- 1. Check if we have ANY dish sales data
\echo '1. Dish Monthly Sales Data Check:'
SELECT year, month, COUNT(DISTINCT store_id) as stores, COUNT(*) as records
FROM dish_monthly_sale
WHERE (year = 2025 AND month IN (4, 5)) OR (year = 2024 AND month = 5)
GROUP BY year, month
ORDER BY year DESC, month DESC;

-- 2. Check if we have ANY material usage data
\echo ''
\echo '2. Material Monthly Usage Data Check:'
SELECT year, month, COUNT(DISTINCT store_id) as stores, COUNT(*) as records
FROM material_monthly_usage
WHERE (year = 2025 AND month IN (4, 5)) OR (year = 2024 AND month = 5)
GROUP BY year, month
ORDER BY year DESC, month DESC;

-- 3. Check material price history
\echo ''
\echo '3. Material Price History Check:'
SELECT 
    EXTRACT(YEAR FROM effective_date) as year,
    EXTRACT(MONTH FROM effective_date) as month,
    COUNT(DISTINCT store_id) as stores,
    COUNT(DISTINCT material_id) as materials,
    COUNT(*) as price_records
FROM material_price_history
WHERE effective_date BETWEEN '2024-05-01' AND '2025-05-31'
    AND is_active = true
GROUP BY EXTRACT(YEAR FROM effective_date), EXTRACT(MONTH FROM effective_date)
ORDER BY year DESC, month DESC
LIMIT 10;

-- 4. Check specific store data for May 2025
\echo ''
\echo '4. Store 1 (加拿大一店) May 2025 Data:'
\echo '   Dish Sales:'
SELECT COUNT(*) as dish_count, SUM(sale_amount) as total_sales
FROM dish_monthly_sale
WHERE store_id = 1 AND year = 2025 AND month = 5;

\echo '   Material Usage:'
SELECT COUNT(*) as material_count, SUM(material_used) as total_usage
FROM material_monthly_usage
WHERE store_id = 1 AND year = 2025 AND month = 5;

\echo '   Material Prices:'
SELECT COUNT(DISTINCT material_id) as materials_with_prices
FROM material_price_history
WHERE store_id = 1 
    AND effective_date <= '2025-05-31'
    AND is_active = true;

-- 5. Check if tables are completely empty
\echo ''
\echo '5. Table Record Counts:'
SELECT 
    'dish_monthly_sale' as table_name, COUNT(*) as total_records
FROM dish_monthly_sale
UNION ALL
SELECT 'material_monthly_usage', COUNT(*) FROM material_monthly_usage
UNION ALL
SELECT 'material_price_history', COUNT(*) FROM material_price_history
UNION ALL
SELECT 'dish_price_history', COUNT(*) FROM dish_price_history
UNION ALL
SELECT 'daily_report', COUNT(*) FROM daily_report;

-- 6. Check dish and material existence
\echo ''
\echo '6. Basic Data Check:'
SELECT 
    'Total Dishes' as item, COUNT(*) as count FROM dish
UNION ALL
SELECT 'Total Materials', COUNT(*) FROM material
UNION ALL
SELECT 'Total Stores', COUNT(*) FROM store;

-- 7. Sample query to test the gross margin calculation
\echo ''
\echo '7. Test Gross Margin Query for Store 1, May 2025:'
WITH test_data AS (
    SELECT 
        s.name as store_name,
        COALESCE(SUM(dms.sale_amount), 0) as revenue,
        COALESCE(SUM(mmu.material_used * mph.price), 0) as cost
    FROM store s
    LEFT JOIN dish_monthly_sale dms ON s.id = dms.store_id
        AND dms.year = 2025 AND dms.month = 5
    LEFT JOIN material_monthly_usage mmu ON s.id = mmu.store_id
        AND mmu.year = 2025 AND mmu.month = 5
    LEFT JOIN LATERAL (
        SELECT price 
        FROM material_price_history 
        WHERE material_id = mmu.material_id 
            AND store_id = mmu.store_id 
            AND is_active = true
            AND effective_date <= '2025-05-31'
        ORDER BY effective_date DESC
        LIMIT 1
    ) mph ON true
    WHERE s.id = 1
    GROUP BY s.name
)
SELECT 
    store_name,
    revenue,
    cost,
    CASE WHEN revenue > 0 THEN ROUND((revenue - cost) / revenue * 100, 2) ELSE 0 END as margin_pct
FROM test_data;

\echo ''
\echo '=== END DEBUG ==='