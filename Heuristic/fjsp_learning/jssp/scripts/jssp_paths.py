"""Shared paths for the JSSP teaching-note tools."""

from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
JSSP_DIR = SCRIPT_DIR.parent
CHECKS_DIR = JSSP_DIR / "checks"
NOTES_DIR = REPO_ROOT / "docs" / "运筹优化" / "调度与生产" / "JSSP"
ASSETS_DIR = NOTES_DIR / "assets"
