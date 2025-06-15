#!/usr/bin/env python3
"""
Advanced test runner for the paperwork automation scripts.
Runs all tests with coverage reporting and detailed output.
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    try:
        import coverage  # type: ignore
        
        # Initialize coverage
        cov = coverage.Coverage(source=['scripts'])
        cov.start()
        
        # Run tests
        result = run_all_tests()
        
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\n" + "="*80)
        print("COVERAGE REPORT")
        print("="*80)
        cov.report(show_missing=True)
        
        # Generate HTML coverage report
        try:
            cov.html_report(directory='htmlcov')
            print(f"\n📊 HTML coverage report generated in 'htmlcov' directory")
        except Exception as e:
            print(f"⚠️  Could not generate HTML report: {e}")
        
        return result
        
    except ImportError:
        print("⚠️  Coverage package not installed. Running tests without coverage...")
        return run_all_tests()

def run_all_tests():
    """Run all test suites."""
    print("🧪 Running Paperwork Automation Test Suite")
    print("="*80)
    
    # Test discovery
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Test modules to include
    test_modules = [
        'tests.test_insert_data',
        'tests.test_extract_time_segments', 
        'tests.test_extract_all',
        'tests.test_validation_edge_cases',
        'tests.test_validation_integration'
    ]
    
    # Load tests from each module
    total_tests = 0
    for module_name in test_modules:
        try:
            module_suite = test_loader.loadTestsFromName(module_name)
            test_count = module_suite.countTestCases()
            test_suite.addTest(module_suite)
            total_tests += test_count
            print(f"✅ Loaded {test_count} tests from {module_name}")
        except Exception as e:
            print(f"❌ Failed to load tests from {module_name}: {e}")
    
    print(f"\n📋 Total tests loaded: {total_tests}")
    print("-"*80)
    
    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True,
        failfast=False
    )
    
    start_time = time.time()
    result = runner.run(test_suite)
    end_time = time.time()
    
    # Print results
    output = stream.getvalue()
    print(output)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"⏱️  Execution time: {end_time - start_time:.3f} seconds")
    print(f"🧪 Tests run: {result.testsRun}")
    print(f"✅ Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    if result.failures:
        print(f"❌ Failures: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"   • {test}")
    
    if result.errors:
        print(f"💥 Errors: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"   • {test}")
    
    if result.skipped:
        print(f"⏭️  Skipped: {len(result.skipped)}")
        for test, reason in result.skipped:
            print(f"   • {test}: {reason}")
    
    # Overall result
    if result.wasSuccessful():
        print(f"\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n💔 SOME TESTS FAILED")
        return False

def run_specific_test_category(category):
    """Run tests for a specific category."""
    category_modules = {
        'validation': [
            'tests.test_extract_all',
            'tests.test_validation_edge_cases', 
            'tests.test_validation_integration'
        ],
        'core': [
            'tests.test_insert_data',
            'tests.test_extract_time_segments'
        ],
        'integration': [
            'tests.test_extract_all',
            'tests.test_validation_integration'
        ]
    }
    
    if category not in category_modules:
        print(f"❌ Unknown test category: {category}")
        print(f"Available categories: {', '.join(category_modules.keys())}")
        return False
    
    print(f"🧪 Running {category.upper()} tests")
    print("="*80)
    
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    total_tests = 0
    for module_name in category_modules[category]:
        try:
            module_suite = test_loader.loadTestsFromName(module_name)
            test_count = module_suite.countTestCases()
            test_suite.addTest(module_suite)
            total_tests += test_count
            print(f"✅ Loaded {test_count} tests from {module_name}")
        except Exception as e:
            print(f"❌ Failed to load tests from {module_name}: {e}")
    
    print(f"\n📋 Total tests loaded: {total_tests}")
    print("-"*80)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

def run_quick_validation_tests():
    """Run a quick subset of validation tests for rapid feedback."""
    print("⚡ Running Quick Validation Tests")
    print("="*50)
    
    test_loader = unittest.TestLoader()
    
    # Load specific test methods for quick validation
    quick_tests = [
        'tests.test_extract_all.TestValidationFunctions.test_validate_excel_file_valid',
        'tests.test_extract_all.TestValidationFunctions.test_validate_daily_sheet_missing_columns',
        'tests.test_extract_all.TestValidationFunctions.test_validate_date_column_valid',
        'tests.test_extract_all.TestValidationFunctions.test_validate_holiday_column_valid',
        'tests.test_extract_all.TestValidationFunctions.test_validate_numeric_column_valid',
        'tests.test_validation_integration.TestValidationIntegration.test_complete_valid_file_validation'
    ]
    
    test_suite = unittest.TestSuite()
    for test_name in quick_tests:
        try:
            test_suite.addTest(test_loader.loadTestsFromName(test_name))
        except Exception as e:
            print(f"⚠️  Could not load {test_name}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    if result.wasSuccessful():
        print("\n✅ Quick validation tests passed!")
    else:
        print("\n❌ Some quick validation tests failed")
    
    return result.wasSuccessful()

def main():
    """Main test runner function."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'coverage':
            success = run_tests_with_coverage()
        elif command == 'quick':
            success = run_quick_validation_tests()
        elif command in ['validation', 'core', 'integration']:
            success = run_specific_test_category(command)
        elif command == 'help':
            print("📚 Test Runner Usage:")
            print("  python run_tests.py              - Run all tests")
            print("  python run_tests.py coverage     - Run all tests with coverage")
            print("  python run_tests.py quick        - Run quick validation tests")
            print("  python run_tests.py validation   - Run validation tests only")
            print("  python run_tests.py core         - Run core functionality tests")
            print("  python run_tests.py integration  - Run integration tests")
            print("  python run_tests.py help         - Show this help")
            return True
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python run_tests.py help' for usage information")
            return False
    else:
        success = run_tests_with_coverage()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 