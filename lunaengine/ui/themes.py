"""
themes.py - UI Themes Manager for LunaEngine

ENGINE PATH:
lunaengine -> ui -> themes.py

DESCRIPTION:
This module manages comprehensive UI themes with predefined color schemes
for various applications and visual styles. It includes a wide range of
themes from basic functional ones to brand-specific and aesthetic designs.

MAIN FEATURES:
- Tries to load themes from local themes.json file
- If not found, tries to download from GitHub
- Fallback to default theme if everything fails
"""

from enum import Enum
from typing import Dict, Tuple, Optional, List, Literal
from dataclasses import dataclass
import os
import json
import urllib.request
import urllib.error

# color_name is for typing in the get_color function
color_name_type = Literal['button_normal', 'button_hover', 'button_pressed', 'button_disabled', 
                     'button_text', 'button_border',
                     'dropdown_normal', 'dropdown_hover', 'dropdown_expanded', 'dropdown_text',
                     'dropdown_option_normal', 'dropdown_option_hover', 'dropdown_option_selected',
                     'dropdown_border',
                     'slider_track', 'slider_thumb_normal', 'slider_thumb_hover', 'slider_thumb_pressed',
                     'slider_text',
                     'label_text',
                     'background', 'background2', 'text_primary', 'text_secondary', 'border', 'border2',
                     'switch_track_on', 'switch_track_off', 'switch_thumb_on', 'switch_thumb_off',
                     'dialog_background', 'dialog_border', 'dialog_text', 'dialog_name_bg', 'dialog_name_text', 'dialog_continue_indicator',
                     'tooltip_background', 'tooltip_border', 'tooltip_text',
                     # New notification colors
                     'notification_success_background', 'notification_success_border', 'notification_success_text',
                     'notification_info_background', 'notification_info_border', 'notification_info_text',
                     'notification_warning_background', 'notification_warning_border', 'notification_warning_text',
                     'notification_custom_background', 'notification_custom_border', 'notification_custom_text',
                     'notification_error_background', 'notification_error_border', 'notification_error_text',
                     # New accent colors
                     'accent1', 'accent2']

@dataclass
class UITheme:
    """Complete UI theme configuration for all elements"""
    # Button colors
    button_normal: Tuple[int, int, int]
    button_hover: Tuple[int, int, int]
    button_pressed: Tuple[int, int, int]
    button_disabled: Tuple[int, int, int]
    button_text: Tuple[int, int, int]
    
    # Dropdown colors
    dropdown_normal: Tuple[int, int, int]
    dropdown_hover: Tuple[int, int, int]
    dropdown_expanded: Tuple[int, int, int]
    dropdown_text: Tuple[int, int, int]
    dropdown_option_normal: Tuple[int, int, int]
    dropdown_option_hover: Tuple[int, int, int]
    dropdown_option_selected: Tuple[int, int, int]
    
    # Slider colors
    slider_track: Tuple[int, int, int]
    slider_thumb_normal: Tuple[int, int, int]
    slider_thumb_hover: Tuple[int, int, int]
    slider_thumb_pressed: Tuple[int, int, int]
    slider_text: Tuple[int, int, int]
    
    # TextLabel colors
    label_text: Tuple[int, int, int]
    
    # General UI colors
    background: Tuple[int, int, int]
    background2: Tuple[int, int, int]
    text_primary: Tuple[int, int, int]
    text_secondary: Tuple[int, int, int]
    
    # Switch colors
    switch_track_on: Tuple[int, int, int]
    switch_track_off: Tuple[int, int, int]
    switch_thumb_on: Tuple[int, int, int]
    switch_thumb_off: Tuple[int, int, int]
    
    # Dialog colors
    dialog_background: Tuple[int, int, int]
    dialog_border: Tuple[int, int, int]
    dialog_text: Tuple[int, int, int]
    dialog_name_bg: Tuple[int, int, int]
    dialog_name_text: Tuple[int, int, int]
    dialog_continue_indicator: Tuple[int, int, int]
    
    # Tooltips colors
    tooltip_background: Tuple[int, int, int]
    tooltip_border: Tuple[int, int, int]
    tooltip_text: Tuple[int, int, int]
    
    # Notification colors
    notification_success_background: Tuple[int, int, int]
    notification_success_border: Tuple[int, int, int]
    notification_success_text: Tuple[int, int, int]
    notification_info_background: Tuple[int, int, int]
    notification_info_border: Tuple[int, int, int]
    notification_info_text: Tuple[int, int, int]
    notification_warning_background: Tuple[int, int, int]
    notification_warning_border: Tuple[int, int, int]
    notification_warning_text: Tuple[int, int, int]
    notification_custom_background: Tuple[int, int, int]
    notification_custom_border: Tuple[int, int, int]
    notification_custom_text: Tuple[int, int, int]
    notification_error_background: Tuple[int, int, int]
    notification_error_border: Tuple[int, int, int]
    notification_error_text: Tuple[int, int, int]
    
    # Accent colors
    accent1: Tuple[int, int, int]
    accent2: Tuple[int, int, int]
    
    # Optional fields with defaults
    button_border: Optional[Tuple[int, int, int]] = None
    dropdown_border: Optional[Tuple[int, int, int]] = None
    border: Optional[Tuple[int, int, int]] = None
    border2: Optional[Tuple[int, int, int]] = None

