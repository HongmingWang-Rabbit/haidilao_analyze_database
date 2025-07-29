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
python3 scripts/generate_database_report.py --date 2025-06-10
python3 scripts/generate_gross_margin_report.py --date 2025-06-10
python3 scripts/generate_monthly_material_report.py --date 2025-06-01
```

## Architecture

### Core Structure

```
lib/                        # Core business logic modules
├── business_insight_worksheet.py
├── yearly_comparison_worksheet.py
├── yearly_comparison_daily_worksheet.py
├── time_segment_worksheet.py
├── material_usage_summary_worksheet.py
├── detailed_material_spending_worksheet.py
├── gross_margin_worksheet.py
├── beverage_variance_worksheet.py
├── monthly_dishes_worksheet.py
├── store_gross_profit_worksheet.py
├── daily_store_tracking_worksheet.py
├── data_extraction.py
├── database_queries.py
├── extraction_modules.py
├── monthly_automation_base.py
└── qbi_scraper.py

scripts/                    # Entry points and automation tools
├── automation-gui.py       # Modern GUI interface
├── automation-menu.py      # Interactive CLI menu  
├── complete_automation.py  # Daily workflow automation
├── complete_monthly_automation_new.py # Monthly automation
├── qbi_scraper_cli.py      # Web scraping for QBI system
├── process_bank_transactions.py # Bank data processing
├── extract-all.py          # Data extraction orchestrator
├── extract-dishes.py       # Dish extraction with sizes
├── extract-materials.py    # Material extraction
├── extract-dish-materials.py # Dish-material relationships
├── extract_dish_price_history.py # Price history extraction
├── extract_material_detail_prices_by_store_batch.py # Material price extraction
├── generate_database_report.py # Report generation
├── generate_gross_margin_report.py # Gross margin reports
└── generate_monthly_material_report.py # Monthly material reports

