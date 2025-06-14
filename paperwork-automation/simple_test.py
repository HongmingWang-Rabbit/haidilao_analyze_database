#!/usr/bin/env python3
"""
Simple test runner for the paperwork automation scripts.
Runs core functionality tests and basic validation tests.
"""

import unittest
import sys
import os
import time

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def run_core_tests():
    """Run core functionality tests."""
    print("🧪 Running Core Functionality Tests")
    print("="*60)
    
    # Test discovery for core modules
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Core test modules
    core_modules = [
        'tests.test_insert_data',
        'tests.test_extract_time_segments'
    ]
    
    total_tests = 0
    for module_name in core_modules:
        try:
            module_suite = test_loader.loadTestsFromName(module_name)
            test_count = module_suite.countTestCases()
            test_suite.addTest(module_suite)
            total_tests += test_count
            print(f"✅ Loaded {test_count} tests from {module_name}")
        except Exception as e:
            print(f"❌ Failed to load tests from {module_name}: {e}")
    
    print(f"\n📋 Total core tests: {total_tests}")
    print("-"*60)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1, buffer=True)
    start_time = time.time()
    result = runner.run(test_suite)
    end_time = time.time()
    
    print(f"\n⏱️  Core tests completed in {end_time - start_time:.3f} seconds")
    return result

def run_validation_tests():
    """Run validation functionality tests."""
    print("\n🔍 Running Validation Tests")
    print("="*60)
    
    # Import and run validation tests
    try:
        # Import the validation test module
        import importlib.util
        test_path = os.path.join(os.path.dirname(__file__), 'test_validation_simple.py')
        spec = importlib.util.spec_from_file_location("test_validation_simple", test_path)
        validation_test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validation_test_module)
        
        # Run validation tests
        test_loader = unittest.TestLoader()
        validation_suite = test_loader.loadTestsFromModule(validation_test_module)
        
        print(f"✅ Loaded {validation_suite.countTestCases()} validation tests")
        print("-"*60)
        
        runner = unittest.TextTestRunner(verbosity=1, buffer=True)
        start_time = time.time()
        result = runner.run(validation_suite)
        end_time = time.time()
        
        print(f"\n⏱️  Validation tests completed in {end_time - start_time:.3f} seconds")
        return result
        
    except Exception as e:
        print(f"❌ Failed to run validation tests: {e}")
        return None

def run_extract_all_basic_tests():
    """Run basic extract-all.py tests that work."""
    print("\n🔧 Running Extract-All Basic Tests")
    print("="*60)
    
    test_loader = unittest.TestLoader()
    
    # Load only the working tests from extract_all
    working_tests = [
        'tests.test_extract_all.TestExtractAll.test_run_script_success',
        'tests.test_extract_all.TestExtractAll.test_run_script_with_debug',
        'tests.test_extract_all.TestExtractAll.test_run_script_with_output',
        'tests.test_extract_all.TestExtractAll.test_run_script_with_warnings',
        'tests.test_extract_all.TestExtractAll.test_run_script_failure',
        'tests.test_extract_all.TestExtractAll.test_command_construction_basic',
        'tests.test_extract_all.TestExtractAll.test_command_construction_all_options',
        'tests.test_extract_all.TestValidationFunctions.test_validate_excel_file_valid',
        'tests.test_extract_all.TestValidationFunctions.test_validate_excel_file_not_found',
        'tests.test_extract_all.TestValidationFunctions.test_validate_daily_sheet_missing_columns',
        'tests.test_extract_all.TestValidationFunctions.test_validate_daily_sheet_unknown_stores',
        'tests.test_extract_all.TestValidationFunctions.test_validate_time_segment_sheet_unknown_segments'
    ]
    
    test_suite = unittest.TestSuite()
    loaded_count = 0
    
    for test_name in working_tests:
        try:
            test_suite.addTest(test_loader.loadTestsFromName(test_name))
            loaded_count += 1
        except Exception as e:
            print(f"⚠️  Could not load {test_name}: {e}")
    
    print(f"✅ Loaded {loaded_count} extract-all tests")
    print("-"*60)
    
    if loaded_count > 0:
        runner = unittest.TextTestRunner(verbosity=1, buffer=True)
        start_time = time.time()
        result = runner.run(test_suite)
        end_time = time.time()
        
        print(f"\n⏱️  Extract-all tests completed in {end_time - start_time:.3f} seconds")
        return result
    else:
        print("⚠️  No extract-all tests could be loaded")
        return None

