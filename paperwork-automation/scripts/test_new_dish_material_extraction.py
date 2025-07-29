#!/usr/bin/env python3
"""
Test the adapted dish material extraction with the new input format
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.complete_monthly_automation_new import MonthlyAutomationProcessor
from utils.database import DatabaseConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_extraction():
    """Test the dish material extraction with the new file format"""
    
    # Initialize processor
    processor = MonthlyAutomationProcessor(is_test=True)  # Use test database
    
    # Find the new input file
    calc_folder = Path("Input/monthly_report/calculated_dish_material_usage")
    calc_files = list(calc_folder.glob("*.xlsx"))
    
    if not calc_files:
        logger.error("No xlsx files found in calculated_dish_material_usage folder")
        return False
    
    input_file = calc_files[0]
    logger.info(f"Testing extraction with file: {input_file}")
    
    try:
        # Test the extraction method
        success = processor.extract_dish_materials(input_file)
        
        if success:
            logger.info("✅ Extraction successful!")
            logger.info(f"Dish-material relationships processed: {processor.results.get('dish_materials', 0)}")
        else:
            logger.error("❌ Extraction failed!")
            
        return success
        
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_extraction()
    if success:
        print("\\n✅ Test completed successfully!")
    else:
        print("\\n❌ Test failed!")
        sys.exit(1)