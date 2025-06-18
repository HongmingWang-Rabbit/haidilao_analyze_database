#!/usr/bin/env python3
"""
Comprehensive tests for lib/data_extraction.py module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, date

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from lib.data_extraction import (
    extract_daily_reports, extract_time_segments,
    transform_daily_report_data, transform_time_segment_data
)


class TestDataExtractionFunctions(unittest.TestCase):
    """Test cases for data extraction functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Sample daily report data
        self.daily_report_data = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02', '2025-06-03'],
            'Store': ['加拿大一店', '加拿大二店', '加拿大三店'],
            'Revenue (Tax Not Included)': [25000.50, 18000.25, 22000.75],
            'Tables Served (Validated)': [180.5, 145.0, 165.5],
            'Customers': [520, 420, 480],
            'Turnover Rate': [3.8, 3.2, 3.5],
            'Takeout Tables': [12.5, 8.5, 10.0],
            'Tables Served': [185.0, 148.0, 170.0],
            'Holiday': ['否', '否', '是']
        })
        
        # Sample time segment data
        self.time_segment_data = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-01', '2025-06-02'],
            'Store': ['加拿大一店', '加拿大二店', '加拿大一店'],
            'Time Segment': ['11:00-14:00', '11:00-14:00', '11:00-14:00'],
            'Revenue': [8000.0, 6000.0, 7500.0],
            'Tables': [60.0, 45.0, 55.0],
            'Customers': [180, 140, 165],
            'Holiday': ['否', '否', '否']
        })

    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_daily_reports_success(self, mock_file, mock_makedirs, mock_read_excel):
        """Test successful daily reports extraction"""
        mock_read_excel.return_value = self.daily_report_data
        
        result = extract_daily_reports('test_file.xlsx', 'output_dir')
        
        self.assertTrue(result)
        mock_read_excel.assert_called_once_with('test_file.xlsx', sheet_name='Daily Report')
        mock_makedirs.assert_called_once_with('output_dir', exist_ok=True)
        mock_file.assert_called()

    @patch('lib.data_extraction.pd.read_excel')
    def test_extract_daily_reports_file_not_found(self, mock_read_excel):
        """Test daily reports extraction with file not found"""
        mock_read_excel.side_effect = FileNotFoundError("File not found")
        
        result = extract_daily_reports('nonexistent.xlsx', 'output_dir')
        
        self.assertFalse(result)

    @patch('lib.data_extraction.pd.read_excel')
    def test_extract_daily_reports_invalid_excel(self, mock_read_excel):
        """Test daily reports extraction with invalid Excel file"""
        mock_read_excel.side_effect = Exception("Invalid Excel file")
        
        result = extract_daily_reports('invalid.xlsx', 'output_dir')
        
        self.assertFalse(result)

    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_daily_reports_empty_data(self, mock_file, mock_makedirs, mock_read_excel):
        """Test daily reports extraction with empty data"""
        empty_df = pd.DataFrame()
        mock_read_excel.return_value = empty_df
        
        result = extract_daily_reports('test_file.xlsx', 'output_dir')
        
        self.assertTrue(result)  # Should still succeed but with empty data

    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_daily_reports_missing_columns(self, mock_file, mock_makedirs, mock_read_excel):
        """Test daily reports extraction with missing columns"""
        incomplete_df = pd.DataFrame({
            'Date': ['2025-06-01'],
            'Store': ['加拿大一店']
            # Missing other required columns
        })
        mock_read_excel.return_value = incomplete_df
        
        result = extract_daily_reports('test_file.xlsx', 'output_dir')
        
        # Should handle missing columns gracefully
        self.assertTrue(result)

    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extract_time_segments_success(self, mock_file, mock_makedirs, mock_read_excel):
        """Test successful time segments extraction"""
        mock_read_excel.return_value = self.time_segment_data
        
        result = extract_time_segments('test_file.xlsx', 'output_dir')
        
        self.assertTrue(result)
        mock_read_excel.assert_called_once_with('test_file.xlsx', sheet_name='Time Segment')
        mock_makedirs.assert_called_once_with('output_dir', exist_ok=True)
        mock_file.assert_called()

    @patch('lib.data_extraction.pd.read_excel')
    def test_extract_time_segments_file_error(self, mock_read_excel):
        """Test time segments extraction with file error"""
        mock_read_excel.side_effect = Exception("File error")
        
        result = extract_time_segments('error_file.xlsx', 'output_dir')
        
        self.assertFalse(result)

    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    def test_extract_time_segments_makedirs_error(self, mock_makedirs, mock_read_excel):
        """Test time segments extraction with makedirs error"""
        mock_read_excel.return_value = self.time_segment_data
        mock_makedirs.side_effect = OSError("Permission denied")
        
        result = extract_time_segments('test_file.xlsx', 'output_dir')
        
        self.assertFalse(result)

    def test_transform_daily_report_data_basic(self):
        """Test basic daily report data transformation"""
        result = transform_daily_report_data(self.daily_report_data)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        
        # Check first record
        first_record = result[0]
        self.assertIn('date', first_record)
        self.assertIn('store_name', first_record)
        self.assertIn('revenue_tax_not_included', first_record)
        self.assertIn('tables_served_validated', first_record)
        self.assertIn('customers', first_record)
        self.assertIn('turnover_rate', first_record)
        self.assertIn('is_holiday', first_record)

    def test_transform_daily_report_data_empty(self):
        """Test daily report data transformation with empty DataFrame"""
        empty_df = pd.DataFrame()
        result = transform_daily_report_data(empty_df)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_transform_daily_report_data_none(self):
        """Test daily report data transformation with None input"""
        result = transform_daily_report_data(None)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_transform_daily_report_data_missing_columns(self):
        """Test daily report data transformation with missing columns"""
        incomplete_df = pd.DataFrame({
            'Date': ['2025-06-01'],
            'Store': ['加拿大一店']
            # Missing other columns
        })
        
        result = transform_daily_report_data(incomplete_df)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        # Should have default values for missing columns
        record = result[0]
        self.assertEqual(record['revenue_tax_not_included'], 0.0)
        self.assertEqual(record['tables_served_validated'], 0.0)
        self.assertEqual(record['customers'], 0)

    def test_transform_daily_report_data_data_types(self):
        """Test daily report data transformation with various data types"""
        mixed_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02'],
            'Store': ['加拿大一店', '加拿大二店'],
            'Revenue (Tax Not Included)': ['25000.50', 18000.25],  # Mixed string/float
            'Tables Served (Validated)': [180.5, '145.0'],  # Mixed float/string
            'Customers': ['520', 420],  # Mixed string/int
            'Turnover Rate': [3.8, '3.2'],  # Mixed float/string
            'Holiday': ['否', 'No']  # Different holiday formats
        })
        
        result = transform_daily_report_data(mixed_df)
        
        self.assertEqual(len(result), 2)
        
        # Check data type conversions
        first_record = result[0]
        self.assertIsInstance(first_record['revenue_tax_not_included'], float)
        self.assertIsInstance(first_record['tables_served_validated'], float)
        self.assertIsInstance(first_record['customers'], int)
        self.assertIsInstance(first_record['turnover_rate'], float)
        self.assertIsInstance(first_record['is_holiday'], bool)

    def test_transform_daily_report_data_nan_values(self):
        """Test daily report data transformation with NaN values"""
        nan_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02'],
            'Store': ['加拿大一店', '加拿大二店'],
            'Revenue (Tax Not Included)': [25000.50, np.nan],
            'Tables Served (Validated)': [np.nan, 145.0],
            'Customers': [520, np.nan],
            'Turnover Rate': [np.nan, 3.2],
            'Holiday': ['否', np.nan]
        })
        
        result = transform_daily_report_data(nan_df)
        
        self.assertEqual(len(result), 2)
        
        # Check NaN handling
        first_record = result[0]
        second_record = result[1]
        
        # NaN should be converted to appropriate default values
        self.assertEqual(second_record['revenue_tax_not_included'], 0.0)
        self.assertEqual(first_record['tables_served_validated'], 0.0)
        self.assertEqual(second_record['customers'], 0)
        self.assertEqual(first_record['turnover_rate'], 0.0)

    def test_transform_daily_report_data_holiday_variations(self):
        """Test daily report data transformation with various holiday formats"""
        holiday_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02', '2025-06-03', '2025-06-04'],
            'Store': ['店1', '店2', '店3', '店4'],
            'Holiday': ['是', '否', 'Yes', 'No']
        })
        
        result = transform_daily_report_data(holiday_df)
        
        self.assertEqual(len(result), 4)
        
        # Check holiday boolean conversion
        self.assertTrue(result[0]['is_holiday'])   # '是'
        self.assertFalse(result[1]['is_holiday'])  # '否'
        self.assertTrue(result[2]['is_holiday'])   # 'Yes'
        self.assertFalse(result[3]['is_holiday'])  # 'No'

    def test_transform_daily_report_data_date_formats(self):
        """Test daily report data transformation with various date formats"""
        date_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025/06/02', datetime(2025, 6, 3), date(2025, 6, 4)],
            'Store': ['店1', '店2', '店3', '店4']
        })
        
        result = transform_daily_report_data(date_df)
        
        self.assertEqual(len(result), 4)
        
        # All dates should be converted to string format
        for record in result:
            self.assertIsInstance(record['date'], str)
            self.assertRegex(record['date'], r'\d{4}-\d{2}-\d{2}')

    def test_transform_time_segment_data_basic(self):
        """Test basic time segment data transformation"""
        result = transform_time_segment_data(self.time_segment_data)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)
        
        # Check first record
        first_record = result[0]
        self.assertIn('date', first_record)
        self.assertIn('store_name', first_record)
        self.assertIn('time_segment', first_record)
        self.assertIn('revenue', first_record)
        self.assertIn('tables', first_record)
        self.assertIn('customers', first_record)
        self.assertIn('is_holiday', first_record)

    def test_transform_time_segment_data_empty(self):
        """Test time segment data transformation with empty DataFrame"""
        empty_df = pd.DataFrame()
        result = transform_time_segment_data(empty_df)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_transform_time_segment_data_none(self):
        """Test time segment data transformation with None input"""
        result = transform_time_segment_data(None)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_transform_time_segment_data_missing_columns(self):
        """Test time segment data transformation with missing columns"""
        incomplete_df = pd.DataFrame({
            'Date': ['2025-06-01'],
            'Store': ['加拿大一店'],
            'Time Segment': ['11:00-14:00']
            # Missing other columns
        })
        
        result = transform_time_segment_data(incomplete_df)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        
        # Should have default values for missing columns
        record = result[0]
        self.assertEqual(record['revenue'], 0.0)
        self.assertEqual(record['tables'], 0.0)
        self.assertEqual(record['customers'], 0)

    def test_transform_time_segment_data_data_types(self):
        """Test time segment data transformation with various data types"""
        mixed_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02'],
            'Store': ['加拿大一店', '加拿大二店'],
            'Time Segment': ['11:00-14:00', '14:00-17:00'],
            'Revenue': ['8000.0', 6000.0],  # Mixed string/float
            'Tables': [60.0, '45.0'],  # Mixed float/string
            'Customers': ['180', 140],  # Mixed string/int
            'Holiday': ['否', 'No']
        })
        
        result = transform_time_segment_data(mixed_df)
        
        self.assertEqual(len(result), 2)
        
        # Check data type conversions
        first_record = result[0]
        self.assertIsInstance(first_record['revenue'], float)
        self.assertIsInstance(first_record['tables'], float)
        self.assertIsInstance(first_record['customers'], int)
        self.assertIsInstance(first_record['is_holiday'], bool)

    def test_transform_time_segment_data_nan_values(self):
        """Test time segment data transformation with NaN values"""
        nan_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02'],
            'Store': ['加拿大一店', '加拿大二店'],
            'Time Segment': ['11:00-14:00', '14:00-17:00'],
            'Revenue': [8000.0, np.nan],
            'Tables': [np.nan, 45.0],
            'Customers': [180, np.nan],
            'Holiday': ['否', np.nan]
        })
        
        result = transform_time_segment_data(nan_df)
        
        self.assertEqual(len(result), 2)
        
        # Check NaN handling
        first_record = result[0]
        second_record = result[1]
        
        # NaN should be converted to appropriate default values
        self.assertEqual(second_record['revenue'], 0.0)
        self.assertEqual(first_record['tables'], 0.0)
        self.assertEqual(second_record['customers'], 0)

    def test_transform_time_segment_data_time_segment_formats(self):
        """Test time segment data transformation with various time segment formats"""
        time_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02', '2025-06-03'],
            'Store': ['店1', '店2', '店3'],
            'Time Segment': ['11:00-14:00', '14:00-17:00', '17:00-20:00'],
            'Revenue': [8000.0, 6000.0, 7000.0]
        })
        
        result = transform_time_segment_data(time_df)
        
        self.assertEqual(len(result), 3)
        
        # Check time segment preservation
        time_segments = [record['time_segment'] for record in result]
        self.assertIn('11:00-14:00', time_segments)
        self.assertIn('14:00-17:00', time_segments)
        self.assertIn('17:00-20:00', time_segments)

    def test_transform_functions_with_large_datasets(self):
        """Test transform functions with large datasets"""
        # Create large dataset
        large_daily_data = pd.DataFrame({
            'Date': ['2025-06-01'] * 1000,
            'Store': [f'店{i}' for i in range(1000)],
            'Revenue (Tax Not Included)': [25000.50 + i for i in range(1000)],
            'Tables Served (Validated)': [180.5 + i for i in range(1000)],
            'Customers': [520 + i for i in range(1000)],
            'Holiday': ['否'] * 1000
        })
        
        result = transform_daily_report_data(large_daily_data)
        
        self.assertEqual(len(result), 1000)
        self.assertIsInstance(result, list)

    def test_transform_functions_with_special_characters(self):
        """Test transform functions with special characters in store names"""
        special_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02'],
            'Store': ['加拿大一店 (Main)', '加拿大二店 & 分店'],
            'Revenue (Tax Not Included)': [25000.50, 18000.25]
        })
        
        result = transform_daily_report_data(special_df)
        
        self.assertEqual(len(result), 2)
        
        # Special characters should be preserved
        store_names = [record['store_name'] for record in result]
        self.assertIn('加拿大一店 (Main)', store_names)
        self.assertIn('加拿大二店 & 分店', store_names)

    def test_transform_functions_with_extreme_values(self):
        """Test transform functions with extreme values"""
        extreme_df = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02', '2025-06-03'],
            'Store': ['店1', '店2', '店3'],
            'Revenue (Tax Not Included)': [0, 999999999.99, -1000],  # Zero, very large, negative
            'Tables Served (Validated)': [0, 9999.99, -10],
            'Customers': [0, 99999, -5],
            'Turnover Rate': [0, 99.99, -1.5]
        })
        
        result = transform_daily_report_data(extreme_df)
        
        self.assertEqual(len(result), 3)
        
        # Should handle extreme values without crashing
        for record in result:
            self.assertIsInstance(record['revenue_tax_not_included'], float)
            self.assertIsInstance(record['tables_served_validated'], float)
            self.assertIsInstance(record['customers'], int)
            self.assertIsInstance(record['turnover_rate'], float)

    def test_error_handling_in_transformations(self):
        """Test error handling in transformation functions"""
        # Test with invalid data types that can't be converted
        problematic_df = pd.DataFrame({
            'Date': ['2025-06-01'],
            'Store': ['店1'],
            'Revenue (Tax Not Included)': ['invalid_number'],
            'Tables Served (Validated)': ['not_a_number'],
            'Customers': ['text'],
            'Turnover Rate': ['abc']
        })
        
        # Should handle conversion errors gracefully
        result = transform_daily_report_data(problematic_df)
        
        self.assertEqual(len(result), 1)
        
        # Invalid values should be converted to defaults
        record = result[0]
        self.assertEqual(record['revenue_tax_not_included'], 0.0)
        self.assertEqual(record['tables_served_validated'], 0.0)
        self.assertEqual(record['customers'], 0)
        self.assertEqual(record['turnover_rate'], 0.0)

    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_extraction_with_different_sheet_names(self, mock_file, mock_makedirs, mock_read_excel):
        """Test extraction functions with different sheet names"""
        mock_read_excel.return_value = self.daily_report_data
        
        # Test daily reports extraction
        result = extract_daily_reports('test.xlsx', 'output')
        self.assertTrue(result)
        mock_read_excel.assert_called_with('test.xlsx', sheet_name='Daily Report')
        
        # Reset mock
        mock_read_excel.reset_mock()
        mock_read_excel.return_value = self.time_segment_data
        
        # Test time segments extraction
        result = extract_time_segments('test.xlsx', 'output')
        self.assertTrue(result)
        mock_read_excel.assert_called_with('test.xlsx', sheet_name='Time Segment')

    @patch('lib.data_extraction.pd.read_excel')
    def test_extraction_with_wrong_sheet_name(self, mock_read_excel):
        """Test extraction functions with wrong sheet name"""
        mock_read_excel.side_effect = ValueError("Sheet 'Daily Report' not found")
        
        result = extract_daily_reports('test.xlsx', 'output')
        
        self.assertFalse(result)

    def test_data_consistency_after_transformation(self):
        """Test data consistency after transformation"""
        # Test that transformation preserves data integrity
        original_data = self.daily_report_data.copy()
        result = transform_daily_report_data(original_data)
        
        # Check that number of records is preserved
        self.assertEqual(len(result), len(original_data))
        
        # Check that key data is preserved
        for i, record in enumerate(result):
            original_row = original_data.iloc[i]
            self.assertEqual(record['store_name'], original_row['Store'])
            self.assertEqual(record['date'], str(original_row['Date']))


