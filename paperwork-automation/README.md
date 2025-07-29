# 🍲 Haidilao Paperwork Automation System

**Production-grade automation system for Haidilao restaurant data processing and comprehensive report generation**

## 🎯 Overview

This system processes Haidilao restaurant Excel data and generates **4 professional database reports** with complete **100% test coverage**. Features an **interactive automation menu**, **comprehensive worksheet generators**, and **bulletproof data validation**.

## ✨ Features

### 🌐 **Web Scraping & Complete Automation**

- **🤖 QBI System Integration**: Automated web scraping from QBI dashboard with Selenium
- **🔐 Secure Authentication**: Login handling with environment variables and credential prompts
- **📅 Smart Date Ranges**: Automatic calculation of target_date ± 1 day for optimal data coverage
- **📊 Complete Workflow**: End-to-end automation from scraping → processing → database → reports
- **🖥️ Browser Control**: Headless mode for automation or GUI mode for debugging
- **📂 Organized Output**: Automatic file organization with timestamps and workflow summaries

### 📊 **Complete Report Generation System**

- **🎯 6 Professional Worksheets**: 对比上月表 (Monthly Comparison), 同比数据 (Yearly Comparison), 对比上年表 (Year-over-Year Comparison), 分时段-上报 (Time Segment), 营业透视 (Business Insight), 门店日-加拿大 (Daily Store Tracking)
- **🏪 Material Usage Summary (NEW)**: Store-by-store material consumption analysis with type classifications and financial tracking
- **📋 Detailed Material Spending (NEW)**: Individual material consumption worksheets for each store with granular breakdowns by material type
- **📈 Advanced Analytics**: Growth rates, MTD comparisons, turnover analysis, target achievement tracking, material variance analysis
- **🎨 Professional Excel Formatting**: Conditional formatting, merged cells, proper styling, Chinese character support
- **🏪 Smart Store Management**: Handles all 7 Canadian stores including Store 6 closure scenarios

### 🧪 **100% Test Coverage & Validation**

- **📋 93 Comprehensive Tests** with **100% success rate** across all modules
- **🎯 Complete Coverage**: Business Insight (9), Yearly Comparison (21), Time Segment (9), Material Usage Summary (16), Detailed Material Spending (15), Data Extraction (18), Validation (5)
- **⚡ Performance Optimized**: < 1 second execution for core test suite
- **🛡️ Bulletproof Error Handling**: Graceful degradation and comprehensive edge case coverage

### 🚀 **Production-Ready Infrastructure**

- **🖥️ Interactive Automation Menu**: Professional CLI interface with emoji-enhanced UX and confirmation prompts
- **🗄️ Database Integration**: PostgreSQL support with test/production environments and optimized queries
- **📁 Multiple Entry Points**: Enhanced TypeScript, Python scripts, NPM integration following `.cursorrules` standards
- **🔍 Advanced Data Validation**: File structure, store names, time segments, date formats, and data consistency validation

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ with pandas, openpyxl, PostgreSQL support
- PostgreSQL database access
- pip package manager
- **Google Chrome browser** (for web scraping functionality)
- **ChromeDriver** (automatically managed by webdriver-manager)

### Installation

```bash
# Install all Python dependencies
pip install -r requirements.txt

# Verify installation with comprehensive test suite
python3 -m unittest tests.test_* -v
```

## 📋 Entry Points

### 🎯 1. Graphical User Interface (Recommended for New Users)

The **modern GUI interface** provides the most user-friendly experience with visual controls and real-time output.

```bash
# Launch the beautiful GUI interface
python3 scripts/automation-gui.py

# Alternative launcher
python3 launch-gui.py
```

**GUI Features:**

