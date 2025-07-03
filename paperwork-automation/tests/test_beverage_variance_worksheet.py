#!/usr/bin/env python3
"""
Test suite for BeverageVarianceGenerator
"""

from lib.beverage_variance_worksheet import BeverageVarianceGenerator
import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from openpyxl import Workbook
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBeverageVarianceGenerator(unittest.TestCase):
    """Test cases for BeverageVarianceGenerator"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_provider = Mock()
        self.mock_db_manager = Mock()
        self.mock_data_provider.db_manager = self.mock_db_manager
        self.generator = BeverageVarianceGenerator(self.mock_data_provider)

    def test_generator_initialization(self):
        """Test generator initialization"""
        self.assertIsInstance(self.generator, BeverageVarianceGenerator)
        self.assertEqual(self.generator.data_provider, self.mock_data_provider)
        self.assertEqual(self.generator.db_manager, self.mock_db_manager)

    def test_generate_worksheet_basic(self):
        """Test basic worksheet generation"""
        workbook = Workbook()
        target_date = "2025-06-01"

        # Mock database response
        mock_variance_details = [
            {
                'store_id': 1,
                'store_name': '加拿大一店',
                'material_number': 'MAT001',
                'material_name': '青岛啤酒',
                'specification': '500ml',
                'unit': '瓶',
                'system_quantity': '100.00',
                'counted_quantity': '95.00',
                'variance_quantity': '-5.00',
                'unit_price': '5.00',
                'variance_amount': '-25.00',
                'source': 'SAP系统',
                'region': '加拿大',
                'remarks': '差异需要关注'
            }
        ]

        with patch.object(self.generator, 'get_beverage_variance_details', return_value=mock_variance_details):
            worksheet = self.generator.generate_worksheet(
                workbook, target_date)

            # Verify worksheet was created
            self.assertIsNotNone(worksheet)
            self.assertEqual(worksheet.title, "酒水差异明细表")

            # Verify headers
            expected_headers = [
                "月份", "来源", "大区", "门店", "物料编号", "物料名称",
                "规格", "单位", "系统数量", "盘点数量", "差异数量",
                "单价", "差异金额", "备注"
            ]

            for col, expected_header in enumerate(expected_headers, 1):
                actual_header = worksheet.cell(row=1, column=col).value
                self.assertEqual(actual_header, expected_header)

            # Verify data row
            self.assertEqual(worksheet.cell(row=2, column=1).value, "202506")
            self.assertEqual(worksheet.cell(row=2, column=4).value, "加拿大一店")
            self.assertEqual(worksheet.cell(row=2, column=6).value, "青岛啤酒")

    def test_generate_worksheet_empty_data(self):
        """Test worksheet generation with empty data"""
        workbook = Workbook()
        target_date = "2025-06-01"

        with patch.object(self.generator, 'get_beverage_variance_details', return_value=[]):
            worksheet = self.generator.generate_worksheet(
                workbook, target_date)

            # Verify worksheet was created with headers only
            self.assertIsNotNone(worksheet)
            self.assertEqual(worksheet.title, "酒水差异明细表")

            # Should have headers but no data rows
            self.assertEqual(worksheet.cell(row=1, column=1).value, "月份")
            self.assertIsNone(worksheet.cell(row=2, column=1).value)

    def test_generate_worksheet_with_summary(self):
        """Test worksheet generation with summary calculation"""
        workbook = Workbook()
        target_date = "2025-06-01"

        mock_variance_details = [
            {
                'store_id': 1,
                'store_name': '加拿大一店',
                'material_number': 'MAT001',
                'material_name': '青岛啤酒',
                'specification': '500ml',
                'unit': '瓶',
                'system_quantity': '100.00',
                'counted_quantity': '95.00',
                'variance_quantity': '-5.00',
                'unit_price': '5.00',
                'variance_amount': '-25.00',
                'source': 'SAP系统',
                'region': '加拿大',
                'remarks': '差异需要关注'
            },
            {
                'store_id': 2,
                'store_name': '加拿大二店',
                'material_number': 'MAT002',
                'material_name': '可口可乐',
                'specification': '330ml',
                'unit': '罐',
                'system_quantity': '200.00',
                'counted_quantity': '210.00',
                'variance_quantity': '10.00',
                'unit_price': '3.00',
                'variance_amount': '30.00',
                'source': 'SAP系统',
                'region': '加拿大',
                'remarks': '差异需要关注'
            }
        ]

        with patch.object(self.generator, 'get_beverage_variance_details', return_value=mock_variance_details):
            worksheet = self.generator.generate_worksheet(
                workbook, target_date)

            # Check summary row (should be row 4: header + 2 data rows + 1 summary row)
            self.assertEqual(worksheet.cell(row=4, column=9).value, "合计")
            self.assertEqual(worksheet.cell(
                row=4, column=10).value, 300.0)  # 100 + 200
            self.assertEqual(worksheet.cell(
                row=4, column=11).value, 305.0)  # 95 + 210
            self.assertEqual(worksheet.cell(
                row=4, column=12).value, 5.0)    # -5 + 10
            self.assertEqual(worksheet.cell(
                row=4, column=14).value, 5.0)    # -25 + 30

    def test_get_beverage_variance_details_success(self):
        """Test successful beverage variance details retrieval"""
        year, month = 2025, 6

        # Mock database connection and cursor
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None

        self.mock_db_manager.get_connection.return_value = mock_connection

        # Mock query results
        mock_cursor.fetchall.return_value = [
            (1, '加拿大一店', 'MAT001', '青岛啤酒', '500ml', '瓶',
             100.0, 95.0, -5.0, 5.0, -25.0, '酒类', '啤酒', '差异需要关注')
        ]

        result = self.generator.get_beverage_variance_details(year, month)

        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['store_name'], '加拿大一店')
        self.assertEqual(result[0]['material_name'], '青岛啤酒')
        self.assertEqual(result[0]['variance_quantity'], '-5.00')

    def test_get_beverage_variance_details_database_error(self):
        """Test beverage variance details retrieval with database error"""
        year, month = 2025, 6

        # Mock database connection to raise exception
        self.mock_db_manager.get_connection.side_effect = Exception(
            "Database connection failed")

        result = self.generator.get_beverage_variance_details(year, month)

        # Should return empty list on error
        self.assertEqual(result, [])

    def test_get_beverage_variance_details_empty_results(self):
        """Test beverage variance details retrieval with empty results"""
        year, month = 2025, 6

        # Mock database connection and cursor
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None

        self.mock_db_manager.get_connection.return_value = mock_connection

        # Mock empty query results
        mock_cursor.fetchall.return_value = []

        result = self.generator.get_beverage_variance_details(year, month)

        # Should return empty list
        self.assertEqual(result, [])

    def test_worksheet_styling(self):
        """Test worksheet styling is applied correctly"""
        workbook = Workbook()
        target_date = "2025-06-01"

        mock_variance_details = [
            {
                'store_id': 1,
                'store_name': '加拿大一店',
                'material_number': 'MAT001',
                'material_name': '青岛啤酒',
                'specification': '500ml',
                'unit': '瓶',
                'system_quantity': '100.00',
                'counted_quantity': '95.00',
                'variance_quantity': '-5.00',
                'unit_price': '5.00',
                'variance_amount': '-25.00',
                'source': 'SAP系统',
                'region': '加拿大',
                'remarks': '差异需要关注'
            }
        ]

        with patch.object(self.generator, 'get_beverage_variance_details', return_value=mock_variance_details):
            worksheet = self.generator.generate_worksheet(
                workbook, target_date)

            # Check header styling
            header_cell = worksheet.cell(row=1, column=1)
            self.assertEqual(header_cell.font.color.rgb, "FFFFFF")
            self.assertEqual(header_cell.fill.start_color.index, "C41E3A")

            # Check column widths are set
            self.assertEqual(worksheet.column_dimensions['A'].width, 10)
            self.assertEqual(worksheet.column_dimensions['F'].width, 25)

    def test_date_parsing(self):
        """Test date parsing in worksheet generation"""
        workbook = Workbook()
        target_date = "2025-06-15"  # Different day

        with patch.object(self.generator, 'get_beverage_variance_details', return_value=[]):
            worksheet = self.generator.generate_worksheet(
                workbook, target_date)

            # The month should still be extracted correctly
            self.assertIsNotNone(worksheet)
            # Verify get_beverage_variance_details was called with correct year/month
            self.generator.get_beverage_variance_details.assert_called_with(
                2025, 6)

    def test_variance_calculation_formatting(self):
        """Test variance calculation and formatting"""
        workbook = Workbook()
        target_date = "2025-06-01"

        # Mock data with various variance scenarios
        mock_variance_details = [
            {
                'store_id': 1,
                'store_name': '加拿大一店',
                'material_number': 'MAT001',
                'material_name': '青岛啤酒',
                'specification': '500ml',
                'unit': '瓶',
                'system_quantity': '100.50',  # Decimal values
                'counted_quantity': '95.25',
                'variance_quantity': '-5.25',
                'unit_price': '5.50',
                'variance_amount': '-28.88',
                'source': 'SAP系统',
                'region': '加拿大',
                'remarks': '差异需要关注'
            }
        ]

        with patch.object(self.generator, 'get_beverage_variance_details', return_value=mock_variance_details):
            worksheet = self.generator.generate_worksheet(
                workbook, target_date)

            # Check data formatting
            self.assertEqual(worksheet.cell(row=2, column=9).value, '100.50')
            self.assertEqual(worksheet.cell(row=2, column=10).value, '95.25')
            self.assertEqual(worksheet.cell(row=2, column=11).value, '-5.25')

    def test_beverage_filtering_logic(self):
        """Test that only beverage-related materials are included"""
        year, month = 2025, 6

        # Mock database connection and cursor
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None

        self.mock_db_manager.get_connection.return_value = mock_connection

        # Mock query results
        mock_cursor.fetchall.return_value = []

        self.generator.get_beverage_variance_details(year, month)

        # Verify the SQL query contains beverage filtering logic
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]

        # Check that the query includes beverage filtering conditions
        self.assertIn("酒%", query)
        self.assertIn("饮料%", query)
        self.assertIn("水%", query)


if __name__ == '__main__':
    unittest.main()
