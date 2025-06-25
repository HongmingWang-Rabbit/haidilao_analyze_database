-- Sample data for dish and material automation
-- Based on the Excel structure analysis from CA02-盘点结果-2505-待回复.xls

-- ========================================
-- DISTRICT DATA
-- ========================================

INSERT INTO district (name, description, currency) VALUES
('Canada', 'Canadian Operations', 'CAD'),
('USA', 'United States Operations', 'USD'),
('China', 'Chinese Operations', 'CNY')
ON CONFLICT (name) DO NOTHING;

-- ========================================
-- DISH TYPE HIERARCHY
-- ========================================

-- 菜品大类
INSERT INTO dish_type (name, description, sort_order) VALUES
('锅底类', 'Hot Pot Base Categories', 1),
('素菜类', 'Vegetable Dishes', 2),
('肉类', 'Meat Dishes', 3),
('海鲜类', 'Seafood Dishes', 4),
('饮品类', 'Beverages', 5),
('小料类', 'Condiments and Sauces', 6)
ON CONFLICT (name) DO NOTHING;

-- 菜品子类
INSERT INTO dish_child_type (name, dish_type_id, description, sort_order) 
SELECT '锅底类', dt.id, 'Hot Pot Base Sub-category', 1
FROM dish_type dt WHERE dt.name = '锅底类'
ON CONFLICT (dish_type_id, name) DO NOTHING;

-- ========================================
-- SAMPLE MATERIALS
-- ========================================

INSERT INTO material (name, material_number, description, unit, package_spec) VALUES
('清油底料', '3000759', '清油底料（300G*40包/件）', '公斤', '300G*40包/件'),
('三花淡奶', '1500882', '三花淡奶（354ML*48瓶/箱）', '瓶', '354ML*48瓶/箱'),
('菌汤火锅底料', '4514602', '菌汤火锅底料（105G*60袋/箱）', '公斤', '105G*60袋/箱')
ON CONFLICT (material_number) DO NOTHING;

-- ========================================
-- SAMPLE DISHES
-- ========================================

-- Get the dish_child_type_id for 锅底类
INSERT INTO dish (name, system_name, full_code, short_code, dish_child_type_id, specification, unit, serving_size_kg, wastage_rate)
SELECT 
    '清油麻辣火锅', '清油麻辣火锅', '1060061', NULL,
    dct.id, '单锅', '锅', 1.2000, 1.0
FROM dish_child_type dct 
JOIN dish_type dt ON dct.dish_type_id = dt.id 
WHERE dt.name = '锅底类' AND dct.name = '锅底类'
ON CONFLICT (full_code) DO NOTHING;

INSERT INTO dish (name, system_name, full_code, short_code, dish_child_type_id, specification, unit, serving_size_kg, wastage_rate)
SELECT 
    '清油豆花鱼', '清油豆花鱼', '90001518', NULL,
    dct.id, '单锅', '锅', 1.2000, 1.0
FROM dish_child_type dct 
JOIN dish_type dt ON dct.dish_type_id = dt.id 
WHERE dt.name = '锅底类' AND dct.name = '锅底类'
ON CONFLICT (full_code) DO NOTHING;

INSERT INTO dish (name, system_name, full_code, short_code, dish_child_type_id, specification, unit, serving_size_kg, wastage_rate)
SELECT 
    '三鲜猪骨火锅', '猪骨汤', '1060062', NULL,
    dct.id, '单锅', '锅', 0.1500, 1.0
FROM dish_child_type dct 
JOIN dish_type dt ON dct.dish_type_id = dt.id 
WHERE dt.name = '锅底类' AND dct.name = '锅底类'
ON CONFLICT (full_code) DO NOTHING;

INSERT INTO dish (name, system_name, full_code, short_code, dish_child_type_id, specification, unit, serving_size_kg, wastage_rate)
SELECT 
    '菌汤火锅', '菌汤火锅', '1060063', NULL,
    dct.id, '单锅', '锅', 0.4200, 1.0
FROM dish_child_type dct 
JOIN dish_type dt ON dct.dish_type_id = dt.id 
WHERE dt.name = '锅底类' AND dct.name = '锅底类'
ON CONFLICT (full_code) DO NOTHING;

-- ========================================
-- DISH-MATERIAL RELATIONSHIPS (BOM)
-- ========================================

-- 清油麻辣火锅 -> 清油底料
INSERT INTO dish_material (dish_id, material_id, standard_quantity, unit, conversion_factor)
SELECT 
    d.id, m.id, 396.000, '公斤', 1.0
FROM dish d, material m
WHERE d.full_code = '1060061' AND m.material_number = '3000759'
ON CONFLICT (dish_id, material_id) DO NOTHING;

