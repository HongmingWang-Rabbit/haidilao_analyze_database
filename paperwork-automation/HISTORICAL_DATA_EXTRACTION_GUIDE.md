# Historical Data Extraction and Monthly Report Generation Guide

## Overview
This guide walks through extracting all historical data and generating a complete monthly report with discount analysis.

## Step 1: Extract Daily Report Historical Data

Daily reports contain revenue, customer counts, and discount totals. You need to extract these first.

### Option A: Via Automation Menu
```bash
python3 scripts/automation-menu.py
# Select: 4) 📥 Extract Data Only (Generate SQL Files)
# Then: 1) Extract Daily Report (营业日报表)
# Point to your daily report Excel file in history_files/daily_report_inputs/
```

### Option B: Direct Command
```bash
# Extract a specific daily report file
python3 scripts/extract-all.py "history_files/daily_report_inputs/20240401-20250724/daily_store_report/海外门店经营日报数据_20250725_1853.xlsx" --direct-db --daily-only

# Or extract all daily reports in a folder
for file in history_files/daily_report_inputs/20240401-20250724/daily_store_report/*.xlsx; do
    echo "Processing: $file"
    python3 scripts/extract-all.py "$file" --direct-db --daily-only
done
```

## Step 2: Extract Monthly Historical Data

This extracts dishes, materials, prices, and monthly sales/usage data.

### Via Automation Menu (Recommended)
```bash
python3 scripts/automation-menu.py
# Select: 4) 📥 Extract Data Only (Generate SQL Files)
# Then: h) Historical Data Extraction (All Months)

# When prompted:
# - Start month: 2024-05 (or press Enter for all)
# - End month: 2025-06 (or press Enter for all)
# - Enable debug: n
```

This will extract:
- Dish types and dishes from monthly_dish_sale/
- Dish price history
- Materials from monthly_material_usage/
- Material price history from material_detail/

## Step 3: Run Complete Monthly Automation

After historical data is extracted, run the monthly automation for May 2025:

### Via Automation Menu
```bash
python3 scripts/automation-menu.py
# Select: 3) 📊 Complete Monthly Automation (NEW WORKFLOW)
# Enter target date: 2025-05-31
```

### Direct Command
```bash
python3 scripts/complete_monthly_automation_new.py --date 2025-05-31
```

This will:
1. Extract monthly dish sales data
2. Extract material usage data
3. Extract material prices
4. Generate material variance report
5. Generate beverage variance report
6. Generate monthly gross margin report (with discount analysis)

## Step 4: Verify the Generated Reports

Check the output directory for generated reports:
```bash
# List all generated reports
ls -la output/monthly_reports/2025/05/
ls -la output/monthly_gross_margin/

# The main gross margin report with discount analysis:
# output/monthly_gross_margin/毛利相关分析指标-202505.xlsx
```

## Step 5: Troubleshooting

### If some sheets are empty:

1. **Check if historical data was extracted:**
   ```bash
   python3 scripts/verify_gross_margin_queries.sql
   ```

2. **Verify discount data:**
   ```bash
   python3 scripts/verify_discount_analysis.py
   ```

3. **Check specific data availability:**
   ```sql
   -- Connect to database
   psql -U hongming -d haidilao-paperwork

   -- Check dish monthly sales for May 2025
   SELECT COUNT(*) FROM dish_monthly_sale WHERE year = 2025 AND month = 5;
   
   -- Check material monthly usage
   SELECT COUNT(*) FROM material_monthly_usage WHERE year = 2025 AND month = 5;
   
   -- Check price history
   SELECT COUNT(*) FROM material_price_history WHERE effective_date BETWEEN '2025-05-01' AND '2025-05-31';
   ```

## Quick Start Commands

For a complete setup and report generation:

```bash
# 1. Fix encoding (Windows only)
chcp 65001

# 2. Extract daily reports (if you have them)
python3 scripts/extract-all.py "history_files/daily_report_inputs/20240401-20250724/daily_store_report/海外门店经营日报数据_20250725_1853.xlsx" --direct-db --daily-only

# 3. Extract all monthly historical data
python3 scripts/automation-menu.py
# Select option 4, then h

# 4. Run complete monthly automation for May 2025
python3 scripts/complete_monthly_automation_new.py --date 2025-05-31

# 5. Verify the report
# Check: output/monthly_gross_margin/毛利相关分析指标-202505.xlsx
```

## Expected Output

The monthly gross margin report should contain:
1. **菜品价格变动及菜品损耗表** - Dish price changes and loss analysis
2. **原材料成本变动表** - Material cost changes (with data)
3. **打折优惠表** - Discount analysis by type (with data from migration)
4. **各店毛利率分析** - Store gross profit analysis (with costs)
5. **月度毛利汇总** - Monthly summary (with data)
6. **同比环比分析** - YoY/MoM analysis (with comparisons)

All sheets should have data after proper historical extraction.