"""
themes.py - UI Themes Manager for LunaEngine

ENGINE PATH:
lunaengine -> ui -> themes.py

DESCRIPTION:
This module manages comprehensive UI themes with predefined color schemes
for various applications and visual styles. It includes a wide range of
themes from basic functional ones to brand-specific and aesthetic designs.

LIBRARIES USED:
- enum: For theme type definitions
- typing: For type hints and type annotations
- dataclasses: For structured theme data storage

MAIN CLASSES:

1. UITheme (dataclass):
   - Complete UI theme configuration for all elements
   - Defines colors for buttons, dropdowns, sliders, labels, and general UI
   - Supports optional border colors for different elements
   - Now includes background2 for better contrast

2. ThemeType (Enum):
   - Comprehensive enumeration of available theme types including:
     - Basic: DEFAULT, PRIMARY, SECONDARY, WARN, ERROR, SUCCESS, INFO
     - Fantasy: FANTASY_DARK, FANTASY_LIGHT
     - Cherry: CHERRY_DARK, CHERRY_LIGHT
     - Gemstones: RUBY, EMERALD, DIAMOND
     - Metals: SILVER, COPPER, BRONZE
     - Brand: ROBLOX, DISCORD, GMAIL, YOUTUBE
     - Aesthetic: AZURE, EIGHTIES, CLOUDS, QUEEN, KING
     - New: FOREST, SUNSET, OCEAN, MATRIX, LAVENDER, CHOCOLATE
     - New Dark/Light: DEEP_SPACE, NORD, DRACULA, SOLARIZED, MONOKAI, GRUVBOX

3. ThemeManager:
   - Manages theme registration, retrieval, and application
   - Provides access to predefined themes
   - Handles current theme state management
   - Supports theme customization and overrides

This module provides a rich theming system with over 20 predefined color schemes
suitable for various application types and visual preferences.
"""

from enum import Enum
from typing import Dict, Tuple, Optional, List, Literal
from dataclasses import dataclass
import os, json

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
                     'tooltip_background', 'tooltip_border', 'tooltip_text']

@dataclass
class UITheme:
    """Complete UI theme configuration for all elements"""
    # Button colors (no defaults)
    button_normal: Tuple[int, int, int]
    button_hover: Tuple[int, int, int]
    button_pressed: Tuple[int, int, int]
    button_disabled: Tuple[int, int, int]
    button_text: Tuple[int, int, int]
    
    # Dropdown colors (no defaults)
    dropdown_normal: Tuple[int, int, int]
    dropdown_hover: Tuple[int, int, int]
    dropdown_expanded: Tuple[int, int, int]
    dropdown_text: Tuple[int, int, int]
    dropdown_option_normal: Tuple[int, int, int]
    dropdown_option_hover: Tuple[int, int, int]
    dropdown_option_selected: Tuple[int, int, int]
    
    # Slider colors (no defaults)
    slider_track: Tuple[int, int, int]
    slider_thumb_normal: Tuple[int, int, int]
    slider_thumb_hover: Tuple[int, int, int]
    slider_thumb_pressed: Tuple[int, int, int]
    slider_text: Tuple[int, int, int]
    
    # TextLabel colors (no defaults)
    label_text: Tuple[int, int, int]
    
    # General UI colors (no defaults)
    background: Tuple[int, int, int]
    background2: Tuple[int, int, int]  # Nova variável para contraste
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
    
    # Optional fields with defaults (must come last)
    button_border: Optional[Tuple[int, int, int]] = None
    dropdown_border: Optional[Tuple[int, int, int]] = None
    border: Optional[Tuple[int, int, int]] = None
    border2: Optional[Tuple[int, int, int]] = None

class ThemeType(Enum):
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
    
    # gemstone themes
    RUBY = "ruby"
    EMERALD = "emerald"
    DIAMOND = "diamond"
    
    # metal themes
    SILVER = "silver"
    COPPER = "copper"
    BRONZE = "bronze"
    
    AZURE = "azure"
    EIGHTIES = "80s"
    CLOUDS = "clouds"
    
    # Platforms themes
    ROBLOX = "roblox"
    DISCORD = "discord"
    GMAIL = "gmail"
    YOUTUBE = "youtube"
    STEAM_DARK = "steam_dark"
    STEAM_LIGHT = "steam_light"
    
    QUEEN = "queen"
    KING = "king"
    
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
    
    # Country Themes
    BRAZIL = "brazil"
    JAPAN = "japan"
    USA = "usa"
    EUROPEAN = "european"
    
    DYNASTY = "dynasty"
    VIKINGS = "vikings"


