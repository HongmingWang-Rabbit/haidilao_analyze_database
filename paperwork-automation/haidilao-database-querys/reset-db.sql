-- WARNING: This will delete all your reporting data. Use with caution.
-- UPDATED SCHEMA: Store-specific dishes and materials

-- Drop tables if they exist (in reverse dependency order)
-- First drop all tables that depend on other tables

-- Drop monthly performance tables (new)
DROP TABLE IF EXISTS monthly_combo_dish_sale;
DROP TABLE IF EXISTS material_monthly_usage;
DROP TABLE IF EXISTS dish_monthly_sale;

-- Drop combo tables
DROP TABLE IF EXISTS combo;

-- Drop inventory and price history tables
DROP TABLE IF EXISTS inventory_count;
DROP TABLE IF EXISTS material_price_history;
DROP TABLE IF EXISTS dish_price_history;

-- Drop dish-material relationship table
DROP TABLE IF EXISTS dish_material;

-- Drop dish and material tables
DROP TABLE IF EXISTS dish;
DROP TABLE IF EXISTS material;

-- Drop material type tables
DROP TABLE IF EXISTS material_child_type;
DROP TABLE IF EXISTS material_type;

-- Drop dish type tables
DROP TABLE IF EXISTS dish_child_type;
DROP TABLE IF EXISTS dish_type;

-- Drop store operational tables
DROP TABLE IF EXISTS store_monthly_time_target;
DROP TABLE IF EXISTS store_monthly_target;
DROP TABLE IF EXISTS store_time_report;
DROP TABLE IF EXISTS daily_report;

-- Drop basic tables
DROP TABLE IF EXISTS time_segment;
DROP TABLE IF EXISTS store;
DROP TABLE IF EXISTS district;

-- ========================================
-- DISTRICT & STORE MANAGEMENT
-- ========================================

CREATE TABLE district (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,           -- 区域名称 (e.g., "Canada", "USA", "China")
    description VARCHAR,                    -- 区域描述
    currency VARCHAR(3) DEFAULT 'CAD',     -- 默认货币
    is_active BOOLEAN DEFAULT TRUE,        -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE store (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,          -- 门店名称
    district_id INTEGER REFERENCES district(id), -- 外键：区域
    country VARCHAR,                       -- 国家
    manager VARCHAR,                       -- 国家负责人
    opened_at DATE,                        -- 开业日期
    seats_total INTEGER,                   -- 所有餐位数 (fixed capacity)
    is_active BOOLEAN DEFAULT TRUE,        -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- STORE OPERATIONAL REPORTING TABLES
-- ========================================

CREATE TABLE daily_report (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id), -- 外键：门店
    date DATE,                             -- 日期
    is_holiday BOOLEAN,                    -- 是否节假日
    tables_served NUMERIC(10, 2),                -- 营业桌数
    tables_served_validated NUMERIC(10, 2),      -- 营业桌数(考核)
    turnover_rate NUMERIC(6, 3),          -- 翻台率(考核)
    revenue_tax_not_included NUMERIC(10, 2),  -- 营业收入(含税)
    takeout_tables NUMERIC(10, 2),        -- 营业桌数(考核)(外卖)
    customers NUMERIC(10, 2),                    -- 就餐人数
    discount_total NUMERIC(10, 2),        -- 优惠总金额(含税)
    UNIQUE(store_id, date)                -- Unique constraint for UPSERT
);

CREATE TABLE time_segment (
    id SERIAL PRIMARY KEY,
    label VARCHAR NOT NULL UNIQUE,        -- 分时段标签，例如 "08:00-13:59"
    start_time TIME,                      -- 开始时间
    end_time TIME,                        -- 结束时间
    description VARCHAR                   -- 描述（可选）
);

CREATE TABLE store_time_report (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id),             -- 外键：门店
    date DATE,                                          -- 日期
    time_segment_id INTEGER REFERENCES time_segment(id), -- 外键：分时段
    is_holiday BOOLEAN,                                -- 是否节假日
    tables_served_validated NUMERIC(10, 2),                   -- 营业桌数(考核)
    turnover_rate NUMERIC(6, 3),                       -- 翻台率(考核)
    UNIQUE(store_id, date, time_segment_id)            -- Unique constraint for UPSERT
);

CREATE TABLE store_monthly_target (
  id SERIAL PRIMARY KEY,                     -- 主键，自增
  store_id INT REFERENCES store(id),         -- 外键：门店 ID
  month DATE NOT NULL,                       -- 目标月份（建议使用每月第一天作为标识）

  turnover_rate NUMERIC(6, 3),               -- 目标翻台率
  table_avg_spending NUMERIC(10, 2),         -- 目标每桌消费金额
  revenue NUMERIC(14, 2),                    -- 营业收入目标（含税）
  labor_percentage NUMERIC(5, 2),            -- 人工成本占比（百分比形式：如 28.5）
  gross_revenue NUMERIC(14, 2),              -- 毛收入目标
  
  UNIQUE(store_id, month)                    -- 防止重复插入同一店铺同一月目标
);

CREATE TABLE store_monthly_time_target (
  id SERIAL PRIMARY KEY,                     -- 主键，自增
  store_id INT REFERENCES store(id),         -- 外键：门店 ID
  month DATE NOT NULL,                       -- 目标月份（建议使用每月第一天作为标识）
  time_segment_id INT REFERENCES time_segment(id), -- 外键：分时段 ID
  
  turnover_rate NUMERIC(6, 3),               -- 该时段目标翻台率
  
  UNIQUE(store_id, month, time_segment_id)   -- 防止重复插入同一店铺同一月同一时段
);

-- ========================================
-- DISH & MATERIAL MANAGEMENT
-- ========================================

-- 菜品大类 (e.g., "锅底类", "素菜类", "肉类")
CREATE TABLE dish_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,          -- 大类名称
    description VARCHAR,                   -- 描述
    sort_order INTEGER DEFAULT 0,         -- 排序顺序
    is_active BOOLEAN DEFAULT TRUE,       -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 菜品子类 (e.g., "锅底类" -> "单锅", "拼锅", "四宫格")
CREATE TABLE dish_child_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,                -- 子类名称
    dish_type_id INTEGER REFERENCES dish_type(id), -- 外键：菜品大类
    description VARCHAR,                  -- 描述
    sort_order INTEGER DEFAULT 0,        -- 排序顺序
    is_active BOOLEAN DEFAULT TRUE,      -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dish_type_id, name)           -- 同一大类下子类名称不能重复
);

