"""
themes.py - UI Themes Manager for LunaEngine

ENGINE PATH:
lunaengine -> ui -> themes.py

DESCRIPTION:
This module manages comprehensive UI themes with predefined color schemes
for various applications and visual styles. It includes a wide range of
themes from basic functional ones to brand-specific and aesthetic designs.

MAIN FEATURES:
- Loads themes from individual JSON files in lunaengine/assets/themes/
- If directory is empty or missing, falls back to local themes.json
- If still not found, tries to download from GitHub
- Final fallback to default theme
- Supports full theme properties: colors (RGBA), corner radius, border width, blur
"""

from enum import Enum
from typing import Dict, Tuple, Optional, List, Literal, Union
from dataclasses import dataclass, field
import os
import json
import urllib.request
import urllib.error

# color_name is for typing in the get_color function
color_name_type = Literal[
    'button_normal', 'button_hover', 'button_pressed', 'button_disabled',
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
    'notification_success_background', 'notification_success_border', 'notification_success_text',
    'notification_info_background', 'notification_info_border', 'notification_info_text',
    'notification_warning_background', 'notification_warning_border', 'notification_warning_text',
    'notification_custom_background', 'notification_custom_border', 'notification_custom_text',
    'notification_error_background', 'notification_error_border', 'notification_error_text',
    'accent1', 'accent2'
]

@dataclass
class ThemeStyle:
    """Complete style definition for a single UI element state."""
    color: Tuple[int, int, int]      # RGB (0-255)
    alpha: float = 1.0               # 0.0 - 1.0
    corner_radius: int = 0
    border_width: int = 0
    blur: int = 0

    def to_rgb(self) -> Tuple[int, int, int]:
        """Return RGB tuple (alpha ignored)."""
        return self.color

    def to_rgba(self) -> Tuple[int, int, int, int]:
        """Return RGBA tuple with alpha as 0-255."""
        return (self.color[0], self.color[1], self.color[2], int(self.alpha * 255))

    @classmethod
    def from_rgb_list(cls, rgb_list: List[int], alpha: float = 1.0,
                      corner_radius: int = 0, border_width: int = 0, blur: int = 0) -> 'ThemeStyle':
        """Create from a list of 3 or 4 integers."""
        if len(rgb_list) >= 3:
            r, g, b = rgb_list[0], rgb_list[1], rgb_list[2]
            if len(rgb_list) >= 4:
                alpha = rgb_list[3] / 255.0 if isinstance(rgb_list[3], (int, float)) else 1.0
        else:
            r = g = b = 0
        return cls(color=(r, g, b), alpha=alpha,
                   corner_radius=corner_radius, border_width=border_width, blur=blur)


@dataclass
class UITheme:
    """Complete UI theme configuration for all elements."""
    # All required fields first (no default values)
    button_normal: ThemeStyle
    button_hover: ThemeStyle
    button_pressed: ThemeStyle
    button_disabled: ThemeStyle
    button_text: ThemeStyle

    dropdown_normal: ThemeStyle
    dropdown_hover: ThemeStyle
    dropdown_expanded: ThemeStyle
    dropdown_text: ThemeStyle
    dropdown_option_normal: ThemeStyle
    dropdown_option_hover: ThemeStyle
    dropdown_option_selected: ThemeStyle

    slider_track: ThemeStyle
    slider_thumb_normal: ThemeStyle
    slider_thumb_hover: ThemeStyle
    slider_thumb_pressed: ThemeStyle
    slider_text: ThemeStyle

    label_text: ThemeStyle

    background: ThemeStyle
    background2: ThemeStyle
    text_primary: ThemeStyle
    text_secondary: ThemeStyle

    switch_track_on: ThemeStyle
    switch_track_off: ThemeStyle
    switch_thumb_on: ThemeStyle
    switch_thumb_off: ThemeStyle

    dialog_background: ThemeStyle
    dialog_border: ThemeStyle
    dialog_text: ThemeStyle
    dialog_name_bg: ThemeStyle
    dialog_name_text: ThemeStyle
    dialog_continue_indicator: ThemeStyle

    tooltip_background: ThemeStyle
    tooltip_border: ThemeStyle
    tooltip_text: ThemeStyle

    notification_success_background: ThemeStyle
    notification_success_border: ThemeStyle
    notification_success_text: ThemeStyle
    notification_info_background: ThemeStyle
    notification_info_border: ThemeStyle
    notification_info_text: ThemeStyle
    notification_warning_background: ThemeStyle
    notification_warning_border: ThemeStyle
    notification_warning_text: ThemeStyle
    notification_custom_background: ThemeStyle
    notification_custom_border: ThemeStyle
    notification_custom_text: ThemeStyle
    notification_error_background: ThemeStyle
    notification_error_border: ThemeStyle
    notification_error_text: ThemeStyle

    accent1: ThemeStyle
    accent2: ThemeStyle

    # Optional fields with defaults (must come after all required fields)
    button_border: Optional[ThemeStyle] = None
    dropdown_border: Optional[ThemeStyle] = None
    border: Optional[ThemeStyle] = None
    border2: Optional[ThemeStyle] = None


