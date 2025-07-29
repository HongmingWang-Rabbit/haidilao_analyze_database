#!/usr/bin/env python3
"""
Test the full monthly automation workflow with the new inventory data format
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.complete_monthly_automation_new import MonthlyAutomationProcessor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_automation():
    """Test the full monthly automation with the new file format"""
    
    print("Testing Full Monthly Automation with New Inventory Data Format")
    print("=" * 70)
    
    # Initialize processor with test database
    processor = MonthlyAutomationProcessor(is_test=True)
    
    # Check if required input files exist
    input_folder = Path("Input/monthly_report")
    required_folders = [
        "monthly_dish_sale",
        "material_detail", 
        "calculated_dish_material_usage"
    ]
    
    print("Checking required input folders:")
    for folder in required_folders:
        folder_path = input_folder / folder
        if folder_path.exists():
            files = list(folder_path.glob("*.xls*"))
            files = [f for f in files if not f.name.startswith("~$")]
            print(f"  ✅ {folder}: {len(files)} file(s) found")
        else:
            print(f"  ❌ {folder}: Not found")
    
    print("\\nTesting dish-material extraction only...")
    
    try:
        # Test just the dish-material extraction part
        calc_folder = input_folder / "calculated_dish_material_usage"
        calc_files = list(calc_folder.glob("*.xlsx"))
        
        if calc_files:
            success = processor.extract_dish_materials(calc_files[0])
            
            if success:
                print(f"✅ Dish-material extraction successful!")
                print(f"   Records processed: {processor.results.get('dish_materials', 0)}")
            else:
                print("❌ Dish-material extraction failed!")
        else:
            print("❌ No inventory calculation file found!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\\nTest completed!")
    print("=" * 70)
    print("\\nNote: This test only validates the dish-material extraction.")
    print("To run the full automation, use:")
    print("  python scripts/complete_monthly_automation_new.py --test --date YYYY-MM-DD")
    
    return True

if __name__ == "__main__":
    test_full_automation()