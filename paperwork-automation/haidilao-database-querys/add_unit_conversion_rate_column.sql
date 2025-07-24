-- ========================================
-- ADD UNIT_CONVERSION_RATE COLUMN TO DISH_MATERIAL TABLE
-- ========================================
-- This migration adds unit_conversion_rate column to support material unit conversions
-- Used for converting theoretical usage and combo usage in material reports

-- Add unit_conversion_rate column to dish_material table
ALTER TABLE dish_material 
ADD COLUMN IF NOT EXISTS unit_conversion_rate NUMERIC(12, 6) DEFAULT 1.0;

-- Add comment to document the column purpose
COMMENT ON COLUMN dish_material.unit_conversion_rate IS 'Unit conversion rate from 物料单位 field. If blank, defaults to 1.0. Used to convert theoretical and combo usage calculations.';

-- Update existing records to have default conversion rate of 1.0
UPDATE dish_material 
SET unit_conversion_rate = 1.0 
WHERE unit_conversion_rate IS NULL;

-- Set NOT NULL constraint after updating existing records
ALTER TABLE dish_material 
ALTER COLUMN unit_conversion_rate SET NOT NULL;

-- Add index for performance on queries that filter by conversion rate
CREATE INDEX IF NOT EXISTS idx_dish_material_conversion_rate 
ON dish_material(unit_conversion_rate);

-- Example of expected data:
-- INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
-- VALUES (
--     (SELECT id FROM dish WHERE full_code = '1060062'),
--     (SELECT id FROM material WHERE material_number = '1500882'),
--     1.0,        -- standard_quantity
--     1.0,        -- loss_rate  
--     0.354       -- unit_conversion_rate from "物料单位" field
-- );

-- Verification query to check the new column
-- SELECT d.full_code, m.material_number, dm.standard_quantity, dm.unit_conversion_rate
-- FROM dish_material dm
-- JOIN dish d ON dm.dish_id = d.id  
-- JOIN material m ON dm.material_id = m.id
-- WHERE d.full_code = '1060062' AND m.material_number = '1500882'; 