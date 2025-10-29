"""
__init__.py - UI Package Initialization for LunaEngine

ENGINE PATH:
lunaengine -> ui -> __init__.py

DESCRIPTION:
This module serves as the package initialization file for the LunaEngine UI system.
It exports all public classes and functions from the UI modules, providing a
clean and organized interface for importing UI components.

EXPORTS:
- Elements: UIElement, TextLabel, Button, Slider, Dropdown, ImageLabel, ImageButton, 
            TextBox, ProgressBar, UIDraggable, UIGradient, Select, Switch, FontManager
- Layout: UILayout, VerticalLayout, HorizontalLayout
- Themes: ThemeManager, ThemeType, UITheme
- Styles: UIStyle, Theme, UIState

This module enables convenient imports like:
from lunaengine.ui import Button, VerticalLayout, ThemeManager

It ensures that all major UI components are easily accessible from a single import point.
"""

from .elements import (
    UIElement, TextLabel, Button, Slider, Dropdown, FontManager,
    ImageLabel, ImageButton, TextBox, ProgressBar, UIDraggable,
    UIGradient, Select, Switch, ScrollingFrame
)
from .layout import UILayout, VerticalLayout, HorizontalLayout, GridLayout, JustifiedLayout
from .themes import ThemeManager, ThemeType, UITheme
from .styles import UIStyle, Theme, UIState

__all__ = [
    # Elements
    'UIElement', 'TextLabel', 'Button', 'Slider', 'Dropdown', 'FontManager',
    'ImageLabel', 'ImageButton', 'TextBox', 'ProgressBar', 'UIDraggable', 
    'UIGradient', 'Select', 'Switch', 'ScrollingFrame', 'UIState',
    
    # Layout
    'UILayout', 'VerticalLayout', 'HorizontalLayout', 'GridLayout', 'JustifiedLayout',
    
    # Themes
    'ThemeManager', 'ThemeType', 'UITheme',
    
    # Styles
    'UIStyle', 'Theme'
]