#!/usr/bin/env python3
"""
Fix date formatting issues in the gross margin report generation
"""

import re
import sys
import os

def fix_date_formatting():
    """Fix hardcoded -31 date issues in the script"""
    
    script_path = "scripts/generate_monthly_gross_margin_report.py"
    
    # Read the file
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The problematic pattern: CAST(%s || '-' || LPAD(%s::text, 2, '0') || '-31' AS DATE)
    # This creates invalid dates like 2025-04-31
    
    # We need to replace this with proper last day of month calculation
    # Using PostgreSQL's date_trunc + interval approach
    
    old_pattern = r"CAST\(%s \|\| '-' \|\| LPAD\(%s::text, 2, '0'\) \|\| '-31' AS DATE\)"
    new_pattern = r"(date_trunc('month', make_date(%s, %s, 1)) + interval '1 month - 1 day')::date"
    
    # Count occurrences first
    matches = re.findall(old_pattern, content)
    print(f"Found {len(matches)} hardcoded -31 date patterns")
    
    if matches:
        # Replace the pattern
        content = re.sub(old_pattern, new_pattern, content)
        
        # Write back
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed {len(matches)} date formatting issues")
        print("✅ Script updated successfully")
    else:
        print("❌ No date patterns found to fix")

if __name__ == "__main__":
    fix_date_formatting()