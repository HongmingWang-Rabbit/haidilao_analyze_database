#!/usr/bin/env python3
"""
File discovery utilities for finding monthly report files dynamically.
"""

import logging
from pathlib import Path
from typing import Optional, List
import re

logger = logging.getLogger(__name__)

# Base directories for monthly reports
INPUT_MONTHLY_REPORT_DIR = Path("D:/personal_programming_work/honeypot_frontend_v2/haidilao_analyze_database/paperwork-automation/Input/monthly_report")
HISTORY_MONTHLY_REPORT_DIR = Path("D:/personal_programming_work/honeypot_frontend_v2/haidilao_analyze_database/paperwork-automation/history_files/monthly_report_inputs")

# Default to history files (more reliable)
USE_HISTORY_FILES = True


def find_dish_sales_file(year: int, month: int, use_history: bool = None) -> Optional[Path]:
    """
    Find dish sales file for the specified year and month.
    
    Looks for files in monthly_dish_sale folder with patterns like:
    - 海外菜品销售报表_YYYYMMDD_*.xlsx
    - 菜品销售报表YYYY-MM-DD_*.xlsx
    - Or any Excel file in the folder (if only one exists)
    """
    if use_history:
        # Use history files structure: history_files/monthly_report_inputs/YYYY-MM/monthly_dish_sale/
        base_dir = HISTORY_MONTHLY_REPORT_DIR / f"{year}-{month:02d}"
        dish_sale_dir = base_dir / "monthly_dish_sale"
    else:
        # Use input folder
        dish_sale_dir = INPUT_MONTHLY_REPORT_DIR / "monthly_dish_sale"
    
    if not dish_sale_dir.exists():
        logger.warning(f"Dish sale directory does not exist: {dish_sale_dir}")
        return None
    
    # Try to find files with year-month pattern
    excel_files = list(dish_sale_dir.glob("*.xlsx")) + list(dish_sale_dir.glob("*.xls"))
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]  # Exclude temp files
    
    if not excel_files:
        logger.warning(f"No Excel files found in {dish_sale_dir}")
        return None
    
    # Try to match files with the target year/month
    year_month_str = f"{year:04d}{month:02d}"
    year_month_dash = f"{year:04d}-{month:02d}"
    
    for file in excel_files:
        filename = file.name
        # Check if filename contains the year-month pattern
        if year_month_str in filename or year_month_dash in filename:
            logger.info(f"Found dish sales file for {year}-{month:02d}: {file.name}")
            return file
    
    # If only one file exists, use it (common case)
    if len(excel_files) == 1:
        logger.info(f"Using only available dish sales file: {excel_files[0].name}")
        return excel_files[0]
    
    # If multiple files exist but none match, log them
    logger.warning(f"Multiple dish sales files found but none match {year}-{month:02d}:")
    for file in excel_files:
        logger.warning(f"  - {file.name}")
    
    # Return the most recently modified file as fallback
    latest_file = max(excel_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Using most recent file: {latest_file.name}")
    return latest_file


def find_material_file(year: int, month: int, use_history: bool = None) -> Optional[Path]:
    """
    Find material export file for the specified year and month.
    
    Looks for files in material_detail folder with patterns like:
    - export.XLSX (default)
    - exportYYYY-MM.XLSX
    - export2025-06.XLSX
    """
    if use_history is None:
        use_history = USE_HISTORY_FILES
    
    if use_history:
        # Use history files structure
        base_dir = HISTORY_MONTHLY_REPORT_DIR / f"{year}-{month:02d}"
        material_dir = base_dir / "material_detail"
    else:
        # Use input folder
        material_dir = INPUT_MONTHLY_REPORT_DIR / "material_detail"
    
    if not material_dir.exists():
        logger.warning(f"Material directory does not exist: {material_dir}")
        return None
    
    # First try specific month file
    month_patterns = [
        f"export{year}-{month:02d}.XLSX",
        f"export{year}-{month}.XLSX",
        f"export_{year}_{month:02d}.XLSX",
        f"export_{year}{month:02d}.XLSX",
    ]
    
    for pattern in month_patterns:
        file_path = material_dir / pattern
        if file_path.exists():
            logger.info(f"Found material file for {year}-{month:02d}: {file_path.name}")
            return file_path
    
    # Fall back to default export.XLSX
    default_file = material_dir / "export.XLSX"
    if default_file.exists():
        logger.info(f"Using default material file: export.XLSX")
        return default_file
    
    # Try to find any Excel file
    excel_files = list(material_dir.glob("*.XLSX")) + list(material_dir.glob("*.xlsx"))
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]
    
    if excel_files:
        # Return most recent
        latest_file = max(excel_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Using most recent material file: {latest_file.name}")
        return latest_file
    
    logger.warning(f"No material files found in {material_dir}")
    return None


def find_dish_material_mapping_file(year: int, month: int, use_history: bool = None) -> Optional[Path]:
    """
    Find dish-material mapping file for the specified year and month.
    
    Looks for files in calculated_dish_material_usage folder.
    """
    if use_history is None:
        use_history = USE_HISTORY_FILES
    
    if use_history:
        # Use history files structure
        base_dir = HISTORY_MONTHLY_REPORT_DIR / f"{year}-{month:02d}"
        mapping_dir = base_dir / "calculated_dish_material_usage"
    else:
        # Use input folder
        mapping_dir = INPUT_MONTHLY_REPORT_DIR / "calculated_dish_material_usage"
    
    if not mapping_dir.exists():
        logger.warning(f"Mapping directory does not exist: {mapping_dir}")
        return None
    
    # Find Excel files
    excel_files = list(mapping_dir.glob("*.xlsx")) + list(mapping_dir.glob("*.xls"))
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]
    
    if not excel_files:
        logger.warning(f"No mapping files found in {mapping_dir}")
        return None
    
    # Try to match year-month pattern
    year_month_str = f"{year:04d}{month:02d}"
    year_month_dash = f"{year:04d}-{month:02d}"
    
    for file in excel_files:
        filename = file.name
        if year_month_str in filename or year_month_dash in filename:
            logger.info(f"Found mapping file for {year}-{month:02d}: {file.name}")
            return file
    
    # Return the most recent file
    latest_file = max(excel_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Using most recent mapping file: {latest_file.name}")
    return latest_file


def find_combo_sales_file(year: int, month: int, use_history: bool = None) -> Optional[Path]:
    """
    Find combo sales file for the specified year and month.
    
    Looks for files in monthly_combo_sale folder.
    """
    if use_history is None:
        use_history = USE_HISTORY_FILES
    
    if use_history:
        # Use history files structure
        base_dir = HISTORY_MONTHLY_REPORT_DIR / f"{year}-{month:02d}"
        combo_dir = base_dir / "monthly_combo_sale"
    else:
        # Use input folder
        combo_dir = INPUT_MONTHLY_REPORT_DIR / "monthly_combo_sale"
    
    if not combo_dir.exists():
        logger.warning(f"Combo sales directory does not exist: {combo_dir}")
        return None
    
    # Find Excel files
    excel_files = list(combo_dir.glob("*.xlsx")) + list(combo_dir.glob("*.xls"))
    excel_files = [f for f in excel_files if not f.name.startswith('~$')]
    
    if not excel_files:
        logger.warning(f"No combo sales files found in {combo_dir}")
        return None
    
    # Try to match year-month pattern
    year_month_str = f"{year:04d}{month:02d}"
    year_month_dash = f"{year:04d}-{month:02d}"
    
    for file in excel_files:
        filename = file.name
        if year_month_str in filename or year_month_dash in filename:
            logger.info(f"Found combo sales file for {year}-{month:02d}: {file.name}")
            return file
    
    # Return the most recent file
    latest_file = max(excel_files, key=lambda f: f.stat().st_mtime)
    logger.info(f"Using most recent combo sales file: {latest_file.name}")
    return latest_file


def find_inventory_files(year: int, month: int, use_history: bool = None) -> List[Path]:
    """
    Find inventory checking files for the specified year and month.
    
    Returns list of paths to store folders containing inventory files.
    """
    if use_history is None:
        use_history = USE_HISTORY_FILES
    
    if use_history:
        # Use history files structure
        base_dir = HISTORY_MONTHLY_REPORT_DIR / f"{year}-{month:02d}"
        inventory_dir = base_dir / "inventory_checking_result"
    else:
        # Use input folder
        inventory_dir = INPUT_MONTHLY_REPORT_DIR / "inventory_checking_result"
    
    if not inventory_dir.exists():
        logger.warning(f"Inventory directory does not exist: {inventory_dir}")
        return []
    
    # Get all store folders (numbered directories)
    store_folders = [d for d in inventory_dir.iterdir() if d.is_dir()]
    
    if not store_folders:
        logger.warning(f"No store folders found in {inventory_dir}")
        return []
    
    logger.info(f"Found {len(store_folders)} store folders for inventory")
    return store_folders


def discover_all_files(year: int, month: int, use_history: bool = None):
    """
    Discover all available files for a given year and month.
    
    Returns a dictionary with file paths for each type.
    """
    if use_history is None:
        use_history = USE_HISTORY_FILES
        
    files = {
        'dish_sales': find_dish_sales_file(year, month, use_history),
        'materials': find_material_file(year, month, use_history),
        'dish_material_mapping': find_dish_material_mapping_file(year, month, use_history),
        'combo_sales': find_combo_sales_file(year, month, use_history),
        'inventory': find_inventory_files(year, month, use_history)
    }
    
    # Log summary
    logger.info(f"\nFile discovery summary for {year}-{month:02d}:")
    for file_type, path in files.items():
        if file_type == 'inventory':
            if path:
                logger.info(f"  {file_type}: {len(path)} store folders found")
            else:
                logger.info(f"  {file_type}: Not found")
        else:
            if path:
                logger.info(f"  {file_type}: {path.name}")
            else:
                logger.info(f"  {file_type}: Not found")
    
    return files


if __name__ == '__main__':
    import argparse
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    parser = argparse.ArgumentParser(description='Discover monthly report files')
    parser.add_argument('--year', type=int, required=True, help='Year')
    parser.add_argument('--month', type=int, required=True, help='Month')
    
    args = parser.parse_args()
    
    print(f"\nDiscovering files for {args.year}-{args.month:02d}...")
    print("="*60)
    
    files = discover_all_files(args.year, args.month)
    
    print("\nResults:")
    print("-"*60)
    for file_type, path in files.items():
        if file_type == 'inventory':
            if path:
                print(f"{file_type:20s}: {len(path)} store folders")
            else:
                print(f"{file_type:20s}: NOT FOUND")
        else:
            if path:
                print(f"{file_type:20s}: {path}")
            else:
                print(f"{file_type:20s}: NOT FOUND")