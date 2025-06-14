#!/usr/bin/env python3
"""
Simple test runner for core functionality.
"""

import unittest
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Import test modules
from test_insert_data import TestInsertData, TestDataValidation
from test_extract_time_segments import TestExtractTimeSegments, TestDataValidation as TimeSegmentDataValidation

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add insert-data tests
    suite.addTest(loader.loadTestsFromTestCase(TestInsertData))
    suite.addTest(loader.loadTestsFromTestCase(TestDataValidation))
    
    # Add time segment tests
    suite.addTest(loader.loadTestsFromTestCase(TestExtractTimeSegments))
    suite.addTest(loader.loadTestsFromTestCase(TimeSegmentDataValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1) 