#!/usr/bin/env python3
"""
Verify data availability for May 2025
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def verify_may_data():
    """Verify data availability"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        # Check dish_monthly_sale for May 2025
        print("1. Checking dish_monthly_sale for May 2025:")
        dms_sql = "SELECT COUNT(*), COUNT(DISTINCT store_id) as stores FROM dish_monthly_sale WHERE year = 2025 AND month = 5"
        dms_result = db_manager.fetch_one(dms_sql)
        print(f"   Records: {dms_result['count']}, Stores: {dms_result['stores']}")
        
        # Check material_monthly_usage for May 2025
        print("2. Checking material_monthly_usage for May 2025:")
        mmu_sql = "SELECT COUNT(*), COUNT(DISTINCT store_id) as stores FROM material_monthly_usage WHERE year = 2025 AND month = 5"
        mmu_result = db_manager.fetch_one(mmu_sql)
        print(f"   Records: {mmu_result['count']}, Stores: {mmu_result['stores']}")
        
        # Check daily_report for April 2025 (previous month)
        print("3. Checking daily_report for April 2025:")
        dr_sql = "SELECT COUNT(*), COUNT(DISTINCT store_id) as stores FROM daily_report WHERE EXTRACT(YEAR FROM date) = 2025 AND EXTRACT(MONTH FROM date) = 4"
        dr_result = db_manager.fetch_one(dr_sql)
        print(f"   Records: {dr_result['count']}, Stores: {dr_result['stores']}")
        
        # Check material_price_history
        print("4. Checking material_price_history for May 2025:")
        mph_sql = """
        SELECT COUNT(*), COUNT(DISTINCT material_id) as materials, COUNT(DISTINCT store_id) as stores 
        FROM material_price_history 
        WHERE is_active = true AND effective_date <= '2025-05-31'
        """
        mph_result = db_manager.fetch_one(mph_sql)
        print(f"   Records: {mph_result['count']}, Materials: {mph_result['materials']}, Stores: {mph_result['stores']}")
        
        # Check if stores exist
        print("5. Checking stores 1-7:")
        store_sql = "SELECT COUNT(*) FROM store WHERE id BETWEEN 1 AND 7"
        store_result = db_manager.fetch_one(store_sql)
        print(f"   Stores available: {store_result['count']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_may_data()