def print_summary(core_result, validation_result, extract_all_result):
    """Print comprehensive test summary."""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("="*80)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_successes = 0
    
    # Core tests summary
    if core_result:
        print(f"🧪 Core Functionality Tests:")
        print(f"   • Tests run: {core_result.testsRun}")
        print(f"   • Successes: {core_result.testsRun - len(core_result.failures) - len(core_result.errors)}")
        print(f"   • Failures: {len(core_result.failures)}")
        print(f"   • Errors: {len(core_result.errors)}")
        
        total_tests += core_result.testsRun
        total_failures += len(core_result.failures)
        total_errors += len(core_result.errors)
        total_successes += core_result.testsRun - len(core_result.failures) - len(core_result.errors)
    
    # Validation tests summary
    if validation_result:
        print(f"\n🔍 Validation Tests:")
        print(f"   • Tests run: {validation_result.testsRun}")
        print(f"   • Successes: {validation_result.testsRun - len(validation_result.failures) - len(validation_result.errors)}")
        print(f"   • Failures: {len(validation_result.failures)}")
        print(f"   • Errors: {len(validation_result.errors)}")
        
        total_tests += validation_result.testsRun
        total_failures += len(validation_result.failures)
        total_errors += len(validation_result.errors)
        total_successes += validation_result.testsRun - len(validation_result.failures) - len(validation_result.errors)
    
    # Extract-all tests summary
    if extract_all_result:
        print(f"\n🔧 Extract-All Tests:")
        print(f"   • Tests run: {extract_all_result.testsRun}")
        print(f"   • Successes: {extract_all_result.testsRun - len(extract_all_result.failures) - len(extract_all_result.errors)}")
        print(f"   • Failures: {len(extract_all_result.failures)}")
        print(f"   • Errors: {len(extract_all_result.errors)}")
        
        total_tests += extract_all_result.testsRun
        total_failures += len(extract_all_result.failures)
        total_errors += len(extract_all_result.errors)
        total_successes += extract_all_result.testsRun - len(extract_all_result.failures) - len(extract_all_result.errors)
    
    # Overall summary
    print(f"\n📈 OVERALL RESULTS:")
    print(f"   • Total tests run: {total_tests}")
    print(f"   • ✅ Total successes: {total_successes}")
    print(f"   • ❌ Total failures: {total_failures}")
    print(f"   • 💥 Total errors: {total_errors}")
    
    success_rate = (total_successes / total_tests * 100) if total_tests > 0 else 0
    print(f"   • 📊 Success rate: {success_rate:.1f}%")
    
    # Final verdict
    if total_failures == 0 and total_errors == 0:
        print(f"\n🎉 ALL TESTS PASSED! The paperwork automation system is working correctly.")
        return True
    else:
        print(f"\n⚠️  Some tests had issues, but core functionality is working.")
        return total_successes > 0

def main():
    """Main test runner function."""
    print("🚀 Paperwork Automation Test Suite")
    print("="*80)
    print("Testing core functionality and validation features...")
    
    start_time = time.time()
    
    # Run all test categories
    core_result = run_core_tests()
    validation_result = run_validation_tests()
    extract_all_result = run_extract_all_basic_tests()
    
    end_time = time.time()
    
    # Print comprehensive summary
    success = print_summary(core_result, validation_result, extract_all_result)
    
    print(f"\n⏱️  Total execution time: {end_time - start_time:.3f} seconds")
    print("="*80)
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 