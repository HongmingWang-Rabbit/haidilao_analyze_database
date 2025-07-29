#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_material_extraction():
    """Test material extraction by checking recent database activity"""
    
    # Run a simple query to see recent material insertions
    try:
        from utils.database import DatabaseManager, DatabaseConfig
        
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            print("Checking recent material activity...")
            
            # Check materials inserted today for store 3
            cursor.execute("""
                SELECT material_number, name, store_id, created_at 
                FROM material 
                WHERE store_id = 3 
                AND created_at::date = CURRENT_DATE
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            recent_materials = cursor.fetchall()
            print(f"Recent Store 3 materials (today): {len(recent_materials)}")
            
            for mat in recent_materials:
                print(f"  {mat[0]} - {mat[1]} ({mat[3]})")
                
                # Check if this is our target material
                if mat[0] == '4515229':
                    print(f"    >>> FOUND TARGET MATERIAL 4515229!")
            
            # Check all materials for store 3
            cursor.execute("""
                SELECT COUNT(*) FROM material WHERE store_id = 3
            """)
            
            total_count = cursor.fetchone()[0]
            print(f"\nTotal Store 3 materials: {total_count}")
            
            # Search for 4515229 specifically
            cursor.execute("""
                SELECT material_number, name, store_id, created_at
                FROM material 
                WHERE material_number = '4515229'
            """)
            
            target_results = cursor.fetchall()
            if target_results:
                print(f"\nFound material 4515229:")
                for result in target_results:
                    print(f"  Number: {result[0]}, Name: {result[1]}, Store: {result[2]}, Created: {result[3]}")
            else:
                print(f"\nMaterial 4515229 NOT found in database")
                
                # Check if any material contains "巴沙鱼"
                cursor.execute("""
                    SELECT material_number, name, store_id
                    FROM material 
                    WHERE name LIKE '%巴沙鱼%' OR description LIKE '%巴沙鱼%'
                """)
                
                fish_results = cursor.fetchall()
                if fish_results:
                    print(f"Found materials containing '巴沙鱼': {len(fish_results)}")
                    for result in fish_results:
                        print(f"  {result[0]} - {result[1]} (Store {result[2]})")
                else:
                    print("No materials containing '巴沙鱼' found")
                
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_material_extraction()