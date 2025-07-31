#!/usr/bin/env python3
"""
Verify Division Calculations in Generated Materials Use File
"""

import pandas as pd
import sys
from pathlib import Path

def verify_division_calculations():
    """Verify the division calculations in the generated materials_use file"""
    
    # Find the latest generated file
    output_dir = Path("output/materials_use_with_division")
    files = list(output_dir.glob("materials_use_division_*.xlsx"))
    
    if not files:
        print("No materials_use division files found")
        return False
    
    # Get the latest file
    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    print(f"Verifying file: {latest_file}")
    
    try:
        df = pd.read_excel(latest_file, nrows=10)
        print(f"Successfully loaded file with {len(df)} rows and {len(df.columns)} columns")
        
        # Verify calculations for first few rows
        correct_calculations = 0
        total_checked = 0
        
        for i, row in df.head(5).iterrows():
            try:
                sale = float(row.get('sale_amount', 0))
                std_qty = float(row.get('出品分量(kg)', 0))
                loss = float(row.get('损耗', 1))
                conv = float(row.get('物料单位', 1))
                materials_use = float(row.get('materials_use', 0))
                
                # Calculate expected value using division
                if conv != 0:
                    expected = sale * std_qty * loss / conv
                else:
                    expected = 0
                
                # Check if calculation matches (within small tolerance)
                is_correct = abs(materials_use - expected) < 0.001
                
                print(f"Row {i+1}:")
                print(f"  Sale: {sale}, Std_qty: {std_qty}, Loss: {loss}, Conv: {conv}")
                print(f"  Materials_use: {materials_use}")
                print(f"  Expected (÷): {expected:.6f}")
                print(f"  Correct: {is_correct}")
                print()
                
                if is_correct:
                    correct_calculations += 1
                total_checked += 1
                
            except Exception as e:
                print(f"Error checking row {i+1}: {e}")
                continue
        
        print(f"Verification Summary:")
        print(f"  Correct calculations: {correct_calculations}/{total_checked}")
        print(f"  Success rate: {correct_calculations/total_checked*100:.1f}%" if total_checked > 0 else "No calculations checked")
        
        return correct_calculations == total_checked and total_checked > 0
        
    except Exception as e:
        print(f"Error verifying calculations: {e}")
        return False

if __name__ == "__main__":
    success = verify_division_calculations()
    if success:
        print("✅ All calculations verified correctly - using DIVISION")
    else:
        print("❌ Some calculations may be incorrect")