#!/usr/bin/env python3
"""
Challenge Targets Configuration Package

This package contains challenge target configurations for different periods.

Architecture:
- MONTHLY_TARGETS: Central config dictionary keyed by (year, month)
- get_monthly_config(): Get config for any date
- Helper functions for specific target types

To add new month targets, only update MONTHLY_TARGETS in q1_2026_targets.py.
"""

from .q1_2026_targets import (
    # Period constants
    Q1_2026_START_DATE,
    Q1_2026_END_DATE,
    # Default improvement values
    DEFAULT_TURNOVER_IMPROVEMENT,
    DAILY_TABLES_IMPROVEMENT,
    WEEKLY_TABLES_IMPROVEMENT,
    DEFAULT_SLOW_TIME_TARGET,
    # Monthly targets (central config)
    MONTHLY_TARGETS,
    get_monthly_config,
    # Legacy exported constants (backwards compatibility)
    JANUARY_2026_TURNOVER_TARGETS,
    JANUARY_2026_PROFIT_TARGETS,
    JANUARY_2026_TAKEOUT_TARGETS,
    AFTERNOON_SLOW_TARGETS,
    LATE_NIGHT_TARGETS,
    STORE_6_TURNOVER_TARGET,
    STORE_8_TURNOVER_TARGET,
    # Time segment config
    TIME_SEGMENT_LABELS,
    TIME_SEGMENT_CONFIG,
    # Store config
    STORE_TARGET_CONFIG,
    # Target getter functions
    get_store_turnover_target,
    get_store_tables_target,
    get_absolute_time_segment_target,
    get_profit_target,
    get_takeout_target,
    is_using_absolute_targets,
    # Store exclusion helpers
    is_store_excluded_from_regional,
    is_store_excluded_from_regional_totals,
    is_q1_2026_active,
    get_store_target_notes,
    # Takeout legacy
    TAKEOUT_EXCHANGE_RATES,
    TAKEOUT_DAILY_IMPROVEMENT_USD,
    get_takeout_daily_improvement_cad,
)

__all__ = [
    # Period constants
    'Q1_2026_START_DATE',
    'Q1_2026_END_DATE',
    # Default improvement values
    'DEFAULT_TURNOVER_IMPROVEMENT',
    'DAILY_TABLES_IMPROVEMENT',
    'WEEKLY_TABLES_IMPROVEMENT',
    'DEFAULT_SLOW_TIME_TARGET',
    # Monthly targets (central config)
    'MONTHLY_TARGETS',
    'get_monthly_config',
    # Legacy exported constants (backwards compatibility)
    'JANUARY_2026_TURNOVER_TARGETS',
    'JANUARY_2026_PROFIT_TARGETS',
    'JANUARY_2026_TAKEOUT_TARGETS',
    'AFTERNOON_SLOW_TARGETS',
    'LATE_NIGHT_TARGETS',
    'STORE_6_TURNOVER_TARGET',
    'STORE_8_TURNOVER_TARGET',
    # Time segment config
    'TIME_SEGMENT_LABELS',
    'TIME_SEGMENT_CONFIG',
    # Store config
    'STORE_TARGET_CONFIG',
    # Target getter functions
    'get_store_turnover_target',
    'get_store_tables_target',
    'get_absolute_time_segment_target',
    'get_profit_target',
    'get_takeout_target',
    'is_using_absolute_targets',
    # Store exclusion helpers
    'is_store_excluded_from_regional',
    'is_store_excluded_from_regional_totals',
    'is_q1_2026_active',
    'get_store_target_notes',
    # Takeout legacy
    'TAKEOUT_EXCHANGE_RATES',
    'TAKEOUT_DAILY_IMPROVEMENT_USD',
    'get_takeout_daily_improvement_cad',
]