class TestDataExtractionIntegration(unittest.TestCase):
    """Integration tests for data extraction module"""
    
    @patch('lib.data_extraction.pd.read_excel')
    @patch('lib.data_extraction.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_full_extraction_workflow(self, mock_file, mock_makedirs, mock_read_excel):
        """Test complete extraction workflow"""
        # Set up mock data
        daily_data = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02'],
            'Store': ['加拿大一店', '加拿大二店'],
            'Revenue (Tax Not Included)': [25000.50, 18000.25],
            'Tables Served (Validated)': [180.5, 145.0],
            'Customers': [520, 420],
            'Holiday': ['否', '是']
        })
        
        time_data = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02'],
            'Store': ['加拿大一店', '加拿大二店'],
            'Time Segment': ['11:00-14:00', '14:00-17:00'],
            'Revenue': [8000.0, 6000.0],
            'Tables': [60.0, 45.0],
            'Customers': [180, 140],
            'Holiday': ['否', '是']
        })
        
        mock_read_excel.side_effect = [daily_data, time_data]
        
        # Test daily extraction
        daily_result = extract_daily_reports('test.xlsx', 'output')
        self.assertTrue(daily_result)
        
        # Test time segment extraction
        time_result = extract_time_segments('test.xlsx', 'output')
        self.assertTrue(time_result)
        
        # Verify both functions were called with correct parameters
        self.assertEqual(mock_read_excel.call_count, 2)
        self.assertEqual(mock_makedirs.call_count, 2)

    def test_transformation_workflow(self):
        """Test complete transformation workflow"""
        # Create test data
        daily_data = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02', '2025-06-03'],
            'Store': ['加拿大一店', '加拿大二店', '加拿大三店'],
            'Revenue (Tax Not Included)': [25000.50, 18000.25, 22000.75],
            'Tables Served (Validated)': [180.5, 145.0, 165.5],
            'Customers': [520, 420, 480],
            'Turnover Rate': [3.8, 3.2, 3.5],
            'Holiday': ['否', '是', '否']
        })
        
        time_data = pd.DataFrame({
            'Date': ['2025-06-01', '2025-06-02', '2025-06-03'],
            'Store': ['加拿大一店', '加拿大二店', '加拿大三店'],
            'Time Segment': ['11:00-14:00', '14:00-17:00', '17:00-20:00'],
            'Revenue': [8000.0, 6000.0, 7000.0],
            'Tables': [60.0, 45.0, 50.0],
            'Customers': [180, 140, 160],
            'Holiday': ['否', '是', '否']
        })
        
        # Transform both datasets
        daily_result = transform_daily_report_data(daily_data)
        time_result = transform_time_segment_data(time_data)
        
        # Verify results
        self.assertEqual(len(daily_result), 3)
        self.assertEqual(len(time_result), 3)
        
        # Verify data structure
        for record in daily_result:
            required_fields = ['date', 'store_name', 'revenue_tax_not_included', 
                             'tables_served_validated', 'customers', 'turnover_rate', 'is_holiday']
            for field in required_fields:
                self.assertIn(field, record)
        
        for record in time_result:
            required_fields = ['date', 'store_name', 'time_segment', 
                             'revenue', 'tables', 'customers', 'is_holiday']
            for field in required_fields:
                self.assertIn(field, record)


if __name__ == '__main__':
    unittest.main() 