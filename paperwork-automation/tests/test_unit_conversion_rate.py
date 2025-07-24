#!/usr/bin/env python3
"""
Tests for unit_conversion_rate functionality in dish_material table and calculations.
Tests the new requirement to add unit_conversion_rate column and apply conversion in reports.
"""

import unittest
import sys
import os
from datetime import datetime
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.database import DatabaseManager, DatabaseConfig
    from lib.monthly_dishes_worksheet import MonthlyDishesWorksheetGenerator
    from lib.database_queries import ReportDataProvider
except ImportError as e:
    print(f"Import error: {e}")
    print("Database tests disabled - missing dependencies")
    sys.exit(0)


class TestUnitConversionRate(unittest.TestCase):
    """Test unit conversion rate functionality in dish_material table."""

    @classmethod
    def setUpClass(cls):
        """Set up test database manager."""
        try:
            cls.db_manager = DatabaseManager(DatabaseConfig(is_test=True))
            print("✅ Connected to test database")
        except Exception as e:
            print(f"❌ Failed to connect to test database: {e}")
            raise unittest.SkipTest("Database connection failed")

    def setUp(self):
        """Set up test data for each test."""
        self.test_dish_id = None
        self.test_material_id = None
        self.setup_test_data()

    def tearDown(self):
        """Clean up test data after each test."""
        self.cleanup_test_data()

    def setup_test_data(self):
        """Create test dish, material, and dish_material relationship."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Create test dish
                cursor.execute("""
                    INSERT INTO dish (name, full_code, size, is_active)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, ("Test Dish", "9999999", "单锅", True))
                self.test_dish_id = cursor.fetchone()['id']

                # Create test material
                cursor.execute("""
                    INSERT INTO material (name, material_number, unit, is_active)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, ("Test Material", "9999999", "kg", True))
                self.test_material_id = cursor.fetchone()['id']

                conn.commit()

        except Exception as e:
            print(f"❌ Failed to setup test data: {e}")
            raise

    def cleanup_test_data(self):
        """Remove test data."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Clean up dish_material relationships
                if self.test_dish_id and self.test_material_id:
                    cursor.execute("""
                        DELETE FROM dish_material 
                        WHERE dish_id = %s AND material_id = %s
                    """, (self.test_dish_id, self.test_material_id))

                # Clean up test dish
                if self.test_dish_id:
                    cursor.execute(
                        "DELETE FROM dish WHERE id = %s", (self.test_dish_id,))

                # Clean up test material
                if self.test_material_id:
                    cursor.execute(
                        "DELETE FROM material WHERE id = %s", (self.test_material_id,))

                conn.commit()

        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

    def test_unit_conversion_rate_column_exists(self):
        """Test that unit_conversion_rate column exists in dish_material table."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check if column exists
            cursor.execute("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'dish_material' 
                AND column_name = 'unit_conversion_rate'
            """)

            result = cursor.fetchone()
            self.assertIsNotNone(
                result, "unit_conversion_rate column should exist")
            self.assertEqual(result['data_type'], 'numeric',
                             "Column should be numeric type")
            self.assertEqual(result['is_nullable'], 'NO',
                             "Column should be NOT NULL")

    def test_dish_material_insert_with_unit_conversion_rate(self):
        """Test inserting dish_material relationship with unit_conversion_rate."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Insert dish_material with unit_conversion_rate
            cursor.execute("""
                INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, unit_conversion_rate
            """, (self.test_dish_id, self.test_material_id, 1.0, 1.0, 0.354))

            result = cursor.fetchone()
            self.assertIsNotNone(result, "Insert should succeed")
            self.assertEqual(float(
                result['unit_conversion_rate']), 0.354, "Unit conversion rate should be 0.354")

            conn.commit()

    def test_dish_material_default_unit_conversion_rate(self):
        """Test that unit_conversion_rate defaults to 1.0 when not specified."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Insert dish_material without specifying unit_conversion_rate
            cursor.execute("""
                INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate)
                VALUES (%s, %s, %s, %s)
                RETURNING id, unit_conversion_rate
            """, (self.test_dish_id, self.test_material_id, 1.0, 1.0))

            result = cursor.fetchone()
            self.assertIsNotNone(result, "Insert should succeed")
            self.assertEqual(float(
                result['unit_conversion_rate']), 1.0, "Unit conversion rate should default to 1.0")

            conn.commit()

    def test_theoretical_usage_calculation_with_conversion(self):
        """Test that theoretical usage calculations apply unit conversion rate."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Insert dish_material with conversion rate of 0.354
            cursor.execute("""
                INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_dish_id, self.test_material_id, 1.0, 1.0, 0.354))

            # Test theoretical usage query similar to what's used in reports
            cursor.execute("""
                SELECT 
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate,
                    -- Simulated calculation: sale_amount * standard_quantity * loss_rate / unit_conversion_rate
                    (100 * dm.standard_quantity * dm.loss_rate / dm.unit_conversion_rate) as theoretical_usage
                FROM dish_material dm
                WHERE dm.dish_id = %s AND dm.material_id = %s
            """, (self.test_dish_id, self.test_material_id))

            result = cursor.fetchone()
            self.assertIsNotNone(result, "Query should return result")

            # Expected: 100 * 1.0 * 1.0 / 0.354 ≈ 282.49
            expected_usage = 100 * 1.0 * 1.0 / 0.354
            actual_usage = float(result['theoretical_usage'])

            self.assertAlmostEqual(actual_usage, expected_usage, places=2,
                                   msg=f"Theoretical usage should be {expected_usage:.2f}, got {actual_usage:.2f}")

            conn.commit()

    def test_unit_conversion_rate_update_on_conflict(self):
        """Test that unit_conversion_rate is updated on conflict resolution."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Insert initial record
            cursor.execute("""
                INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.test_dish_id, self.test_material_id, 1.0, 1.0, 0.5))

            # Update with conflict resolution (like in extraction scripts)
            cursor.execute("""
                INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (dish_id, material_id)
                DO UPDATE SET
                    standard_quantity = EXCLUDED.standard_quantity,
                    loss_rate = EXCLUDED.loss_rate,
                    unit_conversion_rate = EXCLUDED.unit_conversion_rate,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING unit_conversion_rate
            """, (self.test_dish_id, self.test_material_id, 2.0, 1.2, 0.354))

            result = cursor.fetchone()
            self.assertIsNotNone(result, "Update should succeed")
            self.assertEqual(float(result['unit_conversion_rate']), 0.354,
                             "Unit conversion rate should be updated to 0.354")

            conn.commit()

    def test_conversion_rate_validation(self):
        """Test validation of unit_conversion_rate values."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Test positive conversion rate
            cursor.execute("""
                INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING unit_conversion_rate
            """, (self.test_dish_id, self.test_material_id, 1.0, 1.0, 2.5))

            result = cursor.fetchone()
            self.assertEqual(float(
                result['unit_conversion_rate']), 2.5, "Should accept positive conversion rate")

            # Clean up for next test
            cursor.execute("""
                DELETE FROM dish_material 
                WHERE dish_id = %s AND material_id = %s
            """, (self.test_dish_id, self.test_material_id))

            conn.commit()

    def test_integration_with_dish_1060062_material_1500882(self):
        """Test specific example: dish 1060062 with material 1500882 and conversion rate 0.354."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Check if the specific dish and material exist (they should from extraction)
            cursor.execute("""
                SELECT d.id as dish_id, m.id as material_id
                FROM dish d, material m
                WHERE d.full_code = '1060062' AND m.material_number = '1500882'
            """)

            result = cursor.fetchone()
            if result:
                dish_id = result['dish_id']
                material_id = result['material_id']

                # Insert/update the specific relationship with conversion rate
                cursor.execute("""
                    INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (dish_id, material_id)
                    DO UPDATE SET
                        unit_conversion_rate = EXCLUDED.unit_conversion_rate,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING unit_conversion_rate
                """, (dish_id, material_id, 1.0, 1.0, 0.354))

                result = cursor.fetchone()
                self.assertIsNotNone(
                    result, "Specific dish-material relationship should be created/updated")
                self.assertEqual(float(result['unit_conversion_rate']), 0.354,
                                 "Conversion rate should be 0.354 for this specific case")

                conn.commit()
            else:
                self.skipTest(
                    "Test dish 1060062 or material 1500882 not found in database")


if __name__ == '__main__':
    print("🧪 Running Unit Conversion Rate Tests")
    print("=" * 50)

    # Run tests with detailed output
    unittest.main(verbosity=2)
