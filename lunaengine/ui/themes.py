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

# color_name is for typing in the get_color fucntion
color_name_type = Literal['button_normal', 'button_hover', 'button_pressed', 'button_disabled', 
                     'button_text', 'button_border',
                     'dropdown_normal', 'dropdown_hover', 'dropdown_expanded', 'dropdown_text',
                     'dropdown_option_normal', 'dropdown_option_hover', 'dropdown_option_selected',
                     'dropdown_border',
                     'slider_track', 'slider_thumb_normal', 'slider_thumb_hover', 'slider_thumb_pressed',
                     'slider_text',
                     'label_text',
                     'background', 'background2', 'text_primary', 'text_secondary', 'border', 'border2',
                     'switch_track_on', 'switch_track_off', 'switch_thumb_on', 'switch_thumb_off']

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
    
    # Switch colors (new)
    switch_track_on: Tuple[int, int, int]
    switch_track_off: Tuple[int, int, int]
    switch_thumb_on: Tuple[int, int, int]
    switch_thumb_off: Tuple[int, int, int]
    
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
        
    @classmethod
    def initialize_default_themes(cls):
        """Initialize all complete UI themes"""
        
        # DEFAULT THEME - Clean and modern
        cls._themes[ThemeType.DEFAULT] = UITheme(
            # Button
            button_normal=(70, 130, 180),
            button_hover=(50, 110, 160),
            button_pressed=(30, 90, 140),
            button_disabled=(120, 120, 120),
            button_text=(255, 255, 255),
            button_border=(100, 150, 200),
            
            # Dropdown
            dropdown_normal=(90, 90, 110),
            dropdown_hover=(110, 110, 130),
            dropdown_expanded=(100, 100, 120),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(70, 70, 90),
            dropdown_option_hover=(80, 80, 100),
            dropdown_option_selected=(90, 90, 110),
            dropdown_border=(150, 150, 170),
            
            # Slider
            slider_track=(80, 80, 80),
            slider_thumb_normal=(200, 100, 100),
            slider_thumb_hover=(220, 120, 120),
            slider_thumb_pressed=(180, 80, 80),
            slider_text=(255, 255, 255),
            
            # Label
            label_text=(240, 240, 240),
            
            # General
            background=(50, 50, 70),
            background2=(40, 40, 60),
            text_primary=(240, 240, 240),
            text_secondary=(200, 200, 200),
            
            # Switch
            switch_track_on=(0, 200, 0),
            switch_track_off=(80, 80, 80),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(220, 220, 220),
            
            border=(120, 120, 140),
            border2=(100, 100, 120)
        )
        
        # PRIMARY THEME
        cls._themes[ThemeType.PRIMARY] = UITheme(
            button_normal=(0, 120, 215),
            button_hover=(0, 100, 190),
            button_pressed=(0, 80, 160),
            button_disabled=(100, 100, 100),
            button_text=(255, 255, 255),
            button_border=None,
            
            dropdown_normal=(80, 80, 120),
            dropdown_hover=(100, 100, 140),
            dropdown_expanded=(90, 90, 130),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(60, 60, 100),
            dropdown_option_hover=(70, 70, 110),
            dropdown_option_selected=(80, 80, 120),
            dropdown_border=(200, 200, 200),
            
            slider_track=(100, 100, 100),
            slider_thumb_normal=(150, 80, 80),
            slider_thumb_hover=(170, 90, 90),
            slider_thumb_pressed=(200, 100, 100),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(40, 40, 60),
            background2=(30, 30, 50),
            text_primary=(255, 255, 255),
            text_secondary=(200, 200, 200),
            
            switch_track_on=(40, 167, 69),
            switch_track_off=(108, 117, 125),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 240, 240),
            
            border=(150, 150, 150),
            border2=(130, 130, 150)
        )
        
        # SECONDARY THEME
        cls._themes[ThemeType.SECONDARY] = UITheme(
            button_normal=(108, 117, 125),
            button_hover=(88, 97, 105),
            button_pressed=(68, 77, 85),
            button_disabled=(150, 150, 150),
            button_text=(255, 255, 255),
            button_border=None,
            
            dropdown_normal=(80, 80, 100),
            dropdown_hover=(100, 100, 120),
            dropdown_expanded=(90, 90, 110),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(60, 60, 80),
            dropdown_option_hover=(70, 70, 90),
            dropdown_option_selected=(80, 80, 100),
            dropdown_border=(150, 150, 170),
            
            slider_track=(90, 90, 90),
            slider_thumb_normal=(108, 117, 125),
            slider_thumb_hover=(128, 137, 145),
            slider_thumb_pressed=(88, 97, 105),
            slider_text=(255, 255, 255),
            
            label_text=(240, 240, 240),
            
            background=(60, 60, 80),
            background2=(50, 50, 70),
            text_primary=(240, 240, 240),
            text_secondary=(200, 200, 200),
            
            switch_track_on=(108, 117, 125),
            switch_track_off=(70, 70, 80),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(220, 220, 220),
            
            border=(120, 120, 140),
            border2=(100, 100, 120)
        )

        # WARN THEME
        cls._themes[ThemeType.WARN] = UITheme(
            button_normal=(255, 193, 7),
            button_hover=(235, 173, 0),
            button_pressed=(215, 153, 0),
            button_disabled=(180, 170, 120),
            button_text=(0, 0, 0),
            button_border=None,
            
            dropdown_normal=(90, 90, 70),
            dropdown_hover=(110, 110, 90),
            dropdown_expanded=(100, 100, 80),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(70, 70, 50),
            dropdown_option_hover=(80, 80, 60),
            dropdown_option_selected=(90, 90, 70),
            dropdown_border=(200, 180, 100),
            
            slider_track=(100, 90, 60),
            slider_thumb_normal=(255, 193, 7),
            slider_thumb_hover=(255, 213, 27),
            slider_thumb_pressed=(235, 173, 0),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(70, 60, 40),
            background2=(60, 50, 30),
            text_primary=(255, 255, 255),
            text_secondary=(255, 220, 150),
            
            switch_track_on=(255, 193, 7),
            switch_track_off=(100, 90, 60),
            switch_thumb_on=(0, 0, 0),
            switch_thumb_off=(200, 190, 160),
            
            border=(200, 180, 100),
            border2=(180, 160, 80)
        )

        # ERROR THEME
        cls._themes[ThemeType.ERROR] = UITheme(
            button_normal=(220, 53, 69),
            button_hover=(200, 33, 49),
            button_pressed=(180, 13, 29),
            button_disabled=(150, 100, 110),
            button_text=(255, 255, 255),
            button_border=None,
            
            dropdown_normal=(90, 50, 55),
            dropdown_hover=(110, 70, 75),
            dropdown_expanded=(100, 60, 65),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(70, 30, 35),
            dropdown_option_hover=(80, 40, 45),
            dropdown_option_selected=(90, 50, 55),
            dropdown_border=(200, 100, 110),
            
            slider_track=(100, 60, 65),
            slider_thumb_normal=(220, 53, 69),
            slider_thumb_hover=(240, 73, 89),
            slider_thumb_pressed=(200, 33, 49),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(70, 30, 35),
            background2=(60, 20, 25),
            text_primary=(255, 255, 255),
            text_secondary=(255, 200, 200),
            
            switch_track_on=(220, 53, 69),
            switch_track_off=(100, 60, 65),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 200, 200),
            
            border=(200, 100, 110),
            border2=(180, 80, 90)
        )

        # SUCCESS THEME
        cls._themes[ThemeType.SUCCESS] = UITheme(
            button_normal=(40, 167, 69),
            button_hover=(20, 147, 49),
            button_pressed=(0, 127, 29),
            button_disabled=(100, 150, 120),
            button_text=(255, 255, 255),
            button_border=None,
            
            dropdown_normal=(50, 80, 60),
            dropdown_hover=(70, 100, 80),
            dropdown_expanded=(60, 90, 70),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(30, 60, 40),
            dropdown_option_hover=(40, 70, 50),
            dropdown_option_selected=(50, 80, 60),
            dropdown_border=(100, 180, 120),
            
            slider_track=(60, 100, 70),
            slider_thumb_normal=(40, 167, 69),
            slider_thumb_hover=(60, 187, 89),
            slider_thumb_pressed=(20, 147, 49),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(30, 60, 40),
            background2=(20, 50, 30),
            text_primary=(255, 255, 255),
            text_secondary=(200, 240, 200),
            
            switch_track_on=(40, 167, 69),
            switch_track_off=(60, 100, 70),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(220, 240, 220),
            
            border=(100, 180, 120),
            border2=(80, 160, 100)
        )

        # INFO THEME
        cls._themes[ThemeType.INFO] = UITheme(
            button_normal=(23, 162, 184),
            button_hover=(3, 142, 164),
            button_pressed=(0, 122, 144),
            button_disabled=(100, 150, 160),
            button_text=(255, 255, 255),
            button_border=None,
            
            dropdown_normal=(50, 70, 90),
            dropdown_hover=(70, 90, 110),
            dropdown_expanded=(60, 80, 100),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(30, 50, 70),
            dropdown_option_hover=(40, 60, 80),
            dropdown_option_selected=(50, 70, 90),
            dropdown_border=(100, 170, 200),
            
            slider_track=(60, 100, 120),
            slider_thumb_normal=(23, 162, 184),
            slider_thumb_hover=(43, 182, 204),
            slider_thumb_pressed=(3, 142, 164),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(30, 50, 70),
            background2=(20, 40, 60),
            text_primary=(255, 255, 255),
            text_secondary=(200, 230, 255),
            
            switch_track_on=(23, 162, 184),
            switch_track_off=(60, 100, 120),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(220, 240, 255),
            
            border=(100, 170, 200),
            border2=(80, 150, 180)
        )
        
        # ECLIPSE THEME
        cls._themes[ThemeType.ECLIPSE] = UITheme(
            button_normal=(58, 12, 163),
            button_hover=(78, 32, 183),
            button_pressed=(38, 2, 143),
            button_disabled=(80, 60, 120),
            button_text=(255, 255, 0),
            button_border=(255, 165, 0),
            
            dropdown_normal=(40, 5, 100),
            dropdown_hover=(60, 25, 120),
            dropdown_expanded=(50, 15, 110),
            dropdown_text=(255, 255, 0),
            dropdown_option_normal=(30, 0, 80),
            dropdown_option_hover=(35, 5, 90),
            dropdown_option_selected=(40, 10, 100),
            dropdown_border=(255, 165, 0),
            
            slider_track=(50, 10, 90),
            slider_thumb_normal=(255, 140, 0),
            slider_thumb_hover=(255, 160, 0),
            slider_thumb_pressed=(255, 120, 0),
            slider_text=(255, 255, 0),
            
            label_text=(255, 255, 0),
            
            background=(20, 0, 40),
            background2=(10, 0, 25),
            text_primary=(255, 255, 0),
            text_secondary=(255, 200, 0),
            
            switch_track_on=(255, 140, 0),
            switch_track_off=(50, 10, 90),
            switch_thumb_on=(255, 255, 0),
            switch_thumb_off=(200, 180, 100),
            
            border=(255, 140, 0),
            border2=(200, 100, 0)
        )
        
        # MIDNIGHT DARK THEME
        cls._themes[ThemeType.MIDNIGHT_DARK] = UITheme(
            button_normal=(25, 25, 112),
            button_hover=(45, 45, 132),
            button_pressed=(15, 15, 92),
            button_disabled=(60, 60, 100),
            button_text=(176, 224, 230),
            button_border=(70, 130, 180),
            
            dropdown_normal=(15, 15, 35),
            dropdown_hover=(25, 25, 55),
            dropdown_expanded=(20, 20, 45),
            dropdown_text=(176, 224, 230),
            dropdown_option_normal=(10, 10, 25),
            dropdown_option_hover=(12, 12, 30),
            dropdown_option_selected=(15, 15, 35),
            dropdown_border=(70, 130, 180),
            
            slider_track=(30, 30, 60),
            slider_thumb_normal=(100, 149, 237),
            slider_thumb_hover=(120, 169, 255),
            slider_thumb_pressed=(80, 129, 217),
            slider_text=(176, 224, 230),
            
            label_text=(176, 224, 230),
            
            background=(5, 5, 15),
            background2=(2, 2, 8),
            text_primary=(176, 224, 230),
            text_secondary=(135, 206, 250),
            
            switch_track_on=(70, 130, 180),
            switch_track_off=(30, 30, 60),
            switch_thumb_on=(176, 224, 230),
            switch_thumb_off=(100, 149, 237),
            
            border=(70, 130, 180),
            border2=(50, 110, 160)
        )
        
        # MIDNIGHT LIGHT THEME
        cls._themes[ThemeType.MIDNIGHT_LIGHT] = UITheme(
            button_normal=(135, 206, 250),
            button_hover=(115, 186, 230),
            button_pressed=(95, 166, 210),
            button_disabled=(180, 200, 220),
            button_text=(25, 25, 112),
            button_border=(70, 130, 180),
            
            dropdown_normal=(240, 248, 255),
            dropdown_hover=(220, 228, 235),
            dropdown_expanded=(230, 238, 245),
            dropdown_text=(25, 25, 112),
            dropdown_option_normal=(250, 250, 255),
            dropdown_option_hover=(245, 245, 250),
            dropdown_option_selected=(240, 248, 255),
            dropdown_border=(70, 130, 180),
            
            slider_track=(200, 220, 240),
            slider_thumb_normal=(70, 130, 180),
            slider_thumb_hover=(90, 150, 200),
            slider_thumb_pressed=(50, 110, 160),
            slider_text=(25, 25, 112),
            
            label_text=(25, 25, 112),
            
            background=(230, 240, 255),
            background2=(220, 230, 245),
            text_primary=(25, 25, 112),
            text_secondary=(65, 105, 225),
            
            switch_track_on=(70, 130, 180),
            switch_track_off=(200, 220, 240),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 248, 255),
            
            border=(135, 206, 250),
            border2=(100, 180, 230)
        )
        
        # FANTASY DARK THEME - Magical and mystical
        cls._themes[ThemeType.FANTASY_DARK] = UITheme(
            button_normal=(75, 0, 130),
            button_hover=(95, 20, 150),
            button_pressed=(65, 0, 110),
            button_disabled=(60, 40, 80),
            button_text=(255, 215, 0),
            button_border=(255, 215, 0),
            
            dropdown_normal=(50, 0, 90),
            dropdown_hover=(70, 20, 110),
            dropdown_expanded=(60, 10, 100),
            dropdown_text=(255, 215, 0),
            dropdown_option_normal=(40, 0, 70),
            dropdown_option_hover=(50, 10, 80),
            dropdown_option_selected=(60, 20, 90),
            dropdown_border=(255, 215, 0),
            
            slider_track=(70, 30, 100),
            slider_thumb_normal=(255, 165, 0),
            slider_thumb_hover=(255, 185, 0),
            slider_thumb_pressed=(255, 140, 0),
            slider_text=(255, 215, 0),
            
            label_text=(255, 215, 0),
            
            background=(30, 0, 50),
            background2=(20, 0, 35),
            text_primary=(255, 215, 0),
            text_secondary=(255, 165, 0),
            
            switch_track_on=(255, 165, 0),
            switch_track_off=(70, 30, 100),
            switch_thumb_on=(255, 215, 0),
            switch_thumb_off=(200, 150, 50),
            
            border=(255, 215, 0),
            border2=(200, 165, 0)
        )
        
        # FANTASY LIGHT THEME
        cls._themes[ThemeType.FANTASY_LIGHT] = UITheme(
            button_normal=(216, 191, 216),
            button_hover=(200, 170, 200),
            button_pressed=(180, 150, 180),
            button_disabled=(230, 210, 230),
            button_text=(75, 0, 130),
            button_border=(147, 112, 219),
            
            dropdown_normal=(240, 230, 240),
            dropdown_hover=(230, 220, 230),
            dropdown_expanded=(235, 225, 235),
            dropdown_text=(75, 0, 130),
            dropdown_option_normal=(250, 240, 250),
            dropdown_option_hover=(240, 230, 240),
            dropdown_option_selected=(230, 220, 230),
            dropdown_border=(147, 112, 219),
            
            slider_track=(200, 180, 200),
            slider_thumb_normal=(147, 112, 219),
            slider_thumb_hover=(127, 92, 199),
            slider_thumb_pressed=(107, 72, 179),
            slider_text=(75, 0, 130),
            
            label_text=(75, 0, 130),
            
            background=(255, 250, 250),
            background2=(245, 240, 245),
            text_primary=(75, 0, 130),
            text_secondary=(100, 50, 150),
            
            switch_track_on=(147, 112, 219),
            switch_track_off=(200, 180, 200),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 230, 240),
            
            border=(147, 112, 219),
            border2=(120, 90, 190)
        )
        
        # CHERRY DARK THEME
        cls._themes[ThemeType.CHERRY_DARK] = UITheme(
            button_normal=(219, 112, 147),
            button_hover=(199, 92, 127),
            button_pressed=(179, 72, 107),
            button_disabled=(150, 100, 120),
            button_text=(255, 250, 250),
            button_border=(255, 182, 193),
            
            dropdown_normal=(180, 80, 120),
            dropdown_hover=(160, 60, 100),
            dropdown_expanded=(170, 70, 110),
            dropdown_text=(255, 250, 250),
            dropdown_option_normal=(150, 50, 90),
            dropdown_option_hover=(140, 40, 80),
            dropdown_option_selected=(160, 60, 100),
            dropdown_border=(255, 182, 193),
            
            slider_track=(150, 80, 100),
            slider_thumb_normal=(255, 105, 180),
            slider_thumb_hover=(255, 85, 160),
            slider_thumb_pressed=(255, 65, 140),
            slider_text=(255, 250, 250),
            
            label_text=(255, 250, 250),
            
            background=(80, 30, 50),
            background2=(60, 20, 35),
            text_primary=(255, 250, 250),
            text_secondary=(255, 182, 193),
            
            switch_track_on=(255, 105, 180),
            switch_track_off=(150, 80, 100),
            switch_thumb_on=(255, 250, 250),
            switch_thumb_off=(255, 200, 210),
            
            border=(255, 182, 193),
            border2=(220, 150, 160)
        )
        
        # CHERRY LIGHT THEME
        cls._themes[ThemeType.CHERRY_LIGHT] = UITheme(
            button_normal=(255, 228, 225),
            button_hover=(255, 218, 215),
            button_pressed=(255, 208, 205),
            button_disabled=(240, 230, 230),
            button_text=(178, 34, 34),
            button_border=(219, 112, 147),
            
            dropdown_normal=(255, 240, 245),
            dropdown_hover=(255, 230, 235),
            dropdown_expanded=(255, 235, 240),
            dropdown_text=(178, 34, 34),
            dropdown_option_normal=(255, 250, 250),
            dropdown_option_hover=(255, 245, 245),
            dropdown_option_selected=(255, 240, 245),
            dropdown_border=(219, 112, 147),
            
            slider_track=(240, 220, 220),
            slider_thumb_normal=(219, 112, 147),
            slider_thumb_hover=(199, 92, 127),
            slider_thumb_pressed=(179, 72, 107),
            slider_text=(178, 34, 34),
            
            label_text=(178, 34, 34),
            
            background=(255, 250, 250),
            background2=(245, 240, 240),
            text_primary=(178, 34, 34),
            text_secondary=(205, 92, 92),
            
            switch_track_on=(219, 112, 147),
            switch_track_off=(240, 220, 220),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(255, 240, 245),
            
            border=(219, 112, 147),
            border2=(190, 90, 125)
        )

        # GALAXY DARK THEME - Deep space with cosmic purple and blue
        cls._themes[ThemeType.GALAXY_DARK] = UITheme(
            button_normal=(75, 0, 130),
            button_hover=(95, 25, 150),
            button_pressed=(65, 0, 110),
            button_disabled=(60, 40, 80),
            button_text=(230, 230, 250),
            button_border=(138, 43, 226),
            
            dropdown_normal=(25, 25, 55),
            dropdown_hover=(35, 35, 75),
            dropdown_expanded=(30, 30, 65),
            dropdown_text=(230, 230, 250),
            dropdown_option_normal=(20, 20, 45),
            dropdown_option_hover=(22, 22, 50),
            dropdown_option_selected=(25, 25, 55),
            dropdown_border=(138, 43, 226),
            
            slider_track=(40, 40, 80),
            slider_thumb_normal=(147, 112, 219),
            slider_thumb_hover=(167, 132, 239),
            slider_thumb_pressed=(127, 92, 199),
            slider_text=(230, 230, 250),
            
            label_text=(230, 230, 250),
            
            background=(10, 10, 30),
            background2=(5, 5, 20),
            text_primary=(230, 230, 250),
            text_secondary=(176, 224, 230),
            
            switch_track_on=(138, 43, 226),
            switch_track_off=(40, 40, 80),
            switch_thumb_on=(230, 230, 250),
            switch_thumb_off=(147, 112, 219),
            
            border=(138, 43, 226),
            border2=(100, 30, 180)
        )

        # GALAXY LIGHT THEME - Nebula inspired pastel colors
        cls._themes[ThemeType.GALAXY_LIGHT] = UITheme(
            button_normal=(216, 191, 216),
            button_hover=(196, 171, 196),
            button_pressed=(176, 151, 176),
            button_disabled=(230, 220, 230),
            button_text=(75, 0, 130),
            button_border=(147, 112, 219),
            
            dropdown_normal=(230, 230, 250),
            dropdown_hover=(210, 210, 230),
            dropdown_expanded=(220, 220, 240),
            dropdown_text=(75, 0, 130),
            dropdown_option_normal=(240, 240, 255),
            dropdown_option_hover=(235, 235, 250),
            dropdown_option_selected=(230, 230, 250),
            dropdown_border=(147, 112, 219),
            
            slider_track=(200, 200, 220),
            slider_thumb_normal=(186, 85, 211),
            slider_thumb_hover=(166, 65, 191),
            slider_thumb_pressed=(146, 45, 171),
            slider_text=(75, 0, 130),
            
            label_text=(75, 0, 130),
            
            background=(248, 248, 255),
            background2=(240, 240, 250),
            text_primary=(75, 0, 130),
            text_secondary=(106, 90, 205),
            
            switch_track_on=(186, 85, 211),
            switch_track_off=(200, 200, 220),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(230, 230, 250),
            
            border=(147, 112, 219),
            border2=(120, 90, 190)
        )

        # BUILDER THEME - Construction/development inspired
        cls._themes[ThemeType.BUILDER] = UITheme(
            button_normal=(210, 180, 140),
            button_hover=(190, 160, 120),
            button_pressed=(170, 140, 100),
            button_disabled=(150, 140, 130),
            button_text=(47, 79, 79),
            button_border=(160, 120, 80),
            
            dropdown_normal=(245, 245, 220),
            dropdown_hover=(225, 225, 200),
            dropdown_expanded=(235, 235, 210),
            dropdown_text=(47, 79, 79),
            dropdown_option_normal=(255, 255, 240),
            dropdown_option_hover=(250, 250, 230),
            dropdown_option_selected=(245, 245, 220),
            dropdown_border=(160, 120, 80),
            
            slider_track=(200, 180, 160),
            slider_thumb_normal=(139, 69, 19),
            slider_thumb_hover=(159, 89, 39),
            slider_thumb_pressed=(119, 49, 0),
            slider_text=(47, 79, 79),
            
            label_text=(47, 79, 79),
            
            background=(253, 245, 230),
            background2=(243, 235, 220),
            text_primary=(47, 79, 79),
            text_secondary=(101, 67, 33),
            
            switch_track_on=(160, 120, 80),
            switch_track_off=(200, 180, 160),
            switch_thumb_on=(255, 250, 240),
            switch_thumb_off=(245, 245, 220),
            
            border=(160, 120, 80),
            border2=(140, 100, 60)
        )

        # NEON THEME
        cls._themes[ThemeType.NEON] = UITheme(
            button_normal=(0, 255, 255),
            button_hover=(0, 235, 235),
            button_pressed=(0, 215, 215),
            button_disabled=(100, 200, 200),
            button_text=(0, 0, 0),
            button_border=(255, 0, 255),
            
            dropdown_normal=(0, 200, 200),
            dropdown_hover=(0, 180, 180),
            dropdown_expanded=(0, 190, 190),
            dropdown_text=(0, 0, 0),
            dropdown_option_normal=(0, 150, 150),
            dropdown_option_hover=(0, 130, 130),
            dropdown_option_selected=(0, 170, 170),
            dropdown_border=(255, 0, 255),
            
            slider_track=(0, 100, 100),
            slider_thumb_normal=(255, 0, 255),
            slider_thumb_hover=(235, 0, 235),
            slider_thumb_pressed=(215, 0, 215),
            slider_text=(0, 255, 255),
            
            label_text=(0, 255, 255),
            
            background=(10, 10, 30),
            background2=(5, 5, 20),
            text_primary=(0, 255, 255),
            text_secondary=(255, 0, 255),
            
            switch_track_on=(255, 0, 255),
            switch_track_off=(0, 100, 100),
            switch_thumb_on=(0, 0, 0),
            switch_thumb_off=(0, 150, 150),
            
            border=(255, 0, 255),
            border2=(200, 0, 200)
        )
        
        # RUBY THEME - Deep red gemstone
        cls._themes[ThemeType.RUBY] = UITheme(
            button_normal=(220, 20, 60),
            button_hover=(200, 0, 40),
            button_pressed=(180, 0, 20),
            button_disabled=(120, 80, 90),
            button_text=(255, 255, 255),
            button_border=(255, 105, 180),
            
            dropdown_normal=(160, 0, 40),
            dropdown_hover=(140, 0, 30),
            dropdown_expanded=(150, 0, 35),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(120, 0, 30),
            dropdown_option_hover=(130, 0, 35),
            dropdown_option_selected=(140, 0, 40),
            dropdown_border=(255, 182, 193),
            
            slider_track=(100, 0, 20),
            slider_thumb_normal=(255, 20, 147),
            slider_thumb_hover=(255, 105, 180),
            slider_thumb_pressed=(219, 112, 147),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(60, 0, 15),
            background2=(40, 0, 10),
            text_primary=(255, 255, 255),
            text_secondary=(255, 182, 193),
            
            switch_track_on=(255, 20, 147),
            switch_track_off=(100, 0, 20),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(255, 182, 193),
            
            border=(255, 105, 180),
            border2=(220, 80, 150)
        )
        
        # EMERALD THEME - Rich green gemstone
        cls._themes[ThemeType.EMERALD] = UITheme(
            button_normal=(80, 200, 120),
            button_hover=(60, 180, 100),
            button_pressed=(40, 160, 80),
            button_disabled=(100, 130, 110),
            button_text=(255, 255, 255),
            button_border=(0, 100, 0),
            
            dropdown_normal=(40, 120, 80),
            dropdown_hover=(60, 140, 100),
            dropdown_expanded=(50, 130, 90),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(30, 100, 60),
            dropdown_option_hover=(35, 110, 70),
            dropdown_option_selected=(40, 120, 80),
            dropdown_border=(0, 150, 0),
            
            slider_track=(20, 80, 40),
            slider_thumb_normal=(0, 255, 127),
            slider_thumb_hover=(60, 255, 150),
            slider_thumb_pressed=(0, 200, 100),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(10, 40, 20),
            background2=(5, 25, 12),
            text_primary=(255, 255, 255),
            text_secondary=(200, 255, 200),
            
            switch_track_on=(0, 255, 127),
            switch_track_off=(20, 80, 40),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(100, 200, 150),
            
            border=(0, 150, 0),
            border2=(0, 120, 0)
        )
        
        # DIAMOND THEME - Crystal clear and bright
        cls._themes[ThemeType.DIAMOND] = UITheme(
            button_normal=(200, 220, 240),
            button_hover=(180, 200, 220),
            button_pressed=(160, 180, 200),
            button_disabled=(150, 160, 170),
            button_text=(0, 0, 0),
            button_border=(255, 255, 255),
            
            dropdown_normal=(180, 200, 220),
            dropdown_hover=(160, 180, 200),
            dropdown_expanded=(170, 190, 210),
            dropdown_text=(0, 0, 0),
            dropdown_option_normal=(200, 220, 240),
            dropdown_option_hover=(190, 210, 230),
            dropdown_option_selected=(180, 200, 220),
            dropdown_border=(255, 255, 255),
            
            slider_track=(150, 170, 190),
            slider_thumb_normal=(240, 248, 255),
            slider_thumb_hover=(255, 255, 255),
            slider_thumb_pressed=(220, 240, 255),
            slider_text=(0, 0, 0),
            
            label_text=(0, 0, 0),
            
            background=(240, 248, 255),
            background2=(230, 238, 245),
            text_primary=(0, 0, 0),
            text_secondary=(50, 50, 50),
            
            switch_track_on=(180, 200, 220),
            switch_track_off=(150, 170, 190),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 248, 255),
            
            border=(200, 220, 240),
            border2=(180, 200, 220)
        )
        
        # SILVER THEME - Metallic silver
        cls._themes[ThemeType.SILVER] = UITheme(
            button_normal=(192, 192, 192),
            button_hover=(169, 169, 169),
            button_pressed=(150, 150, 150),
            button_disabled=(120, 120, 120),
            button_text=(0, 0, 0),
            button_border=(220, 220, 220),
            
            dropdown_normal=(169, 169, 169),
            dropdown_hover=(150, 150, 150),
            dropdown_expanded=(160, 160, 160),
            dropdown_text=(0, 0, 0),
            dropdown_option_normal=(192, 192, 192),
            dropdown_option_hover=(180, 180, 180),
            dropdown_option_selected=(169, 169, 169),
            dropdown_border=(220, 220, 220),
            
            slider_track=(130, 130, 130),
            slider_thumb_normal=(230, 230, 230),
            slider_thumb_hover=(240, 240, 240),
            slider_thumb_pressed=(210, 210, 210),
            slider_text=(0, 0, 0),
            
            label_text=(0, 0, 0),
            
            background=(105, 105, 105),
            background2=(85, 85, 85),
            text_primary=(255, 255, 255),
            text_secondary=(220, 220, 220),
            
            switch_track_on=(169, 169, 169),
            switch_track_off=(130, 130, 130),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(220, 220, 220),
            
            border=(192, 192, 192),
            border2=(169, 169, 169)
        )
        
        # COPPER THEME - Warm metallic copper
        cls._themes[ThemeType.COPPER] = UITheme(
            button_normal=(184, 115, 51),
            button_hover=(164, 95, 31),
            button_pressed=(144, 75, 11),
            button_disabled=(130, 100, 80),
            button_text=(255, 255, 255),
            button_border=(210, 140, 70),
            
            dropdown_normal=(150, 90, 40),
            dropdown_hover=(130, 70, 20),
            dropdown_expanded=(140, 80, 30),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(120, 60, 15),
            dropdown_option_hover=(135, 75, 25),
            dropdown_option_selected=(150, 90, 40),
            dropdown_border=(210, 140, 70),
            
            slider_track=(100, 50, 10),
            slider_thumb_normal=(218, 138, 56),
            slider_thumb_hover=(228, 158, 76),
            slider_thumb_pressed=(198, 118, 36),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(80, 40, 5),
            background2=(60, 30, 3),
            text_primary=(255, 255, 255),
            text_secondary=(255, 200, 150),
            
            switch_track_on=(184, 115, 51),
            switch_track_off=(100, 50, 10),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(218, 138, 56),
            
            border=(184, 115, 51),
            border2=(150, 90, 30)
        )
        
        # BRONZE THEME - Rich bronze metal
        cls._themes[ThemeType.BRONZE] = UITheme(
            button_normal=(205, 127, 50),
            button_hover=(185, 107, 30),
            button_pressed=(165, 87, 10),
            button_disabled=(140, 110, 80),
            button_text=(255, 255, 255),
            button_border=(210, 150, 80),
            
            dropdown_normal=(160, 100, 40),
            dropdown_hover=(140, 80, 20),
            dropdown_expanded=(150, 90, 30),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(130, 70, 15),
            dropdown_option_hover=(145, 85, 25),
            dropdown_option_selected=(160, 100, 40),
            dropdown_border=(210, 150, 80),
            
            slider_track=(110, 60, 10),
            slider_thumb_normal=(210, 140, 60),
            slider_thumb_hover=(220, 160, 80),
            slider_thumb_pressed=(190, 120, 40),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(90, 50, 5),
            background2=(70, 35, 3),
            text_primary=(255, 255, 255),
            text_secondary=(255, 220, 170),
            
            switch_track_on=(205, 127, 50),
            switch_track_off=(110, 60, 10),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(210, 140, 60),
            
            border=(205, 127, 50),
            border2=(170, 100, 30)
        )
        
        # AZURE THEME - Bright sky blue
        cls._themes[ThemeType.AZURE] = UITheme(
            button_normal=(0, 127, 255),
            button_hover=(0, 107, 235),
            button_pressed=(0, 87, 215),
            button_disabled=(100, 150, 200),
            button_text=(255, 255, 255),
            button_border=(135, 206, 250),
            
            dropdown_normal=(30, 144, 255),
            dropdown_hover=(50, 164, 255),
            dropdown_expanded=(40, 154, 255),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(20, 124, 235),
            dropdown_option_hover=(25, 134, 245),
            dropdown_option_selected=(30, 144, 255),
            dropdown_border=(135, 206, 250),
            
            slider_track=(70, 130, 180),
            slider_thumb_normal=(173, 216, 230),
            slider_thumb_hover=(193, 236, 250),
            slider_thumb_pressed=(153, 196, 210),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(25, 25, 112),
            background2=(15, 15, 80),
            text_primary=(255, 255, 255),
            text_secondary=(173, 216, 230),
            
            switch_track_on=(0, 127, 255),
            switch_track_off=(70, 130, 180),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(173, 216, 230),
            
            border=(135, 206, 250),
            border2=(100, 180, 230)
        )
        
        # 80s THEME - Vibrant retro colors
        cls._themes[ThemeType.EIGHTIES] = UITheme(
            button_normal=(255, 0, 128),
            button_hover=(235, 0, 108),
            button_pressed=(215, 0, 88),
            button_disabled=(150, 100, 130),
            button_text=(255, 255, 0),
            button_border=(0, 255, 255),
            
            dropdown_normal=(128, 0, 255),
            dropdown_hover=(148, 20, 255),
            dropdown_expanded=(138, 10, 255),
            dropdown_text=(255, 255, 0),
            dropdown_option_normal=(108, 0, 235),
            dropdown_option_hover=(118, 0, 245),
            dropdown_option_selected=(128, 0, 255),
            dropdown_border=(0, 255, 255),
            
            slider_track=(255, 0, 255),
            slider_thumb_normal=(0, 255, 255),
            slider_thumb_hover=(20, 255, 255),
            slider_thumb_pressed=(0, 235, 235),
            slider_text=(255, 255, 0),
            
            label_text=(255, 255, 0),
            
            background=(0, 0, 0),
            background2=(10, 5, 15),
            text_primary=(255, 255, 0),
            text_secondary=(0, 255, 255),
            
            switch_track_on=(255, 0, 128),
            switch_track_off=(128, 0, 255),
            switch_thumb_on=(255, 255, 0),
            switch_thumb_off=(0, 255, 255),
            
            border=(255, 0, 255),
            border2=(200, 0, 200)
        )
        
        # CLOUDS THEME - Soft and dreamy
        cls._themes[ThemeType.CLOUDS] = UITheme(
            button_normal=(236, 240, 241),
            button_hover=(216, 220, 221),
            button_pressed=(196, 200, 201),
            button_disabled=(180, 185, 188),
            button_text=(52, 73, 94),
            button_border=(189, 195, 199),
            
            dropdown_normal=(220, 225, 228),
            dropdown_hover=(200, 205, 208),
            dropdown_expanded=(210, 215, 218),
            dropdown_text=(52, 73, 94),
            dropdown_option_normal=(240, 245, 248),
            dropdown_option_hover=(230, 235, 238),
            dropdown_option_selected=(220, 225, 228),
            dropdown_border=(189, 195, 199),
            
            slider_track=(200, 205, 208),
            slider_thumb_normal=(149, 165, 166),
            slider_thumb_hover=(169, 185, 186),
            slider_thumb_pressed=(129, 145, 146),
            slider_text=(52, 73, 94),
            
            label_text=(52, 73, 94),
            
            background=(245, 245, 245),
            background2=(235, 235, 235),
            text_primary=(52, 73, 94),
            text_secondary=(127, 140, 141),
            
            switch_track_on=(149, 165, 166),
            switch_track_off=(200, 205, 208),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 245, 248),
            
            border=(189, 195, 199),
            border2=(170, 180, 185)
        )
        
        # QUEEN THEME - Royal purple and gold
        cls._themes[ThemeType.QUEEN] = UITheme(
            button_normal=(147, 112, 219),
            button_hover=(127, 92, 199),
            button_pressed=(107, 72, 179),
            button_disabled=(180, 160, 210),
            button_text=(255, 215, 0),
            button_border=(255, 215, 0),
            
            dropdown_normal=(120, 80, 180),
            dropdown_hover=(140, 100, 200),
            dropdown_expanded=(130, 90, 190),
            dropdown_text=(255, 215, 0),
            dropdown_option_normal=(100, 60, 160),
            dropdown_option_hover=(110, 70, 170),
            dropdown_option_selected=(120, 80, 180),
            dropdown_border=(255, 215, 0),
            
            slider_track=(80, 40, 120),
            slider_thumb_normal=(255, 215, 0),
            slider_thumb_hover=(255, 235, 0),
            slider_thumb_pressed=(255, 195, 0),
            slider_text=(255, 215, 0),
            
            label_text=(255, 215, 0),
            
            background=(50, 20, 80),
            background2=(35, 10, 55),
            text_primary=(255, 215, 0),
            text_secondary=(255, 165, 0),
            
            switch_track_on=(147, 112, 219),
            switch_track_off=(80, 40, 120),
            switch_thumb_on=(255, 215, 0),
            switch_thumb_off=(200, 150, 100),
            
            border=(255, 215, 0),
            border2=(200, 165, 0)
        )

        # KING THEME - Royal blue and silver
        cls._themes[ThemeType.KING] = UITheme(
            button_normal=(65, 105, 225),
            button_hover=(45, 85, 205),
            button_pressed=(25, 65, 185),
            button_disabled=(130, 150, 200),
            button_text=(255, 255, 255),
            button_border=(192, 192, 192),
            
            dropdown_normal=(40, 70, 180),
            dropdown_hover=(60, 90, 200),
            dropdown_expanded=(50, 80, 190),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(30, 60, 160),
            dropdown_option_hover=(35, 65, 170),
            dropdown_option_selected=(40, 70, 180),
            dropdown_border=(192, 192, 192),
            
            slider_track=(20, 50, 120),
            slider_thumb_normal=(192, 192, 192),
            slider_thumb_hover=(220, 220, 220),
            slider_thumb_pressed=(160, 160, 160),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(10, 30, 80),
            background2=(5, 15, 50),
            text_primary=(255, 255, 255),
            text_secondary=(192, 192, 192),
            
            switch_track_on=(65, 105, 225),
            switch_track_off=(20, 50, 120),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(192, 192, 192),
            
            border=(65, 105, 225),
            border2=(40, 80, 180)
        )

        # ROBLOX THEME - Roblox brand colors
        cls._themes[ThemeType.ROBLOX] = UITheme(
            button_normal=(25, 25, 25),
            button_hover=(45, 45, 45),
            button_pressed=(15, 15, 15),
            button_disabled=(80, 80, 80),
            button_text=(226, 48, 74),
            button_border=(226, 48, 74),
            
            dropdown_normal=(40, 40, 40),
            dropdown_hover=(60, 60, 60),
            dropdown_expanded=(50, 50, 50),
            dropdown_text=(226, 48, 74),
            dropdown_option_normal=(30, 30, 30),
            dropdown_option_hover=(35, 35, 35),
            dropdown_option_selected=(40, 40, 40),
            dropdown_border=(226, 48, 74),
            
            slider_track=(60, 60, 60),
            slider_thumb_normal=(226, 48, 74),
            slider_thumb_hover=(246, 68, 94),
            slider_thumb_pressed=(206, 28, 54),
            slider_text=(226, 48, 74),
            
            label_text=(226, 48, 74),
            
            background=(15, 15, 15),
            background2=(8, 8, 8),
            text_primary=(226, 48, 74),
            text_secondary=(255, 255, 255),
            
            switch_track_on=(226, 48, 74),
            switch_track_off=(60, 60, 60),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(100, 100, 100),
            
            border=(226, 48, 74),
            border2=(180, 30, 50)
        )

        # DISCORD THEME - Discord brand colors
        cls._themes[ThemeType.DISCORD] = UITheme(
            button_normal=(88, 101, 242),
            button_hover=(68, 81, 222),
            button_pressed=(48, 61, 202),
            button_disabled=(120, 130, 200),
            button_text=(255, 255, 255),
            button_border=(114, 137, 218),
            
            dropdown_normal=(54, 57, 63),
            dropdown_hover=(64, 67, 73),
            dropdown_expanded=(59, 62, 68),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(44, 47, 53),
            dropdown_option_hover=(49, 52, 58),
            dropdown_option_selected=(54, 57, 63),
            dropdown_border=(114, 137, 218),
            
            slider_track=(40, 43, 48),
            slider_thumb_normal=(114, 137, 218),
            slider_thumb_hover=(134, 157, 238),
            slider_thumb_pressed=(94, 117, 198),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(35, 39, 42),
            background2=(25, 28, 32),
            text_primary=(255, 255, 255),
            text_secondary=(220, 220, 220),
            
            switch_track_on=(114, 137, 218),
            switch_track_off=(40, 43, 48),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(80, 85, 95),
            
            border=(114, 137, 218),
            border2=(90, 110, 180)
        )

        # GMAIL THEME - Gmail brand colors
        cls._themes[ThemeType.GMAIL] = UITheme(
            button_normal=(234, 67, 53),
            button_hover=(214, 47, 33),
            button_pressed=(194, 27, 13),
            button_disabled=(200, 120, 120),
            button_text=(255, 255, 255),
            button_border=(251, 188, 5),
            
            dropdown_normal=(66, 133, 244),
            dropdown_hover=(86, 153, 255),
            dropdown_expanded=(76, 143, 254),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(46, 113, 224),
            dropdown_option_hover=(56, 123, 234),
            dropdown_option_selected=(66, 133, 244),
            dropdown_border=(251, 188, 5),
            
            slider_track=(52, 168, 83),
            slider_thumb_normal=(234, 67, 53),
            slider_thumb_hover=(254, 87, 73),
            slider_thumb_pressed=(214, 47, 33),
            slider_text=(255, 255, 255),
            
            label_text=(60, 64, 67),
            
            background=(255, 255, 255),
            background2=(245, 245, 245),
            text_primary=(60, 64, 67),
            text_secondary=(95, 99, 104),
            
            switch_track_on=(52, 168, 83),
            switch_track_off=(218, 220, 224),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 240, 240),
            
            border=(218, 220, 224),
            border2=(200, 202, 205)
        )

        # YOUTUBE THEME - YouTube brand colors
        cls._themes[ThemeType.YOUTUBE] = UITheme(
            button_normal=(255, 0, 0),
            button_hover=(235, 0, 0),
            button_pressed=(215, 0, 0),
            button_disabled=(180, 100, 100),
            button_text=(255, 255, 255),
            button_border=(40, 40, 40),
            
            dropdown_normal=(40, 40, 40),
            dropdown_hover=(60, 60, 60),
            dropdown_expanded=(50, 50, 50),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(30, 30, 30),
            dropdown_option_hover=(35, 35, 35),
            dropdown_option_selected=(40, 40, 40),
            dropdown_border=(255, 0, 0),
            
            slider_track=(60, 60, 60),
            slider_thumb_normal=(255, 0, 0),
            slider_thumb_hover=(255, 20, 20),
            slider_thumb_pressed=(235, 0, 0),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(15, 15, 15),
            background2=(8, 8, 8),
            text_primary=(255, 255, 255),
            text_secondary=(170, 170, 170),
            
            switch_track_on=(255, 0, 0),
            switch_track_off=(60, 60, 60),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(100, 100, 100),
            
            border=(255, 0, 0),
            border2=(200, 0, 0)
        )

        # FOREST THEME - Nature inspired
        cls._themes[ThemeType.FOREST] = UITheme(
            button_normal=(34, 139, 34),
            button_hover=(50, 159, 50),
            button_pressed=(20, 119, 20),
            button_disabled=(100, 130, 100),
            button_text=(255, 255, 255),
            button_border=(139, 69, 19),
            
            dropdown_normal=(47, 79, 79),
            dropdown_hover=(67, 99, 99),
            dropdown_expanded=(57, 89, 89),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(37, 69, 69),
            dropdown_option_hover=(42, 74, 74),
            dropdown_option_selected=(47, 79, 79),
            dropdown_border=(139, 69, 19),
            
            slider_track=(60, 100, 60),
            slider_thumb_normal=(160, 82, 45),
            slider_thumb_hover=(180, 102, 65),
            slider_thumb_pressed=(140, 62, 25),
            slider_text=(255, 255, 255),
            
            label_text=(240, 255, 240),
            
            background=(15, 56, 15),
            background2=(10, 40, 10),
            text_primary=(240, 255, 240),
            text_secondary=(200, 230, 200),
            
            switch_track_on=(34, 139, 34),
            switch_track_off=(60, 100, 60),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(200, 230, 200),
            
            border=(85, 107, 47),
            border2=(60, 80, 30)
        )

        # SUNSET THEME - Warm sunset colors
        cls._themes[ThemeType.SUNSET] = UITheme(
            button_normal=(255, 140, 0),
            button_hover=(255, 165, 0),
            button_pressed=(255, 120, 0),
            button_disabled=(180, 140, 100),
            button_text=(75, 0, 130),
            button_border=(255, 69, 0),
            
            dropdown_normal=(255, 99, 71),
            dropdown_hover=(255, 119, 91),
            dropdown_expanded=(255, 109, 81),
            dropdown_text=(75, 0, 130),
            dropdown_option_normal=(255, 79, 61),
            dropdown_option_hover=(255, 89, 71),
            dropdown_option_selected=(255, 99, 71),
            dropdown_border=(255, 69, 0),
            
            slider_track=(205, 92, 92),
            slider_thumb_normal=(138, 43, 226),
            slider_thumb_hover=(158, 63, 246),
            slider_thumb_pressed=(118, 23, 206),
            slider_text=(75, 0, 130),
            
            label_text=(75, 0, 130),
            
            background=(255, 218, 185),
            background2=(255, 200, 170),
            text_primary=(75, 0, 130),
            text_secondary=(106, 90, 205),
            
            switch_track_on=(255, 140, 0),
            switch_track_off=(205, 92, 92),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(255, 218, 185),
            
            border=(255, 69, 0),
            border2=(220, 50, 0)
        )

        # OCEAN THEME - Deep ocean blues
        cls._themes[ThemeType.OCEAN] = UITheme(
            button_normal=(0, 105, 148),
            button_hover=(0, 125, 168),
            button_pressed=(0, 85, 128),
            button_disabled=(80, 120, 140),
            button_text=(255, 255, 255),
            button_border=(64, 224, 208),
            
            dropdown_normal=(25, 25, 112),
            dropdown_hover=(45, 45, 132),
            dropdown_expanded=(35, 35, 122),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(15, 15, 102),
            dropdown_option_hover=(20, 20, 107),
            dropdown_option_selected=(25, 25, 112),
            dropdown_border=(64, 224, 208),
            
            slider_track=(70, 130, 180),
            slider_thumb_normal=(72, 209, 204),
            slider_thumb_hover=(92, 229, 224),
            slider_thumb_pressed=(52, 189, 184),
            slider_text=(255, 255, 255),
            
            label_text=(224, 255, 255),
            
            background=(0, 0, 139),
            background2=(0, 0, 100),
            text_primary=(224, 255, 255),
            text_secondary=(173, 216, 230),
            
            switch_track_on=(0, 105, 148),
            switch_track_off=(70, 130, 180),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(173, 216, 230),
            
            border=(64, 224, 208),
            border2=(50, 180, 170)
        )

        # MATRIX THEME - Green code style
        cls._themes[ThemeType.MATRIX] = UITheme(
            button_normal=(0, 255, 0),
            button_hover=(50, 255, 50),
            button_pressed=(0, 200, 0),
            button_disabled=(80, 120, 80),
            button_text=(0, 0, 0),
            button_border=(0, 100, 0),
            
            dropdown_normal=(0, 50, 0),
            dropdown_hover=(0, 70, 0),
            dropdown_expanded=(0, 60, 0),
            dropdown_text=(0, 255, 0),
            dropdown_option_normal=(0, 30, 0),
            dropdown_option_hover=(0, 40, 0),
            dropdown_option_selected=(0, 50, 0),
            dropdown_border=(0, 100, 0),
            
            slider_track=(0, 80, 0),
            slider_thumb_normal=(0, 255, 127),
            slider_thumb_hover=(50, 255, 150),
            slider_thumb_pressed=(0, 220, 100),
            slider_text=(0, 255, 0),
            
            label_text=(0, 255, 0),
            
            background=(0, 20, 0),
            background2=(0, 10, 0),
            text_primary=(0, 255, 0),
            text_secondary=(50, 205, 50),
            
            switch_track_on=(0, 255, 0),
            switch_track_off=(0, 80, 0),
            switch_thumb_on=(0, 0, 0),
            switch_thumb_off=(0, 150, 0),
            
            border=(0, 100, 0),
            border2=(0, 80, 0)
        )

        # LAVENDER THEME - Soft purple theme
        cls._themes[ThemeType.LAVENDER] = UITheme(
            button_normal=(230, 230, 250),
            button_hover=(210, 210, 230),
            button_pressed=(190, 190, 210),
            button_disabled=(200, 200, 220),
            button_text=(75, 0, 130),
            button_border=(147, 112, 219),
            
            dropdown_normal=(216, 191, 216),
            dropdown_hover=(196, 171, 196),
            dropdown_expanded=(206, 181, 206),
            dropdown_text=(75, 0, 130),
            dropdown_option_normal=(226, 201, 226),
            dropdown_option_hover=(221, 196, 221),
            dropdown_option_selected=(216, 191, 216),
            dropdown_border=(147, 112, 219),
            
            slider_track=(200, 180, 200),
            slider_thumb_normal=(186, 85, 211),
            slider_thumb_hover=(206, 105, 231),
            slider_thumb_pressed=(166, 65, 191),
            slider_text=(75, 0, 130),
            
            label_text=(75, 0, 130),
            
            background=(248, 248, 255),
            background2=(240, 240, 250),
            text_primary=(75, 0, 130),
            text_secondary=(106, 90, 205),
            
            switch_track_on=(147, 112, 219),
            switch_track_off=(200, 180, 200),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 240, 250),
            
            border=(147, 112, 219),
            border2=(120, 90, 190)
        )

        # CHOCOLATE THEME - Rich brown theme
        cls._themes[ThemeType.CHOCOLATE] = UITheme(
            button_normal=(210, 105, 30),
            button_hover=(190, 85, 10),
            button_pressed=(170, 65, 0),
            button_disabled=(150, 120, 100),
            button_text=(255, 250, 240),
            button_border=(139, 69, 19),
            
            dropdown_normal=(160, 82, 45),
            dropdown_hover=(140, 62, 25),
            dropdown_expanded=(150, 72, 35),
            dropdown_text=(255, 250, 240),
            dropdown_option_normal=(130, 52, 15),
            dropdown_option_hover=(135, 57, 20),
            dropdown_option_selected=(140, 62, 25),
            dropdown_border=(139, 69, 19),
            
            slider_track=(120, 60, 30),
            slider_thumb_normal=(205, 133, 63),
            slider_thumb_hover=(225, 153, 83),
            slider_thumb_pressed=(185, 113, 43),
            slider_text=(255, 250, 240),
            
            label_text=(255, 250, 240),
            
            background=(101, 67, 33),
            background2=(80, 50, 25),
            text_primary=(255, 250, 240),
            text_secondary=(245, 222, 179),
            
            switch_track_on=(160, 82, 45),
            switch_track_off=(120, 60, 30),
            switch_thumb_on=(255, 250, 240),
            switch_thumb_off=(205, 133, 63),
            
            border=(139, 69, 19),
            border2=(110, 50, 10)
        )

        # DEEP SPACE THEME - Dark cosmic theme
        cls._themes[ThemeType.DEEP_SPACE] = UITheme(
            button_normal=(100, 65, 165),
            button_hover=(120, 85, 185),
            button_pressed=(80, 45, 145),
            button_disabled=(60, 60, 80),
            button_text=(230, 230, 250),
            button_border=(138, 43, 226),
            
            dropdown_normal=(30, 25, 45),
            dropdown_hover=(50, 45, 65),
            dropdown_expanded=(40, 35, 55),
            dropdown_text=(230, 230, 250),
            dropdown_option_normal=(20, 15, 35),
            dropdown_option_hover=(25, 20, 40),
            dropdown_option_selected=(30, 25, 45),
            dropdown_border=(147, 112, 219),
            
            slider_track=(40, 35, 60),
            slider_thumb_normal=(186, 85, 211),
            slider_thumb_hover=(206, 105, 231),
            slider_thumb_pressed=(166, 65, 191),
            slider_text=(230, 230, 250),
            
            label_text=(230, 230, 250),
            
            background=(15, 10, 25),
            background2=(10, 5, 15),
            text_primary=(230, 230, 250),
            text_secondary=(176, 196, 222),
            
            switch_track_on=(123, 104, 238),
            switch_track_off=(50, 45, 65),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(200, 200, 210),
            
            border=(75, 0, 130),
            border2=(60, 0, 100)
        )
        
        # NORD DARK THEME - Arctic dark theme
        cls._themes[ThemeType.NORD_DARK] = UITheme(
            button_normal=(94, 129, 172),
            button_hover=(114, 149, 192),
            button_pressed=(74, 109, 152),
            button_disabled=(100, 120, 140),
            button_text=(236, 239, 244),
            button_border=(129, 161, 193),
            
            dropdown_normal=(46, 52, 64),
            dropdown_hover=(59, 66, 82),
            dropdown_expanded=(52, 59, 73),
            dropdown_text=(236, 239, 244),
            dropdown_option_normal=(40, 46, 58),
            dropdown_option_hover=(43, 49, 61),
            dropdown_option_selected=(46, 52, 64),
            dropdown_border=(76, 86, 106),
            
            slider_track=(67, 76, 94),
            slider_thumb_normal=(136, 192, 208),
            slider_thumb_hover=(156, 212, 228),
            slider_thumb_pressed=(116, 172, 188),
            slider_text=(236, 239, 244),
            
            label_text=(236, 239, 244),
            
            background=(36, 41, 51),
            background2=(30, 35, 42),
            text_primary=(236, 239, 244),
            text_secondary=(216, 222, 233),
            
            switch_track_on=(143, 188, 187),
            switch_track_off=(67, 76, 94),
            switch_thumb_on=(236, 239, 244),
            switch_thumb_off=(200, 205, 215),
            
            border=(76, 86, 106),
            border2=(59, 66, 82)
        )
        
        # NORD LIGHT THEME - Arctic light theme
        cls._themes[ThemeType.NORD_LIGHT] = UITheme(
            button_normal=(136, 192, 208),
            button_hover=(116, 172, 188),
            button_pressed=(96, 152, 168),
            button_disabled=(180, 200, 210),
            button_text=(46, 52, 64),
            button_border=(129, 161, 193),
            
            dropdown_normal=(236, 239, 244),
            dropdown_hover=(216, 222, 233),
            dropdown_expanded=(226, 232, 240),
            dropdown_text=(46, 52, 64),
            dropdown_option_normal=(245, 247, 250),
            dropdown_option_hover=(240, 244, 248),
            dropdown_option_selected=(236, 239, 244),
            dropdown_border=(216, 222, 233),
            
            slider_track=(229, 233, 240),
            slider_thumb_normal=(94, 129, 172),
            slider_thumb_hover=(114, 149, 192),
            slider_thumb_pressed=(74, 109, 152),
            slider_text=(46, 52, 64),
            
            label_text=(46, 52, 64),
            
            background=(255, 255, 255),
            background2=(245, 247, 250),
            text_primary=(46, 52, 64),
            text_secondary=(76, 86, 106),
            
            switch_track_on=(143, 188, 187),
            switch_track_off=(229, 233, 240),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(245, 247, 250),
            
            border=(216, 222, 233),
            border2=(196, 202, 213)
        )
        
        # DRACULA THEME - Popular dark theme
        cls._themes[ThemeType.DRACULA] = UITheme(
            button_normal=(189, 147, 249),
            button_hover=(169, 127, 229),
            button_pressed=(149, 107, 209),
            button_disabled=(100, 100, 130),
            button_text=(40, 42, 54),
            button_border=(98, 114, 164),
            
            dropdown_normal=(68, 71, 90),
            dropdown_hover=(88, 91, 110),
            dropdown_expanded=(78, 81, 100),
            dropdown_text=(248, 248, 242),
            dropdown_option_normal=(58, 61, 80),
            dropdown_option_hover=(63, 66, 85),
            dropdown_option_selected=(68, 71, 90),
            dropdown_border=(98, 114, 164),
            
            slider_track=(40, 42, 54),
            slider_thumb_normal=(255, 121, 198),
            slider_thumb_hover=(255, 141, 218),
            slider_thumb_pressed=(235, 101, 178),
            slider_text=(248, 248, 242),
            
            label_text=(248, 248, 242),
            
            background=(40, 42, 54),
            background2=(30, 31, 41),
            text_primary=(248, 248, 242),
            text_secondary=(189, 147, 249),
            
            switch_track_on=(80, 250, 123),
            switch_track_off=(68, 71, 90),
            switch_thumb_on=(40, 42, 54),
            switch_thumb_off=(139, 233, 253),
            
            border=(98, 114, 164),
            border2=(78, 94, 144)
        )
        
        # SOLARIZED DARK THEME
        cls._themes[ThemeType.SOLARIZED_DARK] = UITheme(
            button_normal=(38, 139, 210),
            button_hover=(58, 159, 230),
            button_pressed=(28, 119, 190),
            button_disabled=(80, 100, 120),
            button_text=(253, 246, 227),
            button_border=(42, 161, 152),
            
            dropdown_normal=(0, 43, 54),
            dropdown_hover=(7, 54, 66),
            dropdown_expanded=(3, 48, 60),
            dropdown_text=(253, 246, 227),
            dropdown_option_normal=(0, 35, 44),
            dropdown_option_hover=(0, 39, 49),
            dropdown_option_selected=(0, 43, 54),
            dropdown_border=(42, 161, 152),
            
            slider_track=(7, 54, 66),
            slider_thumb_normal=(181, 137, 0),
            slider_thumb_hover=(201, 157, 0),
            slider_thumb_pressed=(161, 117, 0),
            slider_text=(253, 246, 227),
            
            label_text=(253, 246, 227),
            
            background=(0, 43, 54),
            background2=(0, 32, 41),
            text_primary=(253, 246, 227),
            text_secondary=(131, 148, 150),
            
            switch_track_on=(133, 153, 0),
            switch_track_off=(7, 54, 66),
            switch_thumb_on=(253, 246, 227),
            switch_thumb_off=(131, 148, 150),
            
            border=(42, 161, 152),
            border2=(32, 131, 122)
        )
        
        # SOLARIZED LIGHT THEME
        cls._themes[ThemeType.SOLARIZED_LIGHT] = UITheme(
            button_normal=(38, 139, 210),
            button_hover=(58, 159, 230),
            button_pressed=(28, 119, 190),
            button_disabled=(150, 170, 190),
            button_text=(253, 246, 227),
            button_border=(42, 161, 152),
            
            dropdown_normal=(253, 246, 227),
            dropdown_hover=(238, 232, 213),
            dropdown_expanded=(245, 239, 220),
            dropdown_text=(101, 123, 131),
            dropdown_option_normal=(255, 255, 255),
            dropdown_option_hover=(250, 244, 225),
            dropdown_option_selected=(253, 246, 227),
            dropdown_border=(42, 161, 152),
            
            slider_track=(238, 232, 213),
            slider_thumb_normal=(181, 137, 0),
            slider_thumb_hover=(201, 157, 0),
            slider_thumb_pressed=(161, 117, 0),
            slider_text=(101, 123, 131),
            
            label_text=(101, 123, 131),
            
            background=(253, 246, 227),
            background2=(238, 232, 213),
            text_primary=(101, 123, 131),
            text_secondary=(147, 161, 161),
            
            switch_track_on=(133, 153, 0),
            switch_track_off=(238, 232, 213),
            switch_thumb_on=(253, 246, 227),
            switch_thumb_off=(147, 161, 161),
            
            border=(42, 161, 152),
            border2=(32, 131, 122)
        )
        
        # MONOKAI THEME - Vibrant programmer theme
        cls._themes[ThemeType.MONOKAI] = UITheme(
            button_normal=(249, 38, 114),
            button_hover=(229, 18, 94),
            button_pressed=(209, 0, 74),
            button_disabled=(120, 100, 110),
            button_text=(39, 40, 34),
            button_border=(174, 129, 255),
            
            dropdown_normal=(39, 40, 34),
            dropdown_hover=(59, 60, 54),
            dropdown_expanded=(49, 50, 44),
            dropdown_text=(248, 248, 242),
            dropdown_option_normal=(29, 30, 24),
            dropdown_option_hover=(34, 35, 29),
            dropdown_option_selected=(39, 40, 34),
            dropdown_border=(174, 129, 255),
            
            slider_track=(65, 67, 57),
            slider_thumb_normal=(102, 217, 239),
            slider_thumb_hover=(122, 237, 255),
            slider_thumb_pressed=(82, 197, 219),
            slider_text=(248, 248, 242),
            
            label_text=(248, 248, 242),
            
            background=(39, 40, 34),
            background2=(29, 30, 24),
            text_primary=(248, 248, 242),
            text_secondary=(249, 38, 114),
            
            switch_track_on=(166, 226, 46),
            switch_track_off=(65, 67, 57),
            switch_thumb_on=(39, 40, 34),
            switch_thumb_off=(249, 38, 114),
            
            border=(174, 129, 255),
            border2=(140, 100, 210)
        )
        
        # GRUVBOX DARK THEME - Warm dark theme
        cls._themes[ThemeType.GRUVBOX_DARK] = UITheme(
            button_normal=(251, 73, 52),
            button_hover=(231, 53, 32),
            button_pressed=(211, 33, 12),
            button_disabled=(120, 100, 90),
            button_text=(40, 40, 40),
            button_border=(184, 187, 38),
            
            dropdown_normal=(60, 56, 54),
            dropdown_hover=(80, 76, 74),
            dropdown_expanded=(70, 66, 64),
            dropdown_text=(251, 241, 199),
            dropdown_option_normal=(50, 46, 44),
            dropdown_option_hover=(55, 51, 49),
            dropdown_option_selected=(60, 56, 54),
            dropdown_border=(184, 187, 38),
            
            slider_track=(80, 73, 69),
            slider_thumb_normal=(254, 128, 25),
            slider_thumb_hover=(255, 148, 45),
            slider_thumb_pressed=(234, 108, 5),
            slider_text=(251, 241, 199),
            
            label_text=(251, 241, 199),
            
            background=(40, 40, 40),
            background2=(29, 32, 33),
            text_primary=(251, 241, 199),
            text_secondary=(213, 196, 161),
            
            switch_track_on=(152, 151, 26),
            switch_track_off=(80, 73, 69),
            switch_thumb_on=(251, 241, 199),
            switch_thumb_off=(213, 196, 161),
            
            border=(184, 187, 38),
            border2=(150, 150, 30)
        )
        
        # GRUVBOX LIGHT THEME - Warm light theme
        cls._themes[ThemeType.GRUVBOX_LIGHT] = UITheme(
            button_normal=(204, 36, 29),
            button_hover=(184, 16, 9),
            button_pressed=(164, 0, 0),
            button_disabled=(180, 150, 140),
            button_text=(251, 241, 199),
            button_border=(215, 153, 33),
            
            dropdown_normal=(251, 241, 199),
            dropdown_hover=(235, 219, 178),
            dropdown_expanded=(243, 230, 188),
            dropdown_text=(60, 56, 54),
            dropdown_option_normal=(255, 255, 255),
            dropdown_option_hover=(247, 237, 206),
            dropdown_option_selected=(251, 241, 199),
            dropdown_border=(215, 153, 33),
            
            slider_track=(213, 196, 161),
            slider_thumb_normal=(254, 128, 25),
            slider_thumb_hover=(255, 148, 45),
            slider_thumb_pressed=(234, 108, 5),
            slider_text=(60, 56, 54),
            
            label_text=(60, 56, 54),
            
            background=(251, 241, 199),
            background2=(235, 219, 178),
            text_primary=(60, 56, 54),
            text_secondary=(124, 111, 100),
            
            switch_track_on=(152, 151, 26),
            switch_track_off=(213, 196, 161),
            switch_thumb_on=(251, 241, 199),
            switch_thumb_off=(235, 219, 178),
            
            border=(215, 153, 33),
            border2=(180, 125, 20)
        )
        
        # BRAZIL THEME - Green and yellow colors
        cls._themes[ThemeType.BRAZIL] = UITheme(
            button_normal=(0, 156, 59),
            button_hover=(0, 136, 39),
            button_pressed=(0, 116, 19),
            button_disabled=(100, 130, 110),
            button_text=(255, 223, 0),
            button_border=(255, 223, 0),
            
            dropdown_normal=(0, 100, 40),
            dropdown_hover=(0, 120, 50),
            dropdown_expanded=(0, 110, 45),
            dropdown_text=(255, 223, 0),
            dropdown_option_normal=(0, 80, 30),
            dropdown_option_hover=(0, 90, 35),
            dropdown_option_selected=(0, 100, 40),
            dropdown_border=(255, 223, 0),
            
            slider_track=(0, 80, 30),
            slider_thumb_normal=(255, 223, 0),
            slider_thumb_hover=(255, 243, 20),
            slider_thumb_pressed=(235, 203, 0),
            slider_text=(255, 223, 0),
            
            label_text=(255, 223, 0),
            
            background=(0, 50, 20),
            background2=(0, 35, 12),
            text_primary=(255, 223, 0),
            text_secondary=(200, 180, 0),
            
            switch_track_on=(0, 156, 59),
            switch_track_off=(0, 80, 30),
            switch_thumb_on=(255, 223, 0),
            switch_thumb_off=(200, 180, 0),
            
            border=(255, 223, 0),
            border2=(200, 180, 0)
        )
        
        # JAPAN THEME - Red and white colors
        cls._themes[ThemeType.JAPAN] = UITheme(
            button_normal=(188, 0, 45),
            button_hover=(168, 0, 25),
            button_pressed=(148, 0, 15),
            button_disabled=(150, 100, 110),
            button_text=(255, 255, 255),
            button_border=(255, 255, 255),
            
            dropdown_normal=(220, 220, 220),
            dropdown_hover=(200, 200, 200),
            dropdown_expanded=(210, 210, 210),
            dropdown_text=(188, 0, 45),
            dropdown_option_normal=(240, 240, 240),
            dropdown_option_hover=(230, 230, 230),
            dropdown_option_selected=(220, 220, 220),
            dropdown_border=(188, 0, 45),
            
            slider_track=(200, 200, 200),
            slider_thumb_normal=(188, 0, 45),
            slider_thumb_hover=(208, 20, 65),
            slider_thumb_pressed=(168, 0, 25),
            slider_text=(188, 0, 45),
            
            label_text=(188, 0, 45),
            
            background=(255, 255, 255),
            background2=(245, 245, 245),
            text_primary=(188, 0, 45),
            text_secondary=(150, 0, 30),
            
            switch_track_on=(188, 0, 45),
            switch_track_off=(200, 200, 200),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 240, 240),
            
            border=(188, 0, 45),
            border2=(150, 0, 30)
        )
        
        # USA THEME - Red, white and blue colors
        cls._themes[ThemeType.USA] = UITheme(
            button_normal=(179, 25, 66),
            button_hover=(159, 5, 46),
            button_pressed=(139, 0, 26),
            button_disabled=(140, 100, 110),
            button_text=(255, 255, 255),
            button_border=(60, 59, 110),
            
            dropdown_normal=(60, 59, 110),
            dropdown_hover=(80, 79, 130),
            dropdown_expanded=(70, 69, 120),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(40, 39, 90),
            dropdown_option_hover=(50, 49, 100),
            dropdown_option_selected=(60, 59, 110),
            dropdown_border=(179, 25, 66),
            
            slider_track=(100, 100, 140),
            slider_thumb_normal=(179, 25, 66),
            slider_thumb_hover=(199, 45, 86),
            slider_thumb_pressed=(159, 5, 46),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(10, 30, 80),
            background2=(5, 20, 60),
            text_primary=(255, 255, 255),
            text_secondary=(200, 200, 220),
            
            switch_track_on=(179, 25, 66),
            switch_track_off=(60, 59, 110),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(200, 200, 220),
            
            border=(179, 25, 66),
            border2=(140, 15, 50)
        )
        
        # EUROPEAN THEME - Blue and gold colors
        cls._themes[ThemeType.EUROPEAN] = UITheme(
            button_normal=(0, 51, 153),
            button_hover=(0, 71, 173),
            button_pressed=(0, 31, 133),
            button_disabled=(80, 100, 150),
            button_text=(255, 204, 0),
            button_border=(255, 204, 0),
            
            dropdown_normal=(0, 51, 153),
            dropdown_hover=(0, 71, 173),
            dropdown_expanded=(0, 61, 163),
            dropdown_text=(255, 204, 0),
            dropdown_option_normal=(0, 31, 123),
            dropdown_option_hover=(0, 41, 143),
            dropdown_option_selected=(0, 51, 153),
            dropdown_border=(255, 204, 0),
            
            slider_track=(0, 31, 103),
            slider_thumb_normal=(255, 204, 0),
            slider_thumb_hover=(255, 224, 20),
            slider_thumb_pressed=(235, 184, 0),
            slider_text=(255, 204, 0),
            
            label_text=(255, 204, 0),
            
            background=(0, 20, 80),
            background2=(0, 10, 50),
            text_primary=(255, 204, 0),
            text_secondary=(255, 153, 0),
            
            switch_track_on=(0, 51, 153),
            switch_track_off=(0, 31, 103),
            switch_thumb_on=(255, 204, 0),
            switch_thumb_off=(200, 160, 0),
            
            border=(255, 204, 0),
            border2=(200, 160, 0)
        )
        
        # KIWI THEME - Green and brown colors
        cls._themes[ThemeType.KIWI] = UITheme(
            button_normal=(111, 168, 86),
            button_hover=(91, 148, 66),
            button_pressed=(71, 128, 46),
            button_disabled=(120, 140, 110),
            button_text=(255, 255, 255),
            button_border=(139, 69, 19),
            
            dropdown_normal=(85, 107, 47),
            dropdown_hover=(105, 127, 67),
            dropdown_expanded=(95, 117, 57),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(65, 87, 27),
            dropdown_option_hover=(75, 97, 37),
            dropdown_option_selected=(85, 107, 47),
            dropdown_border=(139, 69, 19),
            
            slider_track=(60, 80, 30),
            slider_thumb_normal=(160, 82, 45),
            slider_thumb_hover=(180, 102, 65),
            slider_thumb_pressed=(140, 62, 25),
            slider_text=(255, 255, 255),
            
            label_text=(240, 255, 240),
            
            background=(34, 85, 34),
            background2=(20, 60, 20),
            text_primary=(240, 255, 240),
            text_secondary=(200, 230, 200),
            
            switch_track_on=(111, 168, 86),
            switch_track_off=(60, 80, 30),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(200, 230, 200),
            
            border=(139, 69, 19),
            border2=(110, 50, 10)
        )
        
        # NINJA DARK THEME - Stealth black and red
        cls._themes[ThemeType.NINJA_DARK] = UITheme(
            button_normal=(40, 40, 40),
            button_hover=(60, 60, 60),
            button_pressed=(20, 20, 20),
            button_disabled=(80, 80, 80),
            button_text=(220, 20, 60),
            button_border=(220, 20, 60),
            
            dropdown_normal=(20, 20, 20),
            dropdown_hover=(40, 40, 40),
            dropdown_expanded=(30, 30, 30),
            dropdown_text=(220, 20, 60),
            dropdown_option_normal=(10, 10, 10),
            dropdown_option_hover=(15, 15, 15),
            dropdown_option_selected=(20, 20, 20),
            dropdown_border=(220, 20, 60),
            
            slider_track=(40, 40, 40),
            slider_thumb_normal=(220, 20, 60),
            slider_thumb_hover=(240, 40, 80),
            slider_thumb_pressed=(200, 0, 40),
            slider_text=(220, 20, 60),
            
            label_text=(220, 20, 60),
            
            background=(0, 0, 0),
            background2=(10, 10, 10),
            text_primary=(220, 20, 60),
            text_secondary=(180, 10, 40),
            
            switch_track_on=(220, 20, 60),
            switch_track_off=(40, 40, 40),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(100, 100, 100),
            
            border=(220, 20, 60),
            border2=(180, 10, 40)
        )
        
        # NINJA LIGHT THEME - Light stealth theme
        cls._themes[ThemeType.NINJA_LIGHT] = UITheme(
            button_normal=(220, 220, 220),
            button_hover=(200, 200, 200),
            button_pressed=(180, 180, 180),
            button_disabled=(230, 230, 230),
            button_text=(220, 20, 60),
            button_border=(150, 150, 150),
            
            dropdown_normal=(240, 240, 240),
            dropdown_hover=(220, 220, 220),
            dropdown_expanded=(230, 230, 230),
            dropdown_text=(220, 20, 60),
            dropdown_option_normal=(250, 250, 250),
            dropdown_option_hover=(245, 245, 245),
            dropdown_option_selected=(240, 240, 240),
            dropdown_border=(150, 150, 150),
            
            slider_track=(200, 200, 200),
            slider_thumb_normal=(220, 20, 60),
            slider_thumb_hover=(240, 40, 80),
            slider_thumb_pressed=(200, 0, 40),
            slider_text=(220, 20, 60),
            
            label_text=(220, 20, 60),
            
            background=(255, 255, 255),
            background2=(245, 245, 245),
            text_primary=(220, 20, 60),
            text_secondary=(180, 10, 40),
            
            switch_track_on=(220, 20, 60),
            switch_track_off=(200, 200, 200),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 240, 240),
            
            border=(150, 150, 150),
            border2=(120, 120, 120)
        )
        
        # STEAM DARK THEME - Steam platform dark theme
        cls._themes[ThemeType.STEAM_DARK] = UITheme(
            button_normal=(27, 40, 56),
            button_hover=(47, 60, 76),
            button_pressed=(17, 30, 46),
            button_disabled=(70, 80, 90),
            button_text=(200, 200, 200),
            button_border=(90, 120, 140),
            
            dropdown_normal=(34, 49, 63),
            dropdown_hover=(44, 59, 73),
            dropdown_expanded=(39, 54, 68),
            dropdown_text=(200, 200, 200),
            dropdown_option_normal=(24, 39, 53),
            dropdown_option_hover=(29, 44, 58),
            dropdown_option_selected=(34, 49, 63),
            dropdown_border=(90, 120, 140),
            
            slider_track=(50, 65, 79),
            slider_thumb_normal=(102, 192, 244),
            slider_thumb_hover=(122, 212, 255),
            slider_thumb_pressed=(82, 172, 224),
            slider_text=(200, 200, 200),
            
            label_text=(200, 200, 200),
            
            background=(18, 27, 34),
            background2=(12, 18, 24),
            text_primary=(200, 200, 200),
            text_secondary=(150, 150, 150),
            
            switch_track_on=(102, 192, 244),
            switch_track_off=(50, 65, 79),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(120, 140, 160),
            
            border=(90, 120, 140),
            border2=(70, 100, 120)
        )
        
        # STEAM LIGHT THEME - Steam platform light theme
        cls._themes[ThemeType.STEAM_LIGHT] = UITheme(
            button_normal=(236, 240, 241),
            button_hover=(216, 220, 221),
            button_pressed=(196, 200, 201),
            button_disabled=(220, 225, 228),
            button_text=(44, 62, 80),
            button_border=(149, 165, 166),
            
            dropdown_normal=(220, 225, 228),
            dropdown_hover=(200, 205, 208),
            dropdown_expanded=(210, 215, 218),
            dropdown_text=(44, 62, 80),
            dropdown_option_normal=(240, 245, 248),
            dropdown_option_hover=(230, 235, 238),
            dropdown_option_selected=(220, 225, 228),
            dropdown_border=(149, 165, 166),
            
            slider_track=(200, 205, 208),
            slider_thumb_normal=(52, 152, 219),
            slider_thumb_hover=(72, 172, 239),
            slider_thumb_pressed=(32, 132, 199),
            slider_text=(44, 62, 80),
            
            label_text=(44, 62, 80),
            
            background=(245, 245, 245),
            background2=(235, 235, 235),
            text_primary=(44, 62, 80),
            text_secondary=(85, 105, 125),
            
            switch_track_on=(52, 152, 219),
            switch_track_off=(200, 205, 208),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(240, 245, 248),
            
            border=(149, 165, 166),
            border2=(130, 145, 146)
        )
        
        # DYNASTY THEME - Imperial Chinese style
        cls._themes[ThemeType.DYNASTY] = UITheme(
            button_normal=(205, 92, 92),
            button_hover=(185, 72, 72),
            button_pressed=(165, 52, 52),
            button_disabled=(150, 120, 120),
            button_text=(255, 215, 0),
            button_border=(139, 0, 0),
            
            dropdown_normal=(160, 50, 50),
            dropdown_hover=(180, 70, 70),
            dropdown_expanded=(170, 60, 60),
            dropdown_text=(255, 215, 0),
            dropdown_option_normal=(140, 30, 30),
            dropdown_option_hover=(150, 40, 40),
            dropdown_option_selected=(160, 50, 50),
            dropdown_border=(139, 0, 0),
            
            slider_track=(120, 30, 30),
            slider_thumb_normal=(255, 215, 0),
            slider_thumb_hover=(255, 235, 20),
            slider_thumb_pressed=(235, 195, 0),
            slider_text=(255, 215, 0),
            
            label_text=(255, 215, 0),
            
            background=(80, 20, 20),
            background2=(60, 10, 10),
            text_primary=(255, 215, 0),
            text_secondary=(255, 165, 0),
            
            switch_track_on=(205, 92, 92),
            switch_track_off=(120, 30, 30),
            switch_thumb_on=(255, 215, 0),
            switch_thumb_off=(200, 160, 0),
            
            border=(139, 0, 0),
            border2=(110, 0, 0)
        )
        
        # VIKINGS THEME - Norse warrior style
        cls._themes[ThemeType.VIKINGS] = UITheme(
            button_normal=(65, 105, 225),
            button_hover=(45, 85, 205),
            button_pressed=(25, 65, 185),
            button_disabled=(100, 120, 180),
            button_text=(255, 255, 255),
            button_border=(139, 69, 19),
            
            dropdown_normal=(47, 79, 79),
            dropdown_hover=(67, 99, 99),
            dropdown_expanded=(57, 89, 89),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(37, 69, 69),
            dropdown_option_hover=(42, 74, 74),
            dropdown_option_selected=(47, 79, 79),
            dropdown_border=(139, 69, 19),
            
            slider_track=(30, 60, 90),
            slider_thumb_normal=(160, 82, 45),
            slider_thumb_hover=(180, 102, 65),
            slider_thumb_pressed=(140, 62, 25),
            slider_text=(255, 255, 255),
            
            label_text=(255, 255, 255),
            
            background=(25, 40, 65),
            background2=(15, 25, 40),
            text_primary=(255, 255, 255),
            text_secondary=(200, 220, 240),
            
            switch_track_on=(65, 105, 225),
            switch_track_off=(30, 60, 90),
            switch_thumb_on=(255, 255, 255),
            switch_thumb_off=(160, 180, 220),
            
            border=(139, 69, 19),
            border2=(110, 50, 10)
        )

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
ThemeManager.initialize_default_themes()