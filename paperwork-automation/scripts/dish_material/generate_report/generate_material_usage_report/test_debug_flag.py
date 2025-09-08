#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to demonstrate the debug flag functionality
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.database import DatabaseManager, DatabaseConfig
from scripts.dish_material.generate_report.generate_material_usage_report.compare_material_usage_sheet import (
    get_material_usage_mapping
)

def test_debug_output():
    """Test the debug output format"""
    
    # Create database connection
    db_config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(db_config)
    
    year = 2025
    month = 1
    store_id = 1
    
    print("=" * 70)
    print("TESTING DEBUG FLAG FUNCTIONALITY")
    print("=" * 70)
    
    # Test without debug flag
    print("\n1. WITHOUT DEBUG FLAG (--debug=False):")
    print("-" * 50)
    mapping_normal = get_material_usage_mapping(db_manager, year, month, store_id, debug=False)
    
    # Show example output
    for i, (material_number, material_data) in enumerate(mapping_normal.items()):
        if i >= 1:  # Just show 1 material
            break
        print(f"\nMaterial: {material_data['material_name']} ({material_number})")
        for j, (dish_code, usage_info) in enumerate(material_data['usages'].items()):
            if j >= 2:  # Show 2 dishes
                break
            # Normal format: just dish name and usage
            print(f"  {usage_info['name']}: {usage_info['usage']:.2f}")
    
    # Test with debug flag
    print("\n\n2. WITH DEBUG FLAG (--debug=True):")
    print("-" * 50)
    mapping_debug = get_material_usage_mapping(db_manager, year, month, store_id, debug=True)
    
    # Show example output
    for i, (material_number, material_data) in enumerate(mapping_debug.items()):
        if i >= 1:  # Just show 1 material
            break
        print(f"\nMaterial: {material_data['material_name']} ({material_number})")
        for j, (dish_code, usage_info) in enumerate(material_data['usages'].items()):
            if j >= 2:  # Show 2 dishes
                break
            # Debug format: includes calculation details
            if 'quantity_sold' in usage_info:
                print(f"  {usage_info['name']} {dish_code} 实收数量:{usage_info['quantity_sold']:.0f} "
                      f"出品分量(kg):{usage_info['standard_quantity']:.2f} "
                      f"损耗:{usage_info['loss_rate']:.1f} "
                      f"物料单位:{usage_info['unit_conversion']:.1f} "
                      f"计算用量:{usage_info['usage']:.2f}")
            else:
                print(f"  {usage_info['name']} {dish_code}: {usage_info['usage']:.2f}")
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("- Without --debug: Shows only dish name and calculated usage")
    print("- With --debug: Shows dish codes and detailed calculation parameters")
    print("=" * 70)

if __name__ == "__main__":
    test_debug_output()