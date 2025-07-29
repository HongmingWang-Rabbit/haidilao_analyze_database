#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append('.')

# Set UTF-8 encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

def test_material_extraction_for_4515229():
    """Test material extraction specifically for material 4515229"""
    
    # Import the extraction function
    from scripts.extract_material_detail_prices_by_store_batch import extract_material_prices_from_store_excel
    
    # Store 3 file
    store3_file = Path("Input/monthly_report/material_detail/3/ca03-202505.XLSX")
    
    print("🔍 Testing material 4515229 extraction from Store 3 file")
    print(f"📁 File: {store3_file}")
    
    # Extract with debug enabled
    result = extract_material_prices_from_store_excel(
        file_path=store3_file,
        store_id=3,
        target_date="2025-06-01",
        debug=True
    )
    
    print(f"\n📊 Extraction results: {len(result)} materials extracted")
    
    # Look for our target material
    target_found = False
    for material in result:
        if material.get('material_number') == '4515229':
            print(f"\n✅ Found target material 4515229!")
            print(f"📄 Details: {material}")
            target_found = True
            break
    
    if not target_found:
        print(f"\n❌ Material 4515229 not found in extraction results")
        
        # Show first few materials for debugging
        print(f"\n🔍 First 5 extracted materials:")
        for i, material in enumerate(result[:5]):
            print(f"   {i+1}. {material.get('material_number')} - {material.get('material_name', 'N/A')}")
        
        # Check if any material number contains 4515229
        similar_materials = [m for m in result if '4515229' in str(m.get('material_number', ''))]
        if similar_materials:
            print(f"\n🔍 Materials containing '4515229': {similar_materials}")
    
    return result, target_found

if __name__ == "__main__":
    test_material_extraction_for_4515229()