"""
elements.py - UI Elements Module for LunaEngine

ENGINE PATH:
lunaengine -> ui -> elements.py

DESCRIPTION:
This module provides a comprehensive collection of user interface (UI) elements
for creating interactive graphical interfaces in Pygame. It includes basic components
like buttons, labels, and text fields, as well as more complex elements like dropdown
menus, progress bars, and scrollable containers.

LIBRARIES USED:
- pygame: For graphical rendering and event handling
- numpy: For mathematical calculations (primarily in gradients)
- typing: For type hints and type annotations
- enum: For enum definitions (UI states)

MAIN CLASSES:

1. UIState (Enum):
   - Defines possible UI element states (NORMAL, HOVERED, PRESSED, DISABLED)

2. FontManager:
   - Manages Pygame fonts with lazy loading and caching
   - Ensures proper font system initialization

3. UIElement:
   - Base class for all UI elements providing common functionality
   - Handles positioning, theming, mouse interaction, and rendering

4. TextLabel:
   - Displays static or dynamic text with theme support
   - Supports custom fonts and colors

5. ImageLabel:
   - Displays images with optional scaling
   - Supports various image formats

6. Button:
   - Interactive button with hover, press, and disabled states
   - Supports text and theme-based styling

7. ImageButton:
   - Button that uses images instead of text
   - Includes state-based visual feedback

8. TextBox:
   - Interactive text input field with cursor
   - Supports keyboard input and text editing

9. ProgressBar:
   - Visual progress indicator for loading or value display
   - Shows percentage and customizable range

10. UIDraggable:
    - UI element that can be dragged around the screen
    - Provides visual feedback during dragging

11. UIGradient:
    - UI element with gradient background
    - Supports horizontal and vertical gradients with multiple colors

12. Select:
    - Selection element with arrow buttons to cycle through options
    - Compact alternative to dropdowns

13. Switch:
    - Toggle switch element with sliding animation
    - Alternative to checkboxes with smooth transitions

14. ScrollingFrame:
    - Container element with scrollable content
    - Supports both horizontal and vertical scrolling

15. Slider:
    - Interactive slider for selecting numeric values
    - Draggable thumb with value display

16. Dropdown:
    - Dropdown menu for selecting from a list of options
    - Supports scrolling for long lists and custom themes
    
17. Frame:
    - Container element for grouping UI elements
    - Supports nested frames and theme-based styling

This module forms the core of LunaEngine's UI system, providing a flexible and
themeable foundation for building complex user interfaces in Pygame applications.
"""

import pygame
import numpy as np
from typing import Optional, Callable, List, Tuple, Any
from enum import Enum
from abc import ABC, abstractmethod
from .themes import ThemeManager, ThemeType

class _UIDGenerator:
    """
    Internal class for generating unique IDs for UI elements.
    
    Generates IDs in the format: ui_{element_type}_{counter}
    Example: ui_button_1, ui_label_2, ui_dropdown_1
    """
    
    def __init__(self):
        self._counters = {}
    
    def generate_id(self, element_type: str) -> str:
        """
        Generate a unique ID for a UI element.
        
        Args:
            element_type (str): Type of the UI element (e.g., 'button', 'label')
            
        Returns:
            str: Unique ID in format "ui_{element_type}_{counter}"
        """
        if element_type not in self._counters:
            self._counters[element_type] = 0
        
        self._counters[element_type] += 1
        return f"ui_{element_type}_{self._counters[element_type]}"

# Global ID generator instance
_uid_generator = _UIDGenerator()

class UIState(Enum):
    """Enumeration of possible UI element states."""
    NORMAL = 0
    HOVERED = 1
    PRESSED = 2
    DISABLED = 3

class FontManager:
    """Manages fonts and ensures Pygame font system is initialized."""
    
    _initialized = False
    _default_fonts = {}
    
    @classmethod
    def initialize(cls):
        """
        Initialize the font system.
        
        This method should be called before using any font-related functionality.
        It initializes Pygame's font module if not already initialized.
        """
        if not cls._initialized:
            pygame.font.init()
            cls._initialized = True
    
    @classmethod
    def get_font(cls, font_name: Optional[str] = None, font_size: int = 24):
        """
        Get a font object for rendering text.
        
        Args:
            font_name (Optional[str]): Path to font file or None for default system font.
            font_size (int): Size of the font in pixels.
            
        Returns:
            pygame.font.Font: A font object ready for text rendering.
        """
        if not cls._initialized:
            cls.initialize()
            
        if font_name is None:
            key = (None, font_size)
            if key not in cls._default_fonts:
                cls._default_fonts[key] = pygame.font.Font(None, font_size)
            return cls._default_fonts[key]
        else:
            return pygame.font.Font(font_name, font_size)

class UIElement(ABC):
    """
    Base class for all UI elements providing common functionality.
    
    Attributes:
        element_id (str): Unique identifier for this element in format ui_{type}_{counter}
        x (int): X coordinate position
        y (int): Y coordinate position
        width (int): Width of the element in pixels
        height (int): Height of the element in pixels
        root_point (Tuple[float, float]): Anchor point for positioning
        state (UIState): Current state of the element
        visible (bool): Whether element is visible
        enabled (bool): Whether element is enabled
        children (List[UIElement]): Child elements
        parent (UIElement): Parent element
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, root_point: Tuple[float, float] = (0, 0),
                 element_id: Optional[str] = None):
        """
        Initialize a UI element with position and dimensions.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            width (int): Width of the element in pixels.
            height (int): Height of the element in pixels.
            root_point (Tuple[float, float]): Anchor point for positioning where (0,0) is top-left 
                                            and (1,1) is bottom-right.
            element_id (Optional[str]): Custom element ID. If None, generates automatic ID.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.root_point = root_point
        self.state = UIState.NORMAL
        self.visible = True
        self.enabled = True
        self.children = []
        self.parent = None
        
        # Generate unique ID using element type name
        element_type = self.__class__.__name__.lower()
        self.element_id = element_id if element_id else _uid_generator.generate_id(element_type)
    
    def get_id(self) -> str:
        """
        Get the unique ID of this UI element.
        
        Returns:
            str: The unique element ID
        """
        return self.element_id
        
    def set_id(self, new_id: str) -> None:
        """
        Set a new unique ID for this UI element.
        
        Args:
            new_id (str): The new unique ID to set
        """
        self.element_id = new_id
        
    def get_actual_position(self, parent_width: int = 0, parent_height: int = 0) -> Tuple[int, int]:
        """
        Calculate actual screen position based on root_point anchor.
        
        Args:
            parent_width (int): Width of parent element if applicable.
            parent_height (int): Height of parent element if applicable.
            
        Returns:
            Tuple[int, int]: The actual (x, y) screen coordinates.
        """
        anchor_x, anchor_y = self.root_point
        
        if self.parent:
            parent_x, parent_y = self.parent.get_actual_position()
            actual_x = parent_x + self.x - int(self.width * anchor_x)
            actual_y = parent_y + self.y - int(self.height * anchor_y)
        else:
            actual_x = self.x - int(self.width * anchor_x)
            actual_y = self.y - int(self.height * anchor_y)
            
        return (actual_x, actual_y)
        
    def add_child(self, child):
        """
        Add a child element to this UI element.
        
        Args:
            child: The child UI element to add.
        """
        child.parent = self
        self.children.append(child)
        
    def update(self, dt: float):
        """
        Update element state.
        
        Args:
            dt (float): Delta time in seconds since last update.
        """
        pass
    
    def update_theme(self, theme_type: ThemeType):
        """
        Update the theme for this element and all its children.
        
        Args:
            theme_type (ThemeType): The new theme to apply.
        """
        self.theme_type = theme_type
        for child in self.children:
            if hasattr(child, 'update_theme'):
                child.update_theme(theme_type)    
    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """
        Update element with current mouse state for interaction.
        
        Args:
            mouse_pos (Tuple[int, int]): Current mouse position (x, y).
            mouse_pressed (bool): Whether mouse button is currently pressed.
            dt (float): Delta time in seconds.
        """
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if (actual_x <= mouse_pos[0] <= actual_x + self.width and 
            actual_y <= mouse_pos[1] <= actual_y + self.height):
            
            if mouse_pressed:
                self.state = UIState.PRESSED
                self.on_click()
            else:
                self.state = UIState.HOVERED
                self.on_hover()
        else:
            self.state = UIState.NORMAL
            
        for child in self.children:
            child._update_with_mouse(mouse_pos, mouse_pressed, dt)


    def render_pygame(self, renderer):
        """
        Render this element using Pygame backend.
        Override this in subclasses for Pygame-specific rendering.
        """
        # Default implementation - render children only
        for child in self.children:
            child.render(renderer)
    
    def render_opengl(self, renderer):
        """
        Render this element using OpenGL backend.  
        Override this in subclasses for OpenGL-specific rendering.
        """
        # Default implementation - render children only
        for child in self.children:
            child.render(renderer)
    
    def render(self, renderer):
        """Universal render method"""
        if not self.visible:
            return
            
        # Proper OpenGL detection
        if hasattr(renderer, 'render_opengl'):
            self.render_opengl(renderer)
        else:
            self.render_pygame(renderer)
    
    def on_click(self):
        """Called when element is clicked by the user."""
        pass
        
    def on_hover(self):
        """Called when mouse hovers over the element."""
        pass


