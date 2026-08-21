#!/usr/bin/env python3
"""
Unified Theme Tool for LunaEngine.
Subcommands:
  compile    – Merge individual theme JSONs into a single themes.json
  uncompile  – Split themes.json back into separate theme files
  fix-shadows – Add shadow properties to all theme variants
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Literal, Tuple

ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent
DEFAULT_THEMES_PATH = ROOT / "assets" / "themes"
DEFAULT_OUTPUT = ROOT / "themes.json"


def get_shadow_for_variant(mode: Literal["dark", "light"], base_color: Tuple[int, int, int, float]) -> Dict:
    """Generate shadow dict from variant mode and base colour."""
    if mode == "dark":
        factors = (0.65, 0.65, 0.65, 0.8)
    else:
        factors = (0.7, 0.7, 0.7, 0.5)

    r, g, b, a = base_color
    new_color = (int(r * factors[0]), int(g * factors[1]), int(b * factors[2]))
    alpha = factors[3] * a
    return {
        "distance": 2,
        "color": new_color,
        "alpha": alpha,
        "direction": [0.0, 0.0, 1.0, 1.0]
    }


def compile_themes(themes_path: Path, output_path: Path, compact: bool = False):
    """Compile all theme JSON files into a single themes.json."""
    if not themes_path.exists():
        raise FileNotFoundError(f"Themes path '{themes_path}' does not exist.")

    themes_data = {
        "output_path": str(output_path),
        "compact_themes": compact,
        "themes_path": str(themes_path),
        "themes": {},
        "total_themes": 0
    }

    for theme_file in themes_path.glob("*.json"):
        print(f"Compiling: {theme_file.name}")
        data = json.loads(theme_file.read_text(encoding="utf-8"))
        themes_data["themes"][theme_file.name.upper()] = {
            "name": theme_file.name,
            "path": str(theme_file),
            "data": data
        }

    themes_data["total_themes"] = len(themes_data["themes"])

    indent = None if compact else 4
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(themes_data, f, indent=indent, ensure_ascii=False, separators=(",", ":"))
    print(f"✅ Compiled {themes_data['total_themes']} themes to '{output_path}'")


def uncompile_themes(input_path: Path, themes_path: Path, compact: bool = False):
    """Split a themes.json into separate theme files."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input '{input_path}' not found.")
    if not themes_path.exists():
        themes_path.mkdir(parents=True, exist_ok=True)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    total = data.get("total_themes", 0)
    print(f"Uncompiling {total} themes from '{input_path}'")

    for key, entry in data.get("themes", {}).items():
        print(f"  Writing: {entry['name']}")
        try:
            out_file = Path(entry["path"]) if entry.get("path") else themes_path / entry["name"]
            indent = None if compact else 4
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(entry["data"], f, indent=indent, ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            print(f"  ⚠️ Skipping {entry['name']}: {e}")


def fix_shadows(input_path: Path, output_path: Path):
    """Add shadow properties to every style entry in all themes."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input '{input_path}' not found.")

    data = json.loads(input_path.read_text(encoding="utf-8"))

    for theme_entry in data.get("themes", {}).values():
        variants = theme_entry.get("data", {}).get("variants", {})
        mode = theme_entry.get("data", {}).get("mode", "light")
        for variant_data in variants.values():
            for style_props in variant_data.values():
                if isinstance(style_props, dict) and "color" in style_props:
                    style_props["shadow"] = get_shadow_for_variant(mode, style_props["color"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ Fixed shadows saved to '{output_path}'")


def main():
    parser = argparse.ArgumentParser(description="LunaEngine Theme Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compile
    compile_parser = subparsers.add_parser("compile", help="Compile themes")
    compile_parser.add_argument("-i", "--input", dest="input_path", type=Path, default=DEFAULT_THEMES_PATH,
                                help="Path to folder containing theme JSONs")
    compile_parser.add_argument("-o", "--output", dest="output_path", type=Path, default=DEFAULT_OUTPUT,
                                help="Output path for themes.json")
    compile_parser.add_argument("-c", "--compact", action="store_true", help="Compact output (no indentation)")

    # uncompile
    uncompile_parser = subparsers.add_parser("uncompile", help="Uncompile themes")
    uncompile_parser.add_argument("-i", "--input", dest="input_path", type=Path, default=DEFAULT_OUTPUT,
                                  help="Path to themes.json")
    uncompile_parser.add_argument("-o", "--output", dest="output_path", type=Path, default=DEFAULT_THEMES_PATH,
                                  help="Output folder for individual theme files")
    uncompile_parser.add_argument("-c", "--compact", action="store_true", help="Compact output (no indentation)")

    # fix-shadows
    fix_parser = subparsers.add_parser("fix-shadows", help="Add shadow properties to themes")
    fix_parser.add_argument("-i", "--input", dest="input_path", type=Path, default=DEFAULT_OUTPUT,
                            help="Path to themes.json")
    fix_parser.add_argument("-o", "--output", dest="output_path", type=Path, default=DEFAULT_OUTPUT,
                            help="Output path (default: overwrite input)")

    args = parser.parse_args()

    if args.command == "compile":
        compile_themes(args.input_path, args.output_path, args.compact)
    elif args.command == "uncompile":
        uncompile_themes(args.input_path, args.output_path, args.compact)
    elif args.command == "fix-shadows":
        fix_shadows(args.input_path, args.output_path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()