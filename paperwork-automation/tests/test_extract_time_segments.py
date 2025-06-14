#!/usr/bin/env python3
"""
Unit tests for extract-time-segments.py script.
Tests time segment data extraction, transformation, and SQL generation functionality.
"""

import unittest
import pandas as pd
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add the scripts directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import the functions we want to test
try:
    from extract_time_segments import (
        transform_time_segment_data,
        generate_upsert_sql
    )
except ImportError:
    # Try with hyphen-to-underscore conversion
    import importlib.util
    import os
    script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'extract-time-segments.py')
    spec = importlib.util.spec_from_file_location("extract_time_segments", script_path)
    extract_time_segments = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extract_time_segments)
    
    transform_time_segment_data = extract_time_segments.transform_time_segment_data
    generate_upsert_sql = extract_time_segments.generate_upsert_sql

class TestExtractTimeSegments(unittest.TestCase):
    
    def test_transform_time_segment_data(self):
        """Test transformation of time segment Excel data to database format."""
        # Create sample DataFrame
        sample_data = {
            '门店名称': ['加拿大一店', '加拿大二店', '加拿大一店', '未知店铺'],
            '日期': [20250610, 20250610, 20250610, 20250610],
            '分时段': ['08:00-13:59', '14:00-16:59', '17:00-21:59', '08:00-13:59'],
            '节假日': ['工作日', '节假日', '工作日', '工作日'],
            '营业桌数(考核)': [25.0, 20.0, 30.0, 15.0],
            '翻台率(考核)': [1.5, 2.0, 2.8, 1.2]
        }
        df = pd.DataFrame(sample_data)
        
        result = transform_time_segment_data(df)
        
        # Should only process known stores (3 out of 4)
        self.assertEqual(len(result), 3)
        
        # Test first store data
        first_segment = result[0]
        self.assertEqual(first_segment['store_id'], 1)
        self.assertEqual(first_segment['date'], '2025-06-10')
        self.assertEqual(first_segment['time_segment_id'], 1)  # 08:00-13:59
        self.assertEqual(first_segment['is_holiday'], False)  # 工作日
        self.assertEqual(first_segment['tables_served_validated'], 25.0)
        self.assertEqual(first_segment['turnover_rate'], 1.5)
        
        # Test second store data
        second_segment = result[1]
        self.assertEqual(second_segment['store_id'], 2)
        self.assertEqual(second_segment['time_segment_id'], 2)  # 14:00-16:59
        self.assertEqual(second_segment['is_holiday'], True)  # 节假日
        
        # Test third segment (same store, different time)
        third_segment = result[2]
        self.assertEqual(third_segment['store_id'], 1)
        self.assertEqual(third_segment['time_segment_id'], 3)  # 17:00-21:59
    
    def test_transform_time_segment_data_unknown_store(self):
        """Test handling of unknown store names."""
        sample_data = {
            '门店名称': ['未知店铺'],
            '日期': [20250610],
            '分时段': ['08:00-13:59'],
            '节假日': ['工作日'],
            '营业桌数(考核)': [25.0],
            '翻台率(考核)': [1.5]
        }
        df = pd.DataFrame(sample_data)
        
        result = transform_time_segment_data(df)
        
        # Should skip unknown store and return empty list
        self.assertEqual(len(result), 0)
    
    def test_transform_time_segment_data_unknown_time_segment(self):
        """Test handling of unknown time segment labels."""
        sample_data = {
            '门店名称': ['加拿大一店'],
            '日期': [20250610],
            '分时段': ['未知时段'],
            '节假日': ['工作日'],
            '营业桌数(考核)': [25.0],
            '翻台率(考核)': [1.5]
        }
        df = pd.DataFrame(sample_data)
        
        with patch('builtins.print') as mock_print:
            result = transform_time_segment_data(df)
            # Should skip unknown time segment and return empty list
            self.assertEqual(len(result), 0)
            # Should print warning
            mock_print.assert_called()
    
    def test_transform_time_segment_data_invalid_date(self):
        """Test handling of invalid date formats."""
        sample_data = {
            '门店名称': ['加拿大一店'],
            '日期': ['invalid_date'],
            '分时段': ['08:00-13:59'],
            '节假日': ['工作日'],
            '营业桌数(考核)': [25.0],
            '翻台率(考核)': [1.5]
        }
        df = pd.DataFrame(sample_data)
        
        with patch('builtins.print') as mock_print:
            result = transform_time_segment_data(df)
            # Should skip invalid date and return empty list
            self.assertEqual(len(result), 0)
            # Should print warning
            mock_print.assert_called()
    
    def test_time_segment_id_mapping(self):
        """Test that all time segments are mapped correctly."""
        expected_segments = {
            '08:00-13:59': 1,
            '14:00-16:59': 2,
            '17:00-21:59': 3,
            '22:00-(次)07:59': 4
        }
        
        # Create test data with all time segments
        sample_data = {
            '门店名称': ['加拿大一店'] * len(expected_segments),
            '日期': [20250610] * len(expected_segments),
            '分时段': list(expected_segments.keys()),
            '节假日': ['工作日'] * len(expected_segments),
            '营业桌数(考核)': [25.0] * len(expected_segments),
            '翻台率(考核)': [1.5] * len(expected_segments)
        }
        df = pd.DataFrame(sample_data)
        
        result = transform_time_segment_data(df)
        
        # Should process all 4 time segments
        self.assertEqual(len(result), 4)
        
        # Check time segment IDs are correct
        time_segment_ids = [row['time_segment_id'] for row in result]
        self.assertEqual(sorted(time_segment_ids), list(range(1, 5)))
    
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
            '分时段': ['08:00-13:59'] * len(expected_stores),
            '节假日': ['工作日'] * len(expected_stores),
            '营业桌数(考核)': [25.0] * len(expected_stores),
            '翻台率(考核)': [1.5] * len(expected_stores)
        }
        df = pd.DataFrame(sample_data)
        
        result = transform_time_segment_data(df)
        
        # Should process all 7 stores
        self.assertEqual(len(result), 7)
        
        # Check store IDs are correct
        store_ids = [row['store_id'] for row in result]
        self.assertEqual(sorted(store_ids), list(range(1, 8)))
    
    def test_generate_upsert_sql(self):
        """Test SQL UPSERT statement generation for time segments."""
        sample_data = [
            {
                'store_id': 1,
                'date': '2025-06-10',
                'time_segment_id': 1,
                'is_holiday': False,
                'tables_served_validated': 25.0,
                'turnover_rate': 1.5
            }
        ]
        
        sql = generate_upsert_sql(sample_data, 'store_time_report')
        
        # Check SQL structure
        self.assertIn('INSERT INTO store_time_report', sql)
        self.assertIn('ON CONFLICT (store_id, date, time_segment_id) DO UPDATE SET', sql)
        self.assertIn('VALUES', sql)
        
        # Check data values
        self.assertIn("1, '2025-06-10', 1, False", sql)
        self.assertIn('25.0', sql)
        self.assertIn('1.5', sql)
    
    def test_generate_upsert_sql_empty_data(self):
        """Test SQL generation with empty data."""
        sql = generate_upsert_sql([], 'store_time_report')
        self.assertEqual(sql, "")
    
    def test_generate_upsert_sql_with_nulls(self):
        """Test SQL generation with NULL values."""
        sample_data = [
            {
                'store_id': 1,
                'date': '2025-06-10',
                'time_segment_id': 1,
                'is_holiday': True,
                'tables_served_validated': None,
                'turnover_rate': 1.5
            }
        ]
        
        sql = generate_upsert_sql(sample_data, 'store_time_report')
        
        # Check NULL values are properly formatted
        self.assertIn('NULL', sql)
        self.assertIn('True', sql)  # Boolean value
    
    def test_generate_upsert_sql_multiple_records(self):
        """Test SQL generation with multiple records."""
        sample_data = [
            {
                'store_id': 1,
                'date': '2025-06-10',
                'time_segment_id': 1,
                'is_holiday': False,
                'tables_served_validated': 25.0,
                'turnover_rate': 1.5
            },
            {
                'store_id': 1,
                'date': '2025-06-10',
                'time_segment_id': 2,
                'is_holiday': False,
                'tables_served_validated': 20.0,
                'turnover_rate': 2.0
            },
            {
                'store_id': 2,
                'date': '2025-06-10',
                'time_segment_id': 1,
                'is_holiday': True,
                'tables_served_validated': 30.0,
                'turnover_rate': 1.8
            }
        ]
        
        sql = generate_upsert_sql(sample_data, 'store_time_report')
        
        # Check that all records are included
        self.assertEqual(sql.count('(1,'), 2)  # Two records for store 1
        self.assertEqual(sql.count('(2,'), 1)  # One record for store 2
        
        # Check different time segments
        self.assertIn("1, '2025-06-10', 1,", sql)  # Store 1, segment 1
        self.assertIn("1, '2025-06-10', 2,", sql)  # Store 1, segment 2
        self.assertIn("2, '2025-06-10', 1,", sql)  # Store 2, segment 1

