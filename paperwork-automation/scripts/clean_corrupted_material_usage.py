#!/usr/bin/env python3
"""
Clean corrupted material monthly usage data from 2025-07-26 batch extraction.

The corrupted data was caused by reading material numbers (column 2) as usage values
instead of the actual usage columns in mb5b files.
"""

import sys
from pathlib import Path
import psycopg2
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseConfig

def clean_corrupted_data():
    """Remove corrupted material monthly usage data from 2025-07-26 batch"""
    
    print("=== CLEANING CORRUPTED MATERIAL USAGE DATA ===")
    print("Target: Records created on 2025-07-26 between 22:59:00 and 23:16:00")
    print()
    
    config = DatabaseConfig()
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database
    )
    
    cursor = conn.cursor()
    
    try:
        # First, show what we're about to delete
        print("1. ANALYZING CORRUPTED DATA...")
        cursor.execute("""
            SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT material_id) as unique_materials,
                   COUNT(DISTINCT store_id) as unique_stores,
                   MIN(created_at) as earliest,
                   MAX(created_at) as latest,
                   AVG(material_used) as avg_usage,
                   MAX(material_used) as max_usage
            FROM material_monthly_usage 
            WHERE created_at >= '2025-07-26 22:59:00' 
            AND created_at <= '2025-07-26 23:16:00'
        """)
        
        stats = cursor.fetchone()
        if stats:
            print(f"   Total records: {stats[0]}")
            print(f"   Unique materials: {stats[1]}")
            print(f"   Unique stores: {stats[2]}")
            print(f"   Time range: {stats[3]} to {stats[4]}")
            print(f"   Average usage: {stats[5]:.2f}")
            print(f"   Maximum usage: {stats[6]:.2f}")
        
        # Show some examples of the corrupted data
        print("\n2. EXAMPLES OF CORRUPTED DATA:")
        cursor.execute("""
            SELECT m.material_number, mmu.store_id, mmu.year, mmu.month, mmu.material_used
            FROM material_monthly_usage mmu
            JOIN material m ON m.id = mmu.material_id
            WHERE mmu.created_at >= '2025-07-26 22:59:00' 
            AND mmu.created_at <= '2025-07-26 23:16:00'
            AND mmu.material_used > 1000
            ORDER BY mmu.material_used DESC
            LIMIT 10
        """)
        
        examples = cursor.fetchall()
        for material_number, store_id, year, month, material_used in examples:
            print(f"   Material {material_number}, Store {store_id}, {year}-{month:02d}: {material_used}")
        
        # Confirm deletion
        print(f"\n3. PREPARING TO DELETE {stats[0] if stats else 'unknown'} CORRUPTED RECORDS...")
        print("Auto-proceeding with deletion (script running in automated mode)...")
        
        # Perform deletion
        print("\n4. DELETING CORRUPTED DATA...")
        cursor.execute("""
            DELETE FROM material_monthly_usage 
            WHERE created_at >= '2025-07-26 22:59:00' 
            AND created_at <= '2025-07-26 23:16:00'
        """)
        
        deleted_count = cursor.rowcount
        print(f"   Successfully deleted {deleted_count} corrupted records")
        
        # Commit the changes
        conn.commit()
        print("   Transaction committed")
        
        # Verify deletion
        print("\n5. VERIFYING DELETION...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM material_monthly_usage 
            WHERE created_at >= '2025-07-26 22:59:00' 
            AND created_at <= '2025-07-26 23:16:00'
        """)
        
        remaining_count = cursor.fetchone()[0]
        print(f"   Remaining records in time range: {remaining_count}")
        
        if remaining_count == 0:
            print("   ✅ All corrupted data successfully removed!")
        else:
            print(f"   ⚠️  Warning: {remaining_count} records still remain")
        
        return deleted_count > 0
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_specific_materials():
    """Verify that specific problem materials are now clean"""
    
    print("\n=== VERIFYING SPECIFIC PROBLEM MATERIALS ===")
    
    config = DatabaseConfig()
    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        database=config.database
    )
    
    cursor = conn.cursor()
    
    # Check our known problem materials
    problem_materials = ['1500900', '1500968', '1000233']
    
    for material_num in problem_materials:
        print(f"\nMaterial {material_num}:")
        
        cursor.execute("""
            SELECT mmu.store_id, mmu.year, mmu.month, mmu.material_used, mmu.created_at
            FROM material_monthly_usage mmu
            JOIN material m ON m.id = mmu.material_id
            WHERE m.material_number = %s
            ORDER BY mmu.created_at DESC
            LIMIT 5
        """, (material_num,))
        
        results = cursor.fetchall()
        if results:
            print("   Recent records:")
            for store_id, year, month, material_used, created_at in results:
                print(f"     Store {store_id}, {year}-{month:02d}: {material_used} (created: {created_at})")
        else:
            print("   No records found (completely cleaned)")
    
    conn.close()

if __name__ == "__main__":
    success = clean_corrupted_data()
    if success:
        verify_specific_materials()
    else:
        print("Cleanup failed or was cancelled.")