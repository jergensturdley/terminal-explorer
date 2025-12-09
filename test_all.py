"""
Master test runner for Terminal Explorer.
Runs all test suites and provides a comprehensive report.
"""

import sys
import subprocess


def run_test_suite(name, script):
    """Run a test suite and return the result."""
    print(f"\n{'='*60}")
    print(f"Running {name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=30  # Reduced from 60 to 30 seconds
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"ERROR: {name} timed out!")
        return False
    except Exception as e:
        print(f"ERROR running {name}: {e}")
        return False


def main():
    """Run all test suites."""
    print("="*60)
    print("Terminal Explorer - Master Test Runner")
    print("="*60)
    
    test_suites = [
        ("Basic Load Test", "test_load.py"),
        ("Comprehensive Unit Tests", "test_comprehensive.py"),
        ("Integration Tests", "test_integration.py"),
        ("UI and App Logic Tests", "test_ui.py"),
    ]
    
    results = {}
    
    for name, script in test_suites:
        results[name] = run_test_suite(name, script)
    
    # Summary
    print("\n" + "="*60)
    print("OVERALL TEST SUMMARY")
    print("="*60)
    
    total_suites = len(results)
    passed_suites = sum(1 for r in results.values() if r)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*60)
    print(f"Test Suites: {passed_suites}/{total_suites} passed")
    print("="*60)
    
    if passed_suites == total_suites:
        print("\n🎉 All test suites passed! 🎉")
        print("\nNo crashes detected in any functionality.")
        print("The application appears to be stable and robust.")
        return 0
    else:
        print(f"\n⚠️  {total_suites - passed_suites} test suite(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
