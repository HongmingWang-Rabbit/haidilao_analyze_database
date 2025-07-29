#!/usr/bin/env python3
"""
Create realistic material types based on common restaurant material classifications
"""

import sys
import os
from pathlib import Path
import pandas as pd
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def create_realistic_material_types():
    """Create realistic material types for restaurant materials"""
    
    print("CREATING REALISTIC MATERIAL TYPES")
    print("=" * 35)
    
    # Define realistic material types for a restaurant
    material_types = [
        {"name": "Food Ingredients", "description": "Raw food ingredients and components", "sort_order": 1},
        {"name": "Beverages", "description": "Drinks and beverage components", "sort_order": 2},
        {"name": "Packaging", "description": "Food packaging and containers", "sort_order": 3},
        {"name": "Cleaning Supplies", "description": "Cleaning and sanitation materials", "sort_order": 4},
        {"name": "Kitchen Equipment", "description": "Kitchen tools and equipment", "sort_order": 5},
        {"name": "Disposables", "description": "Disposable items and utensils", "sort_order": 6},
        {"name": "Condiments", "description": "Sauces, spices, and condiments", "sort_order": 7},
        {"name": "Paper Products", "description": "Paper towels, napkins, and paper goods", "sort_order": 8},
        {"name": "Office Supplies", "description": "Administrative and office materials", "sort_order": 9},
        {"name": "Maintenance", "description": "Maintenance and repair materials", "sort_order": 10},
    ]
    
    # Define child types for each material type
    child_types = {
        "Food Ingredients": ["Meat & Seafood", "Vegetables", "Dairy", "Grains & Pasta", "Frozen Foods"],
        "Beverages": ["Soft Drinks", "Tea & Coffee", "Alcohol", "Juices", "Water"],
        "Packaging": ["Takeout Containers", "Food Bags", "Labels", "Boxes", "Wrapping"],
        "Cleaning Supplies": ["Sanitizers", "Detergents", "Disinfectants", "Cleaning Tools"],
        "Kitchen Equipment": ["Utensils", "Cookware", "Small Appliances", "Storage"],
        "Disposables": ["Plates & Cups", "Cutlery", "Napkins", "Straws"],
        "Condiments": ["Sauces", "Spices", "Oils", "Seasonings"],
        "Paper Products": ["Towels", "Napkins", "Tissues", "Bags"],
        "Office Supplies": ["Stationery", "Forms", "Printing"],
        "Maintenance": ["Tools", "Hardware", "Replacement Parts"]
    }
    
    config = DatabaseConfig(is_test=True)
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Clearing existing material types...")
        cursor.execute("UPDATE material SET material_type_id = NULL, material_child_type_id = NULL")
        cursor.execute("DELETE FROM material_child_type")
        cursor.execute("DELETE FROM material_type")
        
        print("2. Creating realistic material types...")
        
        type_id_mapping = {}
        for mat_type in material_types:
            cursor.execute("""
                INSERT INTO material_type (name, description, sort_order, is_active)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (mat_type['name'], mat_type['description'], mat_type['sort_order'], True))
            
            result = cursor.fetchone()
            type_id_mapping[mat_type['name']] = result['id']
            print(f"  Created type: {mat_type['name']} (ID: {result['id']})")
        
        print("3. Creating child types...")
        
        child_type_id_mapping = {}
        for parent_name, children in child_types.items():
            parent_id = type_id_mapping[parent_name]
            
            for i, child_name in enumerate(children):
                cursor.execute("""
                    INSERT INTO material_child_type (name, material_type_id, description, sort_order, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (child_name, parent_id, f"{parent_name} - {child_name}", i + 1, True))
                
                result = cursor.fetchone()
                child_type_id_mapping[(parent_name, child_name)] = result['id']
                print(f"  Created child type: {child_name} under {parent_name}")
        
        print("4. Assigning realistic types to materials...")
        
        # Get all materials
        cursor.execute("SELECT id, store_id, material_number, name FROM material ORDER BY id")
        materials = cursor.fetchall()
        
        print(f"  Found {len(materials)} materials to classify")
        
        # Create realistic assignment rules based on material characteristics
        assignment_rules = [
            # Food-related keywords
            (["meat", "beef", "chicken", "pork", "fish", "seafood"], "Food Ingredients", "Meat & Seafood"),
            (["vegetable", "potato", "onion", "carrot", "tomato"], "Food Ingredients", "Vegetables"),
            (["milk", "cheese", "butter", "cream", "dairy"], "Food Ingredients", "Dairy"),
            (["rice", "noodle", "pasta", "bread", "flour"], "Food Ingredients", "Grains & Pasta"),
            (["frozen", "ice"], "Food Ingredients", "Frozen Foods"),
            
            # Beverages
            (["drink", "cola", "soda", "juice", "water"], "Beverages", "Soft Drinks"),
            (["tea", "coffee"], "Beverages", "Tea & Coffee"),
            (["beer", "wine", "alcohol"], "Beverages", "Alcohol"),
            
            # Packaging
            (["box", "container", "bag", "packaging"], "Packaging", "Takeout Containers"),
            (["label", "sticker"], "Packaging", "Labels"),
            
            # Cleaning
            (["clean", "soap", "detergent", "sanitize"], "Cleaning Supplies", "Sanitizers"),
            (["towel", "cloth", "wipe"], "Cleaning Supplies", "Cleaning Tools"),
            
            # Disposables
            (["cup", "plate", "bowl", "disposable"], "Disposables", "Plates & Cups"),
            (["fork", "knife", "spoon", "chopstick"], "Disposables", "Cutlery"),
            (["napkin", "tissue"], "Disposables", "Napkins"),
            
            # Condiments
            (["sauce", "oil", "vinegar", "seasoning"], "Condiments", "Sauces"),
            (["salt", "pepper", "spice"], "Condiments", "Spices"),
            
            # Paper products
            (["paper", "napkin", "towel"], "Paper Products", "Towels"),
            
            # Default fallback
            ([], "Food Ingredients", None)  # Default to food ingredients
        ]
        
        updated_count = 0
        
        for material in materials:
            material_name = (material['name'] or '').lower()
            material_number = material['material_number'] or ''
            
            # Find matching rule
            assigned_type = None
            assigned_child = None
            
            for keywords, type_name, child_name in assignment_rules:
                if not keywords:  # Default rule
                    assigned_type = type_name
                    assigned_child = child_name
                    break
                
                # Check if any keyword matches
                if any(keyword in material_name for keyword in keywords):
                    assigned_type = type_name
                    assigned_child = child_name
                    break
            
            # If no specific match, assign randomly but realistically
            if not assigned_type:
                # For materials with numbers starting with certain patterns, assign specific types
                if material_number.startswith('1'):
                    assigned_type = "Food Ingredients"
                    assigned_child = random.choice(["Meat & Seafood", "Vegetables", "Dairy"])
                elif material_number.startswith('2'):
                    assigned_type = "Beverages"
                    assigned_child = random.choice(["Soft Drinks", "Tea & Coffee"])
                elif material_number.startswith('3'):
                    assigned_type = "Packaging"
                    assigned_child = "Takeout Containers"
                else:
                    assigned_type = "Food Ingredients"
                    assigned_child = "Vegetables"
            
            # Get IDs
            type_id = type_id_mapping.get(assigned_type)
            child_type_id = None
            if assigned_child:
                child_type_id = child_type_id_mapping.get((assigned_type, assigned_child))
            
            # Update material
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
                    print(f"    Error updating material {material['id']}: {e}")
                    continue
        
        conn.commit()
        
        print(f"   Updated {updated_count} materials with realistic type assignments")
        
        # Show final distribution
        print("\n5. Final type distribution:")
        cursor.execute("""
            SELECT mt.name, COUNT(m.id) as material_count 
            FROM material_type mt 
            LEFT JOIN material m ON mt.id = m.material_type_id 
            GROUP BY mt.id, mt.name 
            ORDER BY material_count DESC
        """)
        
        for row in cursor.fetchall():
            print(f"  {row['name']}: {row['material_count']} materials")
        
        return True

def main():
    """Main function"""
    
    success = create_realistic_material_types()
    
    if success:
        print("\nRealistic material type creation completed successfully!")
    else:
        print("\nMaterial type creation failed!")
    
    return success

if __name__ == "__main__":
    main()