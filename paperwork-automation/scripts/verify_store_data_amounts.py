#!/usr/bin/env python3
"""
Verify that store data shows the correct monthly amounts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.database_queries import ReportDataProvider
from utils.database import DatabaseManager, DatabaseConfig

def verify_store_amounts():
    """Verify store data amounts"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    data_provider = ReportDataProvider(db_manager)
    
    try:
        print("Verifying store gross profit data amounts...")
        result = data_provider.get_store_gross_profit_data("2025-05-01")
        
        print(f"\\nStore Data Verification:")
        print("=" * 80)
        
        for store in result:
            store_id = store['store_id']
            current_rev = store['current_revenue']
            current_cost = store['current_cost']
            prev_rev = store['previous_revenue']
            prev_cost = store['previous_cost']
            
            try:
                store_name = store['store_name'][:20] if len(store['store_name']) > 20 else store['store_name']
            except UnicodeEncodeError:
                store_name = f"Store {store_id}"
            
            print(f"Store {store_id} ({store_name}):")
            print(f"  Current Revenue: ${current_rev:>10,.0f}  (May 2025)")
            print(f"  Current Cost:    ${current_cost:>10,.0f}  (May 2025)")
            print(f"  Previous Revenue:${prev_rev:>10,.0f}  (April 2025)")
            print(f"  Previous Cost:   ${prev_cost:>10,.0f}  (April 2025)")
            
            # Check if amounts look reasonable for monthly data
            if prev_rev > 500000:  # Previous revenue > $500K looks like monthly
                status = "✅ Monthly amount"
            elif prev_rev < 50000:  # < $50K likely daily
                status = "⚠️ Too small (daily?)"
            else:
                status = "❓ Uncertain"
            
            print(f"  Status: {status}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_store_amounts()