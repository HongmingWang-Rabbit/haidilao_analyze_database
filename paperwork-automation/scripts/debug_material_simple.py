#!/usr/bin/env python3
"""
Simple debug script for material extraction issues (no emojis for Windows)
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

# Configure logging for debug
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_material_file_reading():
    """Test reading material files directly"""
    
    print("TESTING MATERIAL FILE READING")
    print("=" * 35)
    
    # Test file path
    test_file = Path("history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls")
    
    if not test_file.exists():
        print(f"ERROR: Test file not found: {test_file}")
        return False
    
    print(f"Testing file: {test_file}")
    print(f"File size: {test_file.stat().st_size} bytes")
    
    # Test reading with different engines
    engines = ['openpyxl', 'xlrd']
    
    for engine in engines:
        print(f"\nTesting engine: {engine}")
        try:
            df = pd.read_excel(test_file, engine=engine, nrows=20)
            print(f"SUCCESS with {engine}: {len(df)} rows, {len(df.columns)} columns")
            print(f"Columns (first 5): {list(df.columns)[:5]}")
            
            # Look for material-related columns
            material_cols = []
            for col in df.columns:
                if any(keyword in str(col) for keyword in ['物料', 'Material', '编号', 'Number']):
                    material_cols.append(col)
            
            print(f"Material-related columns: {material_cols}")
            
            # Show first few rows
            if len(df) > 0:
                print("First few rows:")
                print(df.head(3).to_string())
            
            return True
            
        except Exception as e:
            print(f"FAILED with {engine}: {e}")
    
    return False


def test_material_detail_files():
    """Test reading material detail files"""
    
    print("\n\nTESTING MATERIAL DETAIL FILES")
    print("=" * 35)
    
    # Test material detail folder
    material_detail_folder = Path("history_files/monthly_report_inputs/2025-05/material_detail")
    
    if not material_detail_folder.exists():
        print(f"ERROR: Folder not found: {material_detail_folder}")
        return False
    
    print(f"Testing folder: {material_detail_folder}")
    
    # Check store folders
    store_folders = [f for f in material_detail_folder.iterdir() if f.is_dir()]
    print(f"Store folders found: {[f.name for f in store_folders]}")
    
    # Test first store folder
    if store_folders:
        store_folder = store_folders[0]
        excel_files = list(store_folder.glob("*.xlsx")) + list(store_folder.glob("*.XLSX"))
        
        if excel_files:
            test_file = excel_files[0]
            print(f"\nTesting store file: {test_file}")
            
            try:
                df = pd.read_excel(test_file, nrows=10)
                print(f"SUCCESS: {len(df)} rows, {len(df.columns)} columns")
                print(f"Columns: {list(df.columns)}")
                
                return True
                
            except Exception as e:
                print(f"ERROR reading file: {e}")
                return False
    
    return False


def check_database_materials():
    """Check current database state"""
    
    print("\n\nCHECKING DATABASE STATE")
    print("=" * 25)
    
    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE '%material%'
            """)
            tables = cursor.fetchall()
            print(f"Material-related tables: {[t['table_name'] for t in tables]}")
            
            # Check material count
            cursor.execute("SELECT COUNT(*) as count FROM material")
            material_count = cursor.fetchone()['count']
            print(f"Materials in database: {material_count}")
            
            # Check if store_id column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'material' AND column_name = 'store_id'
            """)
            store_col = cursor.fetchone()
            print(f"Material table has store_id: {'Yes' if store_col else 'No'}")
            
            if material_count > 0:
                cursor.execute("SELECT id, name, material_number, store_id FROM material LIMIT 3")
                samples = cursor.fetchall()
                print("Sample materials:")
                for sample in samples:
                    print(f"  ID:{sample['id']} | {sample['name'][:20]} | #{sample['material_number']} | Store:{sample['store_id']}")
        
        return True
        
    except Exception as e:
        print(f"Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("HAIDILAO MATERIAL EXTRACTION DEBUG")
    print("=" * 35)
    
    # Run tests
    file_test = test_material_file_reading()
    detail_test = test_material_detail_files()
    db_test = check_database_materials()
    
    print(f"\n\nSUMMARY")
    print("=" * 10)
    print(f"Material file reading: {'PASS' if file_test else 'FAIL'}")
    print(f"Material detail files: {'PASS' if detail_test else 'FAIL'}")
    print(f"Database check: {'PASS' if db_test else 'FAIL'}")
    
    if file_test and detail_test:
        print("\nFiles are readable - issue is likely in the extraction logic.")
    else:
        print("\nFiles have issues - check file paths and formats.")