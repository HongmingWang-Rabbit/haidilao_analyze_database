#!/usr/bin/env python3
"""
Q1 2026 Challenge Targets Configuration

This module contains the challenge targets for Q1 2026 performance tracking.
Based on the Canada region's 2026 Q1 challenge target document.

Target Rules:
- Store 6: Fixed turnover target of 3.65 due to road construction (Jan 2026 - Dec 2030)
- Store 8: Fixed turnover target of 4.0 (new store opened Oct 2025, excluded from regional YoY)
- Stores 1-5, 7: Turnover target = last year same period + 0.16
- All stores except 8: Tables target = last year same period + 8 tables/day (56/week)
"""

from typing import Dict, Any, Optional
from datetime import datetime

# ============================================================================
# Q1 2026 CHALLENGE PERIOD
# ============================================================================

Q1_2026_START_DATE = "2026-01-01"
Q1_2026_END_DATE = "2026-03-31"

# ============================================================================
# STORE-SPECIFIC TARGET CONSTANTS
# ============================================================================

# Store 6: Fixed turnover target due to road construction
# Reason: Road construction from Jan 2026 to Dec 2030
STORE_6_TURNOVER_TARGET = 3.65
STORE_6_EXEMPTION_REASON = "道路施工影响 (2026年1月至2030年12月)"

# Store 8: New store with fixed target, excluded from regional YoY
# Reason: Opened Oct 18, 2025, no comparable previous year data
STORE_8_TURNOVER_TARGET = 4.0
STORE_8_EXCLUSION_REASON = "新店开业 (2025年10月18日)"
STORE_8_OPENING_DATE = "2025-10-18"

# Default improvement targets for other stores (1-5, 7)
DEFAULT_TURNOVER_IMPROVEMENT = 0.18  # +0.18 over last year same period
DAILY_TABLES_IMPROVEMENT = 8  # 8 tables per day improvement (legacy)
WEEKLY_TABLES_IMPROVEMENT = 56  # 8 tables * 7 days = 56 tables/week (legacy)

# ============================================================================
# TIME SEGMENT CHALLENGE TARGETS (Hardcoded daily targets)
# ============================================================================

# Time segment labels mapping (must match database time_segment.label values)
TIME_SEGMENT_LABELS = {
    'morning': '08:00-13:59',
    'afternoon': '14:00-16:59',
    'evening': '17:00-21:59',
    'late_night': '22:00-(次)07:59'
}

# Default slow time target for stores not explicitly configured
DEFAULT_SLOW_TIME_TARGET = 3

# Slow time segments have fixed daily targets per store
# 14:00-16:59 (afternoon slow period) - daily table improvement target
AFTERNOON_SLOW_TARGETS: Dict[int, int] = {
    1: 3,
    2: 2,
    3: 3,
    4: 4,
    5: 3,
    6: 3,
    7: 4,
    8: 40  # New store, higher expectation
}

# 22:00-(次)07:59 (late night) - daily table improvement target
LATE_NIGHT_TARGETS: Dict[int, int] = {
    1: 3,
    2: 2,
    3: 3,
    4: 4,
    5: 3,
    6: 3,
    7: 4,
    8: 44  # New store, higher expectation
}

# Time segment challenge configuration
# Defines which segments are slow/busy and their target sources
TIME_SEGMENT_CONFIG = [
    {
        'label': TIME_SEGMENT_LABELS['afternoon'],
        'key': 'afternoon',
        'type': 'slow',
        'targets': AFTERNOON_SLOW_TARGETS
    },
    {
        'label': TIME_SEGMENT_LABELS['late_night'],
        'key': 'late_night',
        'type': 'slow',
        'targets': LATE_NIGHT_TARGETS
    },
    {
        'label': TIME_SEGMENT_LABELS['morning'],
        'key': 'morning',
        'type': 'busy',
        'targets': None  # Calculated from leftover
    },
    {
        'label': TIME_SEGMENT_LABELS['evening'],
        'key': 'evening',
        'type': 'busy',
        'targets': None  # Calculated from leftover
    }
]

# ============================================================================
# STORE TARGET CONFIGURATION
# ============================================================================

