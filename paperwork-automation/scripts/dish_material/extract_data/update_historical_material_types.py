#!/usr/bin/env python3
"""
Update material_use_type for all existing material_monthly_usage records
by reading from material_detail files for each month.
"""

import sys
import pandas as pd
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from utils.database import DatabaseManager, DatabaseConfig
from scripts.dish_material.extract_data.file_discovery import find_material_file

def load_material_types_for_month(year: int, month: int) -> Dict[str, str]:
    """Load material types from material_detail file for a specific month."""
    material_types = {}
    
    # Find the material_detail file
    material_file = find_material_file(year, month, use_history=True)
    if not material_file or not material_file.exists():
        print(f"  Material detail file not found for {year}-{month:02d}")
        return material_types
    
    try:
        print(f"  Loading material types from {material_file.name}")
        
        # Read the Excel file with proper dtype to preserve material numbers
        df = pd.read_excel(material_file, dtype={'物料': str})
        
        # Check if required columns exist
        if '物料' not in df.columns or '大类' not in df.columns:
            print(f"  Required columns (物料, 大类) not found")
            return material_types
        
        # Build the mapping
        for _, row in df.iterrows():
            material_number = str(row['物料']).strip() if pd.notna(row['物料']) else None
            material_type = str(row['大类']).strip() if pd.notna(row['大类']) else None
            
            if material_number and material_type:
                # Remove leading zeros to match with database material codes
                material_number = material_number.lstrip('0') or '0'
                material_types[material_number] = material_type
        
        print(f"  Loaded {len(material_types)} material types")
        
    except Exception as e:
        print(f"  Error reading material detail file: {e}")
    
    return material_types


def update_material_types_for_month(db_manager: DatabaseManager, year: int, month: int):
    """Update material_use_type for all records in a specific month."""
    print(f"\nProcessing {year}-{month:02d}:")
    
    # Load material types for this month
    material_types = load_material_types_for_month(year, month)
    if not material_types:
        return 0
    
    updated_count = 0
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all material_monthly_usage records for this month that don't have material_use_type
        cursor.execute("""
            SELECT mmu.id, m.material_number
            FROM material_monthly_usage mmu
            JOIN material m ON m.id = mmu.material_id AND m.store_id = mmu.store_id
            WHERE mmu.year = %s 
              AND mmu.month = %s 
              AND mmu.material_use_type IS NULL
        """, (year, month))
        
        records = cursor.fetchall()
        print(f"  Found {len(records)} records without material_use_type")
        
        # Update each record
        for record in records:
            material_number = record['material_number']
            material_type = material_types.get(material_number)
            
            if material_type:
                cursor.execute("""
                    UPDATE material_monthly_usage
                    SET material_use_type = %s
                    WHERE id = %s
                """, (material_type, record['id']))
                updated_count += 1
        
        conn.commit()
        print(f"  Updated {updated_count} records")
    
    return updated_count


def main():
    """Update material_use_type for all historical records."""
    print("Updating material_use_type for all historical records...")
    
    # Connect to database
    db_config = DatabaseConfig()
    db_manager = DatabaseManager(db_config)
    
    # Get all unique year/month combinations that need updating
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT year, month
            FROM material_monthly_usage
            WHERE material_use_type IS NULL
            ORDER BY year, month
        """)
        months_to_update = cursor.fetchall()
    
    print(f"Found {len(months_to_update)} months to update")
    
    total_updated = 0
    for row in months_to_update:
        year = row['year']
        month = row['month']
        updated = update_material_types_for_month(db_manager, year, month)
        total_updated += updated
    
    print(f"\n{'='*50}")
    print(f"Total records updated: {total_updated}")
    
    # Show final statistics
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(material_use_type) as with_type,
                COUNT(*) - COUNT(material_use_type) as without_type,
                ROUND(COUNT(material_use_type)::numeric / COUNT(*) * 100, 1) as coverage_pct
            FROM material_monthly_usage
        """)
        stats = cursor.fetchone()
        
        print(f"\nFinal Statistics:")
        print(f"  Total records: {stats['total']:,}")
        print(f"  With material_use_type: {stats['with_type']:,} ({stats['coverage_pct']}%)")
        print(f"  Without material_use_type: {stats['without_type']:,}")


if __name__ == "__main__":
    main()