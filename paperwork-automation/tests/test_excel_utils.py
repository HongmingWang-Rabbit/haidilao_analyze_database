#!/usr/bin/env python3
"""
Comprehensive tests for lib/excel_utils.py
Tests all Excel processing utilities that were consolidated from 20+ files.
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from lib.excel_utils import (
    MATERIAL_DTYPE_SPEC, DISH_CODE_DTYPE_SPEC,
    suppress_excel_warnings, safe_read_excel, clean_dish_code, clean_material_number,
    validate_required_columns, clean_numeric_value, get_material_reading_dtype,
    get_dish_reading_dtype, safe_get_sheet_names, detect_sheet_structure,
    COMMON_SHEET_PATTERNS, standardize_column_names
)


class TestExcelUtilsConstants(unittest.TestCase):
    """Test Excel utility constants and specifications"""
    
    def test_material_dtype_spec(self):
        """Test material dtype specification contains critical fix"""
        self.assertIn('物料', MATERIAL_DTYPE_SPEC)
        self.assertEqual(MATERIAL_DTYPE_SPEC['物料'], str)
        
    def test_dish_code_dtype_spec(self):
        """Test dish code dtype specification"""
        self.assertIn('菜品编号', DISH_CODE_DTYPE_SPEC)
        self.assertIn('菜品代码', DISH_CODE_DTYPE_SPEC)
        self.assertEqual(DISH_CODE_DTYPE_SPEC['菜品编号'], str)
        
    def test_common_sheet_patterns(self):
        """Test common sheet structure patterns"""
        self.assertIn('daily_store_report', COMMON_SHEET_PATTERNS)
        self.assertIn('material_detail', COMMON_SHEET_PATTERNS)
        
        # Check that daily store report pattern has required columns
        daily_pattern = COMMON_SHEET_PATTERNS['daily_store_report']
        self.assertIn('门店名称', daily_pattern)
        self.assertIn('日期', daily_pattern)


class TestCleaningFunctions(unittest.TestCase):
    """Test data cleaning functions"""
    
    def test_clean_dish_code_success_cases(self):
        """Test clean_dish_code with valid inputs"""
        # Test float with .0 suffix removal
        self.assertEqual(clean_dish_code(90001690.0), "90001690")
        
        # Test string input
        self.assertEqual(clean_dish_code("90001691"), "90001691")
        
        # Test integer input
        self.assertEqual(clean_dish_code(90001692), "90001692")
        
        # Test string with spaces
        self.assertEqual(clean_dish_code("  90001693  "), "90001693")
        
    def test_clean_dish_code_edge_cases(self):
        """Test clean_dish_code with edge cases"""
        # Test NaN input
        self.assertIsNone(clean_dish_code(np.nan))
        
        # Test None input
        self.assertIsNone(clean_dish_code(None))
        
        # Test dash input
        self.assertIsNone(clean_dish_code("-"))
        
        # Test empty string
        self.assertIsNone(clean_dish_code(""))
        self.assertIsNone(clean_dish_code("   "))
        
    def test_clean_material_number_success_cases(self):
        """Test clean_material_number with valid inputs"""
        # Test critical case: leading zeros removal
        self.assertEqual(clean_material_number("000000000001500680"), "1500680")
        
        # Test float with .0 suffix
        self.assertEqual(clean_material_number(1500681.0), "1500681")
        
        # Test string input
        self.assertEqual(clean_material_number("1500682"), "1500682")
        
        # Test mixed leading zeros and float
        self.assertEqual(clean_material_number("000001500683.0"), "1500683")
        
    def test_clean_material_number_edge_cases(self):
        """Test clean_material_number with edge cases"""
        # Test NaN input
        self.assertIsNone(clean_material_number(np.nan))
        
        # Test None input
        self.assertIsNone(clean_material_number(None))
        
        # Test all zeros
        self.assertEqual(clean_material_number("000000000000"), "0")
        
        # Test single zero
        self.assertEqual(clean_material_number("0"), "0")
        
    def test_clean_numeric_value_success_cases(self):
        """Test clean_numeric_value with valid inputs"""
        # Test normal number
        self.assertEqual(clean_numeric_value(123.45), 123.45)
        
        # Test string number with commas
        self.assertEqual(clean_numeric_value("1,234.56"), 1234.56)
        
        # Test string number with spaces
        self.assertEqual(clean_numeric_value("  789.12  "), 789.12)
        
        # Test integer
        self.assertEqual(clean_numeric_value(100), 100.0)
        
    def test_clean_numeric_value_edge_cases(self):
        """Test clean_numeric_value with edge cases"""
        # Test NaN input
        self.assertEqual(clean_numeric_value(np.nan), 0.0)
        
        # Test None input
        self.assertEqual(clean_numeric_value(None), 0.0)
        
        # Test empty string
        self.assertEqual(clean_numeric_value(""), 0.0)
        
        # Test dash
        self.assertEqual(clean_numeric_value("-"), 0.0)
        
        # Test invalid string
        self.assertEqual(clean_numeric_value("invalid"), 0.0)
        
        # Test custom default
        self.assertEqual(clean_numeric_value("invalid", default=99.0), 99.0)


class TestExcelReading(unittest.TestCase):
    """Test Excel file reading functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def create_test_excel(self, filename, data, sheet_name='Sheet1'):
        """Create a test Excel file"""
        file_path = Path(self.temp_dir) / filename
        df = pd.DataFrame(data)
        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        return file_path
        
    def test_safe_read_excel_success(self):
        """Test safe_read_excel with valid file"""
        test_data = {
            '物料': ['000000000001500680', '000000000001500681'],
            '物料描述': ['Material A', 'Material B'],
            '数量': [10, 20]
        }
        
        file_path = self.create_test_excel('test_materials.xlsx', test_data)
        
        # Test reading with material dtype specification
        df = safe_read_excel(file_path, dtype_spec=get_material_reading_dtype())
        
        self.assertEqual(len(df), 2)
        self.assertIn('物料', df.columns)
        
        # Critical test: material numbers should be strings
        self.assertIsInstance(df['物料'].iloc[0], str)
        self.assertEqual(df['物料'].iloc[0], '000000000001500680')
        
    def test_safe_read_excel_file_not_found(self):
        """Test safe_read_excel with non-existent file"""
        with self.assertRaises(FileNotFoundError):
            safe_read_excel('/nonexistent/file.xlsx')
            
    def test_safe_read_excel_with_sheet_name(self):
        """Test safe_read_excel with specific sheet name"""
        test_data = {'col1': [1, 2], 'col2': [3, 4]}
        file_path = self.create_test_excel('test_sheet.xlsx', test_data, 'TestSheet')
        
        df = safe_read_excel(file_path, sheet_name='TestSheet')
        self.assertEqual(len(df), 2)
        
    def test_safe_get_sheet_names(self):
        """Test safe_get_sheet_names function"""
        test_data = {'col1': [1, 2]}
        file_path = self.create_test_excel('test_sheets.xlsx', test_data, 'CustomSheet')
        
        sheet_names = safe_get_sheet_names(file_path)
        self.assertEqual(sheet_names, ['CustomSheet'])
        
    def test_safe_get_sheet_names_invalid_file(self):
        """Test safe_get_sheet_names with invalid file"""
        sheet_names = safe_get_sheet_names('/nonexistent/file.xlsx')
        self.assertEqual(sheet_names, [])


