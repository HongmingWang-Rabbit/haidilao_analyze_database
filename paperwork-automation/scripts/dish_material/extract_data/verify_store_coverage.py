#!/usr/bin/env python3
"""
Verify that dish-material mappings exist for all stores and check coverage.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from lib.config import STORE_ID_TO_NAME_MAPPING

def verify_store_coverage():
    """Verify dish-material mapping coverage for all stores."""
    
    db_config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(db_config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("=" * 60)
        print("DISH-MATERIAL MAPPING COVERAGE BY STORE")
        print("=" * 60)
        
        # Get overall statistics
        cursor.execute("""
            SELECT 
                store_id,
                COUNT(DISTINCT dish_id) as unique_dishes,
                COUNT(DISTINCT material_id) as unique_materials,
                COUNT(*) as total_mappings,
                COUNT(DISTINCT CASE WHEN loss_rate != 1.0 THEN id END) as mappings_with_loss
            FROM dish_material
            GROUP BY store_id
            ORDER BY store_id
        """)
        
        results = cursor.fetchall()
        
        for row in results:
            store_name = STORE_ID_TO_NAME_MAPPING.get(row['store_id'], f"Store {row['store_id']}")
            print(f"\n{store_name} (ID: {row['store_id']}):")
            print(f"  - Unique dishes: {row['unique_dishes']}")
            print(f"  - Unique materials: {row['unique_materials']}")
            print(f"  - Total mappings: {row['total_mappings']}")
            print(f"  - Mappings with loss (loss_rate != 1.0): {row['mappings_with_loss']}")
        
        # Check for dishes that don't have mappings in all stores
        print("\n" + "=" * 60)
        print("DISH COVERAGE ANALYSIS")
        print("=" * 60)
        
        cursor.execute("""
            WITH dish_store_counts AS (
                SELECT 
                    dish_id,
                    COUNT(DISTINCT store_id) as store_count
                FROM dish_material
                GROUP BY dish_id
            )
            SELECT 
                d.full_code,
                d.name,
                dsc.store_count
            FROM dish_store_counts dsc
            JOIN dish d ON d.id = dsc.dish_id
            WHERE dsc.store_count < 7
            ORDER BY dsc.store_count DESC, d.full_code
            LIMIT 10
        """)
        
        incomplete_dishes = cursor.fetchall()
        
        if incomplete_dishes:
            print("\nDishes not mapped in all 7 stores (showing first 10):")
            for row in incomplete_dishes:
                print(f"  - {row['full_code']} ({row['name']}): in {row['store_count']} stores only")
        else:
            print("\nAll dishes are mapped in all 7 stores!")
        
        # Check which stores have dishes missing
        cursor.execute("""
            WITH all_dish_store_combinations AS (
                SELECT 
                    d.id as dish_id,
                    s.store_id
                FROM dish d
                CROSS JOIN (SELECT DISTINCT store_id FROM material WHERE store_id <= 7) s
            ),
            existing_mappings AS (
                SELECT DISTINCT dish_id, store_id
                FROM dish_material
                WHERE store_id <= 7
            )
            SELECT 
                ads.store_id,
                COUNT(DISTINCT ads.dish_id) as missing_dishes
            FROM all_dish_store_combinations ads
            LEFT JOIN existing_mappings em 
                ON ads.dish_id = em.dish_id 
                AND ads.store_id = em.store_id
            WHERE em.dish_id IS NULL
            GROUP BY ads.store_id
            ORDER BY ads.store_id
        """)
        
        missing_by_store = cursor.fetchall()
        
        if missing_by_store:
            print("\n" + "=" * 60)
            print("MISSING MAPPINGS BY STORE")
            print("=" * 60)
            for row in missing_by_store:
                if row['missing_dishes'] > 0:
                    store_name = STORE_ID_TO_NAME_MAPPING.get(row['store_id'], f"Store {row['store_id']}")
                    print(f"{store_name}: {row['missing_dishes']} dishes without mappings")

if __name__ == "__main__":
    verify_store_coverage()