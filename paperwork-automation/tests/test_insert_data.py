#!/usr/bin/env python3
"""
Unit tests for insert-data.py script.
Tests data extraction, transformation, and SQL generation functionality.
"""

import unittest
import pandas as pd
import tempfile
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the scripts directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the functions we want to test
try:
    from insert_data import (
        extract_date_from_filename,
        format_sql_value,
        transform_excel_data,
        generate_upsert_sql,
        process_excel
    )
except ImportError:
    # Try with hyphen-to-underscore conversion
    import importlib.util
    import os
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'insert-data.py')
    spec = importlib.util.spec_from_file_location("insert_data", script_path)
    insert_data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(insert_data)
    
    extract_date_from_filename = insert_data.extract_date_from_filename
    format_sql_value = insert_data.format_sql_value
    transform_excel_data = insert_data.transform_excel_data
    generate_upsert_sql = insert_data.generate_upsert_sql
    process_excel = insert_data.process_excel

class TestInsertData(unittest.TestCase):
    
    def test_extract_date_from_filename(self):
        """Test date extraction from various filename patterns."""
        # Valid patterns
        self.assertEqual(extract_date_from_filename('example_daily_data_2025_6_10.xlsx'), '2025-06-10')
        self.assertEqual(extract_date_from_filename('report_2024_12_31.xlsx'), '2024-12-31')
        self.assertEqual(extract_date_from_filename('data_2023_1_5.xlsx'), '2023-01-05')
        
        # Invalid patterns
        self.assertIsNone(extract_date_from_filename('invalid_filename.xlsx'))
        self.assertIsNone(extract_date_from_filename('no_date_here.xlsx'))
        self.assertIsNone(extract_date_from_filename(''))
    
    def test_format_sql_value(self):
        """Test SQL value formatting for different data types."""
        # Test None/NaN values
        self.assertEqual(format_sql_value(None), 'NULL')
        self.assertEqual(format_sql_value(pd.NA), 'NULL')
        self.assertEqual(format_sql_value(float('nan')), 'NULL')
        
        # Test numeric values
        self.assertEqual(format_sql_value(42), '42')
        self.assertEqual(format_sql_value(3.14), '3.14')
        self.assertEqual(format_sql_value(0), '0')
        
        # Test boolean values
        self.assertEqual(format_sql_value(True), 'True')
        self.assertEqual(format_sql_value(False), 'False')
        
        # Test string values
        self.assertEqual(format_sql_value('test'), "'test'")
        self.assertEqual(format_sql_value("O'Reilly"), "'O''Reilly'")  # SQL escape
        self.assertEqual(format_sql_value(''), "''")
        
        # Test datetime values
        test_date = datetime(2025, 6, 10)
        self.assertEqual(format_sql_value(test_date), "'2025-06-10'")
        
        test_timestamp = pd.Timestamp('2025-06-10')
        self.assertEqual(format_sql_value(test_timestamp), "'2025-06-10'")
    
    def test_transform_excel_data(self):
        """Test transformation of Excel data to database format."""
        # Create sample DataFrame
        sample_data = {
            '门店名称': ['加拿大一店', '加拿大二店', '未知店铺'],
            '日期': [20250610, 20250610, 20250610],
            '节假日': ['工作日', '节假日', '工作日'],
            '营业桌数': [50.0, 45.0, 40.0],
            '营业桌数(考核)': [48.0, 43.0, 38.0],
            '翻台率(考核)': [2.5, 2.8, 2.2],
            '营业收入(不含税)': [15000.0, 18000.0, 12000.0],
            '营业桌数(考核)(外卖)': [5.0, 8.0, 3.0],
            '就餐人数': [120, 150, 95],
            '优惠总金额(不含税)': [500.0, 800.0, 300.0]
        }
        df = pd.DataFrame(sample_data)
        
        result = transform_excel_data(df)
        
        # Should only process known stores (2 out of 3)
        self.assertEqual(len(result), 2)
        
        # Test first store data
        first_store = result[0]
        self.assertEqual(first_store['store_id'], 1)
        self.assertEqual(first_store['date'], '2025-06-10')
        self.assertEqual(first_store['month'], 6)
        self.assertEqual(first_store['is_holiday'], False)  # 工作日
        self.assertEqual(first_store['tables_served'], 50.0)
        self.assertEqual(first_store['customers'], 120)
        
        # Test second store data
        second_store = result[1]
        self.assertEqual(second_store['store_id'], 2)
        self.assertEqual(second_store['is_holiday'], True)  # 节假日
        self.assertEqual(second_store['revenue_tax_included'], 18000.0)
    
    def test_transform_excel_data_invalid_date(self):
        """Test handling of invalid date formats."""
        sample_data = {
            '门店名称': ['加拿大一店'],
            '日期': ['invalid_date'],
            '节假日': ['工作日'],
            '营业桌数': [50.0],
            '营业桌数(考核)': [48.0],
            '翻台率(考核)': [2.5],
            '营业收入(不含税)': [15000.0],
            '营业桌数(考核)(外卖)': [5.0],
            '就餐人数': [120],
            '优惠总金额(不含税)': [500.0]
        }
        df = pd.DataFrame(sample_data)
        
        with patch('builtins.print') as mock_print:
            result = transform_excel_data(df)
            # Should skip invalid date and return empty list
            self.assertEqual(len(result), 0)
            # Should print warning
            mock_print.assert_called()
    
    def test_generate_upsert_sql(self):
        """Test SQL UPSERT statement generation."""
        sample_data = [
            {
                'store_id': 1,
                'date': '2025-06-10',
                'month': 6,
                'is_holiday': False,
                'tables_served': 50.0,
                'tables_served_validated': 48.0,
                'turnover_rate': 2.5,
                'revenue_tax_included': 15000.0,
                'takeout_tables': 5.0,
                'customers': 120,
                'discount_total': 500.0
            }
        ]
        
        sql = generate_upsert_sql(sample_data, 'daily_report')
        
        # Check SQL structure
        self.assertIn('INSERT INTO daily_report', sql)
        self.assertIn('ON CONFLICT (store_id, date) DO UPDATE SET', sql)
        self.assertIn('VALUES', sql)
        
        # Check data values
        self.assertIn("1, '2025-06-10', 6, False", sql)
        self.assertIn('50.0', sql)
        self.assertIn('15000.0', sql)
    
    def test_generate_upsert_sql_empty_data(self):
        """Test SQL generation with empty data."""
        sql = generate_upsert_sql([], 'daily_report')
        self.assertEqual(sql, "")
    
    def test_generate_upsert_sql_with_nulls(self):
        """Test SQL generation with NULL values."""
        sample_data = [
            {
                'store_id': 1,
                'date': '2025-06-10',
                'month': 6,
                'is_holiday': True,
                'tables_served': None,
                'tables_served_validated': 48.0,
                'turnover_rate': None,
                'revenue_tax_included': 15000.0,
                'takeout_tables': 5.0,
                'customers': 120,
                'discount_total': None
            }
        ]
        
        sql = generate_upsert_sql(sample_data, 'daily_report')
        
        # Check NULL values are properly formatted
        self.assertIn('NULL', sql)
        self.assertIn('True', sql)  # Boolean value
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_process_excel_success(self, mock_exists, mock_read_excel):
        """Test successful Excel file processing."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock Excel data
        sample_df = pd.DataFrame({
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
        })
        mock_read_excel.return_value = sample_df
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = process_excel('test_file.xlsx', temp_path)
            self.assertTrue(result)
            
            # Check that SQL file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Check SQL content
            with open(temp_path, 'r') as f:
                content = f.read()
                self.assertIn('INSERT INTO daily_report', content)
                self.assertIn('ON CONFLICT', content)
        
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('os.path.exists')
    def test_process_excel_file_not_found(self, mock_exists):
        """Test handling of non-existent Excel file."""
        mock_exists.return_value = False
        
        with patch('builtins.print') as mock_print:
            result = process_excel('nonexistent.xlsx')
            self.assertFalse(result)
            mock_print.assert_called_with('Error: File not found: nonexistent.xlsx')
    
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_process_excel_exception_handling(self, mock_exists, mock_read_excel):
        """Test exception handling during Excel processing."""
        mock_exists.return_value = True
        mock_read_excel.side_effect = Exception("Test exception")
        
        with patch('builtins.print') as mock_print:
            result = process_excel('test_file.xlsx')
            self.assertFalse(result)
            # Should print error message
            mock_print.assert_called()

class TestDataValidation(unittest.TestCase):
    """Additional tests for data validation and edge cases."""
    
    def test_store_id_mapping(self):
        """Test that all expected stores are mapped correctly."""
        expected_stores = {
            '加拿大一店': 1,
            '加拿大二店': 2,
            '加拿大三店': 3,
            '加拿大四店': 4,
            '加拿大五店': 5,
            '加拿大六店': 6,
            '加拿大七店': 7
        }
        
        # Create test data with all stores
        sample_data = {
            '门店名称': list(expected_stores.keys()),
            '日期': [20250610] * len(expected_stores),
            '节假日': ['工作日'] * len(expected_stores),
            '营业桌数': [50.0] * len(expected_stores),
            '营业桌数(考核)': [48.0] * len(expected_stores),
            '翻台率(考核)': [2.5] * len(expected_stores),
            '营业收入(不含税)': [15000.0] * len(expected_stores),
            '营业桌数(考核)(外卖)': [5.0] * len(expected_stores),
            '就餐人数': [120] * len(expected_stores),
            '优惠总金额(不含税)': [500.0] * len(expected_stores)
        }
        df = pd.DataFrame(sample_data)
        
        result = transform_excel_data(df)
        
        # Should process all 7 stores
        self.assertEqual(len(result), 7)
        
        # Check store IDs are correct
        store_ids = [row['store_id'] for row in result]
        self.assertEqual(sorted(store_ids), list(range(1, 8)))
    
    def test_date_format_variations(self):
        """Test different date format inputs."""
        test_cases = [
            (20250610, '2025-06-10'),
            (20241231, '2024-12-31'),
            (20230101, '2023-01-01'),
            (20250205, '2025-02-05')  # Single digit month/day
        ]
        
        for date_input, expected_output in test_cases:
            sample_data = {
                '门店名称': ['加拿大一店'],
                '日期': [date_input],
                '节假日': ['工作日'],
                '营业桌数': [50.0],
                '营业桌数(考核)': [48.0],
                '翻台率(考核)': [2.5],
                '营业收入(不含税)': [15000.0],
                '营业桌数(考核)(外卖)': [5.0],
                '就餐人数': [120],
                '优惠总金额(不含税)': [500.0]
            }
            df = pd.DataFrame(sample_data)
            
            result = transform_excel_data(df)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['date'], expected_output)

if __name__ == '__main__':
    unittest.main() 