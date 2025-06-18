#!/usr/bin/env python3
"""
Generate comprehensive database report (main wrapper).
Orchestrates all worksheet generation using centralized data provider.
"""

import os
import sys
from pathlib import Path
from openpyxl import Workbook
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.database import DatabaseConfig, DatabaseManager
from lib.database_queries import ReportDataProvider
from lib.comparison_worksheet import ComparisonWorksheetGenerator
from lib.yearly_comparison_worksheet import YearlyComparisonWorksheetGenerator
from lib.time_segment_worksheet import TimeSegmentWorksheetGenerator

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
        self.comparison_generator = ComparisonWorksheetGenerator(self.store_names, self.target_date)
        self.yearly_generator = YearlyComparisonWorksheetGenerator(self.store_names, self.target_date)
        self.time_segment_generator = TimeSegmentWorksheetGenerator(self.store_names, self.target_date)
    
    def generate_report(self):
        """Generate the complete report with all worksheets"""
        print(f"🔄 Generating comprehensive database report for {self.target_date}...")
        
        # Get all required data in single optimized query
        processed_data = self.data_provider.get_all_processed_data(self.target_date)
        
        if not processed_data:
            print("❌ No data found")
            return None
        
        # Unpack processed data
        (daily_data, monthly_data, previous_month_data, current_mtd, prev_mtd, 
         yearly_current, yearly_previous, daily_ranking, monthly_ranking, 
         daily_ranking_values, monthly_ranking_values) = processed_data
        
        print(f"✅ Data ready for {len(daily_data)} stores")
        
        # Create Excel workbook
        wb = Workbook()
        # Remove default sheet
        if wb.active:
            wb.remove(wb.active)
        
        # Generate comparison worksheet (对比上月表)
        print("📊 Generating comparison worksheet...")
        comparison_ws = self.comparison_generator.generate_worksheet(
            wb, daily_data, monthly_data, previous_month_data, 
            monthly_data,  # Use monthly_data as targets (contains target_revenue)
            current_mtd, prev_mtd, 
            daily_ranking, monthly_ranking, daily_ranking_values, monthly_ranking_values
        )
        
        # Generate yearly comparison worksheet (同比数据)
        print("📈 Generating yearly comparison worksheet...")
        yearly_ws = self.yearly_generator.generate_worksheet(
            wb, yearly_current, yearly_previous
        )
        
        # Generate time segment worksheet (分时段-上报)
        print("⏰ Generating time segment worksheet...")
        time_segment_ws = self.time_segment_generator.generate_worksheet(wb)
        
        if not wb.worksheets:
            print("❌ No worksheets generated")
            return None
        
        # Save the report
        output_path = self.save_report(wb)
        if output_path:
            print(f"✅ Comprehensive report generated successfully!")
            print(f"📁 Saved to: {output_path}")
            print(f"📊 Generated {len(wb.worksheets)} worksheets")
            print(f"🚀 Single optimized database query for all data")
            return output_path
        else:
            print("❌ Failed to save report")
            return None
    
    def save_report(self, wb):
        """Save the Excel workbook to file"""
        try:
            filename = f"database_report_{self.target_date.replace('-', '_')}.xlsx"
            output_path = self.output_dir / filename
            wb.save(output_path)
            return output_path
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate comprehensive database report")
    parser.add_argument("--date", default="2025-06-10", help="Target date (YYYY-MM-DD)")
    parser.add_argument("--test", action="store_true", help="Use test database")
    
    args = parser.parse_args()
    
    try:
        generator = DatabaseReportGenerator(args.date, is_test=args.test)
        output_path = generator.generate_report()
        
        if output_path:
            print(f"\n🎯 Success! Database report created: {output_path}")
            print(f"📁 Located in OUTPUT_DIR: {os.getenv('OUTPUT_DIR', './output')}")
            print(f"📊 Clean architecture: wrapper + lib modules")
            print(f"🚀 Optimized: single DB query + multiple worksheets")
        else:
            print("\n❌ Failed to generate report")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 