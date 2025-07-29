#!/usr/bin/env python3
"""
Extract material data with type classifications from material_detail Excel files.
This script extracts:
1. Material types from 187-一级分类 column 
2. Material child types from 187-二级分类 column
3. Materials with their type associations
4. Updates material table with type references

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
from typing import Dict, List, Optional, Tuple
import logging

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from utils.database import get_database_manager, DatabaseConfig
except ImportError:
    print("⚠️  Database module not found. SQL file generation only.")
    get_database_manager = None
    DatabaseConfig = None

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def safe_print(message):
    """Print message safely, handling Unicode encoding errors on Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Remove emojis and special Unicode characters for Windows console
        import re
        clean_message = re.sub(r'[^\x00-\x7F]+', '', message)
        print(clean_message)


def clean_material_number(material_number):
    """
    Clean material number by removing leading zeros and trailing .0
    Example: 000000000001000049 -> 1000049, 1000040.0 -> 1000040
    """
    if pd.isna(material_number):
        return None

    # Convert to string and handle float format
    material_str = str(material_number)

    # Remove .0 if present
    if material_str.endswith('.0'):
        material_str = material_str[:-2]

    # Remove leading zeros by converting to int then back to string
    try:
        # This will automatically remove leading zeros
        cleaned_number = str(int(material_str))
        return cleaned_number
    except (ValueError, TypeError):
        # If conversion fails, return original string
        return material_str


def detect_store_id_from_path(file_path):
    """
    Detect store ID from file path.
    Examples: 
    - Input/monthly_report/material_detail/3/ca03-202505.XLSX -> 3
    - ca03-202505.XLSX -> 3
    """
    file_path_str = str(file_path)
    
    # Try to extract from folder structure first
    # Look for pattern like /material_detail/N/ where N is store number
    import re
    folder_match = re.search(r'/material_detail/(\d+)/', file_path_str.replace('\\', '/'))
    if folder_match:
        return int(folder_match.group(1))
    
    # Try to extract from filename pattern like ca03, CA03, etc.
    filename = Path(file_path).name
    filename_match = re.search(r'ca0?(\d+)', filename.lower())
    if filename_match:
        return int(filename_match.group(1))
    
    # Default to None if cannot detect
    return None


def extract_material_types_and_materials(input_file, debug=False, quiet=False):
    """
    Extract material types, child types, and materials from material_detail Excel file.

    Args:
        input_file: Path to the material_detail Excel file
        debug: Generate CSV for debugging
        quiet: Suppress verbose output

    Returns:
        Tuple[List[Dict], List[Dict], List[Dict]]: (material_types, material_child_types, materials)
    """

    try:
        if not quiet:
            safe_print(f"📁 Reading material detail data from: {input_file}")

        # Detect store ID from file path
        store_id = detect_store_id_from_path(input_file)
        if not quiet and store_id:
            safe_print(f"🏪 Detected store ID: {store_id}")
        elif not quiet:
            safe_print("⚠️ Could not detect store ID from file path")

        # Read the Excel file with 物料 column as text to preserve leading zeros
        df = pd.read_excel(input_file, sheet_name='Sheet1', dtype={'物料': str})

        if not quiet:
            safe_print(f"📊 Found {len(df)} rows of material detail data")

        # Extract unique material types (187-一级分类)
        material_types = []
        material_types_seen = set()

        for material_type_name in df['187-一级分类'].dropna().unique():
            if material_type_name not in material_types_seen:
                material_types_seen.add(material_type_name)
                material_types.append({
                    'name': material_type_name,
                    'description': f'Material type: {material_type_name}',
                    'sort_order': len(material_types) + 1,
                    'is_active': True
                })

        if not quiet:
            safe_print(
                f"🏷️  Extracted {len(material_types)} unique material types")

        # Extract unique material child types (187-二级分类) with parent relationships
        material_child_types = []
        child_types_seen = set()

        # Create a mapping of child type to parent type
        child_parent_mapping = {}
        for _, row in df.iterrows():
            parent_type = row.get('187-一级分类')
            child_type = row.get('187-二级分类')

            if pd.notna(parent_type) and pd.notna(child_type):
                if child_type not in child_parent_mapping:
                    child_parent_mapping[child_type] = parent_type

        for child_type_name, parent_type_name in child_parent_mapping.items():
            if child_type_name not in child_types_seen:
                child_types_seen.add(child_type_name)
                material_child_types.append({
                    'name': child_type_name,
                    'parent_type_name': parent_type_name,
                    'description': f'Material child type: {child_type_name}',
                    'sort_order': len(material_child_types) + 1,
                    'is_active': True
                })

        if not quiet:
            safe_print(
                f"🏷️  Extracted {len(material_child_types)} unique material child types")

        # Extract materials with type associations
        materials = []
        materials_seen = set()

        for _, row in df.iterrows():
            # Get material number (required field)
            material_number = clean_material_number(row.get('物料', ''))

            if not material_number:
                continue

            # Skip duplicates (keep first occurrence)
            if material_number in materials_seen:
                continue
            materials_seen.add(material_number)

            # Extract material data
            name = str(row.get('物料描述', '')).strip()
            description = str(row.get('物料描述', '')).strip()
            unit = str(row.get('单位描述', '个')).strip()

            # Extract type information
            material_type_name = row.get('187-一级分类')
            material_child_type_name = row.get('187-二级分类')

            # Validate required fields
            if not name:
                if not quiet:
                    safe_print(
                        f"⚠️  Skipping material {material_number}: Missing name")
                continue

            # Clean up fields
            if not description:
                description = name  # Use name as description if empty
            if not unit:
                unit = '个'  # Default unit

            materials.append({
                'material_number': material_number,
                'name': name,
                'description': description,
                'unit': unit,
                'package_spec': '',  # Not available in this format
                'material_type_name': material_type_name if pd.notna(material_type_name) else None,
                'material_child_type_name': material_child_type_name if pd.notna(material_child_type_name) else None,
                'is_active': True,
                'store_id': store_id  # Add store_id from detected path
            })

        if not quiet:
            safe_print(f"📦 Processed {len(materials)} unique materials")

        # Generate debug CSV if requested
        if debug:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Material types debug
            if material_types:
                debug_file = f"output/material_types_debug_{timestamp}.csv"
                pd.DataFrame(material_types).to_csv(
                    debug_file, index=False, encoding='utf-8-sig')
                safe_print(f"🐛 Material types debug CSV: {debug_file}")

            # Material child types debug
            if material_child_types:
                debug_file = f"output/material_child_types_debug_{timestamp}.csv"
                pd.DataFrame(material_child_types).to_csv(
                    debug_file, index=False, encoding='utf-8-sig')
                safe_print(f"🐛 Material child types debug CSV: {debug_file}")

            # Materials debug
            if materials:
                debug_file = f"output/materials_with_types_debug_{timestamp}.csv"
                pd.DataFrame(materials).to_csv(
                    debug_file, index=False, encoding='utf-8-sig')
                safe_print(f"🐛 Materials with types debug CSV: {debug_file}")

        return material_types, material_child_types, materials

    except Exception as e:
        safe_print(f"❌ Error extracting material data: {e}")
        import traceback
        traceback.print_exc()
        return [], [], []


