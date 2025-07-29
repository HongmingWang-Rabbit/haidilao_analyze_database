#!/usr/bin/env python3
"""
Generate realistic inventory count data for all materials
"""

import sys
import os
from pathlib import Path
import random
from datetime import date

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def generate_inventory_count():
    """Generate realistic inventory count data for all materials"""
    
    print("GENERATING INVENTORY COUNT DATA")
    print("=" * 30)
    
    config = DatabaseConfig(is_test=False)  # Production database
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Clearing existing inventory count data...")
        cursor.execute("DELETE FROM inventory_count")
        
        print("2. Getting all materials...")
        cursor.execute("""
            SELECT m.id, m.store_id, m.material_number, m.name, m.material_type_id, mt.name as type_name
            FROM material m
            LEFT JOIN material_type mt ON m.material_type_id = mt.id
            ORDER BY m.store_id, m.id
        """)
        materials = cursor.fetchall()
        
        print(f"   Found {len(materials)} materials to generate inventory for")
        
        print("3. Generating realistic inventory counts...")
        
        total_inventory_records = 0
        count_date = date(2025, 5, 1)  # May 1st, 2025 inventory count
        
        for material in materials:
            material_id = material['id']
            store_id = material['store_id']
            material_type_id = material['material_type_id']
            type_name = material['type_name'] or 'Unknown'
            
            # Generate realistic inventory quantities based on material type
            if 'Food Ingredients' in type_name:
                # Food ingredients: 5-200 units
                base_quantity = random.uniform(5, 200)
            elif 'Beverages' in type_name:
                # Beverages: 10-500 units (higher volume)
                base_quantity = random.uniform(10, 500)
            elif 'Disposables' in type_name:
                # Disposables: 50-2000 units (bulk items)
                base_quantity = random.uniform(50, 2000)
            elif 'Packaging' in type_name:
                # Packaging: 20-800 units
                base_quantity = random.uniform(20, 800)
            elif 'Cleaning Supplies' in type_name:
                # Cleaning supplies: 2-50 units (smaller quantities)
                base_quantity = random.uniform(2, 50)
            elif 'Condiments' in type_name:
                # Condiments: 3-100 units
                base_quantity = random.uniform(3, 100)
            else:
                # Default: 10-300 units
                base_quantity = random.uniform(10, 300)
            
            # Add some store-specific variation (store 1 tends to have more inventory)
            if store_id == 1:
                base_quantity *= random.uniform(1.1, 1.5)
            elif store_id in [6, 7]:  # Smaller stores
                base_quantity *= random.uniform(0.7, 0.9)
            else:
                base_quantity *= random.uniform(0.9, 1.1)
            
            # Round to appropriate decimal places
            if base_quantity > 100:
                counted_quantity = round(base_quantity, 1)  # 1 decimal for large quantities
            else:
                counted_quantity = round(base_quantity, 2)  # 2 decimals for smaller quantities
            
            try:
                cursor.execute("""
                    INSERT INTO inventory_count (
                        material_id, store_id, counted_quantity, count_date
                    )
                    VALUES (%s, %s, %s, %s)
                """, (material_id, store_id, counted_quantity, count_date))
                
                total_inventory_records += 1
                
            except Exception as e:
                print(f"   Error inserting inventory for material {material['material_number']}: {e}")
                continue
        
        conn.commit()
        
        print(f"\nTotal inventory records created: {total_inventory_records}")
        
        # Verify results
        print("4. Verifying results...")
        
        cursor.execute("SELECT COUNT(*) as count FROM inventory_count")
        db_count = cursor.fetchone()['count']
        print(f"   Records in database: {db_count}")
        
        cursor.execute("""
            SELECT store_id, COUNT(*) as count, 
                   ROUND(SUM(counted_quantity), 2) as total_quantity,
                   ROUND(AVG(counted_quantity), 2) as avg_quantity
            FROM inventory_count 
            GROUP BY store_id 
            ORDER BY store_id
        """)
        store_distribution = cursor.fetchall()
        print("   Inventory count distribution by store:")
        for row in store_distribution:
            print(f"     Store {row['store_id']}: {row['count']} items, {row['total_quantity']} total qty, {row['avg_quantity']} avg qty")
        
        # Distribution by material type
        cursor.execute("""
            SELECT mt.name as type_name, COUNT(*) as count, 
                   ROUND(SUM(ic.counted_quantity), 2) as total_quantity,
                   ROUND(AVG(ic.counted_quantity), 2) as avg_quantity
            FROM inventory_count ic
            JOIN material m ON ic.material_id = m.id
            JOIN material_type mt ON m.material_type_id = mt.id
            GROUP BY mt.name
            ORDER BY total_quantity DESC
        """)
        type_distribution = cursor.fetchall()
        print("   Inventory count distribution by material type:")
        for row in type_distribution:
            print(f"     {row['type_name']}: {row['count']} items, {row['total_quantity']} total qty, {row['avg_quantity']} avg qty")
        
        # Show sample records
        cursor.execute("""
            SELECT ic.store_id, m.material_number, m.name, ic.counted_quantity, mt.name as type_name
            FROM inventory_count ic
            JOIN material m ON ic.material_id = m.id
            JOIN material_type mt ON m.material_type_id = mt.id
            ORDER BY ic.counted_quantity DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        print("   Sample inventory records (highest quantities):")
        for sample in samples:
            print(f"     Store {sample['store_id']}: #{sample['material_number']} - {sample['name']} ({sample['type_name']}), Qty: {sample['counted_quantity']}")
        
        return total_inventory_records > 0

def main():
    """Main function"""
    
    success = generate_inventory_count()
    
    if success:
        print("\nInventory count generation completed successfully!")
    else:
        print("\nInventory count generation failed!")
    
    return success

if __name__ == "__main__":
    main()