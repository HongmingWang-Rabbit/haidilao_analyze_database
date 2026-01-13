#!/usr/bin/env python3
"""
Q1 2026 Challenge Targets Configuration

This module contains the challenge targets for Q1 2026 performance tracking.
Based on the Canada region's 2026 Q1 challenge target document.

Architecture:
- MONTHLY_TARGETS: Central config dictionary keyed by (year, month) tuples
- Helper functions access targets through get_monthly_config()
- Easy to add new months by adding entries to MONTHLY_TARGETS
- Falls back to improvement-based targets when no monthly config exists
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime


# ============================================================================
# CHALLENGE PERIOD DEFINITION
# ============================================================================

Q1_2026_START_DATE = "2026-01-01"
Q1_2026_END_DATE = "2026-03-31"


# ============================================================================
# DEFAULT IMPROVEMENT TARGETS (used when no monthly config exists)
# ============================================================================

DEFAULT_TURNOVER_IMPROVEMENT = 0.1  # +0.1 over last year same period
DAILY_TABLES_IMPROVEMENT = 6  # 6 tables per day improvement
WEEKLY_TABLES_IMPROVEMENT = 42  # 6 tables * 7 days = 42 tables/week
DEFAULT_SLOW_TIME_TARGET = 3  # Default slow time improvement


# ============================================================================
# TIME SEGMENT LABELS (must match database time_segment.label values)
# ============================================================================

TIME_SEGMENT_LABELS = {
    'morning': '08:00-13:59',
    'afternoon': '14:00-16:59',
    'evening': '17:00-21:59',
    'late_night': '22:00-(次)07:59'
}


# ============================================================================
# MONTHLY TARGETS CONFIGURATION
# ============================================================================
# Central configuration for monthly targets. Each entry is keyed by (year, month).
# When a monthly config exists, absolute targets are used instead of improvements.
#
# To add a new month's targets:
# 1. Add a new entry to MONTHLY_TARGETS with key (year, month)
# 2. Include turnover, afternoon, late_night, profit, and takeout targets
# 3. No code changes needed - the helper functions will automatically use it

MONTHLY_TARGETS: Dict[Tuple[int, int], Dict[str, Any]] = {
    # January 2026 targets
    (2026, 1): {
        'description': '2026年1月门店目标',
        'target_type': 'absolute',  # 'absolute' = fixed targets, 'improvement' = delta-based
        'turnover': {
            1: 4.47, 2: 3.88, 3: 5.45, 4: 4.42,
            5: 5.34, 6: 3.61, 7: 3.63, 8: 4.00,
        },
        'afternoon_tables': {  # 下午低峰期桌数目标 (日均)
            1: 37.6, 2: 22.0, 3: 51.3, 4: 48.4,
            5: 53.0, 6: 30.1, 7: 39.8, 8: 36.0,
        },
        'late_night_tables': {  # 深夜班桌数目标 (日均)
            1: 42.2, 2: 15.1, 3: 42.7, 4: 72.3,
            5: 56.5, 6: 31.9, 7: 26.3, 8: 22.0,
        },
        'profit': {  # 利润目标 (万加币)
            1: 6.77, 2: 3.82, 3: 10.45, 4: 20.14,
            5: 26.48, 6: 2.01, 7: 11.51, 8: 7.50,
        },
        'takeout': {  # 外卖目标 (万加币)
            1: 9.95, 2: 5.64, 3: 4.58, 4: 5.95,
            5: 13.11, 6: 5.33, 7: 1.88, 8: 4.65,
        },
    },
    # Add February 2026, March 2026, etc. as needed:
    # (2026, 2): { ... },
    # (2026, 3): { ... },
}


# ============================================================================
# EXPORTED CONSTANTS (for backwards compatibility)
# ============================================================================

# These are derived from MONTHLY_TARGETS for backwards compatibility
# New code should use get_monthly_config() or the helper functions instead

_jan_2026 = MONTHLY_TARGETS.get((2026, 1), {})

JANUARY_2026_TURNOVER_TARGETS: Dict[int, float] = _jan_2026.get('turnover', {})
JANUARY_2026_PROFIT_TARGETS: Dict[int, float] = _jan_2026.get('profit', {})
JANUARY_2026_TAKEOUT_TARGETS: Dict[int, float] = _jan_2026.get('takeout', {})
AFTERNOON_SLOW_TARGETS: Dict[int, float] = _jan_2026.get('afternoon_tables', {})
LATE_NIGHT_TARGETS: Dict[int, float] = _jan_2026.get('late_night_tables', {})

# Legacy store-specific constants
STORE_6_TURNOVER_TARGET = JANUARY_2026_TURNOVER_TARGETS.get(6, 3.61)
STORE_6_EXEMPTION_REASON = "道路施工影响 (2026年1月至2030年12月)"
STORE_8_TURNOVER_TARGET = JANUARY_2026_TURNOVER_TARGETS.get(8, 4.00)
STORE_8_EXCLUSION_REASON = "新店开业 (2025年10月18日)"
STORE_8_OPENING_DATE = "2025-10-18"


# ============================================================================
# TIME SEGMENT CONFIGURATION
# ============================================================================

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
# STORE TARGET CONFIGURATION (Legacy - for non-monthly periods)
# ============================================================================

STORE_TARGET_CONFIG: Dict[int, Dict[str, Any]] = {
    1: {'target_type': 'improvement', 'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT, 'excluded_from_regional': False,
        'notes': '标准考核目标'},
    2: {'target_type': 'improvement', 'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT, 'excluded_from_regional': False,
        'notes': '标准考核目标'},
    3: {'target_type': 'improvement', 'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT, 'excluded_from_regional': False,
        'notes': '标准考核目标'},
    4: {'target_type': 'improvement', 'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT, 'excluded_from_regional': False,
        'notes': '标准考核目标'},
    5: {'target_type': 'improvement', 'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT, 'excluded_from_regional': False,
        'notes': '标准考核目标'},
    6: {'target_type': 'fixed_turnover', 'turnover_target': STORE_6_TURNOVER_TARGET,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT, 'excluded_from_regional': False,
        'exemption_reason': STORE_6_EXEMPTION_REASON, 'notes': '翻台率固定目标,桌数仍需同比增长'},
    7: {'target_type': 'improvement', 'turnover_delta': DEFAULT_TURNOVER_IMPROVEMENT,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT, 'excluded_from_regional': False,
        'notes': '标准考核目标'},
    8: {'target_type': 'fixed_turnover', 'turnover_target': STORE_8_TURNOVER_TARGET,
        'tables_delta': WEEKLY_TABLES_IMPROVEMENT, 'excluded_from_regional': False,
        'excluded_from_regional_totals': False, 'exemption_reason': STORE_8_EXCLUSION_REASON,
        'notes': '新店,使用固定目标值'},
}


# ============================================================================
# TAKEOUT LEGACY CONFIGURATION
# ============================================================================

TAKEOUT_EXCHANGE_RATES: Dict[int, float] = {
    2025: 0.6952,    # 1 CAD = 0.6952 USD
    2026: 0.728597,  # 1 CAD = 0.728597 USD
}
TAKEOUT_DAILY_IMPROVEMENT_USD = 200


# ============================================================================
# CORE HELPER FUNCTIONS
# ============================================================================


def _parse_date(target_date: str) -> Optional[datetime]:
    """Parse date string to datetime, returning None on failure."""
    if not target_date:
        return None
    try:
        return datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        return None


def get_monthly_config(target_date: str) -> Optional[Dict[str, Any]]:
    """
    Get the monthly target configuration for a given date.

    Args:
        target_date: Target date in YYYY-MM-DD format

    Returns:
        Monthly config dict if exists, None otherwise
    """
    dt = _parse_date(target_date)
    if not dt:
        return None
    return MONTHLY_TARGETS.get((dt.year, dt.month))


def is_using_absolute_targets(target_date: str) -> bool:
    """
    Check if the target date uses absolute targets (not improvement-based).

    Args:
        target_date: Target date in YYYY-MM-DD format

    Returns:
        True if a monthly config with absolute targets exists
    """
    config = get_monthly_config(target_date)
    return config is not None and config.get('target_type') == 'absolute'


def is_q1_2026_active(target_date: str) -> bool:
    """
    Check if the target date falls within Q1 2026.

    Args:
        target_date: Target date in YYYY-MM-DD format

    Returns:
        True if date is within Q1 2026 (Jan 1 - Mar 31, 2026)
    """
    dt = _parse_date(target_date)
    if not dt:
        return False
    start_dt = datetime.strptime(Q1_2026_START_DATE, '%Y-%m-%d')
    end_dt = datetime.strptime(Q1_2026_END_DATE, '%Y-%m-%d')
    return start_dt <= dt <= end_dt


# ============================================================================
# TARGET GETTER FUNCTIONS
# ============================================================================


def get_store_turnover_target(store_id: int, prev_year_turnover: float,
                               target_date: str = None) -> float:
    """
    Get turnover target for a store.

    Uses monthly config if available, otherwise falls back to improvement-based.

    Args:
        store_id: Store ID (1-8)
        prev_year_turnover: Previous year same period average turnover rate
        target_date: Optional target date in YYYY-MM-DD format

    Returns:
        Target turnover rate
    """
    # Check monthly config first
    monthly = get_monthly_config(target_date) if target_date else None
    if monthly and monthly.get('target_type') == 'absolute':
        turnover_targets = monthly.get('turnover', {})
        if store_id in turnover_targets:
            return turnover_targets[store_id]

    # Fall back to store-specific config
    config = STORE_TARGET_CONFIG.get(store_id)
    if not config:
        return prev_year_turnover + DEFAULT_TURNOVER_IMPROVEMENT

    if config['target_type'] == 'fixed_turnover':
        return config['turnover_target']
    return prev_year_turnover + config.get('turnover_delta', DEFAULT_TURNOVER_IMPROVEMENT)


def get_store_tables_target(store_id: int, prev_year_tables: int) -> Optional[int]:
    """
    Calculate tables target for a store (improvement-based).

    Args:
        store_id: Store ID (1-8)
        prev_year_tables: Previous year same week total tables served

    Returns:
        Target tables count, or None if not applicable
    """
    config = STORE_TARGET_CONFIG.get(store_id)
    if not config:
        return prev_year_tables + WEEKLY_TABLES_IMPROVEMENT
    if config.get('tables_delta') is None:
        return None
    return prev_year_tables + config['tables_delta']


def get_absolute_time_segment_target(store_id: int, segment_key: str,
                                      target_date: str = None) -> Optional[float]:
    """
    Get absolute daily table target for a time segment.

    Args:
        store_id: Store ID (1-8)
        segment_key: 'afternoon' or 'late_night'
        target_date: Target date in YYYY-MM-DD format

    Returns:
        Absolute daily table target, or None if not using absolute targets
    """
    monthly = get_monthly_config(target_date) if target_date else None
    if not monthly or monthly.get('target_type') != 'absolute':
        return None

    if segment_key == 'afternoon':
        return monthly.get('afternoon_tables', {}).get(store_id)
    elif segment_key == 'late_night':
        return monthly.get('late_night_tables', {}).get(store_id)
    return None


def get_profit_target(store_id: int, target_date: str) -> Optional[float]:
    """
    Get monthly profit target for a store in 万加币 (10k CAD).

    Args:
        store_id: Store ID (1-8)
        target_date: Target date in YYYY-MM-DD format

    Returns:
        Monthly profit target in 万加币, or None if not applicable
    """
    monthly = get_monthly_config(target_date)
    if not monthly:
        return None
    return monthly.get('profit', {}).get(store_id)


def get_takeout_target(store_id: int, target_date: str) -> Optional[float]:
    """
    Get monthly takeout target for a store in 万加币 (10k CAD).

    Args:
        store_id: Store ID (1-8)
        target_date: Target date in YYYY-MM-DD format

    Returns:
        Monthly takeout target in 万加币, or None if not applicable
    """
    monthly = get_monthly_config(target_date)
    if not monthly:
        return None
    return monthly.get('takeout', {}).get(store_id)


def get_takeout_daily_improvement_cad(year: int) -> float:
    """
    Calculate daily takeout improvement target in CAD (legacy).

    Args:
        year: Target year (2025 or 2026)

    Returns:
        Daily improvement target in CAD ($200 USD converted)
    """
    rate = TAKEOUT_EXCHANGE_RATES.get(year, TAKEOUT_EXCHANGE_RATES[2026])
    return TAKEOUT_DAILY_IMPROVEMENT_USD / rate


# ============================================================================
# STORE EXCLUSION HELPERS
# ============================================================================


def is_store_excluded_from_regional(store_id: int) -> bool:
    """Check if store should be excluded from regional YoY calculations."""
    config = STORE_TARGET_CONFIG.get(store_id)
    return config.get('excluded_from_regional', False) if config else False


def is_store_excluded_from_regional_totals(store_id: int) -> bool:
    """Check if store should be excluded from regional totals (Canada summary)."""
    config = STORE_TARGET_CONFIG.get(store_id)
    return config.get('excluded_from_regional_totals', False) if config else False


def get_store_target_notes(store_id: int) -> str:
    """Get notes/explanation for a store's target rules."""
    config = STORE_TARGET_CONFIG.get(store_id)
    if not config:
        return '标准考核目标'
    notes = config.get('notes', '')
    exemption = config.get('exemption_reason', '')
    return f"{notes} - {exemption}" if exemption else notes


# ============================================================================
# EXPORTS
# ============================================================================

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