tests/                      # Comprehensive test suite (25+ test files)
utils/                      # Database utilities and helpers
haidilao-database-querys/   # SQL schema and migrations
```

### Key Architecture Patterns

- **Worksheet Generators**: Each report type has dedicated generator class with standardized interface
- **Database Layer**: Centralized database operations through `utils/database.py` and `lib/database_queries.py`
- **Data Flow**: Excel → Extraction → Validation → Database → Report Generation
- **Automation Workflows**: Complete end-to-end processing chains for daily/monthly operations
- **Web Scraping Integration**: Selenium-based QBI system integration with authentication
- **Multi-Interface Support**: Both GUI (tkinter) and CLI interfaces for same functionality

### Data Flow

1. **Input Sources**: Excel files, QBI web scraping, bank transaction files
2. **Data Extraction**: Python scripts parse and validate data with proper encoding
3. **Database Storage**: PostgreSQL with comprehensive schema for stores, dishes, materials, transactions
4. **Report Generation**: Multiple worksheet types generated as professional Excel files
5. **Output**: Reports saved to `output/` directory with timestamps and organized structure

## Development Standards

### Mandatory Update Pattern

When adding features, update in this order:

1. Core implementation (lib/)
2. Tests (tests/)
3. Automation menu & GUI
4. README.md
5. requirements.txt (if needed)

### Code Quality Standards

- **Python 3.8+** with type hints and docstrings required
- **Comprehensive test coverage** for all new features 
- **Critical Excel Processing**: Use `dtype={'物料': str}` when reading material numbers to prevent float64 precision loss
- **Chinese Character Support**: Proper Unicode handling throughout system
- **Feature Parity**: Maintain identical functionality between GUI and CLI interfaces
- **Error Handling**: Graceful degradation with specific exception types and user-friendly messages

### Database Configuration

- **Production**: PostgreSQL on localhost (User: hongming, DB: haidilao-paperwork)
- **Test Environment**: Use `DatabaseConfig(is_test=True)` for testing
- **Schema**: Comprehensive tables for stores, dishes, materials, daily reports, time segments, transactions
- **Migrations**: Use SQL files in `haidilao-database-querys/` for schema changes

## Technical Considerations

### Critical Excel Processing Patterns

- **Material Numbers**: ALWAYS use `dtype={'物料': str}` to prevent float64 conversion precision loss (critical bug discovered in material price extraction)
- **Dish Codes**: Remove `.0` suffix from pandas float conversions when reading dish codes
- **Date Formats**: Handle YYYYMMDD conversion properly
- **Chinese Text**: Use Unicode escape sequences for column names in code for reliability
- **Target Dates**: Ensure `--target-date` parameter is passed through automation workflows to prevent CURRENT_DATE usage
- **Representative Product Selection**: When multiple products share same material number, select product with highest total contribution (price × quantity) per material
- **Unit Conversion Rates**: Extract from "物料单位" field during monthly automation, defaults to 1.0 if blank

### Web Scraping & Automation

- **QBI Integration**: Selenium-based with Chrome WebDriver auto-management
- **Authentication**: Environment variables for credentials with fallback prompts
- **Browser Control**: Headless mode for production, GUI mode for debugging
- **File Organization**: Automatic timestamping and structured output organization

### Database & Performance

- **Transactions**: Use proper rollback on errors with specific exception handling
- **Batch Operations**: Process large datasets efficiently
- **Connection Management**: Proper cleanup and connection pooling
- **Schema Evolution**: Use `alter_dish_structure.sql` for safe migrations, dishes now include `size` column for uniqueness
- **Material Price History**: Changed from `district_id` to `store_id` for store-specific pricing
- **Performance Target**: Core operations <1 second, full test suite <5 seconds

## Report Types Generated

The system generates comprehensive Excel reports with multiple worksheets:

- **对比上月表**: Monthly comparison with growth rates
- **同比数据**: Year-over-year comparison 
- **对比上年表**: Year-over-year daily comparison
- **分时段-上报**: Time segment analysis
- **营业透视**: Business insight with rankings
- **门店日-加拿大**: Daily store tracking
- **物料使用汇总**: Material usage summary by store and type
- **Gross Margin Reports**: Detailed profitability analysis

## Store Management & Special Considerations

- **7 Canadian Stores**: 加拿大一店 through 加拿大七店 with consistent ID mapping
- **Store 6 Handling**: Special logic for closure scenarios and data continuity
- **Bank Integration**: Automated transaction processing and reconciliation
- **Multi-Currency**: CAD/USD exchange rate handling with monthly static data (normalized in month_static_data table)
- **Material Classification**: 11 material types with 6 child categories for detailed reporting
- **Unit Conversion System**: dish_material.unit_conversion_rate column for accurate material calculations
- **Discount Analysis**: Multiple discount types tracking (会员折扣, 生日优惠, 节日优惠, etc.)

## Development Workflow (From .cursorrules)

When adding features, ALWAYS update in this exact order:

1. **Core Implementation** (lib/ modules) - Add with proper error handling and type hints
2. **Tests** (tests/ directory) - Comprehensive coverage including edge cases (maintain 100% success rate)
3. **Automation Menu & GUI** - Update both CLI and GUI interfaces for feature parity  
4. **README.md** - Document new functionality and update examples
5. **requirements.txt** - Add any new dependencies

### Mandatory Feature Addition Pattern
- ALL new features MUST be tested with comprehensive test coverage
- BOTH automation-menu.py AND automation-gui.py must be updated for consistency
- Database migrations require SQL files in `haidilao-database-querys/`
- Excel processing must handle Chinese characters and proper data types

## Common Debugging Patterns

From the .cursorrules, key troubleshooting approaches:

- **Material Number Issues**: Check for float64 conversion using `dtype={'物料': str}` - CRITICAL bug that causes different material numbers to appear identical
- **Dish Code Problems**: Look for `.0` suffix removal from pandas conversions
- **Target Date Issues**: Verify `--target-date` parameter passing through automation workflows to prevent CURRENT_DATE usage
- **Step-by-step Diagnostics**: Create diagnostic scripts to isolate complex extraction issues
- **Unicode Handling**: Use escape sequences for Chinese column names in code
- **Representative Product Selection**: When material prices seem wrong, verify highest total contribution logic
- **Schema Migration**: Use safe migration scripts for database structure changes
- **Unit Conversion**: Check unit_conversion_rate extraction from "物料单位" field
- **Price History**: Verify activation logic (deactivate old prices when adding new ones)

## Code Modularization & Redundancy Analysis

### Critical Code Duplication Identified

After comprehensive codebase analysis, significant redundancy was found across 79+ Python files:

#### **High-Priority Duplication (Immediate Action Required)**

1. **Excel Processing Patterns** (20+ files affected)
   - Duplicate pandas imports with warnings suppression
   - Repeated `dtype={'物料': str}` specifications
   - Similar data cleaning functions (`clean_dish_code`, `clean_material_number`)
   - Common Excel reading error handling

2. **Worksheet Generator Patterns** (13+ files affected)
   - Identical class initialization patterns
   - Duplicate openpyxl styling imports and setup
   - Repeated column width and formatting logic
   - Common percentage calculation and formatting functions

3. **Database Connection Patterns** (50+ files affected)
   - Duplicate database import attempts with fallbacks
   - Repeated connection management code
   - Common SQL generation patterns
   - Identical error handling for database operations

4. **Project Setup Patterns** (All scripts)
   - Duplicate path manipulation and sys.path.append logic
   - Repeated environment variable loading
   - Common command-line argument parsing patterns

### **Recommended Modularization Strategy**

#### **Phase 1: Critical Utilities (High Impact)**

**Create `lib/base_classes.py`:**
```python
# Base classes for common patterns
class BaseWorksheetGenerator:
    def __init__(self, store_names, target_date):
        self.store_names = store_names
        self.target_date = target_date
        self.setup_common_styles()
    
    def setup_common_styles(self):
        # Common openpyxl styles
        pass
    
    def set_column_widths(self, ws, widths):
        # Common column width setting
        pass

