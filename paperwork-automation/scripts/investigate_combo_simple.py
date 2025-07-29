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
            print("1. Checking material_monthly_usage table structure:")
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'material_monthly_usage'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            for col in columns:
                print(f"   {col['column_name']}: {col['data_type']}")
            
            # 2. Check for combo dishes using a specific material
            year, month = 2025, 5
            store_id = 1
            material_id = 159  # Pick a material that might have combo usage
            
            print(f"\n2. Looking for combo dishes with material {material_id}:")
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
                    AND (d.name ILIKE '%套餐%' OR d.specification ILIKE '%套餐%')
                ORDER BY net_sales DESC
                LIMIT 10
            """, (material_id, store_id, year, month))
            
            combo_dishes = cursor.fetchall()
            if combo_dishes:
                print(f"   Found {len(combo_dishes)} combo dishes:")
                for dish in combo_dishes:
                    print(f"      {dish['name']} {dish['specification']}: {dish['net_sales']} sales, std_qty: {dish['standard_quantity']}")
            else:
                print("   No combo dishes found for this material")
            
            # 3. Let's check how the existing variance calculation works by looking at the combo_usage in the actual data
            print(f"\n3. Checking what combo_usage shows in the existing variance data:")
            
            # Let's see what the original get_material_variance_data method shows for combo_usage
            # We need to check what combo_usage is in the monthly_dishes_worksheet
            
            # First, let's see what the combo_usage field in the variance data actually represents
            # by checking the existing variance calculation query
            
            # Let's check the material_monthly_usage table to see if it tracks combo usage separately
            cursor.execute("""
                SELECT material_id, store_id, material_used
                FROM material_monthly_usage 
                WHERE material_id = %s 
                    AND store_id = %s
                    AND year = %s 
                    AND month = %s
            """, (material_id, store_id, year, month))
            
            usage_record = cursor.fetchone()
            if usage_record:
                print(f"   Material monthly usage record: {usage_record['material_used']}")
            else:
                print("   No material monthly usage record found")
            
            # 4. Let's check if there's a separate calculation for combo usage in the original code
            print(f"\n4. Looking at the actual variance calculation that should show combo_usage...")
            
            # Let's look for materials that should have combo usage by checking more materials
            cursor.execute("""
                SELECT DISTINCT 
                    dm.material_id,
                    m.name as material_name,
                    COUNT(CASE WHEN d.name ILIKE '%套餐%' OR d.specification ILIKE '%套餐%' THEN 1 END) as combo_dishes,
                    COUNT(*) as total_dishes
                FROM dish_material dm
                INNER JOIN material m ON dm.material_id = m.id
                INNER JOIN dish d ON dm.dish_id = d.id
                GROUP BY dm.material_id, m.name
                HAVING COUNT(CASE WHEN d.name ILIKE '%套餐%' OR d.specification ILIKE '%套餐%' THEN 1 END) > 0
                ORDER BY combo_dishes DESC
                LIMIT 5
            """)
            
            materials_with_combos = cursor.fetchall()
            print(f"   Materials with combo dishes:")
            for mat in materials_with_combos:
                print(f"      Material {mat['material_id']} ({mat['material_name'][:30]}): {mat['combo_dishes']} combo dishes out of {mat['total_dishes']} total")
            
            # 5. Let's check what the combo sales actually are for these materials
            if materials_with_combos:
                test_material = materials_with_combos[0]['material_id']
                print(f"\n5. Testing combo sales for material {test_material}:")
                
                cursor.execute("""
                    SELECT 
                        SUM(dms.sale_amount - COALESCE(dms.return_amount, 0)) as total_combo_sales,
                        SUM((dms.sale_amount - COALESCE(dms.return_amount, 0)) * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0)) as total_combo_usage
                    FROM dish_monthly_sale dms
                    INNER JOIN dish d ON dms.dish_id = d.id
                    INNER JOIN dish_material dm ON d.id = dm.dish_id
                    WHERE dm.material_id = %s
                        AND dms.store_id = %s
                        AND dms.year = %s
                        AND dms.month = %s
                        AND (d.name ILIKE '%套餐%' OR d.specification ILIKE '%套餐%')
                """, (test_material, store_id, year, month))
                
                combo_totals = cursor.fetchone()
                if combo_totals and combo_totals['total_combo_sales']:
                    print(f"      Total combo sales: {combo_totals['total_combo_sales']}")
                    print(f"      Total combo usage: {combo_totals['total_combo_usage']}")
                else:
                    print("      No combo sales found for this material in this month")
                
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    investigate_combo_usage()