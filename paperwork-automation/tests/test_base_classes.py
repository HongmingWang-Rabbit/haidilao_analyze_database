#!/usr/bin/env python3
"""
Comprehensive tests for lib/base_classes.py
Tests base classes that were created to eliminate duplication from 13+ worksheet generators.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import pandas as pd
from datetime import datetime

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from lib.base_classes import BaseWorksheetGenerator, BaseExtractor, BaseReportGenerator


class TestBaseWorksheetGenerator(unittest.TestCase):
    """Test BaseWorksheetGenerator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.store_names = ['加拿大一店', '加拿大二店', '加拿大三店']
        self.target_date = '2025-01-15'
        
    def test_initialization_success(self):
        """Test successful initialization of BaseWorksheetGenerator"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        self.assertEqual(generator.store_names, self.store_names)
        self.assertEqual(generator.target_date, self.target_date)
        self.assertIsInstance(generator.target_dt, datetime)
        self.assertEqual(generator.target_dt.year, 2025)
        self.assertEqual(generator.target_dt.month, 1)
        self.assertEqual(generator.target_dt.day, 15)
        
    def test_initialization_invalid_date(self):
        """Test initialization with invalid date format"""
        with self.assertRaises(ValueError) as context:
            BaseWorksheetGeneratorConcrete(self.store_names, '2025/01/15')  # Wrong format
            
        self.assertIn('YYYY-MM-DD format', str(context.exception))
        
    def test_common_styles_setup(self):
        """Test that common styles are properly set up"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        # Test that style objects exist
        self.assertIsNotNone(generator.header_fill)
        self.assertIsNotNone(generator.header_font)
        self.assertIsNotNone(generator.header_alignment)
        self.assertIsNotNone(generator.data_font)
        self.assertIsNotNone(generator.thin_border)
        
        # Test format strings
        self.assertEqual(generator.percentage_format, '0.0%')
        self.assertEqual(generator.currency_format, '#,##0.00')
        self.assertEqual(generator.integer_format, '#,##0')
        
    def test_set_column_widths(self):
        """Test set_column_widths method"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        # Mock worksheet
        mock_ws = Mock()
        mock_ws.column_dimensions = {}
        
        # Mock get_column_letter to return predictable values
        with patch('lib.base_classes.get_column_letter', side_effect=lambda x: chr(64 + x)):
            generator.set_column_widths(mock_ws, [15, 12, 20])
            
        # Verify that column dimensions were set (can't test exact values due to openpyxl complexity)
        self.assertTrue(len(mock_ws.column_dimensions) > 0)
        
    def test_apply_header_style(self):
        """Test apply_header_style method"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        # Mock cell
        mock_cell = Mock()
        generator.apply_header_style(mock_cell)
        
        # Verify style properties were set
        self.assertEqual(mock_cell.fill, generator.header_fill)
        self.assertEqual(mock_cell.font, generator.header_font)
        self.assertEqual(mock_cell.alignment, generator.header_alignment)
        self.assertEqual(mock_cell.border, generator.thin_border)
        
    def test_apply_data_style(self):
        """Test apply_data_style method with different alignments"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        # Test default (left) alignment
        mock_cell = Mock()
        generator.apply_data_style(mock_cell)
        self.assertEqual(mock_cell.font, generator.data_font)
        self.assertEqual(mock_cell.border, generator.thin_border)
        
        # Test center alignment
        mock_cell_center = Mock()
        generator.apply_data_style(mock_cell_center, align='center')
        self.assertEqual(mock_cell_center.alignment, generator.center_alignment)
        
        # Test right alignment
        mock_cell_right = Mock()
        generator.apply_data_style(mock_cell_right, align='right')
        self.assertEqual(mock_cell_right.alignment, generator.right_alignment)
        
    def test_format_percentage(self):
        """Test format_percentage method"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        # Test normal percentage
        self.assertEqual(generator.format_percentage(0.15), "15.0%")
        self.assertEqual(generator.format_percentage(0.1234), "12.3%")
        
        # Test with different decimal places
        self.assertEqual(generator.format_percentage(0.15, decimals=2), "15.00%")
        
        # Test edge cases
        self.assertEqual(generator.format_percentage(None), "0.0%")
        self.assertEqual(generator.format_percentage(pd.NaType()), "0.0%")
        
    def test_calculate_percentage_change(self):
        """Test calculate_percentage_change method"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        # Test normal calculation
        self.assertAlmostEqual(generator.calculate_percentage_change(120, 100), 0.2)
        self.assertAlmostEqual(generator.calculate_percentage_change(80, 100), -0.2)
        
        # Test zero previous value
        self.assertEqual(generator.calculate_percentage_change(100, 0), 0.0)
        self.assertEqual(generator.calculate_percentage_change(100, None), 0.0)
        
        # Test None current value
        self.assertEqual(generator.calculate_percentage_change(None, 100), -1.0)
        self.assertEqual(generator.calculate_percentage_change(pd.NaType(), 100), -1.0)
        
    def test_safe_divide(self):
        """Test safe_divide method"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        # Test normal division
        self.assertEqual(generator.safe_divide(10, 2), 5.0)
        self.assertEqual(generator.safe_divide(7, 3), 7/3)
        
        # Test zero denominator
        self.assertEqual(generator.safe_divide(10, 0), 0.0)
        self.assertEqual(generator.safe_divide(10, None), 0.0)
        
        # Test custom default
        self.assertEqual(generator.safe_divide(10, 0, default=99.0), 99.0)
        
        # Test None numerator
        self.assertEqual(generator.safe_divide(None, 5), 0.0)
        
    def test_add_title_section(self):
        """Test add_title_section method"""
        generator = BaseWorksheetGeneratorConcrete(self.store_names, self.target_date)
        
        # Mock worksheet
        mock_ws = Mock()
        mock_cell = Mock()
        mock_ws.cell.return_value = mock_cell
        
        # Test title section addition
        next_row = generator.add_title_section(mock_ws, "Test Title", 1, 5)
        
        # Verify merge_cells was called
        mock_ws.merge_cells.assert_called_once_with(start_row=1, start_column=1, end_row=1, end_column=5)
        
        # Verify cell styling was applied
        self.assertIsNotNone(mock_cell.font)
        self.assertIsNotNone(mock_cell.alignment)
        self.assertIsNotNone(mock_cell.fill)
        
        # Verify return value
        self.assertEqual(next_row, 2)


