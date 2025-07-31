#!/usr/bin/env python3
"""
Generate comprehensive database report (main wrapper).
Orchestrates all worksheet generation using centralized data provider.
"""

from lib.business_insight_worksheet import BusinessInsightWorksheetGenerator
from lib.time_segment_worksheet import TimeSegmentWorksheetGenerator
from lib.yearly_comparison_worksheet import YearlyComparisonWorksheetGenerator
from lib.comparison_worksheet import ComparisonWorksheetGenerator
from lib.yearly_comparison_daily_worksheet import YearlyComparisonDailyWorksheetGenerator
from lib.monthly_dishes_worksheet import MonthlyDishesWorksheetGenerator
from lib.daily_store_tracking_worksheet import DailyStoreTrackingGenerator
from lib.weekly_store_tracking_worksheet import WeeklyStoreTrackingGenerator
from lib.database_queries import ReportDataProvider
from utils.database import DatabaseConfig, DatabaseManager
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openpyxl import Workbook

# Add parent directory to path for imports - must be before other imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now import our modules

# Load environment variables
load_dotenv()


class DatabaseReportGenerator:
    """Main report generator wrapper - orchestrates all worksheets"""

    def __init__(self, target_date: str, is_test: bool = False):
        self.target_date = target_date
        self.is_test = is_test
        self.config = DatabaseConfig(is_test=is_test)
        self.db_manager = DatabaseManager(self.config)
        self.output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
        self.output_dir.mkdir(exist_ok=True)

        # Store mapping
        self.store_names = {
            1: "加拿大一店", 2: "加拿大二店", 3: "加拿大三店", 4: "加拿大四店",
            5: "加拿大五店", 6: "加拿大六店", 7: "加拿大七店"
        }

        # Initialize data provider and worksheet generators
        self.data_provider = ReportDataProvider(self.db_manager)
        self.comparison_generator = ComparisonWorksheetGenerator(
            self.store_names, self.target_date)
        self.yearly_generator = YearlyComparisonWorksheetGenerator(
            self.store_names, self.target_date)
        self.yearly_daily_generator = YearlyComparisonDailyWorksheetGenerator(
            self.store_names, self.target_date)
        self.time_segment_generator = TimeSegmentWorksheetGenerator(
            self.store_names, self.target_date, self.data_provider)
        self.business_insight_generator = BusinessInsightWorksheetGenerator(
            self.store_names, self.target_date)
        self.monthly_dishes_generator = MonthlyDishesWorksheetGenerator(
            self.store_names, self.target_date)
        self.daily_tracking_generator = DailyStoreTrackingGenerator(
            self.data_provider)
        self.weekly_tracking_generator = WeeklyStoreTrackingGenerator(
            self.data_provider)

    def generate_report(self):
        """Generate the complete report with all worksheets"""
        print(f"Generating report for {self.target_date}")

        # Get all required data in single optimized query
        processed_data = self.data_provider.get_all_processed_data(
            self.target_date)

        if not processed_data:
            print("ERROR: No data found")
            return None

        # Unpack processed data
        (daily_data, monthly_data, previous_month_data, current_mtd, prev_mtd,
         yearly_current, yearly_previous, daily_ranking, monthly_ranking,
         daily_ranking_values, monthly_ranking_values) = processed_data

        # Create Excel workbook
        wb = Workbook()
        # Remove default sheet
        if wb.active:
            wb.remove(wb.active)

        # Generate comparison worksheet (对比上月表)
        comparison_ws = self.comparison_generator.generate_worksheet(
            wb, daily_data, monthly_data, previous_month_data,
            # Use monthly_data as targets (contains target_revenue)
            monthly_data,
            current_mtd, prev_mtd,
            daily_ranking, monthly_ranking, daily_ranking_values, monthly_ranking_values
        )

        # Generate yearly comparison worksheet (同比数据)
        yearly_ws = self.yearly_generator.generate_worksheet(
            wb, yearly_current, yearly_previous
        )

        # Generate year-over-year daily comparison worksheet (对比上年表)
        # Note: Use daily_data and monthly_data as they contain the prev_yearly_* fields
        yearly_daily_ws = self.yearly_daily_generator.generate_worksheet(
            # daily_data contains prev_yearly_* fields
            wb, daily_data, monthly_data, daily_data,
            monthly_data,  # Use monthly_data as targets
            current_mtd, current_mtd,  # current_mtd contains prev_yearly_mtd_* fields
            daily_ranking, monthly_ranking, daily_ranking_values, monthly_ranking_values
        )

        # Generate time segment worksheet (分时段-上报)
        time_segment_ws = self.time_segment_generator.generate_worksheet(wb)

        # Generate business insight worksheet (营业透视)
        business_insight_ws = self.business_insight_generator.generate_worksheet(
            wb, daily_data, monthly_data, previous_month_data,
            monthly_data,  # Use monthly_data as targets
            current_mtd, prev_mtd,
            daily_ranking, monthly_ranking, daily_ranking_values, monthly_ranking_values
        )

        # Generate daily store tracking worksheet (门店日-加拿大)
        daily_tracking_ws = self.daily_tracking_generator.generate_worksheet(
            wb, self.target_date
        )

        # Generate weekly store tracking worksheet (门店周-加拿大)
        weekly_tracking_ws = self.weekly_tracking_generator.generate_worksheet(
            wb, self.target_date
        )

        if not wb.worksheets:
            print("ERROR: No worksheets generated")
            return None

        # Save the report
        output_path = self.save_report(wb)
        if output_path:
            return output_path
        else:
            print("ERROR: Failed to save report")
            return None

    def save_report(self, wb):
        """Save the Excel workbook to file"""
        try:
            filename = f"database_report_{self.target_date.replace('-', '_')}.xlsx"
            output_path = self.output_dir / filename
            wb.save(output_path)
            return output_path
        except Exception as e:
            print(f"ERROR: Error saving report: {e}")
            return None


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate comprehensive database report")
    parser.add_argument("--date", default="2025-06-10",
                        help="Target date (YYYY-MM-DD)")
    parser.add_argument("--test", action="store_true",
                        help="Use test database")

    args = parser.parse_args()

    try:
        generator = DatabaseReportGenerator(args.date, is_test=args.test)
        output_path = generator.generate_report()

        if output_path:
            print("Finished")
        else:
            print("ERROR: Failed to generate report")
            sys.exit(1)

    except Exception as e:
        import traceback
        print(f"ERROR: Failed to generate report - {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
