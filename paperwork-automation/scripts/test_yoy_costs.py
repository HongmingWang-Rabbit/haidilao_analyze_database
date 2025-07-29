#!/usr/bin/env python3
"""
Test if YoY/MoM material costs are being calculated
"""

import sys
import os
from datetime import datetime, timedelta
import calendar

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_database_manager

def test_material_costs():
    """Test if material costs are calculated for YoY/MoM"""
    
    # Setup dates
    target_dt = datetime.strptime('2025-05-31', '%Y-%m-%d')
    
    db = get_database_manager()
    
    # Test current month material costs
    query = """
    SELECT 
        mmu.store_id,
        SUM(mmu.material_used * COALESCE(mph.price, 0)) as material_cost
    FROM material_monthly_usage mmu
    LEFT JOIN LATERAL (
        SELECT price 
        FROM material_price_history 
        WHERE material_id = mmu.material_id 
            AND store_id = mmu.store_id 
            AND is_active = true
            AND effective_date <= %s
        ORDER BY effective_date DESC
        LIMIT 1
    ) mph ON true
    WHERE mmu.year = %s AND mmu.month = %s
    GROUP BY mmu.store_id
    ORDER BY mmu.store_id
    """
    
    try:
        result = db.fetch_all(query, (target_dt, target_dt.year, target_dt.month))
        
        print(f"Material costs for {target_dt.year}-{target_dt.month}:")
        total_cost = 0
        for row in result:
            cost = row.get('material_cost', 0) or 0
            total_cost += cost
            print(f"  Store {row['store_id']}: ${cost:.2f}")
        
        print(f"Total material costs: ${total_cost:.2f}")
        print(f"Status: {'HAS COSTS' if total_cost > 0 else 'NO COSTS'}")
        
    except Exception as e:
        print(f"Error testing material costs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_material_costs()