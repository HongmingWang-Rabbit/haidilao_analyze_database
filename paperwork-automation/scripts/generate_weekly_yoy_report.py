#!/usr/bin/env python3
"""
Generate MTD (Month-to-Date) Year-over-Year Comparison Report.

This script generates a MTD report that includes:
1. 周对比上年表 - MTD YoY comparison with challenge targets
   - 翻台率挑战: prev year, target, current, gap (colored)
   - 桌数挑战: prev year, target, current, gap (colored)
   - Tables calculated from: 翻台率 × 座位数 × 天数

Usage:
    python scripts/generate_weekly_yoy_report.py --target-date 2026-01-07
    python scripts/generate_weekly_yoy_report.py --target-date 2026-01-07 --output-dir ./reports
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
from openpyxl import Workbook

from lib.weekly_yoy_comparison_worksheet import WeeklyYoYComparisonWorksheetGenerator
from lib.database_queries import ReportDataProvider
from utils.database import DatabaseConfig, DatabaseManager

# Load environment variables
load_dotenv()


class WeeklyYoYReportGenerator:
    """Generate MTD YoY comparison report with challenge targets."""

    def __init__(self, target_date: str, is_test: bool = False, output_dir: str = None):
        """
        Initialize the report generator.

        Args:
            target_date: Target date in YYYY-MM-DD format (end of 7-day period)
            is_test: Whether to use test database
            output_dir: Output directory for reports
        """
        self.target_date = target_date
        self.is_test = is_test

        # Setup database connection
        self.config = DatabaseConfig(is_test=is_test)
        self.db_manager = DatabaseManager(self.config)

        # Setup output directory
        self.output_dir = Path(output_dir) if output_dir else Path(
            os.getenv('OUTPUT_DIR', './output'))
        self.output_dir.mkdir(exist_ok=True)

        # Initialize data provider
        self.data_provider = ReportDataProvider(self.db_manager)

        # Initialize worksheet generator
        self.weekly_yoy_generator = WeeklyYoYComparisonWorksheetGenerator(
            self.data_provider)

    def generate_report(self) -> str:
        """
        Generate the MTD YoY report.

        Returns:
            Path to the generated report file
        """
        print(f"Generating MTD YoY report for {self.target_date}")

        # Parse target date to calculate MTD range
        target_dt = datetime.strptime(self.target_date, '%Y-%m-%d')
        start_dt = target_dt.replace(day=1)

        print(f"MTD range: {start_dt.strftime('%Y-%m-%d')} to {self.target_date}")

        # Create Excel workbook
        wb = Workbook()
        # Remove default sheet
        if wb.active:
            wb.remove(wb.active)

        worksheets_generated = []

        # Generate MTD YoY Comparison worksheet
        print("Generating 周对比上年表 worksheet...")
        try:
            weekly_ws = self.weekly_yoy_generator.generate_worksheet(wb, self.target_date)
            if weekly_ws:
                worksheets_generated.append("周对比上年表")
                print("  ✅ 周对比上年表 worksheet generated")
        except Exception as e:
            print(f"  ❌ Error generating MTD YoY worksheet: {e}")

        # Generate detailed daily data worksheet
        print("Generating 每日详细数据 worksheet...")
        try:
            detail_ws = self.weekly_yoy_generator.generate_detail_worksheet(wb, self.target_date)
            if detail_ws:
                worksheets_generated.append("每日详细数据")
                print("  ✅ 每日详细数据 worksheet generated")
        except Exception as e:
            print(f"  ❌ Error generating detail worksheet: {e}")

        if not worksheets_generated:
            print("❌ No worksheets were generated")
            return None

        # Generate output filename
        output_filename = f"weekly_yoy_report_{self.target_date}.xlsx"
        output_path = self.output_dir / output_filename

        # Save workbook
        wb.save(output_path)
        print(f"\n✅ Report saved to: {output_path}")
        print(f"   Worksheets: {', '.join(worksheets_generated)}")

        return str(output_path)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Generate MTD YoY comparison report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/generate_weekly_yoy_report.py --target-date 2026-01-07
    python scripts/generate_weekly_yoy_report.py --target-date 2026-01-07 --output-dir ./reports
    python scripts/generate_weekly_yoy_report.py --target-date 2026-01-07 --test

The report includes:
  - 周对比上年表: MTD YoY comparison with challenge targets
    - 翻台率挑战: prev year, target (prev+0.16), current, gap (colored)
    - 桌数挑战: prev year, target, current, gap (colored)
    - Tables = 翻台率 × 座位数 × MTD天数
        """
    )

    parser.add_argument(
        "--target-date", "-d",
        required=True,
        help="Target date in YYYY-MM-DD format (MTD will be calculated from 1st of month)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Output directory for the report (default: ./output)"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Use test database instead of production"
    )

    args = parser.parse_args()

    # Validate date format
    try:
        datetime.strptime(args.target_date, '%Y-%m-%d')
    except ValueError:
        print(f"❌ Invalid date format: {args.target_date}")
        print("   Expected format: YYYY-MM-DD (e.g., 2026-01-07)")
        sys.exit(1)

    # Generate report
    try:
        generator = WeeklyYoYReportGenerator(
            target_date=args.target_date,
            is_test=args.test,
            output_dir=args.output_dir
        )
        output_path = generator.generate_report()

        if output_path:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
