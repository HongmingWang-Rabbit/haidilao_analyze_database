-- Monthly targets for June 2025
-- Based on data provided for all Haidilao Canada stores

INSERT INTO store_monthly_target (
    store_id, 
    month, 
    turnover_rate, 
    table_avg_spending, 
    revenue, 
    labor_percentage, 
    gross_revenue, 
    monthly_CAD_USD_rate
) VALUES
-- 加拿大一店 (Store ID: 1)
(1, '2025-06-01', 4.20, 151.98, 1014900.00, 41.0, 50000, 0.695265),

-- 加拿大二店 (Store ID: 2) 
(2, '2025-06-01', 3.50, 140.21, 530000, 42.0, 10000, 0.695265),

-- 加拿大三店 (Store ID: 3)
(3, '2025-06-01', 5.20, 124.00, 928500.00, 38.5, 80000, 0.695265),

-- 加拿大四店 (Store ID: 4)
(4, '2025-06-01', 4.00, 130.95, 1100000, 38.5, 121002, 0.695265),

-- 加拿大五店 (Store ID: 5)
(5, '2025-06-01', 5.10, 135.95, 1144000, 38.5, 122350.8, 0.695265),

-- 加拿大六店 (Store ID: 6)
(6, '2025-06-01', 3.60, 117.39, 710000, 39.0, 30000, 0.695265),

-- 加拿大七店 (Store ID: 7)
(7, '2025-06-01', 3.85, 148.86, 980000.00, 41.0, 50000, 0.695265);

-- Summary of inserted targets:
-- Total stores: 7
-- Target month: June 2025 (2025-06-01)
-- Total revenue target: 6,407,400 CAD
-- Average turnover rate: 4.21
-- Average table spending: 135.62 CAD
-- CAD/USD exchange rate: 0.695265
    