#!/usr/bin/env python3
"""
Test Conversion Rate Change

This script tests the impact of changing from multiplication to division
by unit_conversion_rate in the theoretical usage calculation.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import logging
from utils.database import DatabaseConfig, DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_conversion_rate_change():
    """Test the impact of changing conversion rate calculation"""
    
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                
                logger.info("=== Testing Conversion Rate Change Impact ===")
                
                # Test both multiplication and division for comparison
                logger.info("\nComparing theoretical usage calculations:")
                cursor.execute("""
                    SELECT 
                        m.material_number,
                        m.name as material_name,
                        mmu.store_id,
                        s.name as store_name,
                        mmu.material_used as system_record,
                        
                        -- Old calculation (multiplication)
                        SUM((dms.sale_amount - dms.return_amount) * 
                            COALESCE(dm.standard_quantity, 0) * 
                            COALESCE(dm.loss_rate, 1.0) * 
                            COALESCE(dm.unit_conversion_rate, 1.0)) as theoretical_usage_multiply,
                        
                        -- New calculation (division)
                        SUM((dms.sale_amount - dms.return_amount) * 
                            COALESCE(dm.standard_quantity, 0) * 
                            COALESCE(dm.loss_rate, 1.0) / 
                            COALESCE(dm.unit_conversion_rate, 1.0)) as theoretical_usage_divide,
                        
                        -- Show unit conversion rates being used
                        STRING_AGG(DISTINCT dm.unit_conversion_rate::text, ', ') as conversion_rates_used,
                        
                        -- Variance with multiplication
                        CASE 
                            WHEN SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) * 
                                COALESCE(dm.unit_conversion_rate, 1.0)) > 0 
                            THEN ((mmu.material_used - SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) * 
                                COALESCE(dm.unit_conversion_rate, 1.0))) / 
                                SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) * 
                                COALESCE(dm.unit_conversion_rate, 1.0))) * 100
                            ELSE 0 
                        END as variance_multiply,
                        
                        -- Variance with division
                        CASE 
                            WHEN SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) / 
                                COALESCE(dm.unit_conversion_rate, 1.0)) > 0 
                            THEN ((mmu.material_used - SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) / 
                                COALESCE(dm.unit_conversion_rate, 1.0))) / 
                                SUM((dms.sale_amount - dms.return_amount) * 
                                COALESCE(dm.standard_quantity, 0) * 
                                COALESCE(dm.loss_rate, 1.0) / 
                                COALESCE(dm.unit_conversion_rate, 1.0))) * 100
                            ELSE 0 
                        END as variance_divide
                        
                    FROM material_monthly_usage mmu
                    JOIN material m ON mmu.material_id = m.id AND mmu.store_id = m.store_id
                    JOIN store s ON mmu.store_id = s.id
                    JOIN dish_material dm ON m.id = dm.material_id AND m.store_id = dm.store_id
                    JOIN dish_monthly_sale dms ON dm.dish_id = dms.dish_id AND dm.store_id = dms.store_id
                    WHERE mmu.year = 2025 AND mmu.month = 5
                    AND dms.year = 2025 AND dms.month = 5
                    AND m.material_number = '1500677'  -- Beef brisket material
                    GROUP BY m.material_number, m.name, mmu.store_id, s.name, mmu.material_used
                    ORDER BY mmu.store_id;
                """)
                
                comparison_results = cursor.fetchall()
                if comparison_results:
                    logger.info("Beef brisket material (1500677) - Multiplication vs Division:")
                    for row in comparison_results:
                        logger.info(f"\n  Store {row['store_id']} ({row['store_name']}):")
                        logger.info(f"    System Record: {row['system_record']:.2f}")
                        logger.info(f"    Conversion Rates Used: {row['conversion_rates_used']}")
                        logger.info(f"    Theoretical Usage (multiply): {row['theoretical_usage_multiply']:.2f}")
                        logger.info(f"    Theoretical Usage (divide): {row['theoretical_usage_divide']:.2f}")
                        logger.info(f"    Variance (multiply): {row['variance_multiply']:.1f}%")
                        logger.info(f"    Variance (divide): {row['variance_divide']:.1f}%")
                        
                        # Calculate the impact of the change
                        if row['theoretical_usage_multiply'] > 0 and row['theoretical_usage_divide'] > 0:
                            ratio = row['theoretical_usage_divide'] / row['theoretical_usage_multiply']
                            logger.info(f"    Impact: Division gives {ratio:.1f}x the theoretical usage")
                        
                        # Determine which is better
                        abs_variance_multiply = abs(row['variance_multiply'])
                        abs_variance_divide = abs(row['variance_divide'])
                        
                        if abs_variance_divide < abs_variance_multiply:
                            improvement = abs_variance_multiply - abs_variance_divide
                            logger.info(f"    ✅ DIVISION IS BETTER: {improvement:.1f} percentage points improvement")
                        elif abs_variance_multiply < abs_variance_divide:
                            improvement = abs_variance_divide - abs_variance_multiply
                            logger.info(f"    ❌ MULTIPLICATION WAS BETTER: {improvement:.1f} percentage points worse")
                        else:
                            logger.info(f"    ➡️  NO DIFFERENCE: Both give same variance")
                
                # Check what unit conversion rates are actually being used
                logger.info("\n=== Unit Conversion Rates Analysis ===")
                cursor.execute("""
                    SELECT 
                        d.name as dish_name,
                        dm.unit_conversion_rate,
                        COUNT(*) as usage_count
                    FROM dish_material dm
                    JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                    JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                    WHERE m.material_number = '1500677'
                    AND dm.store_id = 1
                    GROUP BY d.name, dm.unit_conversion_rate
                    ORDER BY dm.unit_conversion_rate DESC;
                """)
                
                conversion_rates = cursor.fetchall()
                logger.info("Unit conversion rates used for beef brisket dishes (Store 1):")
                for rate in conversion_rates:
                    logger.info(f"  {rate['dish_name']}: {rate['unit_conversion_rate']} (used {rate['usage_count']} times)")
                
    except Exception as e:
        logger.error(f"Error testing conversion rate change: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_conversion_rate_change()
    if success:
        print("Conversion rate change test completed!")
    else:
        print("Conversion rate change test failed!")