def insert_material_data_to_database(material_types, material_child_types, materials, is_test=False, quiet=False):
    """
    Insert material types, child types, and materials to database.

    Args:
        material_types: List of material type dictionaries
        material_child_types: List of material child type dictionaries  
        materials: List of material dictionaries
        is_test: Use test database
        quiet: Suppress verbose output

    Returns:
        bool: Success status
    """

    try:
        if get_database_manager is None:
            if not quiet:
                safe_print("❌ Database connection module not available")
            return False

        if not quiet:
            safe_print(
                f"🗄️  Connecting to {'test' if is_test else 'production'} database...")

        config = DatabaseConfig(is_test=is_test)
        db_manager = get_database_manager(is_test=is_test)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:

                # Step 1: Insert/Update material types
                if not quiet:
                    safe_print(
                        f"1️⃣  Inserting {len(material_types)} material types...")

                material_type_ids = {}  # Map name to ID

                for material_type in material_types:
                    query = """
                    INSERT INTO material_type (name, description, sort_order, is_active)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name) 
                    DO UPDATE SET
                        description = EXCLUDED.description,
                        sort_order = EXCLUDED.sort_order,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id;
                    """

                    cursor.execute(query, (
                        material_type['name'],
                        material_type['description'],
                        material_type['sort_order'],
                        material_type['is_active']
                    ))

                    result = cursor.fetchone()
                    material_type_ids[material_type['name']] = result['id']

                # Step 2: Insert/Update material child types
                if not quiet:
                    safe_print(
                        f"2️⃣  Inserting {len(material_child_types)} material child types...")

                # Map (parent_name, child_name) to ID
                material_child_type_ids = {}

                for child_type in material_child_types:
                    parent_type_id = material_type_ids.get(
                        child_type['parent_type_name'])

                    if not parent_type_id:
                        if not quiet:
                            safe_print(
                                f"⚠️  Parent type not found for child type: {child_type['name']}")
                        continue

                    query = """
                    INSERT INTO material_child_type (name, material_type_id, description, sort_order, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (material_type_id, name) 
                    DO UPDATE SET
                        description = EXCLUDED.description,
                        sort_order = EXCLUDED.sort_order,
                        is_active = EXCLUDED.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id;
                    """

                    cursor.execute(query, (
                        child_type['name'],
                        parent_type_id,
                        child_type['description'],
                        child_type['sort_order'],
                        child_type['is_active']
                    ))

                    result = cursor.fetchone()
                    key = (child_type['parent_type_name'], child_type['name'])
                    material_child_type_ids[key] = result['id']

                # Step 3: Insert/Update materials with type associations
                if not quiet:
                    safe_print(
                        f"3️⃣  Inserting {len(materials)} materials with type associations...")

                inserted_count = 0
                updated_count = 0

                for material in materials:
                    # Get type IDs
                    material_type_id = None
                    material_child_type_id = None

                    if material['material_type_name']:
                        material_type_id = material_type_ids.get(
                            material['material_type_name'])

                    if material['material_child_type_name'] and material['material_type_name']:
                        key = (material['material_type_name'],
                               material['material_child_type_name'])
                        material_child_type_id = material_child_type_ids.get(
                            key)

                    # Insert or update materials with type information (store-specific)
                    if material['store_id'] is not None:
                        query = """
                        INSERT INTO material (material_number, name, description, unit, package_spec, 
                                            material_type_id, material_child_type_id, store_id, 
                                            created_at, updated_at, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s)
                        ON CONFLICT (material_number, store_id) 
                        DO UPDATE SET
                            material_type_id = EXCLUDED.material_type_id,
                            material_child_type_id = EXCLUDED.material_child_type_id,
                            name = COALESCE(NULLIF(EXCLUDED.name, ''), material.name),
                            description = COALESCE(NULLIF(EXCLUDED.description, ''), material.description),
                            unit = COALESCE(NULLIF(EXCLUDED.unit, ''), material.unit),
                            package_spec = COALESCE(NULLIF(EXCLUDED.package_spec, ''), material.package_spec),
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted
                        """

                        cursor.execute(query, (
                            material['material_number'],
                            material['name'],
                            material['description'],
                            material['unit'],
                            material['package_spec'],
                            material_type_id,
                            material_child_type_id,
                            material['store_id'],
                            material['is_active']
                        ))

                        result = cursor.fetchone()
                        if result and result['inserted']:
                            inserted_count += 1
                        else:
                            updated_count += 1
                    else:
                        # Fallback to update-only approach if store_id cannot be detected
                        query = """
                        UPDATE material 
                        SET material_type_id = %s,
                            material_child_type_id = %s,
                            name = COALESCE(NULLIF(%s, ''), name),
                            description = COALESCE(NULLIF(%s, ''), description),
                            unit = COALESCE(NULLIF(%s, ''), unit),
                            package_spec = COALESCE(NULLIF(%s, ''), package_spec),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE material_number = %s
                        """

                        cursor.execute(query, (
                            material_type_id,
                            material_child_type_id,
                            material['name'],
                            material['description'],
                            material['unit'],
                            material['package_spec'],
                            material['material_number']
                        ))

                        if cursor.rowcount > 0:
                            updated_count += 1

                # Commit the transaction
                conn.commit()

        if not quiet:
            safe_print("✅ Database update completed:")
            safe_print(f"   📋 Material types: {len(material_types)}")
            safe_print(
                f"   📋 Material child types: {len(material_child_types)}")
            safe_print(f"   📦 Materials inserted: {inserted_count}")
            safe_print(f"   📦 Materials updated: {updated_count}")
            safe_print(f"   📦 Total materials processed: {len(materials)}")

        return True

    except Exception as e:
        if not quiet:
            safe_print(f"❌ Database insertion failed: {e}")
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main entry point for material detail extraction with types"""

    parser = argparse.ArgumentParser(
        description='Extract material data with type classifications from material_detail Excel files'
    )
    parser.add_argument(
        'input_file', help='Path to the material_detail Excel file')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Generate CSV files for manual verification')
    parser.add_argument('--direct-db', action='store_true',
                        help='Insert directly to database (default behavior)')
    parser.add_argument('--test-db', action='store_true',
                        help='Use test database (only with --direct-db)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress verbose output')

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_file):
        safe_print(f"❌ Input file not found: {args.input_file}")
        sys.exit(1)

    is_test = args.test_db
    quiet = args.quiet

    if not quiet:
        safe_print("🍲 HAIDILAO MATERIAL DETAIL EXTRACTION WITH TYPES")
        safe_print("=" * 60)
        safe_print(f"�� Input file: {args.input_file}")
        safe_print(f"🗄️  Database: {'test' if is_test else 'production'}")
        safe_print(f"🐛 Debug mode: {'enabled' if args.debug else 'disabled'}")
        safe_print("=" * 60)

    # Extract data
    material_types, material_child_types, materials = extract_material_types_and_materials(
        input_file=args.input_file,
        debug=args.debug,
        quiet=quiet
    )

    if not material_types and not materials:
        if not quiet:
            safe_print("❌ No valid material data found")
        sys.exit(1)

    # Insert to database
    success = insert_material_data_to_database(
        material_types=material_types,
        material_child_types=material_child_types,
        materials=materials,
        is_test=is_test,
        quiet=quiet
    )

    if not quiet:
        safe_print("=" * 60)

    if success:
        if quiet:
            safe_print("Finished")
        else:
            safe_print(
                "🎉 Material detail extraction with types completed successfully!")
        sys.exit(0)
    else:
        if quiet:
            safe_print("ERROR: Extraction failed")
        else:
            safe_print(
                "❌ Material detail extraction failed. Check the error messages above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
