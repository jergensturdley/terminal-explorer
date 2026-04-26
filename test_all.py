"""Pytest-based test runner for Terminal Explorer."""

import sys
import pytest


def main() -> int:
    """Run the pytest suite."""
    return pytest.main(["-q", "tests"])


if __name__ == "__main__":
    sys.exit(main())
