# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Production-grade automation system for processing Haidilao restaurant operational data from Excel files and generating comprehensive business reports. The system handles daily operational data, time segment analysis, material usage tracking, and generates professional Excel reports for business analysis.

**System Purpose**: Automate the extraction, processing, and reporting of restaurant operational data for 7 Canadian Haidilao stores plus Hi Bowl franchise, replacing manual Excel-based workflows with automated database-driven reporting.

## Key Commands

### Primary Entry Points

```bash
# GUI Interface (recommended for interactive use)
python3 scripts/automation-gui.py

# CLI Menu (recommended for automation)
python3 scripts/automation-menu.py

# Complete automation workflows
python3 scripts/complete_automation.py --target-date YYYY-MM-DD
python3 scripts/complete_monthly_automation_new.py --target-date YYYY-MM-DD

# QBI web scraping with authentication
python3 scripts/qbi_scraper_cli.py --target-date YYYY-MM-DD

# Bank transaction processing
python3 scripts/process_bank_transactions.py

# Hi Bowl daily processing
python3 scripts/process_hi_bowl_daily.py --target-date YYYY-MM-DD
```

### Testing

```bash
# Run all tests with detailed output
python3 -m unittest discover tests -v

# Run specific test modules
python3 -m unittest tests.test_business_insight_worksheet -v
python3 -m unittest tests.test_yearly_comparison_worksheet -v

# Quick test run (comprehensive test suite)
python3 tests/run_comprehensive_tests.py

# Run modular tests
python3 tests/run_modular_tests.py

# Test with test database
export DB_TEST=true
python3 -m unittest tests.test_database_operations -v
```

### Report Generation

```bash
# Generate comprehensive database reports
python3 scripts/generate_database_report.py --date YYYY-MM-DD
python3 scripts/generate_gross_margin_report.py --date YYYY-MM-DD
python3 scripts/generate_monthly_material_report.py --date YYYY-MM-DD
python3 scripts/generate_monthly_gross_margin_report.py --date YYYY-MM-DD
python3 scripts/generate_monthly_beverage_report.py --date YYYY-MM-DD

# Generate Weekly YoY MTD report with challenge tracking
python3 scripts/generate_weekly_yoy_report.py --target-date YYYY-MM-DD

# Generate inventory and material division reports
python3 scripts/generate_inventory_count.py
python3 scripts/generate_materials_use_with_division.py
```

### Dish Material Extraction

```bash
# Extract all historical dish material data
python3 scripts/dish_material/extract_all_historical_data.py

# Individual extraction scripts
python3 scripts/dish_material/extract_dishes_to_database.py
python3 scripts/dish_material/extract_materials_to_database.py
python3 scripts/dish_material/extract_dish_material_mapping.py
python3 scripts/dish_material/extract_combo_sales_to_database.py
python3 scripts/dish_material/extract_inventory_to_database.py

# Run all extractions
python3 scripts/dish_material/run_all_extractions.py

# Generate gross revenue report
python3 scripts/dish_material/generate_gross_revenue_report.py
```

### Bank Statement Processing

```bash
# Process bank transactions from Excel files
python3 scripts/process_bank_transactions.py

# Bank statement processing scripts (in scripts/bank_statement_processing/)
# These handle RBC, TD, CIBC, BMO bank statements
```

## High-Level Architecture

### Core Modular System (lib/)

The system uses a modular architecture with centralized utilities to prevent code duplication:

- **`lib/base_classes.py`**: Base classes for worksheet generators, extractors, and report generators with common styling and formatting logic
- **`lib/excel_utils.py`**: Centralized Excel processing with critical `dtype={'物料': str}` fix for material number precision
- **`lib/config.py`**: All store mappings, time segments, material types, and constants centralized
- **`lib/database_utils.py`**: High-level database operations with batch upsert and conflict handling
- **`lib/monthly_automation_base.py`**: Base class for monthly automation workflows
- **`lib/extraction_modules.py`**: Modular extraction components for reusable data processing

### Worksheet Generator Pattern

All worksheet generators inherit from `BaseWorksheetGenerator` for consistent styling:

- Business Insight, Yearly Comparison, Time Segment Analysis
- Material Usage Summary, Detailed Material Spending
- Gross Margin Analysis, Beverage Variance Reports
- Store Tracking (Daily/Weekly), Hi Bowl Integration

### Data Processing Pipeline

1. **Web Scraping** (`lib/qbi_scraper.py`): Selenium-based automation for QBI dashboard
2. **Excel Extraction**: Modular extraction scripts with proper dtype handling
3. **Database Storage**: PostgreSQL with normalized schema and price history tracking
4. **Report Generation**: Professional Excel reports with multiple worksheets
5. **Automation Workflows**: Complete end-to-end processing chains

