#!/usr/bin/env python3
"""
Unit tests for extract-all.py script.
Tests the orchestration of both daily reports and time segment extractions.
Enhanced with validation functionality tests.
"""

import unittest
import subprocess
import os
import sys
import pandas as pd
import tempfile
from unittest.mock import patch, MagicMock, call

# Add the scripts directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the functions we want to test
import importlib.util
import os

# Load the extract-all.py module dynamically
script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'extract-all.py')
spec = importlib.util.spec_from_file_location("extract_all", script_path)
if spec and spec.loader:
    extract_all = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extract_all)
    
    run_script = extract_all.run_script
    validate_excel_file = extract_all.validate_excel_file
    validate_daily_sheet = extract_all.validate_daily_sheet
    validate_time_segment_sheet = extract_all.validate_time_segment_sheet
    validate_date_column = extract_all.validate_date_column
    validate_holiday_column = extract_all.validate_holiday_column
    validate_numeric_column = extract_all.validate_numeric_column
else:
    raise ImportError("Could not load extract-all.py module")

class TestExtractAll(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_run_script_success(self, mock_subprocess):
        """Test successful script execution."""
        # Mock successful subprocess result
        mock_result = MagicMock()
        mock_result.stdout = "Processing completed successfully"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            result = run_script('insert-data.py', 'test_file.xlsx')
            
            self.assertTrue(result)
            mock_subprocess.assert_called_once()
            mock_print.assert_called()
    
    @patch('subprocess.run')
    def test_run_script_with_debug(self, mock_subprocess):
        """Test script execution with debug flag."""
        # Mock successful subprocess result
        mock_result = MagicMock()
        mock_result.stdout = "Processing completed successfully"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = run_script('insert-data.py', 'test_file.xlsx', debug=True)
        
        self.assertTrue(result)
        # Check that --debug flag was added to command
        called_args = mock_subprocess.call_args[0][0]
        self.assertIn('--debug', called_args)
    
    @patch('subprocess.run')
    def test_run_script_with_output(self, mock_subprocess):
        """Test script execution with custom output file."""
        # Mock successful subprocess result
        mock_result = MagicMock()
        mock_result.stdout = "Processing completed successfully"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = run_script('insert-data.py', 'test_file.xlsx', output='custom_output.sql')
        
        self.assertTrue(result)
        # Check that --output flag was added to command
        called_args = mock_subprocess.call_args[0][0]
        self.assertIn('--output', called_args)
        self.assertIn('custom_output.sql', called_args)
    
    @patch('subprocess.run')
    def test_run_script_with_warnings(self, mock_subprocess):
        """Test script execution with warnings in stderr."""
        # Mock subprocess result with warnings
        mock_result = MagicMock()
        mock_result.stdout = "Processing completed successfully"
        mock_result.stderr = "Warning: Some data was skipped"
        mock_subprocess.return_value = mock_result
        
        with patch('builtins.print') as mock_print:
            result = run_script('insert-data.py', 'test_file.xlsx')
            
            self.assertTrue(result)
            # Check that warnings are printed
            mock_print.assert_any_call("⚠️  Warnings: Warning: Some data was skipped")
    
    @patch('subprocess.run')
    def test_run_script_failure(self, mock_subprocess):
        """Test script execution failure."""
        # Mock failed subprocess result
        error = subprocess.CalledProcessError(1, 'python3')
        error.stdout = "Some output"
        error.stderr = "Error: File not found"
        mock_subprocess.side_effect = error
        
        with patch('builtins.print') as mock_print:
            result = run_script('insert-data.py', 'nonexistent_file.xlsx')
            
            self.assertFalse(result)
            # Check that error messages are printed
            mock_print.assert_any_call("❌ Error running insert-data.py:")
    
    @patch('os.path.join')
    def test_script_path_construction(self, mock_path_join):
        """Test that script path is constructed correctly."""
        mock_path_join.return_value = '/path/to/script.py'
        
        with patch('subprocess.run') as mock_subprocess:
            mock_result = MagicMock()
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result
            
            run_script('test-script.py', 'input.xlsx')
            
            # Check that os.path.join was called to construct script path
            mock_path_join.assert_called()
    
    def test_command_construction_basic(self):
        """Test basic command construction."""
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.path.join', return_value='/path/to/script.py'):
            
            mock_result = MagicMock()
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result
            
            run_script('test-script.py', 'input.xlsx')
            
            # Check the command that was called
            called_args = mock_subprocess.call_args[0][0]
            expected_start = ['python3', '/path/to/script.py', 'input.xlsx']
            self.assertEqual(called_args[:3], expected_start)
    
    def test_command_construction_all_options(self):
        """Test command construction with all options."""
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.path.join', return_value='/path/to/script.py'):
            
            mock_result = MagicMock()
            mock_result.stdout = "Success"
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result
            
            run_script('test-script.py', 'input.xlsx', debug=True, output='output.sql')
            
            # Check the command that was called
            called_args = mock_subprocess.call_args[0][0]
            expected_args = ['python3', '/path/to/script.py', 'input.xlsx', '--debug', '--output', 'output.sql']
            self.assertEqual(called_args, expected_args)

class TestValidationFunctions(unittest.TestCase):
    """Test the new validation functionality."""
    
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
        """Test validation of non-existent file."""
        with patch('builtins.print'):
            is_valid, warnings = validate_excel_file('nonexistent.xlsx')
            
            self.assertFalse(is_valid)
            self.assertTrue(any('File not found' in warning for warning in warnings))
    
    def test_validate_excel_file_wrong_extension(self):
        """Test validation of file with wrong extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_path)
                
                # Should have warning about file extension
                self.assertTrue(any('File extension warning' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_excel_file_missing_sheets(self):
        """Test validation of Excel file with missing required sheets."""
        # Create Excel file with wrong sheet names
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame({'col1': [1, 2, 3]}).to_excel(writer, sheet_name='WrongSheet', index=False)
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_file.name)
                
                self.assertFalse(is_valid)
                self.assertTrue(any('Missing required sheets' in warning for warning in warnings))
                self.assertTrue(any('营业基础表' in warning for warning in warnings))
                self.assertTrue(any('分时段基础表' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_validate_excel_file_valid(self):
        """Test validation of valid Excel file."""
        # Create valid Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(self.valid_daily_data).to_excel(writer, sheet_name='营业基础表', index=False)
                pd.DataFrame(self.valid_time_segment_data).to_excel(writer, sheet_name='分时段基础表', index=False)
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_file.name)
                
                self.assertTrue(is_valid)
                # Should have minimal warnings for valid file
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_validate_daily_sheet_missing_columns(self):
        """Test validation of daily sheet with missing columns."""
        # Create Excel file with missing columns
        incomplete_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610]
            # Missing other required columns
        }
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(incomplete_data).to_excel(writer, sheet_name='营业基础表', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            warnings = validate_daily_sheet(excel_file)
            excel_file.close()
            
            self.assertTrue(any('missing columns' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_validate_daily_sheet_unknown_stores(self):
        """Test validation of daily sheet with unknown store names."""
        invalid_data = self.valid_daily_data.copy()
        invalid_data['门店名称'] = ['加拿大一店', '未知店铺', '测试店']
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(invalid_data).to_excel(writer, sheet_name='营业基础表', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_daily_sheet(excel_file)
            excel_file.close()
            
            self.assertTrue(any('Unknown stores' in warning for warning in warnings))
            self.assertTrue(any('未知店铺' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_validate_time_segment_sheet_unknown_segments(self):
        """Test validation of time segment sheet with unknown time segments."""
        invalid_data = self.valid_time_segment_data.copy()
        invalid_data['分时段'] = ['08:00-13:59', '未知时段', '测试时段', '22:00-(次)07:59']
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                pd.DataFrame(invalid_data).to_excel(writer, sheet_name='分时段基础表', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_time_segment_sheet(excel_file)
            excel_file.close()
            
            self.assertTrue(any('Unknown time segments' in warning for warning in warnings))
            self.assertTrue(any('未知时段' in warning for warning in warnings))
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_validate_date_column_valid(self):
        """Test validation of valid date column."""
        valid_dates = pd.Series([20250610, 20250611, 20250612])
        
        with patch('builtins.print'):
            warnings = validate_date_column(valid_dates, 'TestSheet')
            
            # Should have no warnings for valid dates
            self.assertEqual(len(warnings), 0)
    
    def test_validate_date_column_invalid_format(self):
        """Test validation of invalid date formats."""
        invalid_dates = pd.Series([20250610, 'invalid_date', 2025061, 20251301])  # Invalid month
        
        warnings = validate_date_column(invalid_dates, 'TestSheet')
        
        self.assertTrue(any('date format issues' in warning for warning in warnings))
        self.assertTrue(any('Cannot parse date' in warning for warning in warnings))
        self.assertTrue(any('Invalid month' in warning for warning in warnings))
    
    def test_validate_date_column_null_values(self):
        """Test validation of date column with null values."""
        dates_with_nulls = pd.Series([20250610, None, 20250612])
        
        warnings = validate_date_column(dates_with_nulls, 'TestSheet')
        
        self.assertTrue(any('missing dates' in warning for warning in warnings))
    
    def test_validate_holiday_column_valid(self):
        """Test validation of valid holiday column."""
        valid_holidays = pd.Series(['工作日', '节假日', '工作日'])
        
        with patch('builtins.print'):
            warnings = validate_holiday_column(valid_holidays, 'TestSheet')
            
            # Should have no warnings for valid values
            self.assertEqual(len(warnings), 0)
    
    def test_validate_holiday_column_invalid(self):
        """Test validation of invalid holiday values."""
        invalid_holidays = pd.Series(['工作日', '无效值', '测试'])
        
        warnings = validate_holiday_column(invalid_holidays, 'TestSheet')
        
        self.assertTrue(any('Invalid holiday values' in warning for warning in warnings))
        self.assertTrue(any('无效值' in warning for warning in warnings))
    
    def test_validate_numeric_column_valid(self):
        """Test validation of valid numeric column."""
        valid_numbers = pd.Series([1.5, 2.0, 3.5])
        
        warnings = validate_numeric_column(valid_numbers, '翻台率(考核)', 'TestSheet')
        
        # Should have no warnings for valid numbers
        self.assertEqual(len(warnings), 0)
    
    def test_validate_numeric_column_non_numeric(self):
        """Test validation of numeric column with non-numeric values."""
        invalid_numbers = pd.Series([1.5, 'invalid', 3.5])
        
        warnings = validate_numeric_column(invalid_numbers, '翻台率(考核)', 'TestSheet')
        
        self.assertTrue(any('non-numeric values found' in warning for warning in warnings))
    
    def test_validate_numeric_column_negative_values(self):
        """Test validation of numeric column with negative values where inappropriate."""
        negative_numbers = pd.Series([50, -10, 30])  # Negative table count
        
        warnings = validate_numeric_column(negative_numbers, '营业桌数', 'TestSheet')
        
        self.assertTrue(any('negative values found' in warning for warning in warnings))
    
    def test_validate_numeric_column_high_turnover(self):
        """Test validation of unusually high turnover rates."""
        high_turnover = pd.Series([2.5, 15.0, 3.0])  # 15.0 is unusually high
        
        warnings = validate_numeric_column(high_turnover, '翻台率(考核)', 'TestSheet')
        
        self.assertTrue(any('unusually high turnover rate' in warning for warning in warnings))

class TestMainFunctionWithValidation(unittest.TestCase):
    """Test the main function with validation features."""
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    @patch('sys.argv', ['extract-all.py', 'test_file.xlsx'])
    def test_main_with_validation_success(self, mock_run_script, mock_validate):
        """Test main function with successful validation."""
        # Mock validation success
        mock_validate.return_value = (True, [])
        mock_run_script.return_value = True
        
        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            
            main = extract_all.main
            main()
            
            # Check that validation was called
            mock_validate.assert_called_once_with('test_file.xlsx')
            
            # Check that both scripts were called
            self.assertEqual(mock_run_script.call_count, 2)
            
            # Check success exit
            mock_exit.assert_called_with(0)
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    @patch('sys.argv', ['extract-all.py', 'test_file.xlsx'])
    def test_main_with_validation_warnings(self, mock_run_script, mock_validate):
        """Test main function with validation warnings but no critical errors."""
        # Mock validation with warnings
        mock_validate.return_value = (True, ['⚠️  Some warning'])
        mock_run_script.return_value = True
        
        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            
            main = extract_all.main
            main()
            
            # Check that validation warnings were printed
            mock_print.assert_any_call('⚠️  Some warning')
            
            # Should still proceed with extraction
            self.assertEqual(mock_run_script.call_count, 2)
            mock_exit.assert_called_with(0)
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    @patch('sys.argv', ['extract-all.py', 'test_file.xlsx'])
    def test_main_with_validation_failure(self, mock_run_script, mock_validate):
        """Test main function with validation failure."""
        # Mock validation failure
        mock_validate.return_value = (False, ['❌ Critical error'])
        
        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            
            main = extract_all.main
            main()
            
            # Check that error was printed
            mock_print.assert_any_call('❌ Critical error')
            mock_print.assert_any_call('❌ Critical validation errors found. Please fix the Excel file format before proceeding.')
            
            # Should not run extraction scripts
            mock_run_script.assert_not_called()
            
            # Should exit with error code
            mock_exit.assert_called_with(1)
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    @patch('sys.argv', ['extract-all.py', 'test_file.xlsx', '--skip-validation'])
    def test_main_skip_validation(self, mock_run_script, mock_validate):
        """Test main function with validation skipped."""
        mock_run_script.return_value = True
        
        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            
            main = extract_all.main
            main()
            
            # Check that validation was not called
            mock_validate.assert_not_called()
            
            # Check that skip message was printed
            mock_print.assert_any_call('⚠️  Skipping data format validation...')
            
            # Should still run extraction scripts
            self.assertEqual(mock_run_script.call_count, 2)
            mock_exit.assert_called_with(0)

class TestMainFunction(unittest.TestCase):
    """Test the main function orchestration."""
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    @patch('sys.argv', ['extract-all.py', 'test_file.xlsx'])
    def test_main_success_both_scripts(self, mock_run_script, mock_validate):
        """Test main function when both scripts succeed."""
        # Mock validation success and both scripts succeeding
        mock_validate.return_value = (True, [])
        mock_run_script.return_value = True
        
        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            
            # Import and run main (need to import here to avoid issues with patched argv)
            main = extract_all.main
            main()
            
            # Check that both scripts were called
            self.assertEqual(mock_run_script.call_count, 2)
            
            # Check that success exit was called
            mock_exit.assert_called_with(0)
            
            # Check success message was printed
            mock_print.assert_any_call("✅ All extractions completed successfully!")
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    @patch('sys.argv', ['extract-all.py', 'test_file.xlsx'])
    def test_main_partial_failure(self, mock_run_script, mock_validate):
        """Test main function when one script fails."""
        # Mock validation success, first script succeeding, second failing
        mock_validate.return_value = (True, [])
        mock_run_script.side_effect = [True, False]
        
        with patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            
            main = extract_all.main
            main()
            
            # Check that both scripts were called
            self.assertEqual(mock_run_script.call_count, 2)
            
            # Check that failure exit was called
            mock_exit.assert_called_with(1)
            
            # Check failure message was printed
            mock_print.assert_any_call("❌ Some extractions failed. Check the error messages above.")
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    @patch('sys.argv', ['extract-all.py', 'test_file.xlsx', '--debug'])
    def test_main_with_debug_flag(self, mock_run_script, mock_validate):
        """Test main function with debug flag."""
        mock_validate.return_value = (True, [])
        mock_run_script.return_value = True
        
        with patch('builtins.print'), \
             patch('sys.exit'):
            
            main = extract_all.main
            main()
            
            # Check that debug flag was passed to both scripts
            calls = mock_run_script.call_args_list
            for call_args in calls:
                # call_args[0] contains positional args, call_args[1] contains keyword args
                self.assertTrue(call_args[1].get('debug', False))
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    @patch('sys.argv', ['extract-all.py', 'test_file.xlsx', '--daily-output', 'daily.sql', '--time-output', 'time.sql'])
    def test_main_with_custom_outputs(self, mock_run_script, mock_validate):
        """Test main function with custom output files."""
        mock_validate.return_value = (True, [])
        mock_run_script.return_value = True
        
        with patch('builtins.print'), \
             patch('sys.exit'):
            
            main = extract_all.main
            main()
            
            # Check that custom output files were passed
            calls = mock_run_script.call_args_list
            
            # First call should have daily output
            self.assertEqual(calls[0][1].get('output'), 'daily.sql')
            
            # Second call should have time output
            self.assertEqual(calls[1][1].get('output'), 'time.sql')

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    def test_script_call_order(self, mock_run_script, mock_validate):
        """Test that scripts are called in the correct order."""
        mock_validate.return_value = (True, [])
        mock_run_script.return_value = True
        
        with patch('sys.argv', ['extract-all.py', 'test_file.xlsx']), \
             patch('builtins.print'), \
             patch('sys.exit'):
            
            main = extract_all.main
            main()
            
            # Check the order of script calls
            calls = mock_run_script.call_args_list
            self.assertEqual(len(calls), 2)
            
            # First call should be insert-data.py
            self.assertEqual(calls[0][0][0], 'insert-data.py')
            
            # Second call should be extract-time-segments.py
            self.assertEqual(calls[1][0][0], 'extract-time-segments.py')
    
    @patch('extract_all.validate_excel_file')
    @patch('extract_all.run_script')
    def test_input_file_passed_to_both_scripts(self, mock_run_script, mock_validate):
        """Test that the same input file is passed to both scripts."""
        mock_validate.return_value = (True, [])
        mock_run_script.return_value = True
        
        test_input_file = 'test_data_2025_6_10.xlsx'
        
        with patch('sys.argv', ['extract-all.py', test_input_file]), \
             patch('builtins.print'), \
             patch('sys.exit'):
            
            main = extract_all.main
            main()
            
            # Check that both calls received the same input file
            calls = mock_run_script.call_args_list
            self.assertEqual(calls[0][0][1], test_input_file)  # First script
            self.assertEqual(calls[1][0][1], test_input_file)  # Second script

if __name__ == '__main__':
    unittest.main() 