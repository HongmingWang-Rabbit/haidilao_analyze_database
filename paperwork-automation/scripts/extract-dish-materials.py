#!/usr/bin/env python3
"""
Extract dish-material relationships from inventory calculation data and generate SQL or insert to database.
Handles dish_material table with proper dish and material ID lookups.
"""

import pandas as pd
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Try to import database utilities
try:
    import sys
    sys.path.append('.')
    from utils.database import get_database_manager, DatabaseConfig
    get_database_manager = get_database_manager
except ImportError:
    print("⚠️  Database module not found. SQL file generation only.")
    get_database_manager = None

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def check_database_availability(dish_code, dish_size, material_number, is_test=True):
    """Check if dish and material exist in database"""
    if get_database_manager is None:
        return "DATABASE_CHECK_UNAVAILABLE", "Cannot connect to database"

    try:
        db_manager = get_database_manager(is_test=is_test)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check dish existence - convert dish_code to string to match VARCHAR type
                dish_code_str = str(dish_code)
                if dish_size:
                    cursor.execute("""
                        SELECT id FROM dish 
                        WHERE full_code = %s AND size = %s
                    """, (dish_code_str, dish_size))
                else:
                    cursor.execute("""
                        SELECT id FROM dish 
                        WHERE full_code = %s AND (size IS NULL OR size = '')
                    """, (dish_code_str,))

                dish_result = cursor.fetchone()
                if not dish_result:
                    return "DATABASE_INSERTION_FAILED", f"Dish not found: code={dish_code_str}, size='{dish_size}'"

                # Check material existence - convert material_number to string
                material_number_str = str(material_number)
                cursor.execute("""
                    SELECT id FROM material 
                    WHERE material_number = %s
                """, (material_number_str,))

                material_result = cursor.fetchone()
                if not material_result:
                    return "DATABASE_INSERTION_FAILED", f"Material not found: number={material_number_str}"

                return "SUCCESS", "Both dish and material found in database"

    except Exception as e:
        return "DATABASE_CHECK_ERROR", f"Database error: {str(e)}"


def generate_failure_analysis_report(df: pd.DataFrame, output_file: str = None, is_test: bool = True) -> str:
    """Generate comprehensive failure analysis report for all records"""

    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"output/dish_material_failure_analysis_{timestamp}.csv"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    print(f"📊 Generating failure analysis report...")

    all_records = []
    extraction_failed = 0
    database_failed = 0
    successful = 0

    for index, row in df.iterrows():
        # Extract basic information
        dish_name = row['菜品名称'] if pd.notna(row['菜品名称']) else 'N/A'
        dish_code = row['菜品编码'] if pd.notna(row['菜品编码']) else None
        dish_size = row['规格'] if pd.notna(row['规格']) else ''
        material_name = row['物料描述'] if pd.notna(row['物料描述']) else 'N/A'
        material_number_raw = row['物料号'] if pd.notna(row['物料号']) else None
        quantity = row['物料单位'] if pd.notna(row['物料单位']) else None

        # Clean material number
        material_number = clean_material_number(material_number_raw)

        record = {
            'row_number': index + 1,
            'dish_name': dish_name,
            'dish_number': clean_dish_code(dish_code) if dish_code else 'MISSING',
            'dish_size': dish_size if dish_size else 'N/A',
            'material_name': material_name,
            'material_number': material_number if material_number else 'MISSING',
            'quantity': quantity if quantity is not None else 'MISSING',
            'failure_stage': '',
            'reason': '',
            'detailed_reason': ''
        }

        # Check extraction phase failures
        if not dish_code:
            record['failure_stage'] = 'EXTRACTION'
            record['reason'] = 'Missing dish number'
            record['detailed_reason'] = 'The 菜品编码 column is empty for this row'
            extraction_failed += 1
        elif not material_number:
            record['failure_stage'] = 'EXTRACTION'
            record['reason'] = 'Missing material number'
            record['detailed_reason'] = 'The 物料号 column is empty for this row'
            extraction_failed += 1
        elif quantity is None or quantity == 0:
            record['failure_stage'] = 'EXTRACTION'
            record['reason'] = 'Missing or zero quantity'
            record['detailed_reason'] = f'The 物料单位 column is {quantity} for this row'
            extraction_failed += 1
        else:
            # Valid for extraction, check database availability
            status, reason = check_database_availability(
                dish_code, dish_size, material_number, is_test)

            if status == "SUCCESS":
                record['failure_stage'] = 'SUCCESS'
                record['reason'] = 'Successfully processed'
                record['detailed_reason'] = 'Record was successfully extracted and inserted to database'
                successful += 1
            else:
                record['failure_stage'] = 'DATABASE_INSERTION'
                record['reason'] = status.replace('_', ' ').title()
                record['detailed_reason'] = reason
                database_failed += 1

        all_records.append(record)

    # Create DataFrame and save to CSV
    analysis_df = pd.DataFrame(all_records)

    # Reorder columns for better readability
    column_order = [
        'row_number', 'failure_stage', 'reason',
        'dish_name', 'dish_number', 'dish_size',
        'material_name', 'material_number', 'quantity',
        'detailed_reason'
    ]

    analysis_df = analysis_df[column_order]
    analysis_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"📄 Failure analysis report generated: {output_file}")
    print(f"📈 Analysis summary:")
    print(f"   [OK] Successful: {successful}")
    print(f"   [WARN] Extraction failed: {extraction_failed}")
    print(f"   [ERROR] Database insertion failed: {database_failed}")
    print(f"   [TOTAL] Total: {len(all_records)}")

    return output_file


