"""
Library modules for Haidilao data analysis and report generation.
"""

# Data extraction functions
from .data_extraction import (
    extract_daily_reports,
    extract_time_segments,
    transform_daily_report_data,
    transform_time_segment_data
)

# Report generation functions
from .comparison_worksheet import ComparisonWorksheetGenerator
from .yearly_comparison_worksheet import YearlyComparisonWorksheetGenerator
from .time_segment_worksheet import TimeSegmentWorksheetGenerator
from .business_insight_worksheet import BusinessInsightWorksheetGenerator
from .database_queries import ReportDataProvider 