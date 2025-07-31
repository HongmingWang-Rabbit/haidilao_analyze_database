#!/usr/bin/env python3
"""Test if images are preserved when loading and saving"""

from openpyxl import load_workbook
import sys
import zipfile
import os

# Fix encoding issue
sys.stdout.reconfigure(encoding='utf-8')

template_path = 'Input/daily_report/bank_transactions_reports/CA全部7家店明细.xlsx'
generated_file = 'output/Bank_Transactions_Report_2025-07-29_163931.xlsx'

def check_images_in_file(file_path, label):
    """Check for images in an Excel file"""
    print(f"\n=== {label} ===")
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            file_list = zip_file.namelist()
            
            # Look for media files
            media_files = [f for f in file_list if 'media' in f.lower()]
            drawing_files = [f for f in file_list if 'drawing' in f.lower()]
            
            print(f"Media files: {len(media_files)}")
            for media in media_files:
                print(f"  {media}")
                
            print(f"Drawing files: {len(drawing_files)}")
            for drawing in drawing_files:
                print(f"  {drawing}")
                
            return len(media_files), len(drawing_files)
                
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return 0, 0

# Check original template
original_media, original_drawings = check_images_in_file(template_path, "ORIGINAL TEMPLATE")

# Check generated file
if os.path.exists(generated_file):
    generated_media, generated_drawings = check_images_in_file(generated_file, "GENERATED FILE")
    
    # Compare results
    print(f"\n=== COMPARISON ===")
    print(f"Original:  {original_media} media, {original_drawings} drawings")
    print(f"Generated: {generated_media} media, {generated_drawings} drawings")
    
    if original_media == generated_media and original_drawings == generated_drawings:
        print("✅ Images preserved correctly in generated file!")
    else:
        print("❌ Images were lost in generated file!")
else:
    print(f"Generated file not found: {generated_file}")