class ThemeType(Enum):
    """Enumeration of all available theme types"""
    DEFAULT = "default"
    
    # Basic themes
    PRIMARY = "primary"
    SECONDARY = "secondary"
    WARN = "warn"
    ERROR = "error"
    SUCCESS = "success"
    INFO = "info"
    
    # Fantasy themes
    FANTASY_DARK = "fantasy_dark"
    FANTASY_LIGHT = "fantasy_light"
    
    # Cherry themes
    CHERRY_DARK = "cherry_dark"
    CHERRY_LIGHT = "cherry_light"
    
    # Eclipse theme
    ECLIPSE = "eclipse"
    
    # Midnight themes
    MIDNIGHT_DARK = "midnight_dark"
    MIDNIGHT_LIGHT = "midnight_light"
    
    # Neon theme
    NEON = "neon"
    
    # Gemstone themes
    RUBY = "ruby"
    EMERALD = "emerald"
    DIAMOND = "diamond"
    
    # Metal themes
    SILVER = "silver"
    COPPER = "copper"
    BRONZE = "bronze"
    
    # Aesthetic themes
    AZURE = "azure"
    EIGHTIES = "80s"
    CLOUDS = "clouds"
    
    # Platform themes
    ROBLOX = "roblox"
    DISCORD = "discord"
    GMAIL = "gmail"
    YOUTUBE = "youtube"
    STEAM_DARK = "steam_dark"
    STEAM_LIGHT = "steam_light"
    
    QUEEN = "queen"
    KING = "king"
    
    # Special themes
    MATRIX = "matrix"
    BUILDER = "builder"
    GALAXY_DARK = "galaxy_dark"
    GALAXY_LIGHT = "galaxy_light"
    
    # Nature themes
    FOREST = "forest"
    SUNSET = "sunset"
    OCEAN = "ocean"
    LAVENDER = "lavender"
    CHOCOLATE = "chocolate"
    KIWI = "kiwi"
    
    # Popular color scheme themes
    DEEP_SPACE = "deep_space"
    NORD_DARK = "nord_dark"
    NORD_LIGHT = "nord_light"
    DRACULA = "dracula"
    SOLARIZED_DARK = "solarized_dark"
    SOLARIZED_LIGHT = "solarized_light"
    MONOKAI = "monokai"
    GRUVBOX_DARK = "gruvbox_dark"
    GRUVBOX_LIGHT = "gruvbox_light"
    
    # Ninja themes
    NINJA_DARK = "ninja_dark"
    NINJA_LIGHT = "ninja_light"
    
    # Country themes
    BRAZIL = "brazil"
    JAPAN = "japan"
    USA = "usa"
    EUROPEAN = "european"
    
    # Historical themes
    DYNASTY = "dynasty"
    VIKINGS = "vikings"


