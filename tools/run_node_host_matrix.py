#!/usr/bin/env python
"""Run host-side Router/EndDevice matrix tests for Phase 4.6."""

import os
import subprocess
import sys


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_node_api.py",
        "tests/test_node_matrix_api.py",
        "tests/test_import.py",
        "-q",
    ]
    return subprocess.call(cmd, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