def clean_dish_code(code):
    """Clean and validate dish code"""
    if pd.isna(code):
        return None

    # Convert to string and clean
    code_str = str(code).strip()

    # Remove .0 if it's a whole number (e.g., 90001690.0 -> 90001690)
    if code_str.endswith('.0'):
        code_str = code_str[:-2]

    return code_str if code_str and code_str != '-' else None


def clean_material_number(material_num):
    """Clean and validate material number"""
    if pd.isna(material_num):
        return None

    # Convert to string and clean
    material_str = str(material_num).strip()

    # Remove .0 if it's a whole number (e.g., 3000759.0 -> 3000759)
    if material_str.endswith('.0'):
        material_str = material_str[:-2]

    return material_str if material_str and material_str != '-' else None


def escape_sql_string(value):
    """Escape string for SQL insertion"""
    if value is None:
        return 'NULL'

    # Escape single quotes and wrap in quotes
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def extract_dish_materials(df: pd.DataFrame) -> List[Dict]:
    """
    Extract dish-material relationships from DataFrame

    Returns:
        List of dish_material dictionaries
    """

    print("🔗 Extracting dish-material relationships...")

    dish_materials = []
    processed_count = 0
    skipped_count = 0

    for index, row in df.iterrows():
        processed_count += 1

        # Extract and clean dish code
        dish_code = clean_dish_code(row['菜品编码'])
        if not dish_code:
            print(f"⚠️  Row {index + 1}: Missing dish code")
            skipped_count += 1
            continue

        # Extract size/specification
        size = row['规格'] if pd.notna(row['规格']) else None
        if size:
            size = size.strip()

        # Extract and clean material number
        material_number = clean_material_number(row['物料号'])
        if not material_number:
            print(
                f"⚠️  Row {index + 1}: Missing material number for dish {dish_code}")
            skipped_count += 1
            continue

        # Extract standard quantity (物料单位 will now be unit_conversion_rate)
        # For backward compatibility, if 物料单位 exists, use it as unit_conversion_rate
        # Look for standard_quantity in other potential columns like "标准用量" or "出品分量"
        standard_quantity = None
        unit_conversion_rate = 1.0  # Default conversion rate

        # Try to get standard quantity from various possible columns
        for col_name in ['标准用量', '出品分量(kg)', '出品分量', '菜品用量', '物料用量']:
            if col_name in df.columns and pd.notna(row[col_name]):
                try:
                    standard_quantity = float(row[col_name])
                    break
                except (ValueError, TypeError):
                    continue

        # If no standard quantity found in above columns, use a default value of 1.0
        if standard_quantity is None:
            standard_quantity = 1.0

        # Extract unit conversion rate from 物料单位 (this is the new requirement)
        if '物料单位' in df.columns and pd.notna(row['物料单位']):
            try:
                unit_conversion_rate = float(row['物料单位'])
                if unit_conversion_rate <= 0:
                    unit_conversion_rate = 1.0  # Default if invalid
            except (ValueError, TypeError):
                unit_conversion_rate = 1.0  # Default if conversion fails

        # Validate standard quantity
        if standard_quantity <= 0:
            print(
                f"⚠️  Row {index + 1}: Invalid standard quantity {standard_quantity} for dish {dish_code}, material {material_number}, using default 1.0")
            standard_quantity = 1.0

        # Extract loss rate from column O "损耗" or use default 1.0
        loss_rate = 1.0  # Default loss rate (no loss)

        # Look for loss rate in various possible column names (prioritize "损耗" column)
        for col_name in df.columns:
            if '损耗' in str(col_name):  # Column O "损耗" - just look for this column
                if pd.notna(row[col_name]):
                    loss_rate = float(row[col_name])
                    break
            elif '耗损' in str(col_name) or '损失' in str(col_name):
                if pd.notna(row[col_name]):
                    loss_rate = float(row[col_name])
                    break

        # Create dish-material relationship record
        dish_materials.append({
            'dish_code': dish_code,
            'dish_size': size,
            'material_number': material_number,
            'standard_quantity': standard_quantity,
            'loss_rate': loss_rate,
            'unit_conversion_rate': unit_conversion_rate,
            'dish_name': row['菜品名称'] if pd.notna(row['菜品名称']) else '',
            'material_description': row['物料描述'] if pd.notna(row['物料描述']) else ''
        })

    print(f"[OK] Processed {processed_count} rows")
    print(
        f"[OK] Found {len(dish_materials)} valid dish-material relationships")
    print(f"[WARN] Skipped {skipped_count} rows due to missing/invalid data")

    return dish_materials


