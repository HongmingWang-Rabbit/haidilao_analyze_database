#!/usr/bin/env python3
import sys
sys.path.append('.')
sys.stdout.reconfigure(encoding='utf-8')

from utils.database import DatabaseManager, DatabaseConfig

def check_material_schema():
    """Check the actual material and material_price_history table schemas"""
    
    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            print("🔍 CHECKING MATERIAL TABLE SCHEMA")
            print("=" * 50)
            
            # Check material table schema
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'material' 
                ORDER BY ordinal_position
            """)
            
            material_columns = cursor.fetchall()
            if material_columns:
                print("📋 Material table columns:")
                for col in material_columns:
                    print(f"   {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")
            else:
                print("❌ No material table found or no columns")
            
            print("\n🔍 CHECKING MATERIAL_PRICE_HISTORY TABLE SCHEMA")
            print("=" * 50)
            
            # Check material_price_history table schema
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'material_price_history' 
                ORDER BY ordinal_position
            """)
            
            price_columns = cursor.fetchall()
            if price_columns:
                print("📋 Material_price_history table columns:")
                for col in price_columns:
                    print(f"   {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")
            else:
                print("❌ No material_price_history table found or no columns")
                
                # Check if table exists at all
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name LIKE '%material%'
                """)
                
                material_tables = cursor.fetchall()
                print(f"🔍 Material-related tables found: {[t[0] for t in material_tables]}")
            
            print("\n🔍 CHECKING TABLE CONSTRAINTS")
            print("=" * 50)
            
            # Check constraints on material table
            cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints 
                WHERE table_name = 'material'
            """)
            
            constraints = cursor.fetchall()
            if constraints:
                print("📋 Material table constraints:")
                for constraint in constraints:
                    print(f"   {constraint[0]} ({constraint[1]})")
                    
                    # Get constraint details
                    if constraint[1] == 'UNIQUE':
                        cursor.execute("""
                            SELECT column_name
                            FROM information_schema.constraint_column_usage 
                            WHERE constraint_name = %s
                        """, (constraint[0],))
                        
                        unique_cols = cursor.fetchall()
                        print(f"     Columns: {[col[0] for col in unique_cols]}")
            
            print("\n🔍 SAMPLE MATERIAL DATA")
            print("=" * 50)
            
            # Check some sample materials
            cursor.execute("""
                SELECT material_number, name, store_id, created_at
                FROM material 
                WHERE store_id = 3
                LIMIT 5
            """)
            
            sample_materials = cursor.fetchall()
            if sample_materials:
                print("📋 Sample materials from Store 3:")
                for mat in sample_materials:
                    print(f"   {mat[0]} - {mat[1]} (Store {mat[2]})")
            else:
                print("❌ No materials found for Store 3")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_material_schema()