import sys
import os
import json
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory (parent of lunaengine/)."""
    # This file is at lunaengine/tools/split_themes.py
    # So project root is two levels up
    return Path(__file__).parent.parent.parent

def get_themes_json() -> Path:
    """Path to themes.json in lunaengine/ui/"""
    return get_project_root() / "lunaengine" / "ui" / "themes.json"

def get_themes_output_dir() -> Path:
    """Output directory for individual theme JSON files."""
    return get_project_root() / "lunaengine" / "assets" / "themes"

def create_theme(theme_name: str, theme: dict):
    """Write a single theme to a JSON file (minified)."""
    output_dir = get_themes_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = theme_name.replace(" ", "_").upper()
    output_path = output_dir / f"{safe_name}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(theme, f, separators=(',', ':'))
    print(f"  Created: {output_path}")

def main():
    themes_json_path = get_themes_json()
    if not themes_json_path.exists():
        print(f"ERROR: themes.json not found at {themes_json_path}")
        sys.exit(1)
    
    print(f"Loading themes from: {themes_json_path}")
    with open(themes_json_path, 'r', encoding='utf-8') as f:
        themes = json.load(f)
    
    print(f"Found {len(themes)} themes. Splitting...")
    for theme_name, theme_data in themes.items():
        new_theme = {
            'themeName': theme_name,
            'themeDescription': 'No description provided.',
        }
        for key, rgb_list in theme_data.items():
            # rgb_list is e.g. [70, 130, 180]
            new_theme[key] = {
                "cornerRadius": 0,
                "borderWidth": 0,
                "color": [*rgb_list, 0.0],  # RGB + alpha (float)
                "blur": 0
            }
        create_theme(theme_name, new_theme)
    
    print(f"All themes split successfully into {get_themes_output_dir()}")

if __name__ == '__main__':
    main()