# Dish-Material Extraction Scripts

This folder contains scripts for extracting and managing dish, material, and dish-material mapping (BOM) data for Haidilao restaurants.

## Scripts Overview

### 1. `extract_dishes_to_database.py`
Extracts dish information from monthly sales Excel files.
- **Input**: Excel files with sheet "菜品销售汇总表" 
- **Default Path**: `Input/monthly_report/{year}_{month:02d}/`
- **Creates**: Dishes, dish types, dish prices, dish sales

### 2. `extract_materials_to_database.py`
Extracts material master data from SAP export files.
- **Input**: export.XLSX file from material detail
- **Default Path**: `Input/monthly_report/material_detail/export.XLSX`
- **Creates**: Materials (store-specific), material types, material prices, material usage

### 3. `extract_dish_material_mapping.py`
Creates BOM (Bill of Materials) relationships between dishes and materials.
- **Input**: Calculated dish material usage Excel file
- **Default Path**: `Input/monthly_report/calculated_dish_material_usage/inventory_calculation_*.xlsx`
- **Creates**: Dish-material mappings with quantities and waste factors

### 4. `run_all.py` (Simple Index)
Runs all three extraction scripts in sequence with default inputs.
```bash
python run_all.py --year 2025 --month 7
```

### 5. `run_all_extractions.py` (Advanced Index)
Comprehensive extraction pipeline with options to skip steps and use custom inputs.
```bash
# Run all extractions
python run_all_extractions.py --year 2025 --month 7

# Skip specific steps
python run_all_extractions.py --year 2025 --month 7 --skip-materials

# Use custom input files
python run_all_extractions.py --year 2025 --month 7 \
    --material-input "path/to/export.XLSX" \
    --mapping-input "path/to/mapping.xlsx"
```

## Extraction Order

The scripts MUST be run in this order:
1. **Dishes** - Creates dish records needed by mappings
2. **Materials** - Creates material records (store-specific) needed by mappings  
3. **Mappings** - Links dishes to materials with quantities

## Key Features

### Store-Specific Materials
Materials are store-specific based on the 工厂 (store code) column:
- CA01 → Store 1 (加拿大一店)
- CA02 → Store 2 (加拿大二店)
- CA03 → Store 3 (加拿大三店)
- CA04 → Store 4 (加拿大四店)
- CA05 → Store 5 (加拿大五店)
- CA06 → Store 6 (加拿大六店)
- CA07 → Store 7 (加拿大七店)

### Material Number Processing
- Leading zeros are automatically removed from material numbers
- Example: "000001500680" → "1500680"

### File Format Support
- Excel files (.xlsx, .xls)
- UTF-16 encoded TSV files (SAP exports that appear as .xls)

## Database Tables Updated

- `dish` - Dish master data
- `dish_type` / `dish_child_type` - Dish categorization
- `dish_price_history` - Historical dish prices by store
- `dish_monthly_sale` - Monthly sales data
- `material` - Material master data (store-specific)
- `material_type` / `material_child_type` - Material categorization
- `material_price_history` - Historical material prices by store
- `material_monthly_usage` - Monthly material usage
- `dish_material` - BOM relationships (dish → materials mapping)

## Common Issues

1. **"File is not a zip file"**: The .xls file is actually UTF-16 TSV. The scripts automatically handle this.

2. **Material not found**: Materials must be extracted first before running mapping extraction.

3. **Column name errors**: Check database schema matches script expectations:
   - `dish_material.standard_quantity` (not `quantity`)
   - `dish_material.loss_rate` (not `waste_factor`) 
   - `material_monthly_usage.material_used` (not `usage_quantity`)

## Example Workflow

```bash
# Clear existing data (optional - BE CAREFUL)
python -c "from utils.database import DatabaseManager, DatabaseConfig; ..."

# Run all extractions for July 2025
python run_all.py --year 2025 --month 7

# Or run individually
python extract_dishes_to_database.py --year 2025 --month 7
python extract_materials_to_database.py --year 2025 --month 7
python extract_dish_material_mapping.py --year 2025 --month 7
```

## Output Statistics

After successful extraction:
- ~500-800 dishes
- ~3,500 materials (across 7 stores)
- ~2,500 dish-material mappings