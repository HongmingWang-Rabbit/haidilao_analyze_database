# Test Suite for Paperwork Automation Scripts

This directory contains comprehensive unit tests for the paperwork automation scripts that process Haidilao restaurant Excel data and generate PostgreSQL insert statements.

## Overview

The test suite covers:

- **Data extraction and transformation** from Excel files
- **SQL generation** with UPSERT statements
- **Error handling** for invalid data and missing files
- **Data validation** for store mappings and date formats
- **File processing** workflows

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest fixtures (optional)
├── requirements-test.txt       # Testing dependencies
├── run_tests.py               # Advanced test runner with coverage
├── simple_test.py             # Simple test runner for core tests
├── test_insert_data.py        # Tests for insert-data.py script
├── test_extract_time_segments.py  # Tests for extract-time-segments.py script
├── test_extract_all.py        # Tests for extract-all.py script
└── README.md                  # This file
```

## Running Tests

### Quick Test (Recommended)

Run the core functionality tests:

```bash
python3 tests/simple_test.py
```

This runs 25+ tests covering the main data processing functions.

### Full Test Suite

Run all tests including integration tests:

```bash
python3 tests/run_tests.py
```

### Advanced Options

```bash
# Run with coverage reporting
python3 tests/run_tests.py --coverage

# Run specific test module
python3 tests/run_tests.py --module test_insert_data

# Run with less verbose output
python3 tests/run_tests.py --verbose 1

# List all available tests
python3 tests/run_tests.py --list
```

### Using pytest (Optional)

If you have pytest installed:

```bash
# Install testing dependencies
pip install -r requirements-test.txt

# Run tests with pytest
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=scripts --cov-report=html
```

## Test Coverage

### insert-data.py Tests (`test_insert_data.py`)

- ✅ **Date extraction** from filenames
- ✅ **SQL value formatting** (strings, numbers, booleans, dates, NULL)
- ✅ **Excel data transformation** with store mapping
- ✅ **UPSERT SQL generation** with conflict resolution
- ✅ **File processing** with error handling
- ✅ **Store ID mapping** validation (7 stores)
- ✅ **Date format variations** (YYYYMMDD format)
- ✅ **Invalid data handling** (unknown stores, bad dates)

### extract-time-segments.py Tests (`test_extract_time_segments.py`)

- ✅ **Time segment data transformation**
- ✅ **Time segment ID mapping** (4 time periods)
- ✅ **Store ID mapping** validation
- ✅ **Holiday detection** (工作日 vs 节假日)
- ✅ **UPSERT SQL generation** for time segments
- ✅ **NULL value handling** in numeric fields
- ✅ **Multiple record processing**
- ✅ **Error handling** for unknown stores/segments

### extract-all.py Tests (`test_extract_all.py`)

- ✅ **Script orchestration** (runs both extraction scripts)
- ✅ **Command line argument handling**
- ✅ **Subprocess execution** with success/failure handling
- ✅ **Debug mode** flag passing
- ✅ **Custom output file** handling
- ⚠️ **Main function tests** (some integration issues)

## Test Data

Tests use realistic sample data that mirrors the actual Excel structure:

### Daily Report Data

- **Stores**: 加拿大一店 through 加拿大七店 (IDs 1-7)
- **Date format**: YYYYMMDD (e.g., 20250610)
- **Holiday types**: 工作日 (workday) / 节假日 (holiday)
- **Metrics**: Tables served, turnover rate, revenue, customers, etc.

### Time Segment Data

- **Time periods**:
  - 08:00-13:59 (ID: 1)
  - 14:00-16:59 (ID: 2)
  - 17:00-21:59 (ID: 3)
  - 22:00-(次)07:59 (ID: 4)
- **Metrics**: Tables served (validated), turnover rate

## Adding New Tests

### Test File Structure

```python
#!/usr/bin/env python3
"""
Unit tests for [script_name].py
"""

import unittest
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import with fallback for hyphenated filenames
try:
    from script_name import function_to_test
except ImportError:
    import importlib.util
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script-name.py')
    spec = importlib.util.spec_from_file_location("script_name", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    function_to_test = module.function_to_test

class TestScriptName(unittest.TestCase):

    def test_function_behavior(self):
        """Test description."""
        # Test implementation
        result = function_to_test(input_data)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()
```

### Test Categories

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test complete workflows
3. **Data Validation Tests**: Test data mapping and validation
4. **Error Handling Tests**: Test exception handling and edge cases

### Best Practices

- Use descriptive test method names: `test_transform_excel_data_with_invalid_date`
- Include docstrings explaining what each test validates
- Use `setUp()` and `tearDown()` for test fixtures
- Mock external dependencies (file I/O, subprocess calls)
- Test both success and failure scenarios
- Validate error messages and logging output

## Troubleshooting

### Common Issues

1. **Import Errors**: Scripts use hyphens in filenames, tests use underscores

   - Solution: Use the importlib.util fallback pattern shown above

2. **Path Issues**: Tests can't find the scripts directory

   - Solution: Ensure `sys.path.insert(0, scripts_path)` is called

3. **Mock Issues**: Mocking doesn't work as expected

   - Solution: Use `patch` decorators and verify mock call arguments

4. **Pandas Warnings**: Lots of pandas deprecation warnings
   - Solution: Add `warnings.filterwarnings('ignore')` in test setup

### Dependencies

Core testing uses only Python standard library:

- `unittest` - Test framework
- `unittest.mock` - Mocking utilities
- `tempfile` - Temporary files for testing
- `os`, `sys` - Path manipulation

Optional dependencies (install with `pip install -r requirements-test.txt`):

- `coverage` - Code coverage reporting
- `pytest` - Alternative test runner
- `pandas` - Data processing (already required by main scripts)

## Test Results

When all tests pass, you should see output like:

```
Ran 25 tests in 0.011s

OK
```

This indicates:

- ✅ All data transformation functions work correctly
- ✅ SQL generation produces valid UPSERT statements
- ✅ Error handling catches and reports issues appropriately
- ✅ Store and time segment mappings are accurate
- ✅ File processing workflows complete successfully

The test suite provides confidence that the scripts will process real Excel data correctly and generate valid SQL for the PostgreSQL database.
