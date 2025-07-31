#!/usr/bin/env python3
"""
Check Lunch Meat Calculation

This script verifies that lunch meat calculations now use division instead of multiplication.
Based on user's example, it should show:
- 午餐肉(半): 517 * 0.1 * 1 / 0.34 = 152.0588 (instead of 17.578)
- 午餐肉: 207 * 0.2 * 1 / 0.34 = 121.7647 (instead of 14.076)
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_lunch_meat_calculation():
    """Check lunch meat calculations in the generated materials_use file"""
    
    # Find the latest generated materials_use file
    output_dir = Path("output/materials_use_with_division")
    files = list(output_dir.glob("materials_use_division_*.xlsx"))
    
    if not files:
        logger.error("No materials_use division files found")
        return False
    
    # Get the latest file
    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    logger.info(f"Checking file: {latest_file}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(latest_file)
        logger.info(f"Loaded {len(df)} records from materials_use file")
        
        # Search for lunch meat dishes
        lunch_meat_keywords = ['午餐肉', 'lunch', 'meat']
        lunch_meat_rows = []
        
        for keyword in lunch_meat_keywords:
            keyword_rows = df[df['菜品名称'].str.contains(keyword, na=False, case=False)]
            if len(keyword_rows) > 0:
                lunch_meat_rows.extend(keyword_rows.to_dict('records'))
        
        if not lunch_meat_rows:
            logger.warning("No lunch meat dishes found in the file")
            
            # Show sample dish names to see what's available
            logger.info("Sample dish names in file:")
            for i, dish_name in enumerate(df['菜品名称'].head(10)):
                try:
                    logger.info(f"  {i+1}: {dish_name}")
                except UnicodeEncodeError:
                    logger.info(f"  {i+1}: [dish name with Unicode characters]")
            
            return False
        
        logger.info(f"Found {len(lunch_meat_rows)} lunch meat calculations")
        
        # Check each lunch meat calculation
        correct_calculations = 0
        total_checked = 0
        
        for i, row in enumerate(lunch_meat_rows):
            try:
                dish_name = row.get('菜品名称', 'Unknown')
                sale_amount = float(row.get('sale_amount', 0))
                std_qty = float(row.get('出品分量(kg)', 0))
                loss_rate = float(row.get('损耗', 1))
                conversion_rate = float(row.get('物料单位', 1))
                materials_use = float(row.get('materials_use', 0))
                
                # Calculate expected value using DIVISION
                if conversion_rate != 0:
                    expected_division = sale_amount * std_qty * loss_rate / conversion_rate
                    expected_multiplication = sale_amount * std_qty * loss_rate * conversion_rate
                else:
                    expected_division = 0
                    expected_multiplication = 0
                
                # Check which calculation method was used
                is_using_division = abs(materials_use - expected_division) < 0.001
                is_using_multiplication = abs(materials_use - expected_multiplication) < 0.001
                
                logger.info(f"\nLunch meat dish {i+1}:")
                try:
                    logger.info(f"  Name: {dish_name}")
                except UnicodeEncodeError:
                    logger.info(f"  Name: [Unicode dish name]")
                    
                logger.info(f"  Sale: {sale_amount}, Std_qty: {std_qty}, Loss: {loss_rate}, Conversion: {conversion_rate}")
                logger.info(f"  Materials_use (actual): {materials_use}")
                logger.info(f"  Expected (division): {expected_division:.6f}")
                logger.info(f"  Expected (multiplication): {expected_multiplication:.6f}")
                
                if is_using_division:
                    logger.info(f"  ✅ CORRECT: Using DIVISION")
                    correct_calculations += 1
                elif is_using_multiplication:
                    logger.info(f"  ❌ INCORRECT: Still using MULTIPLICATION")
                else:
                    logger.info(f"  ⚠️  UNKNOWN: Neither calculation matches exactly")
                
                total_checked += 1
                
                # Special check for the user's specific examples
                if (abs(sale_amount - 517) < 0.1 and abs(std_qty - 0.1) < 0.001 and 
                    abs(loss_rate - 1.0) < 0.001 and abs(conversion_rate - 0.34) < 0.001):
                    logger.info(f"  🎯 USER EXAMPLE 1: 午餐肉(半) 517 * 0.1 * 1 / 0.34")
                    logger.info(f"     Expected: 152.0588, Actual: {materials_use}")
                    if abs(materials_use - 152.0588) < 0.001:
                        logger.info(f"     ✅ PERFECT MATCH - Division working correctly!")
                    else:
                        logger.info(f"     ❌ MISMATCH - Still showing multiplication result")
                
                elif (abs(sale_amount - 207) < 0.1 and abs(std_qty - 0.2) < 0.001 and 
                      abs(loss_rate - 1.0) < 0.001 and abs(conversion_rate - 0.34) < 0.001):
                    logger.info(f"  🎯 USER EXAMPLE 2: 午餐肉 207 * 0.2 * 1 / 0.34")
                    logger.info(f"     Expected: 121.7647, Actual: {materials_use}")
                    if abs(materials_use - 121.7647) < 0.001:
                        logger.info(f"     ✅ PERFECT MATCH - Division working correctly!")
                    else:
                        logger.info(f"     ❌ MISMATCH - Still showing multiplication result")
                
            except Exception as e:
                logger.error(f"Error checking lunch meat row {i+1}: {e}")
                continue
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"LUNCH MEAT CALCULATION CHECK SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total lunch meat dishes checked: {total_checked}")
        logger.info(f"Correct calculations (using division): {correct_calculations}")
        logger.info(f"Success rate: {correct_calculations/total_checked*100:.1f}%" if total_checked > 0 else "No calculations checked")
        
        if correct_calculations == total_checked and total_checked > 0:
            logger.info(f"🎉 ALL LUNCH MEAT CALCULATIONS ARE NOW USING DIVISION!")
            return True
        else:
            logger.warning(f"⚠️  Some lunch meat calculations may still be using multiplication")
            return False
        
    except Exception as e:
        logger.error(f"Error checking lunch meat calculations: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_lunch_meat_calculation()
    if success:
        print("✅ SUCCESS: Lunch meat calculations are now using DIVISION correctly!")
    else:
        print("❌ WARNING: Some lunch meat calculations may still need fixing")