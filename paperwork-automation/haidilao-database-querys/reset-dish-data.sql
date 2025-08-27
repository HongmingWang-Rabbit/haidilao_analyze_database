-- WARNING: This will delete only dish-related data while preserving store operational data
-- Use with caution - this will remove all dishes, materials, and related pricing/usage data

-- ========================================
-- STEP 1: DROP DISH-RELATED TABLES
-- ========================================

-- Drop monthly performance tables related to dishes
DROP TABLE IF EXISTS monthly_combo_dish_sale CASCADE;
DROP TABLE IF EXISTS material_monthly_usage CASCADE;
DROP TABLE IF EXISTS dish_monthly_sale CASCADE;

-- Drop combo tables
DROP TABLE IF EXISTS combo CASCADE;

-- Drop inventory and price history tables
DROP TABLE IF EXISTS inventory_count CASCADE;
DROP TABLE IF EXISTS material_price_history CASCADE;
DROP TABLE IF EXISTS dish_price_history CASCADE;

-- Drop dish-material relationship table
DROP TABLE IF EXISTS dish_material CASCADE;

-- Drop dish and material tables
DROP TABLE IF EXISTS dish CASCADE;
DROP TABLE IF EXISTS material CASCADE;

-- Drop material type tables
DROP TABLE IF EXISTS material_child_type CASCADE;
DROP TABLE IF EXISTS material_type CASCADE;

-- Drop dish type tables
DROP TABLE IF EXISTS dish_child_type CASCADE;
DROP TABLE IF EXISTS dish_type CASCADE;

-- ========================================
-- STEP 2: RECREATE DISH & MATERIAL TABLES
-- ========================================

-- Dish type tables
CREATE TABLE dish_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dish_child_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    dish_type_id INTEGER REFERENCES dish_type(id),
    description VARCHAR,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dish_type_id, name)
);

-- Material type tables
CREATE TABLE material_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description VARCHAR,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE material_child_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    material_type_id INTEGER REFERENCES material_type(id),
    description VARCHAR,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(material_type_id, name)
);

-- Dish table
CREATE TABLE dish (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    system_name VARCHAR,
    full_code VARCHAR NOT NULL,
    short_code VARCHAR,
    size VARCHAR,
    dish_child_type_id INTEGER REFERENCES dish_child_type(id),
    specification VARCHAR,
    unit VARCHAR DEFAULT '份',
    serving_size_kg NUMERIC(8, 4),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(full_code, size)
);

-- Material table (store-specific)
CREATE TABLE material (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id),
    name VARCHAR NOT NULL,
    material_number VARCHAR NOT NULL,
    description VARCHAR,
    unit VARCHAR NOT NULL,
    package_spec VARCHAR,
    material_child_type_id INTEGER REFERENCES material_child_type(id),
    material_type_id INTEGER REFERENCES material_type(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(store_id, material_number)
);

-- Dish-Material relationship table (store-specific BOM)
CREATE TABLE dish_material (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES dish(id),
    material_id INTEGER REFERENCES material(id),
    store_id INTEGER REFERENCES store(id),
    standard_quantity NUMERIC(12, 6) NOT NULL,
    loss_rate NUMERIC(5, 2) DEFAULT 1.0,
    unit_conversion_rate NUMERIC(12, 6) DEFAULT 1.0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dish_id, material_id, store_id)
);

-- Price history tables
CREATE TABLE dish_price_history (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES dish(id),
    store_id INTEGER REFERENCES store(id),
    price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    effective_month INTEGER NOT NULL CHECK (effective_month >= 1 AND effective_month <= 12),
    effective_year INTEGER NOT NULL CHECK (effective_year >= 2020),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(dish_id, store_id, effective_month, effective_year)
);

CREATE TABLE material_price_history (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES material(id),
    store_id INTEGER REFERENCES store(id),
    price NUMERIC(12, 4) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CAD',
    effective_month INTEGER NOT NULL CHECK (effective_month >= 1 AND effective_month <= 12),
    effective_year INTEGER NOT NULL CHECK (effective_year >= 2020),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(material_id, store_id, effective_month, effective_year)
);

-- Inventory tracking table
CREATE TABLE inventory_count (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id),
    material_id INTEGER REFERENCES material(id),
    count_date DATE NOT NULL,
    counted_quantity NUMERIC(12, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR,
    UNIQUE(store_id, material_id, count_date)
);