## Critical Technical Patterns

### Excel Processing (CRITICAL)

```python
# ALWAYS use this pattern to prevent material number precision loss
from lib.excel_utils import safe_read_excel, get_material_reading_dtype

dtype_spec = get_material_reading_dtype()  # Returns {'物料': str}
df = safe_read_excel(file_path, dtype_spec=dtype_spec)

# Clean dish codes (remove .0 suffix from float conversion)
from lib.excel_utils import clean_dish_code
cleaned_code = clean_dish_code(raw_code)

# Handle fake Excel files (TSV with UTF-16 encoding from SAP)
# safe_read_excel automatically detects and handles these files
```

### Database Operations

```python
from lib.database_utils import DatabaseOperations

db_ops = DatabaseOperations(database_manager)
success_count = db_ops.batch_upsert(
    table='materials',
    data_list=material_records,
    conflict_columns=['material_number'],
    batch_size=1000
)
```

### Worksheet Generation

```python
from lib.base_classes import BaseWorksheetGenerator

class MyWorksheetGenerator(BaseWorksheetGenerator):
    def generate_worksheet(self, workbook, *args, **kwargs):
        ws = workbook.create_sheet("Sheet Name")
        self.set_column_widths(ws, [15, 12, 12])
        # Use inherited methods: apply_header_style(), calculate_percentage_change()
```

## Common Development Tasks

### Adding New Features

Follow this mandatory pattern:

1. **Core Implementation** (lib/) with error handling and type hints
2. **Tests** (tests/) with comprehensive coverage
3. **Update BOTH** automation-menu.py AND automation-gui.py for feature parity
4. **Update README.md** with new functionality
5. **Update requirements.txt** if new dependencies added

### Running Specific Tests

```bash
# Run single test method
python3 -m unittest tests.test_business_insight_worksheet.TestBusinessInsightWorksheet.test_worksheet_creation -v

# Run test class
python3 -m unittest tests.test_business_insight_worksheet.TestBusinessInsightWorksheet -v

# Run with verbose debugging
python3 -m unittest tests.test_validation_against_actual_data -v
```

### Database Management

```bash
# Connect to production database
psql -h localhost -U hongming -d haidilao-paperwork

# Run migrations
psql -h localhost -U hongming -d haidilao-paperwork -f haidilao-database-querys/migration_script.sql

# Important SQL scripts in haidilao-database-querys/
# - reset-db.sql: Complete database reset with schema
# - reset-dish-data.sql: Reset only dish-related tables
# - create_inventory_views.sql: Create inventory tracking views
# - create_material_consumption_view.sql: Material consumption analysis
# - migrate_inventory_to_monthly.sql: Inventory data migration

# Reset database (CAUTION)
python3 scripts/automation-menu.py  # Then select 'r' for reset
```

## Store and Data Configuration

- **7 Canadian Stores**: 加拿大一店 through 加拿大七店 (IDs 1-7)
- **Store 8**: 加拿大八店 (ID 8) - New store opened Oct 2025, excluded from regional YoY
- **Hi Bowl Store**: ID 101 for Hi Bowl data integration
- **Material Types**: 11 primary types with 6 child categories
- **Time Segments**: 16 segments covering 10:00-02:00 (next day)
- **Discount Types**: 8 types including 会员折扣, 生日优惠, 节日优惠

## Challenge Targets Configuration

Challenge targets are centralized in `configs/challenge_targets/` with a modular, scalable architecture.

### Architecture

```python
# configs/challenge_targets/q1_2026_targets.py

# Central configuration - keyed by (year, month) tuple
MONTHLY_TARGETS = {
    (2026, 1): {
        'description': '2026年1月门店目标',
        'target_type': 'absolute',  # vs 'improvement'
        'turnover': {1: 4.47, 2: 3.88, ...},
        'afternoon_tables': {1: 37.6, 2: 22.0, ...},
        'late_night_tables': {1: 42.2, 2: 15.1, ...},
        'profit': {1: 6.77, 2: 3.82, ...},      # 万加币
        'takeout': {1: 9.95, 2: 5.64, ...},     # 万加币
    },
    # Add new months as needed: (2026, 2): {...}
}
```

### Adding New Monthly Targets

1. Add entry to `MONTHLY_TARGETS` with key `(year, month)`
2. Include all target types (turnover, afternoon_tables, late_night_tables, profit, takeout)
3. No code changes needed - helper functions automatically use it

### Helper Functions

```python
from configs.challenge_targets import (
    get_monthly_config,           # Get config for any date
    get_store_turnover_target,    # Turnover target
    get_absolute_time_segment_target,  # Time segment target
    get_profit_target,            # Profit target (万加币)
    get_takeout_target,           # Takeout target (万加币)
    is_using_absolute_targets,    # Check if absolute or improvement-based
)
```

