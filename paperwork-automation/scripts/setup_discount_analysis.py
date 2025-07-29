#!/usr/bin/env python3
"""
Setup script for discount analysis feature
Creates tables and migrates existing discount data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix encoding issues on Windows
import codecs
if sys.platform.startswith('win'):
    # Set UTF-8 encoding for Windows console
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import subprocess
import os

def main():
    """Setup discount analysis tables and migrate data"""
    
    print("DISCOUNT ANALYSIS SETUP")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Create discount analysis tables")
    print("2. Migrate existing discount data from daily_report table")
    print("3. Verify the setup")
    
    if input("\nProceed with setup? (y/n): ").lower() != 'y':
        print("Setup cancelled.")
        return
    
    # Step 1: Create tables
    print("\n📊 Creating discount analysis tables...")
    sql_file = Path(__file__).parent.parent / "haidilao-database-querys" / "add_discount_analysis_tables.sql"
    
    if sql_file.exists():
        cmd = [
            "psql",
            "-U", "hongming",
            "-d", "haidilao-paperwork",
            "-f", str(sql_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Discount tables created successfully")
            else:
                print(f"❌ Error creating tables: {result.stderr}")
                return
        except Exception as e:
            print(f"❌ Error running psql: {e}")
            return
    else:
        print(f"❌ SQL file not found: {sql_file}")
        return
    
    # Step 2: Migrate existing data
    print("\n📊 Migrating existing discount data...")
    migration_script = Path(__file__).parent / "migrate_discount_data.py"
    
    if migration_script.exists():
        cmd = [sys.executable, str(migration_script)]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.returncode != 0:
                print(f"❌ Migration error: {result.stderr}")
                return
        except Exception as e:
            print(f"❌ Error running migration: {e}")
            return
    else:
        print(f"❌ Migration script not found: {migration_script}")
        return
    
    # Step 3: Verify setup
    print("\n📊 Verifying setup...")
    
    # Create verification SQL
    verify_sql = """
SELECT 'Discount Types' as category, COUNT(*) as count FROM discount_type
UNION ALL
SELECT 'Daily Discount Details', COUNT(*) FROM daily_discount_detail
UNION ALL
SELECT 'Monthly Discount Summary', COUNT(*) FROM monthly_discount_summary;
"""
    
    cmd = [
        "psql",
        "-U", "hongming",
        "-d", "haidilao-paperwork",
        "-c", verify_sql
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("\nDatabase contents:")
            print(result.stdout)
        else:
            print(f"❌ Verification error: {result.stderr}")
    except Exception as e:
        print(f"❌ Error verifying: {e}")
    
    print("\n✅ Discount analysis setup completed!")
    print("\nNext steps:")
    print("1. Run daily/historical data extraction to populate discount details")
    print("2. Generate monthly gross margin report to see discount analysis")
    print("3. The '打折优惠表' sheet will now show discount breakdown by type")

if __name__ == "__main__":
    main()