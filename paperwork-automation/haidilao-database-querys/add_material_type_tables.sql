-- Migration: Add Material Type Tables and Update Material Table Structure
-- This script safely adds material classification tables similar to dish classification
-- Run this BEFORE extracting material data from material_detail files

-- ========================================
-- ADD MATERIAL TYPE TABLES
-- ========================================

-- Create material_type table if it doesn't exist
CREATE TABLE IF NOT EXISTS material_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,          -- 大类名称 (from 187-一级分类)
    description VARCHAR,                   -- 描述
    sort_order INTEGER DEFAULT 0,         -- 排序顺序
    is_active BOOLEAN DEFAULT TRUE,       -- 是否活跃
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create material_child_type table if it doesn't exist
CREATE TABLE IF NOT EXISTS material_child_type (
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

-- Add new columns to material table if they don't exist
DO $$
BEGIN
    -- Add material_type_id column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'material' AND column_name = 'material_type_id'
    ) THEN
        ALTER TABLE material ADD COLUMN material_type_id INTEGER REFERENCES material_type(id);
        COMMENT ON COLUMN material.material_type_id IS '外键：物料大类 (from 187-一级分类)';
    END IF;
    
    -- Add material_child_type_id column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'material' AND column_name = 'material_child_type_id'
    ) THEN
        ALTER TABLE material ADD COLUMN material_child_type_id INTEGER REFERENCES material_child_type(id);
        COMMENT ON COLUMN material.material_child_type_id IS '外键：物料子类 (from 187-二级分类, 可为空)';
    END IF;
END
$$;

-- ========================================
-- ADD INDEXES
-- ========================================

-- Create indexes if they don't exist
DO $$
BEGIN
    -- Material type indexes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_material_type_name') THEN
        CREATE INDEX idx_material_type_name ON material_type(name);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_material_type_active') THEN
        CREATE INDEX idx_material_type_active ON material_type(is_active);
    END IF;
    
    -- Material child type indexes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_material_child_type_material_type') THEN
        CREATE INDEX idx_material_child_type_material_type ON material_child_type(material_type_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_material_child_type_active') THEN
        CREATE INDEX idx_material_child_type_active ON material_child_type(is_active);
    END IF;
    
    -- Material table indexes for new columns
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_material_type') THEN
        CREATE INDEX idx_material_type ON material(material_type_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_material_child_type') THEN
        CREATE INDEX idx_material_child_type ON material(material_child_type_id);
    END IF;
END
$$;

-- ========================================
-- ADD TRIGGERS
-- ========================================

-- Create or replace the update function (if it doesn't exist)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for new tables
DO $$
BEGIN
    -- Material type trigger
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_material_type_updated_at'
    ) THEN
        CREATE TRIGGER update_material_type_updated_at 
        BEFORE UPDATE ON material_type
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    -- Material child type trigger
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_material_child_type_updated_at'
    ) THEN
        CREATE TRIGGER update_material_child_type_updated_at 
        BEFORE UPDATE ON material_child_type
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;

-- ========================================
-- INITIAL DATA INSERTION
-- ========================================

-- Insert material types based on the data analysis
-- From 187-一级分类 column in material_detail export
INSERT INTO material_type (name, description, sort_order, is_active) VALUES
('员工餐', 'Employee meals', 1, TRUE),
('成本-其他类', 'Cost - Other category', 2, TRUE),
('成本-小吃类', 'Cost - Snack category', 3, TRUE),
('成本-小料台类', 'Cost - Condiment station category', 4, TRUE),
('成本-素菜类', 'Cost - Vegetable category', 5, TRUE),
('成本-荤菜类', 'Cost - Meat category', 6, TRUE),
('成本-酒水类', 'Cost - Beverages category', 7, TRUE),
('成本-锅底类', 'Cost - Hot pot base category', 8, TRUE),
('服务费', 'Service fees', 9, TRUE),
('服装费', 'Clothing expenses', 10, TRUE),
('物料消耗', 'Material consumption', 11, TRUE)
ON CONFLICT (name) DO UPDATE SET
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

-- Insert material child types based on the data analysis
-- From 187-二级分类 column in material_detail export
INSERT INTO material_child_type (name, material_type_id, description, sort_order, is_active)
SELECT 
    child_type_name,
    mt.id,
    child_description,
    child_sort_order,
    TRUE
FROM (VALUES
    -- 成本-小料台类 -> 水果
    ('水果', '成本-小料台类', 'Fruits', 1),
    -- 服装费 -> 工服
    ('工服', '服装费', 'Work uniforms', 1),
    -- 物料消耗 -> multiple child types
    ('其他类', '物料消耗', 'Other category', 1),
    ('清洁类', '物料消耗', 'Cleaning supplies', 2),
    ('纸巾类', '物料消耗', 'Tissue category', 3),
    ('餐具类', '物料消耗', 'Tableware category', 4)
) AS child_data(child_type_name, parent_type_name, child_description, child_sort_order)
JOIN material_type mt ON mt.name = child_data.parent_type_name
ON CONFLICT (material_type_id, name) DO UPDATE SET
    description = EXCLUDED.description,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

-- ========================================
-- MIGRATION COMPLETE
-- ========================================
COMMIT;

-- Summary
SELECT 
    'Material Type Tables Migration Complete' as status,
    (SELECT COUNT(*) FROM material_type) as material_types_count,
    (SELECT COUNT(*) FROM material_child_type) as material_child_types_count,
    (SELECT COUNT(*) FROM material WHERE material_type_id IS NOT NULL) as materials_with_type_count,
    (SELECT COUNT(*) FROM material WHERE material_child_type_id IS NOT NULL) as materials_with_child_type_count; 