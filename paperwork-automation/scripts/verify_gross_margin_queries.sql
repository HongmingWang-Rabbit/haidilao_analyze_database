-- Verify Monthly Gross Margin Report Queries for May 2025
-- Run this with: psql -U hongming -d haidilao-paperwork -f scripts/verify_gross_margin_queries.sql

\echo '=== MONTHLY GROSS MARGIN REPORT DATA VERIFICATION FOR MAY 2025 ==='
\echo ''

-- 1. Check Store Gross Profit Data (各店毛利率分析)
\echo '1. Store Gross Profit Analysis (各店毛利率分析):'
\echo '   This should show revenue and costs for each store'
\echo ''

SELECT 
    s.name as store_name,
    COALESCE(cr.current_revenue, 0) as "May Revenue",
    COALESCE(cc.current_cost, 0) as "May Cost",
    CASE WHEN COALESCE(cr.current_revenue, 0) > 0 
        THEN ROUND(((COALESCE(cr.current_revenue, 0) - COALESCE(cc.current_cost, 0)) / COALESCE(cr.current_revenue, 0) * 100), 2)
        ELSE 0 END as "May Margin %",
    COALESCE(pr.previous_revenue, 0) as "Apr Revenue",
    COALESCE(pc.previous_cost, 0) as "Apr Cost"
FROM store s
LEFT JOIN (
    SELECT store_id, SUM(sale_amount) as current_revenue
    FROM dish_monthly_sale
    WHERE year = 2025 AND month = 5
    GROUP BY store_id
) cr ON s.id = cr.store_id
LEFT JOIN (
    SELECT 
        mmu.store_id,
        SUM(mmu.material_used * COALESCE(mph.price, 0)) as current_cost
    FROM material_monthly_usage mmu
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
    WHERE mmu.year = 2025 AND mmu.month = 5
    GROUP BY mmu.store_id
) cc ON s.id = cc.store_id
LEFT JOIN (
    SELECT store_id, SUM(sale_amount) as previous_revenue
    FROM dish_monthly_sale
    WHERE year = 2025 AND month = 4
    GROUP BY store_id
) pr ON s.id = pr.store_id
LEFT JOIN (
    SELECT 
        mmu.store_id,
        SUM(mmu.material_used * COALESCE(mph.price, 0)) as previous_cost
    FROM material_monthly_usage mmu
    LEFT JOIN LATERAL (
        SELECT price 
        FROM material_price_history 
        WHERE material_id = mmu.material_id 
            AND store_id = mmu.store_id 
            AND is_active = true
            AND effective_date <= '2025-04-30'
        ORDER BY effective_date DESC
        LIMIT 1
    ) mph ON true
    WHERE mmu.year = 2025 AND mmu.month = 4
    GROUP BY mmu.store_id
) pc ON s.id = pc.store_id
WHERE s.id BETWEEN 1 AND 7
ORDER BY s.id;

\echo ''
\echo '2. Material Cost Analysis Sample (原材料成本变动表):'
\echo '   Top 10 materials by usage with price changes'
\echo ''

WITH material_costs AS (
    SELECT 
        s.name as store_name,
        m.material_number,
        m.name as material_name,
        m.material_type,
        mmu.material_used,
        COALESCE(mph.price, 0) as current_price,
        COALESCE(mph_prev.price, 0) as prev_price,
        ROUND(CASE WHEN COALESCE(mph_prev.price, 0) > 0 
            THEN ((COALESCE(mph.price, 0) - COALESCE(mph_prev.price, 0)) / COALESCE(mph_prev.price, 0) * 100)
            ELSE 0 END, 2) as price_change_pct
    FROM material_monthly_usage mmu
    JOIN material m ON mmu.material_id = m.id
    JOIN store s ON mmu.store_id = s.id
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
    LEFT JOIN LATERAL (
        SELECT price 
        FROM material_price_history 
        WHERE material_id = mmu.material_id 
            AND store_id = mmu.store_id 
            AND is_active = true
            AND effective_date <= '2025-04-30'
        ORDER BY effective_date DESC
        LIMIT 1
    ) mph_prev ON true
    WHERE mmu.year = 2025 AND mmu.month = 5
)
SELECT 
    store_name,
    material_number,
    material_name,
    material_type,
    material_used as "Usage Qty",
    current_price as "May Price",
    prev_price as "Apr Price",
    price_change_pct as "Change %"