-- 物料大类 (e.g., "成本-荤菜类", "成本-素菜类", "成本-酒水类")
CREATE TABLE material_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,          -- 大类名称 (from 187-一级分类)
    description VARCHAR,                   -- 描述
    sort_order INTEGER DEFAULT 0,         -- 排序顺序
    is_active BOOLEAN DEFAULT TRUE,       -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 物料子类 (e.g., "物料消耗" -> "清洁类", "纸巾类", "餐具类")
CREATE TABLE material_child_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,                -- 子类名称 (from 187-二级分类)
    material_type_id INTEGER REFERENCES material_type(id), -- 外键：物料大类
    description VARCHAR,                  -- 描述
    sort_order INTEGER DEFAULT 0,        -- 排序顺序
    is_active BOOLEAN DEFAULT TRUE,      -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(material_type_id, name)       -- 同一大类下子类名称不能重复
);

-- 菜品主表
CREATE TABLE dish (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,               -- 菜品名称
    system_name VARCHAR,                 -- 菜品名称（系统）
    full_code VARCHAR NOT NULL,          -- 菜品编码 (e.g., "1060061")
    short_code VARCHAR,                  -- 菜品短编码
    size VARCHAR,                        -- 规格/尺寸 (e.g., "单锅", "拼锅", "四宫格", "小份", "大份")
    dish_child_type_id INTEGER REFERENCES dish_child_type(id), -- 外键：菜品子类
    specification VARCHAR,               -- 规格 (e.g., "单锅", "拼锅", "四宫格")
    unit VARCHAR DEFAULT '份',           -- 菜品单位
    serving_size_kg NUMERIC(8, 4),      -- 出品分量(kg)
    broad_type VARCHAR,                  -- 菜品8大类描述 (e.g., "荤菜类", "素菜类", "锅底类", "酒水类", "小吃类")
    is_active BOOLEAN DEFAULT TRUE,     -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(full_code, size)             -- 同一编码不同规格可以存在
);

-- 物料主表
-- 物料主表 (STORE-SPECIFIC)
CREATE TABLE material (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id), -- 外键：门店 (NEW: Store-specific)
    name VARCHAR NOT NULL,              -- 物料名称/描述
    material_number VARCHAR NOT NULL,   -- 物料号 (e.g., "3000759")
    description VARCHAR,                -- 详细描述
    unit VARCHAR NOT NULL,              -- 单位 (e.g., "kg", "g", "oz", "瓶", "包")
    package_spec VARCHAR,               -- 包装规格 (e.g., "300G*40包/件")
    material_child_type_id INTEGER REFERENCES material_child_type(id), -- 外键：物料子类 (可为空)
    material_type_id INTEGER REFERENCES material_type(id), -- 外键：物料大类
    is_active BOOLEAN DEFAULT TRUE,    -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, material_number)  -- 同一门店同一物料号唯一
);

-- 菜品-物料关系表 (BOM - Bill of Materials)
-- 菜品物料关系表 (STORE-SPECIFIC)
CREATE TABLE dish_material (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES dish(id), -- 外键：菜品
    material_id INTEGER REFERENCES material(id), -- 外键：物料
    store_id INTEGER REFERENCES store(id), -- 确保一致性
    standard_quantity NUMERIC(12, 6) NOT NULL, -- 标准用量
    loss_rate NUMERIC(5, 2) DEFAULT 1.0, -- 损耗率 (默认1.0 = 无损耗)
    unit_conversion_rate NUMERIC(12, 6) DEFAULT 1.0 NOT NULL, -- 单位转换率 (从物料单位字段提取，默认1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dish_id, material_id, store_id) -- Store-specific composite key
);

-- 菜品价格历史表
CREATE TABLE dish_price_history (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES dish(id), -- 外键：菜品
    store_id INTEGER REFERENCES store(id), -- 外键：门店 (不同店可能价格不同)
    price NUMERIC(10, 2) NOT NULL,     -- 价格
    currency VARCHAR(3) DEFAULT 'CAD', -- 货币类型
    effective_month INTEGER NOT NULL CHECK (effective_month >= 1 AND effective_month <= 12), -- 生效月份
    effective_year INTEGER NOT NULL CHECK (effective_year >= 2020), -- 生效年份
    is_active BOOLEAN DEFAULT TRUE,    -- 是否当前有效价格
    UNIQUE(dish_id, store_id, effective_month, effective_year) -- 同一菜品同一店同一月份只能有一个价格
);

-- 物料价格历史表
CREATE TABLE material_price_history (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES material(id), -- 外键：物料
    store_id INTEGER REFERENCES store(id), -- 外键：门店 (不同门店可能价格不同)
    price NUMERIC(12, 4) NOT NULL,     -- 价格 (更高精度以支持小单位物料)
    currency VARCHAR(3) DEFAULT 'CAD', -- 货币类型
    effective_month INTEGER NOT NULL CHECK (effective_month >= 1 AND effective_month <= 12), -- 生效月份
    effective_year INTEGER NOT NULL CHECK (effective_year >= 2020), -- 生效年份
    is_active BOOLEAN DEFAULT TRUE,    -- 是否当前有效价格
    UNIQUE(material_id, store_id, effective_month, effective_year) -- 同一物料同一门店同一月份只能有一个价格
);

-- ========================================
-- INVENTORY TRACKING TABLES
-- ========================================

-- 库存盘点表 (对应Excel中的实际数据)
CREATE TABLE inventory_count (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id), -- 外键：门店
    material_id INTEGER REFERENCES material(id),   -- 外键：物料
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12), -- 月份
    year INTEGER NOT NULL CHECK (year >= 2020),  -- 年份
    counted_quantity NUMERIC(12, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR,
    UNIQUE(store_id, material_id, month, year)
);

-- ========================================
-- COMBO MANAGEMENT TABLES
-- ========================================

