# Fix for Missing Material Data in Gross Margin Report

The historical extraction completed but extracted 0 materials and 0 material prices. This is why the gross margin report has empty sheets.

## Quick Fix - Extract Materials Manually

### Step 1: Extract Material Usage Data

```powershell
python3 scripts/automation-menu.py
```

Choose:
1. Option `4` (Extract Data Only)
2. Option `5` (Monthly Material Usage)
3. Navigate to file: `history_files\monthly_report_inputs\2025-05\monthly_material_usage\mb5b.xls`
4. Enter target date: `2025-05-31`

### Step 2: Extract Material Prices (All Stores)

```powershell
python3 scripts/automation-menu.py
```

Choose:
1. Option `4` (Extract Data Only)
2. Option `z` (Batch Extract Material Prices - All Stores)
3. Navigate to folder: `history_files\monthly_report_inputs\2025-05\material_detail`
4. Enter target date: `2025-05-31`
5. Debug mode: `n`

### Step 3: Extract Materials for Other Months (Optional)

If you need April 2025 data for comparisons:
- Repeat steps 1-2 for April folder with date `2025-04-30`

If you need May 2024 data for year-over-year:
- Repeat steps 1-2 for 2024-05 folder with date `2024-05-31`

### Step 4: Regenerate the Gross Margin Report

```powershell
python3 scripts/generate_monthly_gross_margin_report.py --target-date 2025-05-31
```

## Alternative - Direct Commands

### Extract Material Usage:
```powershell
python3 scripts/extract-materials.py "history_files\monthly_report_inputs\2025-05\monthly_material_usage\mb5b.xls" --target-date 2025-05-31 --direct-db
```

### Extract Material Prices for All Stores:
```powershell
# For each store (1-7)
python3 scripts/extract_material_prices_by_store.py --store-id 1 --file "history_files\monthly_report_inputs\2025-05\material_detail\1\ca01-202505.XLSX" --date 2025-05-31 --direct-db

python3 scripts/extract_material_prices_by_store.py --store-id 2 --file "history_files\monthly_report_inputs\2025-05\material_detail\2\ca02-202505.XLSX" --date 2025-05-31 --direct-db

# ... repeat for stores 3-7
```

## Verify Material Data

After extraction, verify the data:

```powershell
psql -U hongming -d haidilao-paperwork -c "SELECT COUNT(*) FROM material;"
psql -U hongming -d haidilao-paperwork -c "SELECT COUNT(*) FROM material_monthly_usage WHERE year = 2025 AND month = 5;"
psql -U hongming -d haidilao-paperwork -c "SELECT COUNT(*) FROM material_price_history WHERE effective_date = '2025-05-31';"
```

## Why Did Historical Extraction Fail?

The historical extraction script has these limitations:
1. It limits rows to 500 for safety (materials might be beyond row 500)
2. It might be skipping .xls files or having encoding issues
3. The material extraction logic might be too strict in filtering

The manual extraction bypasses these issues by using the dedicated material extraction scripts.