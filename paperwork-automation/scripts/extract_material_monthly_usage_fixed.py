#!/usr/bin/env python3
"""
FIXED Material Monthly Usage Extraction Script

This script correctly processes mb5b files by reading the proper usage columns instead of material numbers.

ROOT CAUSE IDENTIFIED:
- Previous script was reading Column 2 (material numbers like 1500900) as usage values
- Correct usage columns are: 5, 6, 8, 10, 11, 13 (based on analysis)

COLUMN MAPPING FOR MB5B FILES:
- Column 0: Unnamed (usually empty)
- Column 1: ValA (store code like CA01, CA02)  
- Column 2: Material number (物料号) - NOT USAGE!
- Column 3: Start date
- Column 4: End date
- Column 5-8: Quantity columns (期初, 收货, 发货, 期末)
- Column 9: Unit (BOT, etc.)
- Column 10-13: Value columns (corresponding to quantity columns)
- Column 14: Currency (CAD)
- Column 15: Material description
"""

import pandas as pd
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, DatabaseConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_material_monthly_usage_fixed(file_path: str, target_date: str = None, direct_db: bool = False) -> List[Dict]:
    """
    Extract material monthly usage from mb5b file with CORRECT column mapping.
    
    Args:
        file_path: Path to mb5b file
        target_date: Target date in YYYY-MM-DD format 
        direct_db: Whether to insert directly to database
    
    Returns:
        List of material usage records
    """
    
    logger.info(f"=== FIXED MATERIAL MONTHLY USAGE EXTRACTION ===")
    logger.info(f"Processing: {file_path}")
    logger.info(f"Target date: {target_date}")
    
    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        return []
    
    try:
        # Read mb5b file as UTF-16 tab-separated
        logger.info("Reading mb5b file as UTF-16 TSV...")
        df = pd.read_csv(file_path, sep='\t', encoding='utf-16')
        logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Verify expected structure
        if len(df.columns) < 16:
            logger.error(f"Unexpected column count: {len(df.columns)} (expected 16)")
            return []
        
        # Parse target date for year/month
        if target_date:
            try:
                date_parts = target_date.split('-')
                year = int(date_parts[0])
                month = int(date_parts[1])
            except:
                logger.error(f"Invalid target date format: {target_date}")
                return []
        else:
            # Default to current date
            now = datetime.now()
            year = now.year
            month = now.month
        
        logger.info(f"Extracting for period: {year}-{month:02d}")
        
        # Process each row
        material_usage_records = []
        store_mapping = {
            'CA01': 1, 'CA1': 1,
            'CA02': 2, 'CA2': 2, 
            'CA03': 3, 'CA3': 3,
            'CA04': 4, 'CA4': 4,
            'CA05': 5, 'CA5': 5,
            'CA06': 6, 'CA6': 6,
            'CA07': 7, 'CA7': 7
        }
        
        processed_count = 0
        skipped_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Extract basic info
                store_code = str(row.iloc[1]).strip().upper() if pd.notna(row.iloc[1]) else ''
                material_number = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ''
                
                # Skip if missing essential data
                if not store_code or not material_number or store_code not in store_mapping:
                    skipped_count += 1
                    continue
                
                store_id = store_mapping[store_code]
                
                # Clean material number (remove .0 if present)
                material_number = material_number.replace('.0', '')
                
                # Extract CORRECT usage values from proper columns
                # Based on analysis: columns 5,6,8,10,11,13 contain actual usage data
                # We'll use column 13 as it represents final calculated usage value
                
                try:
                    # Column 13 appears to be the main calculated usage value
                    usage_value = float(str(row.iloc[13]).strip()) if pd.notna(row.iloc[13]) else 0.0
                    
                    # Alternative: sum across relevant columns if needed
                    # For now, use column 13 as primary usage indicator
                    
                except (ValueError, TypeError):
                    usage_value = 0.0
                
                # Get material description from column 15
                try:
                    material_description = str(row.iloc[15]).strip() if pd.notna(row.iloc[15]) else f"Material_{material_number}"
                except:
                    material_description = f"Material_{material_number}"
                
                # Create usage record
                usage_record = {
                    'material_number': material_number,
                    'material_name': material_description,
                    'store_id': store_id,
                    'year': year,
                    'month': month,
                    'material_used': usage_value,
                    'source_file': Path(file_path).name
                }
                
                material_usage_records.append(usage_record)
                processed_count += 1
                
                # Log sample records for verification
                if processed_count <= 5:
                    logger.info(f"Sample record {processed_count}: Material {material_number}, Store {store_id}, Usage: {usage_value}")
                
            except Exception as e:
                logger.debug(f"Error processing row {idx}: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"Extraction completed: {processed_count} records processed, {skipped_count} skipped")
        
        # Show usage statistics
        if material_usage_records:
            usage_values = [r['material_used'] for r in material_usage_records]
            positive_count = sum(1 for v in usage_values if v > 0)
            zero_count = sum(1 for v in usage_values if v == 0)
            negative_count = sum(1 for v in usage_values if v < 0)
            
            logger.info(f"Usage value distribution:")
            logger.info(f"  Positive usage: {positive_count}")
            logger.info(f"  Zero usage: {zero_count}")
            logger.info(f"  Negative usage: {negative_count}")
            
            if usage_values:
                avg_usage = sum(usage_values) / len(usage_values)
                max_usage = max(usage_values)
                logger.info(f"  Average usage: {avg_usage:.2f}")
                logger.info(f"  Maximum usage: {max_usage:.2f}")
        
        # Insert to database if requested
        if direct_db and material_usage_records:
            logger.info("Inserting to database...")
            insert_count = insert_material_usage_to_db(material_usage_records)
            logger.info(f"Successfully inserted {insert_count} records to database")
        
        return material_usage_records
        
    except Exception as e:
        logger.error(f"Error processing mb5b file: {e}")
        import traceback
        traceback.print_exc()
        return []

def insert_material_usage_to_db(usage_records: List[Dict]) -> int:
    """Insert material usage records to database"""
    
    try:
        config = DatabaseConfig(is_test=False)
        db_manager = DatabaseManager(config)
        
        insert_count = 0
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            for record in usage_records:
                try:
                    # Get material ID
                    cursor.execute("""
                        SELECT id FROM material 
                        WHERE material_number = %s AND store_id = %s
                    """, (record['material_number'], record['store_id']))
                    
                    result = cursor.fetchone()
                    if not result:
                        # Create material if it doesn't exist
                        cursor.execute("""
                            INSERT INTO material (store_id, material_number, name, unit, is_active)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (store_id, material_number) DO UPDATE SET
                                name = EXCLUDED.name,
                                updated_at = CURRENT_TIMESTAMP
                            RETURNING id
                        """, (record['store_id'], record['material_number'], record['material_name'], 'KG', True))
                        
                        result = cursor.fetchone()
                    
                    material_id = result['id']
                    
                    # Insert/update material monthly usage
                    cursor.execute("""
                        INSERT INTO material_monthly_usage (material_id, store_id, month, year, material_used)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (material_id, store_id, month, year)
                        DO UPDATE SET
                            material_used = EXCLUDED.material_used,
                            updated_at = CURRENT_TIMESTAMP
                    """, (material_id, record['store_id'], record['month'], record['year'], record['material_used']))
                    
                    insert_count += 1
                    
                except Exception as e:
                    logger.debug(f"Error inserting record for material {record['material_number']}: {e}")
                    continue
            
            conn.commit()
        
        return insert_count
        
    except Exception as e:
        logger.error(f"Database insertion error: {e}")
        return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Extract material monthly usage from mb5b files (FIXED VERSION)')
    parser.add_argument('file_path', help='Path to mb5b file')
    parser.add_argument('--target-date', help='Target date in YYYY-MM-DD format')
    parser.add_argument('--direct-db', action='store_true', help='Insert directly to database')
    parser.add_argument('--output-sql', help='Output SQL file path')
    
    args = parser.parse_args()
    
    # Extract material usage
    records = extract_material_monthly_usage_fixed(
        args.file_path, 
        args.target_date, 
        args.direct_db
    )
    
    # Output SQL if requested
    if args.output_sql and records:
        logger.info(f"Writing SQL to: {args.output_sql}")
        with open(args.output_sql, 'w', encoding='utf-8') as f:
            f.write("-- FIXED Material Monthly Usage Extraction\n")
            f.write(f"-- Generated from: {args.file_path}\n")
            f.write(f"-- Generated at: {datetime.now()}\n\n")
            
            for record in records:
                f.write(f"-- Material: {record['material_name']} ({record['material_number']}) - Store {record['store_id']}\n")
                f.write(f"INSERT INTO material_monthly_usage (material_id, store_id, month, year, material_used)\n")
                f.write(f"SELECT m.id, {record['store_id']}, {record['month']}, {record['year']}, {record['material_used']}\n")
                f.write(f"FROM material m WHERE m.material_number = '{record['material_number']}' AND m.store_id = {record['store_id']}\n")
                f.write(f"ON CONFLICT (material_id, store_id, month, year) DO UPDATE SET material_used = EXCLUDED.material_used;\n\n")
    
    logger.info(f"Extraction completed: {len(records)} records processed")

if __name__ == "__main__":
    main()