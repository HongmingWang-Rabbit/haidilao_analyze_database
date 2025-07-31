#!/usr/bin/env python3
"""Process Hi-Bowl daily reports"""

import os
import sys
import argparse
from datetime import datetime
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from lib.hi_bowl_daily_processor import HiBowlDailyProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Process Hi-Bowl daily reports')
    parser.add_argument('--input-file', type=str, help='Input Excel file path')
    parser.add_argument('--output-file', type=str, help='Output Excel file path')
    parser.add_argument('--target-month', type=str, help='Target month in YYYYMM format')
    parser.add_argument('--test', action='store_true', help='Run test with sample file')
    
    args = parser.parse_args()
    
    processor = HiBowlDailyProcessor()
    
    if args.test:
        # Test with the sample file
        input_file = os.path.join(
            project_root, 'Input', 'daily_report', 'hi-bowl-report',
            'daily-data', 'HaiDiLao-report-2025-7 (1).xlsx'
        )
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(
            project_root, 'output', 'hi-bowl',
            f'hi_bowl_report_{timestamp}.xlsx'
        )
        
        target_month = '202507'  # July 2025
        
        logger.info(f"Running test with:")
        logger.info(f"  Input: {input_file}")
        logger.info(f"  Output: {output_file}")
        logger.info(f"  Month: {target_month}")
        
    else:
        if not args.input_file or not args.output_file:
            parser.error("--input-file and --output-file are required when not using --test")
            
        input_file = args.input_file
        output_file = args.output_file
        target_month = args.target_month
        
    # Process the file
    success = processor.process_daily_file(input_file, output_file, target_month)
    
    if success:
        logger.info("Processing completed successfully")
        logger.info(f"Output saved to: {output_file}")
        return 0
    else:
        logger.error("Processing failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
