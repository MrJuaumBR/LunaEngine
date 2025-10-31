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

This module forms the core of LunaEngine's UI system, providing a flexible and
themeable foundation for building complex user interfaces in Pygame applications.
"""

import pygame
import numpy as np
from typing import Optional, Callable, List, Tuple, Any
from enum import Enum
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

class UIElement:
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
    
    def render(self, renderer):
        """
        Render the element to the screen.
        
        Args:
            renderer: The renderer object used for drawing.
        """
        if not self.visible:
            return
            
        for child in self.children:
            child.render(renderer)
    
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
        
    def render(self, renderer):
        """Render the text label."""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        text_color = self._get_text_color()
        
        text_surface = self.font.render(self.text, True, text_color)
        renderer.draw_surface(text_surface, actual_x, actual_y)
        
        super().render(renderer)

class ImageLabel(UIElement):
    def __init__(self, x: int, y: int, image_path: str, 
                 width: Optional[int] = None, height: Optional[int] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
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
        
    def render(self, renderer):
        """Render the image label."""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if self._image.get_width() != self.width or self._image.get_height() != self.height:
            scaled_image = pygame.transform.scale(self._image, (self.width, self.height))
            renderer.draw_surface(scaled_image, actual_x, actual_y)
        else:
            renderer.draw_surface(self._image, actual_x, actual_y)
            
        super().render(renderer)

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
            
    def render(self, renderer):
        """Render the button."""
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
            
        super().render(renderer)

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
            
    def render(self, renderer):
        """Render the image button."""
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
            
        super().render(renderer)

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
        """Calculate cursor position - OPTIMIZED"""
        if not self.text or self.cursor_pos == 0:
            return actual_x + 5, actual_y + 5
        
        # Only measure text up to cursor position for efficiency
        text_before_cursor = self.text[:self.cursor_pos]
        text_width = self.font.size(text_before_cursor)[0]
        return actual_x + 5 + text_width, actual_y + 5
    
    def render(self, renderer):
        """Render the text box - FIXED"""
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
        
        # Draw text using cached surface
        if self._text_surface is not None:
            text_y = actual_y + (self.height - self._text_rect.height) // 2
            # Clip text if too long
            if self._text_rect.width > self.width - 10:
                # Create a subsurface for the visible portion
                clip_width = self.width - 10
                # Calculate scroll offset based on cursor position
                if self.focused and self.text:
                    cursor_x = self.font.size(self.text[:self.cursor_pos])[0]
                    if cursor_x > clip_width:
                        scroll_offset = cursor_x - clip_width + 10
                        source_rect = pygame.Rect(scroll_offset, 0, clip_width, self._text_rect.height)
                        clipped_surface = self._text_surface.subsurface(source_rect)
                        renderer.draw_surface(clipped_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
                else:
                    # Just show the beginning of the text
                    source_rect = pygame.Rect(0, 0, clip_width, self._text_rect.height)
                    clipped_surface = self._text_surface.subsurface(source_rect)
                    renderer.draw_surface(clipped_surface, actual_x + 5, text_y)
            else:
                renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
        
        # Draw cursor
        if self.focused and self.cursor_visible:
            cursor_x, cursor_y = self._get_cursor_position(actual_x, actual_y)
            cursor_height = self.height - 10
            renderer.draw_rect(cursor_x, cursor_y, 2, cursor_height, theme.dropdown_text)
        
        # Reset the flag após o redesenho
        self._needs_redraw = False
        super().render(renderer)

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
    
    def render(self, renderer):
        """Render the progress bar."""
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
        
        super().render(renderer)

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
    
    def render(self, renderer):
        """Render the draggable element."""
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
        
        super().render(renderer)

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
    
    def render(self, renderer):
        """Render the gradient element."""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        renderer.draw_surface(self._gradient_surface, actual_x, actual_y)
        
        super().render(renderer)

class Select(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 options: List[str], font_size: int = 20, font_name: Optional[str] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
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
    
    # FIX: Add the missing method
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
    
    def render(self, renderer):
        """Render the select element."""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.dropdown_normal)
        
        # Draw border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.dropdown_border, fill=False)
        
        # Draw arrows
        arrow_color = theme.dropdown_text
        
        # Left arrow
        left_arrow_points = [
            (actual_x + self.arrow_width - 5, actual_y + self.height // 2 - 5),
            (actual_x + 5, actual_y + self.height // 2),
            (actual_x + self.arrow_width - 5, actual_y + self.height // 2 + 5)
        ]
        
        # Right arrow
        right_arrow_points = [
            (actual_x + self.width - self.arrow_width + 5, actual_y + self.height // 2 - 5),
            (actual_x + self.width - 5, actual_y + self.height // 2),
            (actual_x + self.width - self.arrow_width + 5, actual_y + self.height // 2 + 5)
        ]
        
        surface = renderer.get_surface()
        pygame.draw.polygon(surface, arrow_color, left_arrow_points)
        pygame.draw.polygon(surface, arrow_color, right_arrow_points)
        
        # Draw selected text
        if self.options:
            text = self.options[self.selected_index]
            if len(text) > 15:
                text = text[:15] + "..."
            text_surface = self.font.render(text, True, theme.dropdown_text)
            text_x = actual_x + (self.width - text_surface.get_width()) // 2
            text_y = actual_y + (self.height - text_surface.get_height()) // 2
            renderer.draw_surface(text_surface, text_x, text_y)
        
        super().render(renderer)


class Switch(UIElement):
    def __init__(self, x: int, y: int, width: int = 60, height: int = 30,
                 checked: bool = False, root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.checked = checked
        self.animation_progress = 1.0 if checked else 0.0
        self.on_toggle = None
        
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
        
        if mouse_pressed and mouse_over and not self._was_pressed:
            self.toggle()
            self._was_pressed = True
        elif not mouse_pressed:
            self._was_pressed = False
            
        if mouse_over:
            self.state = UIState.HOVERED
        else:
            self.state = UIState.NORMAL
            
        # Animate
        target_progress = 1.0 if self.checked else 0.0
        if self.animation_progress != target_progress:
            self.animation_progress += (target_progress - self.animation_progress) * 0.2
            if abs(self.animation_progress - target_progress) < 0.01:
                self.animation_progress = target_progress
            
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def render(self, renderer):
        """Render the switch."""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw track
        track_color = theme.button_normal if self.checked else theme.slider_track
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, track_color)
        
        # Draw thumb
        thumb_size = int(self.height * 0.8)
        thumb_margin = (self.height - thumb_size) // 2
        thumb_x = actual_x + thumb_margin + int((self.width - thumb_size - thumb_margin * 2) * self.animation_progress)
        thumb_y = actual_y + thumb_margin
        
        thumb_color = theme.button_text if self.checked else theme.slider_thumb_normal
        renderer.draw_rect(thumb_x, thumb_y, thumb_size, thumb_size, thumb_color)
        
        # Draw border
        if theme.border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.border, fill=False)
        
        super().render(renderer)

class ScrollingFrame(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 content_width: int, content_height: int,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):  # NOVO PARÂMETRO
        super().__init__(x, y, width, height, root_point, element_id)
        self.content_width = content_width
        self.content_height = content_height
        self.scroll_x = 0
        self.scroll_y = 0
        self.scrollbar_size = 15
        
        self.theme_type = theme or ThemeManager.get_current_theme()

    
    def handle_scroll(self, scroll_y: int):  # MUDANÇA AQUI: removido scroll_x
        """
        Handle scroll input.
        
        Args:
            scroll_y (int): Vertical scroll amount.
        """
        max_scroll_x = max(0, self.content_width - self.width)
        max_scroll_y = max(0, self.content_height - self.height)
        
        # MUDANÇA AQUI: removido scroll_x
        self.scroll_y = max(0, min(max_scroll_y, self.scroll_y - scroll_y * 20))
    
    def render(self, renderer):
        """Render the scrolling frame."""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.background)
        
        # Setup clipping for content
        original_clip = renderer.get_surface().get_clip()
        renderer.get_surface().set_clip(pygame.Rect(actual_x, actual_y, self.width, self.height))
        
        # Render children with scroll offset
        for child in self.children:
            original_x, original_y = child.x, child.y
            child.x = original_x - self.scroll_x
            child.y = original_y - self.scroll_y
            child.render(renderer)
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
    
    def _draw_horizontal_scrollbar(self, renderer, x: int, y: int, theme):
        """Draw horizontal scrollbar."""
        scrollbar_width = self.width - (self.scrollbar_size if self.content_height > self.height else 0)
        scrollbar_height = self.scrollbar_size
        
        scrollbar_x = x
        scrollbar_y = y + self.height - scrollbar_height
        
        # Track
        renderer.draw_rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, theme.slider_track)
        
        # Thumb
        thumb_width = max(20, int((self.width / self.content_width) * scrollbar_width))
        thumb_x = scrollbar_x + int((self.scroll_x / self.content_width) * (scrollbar_width - thumb_width))
        renderer.draw_rect(thumb_x, scrollbar_y, thumb_width, scrollbar_height, theme.slider_thumb_normal)
    
    def _draw_vertical_scrollbar(self, renderer, x: int, y: int, theme):
        """Draw vertical scrollbar."""
        scrollbar_width = self.scrollbar_size
        scrollbar_height = self.height - (self.scrollbar_size if self.content_width > self.width else 0)
        
        scrollbar_x = x + self.width - scrollbar_width
        scrollbar_y = y
        
        # Track
        renderer.draw_rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, theme.slider_track)
        
        # Thumb
        thumb_height = max(20, int((self.height / self.content_height) * scrollbar_height))
        thumb_y = scrollbar_y + int((self.scroll_y / self.content_height) * (scrollbar_height - thumb_height))
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
            
    def render(self, renderer):
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
        
        super().render(renderer)


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
            
    def render(self, renderer):
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
        surface = renderer.get_surface()
        pygame.draw.polygon(surface, arrow_color, arrow_points)
        
        # Draw expanded options with scroll
        if self.expanded:
            visible_options = self._get_visible_options()
            total_options_height = self.max_visible_options * self._option_height
            
            # Draw options background
            options_bg_width = self.width - (self.scrollbar_width if len(self.options) > self.max_visible_options else 0)
            renderer.draw_rect(actual_x, actual_y + self.height, options_bg_width, total_options_height, theme.dropdown_expanded)
            
            # Draw individual options
            for i, option_index in enumerate(visible_options):
                option_y = actual_y + self.height + i * self._option_height
                is_selected = option_index == self.selected_index
                
                if is_selected:
                    option_color = theme.dropdown_option_selected
                else:
                    option_color = theme.dropdown_option_normal
                
                # Check hover
                mouse_pos = pygame.mouse.get_pos()
                option_rect = (actual_x, option_y, options_bg_width, self._option_height)
                mouse_over_option = (option_rect[0] <= mouse_pos[0] <= option_rect[0] + option_rect[2] and 
                                   option_rect[1] <= mouse_pos[1] <= option_rect[1] + option_rect[3])
                
                if mouse_over_option:
                    option_color = theme.dropdown_option_hover
                
                renderer.draw_rect(actual_x, option_y, options_bg_width, self._option_height, option_color)
                
                if theme.dropdown_border:
                    renderer.draw_rect(actual_x, option_y, options_bg_width, self._option_height, 
                                     theme.dropdown_border, fill=False)
                
                option_text = self.options[option_index]
                if len(option_text) > 20:  # Further truncate for scrollbar space
                    option_text = option_text[:20] + "..."
                text_surface = self.font.render(option_text, True, theme.dropdown_text)
                renderer.draw_surface(text_surface, actual_x + 5, 
                                    option_y + (self._option_height - text_surface.get_height()) // 2)
            
            # Draw scrollbar if needed
            if len(self.options) > self.max_visible_options:
                scrollbar_rect = self._get_scrollbar_rect(actual_x, actual_y)
                scrollbar_color = (150, 150, 150) if self.is_scrolling else (100, 100, 100)
                renderer.draw_rect(scrollbar_rect[0], scrollbar_rect[1], 
                                 scrollbar_rect[2], scrollbar_rect[3], scrollbar_color)
                
        super().render(renderer)
    
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