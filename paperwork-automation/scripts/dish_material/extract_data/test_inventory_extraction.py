#!/usr/bin/env python3
"""
Test script to verify inventory extraction with actual usage calculation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
import pandas as pd

def test_inventory_calculation():
    """Test the inventory actual usage calculation."""
    
    # Test data similar to what's in the Excel files
    test_data = {
        '物料编码': ['1500677', '1500678', '1500679'],
        '物料名称': ['Test Material 1', 'Test Material 2', 'Test Material 3'],
        '库存数量': [6270.07, 1000.0, 500.0],  # Stock quantity
        '盘点数量': [790.264, 200.0, 100.0],    # Count quantity
        '单位': ['KG', 'KG', 'KG']
    }
    
    df = pd.DataFrame(test_data)
    
    # Simulate the column renaming
    df = df.rename(columns={
        '物料编码': 'material_code',
        '物料名称': 'material_name', 
        '库存数量': 'stock_quantity',
        '盘点数量': 'count_quantity',
        '单位': 'unit'
    })
    
    # Convert numeric columns
    df['stock_quantity'] = pd.to_numeric(df['stock_quantity'], errors='coerce')
    df['count_quantity'] = pd.to_numeric(df['count_quantity'], errors='coerce')
    
    # Calculate actual usage
    df['actual_usage'] = df['stock_quantity'] - df['count_quantity']
    
    print("Inventory Actual Usage Calculation Test")
    print("=" * 60)
    print("\nTest Data:")
    print("-" * 60)
    
    for _, row in df.iterrows():
        print(f"\nMaterial: {row['material_code']} - {row['material_name']}")
        print(f"  Stock Quantity:       {row['stock_quantity']:.3f}")
        print(f"  Count Quantity:       {row['count_quantity']:.3f}")
        print(f"  Actual Usage:         {row['actual_usage']:.3f}")
        print(f"  Calculation: {row['stock_quantity']:.3f} - {row['count_quantity']:.3f} = {row['actual_usage']:.3f}")
    
    print("\n" + "=" * 60)
    print("Expected Results:")
    print("-" * 60)
    print("Material 1500677: 6270.070 - 790.264 = 5479.806")
    print("Material 1500678: 1000.000 - 200.000 = 800.000")
    print("Material 1500679: 500.000 - 100.000 = 400.000")
    
    # Verify calculations
    assert abs(df.loc[df['material_code'] == '1500677', 'actual_usage'].values[0] - 5479.806) < 0.001
    assert abs(df.loc[df['material_code'] == '1500678', 'actual_usage'].values[0] - 800.0) < 0.001
    assert abs(df.loc[df['material_code'] == '1500679', 'actual_usage'].values[0] - 400.0) < 0.001
    
    print("\n[OK] All calculations verified correctly!")
    
    # Now test database query
    print("\n" + "=" * 60)
    print("Testing Database Query for Material 1500677 (if exists):")
    print("-" * 60)
    
    db_config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(db_config)
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check what's currently in the database
        cursor.execute("""
            SELECT 
                m.material_number,
                m.store_id,
                mmu.material_used,
                mmu.year,
                mmu.month
            FROM material_monthly_usage mmu
            JOIN material m ON m.id = mmu.material_id AND m.store_id = mmu.store_id
            WHERE m.material_number = '1500677'
              AND mmu.year = 2025
              AND mmu.month = 6
            ORDER BY m.store_id
        """)
        
        results = cursor.fetchall()
        
        if results:
            print("\nCurrent database values for material 1500677 (June 2025):")
            for row in results:
                print(f"  Store {row['store_id']}: material_used = {row['material_used']:.3f}")
                if row['store_id'] == 1 and abs(float(row['material_used']) - 5479.806) > 1:
                    print(f"    [WARNING] Expected ~5479.806 but got {row['material_used']:.3f}")
                    print("    -> Need to re-run inventory extraction to update with correct value")
        else:
            print("No data found for material 1500677 in June 2025")

if __name__ == "__main__":
    test_inventory_calculation()