#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.database import DatabaseManager, DatabaseConfig

def test_db_connection():
    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        print("Testing database connection...")
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Simple test query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"Database version: {version[0]}")
            
            # Check if material table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'material'
                )
            """)
            
            material_exists = cursor.fetchone()[0]
            print(f"Material table exists: {material_exists}")
            
            if material_exists:
                # Get column names directly
                cursor.execute("SELECT * FROM material LIMIT 0")
                col_names = [desc[0] for desc in cursor.description]
                print(f"Material columns: {col_names}")
                
                # Check if there are any materials for store 3
                cursor.execute("SELECT COUNT(*) FROM material WHERE store_id = 3")
                count = cursor.fetchone()[0]
                print(f"Store 3 materials count: {count}")
                
                # Check specific material 4515229
                cursor.execute("SELECT * FROM material WHERE material_number = %s", ("4515229",))
                results = cursor.fetchall()
                print(f"Material 4515229 records: {len(results)}")
                
                if results:
                    for result in results:
                        print(f"  Found: ID={result[0]}, Number={result[1]}, Name={result[2]}, Store={result[8] if len(result) > 8 else 'N/A'}")
                
            # Check material price tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE '%material%price%'
            """)
            
            price_tables = cursor.fetchall()
            print(f"Material price tables: {[t[0] for t in price_tables]}")
                
    except Exception as e:
        print(f"Error details: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_connection()