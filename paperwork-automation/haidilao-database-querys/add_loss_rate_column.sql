-- Migration script to add loss_rate column to dish_material table
-- Run this script to add the loss_rate column to existing databases

-- Add loss_rate column to dish_material table
ALTER TABLE dish_material 
ADD COLUMN IF NOT EXISTS loss_rate NUMERIC(5, 2) DEFAULT 1.0;

-- Update the loss_rate to 1.0 for existing records (no loss)
UPDATE dish_material 
SET loss_rate = 1.0 
WHERE loss_rate IS NULL;

-- Add comment to the column
COMMENT ON COLUMN dish_material.loss_rate IS '损耗率 (默认1.0 = 无损耗)';

-- Verify the column was added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'dish_material' 
ORDER BY ordinal_position; 