class TestValidationFunctions(unittest.TestCase):
    """Test data validation functions"""
    
    def test_validate_required_columns_success(self):
        """Test validate_required_columns with valid DataFrame"""
        df = pd.DataFrame({
            '门店名称': ['店1', '店2'],
            '日期': ['20250101', '20250102'],
            '营业收入(不含税)': [1000, 2000]
        })
        
        required_columns = ['门店名称', '日期', '营业收入(不含税)']
        result = validate_required_columns(df, required_columns, "test sheet")
        self.assertTrue(result)
        
    def test_validate_required_columns_missing(self):
        """Test validate_required_columns with missing columns"""
        df = pd.DataFrame({
            '门店名称': ['店1', '店2'],
            '日期': ['20250101', '20250102']
        })
        
        required_columns = ['门店名称', '日期', '营业收入(不含税)']
        
        with self.assertRaises(ValueError) as context:
            validate_required_columns(df, required_columns, "test sheet")
            
        self.assertIn('Missing required columns', str(context.exception))
        self.assertIn('营业收入(不含税)', str(context.exception))
        
    def test_detect_sheet_structure(self):
        """Test detect_sheet_structure function"""
        # Test daily store report detection
        daily_df = pd.DataFrame({
            '门店名称': ['店1'],
            '日期': ['20250101'],  
            '营业收入(不含税)': [1000],
            '营业桌数': [50]
        })
        
        detected_type = detect_sheet_structure(daily_df, COMMON_SHEET_PATTERNS)
        self.assertEqual(detected_type, 'daily_store_report')
        
        # Test material detail detection
        material_df = pd.DataFrame({
            '物料': ['1500680'],
            '物料描述': ['Material A'],
            '数量': [10],
            '单价': [5.5]
        })
        
        detected_type = detect_sheet_structure(material_df, COMMON_SHEET_PATTERNS)
        self.assertEqual(detected_type, 'material_detail')
        
        # Test unknown structure
        unknown_df = pd.DataFrame({
            'unknown_col1': [1],
            'unknown_col2': [2]
        })
        
        detected_type = detect_sheet_structure(unknown_df, COMMON_SHEET_PATTERNS)
        self.assertIsNone(detected_type)


