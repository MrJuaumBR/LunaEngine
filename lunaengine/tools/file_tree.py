#!/usr/bin/env python3
"""
LunaEngine File Tree Exporter
Generates a text-based tree of the project structure, ignoring specified
directories and files. Useful for sharing context with LLMs/AIs.
"""

import argparse
import fnmatch
import sys
from pathlib import Path
from typing import List, Set

# Default blacklists (same as in code_stats.py)
DEFAULT_IGNORE_DIRS = {
    "__pycache__",
    ".git",
    "build",
    "dist",
    "venv",
    "env",
    ".vscode",
    ".idea",
}
DEFAULT_IGNORE_FILE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
}


def should_ignore(
    path: Path,
    ignore_dirs: Set[str],
    ignore_file_patterns: Set[str],
) -> bool:
    """Return True if the path should be excluded."""
    if path.is_dir():
        return path.name in ignore_dirs
    # For files, check if the name matches any pattern
    for pattern in ignore_file_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return True
    return False


def generate_tree_lines(
    root: Path,
    prefix: str = "",
    ignore_dirs: Set[str] = DEFAULT_IGNORE_DIRS,
    ignore_file_patterns: Set[str] = DEFAULT_IGNORE_FILE_PATTERNS,
    max_depth: int = -1,
    current_depth: int = 0,
) -> List[str]:
    """
    Recursively build the tree as a list of strings.
    Directories are listed first, then files (both sorted alphabetically).
    """
    if max_depth != -1 and current_depth > max_depth:
        return []

    lines = []
    # Gather all items in the directory, filtering ignored ones
    items = []
    for item in sorted(root.iterdir()):
        if should_ignore(item, ignore_dirs, ignore_file_patterns):
            continue
        items.append(item)

    # Separate directories and files for consistent ordering
    dirs = [i for i in items if i.is_dir()]
    files = [i for i in items if i.is_file()]

    # Process directories first
    for i, dir_path in enumerate(dirs):
        is_last = (i == len(dirs) - 1) and not files
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + dir_path.name + "/")
        # Recurse into subdirectory
        new_prefix = prefix + ("    " if is_last else "│   ")
        lines.extend(
            generate_tree_lines(
                dir_path,
                new_prefix,
                ignore_dirs,
                ignore_file_patterns,
                max_depth,
                current_depth + 1,
            )
        )

    # Then files
    for i, file_path in enumerate(files):
        is_last = (i == len(files) - 1)
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + file_path.name)

    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Generate a file tree of the project structure.",
        epilog="Example: %(prog)s --output tree.txt --depth 3",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Root directory to start from (default: project root)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Write tree to a file instead of stdout",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=-1,
        help="Maximum depth to traverse (-1 for unlimited)",
    )
    parser.add_argument(
        "--ignore-dirs",
        nargs="+",
        default=DEFAULT_IGNORE_DIRS,
        help="Additional directory names to ignore (space separated)",
    )
    parser.add_argument(
        "--ignore-files",
        nargs="+",
        default=DEFAULT_IGNORE_FILE_PATTERNS,
        help="Additional file patterns to ignore (e.g. '*.tmp')",
    )
    parser.add_argument(
        "--no-default-ignore",
        action="store_true",
        help="Do not use default ignore lists (only use custom ones)",
    )
    args = parser.parse_args()

    # Determine final ignore sets
    ignore_dirs = set()
    ignore_file_patterns = set()
    if not args.no_default_ignore:
        ignore_dirs.update(DEFAULT_IGNORE_DIRS)
        ignore_file_patterns.update(DEFAULT_IGNORE_FILE_PATTERNS)
    if args.ignore_dirs:
        ignore_dirs.update(args.ignore_dirs)
    if args.ignore_files:
        ignore_file_patterns.update(args.ignore_files)

    root = args.path.resolve()
    if not root.exists():
        print(f"Error: path '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Build the tree
    tree_lines = [str(root) + "/"]
    tree_lines.extend(
        generate_tree_lines(
            root,
            "",
            ignore_dirs,
            ignore_file_patterns,
            args.depth,
            1,  # start at depth 1 because root line is already added
        )
    )

    output_text = "\n".join(tree_lines)

    if args.output:
        args.output.write_text(output_text, encoding="utf-8")
        print(f"Tree written to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()