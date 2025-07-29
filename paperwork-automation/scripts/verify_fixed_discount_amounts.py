#!/usr/bin/env python3
"""
Verify that the fixed discount amounts are now showing monthly totals
"""

import pandas as pd

def verify_fixed_discount_amounts():
    """Check if discount amounts are now monthly totals"""
    
    file_path = r"output\monthly_gross_margin\FIXED_DISCOUNT_202505.xlsx"
    
    try:
        # Read the discount sheet (should be index 2: 打折优惠表)
        df = pd.read_excel(file_path, sheet_name=2, header=None)
        
        print("=== FIXED DISCOUNT AMOUNTS VERIFICATION ===")
        print(f"Total rows in discount sheet: {len(df)}")
        
        # Find data start (usually after headers around row 2-3)
        data_start = None
        for i in range(5):
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
            print("No discount data found")
            return False
        
        # Check discount amounts (should be in column 2: 本月折扣金额)
        current_amounts = []
        
        print("\nDiscount amounts by store (May 2025):")
        for idx, row in data_rows.iterrows():
            if len(row) > 2:
                store_name = str(row.iloc[0])[:15] if pd.notna(row.iloc[0]) else 'Unknown'
                discount_type = str(row.iloc[1])[:10] if pd.notna(row.iloc[1]) else 'Unknown'
                current_amount = row.iloc[2] if pd.notna(row.iloc[2]) else 0
                
                try:
                    amount_float = float(current_amount)
                    current_amounts.append(amount_float)
                    if amount_float > 0:
                        print(f"  {store_name} - {discount_type}: ${amount_float:,.2f}")
                except:
                    continue
        
        if len(current_amounts) == 0:
            print("No valid discount amounts found")
            return False
        
        # Analysis of amounts
        non_zero_amounts = [amt for amt in current_amounts if amt > 0]
        
        if len(non_zero_amounts) == 0:
            print("All discount amounts are zero")
            return False
        
        avg_amount = sum(non_zero_amounts) / len(non_zero_amounts)
        min_amount = min(non_zero_amounts)
        max_amount = max(non_zero_amounts)
        
        print(f"\n=== DISCOUNT AMOUNT ANALYSIS ===")
        print(f"Non-zero discount records: {len(non_zero_amounts)}")
        print(f"Average monthly discount: ${avg_amount:,.2f}")
        print(f"Range: ${min_amount:,.2f} - ${max_amount:,.2f}")
        
        # Check if amounts look like monthly totals now
        reasonable_monthly_min = 20000  # $20K minimum for monthly restaurant discount
        reasonable_monthly_max = 200000  # $200K maximum reasonable monthly discount
        
        reasonable_amounts = [amt for amt in non_zero_amounts if reasonable_monthly_min <= amt <= reasonable_monthly_max]
        
        print(f"\nReasonableness Check:")
        print(f"Amounts in reasonable monthly range (${reasonable_monthly_min:,} - ${reasonable_monthly_max:,}): {len(reasonable_amounts)}")
        
        if len(reasonable_amounts) > 0:
            reasonable_percentage = (len(reasonable_amounts) / len(non_zero_amounts)) * 100
            print(f"Percentage of reasonable amounts: {reasonable_percentage:.1f}%")
            
            if reasonable_percentage >= 80:
                print("\n✅ SUCCESS: Discount amounts now look like proper monthly totals!")
                print("✅ Fixed: Changed from daily amounts (~$3K) to monthly totals (~$80K)")
                return True
            else:
                print(f"\n⚠️  PARTIAL: Some amounts look reasonable, but {100-reasonable_percentage:.1f}% still seem off")
                return False
        else:
            print("\n❌ ISSUE: No amounts fall in reasonable monthly range")
            print("❌ Amounts still appear to be daily rather than monthly totals")
            return False
            
    except Exception as e:
        print(f"Error verifying discount amounts: {e}")
        return False

if __name__ == "__main__":
    verify_fixed_discount_amounts()