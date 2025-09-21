#!/usr/bin/env python3
"""
Extract dish broad type (菜品8大类描述) from monthly dish general type files.

This script reads dish general type Excel files and updates the broad_type column
in the dish table for each dish based on its code.

File format:
- 菜品编码: Dish code
- 菜品8大类描述: Broad type category (e.g., "荤菜类", "素菜类", "锅底类", "酒水类", "小吃类")
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import List, Dict, Optional

# Add parent directory to path for imports - MUST come before local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from lib.excel_utils import safe_read_excel, clean_dish_code
from lib.config import STORE_IDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DishBroadTypeExtractor:
    """Extract and update dish broad type information from general type files."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the extractor.
        
        Args:
            db_manager: Database manager object
        """
        self.db_manager = db_manager
        
    def find_dish_general_type_file(self, target_date: str) -> Optional[str]:
        """
        Find the dish general type file for the given date.
        
        Args:
            target_date: Target date in YYYY-MM-DD format
            
        Returns:
            Path to the file if found, None otherwise
        """
        # Parse date to get year and month
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        year_month = date_obj.strftime("%Y-%m")
        
        # Build the directory path
        base_path = Path("history_files/monthly_report_inputs") / year_month / "dish_general_type"
        
        if not base_path.exists():
            logger.warning(f"Directory does not exist: {base_path}")
            return None
            
        # Look for Excel files in the directory (ignore temporary files starting with ~$)
        excel_files = [f for f in base_path.glob("*.xlsx") if not f.name.startswith("~$")]
        excel_files += [f for f in base_path.glob("*.xls") if not f.name.startswith("~$")]
        
        if not excel_files:
            logger.warning(f"No Excel files found in {base_path}")
            return None
            
        # Return the first file found (there should typically be only one)
        file_path = str(excel_files[0])
        logger.info(f"Found dish general type file: {file_path}")
        return file_path
        
    def extract_broad_types(self, file_path: str) -> Dict[str, str]:
        """
        Extract dish code to broad type mapping from the file.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dictionary mapping dish codes to broad types
        """
        logger.info(f"Reading dish general type file: {file_path}")
        
        # Read the Excel file, skipping the first row which might be headers
        df = safe_read_excel(file_path, skiprows=1)
        
        # Check column names
        logger.debug(f"Columns found: {list(df.columns)}")
        
        # Find the relevant columns
        dish_code_col = None
        broad_type_col = None
        
        for col in df.columns:
            if '菜品编码' in str(col):
                dish_code_col = col
            elif '菜品8大类描述' in str(col):
                broad_type_col = col
                
        if not dish_code_col or not broad_type_col:
            logger.error(f"Required columns not found. Columns: {list(df.columns)}")
            raise ValueError("Could not find required columns: 菜品编码 and 菜品8大类描述")
            
        # Extract the mapping
        broad_type_map = {}
        
        for _, row in df.iterrows():
            dish_code = row[dish_code_col]
            broad_type = row[broad_type_col]
            
            # Skip empty rows
            if pd.isna(dish_code) or pd.isna(broad_type):
                continue
                
            # Clean the dish code
            dish_code = clean_dish_code(str(dish_code))
            broad_type = str(broad_type).strip()
            
            if dish_code and broad_type:
                broad_type_map[dish_code] = broad_type
                
        logger.info(f"Extracted {len(broad_type_map)} dish broad type mappings")
        return broad_type_map
        
    def update_dish_broad_types(self, broad_type_map: Dict[str, str]) -> int:
        """
        Update the broad_type column in the dish table.
        
        Args:
            broad_type_map: Dictionary mapping dish codes to broad types
            
        Returns:
            Number of dishes updated
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Update each dish's broad type
                updated_count = 0
                
                for dish_code, broad_type in broad_type_map.items():
                    cursor.execute("""
                        UPDATE dish 
                        SET broad_type = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE full_code = %s
                    """, (broad_type, dish_code))
                    
                    updated_count += cursor.rowcount
                    
                conn.commit()
                logger.info(f"Updated broad type for {updated_count} dishes")
                return updated_count
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error updating dish broad types: {e}")
                raise
                
            finally:
                cursor.close()
            
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about dish broad types in the database.
        
        Returns:
            Dictionary with statistics
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Count dishes by broad type
                cursor.execute("""
                    SELECT 
                        broad_type,
                        COUNT(*) as count
                    FROM dish
                    GROUP BY broad_type
                    ORDER BY broad_type
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    broad_type = row[0] if row[0] else 'NULL'
                    stats[broad_type] = row[1]
                    
                return stats
                
            finally:
                cursor.close()


def main():
    """Main function to run the dish broad type extraction."""
    parser = argparse.ArgumentParser(
        description='Extract and update dish broad types from general type files'
    )
    parser.add_argument(
        '--target-date',
        required=True,
        help='Target date in YYYY-MM-DD format'
    )
    parser.add_argument(
        '--file-path',
        help='Optional: Direct path to the dish general type file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without updating the database'
    )
    
    args = parser.parse_args()
    
    try:
        # Connect to database
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        
        extractor = DishBroadTypeExtractor(db_manager)
        
        # Find or use provided file
        if args.file_path:
            file_path = args.file_path
        else:
            file_path = extractor.find_dish_general_type_file(args.target_date)
            
        if not file_path:
            logger.error(f"Could not find dish general type file for {args.target_date}")
            return 1
            
        # Extract broad types
        broad_type_map = extractor.extract_broad_types(file_path)
        
        if args.dry_run:
            logger.info("DRY RUN - Not updating database")
            logger.info(f"Would update {len(broad_type_map)} dishes")
            # Show sample of mappings
            sample_items = list(broad_type_map.items())[:10]
            for code, broad_type in sample_items:
                logger.info(f"  {code} -> {broad_type}")
        else:
            # Update database
            updated_count = extractor.update_dish_broad_types(broad_type_map)
            
            # Show statistics
            stats = extractor.get_statistics()
            logger.info("Dish broad type statistics:")
            for broad_type, count in stats.items():
                logger.info(f"  {broad_type}: {count} dishes")
                
        logger.info("Dish broad type extraction completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())