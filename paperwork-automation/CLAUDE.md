# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-grade automation system for processing Haidilao restaurant operational data from Excel files and generating comprehensive business reports. The system handles daily operational data, time segment analysis, material usage tracking, and generates professional Excel reports for business analysis.

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
```

### Report Generation

```bash
# Generate comprehensive database reports
python3 scripts/generate_database_report.py --date YYYY-MM-DD
python3 scripts/generate_gross_margin_report.py --date YYYY-MM-DD
python3 scripts/generate_monthly_material_report.py --date YYYY-MM-DD
python3 scripts/generate_monthly_gross_margin_report.py --date YYYY-MM-DD
python3 scripts/generate_monthly_beverage_report.py --date YYYY-MM-DD
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

dtype_spec = get_material_reading_dtype()  # {'物料': str}
df = safe_read_excel(file_path, dtype_spec=dtype_spec)

# Clean dish codes (remove .0 suffix from float conversion)
from lib.excel_utils import clean_dish_code
cleaned_code = clean_dish_code(raw_code)
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

# Run with test database
export DB_TEST=true
python3 -m unittest tests.test_database_operations -v
```

### Database Management

```bash
# Connect to production database
psql -h localhost -U hongming -d haidilao-paperwork

# Run migrations
psql -h localhost -U hongming -d haidilao-paperwork -f haidilao-database-querys/migration_script.sql

# Reset database (CAUTION)
python3 scripts/automation-menu.py  # Then select 'r' for reset
```

## Store and Data Configuration

- **7 Canadian Stores**: 加拿大一店 through 加拿大七店 (IDs 1-7)
- **Hi Bowl Store**: ID 101 for Hi Bowl data integration
- **Material Types**: 11 primary types with 6 child categories
- **Time Segments**: 16 segments covering 10:00-02:00 (next day)
- **Discount Types**: 8 types including 会员折扣, 生日优惠, 节日优惠

## Common Debugging Patterns

### Material Number Precision Issues

If different material numbers appear identical:
```python
# WRONG - causes precision loss
df = pd.read_excel(file_path)  # 1500680 and 1500681 both become 1500680.0

# CORRECT - preserves material numbers
df = pd.read_excel(file_path, dtype={'物料': str})
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

Use escape sequences for reliability:
```python
# Instead of Chinese characters directly
column_name = '\u7269\u6599'  # 物料
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

## Important Reminders

- **Feature Parity**: Maintain identical functionality between GUI and CLI
- **Test Coverage**: 100% test success rate required before commits
- **Error Messages**: Provide user-friendly messages with recovery suggestions
- **Chinese Support**: Proper Unicode handling throughout the system
- **Price History**: Deactivate old prices when inserting new ones
- **Schema Evolution**: Use migration scripts, never drop tables directly