class TestBaseExtractor(unittest.TestCase):
    """Test BaseExtractor functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock()
        
    def test_initialization_with_db_manager(self):
        """Test initialization with database manager"""
        extractor = BaseExtractorConcrete(self.mock_db_manager)
        
        self.assertEqual(extractor.db_manager, self.mock_db_manager)
        self.assertIsNotNone(extractor.project_root)
        
    def test_initialization_without_db_manager(self):
        """Test initialization without database manager"""
        extractor = BaseExtractorConcrete()
        
        self.assertIsNone(extractor.db_manager)
        
    def test_setup_project_path(self):
        """Test setup_project_path method"""
        extractor = BaseExtractorConcrete()
        
        # Verify project root is set
        self.assertIsInstance(extractor.project_root, Path)
        self.assertTrue(extractor.project_root.exists())
        
        # Verify project root is in sys.path
        self.assertIn(str(extractor.project_root), sys.path)
        
    @patch('lib.base_classes.get_database_manager')
    def test_setup_database_connection_success(self, mock_get_db_manager):
        """Test successful database connection setup"""
        mock_db = Mock()
        mock_get_db_manager.return_value = mock_db
        
        extractor = BaseExtractorConcrete()
        result = extractor.setup_database_connection()
        
        self.assertTrue(result)
        self.assertEqual(extractor.db_manager, mock_db)
        
    def test_setup_database_connection_failure(self):
        """Test database connection setup failure"""
        extractor = BaseExtractorConcrete()
        
        # Mock import error
        with patch('lib.base_classes.get_database_manager', side_effect=ImportError):
            result = extractor.setup_database_connection()
            
        self.assertFalse(result)
        
    def test_safe_database_operation_success(self):
        """Test successful database operation"""
        mock_conn = Mock()
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = mock_conn
        
        extractor = BaseExtractorConcrete(self.mock_db_manager)
        
        # Mock operation function
        mock_operation = Mock(return_value="success")
        
        result = extractor.safe_database_operation(mock_operation, "arg1", "arg2")
        
        self.assertEqual(result, "success")
        mock_operation.assert_called_once_with(mock_conn, "arg1", "arg2")
        
    def test_safe_database_operation_no_manager(self):
        """Test database operation without database manager"""
        extractor = BaseExtractorConcrete()
        
        mock_operation = Mock()
        result = extractor.safe_database_operation(mock_operation)
        
        self.assertIsNone(result)
        mock_operation.assert_not_called()
        
    def test_batch_insert_with_conflict_handling(self):
        """Test batch insert with conflict handling"""
        extractor = BaseExtractorConcrete(self.mock_db_manager)
        
        test_data = [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'}
        ]
        
        # Mock safe_database_operation to return success
        extractor.safe_database_operation = Mock(return_value=2)
        
        result = extractor.batch_insert_with_conflict_handling(
            'test_table', test_data, ['id'], batch_size=10
        )
        
        self.assertEqual(result, 2)
        
    def test_batch_insert_empty_data(self):
        """Test batch insert with empty data"""
        extractor = BaseExtractorConcrete(self.mock_db_manager)
        
        result = extractor.batch_insert_with_conflict_handling(
            'test_table', [], ['id']
        )
        
        self.assertEqual(result, 0)
        
    def test_get_store_id_mapping(self):
        """Test get_store_id_mapping method"""
        extractor = BaseExtractorConcrete()
        
        mapping = extractor.get_store_id_mapping()
        
        self.assertIsInstance(mapping, dict)
        self.assertIn('加拿大一店', mapping)
        self.assertEqual(mapping['加拿大一店'], 1)
        
    def test_validate_file_existence_success(self):
        """Test validate_file_existence with existing file"""
        extractor = BaseExtractorConcrete()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            result = extractor.validate_file_existence(temp_path)
            self.assertTrue(result)
        finally:
            Path(temp_path).unlink()
            
    def test_validate_file_existence_failure(self):
        """Test validate_file_existence with non-existent file"""
        extractor = BaseExtractorConcrete()
        
        result = extractor.validate_file_existence('/nonexistent/file.xlsx')
        self.assertFalse(result)
        
    def test_log_extraction_summary(self):
        """Test log_extraction_summary method"""
        extractor = BaseExtractorConcrete()
        
        # Mock logger
        extractor.logger = Mock()
        
        test_counts = {
            'Materials': 150,
            'Dishes': 75,
            'Relationships': 300
        }
        
        extractor.log_extraction_summary(test_counts)
        
        # Verify that logger.info was called multiple times
        self.assertTrue(extractor.logger.info.call_count >= 6)  # Header, items, footer


class TestBaseReportGenerator(unittest.TestCase):
    """Test BaseReportGenerator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.target_date = '2025-01-15'
        
    def test_initialization_success(self):
        """Test successful initialization"""
        generator = BaseReportGenerator(self.target_date)
        
        self.assertEqual(generator.target_date, self.target_date)
        self.assertIsInstance(generator.target_dt, datetime)
        
    def test_initialization_invalid_date(self):
        """Test initialization with invalid date"""
        with self.assertRaises(ValueError):
            BaseReportGenerator('invalid-date')
            
    def test_generate_output_filename(self):
        """Test generate_output_filename method"""
        generator = BaseReportGenerator(self.target_date)
        
        filename = generator.generate_output_filename('test_report')
        self.assertEqual(filename, 'test_report_2025_01_15.xlsx')
        
        # Test with custom extension
        filename_csv = generator.generate_output_filename('test_report', '.csv')
        self.assertEqual(filename_csv, 'test_report_2025_01_15.csv')
        
    def test_setup_output_directory(self):
        """Test setup_output_directory method"""
        generator = BaseReportGenerator(self.target_date)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / 'test_output'
            
            result_path = generator.setup_output_directory(output_dir)
            
            self.assertTrue(result_path.exists())
            self.assertTrue(result_path.is_dir())
            self.assertEqual(result_path, output_dir)


