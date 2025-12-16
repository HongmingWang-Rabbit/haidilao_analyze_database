#!/usr/bin/env python3
"""
Store Information Configuration
Centralized configuration for all store-related data including managers, seating capacity, etc.
"""

from typing import Dict

# ============================================================================
# STORE MANAGERS
# ============================================================================

STORE_MANAGERS: Dict[int, str] = {
    1: '张森磊',
    2: '潘幸远',
    3: 'Bao Xiaoyun',
    4: '李俊娟',
    5: '陈浩',
    6: '高新菊',
    7: '潘幸远',
    8: '李俊娟'
}


# ============================================================================
# STORE SEATING CAPACITY
# ============================================================================

STORE_SEATING_CAPACITY: Dict[int, int] = {
    1: 53,
    2: 36,
    3: 48,
    4: 70,
    5: 55,
    6: 56,
    7: 57
}


# ============================================================================
# REGIONAL MANAGER
# ============================================================================

REGIONAL_MANAGER: str = '蒋冰遇'


# ============================================================================
# STORE REGIONAL GROUPING
# ============================================================================

# Western region stores
WESTERN_REGION_STORES = [1, 2, 7]  # 一店, 二店, 七店

# Eastern region stores
EASTERN_REGION_STORES = [3, 4, 5, 6]  # 三店, 四店, 五店, 六店

# All Canadian stores
ALL_CANADIAN_STORES = list(range(1, 8))  # Stores 1-7


# ============================================================================
# STORE DISPLAY ORDER
# ============================================================================

# Store order for reports (西部 first, then 东部)
REPORT_STORE_ORDER = [1, 2, 7, 3, 4, 5, 6]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_store_manager(store_id: int) -> str:
    """Get the manager name for a given store ID"""
    return STORE_MANAGERS.get(store_id, REGIONAL_MANAGER)


def get_seating_capacity(store_id: int) -> int:
    """Get the seating capacity for a given store ID"""
    return STORE_SEATING_CAPACITY.get(store_id, 50)


def get_region(store_id: int) -> str:
    """Get the region (西部/东部) for a given store ID"""
    if store_id in WESTERN_REGION_STORES:
        return '西部'
    elif store_id in EASTERN_REGION_STORES:
        return '东部'
    return '未知'


# ============================================================================
# EXPORT ALL
# ============================================================================

__all__ = [
    'STORE_MANAGERS',
    'STORE_SEATING_CAPACITY',
    'REGIONAL_MANAGER',
    'WESTERN_REGION_STORES',
    'EASTERN_REGION_STORES',
    'ALL_CANADIAN_STORES',
    'REPORT_STORE_ORDER',
    'get_store_manager',
    'get_seating_capacity',
    'get_region'
]
