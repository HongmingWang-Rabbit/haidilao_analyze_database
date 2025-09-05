#!/usr/bin/env python3
"""
Extract materials from export.XLSX file and store them in the database.

This script processes the material detail export file for a specific year and month,
extracting material information and storing it in the PostgreSQL database.

Processing Steps:
1. Update material_type and material_child_type tables
2. Update material tables with all information
3. Update material price history table
4. Update material monthly usage table
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports - MUST come before local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from configs.dish_material.material_extraction import (
    MATERIAL_COLUMN_MAPPINGS, 
    STORE_CODE_MAPPING,
    MATERIAL_TYPE_MAPPING
)
from lib.excel_utils import safe_read_excel, get_material_reading_dtype
from utils.database import DatabaseManager, DatabaseConfig
from scripts.dish_material.extract_data.file_discovery import find_material_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MaterialExtractor:
    """Extract materials from export.XLSX file and store in database."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the material extractor."""
        self.db_manager = db_manager
        self.material_types_cache = {}  # Cache for material type lookups
        self.material_child_types_cache = {}  # Cache for material child type lookups
        self.materials_cache = {}  # Cache for material lookups
        
    def extract_materials_for_month(
        self,
        year: int,
        month: int,
        input_file: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Extract materials for a specific year and month.
        
        Args:
            year: Target year
            month: Target month (1-12)
            input_file: Path to export.XLSX file (optional)
            
        Returns:
            Dictionary with extraction statistics
        """
        if input_file is None:
            # Use file discovery to find the material file
            material_file = find_material_file(year, month, use_history=True)
            if material_file:
                input_path = material_file
            else:
                logger.error(f"Could not find material file for {year}-{month:02d}")
                return {'error': 'No material file found'}
        else:
            input_path = Path(input_file)
            if not input_path.exists():
                logger.error(f"Input file does not exist: {input_path}")
                return {'error': 'File not found'}
        
        stats = {
            'rows_processed': 0,
            'material_types_created': 0,
            'material_child_types_created': 0,
            'materials_created': 0,
            'materials_updated': 0,
            'prices_inserted': 0,
            'usage_inserted': 0,
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
                    # Step 1: Update material_type and material_child_type tables
                    logger.info("Step 1: Updating material types...")
                    self._update_material_types(conn, df, stats)
                    
                    # Step 2: Update material tables
                    logger.info("Step 2: Updating materials...")
                    self._update_materials(conn, df, stats)
                    
                    # Step 3: Update material price history
                    logger.info("Step 3: Updating material prices...")
                    self._update_material_prices(conn, df, year, month, stats)
                    
                    # Step 4: Update material monthly usage
                    logger.info("Step 4: Updating material usage...")
                    self._update_material_usage(conn, df, year, month, stats)
                    
                    conn.commit()
                    logger.info("All data committed successfully")
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Error during processing, rolling back: {e}")
                    logger.error(f"Transaction error details: {e.__class__.__name__}: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    stats['errors'] += 1
                    raise
                    
        except Exception as e:
            logger.error(f"Error reading {input_path}: {e}")
            stats['errors'] += 1
        
        logger.info(f"Extraction complete. Statistics: {stats}")
        return stats
    
    def _read_and_process_excel(self, file_path: Path, year: int, month: int) -> Optional[pd.DataFrame]:
        """Read export.XLSX file and normalize columns."""
        try:
            # Read Excel with proper dtype for material numbers
            dtype_spec = get_material_reading_dtype()
            df = safe_read_excel(str(file_path), dtype_spec=dtype_spec)
            logger.info(f"Successfully read Excel file with {len(df)} rows")
            
            # Filter for the target month if dates are provided
            if '开始日期' in df.columns:
                df['开始日期'] = pd.to_datetime(df['开始日期'])
                df = df[(df['开始日期'].dt.year == year) & (df['开始日期'].dt.month == month)]
                logger.info(f"Filtered to {len(df)} rows for {year}-{month:02d}")
            
            # Rename columns based on mapping
            rename_mapping = {}
            for key, chinese_col in MATERIAL_COLUMN_MAPPINGS.items():
                if chinese_col in df.columns:
                    rename_mapping[chinese_col] = key
            
            if not rename_mapping:
                logger.warning(f"No matching columns found in {file_path}")
                return None
            
            df = df.rename(columns=rename_mapping)
            
            # Clean material numbers - remove leading zeros
            if 'material_number' in df.columns:
                df['material_number'] = df['material_number'].astype(str).str.lstrip('0').replace('', '0')
            
            # Map store codes to store IDs
            if 'store_code' in df.columns:
                df['store_id'] = df['store_code'].map(STORE_CODE_MAPPING)
                df = df[df['store_id'].notna()]  # Remove invalid stores
            
            # Convert numeric columns
            numeric_columns = ['unit_price', 'quantity', 'total_amount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
            return None
    
    def _update_material_types(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 1: Update material_type and material_child_type tables."""
        cursor = conn.cursor()
        
        # Process material types from 187-一级分类 column
        if 'material_187_level1' not in df.columns:
            logger.warning("No material type column (187-一级分类) found")
            return
        
        # Get unique type combinations
        type_data = df[['material_187_level1', 'material_187_level2']].dropna(subset=['material_187_level1'])
        unique_types = type_data.drop_duplicates()
        
        for _, row in unique_types.iterrows():
            level1 = row['material_187_level1']
            level2 = row.get('material_187_level2')
            
            if pd.isna(level1):
                continue
            
            try:
                # Get or create material type
                type_id = MATERIAL_TYPE_MAPPING.get(level1)
                if type_id:
                    # Ensure type exists in database
                    cursor.execute(
                        """INSERT INTO material_type (id, name, is_active) 
                           VALUES (%s, %s, TRUE)
                           ON CONFLICT (id) DO UPDATE SET is_active = TRUE""",
                        (type_id, level1)
                    )
                    self.material_types_cache[level1] = type_id
                    
                    # Handle child type if present
                    if level2 and not pd.isna(level2):
                        # Check if child type exists
                        cursor.execute(
                            """SELECT id FROM material_child_type 
                               WHERE name = %s AND material_type_id = %s""",
                            (level2, type_id)
                        )
                        result = cursor.fetchone()
                        
                        if not result:
                            cursor.execute(
                                """INSERT INTO material_child_type (name, material_type_id, is_active)
                                   VALUES (%s, %s, TRUE) RETURNING id""",
                                (level2, type_id)
                            )
                            child_type_id = cursor.fetchone()['id']
                            stats['material_child_types_created'] += 1
                            logger.debug(f"Created child type: {level2}")
                        else:
                            child_type_id = result['id']
                        
                        self.material_child_types_cache[(level1, level2)] = child_type_id
                    else:
                        # Create default child type with same name as parent
                        cursor.execute(
                            """SELECT id FROM material_child_type 
                               WHERE name = %s AND material_type_id = %s""",
                            (level1, type_id)
                        )
                        result = cursor.fetchone()
                        
                        if not result:
                            cursor.execute(
                                """INSERT INTO material_child_type (name, material_type_id, is_active)
                                   VALUES (%s, %s, TRUE) RETURNING id""",
                                (level1, type_id)
                            )
                            child_type_id = cursor.fetchone()['id']
                            stats['material_child_types_created'] += 1
                        else:
                            child_type_id = result['id']
                        
                        self.material_child_types_cache[(level1, None)] = child_type_id
                        
            except Exception as e:
                logger.error(f"Error updating material type {level1}: {e}")
                stats['errors'] += 1
    
    def _update_materials(self, conn, df: pd.DataFrame, stats: Dict):
        """Step 2: Update material tables."""
        cursor = conn.cursor()
        
        # Get unique materials - include store_id for store-specific materials
        material_columns = ['material_number', 'material_description', 'unit_description', 
                          'material_187_level1', 'material_187_level2', 'material_187_generic', 'store_id']
        available_columns = [col for col in material_columns if col in df.columns]
        
        if 'material_number' not in available_columns:
            logger.error("material_number column is required")
            return
        
        if 'store_id' not in available_columns:
            logger.error("store_id column is required")
            return
        
        # Group by material_number AND store_id to get unique materials per store
        unique_materials = df[available_columns].drop_duplicates(subset=['material_number', 'store_id'])
        
        for _, material_row in unique_materials.iterrows():
            try:
                material_number = str(material_row['material_number']).strip()
                if not material_number or material_number == 'nan':
                    continue
                
                # Remove leading zeros from material number
                material_number = material_number.lstrip('0') or '0'  # Keep at least one '0' if all zeros
                
                # Get store_id
                store_id = int(material_row['store_id'])
                
                # Get material description (prefer 187-generic if available)
                description = material_row.get('material_187_generic')
                if pd.isna(description) or not description:
                    description = material_row.get('material_description', '')
                
                # Get material child type
                level1 = material_row.get('material_187_level1')
                level2 = material_row.get('material_187_level2')
                child_type_id = None
                
                if level1 and not pd.isna(level1):
                    child_type_id = self.material_child_types_cache.get((level1, level2))
                    if not child_type_id:
                        child_type_id = self.material_child_types_cache.get((level1, None))
                
                # Check if material exists for this store
                cursor.execute(
                    "SELECT id FROM material WHERE material_number = %s AND store_id = %s",
                    (material_number, store_id)
                )
                result = cursor.fetchone()
                
                unit = material_row.get('unit_description', '')
                if pd.isna(unit):
                    unit = ''
                
                if result:
                    # Update existing material
                    material_id = result['id']
                    update_fields = []
                    update_values = []
                    
                    if description:
                        update_fields.extend(["name = %s", "description = %s"])
                        update_values.extend([description, description])
                    
                    if unit:
                        update_fields.append("unit = %s")
                        update_values.append(unit)
                    
                    if child_type_id:
                        update_fields.append("material_child_type_id = %s")
                        update_values.append(child_type_id)
                    
                    update_fields.append("is_active = TRUE")
                    
                    if update_fields:
                        update_values.append(material_id)
                        cursor.execute(
                            f"""UPDATE material SET {', '.join(update_fields)}
                                WHERE id = %s""",
                            update_values
                        )
                        stats['materials_updated'] += 1
                        logger.debug(f"Updated material: {material_number}")
                
                else:
                    # Insert new material with store_id
                    insert_columns = ['material_number', 'store_id', 'is_active']
                    insert_values = [material_number, store_id, True]
                    
                    if description:
                        insert_columns.extend(['name', 'description'])
                        insert_values.extend([description, description])
                    
                    if unit:
                        insert_columns.append('unit')
                        insert_values.append(unit)
                    
                    if child_type_id:
                        insert_columns.append('material_child_type_id')
                        insert_values.append(child_type_id)
                    
                    placeholders = ', '.join(['%s'] * len(insert_values))
                    columns_str = ', '.join(insert_columns)
                    
                    cursor.execute(
                        f"""INSERT INTO material ({columns_str}) 
                            VALUES ({placeholders}) RETURNING id""",
                        insert_values
                    )
                    material_id = cursor.fetchone()['id']
                    stats['materials_created'] += 1
                    logger.debug(f"Created material: {material_number}")
                
                # Cache the material ID with store_id as part of the key
                self.materials_cache[(material_number, store_id)] = material_id
                
            except Exception as e:
                logger.error(f"Error updating material {material_row.get('material_number', 'UNKNOWN')}: {e}")
                logger.error(f"Material details - Number: {material_number}, Description: {description}")
                logger.error(f"SQL Error: {e.__class__.__name__}: {str(e)}")
                stats['errors'] += 1
                # Re-raise to abort the transaction properly
                raise
    
    def _update_material_prices(self, conn, df: pd.DataFrame, year: int, month: int, stats: Dict):
        """Step 3: Update material price history."""
        cursor = conn.cursor()
        
        if 'unit_price' not in df.columns:
            logger.warning("No price column found")
            return
        
        # Group by store and material to get unique prices
        price_data = df[df['unit_price'] > 0].groupby(
            ['store_id', 'material_number']
        ).agg({
            'unit_price': 'mean'  # Take average if multiple entries
        }).reset_index()
        
        for _, row in price_data.iterrows():
            try:
                material_number = str(row['material_number']).strip()
                # Remove leading zeros from material number
                material_number = material_number.lstrip('0') or '0'
                
                store_id = int(row['store_id'])
                
                # Get material ID from cache or database using both material_number and store_id
                material_id = self.materials_cache.get((material_number, store_id))
                if not material_id:
                    cursor.execute(
                        "SELECT id FROM material WHERE material_number = %s AND store_id = %s",
                        (material_number, store_id)
                    )
                    result = cursor.fetchone()
                    if result:
                        material_id = result['id']
                        self.materials_cache[(material_number, store_id)] = material_id
                    else:
                        logger.warning(f"Material not found for price: {material_number} in store {store_id}")
                        continue
                price = float(row['unit_price'])
                
                # Deactivate old prices
                cursor.execute(
                    """UPDATE material_price_history 
                       SET is_active = FALSE 
                       WHERE material_id = %s AND store_id = %s AND is_active = TRUE""",
                    (material_id, store_id)
                )
                
                # Insert new price
                cursor.execute(
                    """INSERT INTO material_price_history 
                       (material_id, store_id, price, effective_month, effective_year, is_active)
                       VALUES (%s, %s, %s, %s, %s, TRUE)
                       ON CONFLICT (material_id, store_id, effective_month, effective_year) 
                       DO UPDATE SET price = EXCLUDED.price, is_active = TRUE""",
                    (material_id, store_id, price, month, year)
                )
                stats['prices_inserted'] += 1
                
            except Exception as e:
                logger.error(f"Error updating price for material {row.get('material_number', 'UNKNOWN')}: {e}")
                stats['errors'] += 1
    
    def _update_material_usage(self, conn, df: pd.DataFrame, year: int, month: int, stats: Dict):
        """Step 4: Update material monthly usage table."""
        cursor = conn.cursor()
        
        # Group by store and material to aggregate usage
        usage_columns = ['quantity', 'total_amount']
        if not all(col in df.columns for col in usage_columns):
            logger.warning("Missing usage columns")
            return
        
        usage_data = df.groupby(['store_id', 'material_number']).agg({
            'quantity': 'sum',
            'total_amount': 'sum'
        }).reset_index()
        
        for _, row in usage_data.iterrows():
            try:
                material_number = str(row['material_number']).strip()
                # Remove leading zeros from material number
                material_number = material_number.lstrip('0') or '0'
                
                store_id = int(row['store_id'])
                
                # Get material ID using both material_number and store_id
                material_id = self.materials_cache.get((material_number, store_id))
                if not material_id:
                    cursor.execute(
                        "SELECT id FROM material WHERE material_number = %s AND store_id = %s",
                        (material_number, store_id)
                    )
                    result = cursor.fetchone()
                    if result:
                        material_id = result['id']
                        self.materials_cache[(material_number, store_id)] = material_id
                    else:
                        logger.warning(f"Material not found for usage: {material_number} in store {store_id}")
                        continue
                quantity = float(row['quantity'])
                amount = float(row['total_amount'])
                
                # Insert or update usage record
                # Note: The column is material_used, not usage_quantity
                cursor.execute(
                    """INSERT INTO material_monthly_usage 
                       (material_id, store_id, month, year, material_used)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (material_id, store_id, month, year) 
                       DO UPDATE SET 
                           material_used = EXCLUDED.material_used""",
                    (material_id, store_id, month, year, quantity)
                )
                stats['usage_inserted'] += 1
                
            except Exception as e:
                logger.error(f"Error updating usage for material {row.get('material_number', 'UNKNOWN')}: {e}")
                stats['errors'] += 1


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract materials from export.XLSX file to database'
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
        help='Path to export.XLSX file (optional)'
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
    extractor = MaterialExtractor(db_manager)
    stats = extractor.extract_materials_for_month(
        args.year,
        args.month,
        args.input_file
    )
    
    # Print summary
    print("\n" + "="*50)
    print("MATERIAL EXTRACTION SUMMARY")
    print("="*50)
    print(f"Rows Processed:          {stats.get('rows_processed', 0)}")
    print(f"Material Types Created:  {stats.get('material_types_created', 0)}")
    print(f"Child Types Created:     {stats.get('material_child_types_created', 0)}")
    print(f"Materials Created:       {stats.get('materials_created', 0)}")
    print(f"Materials Updated:       {stats.get('materials_updated', 0)}")
    print(f"Prices Inserted:         {stats.get('prices_inserted', 0)}")
    print(f"Usage Records Inserted:  {stats.get('usage_inserted', 0)}")
    print(f"Errors:                  {stats.get('errors', 0)}")
    print("="*50)
    
    # Exit with error if there were any errors
    if stats.get('errors', 0) > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()