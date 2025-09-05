#!/usr/bin/env python3
"""
Simple index script to run all dish-material extraction scripts with automatic file discovery.

Usage:
    python run_all.py --year 2025 --month 7
"""

import argparse
import sys
import subprocess
from pathlib import Path
from extract_data.file_discovery import discover_all_files

def run_extraction(script_name, year, month, input_file=None):
    """Run an extraction script."""
    script_path = Path(__file__).parent / script_name
    
    cmd = [sys.executable, str(script_path), '--year', str(year), '--month', str(month)]
    
    if input_file:
        # Use correct parameter based on script
        if 'dishes' in script_name:
            cmd.extend(['--input-dir', input_file])
        else:
            cmd.extend(['--input-file', input_file])
    
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description='Run all dish-material extractions')
    parser.add_argument('--year', type=int, required=True, help='Year (e.g., 2025)')
    parser.add_argument('--month', type=int, required=True, help='Month (1-12)')
    
    args = parser.parse_args()
    
    print(f"\nSTARTING DISH-MATERIAL EXTRACTION FOR {args.year}-{args.month:02d}")
    
    # Auto-discover files
    print("\nAuto-discovering files...")
    discovered_files = discover_all_files(args.year, args.month)
    
    # Run all extractions in order
    success = True
    
    # 1. Dishes
    if discovered_files.get('dish_sales'):
        # Use --input-dir for dish extraction (it accepts both file and dir)
        if not run_extraction('extract_data/extract_dishes_to_database.py', args.year, args.month,
                             str(discovered_files['dish_sales'])):
            print("[WARNING] Dish extraction had issues")
            success = False
    else:
        print("[WARNING] No dish sales file found - skipping dish extraction")
    
    # 2. Materials  
    if discovered_files.get('materials'):
        if not run_extraction('extract_data/extract_materials_to_database.py', args.year, args.month,
                             str(discovered_files['materials'])):
            print("[WARNING] Material extraction had issues")
            success = False
    else:
        print("[WARNING] No material file found - skipping material extraction")
    
    # 3. Mappings
    if discovered_files.get('dish_material_mapping'):
        if not run_extraction('extract_data/extract_dish_material_mapping.py', args.year, args.month,
                             str(discovered_files['dish_material_mapping'])):
            print("[WARNING] Mapping extraction had issues")
            success = False
    else:
        print("[WARNING] No mapping file found - skipping mapping extraction")
    
    # 4. Combo Sales
    if discovered_files.get('combo_sales'):
        if not run_extraction('extract_data/extract_combo_sales_to_database.py', args.year, args.month,
                             str(discovered_files['combo_sales'])):
            print("[WARNING] Combo sales extraction had issues")
            success = False
    else:
        print("[WARNING] No combo sales file found - skipping combo extraction")
    
    # 5. Inventory
    if discovered_files.get('inventory'):
        if not run_extraction('extract_data/extract_inventory_to_database.py', args.year, args.month):
            print("[WARNING] Inventory extraction had issues")
            success = False
    else:
        print("[WARNING] No inventory folders found - skipping inventory extraction")
    
    # 6. Generate Gross Revenue Report
    if not run_extraction('generate_report/generate_gross_revenue_report.py', args.year, args.month):
        print("[WARNING] Gross revenue report generation had issues")
        success = False
    
    print(f"\n{'='*60}")
    if success:
        print("[SUCCESS] ALL EXTRACTIONS COMPLETED SUCCESSFULLY")
    else:
        print("[WARNING] SOME EXTRACTIONS HAD ISSUES - REVIEW OUTPUT ABOVE")
    print(f"{'='*60}\n")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())