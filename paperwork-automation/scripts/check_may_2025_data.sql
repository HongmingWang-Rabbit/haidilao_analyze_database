-- Check May 2025 Data Availability
-- Run with: psql -U hongming -d haidilao-paperwork -f scripts/check_may_2025_data.sql

\echo 'MAY 2025 DATA AVAILABILITY CHECK'
\echo '================================'
\echo ''

-- 1. Dish Monthly Sales
\echo '1. Dish Monthly Sales (May 2025):'
SELECT 
    COUNT(DISTINCT store_id) as stores, 
    COUNT(DISTINCT dish_id) as dishes,
    TO_CHAR(SUM(sale_amount), 'FM999,999,990.00') as total_revenue
FROM dish_monthly_sale 
WHERE year = 2025 AND month = 5;

-- 2. Material Monthly Usage
\echo ''
\echo '2. Material Monthly Usage (May 2025):'
SELECT 
    COUNT(DISTINCT store_id) as stores,
    COUNT(DISTINCT material_id) as materials,
    TO_CHAR(SUM(material_used), 'FM999,999,990.00') as total_usage
FROM material_monthly_usage 
WHERE year = 2025 AND month = 5;

-- 3. Material Prices
\echo ''
\echo '3. Material Price History (May 2025):'
SELECT 
    COUNT(DISTINCT store_id) as stores,
    COUNT(DISTINCT material_id) as materials,
    COUNT(*) as price_records
FROM material_price_history 
WHERE effective_date BETWEEN '2025-05-01' AND '2025-05-31'
    AND is_active = true;

-- 4. Daily Reports
\echo ''
\echo '4. Daily Reports (May 2025):'
SELECT 
    COUNT(DISTINCT store_id) as stores,
    COUNT(*) as days,
    TO_CHAR(SUM(revenue_tax_not_included), 'FM999,999,990.00') as total_revenue,
    TO_CHAR(SUM(discount_total), 'FM999,999,990.00') as total_discounts
FROM daily_report 
WHERE date BETWEEN '2025-05-01' AND '2025-05-31';

-- 5. Discount Details
\echo ''
\echo '5. Discount Details (May 2025):'
SELECT 
    dt.name as discount_type,
    COUNT(DISTINCT dd.store_id) as stores,
    COUNT(*) as records,
    TO_CHAR(SUM(dd.discount_amount), 'FM999,999,990.00') as total_amount
FROM daily_discount_detail dd
JOIN discount_type dt ON dd.discount_type_id = dt.id
WHERE dd.date BETWEEN '2025-05-01' AND '2025-05-31'
GROUP BY dt.name
ORDER BY SUM(dd.discount_amount) DESC;

-- 6. Data Summary
\echo ''
\echo '6. SUMMARY - Data Availability by Month:'
SELECT 
    year,
    month,
    COUNT(DISTINCT store_id) as stores,
    COUNT(DISTINCT dish_id) as dishes,
    TO_CHAR(SUM(sale_amount), 'FM999,999,990.00') as revenue
FROM dish_monthly_sale
WHERE (year = 2025 AND month <= 6) OR (year = 2024 AND month >= 5)
GROUP BY year, month
ORDER BY year DESC, month DESC
LIMIT 10;

-- 7. Check if we can generate report
\echo ''
\echo '7. REPORT READINESS CHECK:'
WITH data_check AS (
    SELECT 
        (SELECT COUNT(*) FROM dish_monthly_sale WHERE year = 2025 AND month = 5) > 0 as has_dish_sales,
        (SELECT COUNT(*) FROM material_monthly_usage WHERE year = 2025 AND month = 5) > 0 as has_material_usage,
        (SELECT COUNT(*) FROM material_price_history WHERE effective_date BETWEEN '2025-05-01' AND '2025-05-31') > 0 as has_prices,
        (SELECT COUNT(*) FROM daily_discount_detail WHERE date BETWEEN '2025-05-01' AND '2025-05-31') > 0 as has_discounts
)
SELECT 
    CASE WHEN has_dish_sales THEN '✅ Dish Sales' ELSE '❌ Dish Sales' END as dish_sales_status,
    CASE WHEN has_material_usage THEN '✅ Material Usage' ELSE '❌ Material Usage' END as material_usage_status,
    CASE WHEN has_prices THEN '✅ Material Prices' ELSE '❌ Material Prices' END as prices_status,
    CASE WHEN has_discounts THEN '✅ Discount Data' ELSE '❌ Discount Data' END as discount_status,
    CASE 
        WHEN has_dish_sales AND has_material_usage AND has_prices 
        THEN '✅ READY to generate monthly gross margin report!' 
        ELSE '❌ MISSING DATA - Run historical extraction first!' 
    END as overall_status
FROM data_check;

\echo ''
\echo '================================'
\echo 'END OF DATA CHECK'