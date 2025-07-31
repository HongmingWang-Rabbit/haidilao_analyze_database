#!/usr/bin/env python3
"""
Fix All Multiplication to Division in Materials Use Calculations

This script systematically finds and fixes all instances where materials_use 
calculations are using multiplication by unit_conversion_rate instead of division.

Based on user's example:
- WRONG: 午餐肉(半): 517 * 0.1 * 1 * 0.34 = 17.578
- RIGHT: 午餐肉(半): 517 * 0.1 * 1 / 0.34 = 152.0588
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiplicationToNivisionFixer:
    """Find and fix all multiplication to division in materials_use calculations"""
    
    def __init__(self):
        self.root_dir = Path('.')
        self.files_to_check = []
        self.files_modified = []
        self.patterns_found = []
    
    def find_python_files_with_calculations(self):
        """Find all Python files that might contain materials_use calculations"""
        
        logger.info("Scanning for Python files with potential materials_use calculations...")
        
        # Patterns that indicate materials_use calculations
        search_patterns = [
            r'materials_use.*\*.*conversion',
            r'sale.*\*.*standard.*\*.*loss.*\*.*conversion',
            r'standard_quantity.*\*.*loss_rate.*\*.*unit_conversion_rate',
            r'conversion_rate\)', # Files ending calculations with conversion_rate
            r'物料单位.*\*', # Files with material unit multiplication
            r'sale.*分量.*损耗.*单位', # Files with dish-material calculations
        ]
        
        python_files = list(self.root_dir.glob('**/*.py'))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if file contains potential calculation patterns
                for pattern in search_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.files_to_check.append(file_path)
                        logger.info(f"Found potential calculation file: {file_path}")
                        break
                        
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
                continue
        
        logger.info(f"Found {len(self.files_to_check)} files to check for multiplication issues")
    
    def analyze_file_for_multiplication_patterns(self, file_path: Path):
        """Analyze a file for multiplication patterns that should be division"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Patterns to find and fix
            multiplication_patterns = [
                # Pattern 1: Direct multiplication in SQL or Python
                {
                    'pattern': r'(\w+\s*\*\s*\w+\s*\*\s*\w+)\s*\*\s*(unit_conversion_rate|conversion_rate)',
                    'replacement': r'\1 / \2',
                    'description': 'sale * standard * loss / conversion_rate -> sale * standard * loss / conversion_rate'
                },
                
                # Pattern 2: More complex SQL patterns
                {
                    'pattern': r'(COALESCE\([^)]+\)\s*\*\s*COALESCE\([^)]+\)\s*\*\s*COALESCE\([^)]+\))\s*\*\s*COALESCE\(([^)]*unit_conversion_rate[^)]*)\)',
                    'replacement': r'\1 / COALESCE(\2)',
                    'description': 'COALESCE patterns with multiplication'
                },
                
                # Pattern 3: Variable assignments
                {
                    'pattern': r'materials_use\s*=\s*([^*]+\*[^*]+\*[^*]+)\s*\*\s*(unit_conversion_rate|conversion_rate)',
                    'replacement': r'materials_use = \1 / \2',
                    'description': 'materials_use = ... * conversion_rate'
                },
                
                # Pattern 4: Chinese patterns (物料单位)
                {
                    'pattern': r'(\w+\s*\*\s*[^*]+\s*\*\s*[^*]+)\s*\*\s / 物料单位',
                    'replacement': r'\1 / 物料单位',
                    'description': 'Chinese material unit multiplication'
                }
            ]
            
            changes_made = False
            modified_lines = lines.copy()
            
            for line_num, line in enumerate(lines):
                for pattern_info in multiplication_patterns:
                    pattern = pattern_info['pattern']
                    replacement = pattern_info['replacement']
                    
                    if re.search(pattern, line):
                        old_line = line
                        new_line = re.sub(pattern, replacement, line)
                        
                        if old_line != new_line:
                            modified_lines[line_num] = new_line
                            changes_made = True
                            
                            self.patterns_found.append({
                                'file': file_path,
                                'line_num': line_num + 1,
                                'old': old_line.strip(),
                                'new': new_line.strip(),
                                'description': pattern_info['description']
                            })
                            
                            logger.info(f"Found multiplication pattern in {file_path}:{line_num + 1}")
                            logger.info(f"  OLD: {old_line.strip()}")
                            logger.info(f"  NEW: {new_line.strip()}")
            
            return modified_lines if changes_made else None
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return None
    
    def fix_file(self, file_path: Path, modified_content: list):
        """Apply the fixes to a file"""
        
        try:
            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(modified_content))
            
            self.files_modified.append(file_path)
            logger.info(f"✅ Fixed multiplication patterns in: {file_path}")
            logger.info(f"   Backup created at: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error fixing {file_path}: {e}")
            return False
    
    def run_systematic_fix(self):
        """Run systematic fix of all multiplication to division issues"""
        
        logger.info("="*80)
        logger.info("SYSTEMATIC MULTIPLICATION TO DIVISION FIX")
        logger.info("="*80)
        
        # Step 1: Find files to check
        self.find_python_files_with_calculations()
        
        if not self.files_to_check:
            logger.info("No files found with potential calculation patterns")
            return
        
        # Step 2: Analyze and fix each file
        for file_path in self.files_to_check:
            logger.info(f"\nAnalyzing: {file_path}")
            
            modified_content = self.analyze_file_for_multiplication_patterns(file_path)
            
            if modified_content:
                # Ask for confirmation (in real implementation, could add --auto flag)
                logger.info(f"Found multiplication patterns in {file_path}")
                self.fix_file(file_path, modified_content)
            else:
                logger.info(f"No multiplication patterns found in {file_path}")
        
        # Step 3: Summary
        logger.info("\n" + "="*80)
        logger.info("FIX SUMMARY")
        logger.info("="*80)
        logger.info(f"Files checked: {len(self.files_to_check)}")
        logger.info(f"Files modified: {len(self.files_modified)}")
        logger.info(f"Patterns fixed: {len(self.patterns_found)}")
        
        if self.files_modified:
            logger.info("\nModified files:")
            for file_path in self.files_modified:
                logger.info(f"  - {file_path}")
        
        if self.patterns_found:
            logger.info(f"\nPattern fixes applied:")
            for pattern in self.patterns_found:
                logger.info(f"  {pattern['file']}:{pattern['line_num']}")
                logger.info(f"    Description: {pattern['description']}")
                logger.info(f"    Old: {pattern['old']}")
                logger.info(f"    New: {pattern['new']}")
                logger.info()
        
        # Step 4: Recommendations
        if self.files_modified:
            logger.info("NEXT STEPS:")
            logger.info("1. Test the modified files to ensure calculations are correct")
            logger.info("2. Run your materials_use generation script to verify division is working")
            logger.info("3. Check that lunch meat calculation now shows:")
            logger.info("   午餐肉(半): 517 * 0.1 * 1 / 0.34 = 152.0588 (instead of 17.578)")
            logger.info("4. If satisfied with results, you can delete the .backup files")
        
        return len(self.files_modified) > 0


def main():
    """Main function"""
    
    fixer = MultiplicationToNivisionFixer()
    
    try:
        success = fixer.run_systematic_fix()
        
        if success:
            print("✅ SUCCESS: Multiplication to division fixes applied!")
            print("Please test the lunch meat calculation to verify it now uses division.")
            sys.exit(0)
        else:
            print("ℹ️ INFO: No multiplication patterns found to fix.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Error during systematic fix: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()