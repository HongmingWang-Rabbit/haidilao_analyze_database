#!/usr/bin/env python3
"""
Debug why April cost calculation is too low
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseManager, DatabaseConfig

def debug_april_cost_calculation():
    """Debug April cost calculation"""
    
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    
    try:
        print("=== APRIL COST CALCULATION DEBUG ===")
        
        # Compare May prices vs April prices for Store 1
        print("\n1. Price Comparison (Store 1 - Sample Materials):")
        price_comparison_sql = """
        SELECT 
            m.material_number,
            m.name as material_name,
            may_price.price as may_price,
            april_price.price as april_price,
            CASE 
                WHEN april_price.price > 0 AND may_price.price > 0 
                THEN ((april_price.price - may_price.price) / may_price.price * 100)
                ELSE 0 
            END as price_change_percent
        FROM material m
        LEFT JOIN LATERAL (
            SELECT price 
            FROM material_price_history 
            WHERE material_id = m.id 
                AND store_id = 1
                AND is_active = true
                AND effective_date <= '2025-05-31'
            ORDER BY effective_date DESC
            LIMIT 1
        ) may_price ON true
        LEFT JOIN LATERAL (
            SELECT price 
            FROM material_price_history 
            WHERE material_id = m.id 
                AND store_id = 1
                AND is_active = true
                AND effective_date <= '2025-04-30'
            ORDER BY effective_date DESC
            LIMIT 1
        ) april_price ON true
        WHERE may_price.price IS NOT NULL AND april_price.price IS NOT NULL
        ORDER BY m.material_number
        LIMIT 10
        """
        
        price_comparison = db_manager.fetch_all(price_comparison_sql)
        if price_comparison:
            for row in price_comparison:
                print(f"  {row['material_number']}: May=${row['may_price']:.2f}, April=${row['april_price']:.2f} ({row['price_change_percent']:+.1f}%)")
        
        # Check if April prices are significantly lower on average
        print("\n2. Average Price Analysis:")
        avg_price_sql = """
        SELECT 
            'May 2025' as period,
            COUNT(*) as material_count,
            AVG(mph.price) as avg_price,
            MIN(mph.price) as min_price,
            MAX(mph.price) as max_price
        FROM material_price_history mph
        WHERE store_id = 1 
            AND is_active = true
            AND effective_date <= '2025-05-31'
            AND effective_date > '2025-04-30'
        UNION ALL
        SELECT 
            'April 2025' as period,
            COUNT(*) as material_count,
            AVG(mph.price) as avg_price,
            MIN(mph.price) as min_price,
            MAX(mph.price) as max_price
        FROM material_price_history mph
        WHERE store_id = 1 
            AND is_active = true
            AND effective_date <= '2025-04-30'
            AND effective_date > '2025-03-31'
        """
        
        avg_prices = db_manager.fetch_all(avg_price_sql)
        for row in avg_prices:
            print(f"  {row['period']}: {row['material_count']} materials, avg=${row['avg_price']:.2f} (${row['min_price']:.2f}-${row['max_price']:.2f})")
        
        # Check actual cost calculation for Store 1
        print("\n3. Actual Cost Calculation (Store 1):")
        actual_calc_sql = """
        SELECT 
            m.material_number,
            mmu.material_used,
            mph.price as april_price,
            (mmu.material_used * COALESCE(mph.price, 0)) as cost_contribution
        FROM material_monthly_usage mmu
        JOIN material m ON mmu.material_id = m.id
        LEFT JOIN LATERAL (
            SELECT price 
            FROM material_price_history 
            WHERE material_id = mmu.material_id 
                AND store_id = mmu.store_id 
                AND is_active = true
                AND effective_date <= '2025-04-30'
            ORDER BY effective_date DESC
            LIMIT 1
        ) mph ON true
        WHERE mmu.store_id = 1 
            AND mmu.year = 2025 
            AND mmu.month = 5
            AND mmu.material_used > 0
        ORDER BY cost_contribution DESC
        LIMIT 10
        """
        
        cost_calc = db_manager.fetch_all(actual_calc_sql)
        if cost_calc:
            print("Top 10 cost contributors:")
            total_cost = 0
            for row in cost_calc:
                cost = row['cost_contribution'] or 0
                total_cost += cost
                print(f"  {row['material_number']}: {row['material_used']:.2f} units × ${row['april_price'] or 0:.2f} = ${cost:.2f}")
            print(f"  Total from top 10: ${total_cost:.2f}")
        
        # Get total cost for Store 1 to understand the discrepancy
        print("\n4. Total Cost Summary (Store 1):")
        total_cost_sql = """
        SELECT 
            SUM(mmu.material_used * COALESCE(mph.price, 0)) as total_april_cost,
            COUNT(*) as material_count,
            COUNT(CASE WHEN mph.price IS NOT NULL THEN 1 END) as materials_with_prices,
            COUNT(CASE WHEN mph.price IS NULL THEN 1 END) as materials_without_prices
        FROM material_monthly_usage mmu
        LEFT JOIN LATERAL (
            SELECT price 
            FROM material_price_history 
            WHERE material_id = mmu.material_id 
                AND store_id = mmu.store_id 
                AND is_active = true
                AND effective_date <= '2025-04-30'
            ORDER BY effective_date DESC
            LIMIT 1
        ) mph ON true
        WHERE mmu.store_id = 1 
            AND mmu.year = 2025 
            AND mmu.month = 5
        """
        
        total_cost = db_manager.fetch_all(total_cost_sql)
        if total_cost:
            row = total_cost[0]
            print(f"  Total April cost: ${row['total_april_cost'] or 0:.2f}")
            print(f"  Materials processed: {row['material_count']}")
            print(f"  Materials with April prices: {row['materials_with_prices']}")
            print(f"  Materials without April prices: {row['materials_without_prices']}")
            
            price_coverage = (row['materials_with_prices'] / row['material_count']) * 100 if row['material_count'] > 0 else 0
            print(f"  Price coverage: {price_coverage:.1f}%")
        
        print("\n5. DIAGNOSIS:")
        if cost_calc and len(cost_calc) > 0:
            if all(row['april_price'] is None or row['april_price'] == 0 for row in cost_calc[:5]):
                print("  ISSUE: April prices are missing or zero")
                print("  SOLUTION: Use a cost estimation method or fallback to current prices")
            elif total_cost and total_cost[0]['total_april_cost'] and total_cost[0]['total_april_cost'] < 50000:
                print("  ISSUE: April prices are significantly lower than expected")
                print("  SOLUTION: Consider using cost-to-revenue ratio estimation instead")
            else:
                print("  ISSUE: Unknown calculation problem")
        
    except Exception as e:
        print(f"Error debugging April cost: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_april_cost_calculation()