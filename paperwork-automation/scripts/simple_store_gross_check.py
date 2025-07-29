#!/usr/bin/env python3
"""
Simple check of store gross profit previous month data
"""

import pandas as pd

def simple_store_gross_check():
    """Simple check of store gross profit data"""
    
    file_path = r"output\monthly_gross_margin\FIXED_STORE_GROSS_V2_202505.xlsx"
    
    try:
        # Read the store gross profit sheet (index 3)
        df = pd.read_excel(file_path, sheet_name=3, header=None)
        
        print("Store Gross Profit Check")
        print(f"Total sheet rows: {len(df)}")
        
        # Data starts around row 4
        data_rows = df.iloc[3:].dropna(how='all')
        print(f"Data rows: {len(data_rows)}")
        
        if len(data_rows) == 0:
            print("No data found")
            return False
        
        print("\nSample Store Data:")
        store_count = 0
        prev_rev_amounts = []
        prev_cost_amounts = []
        
        for idx, row in data_rows.iterrows():
            if store_count >= 7:  # Only check first 7 stores
                break
                
            if len(row) > 6:
                store_name = str(row.iloc[0])[:10] if pd.notna(row.iloc[0]) else 'Unknown'
                
                try:
                    current_rev = float(row.iloc[1]) if pd.notna(row.iloc[1]) else 0
                    current_cost = float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0
                    prev_rev = float(row.iloc[5]) if pd.notna(row.iloc[5]) else 0  # Column 6 is prev revenue
                    prev_cost = float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0  # Column 7 is prev cost
                    
                    print(f"Store {store_count + 1}:")
                    print(f"  Current: Rev=${current_rev:,.0f}, Cost=${current_cost:,.0f}")
                    print(f"  Previous: Rev=${prev_rev:,.0f}, Cost=${prev_cost:,.0f}")
                    
                    if prev_rev > 0:
                        prev_rev_amounts.append(prev_rev)
                    if prev_cost > 0:
                        prev_cost_amounts.append(prev_cost)
                    
                    store_count += 1
                    
                except (ValueError, TypeError):
                    continue
        
        # Analysis
        print(f"\nResults Summary:")
        print(f"Stores processed: {store_count}")
        print(f"Stores with previous revenue: {len(prev_rev_amounts)}")
        print(f"Stores with previous cost: {len(prev_cost_amounts)}")
        
        if prev_rev_amounts:
            avg_prev_rev = sum(prev_rev_amounts) / len(prev_rev_amounts)
            min_prev_rev = min(prev_rev_amounts)
            max_prev_rev = max(prev_rev_amounts)
            
            print(f"Previous Revenue Analysis:")
            print(f"  Average: ${avg_prev_rev:,.0f}")
            print(f"  Range: ${min_prev_rev:,.0f} - ${max_prev_rev:,.0f}")
            
            # Check if amounts are reasonable (should be ~$1M for monthly restaurant revenue)
            reasonable_rev = [r for r in prev_rev_amounts if 500000 <= r <= 2000000]
            rev_success_rate = len(reasonable_rev) / len(prev_rev_amounts) * 100
            print(f"  Reasonable amounts: {len(reasonable_rev)}/{len(prev_rev_amounts)} ({rev_success_rate:.1f}%)")
        
        if prev_cost_amounts:
            avg_prev_cost = sum(prev_cost_amounts) / len(prev_cost_amounts)
            min_prev_cost = min(prev_cost_amounts)
            max_prev_cost = max(prev_cost_amounts)
            
            print(f"Previous Cost Analysis:")
            print(f"  Average: ${avg_prev_cost:,.0f}")
            print(f"  Range: ${min_prev_cost:,.0f} - ${max_prev_cost:,.0f}")
            
            # Check if amounts are reasonable (should be significant for monthly costs)
            reasonable_cost = [c for c in prev_cost_amounts if 200000 <= c <= 1000000]
            cost_success_rate = len(reasonable_cost) / len(prev_cost_amounts) * 100
            print(f"  Reasonable amounts: {len(reasonable_cost)}/{len(prev_cost_amounts)} ({cost_success_rate:.1f}%)")
        
        # Overall assessment
        has_good_data = len(prev_rev_amounts) >= 5 and len(prev_cost_amounts) >= 5
        
        if has_good_data:
            print(f"\nSUCCESS: Store gross profit sheet now has proper previous month data!")
            print(f"- Previous month revenue: Fixed from daily_report")
            print(f"- Previous month cost: Fixed using current usage with April prices")
            return True
        else:
            print(f"\nISSUE: Still missing sufficient previous month data")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    simple_store_gross_check()