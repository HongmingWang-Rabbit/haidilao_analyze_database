#!/usr/bin/env python3
"""
Store Configuration Package
Centralized configuration for all store-related data and mock data.
"""

from .store_info import (
    STORE_MANAGERS,
    STORE_SEATING_CAPACITY,
    REGIONAL_MANAGER,
    WESTERN_REGION_STORES,
    EASTERN_REGION_STORES,
    ALL_CANADIAN_STORES,
    REPORT_STORE_ORDER,
    get_store_manager,
    get_seating_capacity,
    get_region
)

from .mock_data import (
    DAILY_STORE_MOCK_DATA,
    WEEKLY_STORE_MOCK_DATA,
    get_daily_mock_data,
    get_weekly_mock_data,
    get_mock_data_by_store_id
)

__all__ = [
    # Store info
    'STORE_MANAGERS',
    'STORE_SEATING_CAPACITY',
    'REGIONAL_MANAGER',
    'WESTERN_REGION_STORES',
    'EASTERN_REGION_STORES',
    'ALL_CANADIAN_STORES',
    'REPORT_STORE_ORDER',
    'get_store_manager',
    'get_seating_capacity',
    'get_region',

    # Mock data
    'DAILY_STORE_MOCK_DATA',
    'WEEKLY_STORE_MOCK_DATA',
    'get_daily_mock_data',
    'get_weekly_mock_data',
    'get_mock_data_by_store_id'
]
