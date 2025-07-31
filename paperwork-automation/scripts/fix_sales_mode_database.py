#!/usr/bin/env python3
"""
Fix Sales Mode Database Constraint

This script fixes the database constraint that prevents storing multiple sales modes
(堂食 and 外卖) for the same dish in the same month by:
1. Dropping the existing constraint that excludes sales_mode
2. Adding a new constraint that includes sales_mode
3. Creating an index for better performance
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from utils.database import DatabaseConfig, DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fix_sales_mode_constraint(is_test: bool = False):
    """Fix the database constraint to allow multiple sales modes per dish"""
    
    config = DatabaseConfig(is_test=is_test)
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                
                logger.info("Starting sales mode constraint fix...")
                
                # Step 1: Check current constraint
                logger.info("Checking current constraints...")
                cursor.execute("""
                    SELECT constraint_name, column_name 
                    FROM information_schema.key_column_usage 
                    WHERE table_name = 'dish_monthly_sale' 
                    AND constraint_name LIKE '%dish_monthly_sale%'
                    ORDER BY constraint_name, ordinal_position;
                """)
                
                current_constraints = cursor.fetchall()
                logger.info(f"Current constraints: {current_constraints}")
                
                # Step 2: Drop the existing constraint that doesn't include sales_mode
                logger.info("Dropping existing constraint...")
                try:
                    cursor.execute("""
                        ALTER TABLE dish_monthly_sale 
                        DROP CONSTRAINT dish_monthly_sale_dish_id_store_id_year_month_key;
                    """)
                    logger.info("✅ Successfully dropped old constraint")
                except Exception as e:
                    logger.warning(f"Could not drop constraint (may not exist): {e}")
                
                # Step 3: Add new constraint that includes sales_mode
                logger.info("Adding new constraint with sales_mode...")
                cursor.execute("""
                    ALTER TABLE dish_monthly_sale 
                    ADD CONSTRAINT dish_monthly_sale_dish_id_store_id_year_month_sales_mode_key 
                    UNIQUE (dish_id, store_id, year, month, sales_mode);
                """)
                logger.info("✅ Successfully added new constraint with sales_mode")
                
                # Step 4: Create index for better performance
                logger.info("Creating index for sales_mode...")
                try:
                    cursor.execute("""
                        CREATE INDEX idx_dish_monthly_sale_sales_mode 
                        ON dish_monthly_sale (sales_mode);
                    """)
                    logger.info("✅ Successfully created sales_mode index")
                except Exception as e:
                    logger.warning(f"Could not create index (may already exist): {e}")
                
                # Step 5: Verify the new constraint
                logger.info("Verifying new constraint...")
                cursor.execute("""
                    SELECT constraint_name, column_name 
                    FROM information_schema.key_column_usage 
                    WHERE table_name = 'dish_monthly_sale' 
                    AND constraint_name LIKE '%sales_mode%'
                    ORDER BY constraint_name, ordinal_position;
                """)
                
                new_constraints = cursor.fetchall()
                logger.info(f"New constraints: {new_constraints}")
                
                # Commit the changes
                conn.commit()
                logger.info("✅ All changes committed successfully!")
                
                # Step 6: Test the fix by checking for duplicate sales modes
                logger.info("Testing constraint fix...")
                cursor.execute("""
                    SELECT dish_id, store_id, year, month, sales_mode, COUNT(*) as count
                    FROM dish_monthly_sale 
                    WHERE year = 2025 AND month = 5
                    GROUP BY dish_id, store_id, year, month, sales_mode
                    HAVING COUNT(*) > 1
                    LIMIT 5;
                """)
                
                duplicates = cursor.fetchall()
                if duplicates:
                    logger.warning(f"Found {len(duplicates)} duplicate entries - may need cleanup")
                    for dup in duplicates:
                        logger.warning(f"  Duplicate: {dup}")
                else:
                    logger.info("✅ No duplicate entries found")
                
                # Check if we now have both sales modes for some dishes
                cursor.execute("""
                    SELECT dish_id, store_id, year, month, 
                           COUNT(DISTINCT sales_mode) as sales_mode_count,
                           STRING_AGG(DISTINCT sales_mode, ', ') as sales_modes
                    FROM dish_monthly_sale 
                    WHERE year = 2025 AND month = 5
                    GROUP BY dish_id, store_id, year, month
                    HAVING COUNT(DISTINCT sales_mode) > 1
                    LIMIT 10;
                """)
                
                multi_mode_dishes = cursor.fetchall()
                if multi_mode_dishes:
                    logger.info(f"✅ Found {len(multi_mode_dishes)} dishes with multiple sales modes:")
                    for dish in multi_mode_dishes:
                        logger.info(f"  Dish {dish[0]}, Store {dish[1]}: {dish[5]}")
                else:
                    logger.warning("⚠️  No dishes found with multiple sales modes - constraint fix successful but data may need reprocessing")
                
    except Exception as e:
        logger.error(f"Error fixing constraint: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix Sales Mode Database Constraint')
    parser.add_argument('--test', action='store_true', help='Use test database')
    
    args = parser.parse_args()
    
    success = fix_sales_mode_constraint(is_test=args.test)
    
    if success:
        print("✅ SUCCESS: Sales mode constraint fixed successfully!")
        print("Now dishes can have separate entries for 堂食 (dine-in) and 外卖 (takeout)")
        sys.exit(0)
    else:
        print("❌ ERROR: Failed to fix sales mode constraint")
        sys.exit(1)


if __name__ == "__main__":
    main()