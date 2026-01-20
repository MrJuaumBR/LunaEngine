"""
tooltips.py - Tooltip System for LunaEngine

This module handles tooltips for UI elements, providing helpful information
when hovering over elements.
"""

import pygame
from typing import Optional, Tuple, List, Dict
from enum import Enum
from .elements import UIElement, UIState
from .themes import ThemeManager, ThemeType
from ..backend.types import InputState

class TooltipConfig:
    """
    Configuration class for tooltip appearance and behavior.
    Allows easy customization of tooltips without passing multiple parameters.
    """
    
    def __init__(self, 
                 text: str = "",
                 font_size: int = 14,
                 padding: int = 8,
                 corner_radius: int = 4,
                 offset_x: int = 10,
                 offset_y: int = 10,
                 show_delay: float = 0.5,
                 max_width: int = 300,
                 theme: ThemeType = None):
        """
        Initialize tooltip configuration.
        
        Args:
            text (str): Tooltip text content
            font_size (int): Font size for tooltip text
            padding (int): Padding around text
            corner_radius (int): Border radius for rounded corners
            offset_x (int): Horizontal offset from target element
            offset_y (int): Vertical offset from target element
            show_delay (float): Delay in seconds before showing tooltip
            max_width (int): Maximum width before text wraps
            theme (ThemeType): Custom theme for tooltip
        """
        self.text = text
        self.font_size = font_size
        self.padding = padding
        self.corner_radius = corner_radius
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.show_delay = show_delay
        self.max_width = max_width
        self.theme = theme


class Tooltip(UIElement):
    """
    Tooltip element that displays helpful information when hovering over UI elements.
    Automatically adjusts position to stay within screen boundaries.
    """
    
    def __init__(self, config: TooltipConfig = None, element_id: Optional[str] = None):
        """
        Initialize a tooltip with configuration.
        
        Args:
            config (TooltipConfig): Configuration object for tooltip appearance
            element_id (Optional[str]): Custom element ID
        """
        self.config = config or TooltipConfig()
        
        # Calculate initial size based on text and configuration
        self._calculate_size()
        
        super().__init__(0, 0, self.width, self.height, (0, 0), element_id)
        self.theme_type = self.config.theme or ThemeManager.get_current_theme()
        self.target_element = None
        self._visible = False
        self._hover_time = 0.0
    
    def _calculate_size(self):
        """Calculate tooltip size based on text and configuration."""
        if not self.config.text:
            self.width = 100
            self.height = 30
            return
            
        # Create a temporary font to calculate size
        from .elements import FontManager
        FontManager.initialize()
        font = FontManager.get_font(None, self.config.font_size)
        
        # Wrap text to fit max width
        wrapped_lines = self._wrap_text(self.config.text, font)
        
        # Calculate maximum line width
        max_line_width = 0
        for line in wrapped_lines:
            line_width = font.size(line)[0]
            max_line_width = max(max_line_width, line_width)
        
        # Set dimensions with padding
        self.width = min(self.config.max_width, max_line_width + self.config.padding * 2)
        self.height = len(wrapped_lines) * font.get_height() + self.config.padding * 2
    
    def _wrap_text(self, text: str, font) -> List[str]:
        """
        Wrap text to fit within max width.
        
        Args:
            text (str): Text to wrap
            font: Font object for size calculation
            
        Returns:
            List[str]: List of wrapped lines
        """
        if not text:
            return [""]
            
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = font.size(test_line)[0]
            
            if test_width <= (self.config.max_width - self.config.padding * 2):
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines
    
    def set_text(self, text: str):
        """
        Update tooltip text and recalculate size.
        
        Args:
            text (str): New tooltip text
        """
        self.config.text = text
        self._calculate_size()
    
    def set_config(self, config: TooltipConfig):
        """
        Update tooltip configuration.
        
        Args:
            config (TooltipConfig): New configuration
        """
        self.config = config
        self.theme_type = config.theme or ThemeManager.get_current_theme()
        self._calculate_size()
    
    def set_target(self, element: UIElement):
        """
        Set the target element for this tooltip.
        
        Args:
            element (UIElement): Element to attach tooltip to
        """
        self.target_element = element
    
    def update_tooltip(self, inputState: InputState, dt: float, 
                      screen_width: int, screen_height: int) -> bool:
        """
        Update tooltip state and position.
        
        Args:
            mouse_pos (Tuple[int, int]): Current mouse position
            dt (float): Delta time in seconds
            screen_width (int): Screen width for boundary checking
            screen_height (int): Screen height for boundary checking
            
        Returns:
            bool: True if tooltip should be visible, False otherwise
        """
        if not self.target_element or not self.config.text:
            self._visible = False
            self._hover_time = 0.0
            return False
        if self.target_element.state == UIState.HOVERED:
            self._hover_time += dt
            if self._hover_time >= self.config.show_delay:
                self._visible = True
                self._update_position(screen_width, screen_height, inputState.mouse_pos)
            else:
                self._visible = False
        elif self.target_element.state == UIState.NORMAL:
            self._visible = False
            self._hover_time = 0.0
        else:
            self._visible = False
        
        return self._visible
    
    def _update_position(self, screen_width: int, screen_height: int, mouse_pos: Tuple[int, int]):
        """
        Update tooltip position to follow mouse and stay within screen bounds.
        
        Args:
            screen_width (int): Screen width for boundary checking
            screen_height (int): Screen height for boundary checking
            mouse_pos (Tuple[int, int]): Current mouse position
        """
        # Default position (bottom-right of mouse)
        x = mouse_pos[0] + self.config.offset_x
        y = mouse_pos[1] + self.config.offset_y
        
        # Adjust if going off-screen right
        if x + self.width > screen_width:
            x = mouse_pos[0] - self.width - self.config.offset_x
        
        # Adjust if going off-screen bottom
        if y + self.height > screen_height:
            y = mouse_pos[1] - self.height - self.config.offset_y
        
        # Ensure minimum position
        x = max(0, min(x, screen_width - self.width))
        y = max(0, min(y, screen_height - self.height))
        
        self.x = x
        self.y = y
    
    def render(self, renderer):
        """Render tooltip using OpenGL backend"""
        if not self._visible:
            return
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw border
        if theme.tooltip_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             theme.tooltip_border, fill=False, border_width=1,
                             corner_radius=self.config.corner_radius)
        
        # Draw background (simplified rectangle for OpenGL)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                         theme.tooltip_background,
                         corner_radius=self.config.corner_radius)
        
        # Draw wrapped text
        self._render_wrapped_text(renderer, actual_x, actual_y, theme)
    
    def _render_wrapped_text(self, renderer, x: int, y: int, theme):
        """Render wrapped text inside tooltip."""
        if not self.config.text:
            return
        
        from .elements import FontManager
        font = FontManager.get_font(None, self.config.font_size)
        lines = self._wrap_text(self.config.text, font)
        line_height = font.get_height()
        
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, theme.tooltip_text)
            text_x = x + (self.width - text_surface.get_width()) // 2
            text_y = y + self.config.padding + i * line_height
            
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(text_surface, text_x, text_y)
            else:
                renderer.draw_surface(text_surface, text_x, text_y)


