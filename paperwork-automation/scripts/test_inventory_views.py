#!/usr/bin/env python3
"""
Test script for inventory views - demonstrates how to use the views to query inventory data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def test_inventory_views():
    """Test and demonstrate inventory views."""
    
    db_config = DatabaseConfig()
    db_manager = DatabaseManager(db_config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Test 1: Check inventory with material names
        print("=" * 80)
        print("INVENTORY COUNTS WITH MATERIAL NAMES (Store 1, July 2025)")
        print("=" * 80)
        
        cursor.execute("""
            SELECT material_number, material_name, unit, counted_quantity
            FROM inventory_count_with_materials
            WHERE year = 2025 AND month = 7 AND store_id = 1
            ORDER BY counted_quantity DESC
            LIMIT 15
        """)
        
        print(f"{'Material #':<12} {'Material Name':<40} {'Quantity':>10} {'Unit':<10}")
        print("-" * 80)
        
        for row in cursor.fetchall():
            # Handle potential encoding issues
            material_name = row["material_name"][:40] if row["material_name"] else "N/A"
            print(f"{row['material_number']:<12} {material_name:<40} {row['counted_quantity']:>10.2f} {row['unit']:<10}")
        
        # Test 2: Monthly summary
        print("\n" + "=" * 80)
        print("INVENTORY SUMMARY BY MONTH")
        print("=" * 80)
        
        cursor.execute("""
            SELECT year, month, store_name, material_count, total_quantity
            FROM inventory_summary_by_month
            WHERE year = 2025
            ORDER BY year DESC, month DESC, store_id
        """)
        
        print(f"{'Period':<10} {'Store':<20} {'Materials':>10} {'Total Qty':>15}")
        print("-" * 80)
        
        for row in cursor.fetchall():
            period = f"{row['year']}-{row['month']:02d}"
            print(f"{period:<10} {row['store_name']:<20} {row['material_count']:>10} {row['total_quantity']:>15,.2f}")
        
        # Test 3: Materials with significant changes
        print("\n" + "=" * 80)
        print("MATERIALS WITH QUANTITY CHANGES (June to July 2025)")
        print("=" * 80)
        
        cursor.execute("""
            SELECT store_name, material_name, unit, 
                   previous_quantity, counted_quantity, 
                   quantity_change, percentage_change
            FROM inventory_quantity_changes
            WHERE year = 2025 AND month = 7
            AND ABS(percentage_change) > 50
            ORDER BY ABS(percentage_change) DESC
            LIMIT 10
        """)
        
        print(f"{'Store':<15} {'Material':<30} {'Previous':>10} {'Current':>10} {'Change %':>10}")
        print("-" * 80)
        
        for row in cursor.fetchall():
            material_name = row["material_name"][:30] if row["material_name"] else "N/A"
            store_name = row["store_name"][:15] if row["store_name"] else "N/A"
            pct = row["percentage_change"] if row["percentage_change"] else 0
            print(f"{store_name:<15} {material_name:<30} {row['previous_quantity']:>10.2f} {row['counted_quantity']:>10.2f} {pct:>10.1f}%")
        
        # Test 4: Search for specific materials
        print("\n" + "=" * 80)
        print("SEARCH FOR SPECIFIC MATERIALS (containing 'chicken' or '鸡')")
        print("=" * 80)
        
        cursor.execute("""
            SELECT DISTINCT store_name, material_number, material_name, 
                   counted_quantity, unit
            FROM inventory_count_with_materials
            WHERE (material_name ILIKE '%chicken%' 
                   OR material_name ILIKE '%鸡%')
            AND year = 2025 AND month = 7
            ORDER BY store_name, material_name
            LIMIT 10
        """)
        
        print(f"{'Store':<15} {'Material #':<12} {'Material Name':<35} {'Quantity':>10}")
        print("-" * 80)
        
        for row in cursor.fetchall():
            material_name = row["material_name"][:35] if row["material_name"] else "N/A"
            store_name = row["store_name"][:15] if row["store_name"] else "N/A"
            print(f"{store_name:<15} {row['material_number']:<12} {material_name:<35} {row['counted_quantity']:>10.2f}")
        
        # Test 5: Materials not in inventory
        print("\n" + "=" * 80)
        print("MATERIALS NEVER COUNTED (Store 1)")
        print("=" * 80)
        
        cursor.execute("""
            SELECT material_number, material_name, unit, material_type
            FROM materials_not_in_inventory
            WHERE store_id = 1
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        if results:
            print(f"{'Material #':<12} {'Material Name':<40} {'Type':<20}")
            print("-" * 80)
            
            for row in results:
                material_name = row["material_name"][:40] if row["material_name"] else "N/A"
                material_type = row["material_type"][:20] if row["material_type"] else "N/A"
                print(f"{row['material_number']:<12} {material_name:<40} {material_type:<20}")
        else:
            print("No materials found that haven't been counted.")
        
        print("\n" + "=" * 80)
        print("VIEWS AVAILABLE FOR QUERYING:")
        print("=" * 80)
        print("1. inventory_count_with_materials - Full inventory details with material names")
        print("2. inventory_summary_by_month - Monthly summaries by store")
        print("3. inventory_quantity_changes - Month-over-month changes")
        print("4. materials_not_in_inventory - Materials never counted")
        print("\nUse these views in SQL queries or reports for easy access to inventory data.")


if __name__ == "__main__":
    test_inventory_views()