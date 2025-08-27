#!/usr/bin/env python3
"""
Extract dishes from Excel files and store them in the database.

This script processes dish sales Excel files for a specific year and month,
extracting dish information and storing it in the PostgreSQL database.

Processing Steps:
1. Update dish_type and dish_child_type tables
2. Update dish tables  
3. Update dish price history table
4. Update dish sales table
"""

from utils.database import DatabaseManager, DatabaseConfig
from lib.excel_utils import safe_read_excel, clean_dish_code
from configs.dish_material.dish_sales_extraction import (
    DISH_COLUMN_MAPPINGS,
    DISH_FILE_STOREID_MAPPING
)
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DishExtractor:
    """Extract dishes from Excel files and store in database."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the dish extractor."""
        self.db_manager = db_manager
        self.dish_types_cache = {}  # Cache for dish type lookups
        self.dish_child_types_cache = {}  # Cache for dish child type lookups
        self.dishes_cache = {}  # Cache for dish lookups

    def extract_dishes_for_month(
        self,
        year: int,
        month: int,
        input_dir: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Extract dishes for a specific year and month.

        Args:
            year: Target year
            month: Target month (1-12)
            input_dir: Directory containing Excel files or path to a single Excel file (optional)

        Returns:
            Dictionary with extraction statistics
        """
        if input_dir is None:
            # Default input directory structure
            input_dir = f"Input/monthly_report/{year}_{month:02d}"

        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"Input path does not exist: {input_path}")
            return {'error': 'Path not found'}

        stats = {
            'files_processed': 0,
            'dish_types_created': 0,
            'dish_child_types_created': 0,
            'dishes_created': 0,
            'dishes_updated': 0,
            'prices_inserted': 0,
            'sales_inserted': 0,
            'errors': 0
        }

        # Check if input is a file or directory
        if input_path.is_file():
            # Single file provided
            if input_path.suffix.lower() in ['.xlsx', '.xls']:
                excel_files = [input_path]
                logger.info(f"Processing single file: {input_path}")
            else:
                logger.error(f"File is not an Excel file: {input_path}")
                return {'error': 'Not an Excel file'}
        else:
            # Directory provided - find all Excel files
            excel_files = list(input_path.glob('*.xlsx')) + \
                list(input_path.glob('*.xls'))

        if not excel_files:
            logger.warning(f"No Excel files found in {input_path}")
            return stats

        # First, read all files to collect unique data
        all_data = []
        for excel_file in excel_files:
            try:
                logger.info(f"Reading file: {excel_file}")

                # First try to read the file and check if it has store information
                df = self._read_and_process_excel(excel_file)
                if df is None or df.empty:
                    logger.warning(f"No valid data in file: {excel_file.name}")
                    continue

                # Check if store information is in the data itself
                if 'store_name' in df.columns:
                    # Map store names in the data to store IDs
                    df['store_id'] = df['store_name'].map(
                        DISH_FILE_STOREID_MAPPING)
                    if df['store_id'].isna().all():
                        logger.warning(
                            f"No matching store names found in data")
                        continue
                    # Remove rows with unmapped stores
                    df = df[df['store_id'].notna()]
                else:
                    # Try to get store ID from filename
                    store_id = self._get_store_id_from_filename(
                        excel_file.name)
                    if not store_id:
                        logger.warning(
                            f"Could not determine store from filename: {excel_file.name}")
                        logger.error(
                            f"No 'store_name' column found after mapping. Check if DISH_COLUMN_MAPPINGS includes store_name mapping.")
                        continue
                    else:
                        df['store_id'] = store_id

                df['year'] = year
                df['month'] = month
                all_data.append(df)
                stats['files_processed'] += 1

            except Exception as e:
                logger.error(f"Error reading {excel_file}: {e}")
                stats['errors'] += 1

        if not all_data:
            logger.warning("No valid data found in Excel files")
            return stats

        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)

        # Process in steps
        with self.db_manager.get_connection() as conn:
            try:
                # Step 1: Update dish_type and dish_child_type tables
                logger.info("Step 1: Updating dish types...")
                self._update_dish_types(conn, combined_df, stats)

                # Step 2: Update dish tables
                logger.info("Step 2: Updating dishes...")
                self._update_dishes(conn, combined_df, stats)

                # Step 3: Update dish price history
                logger.info("Step 3: Updating dish prices...")
                self._update_dish_prices(conn, combined_df, year, month, stats)

                # Step 4: Update dish sales
                logger.info("Step 4: Updating dish sales...")
                self._update_dish_sales(conn, combined_df, year, month, stats)

                conn.commit()
                logger.info("All data committed successfully")

            except Exception as e:
                conn.rollback()
                logger.error(f"Error during processing, rolling back: {e}")
                stats['errors'] += 1
                raise

        logger.info(f"Extraction complete. Statistics: {stats}")
        return stats

    def _get_store_id_from_filename(self, filename: str) -> Optional[int]:
        """Extract store ID from filename."""
        for store_name, store_id in DISH_FILE_STOREID_MAPPING.items():
            if store_name in filename:
                return store_id
        return None

    def _read_and_process_excel(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read Excel file and normalize columns."""
        try:
            # Read Excel with proper dtype for codes
            dtype_spec = {}
            if DISH_COLUMN_MAPPINGS.get('full_code'):
                dtype_spec[DISH_COLUMN_MAPPINGS['full_code']] = str
            if DISH_COLUMN_MAPPINGS.get('short_code'):
                dtype_spec[DISH_COLUMN_MAPPINGS['short_code']] = str

            # Read the specific sheet "菜品销售汇总表" - no fallback
            df = safe_read_excel(
                str(file_path), dtype_spec=dtype_spec, sheet_name='菜品销售汇总表')
            logger.info(
                f"Successfully read sheet '菜品销售汇总表' with {len(df)} rows")

            # Rename columns based on mapping
            rename_mapping = {}
            for key, chinese_col in DISH_COLUMN_MAPPINGS.items():
                if chinese_col in df.columns:
                    rename_mapping[chinese_col] = key

            if not rename_mapping:
                logger.warning(f"No matching columns found in {file_path}")
                return None

            df = df.rename(columns=rename_mapping)

            # Clean dish codes
            if 'full_code' in df.columns:
                df['full_code'] = df['full_code'].apply(clean_dish_code)
            if 'short_code' in df.columns:
                df['short_code'] = df['short_code'].apply(clean_dish_code)

            # Convert numeric columns
            numeric_columns = ['dish_price_this_month', 'sale_amount',
                               'return_amount', 'free_amount', 'gift_amount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
            return None

    def _update_dish_types(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 1: Update dish_type and dish_child_type tables."""
        cursor = conn.cursor()

        # Get unique dish types
        if 'dish_type_name' in df.columns:
            unique_types = df['dish_type_name'].dropna().unique()

            for type_name in unique_types:
                try:
                    # Check if type exists
                    cursor.execute(
                        "SELECT id FROM dish_type WHERE name = %s",
                        (type_name,)
                    )
                    result = cursor.fetchone()

                    if not result:
                        # Insert new type
                        cursor.execute(
                            """INSERT INTO dish_type (name, is_active) 
                               VALUES (%s, TRUE) RETURNING id""",
                            (type_name,)
                        )
                        type_id = cursor.fetchone()['id']
                        stats['dish_types_created'] += 1
                        logger.debug(
                            f"Created dish type: {type_name} (ID: {type_id})")
                    else:
                        type_id = result['id']

                    self.dish_types_cache[type_name] = type_id

                    # Now handle child types for this parent type
                    if 'dish_child_type_name' in df.columns:
                        child_types = df[df['dish_type_name'] ==
                                         type_name]['dish_child_type_name'].dropna().unique()

                        for child_type_name in child_types:
                            # Check if child type exists
                            cursor.execute(
                                """SELECT id FROM dish_child_type 
                                   WHERE name = %s AND dish_type_id = %s""",
                                (child_type_name, type_id)
                            )
                            result = cursor.fetchone()

                            if not result:
                                # Insert new child type
                                cursor.execute(
                                    """INSERT INTO dish_child_type (name, dish_type_id, is_active) 
                                       VALUES (%s, %s, TRUE) RETURNING id""",
                                    (child_type_name, type_id)
                                )
                                child_type_id = cursor.fetchone()['id']
                                stats['dish_child_types_created'] += 1
                                logger.debug(
                                    f"Created dish child type: {child_type_name} (ID: {child_type_id})")
                            else:
                                child_type_id = result['id']

                            self.dish_child_types_cache[(
                                type_name, child_type_name)] = child_type_id

                except Exception as e:
                    logger.error(f"Error updating dish type {type_name}: {e}")
                    stats['errors'] += 1

    def _update_dishes(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 2: Update dish tables."""
        cursor = conn.cursor()

        # Get unique dishes
        dish_columns = ['full_code', 'name', 'system_name', 'size', 'short_code',
                        'dish_type_name', 'dish_child_type_name']
        available_columns = [col for col in dish_columns if col in df.columns]

        if 'full_code' not in available_columns:
            logger.error("full_code column is required for dish updates")
            return

        # Group by full_code and size to get unique dishes
        unique_dishes = df[available_columns].drop_duplicates(
            subset=['full_code', 'size'] if 'size' in available_columns else ['full_code'])

        for _, dish_row in unique_dishes.iterrows():
            try:
                full_code = dish_row['full_code']
                if pd.isna(full_code) or not full_code:
                    continue

                # Get dish_child_type_id if available
                dish_child_type_id = None
                if 'dish_type_name' in dish_row and 'dish_child_type_name' in dish_row:
                    type_name = dish_row['dish_type_name']
                    child_type_name = dish_row['dish_child_type_name']
                    if not pd.isna(type_name) and not pd.isna(child_type_name):
                        dish_child_type_id = self.dish_child_types_cache.get(
                            (type_name, child_type_name))

                # Check if dish exists
                size = dish_row.get('size', '') if 'size' in dish_row else ''
                if pd.isna(size):
                    size = ''

                cursor.execute(
                    """SELECT id FROM dish 
                       WHERE full_code = %s AND COALESCE(size, '') = %s""",
                    (full_code, size)
                )
                result = cursor.fetchone()

                if result:
                    # Update existing dish
                    dish_id = result['id']
                    update_fields = []
                    update_values = []

                    if 'name' in dish_row and not pd.isna(dish_row['name']):
                        update_fields.append("name = %s")
                        update_values.append(dish_row['name'])

                    if 'system_name' in dish_row and not pd.isna(dish_row['system_name']):
                        update_fields.append("system_name = %s")
                        update_values.append(dish_row['system_name'])

                    if 'short_code' in dish_row and not pd.isna(dish_row['short_code']):
                        update_fields.append("short_code = %s")
                        update_values.append(dish_row['short_code'])

                    if dish_child_type_id:
                        update_fields.append("dish_child_type_id = %s")
                        update_values.append(dish_child_type_id)

                    update_fields.append("is_active = TRUE")

                    if update_fields:
                        update_values.append(dish_id)
                        cursor.execute(
                            f"""UPDATE dish SET {', '.join(update_fields)}
                                WHERE id = %s""",
                            update_values
                        )
                        stats['dishes_updated'] += 1
                        logger.debug(
                            f"Updated dish: {full_code} (ID: {dish_id})")

                else:
                    # Insert new dish
                    insert_columns = ['full_code', 'size', 'is_active']
                    insert_values = [full_code, size, True]

                    if 'name' in dish_row and not pd.isna(dish_row['name']):
                        insert_columns.append('name')
                        insert_values.append(dish_row['name'])

                    if 'system_name' in dish_row and not pd.isna(dish_row['system_name']):
                        insert_columns.append('system_name')
                        insert_values.append(dish_row['system_name'])

                    if 'short_code' in dish_row and not pd.isna(dish_row['short_code']):
                        insert_columns.append('short_code')
                        insert_values.append(dish_row['short_code'])

                    if dish_child_type_id:
                        insert_columns.append('dish_child_type_id')
                        insert_values.append(dish_child_type_id)

                    placeholders = ', '.join(['%s'] * len(insert_values))
                    columns_str = ', '.join(insert_columns)

                    cursor.execute(
                        f"""INSERT INTO dish ({columns_str}) 
                            VALUES ({placeholders}) RETURNING id""",
                        insert_values
                    )
                    dish_id = cursor.fetchone()['id']
                    stats['dishes_created'] += 1
                    logger.debug(f"Created dish: {full_code} (ID: {dish_id})")

                # Cache the dish ID
                self.dishes_cache[(full_code, size)] = dish_id

            except Exception as e:
                logger.error(
                    f"Error updating dish {dish_row.get('full_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1

    def _update_dish_prices(self, conn, df: pd.DataFrame, year: int, month: int, stats: Dict):
        """Step 3: Update dish price history."""
        cursor = conn.cursor()

        if 'dish_price_this_month' not in df.columns:
            logger.warning("No price column found, skipping price updates")
            return

        # Group by store, dish to get unique prices
        price_data = df[df['dish_price_this_month'] > 0].groupby(
            ['store_id', 'full_code', 'size'] if 'size' in df.columns else [
                'store_id', 'full_code']
        ).agg({
            'dish_price_this_month': 'first'  # Take first price if multiple entries
        }).reset_index()

        for _, row in price_data.iterrows():
            try:
                full_code = row['full_code']
                size = row.get('size', '') if 'size' in row else ''
                if pd.isna(size):
                    size = ''

                # Get dish ID from cache
                dish_id = self.dishes_cache.get((full_code, size))
                if not dish_id:
                    # Look up in database
                    cursor.execute(
                        """SELECT id FROM dish 
                           WHERE full_code = %s AND COALESCE(size, '') = %s""",
                        (full_code, size)
                    )
                    result = cursor.fetchone()
                    if result:
                        dish_id = result['id']
                        self.dishes_cache[(full_code, size)] = dish_id
                    else:
                        logger.warning(
                            f"Dish not found for price update: {full_code} (size: {size})")
                        continue

                store_id = row['store_id']
                price = row['dish_price_this_month']

                # Deactivate old prices for this dish/store combination
                cursor.execute(
                    """UPDATE dish_price_history 
                       SET is_active = FALSE 
                       WHERE dish_id = %s AND store_id = %s AND is_active = TRUE""",
                    (dish_id, store_id)
                )

                # Insert new price
                cursor.execute(
                    """INSERT INTO dish_price_history 
                       (dish_id, store_id, price, effective_month, effective_year, is_active)
                       VALUES (%s, %s, %s, %s, %s, TRUE)
                       ON CONFLICT (dish_id, store_id, effective_month, effective_year) 
                       DO UPDATE SET price = EXCLUDED.price, is_active = TRUE""",
                    (dish_id, store_id, price, month, year)
                )
                stats['prices_inserted'] += 1
                logger.debug(
                    f"Updated price for dish {full_code} in store {store_id}: {price}")

            except Exception as e:
                logger.error(
                    f"Error updating price for dish {row.get('full_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1

    def _update_dish_sales(self, conn, df: pd.DataFrame, year: int, month: int, stats: Dict):
        """Step 4: Update dish sales table."""
        cursor = conn.cursor()

        # Sales columns
        sales_columns = ['sale_amount', 'return_amount',
                         'free_amount', 'gift_amount']
        available_sales_columns = [
            col for col in sales_columns if col in df.columns]

        if not available_sales_columns:
            logger.warning("No sales columns found, skipping sales updates")
            return

        # Group by store and dish to aggregate sales
        group_columns = ['store_id', 'full_code']
        if 'size' in df.columns:
            group_columns.append('size')

        # Prepare aggregation dict
        agg_dict = {}
        for col in available_sales_columns:
            agg_dict[col] = 'sum'

        sales_data = df.groupby(group_columns).agg(agg_dict).reset_index()

        for _, row in sales_data.iterrows():
            try:
                full_code = row['full_code']
                size = row.get('size', '') if 'size' in row else ''
                if pd.isna(size):
                    size = ''

                # Get dish ID from cache
                dish_id = self.dishes_cache.get((full_code, size))
                if not dish_id:
                    # Look up in database
                    cursor.execute(
                        """SELECT id FROM dish 
                           WHERE full_code = %s AND COALESCE(size, '') = %s""",
                        (full_code, size)
                    )
                    result = cursor.fetchone()
                    if result:
                        dish_id = result['id']
                        self.dishes_cache[(full_code, size)] = dish_id
                    else:
                        logger.warning(
                            f"Dish not found for sales update: {full_code} (size: {size})")
                        continue

                store_id = row['store_id']

                # Prepare sales data with proper column mapping
                sale_amount = row.get('sale_amount', 0)
                return_amount = row.get('return_amount', 0)
                # Map free_amount to free_meal_amount in database
                free_meal_amount = row.get('free_amount', 0)
                gift_amount = row.get('gift_amount', 0)

                # Insert or update sales record
                cursor.execute(
                    """INSERT INTO dish_monthly_sale 
                       (dish_id, store_id, month, year, sale_amount, return_amount, 
                        free_meal_amount, gift_amount)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (dish_id, store_id, month, year) 
                       DO UPDATE SET 
                           sale_amount = EXCLUDED.sale_amount,
                           return_amount = EXCLUDED.return_amount,
                           free_meal_amount = EXCLUDED.free_meal_amount,
                           gift_amount = EXCLUDED.gift_amount""",
                    (dish_id, store_id, month, year, sale_amount, return_amount,
                     free_meal_amount, gift_amount)
                )
                stats['sales_inserted'] += 1
                logger.debug(
                    f"Updated sales for dish {full_code} in store {store_id}")

            except Exception as e:
                logger.error(
                    f"Error updating sales for dish {row.get('full_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract dishes from Excel files to database'
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
        '--input-dir',
        type=str,
        help='Input directory containing Excel files or path to a single Excel file (optional)'
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

    logger.info(
        f"Connected to {'test' if args.test else 'production'} database")

    # Create extractor and process files
    extractor = DishExtractor(db_manager)
    stats = extractor.extract_dishes_for_month(
        args.year,
        args.month,
        args.input_dir
    )

    # Print summary
    print("\n" + "="*50)
    print("EXTRACTION SUMMARY")
    print("="*50)
    print(f"Files Processed:        {stats.get('files_processed', 0)}")
    print(f"Dish Types Created:     {stats.get('dish_types_created', 0)}")
    print(
        f"Child Types Created:    {stats.get('dish_child_types_created', 0)}")
    print(f"Dishes Created:         {stats.get('dishes_created', 0)}")
    print(f"Dishes Updated:         {stats.get('dishes_updated', 0)}")
    print(f"Prices Inserted:        {stats.get('prices_inserted', 0)}")
    print(f"Sales Records Inserted: {stats.get('sales_inserted', 0)}")
    print(f"Errors:                 {stats.get('errors', 0)}")
    print("="*50)

    # Exit with error if there were any errors
    if stats.get('errors', 0) > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