class UITooltipManager:
    """
    Manages tooltips globally to ensure proper display and positioning.
    Supports multiple tooltips for different UI elements.
    """
    
    _instance = None
    _tooltips: Dict[str, Tooltip] = {}  # element_id -> Tooltip mapping
    _active_tooltip: Optional[Tooltip] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UITooltipManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register_tooltip(cls, element: UIElement, tooltip: Tooltip):
        """
        Register a tooltip for a UI element.
        
        Args:
            element (UIElement): The UI element that triggers the tooltip
            tooltip (Tooltip): The tooltip to show
        """
        tooltip.set_target(element)
        cls._tooltips[element.element_id] = tooltip
    
    @classmethod
    def unregister_tooltip(cls, element: UIElement):
        """
        Unregister tooltip for a UI element.
        
        Args:
            element (UIElement): The UI element to remove tooltip from
        """
        if element.element_id in cls._tooltips:
            del cls._tooltips[element.element_id]
    
    @classmethod
    def update(cls, engine: 'LunaEngine', dt: float):
        """
        Update all tooltips and determine which one should be active.
        
        Args:
            engine (LunaEngine): The main engine instance
            dt (float): Delta time in seconds
        """
        cls._active_tooltip = None
        
        # Find the tooltip that should be active (prioritize by hover time)
        best_tooltip = None
        best_hover_time = 0
        
        for tooltip in cls._tooltips.values():
            if engine.current_scene and engine.current_scene == tooltip.target_element.scene:
                if tooltip.update_tooltip(engine.input_state, dt, engine.width, engine.height):
                    if tooltip._hover_time > best_hover_time:
                        best_tooltip = tooltip
                        best_hover_time = tooltip._hover_time
        
        cls._active_tooltip = best_tooltip
    
    @classmethod
    def get_tooltip_to_render(cls, engine: 'LunaEngine') -> List[Tooltip]:
        """
        Get the currently active tooltip to render.
        
        Args:
            engine (LunaEngine): The main engine instance
            
        Returns:
            List[Tooltip]: List containing the active tooltip, or empty if none
        """
        l = []
        for tooltip in cls._tooltips.values():
            if engine.current_scene and engine.current_scene == tooltip.target_element.scene:
                if tooltip._visible:
                    l.append(tooltip)
                    
        return l
    
    @classmethod
    def render(cls, renderer):
        """Render the active tooltip."""
        if cls._active_tooltip:
            cls._active_tooltip.render(renderer)
    
    @classmethod
    def clear_all(cls):
        """Clear all registered tooltips."""
        cls._tooltips.clear()
        cls._active_tooltip = None