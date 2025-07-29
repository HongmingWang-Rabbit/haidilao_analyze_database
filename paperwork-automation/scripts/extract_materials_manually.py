#!/usr/bin/env python3
"""
Manually extract materials and prices for May 2025
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix encoding
import codecs
if sys.platform.startswith('win'):
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def extract_may_2025_materials():
    """Extract materials for May 2025"""
    
    print("EXTRACTING MAY 2025 MATERIALS")
    print("=" * 60)
    
    # Extract monthly material usage
    print("\n1. Extracting material usage...")
    material_usage_file = "history_files/monthly_report_inputs/2025-05/monthly_material_usage/mb5b.xls"
    
    cmd = [
        sys.executable,
        "-m", "scripts.extract-materials",
        material_usage_file,
        "--target-date", "2025-05-31",
        "--direct-db"
    ]
    
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Material usage extracted successfully")
        print(result.stdout)
    else:
        print("❌ Material usage extraction failed")
        print(result.stderr)
    
    # Extract material prices for each store
    print("\n2. Extracting material prices...")
    for store_id in range(1, 8):
        price_file = f"history_files/monthly_report_inputs/2025-05/material_detail/{store_id}/ca{store_id:02d}-202505.XLSX"
        
        if Path(price_file).exists():
            print(f"\n   Extracting prices for store {store_id}...")
            cmd = [
                sys.executable,
                "-m", "scripts.extract_material_prices_by_store",
                "--store-id", str(store_id),
                "--file", price_file,
                "--date", "2025-05-31",
                "--direct-db"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ Store {store_id} prices extracted")
            else:
                print(f"   ❌ Store {store_id} failed: {result.stderr}")
    
    print("\n" + "=" * 60)
    print("Material extraction completed!")
    print("\nNow you can generate the monthly gross margin report:")
    print("python3 scripts/generate_monthly_gross_margin_report.py --target-date 2025-05-31")

if __name__ == "__main__":
    extract_may_2025_materials()