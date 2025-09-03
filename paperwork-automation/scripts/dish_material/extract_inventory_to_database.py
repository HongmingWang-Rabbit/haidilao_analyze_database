#!/usr/bin/env python3
"""
Extract inventory checking results from Excel files and store them in the database.

This script processes inventory count Excel files for a specific year and month,
extracting physical inventory counts and storing them in the PostgreSQL database.

Processing Steps:
1. Read inventory files from each store folder
2. Match materials by material code
3. Store inventory counts with date
"""

import argparse
import logging
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports - MUST come before local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from configs.dish_material.inventory_extraction import (
    INVENTORY_COLUMN_MAPPINGS,
    INVENTORY_STORE_MAPPING,
    INVENTORY_STORE_CODE_MAPPING,
    INVENTORY_FILE_PATTERN
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InventoryExtractor:
    """Extract inventory counts from Excel files and store in database."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the inventory extractor."""
        self.db_manager = db_manager
        self.materials_cache = {}  # Cache for material lookups

    def extract_inventory_for_month(
        self,
        year: int,
        month: int,
        input_dir: Optional[str] = None,
        use_history_files: bool = True
    ) -> Dict[str, int]:
        """
        Extract inventory counts for a specific year and month.

        Args:
            year: Target year
            month: Target month (1-12)
            input_dir: Directory containing inventory folders (optional)
            use_history_files: Whether to use history_files folder structure

        Returns:
            Dictionary with extraction statistics
        """
        if input_dir is None:
            if use_history_files:
                # Use history files structure
                base_dir = Path("history_files/monthly_report_inputs")
                input_dir = base_dir / f"{year}-{month:02d}" / "inventory_checking_result"
            else:
                # Default input directory
                input_dir = Path("Input/monthly_report/inventory_checking_result")

        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"Input directory does not exist: {input_path}")
            return {'error': 'Directory not found'}

        logger.info(f"Processing inventory for {year}-{month:02d}")

        stats = {
            'files_processed': 0,
            'stores_processed': 0,
            'materials_found': 0,
            'materials_not_found': 0,
            'counts_created': 0,
            'counts_updated': 0,
            'errors': 0
        }

        # Process each store folder
        for store_folder in input_path.iterdir():
            if not store_folder.is_dir():
                continue
            
            # Get store ID from folder name
            folder_name = store_folder.name
            store_id = INVENTORY_STORE_MAPPING.get(folder_name)
            
            if not store_id:
                logger.warning(f"Unknown store folder: {folder_name}")
                continue
            
            logger.info(f"Processing store {store_id} from folder {folder_name}")
            stats['stores_processed'] += 1
            
            # Find inventory files in the folder
            inventory_files = list(store_folder.glob("*.xls")) + list(store_folder.glob("*.xlsx"))
            
            for inv_file in inventory_files:
                # Skip temp files
                if inv_file.name.startswith('~$'):
                    continue
                    
                logger.info(f"Processing file: {inv_file}")
                self._process_inventory_file(
                    inv_file, store_id, year, month, stats
                )
                stats['files_processed'] += 1

        logger.info(f"Extraction complete. Statistics: {stats}")
        return stats

    def _process_inventory_file(
        self, 
        file_path: Path, 
        store_id: int,
        year: int,
        month: int,
        stats: Dict
    ):
        """Process a single inventory file."""
        try:
            # Read the file
            df = self._read_and_process_excel(file_path)
            if df is None or df.empty:
                logger.warning(f"No valid data in file: {file_path.name}")
                return
            
            logger.info(f"Processing {len(df)} inventory records for store {store_id}")
            
            # Process records
            with self.db_manager.get_connection() as conn:
                try:
                    self._update_inventory_counts(
                        conn, df, store_id, year, month, stats
                    )
                    conn.commit()
                    logger.info(f"Committed inventory data for store {store_id}")
                    
                except Exception as e:
                    conn.rollback()
                    import traceback
                    logger.error(f"Error processing store {store_id}, rolling back: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    stats['errors'] += 1
                    
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            stats['errors'] += 1

    def _read_and_process_excel(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read Excel file and normalize columns."""
        try:
            # These files have .xls extension but are actually .xlsx
            # Try openpyxl first
            try:
                df = pd.read_excel(str(file_path), engine='openpyxl', dtype={'物料编码': str})
                logger.info(f"Successfully read with openpyxl: {len(df)} rows")
            except:
                # Fall back to default
                df = pd.read_excel(str(file_path), dtype={'物料编码': str})
                logger.info(f"Successfully read with default engine: {len(df)} rows")
            
            # Rename columns based on mapping
            rename_mapping = {}
            for key, chinese_col in INVENTORY_COLUMN_MAPPINGS.items():
                if chinese_col in df.columns:
                    rename_mapping[chinese_col] = key
            
            if not rename_mapping:
                logger.warning(f"No matching columns found in {file_path}")
                return None
            
            df = df.rename(columns=rename_mapping)
            
            # Clean material codes - remove leading zeros
            if 'material_code' in df.columns:
                df['material_code'] = df['material_code'].astype(str).str.strip().str.lstrip('0').replace('', '0')
            
            # Convert numeric columns
            if 'count_quantity' in df.columns:
                df['count_quantity'] = pd.to_numeric(df['count_quantity'], errors='coerce')
                # Remove rows with invalid quantities
                df = df[df['count_quantity'].notna()]
            
            return df
            
        except Exception as e:
            logger.error(f"Error processing Excel file {file_path}: {e}")
            return None

    def _update_inventory_counts(
        self, 
        conn, 
        df: pd.DataFrame, 
        store_id: int,
        year: int,
        month: int,
        stats: Dict
    ):
        """Update inventory counts in database."""
        cursor = conn.cursor()
        
        if 'material_code' not in df.columns or 'count_quantity' not in df.columns:
            logger.error("Required columns missing: material_code and count_quantity")
            return
        
        for _, row in df.iterrows():
            try:
                material_code = str(row['material_code']).strip()
                if not material_code or material_code == 'nan':
                    continue
                
                count_quantity = float(row['count_quantity'])
                
                # Look up material by code and store
                material_id = self._get_material_id(cursor, material_code, store_id)
                
                if not material_id:
                    logger.warning(f"Material not found: {material_code} for store {store_id}")
                    stats['materials_not_found'] += 1
                    continue
                
                stats['materials_found'] += 1
                
                # Check if count already exists (using year/month)
                cursor.execute(
                    """SELECT id FROM inventory_count
                       WHERE store_id = %s AND material_id = %s AND year = %s AND month = %s""",
                    (store_id, material_id, year, month)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing count
                    cursor.execute(
                        """UPDATE inventory_count
                           SET counted_quantity = %s,
                               created_at = CURRENT_TIMESTAMP
                           WHERE id = %s""",
                        (count_quantity, result['id'])
                    )
                    stats['counts_updated'] += 1
                    logger.debug(f"Updated count for material {material_code}: {count_quantity}")
                else:
                    # Insert new count (with year/month)
                    cursor.execute(
                        """INSERT INTO inventory_count
                           (store_id, material_id, year, month, counted_quantity, created_by)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (store_id, material_id, year, month, count_quantity, 'inventory_extraction')
                    )
                    stats['counts_created'] += 1
                    logger.debug(f"Created count for material {material_code}: {count_quantity}")
                
            except Exception as e:
                logger.error(f"Error updating count for material {row.get('material_code', 'UNKNOWN')}: {e}")
                stats['errors'] += 1

    def _get_material_id(self, cursor, material_code: str, store_id: int) -> Optional[int]:
        """Get material ID from cache or database."""
        cache_key = (material_code, store_id)
        
        # Check cache
        if cache_key in self.materials_cache:
            return self.materials_cache[cache_key]
        
        # Look up in database - materials are store-specific
        cursor.execute(
            "SELECT id FROM material WHERE material_number = %s AND store_id = %s",
            (material_code, store_id)
        )
        result = cursor.fetchone()
        
        if result:
            material_id = result['id']
            self.materials_cache[cache_key] = material_id
            return material_id
        
        return None


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract inventory counts from Excel files to database'
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
        help='Input directory containing inventory folders (optional)'
    )
    parser.add_argument(
        '--use-history',
        dest='use_history',
        action='store_true',
        default=True,
        help='Use history_files folder structure (default: True)'
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
    
    # No need to parse count_date anymore as we use year/month

    # Initialize database connection
    db_config = DatabaseConfig(is_test=args.test)
    db_manager = DatabaseManager(db_config)

    # Test database connection
    if not db_manager.test_connection():
        logger.error("Failed to connect to database")
        sys.exit(1)

    logger.info(f"Connected to {'test' if args.test else 'production'} database")

    # Create extractor and process files
    extractor = InventoryExtractor(db_manager)
    stats = extractor.extract_inventory_for_month(
        args.year,
        args.month,
        args.input_dir,
        args.use_history
    )

    # Print summary
    print("\n" + "="*50)
    print("INVENTORY EXTRACTION SUMMARY")
    print("="*50)
    print(f"Files Processed:       {stats.get('files_processed', 0)}")
    print(f"Stores Processed:      {stats.get('stores_processed', 0)}")
    print(f"Materials Found:       {stats.get('materials_found', 0)}")
    print(f"Materials Not Found:   {stats.get('materials_not_found', 0)}")
    print(f"Counts Created:        {stats.get('counts_created', 0)}")
    print(f"Counts Updated:        {stats.get('counts_updated', 0)}")
    print(f"Errors:                {stats.get('errors', 0)}")
    print("="*50)

    # Exit with error if there were any errors
    if stats.get('errors', 0) > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()