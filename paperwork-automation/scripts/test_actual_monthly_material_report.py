#!/usr/bin/env python3
"""
Test the actual monthly material report to verify new columns are included
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_monthly_material_report import MonthlyMaterialReportGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_actual_monthly_report():
    """Test the actual monthly material report"""
    
    print("Testing Actual Monthly Material Report")
    print("=" * 40)
    
    try:
        # Generate the monthly material report
        target_date = "2025-05-31"
        generator = MonthlyMaterialReportGenerator(target_date, is_test=True)
        
        print(f"Target date: {target_date}")
        print("Generating monthly material report...")
        
        # Generate the report
        output_file = generator.generate_report()
        
        if output_file:
            print(f"✅ Report generated successfully!")
            print(f"📁 Output file: {output_file}")
            
            # Check if the file exists and get basic info
            if Path(output_file).exists():
                print(f"📊 File exists and can be opened")
                return True
            else:
                print(f"❌ Output file not found: {output_file}")
                return False
        else:
            print("❌ Report generation failed - no output file returned")
            return False
            
    except Exception as e:
        print(f"❌ Error during report generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_actual_monthly_report()
    if not success:
        sys.exit(1)