class TextLabel(UIElement):
    """UI element for displaying text labels."""
    
    def __init__(self, x: int, y: int, text: str, font_size: int = 24, 
                 color: Optional[Tuple[int, int, int]] = None,
                 font_name: Optional[str] = None, 
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        """
        Initialize a text label element.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            text (str): The text to display.
            font_size (int): Size of the font in pixels.
            color (Optional[Tuple[int, int, int]]): Custom text color (overrides theme).
            font_name (Optional[str]): Path to font file or None for default font.
            root_point (Tuple[float, float]): Anchor point for positioning.
            theme (ThemeType): Theme to use for text color.
            element_id (Optional[str]): Custom element ID. If None, generates automatic ID.
        """
        FontManager.initialize()
        temp_color = color or (255, 255, 255)
        font = FontManager.get_font(font_name, font_size)
        text_surface = font.render(text, True, temp_color)
        
        super().__init__(x, y, text_surface.get_width(), text_surface.get_height(), root_point, element_id)
        self.text = text
        self.font_size = font_size
        self.custom_color = color
        self.font_name = font_name
        self._font = None
        
        self.theme_type = theme or ThemeManager.get_current_theme()
    
    def update_theme(self, theme_type):
        """Update theme for text label."""
        return super().update_theme(theme_type)
    
    @property
    def font(self):
        """
        Get the font object (lazy loading).
        
        Returns:
            pygame.font.Font: The font object for this label.
        """
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
        
    def set_text(self, text: str):
        """
        Update the displayed text and recalculate element size.
        
        Args:
            text (str): The new text to display.
        """
        self.text = text
        text_surface = self.font.render(text, True, self.custom_color or (255, 255, 255))
        self.width = text_surface.get_width()
        self.height = text_surface.get_height()
    
    def set_theme(self, theme_type: ThemeType):
        """
        Set the theme for this text label.
        
        Args:
            theme_type (ThemeType): The theme to apply.
        """
        self.theme_type = theme_type
    
    def _get_text_color(self) -> Tuple[int, int, int]:
        """
        Get the current text color.
        
        Returns:
            Tuple[int, int, int]: RGB color tuple for the text.
        """
        if self.custom_color:
            return self.custom_color
        return ThemeManager.get_theme(self.theme_type).label_text
        
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        text_color = self._get_text_color()
        
        text_surface = self.font.render(self.text, True, text_color)
        
        renderer.draw_surface(text_surface, actual_x, actual_y)
        
        # Render children
        super().render_pygame(renderer)
            
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        text_color = self._get_text_color()
        
        text_surface = self.font.render(self.text, True, text_color)
        
        # Use render_surface instead of draw_surface
        if hasattr(renderer, 'render_surface'):
            renderer.render_surface(text_surface, actual_x, actual_y)
        
        super().render_opengl(renderer)

class ImageLabel(UIElement):
    def __init__(self, x: int, y: int, image_path: str, 
                 width: Optional[int] = None, height: Optional[int] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 element_id: Optional[str] = None):
        self.image_path = image_path
        self._image = None
        self._load_image()
        
        if width is None:
            width = self._image.get_width()
        if height is None:
            height = self._image.get_height()
            
        super().__init__(x, y, width, height, root_point, element_id)

        
    def _load_image(self):
        """Load and prepare the image."""
        try:
            self._image = pygame.image.load(self.image_path).convert_alpha()
        except:
            self._image = pygame.Surface((100, 100))
            self._image.fill((255, 0, 255))
        
    def set_image(self, image_path: str):
        """
        Change the displayed image.
        
        Args:
            image_path (str): Path to the new image file.
        """
        self.image_path = image_path
        self._load_image()
        
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if self._image.get_width() != self.width or self._image.get_height() != self.height:
            scaled_image = pygame.transform.scale(self._image, (self.width, self.height))
            renderer.draw_surface(scaled_image, actual_x, actual_y)
        else:
            renderer.draw_surface(self._image, actual_x, actual_y)
            
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if self._image.get_width() != self.width or self._image.get_height() != self.height:
            scaled_image = pygame.transform.scale(self._image, (self.width, self.height))
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(scaled_image, actual_x, actual_y)
            else:
                renderer.draw_surface(scaled_image, actual_x, actual_y)
        else:
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(self._image, actual_x, actual_y)
            else:
                renderer.draw_surface(self._image, actual_x, actual_y)
                
        super().render_opengl(renderer)

class Button(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, text: str = "", 
                 font_size: int = 20, font_name: Optional[str] = None, 
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.text = text
        self.font_size = font_size
        self.font_name = font_name
        self.on_click_callback = None
        self._font = None
        self._was_pressed = False
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
    @property
    def font(self):
        """Get the font object (lazy loading)."""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
        
    def set_on_click(self, callback: Callable):
        """
        Set the callback function for click events.
        
        Args:
            callback (Callable): Function to call when button is clicked.
        """
        self.on_click_callback = callback
        
    def set_theme(self, theme_type: ThemeType):
        """
        Set the theme for this button.
        
        Args:
            theme_type (ThemeType): The theme to apply.
        """
        self.theme_type = theme_type
    
    def _get_colors(self):
        """
        Get colors from the current theme.
        
        Returns:
            UITheme: The current theme object.
        """
        return ThemeManager.get_theme(self.theme_type)
    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update button with mouse interaction."""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        mouse_over = (actual_x <= mouse_pos[0] <= actual_x + self.width and 
                     actual_y <= mouse_pos[1] <= actual_y + self.height)
        
        if mouse_over:
            if mouse_pressed:
                self.state = UIState.PRESSED
                if not self._was_pressed and self.on_click_callback:
                    self.on_click_callback()
                self._was_pressed = True
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False
            
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def _get_color_for_state(self) -> Tuple[int, int, int]:
        """
        Get the appropriate color for the current button state.
        
        Returns:
            Tuple[int, int, int]: RGB color tuple for the current state.
        """
        theme = self._get_colors()
        
        if self.state == UIState.NORMAL:
            return theme.button_normal
        elif self.state == UIState.HOVERED:
            return theme.button_hover
        elif self.state == UIState.PRESSED:
            return theme.button_pressed
        else:
            return theme.button_disabled
    
    def _get_text_color(self) -> Tuple[int, int, int]:
        """
        Get the text color from the current theme.
        
        Returns:
            Tuple[int, int, int]: RGB color tuple for the text.
        """
        return self._get_colors().button_text
            
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = self._get_colors()
        
        color = self._get_color_for_state()
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, color)
        
        if theme.button_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             theme.button_border, fill=False)
        
        if self.text:
            text_color = self._get_text_color()
            text_surface = self.font.render(self.text, True, text_color)
            text_x = actual_x + (self.width - text_surface.get_width()) // 2
            text_y = actual_y + (self.height - text_surface.get_height()) // 2
            renderer.draw_surface(text_surface, text_x, text_y)
            
        # Render children
        super().render_pygame(renderer)
            
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = self._get_colors()
        
        # First: Draw the border if applicable
        if theme.button_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                            theme.button_border, fill=False, border_width=1)
        
        # SECOND: Draw the button background
        color = self._get_color_for_state()
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, color)
        
        # Finally: Draw the text on top
        if self.text:
            text_color = self._get_text_color()
            text_surface = self.font.render(self.text, True, text_color)
            text_x = actual_x + (self.width - text_surface.get_width()) // 2
            text_y = actual_y + (self.height - text_surface.get_height()) // 2
            
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(text_surface, text_x, text_y)
            else:
                renderer.draw_surface(text_surface, text_x, text_y)
                    
        super().render_opengl(renderer)

class ImageButton(UIElement):
    def __init__(self, x: int, y: int, image_path: str, 
                 width: Optional[int] = None, height: Optional[int] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        self.image_path = image_path
        self._image = None
        self._load_image()
        
        if width is None:
            width = self._image.get_width()
        if height is None:
            height = self._image.get_height()
            
        super().__init__(x, y, width, height, root_point, element_id)
        self.on_click_callback = None
        self._was_pressed = False
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
    def _load_image(self):
        """Load the button image."""
        try:
            self._image = pygame.image.load(self.image_path).convert_alpha()
        except:
            self._image = pygame.Surface((100, 100))
            self._image.fill((0, 255, 255))
        
    def set_on_click(self, callback: Callable):
        """
        Set the callback function for click events.
        
        Args:
            callback (Callable): Function to call when button is clicked.
        """
        self.on_click_callback = callback
        
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update image button with mouse interaction."""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        mouse_over = (actual_x <= mouse_pos[0] <= actual_x + self.width and 
                     actual_y <= mouse_pos[1] <= actual_y + self.height)
        
        if mouse_over:
            if mouse_pressed:
                self.state = UIState.PRESSED
                if not self._was_pressed and self.on_click_callback:
                    self.on_click_callback()
                self._was_pressed = True
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False
            
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def _get_overlay_color(self) -> Optional[Tuple[int, int, int]]:
        """
        Get overlay color based on button state.
        
        Returns:
            Optional[Tuple[int, int, int]]: Overlay color or None for no overlay.
        """
        if self.state == UIState.HOVERED:
            return (255, 255, 255, 50)  # Semi-transparent white
        elif self.state == UIState.PRESSED:
            return (0, 0, 0, 50)  # Semi-transparent black
        return None
            
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if self._image.get_width() != self.width or self._image.get_height() != self.height:
            scaled_image = pygame.transform.scale(self._image, (self.width, self.height))
            renderer.draw_surface(scaled_image, actual_x, actual_y)
        else:
            renderer.draw_surface(self._image, actual_x, actual_y)
        
        overlay_color = self._get_overlay_color()
        if overlay_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, overlay_color)
            
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if self._image.get_width() != self.width or self._image.get_height() != self.height:
            scaled_image = pygame.transform.scale(self._image, (self.width, self.height))
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(scaled_image, actual_x, actual_y)
            else:
                renderer.draw_surface(scaled_image, actual_x, actual_y)
        else:
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(self._image, actual_x, actual_y)
            else:
                renderer.draw_surface(self._image, actual_x, actual_y)
        
        overlay_color = self._get_overlay_color()
        if overlay_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, overlay_color)
                
        super().render_opengl(renderer)

