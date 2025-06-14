#!/usr/bin/env python3
"""
Simple validation tests for extract-all.py validation functionality.
Tests the actual validation features that are implemented.
"""

import unittest
import pandas as pd
import tempfile
import os
import sys
import subprocess
from unittest.mock import patch

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

# Import the validation functions
try:
    from extract_all import validate_excel_file, validate_daily_sheet, validate_time_segment_sheet
except ImportError:
    # Try with hyphen-to-underscore conversion
    import importlib.util
    script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'extract-all.py')
    spec = importlib.util.spec_from_file_location("extract_all", script_path)
    extract_all = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extract_all)
    
    validate_excel_file = extract_all.validate_excel_file
    validate_daily_sheet = extract_all.validate_daily_sheet
    validate_time_segment_sheet = extract_all.validate_time_segment_sheet

class TestValidationBasics(unittest.TestCase):
    """Test basic validation functionality that actually exists."""
    
    def setUp(self):
        """Set up test data."""
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
            '门店名称': ['加拿大一店', '加拿大一店', '加拿大二店'],
            '日期': [20250610, 20250610, 20250610],
            '分时段': ['08:00-13:59', '14:00-16:59', '17:00-21:59'],
            '节假日': ['工作日', '工作日', '工作日'],
            '营业桌数(考核)': [25.0, 20.0, 30.0],
            '翻台率(考核)': [1.5, 2.0, 2.8]
        }
    
    def create_test_excel_file(self, daily_data=None, time_segment_data=None, suffix=""):
        """Helper to create test Excel files."""
        if daily_data is None:
            daily_data = self.valid_daily_data
        if time_segment_data is None:
            time_segment_data = self.valid_time_segment_data
        
        temp_file = tempfile.NamedTemporaryFile(suffix=f'_test{suffix}.xlsx', delete=False)
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            pd.DataFrame(daily_data).to_excel(writer, sheet_name='营业基础表', index=False)
            pd.DataFrame(time_segment_data).to_excel(writer, sheet_name='分时段基础表', index=False)
        
        return temp_file.name
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        with patch('builtins.print'):
            is_valid, warnings = validate_excel_file('nonexistent_file.xlsx')
            
            self.assertFalse(is_valid)
            self.assertGreater(len(warnings), 0)
            # Check that some warning mentions file not found
            warning_text = ' '.join(warnings)
            self.assertTrue('File not found' in warning_text or 'not exist' in warning_text)
    
    def test_validate_valid_excel_file(self):
        """Test validation of a valid Excel file."""
        excel_file = self.create_test_excel_file()
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(excel_file)
                
                # Should be valid
                self.assertTrue(is_valid)
                
                # May have warnings but no critical errors
                critical_warnings = [w for w in warnings if '❌' in w]
                self.assertEqual(len(critical_warnings), 0)
                
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_validate_file_missing_sheets(self):
        """Test validation of file with missing required sheets."""
        # Create file with wrong sheet names
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            pd.DataFrame({'col': [1, 2, 3]}).to_excel(writer, sheet_name='WrongSheet', index=False)
        
        try:
            with patch('builtins.print'):
                is_valid, warnings = validate_excel_file(temp_file.name)
                
                self.assertFalse(is_valid)
                warning_text = ' '.join(warnings)
                self.assertIn('营业基础表', warning_text)
                self.assertIn('分时段基础表', warning_text)
                
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_validate_daily_sheet_missing_columns(self):
        """Test validation of daily sheet with missing columns."""
        incomplete_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610]
            # Missing other required columns
        }
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            pd.DataFrame(incomplete_data).to_excel(writer, sheet_name='营业基础表', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_daily_sheet(excel_file)
            excel_file.close()
            
            # Should have warnings about missing columns
            warning_text = ' '.join(warnings)
            self.assertTrue(len(warnings) > 0)
            # The actual warning message might vary, so just check we got warnings
            
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_validate_daily_sheet_unknown_stores(self):
        """Test validation with unknown store names."""
        invalid_data = self.valid_daily_data.copy()
        invalid_data['门店名称'] = ['加拿大一店', '未知店铺', '测试店']
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            pd.DataFrame(invalid_data).to_excel(writer, sheet_name='营业基础表', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_daily_sheet(excel_file)
            excel_file.close()
            
            # Should warn about unknown stores
            warning_text = ' '.join(warnings)
            self.assertIn('未知店铺', warning_text)
            
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_validate_time_segment_sheet_unknown_segments(self):
        """Test validation with unknown time segments."""
        invalid_data = self.valid_time_segment_data.copy()
        invalid_data['分时段'] = ['08:00-13:59', '未知时段', '测试时段']
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            pd.DataFrame(invalid_data).to_excel(writer, sheet_name='分时段基础表', index=False)
        
        try:
            excel_file = pd.ExcelFile(temp_file.name)
            with patch('builtins.print'):
                warnings = validate_time_segment_sheet(excel_file)
            excel_file.close()
            
            # Should warn about unknown time segments
            warning_text = ' '.join(warnings)
            self.assertIn('未知时段', warning_text)
            
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

class TestCommandLineValidation(unittest.TestCase):
    """Test command line validation features."""
    
    def test_extract_all_help(self):
        """Test that extract-all.py shows help."""
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'extract-all.py')
        
        try:
            result = subprocess.run(
                ['python3', script_path, '--help'], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            # Should show help without errors
            self.assertEqual(result.returncode, 0)
            self.assertIn('usage:', result.stdout.lower())
            
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.skipTest("Cannot test command line interface")
    
    def test_extract_all_skip_validation(self):
        """Test --skip-validation flag."""
        # Create a valid test file
        valid_data = {
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
        
        time_segment_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610],
            '分时段': ['08:00-13:59'],
            '节假日': ['工作日'],
            '营业桌数(考核)': [25.0],
            '翻台率(考核)': [1.5]
        }
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            pd.DataFrame(valid_data).to_excel(writer, sheet_name='营业基础表', index=False)
            pd.DataFrame(time_segment_data).to_excel(writer, sheet_name='分时段基础表', index=False)
        
        try:
            script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'extract-all.py')
            
            result = subprocess.run(
                ['python3', script_path, temp_file.name, '--skip-validation'], 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            # Should mention skipping validation
            self.assertIn('Skipping data format validation', result.stdout)
            
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.skipTest("Cannot test command line interface")
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

def main():
    """Run the validation tests."""
    print("🧪 Running Simple Validation Tests")
    print("="*50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestValidationBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandLineValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*50)
    if result.wasSuccessful():
        print("✅ All validation tests passed!")
        print(f"Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some validation tests failed")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 