class BaseExtractor:
    def __init__(self, database_manager=None):
        self.db_manager = database_manager
        self.setup_logging()
    
    def setup_project_path(self):
        # Common project path setup
        pass
```

**Create `lib/excel_utils.py`:**
```python
# Centralized Excel processing utilities
MATERIAL_DTYPE_SPEC = {'物料': str}  # Critical fix for material number precision

def safe_read_excel(file_path, sheet_name=None, dtype_spec=None):
    """Standardized Excel reading with proper dtype handling"""
    pass

def clean_dish_code(code):
    """Standardized dish code cleaning (remove .0 suffix)"""
    pass

def clean_material_number(material_number):
    """Standardized material number cleaning"""
    pass

def suppress_excel_warnings():
    """Standard warning suppression for openpyxl"""
    pass
```

**Create `lib/config.py`:**
```python
# Centralized configuration and constants
STORE_NAME_MAPPING = {
    '加拿大一店': 1,
    '加拿大二店': 2,
    # ... complete mapping
}

DATABASE_TIMEOUT = 30
EXCEL_CHUNK_SIZE = 1000
DEFAULT_DATE_FORMAT = '%Y-%m-%d'
```

#### **Phase 2: Database Abstraction (Medium Impact)**

**Enhance `utils/database.py`:**
```python
class DatabaseOperations:
    """High-level database operations for common patterns"""
    
    def safe_insert_with_conflict_handling(self, table, data, conflict_columns):
        """Standardized insert with conflict resolution"""
        pass
    
    def batch_upsert(self, table, data_list, batch_size=1000):
        """Optimized batch operations"""
        pass
    
    def get_or_create_lookup(self, table, lookup_data):
        """Common lookup pattern with creation"""
        pass
