"""Ensure the project's src/ is on sys.path when running locally.

This file is auto-imported by Python if discoverable on sys.path.
"""
from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
src = repo_root / "src"
if src.exists():
    sys.path.insert(0, str(src))


