#!/usr/bin/env python3
"""
Index script to run all dish-material extraction scripts in sequence.

This script runs the following extractions in order:
1. Dish extraction - Extracts dishes from sales data
2. Material extraction - Extracts materials from export.XLSX 
3. Dish-Material mapping - Creates BOM relationships between dishes and materials
4. Inventory extraction - Extracts inventory counts from store inventory files

Usage:
    python run_all_extractions.py --year 2025 --month 7
    python run_all_extractions.py --year 2025 --month 7 --test  # Use test database
"""

import argparse
import logging
import sys
import subprocess
from pathlib import Path
from typing import Dict, List

# Import file discovery
from file_discovery import discover_all_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_script(script_name: str, args: List[str]) -> bool:
    """
    Run a Python script with given arguments.
    
    Args:
        script_name: Name of the script to run
        args: Command line arguments to pass
        
    Returns:
        True if successful, False otherwise
    """
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    cmd = [sys.executable, str(script_path)] + args
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            logger.error(f"Script {script_name} failed with return code {result.returncode}")
            return False
            
        logger.info(f"Script {script_name} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Run all dish-material extraction scripts in sequence'
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
    parser.add_argument(
        '--skip-dishes',
        action='store_true',
        help='Skip dish extraction'
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
    
    # Optional file paths for custom input files
    parser.add_argument(
        '--dish-input',
        type=str,
        help='Custom input directory/file for dish extraction (overrides auto-discovery)'
    )
    parser.add_argument(
        '--material-input',
        type=str,
        help='Custom input file for material extraction (overrides auto-discovery)'
    )
    parser.add_argument(
        '--mapping-input',
        type=str,
        help='Custom input file for dish-material mapping (overrides auto-discovery)'
    )
    parser.add_argument(
        '--auto-discover',
        action='store_true',
        default=True,
        help='Automatically discover input files based on year/month (default: True)'
    )
    parser.add_argument(
        '--no-auto-discover',
        dest='auto_discover',
        action='store_false',
        help='Disable automatic file discovery'
    )
    
    args = parser.parse_args()
    
    # Validate month
    if not 1 <= args.month <= 12:
        logger.error("Month must be between 1 and 12")
        sys.exit(1)
    
    # Auto-discover files if enabled
    discovered_files = {}
    if args.auto_discover:
        print("\n" + "="*60)
        print("AUTO-DISCOVERING FILES")
        print("="*60)
        discovered_files = discover_all_files(args.year, args.month)
        
        # Use discovered files if not overridden
        if not args.dish_input and discovered_files.get('dish_sales'):
            args.dish_input = str(discovered_files['dish_sales'])
            try:
                print(f"Dish sales: {discovered_files['dish_sales'].name}")
            except UnicodeEncodeError:
                print(f"Dish sales: [file found]")
        
        if not args.material_input and discovered_files.get('materials'):
            args.material_input = str(discovered_files['materials'])
            try:
                print(f"Materials: {discovered_files['materials'].name}")
            except UnicodeEncodeError:
                print(f"Materials: [file found]")
        
        if not args.mapping_input and discovered_files.get('dish_material_mapping'):
            args.mapping_input = str(discovered_files['dish_material_mapping'])
            try:
                print(f"Mapping: {discovered_files['dish_material_mapping'].name}")
            except UnicodeEncodeError:
                print(f"Mapping: [file found]")
    
    # Build common arguments
    common_args = [
        '--year', str(args.year),
        '--month', str(args.month)
    ]
    
    if args.test:
        common_args.append('--test')
    
    print("\n" + "="*60)
    print("DISH-MATERIAL EXTRACTION PIPELINE")
    print("="*60)
    print(f"Year: {args.year}")
    print(f"Month: {args.month}")
    print(f"Database: {'Test' if args.test else 'Production'}")
    print(f"Auto-discover: {args.auto_discover}")
    print("="*60 + "\n")
    
    success = True
    
    # Step 1: Extract dishes
    if not args.skip_dishes:
        print("\n" + "-"*60)
        print("STEP 1: EXTRACTING DISHES")
        print("-"*60)
        
        dish_args = common_args.copy()
        if args.dish_input:
            dish_args.extend(['--input-dir', args.dish_input])
        
        if not run_script('extract_dishes_to_database.py', dish_args):
            logger.error("Dish extraction failed")
            success = False
            if not input("\nDish extraction failed. Continue anyway? (y/n): ").lower().startswith('y'):
                sys.exit(1)
    else:
        logger.info("Skipping dish extraction")
    
    # Step 2: Extract materials
    if not args.skip_materials:
        print("\n" + "-"*60)
        print("STEP 2: EXTRACTING MATERIALS")
        print("-"*60)
        
        material_args = common_args.copy()
        material_args.extend(['--input-file', args.material_input])
        
        if not run_script('extract_materials_to_database.py', material_args):
            logger.error("Material extraction failed")
            success = False
            if not input("\nMaterial extraction failed. Continue anyway? (y/n): ").lower().startswith('y'):
                sys.exit(1)
    else:
        logger.info("Skipping material extraction")
    
    # Step 3: Extract dish-material mappings
    if not args.skip_mapping:
        print("\n" + "-"*60)
        print("STEP 3: EXTRACTING DISH-MATERIAL MAPPINGS")
        print("-"*60)
        
        mapping_args = common_args.copy()
        mapping_args.extend(['--input-file', args.mapping_input])
        
        if not run_script('extract_dish_material_mapping.py', mapping_args):
            logger.error("Dish-material mapping extraction failed")
            success = False
    else:
        logger.info("Skipping dish-material mapping extraction")
    
    # Step 4: Extract inventory counts
    if not args.skip_inventory:
        print("\n" + "-"*60)
        print("STEP 4: EXTRACTING INVENTORY COUNTS")
        print("-"*60)
        
        inventory_args = common_args.copy()
        
        # Check if inventory files exist for this month
        if discovered_files.get('inventory'):
            logger.info(f"Found {len(discovered_files['inventory'])} inventory files")
            
            if not run_script('extract_inventory_to_database.py', inventory_args):
                logger.error("Inventory extraction failed")
                success = False
                if not input("\nInventory extraction failed. Continue anyway? (y/n): ").lower().startswith('y'):
                    sys.exit(1)
        else:
            logger.warning("No inventory files found for this month")
    else:
        logger.info("Skipping inventory extraction")
    
    # Print summary
    print("\n" + "="*60)
    print("EXTRACTION PIPELINE SUMMARY")
    print("="*60)
    
    if success:
        print("[SUCCESS] All extractions completed successfully")
        
        # Print database statistics
        try:
            # Add parent directories to path for imports
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from utils.database import DatabaseManager, DatabaseConfig
            
            db_config = DatabaseConfig(is_test=args.test)
            db_manager = DatabaseManager(db_config)
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get counts
                cursor.execute('SELECT COUNT(*) FROM dish')
                dish_count = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) FROM material')
                material_count = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) FROM dish_material')
                mapping_count = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) FROM inventory_count')
                inventory_count = cursor.fetchone()['count']
                
                print(f"\nDatabase Statistics:")
                print(f"  Dishes:               {dish_count:,}")
                print(f"  Materials:            {material_count:,}")
                print(f"  Dish-Material Links:  {mapping_count:,}")
                print(f"  Inventory Counts:     {inventory_count:,}")
                
        except Exception as e:
            logger.warning(f"Could not retrieve database statistics: {e}")
    else:
        print("[FAILED] Some extractions failed - please review the logs above")
    
    print("="*60 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()