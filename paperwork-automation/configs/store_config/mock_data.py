#!/usr/bin/env python3
"""
Mock Data Configuration for Store Tracking Worksheets
Used for testing and development when real database data is not available.
"""

from typing import Dict, List, Any


# ============================================================================
# DAILY STORE TRACKING MOCK DATA
# ============================================================================

DAILY_STORE_MOCK_DATA: List[Dict[str, Any]] = [
    {
        'store_id': 1,
        'store_name': '加拿大一店',
        'manager_name': '张森磊',
        'seating_capacity': 53,
        'annual_avg_turnover_2024': 4.51,
        'current_turnover_rate': 4.75,
        'prev_turnover_rate': 4.06,
        'current_revenue': 4.34,
        'prev_revenue': 3.83
    },
    {
        'store_id': 2,
        'store_name': '加拿大二店',
        'manager_name': '潘幸远',
        'seating_capacity': 36,
        'annual_avg_turnover_2024': 4.02,
        'current_turnover_rate': 2.85,
        'prev_turnover_rate': 3.98,
        'current_revenue': 1.59,
        'prev_revenue': 1.87
    },
    {
        'store_id': 3,
        'store_name': '加拿大三店',
        'manager_name': 'Bao Xiaoyun',
        'seating_capacity': 48,
        'annual_avg_turnover_2024': 3.54,
        'current_turnover_rate': 3.14,
        'prev_turnover_rate': 4.4,
        'current_revenue': 2.4,
        'prev_revenue': 3.25
    },
    {
        'store_id': 4,
        'store_name': '加拿大四店',
        'manager_name': '李俊娟',
        'seating_capacity': 70,
        'annual_avg_turnover_2024': 3.32,
        'current_turnover_rate': 3.43,
        'prev_turnover_rate': 5.38,
        'current_revenue': 4.31,
        'prev_revenue': 6.76
    },
    {
        'store_id': 5,
        'store_name': '加拿大五店',
        'manager_name': '陈浩',
        'seating_capacity': 55,
        'annual_avg_turnover_2024': 4.31,
        'current_turnover_rate': 4.78,
        'prev_turnover_rate': 7.2,
        'current_revenue': 4.76,
        'prev_revenue': 7.18
    },
    {
        'store_id': 6,
        'store_name': '加拿大六店',
        'manager_name': '高新菊',
        'seating_capacity': 56,
        'annual_avg_turnover_2024': 3.82,
        'current_turnover_rate': 3.82,
        'prev_turnover_rate': 5.1,
        'current_revenue': 4.03,
        'prev_revenue': 5.4
    },
    {
        'store_id': 7,
        'store_name': '加拿大七店',
        'manager_name': '潘幸远',
        'seating_capacity': 57,
        'annual_avg_turnover_2024': 3.80,
        'current_turnover_rate': 2.71,
        'prev_turnover_rate': 4.06,
        'current_revenue': 1.59,
        'prev_revenue': 1.87
    },
    {
        'store_id': 8,
        'store_name': '加拿大八店',
        'manager_name': '李俊娟',
        'seating_capacity': 56,
        'annual_avg_turnover_2024': 3.32,
        'current_turnover_rate': 4.86,
        'prev_turnover_rate': 3.86,
        'current_revenue': 4.31,
        'prev_revenue': 3.64
    }
]


# ============================================================================
# WEEKLY STORE TRACKING MOCK DATA
# ============================================================================