### Target Types

- **Absolute targets**: Fixed values for the month (e.g., January 2026)
- **Improvement targets**: Delta over previous year (fallback when no monthly config)

### MTD Normalization Pattern

For fair year-over-year comparisons, use normalized calculations:

```python
# Helper methods in WeeklyYoYComparisonWorksheetGenerator:
_normalize_to_mtd(full_month_total, full_month_days, current_days)
# Formula: full_month_total / full_month_days * current_days

_prorate_monthly_target(monthly_target, target_year, target_month, current_days)
# Formula: monthly_target / days_in_month * current_days
```

### Database Queries for MTD Data

```python
# lib/database_queries.py - ReportDataProvider class
get_takeout_mtd_data(target_date) # Takeout from daily_takeout_revenue

# Returns dict with:
# - current_mtd_total, current_days
# - prev_year_mtd_total, prev_year_mtd_days
# - prev_year_month_total, prev_year_days
# - prev_year_month_days (for normalization)
```

## Common Debugging Patterns

### Material Number Precision Issues (CRITICAL)

**Problem**: Different material numbers (e.g., 1500680 and 1500681) appear identical after reading Excel.

```python
# WRONG - causes precision loss (float64 conversion)
df = pd.read_excel(file_path)  # 1500680 and 1500681 both become 1500680.0

# CORRECT - preserves material numbers as strings
df = pd.read_excel(file_path, dtype={'物料': str})

# OR use centralized utility
from lib.excel_utils import get_material_reading_dtype
dtype_spec = get_material_reading_dtype()
df = pd.read_excel(file_path, dtype=dtype_spec)
```

### Target Date Parameter

Ensure `--target-date` is passed through automation workflows:

```python
# In automation scripts
cmd = f"python3 script.py --target-date {target_date}"  # Not CURRENT_DATE
```

### Representative Product Selection

When multiple products share a material number:

1. Group by material description
2. Calculate total contribution (price × quantity)
3. Select product with highest contribution
4. Use weighted average price

### Unicode Column Names

Handle Chinese characters properly in column names:

```python
# Use escape sequences for reliability when needed
column_name = '\u7269\u6599'  # 物料

# But modern Python handles UTF-8 directly
df['物料']  # Works fine in most cases
```

## Performance Targets

- Core operations: < 1 second
- Full test suite: < 5 seconds
- Report generation: < 30 seconds
- Database queries: < 10 seconds

## Environment Configuration

### Database Connection

```bash
# Production
Host: localhost
Database: haidilao-paperwork
User: hongming
Password: [environment variable]

# Test Environment
Use DatabaseConfig(is_test=True)
```

### Web Scraping

```bash
# QBI credentials (environment variables)
export QBI_USERNAME="your_username"
export QBI_PASSWORD="your_password"
```

## Common Issues and Solutions

### Fake Excel Files (SAP Exports)
Some files with .xls extension are actually TSV files with UTF-16 encoding. The `safe_read_excel` function automatically detects and handles these.

### Date Handling
- Always use `--target-date` parameter, avoid CURRENT_DATE
- Target date should flow through entire automation pipeline
- Use proper date formatting: YYYY-MM-DD

### Store Name Mapping
Use constants from `lib/config.py` for consistent store ID mapping:
- 加拿大一店 through 加拿大七店: IDs 1-7
- Hi Bowl: ID 101

### Price History Management
When inserting new prices:
1. Deactivate existing prices for same entity
2. Insert new price with is_active=True
3. Maintain historical records for reporting

## Development Standards (from .cursorrules)

### Mandatory Update Requirements

When adding ANY new feature, you MUST update in this order:

1. **Core Implementation** (lib/) with error handling and type hints
2. **Tests** (tests/) with comprehensive coverage
3. **Update BOTH** automation-menu.py AND automation-gui.py for feature parity
4. **Update README.md** with new functionality
5. **Update requirements.txt** if new dependencies added

### Code Quality Requirements

- **Test Coverage**: 100% test success rate required before commits
- **Type Hints**: Required for all function parameters and returns
- **Error Handling**: Graceful degradation with specific exception types
- **Documentation**: Docstrings for all classes and public methods
- **Chinese Support**: Proper Unicode handling throughout the system

### Database Best Practices

- **Price History**: Deactivate old prices when inserting new ones
- **Schema Evolution**: Use migration scripts, never drop tables directly
- **Transaction Safety**: Always use rollback on errors
- **Connection Management**: Use context managers and proper cleanup
- **Batch Operations**: Use `DatabaseOperations.batch_upsert()` for bulk inserts
- **Conflict Handling**: Specify conflict_columns for upsert operations
