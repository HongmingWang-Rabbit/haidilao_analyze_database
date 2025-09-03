-- Migration script to convert inventory_count from date-based to month/year-based
-- This preserves existing data while updating the schema

-- Step 1: Create a temporary table with the new structure
CREATE TABLE inventory_count_new (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id),
    material_id INTEGER REFERENCES material(id),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    year INTEGER NOT NULL CHECK (year >= 2020),
    counted_quantity NUMERIC(12, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR,
    UNIQUE(store_id, material_id, month, year)
);

-- Step 2: Copy data from old table to new table
-- Extract month and year from count_date
INSERT INTO inventory_count_new (store_id, material_id, month, year, counted_quantity, created_at, created_by)
SELECT 
    store_id,
    material_id,
    EXTRACT(MONTH FROM count_date)::INTEGER as month,
    EXTRACT(YEAR FROM count_date)::INTEGER as year,
    counted_quantity,
    created_at,
    created_by
FROM inventory_count
ON CONFLICT (store_id, material_id, month, year) 
DO UPDATE SET 
    counted_quantity = EXCLUDED.counted_quantity;

-- Step 3: Drop the old table and rename the new one
DROP TABLE inventory_count CASCADE;
ALTER TABLE inventory_count_new RENAME TO inventory_count;

-- Step 4: Recreate indexes
CREATE INDEX idx_inventory_count_store_date ON inventory_count(store_id, year, month);
CREATE INDEX idx_inventory_count_material ON inventory_count(material_id);

-- Step 5: Add foreign key constraints back if needed
-- (These should already be in place from the table creation)

COMMENT ON TABLE inventory_count IS 'Monthly inventory counts per store and material';
COMMENT ON COLUMN inventory_count.month IS 'Month of inventory count (1-12)';
COMMENT ON COLUMN inventory_count.year IS 'Year of inventory count';