class ThemeManager:
    """Manages complete UI themes with local/remote loading"""
    
    _themes: Dict[ThemeType, UITheme] = {}
    _current_theme: ThemeType = ThemeType.DEFAULT
    _themes_loaded: bool = False
    
    # GitHub URL to download themes.json
    GITHUB_THEMES_URL = "https://raw.githubusercontent.com/MrJuaumBR/LunaEngine/refs/heads/main/lunaengine/ui/themes.json"
    
    @classmethod
    def _get_themes_file_path(cls) -> str:
        """Get the path to themes.json file (cross-platform)"""
        # Get the directory where themes.py is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "themes.json")
    
    @classmethod
    def _download_from_github(cls) -> Optional[dict]:
        """Download themes.json from GitHub"""
        try:
            print(f"🌐 Trying to download themes from GitHub: {cls.GITHUB_THEMES_URL}")
            
            # Add headers to avoid blocking
            headers = {
                'User-Agent': 'LunaEngine/1.0 (https://github.com/MrJuaumBR/LunaEngine)'
            }
            
            req = urllib.request.Request(cls.GITHUB_THEMES_URL, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = response.read()
                    themes_data = json.loads(data.decode('utf-8'))
                    print(f"Themes downloaded successfully from GitHub ({len(themes_data)} themes)")
                    return themes_data
                else:
                    print(f"/ Download failed: Status {response.status}")
                    return None
                    
        except urllib.error.URLError as e:
            print(f"/ URL error downloading from GitHub: {e}")
            return None
        except urllib.error.HTTPError as e:
            print(f"/ HTTP error downloading from GitHub: {e.code} - {e.reason}")
            return None
        except json.JSONDecodeError as e:
            print(f"/ Error decoding JSON from GitHub: {e}")
            return None
        except Exception as e:
            print(f"/ Unexpected error downloading from GitHub: {e}")
            return None
    
    @classmethod
    def _save_themes_to_cache(cls, themes_data: dict) -> bool:
        """Save downloaded themes to local cache"""
        try:
            cache_path = cls._get_themes_file_path()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(themes_data, f, indent=2)
            
            print(f"Themes saved to local cache: {cache_path}")
            return True
            
        except Exception as e:
            print(f"! Could not save local cache: {e}")
            return False
    
    @classmethod
    def _load_themes_from_json(cls):
        """Load themes from JSON file or GitHub"""
        themes_data = None
        
        # 1. Try to load from local file
        themes_file = cls._get_themes_file_path()
        
        if os.path.exists(themes_file):
            try:
                with open(themes_file, 'r', encoding='utf-8') as f:
                    themes_data = json.load(f)
                print(f"Themes loaded from local file: {themes_file}")
            except Exception as e:
                print(f"! Error loading local file: {e}")
                themes_data = None
        
        # 2. If not found locally, try to download from GitHub
        if themes_data is None:
            themes_data = cls._download_from_github()
            
            # 3. If downloaded successfully, save as cache
            if themes_data:
                cls._save_themes_to_cache(themes_data)
        
        # 4. If data was loaded, process it
        if themes_data:
            cls._process_themes_data(themes_data)
        else:
            # 5. Fallback to default theme
            print("! Could not load themes. Using fallback theme.")
            cls._create_fallback_theme()
    
    @classmethod
    def _process_themes_data(cls, themes_data: dict):
        """Process themes data from dictionary"""
        loaded_count = 0
        
        for theme_name, theme_dict in themes_data.items():
            try:
                # Convert theme name to ThemeType
                theme_type = None
                for t in ThemeType:
                    if t.name == theme_name:
                        theme_type = t
                        break
                
                if theme_type is None:
                    print(f"! Unknown theme type: '{theme_name}'")
                    continue
                
                # Convert list to tuple for color values and handle None values
                processed_theme = {}
                for key, value in theme_dict.items():
                    if value is None:
                        processed_theme[key] = None
                    elif isinstance(value, list) and len(value) == 3:
                        processed_theme[key] = tuple(value)
                    else:
                        processed_theme[key] = value
                
                # Create UITheme instance
                theme = UITheme(**processed_theme)
                cls._themes[theme_type] = theme
                loaded_count += 1
                
            except Exception as e:
                print(f"/ Error processing theme '{theme_name}': {e}")
        
        cls._themes_loaded = True
        print(f"{loaded_count} themes loaded successfully")
        
        # Ensure DEFAULT theme is loaded
        if ThemeType.DEFAULT not in cls._themes:
            print("! DEFAULT theme not found. Creating fallback...")
            cls._create_fallback_theme()
    
    @classmethod
    def _create_fallback_theme(cls):
        """Create a simple fallback theme if loading fails"""
        fallback_theme = UITheme(
            button_normal=(70, 130, 180),
            button_hover=(50, 110, 160),
            button_pressed=(30, 90, 140),
            button_disabled=(120, 120, 120),
            button_text=(255, 255, 255),
            button_border=(100, 150, 200),
            dropdown_normal=(90, 90, 110),
            dropdown_hover=(110, 110, 130),
            dropdown_expanded=(100, 100, 120),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(70, 70, 90),
            dropdown_option_hover=(80, 80, 100),
            dropdown_option_selected=(90, 90, 110),
            dropdown_border=(150, 150, 170),
            slider_track=(80, 80, 80),
            slider_thumb_normal=(200, 100, 100),
            slider_thumb_hover=(220, 120, 120),
            slider_thumb_pressed=(180, 80, 80),
            slider_text=(255, 255, 255),
            label_text=(240, 240, 240),
            background=(50, 50, 70),
            background2=(40, 40, 60),
            text_primary=(240, 240, 240),
            text_secondary=(200, 200, 200),
            switch_track_on=(0, 200, 0),
            switch_track_off=(80, 80, 80),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(220, 220, 220),
            dialog_background=(60, 60, 80),
            dialog_border=(120, 120, 140),
            dialog_text=(240, 240, 240),
            dialog_name_bg=(70, 130, 180),
            dialog_name_text=(255, 255, 255),
            dialog_continue_indicator=(200, 200, 200),
            tooltip_background=(40, 40, 60),
            tooltip_border=(100, 100, 120),
            tooltip_text=(240, 240, 240),
            border=(120, 120, 140),
            border2=(100, 100, 120),
            # New notification colors
            notification_success_background=(40, 167, 69),
            notification_success_border=(20, 147, 49),
            notification_success_text=(255, 255, 255),
            notification_info_background=(23, 162, 184),
            notification_info_border=(3, 142, 164),
            notification_info_text=(255, 255, 255),
            notification_warning_background=(255, 193, 7),
            notification_warning_border=(235, 173, 0),
            notification_warning_text=(0, 0, 0),
            notification_custom_background=(147, 112, 219),
            notification_custom_border=(127, 92, 199),
            notification_custom_text=(255, 255, 255),
            notification_error_background=(220, 53, 69),
            notification_error_border=(200, 33, 49),
            notification_error_text=(255, 255, 255),
            # New accent colors
            accent1=(70, 130, 180),  # Steel blue
            accent2=(255, 193, 7)    # Golden yellow
        )
        cls._themes[ThemeType.DEFAULT] = fallback_theme
        cls._themes_loaded = True
        print("Fallback theme created")
    
    @classmethod
    def ensure_themes_loaded(cls):
        """Ensure themes are loaded from JSON or GitHub"""
        if not cls._themes_loaded:
            cls._load_themes_from_json()
    
    @classmethod
    def get_theme_by_name(cls, name: str) -> UITheme:
        """Get theme by name string"""
        cls.ensure_themes_loaded()
        theme_type = cls.get_theme_type_by_name(name)
        return cls._themes.get(theme_type, cls._themes[ThemeType.DEFAULT])
    
    @classmethod
    def get_theme_type_by_name(cls, name: str) -> ThemeType:
        """Get theme type by name string"""
        cls.ensure_themes_loaded()
        for theme_type in ThemeType:
            if theme_type.value.lower() == name.lower():
                return theme_type
        return ThemeType.DEFAULT
    
    @classmethod
    def get_theme(cls, theme_type: ThemeType) -> UITheme:
        """Get complete theme by type"""
        cls.ensure_themes_loaded()
        return cls._themes.get(theme_type, cls._themes[ThemeType.DEFAULT])
    
    @classmethod
    def set_theme(cls, theme_type: ThemeType, theme: UITheme):
        """Set or override a theme"""
        cls._themes[theme_type] = theme
    
    @classmethod
    def set_current_theme(cls, theme_type: ThemeType):
        """Set the current default theme"""
        cls._current_theme = theme_type
    
    @classmethod
    def get_current_theme(cls) -> ThemeType:
        """Get current default theme"""
        return cls._current_theme
    
    @classmethod
    def get_themes(cls) -> Dict[ThemeType, UITheme]:
        """Get all available themes"""
        cls.ensure_themes_loaded()
        return cls._themes
    
    @classmethod
    def get_theme_types(cls) -> List[ThemeType]:
        """Get all available theme types"""
        cls.ensure_themes_loaded()
        return list(cls._themes.keys())
    
    @classmethod
    def get_theme_names(cls) -> List[str]:
        """Get all available theme names"""
        cls.ensure_themes_loaded()
        return [theme.value for theme in cls._themes.keys()]
    
    @classmethod
    def get_color(cls, color_name: color_name_type) -> Tuple[int, int, int]:
        """Get a specific color from the current theme"""
        cls.ensure_themes_loaded()
        theme = cls.get_theme(cls._current_theme)
        if theme is None: 
            return (0, 0, 0)
        elif getattr(theme, color_name, None) is None: 
            return (0, 0, 0)
        else: 
            return getattr(theme, color_name)
    
    @classmethod
    def reload_themes(cls):
        """Force reload themes from source"""
        cls._themes.clear()
        cls._themes_loaded = False
        cls.ensure_themes_loaded()
        print("Themes reloaded.")
    
    @classmethod
    def get_loaded_count(cls) -> int:
        """Get number of loaded themes"""
        cls.ensure_themes_loaded()
        return len(cls._themes)
    
    @classmethod
    def is_theme_available(cls, theme_name: str) -> bool:
        """Check if a theme is available by name"""
        cls.ensure_themes_loaded()
        for theme_type in cls._themes.keys():
            if theme_type.value.lower() == theme_name.lower():
                return True
        return False


# Initialize themes on module import
ThemeManager.ensure_themes_loaded()