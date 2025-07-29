#!/usr/bin/env python3
"""
Modular historical data extraction script using shared extraction modules.
Replaces extract_historical_data_batch.py and extract_historical_data_simple.py with unified approach.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig
from lib.extraction_modules import ExtractionOrchestrator, StoreMapping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalDataExtractor:
    """Unified historical data extraction using modular components"""
    
    def __init__(self, debug: bool = False, is_test: bool = False):
        self.debug = debug
        self.config = DatabaseConfig(is_test=is_test)
        self.db_manager = DatabaseManager(self.config)
        self.orchestrator = ExtractionOrchestrator(self.db_manager, debug)
    
    def extract_from_file(self, file_path: Path, target_date: str) -> Dict[str, int]:
        """Extract data from a single file"""
        logger.info(f"📊 Processing file: {file_path.name}")
        logger.info(f"🗓️ Target date: {target_date}")
        
        try:
            # Use modular extraction
            dish_type_count, dish_child_type_count, dish_count, price_history_count, monthly_sales_count = \
                self.orchestrator.extract_dishes_complete(file_path, target_date)
            
            results = {
                'dish_types': dish_type_count,
                'dish_child_types': dish_child_type_count,
                'dishes': dish_count,
                'price_history': price_history_count,
                'monthly_sales': monthly_sales_count
            }
            
            # Log results
            logger.info("📈 Extraction Results:")
            for category, count in results.items():
                logger.info(f"  {category.replace('_', ' ').title()}: {count}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error processing file {file_path.name}: {e}")
            return {key: 0 for key in ['dish_types', 'dish_child_types', 'dishes', 'price_history', 'monthly_sales']}
    
    def extract_from_directory(self, directory_path: Path, target_date: str, 
                             file_pattern: str = "*.xlsx") -> Dict[str, int]:
        """Extract data from all files in a directory"""
        logger.info(f"📁 Processing directory: {directory_path}")
        
        # Find Excel files
        excel_files = list(directory_path.glob(file_pattern))
        if not excel_files:
            logger.warning(f"No Excel files found matching pattern: {file_pattern}")
            return {key: 0 for key in ['dish_types', 'dish_child_types', 'dishes', 'price_history', 'monthly_sales']}
        
        logger.info(f"Found {len(excel_files)} files to process")
        
        # Aggregate results
        total_results = {key: 0 for key in ['dish_types', 'dish_child_types', 'dishes', 'price_history', 'monthly_sales']}
        
        for file_path in excel_files:
            file_results = self.extract_from_file(file_path, target_date)
            for key in total_results:
                total_results[key] += file_results[key]
        
        # Log total results
        logger.info("🎯 Total Results Across All Files:")
        for category, count in total_results.items():
            logger.info(f"  {category.replace('_', ' ').title()}: {count}")
        
        return total_results
    
    def extract_historical_range(self, base_directory: Path, start_date: str, end_date: str,
                               file_pattern: str = "*.xlsx") -> Dict[str, int]:
        """Extract data for a date range with monthly increments"""
        logger.info(f"📅 Processing historical range: {start_date} to {end_date}")
        
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return {key: 0 for key in ['dish_types', 'dish_child_types', 'dishes', 'price_history', 'monthly_sales']}
        
        total_results = {key: 0 for key in ['dish_types', 'dish_child_types', 'dishes', 'price_history', 'monthly_sales']}
        
        # Process each month
        current_dt = start_dt
        while current_dt <= end_dt:
            month_str = current_dt.strftime('%Y-%m')
            target_date = current_dt.strftime('%Y-%m-%d')
            
            logger.info(f"🗓️ Processing month: {month_str}")
            
            # Look for files for this month
            month_directory = base_directory / month_str
            if month_directory.exists():
                month_results = self.extract_from_directory(month_directory, target_date, file_pattern)
                for key in total_results:
                    total_results[key] += month_results[key]
            else:
                logger.warning(f"Directory not found for {month_str}: {month_directory}")
            
            # Move to next month
            if current_dt.month == 12:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 1)
        
        # Log final results
        logger.info("🏆 Final Historical Extraction Results:")
        for category, count in total_results.items():
            logger.info(f"  {category.replace('_', ' ').title()}: {count}")
        
        return total_results


def main():
    """Main entry point for historical data extraction"""
    parser = argparse.ArgumentParser(
        description='Modular historical data extraction for Haidilao restaurant data'
    )
    parser.add_argument('input_path', help='Path to Excel file or directory')
    parser.add_argument('--target-date', required=True, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date for range processing (YYYY-MM-DD)')
    parser.add_argument('--file-pattern', default='*.xlsx', help='File pattern for directory processing')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    parser.add_argument('--test-db', action='store_true', help='Use test database')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress verbose output')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input path
    input_path = Path(args.input_path)
    if not input_path.exists():
        logger.error(f"❌ Input path not found: {input_path}")
        sys.exit(1)
    
    # Initialize extractor
    extractor = HistoricalDataExtractor(debug=args.debug, is_test=args.test_db)
    
    logger.info("🍲 HAIDILAO MODULAR HISTORICAL DATA EXTRACTION")
    logger.info("=" * 55)
    logger.info(f"📂 Input: {input_path}")
    logger.info(f"🗓️ Target Date: {args.target_date}")
    logger.info(f"🗄️ Database: {'Test' if args.test_db else 'Production'}")
    
    try:
        if input_path.is_file():
            # Single file processing
            results = extractor.extract_from_file(input_path, args.target_date)
            
        elif input_path.is_dir():
            if args.end_date:
                # Date range processing
                results = extractor.extract_historical_range(
                    input_path, args.target_date, args.end_date, args.file_pattern)
            else:
                # Directory processing
                results = extractor.extract_from_directory(
                    input_path, args.target_date, args.file_pattern)
        else:
            logger.error(f"❌ Invalid input path: {input_path}")
            sys.exit(1)
        
        # Summary
        total_records = sum(results.values())
        if total_records > 0:
            logger.info(f"✅ Extraction completed successfully!")
            logger.info(f"📊 Total records processed: {total_records}")
        else:
            logger.warning("⚠️ No data was extracted. Check file format and content.")
            
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()