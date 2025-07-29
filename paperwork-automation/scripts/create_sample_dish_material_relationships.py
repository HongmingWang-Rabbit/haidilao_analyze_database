#!/usr/bin/env python3
"""
Create sample dish-material relationships since calculated_dish_material_usage folder is empty
"""

import sys
import os
from pathlib import Path
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def create_sample_dish_material_relationships():
    """Create realistic dish-material relationships"""
    
    print("CREATING SAMPLE DISH-MATERIAL RELATIONSHIPS")
    print("=" * 45)
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Getting available dishes and materials...")
        
        # Get dishes by store
        cursor.execute("""
            SELECT d.id, d.store_id, d.full_code, d.name, d.size 
            FROM dish d 
            ORDER BY d.store_id, d.id 
            LIMIT 200
        """)
        dishes = cursor.fetchall()
        
        # Get materials by store  
        cursor.execute("""
            SELECT m.id, m.store_id, m.material_number, m.name, m.material_type_id
            FROM material m
            ORDER BY m.store_id, m.id
            LIMIT 500
        """)
        materials = cursor.fetchall()
        
        print(f"   Found {len(dishes)} dishes")
        print(f"   Found {len(materials)} materials")
        
        # Group by store
        dishes_by_store = {}
        materials_by_store = {}
        
        for dish in dishes:
            store_id = dish['store_id']
            if store_id not in dishes_by_store:
                dishes_by_store[store_id] = []
            dishes_by_store[store_id].append(dish)
        
        for material in materials:
            store_id = material['store_id']
            if store_id not in materials_by_store:
                materials_by_store[store_id] = []
            materials_by_store[store_id].append(material)
        
        print("2. Creating dish-material relationships...")
        
        total_relationships = 0
        
        for store_id in range(1, 8):  # Stores 1-7
            if store_id not in dishes_by_store or store_id not in materials_by_store:
                continue
                
            store_dishes = dishes_by_store[store_id]
            store_materials = materials_by_store[store_id]
            
            print(f"   Store {store_id}: {len(store_dishes)} dishes, {len(store_materials)} materials")
            
            store_relationships = 0
            
            # Create relationships for each dish
            for dish in store_dishes:
                # Each dish uses 2-8 materials on average
                num_materials = random.randint(2, 8)
                
                # Select random materials for this dish
                selected_materials = random.sample(store_materials, min(num_materials, len(store_materials)))
                
                for material in selected_materials:
                    # Create realistic quantities based on material type
                    if material['material_type_id'] == 18:  # Food Ingredients
                        standard_qty = round(random.uniform(0.1, 2.0), 3)
                    elif material['material_type_id'] == 19:  # Beverages  
                        standard_qty = round(random.uniform(0.05, 0.5), 3)
                    elif material['material_type_id'] == 23:  # Disposables
                        standard_qty = round(random.uniform(1.0, 5.0), 0)
                    else:
                        standard_qty = round(random.uniform(0.1, 1.0), 3)
                    
                    # Loss rate between 1.0 and 1.2 (0% to 20% loss)
                    loss_rate = round(random.uniform(1.0, 1.2), 2)
                    
                    # Unit conversion rate usually 1.0
                    unit_conversion_rate = 1.0
                    
                    try:
                        cursor.execute("""
                            INSERT INTO dish_material (
                                dish_id, material_id, standard_quantity, loss_rate, 
                                unit_conversion_rate, store_id
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (dish_id, material_id, store_id) DO UPDATE SET
                                standard_quantity = EXCLUDED.standard_quantity,
                                loss_rate = EXCLUDED.loss_rate,
                                unit_conversion_rate = EXCLUDED.unit_conversion_rate
                        """, (dish['id'], material['id'], standard_qty, loss_rate, 
                              unit_conversion_rate, store_id))
                        
                        store_relationships += 1
                        
                    except Exception as e:
                        print(f"      Error creating relationship: {e}")
                        continue
            
            conn.commit()
            print(f"     Created {store_relationships} relationships for store {store_id}")
            total_relationships += store_relationships
        
        print(f"\nTotal relationships created: {total_relationships}")
        
        # Verify results
        cursor.execute("SELECT COUNT(*) as count FROM dish_material")
        db_count = cursor.fetchone()['count']
        print(f"Relationships in database: {db_count}")
        
        # Show distribution by store
        cursor.execute("""
            SELECT store_id, COUNT(*) as count 
            FROM dish_material 
            GROUP BY store_id 
            ORDER BY store_id
        """)
        store_distribution = cursor.fetchall()
        print("Relationship distribution by store:")
        for row in store_distribution:
            print(f"  Store {row['store_id']}: {row['count']} relationships")
        
        return total_relationships > 0

def main():
    """Main function"""
    
    success = create_sample_dish_material_relationships()
    
    if success:
        print("\nDish-material relationship creation completed successfully!")
    else:
        print("\nDish-material relationship creation failed!")
    
    return success

if __name__ == "__main__":
    main()