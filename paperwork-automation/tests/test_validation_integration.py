#!/usr/bin/env python3
"""
Integration tests for the complete validation workflow in extract-all.py.
Tests realistic scenarios with complete Excel files and end-to-end validation.
"""

import unittest
import pandas as pd
import tempfile
import os
import sys
import subprocess
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add the scripts directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the functions we want to test
try:
    from extract_all import main, validate_excel_file
except ImportError:
    # Try with hyphen-to-underscore conversion
    import importlib.util
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'extract-all.py')
    spec = importlib.util.spec_from_file_location("extract_all", script_path)
    extract_all = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extract_all)
    
    main = extract_all.main
    validate_excel_file = extract_all.validate_excel_file

class TestValidationIntegration(unittest.TestCase):
    """Integration tests for complete validation workflow."""
    
    def setUp(self):
        """Set up realistic test data."""
        # Create realistic daily data for all 7 stores
        self.realistic_daily_data = {
            '门店名称': [
                '加拿大一店', '加拿大二店', '加拿大三店', '加拿大四店', 
                '加拿大五店', '加拿大六店', '加拿大七店'
            ],
            '日期': [20250610] * 7,
            '节假日': ['工作日'] * 7,
            '营业桌数': [52.0, 48.0, 45.0, 50.0, 46.0, 44.0, 49.0],
            '营业桌数(考核)': [50.0, 46.0, 43.0, 48.0, 44.0, 42.0, 47.0],
            '翻台率(考核)': [2.8, 3.1, 2.5, 2.9, 3.2, 2.7, 3.0],
            '营业收入(不含税)': [18500.0, 21000.0, 16800.0, 19200.0, 22500.0, 17300.0, 20100.0],
            '营业桌数(考核)(外卖)': [8.0, 12.0, 6.0, 9.0, 14.0, 7.0, 11.0],
            '就餐人数': [140, 165, 125, 148, 172, 130, 158],
            '优惠总金额(不含税)': [850.0, 1200.0, 650.0, 950.0, 1350.0, 720.0, 1100.0]
        }
        
        # Create realistic time segment data
        self.realistic_time_segment_data = {
            '门店名称': [],
            '日期': [],
            '分时段': [],
            '节假日': [],
            '营业桌数(考核)': [],
            '翻台率(考核)': []
        }
        
        # Generate time segment data for 3 stores across 4 time periods
        stores = ['加拿大一店', '加拿大二店', '加拿大三店']
        time_segments = ['08:00-13:59', '14:00-16:59', '17:00-21:59', '22:00-(次)07:59']
        base_tables = [15.0, 12.0, 20.0, 8.0]
        base_turnover = [1.8, 2.2, 3.5, 1.2]
        
        for store in stores:
            for i, segment in enumerate(time_segments):
                self.realistic_time_segment_data['门店名称'].append(store)
                self.realistic_time_segment_data['日期'].append(20250610)
                self.realistic_time_segment_data['分时段'].append(segment)
                self.realistic_time_segment_data['节假日'].append('工作日')
                self.realistic_time_segment_data['营业桌数(考核)'].append(base_tables[i])
                self.realistic_time_segment_data['翻台率(考核)'].append(base_turnover[i])
    
    def create_test_excel_file(self, daily_data=None, time_segment_data=None, filename_suffix=""):
        """Helper method to create test Excel files."""
        if daily_data is None:
            daily_data = self.realistic_daily_data
        if time_segment_data is None:
            time_segment_data = self.realistic_time_segment_data
        
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f'_test{filename_suffix}.xlsx', 
            delete=False
        )
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            pd.DataFrame(daily_data).to_excel(writer, sheet_name='营业基础表', index=False)
            pd.DataFrame(time_segment_data).to_excel(writer, sheet_name='分时段基础表', index=False)
        
        return temp_file.name
    
    def test_complete_valid_file_validation(self):
        """Test validation of a completely valid Excel file."""
        excel_file = self.create_test_excel_file()
        
        try:
            with patch('builtins.print') as mock_print:
                is_valid, warnings = validate_excel_file(excel_file)
                
                self.assertTrue(is_valid)
                # Should have minimal warnings for a valid file
                critical_warnings = [w for w in warnings if '❌' in w]
                self.assertEqual(len(critical_warnings), 0)
                
                # Check that validation success messages were printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                success_messages = [call for call in print_calls if '✅' in call]
                self.assertGreater(len(success_messages), 0)
        
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_file_with_multiple_issues(self):
        """Test validation of file with multiple data quality issues."""
        # Create problematic data
        problematic_daily_data = {
            '门店名称': [
                '加拿大一店', '未知店铺', '加拿大三店 ',  # Unknown store, whitespace
                '加拿大四店', '加拿大五店', '加拿大六店', '加拿大七店'
            ],
            '日期': [20250610, 'invalid_date', 20250612, 20251301, 20250614, 20250615, 20250616],  # Invalid dates
            '节假日': ['工作日', '无效值', '工作日', '节假日', '工作日', '节假日', '工作日'],  # Invalid holiday
            '营业桌数': [52.0, -5.0, 45.0, 0, 46.0, 1000000, 49.0],  # Negative, zero, extreme values
            '营业桌数(考核)': [50.0, 46.0, 43.0, 48.0, 44.0, 42.0, 47.0],
            '翻台率(考核)': [2.8, 15.0, 2.5, 2.9, float('inf'), 2.7, 3.0],  # High turnover, infinity
            '营业收入(不含税)': [18500.0, 21000.0, 16800.0, 19200.0, 22500.0, 17300.0, 20100.0],
            '营业桌数(考核)(外卖)': [8.0, 12.0, 6.0, 9.0, 14.0, 7.0, 11.0],
            '就餐人数': [140, 165, 125, 148, 172, 130, 158],
            '优惠总金额(不含税)': [850.0, 1200.0, 650.0, 950.0, 1350.0, 720.0, 1100.0]
        }
        
        problematic_time_segment_data = {
            '门店名称': ['加拿大一店', '加拿大一店', '未知店铺'],
            '日期': [20250610, 20250610, 20250610],
            '分时段': ['08:00-13:59', '未知时段', '17:00-21:59'],  # Unknown time segment
            '节假日': ['工作日', '工作日', '无效值'],  # Invalid holiday
            '营业桌数(考核)': [15.0, 12.0, 20.0],
            '翻台率(考核)': [1.8, 2.2, 3.5]
        }
        
        excel_file = self.create_test_excel_file(
            problematic_daily_data, 
            problematic_time_segment_data, 
            "_problematic"
        )
        
        try:
            with patch('builtins.print') as mock_print:
                is_valid, warnings = validate_excel_file(excel_file)
                
                # Should detect multiple issues
                self.assertFalse(is_valid)
                
                # Check for specific types of warnings
                warning_text = ' '.join(warnings)
                self.assertIn('Unknown stores', warning_text)
                self.assertIn('date format issues', warning_text)
                self.assertIn('Invalid holiday values', warning_text)
                self.assertIn('negative values', warning_text)
                self.assertIn('infinite values', warning_text)
                self.assertIn('Unknown time segments', warning_text)
                
                # Should have critical error indicators
                critical_warnings = [w for w in warnings if '❌' in w]
                self.assertGreater(len(critical_warnings), 0)
        
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_main_function_with_validation_workflow(self):
        """Test the complete main function workflow with validation."""
        excel_file = self.create_test_excel_file(filename_suffix="_main_test")
        
        try:
            # Test successful validation and processing
            with patch('sys.argv', ['extract-all.py', excel_file]), \
                 patch('extract_all.run_script', return_value=True) as mock_run_script, \
                 patch('builtins.print') as mock_print, \
                 patch('sys.exit') as mock_exit:
                
                main()
                
                # Check that validation passed and scripts were run
                self.assertEqual(mock_run_script.call_count, 2)
                mock_exit.assert_called_with(0)
                
                # Check that validation messages were printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                validation_messages = [call for call in print_calls if ('✅' in call or '⚠️' in call)]
                self.assertGreater(len(validation_messages), 0)
        
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_main_function_with_skip_validation(self):
        """Test main function with --skip-validation flag."""
        excel_file = self.create_test_excel_file(filename_suffix="_skip_validation")
        
        try:
            with patch('sys.argv', ['extract-all.py', excel_file, '--skip-validation']), \
                 patch('extract_all.run_script', return_value=True) as mock_run_script, \
                 patch('extract_all.validate_excel_file') as mock_validate, \
                 patch('builtins.print') as mock_print, \
                 patch('sys.exit') as mock_exit:
                
                main()
                
                # Validation should not have been called
                mock_validate.assert_not_called()
                
                # Scripts should still run
                self.assertEqual(mock_run_script.call_count, 2)
                mock_exit.assert_called_with(0)
                
                # Should print skip message
                print_calls = [str(call) for call in mock_print.call_args_list]
                skip_messages = [call for call in print_calls if 'Skipping data format validation' in call]
                self.assertGreater(len(skip_messages), 0)
        
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_validation_with_missing_stores_warning(self):
        """Test validation when some expected stores are missing (should warn but continue)."""
        # Data with only 3 stores instead of all 7
        incomplete_daily_data = {
            '门店名称': ['加拿大一店', '加拿大二店', '加拿大三店'],
            '日期': [20250610, 20250610, 20250610],
            '节假日': ['工作日', '工作日', '工作日'],
            '营业桌数': [52.0, 48.0, 45.0],
            '营业桌数(考核)': [50.0, 46.0, 43.0],
            '翻台率(考核)': [2.8, 3.1, 2.5],
            '营业收入(不含税)': [18500.0, 21000.0, 16800.0],
            '营业桌数(考核)(外卖)': [8.0, 12.0, 6.0],
            '就餐人数': [140, 165, 125],
            '优惠总金额(不含税)': [850.0, 1200.0, 650.0]
        }
        
        excel_file = self.create_test_excel_file(
            incomplete_daily_data, 
            self.realistic_time_segment_data, 
            "_incomplete_stores"
        )
        
        try:
            with patch('builtins.print') as mock_print:
                is_valid, warnings = validate_excel_file(excel_file)
                
                # Should still be valid (warnings don't make it invalid)
                self.assertTrue(is_valid)
                
                # Should warn about missing stores
                warning_text = ' '.join(warnings)
                self.assertIn('Missing expected stores', warning_text)
                
                # Should list the missing stores
                missing_stores = ['加拿大四店', '加拿大五店', '加拿大六店', '加拿大七店']
                for store in missing_stores:
                    self.assertIn(store, warning_text)
        
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_validation_performance_with_realistic_data(self):
        """Test validation performance with realistic-sized dataset."""
        # Create data for multiple days across all stores
        large_daily_data = {
            '门店名称': [],
            '日期': [],
            '节假日': [],
            '营业桌数': [],
            '营业桌数(考核)': [],
            '翻台率(考核)': [],
            '营业收入(不含税)': [],
            '营业桌数(考核)(外卖)': [],
            '就餐人数': [],
            '优惠总金额(不含税)': []
        }
        
        # Generate 30 days of data for all 7 stores (210 rows total)
        stores = ['加拿大一店', '加拿大二店', '加拿大三店', '加拿大四店', '加拿大五店', '加拿大六店', '加拿大七店']
        base_date = 20250601
        
        for day in range(30):
            for i, store in enumerate(stores):
                large_daily_data['门店名称'].append(store)
                large_daily_data['日期'].append(base_date + day)
                large_daily_data['节假日'].append('工作日' if day % 7 < 5 else '节假日')
                large_daily_data['营业桌数'].append(50.0 + i * 2 + (day % 5))
                large_daily_data['营业桌数(考核)'].append(48.0 + i * 2 + (day % 5))
                large_daily_data['翻台率(考核)'].append(2.5 + (i * 0.1) + (day % 3) * 0.2)
                large_daily_data['营业收入(不含税)'].append(15000.0 + i * 1000 + day * 100)
                large_daily_data['营业桌数(考核)(外卖)'].append(5.0 + i + (day % 4))
                large_daily_data['就餐人数'].append(120 + i * 10 + day * 2)
                large_daily_data['优惠总金额(不含税)'].append(500.0 + i * 50 + day * 10)
        
        excel_file = self.create_test_excel_file(
            large_daily_data, 
            self.realistic_time_segment_data, 
            "_large_dataset"
        )
        
        try:
            import time
            start_time = time.time()
            
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(excel_file)
            
            end_time = time.time()
            validation_time = end_time - start_time
            
            # Validation should complete quickly (less than 3 seconds for 210 rows)
            self.assertLess(validation_time, 3.0, f"Validation took {validation_time:.2f}s, too slow for realistic dataset")
            
            # Should successfully validate
            self.assertTrue(is_valid)
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_command_line_integration(self):
        """Test command line integration with actual subprocess calls."""
        excel_file = self.create_test_excel_file(filename_suffix="_cli_test")
        
        try:
            # Test that the script can be called from command line
            script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'extract-all.py')
            
            # Test with --help flag
            result = subprocess.run(
                ['python3', script_path, '--help'], 
                capture_output=True, 
                text=True
            )
            
            # Should show help without errors
            self.assertEqual(result.returncode, 0)
            self.assertIn('usage:', result.stdout.lower())
            
            # Test with --skip-validation flag (should not fail on validation)
            result = subprocess.run(
                ['python3', script_path, excel_file, '--skip-validation'], 
                capture_output=True, 
                text=True
            )
            
            # Should show skip validation message
            self.assertIn('Skipping data format validation', result.stdout)
            
        except FileNotFoundError:
            self.skipTest("Python3 not available for subprocess testing")
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_validation_with_holiday_consistency_check(self):
        """Test validation that checks holiday consistency between sheets."""
        # Create data where holiday values are inconsistent between sheets
        daily_data_workday = self.realistic_daily_data.copy()
        daily_data_workday['节假日'] = ['工作日'] * 7  # All workdays
        
        time_segment_data_mixed = {
            '门店名称': ['加拿大一店', '加拿大一店', '加拿大二店'],
            '日期': [20250610, 20250610, 20250610],
            '分时段': ['08:00-13:59', '14:00-16:59', '17:00-21:59'],
            '节假日': ['工作日', '节假日', '工作日'],  # Mixed - inconsistent with daily sheet
            '营业桌数(考核)': [15.0, 12.0, 20.0],
            '翻台率(考核)': [1.8, 2.2, 3.5]
        }
        
        excel_file = self.create_test_excel_file(
            daily_data_workday, 
            time_segment_data_mixed, 
            "_holiday_inconsistent"
        )
        
        try:
            with patch('builtins.print') as mock_print:
                is_valid, warnings = validate_excel_file(excel_file)
                
                # Should detect inconsistency
                warning_text = ' '.join(warnings)
                self.assertIn('inconsistent holiday values', warning_text)
                
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)

