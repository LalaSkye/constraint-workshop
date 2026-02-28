"""conftest.py — Add repository root to sys.path for tests in this directory."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
