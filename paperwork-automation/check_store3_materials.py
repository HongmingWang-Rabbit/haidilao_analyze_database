#!/usr/bin/env python3
import sys
sys.path.append('.')
sys.stdout.reconfigure(encoding='utf-8')

from utils.database import DatabaseManager, DatabaseConfig

def check_store3_materials():
    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check Store 3 materials containing 4515
            cursor.execute("""
                SELECT material_number, name, store_id 
                FROM material 
                WHERE store_id = 3 AND material_number LIKE '%4515%'
                ORDER BY material_number
            """)
            
            materials = cursor.fetchall()
            print(f"Store 3 materials containing '4515': {len(materials)}")
            for mat in materials:
                print(f"  {mat['material_number']} - {mat['name']}")
            
            # Check Store 3 materials containing 'fish' or '巴沙鱼'
            cursor.execute("""
                SELECT material_number, name, store_id 
                FROM material 
                WHERE store_id = 3 AND (name LIKE '%fish%' OR name LIKE '%巴沙鱼%')
                ORDER BY material_number
            """)
            
            fish_materials = cursor.fetchall()
            print(f"\nStore 3 materials containing 'fish' or '巴沙鱼': {len(fish_materials)}")
            for mat in fish_materials:
                print(f"  {mat['material_number']} - {mat['name']}")
            
            # Check total Store 3 materials
            cursor.execute("""
                SELECT COUNT(*) 
                FROM material 
                WHERE store_id = 3
            """)
            
            total = cursor.fetchone()
            print(f"\nTotal Store 3 materials: {total['count']}")
            
            # Show some sample Store 3 materials
            cursor.execute("""
                SELECT material_number, name 
                FROM material 
                WHERE store_id = 3
                ORDER BY material_number
                LIMIT 10
            """)
            
            samples = cursor.fetchall()
            print(f"\nSample Store 3 materials:")
            for mat in samples:
                print(f"  {mat['material_number']} - {mat['name']}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_store3_materials()