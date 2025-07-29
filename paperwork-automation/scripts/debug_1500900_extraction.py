#!/usr/bin/env python3
"""
Debug script to trace exactly how material 1500900 冬瓜茶 gets processed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import psycopg2
from utils.database import DatabaseConfig

def check_mb5b_file():
    """Check what values are in the mb5b file for material 1500900"""
    print("=== CHECKING MB5B FILE DATA ===")
    
    file_path = "history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls"
    
    try:
        # Read the UTF-16 TSV file
        df = pd.read_csv(file_path, sep='\t', encoding='utf-16')
        print(f"File shape: {df.shape}")
        
        # Find rows with material 1500900
        mask = df.astype(str).apply(lambda x: x.str.contains('1500900', na=False)).any(axis=1)
        material_rows = df[mask]
        
        print(f"Found {len(material_rows)} rows with material 1500900")
        
        # Check the CA01 row specifically
        ca01_mask = material_rows.astype(str).apply(lambda x: x.str.contains('CA01', na=False)).any(axis=1)
        ca01_rows = material_rows[ca01_mask]
        
        if not ca01_rows.empty:
            print("\n=== CA01 ROW FOR MATERIAL 1500900 ===")
            row = ca01_rows.iloc[0]
            
            # Show all numeric columns that might be usage values
            for i, (col_name, value) in enumerate(zip(df.columns, row)):
                try:
                    # Try to convert to float to see if it's numeric
                    if pd.notna(value):
                        try:
                            float_val = float(value)
                            if float_val != 0:  # Only show non-zero values
                                print(f"Column {i}: '{col_name}' = {float_val}")
                        except (ValueError, TypeError):
                            # Not numeric, check if it contains important text
                            str_val = str(value)
                            if '冬瓜茶' in str_val or 'CA01' in str_val or '1500900' in str_val:
                                print(f"Column {i}: '{col_name}' = '{str_val}'")
                except Exception as e:
                    pass
            
            # Also show ALL values for debugging
            print("\n=== ALL VALUES IN ROW ===")
            for i, value in enumerate(row):
                try:
                    print(f"[{i}]: {repr(value)}")
                except:
                    print(f"[{i}]: [unprintable]")
                    
        return material_rows
        
    except Exception as e:
        print(f"Error reading mb5b file: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_database_values():
    """Check what values are currently in the database"""
    print("\n=== CHECKING DATABASE VALUES ===")
    
    config = DatabaseConfig()
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database
    )
    
    cursor = conn.cursor()
    
    # Get material monthly usage for 1500900
    cursor.execute("""
        SELECT mmu.store_id, mmu.year, mmu.month, mmu.material_used, 
               m.material_number, m.name, mmu.created_at
        FROM material_monthly_usage mmu
        JOIN material m ON m.id = mmu.material_id
        WHERE m.material_number = %s
        ORDER BY mmu.year DESC, mmu.month DESC, mmu.store_id
    """, ('1500900',))
    
    results = cursor.fetchall()
    for store_id, year, month, material_used, material_number, name, created_at in results:
        print(f"Store {store_id}, {year}-{month:02d}: {material_used} (Created: {created_at})")
    
    conn.close()

def trace_extraction_logic():
    """Simulate the extraction logic to see what would be calculated"""
    print("\n=== SIMULATING EXTRACTION LOGIC ===")
    
    # Based on the grep results, the mb5b file shows for CA01 1500900:
    # All values are 0.00 according to the output we saw
    
    print("From mb5b file (CA01 1500900):")
    print("  All numeric values appear to be 0.00")
    print("  But database shows: 8883.5580")
    print("  This suggests either:")
    print("    1. Data was extracted from a different source")
    print("    2. Extraction script has a bug")
    print("    3. Database was manually updated")
    print("    4. Wrong column was read during extraction")

if __name__ == "__main__":
    check_mb5b_file()
    check_database_values()
    trace_extraction_logic()