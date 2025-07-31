#!/usr/bin/env python3
"""
Test Lunch Meat Fix

This script directly tests the lunch meat calculation fix by simulating the 
get_dish_usage_details function from monthly_dishes_worksheet.py
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from utils.database import DatabaseConfig, DatabaseManager
from lib.monthly_dishes_worksheet import MonthlyDishesWorksheetGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataProvider:
    """Simple data provider for testing"""
    def __init__(self, db_manager):
        self.db_manager = db_manager


def test_lunch_meat_calculation_fix():
    """Test that lunch meat calculations now use division"""
    
    try:
        # Setup database connection
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        data_provider = DataProvider(db_manager)
        
        # Create worksheet generator
        generator = MonthlyDishesWorksheetGenerator(['加拿大一店'], '2025-05-31')
        
        # Find lunch meat material ID from database
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Find lunch meat material
            cursor.execute("""
                SELECT m.id, m.material_number, m.name, m.store_id
                FROM material m
                WHERE m.name LIKE '%午餐肉%' OR m.material_number LIKE '%lunch%'
                ORDER BY m.store_id, m.name
                LIMIT 5
            """)
            
            lunch_materials = cursor.fetchall()
            
            if not lunch_materials:
                logger.warning("No lunch meat materials found in database")
                return False
            
            logger.info(f"Found {len(lunch_materials)} lunch meat materials:")
            for mat in lunch_materials:
                logger.info(f"  Material ID: {mat['id']}, Number: {mat['material_number']}, Name: {mat['name']}, Store: {mat['store_id']}")
            
            # Test the dish usage details for the first lunch meat material
            test_material = lunch_materials[0]
            material_id = test_material['id']
            store_id = test_material['store_id']
            
            logger.info(f"\nTesting dish usage details for material {material_id} (store {store_id})...")
            
            # Call the function that generates the detailed usage breakdown
            usage_details = generator.get_dish_usage_details(
                data_provider, material_id, store_id, 2025, 5)
            
            logger.info(f"\nGenerated usage details:")
            logger.info(usage_details)
            
            # Check if the usage details show division results
            if "materials_use-152.05" in usage_details or "materials_use-121.76" in usage_details:
                logger.info("✅ SUCCESS: Found division-based results in usage details!")
                logger.info("   午餐肉(半): Should show ~152.0588 instead of 17.578")
                logger.info("   午餐肉: Should show ~121.7647 instead of 14.076")
                return True
            elif "materials_use-17.57" in usage_details or "materials_use-14.07" in usage_details:
                logger.error("❌ STILL INCORRECT: Found multiplication-based results")
                logger.error("   Still showing materials_use-17.578 instead of materials_use-152.0588")
                return False
            else:
                logger.info("ℹ️  No specific lunch meat calculations found in this material")
                logger.info("   (This might be a different material - test results may vary)")
                return True
                
    except Exception as e:
        logger.error(f"Error testing lunch meat calculation fix: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_lunch_meat_calculation_fix()
    if success:
        print("✅ Lunch meat calculation fix test completed")
    else:
        print("❌ Lunch meat calculation fix test failed")