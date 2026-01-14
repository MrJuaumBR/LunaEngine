"""
UI Module - User Interface System for LunaEngine

LOCATION: lunaengine/ui/__init__.py

DESCRIPTION:
Initialization file for the UI module. This module provides a comprehensive
user interface system for LunaEngine with reusable components, layout managers,
theming system, and interactive elements.

MODULES PROVIDED:
- elements: Core UI element classes (buttons, labels, sliders, dropdowns)
- layout: Layout managers for automatic UI element arrangement
- themes: Comprehensive theming system with multiple color schemes
- styles: Basic style definitions and UI state management

LIBRARIES USED:
- typing: For type hints and annotations
- enum: For enumerated types and constants
- dataclasses: For structured data storage in themes

This module enables developers to create rich, interactive user interfaces
with consistent styling and responsive layouts across different game scenes.
"""

import inspect
from . import elements, layout, themes, styles, tween, layer_manager

# Automatically discover all UIElement subclasses
_ui_element_classes = []
for name, obj in inspect.getmembers(elements):
    if (inspect.isclass(obj) and 
        issubclass(obj, elements.UIElement) and 
        obj != elements.UIElement):
        _ui_element_classes.append(name)

# Add base classes and managers
_base_classes = ['UIElement', 'UIState', 'FontManager', 'TooltipConfig', 'Tooltip', 'UITooltipManager']

# Import layout classes
_layout_classes = ['UILayout', 'VerticalLayout', 'HorizontalLayout', 'GridLayout', 'JustifiedLayout']

# Import theme classes
_theme_classes = ['ThemeManager', 'ThemeType', 'UITheme']

# Import style classes  
_style_classes = ['UIStyle', 'Theme']

# Add tween module
_tween_classes = ['EasingType', 'TweenProperty', 'Tween', 'AnimationHandler', 'TweenGroup', 'TweenSequence', 'TweenParallel']

# Add layer manager
_layer_manager = ['UILayerManager']

# Combine all exports
__all__ = _base_classes + _ui_element_classes + _layout_classes + _theme_classes + _style_classes +  _tween_classes

# Import everything for direct access
from .elements import *
from .layout import *
from .themes import *
from .styles import *
from .tween import *
from .layer_manager import *