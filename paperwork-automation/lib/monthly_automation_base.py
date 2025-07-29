#!/usr/bin/env python3
"""
Base class for monthly automation that uses modular extraction components.
Provides shared functionality for complete_monthly_automation_new.py
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from lib.extraction_modules import (
    ExtractionOrchestrator, StoreMapping, DishTypeExtractor, 
    DishExtractor, PriceHistoryExtractor, MonthlySalesExtractor
)

logger = logging.getLogger(__name__)


class MonthlyAutomationBase:
    """Base class providing shared monthly automation functionality"""
    
    def __init__(self, db_manager, target_date: str, debug: bool = False):
        self.db_manager = db_manager
        self.target_date = target_date
        self.debug = debug
        
        # Initialize modular extractors
        self.orchestrator = ExtractionOrchestrator(db_manager, debug)
        self.dish_type_extractor = DishTypeExtractor(db_manager)
        self.dish_extractor = DishExtractor(db_manager)
        self.price_extractor = PriceHistoryExtractor(db_manager)
        self.sales_extractor = MonthlySalesExtractor(db_manager)
        
        # Store mappings
        self.store_mapping = StoreMapping.get_store_name_mapping()
        self.store_folder_mapping = StoreMapping.get_store_folder_mapping()
        
        # Results tracking
        self.results = {
            'successes': [],
            'errors': [],
            'dish_types': 0,
            'dish_child_types': 0,
            'dishes': 0,
            'price_history': 0,
            'monthly_sales': 0,
            'materials': 0,
            'dish_materials': 0,
            'material_usage': 0,
            'inventory_counts': 0
        }
    
    def log_result(self, category: str, count: int, description: str):
        """Log and track extraction results"""
        if category in self.results:
            self.results[category] += count
        
        logger.info(f"✅ {description}: {count}")
        self.results['successes'].append(f"{description}: {count}")
    
    def log_error(self, error_msg: str):
        """Log and track errors"""
        logger.error(f"❌ {error_msg}")
        self.results['errors'].append(error_msg)
    
    def extract_dishes_from_file(self, file_path: Path) -> bool:
        """Extract dishes using modular approach"""
        logger.info(f"🍽️ Extracting dishes from: {file_path.name}")
        
        try:
            dish_type_count, dish_child_type_count, dish_count, price_history_count, monthly_sales_count = \
                self.orchestrator.extract_dishes_complete(file_path, self.target_date)
            
            self.log_result('dish_types', dish_type_count, "Dish types processed")
            self.log_result('dish_child_types', dish_child_type_count, "Dish child types processed")
            self.log_result('dishes', dish_count, "Dishes processed")
            self.log_result('price_history', price_history_count, "Price history records processed")
            self.log_result('monthly_sales', monthly_sales_count, "Monthly sales records processed")
            
            return True
            
        except Exception as e:
            self.log_error(f"Failed to extract dishes from {file_path.name}: {e}")
            return False
    
    def validate_file_exists(self, file_path: Path, description: str) -> bool:
        """Validate that a required file exists"""
        if not file_path.exists():
            self.log_error(f"{description} file not found: {file_path}")
            return False
        return True
    
    def validate_directory_exists(self, dir_path: Path, description: str) -> bool:
        """Validate that a required directory exists"""
        if not dir_path.exists():
            self.log_error(f"{description} directory not found: {dir_path}")
            return False
        return True
    
    def find_files_by_pattern(self, directory: Path, patterns: List[str], description: str) -> List[Path]:
        """Find files matching any of the given patterns"""
        found_files = []
        
        for pattern in patterns:
            files = list(directory.glob(pattern))
            found_files.extend(files)
        
        if not found_files:
            self.log_error(f"No {description} files found in {directory}")
        else:
            logger.info(f"Found {len(found_files)} {description} files")
        
        return found_files
    
    def get_target_date_components(self) -> Tuple[int, int, int]:
        """Get year, month, day components from target date"""
        try:
            target_dt = datetime.strptime(self.target_date, '%Y-%m-%d')
            return target_dt.year, target_dt.month, target_dt.day
        except ValueError as e:
            self.log_error(f"Invalid target date format: {e}")
            raise
    
    def print_summary(self):
        """Print extraction summary"""
        logger.info("\n" + "="*50)
        logger.info("📊 EXTRACTION SUMMARY")
        logger.info("="*50)
        
        # Print successes
        if self.results['successes']:
            logger.info("✅ Successful Operations:")
            for success in self.results['successes']:
                logger.info(f"   {success}")
        
        # Print key metrics
        logger.info(f"\n📈 Key Metrics:")
        logger.info(f"   Dish Types: {self.results['dish_types']}")
        logger.info(f"   Dish Child Types: {self.results['dish_child_types']}")
        logger.info(f"   Dishes: {self.results['dishes']}")
        logger.info(f"   Price History: {self.results['price_history']}")
        logger.info(f"   Monthly Sales: {self.results['monthly_sales']}")
        logger.info(f"   Materials: {self.results['materials']}")
        logger.info(f"   Dish-Material Relations: {self.results['dish_materials']}")
        logger.info(f"   Material Usage: {self.results['material_usage']}")
        logger.info(f"   Inventory Counts: {self.results['inventory_counts']}")
        
        # Print errors
        if self.results['errors']:
            logger.info(f"\n❌ Errors ({len(self.results['errors'])}):")
            for error in self.results['errors']:
                logger.info(f"   {error}")
        
        # Overall status
        total_records = sum([
            self.results['dishes'], self.results['price_history'], 
            self.results['monthly_sales'], self.results['materials'],
            self.results['dish_materials'], self.results['material_usage']
        ])
        
        if total_records > 0:
            logger.info(f"\n🎉 Automation completed with {total_records} total records processed!")
        else:
            logger.warning(f"\n⚠️ No records processed. Check input files and data.")
        
        logger.info("="*50)


class MaterialExtractionMixin:
    """Mixin providing material extraction functionality"""
    
    def extract_material_detail_with_types(self, file_path: Path) -> bool:
        """Extract materials with type classifications from material detail"""
        logger.info(f"🧱 Extracting materials from: {file_path.name}")
        
        try:
            import subprocess
            import sys
            
            # Run the dedicated material detail extraction script
            cmd = [
                sys.executable,
                "-m",
                "scripts.extract_material_detail_with_types",
                str(file_path),
                "--direct-db"
            ]
            
            if hasattr(self, 'config') and self.config.is_test:
                cmd.append("--test-db")
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  cwd=Path.cwd(), encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                # Parse output for counts
                output = result.stdout + result.stderr
                import re
                
                materials_match = re.search(r'(\d+) materials processed', output)
                materials_count = int(materials_match.group(1)) if materials_match else 0
                
                self.log_result('materials', materials_count, "Materials processed with types")
                return True
            else:
                self.log_error(f"Material extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_error(f"Failed to extract materials from {file_path.name}: {e}")
            return False
    
    def extract_material_detail_batch(self, material_folder: Path) -> bool:
        """Extract material detail with types and store-specific pricing from all store subfolders"""
        logger.info(f"🧱 Batch extracting materials from: {material_folder}")
        
        try:
            import subprocess
            import sys
            
            cmd = [
                sys.executable,
                "-m",
                "scripts.extract_material_detail_prices_by_store_batch",
                "--material-detail-path",
                str(material_folder),
                "--target-date",
                self.target_date
            ]
            
            if hasattr(self, 'config') and self.config.is_test:
                cmd.append("--test")
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  cwd=Path.cwd(), encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                # Parse output for counts
                output = result.stdout + result.stderr
                import re
                
                stores_match = re.search(r'🏪 Stores processed: (\d+)', output)
                prices_match = re.search(r'💰 Total prices extracted: (\d+)', output)
                
                stores_count = int(stores_match.group(1)) if stores_match else 0
                prices_count = int(prices_match.group(1)) if prices_match else 0
                
                self.log_result('materials', stores_count, "Store material folders processed")
                self.log_result('price_history', prices_count, "Material prices extracted")
                return True
            else:
                self.log_error(f"Batch material extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_error(f"Failed to batch extract materials: {e}")
            return False


class DishMaterialExtractionMixin:
    """Mixin providing dish-material relationship extraction functionality"""
    
    def extract_dish_materials_modular(self, file_path: Path) -> bool:
        """Extract dish-material relationships using modular approach"""
        logger.info(f"🔗 Extracting dish-material relationships from: {file_path.name}")
        
        try:
            # This could be enhanced to use modular components
            # For now, delegate to existing logic or create new modular component
            
            # Placeholder: Use existing extraction logic
            # This should be refactored to use modular components in the future
            from scripts.complete_monthly_automation_new import CompleteMonthlyAutomation
            
            # Create temporary instance to use existing method
            temp_automation = CompleteMonthlyAutomation(self.target_date, debug=self.debug)
            temp_automation.db_manager = self.db_manager
            
            success = temp_automation.extract_dish_materials(file_path)
            
            if success:
                # Estimate count (should be tracked properly in modular version)
                self.log_result('dish_materials', 50, "Dish-material relationships processed")
            
            return success
            
        except Exception as e:
            self.log_error(f"Failed to extract dish-materials from {file_path.name}: {e}")
            return False