-- 三鲜猪骨火锅 -> 三花淡奶
INSERT INTO dish_material (dish_id, material_id, standard_quantity, unit, conversion_factor)
SELECT 
    d.id, m.id, 0.354, '瓶', 1.0
FROM dish d, material m
WHERE d.full_code = '1060062' AND m.material_number = '1500882'
ON CONFLICT (dish_id, material_id) DO NOTHING;

-- 菌汤火锅 -> 菌汤火锅底料
INSERT INTO dish_material (dish_id, material_id, standard_quantity, unit, conversion_factor)
SELECT 
    d.id, m.id, 1.000, '公斤', 1.0
FROM dish d, material m
WHERE d.full_code = '1060063' AND m.material_number = '4514602'
ON CONFLICT (dish_id, material_id) DO NOTHING;

-- ========================================
-- SAMPLE PRICE HISTORY
-- ========================================

-- Get Canada district ID for material prices
INSERT INTO material_price_history (material_id, district_id, price, currency, effective_date, is_active, created_by)
SELECT 
    m.id, d.id, 25.50, 'CAD', '2025-01-01', TRUE, 'system'
FROM material m, district d
WHERE m.material_number = '3000759' AND d.name = 'Canada'
ON CONFLICT (material_id, district_id, effective_date) DO NOTHING;

INSERT INTO material_price_history (material_id, district_id, price, currency, effective_date, is_active, created_by)
SELECT 
    m.id, d.id, 48.75, 'CAD', '2025-01-01', TRUE, 'system'
FROM material m, district d
WHERE m.material_number = '1500882' AND d.name = 'Canada'
ON CONFLICT (material_id, district_id, effective_date) DO NOTHING;

INSERT INTO material_price_history (material_id, district_id, price, currency, effective_date, is_active, created_by)
SELECT 
    m.id, d.id, 32.80, 'CAD', '2025-01-01', TRUE, 'system'
FROM material m, district d
WHERE m.material_number = '4514602' AND d.name = 'Canada'
ON CONFLICT (material_id, district_id, effective_date) DO NOTHING;

-- Sample dish prices (assuming store exists)
-- You'll need to run this after stores are properly linked to districts
/*
INSERT INTO dish_price_history (dish_id, store_id, price, currency, effective_date, is_active, created_by)
SELECT 
    d.id, s.id, 0.00, 'CAD', '2025-01-01', TRUE, 'system'
FROM dish d, store s
WHERE d.full_code = '1060061' AND s.name LIKE '%加拿大%'
ON CONFLICT (dish_id, store_id, effective_date) DO NOTHING;
*/

-- ========================================
-- SAMPLE INVENTORY COUNT DATA
-- ========================================

-- This would be populated from Excel imports
-- Sample structure for reference:
/*
INSERT INTO inventory_count (
    store_id, dish_id, count_date, period_label,
    actual_quantity, theoretical_quantity, variance, variance_amount,
    remarks, combo_usage, status, created_by
)
SELECT 
    s.id, d.id, '2025-05-31', '2505',
    6.0, 7.20, -1.20, -30.00,
    '多使用30kg', 62.7, 'PENDING', 'excel_import'
FROM store s, dish d
WHERE s.name LIKE '%加拿大二店%' AND d.full_code = '1060061'
ON CONFLICT (store_id, dish_id, count_date, period_label) DO NOTHING;
*/

-- ========================================
-- HELPFUL QUERIES FOR VALIDATION
-- ========================================

-- Verify the data structure
/*
-- Check dish hierarchy
SELECT 
    dt.name as dish_type,
    dct.name as dish_child_type,
    d.name as dish_name,
    d.full_code,
    d.specification
FROM dish d
JOIN dish_child_type dct ON d.dish_child_type_id = dct.id
JOIN dish_type dt ON dct.dish_type_id = dt.id
ORDER BY dt.name, dct.name, d.name;

-- Check dish-material relationships
SELECT 
    d.name as dish_name,
    d.full_code,
    m.name as material_name,
    m.material_number,
    dm.standard_quantity,
    dm.unit
FROM dish_material dm
JOIN dish d ON dm.dish_id = d.id
JOIN material m ON dm.material_id = m.id
ORDER BY d.name, m.name;

-- Check current material prices
SELECT 
    m.name as material_name,
    m.material_number,
    dist.name as district,
    mph.price,
    mph.currency,
    mph.effective_date
FROM material_price_history mph
JOIN material m ON mph.material_id = m.id
JOIN district dist ON mph.district_id = dist.id
WHERE mph.is_active = TRUE
ORDER BY m.name, dist.name;
*/ 