#!/usr/bin/env python3
"""
Verify that store gross profit previous month data is now showing proper amounts
"""

import pandas as pd

def verify_fixed_store_gross_profit():
    """Check if previous month revenue and cost are now proper monthly amounts"""
    
    file_path = r"output\monthly_gross_margin\FIXED_STORE_GROSS_V2_202505.xlsx"
    
    try:
        # Read the store gross profit sheet (should be index 3: 各店毛利率分析)
        df = pd.read_excel(file_path, sheet_name=3, header=None)
        
        print("=== STORE GROSS PROFIT VERIFICATION ===")
        print(f"Total rows in sheet: {len(df)}")
        
        # Find data start (usually after headers around row 2-3)
        data_start = None
        for i in range(10):
            if i < len(df) and len(df.columns) > 0:
                first_col = df.iloc[i, 0] if pd.notna(df.iloc[i, 0]) else ""
                if '店' in str(first_col) and '加拿大' in str(first_col):
                    data_start = i
                    break
        
        if data_start is None:
            print("Could not find data start")
            return False
            
        print(f"Data starts at row: {data_start + 1}")
        
        # Get data rows  
        data_rows = df.iloc[data_start:].dropna(how='all')
        print(f"Data rows: {len(data_rows)}")
        
        if len(data_rows) == 0:
            print("No store data found")
            return False
        
        # Expected column structure for store gross profit:
        # 0: Store Name, 1: Current Revenue, 2: Current Cost, 3: Current Gross Profit, 4: Current Gross Margin%
        # 5: Previous Revenue, 6: Previous Cost, 7: Previous Gross Profit, 8: Previous Gross Margin%
        # 9: Revenue Change, 10: Cost Change, etc.
        
        print("\nStore Gross Profit Data:")
        print("Store Name | Current Rev | Current Cost | Prev Rev | Prev Cost")
        print("-" * 70)
        
        results = []
        for idx, row in data_rows.iterrows():
            if len(row) > 6:
                store_name = str(row.iloc[0])[:12] if pd.notna(row.iloc[0]) else 'Unknown'
                current_rev = row.iloc[1] if pd.notna(row.iloc[1]) else 0
                current_cost = row.iloc[2] if pd.notna(row.iloc[2]) else 0  
                prev_rev = row.iloc[5] if pd.notna(row.iloc[5]) else 0
                prev_cost = row.iloc[6] if pd.notna(row.iloc[6]) else 0
                
                try:
                    current_rev_f = float(current_rev)
                    current_cost_f = float(current_cost)
                    prev_rev_f = float(prev_rev)
                    prev_cost_f = float(prev_cost)
                    
                    print(f"{store_name:<12} | ${current_rev_f:>9,.0f} | ${current_cost_f:>10,.0f} | ${prev_rev_f:>8,.0f} | ${prev_cost_f:>9,.0f}")
                    
                    results.append({
                        'store': store_name,
                        'current_rev': current_rev_f,
                        'current_cost': current_cost_f,
                        'prev_rev': prev_rev_f,
                        'prev_cost': prev_cost_f
                    })
                except (ValueError, TypeError):
                    print(f"{store_name:<12} | Invalid data format")
                    continue
        
        if len(results) == 0:
            print("No valid store data found")
            return False
        
        # Analysis
        print(f"\n=== ANALYSIS ===")
        print(f"Stores analyzed: {len(results)}")
        
        # Check previous month revenue (should be ~$1M from daily_report)
        prev_revs = [r['prev_rev'] for r in results if r['prev_rev'] > 0]
        if prev_revs:
            avg_prev_rev = sum(prev_revs) / len(prev_revs)
            print(f"Previous month revenue average: ${avg_prev_rev:,.0f}")
            
            reasonable_prev_rev = [r for r in prev_revs if 500000 <= r <= 2000000]  # $500K - $2M range
            prev_rev_success = len(reasonable_prev_rev) / len(prev_revs) * 100
            print(f"Previous revenue in reasonable range: {len(reasonable_prev_rev)}/{len(prev_revs)} ({prev_rev_success:.1f}%)")
        else:
            print("No previous month revenue data found")
            prev_rev_success = 0
        
        # Check previous month cost (should be significant amounts)
        prev_costs = [r['prev_cost'] for r in results if r['prev_cost'] > 0]
        if prev_costs:
            avg_prev_cost = sum(prev_costs) / len(prev_costs)
            print(f"Previous month cost average: ${avg_prev_cost:,.0f}")
            
            reasonable_prev_cost = [c for c in prev_costs if 200000 <= c <= 1000000]  # $200K - $1M range
            prev_cost_success = len(reasonable_prev_cost) / len(prev_costs) * 100
            print(f"Previous cost in reasonable range: {len(reasonable_prev_cost)}/{len(prev_costs)} ({prev_cost_success:.1f}%)")
        else:
            print("No previous month cost data found")
            prev_cost_success = 0
        
        # Overall success check
        print(f"\n=== RESULTS ===")
        if prev_rev_success >= 80 and prev_cost_success >= 80:
            print("SUCCESS: Previous month revenue and cost now show proper monthly amounts!")
            print("- Fixed: Previous month revenue from daily_report aggregation")
            print("- Fixed: Previous month cost using current usage with April prices")
            return True
        elif prev_rev_success >= 80:
            print("PARTIAL: Previous month revenue fixed, but cost still needs work")
            return False
        elif prev_cost_success >= 80:
            print("PARTIAL: Previous month cost fixed, but revenue still needs work")
            return False
        else:
            print("ISSUE: Both previous month revenue and cost still need fixing")
            return False
            
    except Exception as e:
        print(f"Error verifying store gross profit: {e}")
        return False

if __name__ == "__main__":
    verify_fixed_store_gross_profit()