class TextBox(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str = "", font_size: int = 20, font_name: Optional[str] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.placeholder_text = text
        self.text = ""
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self._text_surface = None
        self._text_rect = None
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.focused = False
        self._needs_redraw = True
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
    @property
    def font(self):
        """Get the font object with lazy loading."""
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    def _update_text_surface(self):
        """Update text surface cache when text changes."""
        display_text = self.text if self.text else self.placeholder_text
        text_color = self._get_text_color()
        
        if display_text:
            self._text_surface = self.font.render(display_text, True, text_color)
            self._text_rect = self._text_surface.get_rect()
        else:
            self._text_surface = None
            self._text_rect = None
        
        self._needs_redraw = True
    
    def _get_text_color(self):
        """Get appropriate text color based on state."""
        theme = ThemeManager.get_theme(self.theme_type)
        if not self.text and self.placeholder_text:
            # Lighter color for placeholder
            return tuple(max(0, c - 80) for c in theme.dropdown_text)
        return theme.dropdown_text
    
    def _get_background_color(self):
        """Get background color based on state."""
        theme = ThemeManager.get_theme(self.theme_type)
        if self.state == UIState.DISABLED:
            return (100, 100, 100)
        elif self.focused:
            return theme.dropdown_expanded
        else:
            return theme.dropdown_normal
    
    def set_text(self, text: str):
        """
        Set the text content.
        
        Args:
            text (str): New text content.
        """
        if self.text != text:
            self.text = text
            self.cursor_pos = len(text)
            self._update_text_surface()
    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update text box with mouse interaction - OPTIMIZED"""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            self.focused = False
            return
        
        actual_x, actual_y = self.get_actual_position()
        mouse_over = (
            actual_x <= mouse_pos[0] <= actual_x + self.width and 
            actual_y <= mouse_pos[1] <= actual_y + self.height
        )
        
        # Handle focus changes
        old_focused = self.focused
        if mouse_pressed:
            self.focused = mouse_over
            if mouse_over:
                self.state = UIState.PRESSED
                self._needs_redraw = True
            else:
                self.state = UIState.NORMAL
                self._needs_redraw = True
        else:
            self.state = UIState.HOVERED if mouse_over else UIState.NORMAL
        
        # Update cursor blink only when focused
        if self.focused:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:  # Blink every 0.5 seconds
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
                self._needs_redraw = True
        elif old_focused != self.focused:
            # Lost focus, ensure cursor is visible next time
            self.cursor_visible = True
            self.cursor_timer = 0
            self._needs_redraw = True
        
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def handle_key_input(self, event):
        """
        Handle keyboard input when focused - OPTIMIZED
        
        Args:
            event: Pygame keyboard event.
        """
        if not self.focused or event.type != pygame.KEYDOWN:
            return
        
        text_changed = False
        cursor_moved = False
        
        # Handle special keys
        if event.key == pygame.K_BACKSPACE:
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
                text_changed = True
                cursor_moved = True
                
        elif event.key == pygame.K_DELETE:
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                text_changed = True
                
        elif event.key == pygame.K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            cursor_moved = True
            
        elif event.key == pygame.K_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            cursor_moved = True
            
        elif event.key == pygame.K_HOME:
            self.cursor_pos = 0
            cursor_moved = True
            
        elif event.key == pygame.K_END:
            self.cursor_pos = len(self.text)
            cursor_moved = True
            
        elif event.unicode and event.unicode.isprintable():
            # Insert character at cursor position
            self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
            self.cursor_pos += len(event.unicode)
            text_changed = True
            cursor_moved = True
        
        # Update rendering if needed
        if text_changed:
            self._update_text_surface()
        elif cursor_moved:
            self.cursor_visible = True
            self.cursor_timer = 0
            self._needs_redraw = True
    
    def _get_cursor_position(self, actual_x: int, actual_y: int) -> Tuple[int, int]:
        """Calculate cursor position - IMPROVED with bounds checking"""
        # Default position for empty text or cursor at start
        base_x = actual_x + 5
        base_y = actual_y + (self.height - self.font.get_height()) // 2
        
        if not self.text or self.cursor_pos == 0:
            return base_x, base_y
        
        # Only measure text up to cursor position for efficiency
        text_before_cursor = self.text[:self.cursor_pos]
        text_width = self.font.size(text_before_cursor)[0]
        
        # Calculate cursor position with scrolling if needed
        cursor_x = base_x + text_width
        
        # Apply scrolling if text is too long
        if self._text_surface and self._text_rect.width > self.width - 10:
            clip_width = self.width - 10
            if text_width > clip_width:
                # Text needs scrolling - adjust cursor position
                scroll_offset = text_width - clip_width + 5
                cursor_x = base_x + text_width - scroll_offset
        
        return cursor_x, base_y
    
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw background
        bg_color = self._get_background_color()
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color)
        
        # Draw border
        if theme.dropdown_border:
            border_color = theme.text_primary if self.focused else theme.dropdown_border
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color, fill=False)
        
        # Draw text
        self._render_text_content(renderer, actual_x, actual_y, theme)
        
        # Draw cursor
        if self.focused and self.cursor_visible:
            cursor_x, cursor_y = self._get_cursor_position(actual_x, actual_y)
            cursor_height = self.height - 10
            renderer.draw_rect(cursor_x, cursor_y, 2, cursor_height, theme.dropdown_text)
        
        self._needs_redraw = False
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend - FIXED cursor visibility"""
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # FIRST: Draw border
        if theme.dropdown_border:
            border_color = theme.text_primary if self.focused else theme.dropdown_border
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color, fill=False)
        
        # THEN: Draw background
        bg_color = self._get_background_color()
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color)
        
        # Draw text
        self._render_text_content(renderer, actual_x, actual_y, theme, opengl=True)
        
        if self.focused and self.cursor_visible:
            cursor_x, cursor_y = self._get_cursor_position(actual_x, actual_y)
            cursor_height = self.font.get_height()
            cursor_y = actual_y + (self.height - cursor_height) // 2
            
            cursor_color = theme.text_primary
            
            # FIXED: Ensure cursor is within textbox bounds
            if cursor_x < actual_x + self.width - 2:  # Leave 2px margin
                renderer.draw_rect(cursor_x, cursor_y, 5, cursor_height, cursor_color)
        
        self._needs_redraw = False
        
        # Render children (important for any child elements)
        for child in self.children:
            child.render_opengl(renderer)
    
    def _render_text_content(self, renderer, actual_x: int, actual_y: int, theme, opengl=False):
        """Helper method to render text content - FIXED subsurface error"""
        if self._text_surface is None:
            return
            
        text_y = actual_y + (self.height - self._text_rect.height) // 2
        
        # Clip text if too long - FIXED: Check bounds before creating subsurface
        if self._text_rect.width > self.width - 10:
            clip_width = self.width - 10
            
            if self.focused and self.text:
                # Calculate scroll offset for focused text with cursor
                cursor_x = self.font.size(self.text[:self.cursor_pos])[0]
                if cursor_x > clip_width:
                    scroll_offset = cursor_x - clip_width + 10
                    # FIXED: Ensure source_rect is within surface bounds
                    source_rect = pygame.Rect(
                        max(0, min(scroll_offset, self._text_rect.width - clip_width)),
                        0,
                        min(clip_width, self._text_rect.width),
                        self._text_rect.height
                    )
                    if (source_rect.width > 0 and source_rect.height > 0 and 
                        source_rect.right <= self._text_rect.width and 
                        source_rect.bottom <= self._text_rect.height):
                        clipped_surface = self._text_surface.subsurface(source_rect)
                        if opengl and hasattr(renderer, 'render_surface'):
                            renderer.render_surface(clipped_surface, actual_x + 5, text_y)
                        else:
                            renderer.draw_surface(clipped_surface, actual_x + 5, text_y)
                    else:
                        # Fallback: render without clipping if bounds are invalid
                        if opengl and hasattr(renderer, 'render_surface'):
                            renderer.render_surface(self._text_surface, actual_x + 5, text_y)
                        else:
                            renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
                else:
                    # Text fits without scrolling
                    if opengl and hasattr(renderer, 'render_surface'):
                        renderer.render_surface(self._text_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
            else:
                # Not focused - just clip from start
                source_rect = pygame.Rect(0, 0, min(clip_width, self._text_rect.width), self._text_rect.height)
                if (source_rect.width > 0 and source_rect.height > 0 and 
                    source_rect.right <= self._text_rect.width and 
                    source_rect.bottom <= self._text_rect.height):
                    clipped_surface = self._text_surface.subsurface(source_rect)
                    if opengl and hasattr(renderer, 'render_surface'):
                        renderer.render_surface(clipped_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(clipped_surface, actual_x + 5, text_y)
                else:
                    # Fallback: render without clipping
                    if opengl and hasattr(renderer, 'render_surface'):
                        renderer.render_surface(self._text_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
        else:
            # Text fits normally
            if opengl and hasattr(renderer, 'render_surface'):
                renderer.render_surface(self._text_surface, actual_x + 5, text_y)
            else:
                renderer.draw_surface(self._text_surface, actual_x + 5, text_y)

class ProgressBar(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 min_val: float = 0, max_val: float = 100, value: float = 0,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        
        self.theme_type = theme or ThemeManager.get_current_theme()
    
    def set_value(self, value: float):
        """
        Set the current progress value.
        
        Args:
            value (float): New progress value.
        """
        self.value = max(self.min_val, min(self.max_val, value))
    
    def get_percentage(self) -> float:
        """
        Get progress as percentage.
        
        Returns:
            float: Progress percentage (0-100).
        """
        return (self.value - self.min_val) / (self.max_val - self.min_val) * 100
    
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.slider_track)
        
        # Draw progress
        progress_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        if progress_width > 0:
            renderer.draw_rect(actual_x, actual_y, progress_width, self.height, theme.button_normal)
        
        # Draw border
        if theme.border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.border, fill=False)
        
        # Draw text
        font = pygame.font.Font(None, 12)
        text = f"{self.get_percentage():.1f}%"
        text_surface = font.render(text, True, theme.slider_text)
        text_x = actual_x + (self.width - text_surface.get_width()) // 2
        text_y = actual_y + (self.height - text_surface.get_height()) // 2
        renderer.draw_surface(text_surface, text_x, text_y)
        
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw border
        if theme.border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.border, fill=False)
        
        # Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.slider_track)
        
        # Draw progress
        progress_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        if progress_width > 0:
            renderer.draw_rect(actual_x, actual_y, progress_width, self.height, theme.button_normal)
        
        # Draw text
        font = pygame.font.Font(None, 12)
        text = f"{self.get_percentage():.1f}%"
        text_surface = font.render(text, True, theme.slider_text)
        text_x = actual_x + (self.width - text_surface.get_width()) // 2
        text_y = actual_y + (self.height - text_surface.get_height()) // 2
        
        if hasattr(renderer, 'render_surface'):
            renderer.render_surface(text_surface, text_x, text_y)
        else:
            renderer.draw_surface(text_surface, text_x, text_y)
                
        super().render_opengl(renderer)

class UIDraggable(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.dragging = False
        self.drag_offset = (0, 0)
        
        self.theme_type = theme or ThemeManager.get_current_theme()

    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update draggable element with mouse interaction."""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        mouse_over = (actual_x <= mouse_pos[0] <= actual_x + self.width and 
                     actual_y <= mouse_pos[1] <= actual_y + self.height)
        
        if mouse_pressed and mouse_over and not self.dragging:
            self.dragging = True
            self.drag_offset = (mouse_pos[0] - actual_x, mouse_pos[1] - actual_y)
            self.state = UIState.PRESSED
        elif not mouse_pressed:
            self.dragging = False
            self.state = UIState.HOVERED if mouse_over else UIState.NORMAL
        
        if self.dragging and mouse_pressed:
            new_x = mouse_pos[0] - self.drag_offset[0] + int(self.width * self.root_point[0])
            new_y = mouse_pos[1] - self.drag_offset[1] + int(self.height * self.root_point[1])
            self.x = new_x
            self.y = new_y
            
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        color = theme.button_normal
        if self.dragging:
            color = theme.button_pressed
        elif self.state == UIState.HOVERED:
            color = theme.button_hover
            
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, color)
        
        if theme.button_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.button_border, fill=False)
        
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        color = theme.button_normal
        if self.dragging:
            color = theme.button_pressed
        elif self.state == UIState.HOVERED:
            color = theme.button_hover
        
        # Draw border
        if theme.button_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.button_border, fill=False)
            
        # Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, color)
        
        
        super().render_opengl(renderer)

class UIGradient(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 colors: List[Tuple[int, int, int]],
                 direction: str = "horizontal",
                 root_point: Tuple[float, float] = (0, 0),
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.colors = colors
        self.direction = direction
        self._gradient_surface = None
        self._generate_gradient()
    
    def _generate_gradient(self):
        """Generate the gradient surface."""
        self._gradient_surface = pygame.Surface((self.width, self.height))
        
        if self.direction == "horizontal":
            for x in range(self.width):
                ratio = x / (self.width - 1) if self.width > 1 else 0
                color = self._interpolate_colors(ratio)
                pygame.draw.line(self._gradient_surface, color, (x, 0), (x, self.height))
        else:  # vertical
            for y in range(self.height):
                ratio = y / (self.height - 1) if self.height > 1 else 0
                color = self._interpolate_colors(ratio)
                pygame.draw.line(self._gradient_surface, color, (0, y), (self.width, y))
    
    def _interpolate_colors(self, ratio: float) -> Tuple[int, int, int]:
        """
        Interpolate between gradient colors.
        
        Args:
            ratio (float): Interpolation ratio (0-1).
            
        Returns:
            Tuple[int, int, int]: Interpolated color.
        """
        if len(self.colors) == 1:
            return self.colors[0]
        
        segment = ratio * (len(self.colors) - 1)
        segment_index = int(segment)
        segment_ratio = segment - segment_index
        
        if segment_index >= len(self.colors) - 1:
            return self.colors[-1]
        
        color1 = self.colors[segment_index]
        color2 = self.colors[segment_index + 1]
        
        return (
            int(color1[0] + (color2[0] - color1[0]) * segment_ratio),
            int(color1[1] + (color2[1] - color1[1]) * segment_ratio),
            int(color1[2] + (color2[2] - color1[2]) * segment_ratio)
        )
    
    def set_colors(self, colors: List[Tuple[int, int, int]]):
        """
        Set new gradient colors.
        
        Args:
            colors (List[Tuple[int, int, int]]): New gradient colors.
        """
        self.colors = colors
        self._generate_gradient()
    
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        renderer.draw_surface(self._gradient_surface, actual_x, actual_y)
        
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if hasattr(renderer, 'render_surface'):
            renderer.render_surface(self._gradient_surface, actual_x, actual_y)
        else:
            renderer.draw_surface(self._gradient_surface, actual_x, actual_y)
                
        super().render_opengl(renderer)

class Select(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 options: List[str], font_size: int = 20, font_name: Optional[str] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.options = options
        self.selected_index = 0
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self.on_selection_changed = None
        
        # Fix: Add click cooldown to prevent rapid switching
        self._click_cooldown = 0
        self._click_delay = 0.3  # 300ms between clicks
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
        # Arrow button dimensions
        self.arrow_width = 20
        
        # Pre-create arrow surfaces for consistent rendering
        self._left_arrow_surface = None
        self._right_arrow_surface = None
        self._create_arrow_surfaces()
        
    def _create_arrow_surfaces(self):
        """Create arrow surfaces for both backends"""
        # Create left arrow surface (points left)
        self._left_arrow_surface = pygame.Surface((15, 10), pygame.SRCALPHA)
        left_arrow_points = [(10, 0), (0, 5), (10, 10)]
        pygame.draw.polygon(self._left_arrow_surface, (255, 255, 255), left_arrow_points)
        
        # Create right arrow surface (points right)  
        self._right_arrow_surface = pygame.Surface((15, 10), pygame.SRCALPHA)
        right_arrow_points = [(0, 0), (10, 5), (0, 10)]
        pygame.draw.polygon(self._right_arrow_surface, (255, 255, 255), right_arrow_points)
        
    @property
    def font(self):
        """Get the font object."""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    def next_option(self):
        """Select the next option."""
        if self.options:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            if self.on_selection_changed:
                self.on_selection_changed(self.selected_index, self.options[self.selected_index])
    
    def previous_option(self):
        """Select the previous option."""
        if self.options:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            if self.on_selection_changed:
                self.on_selection_changed(self.selected_index, self.options[self.selected_index])
    
    def set_selected_index(self, index: int):
        """
        Set selected option by index.
        
        Args:
            index (int): Index of option to select.
        """
        if 0 <= index < len(self.options):
            self.selected_index = index
    
    def set_on_selection_changed(self, callback: Callable[[int, str], None]):
        """
        Set selection change callback.
        
        Args:
            callback (Callable): Function called when selection changes.
        """
        self.on_selection_changed = callback
    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update select element with mouse interaction."""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        # Update cooldown
        if self._click_cooldown > 0:
            self._click_cooldown -= dt
            
        actual_x, actual_y = self.get_actual_position()
        
        # Check left arrow
        left_arrow_rect = (actual_x, actual_y, self.arrow_width, self.height)
        left_arrow_hover = (left_arrow_rect[0] <= mouse_pos[0] <= left_arrow_rect[0] + left_arrow_rect[2] and
                           left_arrow_rect[1] <= mouse_pos[1] <= left_arrow_rect[1] + left_arrow_rect[3])
        
        # Check right arrow
        right_arrow_rect = (actual_x + self.width - self.arrow_width, actual_y, self.arrow_width, self.height)
        right_arrow_hover = (right_arrow_rect[0] <= mouse_pos[0] <= right_arrow_rect[0] + right_arrow_rect[2] and
                            right_arrow_rect[1] <= mouse_pos[1] <= right_arrow_rect[1] + right_arrow_rect[3])
        
        # Only process click if not in cooldown
        if mouse_pressed and self._click_cooldown <= 0:
            if left_arrow_hover:
                self.previous_option()
                self._click_cooldown = self._click_delay
            elif right_arrow_hover:
                self.next_option()
                self._click_cooldown = self._click_delay
        
        self.state = UIState.HOVERED if (left_arrow_hover or right_arrow_hover) else UIState.NORMAL
            
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw background
        if self.state == UIState.NORMAL:
            bg_color = theme.dropdown_normal
        else:
            bg_color = theme.dropdown_hover
            
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color)
        
        # Draw border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             theme.dropdown_border, fill=False)
        
        # Draw arrows and text
        self._render_select_content(renderer, actual_x, actual_y, theme, opengl=False)
        
        # Render children
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # FIRST: Draw border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                            theme.dropdown_border, fill=False, border_width=1)
        
        # THEN: Draw background
        if self.state == UIState.NORMAL:
            bg_color = theme.dropdown_normal
        else:
            bg_color = theme.dropdown_hover
            
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color)
        
        # FINALLY: Draw arrows and text
        self._render_select_content(renderer, actual_x, actual_y, theme, opengl=True)
        
        # Render children
        super().render_opengl(renderer)
    
    def _render_select_content(self, renderer, actual_x: int, actual_y: int, theme, opengl=False):
        """Helper method to render select content for both backends"""
        arrow_color = theme.dropdown_text
        
        # Calculate arrow positions
        left_arrow_x = actual_x + 5
        left_arrow_y = actual_y + (self.height - 10) // 2
        
        right_arrow_x = actual_x + self.width - 20
        right_arrow_y = actual_y + (self.height - 10) // 2
        
        # Create colored arrow surfaces
        if self._left_arrow_surface and self._right_arrow_surface:
            # Create temporary surfaces with the correct theme color
            left_arrow_colored = self._left_arrow_surface.copy()
            left_arrow_colored.fill(arrow_color, special_flags=pygame.BLEND_RGBA_MULT)
            
            right_arrow_colored = self._right_arrow_surface.copy()
            right_arrow_colored.fill(arrow_color, special_flags=pygame.BLEND_RGBA_MULT)
            
            # Draw arrows using surface rendering (works for both backends)
            if opengl:
                if hasattr(renderer, 'render_surface'):
                    renderer.render_surface(left_arrow_colored, left_arrow_x, left_arrow_y)
                    renderer.render_surface(right_arrow_colored, right_arrow_x, right_arrow_y)
                else:
                    # Fallback for OpenGL renderers without render_surface
                    renderer.draw_surface(left_arrow_colored, left_arrow_x, left_arrow_y)
                    renderer.draw_surface(right_arrow_colored, right_arrow_x, right_arrow_y)
            else:
                # Pygame backend
                renderer.draw_surface(left_arrow_colored, left_arrow_x, left_arrow_y)
                renderer.draw_surface(right_arrow_colored, right_arrow_x, right_arrow_y)
        else:
            # Fallback: draw simple triangles if surfaces aren't available
            self._draw_fallback_arrows(renderer, actual_x, actual_y, arrow_color, opengl)
        
        # Draw selected text
        if self.options:
            text = self.options[self.selected_index]
            if len(text) > 15:
                text = text[:15] + "..."
            text_surface = self.font.render(text, True, theme.dropdown_text)
            text_x = actual_x + (self.width - text_surface.get_width()) // 2
            text_y = actual_y + (self.height - text_surface.get_height()) // 2
            
            if opengl and hasattr(renderer, 'render_surface'):
                renderer.render_surface(text_surface, text_x, text_y)
            else:
                renderer.draw_surface(text_surface, text_x, text_y)
    
    def _draw_fallback_arrows(self, renderer, actual_x: int, actual_y: int, arrow_color, opengl=False):
        """Fallback arrow drawing method"""
        # Left arrow points (points left)
        left_arrow_points = [
            (actual_x + 15, actual_y + self.height // 2 - 5),
            (actual_x + 5, actual_y + self.height // 2),
            (actual_x + 15, actual_y + self.height // 2 + 5)
        ]
        
        # Right arrow points (points right)
        right_arrow_points = [
            (actual_x + self.width - 15, actual_y + self.height // 2 - 5),
            (actual_x + self.width - 5, actual_y + self.height // 2),
            (actual_x + self.width - 15, actual_y + self.height // 2 + 5)
        ]
        
        if opengl:
            # For OpenGL, try polygon drawing first
            if hasattr(renderer, 'draw_polygon'):
                renderer.draw_polygon(left_arrow_points, arrow_color)
                renderer.draw_polygon(right_arrow_points, arrow_color)
            elif hasattr(renderer, 'draw_line'):
                # Draw as thick lines
                for points in [left_arrow_points, right_arrow_points]:
                    for i in range(len(points)):
                        start_point = points[i]
                        end_point = points[(i + 1) % len(points)]
                        renderer.draw_line(start_point[0], start_point[1], 
                                         end_point[0], end_point[1], arrow_color, 2)
        else:
            # For Pygame, draw directly on surface
            surface = renderer.get_surface()
            pygame.draw.polygon(surface, arrow_color, left_arrow_points)
            pygame.draw.polygon(surface, arrow_color, right_arrow_points)


class Switch(UIElement):
    def __init__(self, x: int, y: int, width: int = 60, height: int = 30,
                 checked: bool = False, root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.checked = checked
        self.animation_progress = 1.0 if checked else 0.0
        self.on_toggle = None
        self._was_pressed = False
        
        self.theme_type = theme or ThemeManager.get_current_theme()
    
    def toggle(self):
        """Toggle the switch state."""
        self.checked = not self.checked
        if self.on_toggle:
            self.on_toggle(self.checked)
    
    def set_checked(self, checked: bool):
        """
        Set the switch state.
        
        Args:
            checked (bool): New state.
        """
        self.checked = checked
    
    def set_on_toggle(self, callback: Callable[[bool], None]):
        """
        Set toggle callback.
        
        Args:
            callback (Callable): Function called when switch is toggled.
        """
        self.on_toggle = callback
    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update switch with mouse interaction."""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        mouse_over = (actual_x <= mouse_pos[0] <= actual_x + self.width and 
                     actual_y <= mouse_pos[1] <= actual_y + self.height)
        
        # Handle click with cooldown
        if mouse_pressed and mouse_over and not self._was_pressed:
            self.toggle()
            self._was_pressed = True
        elif not mouse_pressed:
            self._was_pressed = False
            
        if mouse_over:
            self.state = UIState.HOVERED
        else:
            self.state = UIState.NORMAL
            
        # Smooth animation
        target_progress = 1.0 if self.checked else 0.0
        if self.animation_progress != target_progress:
            self.animation_progress += (target_progress - self.animation_progress) * 0.2
            if abs(self.animation_progress - target_progress) < 0.01:
                self.animation_progress = target_progress
            
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def _get_colors(self):
        """Get colors from current theme for switch"""
        theme = ThemeManager.get_theme(self.theme_type)
        
        if self.checked:
            track_color = theme.switch_track_on
            thumb_color = theme.switch_thumb_on
        else:
            track_color = theme.switch_track_off
            thumb_color = theme.switch_thumb_off
        
        # Apply hover effect
        if self.state == UIState.HOVERED:
            if self.checked:
                track_color = tuple(min(255, c + 20) for c in track_color)
            else:
                track_color = tuple(min(255, c + 20) for c in track_color)
        
        return track_color, thumb_color
    
    def render_pygame(self, renderer):
        """Render using Pygame backend - CONSISTENT with OpenGL"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        track_color, thumb_color = self._get_colors()
        
        # Draw track with rounded corners effect
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, track_color)
        
        # Draw thumb with smooth animation
        thumb_size = max(10, int(self.height * 0.7))
        thumb_margin = max(2, (self.height - thumb_size) // 2)
        max_thumb_travel = max(10, self.width - thumb_size - (thumb_margin * 2))
        
        thumb_x = actual_x + thumb_margin + int(max_thumb_travel * self.animation_progress)
        thumb_y = actual_y + thumb_margin
        
        # Ensure thumb stays within bounds
        thumb_x = max(actual_x + thumb_margin, 
                     min(thumb_x, actual_x + self.width - thumb_size - thumb_margin))
        
        renderer.draw_rect(thumb_x, thumb_y, thumb_size, thumb_size, thumb_color)
        
        # Draw border
        border_color = (150, 150, 150)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color, fill=False)
        
        super().render_pygame(renderer)

    def render_opengl(self, renderer):
        """Render using OpenGL backend - CONSISTENT with Pygame"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        track_color, thumb_color = self._get_colors()
        
        # PRIMEIRO: desenhar a borda
        border_color = (150, 150, 150)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color, 
                        fill=False, border_width=1)
        
        # DEPOIS: desenhar o track
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, track_color)
        
        # FINALMENTE: desenhar o thumb
        thumb_size = max(10, int(self.height * 0.7))
        thumb_margin = max(2, (self.height - thumb_size) // 2)
        max_thumb_travel = max(10, self.width - thumb_size - (thumb_margin * 2))
        
        thumb_x = actual_x + thumb_margin + int(max_thumb_travel * self.animation_progress)
        thumb_y = actual_y + thumb_margin
        
        renderer.draw_rect(thumb_x, thumb_y, thumb_size, thumb_size, thumb_color)
        
        super().render_opengl(renderer)

class ScrollingFrame(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 content_width: int, content_height: int,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.content_width = content_width
        self.content_height = content_height
        self.scroll_x = 0
        self.scroll_y = 0
        self.scrollbar_size = 15
        self.dragging_vertical = False
        self.dragging_horizontal = False
        self.scroll_drag_start = (0, 0)
        
        self.theme_type = theme or ThemeManager.get_current_theme()

    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update scrolling frame with proper scroll handling"""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        # Calculate max scroll values
        max_scroll_x = max(0, self.content_width - self.width)
        max_scroll_y = max(0, self.content_height - self.height)
        
        # Handle scrollbar dragging
        if mouse_pressed:
            if not (self.dragging_vertical or self.dragging_horizontal):
                # Check vertical scrollbar
                if max_scroll_y > 0:
                    scrollbar_rect = self._get_vertical_scrollbar_rect(actual_x, actual_y)
                    if (scrollbar_rect[0] <= mouse_pos[0] <= scrollbar_rect[0] + scrollbar_rect[2] and 
                        scrollbar_rect[1] <= mouse_pos[1] <= scrollbar_rect[1] + scrollbar_rect[3]):
                        self.dragging_vertical = True
                        self.scroll_drag_start = (mouse_pos[0], mouse_pos[1])
                        self.scroll_start_y = self.scroll_y
                
                # Check horizontal scrollbar  
                if max_scroll_x > 0:
                    scrollbar_rect = self._get_horizontal_scrollbar_rect(actual_x, actual_y)
                    if (scrollbar_rect[0] <= mouse_pos[0] <= scrollbar_rect[0] + scrollbar_rect[2] and 
                        scrollbar_rect[1] <= mouse_pos[1] <= scrollbar_rect[1] + scrollbar_rect[3]):
                        self.dragging_horizontal = True
                        self.scroll_drag_start = (mouse_pos[0], mouse_pos[1])
                        self.scroll_start_x = self.scroll_x
        else:
            self.dragging_vertical = False
            self.dragging_horizontal = False
            
        # Update scroll position if dragging
        if self.dragging_vertical and max_scroll_y > 0:
            drag_delta_y = mouse_pos[1] - self.scroll_drag_start[1]
            scroll_area_height = self.height - self.scrollbar_size
            scroll_ratio = drag_delta_y / scroll_area_height
            self.scroll_y = max(0, min(max_scroll_y, self.scroll_start_y + int(scroll_ratio * max_scroll_y)))
            
        if self.dragging_horizontal and max_scroll_x > 0:
            drag_delta_x = mouse_pos[0] - self.scroll_drag_start[0]
            scroll_area_width = self.width - self.scrollbar_size
            scroll_ratio = drag_delta_x / scroll_area_width
            self.scroll_x = max(0, min(max_scroll_x, self.scroll_start_x + int(scroll_ratio * max_scroll_x)))
        
        # Update children with scrolled mouse position for interaction
        scrolled_mouse_pos = (mouse_pos[0] + self.scroll_x, mouse_pos[1] + self.scroll_y)
        for child in self.children:
            child._update_with_mouse(scrolled_mouse_pos, mouse_pressed, dt)
            
        self.state = UIState.NORMAL
    
    def handle_scroll(self, scroll_y: int):
        """Handle mouse wheel scrolling"""
        max_scroll_y = max(0, self.content_height - self.height)
        self.scroll_y = max(0, min(max_scroll_y, self.scroll_y - scroll_y * 30))
        max_scroll_x = max(0, self.content_width - self.width)
        self.scroll_x = max(0, min(max_scroll_x, self.scroll_x - scroll_y * 30))
    
    def render_pygame(self, renderer):
        """Render using Pygame backend - FIXED scroll application"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.background)
        
        # Setup clipping for content
        original_clip = renderer.get_surface().get_clip()
        renderer.get_surface().set_clip(pygame.Rect(actual_x, actual_y, self.width, self.height))
        
        # Apply scroll transform by adjusting rendering position
        for child in self.children:
            # Save original position
            original_x, original_y = child.x, child.y
            
            # Apply scroll offset to child position for rendering only
            child.x = original_x - self.scroll_x
            child.y = original_y - self.scroll_y
            
            # Render child with scrolled position
            child.render_pygame(renderer)
            
            # Restore original position immediately
            child.x, child.y = original_x, original_y
        
        # Restore clipping
        renderer.get_surface().set_clip(original_clip)
        
        # Draw scrollbars if needed
        if self.content_width > self.width:
            self._draw_horizontal_scrollbar(renderer, actual_x, actual_y, theme)
        
        if self.content_height > self.height:
            self._draw_vertical_scrollbar(renderer, actual_x, actual_y, theme)
        
        # Draw border
        if theme.border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.border, fill=False)
        
        # super().render_pygame(renderer) - Will render duplicated children

    def render_opengl(self, renderer):
        """Render using OpenGL backend - FIXED clipping"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # FIRST: Draw border
        if theme.border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.border, fill=False)
        
        # THEN: Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.background)
        
        # Clips content
        if hasattr(renderer, 'enable_scissor'):
            # OpenGL scissor uses bottom-left origin, no Y flipping needed
            renderer.enable_scissor(actual_x, actual_y, self.width, self.height)
        
        # Apply scroll transform to children rendering
        for child in self.children:
            # Save original position
            original_x, original_y = child.x, child.y
            
            # Apply scroll offset to child position for rendering only
            child.x = original_x - self.scroll_x
            child.y = original_y - self.scroll_y
            
            # Render child with scrolled position
            child.render_opengl(renderer)
            
            # Restore original position immediately
            child.x, child.y = original_x, original_y
        
        # Disable scissor test
        if hasattr(renderer, 'disable_scissor'):
            renderer.disable_scissor()
        
        # Draw scrollbars on top
        if self.content_width > self.width:
            self._draw_horizontal_scrollbar(renderer, actual_x, actual_y, theme)
        
        if self.content_height > self.height:
            self._draw_vertical_scrollbar(renderer, actual_x, actual_y, theme)
    
    def _get_vertical_scrollbar_rect(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """Get the vertical scrollbar rectangle - FIXED limits"""
        if self.content_height <= self.height:
            return (0, 0, 0, 0)
        
        scrollbar_width = self.scrollbar_size
        scrollbar_height = self.height - (self.scrollbar_size if self.content_width > self.width else 0)
        
        scrollbar_x = x + self.width - scrollbar_width
        scrollbar_y = y
        
        # Calculate thumb height and position - FIXED: Same logic as drawing
        max_scroll_y = max(1, self.content_height - self.height)
        thumb_height = max(20, int((self.height / self.content_height) * scrollbar_height))
        
        available_height = scrollbar_height - thumb_height
        scroll_ratio = self.scroll_y / max_scroll_y
        thumb_y = scrollbar_y + int(scroll_ratio * available_height)
        
        return (scrollbar_x, thumb_y, scrollbar_width, thumb_height)

    def _get_horizontal_scrollbar_rect(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """Get the horizontal scrollbar rectangle - FIXED limits"""
        if self.content_width <= self.width:
            return (0, 0, 0, 0)
        
        scrollbar_width = self.width - (self.scrollbar_size if self.content_height > self.height else 0)
        scrollbar_height = self.scrollbar_size
        
        scrollbar_x = x
        scrollbar_y = y + self.height - scrollbar_height
        
        # Calculate thumb width and position - FIXED: Same logic as drawing
        max_scroll_x = max(1, self.content_width - self.width)
        thumb_width = max(20, int((self.width / self.content_width) * scrollbar_width))
        
        available_width = scrollbar_width - thumb_width
        scroll_ratio = self.scroll_x / max_scroll_x
        thumb_x = scrollbar_x + int(scroll_ratio * available_width)
        
        return (thumb_x, scrollbar_y, thumb_width, scrollbar_height)
    
    def _draw_horizontal_scrollbar(self, renderer, x: int, y: int, theme):
        """Draw horizontal scrollbar - FIXED limits"""
        scrollbar_width = self.width - (self.scrollbar_size if self.content_height > self.height else 0)
        scrollbar_height = self.scrollbar_size
        
        scrollbar_x = x
        scrollbar_y = y + self.height - scrollbar_height
        
        # Track
        renderer.draw_rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, theme.slider_track)
        
        # Thumb - FIXED: Calculate thumb position correctly
        max_scroll_x = max(1, self.content_width - self.width)  # Avoid division by zero
        thumb_width = max(20, int((self.width / self.content_width) * scrollbar_width))
        
        # Ensure thumb doesn't exceed scrollbar bounds
        available_width = scrollbar_width - thumb_width
        scroll_ratio = self.scroll_x / max_scroll_x
        thumb_x = scrollbar_x + int(scroll_ratio * available_width)
        
        renderer.draw_rect(thumb_x, scrollbar_y, thumb_width, scrollbar_height, theme.slider_thumb_normal)

    def _draw_vertical_scrollbar(self, renderer, x: int, y: int, theme):
        """Draw vertical scrollbar - FIXED limits"""
        scrollbar_width = self.scrollbar_size
        scrollbar_height = self.height - (self.scrollbar_size if self.content_width > self.width else 0)
        
        scrollbar_x = x + self.width - scrollbar_width
        scrollbar_y = y
        
        # Track
        renderer.draw_rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, theme.slider_track)
        
        # Thumb - FIXED: Calculate thumb position correctly
        max_scroll_y = max(1, self.content_height - self.height)  # Avoid division by zero
        thumb_height = max(20, int((self.height / self.content_height) * scrollbar_height))
        
        # Ensure thumb doesn't exceed scrollbar bounds
        available_height = scrollbar_height - thumb_height
        scroll_ratio = self.scroll_y / max_scroll_y
        thumb_y = scrollbar_y + int(scroll_ratio * available_height)
        
        renderer.draw_rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height, theme.slider_thumb_normal)

class Slider(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, 
                 min_val: float = 0, max_val: float = 100, value: float = 50,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.dragging = False
        self.on_value_changed = None
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
    def set_theme(self, theme_type: ThemeType):
        """Set slider theme"""
        self.theme_type = theme_type
    
    def _get_colors(self):
        """Get colors from current theme"""
        return ThemeManager.get_theme(self.theme_type)
    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update slider with mouse interaction"""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
            
        thumb_x = actual_x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        thumb_rect = (thumb_x - 5, actual_y, 10, self.height)
        
        mouse_over_thumb = (thumb_rect[0] <= mouse_pos[0] <= thumb_rect[0] + thumb_rect[2] and 
                           thumb_rect[1] <= mouse_pos[1] <= thumb_rect[1] + thumb_rect[3])
        
        if mouse_pressed and (mouse_over_thumb or self.dragging):
            self.dragging = True
            self.state = UIState.PRESSED
            # Update value based on mouse position
            relative_x = max(0, min(self.width, mouse_pos[0] - actual_x))
            new_value = self.min_val + (relative_x / self.width) * (self.max_val - self.min_val)
            
            if new_value != self.value:
                self.value = new_value
                if self.on_value_changed:
                    self.on_value_changed(self.value)
        else:
            self.dragging = False
            if (thumb_rect[0] <= mouse_pos[0] <= thumb_rect[0] + thumb_rect[2] and 
                thumb_rect[1] <= mouse_pos[1] <= thumb_rect[1] + thumb_rect[3]):
                self.state = UIState.HOVERED
            else:
                self.state = UIState.NORMAL
                
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
            
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        theme = self._get_colors()
        actual_x, actual_y = self.get_actual_position()
        
        # Draw track
        renderer.draw_rect(actual_x, actual_y + self.height//2 - 2, 
                         self.width, 4, theme.slider_track)
        
        # Draw thumb
        thumb_x = actual_x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        
        if self.state == UIState.PRESSED:
            thumb_color = theme.slider_thumb_pressed
        elif self.state == UIState.HOVERED:
            thumb_color = theme.slider_thumb_hover
        else:
            thumb_color = theme.slider_thumb_normal
            
        renderer.draw_rect(thumb_x - 5, actual_y, 10, self.height, thumb_color)
        
        # Draw value text
        font = pygame.font.Font(None, 12)
        value_text = f"{self.value:.1f}"
        text_surface = font.render(value_text, True, theme.slider_text)
        renderer.draw_surface(text_surface, thumb_x - text_surface.get_width()//2, 
                            actual_y + self.height + 5)
        
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        theme = self._get_colors()
        actual_x, actual_y = self.get_actual_position()
        
        # Draw track
        renderer.draw_rect(actual_x, actual_y + self.height//2 - 2, 
                         self.width, 4, theme.slider_track)
        
        # Draw thumb
        thumb_x = actual_x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        
        if self.state == UIState.PRESSED:
            thumb_color = theme.slider_thumb_pressed
        elif self.state == UIState.HOVERED:
            thumb_color = theme.slider_thumb_hover
        else:
            thumb_color = theme.slider_thumb_normal
            
        renderer.draw_rect(thumb_x - 5, actual_y, 10, self.height, thumb_color)
        
        # Draw value text
        font = pygame.font.Font(None, 12)
        value_text = f"{self.value:.1f}"
        text_surface = font.render(value_text, True, theme.slider_text)
        
        if hasattr(renderer, 'render_surface'):
            renderer.render_surface(text_surface, thumb_x - text_surface.get_width()//2, 
                                actual_y + self.height + 5)
        else:
            renderer.draw_surface(text_surface, thumb_x - text_surface.get_width()//2, 
                                actual_y + self.height + 5)
                
        super().render_opengl(renderer)


class Dropdown(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, 
                 options: List[str] = None, font_size: int = 20, 
                 font_name: Optional[str] = None, 
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 max_visible_options: int = 10,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.options = options or []
        self.selected_index = 0
        self.expanded = False
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self._option_height = 25
        self.on_selection_changed = None
        self._just_opened = False
        
        # Scroll functionality
        self.max_visible_options = max_visible_options
        self.scroll_offset = 0
        self.scrollbar_width = 10
        self.is_scrolling = False
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
    @property
    def font(self):
        """Lazy font loading"""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
        
    def set_theme(self, theme_type: ThemeType):
        """Set dropdown theme"""
        self.theme_type = theme_type
    
    def _get_colors(self):
        """Get colors from current theme"""
        return ThemeManager.get_theme(self.theme_type)
    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update dropdown with mouse interaction and scroll support"""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
            
        # Check if mouse is over main dropdown
        main_rect = (actual_x, actual_y, self.width, self.height)
        mouse_over_main = (main_rect[0] <= mouse_pos[0] <= main_rect[0] + main_rect[2] and 
                          main_rect[1] <= mouse_pos[1] <= main_rect[1] + main_rect[3])
        
        # Handle scrollbar interaction
        if self.expanded and len(self.options) > self.max_visible_options:
            scrollbar_rect = self._get_scrollbar_rect(actual_x, actual_y)
            if mouse_pressed and scrollbar_rect[0] <= mouse_pos[0] <= scrollbar_rect[0] + scrollbar_rect[2] and \
               scrollbar_rect[1] <= mouse_pos[1] <= scrollbar_rect[1] + scrollbar_rect[3]:
                self.is_scrolling = True
            elif not mouse_pressed:
                self.is_scrolling = False
            
            if self.is_scrolling and mouse_pressed:
                # Calculate scroll position based on mouse Y
                options_height = len(self.options) * self._option_height
                visible_height = self.max_visible_options * self._option_height
                scroll_area_height = visible_height - (self.scrollbar_width * 2)
                
                relative_y = mouse_pos[1] - (actual_y + self.height + self.scrollbar_width)
                scroll_ratio = max(0, min(1, relative_y / scroll_area_height))
                max_scroll = max(0, len(self.options) - self.max_visible_options)
                self.scroll_offset = int(scroll_ratio * max_scroll)
        
        # Handle mouse press
        if mouse_pressed and not self._just_opened and not self.is_scrolling:
            if mouse_over_main:
                # Toggle expansion
                self.expanded = not self.expanded
                self._just_opened = self.expanded
                self.scroll_offset = 0  # Reset scroll when opening
            elif self.expanded:
                # Check if clicking on an option
                option_clicked = False
                visible_options = self._get_visible_options()
                
                for i, option_index in enumerate(visible_options):
                    option_rect = (actual_x, actual_y + self.height + i * self._option_height, 
                                 self.width - (self.scrollbar_width if len(self.options) > self.max_visible_options else 0), 
                                 self._option_height)
                    if (option_rect[0] <= mouse_pos[0] <= option_rect[0] + option_rect[2] and 
                        option_rect[1] <= mouse_pos[1] <= option_rect[1] + option_rect[3]):
                        old_index = self.selected_index
                        self.selected_index = option_index
                        self.expanded = False
                        self._just_opened = False
                        self.scroll_offset = 0  # Reset scroll when selecting
                        if old_index != option_index and self.on_selection_changed:
                            self.on_selection_changed(option_index, self.options[option_index])
                        option_clicked = True
                        break
                
                # Clicked outside dropdown, close it
                if not option_clicked:
                    self.expanded = False
                    self._just_opened = False
        else:
            # Reset the just_opened flag when mouse is released
            if not mouse_pressed:
                self._just_opened = False
                self.is_scrolling = False
            
            if mouse_over_main or self.expanded:
                self.state = UIState.HOVERED
            else:
                self.state = UIState.NORMAL
                
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def handle_scroll(self, scroll_y: int):
        """Handle mouse wheel scrolling"""
        if self.expanded and len(self.options) > self.max_visible_options:
            self.scroll_offset = max(0, min(
                len(self.options) - self.max_visible_options,
                self.scroll_offset - scroll_y  # Invert for natural scrolling
            ))
    
    def _get_visible_options(self):
        """Get the list of option indices that are currently visible"""
        if len(self.options) <= self.max_visible_options:
            return list(range(len(self.options)))
        
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.max_visible_options, len(self.options))
        return list(range(start_idx, end_idx))
    
    def _get_scrollbar_rect(self, actual_x: int, actual_y: int) -> Tuple[int, int, int, int]:
        """Get the scrollbar rectangle"""
        total_height = self.max_visible_options * self._option_height
        visible_ratio = self.max_visible_options / len(self.options)
        scrollbar_height = max(20, int(total_height * visible_ratio))
        
        max_scroll = max(0, len(self.options) - self.max_visible_options)
        scroll_ratio = self.scroll_offset / max_scroll if max_scroll > 0 else 0
        
        scrollbar_y = actual_y + self.height + int((total_height - scrollbar_height) * scroll_ratio)
        scrollbar_x = actual_x + self.width - self.scrollbar_width
        
        return (scrollbar_x, scrollbar_y, self.scrollbar_width, scrollbar_height)
            
    def render_pygame(self, renderer):
        """Render using Pygame backend"""
        if not self.visible:
            return
            
        theme = self._get_colors()
        actual_x, actual_y = self.get_actual_position()
        
        # Draw main box
        if self.state == UIState.NORMAL:
            main_color = theme.dropdown_normal
        else:
            main_color = theme.dropdown_hover
            
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, main_color)
        
        # Draw border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             theme.dropdown_border, fill=False)
        
        # Draw selected text
        if self.options:
            text = self.options[self.selected_index]
            # Truncate text if too long
            if len(text) > 15:
                text = text[:15] + "..."
            text_surface = self.font.render(text, True, theme.dropdown_text)
            renderer.draw_surface(text_surface, actual_x + 5, 
                                actual_y + (self.height - text_surface.get_height()) // 2)
        
        # Draw dropdown arrow
        arrow_color = theme.dropdown_text
        arrow_points = [
            (actual_x + self.width - 15, actual_y + self.height//2 - 3),
            (actual_x + self.width - 5, actual_y + self.height//2 - 3),
            (actual_x + self.width - 10, actual_y + self.height//2 + 3)
        ]
        
        # Pygame-specific arrow drawing
        if hasattr(renderer, 'get_surface'):
            surface = renderer.get_surface()
            pygame.draw.polygon(surface, arrow_color, arrow_points)
        else:
            # Fallback for renderers without get_surface
            self._draw_arrow_polygon(renderer, arrow_points, arrow_color)
        
        # Draw expanded options with scroll
        if self.expanded:
            self._render_expanded_options(renderer, actual_x, actual_y, theme)
        
        super().render_pygame(renderer)
    
    
    def render_opengl(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        theme = self._get_colors()
        actual_x, actual_y = self.get_actual_position()
        
        # First: draw border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                            theme.dropdown_border, fill=False, border_width=1)
        
        # Then: draw main box
        if self.state == UIState.NORMAL:
            main_color = theme.dropdown_normal
        else:
            main_color = theme.dropdown_hover
            
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, main_color)
        
        # Draw selected text
        if self.options:
            text = self.options[self.selected_index]
            # Truncate text if too long
            if len(text) > 15:
                text = text[:15] + "..."
            text_surface = self.font.render(text, True, theme.dropdown_text)
            
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(text_surface, actual_x + 5, 
                                    actual_y + (self.height - text_surface.get_height()) // 2)
            else:
                renderer.draw_surface(text_surface, actual_x + 5, 
                                    actual_y + (self.height - text_surface.get_height()) // 2)
        
        # Draw dropdown arrow - OpenGL compatible
        arrow_color = theme.dropdown_text
        arrow_points = [
            (actual_x + self.width - 15, actual_y + self.height//2 - 3),
            (actual_x + self.width - 5, actual_y + self.height//2 - 3),
            (actual_x + self.width - 10, actual_y + self.height//2 + 3)
        ]
        
        # Use polygon drawing method compatible with OpenGL
        self._draw_arrow_polygon(renderer, arrow_points, arrow_color)
        
        # Draw expanded options with scroll
        if self.expanded:
            self._render_expanded_options(renderer, actual_x, actual_y, theme, opengl=True)
        
        super().render_opengl(renderer)
    
    def _draw_arrow_polygon(self, renderer, points, color):
        """
        Draw arrow polygon in a way compatible with both Pygame and OpenGL.
        
        Args:
            renderer: The renderer object
            points: List of (x, y) points for the polygon
            color: RGB color tuple
        """
        # For OpenGL renderers, we need to draw the polygon differently
        # This is a simplified approach - you might need to adjust based on your OpenGL renderer
        
        # Method 1: Try using renderer's polygon drawing if available
        if hasattr(renderer, 'draw_polygon'):
            renderer.draw_polygon(points, color)
        # Method 2: Draw as individual triangles/lines
        elif hasattr(renderer, 'draw_line'):
            # Draw the arrow as connected lines
            for i in range(len(points)):
                start_point = points[i]
                end_point = points[(i + 1) % len(points)]
                renderer.draw_line(start_point[0], start_point[1], 
                                 end_point[0], end_point[1], color, 2)
        # Method 3: Fallback - create a small surface with the arrow
        else:
            try:
                # Create a small surface for the arrow
                arrow_surface = pygame.Surface((20, 10), pygame.SRCALPHA)
                pygame.draw.polygon(arrow_surface, color, [
                    (5, 0), (15, 0), (10, 5)
                ])
                
                # Calculate position for the arrow surface
                arrow_x = points[0][0] - 10  # Center the arrow
                arrow_y = points[0][1] - 2   # Adjust vertical position
                
                if hasattr(renderer, 'render_surface'):
                    renderer.render_surface(arrow_surface, arrow_x, arrow_y)
                else:
                    renderer.draw_surface(arrow_surface, arrow_x, arrow_y)
            except:
                # Final fallback - just draw a simple rectangle as arrow indicator
                arrow_rect = (points[0][0] - 5, points[0][1] - 2, 10, 5)
                renderer.draw_rect(arrow_rect[0], arrow_rect[1], 
                                 arrow_rect[2], arrow_rect[3], color)
    
    def _render_expanded_options(self, renderer, actual_x: int, actual_y: int, theme, opengl=False):
        """Helper method to render expanded options - WITH OPTION SEPARATORS"""
        visible_options = self._get_visible_options()
        total_options_height = self.max_visible_options * self._option_height
        
        # Calculate width for options area
        options_bg_width = self.width - (self.scrollbar_width if len(self.options) > self.max_visible_options else 0)
        
        # FIRST: Draw the main expanded options container border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y + self.height, options_bg_width, total_options_height, 
                            theme.dropdown_border, fill=False, border_width=1)
        
        # SECOND: Draw the main expanded options background (inset by border)
        renderer.draw_rect(actual_x, actual_y + self.height, options_bg_width, total_options_height, 
                        theme.dropdown_expanded, fill=True, border_width=1)
        
        # THIRD: Draw individual options with subtle separators
        for i, option_index in enumerate(visible_options):
            option_y = actual_y + self.height + i * self._option_height
            is_selected = option_index == self.selected_index
            
            # Determine option background color
            if is_selected:
                option_color = theme.dropdown_option_selected
            else:
                option_color = theme.dropdown_option_normal
            
            # Check hover state
            mouse_pos = pygame.mouse.get_pos()
            option_rect = (actual_x, option_y, options_bg_width, self._option_height)
            mouse_over_option = (option_rect[0] <= mouse_pos[0] <= option_rect[0] + option_rect[2] and 
                            option_rect[1] <= mouse_pos[1] <= option_rect[1] + option_rect[3])
            
            if mouse_over_option:
                option_color = theme.dropdown_option_hover
            
            # Draw option background (full height, no individual borders)
            renderer.draw_rect(actual_x, option_y, options_bg_width, self._option_height, option_color, fill=True, border_width=0)
            
            # Draw subtle separator line between options (except for the last one)
            if i < len(visible_options) - 1 and theme.dropdown_border:
                separator_y = option_y + self._option_height - 1
                separator_color = (theme.dropdown_border[0]//2, theme.dropdown_border[1]//2, theme.dropdown_border[2]//2)
                renderer.draw_rect(actual_x + 1, separator_y, options_bg_width - 2, 1, separator_color)
            
            # Draw option text
            option_text = self.options[option_index]
            if len(option_text) > 20:
                option_text = option_text[:20] + "..."
            text_surface = self.font.render(option_text, True, theme.dropdown_text)
            
            text_x = actual_x + 5 + 1  # Adjust for main container border
            text_y = option_y + (self._option_height - text_surface.get_height()) // 2
            
            if opengl and hasattr(renderer, 'render_surface'):
                renderer.render_surface(text_surface, text_x, text_y)
            else:
                renderer.draw_surface(text_surface, text_x, text_y)
        
        # FOURTH: Draw scrollbar if needed
        if len(self.options) > self.max_visible_options:
            scrollbar_rect = self._get_scrollbar_rect(actual_x, actual_y)
            scrollbar_color = (150, 150, 150) if self.is_scrolling else (100, 100, 100)
            renderer.draw_rect(scrollbar_rect[0], scrollbar_rect[1], 
                            scrollbar_rect[2], scrollbar_rect[3], scrollbar_color)
    
    def add_option(self, option: str):
        """Add an option to the dropdown"""
        self.options.append(option)
    
    def remove_option(self, option: str):
        """Remove an option from the dropdown"""
        if option in self.options:
            self.options.remove(option)
            # Adjust selected index if needed
            if self.selected_index >= len(self.options):
                self.selected_index = max(0, len(self.options) - 1)
    
    def set_selected_index(self, index: int):
        """Set the selected option by index"""
        if 0 <= index < len(self.options):
            old_index = self.selected_index
            self.selected_index = index
            if old_index != index and self.on_selection_changed:
                self.on_selection_changed(index, self.options[index])
    
    def set_on_selection_changed(self, callback: Callable[[int, str], None]):
        """Set callback for when selection changes"""
        self.on_selection_changed = callback
        
class UiFrame(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, 
                 root_point: Tuple[float, float] = (0, 0), 
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        """
        Initialize a UI Frame container element.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            width (int): Width of the frame in pixels.
            height (int): Height of the frame in pixels.
            root_point (Tuple[float, float]): Anchor point for positioning.
            theme (ThemeType): Theme to use for frame styling.
            element_id (Optional[str]): Custom element ID. If None, generates automatic ID.
        """
        super().__init__(x, y, width, height, root_point, element_id)
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.background_color = None  # None means transparent background
        self.border_color = None      # None means no border
        self.border_width = 1
        self.padding = 5  # Padding inside the frame
        
    def set_background_color(self, color: Optional[Tuple[int, int, int]]):
        """
        Set the background color of the frame.
        
        Args:
            color (Optional[Tuple[int, int, int]]): RGB color tuple or None for transparent.
        """
        self.background_color = color
        
    def set_border(self, color: Optional[Tuple[int, int, int]], width: int = 1):
        """
        Set the border properties of the frame.
        
        Args:
            color (Optional[Tuple[int, int, int]]): Border color or None for no border.
            width (int): Border width in pixels.
        """
        self.border_color = color
        self.border_width = width
        
    def set_padding(self, padding: int):
        """
        Set the padding inside the frame.
        
        Args:
            padding (int): Padding in pixels.
        """
        self.padding = padding
        
    def add_child(self, child: UIElement):
        """
        Add a child element to this frame with automatic positioning.
        
        Args:
            child (UIElement): The child UI element to add.
        """
        super().add_child(child)
        
    def get_content_rect(self) -> Tuple[int, int, int, int]:
        """
        Get the rectangle area available for child elements (inside padding).
        
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height) of content area.
        """
        actual_x, actual_y = self.get_actual_position()
        content_x = actual_x + self.padding
        content_y = actual_y + self.padding
        content_width = self.width - (self.padding * 2)
        content_height = self.height - (self.padding * 2)
        
        return (content_x, content_y, content_width, content_height)
        
    def update_theme(self, theme_type: ThemeType):
        """
        Update the theme for this frame and all its children.
        
        Args:
            theme_type (ThemeType): The new theme to apply.
        """
        self.theme_type = theme_type
        super().update_theme(theme_type)
    
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """
        Update frame and children with mouse interaction.
        
        Args:
            mouse_pos (Tuple[int, int]): Current mouse position.
            mouse_pressed (bool): Whether mouse button is pressed.
            dt (float): Delta time in seconds.
        """
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            # Still update children but with disabled state
            for child in self.children:
                child._update_with_mouse(mouse_pos, mouse_pressed, dt)
            return
            
        # Frame itself doesn't have interactive states beyond enabled/disabled
        self.state = UIState.NORMAL
        
        # Update all children with the same mouse state
        for child in self.children:
            child._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def render_pygame(self, renderer):
        """Render frame using Pygame backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw background
        if self.background_color is not None:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, self.background_color)
        else:
            # Use theme background if no custom color
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.background)
        
        # Draw border
        if self.border_color is not None:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             self.border_color, fill=False, border_width=self.border_width)
        elif theme.border:
            # Use theme border if no custom border
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             theme.border, fill=False, border_width=self.border_width)
        
        # Render children
        super().render_pygame(renderer)
    
    def render_opengl(self, renderer):
        """Render frame using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw border first (if any)
        border_color = self.border_color or (theme.border if theme.border else None)
        if border_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             border_color, fill=False, border_width=self.border_width)
        
        # Draw background
        bg_color = self.background_color or theme.background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color)
        
        # Render children
        super().render_opengl(renderer)
    
    def arrange_children_vertically(self, spacing: int = 5, align: str = "left"):
        """
        Arrange child elements vertically within the frame.
        
        Args:
            spacing (int): Space between children in pixels.
            align (str): Alignment ("left", "center", "right").
        """
        content_x, content_y, content_width, content_height = self.get_content_rect()
        current_y = content_y
        
        for child in self.children:
            # Set X position based on alignment
            if align == "center":
                child.x = content_x + (content_width - child.width) // 2
            elif align == "right":
                child.x = content_x + content_width - child.width
            else:  # left
                child.x = content_x
                
            # Set Y position
            child.y = current_y
            child.root_point = (0, 0)  # Reset to top-left anchor for vertical arrangement
            
            # Update current Y position
            current_y += child.height + spacing
    
    def arrange_children_horizontally(self, spacing: int = 5, align: str = "top"):
        """
        Arrange child elements horizontally within the frame.
        
        Args:
            spacing (int): Space between children in pixels.
            align (str): Alignment ("top", "center", "bottom").
        """
        content_x, content_y, content_width, content_height = self.get_content_rect()
        current_x = content_x
        
        for child in self.children:
            # Set Y position based on alignment
            if align == "center":
                child.y = content_y + (content_height - child.height) // 2
            elif align == "bottom":
                child.y = content_y + content_height - child.height
            else:  # top
                child.y = content_y
                
            # Set X position
            child.x = current_x
            child.root_point = (0, 0)  # Reset to top-left anchor for horizontal arrangement
            
            # Update current X position
            current_x += child.width + spacing
    
    def clear_children(self):
        """Remove all child elements from this frame."""
        for child in self.children:
            child.parent = None
        self.children.clear()