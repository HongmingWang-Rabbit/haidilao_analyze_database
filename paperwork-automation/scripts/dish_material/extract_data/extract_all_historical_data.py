#!/usr/bin/env python3
"""
Extract all historical dish and material data from the history_files folder.

This script automatically discovers and processes all available months in the
history_files/monthly_report_inputs directory by calling run_all_extractions.py
for each month, ensuring consistency with single-month processing.

It processes months in chronological order to ensure proper data dependencies.
"""

import argparse
import logging
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Path to the history files directory
HISTORY_MONTHLY_REPORT_DIR = Path("history_files/monthly_report_inputs")


def discover_available_months() -> List[Tuple[int, int]]:
    """
    Discover all available months in the history_files folder.
    
    Returns:
        List of (year, month) tuples sorted chronologically
    """
    if not HISTORY_MONTHLY_REPORT_DIR.exists():
        logger.error(f"History directory does not exist: {HISTORY_MONTHLY_REPORT_DIR}")
        return []
    
    available_months = []
    
    # Pattern to match YYYY-MM folders
    pattern = re.compile(r'^(\d{4})-(\d{2})$')
    
    for folder in HISTORY_MONTHLY_REPORT_DIR.iterdir():
        if folder.is_dir():
            match = pattern.match(folder.name)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                available_months.append((year, month))
    
    # Sort chronologically
    available_months.sort()
    
    return available_months


def run_extraction_for_month(year: int, month: int, test_db: bool = False, 
                            skip_options: List[str] = None) -> Dict[str, any]:
    """
    Run the extraction for a specific month by calling run_all_extractions.py.
    
    Args:
        year: Target year
        month: Target month
        test_db: Whether to use test database
        skip_options: List of skip flags to pass (e.g., ['--skip-inventory'])
        
    Returns:
        Dictionary with extraction results
    """
    results = {
        'year': year,
        'month': month,
        'success': False,
        'return_code': None,
        'stdout': '',
        'stderr': ''
    }
    
    # Build the command
    run_all_script = Path(__file__).parent / "run_all_extractions.py"
    
    cmd = [
        sys.executable,
        str(run_all_script),
        '--year', str(year),
        '--month', str(month)
    ]
    
    if test_db:
        cmd.append('--test')
    
    # Add skip options if provided
    if skip_options:
        cmd.extend(skip_options)
    
    logger.info(f"Running extraction for {year}-{month:02d}")
    logger.debug(f"Command: {' '.join(cmd)}")
    
    try:
        # Run the extraction script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=Path(__file__).parent.parent.parent.parent  # Run from project root
        )
        
        results['return_code'] = result.returncode
        results['stdout'] = result.stdout
        results['stderr'] = result.stderr
        results['success'] = (result.returncode == 0)
        
        if results['success']:
            logger.info(f"  ✓ Successfully processed {year}-{month:02d}")
        else:
            logger.error(f"  ✗ Failed to process {year}-{month:02d} (exit code: {result.returncode})")
            if result.stderr:
                logger.error(f"  Error output: {result.stderr[:500]}")  # First 500 chars of error
        
    except Exception as e:
        logger.error(f"Error running extraction for {year}-{month:02d}: {e}")
        results['error'] = str(e)
    
    return results


def extract_all_historical_data(start_year: int = None, start_month: int = None,
                               end_year: int = None, end_month: int = None,
                               test_db: bool = False, skip_options: List[str] = None) -> Dict:
    """
    Extract all historical data from the history_files folder.
    
    Args:
        start_year: Optional start year
        start_month: Optional start month
        end_year: Optional end year
        end_month: Optional end month
        test_db: Whether to use test database
        skip_options: List of skip flags to pass to run_all_extractions.py
        
    Returns:
        Dictionary with overall extraction statistics
    """
    # Discover available months
    available_months = discover_available_months()
    
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
        'month_results': [],
        'failed_months': []
    }
    
    for year, month in available_months:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {year}-{month:02d}")
        logger.info(f"{'='*60}")
        
        month_result = run_extraction_for_month(year, month, test_db, skip_options)
        overall_stats['month_results'].append(month_result)
        overall_stats['months_processed'] += 1
        
        if month_result['success']:
            overall_stats['months_successful'] += 1
            
            # Parse and display summary from stdout if available
            if month_result['stdout']:
                # Try to extract database statistics from the output
                for line in month_result['stdout'].split('\n'):
                    if 'Database Statistics:' in line:
                        # Print the statistics section
                        logger.info("  Database Statistics from extraction:")
                        in_stats = True
                        continue
                    elif line.startswith('  ') and 'in_stats' in locals() and in_stats:
                        logger.info(f"    {line.strip()}")
                    elif line.startswith('=') and 'in_stats' in locals() and in_stats:
                        break
        else:
            overall_stats['months_failed'] += 1
            overall_stats['failed_months'].append(f"{year}-{month:02d}")
    
    return overall_stats


