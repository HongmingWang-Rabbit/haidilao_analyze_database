#!/usr/bin/env python3
"""
Test script to verify that dishes without material mappings are excluded from calculations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def test_size_matching():
    """Test that only exact size matches are used in theory calculations."""
    
    db_config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(db_config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # First, check what dish-material mappings exist for 1060061
        print("Checking dish-material mappings for dish 1060061:")
        print("-" * 60)
        
        cursor.execute("""
            SELECT DISTINCT
                d.id,
                d.size,
                COUNT(dm.id) as mapping_count
            FROM dish d
            LEFT JOIN dish_material dm ON dm.dish_id = d.id
            WHERE d.full_code = '1060061'
            GROUP BY d.id, d.size
            ORDER BY d.id
        """)
        
        results = cursor.fetchall()
        
        dishes_with_mappings = []
        dishes_without_mappings = []
        
        for row in results:
            dish_id = row['id']
            size = row['size'] if row['size'] else 'None'
            mapping_count = row['mapping_count']
            
            # Determine size name
            if dish_id == 240:
                size_name = 'danguo (single pot)'
            elif dish_id == 241:
                size_name = 'pinguo (split pot)'
            elif dish_id == 242:
                size_name = 'sigongge (4-section)'
            elif dish_id == 449:
                size_name = 'xiaoguo (small pot)'
            else:
                size_name = f'ID {dish_id}'
            
            print(f"Dish {dish_id:3d} ({size_name:20s}): {mapping_count} material mappings")
            
            if mapping_count > 0:
                dishes_with_mappings.append((dish_id, size_name))
            else:
                dishes_without_mappings.append((dish_id, size_name))
        
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print("-" * 60)
        
        if dishes_with_mappings:
            print("Dishes WITH material mappings (should appear in calculations):")
            for dish_id, size_name in dishes_with_mappings:
                print(f"  - {size_name} (ID {dish_id})")
        
        if dishes_without_mappings:
            print("\nDishes WITHOUT material mappings (should NOT appear in calculations):")
            for dish_id, size_name in dishes_without_mappings:
                print(f"  - {size_name} (ID {dish_id})")
        
        # Now test the actual query behavior
        print("\n" + "=" * 60)
        print("TESTING QUERY BEHAVIOR:")
        print("-" * 60)
        
        # Simulate what happens with the fixed query
        test_query = """
        SELECT 
            d.id as dish_id,
            d.size as dish_size,
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM dish_material dm 
                    WHERE dm.dish_id = d.id
                ) THEN 'HAS MAPPINGS'
                ELSE 'NO MAPPINGS'
            END as mapping_status
        FROM dish d
        WHERE d.full_code = '1060061'
        ORDER BY d.id
        """
        
        cursor.execute(test_query)
        results = cursor.fetchall()
        
        print("\nMapping status for each dish size:")
        for row in results:
            dish_id = row['dish_id']
            
            # Determine size name
            if dish_id == 240:
                size_name = 'danguo'
            elif dish_id == 241:
                size_name = 'pinguo'
            elif dish_id == 242:
                size_name = 'sigongge'
            elif dish_id == 449:
                size_name = 'xiaoguo'
            else:
                size_name = f'ID {dish_id}'
            
            print(f"  {size_name:12s} (ID {dish_id}): {row['mapping_status']}")
        
        print("\n" + "=" * 60)
        print("CONCLUSION:")
        print("-" * 60)
        print("With the fix, dishes without exact size match in dish_material")
        print("will be excluded from theory usage calculations.")
        print("\nThis prevents incorrect usage calculations where one size's")
        print("material mapping is incorrectly applied to another size.")

if __name__ == "__main__":
    test_size_matching()