#!/usr/bin/env python3
"""Run dependency-light betting and v3.1 tests, excluding ecological science tests.

The ecological tests are run separately by ecology-tests.yml with NumPy,
SciPy, pandas, and statsmodels installed. Keeping the suites distinct
prevents accidental import failures and avoids duplicate scientific runs.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest


def select_test_files(tests_dir: Path) -> list[Path]:
    """Select every non-ecological unittest module, without a brittle allowlist."""
    return [
        path for path in sorted(tests_dir.glob("test_*.py"))
        if path.is_file() and not path.name.startswith("test_ecology_")
    ]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    tests_dir = repo_root / "tests"
    files = select_test_files(tests_dir)
    if not files:
        print("ERROR: no non-ecology unit tests discovered", file=sys.stderr)
        return 2

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for path in files:
        suite.addTests(loader.discover(start_dir=str(tests_dir), pattern=path.name))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"Non-ecology modules: {len(files)}; tests executed: {result.testsRun}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
