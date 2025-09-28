#!/usr/bin/env python3
"""
Extract combo sales from Excel files and store them in the database.

This script processes combo sales Excel files for a specific year and month,
extracting combo information and their dish sales, storing them in the PostgreSQL database.

Processing Steps:
1. Create/update combo records
2. Validate dishes exist in database
3. Create combo-dish sales records in monthly_combo_dish_sale table
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# Add parent directory to path for imports - MUST come before local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from lib.excel_utils import safe_read_excel, clean_dish_code
from scripts.dish_material.extract_data.file_discovery import find_combo_sales_file
from configs.dish_material.combo_sales_extraction import (
    COMBO_SALES_COLUMN_MAPPINGS,
    COMBO_STORE_MAPPING,
    COMBO_SALES_SHEET_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComboSalesExtractor:
    """Extract combo sales from Excel files and store in database."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the combo sales extractor."""
        self.db_manager = db_manager
        self.combos_cache = {}  # Cache for combo lookups
        self.dishes_cache = {}  # Cache for dish lookups

    def extract_combo_sales_for_month(
        self,
        year: int,
        month: int,
        input_file: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Extract combo sales for a specific year and month.

        Args:
            year: Target year
            month: Target month (1-12)
            input_file: Path to Excel file (optional)

        Returns:
            Dictionary with extraction statistics
        """
        if input_file is None:
            # Use file discovery to find the combo sales file
            combo_file = find_combo_sales_file(year, month, use_history=True)
            if combo_file:
                input_path = combo_file
            else:
                logger.warning(f"Could not find combo sales file for {year}-{month:02d} (this is optional)")
                return {'error': 'No combo sales file found', 'files_processed': 0}
        else:
            input_path = Path(input_file)
            if not input_path.exists():
                logger.error(f"Input file does not exist: {input_path}")
                return {'error': 'File not found'}

        stats = {
            'rows_processed': 0,
            'combos_created': 0,
            'combos_validated': 0,
            'dishes_validated': 0,
            'sales_created': 0,
            'sales_updated': 0,
            'errors': 0
        }

        try:
            logger.info(f"Reading file: {input_path}")

            # Read the Excel file
            df = self._read_and_process_excel(input_path, year, month)
            if df is None or df.empty:
                logger.warning(f"No valid data in file: {input_path.name}")
                return stats

            stats['rows_processed'] = len(df)
            logger.info(f"Processing {len(df)} rows for {year}-{month:02d}")

            # Process in steps
            with self.db_manager.get_connection() as conn:
                try:
                    # Step 1: Create/update combos
                    logger.info("Step 1: Creating/updating combos...")
                    self._update_combos(conn, df, stats)

                    # Step 2: Validate dishes exist
                    logger.info("Step 2: Validating dishes...")
                    self._validate_dishes(conn, df, stats)

                    # Step 3: Create combo-dish sales records
                    logger.info("Step 3: Creating combo-dish sales...")
                    self._create_combo_dish_sales(conn, df, year, month, stats)

                    conn.commit()
                    logger.info("All data committed successfully")

                except Exception as e:
                    conn.rollback()
                    logger.error(f"Error during processing, rolling back: {e}")
                    stats['errors'] += 1
                    raise

        except Exception as e:
            logger.error(f"Error reading {input_path}: {e}")
            stats['errors'] += 1

        logger.info(f"Extraction complete. Statistics: {stats}")
        return stats

    def _read_and_process_excel(self, file_path: Path, year: int, month: int) -> Optional[pd.DataFrame]:
        """Read Excel file and normalize columns."""
        try:
            # Read Excel with proper dtype for codes
            dtype_spec = {
                '套餐编码': str,
                '菜品编码': str
            }

            # Read the specific sheet
            df = safe_read_excel(
                str(file_path), 
                dtype_spec=dtype_spec, 
                sheet_name=COMBO_SALES_SHEET_NAME
            )
            logger.info(f"Successfully read sheet '{COMBO_SALES_SHEET_NAME}' with {len(df)} rows")

            # Rename columns based on mapping
            rename_mapping = {}
            for key, chinese_col in COMBO_SALES_COLUMN_MAPPINGS.items():
                if chinese_col in df.columns:
                    rename_mapping[chinese_col] = key

            if not rename_mapping:
                logger.warning(f"No matching columns found in {file_path}")
                return None

            df = df.rename(columns=rename_mapping)

            # Clean codes
            if 'combo_code' in df.columns:
                df['combo_code'] = df['combo_code'].apply(clean_dish_code)
            if 'dish_code' in df.columns:
                df['dish_code'] = df['dish_code'].apply(clean_dish_code)

            # Map store names to IDs
            if 'store_name' in df.columns:
                df['store_id'] = df['store_name'].map(COMBO_STORE_MAPPING)
                df = df[df['store_id'].notna()]  # Remove unmapped stores

            # Filter for target year/month if month column exists
            if 'month' in df.columns:
                # Convert YYYYMM format to year and month
                df['data_year'] = df['month'] // 100
                df['data_month'] = df['month'] % 100
                df = df[(df['data_year'] == year) & (df['data_month'] == month)]
                logger.info(f"Filtered to {len(df)} rows for {year}-{month:02d}")

            # Convert numeric columns
            numeric_columns = ['combo_price', 'dish_price', 'sale_quantity',
                             'return_quantity', 'net_quantity', 'actual_revenue', 'tax']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
            return None

    def _update_combos(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 1: Create or update combo records."""
        cursor = conn.cursor()

        # Get unique combos
        combo_columns = ['combo_code', 'combo_name', 'combo_size']
        available_columns = [col for col in combo_columns if col in df.columns]
        
        if 'combo_code' not in available_columns:
            logger.error("combo_code column is required")
            return

        unique_combos = df[available_columns].drop_duplicates(subset=['combo_code'])

        for _, combo_row in unique_combos.iterrows():
            try:
                combo_code = combo_row['combo_code']
                if pd.isna(combo_code) or not combo_code:
                    continue

                # Check if combo exists
                cursor.execute(
                    "SELECT id FROM combo WHERE combo_code = %s",
                    (combo_code,)
                )
                result = cursor.fetchone()

                if result:
                    combo_id = result['id']
                    stats['combos_validated'] += 1
                    
                    # Optionally update combo name if different
                    if 'combo_name' in combo_row and not pd.isna(combo_row['combo_name']):
                        cursor.execute(
                            "UPDATE combo SET name = %s WHERE id = %s",
                            (combo_row['combo_name'], combo_id)
                        )
                else:
                    # Create new combo
                    combo_name = combo_row.get('combo_name', combo_code)
                    if pd.isna(combo_name):
                        combo_name = combo_code
                    
                    description = combo_row.get('combo_size', '')
                    if pd.isna(description):
                        description = ''
                    
                    cursor.execute(
                        """INSERT INTO combo (combo_code, name, description, is_active)
                           VALUES (%s, %s, %s, TRUE) RETURNING id""",
                        (combo_code, combo_name, description)
                    )
                    combo_id = cursor.fetchone()['id']
                    stats['combos_created'] += 1
                    logger.debug(f"Created combo: {combo_code} - {combo_name}")

                # Cache the combo ID
                self.combos_cache[combo_code] = combo_id

            except Exception as e:
                logger.error(f"Error updating combo {combo_row.get('combo_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1

    def _validate_dishes(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 2: Validate that dishes exist in database."""
        cursor = conn.cursor()

        if 'dish_code' not in df.columns:
            logger.error("dish_code column is required")
            return

        # Get unique dishes
        dish_columns = ['dish_code', 'dish_name', 'dish_size']
        available_columns = [col for col in dish_columns if col in df.columns]
        
        unique_dishes = df[available_columns].drop_duplicates(subset=['dish_code'])

        for _, dish_row in unique_dishes.iterrows():
            try:
                dish_code = dish_row['dish_code']
                if pd.isna(dish_code) or not dish_code:
                    continue

                # Check if dish exists
                cursor.execute(
                    "SELECT id FROM dish WHERE full_code = %s",
                    (dish_code,)
                )
                result = cursor.fetchone()

                if result:
                    dish_id = result['id']
                    stats['dishes_validated'] += 1
                    self.dishes_cache[dish_code] = dish_id
                else:
                    # Log warning but don't create - dishes should come from dish extraction
                    logger.warning(f"Dish not found: {dish_code} - {dish_row.get('dish_name', 'Unknown')}")
                    stats['errors'] += 1

            except Exception as e:
                logger.error(f"Error validating dish {dish_row.get('dish_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1

    def _create_combo_dish_sales(self, conn, df: pd.DataFrame, year: int, month: int, stats: Dict):
        """Step 3: Create combo-dish sales records."""
        cursor = conn.cursor()

        # Group by combo, dish, and store
        grouping_cols = ['combo_code', 'dish_code', 'store_id']
        if not all(col in df.columns for col in grouping_cols):
            logger.error("Missing required columns for sales records")
            return

        # Aggregate quantities (sale - return = net) and tax
        agg_dict = {}
        if 'net_quantity' in df.columns:
            agg_dict['net_quantity'] = 'sum'
        elif 'sale_quantity' in df.columns and 'return_quantity' in df.columns:
            df['net_quantity'] = df['sale_quantity'] - df['return_quantity']
            agg_dict['net_quantity'] = 'sum'
        else:
            logger.error("No quantity columns found")
            return

        # Add tax aggregation if present
        if 'tax' in df.columns:
            agg_dict['tax'] = 'sum'

        sales_data = df.groupby(grouping_cols).agg(agg_dict).reset_index()

        for _, row in sales_data.iterrows():
            try:
                combo_code = row['combo_code']
                dish_code = row['dish_code']
                store_id = int(row['store_id'])
                sale_amount = float(row['net_quantity'])
                tax_amount = float(row.get('tax', 0))

                # Get combo ID
                combo_id = self.combos_cache.get(combo_code)
                if not combo_id:
                    logger.warning(f"Combo not found in cache: {combo_code}")
                    continue

                # Get dish ID
                dish_id = self.dishes_cache.get(dish_code)
                if not dish_id:
                    # Try to look up in database
                    cursor.execute(
                        "SELECT id FROM dish WHERE full_code = %s",
                        (dish_code,)
                    )
                    result = cursor.fetchone()
                    if result:
                        dish_id = result['id']
                        self.dishes_cache[dish_code] = dish_id
                    else:
                        logger.warning(f"Dish not found: {dish_code}")
                        continue

                # Check if sales record exists
                cursor.execute(
                    """SELECT id FROM monthly_combo_dish_sale
                       WHERE combo_id = %s AND dish_id = %s AND store_id = %s 
                       AND month = %s AND year = %s""",
                    (combo_id, dish_id, store_id, month, year)
                )
                result = cursor.fetchone()

                if result:
                    # Update existing record
                    cursor.execute(
                        """UPDATE monthly_combo_dish_sale
                           SET sale_amount = %s, tax_amount = %s
                           WHERE id = %s""",
                        (sale_amount, tax_amount, result['id'])
                    )
                    stats['sales_updated'] += 1
                else:
                    # Create new record
                    cursor.execute(
                        """INSERT INTO monthly_combo_dish_sale
                           (combo_id, dish_id, store_id, month, year, sale_amount, tax_amount)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (combo_id, dish_id, store_id, month, year, sale_amount, tax_amount)
                    )
                    stats['sales_created'] += 1

                logger.debug(f"Recorded sales: Combo {combo_code} -> Dish {dish_code} in store {store_id}: {sale_amount}")

            except Exception as e:
                logger.error(f"Error creating sales for combo {row.get('combo_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract combo sales from Excel files to database'
    )
    parser.add_argument(
        '--year',
        type=int,
        required=True,
        help='Target year (e.g., 2025)'
    )
    parser.add_argument(
        '--month',
        type=int,
        required=True,
        help='Target month (1-12)'
    )
    parser.add_argument(
        '--input-file',
        type=str,
        help='Path to Excel file (optional)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Use test database'
    )

    args = parser.parse_args()

    # Validate month
    if not 1 <= args.month <= 12:
        logger.error("Month must be between 1 and 12")
        sys.exit(1)

    # Initialize database connection
    db_config = DatabaseConfig(is_test=args.test)
    db_manager = DatabaseManager(db_config)

    # Test database connection
    if not db_manager.test_connection():
        logger.error("Failed to connect to database")
        sys.exit(1)

    logger.info(f"Connected to {'test' if args.test else 'production'} database")

    # Create extractor and process files
    extractor = ComboSalesExtractor(db_manager)
    stats = extractor.extract_combo_sales_for_month(
        args.year,
        args.month,
        args.input_file
    )

    # Print summary
    print("\n" + "="*50)
    print("COMBO SALES EXTRACTION SUMMARY")
    print("="*50)
    print(f"Rows Processed:        {stats.get('rows_processed', 0)}")
    print(f"Combos Created:        {stats.get('combos_created', 0)}")
    print(f"Combos Validated:      {stats.get('combos_validated', 0)}")
    print(f"Dishes Validated:      {stats.get('dishes_validated', 0)}")
    print(f"Sales Created:         {stats.get('sales_created', 0)}")
    print(f"Sales Updated:         {stats.get('sales_updated', 0)}")
    print(f"Errors:                {stats.get('errors', 0)}")
    print("="*50)

    # Exit with error if there were any errors
    if stats.get('errors', 0) > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()