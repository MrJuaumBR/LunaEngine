import json
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lunaengine.ui.themes import ThemeManager, ThemeType

file_arg = sys.argv[1] if len(sys.argv) > 1 else None
themes_file = file_arg if file_arg else os.path.join(os.path.dirname(__file__), 'themes.json')

def convert_themes_to_json():
    """Convert all current themes to JSON format"""
    
    # Ensure themes are initialized
    ThemeManager.initialize_default_themes()
    
    # Get all themes
    themes = ThemeManager.get_themes()
    
    # Convert to JSON-serializable format
    json_themes = {}
    
    for theme_type, theme in themes.items():
        theme_dict = {}
        for field_name, field_value in theme.__dict__.items():
            if field_value is None:
                theme_dict[field_name] = None
            elif isinstance(field_value, tuple):
                theme_dict[field_name] = list(field_value)
            else:
                theme_dict[field_name] = field_value
        json_themes[theme_type.name] = theme_dict
    
    # Save to JSON file
    
    with open(themes_file, 'w', encoding='utf-8') as f:
        json.dump(json_themes, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {len(json_themes)} themes to {themes_file}")

if __name__ == "__main__":
    convert_themes_to_json()