class TestConfigurationFunctions(unittest.TestCase):
    """Test configuration and utility functions"""
    
    def test_get_material_reading_dtype(self):
        """Test get_material_reading_dtype returns correct specification"""
        dtype_spec = get_material_reading_dtype()
        self.assertIsInstance(dtype_spec, dict)
        self.assertIn('物料', dtype_spec)
        self.assertEqual(dtype_spec['物料'], str)
        
    def test_get_dish_reading_dtype(self):
        """Test get_dish_reading_dtype returns correct specification"""
        dtype_spec = get_dish_reading_dtype()
        self.assertIsInstance(dtype_spec, dict)
        self.assertIn('菜品编号', dtype_spec)
        self.assertIn('菜品代码', dtype_spec)
        
    def test_standardize_column_names(self):
        """Test standardize_column_names function"""
        df = pd.DataFrame({
            '門店名稱': ['店1'],  # Traditional Chinese
            '營業收入': [1000],   # Traditional Chinese
            '菜品編號': ['123'],   # Traditional Chinese
            'normal_col': ['data']
        })
        
        standardized_df = standardize_column_names(df)
        
        # Check that traditional Chinese was converted to simplified
        self.assertIn('门店名称', standardized_df.columns)
        self.assertIn('营业收入(不含税)', standardized_df.columns)
        self.assertIn('菜品编号', standardized_df.columns)
        self.assertIn('normal_col', standardized_df.columns)
        
        # Check that data is preserved
        self.assertEqual(standardized_df['门店名称'].iloc[0], '店1')
        
    def test_standardize_column_names_with_custom_mapping(self):
        """Test standardize_column_names with custom mapping"""
        df = pd.DataFrame({
            'old_name': [1],
            'another_old': [2]
        })
        
        custom_mapping = {
            'old_name': 'new_name',
            'another_old': 'another_new'
        }
        
        standardized_df = standardize_column_names(df, custom_mapping)
        
        self.assertIn('new_name', standardized_df.columns)
        self.assertIn('another_new', standardized_df.columns)
        self.assertNotIn('old_name', standardized_df.columns)