```

#### **Phase 3: Worksheet Generation Framework (Medium Impact)**

**Standardize worksheet generators to inherit from base:**
- `BusinessInsightWorksheetGenerator(BaseWorksheetGenerator)`
- `YearlyComparisonWorksheetGenerator(BaseWorksheetGenerator)`
- All other worksheet generators follow same pattern

#### **Phase 4: Script Templates (Lower Impact)**

**Create `lib/script_template.py`:**
```python
class BaseScript:
    """Template for extraction and processing scripts"""
    
    def setup_environment(self):
        """Standard environment setup"""
        pass
    
    def parse_arguments(self):
        """Common argument parsing patterns"""
        pass
    
    def main(self):
        """Template main method"""
        pass
```

### **Implementation Benefits**

#### **Quantified Code Reduction:**
- **Phase 1**: ~2,000 lines eliminated (Excel processing consolidation)
- **Phase 2**: ~1,500 lines eliminated (Database pattern consolidation)  
- **Phase 3**: ~1,000 lines eliminated (Worksheet generator consolidation)
- **Phase 4**: ~500 lines eliminated (Script template adoption)
- **Total**: ~5,000 lines of duplicate code eliminated (15-20% of codebase)

#### **Maintenance Benefits:**
- **Single Point of Change**: Update Excel processing logic once instead of 20+ files
- **Consistency**: All worksheet generators use identical styling and patterns
- **Bug Fixes**: Fix critical dtype={'物料': str} issue in one place
- **Testing**: Test common utilities once instead of in every file
- **Documentation**: Centralized documentation for common patterns

#### **Risk Mitigation:**
- **Phased Approach**: Implement high-impact changes first
- **Backward Compatibility**: Keep existing interfaces during transition
- **Comprehensive Testing**: Test utilities independently before integration
- **Gradual Migration**: Update files incrementally to use new utilities

### **Implementation Status: COMPLETED ✅**

**Phase 1 Implementation Results:**

| Component | Status | Files Created | Impact |
|-----------|--------|---------------|---------|
| **Excel Utils** | ✅ COMPLETED | `lib/excel_utils.py` | 20+ files updated |
| **Base Classes** | ✅ COMPLETED | `lib/base_classes.py` | 13+ generators updated |
| **Config Constants** | ✅ COMPLETED | `lib/config.py` | All files can now use |
| **Database Utils** | ✅ COMPLETED | `lib/database_utils.py` | 50+ files can benefit |

**New Utility Modules Created:**

1. **`lib/excel_utils.py`** (585 lines)
   - Centralized Excel processing with critical `dtype={'物料': str}` fix
   - Functions: `safe_read_excel()`, `clean_dish_code()`, `clean_material_number()`
   - Standardized column validation and data cleaning
   - Common sheet structure detection

2. **`lib/base_classes.py`** (380 lines)  
   - `BaseWorksheetGenerator` with common styling and formatting
   - `BaseExtractor` with standardized project setup and database operations
   - `BaseReportGenerator` for report generation patterns
   - Common percentage calculations and data formatting

3. **`lib/config.py`** (450 lines)
   - All store mappings, time segments, and constants centralized
   - Database, Excel, and validation configuration
   - Material types, discount types, and report structures
   - Performance targets and error handling configuration

4. **`lib/database_utils.py`** (320 lines)
   - `DatabaseOperations` class with batch upsert and conflict handling
   - Common query patterns and data validation methods
   - Standardized connection management and error handling

**Migration Completed:**
- ✅ `BusinessInsightWorksheetGenerator` now inherits from `BaseWorksheetGenerator`
- ✅ `YearlyComparisonWorksheetGenerator` now inherits from `BaseWorksheetGenerator`
- ✅ `extract-materials.py` now uses centralized Excel utilities
- ✅ `extract-dishes.py` now uses centralized Excel utilities
- ✅ All duplicate functions removed and replaced with centralized versions

### **Migration Guide for Remaining Files**

**For Worksheet Generators:**
```python
# OLD Pattern (duplicated across 13+ files):
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class MyWorksheetGenerator:
    def __init__(self, store_names, target_date):
        self.store_names = store_names
        self.target_date = target_date
        # Manual style setup...

