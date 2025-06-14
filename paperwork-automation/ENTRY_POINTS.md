# 🚀 Entry Points Guide

## Overview

The Haidilao Paperwork Automation System now provides multiple entry points to suit different workflows and preferences. All entry points integrate with the enhanced validation system for reliable data processing.

## 🎯 Recommended Entry Point

### Enhanced TypeScript Interface

**Best for**: Interactive use, development, and comprehensive feedback

```bash
# Show system status and available commands
npm run status

# Process Excel file with full validation
npm run extract-enhanced process data.xlsx

# Process with custom output files
npm run extract-enhanced process data.xlsx \
  --daily-output daily_reports.sql \
  --time-output time_segments.sql

# Skip validation for trusted files
npm run extract-enhanced process data.xlsx --skip-validation

# Debug mode with detailed output
npm run extract-enhanced process data.xlsx --debug

# Validate file without processing
npm run extract-enhanced validate data.xlsx

# Run tests through TypeScript interface
npm run extract-enhanced test quick
npm run extract-enhanced test core
npm run extract-enhanced test validation
```

**Features:**

- 🔍 Comprehensive validation with clear feedback
- 📊 Progress indicators and emoji status
- 🛡️ Graceful error handling
- 🧪 Integrated test runner
- 📈 Performance monitoring

## 🐍 Python Direct Interface

### Main Orchestrator Script

**Best for**: Production automation, scripting, and batch processing

```bash
# Process both daily and time segment data
npm run extract-all path/to/target/xlsx

# With custom output files
python3 scripts/extract-all.py data.xlsx \
  --daily-output daily_reports.sql \
  --time-output time_segments.sql

# Skip validation for trusted files
python3 scripts/extract-all.py data.xlsx --skip-validation

# Debug mode
python3 scripts/extract-all.py data.xlsx --debug

# Show help
npm run help
```

### Individual Processing Scripts

**Best for**: Specific data extraction needs

```bash
# Process only daily reports
npm run extract-daily data.xlsx
# or
python3 scripts/insert-data.py data.xlsx

# Process only time segments
npm run extract-time data.xlsx
# or
python3 scripts/extract-time-segments.py data.xlsx
```

## 🧪 Testing Entry Points

### Comprehensive Test Suite

```bash
# Run all tests (45 tests)
npm run test

# Run specific test categories
npm run test:core        # Core functionality (25 tests)
npm run test:validation  # Validation system (8 tests)
npm run test:quick       # Quick validation (6 tests)
npm run test:coverage    # With coverage report

# Validation-only tests
npm run validate
```

### Advanced Test Runner

```bash
# Direct access to advanced test runner
python3 run_tests.py core
python3 run_tests.py validation
python3 run_tests.py quick
python3 run_tests.py coverage
```

## 📊 Legacy Entry Points

### Original TypeScript Interface

**Available for**: Backward compatibility

```bash
npm run extract-sql data.xlsx
# or
npx ts-node scripts/extract-sql.ts data.xlsx
```

## 🔧 Command Line Options

### Enhanced TypeScript Interface Options

```bash
npx ts-node scripts/extract-sql-enhanced.ts process [options] <excel-file>

Options:
  -d, --daily-output <file>  Output file for daily reports SQL
  -t, --time-output <file>   Output file for time segments SQL
  --skip-validation          Skip data format validation
  --debug                    Enable debug output
```

### Python Script Options

```bash
python3 scripts/extract-all.py [options] <excel-file>

Options:
  --daily-output <file>      Output file for daily reports SQL
  --time-output <file>       Output file for time segments SQL
  --skip-validation          Skip data format validation
  --debug                    Enable debug output
  -h, --help                 Show help message
```

## 🎯 Usage Scenarios

### Scenario 1: First-time User

```bash
# Check system status
npm run status

# Validate a file first
npm run extract-enhanced validate sample_data.xlsx

# Process with full validation
npm run extract-enhanced process sample_data.xlsx
```

### Scenario 2: Production Automation

```bash
# Automated processing with validation
npm run extract-all daily_reports_20250610.xlsx

# Or skip validation for trusted sources
python3 scripts/extract-all.py daily_reports_20250610.xlsx --skip-validation
```

### Scenario 3: Development & Testing

```bash
# Run tests first
npm run test:quick

# Process with debug output
npm run extract-enhanced process test_data.xlsx --debug

# Validate specific functionality
npm run test:validation
```

### Scenario 4: Custom Output Files

```bash
# TypeScript interface
npm run extract-enhanced process data.xlsx \
  --daily-output "reports/daily_$(date +%Y%m%d).sql" \
  --time-output "reports/time_$(date +%Y%m%d).sql"

# Python interface
python3 scripts/extract-all.py data.xlsx \
  --daily-output "reports/daily_$(date +%Y%m%d).sql" \
  --time-output "reports/time_$(date +%Y%m%d).sql"
```

## 🚨 Error Handling

All entry points provide consistent error handling:

- **❌ Critical Errors**: Stop processing with clear error messages
- **⚠️ Warnings**: Continue processing with caution indicators
- **✅ Success**: Clear confirmation with file locations

### Common Error Resolution

```bash
# File not found
npm run extract-enhanced validate /path/to/file.xlsx

# Validation errors
npm run extract-enhanced process file.xlsx --debug

# Skip validation if needed
npm run extract-enhanced process file.xlsx --skip-validation
```

## 📈 Performance Comparison

| Entry Point   | Startup Time | Validation Speed | Processing Speed | Best For        |
| ------------- | ------------ | ---------------- | ---------------- | --------------- |
| Enhanced TS   | ~2.5s        | Fast             | Fast             | Interactive use |
| Python Direct | ~1.2s        | Fast             | Fast             | Automation      |
| Legacy TS     | ~2.0s        | None             | Fast             | Compatibility   |

## 🔄 Migration Guide

### From Legacy TypeScript

```bash
# Old way
npm run extract-sql data.xlsx

# New way (recommended)
npm run extract-enhanced process data.xlsx
```

### From Direct Python

```bash
# Old way
python3 scripts/insert-data.py data.xlsx

# New way (with validation)
npm run extract-all data.xlsx
```

## 🎉 Quick Start Commands

```bash
# 1. Check system status
npm run status

# 2. Run tests to verify everything works
npm run test:quick

# 3. Process your first file
npm run extract-enhanced process your_data.xlsx

# 4. Check the generated SQL files
ls -la *.sql
```

---

**💡 Tip**: Start with `npm run status` to see all available commands and system status!