-- Combo table
CREATE TABLE combo (
    id SERIAL PRIMARY KEY,
    combo_code VARCHAR NOT NULL UNIQUE,
    name VARCHAR NOT NULL,
    description VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monthly performance tables
CREATE TABLE dish_monthly_sale (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER REFERENCES dish(id),
    store_id INTEGER REFERENCES store(id),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    year INTEGER NOT NULL CHECK (year >= 2020),
    sale_amount NUMERIC(12, 4) DEFAULT 0,
    return_amount NUMERIC(12, 4) DEFAULT 0,
    free_meal_amount NUMERIC(12, 4) DEFAULT 0,
    gift_amount NUMERIC(12, 4) DEFAULT 0,
    UNIQUE(dish_id, store_id, month, year)
);

CREATE TABLE monthly_combo_dish_sale (
    id SERIAL PRIMARY KEY,
    combo_id INTEGER REFERENCES combo(id),
    dish_id INTEGER REFERENCES dish(id),
    store_id INTEGER REFERENCES store(id),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    year INTEGER NOT NULL CHECK (year >= 2020),
    sale_amount NUMERIC(12, 4) DEFAULT 0,
    UNIQUE(combo_id, dish_id, store_id, month, year)
);

CREATE TABLE material_monthly_usage (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES material(id),
    store_id INTEGER REFERENCES store(id),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    year INTEGER NOT NULL CHECK (year >= 2020),
    material_used NUMERIC(12, 4) NOT NULL,
    UNIQUE(material_id, store_id, month, year)
);

-- ========================================
-- STEP 3: CREATE INDEXES
-- ========================================

-- Dish type indexes
CREATE INDEX idx_dish_type_name ON dish_type(name);
CREATE INDEX idx_dish_type_active ON dish_type(is_active);
CREATE INDEX idx_dish_child_type_dish_type ON dish_child_type(dish_type_id);
CREATE INDEX idx_dish_child_type_active ON dish_child_type(is_active);

-- Material type indexes
CREATE INDEX idx_material_type_name ON material_type(name);
CREATE INDEX idx_material_type_active ON material_type(is_active);
CREATE INDEX idx_material_child_type_material_type ON material_child_type(material_type_id);
CREATE INDEX idx_material_child_type_active ON material_child_type(is_active);

-- Dish indexes
CREATE INDEX idx_dish_code ON dish(full_code);
CREATE INDEX idx_dish_child_type ON dish(dish_child_type_id);
CREATE INDEX idx_dish_active ON dish(is_active);

-- Material indexes
CREATE INDEX idx_material_store_number ON material(store_id, material_number);
CREATE INDEX idx_material_store_active ON material(store_id, is_active);
CREATE INDEX idx_material_type ON material(material_type_id);
CREATE INDEX idx_material_child_type ON material(material_child_type_id);

-- Dish-Material relationship indexes
CREATE INDEX idx_dish_material_store ON dish_material(store_id);
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
CREATE INDEX idx_inventory_count_store_date ON inventory_count(store_id, count_date);

-- Combo indexes
CREATE INDEX idx_combo_code ON combo(combo_code);
CREATE INDEX idx_combo_active ON combo(is_active);

-- Monthly performance indexes
CREATE INDEX idx_dish_monthly_sale_dish_store_date ON dish_monthly_sale(dish_id, store_id, year, month);
CREATE INDEX idx_dish_monthly_sale_store_date ON dish_monthly_sale(store_id, year, month);

CREATE INDEX idx_monthly_combo_dish_sale_combo_dish_store_date ON monthly_combo_dish_sale(combo_id, dish_id, store_id, year, month);
CREATE INDEX idx_monthly_combo_dish_sale_store_date ON monthly_combo_dish_sale(store_id, year, month);

CREATE INDEX idx_material_monthly_usage_material_store_date ON material_monthly_usage(material_id, store_id, year, month);
CREATE INDEX idx_material_monthly_usage_store_date ON material_monthly_usage(store_id, year, month);

-- ========================================
-- STEP 4: CREATE TRIGGERS
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

-- Function to validate dish_material store consistency
CREATE OR REPLACE FUNCTION validate_dish_material_store_consistency()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if material belongs to the same store as the relationship
    IF NOT EXISTS (
        SELECT 1 FROM material m 
        WHERE m.id = NEW.material_id 
        AND m.store_id = NEW.store_id
    ) THEN
        RAISE EXCEPTION 'dish_material store_id must match material store_id';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce store consistency on dish_material
CREATE TRIGGER trigger_dish_material_store_consistency
    BEFORE INSERT OR UPDATE ON dish_material
    FOR EACH ROW
    EXECUTE FUNCTION validate_dish_material_store_consistency();

-- ========================================
-- DISH DATA RESET COMPLETE
-- ========================================
-- Summary:
-- - All dish-related tables have been dropped and recreated
-- - Store operational data (daily_report, store_time_report, etc.) is preserved
-- - Store and district data remains intact
-- - Monthly targets and time segment targets are preserved
-- - All indexes and triggers have been recreated
-- - Ready for fresh dish/material data import