# NEW Pattern (use base class):
from lib.base_classes import BaseWorksheetGenerator

class MyWorksheetGenerator(BaseWorksheetGenerator):
    def __init__(self, store_names, target_date):
        super().__init__(store_names, target_date)
        # Common styles already set up!
    
    def generate_worksheet(self, workbook, *args, **kwargs):
        ws = workbook.create_sheet("My Sheet")
        self.set_column_widths(ws, [15, 12, 12])  # Use parent method
        # Use self.apply_header_style(), self.calculate_percentage_change(), etc.
```

**For Extraction Scripts:**
```python
# OLD Pattern (duplicated across 20+ files):
import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def clean_material_number(material_number):
    # Duplicate function...

df = pd.read_excel(file_path, engine='openpyxl')  # Missing critical dtype!

# NEW Pattern (use utilities):
from lib.excel_utils import (
    safe_read_excel, clean_material_number, get_material_reading_dtype,
    suppress_excel_warnings
)

suppress_excel_warnings()
dtype_spec = get_material_reading_dtype()  # Critical dtype={'物料': str} fix
df = safe_read_excel(file_path, dtype_spec=dtype_spec)
cleaned_number = clean_material_number(raw_number)  # Use centralized function
```

**For Database Operations:**
```python
# OLD Pattern (duplicated across 50+ files):
# Manual connection management, duplicate batch insert logic...

# NEW Pattern (use database utilities):
from lib.database_utils import DatabaseOperations

db_ops = DatabaseOperations(database_manager)
success_count = db_ops.batch_upsert(
    table='materials',
    data_list=material_records,
    conflict_columns=['material_number'],
    batch_size=1000
)
```

**For Configuration:**
```python
# OLD Pattern (scattered across files):
STORE_MAPPING = {'加拿大一店': 1, '加拿大二店': 2, ...}  # Duplicated everywhere

# NEW Pattern (use centralized config):
from lib.config import STORE_NAME_MAPPING, TIME_SEGMENTS, EXCEL_FORMATS

store_id = STORE_NAME_MAPPING.get(store_name)
for segment in TIME_SEGMENTS:
    # Process segments...
```

### **Next Phase Recommendations**

**Remaining Files to Migrate (40+ files):**
- All remaining worksheet generators in `lib/`
- All remaining extraction scripts in `scripts/`
- Test files to use new utilities for consistency
- GUI and automation menu (already compatible)

**Expected Additional Benefits:**
- **~3,000 more lines** can be eliminated in remaining migrations
- **Single point of maintenance** for all common operations
- **Consistent error handling** across entire codebase
- **Improved test coverage** through centralized utility testing

## Current System Capabilities (100+ scripts, 25+ test files)

### Data Processing & Extraction
- **Daily & Time Segment Data**: Complete Excel processing with validation
- **Material Management**: Store-specific material price extraction with representative product selection
- **Dish Management**: Dish extraction with size handling and price history
- **Relationship Mapping**: Dish-material relationships with unit conversion rates
- **Web Scraping**: QBI system integration with Selenium automation
- **Bank Processing**: Transaction automation and reconciliation

### Report Generation (Professional Excel Output)
- **Database Reports**: 6-worksheet comprehensive reports with professional formatting
- **Monthly Reports**: Material usage summaries, beverage variance analysis
- **Gross Margin Analysis**: Detailed profitability reports with MoM/YoY comparisons
- **Inventory Reports**: Count generation and material usage tracking

### Quality Assurance
- **100% Test Coverage**: 78+ comprehensive tests across all modules
- **Validation Systems**: File structure, data consistency, store name validation
- **Error Handling**: Graceful degradation with specific exception types
- **Performance Standards**: <1 second core operations, <5 seconds full test suite

### User Interfaces
- **Modern GUI**: Tkinter-based interface with tabbed layout and live console
- **Interactive CLI**: Emoji-enhanced menu system with logical organization
- **Automation Workflows**: Complete end-to-end processing chains

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
