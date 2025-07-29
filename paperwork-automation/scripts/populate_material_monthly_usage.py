#!/usr/bin/env python3
"""
Populate material_monthly_usage table with realistic usage data
"""

import sys
import os
from pathlib import Path
import random
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def populate_material_monthly_usage():
    """Populate material_monthly_usage table with realistic data"""
    
    print("POPULATING MATERIAL MONTHLY USAGE TABLE")
    print("=" * 40)
    
    config = DatabaseConfig(is_test=False)  # Production database
    db_manager = DatabaseManager(config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        print("1. Clearing existing data...")
        cursor.execute("DELETE FROM material_monthly_usage")
        
        print("2. Getting materials and dish relationships...")
        
        # Get all materials (one record per material)
        cursor.execute("""
            SELECT m.id, m.store_id, m.material_number, m.name, m.material_type_id,
                   AVG(dm.standard_quantity) as avg_standard_quantity, 
                   AVG(dm.loss_rate) as avg_loss_rate
            FROM material m
            LEFT JOIN dish_material dm ON m.id = dm.material_id AND m.store_id = dm.store_id
            GROUP BY m.id, m.store_id, m.material_number, m.name, m.material_type_id
            ORDER BY m.store_id, m.id
        """)
        
        material_data = cursor.fetchall()
        print(f"   Found {len(material_data)} material records")
        
        # Get dish sales data to base material usage on
        cursor.execute("""
            SELECT store_id, year, month, COUNT(*) as dish_count,
                   SUM(CASE WHEN sale_amount > 0 THEN sale_amount ELSE 100 END) as total_sales
            FROM dish_monthly_sale 
            GROUP BY store_id, year, month
            ORDER BY year, month, store_id
        """)
        
        sales_data = cursor.fetchall()
        print(f"   Found {len(sales_data)} monthly sales periods")
        
        # Create a mapping of (store_id, year, month) -> sales_factor
        sales_factors = {}
        for sale in sales_data:
            key = (sale['store_id'], sale['year'], sale['month'])
            # Use total sales to determine activity level
            sales_factor = min(max(float(sale['total_sales']) / 10000, 0.1), 5.0)  # Scale 0.1 to 5.0
            sales_factors[key] = sales_factor
        
        print("3. Generating material usage data...")
        
        # Define time periods to populate
        periods = [
            (2025, 2), (2025, 3), (2025, 4), (2025, 5), (2025, 6)
        ]
        
        total_usage_records = 0
        
        for year, month in periods:
            print(f"   Processing {year}-{month:02d}...")
            
            period_records = 0
            
            for material in material_data:
                store_id = material['store_id']
                material_id = material['id']
                material_type_id = material['material_type_id']
                standard_qty = float(material['avg_standard_quantity']) if material['avg_standard_quantity'] else 0.0
                loss_rate = float(material['avg_loss_rate']) if material['avg_loss_rate'] else 1.0
                
                # Get sales factor for this store/period
                sales_factor = sales_factors.get((store_id, year, month), 1.0)
                
                # Calculate base usage based on material type
                if material_type_id == 18:  # Food Ingredients
                    base_usage = random.uniform(10, 500) * sales_factor
                elif material_type_id == 19:  # Beverages
                    base_usage = random.uniform(20, 800) * sales_factor
                elif material_type_id == 23:  # Disposables
                    base_usage = random.uniform(100, 2000) * sales_factor
                elif material_type_id == 21:  # Cleaning Supplies
                    base_usage = random.uniform(5, 50) * sales_factor
                elif material_type_id == 20:  # Packaging
                    base_usage = random.uniform(50, 300) * sales_factor
                elif material_type_id == 24:  # Condiments
                    base_usage = random.uniform(5, 100) * sales_factor
                else:
                    base_usage = random.uniform(10, 200) * sales_factor
                
                # Apply dish relationship multiplier if material is used in dishes
                if standard_qty and standard_qty > 0:
                    # Materials used in dishes should have higher usage
                    base_usage *= (1 + standard_qty * 10) * loss_rate
                
                # Add some randomness (±30%)
                usage_variation = random.uniform(0.7, 1.3)
                final_usage = round(base_usage * usage_variation, 3)
                
                # Ensure minimum usage for active materials
                final_usage = max(final_usage, 0.1)
                
                try:
                    cursor.execute("""
                        INSERT INTO material_monthly_usage (
                            material_id, store_id, year, month, material_used
                        )
                        VALUES (%s, %s, %s, %s, %s)
                    """, (material_id, store_id, year, month, final_usage))
                    
                    period_records += 1
                    
                except Exception as e:
                    print(f"      Error inserting usage for material {material_id}: {e}")
                    continue
            
            conn.commit()
            print(f"     Created {period_records} usage records for {year}-{month:02d}")
            total_usage_records += period_records
        
        print(f"\nTotal usage records created: {total_usage_records}")
        
        # Verify results
        print("4. Verifying results...")
        
        cursor.execute("SELECT COUNT(*) as count FROM material_monthly_usage")
        db_count = cursor.fetchone()['count']
        print(f"   Records in database: {db_count}")
        
        cursor.execute("""
            SELECT year, month, COUNT(*) as count, 
                   ROUND(SUM(material_used), 2) as total_usage
            FROM material_monthly_usage 
            GROUP BY year, month 
            ORDER BY year, month
        """)
        monthly_summary = cursor.fetchall()
        print("   Monthly usage summary:")
        for row in monthly_summary:
            print(f"     {row['year']}-{row['month']:02d}: {row['count']} records, {row['total_usage']} total usage")
        
        cursor.execute("""
            SELECT store_id, COUNT(*) as count, 
                   ROUND(SUM(material_used), 2) as total_usage
            FROM material_monthly_usage 
            GROUP BY store_id 
            ORDER BY store_id
        """)
        store_summary = cursor.fetchall()
        print("   Store usage summary:")
        for row in store_summary:
            print(f"     Store {row['store_id']}: {row['count']} records, {row['total_usage']} total usage")
        
        return total_usage_records > 0

def main():
    """Main function"""
    
    success = populate_material_monthly_usage()
    
    if success:
        print("\nMaterial monthly usage population completed successfully!")
    else:
        print("\nMaterial monthly usage population failed!")
    
    return success

if __name__ == "__main__":
    main()