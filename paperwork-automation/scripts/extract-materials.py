#!/usr/bin/env python3
"""
Extract material data from company system export.XLSX file and generate SQL for database insertion.
Supports both SQL file generation and direct database insertion.
"""

import argparse
import sys
import os
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import warnings
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from utils.database import get_database_manager
except ImportError:
    print("⚠️  Database module not found. SQL file generation only.")
    get_database_manager = None

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')


def clean_material_number(material_number):
    """
    Clean material number by removing trailing zeroes before the actual number.
    Example: 1000040.0 -> 1000040
    """
    if pd.isna(material_number):
        return None

    # Convert to string and handle float format
    material_str = str(material_number)

    # Remove .0 if present
    if material_str.endswith('.0'):
        material_str = material_str[:-2]

    return material_str


def escape_sql_string(value):
    """Escape SQL string values to prevent injection and handle special characters"""
    if pd.isna(value) or value is None:
        return 'NULL'

    # Convert to string and escape single quotes
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def extract_materials_to_sql(input_file, output_file=None, debug=False, direct_db=False, is_test=False, quiet=False):
    """
    Extract material data from Excel file and generate SQL or insert to database

    Args:
        input_file: Path to the Excel file
        output_file: Path to output SQL file (ignored if direct_db=True)
        debug: Generate CSV for debugging
        direct_db: Insert directly to database instead of generating SQL
        is_test: Use test database
        quiet: Suppress verbose output

    Returns:
        bool: Success status
    """

    try:
        if not quiet:
            print(f"Reading material data from: {input_file}")

        # Read the file - try different formats for compatibility
        try:
            # First try as Excel file
            df = pd.read_excel(input_file, sheet_name=0, engine='xlrd')
        except Exception:
            try:
                df = pd.read_excel(input_file, sheet_name=0, engine='openpyxl')
            except Exception:
                try:
                    # If Excel fails, try as tab-delimited file with UTF-16 encoding
                    df = pd.read_csv(input_file, sep='\t', encoding='utf-16')
                except Exception:
                    try:
                        # Try with UTF-8 encoding
                        df = pd.read_csv(input_file, sep='\t',
                                         encoding='utf-8')
                    except Exception:
                        # Last resort - try default Excel read
                        df = pd.read_excel(input_file, sheet_name=0)

        if not quiet:
            print(f"Found {len(df)} rows of material data")

        # Process materials
        materials_data = []
        seen_materials = set()  # Track duplicates

        for index, row in df.iterrows():
            # Get material number (required field)
            material_number = clean_material_number(row.get('物料', ''))

            if not material_number:
                if not quiet:
                    print(f"Skipping row {index + 1}: Missing material number")
                continue

            # Skip duplicates (keep first occurrence)
            if material_number in seen_materials:
                continue
            seen_materials.add(material_number)

            # Extract other fields with proper defaults
            name = str(row.get('物料描述', '')).strip()
            description = str(row.get('物料描述', '')).strip()
            unit = str(row.get('计', '个')).strip()
            package_spec = ''  # Not available in this format

            # Validate required fields
            if not name:
                if not quiet:
                    print(f"Skipping material {material_number}: Missing name")
                continue

            # Clean up fields
            if not description:
                description = name  # Use name as description if empty

            if not unit:
                unit = '个'  # Default unit

            if package_spec in ['', '-', 'nan', 'None']:
                package_spec = ''

            materials_data.append({
                'material_number': material_number,
                'name': name,
                'description': description,
                'unit': unit,
                'package_spec': package_spec,
                'is_active': True
            })

        if not quiet:
            print(f"Processed {len(materials_data)} unique materials")

        if not materials_data:
            if not quiet:
                print("No valid material data found")
            return False

        # Generate debug CSV if requested
        if debug:
            debug_file = f"output/materials_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            debug_df = pd.DataFrame(materials_data)
            debug_df.to_csv(debug_file, index=False, encoding='utf-8-sig')
            print(f"🐛 Debug CSV saved to: {debug_file}")

        # Handle direct database insertion
        if direct_db:
            return insert_materials_to_database(materials_data, is_test, quiet)

        # Generate SQL file
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"output/materials_insert_{timestamp}.sql"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        print(f"📝 Generating SQL file: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- Material data insertion script\n")
            f.write(f"-- Generated from: {input_file}\n")
            f.write(
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Total materials: {len(materials_data)}\n\n")

            f.write("-- Insert material data with UPSERT to handle duplicates\n")
            f.write("-- This will INSERT new materials or UPDATE existing ones\n\n")

            # Write INSERT statements with UPSERT
            for material in materials_data:
                material_number = escape_sql_string(
                    material['material_number'])
                name = escape_sql_string(material['name'])
                description = escape_sql_string(material['description'])
                unit = escape_sql_string(material['unit'])
                package_spec = escape_sql_string(material['package_spec'])
                is_active = 'TRUE'

                sql = f"""INSERT INTO material (material_number, name, description, unit, package_spec, is_active)
VALUES ({material_number}, {name}, {description}, {unit}, {package_spec}, {is_active})
ON CONFLICT (material_number) 
DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    unit = EXCLUDED.unit,
    package_spec = EXCLUDED.package_spec,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            f.write(f"\n-- End of material insertion script\n")
            f.write(f"-- {len(materials_data)} materials processed\n")

        print(f"✅ SQL file generated successfully: {output_file}")
        print(f"📊 {len(materials_data)} materials ready for insertion")

        return True

    except Exception as e:
        print(f"❌ Error extracting materials: {e}")
        import traceback
        traceback.print_exc()
        return False


def insert_materials_to_database(materials_data, is_test=False, quiet=False):
    """
    Insert material data directly to database

    Args:
        materials_data: List of material dictionaries
        is_test: Use test database
        quiet: Suppress verbose output

    Returns:
        bool: Success status
    """

    try:
        if get_database_manager is None:
            if not quiet:
                print("Database connection module not available")
            return False

        if not quiet:
            print(
                f"Connecting to {'test' if is_test else 'production'} database...")

        from utils.database import DatabaseConfig
        config = DatabaseConfig(is_test=is_test)
        db_manager = get_database_manager(is_test=is_test)

        if not quiet:
            print(f"Inserting {len(materials_data)} materials to database...")

        inserted_count = 0
        updated_count = 0

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for material in materials_data:
                    # Use UPSERT query
                    query = """
                    INSERT INTO material (material_number, name, description, unit, package_spec, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (material_number) 
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        unit = EXCLUDED.unit,
                        package_spec = EXCLUDED.package_spec,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) AS inserted;
                    """

                    cursor.execute(query, (
                        material['material_number'],
                        material['name'],
                        material['description'],
                        material['unit'],
                        material['package_spec'],
                        material['is_active']
                    ))

                    # Check if it was an insert or update
                    result = cursor.fetchone()
                    # inserted = True means new insert
                    if result and result['inserted']:
                        inserted_count += 1
                    else:
                        updated_count += 1

                # Commit the transaction
                conn.commit()

        if not quiet:
            print(f"Database insertion completed:")
            print(f"   Inserted: {inserted_count} new materials")
            print(f"   Updated: {updated_count} existing materials")
            print(f"   Total processed: {len(materials_data)} materials")

        return True

    except Exception as e:
        if not quiet:
            print(f"Database insertion failed: {e}")
            import traceback
            traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Extract material data from company system export and generate SQL or insert to database')
    parser.add_argument('input_file', help='Path to the export.XLSX file')
    parser.add_argument('--output', '-o', help='Path to the output SQL file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Generate CSV files for manual verification')
    parser.add_argument('--direct-db', action='store_true',
                        help='Insert directly to database instead of generating SQL files')
    parser.add_argument('--test-db', action='store_true',
                        help='Use test database (only with --direct-db)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress verbose output')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)

    # Check if we should use direct database insertion
    direct_db_insert = args.direct_db or os.getenv(
        'DIRECT_DB_INSERT', 'false').lower() == 'true'
    is_test = args.test_db
    quiet = args.quiet

    if not quiet:
        if direct_db_insert:
            print("Direct database insertion mode enabled")
            if is_test:
                print("Using test database")
            else:
                print("Using production database")

        print(f"HAIDILAO MATERIAL EXTRACTION")
        print(f"Processing file...")
        print("=" * 60)

    # Extract materials
    success = extract_materials_to_sql(
        input_file=args.input_file,
        output_file=args.output,
        debug=args.debug,
        direct_db=direct_db_insert,
        is_test=is_test,
        quiet=quiet
    )

    if not quiet:
        print("=" * 60)

    if success:
        if quiet:
            print("Finished")
        else:
            print("Material extraction completed successfully!")
            if direct_db_insert:
                print("Materials have been inserted/updated in the database")
            else:
                print("SQL file has been generated")
        sys.exit(0)
    else:
        if quiet:
            print("ERROR: Extraction failed")
        else:
            print("Material extraction failed. Check the error messages above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
