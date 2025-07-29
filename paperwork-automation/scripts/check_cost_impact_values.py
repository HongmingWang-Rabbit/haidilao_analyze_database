#!/usr/bin/env python3
"""
Check cost impact values in the material cost changes sheet
"""

import pandas as pd
import os

def check_cost_impact_values():
    """Check cost impact calculation values"""
    
    # Use the Unicode-safe filename
    file_path = "output/monthly_gross_margin/毛利相关分析指标-202505.xlsx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        # Read the material cost changes sheet (index 1)
        df = pd.read_excel(file_path, sheet_name=1, header=None)
        
        print("Material Cost Changes Sheet Analysis:")
        print(f"Total rows: {len(df)}")
        
        # Skip header rows (first 2 rows) and get data
        data_rows = df.iloc[2:].dropna(how='all')
        print(f"Data rows: {len(data_rows)}")
        
        if len(data_rows) == 0:
            print("No data found")
            return False
        
        # Cost impact should be in column 11 (index 11, which is column L)
        cost_impact_column = 11
        
        positive_count = 0
        negative_count = 0
        zero_count = 0
        total_with_data = 0
        
        sample_values = []
        
        for idx, row in data_rows.iterrows():
            if len(row) > cost_impact_column:
                cost_impact = row.iloc[cost_impact_column]
                if pd.notna(cost_impact) and cost_impact != '':
                    total_with_data += 1
                    
                    # Store sample for display
                    if len(sample_values) < 10:
                        material_num = row.iloc[1] if len(row) > 1 else 'Unknown'
                        current_price = row.iloc[5] if len(row) > 5 else 0
                        prev_price = row.iloc[6] if len(row) > 6 else 0
                        usage = row.iloc[9] if len(row) > 9 else 0
                        
                        sample_values.append({
                            'material': str(material_num).replace('.0', ''),
                            'usage': usage,
                            'current_price': current_price,
                            'prev_price': prev_price,
                            'cost_impact': cost_impact
                        })
                    
                    if cost_impact > 0:
                        positive_count += 1
                    elif cost_impact < 0:
                        negative_count += 1
                    else:
                        zero_count += 1
        
        print(f"\nCost Impact Distribution:")
        print(f"  Positive values: {positive_count}")
        print(f"  Negative values: {negative_count}") 
        print(f"  Zero values: {zero_count}")
        print(f"  Total with data: {total_with_data}")
        
        print(f"\nSample Cost Impact Values:")
        for sample in sample_values[:5]:
            print(f"  Material {sample['material']}:")
            
            # Convert to float for formatting
            try:
                usage = float(sample['usage']) if pd.notna(sample['usage']) else 0
                current_price = float(sample['current_price']) if pd.notna(sample['current_price']) else 0
                prev_price = float(sample['prev_price']) if pd.notna(sample['prev_price']) else 0
                cost_impact = float(sample['cost_impact']) if pd.notna(sample['cost_impact']) else 0
                
                print(f"    Usage: {usage:.4f}")
                print(f"    Current Price: ${current_price:.4f}")
                print(f"    Previous Price: ${prev_price:.4f}")
                print(f"    Cost Impact: ${cost_impact:.4f}")
                
                # Verify calculation: usage * (prev_price - current_price)
                expected = usage * (prev_price - current_price)
                print(f"    Expected: ${expected:.4f}")
                print(f"    Match: {'✅' if abs(cost_impact - expected) < 0.01 else '❌'}")
                print()
            except (ValueError, TypeError) as e:
                print(f"    Error formatting values: {e}")
                print()
        
        if total_with_data > 0:
            print("SUCCESS: Cost impact values are being calculated!")
            return True
        else:
            print("ISSUE: No cost impact data found")
            return False
            
    except Exception as e:
        print(f"Error checking cost impact: {e}")
        return False

if __name__ == "__main__":
    check_cost_impact_values()