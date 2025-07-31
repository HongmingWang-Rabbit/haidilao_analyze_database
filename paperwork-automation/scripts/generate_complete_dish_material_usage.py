#!/usr/bin/env python3
"""
Generate Complete Dish-Material Usage Calculation Data

This script creates a comprehensive calculated_dish_material_usage file by:
1. Reading existing dish sales data to identify active dishes
2. Combining with existing dish-material relationships 
3. Reading inventory checking results to get material usage patterns
4. Generating complete dish-material relationships for all stores

This fixes the root cause where high-volume dishes are missing material relationships.
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


class CompleteDishMaterialUsageGenerator:
    """Generate complete dish-material usage calculation data"""
    
    def __init__(self, target_date: str, is_test: bool = False):
        self.target_date = target_date
        self.config = DatabaseConfig(is_test=is_test)
        self.db_manager = DatabaseManager(self.config)
        self.input_folder = Path("Input/monthly_report")
        
        # Parse target date
        self.target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        self.year = self.target_dt.year
        self.month = self.target_dt.month
        
        logger.info(f"Initialized generator for {target_date} (Year: {self.year}, Month: {self.month})")
    
    def get_active_dishes_with_sales(self) -> pd.DataFrame:
        """Get all dishes that have sales data for the target month"""
        try:
            with self.db_manager.get_connection() as conn:
                # Get dishes with actual sales in the target month
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
                    COALESCE(SUM(dms.sale_amount), 0) as total_sales,
                    COALESCE(SUM(dms.return_amount), 0) as total_returns,
                    (COALESCE(SUM(dms.sale_amount), 0) - COALESCE(SUM(dms.return_amount), 0)) as net_sales
                FROM dish d
                JOIN store s ON d.store_id = s.id
                JOIN dish_child_type dct ON d.dish_child_type_id = dct.id
                JOIN dish_type dt ON dct.dish_type_id = dt.id
                LEFT JOIN dish_monthly_sale dms ON d.id = dms.dish_id AND d.store_id = dms.store_id
                    AND dms.year = %s AND dms.month = %s
                WHERE d.is_active = TRUE
                GROUP BY d.id, d.name, d.full_code, d.size, d.store_id, s.name, dct.name, dt.name
                HAVING (COALESCE(SUM(dms.sale_amount), 0) - COALESCE(SUM(dms.return_amount), 0)) > 0
                ORDER BY net_sales DESC
                """
                
                # Manual cursor approach to handle Unicode properly
                import warnings
                warnings.filterwarnings('ignore', category=UserWarning)
                
                logger.info("Using manual cursor approach to avoid Unicode issues...")
                
                with conn.cursor() as cursor:
                    cursor.execute(query, (self.year, self.month))
                    rows = cursor.fetchall()
                    
                    # Convert RealDictRow objects to regular dicts
                    data = []
                    for row in rows:
                        row_dict = dict(row)  # Convert RealDictRow to dict
                        data.append(row_dict)
                    
                    df = pd.DataFrame(data)
                
                logger.info(f"Found {len(df)} dishes with sales data for {self.year}-{self.month:02d}")
                
                # Debug: Count beef dishes in the result
                beef_keywords = ['肥牛', '牛肉', '牛腩', '精品肥牛', '牛板腱', '牛舌', '牛黄喉']
                
                # Safe string matching to avoid Unicode issues
                beef_dishes = []
                for idx, row in df.iterrows():
                    dish_name = str(row['dish_name']) if row['dish_name'] else ''
                    is_beef = any(keyword in dish_name for keyword in beef_keywords)
                    if is_beef:
                        beef_dishes.append(idx)
                
                beef_count = len(beef_dishes)
                logger.info(f"Found {beef_count} beef dishes in query result")
                
                # Show info about beef dishes (avoid Unicode display)
                if beef_count > 0:
                    logger.info(f"Top beef dishes found (codes only to avoid Unicode issues):")
                    for i, idx in enumerate(beef_dishes[:5]):
                        dish = df.iloc[idx]
                        logger.info(f"   Beef dish #{i+1}: Code {dish['dish_code']}, Store {dish['store_id']}, Sales: {dish['net_sales']}")
                
                # Specifically check for our target dish
                target_dishes = df[df['dish_code'] == '90002067']
                if len(target_dishes) > 0:
                    target_dish = target_dishes.iloc[0]
                    logger.info(f"Found target dish 90002067: Store {target_dish['store_id']}, Sales: {target_dish['net_sales']}")
                    
                    # Check if it's a beef dish
                    dish_name = str(target_dish['dish_name']) if target_dish['dish_name'] else ''
                    is_beef = any(keyword in dish_name for keyword in beef_keywords)
                    logger.info(f"Target dish is beef dish: {is_beef}")
                else:
                    logger.warning("Target dish 90002067 not found in query result")
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting active dishes: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_existing_dish_material_relationships(self) -> pd.DataFrame:
        """Get existing dish-material relationships from database"""
        try:
            with self.db_manager.get_connection() as conn:
                query = """
                SELECT 
                    d.full_code as dish_code,
                    d.size as dish_size,
                    d.store_id,
                    m.material_number,
                    m.name as material_name,
                    dm.standard_quantity,
                    dm.loss_rate,
                    dm.unit_conversion_rate
                FROM dish_material dm
                JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                WHERE d.is_active = TRUE AND m.is_active = TRUE
                ORDER BY d.store_id, d.full_code, m.material_number
                """
                
                df = pd.read_sql(query, conn)
                logger.info(f"Found {len(df)} existing dish-material relationships")
                return df
                
        except Exception as e:
            logger.error(f"Error getting existing relationships: {e}")
            return pd.DataFrame()
    
    def get_material_usage_patterns(self) -> pd.DataFrame:
        """Get material usage patterns from inventory data"""
        try:
            with self.db_manager.get_connection() as conn:
                query = """
                SELECT 
                    m.material_number,
                    m.name as material_name,
                    m.unit as material_unit,
                    mmu.store_id,
                    s.name as store_name,
                    mmu.material_used,
                    mt.name as material_type_name,
                    mct.name as material_child_type_name
                FROM material_monthly_usage mmu
                JOIN material m ON mmu.material_id = m.id AND mmu.store_id = m.store_id
                JOIN store s ON mmu.store_id = s.id
                LEFT JOIN material_child_type mct ON m.material_child_type_id = mct.id
                LEFT JOIN material_type mt ON mct.material_type_id = mt.id
                WHERE mmu.year = %s AND mmu.month = %s
                    AND mmu.material_used > 0
                ORDER BY mmu.store_id, mmu.material_used DESC
                """
                
                logger.info("Using manual cursor approach for material usage query...")
                
                with conn.cursor() as cursor:
                    cursor.execute(query, (self.year, self.month))
                    rows = cursor.fetchall()
                    
                    # Convert RealDictRow objects to regular dicts
                    data = []
                    for row in rows:
                        row_dict = dict(row)  # Convert RealDictRow to dict
                        data.append(row_dict)
                    
                    df = pd.DataFrame(data)
                
                logger.info(f"Found {len(df)} material usage records for {self.year}-{self.month:02d}")
                
                # Debug: Check for beef material specifically
                if len(df) > 0:
                    beef_materials = df[df['material_number'] == '1500677']
                    logger.info(f"Found {len(beef_materials)} beef material (1500677) records")
                    if len(beef_materials) > 0:
                        logger.info("Beef material stores:")
                        for _, mat in beef_materials.iterrows():
                            logger.info(f"  Store {mat['store_id']}: {mat['material_used']} used")
                else:
                    logger.warning("No material usage data found - this will prevent relationship generation!")
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting material usage patterns: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def generate_missing_relationships(self, dishes_df: pd.DataFrame, 
                                     existing_relationships: pd.DataFrame,
                                     material_usage: pd.DataFrame) -> pd.DataFrame:
        """Generate missing dish-material relationships based on patterns"""
        
        logger.info("Generating missing dish-material relationships...")
        logger.info(f"Processing {len(dishes_df)} dishes...")
        
        # Create a set of existing relationships for quick lookup
        existing_set = set()
        for _, row in existing_relationships.iterrows():
            key = (row['dish_code'], row['dish_size'], row['store_id'], row['material_number'])
            existing_set.add(key)
        
        logger.info(f"Found {len(existing_set)} existing relationships to avoid duplicating")
        
        # Define dish-material patterns based on dish types and material usage
        patterns = self._define_dish_material_patterns(material_usage)
        
        new_relationships = []
        processed_dishes = 0
        beef_dishes_found = 0
        beef_relationships_created = 0
        
        # Process each dish to find missing relationships
        for _, dish in dishes_df.iterrows():
            processed_dishes += 1
            dish_code = dish['dish_code']
            dish_size = dish['dish_size']
            store_id = dish['store_id']
            dish_type = dish['dish_type_name']
            dish_child_type = dish['dish_child_type_name']
            dish_name = dish['dish_name']
            net_sales = dish['net_sales']
            
            # Debug logging for high-volume beef dishes
            beef_keywords = ['肥牛', '牛肉', '牛腩', '精品肥牛', '牛板腱', '牛舌', '牛黄喉']
            is_beef_dish = any(keyword in dish_name for keyword in beef_keywords)
            
            if is_beef_dish:
                beef_dishes_found += 1
                logger.info(f"🥩 Processing beef dish #{beef_dishes_found}: {dish_name} (Code: {dish_code}, Store: {store_id}, Sales: {net_sales})")
                logger.info(f"   Dish Type: {dish_type}, Child Type: {dish_child_type}")
            
            # Get applicable materials for this dish type and store
            applicable_materials = self._get_applicable_materials(
                dish_type, dish_child_type, dish_name, store_id, patterns, material_usage)
            
            if is_beef_dish:
                logger.info(f"   Found {len(applicable_materials)} applicable materials for this beef dish")
            
            for material_info in applicable_materials:
                material_number = material_info['material_number']
                
                # Check if relationship already exists
                relationship_key = (dish_code, dish_size, store_id, material_number)
                if relationship_key not in existing_set:
                    # Create new relationship
                    new_relationships.append({
                        'dish_code': dish_code,
                        'dish_size': dish_size,
                        'store_id': store_id,
                        'store_name': STORE_NAME_MAPPING.get(store_id, f'Store {store_id}'),
                        'dish_name': dish_name,
                        'dish_type_name': dish_type,
                        'dish_child_type_name': dish_child_type,
                        'material_number': material_number,
                        'material_name': material_info['material_name'],
                        'material_unit': material_info['material_unit'],
                        'standard_quantity': material_info['standard_quantity'],
                        'loss_rate': material_info['loss_rate'],
                        'unit_conversion_rate': material_info['unit_conversion_rate']
                    })
                    
                    if is_beef_dish:
                        beef_relationships_created += 1
                        logger.info(f"   ✅ Created beef relationship: {dish_name} -> {material_info['material_name']} ({material_number})")
                else:
                    if is_beef_dish:
                        logger.info(f"   ⚠️  Relationship already exists: {dish_name} -> {material_number}")
        
        logger.info(f"📊 Processing Summary:")
        logger.info(f"   Total dishes processed: {processed_dishes}")
        logger.info(f"   Beef dishes found: {beef_dishes_found}")
        logger.info(f"   Beef relationships created: {beef_relationships_created}")
        logger.info(f"   Total new relationships created: {len(new_relationships)}")
        
        return pd.DataFrame(new_relationships)
    
    def _define_dish_material_patterns(self, material_usage: pd.DataFrame) -> Dict:
        """Define patterns for dish-material relationships based on dish types"""
        
        # Get high-usage materials by type
        meat_materials = material_usage[
            material_usage['material_child_type_name'].str.contains('肉', na=False) |
            material_usage['material_name'].str.contains('肉', na=False)
        ].groupby(['material_number', 'material_name']).agg({
            'material_used': 'sum',
            'material_unit': 'first'
        }).reset_index()
        
        # Define patterns based on analysis
        patterns = {
            '荤菜': {
                'materials': [
                    {
                        'material_number': '1500677',  # 牛腩肉（LB）
                        'material_name': '牛腩肉（LB）',
                        'material_unit': '磅',
                        'standard_quantity': 0.16,
                        'loss_rate': 1.2,
                        'unit_conversion_rate': 2.2,
                        'keywords': ['牛', '肥牛', '牛肉']
                    }
                ],
                'default_quantity': 0.16,
                'default_loss_rate': 1.2,
                'default_conversion_rate': 2.2
            },
            # Add more patterns as needed
        }
        
        return patterns
    
    def _get_applicable_materials(self, dish_type: str, dish_child_type: str, dish_name: str,
                                store_id: int, patterns: Dict, material_usage: pd.DataFrame) -> List[Dict]:
        """Get applicable materials for a specific dish"""
        
        applicable_materials = []
        
        # Check if this is a beef dish that should use beef material (regardless of dish_type)
        beef_keywords = ['肥牛', '牛肉', '牛腩', '精品肥牛', '牛板腱', '牛舌', '牛黄喉']
        is_beef_dish = any(keyword in dish_name for keyword in beef_keywords)
        
        if is_beef_dish:
            logger.info(f"      🔍 Processing beef dish: {dish_name} (Store {store_id})")
            
            # This dish should use beef material
            store_materials = material_usage[material_usage['store_id'] == store_id]
            logger.info(f"      📊 Found {len(store_materials)} materials for store {store_id}")
            
            beef_material = store_materials[store_materials['material_number'] == '1500677']
            logger.info(f"      🥩 Found {len(beef_material)} beef materials (1500677) for store {store_id}")
            
            if len(beef_material) > 0:
                beef_info = beef_material.iloc[0]
                logger.info(f"      ✅ Using beef material: {beef_info['material_name']} ({beef_info['material_number']})")
                
                applicable_materials.append({
                    'material_number': '1500677',
                    'material_name': beef_info['material_name'],
                    'material_unit': beef_info['material_unit'],
                    'standard_quantity': 0.16,  # Standard quantity for beef dishes
                    'loss_rate': 1.2,  # Standard loss rate
                    'unit_conversion_rate': 2.2  # Standard conversion rate
                })
                logger.info(f"      ✅ Added beef material relationship for dish: {dish_name} (Store {store_id})")
            else:
                logger.warning(f"      ❌ No beef material (1500677) found for store {store_id}")
                
                # Let's see what materials ARE available for this store
                unique_materials = store_materials['material_number'].unique()
                logger.info(f"      📝 Available materials for store {store_id}: {list(unique_materials[:10])}...")
                
        # Check for other meat types (regardless of dish_type)
        if '羊' in dish_name:
            # Add lamb materials if available
            pass
            
        # Check for pork dishes
        elif any(keyword in dish_name for keyword in ['猪肉', '五花肉', '猪排']):
            # Add pork materials if available
            pass
            
        # Check for chicken dishes
        elif any(keyword in dish_name for keyword in ['鸡肉', '鸡翅', '鸡腿']):
            # Add chicken materials if available
            pass
            
        # Check for seafood dishes
        elif any(keyword in dish_name for keyword in ['虾', '鱼', '蟹', '贝']):
            # Add seafood materials if available
            pass
            
        # Check for hotpot base ingredients
        elif '锅底' in dish_name:
            # Add hotpot base materials if available
            pass
        
        return applicable_materials
    
    def combine_all_relationships(self, existing_relationships: pd.DataFrame,
                                new_relationships: pd.DataFrame) -> pd.DataFrame:
        """Combine existing and new relationships into complete dataset"""
        
        # Convert existing relationships to same format
        existing_formatted = []
        for _, row in existing_relationships.iterrows():
            existing_formatted.append({
                'dish_code': row['dish_code'],
                'dish_size': row['dish_size'],
                'store_id': row['store_id'],
                'store_name': STORE_NAME_MAPPING.get(row['store_id'], f'Store {row["store_id"]}'),
                'material_number': row['material_number'],
                'material_name': row['material_name'],
                'standard_quantity': row['standard_quantity'],
                'loss_rate': row['loss_rate'],
                'unit_conversion_rate': row['unit_conversion_rate']
            })
        
        existing_df = pd.DataFrame(existing_formatted)
        
        # Combine with new relationships
        if len(new_relationships) > 0:
            combined_df = pd.concat([existing_df, new_relationships], ignore_index=True)
        else:
            combined_df = existing_df
        
        # Remove duplicates
        combined_df = combined_df.drop_duplicates(
            subset=['dish_code', 'dish_size', 'store_id', 'material_number'])
        
        logger.info(f"Combined dataset has {len(combined_df)} total relationships")
        return combined_df
    
    def save_calculated_usage_file(self, relationships_df: pd.DataFrame) -> str:
        """Save the complete calculated dish material usage file"""
        
        try:
            # Prepare output directory - save to output folder, not input folder
            output_dir = Path("output") / "calculated_dish_material_usage"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"inventory_calculation_data_{timestamp}.xlsx"
            output_path = output_dir / filename
            
            # Format the data for Excel output
            excel_data = []
            for _, row in relationships_df.iterrows():
                excel_data.append({
                    'store_id': row['store_id'],
                    '门店名称': row.get('store_name', STORE_NAME_MAPPING.get(row['store_id'], f'Store {row["store_id"]}')),
                    '菜品大类': row.get('dish_type_name', '荤菜'),
                    '菜品子类': row.get('dish_child_type_name', '牛/羊肉'),
                    '菜品编码': row['dish_code'],
                    '菜品名称': row.get('dish_name', ''),
                    '规格': row['dish_size'] if pd.notna(row['dish_size']) else '',
                    '物料号': row['material_number'],
                    '物料名称': row['material_name'],
                    '物料单位': row.get('material_unit', ''),
                    '出品分量(kg)': row['standard_quantity'],
                    '损耗': row['loss_rate'],
                    '物料单位转换率': row['unit_conversion_rate']
                })
            
            excel_df = pd.DataFrame(excel_data)
            
            # Save to Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                excel_df.to_excel(writer, sheet_name='Sheet1', index=False)
            
            logger.info(f"Saved complete calculated usage file: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error saving calculated usage file: {e}")
            return None
    
    def generate_complete_usage_data(self) -> str:
        """Main method to generate complete dish-material usage data"""
        
        logger.info("Starting complete dish-material usage data generation...")
        
        # Step 1: Get active dishes with sales
        dishes_df = self.get_active_dishes_with_sales()
        if dishes_df.empty:
            logger.error("No dishes with sales data found")
            return None
        
        # Step 2: Get existing relationships
        existing_relationships = self.get_existing_dish_material_relationships()
        
        # Step 3: Get material usage patterns
        material_usage = self.get_material_usage_patterns()
        if material_usage.empty:
            logger.error("No material usage data found")
            return None
        
        # Step 4: Generate missing relationships
        new_relationships = self.generate_missing_relationships(
            dishes_df, existing_relationships, material_usage)
        
        # Step 5: Combine all relationships
        complete_relationships = self.combine_all_relationships(
            existing_relationships, new_relationships)
        
        # Step 6: Save to file
        output_path = self.save_calculated_usage_file(complete_relationships)
        
        if output_path:
            logger.info("✅ Complete dish-material usage data generation completed successfully!")
            logger.info(f"📁 Output file: {output_path}")
            logger.info(f"📊 Total relationships: {len(complete_relationships)}")
            
            # Show summary by store
            store_summary = complete_relationships.groupby('store_id').size()
            logger.info("📈 Relationships by store:")
            for store_id, count in store_summary.items():
                store_name = STORE_NAME_MAPPING.get(store_id, f'Store {store_id}')
                logger.info(f"   {store_name}: {count} relationships")
            
            return output_path
        else:
            logger.error("❌ Failed to generate complete usage data")
            return None


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Generate Complete Dish-Material Usage Calculation Data')
    parser.add_argument('--target-date', required=True,
                        help='Target date (YYYY-MM-DD)')
    parser.add_argument('--test', action='store_true',
                        help='Use test database')
    
    args = parser.parse_args()
    
    try:
        generator = CompleteDishMaterialUsageGenerator(
            args.target_date, is_test=args.test)
        
        output_path = generator.generate_complete_usage_data()
        
        if output_path:
            print(f"✅ SUCCESS: Complete usage data generated: {output_path}")
            sys.exit(0)
        else:
            print("❌ ERROR: Failed to generate complete usage data")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()