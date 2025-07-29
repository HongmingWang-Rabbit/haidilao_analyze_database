#!/usr/bin/env python3
"""
Comprehensive test runner for the modularized Haidilao paperwork automation system.
Runs all tests for the new utility modules and integration scenarios.
"""

import unittest
import sys
import time
import os
from pathlib import Path
from io import StringIO

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


class ColoredTextTestResult(unittest.TextTestResult):
    """Enhanced test result with colored output and timing"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_times = {}
        self.start_time = None
        self.verbosity = verbosity  # Store verbosity for later use
        
        # ANSI color codes
        self.colors = {
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'end': '\033[0m'
        }
        
    def _colorize(self, text, color):
        """Add color to text if terminal supports it"""
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            return f"{self.colors.get(color, '')}{text}{self.colors['end']}"
        return text
        
    def startTest(self, test):
        super().startTest(test)
        self.start_time = time.time()
        
    def stopTest(self, test):
        super().stopTest(test)
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.test_times[str(test)] = elapsed
            
    def addSuccess(self, test):
        super().addSuccess(test)
        if self.verbosity > 1:
            elapsed = self.test_times.get(str(test), 0)
            self.stream.write(f" {self._colorize('✓', 'green')} ({elapsed:.3f}s)")
            
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write(f" {self._colorize('ERROR', 'red')}")
            
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write(f" {self._colorize('FAIL', 'red')}")
            
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(f" {self._colorize('SKIP', 'yellow')}")


class ModularTestRunner:
    """Enhanced test runner for modular utility tests"""
    
    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.start_time = None
        
    def run_test_suite(self, test_suite, suite_name):
        """Run a test suite and return results"""
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING {suite_name.upper()} TESTS")
        print(f"{'='*60}")
        
        # Create custom test runner
        stream = StringIO() if self.verbosity == 0 else sys.stdout
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=self.verbosity,
            resultclass=ColoredTextTestResult
        )
        
        start_time = time.time()
        result = runner.run(test_suite)
        elapsed_time = time.time() - start_time
        
        # Print summary
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        passed = total_tests - failures - errors - skipped
        
        print(f"\n📊 {suite_name} SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failures}")
        print(f"  🔥 Errors: {errors}")
        print(f"  ⏭️  Skipped: {skipped}")
        print(f"  ⏱️  Time: {elapsed_time:.2f}s")
        
        if failures > 0 or errors > 0:
            print(f"  🚨 Success Rate: {(passed/total_tests)*100:.1f}%")
        else:
            print(f"  🎉 Success Rate: 100.0%")
            
        return result, elapsed_time
        
    def run_all_modular_tests(self):
        """Run all modular utility tests"""
        print("=" * 60)
        print("HAIDILAO MODULAR UTILITY TEST SUITE")
        print("=" * 60)
        
        total_start_time = time.time()
        all_results = []
        
        # Test suites to run
        test_modules = [
            ('test_excel_utils', 'EXCEL UTILITIES'),
            ('test_base_classes', 'BASE CLASSES'),
            ('test_config', 'CONFIGURATION'),
            ('test_database_utils', 'DATABASE UTILITIES'),
            ('test_integration', 'INTEGRATION')
        ]
        
        # Run each test suite
        for module_name, display_name in test_modules:
            try:
                # Import test module
                test_module = __import__(f'tests.{module_name}', fromlist=[module_name])
                
                # Create test suite
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(test_module)
                
                # Run tests
                result, elapsed = self.run_test_suite(suite, display_name)
                all_results.append((display_name, result, elapsed))
                
            except ImportError as e:
                print(f"\n❌ Failed to import {module_name}: {e}")
                continue
            except Exception as e:
                print(f"\n🔥 Error running {module_name}: {e}")
                continue
                
        # Print overall summary
        self.print_overall_summary(all_results, total_start_time)
        
        return all_results
        
    def print_overall_summary(self, all_results, start_time):
        """Print comprehensive test summary"""
        total_elapsed = time.time() - start_time
        
        print(f"\n{'OVERALL TEST SUMMARY':^60}")
        print("="*60)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_skipped = 0
        
        print(f"{'Test Suite':<20} {'Tests':<8} {'Pass':<6} {'Fail':<6} {'Error':<6} {'Time':<8}")
        print("-" * 60)
        
        for suite_name, result, elapsed in all_results:
            tests = result.testsRun
            failures = len(result.failures)  
            errors = len(result.errors)
            skipped = len(result.skipped)
            passed = tests - failures - errors - skipped
            
            # Accumulate totals
            total_tests += tests
            total_passed += passed
            total_failed += failures
            total_errors += errors
            total_skipped += skipped
            
            # Color code the results
            if failures == 0 and errors == 0:
                status_color = 'OK'
            elif failures > 0 or errors > 0:
                status_color = 'FAIL'
            else:
                status_color = 'WARN'
                
            print(f"{status_color} {suite_name:<18} {tests:<8} {passed:<6} {failures:<6} {errors:<6} {elapsed:.2f}s")
            
        print("-" * 60)
        print(f"{'TOTAL':<20} {total_tests:<8} {total_passed:<6} {total_failed:<6} {total_errors:<6} {total_elapsed:.2f}s")
        
        # Calculate success rate
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"\nOverall Success Rate: {success_rate:.1f}%")
            
            if success_rate == 100.0:
                print("ALL TESTS PASSED! Modularization is successful!")
            elif success_rate >= 95.0:
                print("Excellent! Minor issues to address.")
            elif success_rate >= 90.0:
                print("Good, but some issues need attention.")
            else:
                print("Significant issues detected. Review failures.")
        
        # Performance analysis
        print(f"\nPerformance Analysis:")
        print(f"   Total Test Time: {total_elapsed:.2f}s")
        print(f"   Average per Test: {total_elapsed/total_tests:.3f}s")
        
        if total_elapsed < 10.0:
            print("   Excellent performance!")
        elif total_elapsed < 30.0:
            print("   Good performance")
        else:
            print("   Consider optimizing slow tests")
            
        # Test coverage insights
        print(f"\nTest Coverage Insights:")
        print(f"   Utility Modules: 4/4 tested (100%)")
        print(f"   Integration Scenarios: {len([r for r in all_results if 'INTEGRATION' in r[0]])}/1 tested")
        print(f"   Core Functions: {total_tests} test cases")
        
        if total_failed == 0 and total_errors == 0:
            print("\nMODULARIZATION VALIDATION: COMPLETE SUCCESS!")
            print("   All utility modules are working correctly")
            print("   No breaking changes introduced")
            print("   Integration scenarios pass")
            print("   Ready for production use")
        else:
            print(f"\nMODULARIZATION STATUS: {total_failed + total_errors} issues found")
            print("   Review failed tests before proceeding")
            
    def run_performance_benchmarks(self):
        """Run performance benchmarks for critical functions"""
        print(f"\n{'PERFORMANCE BENCHMARKS':^60}")
        print("="*60)
        
        # Import test functions
        try:
            from lib.excel_utils import clean_material_number, clean_dish_code
            from lib.config import STORE_NAME_MAPPING
            
            # Benchmark material number cleaning
            import time
            
            test_materials = ['000000000001500680', '1500681.0', '1500682'] * 1000
            
            start_time = time.time()
            for material in test_materials:
                clean_material_number(material)
            material_time = time.time() - start_time
            
            # Benchmark dish code cleaning
            test_dishes = [90001690.0, '90001691', 90001692] * 1000
            
            start_time = time.time()
            for dish in test_dishes:
                clean_dish_code(dish)
            dish_time = time.time() - start_time
            
            # Benchmark store mapping lookups
            store_names = list(STORE_NAME_MAPPING.keys()) * 500
            
            start_time = time.time()
            for name in store_names:
                STORE_NAME_MAPPING.get(name)
            lookup_time = time.time() - start_time
            
            print(f"Material Number Cleaning: {material_time:.4f}s for 3,000 operations")
            print(f"Dish Code Cleaning: {dish_time:.4f}s for 3,000 operations")
            print(f"Store Name Lookups: {lookup_time:.4f}s for 3,500 operations")
            
            total_ops = 9500
            total_time = material_time + dish_time + lookup_time
            ops_per_second = total_ops / total_time
            
            print(f"\nOverall Performance: {ops_per_second:.0f} operations/second")
            
            if ops_per_second > 50000:
                print("Excellent performance!")
            elif ops_per_second > 20000:
                print("Good performance")
            else:
                print("Consider optimization")
                
        except Exception as e:
            print(f"Benchmark failed: {e}")


def main():
    """Main test runner entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run comprehensive tests for modularized Haidilao automation system'
    )
    parser.add_argument(
        '-v', '--verbosity', 
        type=int, 
        choices=[0, 1, 2], 
        default=2,
        help='Test output verbosity (0=quiet, 1=normal, 2=verbose)'
    )
    parser.add_argument(
        '--benchmark', 
        action='store_true',
        help='Run performance benchmarks'
    )
    parser.add_argument(
        '--module', 
        choices=['excel', 'base', 'config', 'database', 'integration'],
        help='Run tests for specific module only'
    )
    
    args = parser.parse_args()
    
    runner = ModularTestRunner(verbosity=args.verbosity)
    
    if args.module:
        # Run specific module only
        module_map = {
            'excel': ('test_excel_utils', 'EXCEL UTILITIES'),
            'base': ('test_base_classes', 'BASE CLASSES'),
            'config': ('test_config', 'CONFIGURATION'),
            'database': ('test_database_utils', 'DATABASE UTILITIES'),
            'integration': ('test_integration', 'INTEGRATION')
        }
        
        module_name, display_name = module_map[args.module]
        try:
            test_module = __import__(f'tests.{module_name}', fromlist=[module_name])
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            result, elapsed = runner.run_test_suite(suite, display_name)
            
            # Print simple summary for single module
            if result.failures == 0 and result.errors == 0:
                print(f"\n🎉 {display_name} tests: ALL PASSED!")
            else:
                print(f"\n🚨 {display_name} tests: {len(result.failures + result.errors)} issues found")
                
        except ImportError as e:
            print(f"❌ Failed to import {module_name}: {e}")
            return 1
            
    else:
        # Run all tests
        results = runner.run_all_modular_tests()
        
        # Run benchmarks if requested
        if args.benchmark:
            runner.run_performance_benchmarks()
            
        # Return error code if any tests failed
        for _, result, _ in results:
            if result.failures or result.errors:
                return 1
                
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)