#!/usr/bin/env python3
"""
Unit tests for extract-all.py script.
Tests the core data extraction functionality from the lib module.
"""

import unittest
import os
import sys
import pandas as pd
import tempfile
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the lib module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the functions we want to test from the lib module
from lib.data_extraction import (
    validate_excel_file,
    validate_daily_sheet,
    validate_time_segment_sheet,
    validate_date_column,
    validate_holiday_column,
    validate_numeric_column,
    extract_daily_reports,
    extract_time_segments
)

class TestDataExtractionFunctions(unittest.TestCase):
    """Test the core data extraction functions."""
    
    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    @patch('builtins.open')
    def test_extract_daily_reports_success(self, mock_open, mock_makedirs, mock_read_excel):
        """Test successful daily reports extraction."""
        # Mock DataFrame
        test_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610],
            '节假日': ['工作日'],
            '营业桌数': [50.0],
            '营业桌数(考核)': [48.0],
            '翻台率(考核)': [2.5],
            '营业收入(不含税)': [15000.0],
            '营业桌数(考核)(外卖)': [5.0],
            '就餐人数': [120],
            '优惠总金额(不含税)': [500.0]
        }
        mock_read_excel.return_value = pd.DataFrame(test_data)
        
        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = extract_daily_reports('test_file.xlsx')
        
        self.assertTrue(result)
        mock_read_excel.assert_called_once_with('test_file.xlsx', sheet_name='营业基础表')
    
    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    @patch('builtins.open')
    def test_extract_time_segments_success(self, mock_open, mock_makedirs, mock_read_excel):
        """Test successful time segments extraction."""
        # Mock DataFrame
        test_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610],
            '分时段': ['08:00-13:59'],
            '节假日': ['工作日'],
            '营业桌数(考核)': [25.0],
            '翻台率(考核)': [1.5]
        }
        mock_read_excel.return_value = pd.DataFrame(test_data)
        
        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = extract_time_segments('test_file.xlsx')
        
        self.assertTrue(result)
        mock_read_excel.assert_called_once_with('test_file.xlsx', sheet_name='分时段基础表')

