#!/usr/bin/env python3
"""
Analyze Material Assignments

This script analyzes the current dish-material relationships to identify incorrect assignments
and suggests better material mappings based on dish names and material types.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import logging
from utils.database import DatabaseConfig, DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_material_assignments():
    """Analyze current dish-material assignments and identify problems"""
    
    config = DatabaseConfig(is_test=False)
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                
                logger.info("=== Material Assignment Analysis ===")
                
                # 1. Get all available materials for Store 1
                logger.info("\n1. Available Materials for Store 1")
                cursor.execute("""
                    SELECT 
                        m.material_number,
                        m.name as material_name,
                        mct.name as child_type,
                        mt.name as material_type,
                        mmu.material_used
                    FROM material m
                    LEFT JOIN material_child_type mct ON m.material_child_type_id = mct.id
                    LEFT JOIN material_type mt ON mct.material_type_id = mt.id
                    LEFT JOIN material_monthly_usage mmu ON m.id = mmu.material_id AND m.store_id = mmu.store_id
                        AND mmu.year = 2025 AND mmu.month = 5
                    WHERE m.store_id = 1 
                    AND m.is_active = TRUE
                    AND (m.name LIKE '%牛%' OR m.name LIKE '%肉%')
                    ORDER BY mmu.material_used DESC NULLS LAST, m.material_number;
                """)
                
                beef_materials = cursor.fetchall()
                logger.info(f"Found {len(beef_materials)} beef/meat materials:")
                for mat in beef_materials:
                    usage = mat['material_used'] or 0
                    logger.info(f"  {mat['material_number']}: {mat['material_name']} ({mat['child_type']}) - Used: {usage}")
                
                # 2. Analyze current dish-material relationships for beef dishes
                logger.info("\n2. Current Dish-Material Relationships (Beef Dishes)")
                cursor.execute("""
                    SELECT 
                        d.name as dish_name,
                        d.full_code as dish_code,
                        m.material_number,
                        m.name as material_name,
                        dm.standard_quantity,
                        dm.loss_rate,
                        dm.unit_conversion_rate,
                        -- Get actual sales for this dish
                        COALESCE(SUM(dms.sale_amount - dms.return_amount), 0) as total_sales
                    FROM dish_material dm
                    JOIN dish d ON dm.dish_id = d.id AND dm.store_id = d.store_id
                    JOIN material m ON dm.material_id = m.id AND dm.store_id = m.store_id
                    LEFT JOIN dish_monthly_sale dms ON d.id = dms.dish_id AND d.store_id = dms.store_id
                        AND dms.year = 2025 AND dms.month = 5
                    WHERE d.store_id = 1
                    AND (d.name LIKE '%牛%' OR d.name LIKE '%肉%')
                    GROUP BY d.name, d.full_code, m.material_number, m.name, dm.standard_quantity, dm.loss_rate, dm.unit_conversion_rate
                    ORDER BY total_sales DESC;
                """)
                
                current_relationships = cursor.fetchall()
                logger.info(f"Found {len(current_relationships)} current beef dish-material relationships:")
                
                # Group by material to see what dishes are assigned to each material
                from collections import defaultdict
                material_assignments = defaultdict(list)
                
                for rel in current_relationships:
                    material_assignments[rel['material_number']].append({
                        'dish_name': rel['dish_name'],
                        'dish_code': rel['dish_code'],
                        'total_sales': rel['total_sales']
                    })
                
                for material_num, dishes in material_assignments.items():
                    # Find material name
                    material_name = next((rel['material_name'] for rel in current_relationships if rel['material_number'] == material_num), 'Unknown')
                    total_dishes = len(dishes)
                    total_sales = sum(dish['total_sales'] for dish in dishes)
                    
                    logger.info(f"\n  Material {material_num} ({material_name}):")
                    logger.info(f"    Assigned to {total_dishes} dishes, Total sales: {total_sales}")
                    
                    # Show top dishes for this material
                    top_dishes = sorted(dishes, key=lambda x: x['total_sales'], reverse=True)[:5]
                    for dish in top_dishes:
                        logger.info(f"      {dish['dish_name']} ({dish['dish_code']}): {dish['total_sales']} sales")
                
                # 3. Identify potential misassignments
                logger.info("\n3. Potential Material Misassignments")
                
                # Check if specific dish types are using wrong materials
                problematic_assignments = []
                
                for rel in current_relationships:
                    dish_name = rel['dish_name']
                    material_name = rel['material_name']
                    
                    # Check for obvious mismatches
                    if '牛舌' in dish_name and '牛腩' in material_name:
                        problematic_assignments.append({
                            'dish': dish_name,
                            'material': material_name,
                            'issue': 'Beef tongue dish using beef brisket material'
                        })
                    elif '牛肉丸' in dish_name and '牛腩' in material_name:
                        problematic_assignments.append({
                            'dish': dish_name,
                            'material': material_name,
                            'issue': 'Beef ball dish using beef brisket material'
                        })
                    elif '西冷' in dish_name and '牛腩' in material_name:
                        problematic_assignments.append({
                            'dish': dish_name,
                            'material': material_name,
                            'issue': 'Sirloin dish using beef brisket material'
                        })
                    elif '牛板腱' in dish_name and '牛腩' in material_name:
                        problematic_assignments.append({
                            'dish': dish_name,
                            'material': material_name,
                            'issue': 'Chuck roll dish using beef brisket material'
                        })
                
                if problematic_assignments:
                    logger.info(f"Found {len(problematic_assignments)} potential misassignments:")
                    for prob in problematic_assignments:
                        logger.info(f"  ❗ {prob['issue']}")
                        logger.info(f"     Dish: {prob['dish']}")
                        logger.info(f"     Current Material: {prob['material']}")
                else:
                    logger.info("No obvious misassignments detected based on name matching")
                
                # 4. Suggest better material assignments
                logger.info("\n4. Suggested Material Assignments")
                
                # Create a mapping of dish name patterns to appropriate materials
                dish_material_suggestions = {}
                
                # Find specific materials for different beef types
                beef_material_map = {}
                for mat in beef_materials:
                    mat_name = mat['material_name'].lower()
                    mat_num = mat['material_number']
                    
                    if '牛舌' in mat_name:
                        beef_material_map['tongue'] = (mat_num, mat['material_name'])
                    elif '西冷' in mat_name or 'sirloin' in mat_name:
                        beef_material_map['sirloin'] = (mat_num, mat['material_name'])
                    elif '牛板腱' in mat_name:
                        beef_material_map['chuck'] = (mat_num, mat['material_name'])
                    elif '牛肉丸' in mat_name or '牛丸' in mat_name:
                        beef_material_map['ball'] = (mat_num, mat['material_name'])
                    elif '牛腩' in mat_name:
                        beef_material_map['brisket'] = (mat_num, mat['material_name'])
                
                logger.info("Available specific beef materials:")
                for beef_type, (mat_num, mat_name) in beef_material_map.items():
                    logger.info(f"  {beef_type}: {mat_num} - {mat_name}")
                
                # Suggest corrections for problematic assignments
                if problematic_assignments:
                    logger.info("\nSuggested corrections:")
                    for prob in problematic_assignments:
                        dish_name = prob['dish']
                        if '牛舌' in dish_name and 'tongue' in beef_material_map:
                            mat_num, mat_name = beef_material_map['tongue']
                            logger.info(f"  {dish_name} -> {mat_num} ({mat_name})")
                        elif '西冷' in dish_name and 'sirloin' in beef_material_map:
                            mat_num, mat_name = beef_material_map['sirloin']
                            logger.info(f"  {dish_name} -> {mat_num} ({mat_name})")
                        elif '牛板腱' in dish_name and 'chuck' in beef_material_map:
                            mat_num, mat_name = beef_material_map['chuck']
                            logger.info(f"  {dish_name} -> {mat_num} ({mat_name})")
                        elif '牛肉丸' in dish_name and 'ball' in beef_material_map:
                            mat_num, mat_name = beef_material_map['ball']
                            logger.info(f"  {dish_name} -> {mat_num} ({mat_name})")
                        else:
                            logger.info(f"  {dish_name} -> No specific material found, keep current assignment")
                
    except Exception as e:
        logger.error(f"Error analyzing material assignments: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = analyze_material_assignments()
    if success:
        print("Material assignment analysis completed!")
    else:
        print("Material assignment analysis failed!")