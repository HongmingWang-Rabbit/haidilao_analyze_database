#!/usr/bin/env python3
"""
Extract dish-material mappings (BOM - Bill of Materials) from Excel files and store them in the database.

This script processes the calculated dish material usage Excel files,
extracting the relationship between dishes and materials including quantities.

Processing Steps:
1. Validate dishes exist in database (create if needed)
2. Validate materials exist in database (create if needed)
3. Create/update dish-material relationships with quantities
4. Store serving sizes and waste percentages
"""

# Add parent directory to path for imports - MUST come before local imports

import argparse
import logging
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from configs.dish_material.dish_material_mapping import (
    DISH_MATERIAL_COLUMN_MAPPINGS,
    DISH_MATERIAL_STOREID_MAPPING
)
from lib.excel_utils import safe_read_excel, clean_dish_code
from utils.database import DatabaseManager, DatabaseConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DishMaterialExtractor:
    """Extract dish-material mappings from Excel files and store in database."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the dish-material extractor."""
        self.db_manager = db_manager
        self.dishes_cache = {}  # Cache for dish lookups
        self.materials_cache = {}  # Cache for material lookups
        self.dish_types_cache = {}  # Cache for dish type lookups
        self.dish_child_types_cache = {}  # Cache for dish child type lookups

    def extract_dish_material_mappings(
        self,
        year: int,
        month: int,
        input_file: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Extract dish-material mappings for a specific year and month.

        Args:
            year: Target year
            month: Target month (1-12)
            input_file: Path to Excel file (optional)

        Returns:
            Dictionary with extraction statistics
        """
        if input_file is None:
            # Default input file path
            input_file = f"Input/monthly_report/calculated_dish_material_usage/inventory_calculation_{year}_{month:02d}.xlsx"

        input_path = Path(input_file)
        if not input_path.exists():
            logger.error(f"Input file does not exist: {input_path}")
            return {'error': 'File not found'}

        stats = {
            'rows_processed': 0,
            'dishes_validated': 0,
            'dishes_created': 0,
            'materials_validated': 0,
            'materials_created': 0,
            'mappings_created': 0,
            'mappings_updated': 0,
            'errors': 0
        }

        try:
            logger.info(f"Reading file: {input_path}")

            # Read the Excel file
            df = self._read_and_process_excel(input_path)
            if df is None or df.empty:
                logger.warning(f"No valid data in file: {input_path.name}")
                return stats

            stats['rows_processed'] = len(df)

            # Process in steps
            with self.db_manager.get_connection() as conn:
                try:
                    # Step 1: Validate/create dish types
                    logger.info("Step 1: Validating dish types...")
                    self._validate_dish_types(conn, df, stats)

                    # Step 2: Validate/create dishes
                    logger.info("Step 2: Validating dishes...")
                    self._validate_dishes(conn, df, stats)

                    # Step 3: Skip material validation - materials are store-specific
                    # and will be validated in the mapping step with proper store_id
                    logger.info("Step 3: Skipping material validation (will validate with store_id in mapping step)")

                    # Step 4: Create/update dish-material mappings
                    logger.info("Step 4: Creating dish-material mappings...")
                    self._create_dish_material_mappings(
                        conn, df, year, month, stats)

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

    def _read_and_process_excel(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read Excel file and normalize columns."""
        try:
            # Read Excel with proper dtype for codes
            dtype_spec = {
                '菜品编码': str,
                '物料号': str,
                '菜品短编码': str
            }

            df = safe_read_excel(str(file_path), dtype_spec=dtype_spec)
            logger.info(f"Successfully read Excel file with {len(df)} rows")

            # Rename columns based on mapping
            rename_mapping = {}
            for key, chinese_col in DISH_MATERIAL_COLUMN_MAPPINGS.items():
                if chinese_col in df.columns:
                    rename_mapping[chinese_col] = key

            if not rename_mapping:
                logger.warning(f"No matching columns found in {file_path}")
                return None

            df = df.rename(columns=rename_mapping)

            # Clean dish and material codes
            if 'dish_code' in df.columns:
                df['dish_code'] = df['dish_code'].apply(clean_dish_code)
            if 'dish_short_code' in df.columns:
                df['dish_short_code'] = df['dish_short_code'].apply(
                    clean_dish_code)
            if 'material_number' in df.columns:
                # Remove leading zeros from material numbers to match materials table
                df['material_number'] = df['material_number'].astype(
                    str).str.strip().str.lstrip('0').replace('', '0')

            # Convert numeric columns
            numeric_columns = ['serving_size_kg',
                               'waste_percentage', 'material_unit']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Map store names to IDs
            if 'store_name' in df.columns:
                df['store_id'] = df['store_name'].map(
                    DISH_MATERIAL_STOREID_MAPPING)

            return df

        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
            return None

    def _validate_dish_types(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 1: Validate and create dish types if needed."""
        cursor = conn.cursor()

        if 'dish_type_name' not in df.columns:
            return

        # Get unique dish types, filtering out NaN values
        df_filtered = df[df['dish_type_name'].notna()].copy()
        if df_filtered.empty:
            return

        unique_types = df_filtered[['dish_type_name',
                                    'dish_child_type_name']].drop_duplicates()

        for _, row in unique_types.iterrows():
            type_name = str(row['dish_type_name'])  # Ensure it's a string
            child_type_name = row.get('dish_child_type_name')
            if pd.isna(child_type_name):
                child_type_name = None

            try:
                # Check/create main type
                cursor.execute(
                    "SELECT id FROM dish_type WHERE name = %s",
                    (type_name,)
                )
                result = cursor.fetchone()

                if not result:
                    cursor.execute(
                        """INSERT INTO dish_type (name, is_active) 
                           VALUES (%s, TRUE) RETURNING id""",
                        (type_name,)
                    )
                    type_id = cursor.fetchone()['id']
                    logger.debug(f"Created dish type: {type_name}")
                else:
                    type_id = result['id']

                self.dish_types_cache[type_name] = type_id

                # Check/create child type if present
                if child_type_name and not pd.isna(child_type_name):
                    cursor.execute(
                        """SELECT id FROM dish_child_type 
                           WHERE name = %s AND dish_type_id = %s""",
                        (child_type_name, type_id)
                    )
                    result = cursor.fetchone()

                    if not result:
                        cursor.execute(
                            """INSERT INTO dish_child_type (name, dish_type_id, is_active)
                               VALUES (%s, %s, TRUE) RETURNING id""",
                            (child_type_name, type_id)
                        )
                        child_type_id = cursor.fetchone()['id']
                        logger.debug(
                            f"Created dish child type: {child_type_name}")
                    else:
                        child_type_id = result['id']

                    self.dish_child_types_cache[(
                        type_name, child_type_name)] = child_type_id

            except Exception as e:
                logger.error(f"Error validating dish type {type_name}: {e}")
                stats['errors'] += 1

    def _validate_dishes(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 2: Validate and create dishes if needed."""
        cursor = conn.cursor()

        # Get unique dishes
        dish_columns = ['dish_code', 'dish_name', 'dish_size', 'dish_short_code',
                        'dish_type_name', 'dish_child_type_name', 'serving_size_kg']
        available_columns = [col for col in dish_columns if col in df.columns]

        if 'dish_code' not in available_columns:
            logger.error("dish_code column is required")
            return

        unique_dishes = df[available_columns].drop_duplicates(
            subset=['dish_code', 'dish_size'] if 'dish_size' in available_columns else [
                'dish_code']
        )

        for _, dish_row in unique_dishes.iterrows():
            try:
                dish_code = dish_row['dish_code']
                if pd.isna(dish_code) or not dish_code:
                    continue

                dish_size = dish_row.get('dish_size', '')
                if pd.isna(dish_size):
                    dish_size = ''

                # Check if dish exists
                cursor.execute(
                    """SELECT id FROM dish 
                       WHERE full_code = %s AND COALESCE(size, '') = %s""",
                    (dish_code, dish_size)
                )
                result = cursor.fetchone()

                if result:
                    dish_id = result['id']
                    stats['dishes_validated'] += 1

                    # Update serving size if provided
                    if 'serving_size_kg' in dish_row and not pd.isna(dish_row['serving_size_kg']):
                        cursor.execute(
                            """UPDATE dish SET serving_size_kg = %s WHERE id = %s""",
                            (float(dish_row['serving_size_kg']), dish_id)
                        )
                else:
                    # Create new dish
                    insert_columns = ['full_code', 'size', 'is_active']
                    insert_values = [dish_code, dish_size, True]

                    # Add dish name
                    if 'dish_name' in dish_row and not pd.isna(dish_row['dish_name']):
                        insert_columns.append('name')
                        insert_values.append(dish_row['dish_name'])

                    # Add short code
                    if 'dish_short_code' in dish_row and not pd.isna(dish_row['dish_short_code']):
                        insert_columns.append('short_code')
                        insert_values.append(dish_row['dish_short_code'])

                    # Add serving size
                    if 'serving_size_kg' in dish_row and not pd.isna(dish_row['serving_size_kg']):
                        insert_columns.append('serving_size_kg')
                        insert_values.append(
                            float(dish_row['serving_size_kg']))

                    # Add dish child type if available
                    if 'dish_type_name' in dish_row and 'dish_child_type_name' in dish_row:
                        type_name = dish_row['dish_type_name']
                        child_type_name = dish_row['dish_child_type_name']
                        if not pd.isna(type_name) and not pd.isna(child_type_name):
                            child_type_id = self.dish_child_types_cache.get(
                                (type_name, child_type_name))
                            if child_type_id:
                                insert_columns.append('dish_child_type_id')
                                insert_values.append(child_type_id)

                    placeholders = ', '.join(['%s'] * len(insert_values))
                    columns_str = ', '.join(insert_columns)

                    cursor.execute(
                        f"""INSERT INTO dish ({columns_str})
                            VALUES ({placeholders}) RETURNING id""",
                        insert_values
                    )
                    dish_id = cursor.fetchone()['id']
                    stats['dishes_created'] += 1
                    logger.debug(f"Created dish: {dish_code} (ID: {dish_id})")

                # Cache the dish ID
                self.dishes_cache[(dish_code, dish_size)] = dish_id

            except Exception as e:
                logger.error(
                    f"Error validating dish {dish_row.get('dish_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1

    def _validate_materials(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 3: Validate and create materials if needed."""
        cursor = conn.cursor()

        if 'material_number' not in df.columns:
            logger.error("material_number column is required")
            return

        # Get unique materials
        material_columns = ['material_number', 'material_description', 'unit']
        available_columns = [
            col for col in material_columns if col in df.columns]

        unique_materials = df[available_columns].drop_duplicates(
            subset=['material_number'])

        for _, material_row in unique_materials.iterrows():
            try:
                material_number = str(material_row['material_number']).strip()
                if pd.isna(material_number) or not material_number or material_number == 'nan':
                    continue

                # Remove leading zeros to match materials table
                material_number = material_number.lstrip('0') or '0'

                # Check if material exists for ANY store (we'll handle store-specific lookups later)
                cursor.execute(
                    "SELECT id, store_id FROM material WHERE material_number = %s",
                    (material_number,)
                )
                result = cursor.fetchone()

                if result:
                    material_id = result['id']
                    stats['materials_validated'] += 1
                else:
                    # Skip creating materials - they should already exist from material extraction
                    # Materials without proper store_id and descriptions should not be created here
                    logger.warning(f"Material {material_number} not found in database - skipping")
                    stats['errors'] += 1
                    continue

                # Cache the material ID
                self.materials_cache[material_number] = material_id

            except Exception as e:
                logger.error(
                    f"Error validating material {material_row.get('material_number', 'UNKNOWN')}: {e}")
                stats['errors'] += 1

    def _create_dish_material_mappings(self, conn, df: pd.DataFrame, year: int, month: int, stats: Dict):
        """Step 4: Create or update dish-material mappings."""
        cursor = conn.cursor()

        # Group by unique dish-material-store combinations
        required_cols = ['dish_code', 'material_number', 'store_id']
        if not all(col in df.columns for col in required_cols):
            logger.error("Missing required columns for mappings")
            return

        # Add dish_size to grouping if available
        group_cols = ['dish_code', 'dish_size', 'material_number',
                      'store_id'] if 'dish_size' in df.columns else required_cols

        # Aggregate data
        agg_dict = {}
        if 'serving_size_kg' in df.columns:
            agg_dict['serving_size_kg'] = 'mean'  # Average if multiple entries
        if 'waste_percentage' in df.columns:
            agg_dict['waste_percentage'] = 'mean'
        if 'material_unit' in df.columns:
            agg_dict['material_unit'] = 'mean'

        if agg_dict:
            mapping_data = df.groupby(group_cols).agg(agg_dict).reset_index()
        else:
            mapping_data = df[group_cols].drop_duplicates()

        for _, row in mapping_data.iterrows():
            try:
                dish_code = row['dish_code']
                dish_size = row.get('dish_size', '')
                if pd.isna(dish_size):
                    dish_size = ''

                material_number = str(row['material_number']).strip()
                # Remove leading zeros to match materials table
                material_number = material_number.lstrip('0') or '0'
                store_id = int(row['store_id'])

                # Get dish ID
                dish_id = self.dishes_cache.get((dish_code, dish_size))
                if not dish_id:
                    cursor.execute(
                        """SELECT id FROM dish 
                           WHERE full_code = %s AND COALESCE(size, '') = %s""",
                        (dish_code, dish_size)
                    )
                    result = cursor.fetchone()
                    if result:
                        dish_id = result['id']
                        self.dishes_cache[(dish_code, dish_size)] = dish_id
                    else:
                        logger.warning(
                            f"Dish not found for mapping: {dish_code} (size: {dish_size})")
                        continue

                # Get material ID for this specific store
                cache_key = (material_number, store_id)
                material_id = self.materials_cache.get(cache_key)
                if not material_id:
                    cursor.execute(
                        "SELECT id FROM material WHERE material_number = %s AND store_id = %s",
                        (material_number, store_id)
                    )
                    result = cursor.fetchone()
                    if result:
                        material_id = result['id']
                        self.materials_cache[cache_key] = material_id
                    else:
                        logger.warning(
                            f"Material not found for mapping: {material_number} in store {store_id}")
                        continue

                # Prepare mapping data
                # Use serving_size_kg (出品分量) as the standard quantity
                standard_quantity = row.get('serving_size_kg', 1.0)
                if pd.isna(standard_quantity) or standard_quantity == 0:
                    standard_quantity = 1.0
                
                # Use material_unit (物料单位) as the unit conversion rate
                unit_conversion_rate = row.get('material_unit', 1.0)
                if pd.isna(unit_conversion_rate) or unit_conversion_rate == 0:
                    unit_conversion_rate = 1.0

                # Loss rate from waste_percentage (损耗)
                loss_rate = 1.0
                if 'waste_percentage' in row and not pd.isna(row['waste_percentage']):
                    loss_rate = float(row['waste_percentage'])

                # Check if mapping exists
                cursor.execute(
                    """SELECT id FROM dish_material 
                       WHERE dish_id = %s AND material_id = %s AND store_id = %s""",
                    (dish_id, material_id, store_id)
                )
                result = cursor.fetchone()

                if result:
                    # Update existing mapping
                    cursor.execute(
                        """UPDATE dish_material 
                           SET standard_quantity = %s, loss_rate = %s, unit_conversion_rate = %s
                           WHERE id = %s""",
                        (standard_quantity, loss_rate, unit_conversion_rate, result['id'])
                    )
                    stats['mappings_updated'] += 1
                else:
                    # Create new mapping
                    cursor.execute(
                        """INSERT INTO dish_material 
                           (dish_id, material_id, store_id, standard_quantity, loss_rate, unit_conversion_rate)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (dish_id, material_id, store_id, standard_quantity, loss_rate, unit_conversion_rate)
                    )
                    stats['mappings_created'] += 1

                logger.debug(
                    f"Mapped dish {dish_code} to material {material_number} for store {store_id}")

            except Exception as e:
                logger.error(
                    f"Error creating mapping for dish {row.get('dish_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract dish-material mappings from Excel files to database'
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

    logger.info(
        f"Connected to {'test' if args.test else 'production'} database")

    # Create extractor and process files
    extractor = DishMaterialExtractor(db_manager)
    stats = extractor.extract_dish_material_mappings(
        args.year,
        args.month,
        args.input_file
    )

    # Print summary
    print("\n" + "="*50)
    print("DISH-MATERIAL MAPPING EXTRACTION SUMMARY")
    print("="*50)
    print(f"Rows Processed:        {stats.get('rows_processed', 0)}")
    print(f"Dishes Validated:      {stats.get('dishes_validated', 0)}")
    print(f"Dishes Created:        {stats.get('dishes_created', 0)}")
    print(f"Materials Validated:   {stats.get('materials_validated', 0)}")
    print(f"Materials Created:     {stats.get('materials_created', 0)}")
    print(f"Mappings Created:      {stats.get('mappings_created', 0)}")
    print(f"Mappings Updated:      {stats.get('mappings_updated', 0)}")
    print(f"Errors:                {stats.get('errors', 0)}")
    print("="*50)

    # Exit with error if there were any errors
    if stats.get('errors', 0) > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