# Concrete implementations for testing abstract base classes
class BaseWorksheetGeneratorConcrete(BaseWorksheetGenerator):
    """Concrete implementation for testing BaseWorksheetGenerator"""
    
    def generate_worksheet(self, workbook, *args, **kwargs):
        """Concrete implementation of abstract method"""
        return "worksheet generated"


class BaseExtractorConcrete(BaseExtractor):
    """Concrete implementation for testing BaseExtractor"""
    
    def extract_data(self, input_file, **kwargs):
        """Concrete implementation of abstract method"""
        return {"extracted": True, "file": str(input_file)}


class TestBaseClassesIntegration(unittest.TestCase):
    """Test integration scenarios between base classes"""
    
    def test_worksheet_generator_with_real_data(self):
        """Test worksheet generator with realistic data processing"""
        store_names = ['加拿大一店', '加拿大二店']
        target_date = '2025-06-15'
        
        generator = BaseWorksheetGeneratorConcrete(store_names, target_date)
        
        # Test percentage calculations with real-world values
        current_revenue = 15000.50
        previous_revenue = 12000.00
        
        change = generator.calculate_percentage_change(current_revenue, previous_revenue)
        formatted_change = generator.format_percentage(change)
        
        self.assertAlmostEqual(change, 0.25004166666666664)  # 25% increase
        self.assertEqual(formatted_change, "25.0%")
        
        # Test safe division with restaurant metrics
        total_tables = 45
        operating_hours = 12
        tables_per_hour = generator.safe_divide(total_tables, operating_hours)
        
        self.assertAlmostEqual(tables_per_hour, 3.75)
        
    def test_extractor_with_file_processing(self):
        """Test extractor with file processing workflow"""
        mock_db_manager = Mock()
        extractor = BaseExtractorConcrete(mock_db_manager)
        
        # Test store mapping
        store_mapping = extractor.get_store_id_mapping()
        self.assertEqual(len(store_mapping), 7)  # 7 Canadian stores
        
        # Test batch processing simulation
        test_records = []
        for i in range(1, 101):  # 100 test records
            test_records.append({
                'id': i,
                'name': f'Item {i}',
                'store_id': (i % 7) + 1
            })
            
        # Mock the database operation
        extractor.safe_database_operation = Mock(return_value=len(test_records))
        
        processed_count = extractor.batch_insert_with_conflict_handling(
            'test_items', test_records, ['id'], batch_size=25
        )
        
        self.assertEqual(processed_count, 100)


if __name__ == '__main__':
    # Run all tests with detailed output
    unittest.main(verbosity=2)