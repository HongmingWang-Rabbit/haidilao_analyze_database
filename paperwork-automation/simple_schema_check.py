#!/usr/bin/env python3
import sys
sys.path.append('.')

from utils.database import DatabaseManager, DatabaseConfig

def check_schema():
    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            print("MATERIAL TABLE SCHEMA:")
            print("-" * 30)
            
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'material' 
                ORDER BY ordinal_position
            """)
            
            for col in cursor.fetchall():
                print(f"  {col[0]} ({col[1]})")
            
            print("\nMATERIAL_PRICE_HISTORY TABLE SCHEMA:")
            print("-" * 40)
            
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'material_price_history' 
                ORDER BY ordinal_position
            """)
            
            price_cols = cursor.fetchall()
            if price_cols:
                for col in price_cols:
                    print(f"  {col[0]} ({col[1]})")
            else:
                print("  No material_price_history table found")
                
                # Check what material tables exist
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name LIKE '%material%'
                """)
                
                tables = cursor.fetchall()
                print(f"\nMaterial tables found: {[t[0] for t in tables]}")
            
            print("\nMATERIAL TABLE CONSTRAINTS:")
            print("-" * 30)
            
            cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints 
                WHERE table_name = 'material'
            """)
            
            for constraint in cursor.fetchall():
                print(f"  {constraint[0]} ({constraint[1]})")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()