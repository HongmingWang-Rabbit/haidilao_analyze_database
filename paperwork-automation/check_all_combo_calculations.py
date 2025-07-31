#!/usr/bin/env python3
"""
Check All Combo Calculations

This script checks combo calculations for all materials to find any using multiplication.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from utils.database import DatabaseConfig, DatabaseManager
from datetime import datetime

def check_all_combo_calculations():
    """Check combo calculations for all materials"""
    
    try:
        # Setup database connection
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all combo calculations for May 2025
            cursor.execute("""
                SELECT 
                    m.id as material_id,
                    m.name as material_name,
                    m.material_number,
                    s.name as store_name,
                    SUM(mcds.sale_amount) as total_combo_sales,
                    AVG(dm.standard_quantity) as avg_standard_qty,
                    AVG(dm.loss_rate) as avg_loss_rate,
                    AVG(dm.unit_conversion_rate) as avg_conversion_rate,
                    SUM(mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) / COALESCE(dm.unit_conversion_rate, 1.0)) as combo_total_division,
                    SUM(mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) * COALESCE(dm.unit_conversion_rate, 1.0)) as combo_total_multiply
                FROM material m
                JOIN dish_material dm ON m.id = dm.material_id
                JOIN dish d ON dm.dish_id = d.id
                JOIN monthly_combo_dish_sale mcds ON d.id = mcds.dish_id
                JOIN store s ON mcds.store_id = s.id
                WHERE mcds.year = 2025 AND mcds.month = 5
                GROUP BY m.id, m.name, m.material_number, s.name
                HAVING ABS(SUM(mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) * COALESCE(dm.unit_conversion_rate, 1.0)) - 0.8824) < 0.01
                ORDER BY ABS(SUM(mcds.sale_amount * dm.standard_quantity * COALESCE(dm.loss_rate, 1.0) * COALESCE(dm.unit_conversion_rate, 1.0)) - 0.8824)
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            
            if results:
                print(f"Found {len(results)} materials with combo multiply result near 0.8824:")
                for res in results:
                    div_val = float(res['combo_total_division'])
                    mult_val = float(res['combo_total_multiply'])
                    print(f"\nMaterial: {res['material_name']}")
                    print(f"  Store: {res['store_name']}")
                    print(f"  Total Combo Sales: {res['total_combo_sales']}")
                    print(f"  Avg Standard Qty: {res['avg_standard_qty']:.4f}")
                    print(f"  Avg Loss Rate: {res['avg_loss_rate']:.4f}")
                    print(f"  Avg Conversion Rate: {res['avg_conversion_rate']:.4f}")
                    print(f"  Combo Total (÷): {div_val:.4f}")
                    print(f"  Combo Total (×): {mult_val:.4f}")
                    
                    if abs(mult_val - 0.8824) < 0.001:
                        print(f"  🎯 MATCH: {mult_val:.4f} ≈ 0.8824 (MULTIPLICATION)")
                        # Calculate what division would give
                        print(f"  📊 If using division, would be: {div_val:.4f}")
            else:
                print("No materials found with combo multiply result near 0.8824")
                
    except Exception as e:
        print(f"Error checking combo calculations: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_all_combo_calculations()