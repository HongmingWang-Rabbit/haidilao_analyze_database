-- ========================================
-- MATERIAL TABLES RESET (DEVELOPMENT/TESTING ONLY)
-- ========================================
-- WARNING: This will delete all material-related data. Use with caution.
-- This script only resets material-related tables for debugging purposes.

-- Drop material-related tables in reverse dependency order
-- First drop all tables that depend on material tables

-- Drop monthly performance tables (material-related only)
DROP TABLE IF EXISTS material_monthly_usage;

-- Drop inventory and price history tables (material-related only)
DROP TABLE IF EXISTS inventory_count;
DROP TABLE IF EXISTS material_price_history;

-- Drop dish-material relationship table
DROP TABLE IF EXISTS dish_material;

-- Drop main material table
DROP TABLE IF EXISTS material;

-- Drop material classification tables
DROP TABLE IF EXISTS material_child_type;
DROP TABLE IF EXISTS material_type;

-- Create material type table
CREATE TABLE material_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    sort_order INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create material child type table
CREATE TABLE material_child_type (
    id SERIAL PRIMARY KEY,
    material_type_id INTEGER NOT NULL REFERENCES material_type(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(material_type_id, name)
);

-- Create material table
CREATE TABLE material (
    id SERIAL PRIMARY KEY,
    material_number VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description VARCHAR(200),
    unit VARCHAR(50),
    package_spec VARCHAR(200),
    material_type_id INTEGER REFERENCES material_type(id),
    material_child_type_id INTEGER REFERENCES material_child_type(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create material price history table (store-specific)
CREATE TABLE material_price_history (
    id SERIAL PRIMARY KEY,
    material_id INTEGER NOT NULL REFERENCES material(id),
    store_id INTEGER NOT NULL REFERENCES store(id),
    price DECIMAL(10,4) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CAD',
    effective_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(material_id, store_id, effective_date)
);

-- Create inventory count table
CREATE TABLE inventory_count (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES store(id),
    material_id INTEGER NOT NULL REFERENCES material(id),
    count_date DATE NOT NULL,
    counted_quantity DECIMAL(10,3) NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create dish-material relationship table
CREATE TABLE dish_material (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER NOT NULL REFERENCES dish(id),
    material_id INTEGER NOT NULL REFERENCES material(id),
    standard_quantity DECIMAL(10,4) NOT NULL DEFAULT 1.0,
    loss_rate DECIMAL(5,4) DEFAULT 1.0,
    unit_conversion_rate DECIMAL(12,6) DEFAULT 1.0 NOT NULL,
    unit VARCHAR(50),
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dish_id, material_id)
);

-- Create material monthly usage table
CREATE TABLE material_monthly_usage (
    id SERIAL PRIMARY KEY,
    material_id INTEGER NOT NULL REFERENCES material(id),
    store_id INTEGER NOT NULL REFERENCES store(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    material_used DECIMAL(10,3) NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(material_id, store_id, year, month)
);

-- Create indexes for performance
CREATE INDEX idx_material_number ON material(material_number);
CREATE INDEX idx_material_type ON material(material_type_id);
CREATE INDEX idx_material_child_type ON material(material_child_type_id);
CREATE INDEX idx_material_price_history_material ON material_price_history(material_id);
CREATE INDEX idx_material_price_history_store ON material_price_history(store_id);
CREATE INDEX idx_material_price_history_date ON material_price_history(effective_date);
CREATE INDEX idx_material_price_history_active ON material_price_history(is_active);
CREATE INDEX idx_inventory_count_material ON inventory_count(material_id);
CREATE INDEX idx_inventory_count_store ON inventory_count(store_id);
CREATE INDEX idx_inventory_count_date ON inventory_count(count_date);
CREATE INDEX idx_dish_material_dish ON dish_material(dish_id);
CREATE INDEX idx_dish_material_material ON dish_material(material_id);
CREATE INDEX idx_material_monthly_usage_material ON material_monthly_usage(material_id);
CREATE INDEX idx_material_monthly_usage_store ON material_monthly_usage(store_id);
CREATE INDEX idx_material_monthly_usage_period ON material_monthly_usage(year, month);

-- Insert default material types
INSERT INTO material_type (name, description, sort_order, is_active) VALUES
('调料类', 'Seasoning materials', 1, TRUE),
('蔬菜类', 'Vegetable materials', 2, TRUE),
('肉类', 'Meat materials', 3, TRUE),
('海鲜类', 'Seafood materials', 4, TRUE),
('豆制品', 'Tofu and bean products', 5, TRUE),
('面食类', 'Noodle and flour products', 6, TRUE),
('饮料类', 'Beverage materials', 7, TRUE),
('酒水类', 'Alcoholic beverages', 8, TRUE),
('包装用品', 'Packaging materials', 9, TRUE),
('清洁用品', 'Cleaning supplies', 10, TRUE),
('其他', 'Other materials', 11, TRUE);

-- Insert default material child types
INSERT INTO material_child_type (material_type_id, name, description, sort_order, is_active) 
SELECT id, '通用', 'General category', 1, TRUE FROM material_type;

-- Insert specific child types for beverages
INSERT INTO material_child_type (material_type_id, name, description, sort_order, is_active) VALUES
((SELECT id FROM material_type WHERE name = '饮料类'), '碳酸饮料', 'Carbonated drinks', 2, TRUE),
((SELECT id FROM material_type WHERE name = '饮料类'), '果汁饮料', 'Fruit juice drinks', 3, TRUE),
((SELECT id FROM material_type WHERE name = '饮料类'), '茶饮料', 'Tea beverages', 4, TRUE),
((SELECT id FROM material_type WHERE name = '酒水类'), '啤酒', 'Beer', 2, TRUE),
((SELECT id FROM material_type WHERE name = '酒水类'), '白酒', 'Spirits', 3, TRUE);

-- Add update triggers
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_material_modtime BEFORE UPDATE ON material
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_inventory_count_modtime BEFORE UPDATE ON inventory_count
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_dish_material_modtime BEFORE UPDATE ON dish_material
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_material_monthly_usage_modtime BEFORE UPDATE ON material_monthly_usage
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE '✅ Material tables reset completed successfully';
    RAISE NOTICE '📊 Tables created: material_type, material_child_type, material, material_price_history, inventory_count, dish_material, material_monthly_usage';
    RAISE NOTICE '🔍 Indexes and triggers created';
    RAISE NOTICE '📝 Default material types and child types inserted';
END $$; 