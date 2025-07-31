#!/usr/bin/env python3
"""
Generate Materials Use Calculation Files with Division by Unit Conversion Rate

This script generates detailed materials_use calculation files using division by 
unit_conversion_rate instead of multiplication, as requested by the user.

The calculation formula is:
materials_use = sale_amount * standard_quantity * loss_rate / unit_conversion_rate
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse
import logging

from utils.database import DatabaseConfig, DatabaseManager
from lib.config import STORE_NAME_MAPPING

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MaterialsUseCalculatorWithDivision:
    """Generate materials_use calculation files with division by unit_conversion_rate"""
    
    def __init__(self, target_date: str, is_test: bool = False):
        self.target_date = target_date
        self.config = DatabaseConfig(is_test=is_test)
        self.db_manager = DatabaseManager(self.config)
        
        # Parse target date
        self.target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        self.year = self.target_dt.year
        self.month = self.target_dt.month
        
        logger.info(f"Initialized calculator for {target_date} (Year: {self.year}, Month: {self.month})")
    
    def get_dish_sales_with_materials(self) -> pd.DataFrame:
        """Get dish sales data with their material relationships"""
        try:
            with self.db_manager.get_connection() as conn:
                query = """
                SELECT 
                    d.id as dish_id,
                    d.name as dish_name,
                    d.full_code as dish_code,
                    d.size as dish_size,
                    d.store_id,
                    s.name as store_name,
                    dct.name as dish_child_type_name,
                    dt.name as dish_type_name,
                    
                    -- Dish sales data (aggregate both sales modes)
                    COALESCE(SUM(dms.sale_amount), 0) as total_sale_amount,
                    COALESCE(SUM(dms.return_amount), 0) as total_return_amount,
                    (COALESCE(SUM(dms.sale_amount), 0) - COALESCE(SUM(dms.return_amount), 0)) as net_sales,
                    
                    -- Material information
                    m.material_number,
                    m.name as material_name,
                    m.unit as material_unit,
                    
                    -- Material usage parameters
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate
                    
                FROM dish d
                JOIN store s ON d.store_id = s.id
                JOIN dish_child_type dct ON d.dish_child_type_id = dct.id
                JOIN dish_type dt ON dct.dish_type_id = dt.id
                JOIN dish_material dm ON d.id = dm.dish_id AND d.store_id = dm.store_id
                JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                LEFT JOIN dish_monthly_sale dms ON d.id = dms.dish_id AND d.store_id = dms.store_id
                    AND dms.year = %s AND dms.month = %s
                    
                WHERE d.is_active = TRUE AND m.is_active = TRUE
                
                GROUP BY 
                    d.id, d.name, d.full_code, d.size, d.store_id, s.name, 
                    dct.name, dt.name, m.material_number, m.name, m.unit,
                    dm.standard_quantity, dm.loss_rate, dm.unit_conversion_rate
                    
                HAVING (COALESCE(SUM(dms.sale_amount), 0) - COALESCE(SUM(dms.return_amount), 0)) > 0
                
                ORDER BY d.store_id, net_sales DESC
                """
                
                logger.info("Querying dish sales with material relationships...")
                
                with conn.cursor() as cursor:
                    cursor.execute(query, (self.year, self.month))
                    rows = cursor.fetchall()
                    
                    # Convert to DataFrame
                    data = []
                    for row in rows:
                        row_dict = dict(row)
                        data.append(row_dict)
                    
                    df = pd.DataFrame(data)
                
                logger.info(f"Found {len(df)} dish-material combinations with sales data")
                return df
                
        except Exception as e:
            logger.error(f"Error getting dish sales with materials: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def calculate_materials_use_with_division(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate materials_use using DIVISION by unit_conversion_rate"""
        
        logger.info(f"Calculating materials_use for {len(df)} records using DIVISION...")
        
        calculation_data = []
        
        for _, row in df.iterrows():
            try:
                # Extract values
                store_id = row['store_id']
                store_name = row['store_name']
                dish_name = row['dish_name']
                dish_code = row['dish_code']
                dish_size = row['dish_size'] if pd.notna(row['dish_size']) else ''
                
                net_sales = float(row['net_sales'])
                standard_quantity = float(row['standard_quantity']) if pd.notna(row['standard_quantity']) else 0.0
                loss_rate = float(row['loss_rate']) if pd.notna(row['loss_rate']) else 1.0
                unit_conversion_rate = float(row['unit_conversion_rate']) if pd.notna(row['unit_conversion_rate']) else 1.0
                
                material_number = row['material_number']
                material_name = row['material_name']
                material_unit = row['material_unit'] if pd.notna(row['material_unit']) else ''
                
                # CRITICAL: Calculate materials_use using DIVISION by unit_conversion_rate
                if unit_conversion_rate != 0:
                    materials_use = net_sales * standard_quantity * loss_rate / unit_conversion_rate
                else:
                    materials_use = 0.0
                    logger.warning(f"Zero conversion rate for dish {dish_code}, material {material_number}")
                
                # Create calculation record
                calculation_data.append({
                    'store_id': store_id,
                    '门店名称': store_name,
                    '菜品大类': row['dish_type_name'],
                    '菜品子类': row['dish_child_type_name'],
                    '菜品编码': dish_code,
                    '菜品名称': dish_name,
                    '规格': dish_size,
                    'sale_amount': net_sales,
                    '出品分量(kg)': standard_quantity,
                    '损耗': loss_rate,
                    '物料单位': unit_conversion_rate,
                    '物料号': material_number,
                    '物料名称': material_name,
                    '单位': material_unit,
                    'materials_use': materials_use,
                    'calculation_method': 'division'  # Track the method used
                })
                
            except Exception as e:
                logger.error(f"Error calculating materials_use for row: {e}")
                continue
        
        result_df = pd.DataFrame(calculation_data)
        logger.info(f"Generated {len(result_df)} materials_use calculations using DIVISION")
        
        # Show some examples to verify the calculation
        if len(result_df) > 0:
            logger.info("Sample calculations (using DIVISION):")
            for i, row in result_df.head(3).iterrows():
                sale = row['sale_amount']
                std_qty = row['出品分量(kg)']
                loss = row['损耗']
                conv = row['物料单位']
                materials_use = row['materials_use']
                
                logger.info(f"  {row['菜品名称']}: {sale} * {std_qty} * {loss} / {conv} = {materials_use:.6f}")
        
        return result_df
    
    def save_materials_use_file(self, df: pd.DataFrame) -> str:
        """Save the materials_use calculation file"""
        
        try:
            # Prepare output directory
            output_dir = Path("output") / "materials_use_with_division"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"materials_use_division_{self.year}_{self.month:02d}_{timestamp}.xlsx"
            output_path = output_dir / filename
            
            # Sort by store and sales for better organization
            df_sorted = df.sort_values(['store_id', 'sale_amount'], ascending=[True, False])
            
            # Save to Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df_sorted.to_excel(writer, sheet_name='Materials_Use_Division', index=False)
            
            logger.info(f"Saved materials_use file with DIVISION: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error saving materials_use file: {e}")
            return None
    
    def generate_summary_report(self, df: pd.DataFrame) -> None:
        """Generate summary report of the calculations"""
        
        logger.info("="*80)
        logger.info("MATERIALS USE CALCULATION SUMMARY (DIVISION METHOD)")
        logger.info("="*80)
        
        # Total calculations
        total_records = len(df)
        logger.info(f"Total dish-material calculations: {total_records}")
        
        # By store summary
        if total_records > 0:
            store_summary = df.groupby(['store_id', '门店名称']).agg({
                'materials_use': ['count', 'sum'],
                'sale_amount': 'sum'
            }).round(4)
            
            logger.info("Summary by store:")
            for (store_id, store_name), row in store_summary.iterrows():
                count = row[('materials_use', 'count')]
                total_use = row[('materials_use', 'sum')]
                total_sales = row[('sale_amount', 'sum')]
                
                try:
                    logger.info(f"  {store_name}: {count} calculations, Total materials_use: {total_use:.4f}, Total sales: {total_sales:.2f}")
                except UnicodeEncodeError:
                    logger.info(f"  Store {store_id}: {count} calculations, Total materials_use: {total_use:.4f}, Total sales: {total_sales:.2f}")
            
            # Show calculation method verification
            logger.info(f"\nCalculation Method: materials_use = sale_amount * 出品分量(kg) * 损耗 / 物料单位")
            logger.info(f"All calculations use DIVISION by unit_conversion_rate")
            
            # Show some high-usage examples
            top_usage = df.nlargest(3, 'materials_use')
            logger.info(f"\nTop 3 materials_use calculations:")
            for _, row in top_usage.iterrows():
                try:
                    logger.info(f"  {row['菜品名称']}: {row['materials_use']:.6f} (Sale: {row['sale_amount']}, Conv: {row['物料单位']})")
                except UnicodeEncodeError:
                    logger.info(f"  Dish {row['菜品编码']}: {row['materials_use']:.6f} (Sale: {row['sale_amount']}, Conv: {row['物料单位']})")
        
        logger.info("="*80)
    
    def generate_materials_use_with_division(self) -> str:
        """Main method to generate materials_use calculations with division"""
        
        logger.info("Starting materials_use calculation with DIVISION method...")
        
        # Step 1: Get dish sales with material data
        sales_materials_df = self.get_dish_sales_with_materials()
        if sales_materials_df.empty:
            logger.error("No dish sales with material data found")
            return None
        
        # Step 2: Calculate materials_use using division
        calculations_df = self.calculate_materials_use_with_division(sales_materials_df)
        if calculations_df.empty:
            logger.error("No materials_use calculations generated")
            return None
        
        # Step 3: Save to file
        output_path = self.save_materials_use_file(calculations_df)
        if not output_path:
            logger.error("Failed to save materials_use file")
            return None
        
        # Step 4: Generate summary
        self.generate_summary_report(calculations_df)
        
        logger.info("✅ Materials_use calculation with DIVISION completed successfully!")
        logger.info(f"📁 Output file: {output_path}")
        
        return output_path


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Generate Materials Use Calculations with Division by Unit Conversion Rate')
    parser.add_argument('--target-date', required=True,
                        help='Target date (YYYY-MM-DD)')
    parser.add_argument('--test', action='store_true',
                        help='Use test database')
    
    args = parser.parse_args()
    
    try:
        calculator = MaterialsUseCalculatorWithDivision(
            args.target_date, is_test=args.test)
        
        output_path = calculator.generate_materials_use_with_division()
        
        if output_path:
            print(f"✅ SUCCESS: Materials_use calculations with DIVISION generated: {output_path}")
            sys.exit(0)
        else:
            print("❌ ERROR: Failed to generate materials_use calculations")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()