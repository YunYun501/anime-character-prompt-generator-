#!/usr/bin/env python3
"""
Test runner for Random Character Prompt Generator.
"""

import sys
import subprocess
import argparse


def run_tests(verbose=False, coverage=False):
    """Run the test suite."""
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=generator", "--cov=web", "--cov-report=term-missing"])
    
    print(f"Running tests with command: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run tests for Random Character Prompt Generator")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    
    args = parser.parse_args()
    
    # Build pytest command
    pytest_args = []
    
    if args.unit:
        pytest_args.extend(["-m", "unit"])
    elif args.integration:
        pytest_args.extend(["-m", "integration"])
    
    return run_tests(verbose=args.verbose, coverage=args.coverage)


if __name__ == "__main__":
    sys.exit(main())