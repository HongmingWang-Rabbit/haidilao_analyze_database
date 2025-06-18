# Haidilao Paperwork Automation System

🏪 **Enhanced Excel to SQL processor with comprehensive validation**

## Overview

This system automates the processing of Haidilao restaurant daily paperwork from Excel files to SQL insert statements. It includes comprehensive data validation, error handling, and multiple entry points for different use cases.

## ✨ Features

- 📊 **Enhanced Data Validation**: Comprehensive validation of Excel file structure and data quality
- 🔍 **Smart Error Detection**: Detects missing stores, invalid dates, incorrect time segments, and data anomalies
- 🚀 **Multiple Entry Points**: TypeScript and Python interfaces for different workflows
- 🧪 **Comprehensive Testing**: 45+ tests ensuring reliability and data quality
- 📈 **Performance Optimized**: Fast processing with detailed progress reporting
- 🛡️ **Error Handling**: Graceful failure handling with clear error messages

## 🚀 Quick Start

### Prerequisites

- Node.js (for TypeScript interface)
- Python 3.x with pandas, openpyxl
- npm or pnpm package manager

### Installation

```bash
# Install dependencies
npm install
# or
pnpm install

# Install Python dependencies
pip install pandas openpyxl
```

## 📋 Entry Points

### 1. Enhanced TypeScript Interface (Recommended)

The new enhanced TypeScript interface provides the best user experience with comprehensive validation and clear feedback.

```bash
# all in one user interface
npm run open-automation-menu
```

```bash
# Process Excel file with full validation
npm run extract-enhanced process data.xlsx

# Process with custom output files
npm run extract-enhanced process data.xlsx -d daily.sql -t time.sql

# Skip validation (for trusted files)
npm run extract-enhanced process data.xlsx --skip-validation

# Validate file without processing
npm run extract-enhanced validate data.xlsx

# Show system status
npm run status
```

### 2. Python Direct Interface

Direct access to the Python scripts with enhanced validation.

```bash
# Process both daily and time segment data
npm run extract-all data.xlsx

# Process only daily reports
npm run extract-daily data.xlsx

# Process only time segments
npm run extract-time data.xlsx

# Show help
npm run help
```

### 3. Legacy TypeScript Interface

Original TypeScript interface (still available for compatibility).

```bash
npm run extract-sql data.xlsx
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

## 🧪 Testing

### Run All Tests

```bash
npm run test
```

### Run Specific Test Categories

```bash
# Core functionality tests
npm run test:core

# Validation tests only
npm run test:validation

# Quick validation tests
npm run test:quick

# Tests with coverage report
npm run test:coverage

# Validation-only tests
npm run validate
```

### Test Results

- **45 total tests** with **100% success rate**
- **Core functionality**: 25 tests
- **Validation system**: 8 tests
- **Integration tests**: 12 tests
- **Execution time**: ~3.8 seconds

## 📊 Usage Examples

### Example 1: Process Daily Reports

```bash
# Using enhanced TypeScript interface
npm run extract-enhanced process haidilao_data_20250610.xlsx

# Using Python interface
npm run extract-all haidilao_data_20250610.xlsx
```

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

### Project Structure

```
paperwork-automation/
├── scripts/
│   ├── extract-all.py          # Main Python orchestrator
│   ├── insert-data.py          # Daily reports processor
│   ├── extract-time-segments.py # Time segments processor
│   ├── extract-sql.ts          # Legacy TypeScript interface
│   └── extract-sql-enhanced.ts # Enhanced TypeScript interface
├── tests/                      # Comprehensive test suite
├── simple_test.py             # Simple test runner
├── run_tests.py              # Advanced test runner
└── package.json              # NPM configuration
```

### Adding New Features

1. Add functionality to Python scripts
2. Add tests in the `tests/` directory
3. Update TypeScript interface if needed
4. Run tests to ensure compatibility

## 🔧 Configuration

### Environment Variables

- `DEBUG=true` - Enable debug output
- `NODE_ENV=development` - Development mode

### Database Integration

The system generates SQL files by default. For direct database insertion, modify the Python scripts to include database connection logic.

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

## 📄 License

MIT License - see LICENSE file for details.

---

**🏪 Built for Haidilao restaurant operations with ❤️**
