#!/usr/bin/env python3
"""
Challenge Targets Configuration Package

This package contains challenge target configurations for different periods.
"""

from .q1_2026_targets import (
    Q1_2026_START_DATE,
    Q1_2026_END_DATE,
    STORE_6_TURNOVER_TARGET,
    STORE_8_TURNOVER_TARGET,
    DEFAULT_TURNOVER_IMPROVEMENT,
    WEEKLY_TABLES_IMPROVEMENT,
    DEFAULT_SLOW_TIME_TARGET,
    AFTERNOON_SLOW_TARGETS,
    LATE_NIGHT_TARGETS,
    TIME_SEGMENT_LABELS,
    TIME_SEGMENT_CONFIG,
    STORE_TARGET_CONFIG,
    get_store_turnover_target,
    get_store_tables_target,
    is_store_excluded_from_regional,
    is_q1_2026_active
)

__all__ = [
    'Q1_2026_START_DATE',
    'Q1_2026_END_DATE',
    'STORE_6_TURNOVER_TARGET',
    'STORE_8_TURNOVER_TARGET',
    'DEFAULT_TURNOVER_IMPROVEMENT',
    'WEEKLY_TABLES_IMPROVEMENT',
    'DEFAULT_SLOW_TIME_TARGET',
    'AFTERNOON_SLOW_TARGETS',
    'LATE_NIGHT_TARGETS',
    'TIME_SEGMENT_LABELS',
    'TIME_SEGMENT_CONFIG',
    'STORE_TARGET_CONFIG',
    'get_store_turnover_target',
    'get_store_tables_target',
    'is_store_excluded_from_regional',
    'is_q1_2026_active'
]
