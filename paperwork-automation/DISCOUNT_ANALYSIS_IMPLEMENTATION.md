# Discount Analysis Implementation Summary

## Overview
This document summarizes the implementation of the detailed discount analysis feature for the monthly gross margin report.

## Changes Made

### 1. Database Schema Enhancements

**New Tables Created:**
- `discount_type` - Lookup table for discount categories
- `daily_discount_detail` - Stores detailed daily discount information by type
- `monthly_discount_summary` - Pre-aggregated monthly summary with automatic triggers

**SQL File:**
- `haidilao-database-querys/add_discount_analysis_tables.sql`

### 2. Data Extraction Updates

**Modified `lib/data_extraction.py`:**
- Added `save_discount_details()` function to capture discount data during extraction
- Integrated automatic discount detail saving when processing daily reports
- Maintains backward compatibility with existing extraction workflows

### 3. Monthly Gross Margin Report Enhancement

**Updated `scripts/generate_monthly_gross_margin_report.py`:**
- Implemented `_get_discount_analysis_data()` method with full query logic
- Queries discount data by type with MoM/YoY comparisons
- Calculates discount as percentage of revenue
- Populates the previously empty "打折优惠表" sheet

### 4. Setup and Migration Scripts

**New Scripts Created:**
- `scripts/setup_discount_analysis.py` - One-command setup for discount analysis
- `scripts/migrate_discount_data.py` - Migrates existing discount_total data
- `scripts/verify_discount_analysis.py` - Comprehensive verification tool

### 5. Documentation Updates

**Updated README.md:**
- Added discount analysis setup instructions
- Documented the enhanced discount analysis in monthly reports
- Added details about discount types tracked

## Discount Types Supported

1. 会员折扣 (Member discount)
2. 生日优惠 (Birthday promotion)
3. 节日优惠 (Holiday promotion)
4. 满减活动 (Spend and save promotion)
5. 新客优惠 (New customer discount)
6. 团购优惠 (Group purchase discount)
7. 员工折扣 (Employee discount)
8. 赠送 (Complimentary)
9. 其他优惠 (Other promotions) - Default for migrated data

## Setup Instructions

1. **Create Tables and Migrate Data:**
   ```bash
   python3 scripts/setup_discount_analysis.py
   ```

2. **Verify Setup:**
   ```bash
   python3 scripts/verify_discount_analysis.py
   ```

3. **Generate Report:**
   ```bash
   python3 scripts/generate_monthly_gross_margin_report.py --target-date 2025-05-31
   ```

## How It Works

1. **Daily Extraction:** When daily reports are extracted, the total discount amount is automatically saved to `daily_discount_detail` table (currently as "其他优惠" type)

2. **Monthly Aggregation:** A database trigger automatically updates `monthly_discount_summary` whenever daily details are inserted/updated

3. **Report Generation:** The monthly gross margin report queries the aggregated data and displays:
   - Discount breakdown by type and store
   - Month-over-month comparisons
   - Year-over-year comparisons
   - Discount as percentage of revenue

## Future Enhancements

To capture more detailed discount types from the source Excel files:
1. Analyze the daily report structure for discount type columns
2. Update the extraction logic to parse specific discount types
3. Map Excel discount categories to database discount types

## Testing

Run the verification script to ensure everything is working:
```bash
python3 scripts/verify_discount_analysis.py
```

This will check:
- Table existence
- Data migration success
- Monthly aggregation accuracy
- Query performance

## Backward Compatibility

- Existing workflows continue to function without modification
- Historical data is automatically migrated as "其他优惠" type
- No changes required to existing automation scripts