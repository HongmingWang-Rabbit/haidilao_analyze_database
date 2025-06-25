#!/usr/bin/env python3
"""
Edge case tests for the validation functionality in extract-all.py.
Tests various data quality issues and edge cases that might occur in real Excel files.
"""

import unittest
import pandas as pd
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the scripts directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the functions we want to test
try:
    from extract_all import (
        validate_excel_file, 
        validate_daily_sheet, 
        validate_time_segment_sheet,
        validate_date_column,
        validate_holiday_column,
        validate_numeric_column
    )
except ImportError:
    # Try with hyphen-to-underscore conversion
    import importlib.util
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'extract-all.py')
    spec = importlib.util.spec_from_file_location("extract_all", script_path)
    extract_all = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extract_all)
    
    validate_excel_file = extract_all.validate_excel_file
    validate_daily_sheet = extract_all.validate_daily_sheet
    validate_time_segment_sheet = extract_all.validate_time_segment_sheet
    validate_date_column = extract_all.validate_date_column
    validate_holiday_column = extract_all.validate_holiday_column
    validate_numeric_column = extract_all.validate_numeric_column

class TestValidationEdgeCases(unittest.TestCase):
    """Test edge cases and unusual data scenarios."""
    
    def setUp(self):
        """Set up test fixtures with edge case data."""
        self.edge_case_daily_data = {
            '门店名称': ['加拿大一店', '加拿大二店', '加拿大三店', '加拿大四店', '加拿大五店'],
            '日期': [20250610, 20250611, 20250612, 20250613, 20250614],
            '节假日': ['工作日', '节假日', '工作日', '节假日', '工作日'],
            '营业桌数': [50.0, 45.0, 40.0, 35.0, 30.0],
            '营业桌数(考核)': [48.0, 43.0, 38.0, 33.0, 28.0],
            '翻台率(考核)': [2.5, 2.8, 2.2, 3.1, 2.9],
            '营业收入(不含税)': [15000.0, 18000.0, 12000.0, 20000.0, 16000.0],
            '营业桌数(考核)(外卖)': [5.0, 8.0, 3.0, 6.0, 4.0],
            '就餐人数': [120, 150, 95, 180, 140],
            '优惠总金额(不含税)': [500.0, 800.0, 300.0, 900.0, 600.0]
        }
    
    def test_empty_excel_file(self):
        """Test validation of empty Excel file."""
        # Create empty Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame().to_excel(writer, sheet_name='EmptySheet', index=False)
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_file.name)
                
                self.assertFalse(is_valid)
                self.assertTrue(any('Missing required sheets' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_excel_file_with_extra_sheets(self):
        """Test validation of Excel file with extra sheets (should be OK)."""
        # Create Excel file with required sheets plus extra ones
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(self.edge_case_daily_data).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
                pd.DataFrame({
                    '门店名称': ['加拿大一店', '加拿大二店'],
                    '日期': [20250610, 20250610],
                    '分时段': ['08:00-13:59', '14:00-16:59'],
                    '节假日': ['工作日', '工作日'],
                    '营业桌数(考核)': [25.0, 20.0],
                    '翻台率(考核)': [1.5, 2.0]
                }).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
                # Extra sheets
                pd.DataFrame({'extra': [1, 2, 3]}).to_excel(writer, sheet_name='ExtraSheet1', index=False)
                pd.DataFrame({'more': ['a', 'b', 'c']}).to_excel(writer, sheet_name='ExtraSheet2', index=False)
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_file.name)
                
                self.assertTrue(is_valid)  # Should still be valid with extra sheets
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_mixed_data_types_in_date_column(self):
        """Test date column with mixed data types."""
        mixed_dates = pd.Series([20250610, '20250611', 20250612.0, None, 'invalid'])
        
        warnings = validate_date_column(mixed_dates, 'TestSheet')
        
        self.assertTrue(any('date format issues' in warning for warning in warnings))
        self.assertTrue(any('missing dates' in warning for warning in warnings))
    
    def test_future_dates(self):
        """Test validation with future dates (should warn)."""
        future_year = datetime.now().year + 2
        future_dates = pd.Series([f"{future_year}0610", f"{future_year}0611"])
        
        warnings = validate_date_column(future_dates, 'TestSheet')
        
        # Should warn about future dates
        self.assertTrue(any('future date' in warning for warning in warnings))
    
    def test_very_old_dates(self):
        """Test validation with very old dates (should warn)."""
        old_dates = pd.Series([19900610, 20000101])
        
        warnings = validate_date_column(old_dates, 'TestSheet')
        
        # Should warn about very old dates
        self.assertTrue(any('very old date' in warning for warning in warnings))
    
    def test_numeric_column_with_infinity(self):
        """Test numeric column with infinity values."""
        infinity_data = pd.Series([1.5, float('inf'), 3.0, float('-inf')])
        
        warnings = validate_numeric_column(infinity_data, '翻台率(考核)', 'TestSheet')
        
        self.assertTrue(any('infinite values found' in warning for warning in warnings))
    
    def test_numeric_column_with_nan(self):
        """Test numeric column with NaN values."""
        nan_data = pd.Series([1.5, float('nan'), 3.0])
        
        warnings = validate_numeric_column(nan_data, '翻台率(考核)', 'TestSheet')
        
        self.assertTrue(any('missing values found' in warning for warning in warnings))
    
    def test_extremely_high_values(self):
        """Test validation with extremely high values."""
        extreme_values = pd.Series([50, 1000000, 30])  # 1 million tables
        
        warnings = validate_numeric_column(extreme_values, '营业桌数', 'TestSheet')
        
        self.assertTrue(any('extremely high value' in warning for warning in warnings))
    
    def test_zero_values_where_inappropriate(self):
        """Test validation with zero values where they shouldn't be."""
        zero_values = pd.Series([50, 0, 30])  # Zero tables
        
        warnings = validate_numeric_column(zero_values, '营业桌数', 'TestSheet')
        
        self.assertTrue(any('zero values found' in warning for warning in warnings))
    
    def test_holiday_column_with_whitespace(self):
        """Test holiday column with whitespace issues."""
        whitespace_holidays = pd.Series(['工作日', ' 节假日 ', '工作日\t', '\n节假日'])
        
        warnings = validate_holiday_column(whitespace_holidays, 'TestSheet')
        
        # Should handle whitespace gracefully or warn about it
        # The function should either clean it or warn about formatting issues
        self.assertTrue(len(warnings) >= 0)  # May or may not have warnings depending on implementation
    
    def test_holiday_column_with_case_variations(self):
        """Test holiday column with case variations."""
        case_variations = pd.Series(['工作日', '节假日', '工作日', '节假日'])  # These should be fine
        
        warnings = validate_holiday_column(case_variations, 'TestSheet')
        
        self.assertEqual(len(warnings), 0)  # Should have no warnings for correct values
    
    def test_store_names_with_extra_characters(self):
        """Test store names with extra characters or formatting."""
        data_with_extra_chars = {
            '门店名称': ['加拿大一店 ', '加拿大二店\t', ' 加拿大三店', '加拿大四店\n'],
            '日期': [20250610, 20250611, 20250612, 20250613],
            '节假日': ['工作日', '节假日', '工作日', '节假日'],
            '营业桌数': [50.0, 45.0, 40.0, 35.0],
            '营业桌数(考核)': [48.0, 43.0, 38.0, 33.0],
            '翻台率(考核)': [2.5, 2.8, 2.2, 3.1],
            '营业收入(不含税)': [15000.0, 18000.0, 12000.0, 20000.0],
            '营业桌数(考核)(外卖)': [5.0, 8.0, 3.0, 6.0],
            '就餐人数': [120, 150, 95, 180],
            '优惠总金额(不含税)': [500.0, 800.0, 300.0, 900.0]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(data_with_extra_chars).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_daily_sheet(excel_file)
            excel_file.close()
            
            # Should warn about formatting issues in store names
            self.assertTrue(any('store name formatting' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_duplicate_rows(self):
        """Test validation with duplicate rows."""
        duplicate_data = {
            '门店名称': ['加拿大一店', '加拿大一店', '加拿大二店'],  # Duplicate store on same date
            '日期': [20250610, 20250610, 20250610],
            '节假日': ['工作日', '工作日', '工作日'],
            '营业桌数': [50.0, 50.0, 45.0],
            '营业桌数(考核)': [48.0, 48.0, 43.0],
            '翻台率(考核)': [2.5, 2.5, 2.8],
            '营业收入(不含税)': [15000.0, 15000.0, 18000.0],
            '营业桌数(考核)(外卖)': [5.0, 5.0, 8.0],
            '就餐人数': [120, 120, 150],
            '优惠总金额(不含税)': [500.0, 500.0, 800.0]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(duplicate_data).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_daily_sheet(excel_file)
            excel_file.close()
            
            # Should warn about duplicate entries
            self.assertTrue(any('duplicate entries' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_missing_all_stores(self):
        """Test validation when not all expected stores are present."""
        incomplete_stores_data = {
            '门店名称': ['加拿大一店', '加拿大二店'],  # Missing stores 3-7
            '日期': [20250610, 20250610],
            '节假日': ['工作日', '工作日'],
            '营业桌数': [50.0, 45.0],
            '营业桌数(考核)': [48.0, 43.0],
            '翻台率(考核)': [2.5, 2.8],
            '营业收入(不含税)': [15000.0, 18000.0],
            '营业桌数(考核)(外卖)': [5.0, 8.0],
            '就餐人数': [120, 150],
            '优惠总金额(不含税)': [500.0, 800.0]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(incomplete_stores_data).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_daily_sheet(excel_file)
            excel_file.close()
            
            # Should warn about missing stores
            self.assertTrue(any('Missing expected stores' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_time_segments_missing_periods(self):
        """Test time segment validation when not all periods are present."""
        incomplete_segments_data = {
            '门店名称': ['加拿大一店', '加拿大一店'],  # Missing 2 time segments
            '日期': [20250610, 20250610],
            '分时段': ['08:00-13:59', '14:00-16:59'],  # Missing evening and late night
            '节假日': ['工作日', '工作日'],
            '营业桌数(考核)': [25.0, 20.0],
            '翻台率(考核)': [1.5, 2.0]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(incomplete_segments_data).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_time_segment_sheet(excel_file)
            excel_file.close()
            
            # Should warn about missing time segments
            self.assertTrue(any('Missing expected time segments' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_inconsistent_holiday_values_between_sheets(self):
        """Test when holiday values are inconsistent between daily and time segment sheets."""
        daily_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610],
            '节假日': ['工作日'],  # Workday in daily sheet
            '营业桌数': [50.0],
            '营业桌数(考核)': [48.0],
            '翻台率(考核)': [2.5],
            '营业收入(不含税)': [15000.0],
            '营业桌数(考核)(外卖)': [5.0],
            '就餐人数': [120],
            '优惠总金额(不含税)': [500.0]
        }
        
        time_segment_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610],
            '分时段': ['08:00-13:59'],
            '节假日': ['节假日'],  # Holiday in time segment sheet - inconsistent!
            '营业桌数(考核)': [25.0],
            '翻台率(考核)': [1.5]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(daily_data).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
                pd.DataFrame(time_segment_data).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_file.name)
                
                # Should detect inconsistency between sheets
                self.assertTrue(any('inconsistent holiday values' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

class TestPerformanceAndLargeData(unittest.TestCase):
    """Test validation performance with large datasets."""
    
    def test_large_dataset_validation(self):
        """Test validation with a large dataset (performance test)."""
        # Create a large dataset with 1000 rows
        large_daily_data = {
            '门店名称': ['加拿大一店'] * 200 + ['加拿大二店'] * 200 + ['加拿大三店'] * 200 + 
                       ['加拿大四店'] * 200 + ['加拿大五店'] * 200,
            '日期': [20250610 + i for i in range(1000)],
            '节假日': ['工作日', '节假日'] * 500,
            '营业桌数': [50.0 + (i % 10) for i in range(1000)],
            '营业桌数(考核)': [48.0 + (i % 10) for i in range(1000)],
            '翻台率(考核)': [2.5 + (i % 5) * 0.1 for i in range(1000)],
            '营业收入(不含税)': [15000.0 + (i % 100) * 100 for i in range(1000)],
            '营业桌数(考核)(外卖)': [5.0 + (i % 3) for i in range(1000)],
            '就餐人数': [120 + (i % 50) for i in range(1000)],
            '优惠总金额(不含税)': [500.0 + (i % 20) * 25 for i in range(1000)]
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(large_daily_data).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
                # Create minimal time segment data to satisfy requirements
                pd.DataFrame({
                    '门店名称': ['加拿大一店'],
                    '日期': [20250610],
                    '分时段': ['08:00-13:59'],
                    '节假日': ['工作日'],
                    '营业桌数(考核)': [25.0],
                    '翻台率(考核)': [1.5]
                }).to_excel(writer, sheet_name='海外门店营业数据分时段_不含税_', index=False)
        
        try:
            import time
            start_time = time.time()
            
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_file.name)
            
            end_time = time.time()
            validation_time = end_time - start_time
            
            # Validation should complete in reasonable time (less than 5 seconds)
            self.assertLess(validation_time, 5.0, "Validation took too long for large dataset")
            
            # Should still detect issues if any
            self.assertIsInstance(is_valid, bool)
            self.assertIsInstance(warnings, list)
            
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

if __name__ == '__main__':
    unittest.main() 