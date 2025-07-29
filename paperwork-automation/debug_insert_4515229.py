#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append('.')

# Set UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

def test_full_material_insertion_workflow():
    """Test the full material insertion workflow to see where 4515229 fails"""
    
    # Import the batch extraction script
    from scripts.extract_material_detail_prices_by_store_batch import extract_material_prices_from_store_excel
    from utils.database import DatabaseManager, DatabaseConfig
    
    print("🔍 Testing full material insertion workflow for 4515229")
    print("=" * 60)
    
    # Step 1: Extract the material (we know this works)
    store3_file = Path("Input/monthly_report/material_detail/3/ca03-202505.XLSX")
    extracted_materials = extract_material_prices_from_store_excel(
        file_path=store3_file,
        store_id=3,
        target_date="2025-06-01",
        debug=False  # Reduce noise
    )
    
    # Find our target material
    target_material = None
    for material in extracted_materials:
        if material.get('material_number') == '4515229':
            target_material = material
            break
    
    if not target_material:
        print("❌ Material 4515229 not found in extraction results")
        return
    
    print(f"✅ Material 4515229 extracted successfully:")
    print(f"   📄 Details: {target_material}")
    
    # Step 2: Test database insertion manually
    print(f"\n🗄️ Testing database insertion...")
    
    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # First check if material already exists
            cursor.execute("""
                SELECT id, material_number, name, store_id 
                FROM material 
                WHERE material_number = %s AND store_id = %s
            """, (target_material['material_number'], target_material['store_id']))
            
            existing = cursor.fetchone()
            if existing:
                print(f"   ✅ Material {target_material['material_number']} already exists in database:")
                print(f"      ID: {existing[0]}, Name: {existing[2]}, Store: {existing[3]}")
            else:
                print(f"   ❌ Material {target_material['material_number']} NOT found in database")
                
                # Try to manually insert it
                print(f"   🔧 Attempting manual insertion...")
                
                try:
                    cursor.execute("""
                        INSERT INTO material (material_number, name, description, unit, store_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (material_number, store_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            description = EXCLUDED.description,
                            unit = EXCLUDED.unit,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (
                        target_material['material_number'],
                        target_material['material_name'],
                        target_material['material_name'],
                        target_material['unit'],
                        target_material['store_id']
                    ))
                    
                    result = cursor.fetchone()
                    if result:
                        material_id = result[0]
                        print(f"   ✅ Material inserted successfully with ID: {material_id}")
                        
                        # Now try to insert the price history
                        cursor.execute("""
                            INSERT INTO material_price_history 
                            (material_id, unit_price, quantity, currency, effective_date, is_active, store_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            ON CONFLICT (material_id, effective_date, store_id) DO UPDATE SET
                                unit_price = EXCLUDED.unit_price,
                                quantity = EXCLUDED.quantity,
                                currency = EXCLUDED.currency,
                                is_active = EXCLUDED.is_active,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            material_id,
                            target_material['unit_price'],
                            target_material['quantity'],
                            target_material['currency'],
                            target_material['effective_date'],
                            target_material['is_active'],
                            target_material['store_id']
                        ))
                        
                        print(f"   ✅ Price history inserted successfully")
                        
                        # Commit the changes
                        conn.commit()
                        print(f"   ✅ Changes committed to database")
                        
                    else:
                        print(f"   ❌ Material insertion failed - no ID returned")
                        
                except Exception as e:
                    print(f"   ❌ Manual insertion failed: {e}")
                    conn.rollback()
            
            # Final verification
            print(f"\n🔍 Final verification...")
            cursor.execute("""
                SELECT m.id, m.material_number, m.name, m.store_id,
                       mph.unit_price, mph.quantity, mph.effective_date
                FROM material m
                LEFT JOIN material_price_history mph ON m.id = mph.material_id 
                WHERE m.material_number = %s AND m.store_id = %s
            """, (target_material['material_number'], target_material['store_id']))
            
            final_results = cursor.fetchall()
            if final_results:
                print(f"   ✅ Material 4515229 now exists in database:")
                for result in final_results:
                    print(f"      ID: {result[0]}, Number: {result[1]}, Name: {result[2]}")
                    print(f"      Store: {result[3]}, Price: {result[4]}, Quantity: {result[5]}")
                    print(f"      Effective Date: {result[6]}")
            else:
                print(f"   ❌ Material 4515229 still not found in database")
    
    except Exception as e:
        print(f"❌ Database operation failed: {e}")

if __name__ == "__main__":
    test_full_material_insertion_workflow()