#!/usr/bin/env python3
"""
MTD (Month-to-Date) Year-over-Year Comparison Worksheet Generator

This module generates a MTD YoY comparison worksheet (周对比上年表) that includes:

1. Main Challenge Section:
   - 翻台率挑战: Previous year, target (prev + improvement), current, gap
   - 桌数挑战: Derived from turnover rate × seating capacity × days

2. Time Segment Challenge Section:
   - Slow time segments (afternoon, late night): Hardcoded daily targets
   - Busy time segments (morning, evening): Leftover targets distributed proportionally

All configuration values are sourced from configs/challenge_targets/.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# Import centralized configurations
from configs.store_config import STORE_SEATING_CAPACITY, STORE_MANAGERS, REGIONAL_MANAGER
from configs.challenge_targets import (
    get_store_turnover_target,
    is_store_excluded_from_regional,
    STORE_TARGET_CONFIG,
    DEFAULT_TURNOVER_IMPROVEMENT,
    DEFAULT_SLOW_TIME_TARGET,
    AFTERNOON_SLOW_TARGETS,
    LATE_NIGHT_TARGETS,
    TIME_SEGMENT_LABELS,
    TIME_SEGMENT_CONFIG
)


class WeeklyYoYComparisonWorksheetGenerator:
    """Generator for MTD year-over-year comparison worksheet."""

    # Excel styling constants
    HEADER_COLOR = "DC2626"
    GREEN_COLOR = "E6FFE6"
    RED_COLOR = "FFE6E6"
    SUMMARY_COLOR = "FFF3CD"
    EXCLUDED_COLOR = "E0E0E0"

    def __init__(self, data_provider):
        """
        Initialize the generator with data provider.

        Args:
            data_provider: ReportDataProvider instance for database access
        """
        self.data_provider = data_provider
        self.logger = logging.getLogger(__name__)

        # Standard styling
        self.header_fill = PatternFill(
            start_color=self.HEADER_COLOR, end_color=self.HEADER_COLOR, fill_type="solid")
        self.header_font = Font(bold=True, color="FFFFFF")
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        self.center_alignment = Alignment(horizontal="center", vertical="center")

        # Color fills for gap columns
        self.green_fill = PatternFill(start_color=self.GREEN_COLOR, end_color=self.GREEN_COLOR, fill_type="solid")
        self.red_fill = PatternFill(start_color=self.RED_COLOR, end_color=self.RED_COLOR, fill_type="solid")
        self.summary_fill = PatternFill(start_color=self.SUMMARY_COLOR, end_color=self.SUMMARY_COLOR, fill_type="solid")
        self.excluded_fill = PatternFill(start_color=self.EXCLUDED_COLOR, end_color=self.EXCLUDED_COLOR, fill_type="solid")

    @staticmethod
    def _format_date_period(start_dt: datetime, end_dt: datetime) -> str:
        """
        Format date range as Chinese date period string.

        Args:
            start_dt: Start date
            end_dt: End date

        Returns:
            Formatted string like '26年1月1日-1月7日'
        """
        year = end_dt.year % 100
        return f"{year}年{start_dt.month}月{start_dt.day}日-{end_dt.month}月{end_dt.day}日"

    def generate_worksheet(self, workbook: Workbook, target_date: str) -> Worksheet:
        """
        Generate MTD YoY comparison worksheet.

        Args:
            workbook: Excel workbook to add worksheet to
            target_date: Target date in YYYY-MM-DD format

        Returns:
            The generated worksheet
        """
        try:
            self.logger.info(
                f"Generating MTD YoY comparison worksheet for {target_date}")

            # Create worksheet
            ws = workbook.create_sheet("周对比上年表")

            # Parse target date and calculate MTD date ranges
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            # MTD: from first day of month to target date
            start_dt = target_dt.replace(day=1)
            num_days = target_dt.day  # Number of days in MTD period

            # Calculate previous year dates (same MTD period)
            prev_year_start, prev_year_end = self._calculate_prev_year_dates(
                start_dt, target_dt)

            self.logger.info(
                f"Current MTD period: {start_dt.strftime('%Y-%m-%d')} to {target_dt.strftime('%Y-%m-%d')} ({num_days} days)")
            self.logger.info(
                f"Previous year MTD period: {prev_year_start.strftime('%Y-%m-%d')} to {prev_year_end.strftime('%Y-%m-%d')}")

            # Get MTD store performance data
            store_data = self._get_mtd_data(start_dt, target_dt)

            # Generate headers
            self._generate_headers(ws, start_dt, target_dt, prev_year_start, prev_year_end)

            # Add store data rows
            self._add_store_data(ws, store_data, start_row=3, num_days=num_days)

            # Add regional summary (excluding Store 8)
            summary_row = 3 + len(store_data)
            self._add_regional_summary(ws, store_data, row=summary_row, num_days=num_days)

            # Apply formatting to main section
            self._apply_formatting(ws, len(store_data))

            # Add time segment challenge section below main section
            time_segment_start_row = summary_row + 1
            self._add_time_segment_challenge_section(
                ws, target_date, store_data, time_segment_start_row, num_days
            )

            self.logger.info(
                f"MTD YoY comparison worksheet generated with {len(store_data)} stores")

            return ws

        except Exception as e:
            self.logger.error(
                f"Error generating MTD YoY comparison worksheet: {str(e)}")
            raise

    def _calculate_prev_year_dates(self, current_start: datetime,
                                    current_end: datetime) -> tuple:
        """
        Calculate previous year week with same calendar dates.

        Args:
            current_start: Start date of current week
            current_end: End date of current week

        Returns:
            Tuple of (prev_year_start, prev_year_end)
        """
        prev_year = current_end.year - 1

        # Use same calendar dates in previous year
        # Handle leap year dates (Feb 29 -> Feb 28 in non-leap year)
        try:
            prev_year_end = current_end.replace(year=prev_year)
        except ValueError:
            # Feb 29 in leap year -> Feb 28 in non-leap year
            prev_year_end = current_end.replace(year=prev_year, day=28)

        try:
            prev_year_start = current_start.replace(year=prev_year)
        except ValueError:
            # Feb 29 in leap year -> Feb 28 in non-leap year
            prev_year_start = current_start.replace(year=prev_year, day=28)

        return prev_year_start, prev_year_end

    def _get_mtd_data(self, start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """
        Get MTD (month-to-date) store performance data from database.

        Args:
            start_dt: Start date of MTD period (first of month)
            end_dt: End date of MTD period (target date)

        Returns:
            List of store performance data dictionaries
        """
        try:
            # Reuse the weekly performance query - it works for any date range
            store_data = self.data_provider.get_weekly_store_performance(
                start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'))

            if not store_data:
                self.logger.warning("No MTD store performance data found")
                return []

            self.logger.info(f"Retrieved MTD data for {len(store_data)} stores")
            return store_data

        except Exception as e:
            self.logger.error(f"Error getting MTD data: {str(e)}")
            return []

    def _generate_headers(self, ws: Worksheet, start_dt: datetime, end_dt: datetime,
                          prev_start_dt: datetime, prev_end_dt: datetime) -> None:
        """Generate worksheet headers with date ranges."""
        # Format date strings using helper method
        current_period = self._format_date_period(start_dt, end_dt)
        prev_period = self._format_date_period(prev_start_dt, prev_end_dt)

        # Row 1 - Main headers
        headers_row1 = [
            "门店名称",      # A - Store Name
            "翻台率挑战",    # B - Turnover Rate challenge section
            "", "", "",      # C, D, E - Empty for merged cells
            "桌数挑战",      # F - Tables challenge section
            "", "", "",      # G, H, I - Empty for merged cells
            "备注"          # J - Notes
        ]

        for col, header in enumerate(headers_row1, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border

        # Merge header cells
        ws.merge_cells('B1:E1')  # 翻台率挑战
        ws.merge_cells('F1:I1')  # 桌数挑战

        # Row 2 - Sub headers
        sub_headers = [
            "",              # A - Empty (under Store Name)
            prev_period,     # B - Previous year turnover
            "目标",          # C - Target turnover
            current_period,  # D - Current period turnover
            "差距",          # E - Gap
            prev_period,     # F - Previous year tables
            "目标",          # G - Target tables
            current_period,  # H - Current period tables
            "差距",          # I - Gap
            ""               # J - Notes
        ]

        for col, header in enumerate(sub_headers, 1):
            cell = ws.cell(row=2, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border

    def _add_store_data(self, ws: Worksheet, store_data: List[Dict[str, Any]],
                        start_row: int, num_days: int) -> None:
        """Add individual store data rows with challenge targets."""
        for i, store in enumerate(store_data):
            row = start_row + i
            store_id = store.get('store_id', 0)

            # Get target configuration
            config = STORE_TARGET_CONFIG.get(store_id, {})

            # Store name
            ws.cell(row=row, column=1, value=store['store_name'])

            # === Turnover Rate Section ===
            prev_turnover = float(store.get('prev_avg_turnover_rate', 0))
            current_turnover = float(store.get('current_avg_turnover_rate', 0))
            target_turnover = get_store_turnover_target(store_id, prev_turnover)
            turnover_gap = current_turnover - target_turnover

            # B - Previous year turnover
            ws.cell(row=row, column=2, value=prev_turnover)
            # C - Target turnover
            ws.cell(row=row, column=3, value=target_turnover)
            # D - Current turnover
            ws.cell(row=row, column=4, value=current_turnover)
            # E - Gap (with color)
            gap_cell = ws.cell(row=row, column=5, value=turnover_gap)
            gap_cell.fill = self.green_fill if turnover_gap >= 0 else self.red_fill

            # === Tables Section ===
            # Calculate tables from turnover rate × seating capacity × days
            seating_capacity = STORE_SEATING_CAPACITY.get(store_id, 50)
            prev_tables = int(prev_turnover * seating_capacity * num_days)
            current_tables = int(current_turnover * seating_capacity * num_days)
            # Target tables derived from target turnover rate
            target_tables = int(target_turnover * seating_capacity * num_days)

            # F - Previous year tables
            ws.cell(row=row, column=6, value=prev_tables)

            # Check if store 8 (excluded from tables target)
            if not is_store_excluded_from_regional(store_id):
                tables_gap = current_tables - target_tables

                # G - Target tables
                ws.cell(row=row, column=7, value=target_tables)
                # H - Current tables
                ws.cell(row=row, column=8, value=current_tables)
                # I - Gap (with color)
                tables_gap_cell = ws.cell(row=row, column=9, value=tables_gap)
                tables_gap_cell.fill = self.green_fill if tables_gap >= 0 else self.red_fill
            else:
                # Store 8 - no tables target
                ws.cell(row=row, column=7, value="N/A")
                ws.cell(row=row, column=8, value=current_tables)
                na_cell = ws.cell(row=row, column=9, value="N/A")
                na_cell.fill = self.excluded_fill

            # J - Notes
            notes = config.get('notes', '标准考核目标')
            exemption = config.get('exemption_reason', '')
            if exemption:
                notes = f"{notes} ({exemption})" if notes else exemption
            ws.cell(row=row, column=10, value=notes)

    def _add_regional_summary(self, ws: Worksheet, store_data: List[Dict[str, Any]],
                               row: int, num_days: int) -> None:
        """
        Add regional summary row.
        Excludes Store 8 from regional YoY calculations.
        """
        # Filter out Store 8 for regional calculations
        regional_stores = [s for s in store_data if s.get('store_id') != 8]

        if not regional_stores:
            return

        # Store name
        ws.cell(row=row, column=1, value="区域汇总(不含8店)")

        # Calculate weighted average turnover (by seating capacity)
        total_seats = sum(
            STORE_SEATING_CAPACITY.get(s['store_id'], 50) for s in regional_stores)

        current_weighted_turnover = sum(
            float(s.get('current_avg_turnover_rate', 0)) *
            STORE_SEATING_CAPACITY.get(s['store_id'], 50)
            for s in regional_stores
        ) / total_seats if total_seats > 0 else 0

        prev_weighted_turnover = sum(
            float(s.get('prev_avg_turnover_rate', 0)) *
            STORE_SEATING_CAPACITY.get(s['store_id'], 50)
            for s in regional_stores
        ) / total_seats if total_seats > 0 else 0

        # Regional target = prev + 0.16 (the standard improvement)
        target_weighted_turnover = prev_weighted_turnover + DEFAULT_TURNOVER_IMPROVEMENT
        turnover_gap = current_weighted_turnover - target_weighted_turnover

        # B - Previous year turnover
        ws.cell(row=row, column=2, value=prev_weighted_turnover)
        # C - Target turnover
        ws.cell(row=row, column=3, value=target_weighted_turnover)
        # D - Current turnover
        ws.cell(row=row, column=4, value=current_weighted_turnover)
        # E - Gap (with color)
        gap_cell = ws.cell(row=row, column=5, value=turnover_gap)
        gap_cell.fill = self.green_fill if turnover_gap >= 0 else self.red_fill

        # Calculate tables from turnover rate × seating capacity × days
        prev_tables = sum(
            int(float(s.get('prev_avg_turnover_rate', 0)) *
                STORE_SEATING_CAPACITY.get(s['store_id'], 50) * num_days)
            for s in regional_stores
        )
        current_tables = sum(
            int(float(s.get('current_avg_turnover_rate', 0)) *
                STORE_SEATING_CAPACITY.get(s['store_id'], 50) * num_days)
            for s in regional_stores
        )
        # Target tables derived from target turnover rate × seating capacity × days
        target_tables = sum(
            int(get_store_turnover_target(s['store_id'], float(s.get('prev_avg_turnover_rate', 0))) *
                STORE_SEATING_CAPACITY.get(s['store_id'], 50) * num_days)
            for s in regional_stores
        )
        tables_gap = current_tables - target_tables

        # F - Previous year tables
        ws.cell(row=row, column=6, value=prev_tables)
        # G - Target tables
        ws.cell(row=row, column=7, value=target_tables)
        # H - Current tables
        ws.cell(row=row, column=8, value=current_tables)
        # I - Gap (with color)
        tables_gap_cell = ws.cell(row=row, column=9, value=tables_gap)
        tables_gap_cell.fill = self.green_fill if tables_gap >= 0 else self.red_fill

        # J - Notes
        ws.cell(row=row, column=10, value="桌数 = 翻台率目标 × 座位数 × 天数")

        # Style the summary row
        for col in range(1, 11):
            cell = ws.cell(row=row, column=col)
            if col not in [5, 9]:  # Don't override gap colors
                cell.fill = self.summary_fill
            cell.font = Font(bold=True)

    def _apply_formatting(self, ws: Worksheet, num_stores: int) -> None:
        """Apply professional formatting to the worksheet."""
        # Set column widths
        column_widths = {
            'A': 18,   # Store name
            'B': 12,   # Previous year turnover
            'C': 10,   # Target turnover
            'D': 12,   # Current turnover
            'E': 10,   # Turnover gap
            'F': 12,   # Previous year tables
            'G': 10,   # Target tables
            'H': 12,   # Current tables
            'I': 10,   # Tables gap
            'J': 30    # Notes
        }

        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        # Format data rows
        data_rows = range(3, 3 + num_stores + 1)  # Store data + summary
        for row in data_rows:
            for col in range(1, 11):
                cell = ws.cell(row=row, column=col)
                cell.border = self.thin_border
                cell.alignment = self.center_alignment

                # Number formatting
                if col in [2, 3, 4, 5]:  # Turnover rates (2 decimals)
                    if cell.value != "N/A":
                        cell.number_format = '0.00'
                elif col in [6, 7, 8, 9]:  # Tables (integers)
                    if cell.value != "N/A":
                        cell.number_format = '0'

        # Freeze panes
        ws.freeze_panes = "B3"

        self.logger.info("Formatting applied to weekly YoY comparison worksheet")

    def _add_time_segment_challenge_section(self, ws: Worksheet, target_date: str,
                                             store_data: List[Dict[str, Any]],
                                             start_row: int, num_days: int) -> int:
        """
        Add time segment challenge section below the main challenge section.

        Logic:
        1. Calculate daily target: (last year MTD TR + 0.18) × seats = daily target tables
        2. Daily improvement needed = daily target - last year daily tables
        3. Slow times (afternoon 14:00-16:59, late night 22:00-07:59) have hardcoded targets
        4. Busy times get leftover: improvement - afternoon - late_night
        5. Distribute leftover proportionally based on last year turnover

        Args:
            ws: Worksheet to add section to
            target_date: Target date string
            store_data: Store performance data from main section
            start_row: Starting row for this section
            num_days: Number of days in MTD period

        Returns:
            Next available row after this section
        """
        # Get time segment MTD data
        time_segment_data = self.data_provider.get_time_segment_mtd_data(target_date)

        if not time_segment_data:
            self.logger.warning("No time segment data available")
            return start_row

        # Calculate date ranges for headers using helper method
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        start_dt = target_dt.replace(day=1)
        prev_start_dt = start_dt.replace(year=start_dt.year - 1)
        prev_end_dt = target_dt.replace(year=target_dt.year - 1)

        current_period = self._format_date_period(start_dt, target_dt)
        prev_period = self._format_date_period(prev_start_dt, prev_end_dt)

        # Add section header
        current_row = start_row + 2  # Leave a gap

        # Section title
        title_cell = ws.cell(row=current_row, column=1, value="时段挑战")
        title_cell.font = Font(bold=True, size=12)
        current_row += 2

        # Generate tables for each time segment from config
        for segment_config in TIME_SEGMENT_CONFIG:
            is_slow_time = segment_config['type'] == 'slow'
            current_row = self._add_time_segment_table(
                ws, current_row,
                segment_label=segment_config['label'],
                segment_key=segment_config['key'],
                time_segment_data=time_segment_data,
                store_data=store_data,
                hardcoded_targets=segment_config['targets'],
                is_slow_time=is_slow_time,
                num_days=num_days,
                prev_period=prev_period,
                current_period=current_period
            )
            current_row += 2  # Gap between tables

        return current_row

    def _add_time_segment_table(self, ws: Worksheet, start_row: int,
                                 segment_label: str, segment_key: str,
                                 time_segment_data: Dict, store_data: List[Dict],
                                 hardcoded_targets: Dict, is_slow_time: bool,
                                 num_days: int, prev_period: str, current_period: str) -> int:
        """
        Add a single time segment challenge table.

        Args:
            ws: Worksheet
            start_row: Starting row
            segment_label: Time segment label (e.g., '14:00-16:59')
            segment_key: Key for the segment (e.g., 'afternoon')
            time_segment_data: Time segment data from database
            store_data: Store performance data
            hardcoded_targets: Hardcoded daily targets (for slow times)
            is_slow_time: Whether this is a slow time segment
            num_days: Number of days in MTD
            prev_period: Previous year period string (e.g., '25年1月1日-1月7日')
            current_period: Current year period string (e.g., '26年1月1日-1月7日')

        Returns:
            Next row after this table
        """
        current_row = start_row

        # Table header
        if is_slow_time:
            header_text = f"{segment_label} 低峰期挑战"
        else:
            header_text = f"{segment_label} 高峰期挑战"

        header_cell = ws.cell(row=current_row, column=1, value=header_text)
        header_cell.font = Font(bold=True)
        header_cell.fill = self.header_fill
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=10)
        current_row += 1

        # Column headers with dynamic date ranges
        headers = [
            "门店名称", "餐位数",
            f"{prev_period}翻台率", "去年日均桌数",
            "目标日均增量", f"{current_period}日均桌数",
            "日均进度",
            "去年总桌数", "今年总桌数", "总进度"
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=current_row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border

        current_row += 1

        # Data rows
        for store in store_data:
            store_id = store.get('store_id', 0)
            store_name = store.get('store_name', '')
            seating_capacity = STORE_SEATING_CAPACITY.get(store_id, 50)

            # Get time segment data for this store
            store_ts_data = time_segment_data.get(store_id, {}).get('time_segments', {})
            segment_data = store_ts_data.get(segment_label, {})

            prev_avg_turnover = segment_data.get('prev_avg_turnover', 0)
            prev_total_tables = segment_data.get('prev_total_tables', 0)
            prev_days = segment_data.get('prev_days', 0) or num_days
            current_total_tables = segment_data.get('current_total_tables', 0)
            current_days = segment_data.get('current_days', 0) or num_days

            # Calculate daily averages
            prev_daily_tables = prev_total_tables / prev_days if prev_days > 0 else 0
            current_daily_tables = current_total_tables / current_days if current_days > 0 else 0

            # Calculate target
            if is_slow_time and hardcoded_targets:
                # Slow time: use hardcoded target from config
                daily_target_improvement = hardcoded_targets.get(store_id, DEFAULT_SLOW_TIME_TARGET)
            else:
                # Busy time: calculate from leftover
                daily_target_improvement = self._calculate_busy_time_target(
                    store_id, store, time_segment_data, segment_key, num_days
                )

            # Calculate daily progress: current daily - prev daily
            daily_improvement = current_daily_tables - prev_daily_tables

            # Calculate total progress: current total - prev total
            total_improvement = current_total_tables - prev_total_tables

            # Check if target met (based on daily improvement vs daily target)
            target_met = daily_improvement >= daily_target_improvement

            # Write row
            ws.cell(row=current_row, column=1, value=store_name)
            ws.cell(row=current_row, column=2, value=seating_capacity)
            ws.cell(row=current_row, column=3, value=prev_avg_turnover)
            ws.cell(row=current_row, column=4, value=prev_daily_tables)
            ws.cell(row=current_row, column=5, value=daily_target_improvement)
            ws.cell(row=current_row, column=6, value=current_daily_tables)

            # 日均进度 cell with color (green if target met, red if not)
            daily_progress_cell = ws.cell(row=current_row, column=7, value=daily_improvement)
            daily_progress_cell.fill = self.green_fill if target_met else self.red_fill

            # Total columns
            ws.cell(row=current_row, column=8, value=prev_total_tables)
            ws.cell(row=current_row, column=9, value=current_total_tables)

            # 总进度 cell with color
            total_progress_cell = ws.cell(row=current_row, column=10, value=total_improvement)
            total_progress_cell.fill = self.green_fill if total_improvement >= 0 else self.red_fill

            # Apply formatting
            for col in range(1, 11):
                cell = ws.cell(row=current_row, column=col)
                cell.border = self.thin_border
                cell.alignment = self.center_alignment
                if col in [3, 4, 5, 6, 7]:
                    cell.number_format = '0.00'
                elif col in [8, 9, 10]:
                    cell.number_format = '0'

            current_row += 1

        return current_row

    def _calculate_busy_time_target(self, store_id: int, store: Dict,
                                     time_segment_data: Dict, segment_key: str,
                                     num_days: int) -> float:
        """
        Calculate busy time target from leftover after slow times.

        Leftover = total_daily_improvement - afternoon_target - late_night_target
        Busy time target = leftover × (this_segment_turnover / total_busy_turnover)

        Args:
            store_id: Store ID
            store: Store performance data
            time_segment_data: Time segment data from database
            segment_key: 'morning' or 'evening'
            num_days: Number of days in MTD period

        Returns:
            Daily target improvement for this busy time segment
        """
        seating_capacity = STORE_SEATING_CAPACITY.get(store_id, 50)

        # Get overall store data
        prev_turnover = float(store.get('prev_avg_turnover_rate', 0))
        target_turnover = get_store_turnover_target(store_id, prev_turnover)

        # Calculate daily tables improvement needed
        prev_daily_tables = prev_turnover * seating_capacity
        target_daily_tables = target_turnover * seating_capacity
        total_daily_improvement = target_daily_tables - prev_daily_tables

        # Subtract slow time targets from config
        afternoon_target = AFTERNOON_SLOW_TARGETS.get(store_id, DEFAULT_SLOW_TIME_TARGET)
        late_night_target = LATE_NIGHT_TARGETS.get(store_id, DEFAULT_SLOW_TIME_TARGET)
        leftover = total_daily_improvement - afternoon_target - late_night_target

        if leftover <= 0:
            return 0

        # Get busy time turnover rates from last year using config labels
        store_ts_data = time_segment_data.get(store_id, {}).get('time_segments', {})
        morning_label = TIME_SEGMENT_LABELS['morning']
        evening_label = TIME_SEGMENT_LABELS['evening']

        morning_data = store_ts_data.get(morning_label, {})
        evening_data = store_ts_data.get(evening_label, {})

        morning_turnover = morning_data.get('prev_avg_turnover', 0)
        evening_turnover = evening_data.get('prev_avg_turnover', 0)
        total_busy_turnover = morning_turnover + evening_turnover

        if total_busy_turnover <= 0:
            return leftover / 2  # Split evenly if no data

        # Distribute proportionally
        if segment_key == 'morning':
            return leftover * morning_turnover / total_busy_turnover
        else:  # evening
            return leftover * evening_turnover / total_busy_turnover
