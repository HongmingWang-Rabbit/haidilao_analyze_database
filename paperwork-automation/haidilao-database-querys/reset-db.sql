-- WARNING: This will delete all your reporting data. Use with caution.

-- Drop tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS material_price_history;
DROP TABLE IF EXISTS dish_price_history;
DROP TABLE IF EXISTS dish_material;
DROP TABLE IF EXISTS dish;
DROP TABLE IF EXISTS dish_child_type;
DROP TABLE IF EXISTS dish_type;
DROP TABLE IF EXISTS material;
DROP TABLE IF EXISTS store_monthly_time_target;
DROP TABLE IF EXISTS store_monthly_target;
DROP TABLE IF EXISTS store_time_report;
DROP TABLE IF EXISTS daily_report;
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
  monthly_CAD_USD_rate NUMERIC(8, 4)         -- 本月 CAD/USD 汇率
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

-- 菜品主表
CREATE TABLE dish (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,               -- 菜品名称
    system_name VARCHAR,                 -- 菜品名称（系统）
    full_code VARCHAR NOT NULL UNIQUE,  -- 菜品编码 (e.g., "1060061")
    short_code VARCHAR,                  -- 菜品短编码
    dish_child_type_id INTEGER REFERENCES dish_child_type(id), -- 外键：菜品子类
    specification VARCHAR,               -- 规格 (e.g., "单锅", "拼锅", "四宫格")
    unit VARCHAR DEFAULT '份',           -- 菜品单位
    serving_size_kg NUMERIC(8, 4),      -- 出品分量(kg)
    is_active BOOLEAN DEFAULT TRUE,     -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 物料主表
CREATE TABLE material (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,              -- 物料名称/描述
    material_number VARCHAR NOT NULL UNIQUE, -- 物料号 (e.g., "3000759")
    description VARCHAR,                -- 详细描述
    unit VARCHAR NOT NULL,              -- 单位 (e.g., "kg", "g", "oz", "瓶", "包")
    package_spec VARCHAR,               -- 包装规格 (e.g., "300G*40包/件")
    is_active BOOLEAN DEFAULT TRUE,    -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 菜品-物料关系表 (BOM - Bill of Materials)
CREATE TABLE dish_material (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES dish(id), -- 外键：菜品
    material_id INTEGER REFERENCES material(id), -- 外键：物料
    standard_quantity NUMERIC(12, 6) NOT NULL, -- 标准用量
    unit VARCHAR NOT NULL,              -- 用量单位
    conversion_factor NUMERIC(12, 6) DEFAULT 1.0, -- 转换系数（用于单位转换）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dish_id, material_id)       -- 同一菜品同一物料只能有一个配方
);

-- 菜品价格历史表
CREATE TABLE dish_price_history (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES dish(id), -- 外键：菜品
    store_id INTEGER REFERENCES store(id), -- 外键：门店 (不同店可能价格不同)
    price NUMERIC(10, 2) NOT NULL,     -- 价格
    currency VARCHAR(3) DEFAULT 'CAD', -- 货币类型
    effective_date DATE NOT NULL,      -- 生效日期
    is_active BOOLEAN DEFAULT TRUE,    -- 是否当前有效价格
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dish_id, store_id, effective_date) -- 同一菜品同一店同一日期只能有一个价格
);

-- 物料价格历史表
CREATE TABLE material_price_history (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES material(id), -- 外键：物料
    district_id INTEGER REFERENCES district(id), -- 外键：区域 (不同区域采购价可能不同)
    price NUMERIC(12, 4) NOT NULL,     -- 价格 (更高精度以支持小单位物料)
    currency VARCHAR(3) DEFAULT 'CAD', -- 货币类型
    effective_date DATE NOT NULL,      -- 生效日期
    is_active BOOLEAN DEFAULT TRUE,    -- 是否当前有效价格
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(material_id, district_id, effective_date) -- 同一物料同一区域同一日期只能有一个价格
);

-- ========================================
-- INVENTORY TRACKING TABLES
-- ========================================

-- 库存盘点表 (对应Excel中的实际数据)
CREATE TABLE inventory_count (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id), -- 外键：门店
    dish_id INTEGER REFERENCES dish(id),   -- 外键：菜品
    count_date DATE NOT NULL,             -- 盘点日期
    period_label VARCHAR,                 -- 期间标签 (e.g., "2505")
    actual_quantity NUMERIC(12, 4),      -- 实收数量
    theoretical_quantity NUMERIC(12, 4), -- 红火台理论量
    variance NUMERIC(12, 4),             -- 差异 (实际-理论)
    variance_amount NUMERIC(12, 2),      -- 差异金额
    remarks VARCHAR,                      -- 备注
    combo_usage NUMERIC(12, 4),          -- 套餐、拼盘用量
    status VARCHAR DEFAULT 'PENDING',    -- 状态 (PENDING, REVIEWED, APPROVED)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR,
    UNIQUE(store_id, dish_id, count_date, period_label)
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

-- Dish indexes
CREATE INDEX idx_dish_full_code ON dish(full_code);
CREATE INDEX idx_dish_child_type ON dish(dish_child_type_id);
CREATE INDEX idx_dish_active ON dish(is_active);

-- Material indexes
CREATE INDEX idx_material_number ON material(material_number);
CREATE INDEX idx_material_active ON material(is_active);

-- Dish-Material relationship indexes
CREATE INDEX idx_dish_material_dish ON dish_material(dish_id);
CREATE INDEX idx_dish_material_material ON dish_material(material_id);

-- Price history indexes
CREATE INDEX idx_dish_price_dish_store ON dish_price_history(dish_id, store_id);
CREATE INDEX idx_dish_price_active ON dish_price_history(is_active);
CREATE INDEX idx_dish_price_effective ON dish_price_history(effective_date);

CREATE INDEX idx_material_price_material_district ON material_price_history(material_id, district_id);
CREATE INDEX idx_material_price_active ON material_price_history(is_active);
CREATE INDEX idx_material_price_effective ON material_price_history(effective_date);

-- Inventory count indexes
CREATE INDEX idx_inventory_count_store_date ON inventory_count(store_id, count_date);
CREATE INDEX idx_inventory_count_dish ON inventory_count(dish_id);
CREATE INDEX idx_inventory_count_status ON inventory_count(status);

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

CREATE TRIGGER update_material_updated_at BEFORE UPDATE ON material
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dish_material_updated_at BEFORE UPDATE ON dish_material
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
