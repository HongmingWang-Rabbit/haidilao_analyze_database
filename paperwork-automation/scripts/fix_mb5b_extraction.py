#!/usr/bin/env python3
"""
Fix MB5B material extraction by properly handling UTF-16 text format
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def read_mb5b_file(file_path: Path) -> pd.DataFrame:
    """Read MB5B file correctly as UTF-16 tab-delimited"""
    
    print(f"Reading MB5B file: {file_path}")
    
    try:
        # Read as UTF-16 tab-delimited text file
        df = pd.read_csv(
            file_path, 
            sep='\t', 
            encoding='utf-16',
            dtype={'物料': str}  # Critical: keep material numbers as strings
        )
        
        print(f"Successfully read: {len(df)} rows, {len(df.columns)} columns")
        # Skip printing column names to avoid Unicode issues
        # print(f"Columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"Error reading MB5B file: {e}")
        return None


def extract_materials_from_mb5b(df: pd.DataFrame, store_mapping: dict) -> int:
    """Extract materials from MB5B dataframe with store-specific logic"""
    
    if df is None or len(df) == 0:
        return 0
    
    print(f"Extracting materials from {len(df)} rows...")
    
    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)
        
        materials_inserted = 0
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    # Extract material information
                    store_code = str(row.get('ValA', '')).strip() if pd.notna(row.get('ValA')) else ''
                    material_number = str(row.get('物料', '')).strip() if pd.notna(row.get('物料')) else ''
                    
                    if not material_number or not store_code:
                        continue
                    
                    # Map store code to store ID
                    store_id = None
                    if store_code.upper() in ['CA01', 'CA1']:
                        store_id = 1
                    elif store_code.upper() in ['CA02', 'CA2']:
                        store_id = 2
                    elif store_code.upper() in ['CA03', 'CA3']:
                        store_id = 3
                    elif store_code.upper() in ['CA04', 'CA4']:
                        store_id = 4
                    elif store_code.upper() in ['CA05', 'CA5']:
                        store_id = 5
                    elif store_code.upper() in ['CA06', 'CA6']:
                        store_id = 6
                    elif store_code.upper() in ['CA07', 'CA7']:
                        store_id = 7
                    
                    if not store_id:
                        continue
                    
                    # Create a basic material name (can be improved)
                    material_name = f"Material_{material_number}"
                    
                    # Insert material
                    cursor.execute("""
                        INSERT INTO material (
                            store_id, material_number, name, unit, is_active
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (store_id, material_number) DO UPDATE SET
                            name = EXCLUDED.name,
                            updated_at = CURRENT_TIMESTAMP
                    """, (store_id, material_number, material_name, 'KG', True))
                    
                    if cursor.rowcount > 0:
                        materials_inserted += 1
                
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
            
            conn.commit()
        
        print(f"Inserted {materials_inserted} materials")
        return materials_inserted
        
    except Exception as e:
        print(f"Error during material extraction: {e}")
        import traceback
        traceback.print_exc()
        return 0


def fix_mb5b_extraction():
    """Fix the MB5B extraction issue"""
    
    print("FIXING MB5B MATERIAL EXTRACTION")
    print("=" * 35)
    
    # Test file
    test_file = Path("history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls")
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return False
    
    # Read the file correctly
    df = read_mb5b_file(test_file)
    
    if df is None:
        print("Failed to read MB5B file")
        return False
    
    # Skip sample data printing to avoid Unicode issues
    # print("\nSample data:")
    # print(df.head(3).to_string())
    
    # Extract materials
    store_mapping = {
        'CA01': 1, 'CA02': 2, 'CA03': 3, 'CA04': 4,
        'CA05': 5, 'CA06': 6, 'CA07': 7
    }
    
    materials_count = extract_materials_from_mb5b(df, store_mapping)
    
    if materials_count > 0:
        print(f"\nSUCCESS: Extracted {materials_count} materials!")
        
        # Verify in database
        try:
            config = DatabaseConfig(is_test=True)
            db_manager = DatabaseManager(config)
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM material")
                total_count = cursor.fetchone()['count']
                print(f"Total materials now in database: {total_count}")
                
                # Show sample materials
                cursor.execute("SELECT store_id, material_number, name FROM material LIMIT 5")
                samples = cursor.fetchall()
                print("\nSample materials in database:")
                for sample in samples:
                    print(f"  Store {sample['store_id']}: #{sample['material_number']} - {sample['name']}")
        
        except Exception as e:
            print(f"Error verifying database: {e}")
        
        return True
    else:
        print("No materials extracted")
        return False


if __name__ == "__main__":
    fix_mb5b_extraction()