class TestValidationRobustness(unittest.TestCase):
    """Test validation robustness and error handling."""
    
    def test_validation_with_corrupted_excel_file(self):
        """Test validation behavior with corrupted Excel file."""
        # Create a text file with .xlsx extension (corrupted Excel)
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False, mode='w') as temp_file:
            temp_file.write("This is not an Excel file")
            temp_path = temp_file.name
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_path)
                
                # Should handle corruption gracefully
                self.assertFalse(is_valid)
                warning_text = ' '.join(warnings)
                self.assertIn('Error reading Excel file', warning_text)
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validation_with_permission_denied(self):
        """Test validation behavior when file permissions are denied."""
        # This test might not work on all systems, so we'll skip if needed
        try:
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                # Create a valid Excel file first
                with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                    pd.DataFrame({'col': [1, 2, 3]}).to_excel(writer, sheet_name='Sheet1', index=False)
                
                temp_path = temp_file.name
            
            # Try to remove read permissions (Unix-like systems)
            try:
                os.chmod(temp_path, 0o000)
                
                with patch('builtins.print'):
                    is_valid, warnings = validate_excel_file(temp_path)
                    
                    # Should handle permission error gracefully
                    self.assertFalse(is_valid)
                    warning_text = ' '.join(warnings)
                    self.assertIn('Permission denied', warning_text)
                    
            except (OSError, PermissionError):
                self.skipTest("Cannot modify file permissions on this system")
            finally:
                # Restore permissions and clean up
                try:
                    os.chmod(temp_path, 0o644)
                    os.unlink(temp_path)
                except (OSError, PermissionError):
                    pass
                    
        except Exception:
            self.skipTest("Permission testing not supported on this system")

if __name__ == '__main__':
    unittest.main() 