class TestWarningsSuppression(unittest.TestCase):
    """Test warnings suppression functionality"""
    
    @patch('warnings.filterwarnings')
    def test_suppress_excel_warnings(self, mock_filterwarnings):
        """Test suppress_excel_warnings calls warnings.filterwarnings"""
        suppress_excel_warnings()
        
        # Verify that filterwarnings was called
        mock_filterwarnings.assert_called_once_with(
            'ignore', category=UserWarning, module='openpyxl'
        )


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios that combine multiple functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_material_processing_workflow(self):
        """Test complete material data processing workflow"""
        # Create test data that simulates the critical material number precision issue
        test_data = {
            '物料': ['000000000001500680', '000000000001500681.0', '1500682'],
            '物料描述': ['锅底材料A', '荤菜材料B', '素菜材料C'], 
            '数量': ['10.5', '20', 'invalid'],
            '单价': [15.50, 25.00, 30.00]
        }
        
        # Create Excel file
        file_path = Path(self.temp_dir) / 'test_materials.xlsx'
        df = pd.DataFrame(test_data)
        df.to_excel(file_path, index=False)
        
        # Read with proper dtype specification
        dtype_spec = get_material_reading_dtype()
        df_read = safe_read_excel(file_path, dtype_spec=dtype_spec)
        
        # Validate required columns
        required_columns = ['物料', '物料描述', '数量']
        validate_required_columns(df_read, required_columns, "material test")
        
        # Clean the data
        df_read['物料_cleaned'] = df_read['物料'].apply(clean_material_number)
        df_read['数量_cleaned'] = df_read['数量'].apply(clean_numeric_value)
        
        # Verify results
        self.assertEqual(df_read['物料_cleaned'].iloc[0], '1500680')  # Leading zeros removed
        self.assertEqual(df_read['物料_cleaned'].iloc[1], '1500681')  # .0 suffix removed
        self.assertEqual(df_read['物料_cleaned'].iloc[2], '1500682')  # Already clean
        
        self.assertEqual(df_read['数量_cleaned'].iloc[0], 10.5)      # String to float
        self.assertEqual(df_read['数量_cleaned'].iloc[1], 20.0)      # Clean conversion
        self.assertEqual(df_read['数量_cleaned'].iloc[2], 0.0)       # Invalid to default
        
    def test_dish_processing_workflow(self):
        """Test complete dish data processing workflow"""
        # Create test data with float dish codes (common Excel conversion issue)
        test_data = {
            '菜品编号': [90001690.0, 90001691.0, '90001692'],
            '菜品名称': ['麻辣锅底', '清汤锅底', '鸳鸯锅底'],
            '数量': [5, 3, 8],
            '单价': [28.00, 25.00, 30.00]
        }
        
        # Create Excel file
        file_path = Path(self.temp_dir) / 'test_dishes.xlsx'
        df = pd.DataFrame(test_data)
        df.to_excel(file_path, index=False)
        
        # Read with proper dtype specification
        dtype_spec = get_dish_reading_dtype()
        df_read = safe_read_excel(file_path, dtype_spec=dtype_spec)
        
        # Clean dish codes
        df_read['菜品编号_cleaned'] = df_read['菜品编号'].apply(clean_dish_code)
        
        # Verify results - all should be clean strings without .0 suffix
        self.assertEqual(df_read['菜品编号_cleaned'].iloc[0], '90001690')
        self.assertEqual(df_read['菜品编号_cleaned'].iloc[1], '90001691') 
        self.assertEqual(df_read['菜品编号_cleaned'].iloc[2], '90001692')
        
        # Verify all are strings (not floats)
        for cleaned_code in df_read['菜品编号_cleaned']:
            self.assertIsInstance(cleaned_code, str)


if __name__ == '__main__':
    # Run all tests with detailed output
    unittest.main(verbosity=2)