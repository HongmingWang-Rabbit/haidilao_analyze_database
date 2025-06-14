#!/usr/bin/env python3
"""
Test runner for paperwork automation scripts.
Runs all unit tests with optional coverage reporting.
"""

import unittest
import sys
import os
import argparse
from io import StringIO

def discover_and_run_tests(verbosity=2, pattern='test_*.py', coverage=False):
    """
    Discover and run all tests in the tests directory.
    
    Args:
        verbosity (int): Test output verbosity level (0-2)
        pattern (str): Pattern to match test files
        coverage (bool): Whether to run with coverage reporting
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Discover tests
    test_dir = os.path.dirname(os.path.abspath(__file__))
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=pattern)
    
    # Run tests
    if coverage:
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
            
            # Run the tests
            runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
            result = runner.run(suite)
            
            # Stop coverage and generate report
            cov.stop()
            cov.save()
            
            print("\n" + "="*60)
            print("COVERAGE REPORT")
            print("="*60)
            cov.report(show_missing=True)
            
            # Generate HTML coverage report
            html_dir = os.path.join(project_root, 'htmlcov')
            cov.html_report(directory=html_dir)
            print(f"\nHTML coverage report generated in: {html_dir}")
            
        except ImportError:
            print("Warning: coverage package not installed. Running tests without coverage.")
            print("Install with: pip install coverage")
            runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
            result = runner.run(suite)
    else:
        runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
        result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

def run_specific_test(test_module, test_class=None, test_method=None, verbosity=2):
    """
    Run a specific test module, class, or method.
    
    Args:
        test_module (str): Name of the test module (without .py extension)
        test_class (str, optional): Name of the test class
        test_method (str, optional): Name of the test method
        verbosity (int): Test output verbosity level
    
    Returns:
        bool: True if test(s) passed, False otherwise
    """
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Build test name
    test_name = test_module
    if test_class:
        test_name += f".{test_class}"
    if test_method:
        test_name += f".{test_method}"
    
    # Load and run the specific test
    loader = unittest.TestLoader()
    try:
        suite = loader.loadTestsFromName(test_name)
        runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"Error loading test '{test_name}': {e}")
        return False

def list_available_tests():
    """List all available test modules, classes, and methods."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Available Tests:")
    print("="*50)
    
    for filename in sorted(os.listdir(test_dir)):
        if filename.startswith('test_') and filename.endswith('.py'):
            module_name = filename[:-3]  # Remove .py extension
            print(f"\nModule: {module_name}")
            
            # Try to import the module and list its test classes
            try:
                import importlib.util
                module_path = os.path.join(test_dir, filename)
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find test classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, unittest.TestCase) and 
                        attr != unittest.TestCase):
                        
                        print(f"  Class: {attr_name}")
                        
                        # Find test methods
                        for method_name in dir(attr):
                            if method_name.startswith('test_'):
                                print(f"    Method: {method_name}")
                                
            except Exception as e:
                print(f"  Error loading module: {e}")

def main():
    """Main function to handle command line arguments and run tests."""
    parser = argparse.ArgumentParser(
        description='Run unit tests for paperwork automation scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                           # Run all tests
  python run_tests.py --coverage               # Run all tests with coverage
  python run_tests.py --list                   # List available tests
  python run_tests.py --module test_insert_data # Run specific module
  python run_tests.py --verbose 1              # Run with less verbose output
  python run_tests.py --pattern "test_extract*" # Run tests matching pattern
        """
    )
    
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Run tests with coverage reporting')
    parser.add_argument('--verbose', '-v', type=int, choices=[0, 1, 2], default=2,
                       help='Verbosity level (0=quiet, 1=normal, 2=verbose)')
    parser.add_argument('--pattern', '-p', default='test_*.py',
                       help='Pattern to match test files (default: test_*.py)')
    parser.add_argument('--module', '-m',
                       help='Run specific test module (e.g., test_insert_data)')
    parser.add_argument('--class', '-cl', dest='test_class',
                       help='Run specific test class (requires --module)')
    parser.add_argument('--method', '-mt', dest='test_method',
                       help='Run specific test method (requires --module and --class)')
    parser.add_argument('--list', '-l', action='store_true',
                       help='List all available tests')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_tests()
        return
    
    print("Paperwork Automation - Unit Test Runner")
    print("="*60)
    
    success = False
    
    if args.module:
        # Run specific test
        print(f"Running specific test: {args.module}")
        if args.test_class:
            print(f"  Class: {args.test_class}")
        if args.test_method:
            print(f"  Method: {args.test_method}")
        print("-" * 60)
        
        success = run_specific_test(
            args.module, 
            args.test_class, 
            args.test_method, 
            args.verbose
        )
    else:
        # Run all tests
        print(f"Running all tests matching pattern: {args.pattern}")
        if args.coverage:
            print("Coverage reporting enabled")
        print("-" * 60)
        
        success = discover_and_run_tests(
            verbosity=args.verbose,
            pattern=args.pattern,
            coverage=args.coverage
        )
    
    print("\n" + "="*60)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 