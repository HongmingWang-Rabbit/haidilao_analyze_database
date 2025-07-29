# Monthly Gross Margin Report Fixes Summary

## Issues Found and Fixed

### 1. Store Gross Profit Analysis (各店毛利率分析) - Zero Costs Issue

**Problem**: The costs were showing as zero because the material price history join wasn't finding matching prices.

**Root Cause**: The original query was doing a simple LEFT JOIN on `material_price_history` with only `is_active = true`, which wasn't matching any prices for the specific dates.

**Fix Applied** in `lib/database_queries.py`:
```sql
-- OLD (not working):
LEFT JOIN material_price_history mph ON mmu.material_id = mph.material_id
    AND mmu.store_id = mph.store_id
    AND mph.is_active = true

-- NEW (fixed):
LEFT JOIN LATERAL (
    SELECT price 
    FROM material_price_history 
    WHERE material_id = mmu.material_id 
        AND store_id = mmu.store_id 
        AND is_active = true
        AND effective_date <= CAST(%s || '-' || LPAD(%s::text, 2, '0') || '-31' AS DATE)
    ORDER BY effective_date DESC
    LIMIT 1
) mph ON true
```

This fix ensures we get the most recent price on or before the target month end date.

### 2. Material Cost Changes (原材料成本变动表) - Empty Sheet

**Problem**: The sheet was empty because it was using wrong table names.

**Root Cause**: Query was using `material_usage`, `materials`, `stores` instead of the correct `material_monthly_usage`, `material`, `store`.

**Fix Applied** in `scripts/generate_monthly_gross_margin_report.py`:
- Changed all table references to match the actual schema
- Updated the price lookup to use LATERAL JOIN
- Fixed parameter passing for year/month values

### 3. Monthly Summary (月度毛利汇总) - Empty Sheet  

**Problem**: No data was showing in the monthly summary.

**Root Cause**: Similar table naming issues and the query was trying to use `daily_reports` which doesn't exist (should be `daily_report` or use monthly tables).

**Fix Applied**: 
- Rewrote query to use `dish_monthly_sale` for revenue
- Used proper material cost calculation with LATERAL JOIN
- Separated current/previous/last year calculations

### 4. YoY/MoM Analysis (同比环比分析) - Table Issues

**Fix Applied**: Updated the main costs subquery to use monthly tables with proper joins.

## Verification Steps

### 1. Check Database Data
Run the SQL verification script to see if data exists:
```bash
psql -U hongming -d haidilao-paperwork -f scripts/verify_gross_margin_queries.sql
```

This will show:
- Store-by-store revenue and costs for May 2025
- Material cost analysis with price changes
- Monthly summary totals
- Data availability counts

### 2. Generate the Report
Once Python environment is set up with required packages:
```bash
pip install openpyxl pandas psycopg2-binary
python3 scripts/generate_monthly_gross_margin_report.py --target-date 2025-05-31
```

### 3. Compare with Manual File
The generated file will be at: `output/monthly_gross_margin/毛利相关分析指标-202505.xlsx`
Compare with manual file: `data/dishes_related/附件3-毛利相关分析指标-2505.xlsx`

## Expected Results

After the fixes, the report should show:

1. **各店毛利率分析** - Each store's revenue, costs, and gross margins for current and previous month
2. **原材料成本变动表** - Material costs with month-over-month and year-over-year price changes
3. **月度毛利汇总** - Summary of all stores with total revenue, costs, and margins
4. **同比环比分析** - Detailed comparison analysis

## Remaining Issue

The **打折优惠表** (Discount Analysis) sheet will remain empty as it's currently a placeholder. This would require:
- A discount/promotion data table in the database
- Implementation of the `_get_discount_analysis_data` method

## Key Technical Changes

1. **LATERAL JOIN**: Used throughout for price lookups to ensure we get the correct historical price
2. **Proper Table Names**: Fixed all references to match actual database schema
3. **Date Handling**: Prices are matched by effective_date <= month end date
4. **Parameter Matching**: Ensured SQL parameters match the query placeholders

The fixes ensure that the monthly gross margin report will properly calculate and display:
- Revenue from `dish_monthly_sale`
- Costs from `material_monthly_usage` with prices from `material_price_history`
- Proper month-over-month and year-over-year comparisons