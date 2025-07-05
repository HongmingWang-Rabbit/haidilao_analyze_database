#!/usr/bin/env python3
"""
Complete Monthly Automation - New Workflow
Processes monthly report data from Input/monthly_report folder.

Workflow:
1. Extract from monthly_dish_sale: dish_type, dish_child_type, dish, dish_price_history, dish_monthly_sale
2. Extract from material_detail: material, material_price_history
3. Extract from inventory_checking_result: inventory_count, material_price_history
4. Extract from calculated_dish_material_usage: dish_material relationships
5. Generate analysis workbook with material variance calculations
"""

from utils.database import DatabaseManager, DatabaseConfig
import sys
import os
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
from openpyxl import Workbook


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonthlyAutomationProcessor:
    """Complete monthly automation data processor."""

    def __init__(self, is_test: bool = False):
        """Initialize the processor."""
        self.config = DatabaseConfig(is_test=is_test)
        self.db_manager = DatabaseManager(self.config)
        self.input_folder = Path("Input/monthly_report")
        self.results = {
            'dish_types': 0,
            'dish_child_types': 0,
            'dishes': 0,
            'material_types': 0,
            'material_child_types': 0,
            'materials': 0,
            'dish_price_history': 0,
            'material_price_history': 0,
            'dish_monthly_sales': 0,
            'inventory_counts': 0,
            'dish_materials': 0,
            'monthly_material_report': 0,
            'monthly_beverage_report': 0,
            'errors': []
        }

    def log_result(self, category: str, count: int, message: str = ""):
        """Log processing results."""
        self.results[category] = count
        if message:
            logger.info(f"{message}: {count}")
        else:
            logger.info(f"Processed {category}: {count}")

    def get_store_mapping(self) -> Dict[str, int]:
        """Get store name to ID mapping."""
        store_mapping = {}
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name FROM store WHERE is_active = TRUE")
                for store in cursor.fetchall():
                    store_mapping[store['name']] = store['id']
        except Exception as e:
            logger.error(f"Failed to get store mapping: {e}")
        return store_mapping

    def extract_dish_types_and_dishes(self, file_path: Path) -> bool:
        """Extract dish types, child types, dishes from monthly dish sales."""
        logger.info(f"DISH: Extracting dish data from: {file_path.name}")

        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            logger.info(f"Loaded {len(df)} rows from dish sales file")

            # Get store mapping
            store_mapping = self.get_store_mapping()

            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Extract dish types (大类名称)
                dish_types = df['大类名称'].dropna().unique()
                dish_type_count = 0
                for dish_type in dish_types:
                    cursor.execute("""
                        INSERT INTO dish_type (name)
                        VALUES (%s)
                        ON CONFLICT (name) DO NOTHING
                    """, (dish_type,))
                    dish_type_count += cursor.rowcount

                self.log_result('dish_types', dish_type_count,
                                "Inserted dish types")

                # Extract dish child types (子类名称)
                child_type_count = 0
                for _, row in df[['大类名称', '子类名称']].dropna().drop_duplicates().iterrows():
                    cursor.execute("""
                        INSERT INTO dish_child_type (name, dish_type_id)
                        SELECT %s, dt.id FROM dish_type dt WHERE dt.name = %s
                        ON CONFLICT (dish_type_id, name) DO NOTHING
                    """, (row['子类名称'], row['大类名称']))
                    child_type_count += cursor.rowcount

                self.log_result('dish_child_types',
                                child_type_count, "Inserted dish child types")

                # Extract dishes with size information
                dish_count = 0
                price_history_count = 0
                monthly_sales_count = 0

                for _, row in df.iterrows():
                    try:
                        # Clean dish code (remove .0 suffix from floats)
                        full_code = str(int(row['菜品编码'])) if pd.notna(
                            row['菜品编码']) else None
                        short_code = str(int(row['菜品短编码'])) if pd.notna(
                            row['菜品短编码']) else None

                        if not full_code:
                            continue

                        # Insert or update dish
                        cursor.execute("""
                            INSERT INTO dish (
                                name, full_code, short_code, size,
                                dish_child_type_id, specification, unit
                            )
                            SELECT %s, %s, %s, %s, dct.id, %s, %s
                            FROM dish_child_type dct
                            JOIN dish_type dt ON dct.dish_type_id = dt.id
                            WHERE dt.name = %s AND dct.name = %s
                            ON CONFLICT (full_code, size) DO UPDATE SET
                                name = EXCLUDED.name,
                                short_code = EXCLUDED.short_code,
                                specification = EXCLUDED.specification,
                                unit = EXCLUDED.unit,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            row['菜品名称'], full_code, short_code, row['规格'],
                            row['规格'], row['菜品单位'], row['大类名称'], row['子类名称']
                        ))
                        dish_count += cursor.rowcount

                        # Extract dish price history
                        store_name = row['门店名称']
                        if store_name in store_mapping and pd.notna(row['菜品单价']):
                            store_id = store_mapping[store_name]
                            price = float(row['菜品单价'])

                            # Mark existing prices as inactive if different
                            cursor.execute("""
                                UPDATE dish_price_history
                                SET is_active = FALSE
                                WHERE dish_id IN (SELECT id FROM dish WHERE full_code = %s AND size = %s)
                                AND store_id = %s AND price != %s AND is_active = TRUE
                            """, (full_code, row['规格'], store_id, price))

                            # Insert new price history
                            cursor.execute("""
                                INSERT INTO dish_price_history (
                                    dish_id, store_id, price, effective_date, is_active
                                )
                                SELECT d.id, %s, %s, %s, TRUE
                                FROM dish d
                                WHERE d.full_code = %s AND d.size = %s
                                ON CONFLICT (dish_id, store_id, effective_date) DO UPDATE SET
                                    price = EXCLUDED.price,
                                    is_active = TRUE
                            """, (store_id, price, self.target_date, full_code, row['规格']))
                            price_history_count += cursor.rowcount

                        # Extract monthly sales data
                        if store_name in store_mapping:
                            store_id = store_mapping[store_name]
                            # Extract year and month from date string
                            # e.g., "2025-06-01--2025-06-30"
                            date_str = row['日期']
                            if '--' in date_str:
                                start_date = date_str.split('--')[0]
                                year, month = start_date.split('-')[:2]

                                cursor.execute("""
                                    INSERT INTO dish_monthly_sale (
                                        dish_id, store_id, year, month,
                                        sale_amount, return_amount, free_meal_amount, gift_amount
                                    )
                                    SELECT d.id, %s, %s, %s, %s, %s, %s, %s
                                    FROM dish d
                                    WHERE d.full_code = %s AND d.size = %s
                                    ON CONFLICT (dish_id, store_id, year, month) DO UPDATE SET
                                        sale_amount = EXCLUDED.sale_amount,
                                        return_amount = EXCLUDED.return_amount,
                                        free_meal_amount = EXCLUDED.free_meal_amount,
                                        gift_amount = EXCLUDED.gift_amount,
                                        updated_at = CURRENT_TIMESTAMP
                                """, (
                                    store_id, int(year), int(month),
                                    row['出品数量'], row['退菜数量'],
                                    row.get('免单数量', 0), row.get('赠菜数量', 0),
                                    full_code, row['规格']
                                ))
                                monthly_sales_count += cursor.rowcount

                    except Exception as e:
                        logger.error(f"Error processing dish row: {e}")
                        self.results['errors'].append(
                            f"Dish extraction error: {e}")
                        continue

                conn.commit()

                self.log_result('dishes', dish_count, "Processed dishes")
                self.log_result(
                    'dish_price_history', price_history_count, "Processed dish price history")
                self.log_result(
                    'dish_monthly_sales', monthly_sales_count, "Processed dish monthly sales")

                return True

        except Exception as e:
            logger.error(f"Failed to extract dish data: {e}")
            self.results['errors'].append(f"Dish data extraction failed: {e}")
            return False

    def extract_material_detail_with_types(self, file_path: Path) -> bool:
        """Extract materials with type classifications from material detail."""
        logger.info(
            f"MATERIAL: Extracting material detail with types from: {file_path.name}")

        try:
            import subprocess
            import sys

            # Run the dedicated material detail extraction script with types
            cmd = [
                sys.executable,
                "scripts/extract_material_detail_with_types.py",
                str(file_path),
                "--direct-db"
            ]

            # Set up environment
            env = os.environ.copy()
            current_dir = str(Path.cwd())
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{current_dir};{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = current_dir

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path.cwd(), env=env)

            if result.returncode == 0:
                logger.info(
                    "SUCCESS: Material detail extraction with types completed")

                # Try to parse output for counts
                output = result.stdout + result.stderr
                material_types_count = 0
                material_child_types_count = 0
                materials_count = 0

                # Look for success patterns in output
                import re
                type_match = re.search(r'Material types:\s*(\d+)', output)
                if type_match:
                    material_types_count = int(type_match.group(1))

                child_type_match = re.search(
                    r'Material child types:\s*(\d+)', output)
                if child_type_match:
                    material_child_types_count = int(child_type_match.group(1))

                material_match = re.search(
                    r'Materials (?:inserted|updated):\s*(\d+)', output)
                if material_match:
                    materials_count = int(material_match.group(1))

                # Alternative pattern for total materials
                total_match = re.search(
                    r'Total materials processed:\s*(\d+)', output)
                if total_match and not materials_count:
                    materials_count = int(total_match.group(1))

                self.log_result(
                    'material_types', material_types_count, "Processed material types")
                self.log_result(
                    'material_child_types', material_child_types_count, "Processed material child types")
                self.log_result('materials', materials_count,
                                "Processed materials with types")

                return True
            else:
                logger.error(
                    f"ERROR: Material detail extraction with types failed: {result.stderr}")
                self.results['errors'].append(
                    f"Material detail extraction failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to extract material detail with types: {e}")
            self.results['errors'].append(
                f"Material detail extraction error: {e}")
            return False

    def extract_material_master_data(self, material_folder: Path) -> bool:
        """Extract material master data (materials, types) from first available store Excel file."""
        logger.info(
            f"MATERIAL MASTER: Extracting material types and materials from: {material_folder}")

        try:
            # Find first available Excel file from any store
            excel_file = None
            for store_folder in sorted(material_folder.iterdir()):
                if not store_folder.is_dir():
                    continue

                # Look for Excel files in this store folder
                excel_files = list(store_folder.glob("*.xlsx")) + list(store_folder.glob("*.XLSX")) + \
                    list(store_folder.glob("*.xls")) + \
                    list(store_folder.glob("*.XLS"))

                if excel_files:
                    excel_file = excel_files[0]
                    logger.info(
                        f"Using store {store_folder.name} file for material master data: {excel_file.name}")
                    break

            if not excel_file:
                logger.error(
                    "No Excel files found in any store folder for material extraction")
                self.results['errors'].append(
                    "No Excel files found for material extraction")
                return False

            # Run the material extraction script
            import subprocess
            import sys

            cmd = [
                sys.executable,
                "-m",
                "scripts.extract_material_detail_with_types",
                str(excel_file),
                "--direct-db",
                "--quiet"
            ]

            if self.config.is_test:
                cmd.append("--test-db")

            # Set up environment
            env = os.environ.copy()
            current_dir = str(Path.cwd())
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{current_dir};{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = current_dir

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path.cwd(), env=env, encoding='utf-8', errors='replace')

            if result.returncode == 0:
                logger.info(
                    "SUCCESS: Material master data extraction completed")

                # Parse output for counts if available
                output = result.stdout + result.stderr
                import re

                # Look for material counts in output
                types_match = re.search(r'Material types: (\d+)', output)
                child_types_match = re.search(
                    r'Material child types: (\d+)', output)
                materials_match = re.search(
                    r'Total materials processed: (\d+)', output)

                types_count = int(types_match.group(1)) if types_match else 0
                child_types_count = int(child_types_match.group(
                    1)) if child_types_match else 0
                materials_count = int(materials_match.group(
                    1)) if materials_match else 0

                self.log_result('material_types', types_count,
                                "Extracted material types")
                self.log_result(
                    'material_child_types', child_types_count, "Extracted material child types")
                self.log_result('materials', materials_count,
                                "Extracted materials with type associations")

                return True
            else:
                logger.error(
                    f"ERROR: Material master data extraction failed: {result.stderr}")
                self.results['errors'].append(
                    f"Material master data extraction failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to extract material master data: {e}")
            self.results['errors'].append(
                f"Material master data extraction error: {e}")
            return False

    def extract_material_detail_batch(self, material_folder: Path) -> bool:
        """Extract material detail with types and store-specific pricing from all store subfolders."""
        logger.info(
            f"MATERIAL: Batch extracting material detail from store subfolders: {material_folder}")

        try:
            import subprocess
            import sys

            # Run the dedicated batch material detail extraction script
            cmd = [
                sys.executable,
                "-m",
                "scripts.extract_material_detail_prices_by_store_batch",
                "--material-detail-path",
                str(material_folder),
                "--target-date",
                self.target_date,
                "--test" if self.config.is_test else ""
            ]

            # Remove empty --test flag if not testing
            if not self.config.is_test:
                cmd = [arg for arg in cmd if arg]

            # Set up environment
            env = os.environ.copy()
            current_dir = str(Path.cwd())
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{current_dir};{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = current_dir

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path.cwd(), env=env, encoding='utf-8', errors='replace')

            if result.returncode == 0:
                logger.info(
                    "SUCCESS: Batch material detail extraction completed")

                # Parse output for processing counts
                output = result.stdout + result.stderr

                # Look for processing counts in output
                import re
                stores_match = re.search(r'🏪 Stores processed: (\d+)', output)
                prices_match = re.search(
                    r'💰 Total prices extracted: (\d+)', output)

                stores_count = int(stores_match.group(1)
                                   ) if stores_match else 0
                prices_count = int(prices_match.group(1)
                                   ) if prices_match else 0

                self.log_result('materials', 0,
                                "Material master data (handled by separate extraction)")
                self.log_result('material_price_history', prices_count,
                                f"Extracted material prices from {stores_count} stores")

                return True
            else:
                # Check if this is just a "materials not found" issue
                error_output = result.stderr.strip()
                if "Material not found" in error_output or not error_output:
                    logger.warning(
                        "WARNING: Batch material detail extraction had missing materials (expected)")
                    logger.info(
                        "This is normal - materials need to be imported first via material extraction")

                    # Parse what was actually processed
                    output = result.stdout + result.stderr
                    import re
                    stores_match = re.search(
                        r'🏪 Stores processed: (\d+)', output)
                    prices_match = re.search(
                        r'💰 Total prices extracted: (\d+)', output)

                    stores_count = int(stores_match.group(1)
                                       ) if stores_match else 0
                    prices_count = int(prices_match.group(1)
                                       ) if prices_match else 0

                    if stores_count > 0 and prices_count > 0:
                        logger.info(
                            f"Successfully processed {prices_count} prices from {stores_count} stores")
                        self.log_result('material_price_history', prices_count,
                                        f"Extracted material prices from {stores_count} stores (materials pending)")
                        return True

                logger.error(
                    f"ERROR: Batch material detail extraction failed: {error_output}")
                self.results['errors'].append(
                    f"Batch material detail extraction failed: {error_output}")
                return False

        except Exception as e:
            logger.error(f"Failed to extract material detail batch: {e}")
            self.results['errors'].append(
                f"Batch material detail extraction error: {e}")
            return False

    def extract_inventory_data(self, inventory_folder: Path) -> bool:
        """Extract inventory data from store folders."""
        logger.info(
            f"STORE: Extracting inventory data from: {inventory_folder.name}")

        try:
            # Track successful processing
            inventory_count = 0

            # Process each store folder (1, 2, 7)
            for store_folder in inventory_folder.iterdir():
                if not store_folder.is_dir():
                    continue

                try:
                    store_id = int(store_folder.name)
                    logger.info(f"Processing store {store_id} inventory...")

                    # Find Excel files in store folder
                    excel_files = list(store_folder.glob(
                        "*.xls*")) + list(store_folder.glob("*.XLS*"))
                    if not excel_files:
                        logger.warning(
                            f"No Excel files found in store {store_id} folder")
                        continue

                    # Process first Excel file found
                    excel_file = excel_files[0]
                    logger.info(f"Reading inventory file: {excel_file.name}")

                    # Read Excel file with automatic engine detection
                    try:
                        df = pd.read_excel(excel_file, engine='openpyxl')
                    except Exception:
                        try:
                            df = pd.read_excel(excel_file, engine='xlrd')
                        except Exception as e:
                            logger.error(
                                f"Failed to read Excel file {excel_file}: {e}")
                            continue

                    logger.info(f"Found {len(df)} rows in inventory file")

                    # Process inventory data
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        successful_rows = 0

                        for _, row in df.iterrows():
                            try:
                                # Extract material number and quantities
                                material_number = str(int(row['物料编码'])) if pd.notna(
                                    row['物料编码']) else None

                                # Get both values from inventory file for consistency
                                stock_qty = float(row['库存数量']) if pd.notna(
                                    row['库存数量']) else 0  # For System Record
                                counted_qty = float(row['盘点数量']) if pd.notna(
                                    row['盘点数量']) else 0  # For Inventory Count

                                if not material_number:
                                    continue

                                # Store 库存数量 as material monthly usage (System Record)
                                # This ensures consistency - all data from inventory file
                                from datetime import datetime
                                # Use the target date passed to the processor, not system date
                                if hasattr(self, 'target_date') and self.target_date:
                                    target_dt = datetime.strptime(
                                        self.target_date, '%Y-%m-%d')
                                else:
                                    target_dt = datetime.now()
                                year, month = target_dt.year, target_dt.month

                                cursor.execute("""
                                    INSERT INTO material_monthly_usage (
                                        material_id, store_id, year, month, material_used
                                    )
                                    SELECT m.id, %s, %s, %s, %s
                                    FROM material m
                                    WHERE m.material_number = %s
                                    ON CONFLICT (material_id, store_id, year, month) DO UPDATE SET
                                        material_used = EXCLUDED.material_used
                                """, (store_id, year, month, stock_qty, material_number))

                                # Store 盘点数量 as inventory count (Inventory Count)
                                # Use monthly-based approach: delete existing records for this month first
                                # Use the manually entered inventory count date
                                if hasattr(self, 'inventory_count_date') and self.inventory_count_date:
                                    count_date = datetime.strptime(
                                        self.inventory_count_date, '%Y-%m-%d').date()
                                else:
                                    count_date = target_dt.date()  # Fallback to target date

                                # Delete any existing inventory records for this store/material/month
                                cursor.execute("""
                                    DELETE FROM inventory_count ic
                                    USING material m
                                    WHERE ic.material_id = m.id 
                                    AND ic.store_id = %s 
                                    AND m.material_number = %s
                                    AND EXTRACT(YEAR FROM ic.count_date) = %s
                                    AND EXTRACT(MONTH FROM ic.count_date) = %s
                                """, (store_id, material_number, year, month))

                                # Insert new record with manually entered count date
                                cursor.execute("""
                                    INSERT INTO inventory_count (
                                        store_id, material_id, count_date, counted_quantity
                                    )
                                    SELECT %s, m.id, %s, %s
                                    FROM material m
                                    WHERE m.material_number = %s
                                """, (store_id, count_date, counted_qty, material_number))
                                inventory_count += 1  # Count as successful

                                # NOTE: Now using inventory file for both System Record and Inventory Count
                                # This eliminates discrepancies between different data sources

                                # NOTE: Material prices should come from material detail files only,
                                # not from inventory data (which contains quantities, not prices)

                                successful_rows += 1

                            except Exception as e:
                                logger.error(
                                    f"Error processing inventory row for store {store_id}: {e}")
                                # Rollback and start new transaction
                                conn.rollback()
                                continue

                        conn.commit()
                        logger.info(
                            f"Successfully processed {successful_rows} inventory records for store {store_id}")

                except Exception as e:
                    logger.error(
                        f"Error processing store {store_folder.name}: {e}")
                    self.results['errors'].append(
                        f"Store {store_folder.name} inventory error: {e}")
                    continue

            self.log_result('inventory_counts', inventory_count,
                            "Processed inventory data (System Record + Inventory Count)")
            # Note: Material monthly usage now comes from inventory file 库存数量 for consistency
            return True

        except Exception as e:
            logger.error(f"Failed to extract inventory data: {e}")
            self.results['errors'].append(
                f"Inventory data extraction failed: {e}")
            return False

    def extract_dish_materials(self, file_path: Path) -> bool:
        """Extract dish-material relationships from calculated dish material usage."""
        logger.info(
            f"RELATION: Extracting dish-material relationships from: {file_path.name}")

        try:
            # Read the 计算 sheet
            df = pd.read_excel(file_path, sheet_name='计算')
            logger.info(
                f"Loaded {len(df)} rows from dish-material relationships")

            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                dish_material_count = 0

                for _, row in df.iterrows():
                    try:
                        # Get dish and material identifiers
                        full_code = str(int(row['菜品编码'])) if pd.notna(
                            row['菜品编码']) else None
                        short_code = str(int(row['菜品短编码'])) if pd.notna(
                            row['菜品短编码']) else None
                        material_number = str(int(row['物料号'])) if pd.notna(
                            row['物料号']) else None

                        if not full_code or not material_number:
                            continue

                        # Get standard quantity from column N (出品分量(kg))
                        standard_qty = float(row['出品分量(kg)']) if pd.notna(
                            row['出品分量(kg)']) else 0
                        if standard_qty <= 0:
                            continue

                        # Get loss rate from column O "损耗" or use default 1.0
                        loss_rate = 1.0  # Default loss rate (no loss)

                        # Look for loss rate in various possible column names (prioritize "损耗" column)
                        for col_name in df.columns:
                            # Column O "损耗" - just look for this column
                            if '损耗' in str(col_name):
                                if pd.notna(row[col_name]):
                                    loss_rate = float(row[col_name])
                                    break
                            elif '耗损' in str(col_name) or '损失' in str(col_name):
                                if pd.notna(row[col_name]):
                                    loss_rate = float(row[col_name])
                                    break

                        # Try to match dish by both full and short code if short exists
                        if short_code:
                            cursor.execute("""
                                INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate)
                                SELECT d.id, m.id, %s, %s
                                FROM dish d, material m
                                WHERE (d.full_code = %s OR d.short_code = %s)
                                AND m.material_number = %s
                                ON CONFLICT (dish_id, material_id) DO UPDATE SET
                                    standard_quantity = EXCLUDED.standard_quantity,
                                    loss_rate = EXCLUDED.loss_rate,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (standard_qty, loss_rate, full_code, short_code, material_number))
                        else:
                            cursor.execute("""
                                INSERT INTO dish_material (dish_id, material_id, standard_quantity, loss_rate)
                                SELECT d.id, m.id, %s, %s
                                FROM dish d, material m
                                WHERE d.full_code = %s AND m.material_number = %s
                                ON CONFLICT (dish_id, material_id) DO UPDATE SET
                                    standard_quantity = EXCLUDED.standard_quantity,
                                    loss_rate = EXCLUDED.loss_rate,
                                    updated_at = CURRENT_TIMESTAMP
                            """, (standard_qty, loss_rate, full_code, material_number))

                        dish_material_count += cursor.rowcount

                    except Exception as e:
                        logger.error(
                            f"Error processing dish-material row: {e}")
                        self.results['errors'].append(
                            f"Dish-material extraction error: {e}")
                        continue

                conn.commit()

                self.log_result('dish_materials', dish_material_count,
                                "Processed dish-material relationships")
                return True

        except Exception as e:
            logger.error(f"Failed to extract dish-material relationships: {e}")
            self.results['errors'].append(
                f"Dish-material extraction failed: {e}")
            return False

    def generate_analysis_report(self, target_date: str) -> bool:
        """Generate both material and beverage variance analysis reports."""
        logger.info(
            f"REPORT: Generating variance analysis reports for {target_date}")

        material_success = self.generate_material_report(target_date)
        beverage_success = self.generate_beverage_report(target_date)

        # Return True if at least one report was successful
        return material_success or beverage_success

    def generate_material_report(self, target_date: str) -> bool:
        """Generate material variance analysis report with NEW structure."""
        logger.info(
            f"MATERIAL REPORT: Generating material variance analysis report for {target_date}")

        try:
            # Use the updated monthly report generation instead of the old logic
            import subprocess
            import sys

            # Call the updated monthly material report generation script with proper module path
            cmd = [
                sys.executable,
                "-m", "scripts.generate_monthly_material_report",
                "--date", target_date
            ]

            # Set up environment to include current directory in Python path
            import os
            env = os.environ.copy()
            current_dir = str(Path.cwd())
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{current_dir};{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = current_dir

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path.cwd(), env=env)

            if result.returncode == 0:
                logger.info(
                    "SUCCESS: Monthly material report generation completed")
                # The generate_monthly_material_report.py script uses the new structure:
                # - System Record (material_monthly_usage.material_used)
                # - Inventory Count (inventory_count.counted_quantity)
                # - Theoretical Usage (sum of dish_sales * standard_quantity * loss_rate)
                # - Variance = System Record - Theoretical Usage
                self.log_result('monthly_material_report', 1,
                                "Generated monthly material report with new structure")
                return True
            else:
                logger.error(
                    f"ERROR: Monthly material report generation failed: {result.stderr}")
                self.results['errors'].append(
                    f"Monthly material report generation failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to generate material report: {e}")
            self.results['errors'].append(
                f"Material report generation failed: {e}")
            return False

    def generate_beverage_report(self, target_date: str) -> bool:
        """Generate beverage variance analysis report."""
        logger.info(
            f"BEVERAGE REPORT: Generating beverage variance analysis report for {target_date}")

        try:
            import subprocess
            import sys

            # Call the beverage report generation script
            cmd = [
                sys.executable,
                "-m", "scripts.generate_monthly_beverage_report",
                "--date", target_date
            ]

            # Set up environment to include current directory in Python path
            import os
            env = os.environ.copy()
            current_dir = str(Path.cwd())
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{current_dir};{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = current_dir

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path.cwd(), env=env)

            if result.returncode == 0:
                logger.info(
                    "SUCCESS: Monthly beverage report generation completed")
                self.log_result('monthly_beverage_report', 1,
                                "Generated monthly beverage report with variance analysis")
                return True
            else:
                logger.error(
                    f"ERROR: Monthly beverage report generation failed: {result.stderr}")
                self.results['errors'].append(
                    f"Monthly beverage report generation failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to generate beverage report: {e}")
            self.results['errors'].append(
                f"Beverage report generation failed: {e}")
            return False

    def extract_material_monthly_usage(self, mb5b_folder: Path) -> bool:
        """Extract material monthly usage from MB5B file."""
        logger.info(f"MB5B: Extracting material monthly usage from MB5B files")

        try:
            import subprocess
            import sys

            # Look for MB5B files
            mb5b_files = list(mb5b_folder.glob("*.xls*")) + \
                list(mb5b_folder.glob("*.XLS*"))
            if not mb5b_files:
                logger.error("No MB5B file found for material monthly usage")
                return False

            mb5b_file = mb5b_files[0]
            logger.info(f"Processing MB5B file: {mb5b_file.name}")

            # Run the dedicated material monthly usage extraction script
            cmd = [
                sys.executable,
                "scripts/extract_material_monthly_usage.py",
                str(mb5b_file),
                "--direct-db"
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path.cwd())

            if result.returncode == 0:
                logger.info(
                    "SUCCESS: Material monthly usage extraction completed")
                # Try to parse output for count (if available)
                self.log_result('material_monthly_usage_mb5b',
                                1, "Processed MB5B file")
                return True
            else:
                logger.error(
                    f"ERROR: Material monthly usage extraction failed: {result.stderr}")
                self.results['errors'].append(
                    f"MB5B extraction failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to extract material monthly usage: {e}")
            self.results['errors'].append(f"MB5B extraction error: {e}")
            return False

    def process_all(self, target_date: str = None, inventory_count_date: str = None) -> bool:
        """Process all monthly data files."""
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')

        # Store target_date for use in extraction methods
        self.target_date = target_date

        # Store inventory_count_date for use in inventory extraction
        self.inventory_count_date = inventory_count_date or target_date

        logger.info(
            f"STARTING: Complete monthly automation for {target_date}")
        logger.info(
            f"INVENTORY: Using inventory count date: {self.inventory_count_date}")

        success = True

        # Step 1: Extract from monthly dish sales
        dish_sale_folder = self.input_folder / "monthly_dish_sale"
        dish_files = list(dish_sale_folder.glob("*.xlsx")) + \
            list(dish_sale_folder.glob("*.XLSX"))
        if dish_files:
            success &= self.extract_dish_types_and_dishes(dish_files[0])
        else:
            logger.error("No monthly dish sale file found")
            success = False

        # Step 2: Extract material master data (materials, types) from first available store
        material_folder = self.input_folder / "material_detail"
        success &= self.extract_material_master_data(material_folder)

        # Step 3: Extract material prices from all stores (now that materials exist)
        success &= self.extract_material_detail_batch(material_folder)

        # Step 4: Extract from inventory checking results (System Record + Inventory Count)
        # This now handles both: 库存数量 → System Record, 盘点数量 → Inventory Count
        inventory_folder = self.input_folder / "inventory_checking_result"
        if inventory_folder.exists():
            success &= self.extract_inventory_data(inventory_folder)
        else:
            logger.error("No inventory checking result folder found")
            success = False

        # Step 5: Extract dish-material relationships
        calc_folder = self.input_folder / "calculated_dish_material_usage"
        calc_files = list(calc_folder.glob("*.xls*")) + \
            list(calc_folder.glob("*.XLS*"))
        if calc_files:
            success &= self.extract_dish_materials(calc_files[0])
        else:
            logger.error("No calculated dish material usage file found")
            success = False

        # Step 6: Generate analysis reports (both material and beverage)
        if success:
            success &= self.generate_analysis_report(target_date)

        # Print results summary
        self.print_results_summary()

        return success

    def print_results_summary(self):
        """Print processing results summary."""
        logger.info("="*60)
        logger.info("INFO: MONTHLY AUTOMATION RESULTS SUMMARY")
        logger.info("="*60)

        logger.info(f"SUCCESS: Dish types: {self.results['dish_types']}")
        logger.info(
            f"SUCCESS: Dish child types: {self.results['dish_child_types']}")
        logger.info(f"SUCCESS: Dishes: {self.results['dishes']}")
        logger.info(
            f"SUCCESS: Material types: {self.results['material_types']}")
        logger.info(
            f"SUCCESS: Material child types: {self.results['material_child_types']}")
        logger.info(f"SUCCESS: Materials: {self.results['materials']}")
        logger.info(
            f"SUCCESS: Dish price history: {self.results['dish_price_history']}")
        logger.info(
            f"SUCCESS: Material price history: {self.results['material_price_history']}")
        logger.info(
            f"SUCCESS: Dish monthly sales: {self.results['dish_monthly_sales']}")
        logger.info(
            f"SUCCESS: Inventory processing (System Record + Inventory Count): {self.results['inventory_counts']}")
        logger.info(
            f"SUCCESS: Dish-material relationships: {self.results['dish_materials']}")

        # Report generation results
        material_report_count = self.results.get('monthly_material_report', 0)
        beverage_report_count = self.results.get('monthly_beverage_report', 0)
        logger.info(
            f"SUCCESS: Material variance report: {'✅ Generated' if material_report_count > 0 else '❌ Failed'}")
        logger.info(
            f"SUCCESS: Beverage variance report: {'✅ Generated' if beverage_report_count > 0 else '❌ Failed'}")

        if self.results['errors']:
            logger.warning(
                f"WARNING: Errors encountered: {len(self.results['errors'])}")
            for error in self.results['errors'][:5]:  # Show first 5 errors
                logger.warning(f"   - {error}")

        logger.info("="*60)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Complete Monthly Automation - New Workflow')
    parser.add_argument('--test', action='store_true',
                        help='Use test database')
    parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD)',
                        default=datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--inventory-count-date', type=str,
                        help='Inventory count date (YYYY-MM-DD). If not specified, uses target date.')

    args = parser.parse_args()
    processor = MonthlyAutomationProcessor(is_test=args.test)
    success = processor.process_all(args.date, args.inventory_count_date)

    if success:
        logger.info(
            "SUCCESS: Complete monthly automation finished successfully!")
        sys.exit(0)
    else:
        logger.error("ERROR: Complete monthly automation finished with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
