#!/usr/bin/env python3
"""
Investigate how combo usage is calculated in the current variance data
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

def investigate_combo_usage():
    """Investigate combo usage in the database"""
    
    print("Investigating Combo Usage in Database")
    print("=" * 40)
    
    try:
        config = DatabaseConfig(is_test=True)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Check material_monthly_usage table structure
            print("1️⃣ Checking material_monthly_usage table structure:")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'material_monthly_usage'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            for col in columns:
                print(f"   {col['column_name']}: {col['data_type']}")
            
            # 2. Check a sample of material_monthly_usage data
            print(f"\n2️⃣ Sample material_monthly_usage data:")
            cursor.execute("""
                SELECT material_id, store_id, year, month, material_used
                FROM material_monthly_usage 
                WHERE year = 2025 AND month = 5
                LIMIT 5
            """)
            sample_data = cursor.fetchall()
            for row in sample_data:
                print(f"   Material {row['material_id']}, Store {row['store_id']}: {row['material_used']}")
            
            # 3. Check how combo usage is calculated in existing variance logic
            print(f"\n3️⃣ Looking for combo usage in existing variance calculation...")
            
            # Let's see what the current variance data shows for combo_usage
            year, month = 2025, 5
            store_id = 1
            material_id = 159  # Pick a material that might have combo usage
            
            print(f"\n4️⃣ Testing material {material_id} in store {store_id} for {year}-{month}:")
            
            # Check if there's any combo-related data
            cursor.execute("""
                SELECT 
                    dm.dish_id,
                    d.name as dish_name,
                    d.specification,
                    dms.sale_amount,
                    dms.return_amount,
                    dm.standard_quantity
                FROM dish_monthly_sale dms
                INNER JOIN dish d ON dms.dish_id = d.id
                INNER JOIN dish_material dm ON d.id = dm.dish_id
                WHERE dm.material_id = %s 
                    AND dms.store_id = %s
                    AND dms.year = %s 
                    AND dms.month = %s
                    AND (d.name ILIKE '%套餐%' OR d.specification ILIKE '%套餐%')
                ORDER BY dms.sale_amount DESC
            """, (material_id, store_id, year, month))
            
            combo_dishes = cursor.fetchall()
            if combo_dishes:
                print(f"   Found {len(combo_dishes)} combo dishes:")
                for dish in combo_dishes[:3]:
                    print(f"      {dish['dish_name']} {dish['specification']}: sale {dish['sale_amount']}, return {dish['return_amount']}")
            else:
                print("   No combo dishes found with '套餐' in name or specification")
            
            # 5. Check the actual combo_usage field that exists in the variance calculation
            print(f"\n5️⃣ Checking how combo_usage is populated in variance data...")
            
            # Let's check what the existing get_material_variance_data method actually produces
            # by looking at the combo usage calculation in the original method
            
            # Check for dishes with combo in their categorization
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_dishes,
                    COUNT(CASE WHEN d.name ILIKE '%套餐%' THEN 1 END) as combo_name_dishes,
                    COUNT(CASE WHEN d.specification ILIKE '%套餐%' THEN 1 END) as combo_spec_dishes
                FROM dish d
                INNER JOIN dish_material dm ON d.id = dm.dish_id
                WHERE dm.material_id = %s
            """, (material_id,))
            
            dish_stats = cursor.fetchone()
            print(f"   Material {material_id} used in {dish_stats['total_dishes']} dishes")
            print(f"   - {dish_stats['combo_name_dishes']} have '套餐' in name")
            print(f"   - {dish_stats['combo_spec_dishes']} have '套餐' in specification")
            
            # 6. Let's check the original variance data calculation to see what combo_usage shows
            print(f"\n6️⃣ Let's see what the original combo_usage calculation produces...")
            
            # Check what combo_usage field exists in the current variance data structure
            # From the get_material_variance_data method, we know it should show combo usage
            
            # Let's see if there are any dishes categorized differently
            cursor.execute("""
                SELECT 
                    d.id,
                    d.name,
                    d.specification,
                    dms.sale_amount - COALESCE(dms.return_amount, 0) as net_sales,
                    dm.standard_quantity
                FROM dish_monthly_sale dms
                INNER JOIN dish d ON dms.dish_id = d.id  
                INNER JOIN dish_material dm ON d.id = dm.dish_id
                WHERE dm.material_id = %s
                    AND dms.store_id = %s
                    AND dms.year = %s
                    AND dms.month = %s
                    AND (dms.sale_amount - COALESCE(dms.return_amount, 0)) > 0
                ORDER BY net_sales DESC
                LIMIT 10
            """, (material_id, store_id, year, month))
            
            all_dishes = cursor.fetchall()
            print(f"   Top dishes using material {material_id}:")
            for dish in all_dishes:
                combo_indicator = "🍱" if ('套餐' in dish['name'] or '套餐' in str(dish['specification'])) else "🍽️"
                print(f"      {combo_indicator} {dish['name']} {dish['specification']}: {dish['net_sales']} sales")
                
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    investigate_combo_usage()