class ThemeType(Enum):
    """Enumeration of all available theme types."""
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
    WHATSAPP_DARK = "whatsapp_dark"
    WHATSAPP_LIGHT = "whatsapp_light"
    CRUNCHYROLL_DARK = "crunchyroll_dark"
    CRUNCHYROLL_LIGHT = "crunchyroll_light"
    TWITCH_DARK = "twitch_dark"
    TWITCH_LIGHT = "twitch_light"
    TELEGRAM_DARK = "telegram_dark"
    TELEGRAM_LIGHT = "telegram_light"
    XBOX_DARK = "xbox_dark"
    XBOX_LIGHT = "xbox_light"
    PLAYSTATION_DARK = "playstation_dark"
    PLAYSTATION_LIGHT = "playstation_light"
    MINECRAFT_DARK = "minecraft_dark"
    MINECRAFT_LIGHT = "minecraft_light"
    
    CYBERPUNK_DARK = "cyberpunk_dark"
    CYBERPUNK_LIGHT = "cyberpunk_light"
    
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
    
    # Neutral Themes
    BLACK = "black"
    
    # OS Themes
    WINDOWS_DARK = "windows_dark"
    WINDOWS_LIGHT = "windows_light"
    LINUX_DARK = "linux_dark"
    LINUX_LIGHT = "linux_light"
    IOS_DARK = "ios_dark"
    IOS_LIGHT = "ios_light"
    ANDROID_DARK = "android_dark"
    ANDROID_LIGHT = "android_light"
    
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
    """Manages complete UI themes with local/remote loading."""
    
    _themes: Dict[ThemeType, UITheme] = {}
    _current_theme: ThemeType = ThemeType.DEFAULT
    _themes_loaded: bool = False
    
    GITHUB_THEMES_URL = "https://raw.githubusercontent.com/MrJuaumBR/LunaEngine/refs/heads/main/lunaengine/ui/themes.json"
    
    @classmethod
    def _get_themes_dir(cls) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "assets", "themes")
    
    @classmethod
    def _get_legacy_themes_file_path(cls) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "themes.json")
    
    @classmethod
    def _download_from_github(cls) -> Optional[dict]:
        try:
            print(f"🌐 Trying to download themes from GitHub: {cls.GITHUB_THEMES_URL}")
            headers = {'User-Agent': 'LunaEngine/1.0 (https://github.com/MrJuaumBR/LunaEngine)'}
            req = urllib.request.Request(cls.GITHUB_THEMES_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    print(f"Themes downloaded successfully from GitHub ({len(data)} themes)")
                    return data
                else:
                    print(f"/ Download failed: Status {response.status}")
                    return None
        except Exception as e:
            print(f"/ Error downloading from GitHub: {e}")
            return None
    
    @classmethod
    def _save_legacy_cache(cls, themes_data: dict) -> bool:
        try:
            cache_path = cls._get_legacy_themes_file_path()
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(themes_data, f, indent=2)
            print(f"Themes saved to local cache: {cache_path}")
            return True
        except Exception as e:
            print(f"! Could not save local cache: {e}")
            return False
    
    @classmethod
    def _parse_theme_style(cls, data: Union[dict, list, tuple]) -> ThemeStyle:
        """Convert JSON data (new or legacy format) to ThemeStyle."""
        if isinstance(data, dict):
            # New format: { "color": [R,G,B,A], "cornerRadius": X, "borderWidth": Y, "blur": Z }
            color_data = data.get('color', [0, 0, 0])
            if isinstance(color_data, (list, tuple)) and len(color_data) >= 3:
                r, g, b = color_data[0], color_data[1], color_data[2]
                alpha = color_data[3] / 255.0 if len(color_data) > 3 else 1.0
            else:
                r = g = b = 0
                alpha = 1.0
            return ThemeStyle(
                color=(r, g, b),
                alpha=alpha,
                corner_radius=data.get('cornerRadius', 0),
                border_width=data.get('borderWidth', 0),
                blur=data.get('blur', 0)
            )
        elif isinstance(data, (list, tuple)) and len(data) == 3:
            # Legacy format: [R, G, B]
            return ThemeStyle(color=(data[0], data[1], data[2]), alpha=1.0)
        else:
            # Fallback
            return ThemeStyle(color=(0, 0, 0), alpha=1.0)
    
    @classmethod
    def _load_theme_from_json_file(cls, filepath: str) -> Optional[Tuple[ThemeType, UITheme]]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            basename = os.path.basename(filepath)
            theme_name_str = os.path.splitext(basename)[0].upper()
            theme_type = None
            for tt in ThemeType:
                if tt.name == theme_name_str:
                    theme_type = tt
                    break
            if theme_type is None:
                print(f"! Unknown theme type from file: {theme_name_str}")
                return None
            
            theme_params = {}
            for field_name in UITheme.__dataclass_fields__.keys():
                if field_name in data:
                    theme_params[field_name] = cls._parse_theme_style(data[field_name])
                else:
                    theme_params[field_name] = None
            
            theme = UITheme(**theme_params)
            return (theme_type, theme)
        except Exception as e:
            print(f"/ Error loading theme from {filepath}: {e}")
            return None
    
    @classmethod
    def _load_themes_from_directory(cls) -> int:
        themes_dir = cls._get_themes_dir()
        if not os.path.isdir(themes_dir):
            print(f"Themes directory not found: {themes_dir}")
            return 0
        
        loaded_count = 0
        for filename in os.listdir(themes_dir):
            if filename.lower().endswith('.json'):
                filepath = os.path.join(themes_dir, filename)
                result = cls._load_theme_from_json_file(filepath)
                if result:
                    theme_type, theme = result
                    cls._themes[theme_type] = theme
                    loaded_count += 1
        
        if loaded_count > 0:
            print(f"Loaded {loaded_count} themes from {themes_dir}")
        return loaded_count
    
    @classmethod
    def _process_legacy_themes_data(cls, themes_data: dict):
        loaded_count = 0
        for theme_name, theme_dict in themes_data.items():
            try:
                theme_type = None
                for t in ThemeType:
                    if t.name == theme_name:
                        theme_type = t
                        break
                if theme_type is None:
                    continue
                
                processed_theme = {}
                for key, value in theme_dict.items():
                    processed_theme[key] = cls._parse_theme_style(value)
                
                theme = UITheme(**processed_theme)
                cls._themes[theme_type] = theme
                loaded_count += 1
            except Exception as e:
                print(f"/ Error processing theme '{theme_name}': {e}")
        
        cls._themes_loaded = True
        print(f"Loaded {loaded_count} themes from legacy source")
    
    @classmethod
    def _load_legacy_single_file(cls):
        themes_data = None
        legacy_file = cls._get_legacy_themes_file_path()
        
        if os.path.exists(legacy_file):
            try:
                with open(legacy_file, 'r', encoding='utf-8') as f:
                    themes_data = json.load(f)
                print(f"Loaded legacy themes from: {legacy_file}")
            except Exception as e:
                print(f"! Error loading legacy file: {e}")
        
        if themes_data is None:
            themes_data = cls._download_from_github()
            if themes_data:
                cls._save_legacy_cache(themes_data)
        
        if themes_data:
            cls._process_legacy_themes_data(themes_data)
        else:
            cls._create_fallback_theme()
    
    @classmethod
    def _create_fallback_theme(cls):
        def style(rgb, alpha=1.0, radius=0, border=0, blur=0):
            return ThemeStyle(color=rgb, alpha=alpha, corner_radius=radius, border_width=border, blur=blur)
        
        fallback_theme = UITheme(
            button_normal=style((70, 130, 180)),
            button_hover=style((50, 110, 160)),
            button_pressed=style((30, 90, 140)),
            button_disabled=style((120, 120, 120)),
            button_text=style((255, 255, 255)),
            button_border=style((100, 150, 200)),
            dropdown_normal=style((90, 90, 110)),
            dropdown_hover=style((110, 110, 130)),
            dropdown_expanded=style((100, 100, 120)),
            dropdown_text=style((255, 255, 255)),
            dropdown_option_normal=style((70, 70, 90)),
            dropdown_option_hover=style((80, 80, 100)),
            dropdown_option_selected=style((90, 90, 110)),
            dropdown_border=style((150, 150, 170)),
            slider_track=style((80, 80, 80)),
            slider_thumb_normal=style((200, 100, 100)),
            slider_thumb_hover=style((220, 120, 120)),
            slider_thumb_pressed=style((180, 80, 80)),
            slider_text=style((255, 255, 255)),
            label_text=style((240, 240, 240)),
            background=style((50, 50, 70)),
            background2=style((40, 40, 60)),
            text_primary=style((240, 240, 240)),
            text_secondary=style((200, 200, 200)),
            switch_track_on=style((0, 200, 0)),
            switch_track_off=style((80, 80, 80)),
            switch_thumb_on=style((255, 255, 255)),
            switch_thumb_off=style((220, 220, 220)),
            dialog_background=style((60, 60, 80)),
            dialog_border=style((120, 120, 140)),
            dialog_text=style((240, 240, 240)),
            dialog_name_bg=style((70, 130, 180)),
            dialog_name_text=style((255, 255, 255)),
            dialog_continue_indicator=style((200, 200, 200)),
            tooltip_background=style((40, 40, 60)),
            tooltip_border=style((100, 100, 120)),
            tooltip_text=style((240, 240, 240)),
            border=style((120, 120, 140)),
            border2=style((100, 100, 120)),
            notification_success_background=style((40, 167, 69)),
            notification_success_border=style((20, 147, 49)),
            notification_success_text=style((255, 255, 255)),
            notification_info_background=style((23, 162, 184)),
            notification_info_border=style((3, 142, 164)),
            notification_info_text=style((255, 255, 255)),
            notification_warning_background=style((255, 193, 7)),
            notification_warning_border=style((235, 173, 0)),
            notification_warning_text=style((0, 0, 0)),
            notification_custom_background=style((147, 112, 219)),
            notification_custom_border=style((127, 92, 199)),
            notification_custom_text=style((255, 255, 255)),
            notification_error_background=style((220, 53, 69)),
            notification_error_border=style((200, 33, 49)),
            notification_error_text=style((255, 255, 255)),
            accent1=style((70, 130, 180)),
            accent2=style((255, 193, 7))
        )
        cls._themes[ThemeType.DEFAULT] = fallback_theme
        cls._themes_loaded = True
        print("Fallback theme created")
    
    @classmethod
    def ensure_themes_loaded(cls):
        if cls._themes_loaded:
            return
        loaded = cls._load_themes_from_directory()
        if loaded > 0:
            cls._themes_loaded = True
            if ThemeType.DEFAULT not in cls._themes:
                print("! DEFAULT theme not found in loaded themes. Using fallback.")
                cls._create_fallback_theme()
            return
        cls._load_legacy_single_file()
    
    @classmethod
    def get_theme(cls, theme_type: ThemeType) -> UITheme:
        cls.ensure_themes_loaded()
        return cls._themes.get(theme_type, cls._themes[ThemeType.DEFAULT])
    
    @classmethod
    def set_current_theme(cls, theme_type: ThemeType):
        cls._current_theme = theme_type
    
    @classmethod
    def get_current_theme(cls) -> ThemeType:
        return cls._current_theme
    
    @classmethod
    def get_theme_by_name(cls, name: str) -> UITheme:
        cls.ensure_themes_loaded()
        theme_type = cls.get_theme_type_by_name(name)
        return cls._themes.get(theme_type, cls._themes[ThemeType.DEFAULT])
    
    @classmethod
    def get_theme_type_by_name(cls, name: str) -> ThemeType:
        cls.ensure_themes_loaded()
        for theme_type in ThemeType:
            if theme_type.value.lower() == name.lower():
                return theme_type
        return ThemeType.DEFAULT
    
    # --- Property accessors (return raw values) ---
    @classmethod
    def _get_style_property(cls, color_name: color_name_type, property_name: str,
                            theme_type: Optional[ThemeType] = None):
        cls.ensure_themes_loaded()
        if theme_type is None:
            theme_type = cls._current_theme
        theme = cls.get_theme(theme_type)
        style = getattr(theme, color_name, None)
        if style is None:
            return None
        return getattr(style, property_name)
    
    @classmethod
    def get_color(cls, color_name: color_name_type, theme_type: Optional[ThemeType] = None) -> Tuple[int, int, int]:
        """Return RGB tuple (ignores alpha)."""
        color = cls._get_style_property(color_name, 'color', theme_type)
        return color if color is not None else (0, 0, 0)
    
    @classmethod
    def get_alpha(cls, color_name: color_name_type, theme_type: Optional[ThemeType] = None) -> float:
        """Return alpha (0.0–1.0)."""
        alpha = cls._get_style_property(color_name, 'alpha', theme_type)
        return alpha if alpha is not None else 1.0
    
    @classmethod
    def get_corner_radius(cls, color_name: color_name_type, theme_type: Optional[ThemeType] = None) -> int:
        radius = cls._get_style_property(color_name, 'corner_radius', theme_type)
        return radius if radius is not None else 0
    
    @classmethod
    def get_border_width(cls, color_name: color_name_type, theme_type: Optional[ThemeType] = None) -> int:
        width = cls._get_style_property(color_name, 'border_width', theme_type)
        return width if width is not None else 0
    
    @classmethod
    def get_blur(cls, color_name: color_name_type, theme_type: Optional[ThemeType] = None) -> int:
        blur = cls._get_style_property(color_name, 'blur', theme_type)
        return blur if blur is not None else 0
    
    # --- Backward compatibility for old get_color signature ---
    @classmethod
    def get_color_legacy(cls, color_name: color_name_type) -> Tuple[int, int, int]:
        """Maintain compatibility with old `get_color` (no theme_type param)."""
        return cls.get_color(color_name)
    
    @classmethod
    def get_themes(cls) -> Dict[ThemeType, UITheme]:
        cls.ensure_themes_loaded()
        return cls._themes
    
    @classmethod
    def get_theme_types(cls) -> List[ThemeType]:
        cls.ensure_themes_loaded()
        return list(cls._themes.keys())
    
    @classmethod
    def get_theme_names(cls) -> List[str]:
        cls.ensure_themes_loaded()
        return [theme.value for theme in cls._themes.keys()]
    
    @classmethod
    def reload_themes(cls):
        cls._themes.clear()
        cls._themes_loaded = False
        cls.ensure_themes_loaded()
        print("Themes reloaded.")
    
    @classmethod
    def get_loaded_count(cls) -> int:
        cls.ensure_themes_loaded()
        return len(cls._themes)


# Initialize themes on module import
ThemeManager.ensure_themes_loaded()