class ThemeManager:
    """Manages complete UI themes"""
    
    _themes: Dict[ThemeType, UITheme] = {}
    _current_theme: ThemeType = ThemeType.DEFAULT
    _themes_loaded: bool = False
        
    @classmethod
    def _get_themes_file_path(cls) -> str:
        """Get the path to themes.json file (cross-platform)"""
        # Get the directory where themes.py is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "themes.json")
    
    @classmethod
    def _load_themes_from_json(cls):
        """Load themes from JSON file"""
        try:
            themes_file = cls._get_themes_file_path()
            
            if not os.path.exists(themes_file):
                raise FileNotFoundError(f"Themes file not found: {themes_file}")
            
            with open(themes_file, 'r', encoding='utf-8') as f:
                themes_data = json.load(f)
            
            for theme_name, theme_dict in themes_data.items():
                try:
                    # Convert theme name to ThemeType
                    theme_type = None
                    for t in ThemeType:
                        if t.name == theme_name:
                            theme_type = t
                            break
                    
                    if theme_type is None:
                        print(f"Warning: Unknown theme type '{theme_name}' in JSON file")
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
                    
                except Exception as e:
                    print(f"Error loading theme '{theme_name}': {e}")
            
            cls._themes_loaded = True
            print(f"Successfully loaded {len(cls._themes)} themes from JSON")
            
        except Exception as e:
            print(f"Error loading themes from JSON: {e}")
            # Fallback to default theme
            cls._create_fallback_theme()
    
    @classmethod
    def _create_fallback_theme(cls):
        """Create a simple fallback theme if JSON loading fails"""
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
            # New dialog colors
            dialog_background=(60, 60, 80),
            dialog_border=(120, 120, 140),
            dialog_text=(240, 240, 240),
            dialog_name_bg=(70, 130, 180),
            dialog_name_text=(255, 255, 255),
            dialog_continue_indicator=(200, 200, 200),
            # New tooltip colors
            tooltip_background=(40, 40, 60),
            tooltip_border=(100, 100, 120),
            tooltip_text=(240, 240, 240),
            border=(120, 120, 140),
            border2=(100, 100, 120)
        )
        cls._themes[ThemeType.DEFAULT] = fallback_theme
        cls._themes_loaded = True
    
    @classmethod
    def ensure_themes_loaded(cls):
        """Ensure themes are loaded from JSON"""
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
    def get_theme_by_name(cls, name: str) -> UITheme:
        """Get theme by name string"""
        if not cls._themes:
            cls.initialize_default_themes()
        return cls._themes.get(name, cls._themes[ThemeType.PRIMARY])
    
    @classmethod
    def get_theme_type_by_name(cls, name: str) -> ThemeType:
        """Get theme type by name string"""
        if not cls._themes:
            cls.initialize_default_themes()
        for theme_type in ThemeType:
            if theme_type.value.lower() == name.lower():
                return theme_type
        return ThemeType.PRIMARY
    
    @classmethod
    def get_theme(cls, theme_type: ThemeType) -> UITheme:
        """Get complete theme by type"""
        if not cls._themes:
            cls.initialize_default_themes()
        return cls._themes.get(theme_type, cls._themes[ThemeType.PRIMARY])
    
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
        if not cls._themes:
            cls.initialize_default_themes()
        return cls._themes
    
    @classmethod
    def get_theme_types(cls) -> List[ThemeType]:
        """Get all available theme types"""
        if not cls._themes:
            cls.initialize_default_themes()
        return list(cls._themes.keys())
    
    @classmethod
    def get_theme_names(cls) -> List[str]:
        """Get all available theme names"""
        if not cls._themes:
            cls.initialize_default_themes()
        return [theme.value for theme in cls._themes.keys()]
    
    @classmethod
    def get_color(cls, color_name: color_name_type) -> Tuple[int, int, int]:
        """Get a specific color from the current theme"""
        theme = cls.get_theme(cls._current_theme)
        if theme is None: return (0, 0, 0)
        elif theme.__dict__.get(color_name) is None: return (0, 0, 0)
        else: return getattr(theme, color_name)
        

# Initialize themes

ThemeManager.ensure_themes_loaded()