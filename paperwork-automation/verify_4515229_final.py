#!/usr/bin/env python3
import sys
sys.path.append('.')
sys.stdout.reconfigure(encoding='utf-8')

from utils.database import DatabaseManager, DatabaseConfig

def verify_material_4515229():
    """Final verification that material 4515229 is now in database"""
    
    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            print("=== VERIFYING MATERIAL 4515229 ===")
            
            # Check material exists
            cursor.execute("""
                SELECT id, material_number, name, store_id, created_at
                FROM material 
                WHERE material_number = '4515229'
                ORDER BY store_id
            """)
            
            materials = cursor.fetchall()
            if materials:
                print(f"✅ Found {len(materials)} records for material 4515229:")
                for mat in materials:
                    print(f"   Store {mat[3]}: ID={mat[0]}, Name={mat[2]}")
                
                # Check price history
                material_ids = [mat[0] for mat in materials]
                placeholders = ','.join(['%s'] * len(material_ids))
                
                cursor.execute(f"""
                    SELECT material_id, store_id, price, currency, effective_date, is_active
                    FROM material_price_history 
                    WHERE material_id IN ({placeholders})
                    ORDER BY store_id, effective_date DESC
                """, material_ids)
                
                prices = cursor.fetchall()
                if prices:
                    print(f"\n✅ Found {len(prices)} price records:")
                    for price in prices:
                        store_id = price[1]
                        price_val = price[2]
                        currency = price[3]
                        date = price[4]
                        active = price[5]
                        print(f"   Store {store_id}: {price_val} {currency} on {date} (active: {active})")
                else:
                    print(f"\n❌ No price history found for material 4515229")
                    
            else:
                print(f"❌ Material 4515229 NOT found in database")
                
                # Check what materials do exist
                cursor.execute("""
                    SELECT COUNT(*) FROM material WHERE material_number LIKE '451%'
                """)
                
                count = cursor.fetchone()[0]
                print(f"Materials starting with '451': {count}")
                
                # Check what Store 3 materials exist
                cursor.execute("""
                    SELECT COUNT(*) FROM material WHERE store_id = 3
                """)
                
                store3_count = cursor.fetchone()[0]
                print(f"Store 3 total materials: {store3_count}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_material_4515229()