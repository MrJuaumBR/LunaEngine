#!/usr/bin/env python3
"""
Remove all __pycache__ directories recursively.
"""

import sys
import os
import shutil
import argparse
from pathlib import Path

def walk_through_pycache(folder: Path, dry_run: bool = False) -> int:
    """
    Recursively delete __pycache__ directories.
    Returns the number of removed directories.
    """
    removed = 0
    for item in folder.iterdir():
        if item.is_dir():
            if item.name == "__pycache__":
                if dry_run:
                    print(f"[DRY RUN] Would remove {item}")
                else:
                    print(f"Removing {item}")
                    # Remove all files inside first
                    for file in item.iterdir():
                        file.unlink()
                    # Ensure we have permissions and remove the directory
                    os.chmod(item, 0o777)
                    shutil.rmtree(item)
                removed += 1
            else:
                removed += walk_through_pycache(item, dry_run)
    return removed

def main():
    parser = argparse.ArgumentParser(
        description="Remove all __pycache__ directories recursively.",
        epilog="Example: %(prog)s --path ./src --dry-run"
    )
    parser.add_argument(
        "--path", type=Path,
        default=Path(__file__).parent.parent,
        help="Root directory to start searching (default: project root)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be removed without actually deleting"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print detailed output (currently only shows each removal)"
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"Error: path '{args.path}' does not exist.")
        sys.exit(1)

    removed = walk_through_pycache(args.path, args.dry_run)
    print(f"Total __pycache__ directories removed: {removed}")

if __name__ == "__main__":
    main()