FROM material_costs
WHERE store_name = '加拿大一店'
ORDER BY material_used DESC
LIMIT 10;

\echo ''
\echo '3. Monthly Summary Data (月度毛利汇总):'
\echo '   Summary of all stores revenue and margins'
\echo ''

WITH summary AS (
    SELECT 
        s.name as store_name,
        COALESCE(dms.revenue, 0) as revenue,
        COALESCE(cc.cost, 0) as cost,
        COALESCE(dms.revenue, 0) - COALESCE(cc.cost, 0) as gross_profit,
        CASE WHEN COALESCE(dms.revenue, 0) > 0 
            THEN ROUND(((COALESCE(dms.revenue, 0) - COALESCE(cc.cost, 0)) / COALESCE(dms.revenue, 0) * 100), 2)
            ELSE 0 END as margin_pct
    FROM store s
    LEFT JOIN (
        SELECT store_id, SUM(sale_amount) as revenue
        FROM dish_monthly_sale
        WHERE year = 2025 AND month = 5
        GROUP BY store_id
    ) dms ON s.id = dms.store_id
    LEFT JOIN (
        SELECT 
            mmu.store_id,
            SUM(mmu.material_used * COALESCE(mph.price, 0)) as cost
        FROM material_monthly_usage mmu
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
        WHERE mmu.year = 2025 AND mmu.month = 5
        GROUP BY mmu.store_id
    ) cc ON s.id = cc.store_id
    WHERE s.id BETWEEN 1 AND 7
)
SELECT 
    store_name as "Store",
    TO_CHAR(revenue, 'FM999,999,990.00') as "Revenue",
    TO_CHAR(cost, 'FM999,999,990.00') as "Cost",
    TO_CHAR(gross_profit, 'FM999,999,990.00') as "Gross Profit",
    margin_pct || '%' as "Margin %"
FROM summary
UNION ALL
SELECT 
    'TOTAL' as "Store",
    TO_CHAR(SUM(revenue), 'FM999,999,990.00') as "Revenue",
    TO_CHAR(SUM(cost), 'FM999,999,990.00') as "Cost",
    TO_CHAR(SUM(gross_profit), 'FM999,999,990.00') as "Gross Profit",
    CASE WHEN SUM(revenue) > 0 
        THEN ROUND((SUM(gross_profit) / SUM(revenue) * 100), 2) || '%'
        ELSE '0%' END as "Margin %"
FROM summary;

\echo ''
\echo '4. Data Availability Check:'
\echo ''

SELECT 
    'dish_monthly_sale (May)' as data_type,
    COUNT(DISTINCT store_id) as stores,
    COUNT(DISTINCT dish_id) as items,
    TO_CHAR(SUM(sale_amount), 'FM999,999,990.00') as total_value
FROM dish_monthly_sale WHERE year = 2025 AND month = 5
UNION ALL
SELECT 
    'material_monthly_usage (May)',
    COUNT(DISTINCT store_id),
    COUNT(DISTINCT material_id),
    TO_CHAR(SUM(material_used), 'FM999,999,990.00')
FROM material_monthly_usage WHERE year = 2025 AND month = 5
UNION ALL
SELECT 
    'material_price_history (May)',
    COUNT(DISTINCT store_id),
    COUNT(DISTINCT material_id),
    TO_CHAR(AVG(price), 'FM999,999,990.00')
FROM material_price_history 
WHERE effective_date BETWEEN '2025-05-01' AND '2025-05-31' AND is_active = true
UNION ALL
SELECT 
    'dish_price_history (May)',
    COUNT(DISTINCT store_id),
    COUNT(DISTINCT dish_id),
    TO_CHAR(AVG(price), 'FM999,999,990.00')
FROM dish_price_history 
WHERE effective_date BETWEEN '2025-05-01' AND '2025-05-31' AND is_active = true;

\echo ''
\echo '=== END OF VERIFICATION ==='