-- 套餐主表 (Combo Master Table)
CREATE TABLE combo (
    id SERIAL PRIMARY KEY,
    combo_code VARCHAR NOT NULL UNIQUE, -- 套餐编码 (e.g., "3010184", "1000000303")
    name VARCHAR NOT NULL,              -- 套餐名称 (e.g., "儿童套餐", "超值单人套餐")
    description VARCHAR,                -- 描述
    is_active BOOLEAN DEFAULT TRUE,     -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- MONTHLY PERFORMANCE TRACKING TABLES
-- ========================================

-- 菜品月度销售数据表 (Monthly Dish Sales Performance)
CREATE TABLE dish_monthly_sale (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES dish(id), -- 外键：菜品
    store_id INTEGER REFERENCES store(id), -- 外键：门店
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12), -- 月份 (1-12)
    year INTEGER NOT NULL CHECK (year >= 2020), -- 年份
    sale_amount NUMERIC(12, 4) DEFAULT 0, -- 销售数量
    return_amount NUMERIC(12, 4) DEFAULT 0, -- 退菜数量
    free_meal_amount NUMERIC(12, 4) DEFAULT 0, -- 免费餐数量
    gift_amount NUMERIC(12, 4) DEFAULT 0, -- 赠送数量
    tax_amount NUMERIC(12, 4) DEFAULT 0, -- 税额
    UNIQUE(dish_id, store_id, month, year) -- 同一菜品同一门店同一月只能有一条记录
);

-- 套餐月度销售数据表 (Monthly Combo Dish Sales Performance)
CREATE TABLE monthly_combo_dish_sale (
    id SERIAL PRIMARY KEY,
    combo_id INTEGER REFERENCES combo(id), -- 外键：套餐
    dish_id INTEGER REFERENCES dish(id), -- 外键：菜品
    store_id INTEGER REFERENCES store(id), -- 外键：门店
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12), -- 月份 (1-12)
    year INTEGER NOT NULL CHECK (year >= 2020), -- 年份
    sale_amount NUMERIC(12, 4) DEFAULT 0, -- 销售数量 (出品数量 - 退菜数量)
    tax_amount NUMERIC(12, 4) DEFAULT 0, -- 税额
    UNIQUE(combo_id, dish_id, store_id, month, year) -- 同一套餐同一菜品同一门店同一月只能有一条记录
);

-- 物料月度使用量表 (Monthly Material Usage)
CREATE TABLE material_monthly_usage (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES material(id), -- 外键：物料
    store_id INTEGER REFERENCES store(id), -- 外键：门店
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12), -- 月份 (1-12)
    year INTEGER NOT NULL CHECK (year >= 2020), -- 年份
    material_used NUMERIC(12, 4) NOT NULL, -- 实际使用量 (期末库存 - 期初库存)
    material_use_type VARCHAR(100), -- 物料使用类型 (来自material_detail的大类字段)
    UNIQUE(material_id, store_id, month, year) -- 同一物料同一门店同一月只能有一条记录
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- District indexes
CREATE INDEX idx_district_name ON district(name);
CREATE INDEX idx_district_active ON district(is_active);

-- Store indexes
CREATE INDEX idx_store_district ON store(district_id);
CREATE INDEX idx_store_name ON store(name);
CREATE INDEX idx_store_active ON store(is_active);

-- Dish indexes (store-specific)
CREATE INDEX idx_dish_store_code ON dish(store_id, full_code);
CREATE INDEX idx_dish_store_active ON dish(store_id, is_active);
CREATE INDEX idx_dish_child_type ON dish(dish_child_type_id);

-- Material type indexes
CREATE INDEX idx_material_type_name ON material_type(name);
CREATE INDEX idx_material_type_active ON material_type(is_active);
CREATE INDEX idx_material_child_type_material_type ON material_child_type(material_type_id);

-- Material indexes (store-specific)
CREATE INDEX idx_material_store_number ON material(store_id, material_number);
CREATE INDEX idx_material_store_active ON material(store_id, is_active);
CREATE INDEX idx_material_type ON material(material_type_id);

-- Dish-Material relationship indexes
CREATE INDEX idx_dish_material_store ON dish_material(store_id);
CREATE INDEX idx_dish_material_dish ON dish_material(dish_id);
CREATE INDEX idx_dish_material_material ON dish_material(material_id);

-- ========================================
-- TRIGGERS FOR DATA INTEGRITY
-- ========================================

-- Function to validate dish_material store consistency
CREATE OR REPLACE FUNCTION validate_dish_material_store_consistency()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if dish and material belong to the same store as the relationship
    IF NOT EXISTS (
        SELECT 1 FROM dish d, material m 
        WHERE d.id = NEW.dish_id 
        AND m.id = NEW.material_id 
        AND d.store_id = NEW.store_id 
        AND m.store_id = NEW.store_id
    ) THEN
        RAISE EXCEPTION 'dish_material store_id must match both dish and material store_id';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce store consistency on dish_material
CREATE TRIGGER trigger_dish_material_store_consistency
    BEFORE INSERT OR UPDATE ON dish_material
    FOR EACH ROW
    EXECUTE FUNCTION validate_dish_material_store_consistency();
CREATE INDEX idx_material_child_type_active ON material_child_type(is_active);

-- Material indexes
CREATE INDEX idx_material_number ON material(material_number);
CREATE INDEX idx_material_type ON material(material_type_id);
CREATE INDEX idx_material_child_type ON material(material_child_type_id);
CREATE INDEX idx_material_active ON material(is_active);

-- Dish-Material relationship indexes
CREATE INDEX idx_dish_material_dish ON dish_material(dish_id);
CREATE INDEX idx_dish_material_material ON dish_material(material_id);

-- Price history indexes
CREATE INDEX idx_dish_price_dish_store ON dish_price_history(dish_id, store_id);
CREATE INDEX idx_dish_price_active ON dish_price_history(is_active);
CREATE INDEX idx_dish_price_effective ON dish_price_history(effective_year, effective_month);

CREATE INDEX idx_material_price_material_store ON material_price_history(material_id, store_id);
CREATE INDEX idx_material_price_active ON material_price_history(is_active);
CREATE INDEX idx_material_price_effective ON material_price_history(effective_year, effective_month);

-- Inventory count indexes
CREATE INDEX idx_inventory_count_store_date ON inventory_count(store_id, year, month);
CREATE INDEX idx_inventory_count_material ON inventory_count(material_id);

-- Combo indexes
CREATE INDEX idx_combo_code ON combo(combo_code);
CREATE INDEX idx_combo_active ON combo(is_active);

-- Monthly performance indexes
CREATE INDEX idx_dish_monthly_sale_dish_store_date ON dish_monthly_sale(dish_id, store_id, year, month);
CREATE INDEX idx_dish_monthly_sale_store_date ON dish_monthly_sale(store_id, year, month);
CREATE INDEX idx_dish_monthly_sale_date ON dish_monthly_sale(year, month);

