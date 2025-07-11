#!/usr/bin/env python3
"""
Simplified Historical Data Extraction Script - Non-hanging version

This script processes historical monthly data with better error handling
and smaller batch sizes to prevent hanging issues.
"""

from utils.database import DatabaseManager, DatabaseConfig
import sys
import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
import warnings

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('extraction.log')
    ]
)
logger = logging.getLogger(__name__)


class SimpleHistoricalExtractor:
    """Simplified historical data extractor with better error handling."""

    def __init__(self, test_mode: bool = False, debug: bool = False):
        self.test_mode = test_mode
        self.debug = debug
        self.db_manager = DatabaseManager(DatabaseConfig(is_test=test_mode))
        logger.info(
            f"🍲 Initialized extractor - Test mode: {test_mode}, Debug: {debug}")

    def get_store_mapping(self) -> Dict[str, int]:
        """Get store name to ID mapping."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM store")
                return {row[1]: row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error getting store mapping: {e}")
            return {}

    def clean_dish_code(self, code) -> str:
        """Clean dish code (remove .0 suffix from floats)."""
        if pd.isna(code):
            return ""

        code_str = str(code).strip()
        if code_str.endswith('.0'):
            code_str = code_str[:-2]
        return code_str

    def process_month_simple(self, month_folder: Path, target_date: str) -> Dict[str, int]:
        """Process a single month folder with simple logic."""
        logger.info(f"🗓️ Processing month: {month_folder.name}")

        results = {
            'dish_types': 0,
            'child_types': 0,
            'dishes': 0,
            'price_history': 0,
            'materials': 0,
            'material_prices': 0
        }

        try:
            # Process dishes from monthly_dish_sale
            dish_sale_folder = month_folder / "monthly_dish_sale"
            if dish_sale_folder.exists():
                for dish_file in dish_sale_folder.glob("*.xlsx"):
                    logger.info(f"📋 Processing dish file: {dish_file.name}")
                    dish_results = self.process_dish_file_simple(
                        dish_file, target_date)
                    results['dishes'] += dish_results['dishes']
                    results['price_history'] += dish_results['price_history']

                    # Limit processing to prevent hanging
                    if results['dishes'] > 1000:  # Limit for testing
                        logger.warning(
                            "⚠️ Reached dish limit, stopping for safety")
                        break

            # Process materials from monthly_material_usage
            material_usage_folder = month_folder / "monthly_material_usage"
            if material_usage_folder.exists():
                for material_file in material_usage_folder.glob("*.xls*"):
                    logger.info(
                        f"📦 Processing material file: {material_file.name}")
                    material_results = self.process_material_file_simple(
                        material_file, target_date)
                    results['materials'] += material_results['materials']

                    # Limit processing to prevent hanging
                    if results['materials'] > 500:  # Limit for testing
                        logger.warning(
                            "⚠️ Reached material limit, stopping for safety")
                        break

            # Process material prices from material_detail
            material_detail_folder = month_folder / "material_detail"
            if material_detail_folder.exists():
                for store_folder in material_detail_folder.iterdir():
                    if store_folder.is_dir() and store_folder.name.isdigit():
                        store_id = int(store_folder.name)
                        logger.info(
                            f"💰 Processing material prices for store {store_id}")

                        for price_file in store_folder.glob("*.xls*"):
                            price_results = self.process_material_price_file_simple(
                                price_file, target_date, store_id)
                            results['material_prices'] += price_results['material_prices']

                            # Limit processing to prevent hanging
                            if results['material_prices'] > 1000:  # Limit for testing
                                logger.warning(
                                    "⚠️ Reached material price limit, stopping for safety")
                                break

                        if results['material_prices'] > 1000:
                            break

            return results

        except Exception as e:
            logger.error(f"Error processing month {month_folder.name}: {e}")
            return results

    def process_dish_file_simple(self, file_path: Path, target_date: str) -> Dict[str, int]:
        """Process dish file with simple logic and small batches."""
        logger.info(f"🍽️ Processing dish file: {file_path.name}")

        results = {'dishes': 0, 'price_history': 0}

        try:
            # Read file with row limit to prevent hanging
            df = pd.read_excel(file_path, engine='openpyxl',
                               nrows=1000)  # Limit rows
            logger.info(f"📊 Loaded {len(df)} rows (limited for safety)")

            # Find column mappings
            dish_name_col = None
            dish_code_col = None

            for col in df.columns:
                if '菜品名称' in str(col):
                    dish_name_col = col
                if '菜品编码' in str(col):
                    dish_code_col = col

            if not dish_name_col or not dish_code_col:
                logger.warning("Missing required columns, skipping file")
                return results

            logger.info(f"Using columns: {dish_name_col}, {dish_code_col}")

            # Filter valid rows
            valid_rows = []
            for _, row in df.iterrows():
                dish_name = str(row[dish_name_col]).strip()
                dish_code = str(row[dish_code_col]).strip()

                # Skip header rows and invalid data
                if (dish_name not in ['菜品名称', '菜品名称(门店pad显示名称)'] and
                    dish_code not in ['菜品编码', '菜品短编码'] and
                        len(dish_name) > 2 and len(dish_code) > 0):
                    valid_rows.append(row)

                # Limit for safety
                if len(valid_rows) >= 100:  # Process only 100 dishes per file
                    break

            logger.info(f"Found {len(valid_rows)} valid rows")

            # Process in very small batches
            store_mapping = self.get_store_mapping()

            for i in range(0, len(valid_rows), 10):  # Process 10 at a time
                batch = valid_rows[i:i+10]
                batch_results = self.process_dish_batch_simple(
                    batch, dish_name_col, dish_code_col, target_date, store_mapping)
                results['dishes'] += batch_results['dishes']
                results['price_history'] += batch_results['price_history']

                # Log progress
                if i % 50 == 0:
                    logger.info(f"Processed {i+len(batch)} dishes...")

            return results

        except Exception as e:
            logger.error(f"Error processing dish file {file_path}: {e}")
            return results

    def process_dish_batch_simple(self, batch: List, dish_name_col: str, dish_code_col: str, target_date: str, store_mapping: Dict[str, int]) -> Dict[str, int]:
        """Process a small batch of dishes."""
        results = {'dishes': 0, 'price_history': 0}

        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                for row in batch:
                    try:
                        # Clean dish code
                        full_code = self.clean_dish_code(row[dish_code_col])
                        if not full_code:
                            continue

                        dish_name = str(row[dish_name_col]).strip()
                        size = row.get('规格', '') if pd.notna(
                            row.get('规格')) else ''

                        # Insert dish (simple version)
                        cursor.execute("""
                            INSERT INTO dish (full_code, size, name)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (full_code, size) DO UPDATE SET
                                name = EXCLUDED.name,
                                updated_at = CURRENT_TIMESTAMP
                        """, (full_code, size, dish_name))

                        if cursor.rowcount > 0:
                            results['dishes'] += 1

                        # Process price history if available
                        if ('门店名称' in row and '单价' in row and
                                pd.notna(row['门店名称']) and pd.notna(row['单价'])):

                            store_name = str(row['门店名称']).strip()
                            if store_name in store_mapping:
                                try:
                                    price = float(row['单价'])
                                    if price > 0:
                                        store_id = store_mapping[store_name]

                                        # Get dish ID
                                        cursor.execute("SELECT id FROM dish WHERE full_code = %s AND size = %s",
                                                       (full_code, size))
                                        dish_result = cursor.fetchone()

                                        if dish_result:
                                            cursor.execute("""
                                                INSERT INTO dish_price_history (dish_id, store_id, price, effective_date, is_active)
                                                VALUES (%s, %s, %s, %s, true)
                                                ON CONFLICT (dish_id, store_id, effective_date) DO UPDATE SET
                                                    price = EXCLUDED.price,
                                                    updated_at = CURRENT_TIMESTAMP
                                            """, (dish_result[0], store_id, price, target_date))

                                            if cursor.rowcount > 0:
                                                results['price_history'] += 1
                                except (ValueError, TypeError):
                                    continue

                    except Exception as e:
                        logger.debug(f"Error processing individual dish: {e}")
                        continue

                conn.commit()

        except Exception as e:
            logger.error(f"Error processing dish batch: {e}")

        return results

    def process_material_file_simple(self, file_path: Path, target_date: str) -> Dict[str, int]:
        """Process material file with simple logic."""
        logger.info(f"📦 Processing material file: {file_path.name}")

        results = {'materials': 0}

        try:
            # Try different engines for .xls files
            try:
                df = pd.read_excel(
                    file_path, engine='openpyxl', nrows=500)  # Limit rows
            except:
                try:
                    df = pd.read_excel(file_path, engine='xlrd', nrows=500)
                except:
                    logger.warning(f"Could not read file {file_path.name}")
                    return results

            logger.info(f"📊 Loaded {len(df)} rows from material file")

            # Process materials in small batches
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                for _, row in df.iterrows():
                    try:
                        if '物料描述' in row and '物料' in row:
                            material_name = str(row['物料描述']).strip()
                            material_number = str(
                                row['物料']).strip().lstrip('0')

                            if material_name and material_number and len(material_name) > 1:
                                cursor.execute("""
                                    INSERT INTO material (name, material_number, unit)
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (material_number) DO UPDATE SET
                                        name = EXCLUDED.name,
                                        updated_at = CURRENT_TIMESTAMP
                                """, (material_name, material_number, ''))

                                if cursor.rowcount > 0:
                                    results['materials'] += 1
                    except Exception as e:
                        logger.debug(f"Error processing material: {e}")
                        continue

                conn.commit()

        except Exception as e:
            logger.error(f"Error processing material file {file_path}: {e}")

        return results

    def process_material_price_file_simple(self, file_path: Path, target_date: str, store_id: int) -> Dict[str, int]:
        """Process material price file with simple logic."""
        logger.info(f"💰 Processing material price file: {file_path.name}")

        results = {'material_prices': 0}

        try:
            # Try different engines and limit rows
            try:
                # Use string dtype for material column to prevent float conversion [[memory:1779842]]
                df = pd.read_excel(file_path, engine='openpyxl',
                                   nrows=500, dtype={'物料': str})
            except:
                try:
                    df = pd.read_excel(
                        file_path, engine='xlrd', nrows=500, dtype={'物料': str})
                except:
                    logger.warning(f"Could not read file {file_path.name}")
                    return results

            logger.info(f"📊 Loaded {len(df)} rows from material price file")

            # Process material prices in small batches
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                for _, row in df.iterrows():
                    try:
                        if '物料' in row and '单价' in row:
                            material_number = str(
                                row['物料']).strip().lstrip('0')

                            try:
                                price = float(row['单价'])
                                if price > 0 and material_number:
                                    # Get material ID
                                    cursor.execute(
                                        "SELECT id FROM material WHERE material_number = %s", (material_number,))
                                    material_result = cursor.fetchone()

                                    if material_result:
                                        cursor.execute("""
                                            INSERT INTO material_price_history (material_id, store_id, price, effective_date, is_active)
                                            VALUES (%s, %s, %s, %s, true)
                                            ON CONFLICT (material_id, store_id, effective_date) DO UPDATE SET
                                                price = EXCLUDED.price,
                                                updated_at = CURRENT_TIMESTAMP
                                        """, (material_result[0], store_id, price, target_date))

                                        if cursor.rowcount > 0:
                                            results['material_prices'] += 1
                            except (ValueError, TypeError):
                                continue
                    except Exception as e:
                        logger.debug(f"Error processing material price: {e}")
                        continue

                conn.commit()

        except Exception as e:
            logger.error(
                f"Error processing material price file {file_path}: {e}")

        return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Simple Historical Data Extraction')
    parser.add_argument('--month', type=str, required=True,
                        help='Month to process (YYYY-MM)')
    parser.add_argument('--test', action='store_true',
                        help='Use test database')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create extractor
    extractor = SimpleHistoricalExtractor(
        test_mode=args.test, debug=args.debug)

    # Process month
    month_folder = Path(f"history_files/monthly_report_inputs/{args.month}")
    if not month_folder.exists():
        logger.error(f"Month folder not found: {month_folder}")
        return

    target_date = f"{args.month}-01"  # First day of month

    logger.info(f"🍲 Starting simple historical extraction for {args.month}")
    logger.info(f"📅 Target date: {target_date}")

    try:
        results = extractor.process_month_simple(month_folder, target_date)

        logger.info("🎯 EXTRACTION RESULTS")
        logger.info("=" * 40)
        for key, value in results.items():
            logger.info(f"{key}: {value}")

        total_records = sum(results.values())
        logger.info(f"📊 Total records processed: {total_records}")

        if total_records > 0:
            logger.info("✅ Simple extraction completed successfully!")
        else:
            logger.warning("⚠️ No records were processed")

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        return


if __name__ == "__main__":
    main()
