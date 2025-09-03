#!/usr/bin/env python3
"""
Extract all historical dish and material data from the history_files folder.

This script automatically discovers and processes all available months in the
history_files/monthly_report_inputs directory, extracting:
1. Dish sales data
2. Material data  
3. Dish-material mappings
4. Combo sales data (if available)

It processes months in chronological order to ensure proper data dependencies.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import re
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from scripts.dish_material.extract_dishes_to_database import DishExtractor
from scripts.dish_material.extract_materials_to_database import MaterialExtractor
from scripts.dish_material.extract_dish_material_mapping import DishMaterialExtractor
from scripts.dish_material.file_discovery import (
    find_dish_sales_file,
    find_material_file,
    find_dish_material_mapping_file,
    HISTORY_MONTHLY_REPORT_DIR
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalDataExtractor:
    """Extract all historical data from history_files folder."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the historical data extractor."""
        self.db_manager = db_manager
        self.dish_extractor = DishExtractor(db_manager)
        self.material_extractor = MaterialExtractor(db_manager)
        self.dish_material_extractor = DishMaterialExtractor(db_manager)
        
    def discover_available_months(self) -> List[Tuple[int, int]]:
        """
        Discover all available months in the history_files folder.
        
        Returns:
            List of (year, month) tuples sorted chronologically
        """
        history_dir = HISTORY_MONTHLY_REPORT_DIR
        
        if not history_dir.exists():
            logger.error(f"History directory does not exist: {history_dir}")
            return []
        
        available_months = []
        
        # Pattern to match YYYY-MM folders
        pattern = re.compile(r'^(\d{4})-(\d{2})$')
        
        for folder in history_dir.iterdir():
            if folder.is_dir():
                match = pattern.match(folder.name)
                if match:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    available_months.append((year, month))
        
        # Sort chronologically
        available_months.sort()
        
        return available_months
    
    def extract_month_data(self, year: int, month: int) -> Dict[str, any]:
        """
        Extract all data for a specific month.
        
        Args:
            year: Target year
            month: Target month
            
        Returns:
            Dictionary with extraction results
        """
        results = {
            'year': year,
            'month': month,
            'dish_extraction': None,
            'material_extraction': None,
            'mapping_extraction': None,
            'success': False
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {year}-{month:02d}")
        logger.info(f"{'='*60}")
        
        try:
            # Step 1: Extract dishes
            logger.info(f"Step 1: Extracting dishes for {year}-{month:02d}...")
            dish_file = find_dish_sales_file(year, month, use_history=True)
            
            if dish_file:
                logger.info(f"  Found dish file: {dish_file.name}")
                dish_stats = self.dish_extractor.extract_dishes_for_month(
                    year, month, str(dish_file)
                )
                results['dish_extraction'] = dish_stats
                
                if dish_stats.get('errors', 0) > 0:
                    logger.warning(f"  Dish extraction had {dish_stats['errors']} errors")
                else:
                    logger.info(f"  ✓ Dishes extracted successfully")
            else:
                logger.warning(f"  No dish file found for {year}-{month:02d}")
            
            # Step 2: Extract materials
            logger.info(f"Step 2: Extracting materials for {year}-{month:02d}...")
            material_file = find_material_file(year, month, use_history=True)
            
            if material_file:
                logger.info(f"  Found material file: {material_file.name}")
                material_stats = self.material_extractor.extract_materials_for_month(
                    year, month, str(material_file)
                )
                results['material_extraction'] = material_stats
                
                if material_stats.get('errors', 0) > 0:
                    logger.warning(f"  Material extraction had {material_stats['errors']} errors")
                else:
                    logger.info(f"  ✓ Materials extracted successfully")
            else:
                logger.warning(f"  No material file found for {year}-{month:02d}")
            
            # Step 3: Extract dish-material mappings
            logger.info(f"Step 3: Extracting dish-material mappings for {year}-{month:02d}...")
            mapping_file = find_dish_material_mapping_file(year, month, use_history=True)
            
            if mapping_file:
                logger.info(f"  Found mapping file: {mapping_file.name}")
                mapping_stats = self.dish_material_extractor.extract_dish_material_mappings(
                    year, month, str(mapping_file)
                )
                results['mapping_extraction'] = mapping_stats
                
                if mapping_stats.get('errors', 0) > 0:
                    logger.warning(f"  Mapping extraction had {mapping_stats['errors']} errors")
                else:
                    logger.info(f"  ✓ Mappings extracted successfully")
            else:
                logger.warning(f"  No mapping file found for {year}-{month:02d}")
            
            # Check overall success
            has_data = (
                results['dish_extraction'] is not None or
                results['material_extraction'] is not None or
                results['mapping_extraction'] is not None
            )
            
            total_errors = sum([
                (results['dish_extraction'] or {}).get('errors', 0),
                (results['material_extraction'] or {}).get('errors', 0),
                (results['mapping_extraction'] or {}).get('errors', 0)
            ])
            
            results['success'] = has_data and total_errors == 0
            
        except Exception as e:
            logger.error(f"Error processing {year}-{month:02d}: {e}")
            results['error'] = str(e)
        
        return results
    
    def extract_all_historical_data(self, start_year: int = None, start_month: int = None,
                                   end_year: int = None, end_month: int = None) -> Dict:
        """
        Extract all historical data from the history_files folder.
        
        Args:
            start_year: Optional start year
            start_month: Optional start month
            end_year: Optional end year
            end_month: Optional end month
            
        Returns:
            Dictionary with overall extraction statistics
        """
        # Discover available months
        available_months = self.discover_available_months()
        
        if not available_months:
            logger.error("No historical data found")
            return {'error': 'No historical data found'}
        
        logger.info(f"Found {len(available_months)} months of historical data")
        logger.info(f"Range: {available_months[0][0]}-{available_months[0][1]:02d} to "
                   f"{available_months[-1][0]}-{available_months[-1][1]:02d}")
        
        # Filter by date range if specified
        if start_year and start_month:
            available_months = [(y, m) for y, m in available_months 
                              if (y, m) >= (start_year, start_month)]
        if end_year and end_month:
            available_months = [(y, m) for y, m in available_months 
                              if (y, m) <= (end_year, end_month)]
        
        # Process each month
        overall_stats = {
            'months_processed': 0,
            'months_successful': 0,
            'months_failed': 0,
            'total_dishes_created': 0,
            'total_dishes_updated': 0,
            'total_materials_created': 0,
            'total_materials_updated': 0,
            'total_mappings_created': 0,
            'total_mappings_updated': 0,
            'total_errors': 0,
            'month_results': []
        }
        
        for year, month in available_months:
            month_result = self.extract_month_data(year, month)
            overall_stats['month_results'].append(month_result)
            overall_stats['months_processed'] += 1
            
            if month_result['success']:
                overall_stats['months_successful'] += 1
            else:
                overall_stats['months_failed'] += 1
            
            # Aggregate statistics
            if month_result['dish_extraction']:
                stats = month_result['dish_extraction']
                overall_stats['total_dishes_created'] += stats.get('dishes_created', 0)
                overall_stats['total_dishes_updated'] += stats.get('dishes_updated', 0)
                overall_stats['total_errors'] += stats.get('errors', 0)
            
            if month_result['material_extraction']:
                stats = month_result['material_extraction']
                overall_stats['total_materials_created'] += stats.get('materials_created', 0)
                overall_stats['total_materials_updated'] += stats.get('materials_updated', 0)
                overall_stats['total_errors'] += stats.get('errors', 0)
            
            if month_result['mapping_extraction']:
                stats = month_result['mapping_extraction']
                overall_stats['total_mappings_created'] += stats.get('mappings_created', 0)
                overall_stats['total_mappings_updated'] += stats.get('mappings_updated', 0)
                overall_stats['total_errors'] += stats.get('errors', 0)
        
        return overall_stats


def print_summary(stats: Dict):
    """Print a formatted summary of the extraction results."""
    print("\n" + "="*70)
    print("HISTORICAL DATA EXTRACTION COMPLETE")
    print("="*70)
    print(f"Months Processed:      {stats['months_processed']}")
    print(f"Successful:            {stats['months_successful']}")
    print(f"Failed:                {stats['months_failed']}")
    print("-"*70)
    print(f"Dishes Created:        {stats['total_dishes_created']}")
    print(f"Dishes Updated:        {stats['total_dishes_updated']}")
    print(f"Materials Created:     {stats['total_materials_created']}")
    print(f"Materials Updated:     {stats['total_materials_updated']}")
    print(f"Mappings Created:      {stats['total_mappings_created']}")
    print(f"Mappings Updated:      {stats['total_mappings_updated']}")
    print(f"Total Errors:          {stats['total_errors']}")
    print("="*70)
    
    if stats['months_failed'] > 0:
        print("\nFailed Months:")
        for result in stats['month_results']:
            if not result['success']:
                print(f"  - {result['year']}-{result['month']:02d}")
                if 'error' in result:
                    print(f"    Error: {result['error']}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract all historical dish and material data'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        help='Start year (e.g., 2024)'
    )
    parser.add_argument(
        '--start-month',
        type=int,
        help='Start month (1-12)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        help='End year (e.g., 2025)'
    )
    parser.add_argument(
        '--end-month',
        type=int,
        help='End month (1-12)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Use test database'
    )
    
    args = parser.parse_args()
    
    # Validate month ranges
    if args.start_month and not 1 <= args.start_month <= 12:
        logger.error("Start month must be between 1 and 12")
        sys.exit(1)
    if args.end_month and not 1 <= args.end_month <= 12:
        logger.error("End month must be between 1 and 12")
        sys.exit(1)
    
    # Initialize database connection
    db_config = DatabaseConfig(is_test=args.test)
    db_manager = DatabaseManager(db_config)
    
    # Test database connection
    if not db_manager.test_connection():
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    logger.info(f"Connected to {'test' if args.test else 'production'} database")
    
    # Create extractor and process all historical data
    extractor = HistoricalDataExtractor(db_manager)
    
    print("\n" + "="*70)
    print("STARTING HISTORICAL DATA EXTRACTION")
    print("="*70)
    
    if args.start_year or args.end_year:
        print(f"Date Range: {args.start_year or 'earliest'}-{args.start_month or '01':02d} to "
              f"{args.end_year or 'latest'}-{args.end_month or '12':02d}")
    else:
        print("Processing all available historical data...")
    
    # Extract all data
    stats = extractor.extract_all_historical_data(
        start_year=args.start_year,
        start_month=args.start_month,
        end_year=args.end_year,
        end_month=args.end_month
    )
    
    # Print summary
    print_summary(stats)
    
    # Exit with error if there were failures
    if stats.get('months_failed', 0) > 0 or stats.get('total_errors', 0) > 0:
        sys.exit(1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())