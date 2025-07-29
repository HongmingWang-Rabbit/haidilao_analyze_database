#!/usr/bin/env python3
"""
Re-extract all historical material usage data using the FIXED extraction script.

This script processes all mb5b files in the historical data folders and re-extracts
material usage with the correct column mapping.
"""

import sys
from pathlib import Path
import subprocess
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_all_mb5b_files():
    """Find all mb5b files in historical data folders"""
    
    mb5b_files = []
    
    # Current monthly report
    current_path = Path("Input/monthly_report/monthly_material_usage")
    if current_path.exists():
        for mb5b_file in current_path.glob("*mb5b*.xls*"):
            mb5b_files.append((mb5b_file, "2025-07"))  # Current month
    
    # Historical monthly reports
    hist_base = Path("history_files/monthly_report_inputs")
    if hist_base.exists():
        for month_folder in hist_base.iterdir():
            if month_folder.is_dir():
                # Extract target date from folder name (e.g., 2025-05 -> 2025-05-31)
                try:
                    folder_name = month_folder.name
                    if len(folder_name) == 7 and '-' in folder_name:  # Format: YYYY-MM
                        target_date = f"{folder_name}-31"  # Use last day of month
                        
                        material_folder = month_folder / "monthly_material_usage"
                        if material_folder.exists():
                            for mb5b_file in material_folder.glob("*mb5b*.xls*"):
                                mb5b_files.append((mb5b_file, target_date))
                except Exception as e:
                    logger.debug(f"Error processing folder {month_folder}: {e}")
                    continue
    
    return mb5b_files

def re_extract_material_usage():
    """Re-extract all material usage data using fixed script"""
    
    logger.info("=== RE-EXTRACTING ALL MATERIAL USAGE DATA ===")
    logger.info("Using FIXED extraction script to correct column mapping bug")
    logger.info("")
    
    # Find all mb5b files
    mb5b_files = find_all_mb5b_files()
    logger.info(f"Found {len(mb5b_files)} mb5b files to process")
    
    if not mb5b_files:
        logger.error("No mb5b files found!")
        return False
    
    # Process each file
    success_count = 0
    error_count = 0
    total_records = 0
    
    for i, (mb5b_file, target_date) in enumerate(mb5b_files, 1):
        logger.info(f"\n[{i}/{len(mb5b_files)}] Processing: {mb5b_file.name}")
        logger.info(f"   Target date: {target_date}")
        
        try:
            # Run the fixed extraction script
            cmd = [
                sys.executable,
                "scripts/extract_material_monthly_usage_fixed.py",
                str(mb5b_file),
                "--target-date", target_date,
                "--direct-db"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd=Path.cwd(),
                timeout=300  # 5 minute timeout per file
            )
            
            if result.returncode == 0:
                # Parse output for record count
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if "Extraction completed:" in line and "records processed" in line:
                        try:
                            record_count = int(line.split("Extraction completed: ")[1].split(" records")[0])
                            total_records += record_count
                            logger.info(f"   ✅ Success: {record_count} records")
                            break
                        except:
                            logger.info(f"   ✅ Success: processed")
                            
                success_count += 1
            else:
                logger.error(f"   ❌ Failed: {result.stderr}")
                error_count += 1
                
        except subprocess.TimeoutExpired:
            logger.error(f"   ❌ Timeout: Processing took too long")
            error_count += 1
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            error_count += 1
    
    # Summary
    logger.info(f"\n=== RE-EXTRACTION SUMMARY ===")
    logger.info(f"Files processed: {len(mb5b_files)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {error_count}")
    logger.info(f"Total records extracted: {total_records}")
    
    if error_count == 0:
        logger.info("🎉 All files processed successfully!")
        return True
    else:
        logger.warning(f"⚠️ {error_count} files had errors")
        return False

def verify_fix():
    """Verify that the fix worked by checking problem materials"""
    
    logger.info("\n=== VERIFYING FIX ===")
    
    import psycopg2
    from utils.database import DatabaseConfig
    
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
        logger.info(f"\nMaterial {material_num}:")
        
        cursor.execute("""
            SELECT mmu.store_id, mmu.year, mmu.month, mmu.material_used, mmu.created_at
            FROM material_monthly_usage mmu
            JOIN material m ON m.id = mmu.material_id
            WHERE m.material_number = %s
            AND mmu.year = 2025 AND mmu.month = 5 AND mmu.store_id = 1
            ORDER BY mmu.created_at DESC
            LIMIT 1
        """, (material_num,))
        
        result = cursor.fetchone()
        if result:
            store_id, year, month, material_used, created_at = result
            logger.info(f"   Store 1, 2025-05: {material_used} (was 8883.5580+ before fix)")
        else:
            logger.info(f"   No 2025-05 Store 1 record found")
    
    conn.close()

if __name__ == "__main__":
    success = re_extract_material_usage()
    if success:
        verify_fix()
    else:
        logger.error("Re-extraction had errors. Please check the logs.")