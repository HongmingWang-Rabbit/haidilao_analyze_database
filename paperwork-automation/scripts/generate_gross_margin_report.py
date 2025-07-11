#!/usr/bin/env python3
"""
Generate Gross Margin Report (毛利报表)
Generates comprehensive gross margin analysis reports including:
- Detailed revenue data (菜品价格变动及菜品损耗表)
- Material cost analysis (原材料成本变动表)
- Discount analysis (打折优惠表)
"""

from lib.gross_margin_worksheet import GrossMarginWorksheetGenerator
from lib.store_gross_profit_worksheet import StoreGrossProfitWorksheetGenerator
from lib.database_queries import ReportDataProvider
from utils.database import DatabaseManager, DatabaseConfig
import argparse
import sys
import logging
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def generate_gross_margin_report(target_date: str, output_path: str = None):
    """
    Generate comprehensive gross margin report

    Args:
        target_date: Target date in YYYY-MM-DD format
        output_path: Optional custom output path
    """
    logger = logging.getLogger(__name__)

    logger.info(f"🍲 Starting gross margin report generation for {target_date}")

    try:
        # Parse target date for validation
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')

        # Initialize database connection
        db_config = DatabaseConfig()
        db_manager = DatabaseManager(db_config)
        data_provider = ReportDataProvider(db_manager)

        # Create workbook
        wb = Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # Initialize worksheet generator
        worksheet_generator = GrossMarginWorksheetGenerator(target_date)

        # Generate detailed revenue data worksheet
        logger.info("📊 Generating detailed revenue data worksheet...")
        try:
            dish_price_data = data_provider.get_gross_margin_dish_price_data(
                target_date)
            logger.info(
                f"✅ Retrieved {len(dish_price_data)} dish price records")

            worksheet_generator.generate_detailed_revenue_worksheet(
                wb, dish_price_data)
            logger.info(
                "✅ Detailed revenue data worksheet generated successfully")

        except Exception as e:
            logger.error(
                f"❌ Error generating detailed revenue data worksheet: {e}")
            # Continue with other worksheets

        # Generate material cost analysis worksheet
        logger.info("📊 Generating material cost analysis worksheet...")
        try:
            material_cost_data = data_provider.get_gross_margin_material_cost_data(
                target_date)
            logger.info(
                f"✅ Retrieved {len(material_cost_data)} material cost records")

            worksheet_generator.generate_material_cost_worksheet(
                wb, material_cost_data)
            logger.info(
                "✅ Material cost analysis worksheet generated successfully")

        except Exception as e:
            logger.error(
                f"❌ Error generating material cost analysis worksheet: {e}")
            # Continue with other worksheets

        # Generate discount analysis worksheet
        logger.info("📊 Generating discount analysis worksheet...")
        try:
            discount_data = data_provider.get_gross_margin_discount_data(
                target_date)
            logger.info(f"✅ Retrieved {len(discount_data)} discount records")

            worksheet_generator.generate_discount_analysis_worksheet(
                wb, discount_data)
            logger.info("✅ Discount analysis worksheet generated successfully")

        except Exception as e:
            logger.error(
                f"❌ Error generating discount analysis worksheet: {e}")
            # Continue with other worksheets

        # Generate store gross profit worksheet
        logger.info("📊 Generating store gross profit worksheet...")
        try:
            store_gross_profit_generator = StoreGrossProfitWorksheetGenerator(
                data_provider)
            store_gross_profit_generator.generate_worksheet(wb, target_date)
            logger.info(
                "✅ Store gross profit worksheet generated successfully")

        except Exception as e:
            logger.error(
                f"❌ Error generating store gross profit worksheet: {e}")
            # Continue with saving

        # Determine output filename
        if output_path:
            output_file = Path(output_path)
        else:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / \
                f"gross_margin_report_{target_date.replace('-', '_')}.xlsx"

        # Save workbook
        wb.save(output_file)
        logger.info(f"✅ Gross margin report saved to: {output_file}")

        # Report summary
        logger.info("📋 Report generation completed successfully!")
        logger.info(f"📊 Generated worksheets:")
        logger.info(f"   - 菜品价格变动及菜品损耗表 (Detailed Revenue Data)")
        logger.info(f"   - 原材料成本变动表 (Material Cost Analysis)")
        logger.info(f"   - 打折优惠表 (Discount Analysis)")
        logger.info(f"   - 各店毛利率分析 (Store Gross Profit Analysis)")

        return True

    except Exception as e:
        logger.error(f"❌ Error generating gross margin report: {e}")
        return False


def main():
    """Main function to handle command line arguments and generate report"""
    parser = argparse.ArgumentParser(
        description='Generate Gross Margin Report (毛利报表)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python generate_gross_margin_report.py --target-date 2025-06-30
  python generate_gross_margin_report.py --target-date 2025-06-30 --output report.xlsx
        '''
    )

    parser.add_argument(
        '--target-date',
        type=str,
        required=True,
        help='Target date in YYYY-MM-DD format'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (optional)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate target date format
    try:
        datetime.strptime(args.target_date, '%Y-%m-%d')
    except ValueError:
        print("❌ Error: Invalid date format. Please use YYYY-MM-DD")
        sys.exit(1)

    # Generate report
    success = generate_gross_margin_report(args.target_date, args.output)

    if success:
        print(f"✅ Gross margin report generated successfully!")
        sys.exit(0)
    else:
        print(f"❌ Failed to generate gross margin report")
        sys.exit(1)


if __name__ == "__main__":
    main()
