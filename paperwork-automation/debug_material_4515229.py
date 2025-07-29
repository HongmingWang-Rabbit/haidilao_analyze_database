#!/usr/bin/env python3
import pandas as pd
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

def check_material_in_file():
    """Check if material 4515229 exists in Store 3 file"""
    
    # Store 3 material file path
    store3_file = Path("Input/monthly_report/material_detail/3/ca03-202505.XLSX")
    
    if not store3_file.exists():
        print(f"❌ Store 3 file not found: {store3_file}")
        return
    
    print(f"📁 Reading Store 3 file: {store3_file}")
    
    try:
        # Read the Excel file
        xl_file = pd.ExcelFile(store3_file)
        sheet_names = xl_file.sheet_names
        print(f"📋 Available sheets: {sheet_names}")
        
        # Try to find the material in each sheet
        target_material = "4515229"
        material_found = False
        
        for sheet_name in sheet_names:
            print(f"\n🔍 Checking sheet: {sheet_name}")
            
            try:
                df = pd.read_excel(store3_file, sheet_name=sheet_name, dtype={'物料': str, '物料号': str, '物料编码': str})
                
                print(f"   Rows: {len(df)}")
                print(f"   Columns: {list(df.columns)}")
                
                # Look for material number columns
                material_columns = [col for col in df.columns if any(keyword in str(col) for keyword in ['物料', '编码', '号码', 'material', '料号'])]
                print(f"   Material columns: {material_columns}")
                
                # Search for the target material in each potential column
                for col in material_columns:
                    if col in df.columns:
                        # Convert to string and search
                        material_values = df[col].astype(str)
                        matches = material_values.str.contains(target_material, na=False)
                        
                        if matches.any():
                            print(f"   ✅ Found {target_material} in column '{col}'!")
                            matching_rows = df[matches]
                            print(f"   📄 Matching rows: {len(matching_rows)}")
                            
                            # Show the matching row(s)
                            for idx, row in matching_rows.iterrows():
                                print(f"   Row {idx}:")
                                for key, value in row.items():
                                    if pd.notna(value):
                                        print(f"     {key}: {value}")
                                print()
                            
                            material_found = True
                
                # Also check if any row contains the material number anywhere
                if not material_found:
                    for idx, row in df.iterrows():
                        row_str = ' '.join([str(val) for val in row.values if pd.notna(val)])
                        if target_material in row_str:
                            print(f"   ✅ Found {target_material} in row {idx} (somewhere in the data)")
                            print(f"   📄 Row content: {dict(row)}")
                            material_found = True
                            break
                            
            except Exception as e:
                print(f"   ❌ Error reading sheet {sheet_name}: {e}")
        
        if not material_found:
            print(f"\n❌ Material {target_material} not found in any sheet of Store 3 file")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")

def check_material_in_database():
    """Check if material 4515229 exists in database"""
    try:
        import sys
        sys.path.append('.')
        from utils.database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if material exists in database
            cursor.execute("""
                SELECT m.id, m.material_number, m.name, m.description, m.unit, 
                       m.package_spec, m.material_type_id, m.material_child_type_id, m.store_id
                FROM material m 
                WHERE m.material_number = %s
            """, ("4515229",))
            
            results = cursor.fetchall()
            
            if results:
                print(f"\n✅ Material 4515229 found in database!")
                print(f"📊 Records found: {len(results)}")
                
                for result in results:
                    print(f"   ID: {result[0]}")
                    print(f"   Material Number: {result[1]}")
                    print(f"   Name: {result[2]}")
                    print(f"   Description: {result[3]}")
                    print(f"   Unit: {result[4]}")
                    print(f"   Package Spec: {result[5]}")
                    print(f"   Material Type ID: {result[6]}")
                    print(f"   Material Child Type ID: {result[7]}")
                    print(f"   Store ID: {result[8]}")
                    print()
            else:
                print(f"\n❌ Material 4515229 NOT found in database")
                
                # Check if any similar materials exist
                cursor.execute("""
                    SELECT material_number, name, description, store_id 
                    FROM material 
                    WHERE material_number LIKE %s OR name LIKE %s
                """, ("%4515229%", "%巴沙鱼%"))
                
                similar = cursor.fetchall()
                if similar:
                    print(f"🔍 Found {len(similar)} similar materials:")
                    for mat in similar:
                        print(f"   {mat[0]} - {mat[1]} - Store {mat[3]}")
                else:
                    print("🔍 No similar materials found")
    
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    print("🔍 INVESTIGATING MATERIAL 4515229 巴沙鱼（30LB/箱）")
    print("=" * 60)
    
    print("\n1️⃣ CHECKING STORE 3 FILE:")
    check_material_in_file()
    
    print("\n2️⃣ CHECKING DATABASE:")
    check_material_in_database()