CREATE INDEX idx_monthly_combo_dish_sale_combo_dish_store_date ON monthly_combo_dish_sale(combo_id, dish_id, store_id, year, month);
CREATE INDEX idx_monthly_combo_dish_sale_dish_store_date ON monthly_combo_dish_sale(dish_id, store_id, year, month);
CREATE INDEX idx_monthly_combo_dish_sale_store_date ON monthly_combo_dish_sale(store_id, year, month);
CREATE INDEX idx_monthly_combo_dish_sale_date ON monthly_combo_dish_sale(year, month);

CREATE INDEX idx_material_monthly_usage_material_store_date ON material_monthly_usage(material_id, store_id, year, month);
CREATE INDEX idx_material_monthly_usage_store_date ON material_monthly_usage(store_id, year, month);
CREATE INDEX idx_material_monthly_usage_date ON material_monthly_usage(year, month);

-- Month static data indexes
CREATE INDEX idx_month_static_data_month ON month_static_data(month);

-- ========================================
-- TRIGGERS FOR UPDATED_AT
-- ========================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at
CREATE TRIGGER update_district_updated_at BEFORE UPDATE ON district
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_store_updated_at BEFORE UPDATE ON store
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dish_type_updated_at BEFORE UPDATE ON dish_type
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dish_child_type_updated_at BEFORE UPDATE ON dish_child_type
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dish_updated_at BEFORE UPDATE ON dish
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_material_type_updated_at BEFORE UPDATE ON material_type
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_material_child_type_updated_at BEFORE UPDATE ON material_child_type
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_material_updated_at BEFORE UPDATE ON material
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dish_material_updated_at BEFORE UPDATE ON dish_material
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_combo_updated_at BEFORE UPDATE ON combo
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- No update triggers needed for monthly tables (using year/month only)

-- ========================================
-- INITIAL DATA INSERTION
-- ========================================

