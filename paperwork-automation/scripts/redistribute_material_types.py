#!/usr/bin/env python3
"""
Redistribute materials across different types more realistically
"""

import sys
import os
from pathlib import Path
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def redistribute_material_types():
    """Redistribute materials across different types more realistically"""
    
    print("REDISTRIBUTING MATERIAL TYPES")
    print("=" * 30)
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all material types and their IDs
        cursor.execute("SELECT id, name FROM material_type ORDER BY id")
        material_types = cursor.fetchall()
        type_mapping = {row['name']: row['id'] for row in material_types}
        
        print(f"Available material types: {list(type_mapping.keys())}")
        
        # Get all child types
        cursor.execute("""
            SELECT ct.id, ct.name, mt.name as parent_name 
            FROM material_child_type ct 
            JOIN material_type mt ON ct.material_type_id = mt.id
        """)
        child_types = cursor.fetchall()
        child_type_mapping = {}
        for row in child_types:
            child_type_mapping[(row['parent_name'], row['name'])] = row['id']
        
        # Get all materials
        cursor.execute("SELECT id, material_number FROM material ORDER BY material_number")
        materials = cursor.fetchall()
        
        print(f"Found {len(materials)} materials to redistribute")
        
        # Define distribution rules based on material number patterns
        distribution_rules = [
            # Pattern: material number ranges -> (type, child_type, percentage)
            ("10", "Food Ingredients", "Meat & Seafood", 15),
            ("11", "Food Ingredients", "Vegetables", 20), 
            ("12", "Food Ingredients", "Dairy", 10),
            ("13", "Food Ingredients", "Grains & Pasta", 8),
            ("14", "Food Ingredients", "Frozen Foods", 7),
            ("15", "Beverages", "Soft Drinks", 8),
            ("16", "Beverages", "Tea & Coffee", 5),
            ("17", "Beverages", "Juices", 3),
            ("20", "Packaging", "Takeout Containers", 5),
            ("21", "Packaging", "Food Bags", 3),
            ("22", "Packaging", "Labels", 2),
            ("30", "Cleaning Supplies", "Sanitizers", 3),
            ("31", "Cleaning Supplies", "Detergents", 2),
            ("40", "Disposables", "Plates & Cups", 4),
            ("41", "Disposables", "Cutlery", 2),
            ("50", "Condiments", "Sauces", 2),
            ("51", "Condiments", "Spices", 1),
        ]
        
        updated_count = 0
        
        # Redistribute based on material number patterns
        for material in materials:
            material_number = material['material_number']
            
            # Find matching pattern
            assigned_type = "Food Ingredients"  # Default
            assigned_child = "Vegetables"  # Default child
            
            # Check patterns
            for pattern, type_name, child_name, _ in distribution_rules:
                if material_number.startswith(pattern):
                    assigned_type = type_name
                    assigned_child = child_name
                    break
            
            # For some randomization, occasionally assign different types
            if random.random() < 0.1:  # 10% chance of random assignment
                random_rule = random.choice(distribution_rules)
                assigned_type = random_rule[1]
                assigned_child = random_rule[2]
            
            # Get IDs
            type_id = type_mapping.get(assigned_type)
            child_type_id = child_type_mapping.get((assigned_type, assigned_child))
            
            if type_id:
                try:
                    cursor.execute("""
                        UPDATE material 
                        SET material_type_id = %s, 
                            material_child_type_id = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (type_id, child_type_id, material['id']))
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"  Error updating material {material['id']}: {e}")
                    continue
        
        conn.commit()
        
        print(f"Updated {updated_count} materials with redistributed types")
        
        # Show new distribution
        print("\nNew type distribution:")
        cursor.execute("""
            SELECT mt.name, COUNT(m.id) as material_count 
            FROM material_type mt 
            LEFT JOIN material m ON mt.id = m.material_type_id 
            GROUP BY mt.id, mt.name 
            ORDER BY material_count DESC
        """)
        
        for row in cursor.fetchall():
            if row['material_count'] > 0:
                print(f"  {row['name']}: {row['material_count']} materials")
        
        # Show child type distribution for top parent type
        print("\nChild type distribution for Food Ingredients:")
        cursor.execute("""
            SELECT ct.name, COUNT(m.id) as material_count 
            FROM material_child_type ct 
            LEFT JOIN material m ON ct.id = m.material_child_type_id 
            JOIN material_type mt ON ct.material_type_id = mt.id
            WHERE mt.name = 'Food Ingredients'
            GROUP BY ct.id, ct.name 
            ORDER BY material_count DESC
        """)
        
        for row in cursor.fetchall():
            if row['material_count'] > 0:
                print(f"  {row['name']}: {row['material_count']} materials")
        
        return True

def main():
    """Main function"""
    
    success = redistribute_material_types()
    
    if success:
        print("\nMaterial type redistribution completed successfully!")
    else:
        print("\nMaterial type redistribution failed!")
    
    return success

if __name__ == "__main__":
    main()