def print_summary(stats: Dict):
    """Print a formatted summary of the extraction results."""
    print("\n" + "="*70)
    print("HISTORICAL DATA EXTRACTION COMPLETE")
    print("="*70)
    print(f"Months Processed:      {stats['months_processed']}")
    print(f"Successful:            {stats['months_successful']}")
    print(f"Failed:                {stats['months_failed']}")
    
    if stats['failed_months']:
        print("-"*70)
        print("Failed Months:")
        for month in stats['failed_months']:
            print(f"  - {month}")
    
    print("="*70)
    
    # Get final database statistics if possible
    try:
        # Add parent directories to path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from utils.database import DatabaseManager, DatabaseConfig
        
        # Use the same database as specified in arguments
        db_config = DatabaseConfig(is_test=stats.get('test_db', False))
        db_manager = DatabaseManager(db_config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get counts
            cursor.execute('SELECT COUNT(*) FROM dish')
            dish_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) FROM dish WHERE broad_type IS NOT NULL')
            dishes_with_broad_type = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) FROM material')
            material_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) FROM dish_material')
            mapping_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) FROM inventory_count')
            inventory_count = cursor.fetchone()['count']
            
            print("\nFinal Database Statistics:")
            print(f"  Dishes:                 {dish_count:,}")
            print(f"  Dishes with Broad Type: {dishes_with_broad_type:,}")
            print(f"  Materials:              {material_count:,}")
            print(f"  Dish-Material Links:    {mapping_count:,}")
            print(f"  Inventory Counts:       {inventory_count:,}")
            
    except Exception as e:
        logger.warning(f"Could not retrieve database statistics: {e}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract all historical dish and material data by calling run_all_extractions.py for each month'
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
    
    # Skip options to pass through to run_all_extractions.py
    parser.add_argument(
        '--skip-dishes',
        action='store_true',
        help='Skip dish extraction'
    )
    parser.add_argument(
        '--skip-broad-type',
        action='store_true',
        help='Skip dish broad type extraction'
    )
    parser.add_argument(
        '--skip-materials',
        action='store_true',
        help='Skip material extraction'
    )
    parser.add_argument(
        '--skip-mapping',
        action='store_true',
        help='Skip dish-material mapping extraction'
    )
    parser.add_argument(
        '--skip-inventory',
        action='store_true',
        help='Skip inventory extraction'
    )
    
    args = parser.parse_args()
    
    # Validate month ranges
    if args.start_month and not 1 <= args.start_month <= 12:
        logger.error("Start month must be between 1 and 12")
        sys.exit(1)
    if args.end_month and not 1 <= args.end_month <= 12:
        logger.error("End month must be between 1 and 12")
        sys.exit(1)
    
    # Build skip options list
    skip_options = []
    if args.skip_dishes:
        skip_options.append('--skip-dishes')
    if args.skip_broad_type:
        skip_options.append('--skip-broad-type')
    if args.skip_materials:
        skip_options.append('--skip-materials')
    if args.skip_mapping:
        skip_options.append('--skip-mapping')
    if args.skip_inventory:
        skip_options.append('--skip-inventory')
    
    print("\n" + "="*70)
    print("STARTING HISTORICAL DATA EXTRACTION")
    print("="*70)
    print(f"Database: {'Test' if args.test else 'Production'}")
    
    if args.start_year or args.end_year:
        print(f"Date Range: {args.start_year or 'earliest'}-{args.start_month or '01':02d} to "
              f"{args.end_year or 'latest'}-{args.end_month or '12':02d}")
    else:
        print("Processing all available historical data...")
    
    if skip_options:
        print(f"Skipping: {', '.join(opt.replace('--skip-', '') for opt in skip_options)}")
    
    # Extract all data
    stats = extract_all_historical_data(
        start_year=args.start_year,
        start_month=args.start_month,
        end_year=args.end_year,
        end_month=args.end_month,
        test_db=args.test,
        skip_options=skip_options
    )
    
    stats['test_db'] = args.test  # Store for use in print_summary
    
    # Print summary
    print_summary(stats)
    
    # Exit with error if there were failures
    if stats.get('months_failed', 0) > 0:
        sys.exit(1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())