# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-grade automation system for processing Haidilao restaurant operational data from Excel files and generating comprehensive business reports. The system handles daily operational data, time segment analysis, material usage tracking, and generates professional Excel reports for business analysis.

## Key Commands

### Running the Application

```bash
# GUI Interface (recommended for interactive use)
python3 scripts/automation-gui.py

# CLI Menu (recommended for automation)
python3 scripts/automation-menu.py

# Complete automation for a specific date
python3 scripts/complete_automation.py --target-date YYYY-MM-DD

# QBI web scraping
python3 scripts/qbi_scraper_cli.py --target-date YYYY-MM-DD
```

### Testing

```bash
# Run all tests
python3 -m unittest discover tests -v

# Run test suite with summary
python3 tests/run_tests.py
```

### Data Processing

```bash
# Process Excel data
python3 scripts/extract-all.py data.xlsx

# Generate database report
python3 scripts/generate_database_report.py --date 2025-06-10

# Extract specific data types
python3 scripts/extract-dishes.py
python3 scripts/extract-materials.py
python3 scripts/extract_dish_price_history.py
```

## Architecture

### Core Structure

```
lib/                        # Core business logic modules
├── data_extractors/        # Excel data extraction
├── database/               # Database operations
├── report_generators/      # Report generation logic
└── validators/             # Data validation

scripts/                    # Entry points and automation
tests/                      # Comprehensive test suite (93 tests)
utils/                      # Database utilities
haidilao-database-querys/   # SQL schema and migrations
```

### Key Modules

- **BusinessInsightReportGenerator**: Generates business performance insights
- **YearlyComparisonReportGenerator**: Year-over-year comparisons
- **TimeSegmentReportGenerator**: Analyzes performance by time of day
- **MaterialUsageReportGenerator**: Tracks material consumption
- **DatabaseService**: Handles all database operations
- **DataExtractor**: Processes Excel input files

### Data Flow

1. Excel files are placed in `Input/` directory (daily/monthly reports)
2. Data extractors parse and validate the Excel data
3. Validated data is inserted/updated in PostgreSQL database
4. Report generators query database and create comprehensive Excel reports
5. Reports are saved to `output/` directory

## Development Standards

### Mandatory Update Pattern

When adding features, update in this order:

1. Core implementation (lib/)
2. Tests (tests/)
3. Automation menu & GUI
4. README.md
5. requirements.txt (if needed)

### Code Quality

- **Python 3.8+** with type hints and docstrings required
- **100% test coverage** for all new features
- Use `dtype={'物料': str}` when reading material numbers from Excel
- Handle Chinese characters properly throughout the system
- Maintain feature parity between GUI and CLI interfaces

### Database Configuration

- **Production**: PostgreSQL on localhost
  - User: hongming
  - Password: 8894
  - Database: haidilao-paperwork
- **Test**: Use `DatabaseConfig(is_test=True)`
- Schema includes comprehensive tables for districts, stores, daily reports, time segments, dishes, materials

## Technical Considerations

### Excel Processing

- Remove `.0` suffix from dish codes when reading from Excel
- Always use `dtype={'物料': str}` to prevent material number precision loss
- Handle YYYYMMDD date format conversion
- Support Chinese column headers and data

### Error Handling

- Implement graceful degradation for missing data
- Use transactions with proper rollback on errors
- Provide user-friendly error messages with actionable suggestions
- Log detailed information for debugging

### Performance

- Core operations tested to complete in <1 second
- Batch database operations for efficiency
- Use appropriate indexes on frequently queried columns

## Report Types

The system generates 6+ worksheet types in Excel:

- **对比上月表**: Monthly comparison
- **同比数据**: Year-over-year comparison
- **对比上年表**: Year-over-year daily comparison
- **分时段-上报**: Time segment analysis
- **营业透视**: Business insight
- **门店日-加拿大**: Daily store tracking
- **物料使用汇总**: Material usage summary

## Store Management

System handles 7 Canadian Haidilao stores with special handling for Store 6 closure scenarios. All stores are tracked with consistent naming conventions and district associations.
