-- Migration script to add material_use_type column to material_monthly_usage table
-- Run this script to update existing database

-- Add the new column if it doesn't exist
ALTER TABLE material_monthly_usage 
ADD COLUMN IF NOT EXISTS material_use_type VARCHAR(100);

-- Add comment to describe the column
COMMENT ON COLUMN material_monthly_usage.material_use_type IS '物料使用类型 (来自material_detail的大类字段)';

-- Display confirmation
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'material_monthly_usage' 
    AND column_name = 'material_use_type';