class TestValidationFunctions(unittest.TestCase):
    """Test the validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_daily_data = {
            '门店名称': ['加拿大一店', '加拿大二店', '加拿大三店'],
            '日期': [20250610, 20250611, 20250612],
            '节假日': ['工作日', '节假日', '工作日'],
            '营业桌数': [50.0, 45.0, 40.0],
            '营业桌数(考核)': [48.0, 43.0, 38.0],
            '翻台率(考核)': [2.5, 2.8, 2.2],
            '营业收入(不含税)': [15000.0, 18000.0, 12000.0],
            '营业桌数(考核)(外卖)': [5.0, 8.0, 3.0],
            '就餐人数': [120, 150, 95],
            '优惠总金额(不含税)': [500.0, 800.0, 300.0]
        }
        
        self.valid_time_segment_data = {
            '门店名称': ['加拿大一店', '加拿大一店', '加拿大二店', '加拿大二店'],
            '日期': [20250610, 20250610, 20250610, 20250610],
            '分时段': ['08:00-13:59', '14:00-16:59', '17:00-21:59', '22:00-(次)07:59'],
            '节假日': ['工作日', '工作日', '节假日', '节假日'],
            '营业桌数(考核)': [25.0, 20.0, 30.0, 15.0],
            '翻台率(考核)': [1.5, 2.0, 2.8, 1.2]
        }
    
    def test_validate_excel_file_not_found(self):
        """Test validation when Excel file doesn't exist."""
        is_valid, warnings = validate_excel_file('nonexistent_file.xlsx')
        
        self.assertFalse(is_valid)
        self.assertTrue(any('File not found' in warning for warning in warnings))
    
    def test_validate_excel_file_wrong_extension(self):
        """Test validation with wrong file extension."""
        # Create a temporary file with wrong extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            is_valid, warnings = validate_excel_file(tmp_path)
            
            # Should still try to validate but give extension warning
            self.assertTrue(any('File extension warning' in warning for warning in warnings))
        finally:
            os.unlink(tmp_path)
    
    @patch('lib.data_extraction.os.path.exists')
    @patch('lib.data_extraction.pd.ExcelFile')
    def test_validate_excel_file_missing_sheets(self, mock_excel_file, mock_exists):
        """Test validation when required sheets are missing."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Mock Excel file with wrong sheet names
        mock_excel_instance = MagicMock()
        mock_excel_instance.sheet_names = ['Sheet1', 'Sheet2']
        mock_excel_instance.close = MagicMock()
        mock_excel_file.return_value = mock_excel_instance
        
        is_valid, warnings = validate_excel_file('test_file.xlsx')
        
        self.assertFalse(is_valid)
        self.assertTrue(any('Missing required sheets' in warning for warning in warnings))
    
    @patch('lib.data_extraction.os.path.exists')
    @patch('lib.data_extraction.pd.ExcelFile')
    @patch('lib.data_extraction.validate_daily_sheet')
    @patch('lib.data_extraction.validate_time_segment_sheet')
    def test_validate_excel_file_valid(self, mock_validate_time, mock_validate_daily, mock_excel_file, mock_exists):
        """Test validation with valid Excel file."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Mock Excel file with correct sheet names
        mock_excel_instance = MagicMock()
        mock_excel_instance.sheet_names = ['营业基础表', '分时段基础表']
        mock_excel_instance.close = MagicMock()
        mock_excel_file.return_value = mock_excel_instance
        
        # Mock validation functions to return no warnings
        mock_validate_daily.return_value = []
        mock_validate_time.return_value = []
        
        is_valid, warnings = validate_excel_file('test_file.xlsx')
        
        self.assertTrue(is_valid)
    
    def test_validate_daily_sheet_missing_columns(self):
        """Test daily sheet validation with missing columns."""
        # Create DataFrame with missing columns
        incomplete_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610],
            # Missing several required columns
        }
        df = pd.DataFrame(incomplete_data)
        
        # Mock Excel file
        mock_excel_file = MagicMock()
        with patch('pandas.read_excel', return_value=df):
            warnings = validate_daily_sheet(mock_excel_file)
        
        self.assertTrue(any('missing columns' in warning for warning in warnings))
    
    def test_validate_daily_sheet_unknown_stores(self):
        """Test daily sheet validation with unknown store names."""
        # Create DataFrame with unknown store
        invalid_data = self.valid_daily_data.copy()
        invalid_data['门店名称'] = ['Unknown Store', '加拿大二店', '加拿大三店']
        df = pd.DataFrame(invalid_data)
        
        # Mock Excel file
        mock_excel_file = MagicMock()
        with patch('pandas.read_excel', return_value=df):
            warnings = validate_daily_sheet(mock_excel_file)
        
        self.assertTrue(any('Unknown stores' in warning for warning in warnings))
    
    def test_validate_time_segment_sheet_unknown_segments(self):
        """Test time segment sheet validation with unknown time segments."""
        # Create DataFrame with unknown time segment
        invalid_data = self.valid_time_segment_data.copy()
        invalid_data['分时段'] = ['Unknown Time', '14:00-16:59', '17:00-21:59', '22:00-(次)07:59']
        df = pd.DataFrame(invalid_data)
        
        # Mock Excel file
        mock_excel_file = MagicMock()
        with patch('pandas.read_excel', return_value=df):
            warnings = validate_time_segment_sheet(mock_excel_file)
        
        self.assertTrue(any('Unknown time segments' in warning for warning in warnings))
    
    def test_validate_date_column_valid(self):
        """Test date column validation with valid dates."""
        valid_dates = pd.Series([20250610, 20250611, 20250612])
        
        warnings = validate_date_column(valid_dates, 'test_sheet')
        
        # Should have no warnings for valid dates
        self.assertEqual(len([w for w in warnings if 'date format issues' in w]), 0)
    
    def test_validate_date_column_invalid_format(self):
        """Test date column validation with invalid date format."""
        invalid_dates = pd.Series([2025061, 20250611, 2025061299])  # Wrong lengths
        
        warnings = validate_date_column(invalid_dates, 'test_sheet')
        
        self.assertTrue(any('date format issues' in warning for warning in warnings))
    
    def test_validate_date_column_null_values(self):
        """Test date column validation with null values."""
        dates_with_nulls = pd.Series([20250610, None, 20250612])
        
        warnings = validate_date_column(dates_with_nulls, 'test_sheet')
        
        self.assertTrue(any('missing dates' in warning for warning in warnings))
    
    def test_validate_holiday_column_valid(self):
        """Test holiday column validation with valid values."""
        valid_holidays = pd.Series(['工作日', '节假日', '工作日'])
        
        warnings = validate_holiday_column(valid_holidays, 'test_sheet')
        
        # Should have no warnings for valid holiday values
        self.assertEqual(len([w for w in warnings if 'Invalid holiday values' in w]), 0)
    
    def test_validate_holiday_column_invalid(self):
        """Test holiday column validation with invalid values."""
        invalid_holidays = pd.Series(['工作日', 'Invalid', '节假日'])
        
        warnings = validate_holiday_column(invalid_holidays, 'test_sheet')
        
        self.assertTrue(any('Invalid holiday values' in warning for warning in warnings))
    
    def test_validate_numeric_column_valid(self):
        """Test numeric column validation with valid numbers."""
        valid_numbers = pd.Series([1.5, 2.0, 2.8])
        
        warnings = validate_numeric_column(valid_numbers, '翻台率(考核)', 'test_sheet')
        
        # Should have no warnings for valid numbers
        self.assertEqual(len(warnings), 0)
    
    def test_validate_numeric_column_non_numeric(self):
        """Test numeric column validation with non-numeric values."""
        invalid_numbers = pd.Series([1.5, 'invalid', 2.8])
        
        warnings = validate_numeric_column(invalid_numbers, '翻台率(考核)', 'test_sheet')
        
        self.assertTrue(any('non-numeric values found' in warning for warning in warnings))
    
    def test_validate_numeric_column_negative_values(self):
        """Test numeric column validation with negative values where inappropriate."""
        negative_numbers = pd.Series([50, -10, 30])  # Negative table count
        
        warnings = validate_numeric_column(negative_numbers, '营业桌数', 'test_sheet')
        
        self.assertTrue(any('negative values found' in warning for warning in warnings))
    
    def test_validate_numeric_column_high_turnover(self):
        """Test numeric column validation with unusually high turnover rates."""
        high_turnover = pd.Series([2.5, 15.0, 2.8])  # 15.0 is unusually high
        
        warnings = validate_numeric_column(high_turnover, '翻台率(考核)', 'test_sheet')
        
        self.assertTrue(any('unusually high turnover rate' in warning for warning in warnings))

if __name__ == '__main__':
    unittest.main() 