WEEKLY_STORE_MOCK_DATA: List[Dict[str, Any]] = [
    {
        'store_id': 1,
        'store_name': '加拿大一店',
        'manager_name': '张森磊',
        'seating_capacity': 53,
        'annual_avg_turnover_2024': 4.51,
        'current_avg_turnover_rate': 4.75,
        'prev_avg_turnover_rate': 4.06,
        'current_total_revenue': 30.40,
        'prev_total_revenue': 26.83
    },
    {
        'store_id': 2,
        'store_name': '加拿大二店',
        'manager_name': '潘幸远',
        'seating_capacity': 36,
        'annual_avg_turnover_2024': 4.02,
        'current_avg_turnover_rate': 2.85,
        'prev_avg_turnover_rate': 3.98,
        'current_total_revenue': 11.13,
        'prev_total_revenue': 13.09
    },
    {
        'store_id': 3,
        'store_name': '加拿大三店',
        'manager_name': 'Bao Xiaoyun',
        'seating_capacity': 48,
        'annual_avg_turnover_2024': 3.54,
        'current_avg_turnover_rate': 3.14,
        'prev_avg_turnover_rate': 4.40,
        'current_total_revenue': 16.80,
        'prev_total_revenue': 22.75
    },
    {
        'store_id': 4,
        'store_name': '加拿大四店',
        'manager_name': '李俊娟',
        'seating_capacity': 70,
        'annual_avg_turnover_2024': 3.32,
        'current_avg_turnover_rate': 3.43,
        'prev_avg_turnover_rate': 5.38,
        'current_total_revenue': 30.17,
        'prev_total_revenue': 47.32
    },
    {
        'store_id': 5,
        'store_name': '加拿大五店',
        'manager_name': '陈浩',
        'seating_capacity': 55,
        'annual_avg_turnover_2024': 4.31,
        'current_avg_turnover_rate': 4.78,
        'prev_avg_turnover_rate': 7.20,
        'current_total_revenue': 33.32,
        'prev_total_revenue': 50.26
    },
    {
        'store_id': 6,
        'store_name': '加拿大六店',
        'manager_name': '高新菊',
        'seating_capacity': 56,
        'annual_avg_turnover_2024': 3.82,
        'current_avg_turnover_rate': 3.82,
        'prev_avg_turnover_rate': 5.10,
        'current_total_revenue': 28.21,
        'prev_total_revenue': 37.80
    },
    {
        'store_id': 7,
        'store_name': '加拿大七店',
        'manager_name': '潘幸远',
        'seating_capacity': 57,
        'annual_avg_turnover_2024': 3.80,
        'current_avg_turnover_rate': 2.71,
        'prev_avg_turnover_rate': 4.06,
        'current_total_revenue': 11.13,
        'prev_total_revenue': 13.09
    },
    {
        'store_id': 8,
        'store_name': '加拿大八店',
        'manager_name': '李俊娟',
        'seating_capacity': 56,
        'annual_avg_turnover_2024': 3.32,
        'current_avg_turnover_rate': 4.75,
        'prev_avg_turnover_rate': 3.78,
        'current_total_revenue': 30.17,
        'prev_total_revenue': 25.48
    }
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_daily_mock_data() -> List[Dict[str, Any]]:
    """Get mock data for daily store tracking"""
    return DAILY_STORE_MOCK_DATA.copy()


def get_weekly_mock_data() -> List[Dict[str, Any]]:
    """Get mock data for weekly store tracking"""
    return WEEKLY_STORE_MOCK_DATA.copy()


def get_mock_data_by_store_id(store_id: int, data_type: str = 'daily') -> Dict[str, Any]:
    """
    Get mock data for a specific store

    Args:
        store_id: Store ID (1-8)
        data_type: 'daily' or 'weekly'

    Returns:
        Dict with store mock data or empty dict if not found
    """
    data = DAILY_STORE_MOCK_DATA if data_type == 'daily' else WEEKLY_STORE_MOCK_DATA
    for store_data in data:
        if store_data['store_id'] == store_id:
            return store_data.copy()
    return {}


# ============================================================================
# EXPORT ALL
# ============================================================================

__all__ = [
    'DAILY_STORE_MOCK_DATA',
    'WEEKLY_STORE_MOCK_DATA',
    'get_daily_mock_data',
    'get_weekly_mock_data',
    'get_mock_data_by_store_id'
]