def generate_sql_file(dish_materials: List[Dict], output_file: str) -> bool:
    """Generate SQL file with UPSERT statements for dish_material data"""

    try:
        print(f"[INFO] Generating SQL file: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- Dish-Material relationships insertion script\n")
            f.write(
                f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(
                f"-- Dish-Material relationships: {len(dish_materials)}\n\n")

            # Insert dish-material relationships
            f.write("-- ========================================\n")
            f.write("-- DISH-MATERIAL RELATIONSHIPS\n")
            f.write("-- ========================================\n\n")

            for dm in dish_materials:
                dish_code = escape_sql_string(dm['dish_code'])
                dish_size = escape_sql_string(
                    dm['dish_size']) if dm['dish_size'] else 'NULL'
                material_number = escape_sql_string(dm['material_number'])
                standard_quantity = dm['standard_quantity']

                # Create comment with readable info
                f.write(
                    f"-- Dish: {dm['dish_name']} ({dm['dish_code']}) -> Material: {dm['material_description']} ({dm['material_number']}) -> Loss Rate: {dm['loss_rate']} -> Unit Conversion Rate: {dm['unit_conversion_rate']}\n")

                sql = f"""INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
SELECT 
    d.id as dish_id,
    m.id as material_id,
    {standard_quantity},
    {dm['loss_rate']},
    {dm['unit_conversion_rate']}
FROM dish d
CROSS JOIN material m
WHERE d.full_code = {dish_code}
  AND (d.size = {dish_size} OR (d.size IS NULL AND {dish_size} IS NULL))
  AND m.material_number = {material_number}
ON CONFLICT (dish_id, material_id)
DO UPDATE SET
    standard_quantity = EXCLUDED.standard_quantity,
    loss_rate = EXCLUDED.loss_rate,
    unit_conversion_rate = EXCLUDED.unit_conversion_rate,
    updated_at = CURRENT_TIMESTAMP;

"""
                f.write(sql)

            f.write(f"\n-- End of dish-material insertion script\n")
            f.write(
                f"-- {len(dish_materials)} dish-material relationships processed\n")

        print(f"[OK] SQL file generated successfully: {output_file}")
        return True

    except Exception as e:
        print(f"[ERROR] Error generating SQL file: {e}")
        import traceback
        traceback.print_exc()
        return False


def insert_to_database(dish_materials: List[Dict], is_test: bool = False) -> bool:
    """Insert dish-material relationships directly to database"""

    try:
        if get_database_manager is None:
            print("[ERROR] Database connection module not available")
            return False

        print(
            f"🗄️  Connecting to {'test' if is_test else 'production'} database...")

        db_manager = get_database_manager(is_test=is_test)

        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:

                print(
                    f"[INFO] Inserting {len(dish_materials)} dish-material relationships...")
                inserted = 0
                updated = 0
                errors = 0

                for dm in dish_materials:
                    try:
                        # Get dish ID
                        if dm['dish_size']:
                            cursor.execute("""
                                SELECT id FROM dish 
                                WHERE full_code = %s AND size = %s
                            """, (dm['dish_code'], dm['dish_size']))
                        else:
                            cursor.execute("""
                                SELECT id FROM dish 
                                WHERE full_code = %s AND size IS NULL
                            """, (dm['dish_code'],))

                        dish_result = cursor.fetchone()
                        if not dish_result:
                            print(
                                f"⚠️  Warning: Dish not found - code: {dm['dish_code']}, size: {dm['dish_size']}")
                            errors += 1
                            continue

                        dish_id = dish_result['id']

                        # Get material ID
                        cursor.execute("""
                            SELECT id FROM material 
                            WHERE material_number = %s
                        """, (dm['material_number'],))

                        material_result = cursor.fetchone()
                        if not material_result:
                            print(
                                f"⚠️  Warning: Material not found - number: {dm['material_number']}")
                            errors += 1
                            continue

                        material_id = material_result['id']

                        # Insert dish-material relationship
                        query = """
                        INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate, unit_conversion_rate)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (dish_id, material_id)
                        DO UPDATE SET
                            standard_quantity = EXCLUDED.standard_quantity,
                            loss_rate = EXCLUDED.loss_rate,
                            unit_conversion_rate = EXCLUDED.unit_conversion_rate,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING (xmax = 0) AS inserted;
                        """

                        cursor.execute(query, (
                            dish_id,
                            material_id,
                            dm['standard_quantity'],
                            dm['loss_rate'],
                            dm['unit_conversion_rate']
                        ))

                        result = cursor.fetchone()
                        if result and result['inserted']:
                            inserted += 1
                        else:
                            updated += 1

                    except Exception as e:
                        print(
                            f"[ERROR] Error processing dish {dm['dish_code']} - material {dm['material_number']}: {e}")
                        errors += 1
                        continue

                # Commit transaction
                conn.commit()

                print(f"[OK] Database insertion completed:")
                print(f"   [INFO] Inserted: {inserted} new relationships")
                print(f"   [INFO] Updated: {updated} existing relationships")
                if errors > 0:
                    print(f"   [ERROR] Errors: {errors} relationships failed")

                return errors == 0

    except Exception as e:
        print(f"[ERROR] Database insertion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def extract_dish_materials_to_sql(input_file: str, output_file: str = None, debug: bool = False,
                                  direct_db: bool = False, is_test: bool = False) -> bool:
    """
    Main function to extract dish-material data from Excel and generate SQL or insert to database

    Args:
        input_file: Path to input Excel file
        output_file: Path to output SQL file (if not direct_db)
        debug: Enable debug output
        direct_db: Insert directly to database instead of generating SQL
        is_test: Use test database (only applies if direct_db=True)

    Returns:
        bool: Success status
    """

    try:
        print("Haidilao Dish-Material Extraction Tool")
        print("=" * 50)

        # Validate input file
        if not os.path.exists(input_file):
            print(f"[ERROR] Input file not found: {input_file}")
            return False

        print(f"[INFO] Reading Excel file: {input_file}")

        # Read the calculation worksheet
        try:
            df = pd.read_excel(input_file, sheet_name='计算')
            print(f"[OK] Successfully read {len(df)} rows from '计算' worksheet")
        except Exception as e:
            print(f"[ERROR] Error reading Excel file: {e}")
            return False

        if debug:
            print(f"\n🔍 Debug: DataFrame shape: {df.shape}")
            print(f"🔍 Debug: Columns: {list(df.columns)}")

        # Extract dish-material relationships
        dish_materials = extract_dish_materials(df)

        if not dish_materials:
            print("[ERROR] No valid dish-material relationships found")
            return False

        if debug:
            print(f"\n🔍 Debug: Sample dish-material relationships:")
            for i, dm in enumerate(dish_materials[:3]):
                print(
                    f"  {i+1}. Dish: {dm['dish_code']} ({dm['dish_size']}) -> Material: {dm['material_number']} -> Qty: {dm['standard_quantity']}")

        # Generate failure analysis report (always generate for debugging)
        analysis_file = generate_failure_analysis_report(df, is_test=is_test)

        # Generate output
        if direct_db:
            success = insert_to_database(dish_materials, is_test=is_test)
        else:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"output/dish_materials_{timestamp}.sql"

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            success = generate_sql_file(dish_materials, output_file)

        if success:
            print(f"\nDish-material extraction completed successfully!")
            if not direct_db:
                print(f"SQL file: {output_file}")
            print(
                f"Processed: {len(dish_materials)} dish-material relationships")
        else:
            print(f"\nDish-material extraction failed")

        print(f"\nDebug Report:")
        print(f"Failure analysis: {analysis_file}")
        print(f"Use this report to understand what worked and what failed")

        return success

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Extract dish-material relationships from Haidilao inventory calculation data"
    )

    parser.add_argument(
        "input_file",
        help="Path to input Excel file (CA02-盘点结果-2505-待回复.xls)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output SQL file path (default: auto-generated in output/)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )

    parser.add_argument(
        "--direct-db",
        action="store_true",
        help="Insert directly to database instead of generating SQL file"
    )

    parser.add_argument(
        "--test-db",
        action="store_true",
        help="Use test database (only applies with --direct-db)"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()

    success = extract_dish_materials_to_sql(
        input_file=args.input_file,
        output_file=args.output,
        debug=args.debug,
        direct_db=args.direct_db,
        is_test=args.test_db
    )

    if args.quiet:
        if success:
            print("Finished")
        else:
            # For quiet mode, still show percentage info if available
            try:
                # Try to extract some stats from the output for quiet mode
                if 'dish_materials' in locals():
                    print(f"Partial success - check logs for details")
                else:
                    print("ERROR: Extraction failed")
            except:
                print("ERROR: Extraction failed")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