STORE_TARGET_CONFIG: Dict[int, Dict[str, Any]] = {
    1: {
        'target_type': 'improvement',
        'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT,
        'excluded_from_regional': False,
        'notes': '标准考核目标'
    },
    2: {
        'target_type': 'improvement',
        'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT,
        'excluded_from_regional': False,
        'notes': '标准考核目标'
    },
    3: {
        'target_type': 'improvement',
        'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT,
        'excluded_from_regional': False,
        'notes': '标准考核目标'
    },
    4: {
        'target_type': 'improvement',
        'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT,
        'excluded_from_regional': False,
        'notes': '标准考核目标'
    },
    5: {
        'target_type': 'improvement',
        'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT,
        'excluded_from_regional': False,
        'notes': '标准考核目标'
    },
    6: {
        'target_type': 'fixed_turnover',
        'turnover_target': STORE_6_TURNOVER_TARGET,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT,
        'excluded_from_regional': False,
        'exemption_reason': STORE_6_EXEMPTION_REASON,
        'notes': '翻台率固定目标,桌数仍需同比增长'
    },
    7: {
        'target_type': 'improvement',
        'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT,
        'excluded_from_regional': False,
        'notes': '标准考核目标'
    },
    8: {
        'target_type': 'fixed_turnover',
        'turnover_target': STORE_8_TURNOVER_TARGET,
        'tables_delta': None,  # No tables target for Store 8
        'excluded_from_regional': True,  # Excluded from regional YoY calculations
        'exemption_reason': STORE_8_EXCLUSION_REASON,
        'notes': '新店,不参与区域同比计算'
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_store_turnover_target(store_id: int, prev_year_turnover: float) -> float:
    """
    Calculate turnover target for a store.

    Args:
        store_id: Store ID (1-8)
        prev_year_turnover: Previous year same week average turnover rate

    Returns:
        Target turnover rate for the current week
    """
    config = STORE_TARGET_CONFIG.get(store_id)

    if not config:
        # Default to improvement target if store not configured
        return prev_year_turnover + DEFAULT_TURNOVER_IMPROVEMENT

    if config['target_type'] == 'fixed_turnover':
        return config['turnover_target']
    else:
        return prev_year_turnover + config.get('turnover_delta', DEFAULT_TURNOVER_IMPROVEMENT)


def get_store_tables_target(store_id: int, prev_year_tables: int) -> Optional[int]:
    """
    Calculate tables target for a store.

    Args:
        store_id: Store ID (1-8)
        prev_year_tables: Previous year same week total tables served

    Returns:
        Target tables count for the current week, or None for Store 8
    """
    config = STORE_TARGET_CONFIG.get(store_id)

    if not config:
        return prev_year_tables + WEEKLY_TABLES_IMPROVEMENT

    if config.get('tables_delta') is None:
        return None  # Store 8 has no tables target

    return prev_year_tables + config['tables_delta']


def is_store_excluded_from_regional(store_id: int) -> bool:
    """
    Check if store should be excluded from regional YoY calculations.

    Args:
        store_id: Store ID (1-8)

    Returns:
        True if store should be excluded from regional calculations
    """
    config = STORE_TARGET_CONFIG.get(store_id)
    return config.get('excluded_from_regional', False) if config else False


def is_q1_2026_active(target_date: str) -> bool:
    """
    Check if the target date falls within Q1 2026.

    Args:
        target_date: Target date in YYYY-MM-DD format

    Returns:
        True if date is within Q1 2026 (Jan 1 - Mar 31, 2026)
    """
    try:
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        start_dt = datetime.strptime(Q1_2026_START_DATE, '%Y-%m-%d')
        end_dt = datetime.strptime(Q1_2026_END_DATE, '%Y-%m-%d')
        return start_dt <= target_dt <= end_dt
    except ValueError:
        return False


def get_store_target_notes(store_id: int) -> str:
    """
    Get notes/explanation for a store's target rules.

    Args:
        store_id: Store ID (1-8)

    Returns:
        Notes explaining the store's target calculation method
    """
    config = STORE_TARGET_CONFIG.get(store_id)
    if not config:
        return '标准考核目标'

    notes = config.get('notes', '')
    exemption = config.get('exemption_reason', '')

    if exemption:
        return f"{notes} - {exemption}"
    return notes


# ============================================================================
# TAKEOUT CHALLENGE CONFIGURATION
# ============================================================================

# Exchange rates for converting $200 USD daily improvement to CAD
# Formula: $200 USD / exchange_rate = CAD amount
# Rate meaning: 1 CAD = X USD
TAKEOUT_EXCHANGE_RATES: Dict[int, float] = {
    2025: 0.6952,    # 1 CAD = 0.6952 USD (so $200 USD = $287.68 CAD)
    2026: 0.728597,  # 1 CAD = 0.728597 USD (so $200 USD = $274.50 CAD)
}

# Daily takeout improvement target in USD
TAKEOUT_DAILY_IMPROVEMENT_USD = 200


def get_takeout_daily_improvement_cad(year: int) -> float:
    """
    Calculate daily takeout improvement target in CAD.

    Args:
        year: Target year (2025 or 2026)

    Returns:
        Daily improvement target in CAD ($200 USD converted)
    """
    rate = TAKEOUT_EXCHANGE_RATES.get(year, TAKEOUT_EXCHANGE_RATES[2026])
    return TAKEOUT_DAILY_IMPROVEMENT_USD / rate


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'Q1_2026_START_DATE',
    'Q1_2026_END_DATE',
    'STORE_6_TURNOVER_TARGET',
    'STORE_8_TURNOVER_TARGET',
    'DEFAULT_TURNOVER_IMPROVEMENT',
    'DAILY_TABLES_IMPROVEMENT',
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
    'is_q1_2026_active',
    'get_store_target_notes',
    # Takeout challenge
    'TAKEOUT_EXCHANGE_RATES',
    'TAKEOUT_DAILY_IMPROVEMENT_USD',
    'get_takeout_daily_improvement_cad'
]
