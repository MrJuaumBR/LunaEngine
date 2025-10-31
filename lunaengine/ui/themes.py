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
                     'background', 'background2', 'text_primary', 'text_secondary', 'border', 'border2']

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
    
    QUEEN = "queen"
    KING = "king"
    ROBLOX = "roblox"
    DISCORD = "discord"
    GMAIL = "gmail"
    YOUTUBE = "youtube"
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
            background2=(40, 40, 60),  # Mais escuro para contraste
            text_primary=(240, 240, 240),
            text_secondary=(200, 200, 200),
            border=(120, 120, 140)
        )
        
        # PRIMARY THEME
        cls._themes[ThemeType.PRIMARY] = UITheme(
            # Button
            button_normal=(0, 120, 215),
            button_hover=(0, 100, 190),
            button_pressed=(0, 80, 160),
            button_disabled=(100, 100, 100),
            button_text=(255, 255, 255),
            button_border=None,
            
            # Dropdown
            dropdown_normal=(80, 80, 120),
            dropdown_hover=(100, 100, 140),
            dropdown_expanded=(90, 90, 130),
            dropdown_text=(255, 255, 255),
            dropdown_option_normal=(60, 60, 100),
            dropdown_option_hover=(70, 70, 110),
            dropdown_option_selected=(80, 80, 120),
            dropdown_border=(200, 200, 200),
            
            # Slider
            slider_track=(100, 100, 100),
            slider_thumb_normal=(150, 80, 80),
            slider_thumb_hover=(170, 90, 90),
            slider_thumb_pressed=(200, 100, 100),
            slider_text=(255, 255, 255),
            
            # Label
            label_text=(255, 255, 255),
            
            # General
            background=(40, 40, 60),
            background2=(30, 30, 50),
            text_primary=(255, 255, 255),
            text_secondary=(200, 200, 200),
            border=(150, 150, 150)
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
            border=(120, 120, 140)
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
            border=(200, 180, 100)
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
            border=(200, 100, 110)
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
            border=(100, 180, 120)
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
            border=(100, 170, 200)
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
            border=(255, 140, 0)
        )
        
        # MIDNIGHT DARK THEME - Corrigido (não era uma cópia)
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
            border=(70, 130, 180)
        )
        
        # MIDNIGHT LIGHT THEME - Corrigido (não era uma cópia)
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
            border=(135, 206, 250)
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
            border=(255, 215, 0)
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
            border=(147, 112, 219)
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
            border=(255, 182, 193)
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
            border=(219, 112, 147)
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
            border=(138, 43, 226)
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
            border=(147, 112, 219)
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
            border=(160, 120, 80)
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
            border=(255, 0, 255)
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
            border=(255, 105, 180)
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
            border=(0, 150, 0)
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
            border=(200, 220, 240)
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
            border=(192, 192, 192)
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
            border=(184, 115, 51)
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
            border=(205, 127, 50)
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
            border=(135, 206, 250)
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
            border=(255, 0, 255)
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
            border=(189, 195, 199)
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
            border=(255, 215, 0)
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
            border=(65, 105, 225)
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
            border=(226, 48, 74)
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
            border=(114, 137, 218)
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
            border=(218, 220, 224)
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
            border=(255, 0, 0)
        )

        # NOVOS TEMAS ADICIONADOS:

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
            border=(85, 107, 47)
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
            border=(255, 69, 0)
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
            border=(64, 224, 208)
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
            border=(0, 100, 0)
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
            border=(147, 112, 219)
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
            border=(139, 69, 19)
        )

    @classmethod
    def get_theme_by_name(cls, name: str) -> UITheme:
        """Get theme by name string"""
        if not cls._themes:
            cls.initialize_default_themes()
        return cls._themes.get(name, cls._themes[ThemeType.PRIMARY])
    
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