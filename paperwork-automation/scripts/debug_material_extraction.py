#!/usr/bin/env python3
"""
Debug script to investigate why material extraction is failing silently
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from scripts.extract_historical_data_batch import HistoricalDataExtractor

# Configure logging for debug
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def debug_single_material_file():
    """Debug material extraction from a single file"""
    
    print("🔍 DEBUGGING MATERIAL EXTRACTION")
    print("=" * 40)
    
    # Test file path
    test_file = Path("history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📂 Testing file: {test_file}")
    print(f"📏 File size: {test_file.stat().st_size} bytes")
    
    try:
        # Try to read the Excel file directly
        print("\n🔍 Step 1: Direct Excel Reading Test")
        
        # Test different engines
        for engine in ['openpyxl', 'xlrd']:
            print(f"   Testing engine: {engine}")
            try:
                df = pd.read_excel(test_file, engine=engine, nrows=10)
                print(f"   ✅ {engine} success: {len(df)} rows, {len(df.columns)} columns")
                print(f"   📋 Columns: {list(df.columns)[:5]}...")  # First 5 columns
                break
            except Exception as e:
                print(f"   ❌ {engine} failed: {e}")
        
        # Test the actual extraction method
        print("\n🔍 Step 2: Extraction Method Test")
        
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)
        extractor = HistoricalDataExtractor(debug=True, is_test=True)
        extractor.db_manager = db_manager
        
        print("   Calling extract_materials_from_monthly_usage...")
        mat_types, mat_child_types, materials = extractor.extract_materials_from_monthly_usage(
            test_file, "2025-05-31"
        )
        
        print(f"   📊 Results:")
        print(f"      Material types: {mat_types}")
        print(f"      Material child types: {mat_child_types}")
        print(f"      Materials: {materials}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def debug_material_detail_extraction():
    """Debug material detail extraction from store folders"""
    
    print("\n🔍 DEBUGGING MATERIAL DETAIL EXTRACTION")
    print("=" * 45)
    
    # Test material detail folder
    material_detail_folder = Path("history_files/monthly_report_inputs/2025-05/material_detail")
    
    if not material_detail_folder.exists():
        print(f"❌ Material detail folder not found: {material_detail_folder}")
        return False
    
    print(f"📂 Testing folder: {material_detail_folder}")
    
    # Check store folders
    store_folders = [f for f in material_detail_folder.iterdir() if f.is_dir()]
    print(f"🏪 Found {len(store_folders)} store folders: {[f.name for f in store_folders]}")
    
    # Test first store folder
    if store_folders:
        store_folder = store_folders[0]
        print(f"\n📁 Testing store folder: {store_folder}")
        
        excel_files = list(store_folder.glob("*.xlsx")) + list(store_folder.glob("*.XLSX"))
        print(f"📊 Excel files found: {len(excel_files)}")
        
        if excel_files:
            test_file = excel_files[0]
            print(f"📄 Testing file: {test_file.name}")
            
            try:
                df = pd.read_excel(test_file, nrows=10)
                print(f"✅ Successfully read: {len(df)} rows, {len(df.columns)} columns")
                print(f"📋 Columns: {list(df.columns)[:5]}...")
                
                # Look for material-related columns
                material_cols = [col for col in df.columns if any(keyword in str(col).lower() 
                                for keyword in ['物料', 'material', '编号', 'number'])]
                print(f"🧱 Material-related columns: {material_cols}")
                
            except Exception as e:
                print(f"❌ Error reading file: {e}")
        
        # Test the actual extraction method
        print("\n🔍 Step 3: Material Detail Extraction Test")
        
        try:
            config = DatabaseConfig(is_test=True)
            db_manager = DatabaseManager(config)
            extractor = HistoricalDataExtractor(debug=True, is_test=True)
            extractor.db_manager = db_manager
            
            print("   Calling extract_material_prices_from_detail_folders...")
            material_prices = extractor.extract_material_prices_from_detail_folders(
                material_detail_folder, "2025-05-31"
            )
            
            print(f"   📊 Material prices extracted: {material_prices}")
            
        except Exception as e:
            print(f"❌ Error during material detail extraction: {e}")
            import traceback
            traceback.print_exc()


def check_database_state():
    """Check current database state for materials"""
    
    print("\n🔍 CHECKING DATABASE STATE")
    print("=" * 30)
    
    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check material table
            cursor.execute("SELECT COUNT(*) as count FROM material")
            material_count = cursor.fetchone()['count']
            print(f"📊 Materials in database: {material_count}")
            
            # Check material_price_history table
            cursor.execute("SELECT COUNT(*) as count FROM material_price_history")
            price_count = cursor.fetchone()['count']
            print(f"💰 Material prices in database: {price_count}")
            
            # Check if material table has store_id column
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'material' AND column_name = 'store_id'
            """)
            store_col = cursor.fetchone()
            print(f"🏪 Material table has store_id: {'Yes' if store_col else 'No'}")
            
            # Sample some materials if any exist
            if material_count > 0:
                cursor.execute("SELECT id, name, material_number, store_id FROM material LIMIT 5")
                samples = cursor.fetchall()
                print(f"📋 Sample materials:")
                for sample in samples:
                    print(f"   ID:{sample['id']} | {sample['name'][:30]} | #{sample['material_number']} | Store:{sample['store_id']}")
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")


if __name__ == "__main__":
    print("🍲 HAIDILAO MATERIAL EXTRACTION DEBUG")
    print("=" * 40)
    
    # Run all debug tests
    debug_single_material_file()
    debug_material_detail_extraction()
    check_database_state()
    
    print("\n🎯 SUMMARY")
    print("=" * 15)
    print("This debug script helps identify why material extraction is failing.")
    print("Check the output above for specific error messages and issues.")