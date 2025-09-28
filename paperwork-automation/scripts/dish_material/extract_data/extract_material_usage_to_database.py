#!/usr/bin/env python3
"""
Extract material usage data from material_detail and monthly_material_usage Excel files.

This script properly creates material_monthly_usage records with material_use_type
populated from material_detail files, regardless of whether inventory data exists.

Processing Steps:
1. Load material types from material_detail file
2. Load material usage from monthly_material_usage files (if available)
3. Create/update material_monthly_usage records with both usage and type data
"""

import argparse
import logging
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for imports - MUST come before local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from lib.excel_utils import safe_read_excel
from scripts.dish_material.extract_data.file_discovery import find_material_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MaterialUsageExtractor:
    """Extract material usage and types from Excel files and store in database."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize the material usage extractor."""
        self.db_manager = db_manager
        self.materials_cache = {}  # Cache for material lookups

    def extract_material_usage_for_month(
        self,
        year: int,
        month: int,
        use_history_files: bool = True
    ) -> Dict[str, int]:
        """
        Extract material usage and types for a specific year and month.

        Args:
            year: Target year
            month: Target month (1-12)
            use_history_files: Whether to use history_files folder structure

        Returns:
            Dictionary with extraction statistics
        """
        stats = {
            'materials_processed': 0,
            'usage_records_created': 0,
            'usage_records_updated': 0,
            'material_types_set': 0,
            'errors': 0
        }

        # Step 1: Load material types from material_detail file
        material_types = self._load_material_types(year, month, use_history_files)
        if not material_types:
            logger.warning(f"No material types found for {year}-{month:02d}")
        else:
            logger.info(f"Loaded {len(material_types)} material types")

        # Step 2: We don't load material usage from files - just set to empty
        # The actual usage will come from inventory extraction if available
        material_usage = {}
        logger.info("Material usage will be populated from inventory extraction")

        # Step 3: Process and store in database
        with self.db_manager.get_connection() as conn:
            try:
                cursor = conn.cursor()

                # First, get all existing material_monthly_usage records for this month
                cursor.execute("""
                    SELECT mmu.id, mmu.material_id, mmu.store_id, m.material_number
                    FROM material_monthly_usage mmu
                    JOIN material m ON m.id = mmu.material_id AND m.store_id = mmu.store_id
                    WHERE mmu.year = %s AND mmu.month = %s
                    ORDER BY mmu.store_id, m.material_number
                """, (year, month))

                existing_records = cursor.fetchall()
                logger.info(f"Found {len(existing_records)} existing material_monthly_usage records")

                # Update existing records with material_use_type
                for record in existing_records:
                    material_number = record['material_number']
                    material_type = material_types.get(material_number)

                    if material_type:
                        cursor.execute("""
                            UPDATE material_monthly_usage
                            SET material_use_type = %s
                            WHERE id = %s
                        """, (material_type, record['id']))
                        stats['material_types_set'] += 1

                    stats['materials_processed'] += 1

                    if stats['materials_processed'] % 500 == 0:
                        logger.info(f"  Processed {stats['materials_processed']} materials...")

                # If no existing records, create them for all materials
                if not existing_records:
                    logger.info("No existing records found, creating material_monthly_usage for all materials")

                    cursor.execute("""
                        SELECT DISTINCT m.id, m.material_number, m.store_id
                        FROM material m
                        WHERE m.is_active = TRUE
                        ORDER BY m.store_id, m.material_number
                    """)

                    all_materials = cursor.fetchall()

                    for material_row in all_materials:
                        material_id = material_row['id']
                        material_number = material_row['material_number']
                        store_id = material_row['store_id']

                        material_type = material_types.get(material_number)

                        cursor.execute("""
                            INSERT INTO material_monthly_usage
                            (material_id, store_id, month, year, material_used, material_use_type)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (material_id, store_id, month, year)
                            DO NOTHING
                        """, (material_id, store_id, month, year, 0, material_type))

                        stats['materials_processed'] += 1
                        if material_type:
                            stats['material_types_set'] += 1

                        if stats['materials_processed'] % 500 == 0:
                            logger.info(f"  Processed {stats['materials_processed']} materials...")

                conn.commit()
                logger.info(f"Successfully committed {stats['materials_processed']} material records")

            except Exception as e:
                conn.rollback()
                logger.error(f"Error during processing: {e}")
                stats['errors'] += 1
                raise

        logger.info(f"Extraction complete. Statistics: {stats}")
        return stats

    def _load_material_types(self, year: int, month: int, use_history_files: bool) -> Dict[str, str]:
        """
        Load material types from material_detail file.

        Returns:
            Dictionary mapping material_number to material_use_type (大类)
        """
        material_types = {}

        # Find the material_detail file
        material_file = find_material_file(year, month, use_history=use_history_files)
        if not material_file or not material_file.exists():
            logger.warning(f"Material detail file not found for {year}-{month:02d}")
            return material_types

        try:
            logger.info(f"Loading material types from {material_file}")

            # Read the Excel file with proper dtype to preserve material numbers
            df = safe_read_excel(str(material_file), dtype_spec={'物料': str})

            # Check if required columns exist
            if '物料' not in df.columns or '大类' not in df.columns:
                logger.warning(f"Required columns (物料, 大类) not found in {material_file}")
                return material_types

            # Build the mapping
            for _, row in df.iterrows():
                material_number = str(row['物料']).strip() if pd.notna(row['物料']) else None
                material_type = str(row['大类']).strip() if pd.notna(row['大类']) else None

                if material_number and material_type:
                    # Remove leading zeros to match with database material codes
                    material_number = material_number.lstrip('0') or '0'
                    material_types[material_number] = material_type

            logger.info(f"Loaded {len(material_types)} material types from material_detail")

        except Exception as e:
            logger.error(f"Error reading material detail file: {e}")

        return material_types



def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract material usage and types from Excel files to database'
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
    extractor = MaterialUsageExtractor(db_manager)
    stats = extractor.extract_material_usage_for_month(
        args.year,
        args.month,
        use_history_files=True
    )

    # Print summary
    print("\n" + "="*50)
    print("MATERIAL USAGE EXTRACTION SUMMARY")
    print("="*50)
    print(f"Materials Processed:    {stats.get('materials_processed', 0)}")
    print(f"Material Types Set:     {stats.get('material_types_set', 0)}")
    print(f"Errors:                 {stats.get('errors', 0)}")
    print("="*50)

    # Exit with error if there were any errors
    if stats.get('errors', 0) > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()