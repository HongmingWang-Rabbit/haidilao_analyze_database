#!/usr/bin/env python3
"""Tests for takeout revenue extraction module."""

import unittest
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.takeout_extraction import extract_store_id_from_text, transform_takeout_data


class TestTakeoutExtraction(unittest.TestCase):
    """Test cases for takeout extraction functions."""

    def test_extract_store_id_store_1(self):
        """Test store ID extraction for store 1."""
        self.assertEqual(extract_store_id_from_text("01-01日加拿大一店外卖收入"), 1)

    def test_extract_store_id_store_5(self):
        """Test store ID extraction for store 5."""
        self.assertEqual(extract_store_id_from_text("01-03日加拿大五店外卖收入"), 5)

    def test_extract_store_id_store_8(self):
        """Test store ID extraction for store 8."""
        self.assertEqual(extract_store_id_from_text("01-01日加拿大八店外卖收入"), 8)

    def test_extract_store_id_with_prefix(self):
        """Test store ID extraction with RV prefix."""
        self.assertEqual(extract_store_id_from_text("RV 01-03日加拿大六店外卖收入"), 6)

    def test_extract_store_id_no_match(self):
        """Test store ID extraction with non-matching text."""
        self.assertIsNone(extract_store_id_from_text("CA7D MaLaTang Dine-out Revenue"))

    def test_extract_store_id_none_input(self):
        """Test store ID extraction with None input."""
        self.assertIsNone(extract_store_id_from_text(None))

    def test_extract_store_id_empty_string(self):
        """Test store ID extraction with empty string."""
        self.assertIsNone(extract_store_id_from_text(""))

    def test_transform_takeout_data_basic(self):
        """Test basic data transformation."""
        df = pd.DataFrame({
            'Document Date': ['2026-01-01', '2026-01-02'],
            'Text': ['01-01日加拿大一店外卖收入', '01-02日加拿大三店外卖收入'],
            'Amount in Local Currency': [-4755.57, -1034.98]
        })

        result = transform_takeout_data(df)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['store_id'], 1)
        self.assertEqual(result[0]['amount'], 4755.57)  # Converted to positive
        self.assertEqual(result[0]['date'], '2026-01-01')
        self.assertEqual(result[1]['store_id'], 3)
        self.assertEqual(result[1]['amount'], 1034.98)

    def test_transform_takeout_data_skip_invalid_store(self):
        """Test that invalid store names are skipped."""
        df = pd.DataFrame({
            'Document Date': ['2026-01-01'],
            'Text': ['CA7D MaLaTang Revenue'],
            'Amount in Local Currency': [-100.00]
        })

        result = transform_takeout_data(df)

        self.assertEqual(len(result), 0)

    def test_transform_takeout_data_skip_null_date(self):
        """Test that null dates are skipped."""
        df = pd.DataFrame({
            'Document Date': [None],
            'Text': ['01-01日加拿大一店外卖收入'],
            'Amount in Local Currency': [-100.00]
        })

        result = transform_takeout_data(df)

        self.assertEqual(len(result), 0)

    def test_transform_takeout_data_currency(self):
        """Test that currency is set to CAD."""
        df = pd.DataFrame({
            'Document Date': ['2026-01-01'],
            'Text': ['01-01日加拿大一店外卖收入'],
            'Amount in Local Currency': [-100.00]
        })

        result = transform_takeout_data(df)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['currency'], 'CAD')


class TestExchangeRateConfig(unittest.TestCase):
    """Test cases for exchange rate configuration."""

    def test_get_takeout_daily_improvement_2026(self):
        """Test daily improvement calculation for 2026."""
        from configs.challenge_targets import get_takeout_daily_improvement_cad

        result = get_takeout_daily_improvement_cad(2026)

        # $200 USD / 0.728597 = ~$274.50 CAD
        self.assertAlmostEqual(result, 274.50, places=0)

    def test_get_takeout_daily_improvement_2025(self):
        """Test daily improvement calculation for 2025."""
        from configs.challenge_targets import get_takeout_daily_improvement_cad

        result = get_takeout_daily_improvement_cad(2025)

        # $200 USD / 0.6952 = ~$287.68 CAD
        self.assertAlmostEqual(result, 287.68, places=0)

    def test_get_takeout_daily_improvement_unknown_year(self):
        """Test that unknown year defaults to 2026 rate."""
        from configs.challenge_targets import get_takeout_daily_improvement_cad

        result_2030 = get_takeout_daily_improvement_cad(2030)
        result_2026 = get_takeout_daily_improvement_cad(2026)

        self.assertEqual(result_2030, result_2026)


if __name__ == '__main__':
    unittest.main()