class TestDataValidation(unittest.TestCase):
    """Additional tests for data validation and edge cases."""
    
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
                '分时段': ['08:00-13:59'],
                '节假日': ['工作日'],
                '营业桌数(考核)': [25.0],
                '翻台率(考核)': [1.5]
            }
            df = pd.DataFrame(sample_data)
            
            result = transform_time_segment_data(df)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['date'], expected_output)
    
    def test_holiday_detection(self):
        """Test holiday vs workday detection."""
        test_cases = [
            ('工作日', False),
            ('节假日', True)
        ]
        
        for holiday_input, expected_is_holiday in test_cases:
            sample_data = {
                '门店名称': ['加拿大一店'],
                '日期': [20250610],
                '分时段': ['08:00-13:59'],
                '节假日': [holiday_input],
                '营业桌数(考核)': [25.0],
                '翻台率(考核)': [1.5]
            }
            df = pd.DataFrame(sample_data)
            
            result = transform_time_segment_data(df)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['is_holiday'], expected_is_holiday)
    
    def test_numeric_data_handling(self):
        """Test handling of numeric data with NaN values."""
        sample_data = {
            '门店名称': ['加拿大一店', '加拿大二店'],
            '日期': [20250610, 20250610],
            '分时段': ['08:00-13:59', '14:00-16:59'],
            '节假日': ['工作日', '工作日'],
            '营业桌数(考核)': [25.0, None],  # One valid, one None
            '翻台率(考核)': [None, 2.0]  # One None, one valid
        }
        df = pd.DataFrame(sample_data)
        
        result = transform_time_segment_data(df)
        
        # Should process both records
        self.assertEqual(len(result), 2)
        
        # Check None values are handled correctly
        self.assertEqual(result[0]['tables_served_validated'], 25.0)
        self.assertIsNone(result[0]['turnover_rate'])
        
        self.assertIsNone(result[1]['tables_served_validated'])
        self.assertEqual(result[1]['turnover_rate'], 2.0)

if __name__ == '__main__':
    unittest.main() 