-- Insert district data first (required for store references)
INSERT INTO district (id, name, description, currency, is_active) VALUES
(1, 'Canada', 'Canadian operations', 'CAD', TRUE),
(2, 'USA', 'United States operations', 'USD', TRUE),
(3, 'China', 'China operations', 'CNY', TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    currency = EXCLUDED.currency,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

-- Insert store data with proper district references
INSERT INTO store (id, name, district_id, country, manager, opened_at, seats_total, is_active) VALUES
(1, '加拿大一店', 1, '加拿大', '蒋冰遇', '2018-12-18', 53, TRUE),
(2, '加拿大二店', 1, '加拿大', '蒋冰遇', '2020-07-27', 36, TRUE),
(3, '加拿大三店', 1, '加拿大', '蒋冰遇', '2020-08-17', 48, TRUE),
(4, '加拿大四店', 1, '加拿大', '蒋冰遇', '2020-10-30', 70, TRUE),
(5, '加拿大五店', 1, '加拿大', '蒋冰遇', '2022-10-03', 55, TRUE),
(6, '加拿大六店', 1, '加拿大', '蒋冰遇', '2024-01-09', 56, TRUE),
(7, '加拿大七店', 1, '加拿大', '蒋冰遇', '2024-05-01', 57, TRUE),
(8, '加拿大八店', 1, '加拿大', '蒋冰遇', '2025-10-15', 54, TRUE)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    district_id = EXCLUDED.district_id,
    country = EXCLUDED.country,
    manager = EXCLUDED.manager,
    opened_at = EXCLUDED.opened_at,
    seats_total = EXCLUDED.seats_total,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

-- Insert time segment data
INSERT INTO time_segment (id, label, start_time, end_time, description) VALUES
(1, '08:00-13:59', '08:00:00', '13:59:59', 'Morning to early afternoon'),
(2, '14:00-16:59', '14:00:00', '16:59:59', 'Afternoon'),
(3, '17:00-21:59', '17:00:00', '21:59:59', 'Evening'),
(4, '22:00-(次)07:59', '22:00:00', '07:59:59', 'Late night to early morning (next day)')
ON CONFLICT (id) DO UPDATE SET
    label = EXCLUDED.label,
    start_time = EXCLUDED.start_time,
    end_time = EXCLUDED.end_time,
    description = EXCLUDED.description;

-- ========================================
-- MONTHLY TARGETS DATA (JUNE 2025)
-- ========================================

-- Monthly targets for June 2025
-- Based on data provided for all Haidilao Canada stores
INSERT INTO store_monthly_target (
    store_id, 
    month, 
    turnover_rate, 
    table_avg_spending, 
    revenue, 
    labor_percentage, 
    gross_revenue
) VALUES
-- 加拿大一店 (Store ID: 1)
(1, '2025-06-01', 4.20, 151.98, 1014900.00, 41.0, 50000),
-- 加拿大二店 (Store ID: 2) 
(2, '2025-06-01', 3.50, 140.21, 530000, 42.0, 10000),
-- 加拿大三店 (Store ID: 3)
(3, '2025-06-01', 5.20, 124.00, 928500.00, 38.5, 80000),
-- 加拿大四店 (Store ID: 4)
(4, '2025-06-01', 4.00, 130.95, 1100000, 38.5, 121002),
-- 加拿大五店 (Store ID: 5)
(5, '2025-06-01', 5.10, 135.95, 1144000, 38.5, 122350.8),
-- 加拿大六店 (Store ID: 6)
(6, '2025-06-01', 3.60, 117.39, 710000, 39.0, 30000),
-- 加拿大七店 (Store ID: 7)
(7, '2025-06-01', 3.85, 148.86, 980000.00, 41.0, 50000),


-- 加拿大一店 (Store ID: 1)
(1, '2025-07-01', 4.26, 151.98, 1035000.00, 41.0, 50000),
-- 加拿大二店 (Store ID: 2) 
(2, '2025-07-01', 3.20, 140.21, 550000, 40.0, 5000),
-- 加拿大三店 (Store ID: 3)
(3, '2025-07-01', 5.10, 124.00, 941011.00, 39, 70000),
-- 加拿大四店 (Store ID: 4)
(4, '2025-07-01', 3.90, 130.95, 1057875, 38.5, 105787.5),
-- 加拿大五店 (Store ID: 5)
(5, '2025-07-01', 5.10, 135.95, 1147806, 38.5, 114780.6),
-- 加拿大六店 (Store ID: 6)
(6, '2025-07-01', 3.30, 117.39, 700000, 41.0, -30000),
-- 加拿大七店 (Store ID: 7)
(7, '2025-07-01', 3.95, 148.86, 980000.00, 40.0, 40000),

-- 加拿大一店 (Store ID: 1)
(1, '2025-08-01', 4.20, 151.98, 1000600.00, 42.0, 93000),
-- 加拿大二店 (Store ID: 2) 
(2, '2025-08-01', 3.50, 140.21, 506000, 40.0, 0),
-- 加拿大三店 (Store ID: 3)
(3, '2025-08-01', 5.00, 124.00, 930000.00, 39.0, 96000),
-- 加拿大四店 (Store ID: 4)
(4, '2025-08-01', 4.00, 130.95, 1067600, 38.5, 124200),
-- 加拿大五店 (Store ID: 5)
(5, '2025-08-01', 5.20, 135.95, 1152600, 39.5, 126920),
-- 加拿大六店 (Store ID: 6)
(6, '2025-08-01', 3.70, 117.39, 705000, 40.0, 62000),
-- 加拿大七店 (Store ID: 7)
(7, '2025-08-01', 4.14, 148.86, 1020000.00, 40.0, 80000),

-- 加拿大一店 (Store ID: 1)
(1, '2025-09-01', 4.65, 151.98, 1060000, 41.0, 60000),
-- 加拿大二店 (Store ID: 2) 
(2, '2025-09-01', 3.72, 140.21, 630000, 40.0, 3000),
-- 加拿大三店 (Store ID: 3)
(3, '2025-09-01', 5.3, 124.00, 961600, 40.0, 70000),
-- 加拿大四店 (Store ID: 4)
(4, '2025-09-01', 4.00, 130.95, 1155000, 39, 105000),
-- 加拿大五店 (Store ID: 5)
(5, '2025-09-01', 5.3, 135.95, 1189300, 39, 120000),
-- 加拿大六店 (Store ID: 6)
(6, '2025-09-01', 3.3, 117.39, 730000, 40.0, 10000),
-- 加拿大七店 (Store ID: 7)
(7, '2025-09-01', 4.2, 148.86, 1010000.00, 40.0, 50000),

-- 加拿大一店 (Store ID: 1)
(1, '2025-11-01', 4.30, 151.98, 1011900, 41.0, 60000),
-- 加拿大二店 (Store ID: 2) 
(2, '2025-11-01', 3.81, 140.21, 632500, 40.0, 3000),
-- 加拿大三店 (Store ID: 3)
(3, '2025-11-01', 5.20, 124.00, 958500, 40.0, 70000),
-- 加拿大四店 (Store ID: 4)
(4, '2025-11-01',4.08, 130.95, 1190000, 39, 105000),
-- 加拿大五店 (Store ID: 5)
(5, '2025-11-01', 5.15, 135.95, 1287000, 39, 120000),
-- 加拿大六店 (Store ID: 6)
(6, '2025-11-01', 3.30, 117.39, 693000, 40.0, 10000),
-- 加拿大七店 (Store ID: 7)
(7, '2025-11-01', 3.80, 148.86, 942200, 40.0, 50000),
-- 加拿大八店 (Store ID: 8)
(8, '2025-11-01', 3.74, 148.86, 790000, 40.0, 50000),

-- 加拿大一店 (Store ID: 1)
(1, '2025-12-01', 4.68, 151.98, 1150000, 41.0, 60000),
-- 加拿大二店 (Store ID: 2) 
(2, '2025-12-01', 3.95, 140.21, 700000, 40.0, 3000),
-- 加拿大三店 (Store ID: 3)
(3, '2025-12-01', 5.6, 124.00, 1100000, 40.0, 70000),
-- 加拿大四店 (Store ID: 4)
(4, '2025-12-01',4.3, 130.95, 1280000, 39, 105000),
-- 加拿大五店 (Store ID: 5)
(5, '2025-12-01', 5.5, 135.95, 1453500, 39, 120000),
-- 加拿大六店 (Store ID: 6)
(6, '2025-12-01', 4.1, 117.39, 900000, 40.0, 10000),
-- 加拿大七店 (Store ID: 7)
(7, '2025-12-01', 4.00, 148.86, 1120000, 40.0, 50000),
-- 加拿大八店 (Store ID: 8)
(8, '2025-12-01', 4.13, 148.86, 1071600, 40.0, 50000)

ON CONFLICT (store_id, month) DO UPDATE SET
    turnover_rate = EXCLUDED.turnover_rate,
    table_avg_spending = EXCLUDED.table_avg_spending,
    revenue = EXCLUDED.revenue,
    labor_percentage = EXCLUDED.labor_percentage,
    gross_revenue = EXCLUDED.gross_revenue;

-- Time segment targets for June 2025
-- Based on operational patterns for each time segment
INSERT INTO store_monthly_time_target (
    store_id, 
    month, 
    time_segment_id,
    turnover_rate
) VALUES
-- 加拿大一店 (Store ID: 1) - Total target: 4.20
(1, '2025-06-01', 1, 0.85),  -- 08:00-13:59
(1, '2025-06-01', 2, 0.60),  -- 14:00-16:59
(1, '2025-06-01', 3, 1.97),  -- 17:00-21:59
(1, '2025-06-01', 4, 0.78),  -- 22:00-(次)07:59
-- 加拿大二店 (Store ID: 2) - Total target: 3.50
(2, '2025-06-01', 1, 0.50),  -- 08:00-13:59
(2, '2025-06-01', 2, 0.50),  -- 14:00-16:59
(2, '2025-06-01', 3, 1.80),  -- 17:00-21:59
(2, '2025-06-01', 4, 0.70),  -- 22:00-(次)07:59
-- 加拿大三店 (Store ID: 3) - Total target: 5.20
(3, '2025-06-01', 1, 1.20),  -- 08:00-13:59
(3, '2025-06-01', 2, 1.00),  -- 14:00-16:59
(3, '2025-06-01', 3, 2.20),  -- 17:00-21:59
(3, '2025-06-01', 4, 0.80),  -- 22:00-(次)07:59
-- 加拿大四店 (Store ID: 4) - Total target: 4.00
(4, '2025-06-01', 1, 0.51),  -- 08:00-13:59
(4, '2025-06-01', 2, 0.53),  -- 14:00-16:59
(4, '2025-06-01', 3, 1.85),  -- 17:00-21:59
(4, '2025-06-01', 4, 1.01),  -- 22:00-(次)07:59
-- 加拿大五店 (Store ID: 5) - Total target: 5.10
(5, '2025-06-01', 1, 0.85),  -- 08:00-13:59
(5, '2025-06-01', 2, 0.75),  -- 14:00-16:59
(5, '2025-06-01', 3, 2.40),  -- 17:00-21:59
(5, '2025-06-01', 4, 1.10),  -- 22:00-(次)07:59
-- 加拿大六店 (Store ID: 6) - Total target: 3.60
(6, '2025-06-01', 1, 0.60),  -- 08:00-13:59
(6, '2025-06-01', 2, 0.50),  -- 14:00-16:59
(6, '2025-06-01', 3, 1.80),  -- 17:00-21:59
(6, '2025-06-01', 4, 0.70),  -- 22:00-(次)07:59
-- 加拿大七店 (Store ID: 7) - Total target: 3.85
(7, '2025-06-01', 1, 0.65),  -- 08:00-13:59
(7, '2025-06-01', 2, 0.65),  -- 14:00-16:59
(7, '2025-06-01', 3, 1.85),  -- 17:00-21:59
(7, '2025-06-01', 4, 0.70),   -- 22:00-(次)07:59


-- 加拿大一店 (Store ID: 1) - Total target: 4.20
(1, '2025-07-01', 1, 0.78),  -- 08:00-13:59
(1, '2025-07-01', 2, 0.7),  -- 14:00-16:59
(1, '2025-07-01', 3, 2),  -- 17:00-21:59
(1, '2025-07-01', 4, 0.78),  -- 22:00-(次)07:59
-- 加拿大二店 (Store ID: 2) - Total target: 3.50
(2, '2025-07-01', 1, 0.4),  -- 08:00-13:59
(2, '2025-07-01', 2, 0.4),  -- 14:00-16:59
(2, '2025-07-01', 3, 1.9),  -- 17:00-21:59
(2, '2025-07-01', 4, 0.5),  -- 22:00-(次)07:59
-- 加拿大三店 (Store ID: 3) - Total target: 5.20
(3, '2025-07-01', 1, 1.1),  -- 08:00-13:59
(3, '2025-07-01', 2, 1.00),  -- 14:00-16:59
(3, '2025-07-01', 3, 2.20),  -- 17:00-21:59
(3, '2025-07-01', 4, 0.80),  -- 22:00-(次)07:59
-- 加拿大四店 (Store ID: 4) - Total target: 4.00
(4, '2025-07-01', 1, 0.7),  -- 08:00-13:59
(4, '2025-07-01', 2, 0.6),  -- 14:00-16:59
(4, '2025-07-01', 3, 1.7),  -- 17:00-21:59
(4, '2025-07-01', 4, 0.9),  -- 22:00-(次)07:59
-- 加拿大五店 (Store ID: 5) - Total target: 5.10
(5, '2025-07-01', 1, 0.85),  -- 08:00-13:59
(5, '2025-07-01', 2, 0.75),  -- 14:00-16:59
(5, '2025-07-01', 3, 2.40),  -- 17:00-21:59
(5, '2025-07-01', 4, 1.10),  -- 22:00-(次)07:59
-- 加拿大六店 (Store ID: 6) - Total target: 3.60
(6, '2025-07-01', 1, 0.60),  -- 08:00-13:59
(6, '2025-07-01', 2, 0.40),  -- 14:00-16:59
(6, '2025-07-01', 3, 1.30),  -- 17:00-21:59
(6, '2025-07-01', 4, 1.00),  -- 22:00-(次)07:59
-- 加拿大七店 (Store ID: 7) - Total target: 3.85
(7, '2025-07-01', 1, 0.7),  -- 08:00-13:59
(7, '2025-07-01', 2, 0.6),  -- 14:00-16:59
(7, '2025-07-01', 3, 2),  -- 17:00-21:59
(7, '2025-07-01', 4, 0.65),   -- 22:00-(次)07:59

-- August 2025 Time Segment Targets
-- 加拿大一店 (Store ID: 1) - Total target: 4.20
(1, '2025-08-01', 1, 0.85),  -- 08:00-13:59
(1, '2025-08-01', 2, 0.50),  -- 14:00-16:59
(1, '2025-08-01', 3, 2.05),  -- 17:00-21:59
(1, '2025-08-01', 4, 0.80),  -- 22:00-(次)07:59
-- 加拿大二店 (Store ID: 2) - Total target: 3.50
(2, '2025-08-01', 1, 0.50),  -- 08:00-13:59
(2, '2025-08-01', 2, 0.50),  -- 14:00-16:59
(2, '2025-08-01', 3, 1.80),  -- 17:00-21:59
(2, '2025-08-01', 4, 0.70),  -- 22:00-(次)07:59
-- 加拿大三店 (Store ID: 3) - Total target: 5.00
(3, '2025-08-01', 1, 1.15),  -- 08:00-13:59
(3, '2025-08-01', 2, 0.85),  -- 14:00-16:59
(3, '2025-08-01', 3, 2.20),  -- 17:00-21:59
(3, '2025-08-01', 4, 0.80),  -- 22:00-(次)07:59
-- 加拿大四店 (Store ID: 4) - Total target: 4.00
(4, '2025-08-01', 1, 0.75),  -- 08:00-13:59
(4, '2025-08-01', 2, 0.54),  -- 14:00-16:59
(4, '2025-08-01', 3, 1.77),  -- 17:00-21:59
(4, '2025-08-01', 4, 0.94),  -- 22:00-(次)07:59
-- 加拿大五店 (Store ID: 5) - Total target: 5.20
(5, '2025-08-01', 1, 0.85),  -- 08:00-13:59
(5, '2025-08-01', 2, 0.75),  -- 14:00-16:59
(5, '2025-08-01', 3, 2.50),  -- 17:00-21:59
(5, '2025-08-01', 4, 1.10),  -- 22:00-(次)07:59
-- 加拿大六店 (Store ID: 6) - Total target: 3.70
(6, '2025-08-01', 1, 0.70),  -- 08:00-13:59
(6, '2025-08-01', 2, 0.30),  -- 14:00-16:59
(6, '2025-08-01', 3, 1.70),  -- 17:00-21:59
(6, '2025-08-01', 4, 1.00),  -- 22:00-(次)07:59
-- 加拿大七店 (Store ID: 7) - Total target: 4.14
(7, '2025-08-01', 1, 1.02),  -- 08:00-13:59
(7, '2025-08-01', 2, 0.56),  -- 14:00-16:59
(7, '2025-08-01', 3, 1.90),  -- 17:00-21:59
(7, '2025-08-01', 4, 0.66),   -- 22:00-(次)07:59

-- 加拿大一店 (Store ID: 1) - Total target: 4.20
(1, '2025-09-01', 1, 0.96),  -- 08:00-13:59
(1, '2025-09-01', 2, 0.51),  -- 14:00-16:59
(1, '2025-09-01', 3, 2.34),  -- 17:00-21:59
(1, '2025-09-01', 4, 0.84),  -- 22:00-(次)07:59
-- 加拿大二店 (Store ID: 2) - Total target: 3.50
(2, '2025-09-01', 1, 0.70),  -- 08:00-13:59
(2, '2025-09-01', 2, 0.30),  -- 14:00-16:59
(2, '2025-09-01', 3, 2.10),  -- 17:00-21:59
(2, '2025-09-01', 4, 0.62),  -- 22:00-(次)07:59
-- 加拿大三店 (Store ID: 3) - Total target: 5.00
(3, '2025-09-01', 1, 1.35),  -- 08:00-13:59
(3, '2025-09-01', 2, 0.85),  -- 14:00-16:59
(3, '2025-09-01', 3, 2.25),  -- 17:00-21:59
(3, '2025-09-01', 4, 0.85),  -- 22:00-(次)07:59
-- 加拿大四店 (Store ID: 4) - Total target: 4.00
(4, '2025-09-01', 1, 0.73),  -- 08:00-13:59
(4, '2025-09-01', 2, 0.51),  -- 14:00-16:59
(4, '2025-09-01', 3, 1.79),  -- 17:00-21:59
(4, '2025-09-01', 4, 0.97),  -- 22:00-(次)07:59
-- 加拿大五店 (Store ID: 5) - Total target: 5.20
(5, '2025-09-01', 1, 0.80),  -- 08:00-13:59
(5, '2025-09-01', 2, 0.90),  -- 14:00-16:59
(5, '2025-09-01', 3, 2.50),  -- 17:00-21:59
(5, '2025-09-01', 4, 1.10),  -- 22:00-(次)07:59
-- 加拿大六店 (Store ID: 6) - Total target: 3.70
(6, '2025-09-01', 1, 0.60),  -- 08:00-13:59
(6, '2025-09-01', 2, 0.40),  -- 14:00-16:59
(6, '2025-09-01', 3, 1.30),  -- 17:00-21:59
(6, '2025-09-01', 4, 1.00),  -- 22:00-(次)07:59
-- 加拿大七店 (Store ID: 7) - Total target: 4.14
(7, '2025-09-01', 1, 1.1),  -- 08:00-13:59
(7, '2025-09-01', 2, 0.55),  -- 14:00-16:59
(7, '2025-09-01', 3, 2.1),  -- 17:00-21:59
(7, '2025-09-01', 4, 0.65),   -- 22:00-(次)07:59

-- 加拿大一店 (Store ID: 1) - Total target: 4.20
(1, '2025-11-01', 1, 1.01),  -- 08:00-13:59
(1, '2025-11-01', 2, 0.49),  -- 14:00-16:59
(1, '2025-11-01', 3, 2.01),  -- 17:00-21:59
(1, '2025-11-01', 4, 0.79),  -- 22:00-(次)07:59
-- 加拿大二店 (Store ID: 2) - Total target: 3.50
(2, '2025-11-01', 1, 0.80),  -- 08:00-13:59
(2, '2025-11-01', 2, 0.50),  -- 14:00-16:59
(2, '2025-11-01', 3, 1.85),  -- 17:00-21:59
(2, '2025-11-01', 4, 0.65),  -- 22:00-(次)07:59
-- 加拿大三店 (Store ID: 3) - Total target: 5.00
(3, '2025-11-01', 1, 1.30),  -- 08:00-13:59
(3, '2025-11-01', 2, 0.90),  -- 14:00-16:59
(3, '2025-11-01', 3, 2.15),  -- 17:00-21:59
(3, '2025-11-01', 4, 0.85),  -- 22:00-(次)07:59
-- 加拿大四店 (Store ID: 4) - Total target: 4.00
(4, '2025-11-01', 1, 0.78),  -- 08:00-13:59
(4, '2025-11-01', 2, 0.52),  -- 14:00-16:59
(4, '2025-11-01', 3, 1.88),  -- 17:00-21:59
(4, '2025-11-01', 4, 0.90),  -- 22:00-(次)07:59
-- 加拿大五店 (Store ID: 5) - Total target: 5.20
(5, '2025-11-01', 1, 0.85),  -- 08:00-13:59
(5, '2025-11-01', 2, 0.75),  -- 14:00-16:59
(5, '2025-11-01', 3, 2.45),  -- 17:00-21:59
(5, '2025-11-01', 4, 1.10),  -- 22:00-(次)07:59
-- 加拿大六店 (Store ID: 6) - Total target: 3.70
(6, '2025-11-01', 1, 0.60),  -- 08:00-13:59
(6, '2025-11-01', 2, 0.30),  -- 14:00-16:59
(6, '2025-11-01', 3, 1.80),  -- 17:00-21:59
(6, '2025-11-01', 4, 0.60),  -- 22:00-(次)07:59
-- 加拿大七店 (Store ID: 7) - Total target: 4.14
(7, '2025-11-01', 1, 0.85),  -- 08:00-13:59
(7, '2025-11-01', 2, 0.55),  -- 14:00-16:59
(7, '2025-11-01', 3, 1.83),  -- 17:00-21:59
(7, '2025-11-01', 4, 0.57),   -- 22:00-(次)07:59
-- 加拿大八店 (Store ID: 8) - Total target: 4.14
(8, '2025-11-01', 1, 0.79),  -- 08:00-13:59
(8, '2025-11-01', 2, 0.73),  -- 14:00-16:59
(8, '2025-11-01', 3, 1.92),  -- 17:00-21:59
(8, '2025-11-01', 4, 0.30),   -- 22:00-(次)07:59


-- 加拿大一店 (Store ID: 1) - Total target: 4.20
(1, '2025-12-01', 1, 1.1),  -- 08:00-13:59
(1, '2025-12-01', 2, 0.6),  -- 14:00-16:59
(1, '2025-12-01', 3, 2.2),  -- 17:00-21:59
(1, '2025-12-01', 4, 0.6),  -- 22:00-(次)07:59
-- 加拿大二店 (Store ID: 2) - Total target: 3.50
(2, '2025-12-01', 1, 0.80),  -- 08:00-13:59
(2, '2025-12-01', 2, 0.6),  -- 14:00-16:59
(2, '2025-12-01', 3, 1.9),  -- 17:00-21:59
(2, '2025-12-01', 4, 0.65),  -- 22:00-(次)07:59
-- 加拿大三店 (Store ID: 3) - Total target: 5.00
(3, '2025-12-01', 1, 1.4),  -- 08:00-13:59
(3, '2025-12-01', 2, 0.95),  -- 14:00-16:59
(3, '2025-12-01', 3, 2.3),  -- 17:00-21:59
(3, '2025-12-01', 4, 0.95),  -- 22:00-(次)07:59
-- 加拿大四店 (Store ID: 4) - Total target: 4.00
(4, '2025-12-01', 1, 0.78),  -- 08:00-13:59
(4, '2025-12-01', 2, 0.65),  -- 14:00-16:59
(4, '2025-12-01', 3, 1.91),  -- 17:00-21:59
(4, '2025-12-01', 4, 0.96),  -- 22:00-(次)07:59
-- 加拿大五店 (Store ID: 5) - Total target: 5.20
(5, '2025-12-01', 1, 0.95),  -- 08:00-13:59
(5, '2025-12-01', 2, 0.95),  -- 14:00-16:59
(5, '2025-12-01', 3, 2.45),  -- 17:00-21:59
(5, '2025-12-01', 4, 1.15),  -- 22:00-(次)07:59
-- 加拿大六店 (Store ID: 6) - Total target: 3.70
(6, '2025-12-01', 1, 0.70),  -- 08:00-13:59
(6, '2025-12-01', 2, 0.50),  -- 14:00-16:59
(6, '2025-12-01', 3, 2.20),  -- 17:00-21:59
(6, '2025-12-01', 4, 0.70),  -- 22:00-(次)07:59
-- 加拿大七店 (Store ID: 7) - Total target: 4.14
(7, '2025-12-01', 1, 0.95),  -- 08:00-13:59
(7, '2025-12-01', 2, 0.5),  -- 14:00-16:59
(7, '2025-12-01', 3, 1.85),  -- 17:00-21:59
(7, '2025-12-01', 4, 0.6),   -- 22:00-(次)07:59
-- 加拿大八店 (Store ID: 8) - Total target: 4.14
(8, '2025-12-01', 1, 0.85),  -- 08:00-13:59
(8, '2025-12-01', 2, 0.65),  -- 14:00-16:59
(8, '2025-12-01', 3, 2.00),  -- 17:00-21:59
(8, '2025-12-01', 4, 0.63)   -- 22:00-(次)07:59
ON CONFLICT (store_id, month, time_segment_id) DO UPDATE SET
    turnover_rate = EXCLUDED.turnover_rate;

-- ========================================
-- MONTHLY STATIC DATA (Exchange Rates, etc.)
-- ========================================

CREATE TABLE month_static_data (
    id SERIAL PRIMARY KEY,
    month DATE NOT NULL UNIQUE,                    -- 月份（每月第一天作为标识）
    cad_usd_rate NUMERIC(8, 4) NOT NULL,          -- 本月 CAD/USD 汇率
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_month_first_day CHECK (EXTRACT(DAY FROM month) = 1)
);

-- Insert exchange rate data for 2025
INSERT INTO month_static_data (month, cad_usd_rate) VALUES
('2024-01-01', 0.754661),  -- Jan 2024 CAD/USD rate
('2024-02-01', 0.754661),  -- Feb 2024 CAD/USD rate
('2024-03-01', 0.754661),  -- Mar 2024 CAD/USD rate
('2024-04-01', 0.754661),  -- Apr 2024 CAD/USD rate
('2024-05-01', 0.754661),  -- May 2024 CAD/USD rate
('2024-06-01', 0.754661),  -- June 2024 CAD/USD rate
('2024-07-01', 0.754661),  -- July 2024 CAD/USD rate
('2024-08-01', 0.754661),  -- Aug 2024 CAD/USD rate
('2024-09-01', 0.754661),  -- Sep 2024 CAD/USD rate
('2024-10-01', 0.754661),  -- Oct 2024 CAD/USD rate
('2024-11-01', 0.754661),  -- Nov 2024 CAD/USD rate
('2024-12-01', 0.754661),  -- Dec 2024 CAD/USD rate
('2025-01-01', 0.695265),  -- Jan 2025 CAD/USD rate
('2025-02-01', 0.695265),  -- Feb 2025 CAD/USD rate
('2025-03-01', 0.695265),  -- Mar 2025 CAD/USD rate
('2025-04-01', 0.695265),  -- Apr 2025 CAD/USD rate
('2025-05-01', 0.695265),  -- May 2025 CAD/USD rate
('2025-06-01', 0.695265),  -- June 2025 CAD/USD rate
('2025-07-01', 0.695265),  -- July 2025 CAD/USD rate 
('2025-08-01', 0.695265),  -- Aug 2025 CAD/USD rate 
('2025-09-01', 0.72),  -- Sep 2025 CAD/USD rate 
('2025-10-01', 0.695265),  -- Oct 2025 CAD/USD rate 
('2025-11-01', 0.695265),  -- Nov 2025 CAD/USD rate 
('2025-12-01', 0.695265)   -- Dec 2025 CAD/USD rate 
ON CONFLICT (month) DO UPDATE SET
    cad_usd_rate = EXCLUDED.cad_usd_rate,
    updated_at = CURRENT_TIMESTAMP;

-- ========================================
-- RESET COMPLETE
-- ========================================
-- Summary of inserted data:
-- Districts: 3 (Canada, USA, China)
-- Stores: 7 (All Canadian Haidilao stores)
-- Time Segments: 4 (Daily time periods)
-- Monthly Targets: 7 stores for June 2025
-- Time Segment Targets: 28 records (7 stores × 4 time segments)
-- Total revenue target: 6,407,400 CAD
-- Average turnover rate: 4.21
-- CAD/USD exchange rate: 0.695265