- 🎨 **Modern Interface**: Beautiful tabbed interface with Haidilao branding
- 📁 **File Browser**: Easy Excel file selection with drag-and-drop support
- 📊 **Visual Processing**: All 7 processing modes with descriptions
- 📈 **Report Generation**: Date picker and report history viewer
- 🧪 **Integrated Testing**: Visual test execution with real-time output
- 🗄️ **Database Management**: Connection status and database actions
- ⚙️ **Settings Panel**: Environment configuration and system info
- 📋 **Live Console**: Real-time command output with syntax highlighting
- 📂 **Quick Actions**: One-click report generation and testing

### 🎨 GUI Showcase

The automation system now includes a modern tkinter-based GUI alongside the CLI menu. The GUI features:

**🖥️ Interface Design:**

- Clean tabbed interface with 5 main sections
- **Live console panel on the right side** for real-time command output
- Haidilao branding with professional red color scheme (#dc2626)
- Progress indicators and status updates throughout
- Cross-platform file browser integration

**📋 Main Tabs:**

1. **Data Processing** - File browser + 7 processing modes with descriptions
2. **Reports** - Date picker, report generation, and history viewer
3. **Testing** - Visual execution of all 62 comprehensive tests
4. **Database** - Connection monitoring and management tools
5. **Settings** - Environment configuration and system information

**🔧 Live Console Features:**

- **Spacious side panel layout** for better visibility
- Real-time command output with syntax highlighting
- Process control (start/stop/clear)
- Status indicators synchronized with main interface
- Word-wrapped output for long lines
- Console status indicator (🟢 Ready, 🔄 Running, 🔴 Error, 🟡 Stopped)

**🚀 Launch Options:**

```bash
# GUI Interface (recommended for visual users)
python3 scripts/automation-gui.py
# or
python3 launch-gui.py

# CLI Menu (recommended for automation/scripting)
python3 scripts/automation-menu.py
```

### 🎯 2. Interactive Command Line Menu

The **interactive automation menu** provides comprehensive validation and 100% test coverage integration.

```bash
# Launch the interactive automation menu
python3 scripts/automation-menu.py
```

**Menu Features:**

- 📊 Data Processing (4 modes)
- 🗄️ Database Operations (3 modes)
- 📊 Report Generation (4 worksheets)
- 🧪 Testing & Validation (62 tests, 100% coverage)
- ⚙️ Database Management
- 🔧 System Tools

### 🌐 3. Web Scraping & Complete Automation

**NEW: QBI System Integration with complete workflow automation**

```bash
# QBI Web Scraping - Download Excel data from QBI system
python3 scripts/qbi_scraper_cli.py --target-date 2025-06-21

# Complete Automation Workflow - Full end-to-end process
python3 scripts/complete_automation.py --target-date 2025-06-21

# With specific QBI URL parameters
python3 scripts/qbi_scraper_cli.py --target-date 2025-06-21 \
  --product-id "1fcba94f-c81d-4595-80cc-dac5462e0d24" \
  --menu-id "89809ff6-a4fe-4fd7-853d-49315e51b2ec"

# Run with GUI browser (for debugging)
python3 scripts/complete_automation.py --target-date 2025-06-21 --no-headless
```

**Web Scraping Features:**

- 🔐 **Secure Login**: QBI system authentication with credential management
- 📅 **Smart Date Handling**: Automatic target_date ± 1 day range calculation
- 🔍 **Element Detection**: Robust form field and button detection
- 📤 **Export Automation**: Automatic Excel file download and organization
- 🖥️ **Browser Modes**: Headless (production) or GUI (debugging) operation
- 🌐 **URL Parameters**: Support for specific QBI dashboard configurations

**Complete Automation Workflow:**

1. **🌐 Step 1**: Scrape data from QBI system with authentication
2. **🔄 Step 2**: Process scraped data and insert into database
3. **📊 Step 3**: Generate comprehensive Excel reports (4 worksheets)
4. **🧹 Step 4**: Cleanup and organize all output files with timestamps

**Environment Variables:**

```bash
# Set QBI credentials (optional - will prompt if not set)
export QBI_USERNAME="your_qbi_username"
export QBI_PASSWORD="your_qbi_password"
```

### 4. Python Direct Interface

Direct access to the Python scripts with enhanced validation.

```bash
# Process both daily and time segment data
python3 scripts/extract-all.py data.xlsx

# Generate comprehensive database report
python3 scripts/generate_database_report.py --date 2025-06-10

# Launch interactive automation menu
python3 scripts/automation-menu.py
```

## 📁 Expected Excel File Structure

Your Excel file must contain these two sheets:

### Sheet 1: 营业基础表 (Daily Reports)

- **Required columns**: 门店名称, 日期, 节假日, 营业桌数, 营业桌数(考核), 翻台率(考核), 营业收入(不含税), 营业桌数(考核)(外卖), 就餐人数, 优惠总金额(不含税)
- **Expected stores**: 加拿大一店, 加拿大二店, 加拿大三店, 加拿大四店, 加拿大五店, 加拿大六店, 加拿大七店
- **Date format**: YYYYMMDD (e.g., 20250610)
- **Holiday values**: 工作日 or 节假日

### Sheet 2: 分时段基础表 (Time Segments)

- **Required columns**: 门店名称, 日期, 分时段, 节假日, 营业桌数(考核), 翻台率(考核)
- **Time segments**: 08:00-13:59, 14:00-16:59, 17:00-21:59, 22:00-(次)07:59
- **Same store and date format requirements as daily reports**

## 🔍 Validation Features

The system automatically validates:

- ✅ **File Structure**: Excel file existence, required sheets, column presence
- ✅ **Store Names**: All 7 expected stores are present and correctly named
- ✅ **Time Segments**: All 4 time periods are present and correctly formatted
- ✅ **Date Formats**: Proper YYYYMMDD format validation
- ✅ **Holiday Values**: Correct 工作日/节假日 values
- ✅ **Data Ranges**: Reasonable numeric values (no negative tables, extreme turnover rates)
- ✅ **Data Consistency**: Holiday values consistent between sheets

## 🧪 Testing & Validation

### **Comprehensive Test Suite (100% Coverage)**

The system includes **78 comprehensive tests** with **100% success rate** covering all core functionality:

```bash
# Run complete test suite (78 tests)
python3 -m unittest tests.test_business_insight_worksheet tests.test_yearly_comparison_worksheet tests.test_time_segment_worksheet tests.test_material_usage_summary_worksheet tests.test_extract_all tests.test_validation_against_actual_data -v

# Quick core tests
python3 -m unittest tests.test_business_insight_worksheet -q

# Run comprehensive test analysis
python3 tests/run_comprehensive_tests.py
```

### **Via Automation Menu**

```bash
# Launch menu and select testing options
python3 scripts/automation-menu.py
# Then choose: t) Run Comprehensive Tests (62 tests, 100% coverage)
```

### **Test Coverage Breakdown**

- **🎯 Business Insight Worksheet**: 9 tests (initialization, data calculations, formatting)
- **📊 Yearly Comparison Worksheet**: 21 tests (percentage calculations, totals, formatting, edge cases)
- **⏰ Time Segment Worksheet**: 9 tests (data retrieval, calculations, structure)
- **🏪 Material Usage Summary Worksheet**: 16 tests (NEW - store analysis, material type handling, formatting, data validation)
- **📁 Data Extraction & Validation**: 18 tests (file processing, validation, error handling)
- **✅ Integration & Validation**: 5 tests (actual data validation, structure matching)

### **Python-Only Commands**

All testing is now handled through Python's unittest framework:

```bash
# Quick single module test
python3 -m unittest tests.test_business_insight_worksheet -q

# Comprehensive test suite with detailed output
python3 -m unittest discover tests -v
```

### **Performance Standards**

- **⚡ Core Test Execution**: < 1 second
- **📊 Complete Test Suite**: < 5 seconds
- **🎯 Success Rate**: 100% (78/78 tests passing)
- **🔄 Test Categories**: Initialization, Success paths, Error handling, Edge cases, Integration, Data validation

## 📊 Report Generation

### **Database Report Generation (4 Worksheets)**

Generate comprehensive Excel reports with all 4 professional worksheets:

```bash
# Via automation menu (recommended)
python3 scripts/automation-menu.py
# Select: r) Generate Database Report (4 worksheets)

# Direct command
python3 scripts/generate_database_report.py --date 2025-06-10
```

**Generated Report Structure:**

- **📈 对比上月表**: Monthly comparison with growth rates and target completion
- **📊 同比数据**: Year-over-year comparison with percentage changes
- **📅 对比上年表**: Year-over-year daily comparison with same structure as monthly comparison
- **⏰ 分时段-上报**: Time segment analysis with totals and differences
- **🎯 营业透视**: Business insight with store performance rankings
- **🏪 门店日-加拿大**: Daily store performance tracking with normalized scoring

### **Monthly Material Usage Report (NEW)**

Generate comprehensive monthly reports with **material usage summary by store and type**:

```bash
# Via automation menu (recommended)
python3 scripts/automation-menu.py
# Select: 📊 Single Report Generation → 8) Monthly Report with Material Usage Summary

# Direct command
python3 scripts/generate_monthly_report.py --date 2025-06-01
```

**Generated Monthly Report Structure:**

- **📊 月度统计概览**: Monthly statistics overview with dish sales and material usage summaries
- **📈 物料差异分析**: Material variance analysis comparing expected vs actual usage
- **🏪 物料使用汇总**: **NEW - Material usage summary by store and material type**
  - Organized by store with material type breakdowns
  - Usage amounts in CAD with proper formatting
  - Store totals and grand total across all stores
  - Material categories: 成本-锅底类, 成本-荤菜类, 成本-素菜类, etc.

**Material Usage Summary Features:**

- **🏪 Store-by-Store Analysis**: Each store's material consumption broken down by type
- **💰 Financial Tracking**: Usage amounts calculated using material prices and quantities
- **📊 Professional Formatting**: Clean tables with proper borders, colors, and Chinese text support
- **📈 Comprehensive Totals**: Store subtotals and system-wide grand totals
- **🎯 Material Classification**: Leverages the new material type system (11 material types, 6 child types)

**Output:** `output/database_report_YYYY_MM_DD.xlsx`

### **Gross Margin Reports (毛利报表)**

Generate comprehensive gross margin analysis reports:

#### Daily Gross Margin Report
```bash
# Via automation menu (recommended)
python3 scripts/automation-menu.py
# Select: 📊 Single Report Generation → g) Gross Margin Report (毛利报表)

# Direct command
python3 scripts/generate_gross_margin_report.py --target-date 2025-06-30
```

**Generated Sheets:**
- **菜品价格变动及菜品损耗表**: Detailed revenue data with dish price changes
- **原材料成本变动表**: Material cost analysis
- **打折优惠表**: Discount analysis
- **各店毛利率分析**: Store gross profit analysis

**Output:** `output/gross_margin_report_YYYY_MM_DD.xlsx`

### **Complete Monthly Automation (NEW ENHANCED)**

The monthly automation workflow now includes comprehensive analysis reports:

```bash
# Via automation menu (recommended)
python3 scripts/automation-menu.py
# Select: 3) 📊 Complete Monthly Automation (NEW WORKFLOW)

# Direct command
python3 scripts/complete_monthly_automation_new.py --date 2025-06-30
```

**Workflow Steps:**
1. Extract from monthly dish sales → dish types, dishes, price history, sales data
2. Extract from material details → materials, material price history
3. Extract from inventory checking results → inventory counts by store
4. Extract from calculated dish-material usage → dish-material relationships
5. **Generate comprehensive reports:**
   - Material variance analysis report
   - Beverage variance analysis report
   - **Monthly gross margin analysis report (毛利相关分析指标)**

#### Monthly Gross Margin Analysis Report
As part of the monthly automation, a comprehensive gross margin analysis report is generated with:

- **菜品价格变动及菜品损耗表**: Dish price changes and loss analysis for the month
- **原材料成本变动表**: Material cost changes with MoM/YoY comparisons
- **打折优惠表**: Detailed discount analysis by type and store (会员折扣, 生日优惠, 节日优惠, etc.)
- **各店毛利率分析**: Store-by-store gross margin analysis
- **月度毛利汇总**: Monthly summary with revenue, costs, and margins
- **同比环比分析**: Year-over-year and month-over-month comprehensive analysis

**Key Features:**
- **📊 Matches Manual Report Structure**: Replicates the format of 附件3-毛利相关分析指标-YYMM.xlsx
- **📈 Advanced Analytics**: MoM/YoY comparisons, trend analysis, cost breakdowns
- **💰 Financial Insights**: Gross margin calculations, cost rates, revenue impacts
- **🎯 Multi-dimensional Analysis**: By store, material type, time period
- **📁 Professional Output**: Clean Excel format with proper formatting and Chinese support

**Output:** `output/monthly_gross_margin/毛利相关分析指标-YYYYMM.xlsx`

## 📊 Usage Examples

### Example 1: Complete Workflow

```bash
# 1. Launch automation menu
python3 scripts/automation-menu.py

# 2. Process Excel data (menu option 2 or 5)
# 3. Generate reports (menu option r)
# 4. Run tests (menu option t)
```

### Example 2: Direct Processing

### Example 2: Custom Output Files

```bash
npm run extract-enhanced process data.xlsx \
  --daily-output daily_reports_20250610.sql \
  --time-output time_segments_20250610.sql
```

### Example 3: Debug Mode

```bash
npm run extract-enhanced process data.xlsx --debug
```

### Example 4: Skip Validation (for trusted files)

```bash
npm run extract-enhanced process data.xlsx --skip-validation
```

## 🛠️ Development

### **Code Standards & Best Practices**

This project follows comprehensive coding standards defined in **`.cursorrules`**:

- **📋 Mandatory Update Requirements**: Every feature addition must update tests, menu, and README
- **🧪 100% Test Coverage**: All new features require comprehensive test coverage
- **🎯 Type Safety**: Type hints and docstrings for all functions
- **🔧 Error Handling**: Graceful error handling with specific exception types
- **📊 Professional Formatting**: Consistent Excel styling and Chinese character support

### **Project Structure**

```
paperwork-automation/
├── scripts/                    # Entry points and CLI tools
│   ├── automation-menu.py     # Interactive main menu (🔴 MUST UPDATE)
│   ├── extract-all.py         # Data extraction orchestrator
│   └── generate_database_report.py # Report generation
├── lib/                       # Core business logic
│   ├── comparison_worksheet.py
│   ├── yearly_comparison_worksheet.py
│   ├── time_segment_worksheet.py
│   ├── business_insight_worksheet.py
│   ├── data_extraction.py
│   └── database_queries.py
├── tests/                     # Comprehensive test suite (🔴 MUST UPDATE)
│   ├── test_business_insight_worksheet.py (9 tests)
│   ├── test_yearly_comparison_worksheet.py (21 tests)
│   ├── test_time_segment_worksheet.py (9 tests)
│   ├── test_extract_all.py (18 tests)
│   ├── test_validation_against_actual_data.py (5 tests)
│   └── run_comprehensive_tests.py
├── utils/                     # Shared utilities
│   └── database.py
├── output/                    # Generated reports
├── .cursorrules              # 🔴 Development standards (CRITICAL)
├── README.md                 # 🔴 Main documentation (MUST UPDATE)
└── package.json              # NPM scripts
```

### **Development Workflow (Following .cursorrules)**

When adding new features, follow this **mandatory sequence**:

1. **🔧 Core Implementation** (lib/ modules)

   - Implement with proper error handling and type hints
   - Follow existing patterns and Excel formatting standards

2. **🧪 Tests** (tests/ directory)

   - Add comprehensive test coverage (all scenarios)
   - Ensure all tests pass: `python3 -m unittest tests.test_* -v`
   - Update `run_comprehensive_tests.py` if needed

3. **🖥️ Automation Menu** (scripts/automation-menu.py)

   - Add menu option for new feature
   - Update help documentation and status display

4. **📚 Documentation** (README.md)

   - Update feature list and usage examples
   - Update test count and coverage information

5. **📦 Package.json** (if applicable)
   - Add npm scripts for new commands

### **Code Review Checklist**

Before any commit, ensure:

- [ ] All 62 tests pass (100% success rate required)
- [ ] New features have comprehensive test coverage
- [ ] Automation menu updated if needed
- [ ] README.md reflects current capabilities
- [ ] `.cursorrules` standards followed

## 🔧 Configuration

### Environment Variables

- `DEBUG=true` - Enable debug output
- `NODE_ENV=development` - Development mode

### Database Integration

The system generates SQL files by default. For direct database insertion, modify the Python scripts to include database connection logic.

### Discount Analysis Setup

To enable detailed discount analysis in the monthly gross margin report:

```bash
# Setup discount analysis tables and migrate existing data
python3 scripts/setup_discount_analysis.py

# Verify the setup
python3 scripts/verify_discount_analysis.py

# Run migration for existing data
python3 scripts/migrate_discount_data.py
```

The discount analysis feature tracks:
- Multiple discount types (会员折扣, 生日优惠, 节日优惠, etc.)
- Daily and monthly discount summaries
- Discount percentage of revenue
- Year-over-year and month-over-month comparisons

## 📈 Performance

- **Processing speed**: ~3.8 seconds for full test suite
- **File size support**: Tested with 1000+ rows
- **Memory efficient**: Streaming processing for large files
- **Validation speed**: ~2.9 seconds for comprehensive validation

## 🚨 Error Handling

The system provides clear error messages for common issues:

- **❌ Critical Errors**: Stop processing (missing files, wrong structure)
- **⚠️ Warnings**: Continue with caution (missing stores, data anomalies)
- **✅ Success**: Clear confirmation of successful processing

## 📞 Support

### Common Issues

1. **"File not found"**: Check file path and ensure Excel file exists
2. **"Missing required sheets"**: Ensure sheets are named 营业基础表 and 分时段基础表
3. **"Unknown stores"**: Check store names match expected format
4. **"Invalid date format"**: Use YYYYMMDD format (e.g., 20250610)

### Getting Help

```bash
# Show system status and available commands
npm run status

# Show Python script help
npm run help

# Run validation tests
npm run validate
```

## 🎯 Roadmap

- [ ] Direct database integration
- [ ] Web interface for file uploads
- [ ] Automated scheduling
- [ ] Historical data analysis
- [ ] Performance dashboards
- [ ] Multi-language support

## 🔧 Cursor IDE Integration

This project includes comprehensive **`.cursorrules`** for Cursor IDE that enforces:

- **📋 Mandatory Update Requirements**: Automatic reminders to update tests, menu, and README
- **🧪 Test Coverage Standards**: 100% coverage requirements for all new features
- **🎯 Code Quality**: Type hints, docstrings, error handling patterns
- **📊 Excel Formatting**: Professional styling and Chinese character support standards
- **🔄 Development Workflow**: Step-by-step feature addition process

**Benefits for Cursor users:**

- Consistent code quality across all contributions
- Automatic compliance with project standards
- Comprehensive test coverage enforcement
- Professional Excel report formatting
- Database best practices

## 📄 License

MIT License - see LICENSE file for details.

---

**🍲 Built for Haidilao restaurant operations with production-grade reliability and 100% test coverage**

**🔧 Troubleshooting:**

- Use 'Show System Status' to check configuration
- Run 'Comprehensive Tests' to verify all functionality
- Use 'Test Console Output' in Testing tab to verify GUI console
- Ensure .env file contains database credentials
- Check test coverage analysis for detailed diagnostics
