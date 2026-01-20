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
- time: For animation timing

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
    
18. DialogBox:
    - RPG-style dialog boxes with multiple styles and animations
    - Supports multiple lines of text and custom themes

This module forms the core of LunaEngine's UI system, providing a flexible and
themeable foundation for building complex user interfaces in Pygame applications.
"""

import pygame, time, math
import numpy as np
from typing import Optional, Callable, List, Tuple, Any, Dict, Literal, TYPE_CHECKING
from enum import Enum
from abc import ABC
from .themes import ThemeManager, ThemeType
from ..core.renderer import Renderer
from ..backend.types import InputState, ElementsList, LayerType
from ..backend.opengl import OpenGLRenderer

if TYPE_CHECKING:
    from .tooltips import Tooltip, TooltipConfig, UITooltipManager

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
    _global_engine:'LunaEngine' = None
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
        self.visible:bool = True
        self.enabled:bool = True
        self.scene: 'Scene' = None
        self.children: ElementsList = ElementsList()
        self.parent = None
        self.z_index:int = 0  # For rendering order
        self.render_layer:LayerType = LayerType.NORMAL
        self.always_on_top:bool = False
        self.groups:List[str] = []
        self.corner_radius = 0
        self.border_width:int = 0
        
        # Generate unique ID using element type name
        self.element_type = self.__class__.__name__.lower()
        self.element_id = element_id if element_id else _uid_generator.generate_id(self.element_type)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        
    def get_engine(self) -> 'LunaEngine':
        return self._global_engine
    
    def set_corner_radius(self, radius: int|Tuple[int, int, int, int]):
        self.corner_radius = radius
    
    def add_group(self, group:str):
        if group not in self.groups:
            self.groups.append(str(group).lower())
            
    def remove_group(self, group:str):
        if group in self.groups:
            self.groups.remove(str(group).lower())
    
    def clear_groups(self):
        self.groups = []
        
    def has_group(self, group:str) -> bool:
        return str(group).lower() in self.groups
    
    def __str__(self) -> str:
        return f'{str(self.element_type)}-{self.element_id}'
            
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
        
    def remove_child(self, child):
        """
        Remove a child element from this UI element.
        
        Args:
            child: The child UI element to remove.
        """
        self.children.remove(child)
        child.parent = None

    def set_tooltip(self, tooltip: 'Tooltip'):
        """
        Set tooltip for this element using a Tooltip instance.
        
        Args:
            tooltip (Tooltip): Tooltip instance to associate with this element
        """
        # Import here to avoid circular imports
        from .tooltips import UITooltipManager
        UITooltipManager.register_tooltip(self, tooltip)
    
    def set_simple_tooltip(self, text: str, **kwargs):
        """
        Quick method to set a simple tooltip with text.
        
        Args:
            text (str): Tooltip text
            **kwargs: Additional arguments for TooltipConfig
        """
        # Import here to avoid circular imports
        from .tooltips import Tooltip, TooltipConfig
        
        config = TooltipConfig(text=text, **kwargs)
        tooltip = Tooltip(config)
        self.set_tooltip(tooltip)
    
    def remove_tooltip(self):
        """Remove tooltip from this element."""
        # Import here to avoid circular imports
        from .tooltips import UITooltipManager
        UITooltipManager.unregister_tooltip(self)
    
    def update(self, dt: float, inputState:InputState):
        """
        Update element state.
        
        Args:
            dt (float): Delta time in seconds since last update.
        """
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        # Check if event was already consumed by another element
        if inputState.is_event_consumed(self.element_id):
            self.state = UIState.NORMAL
            return
        
        actual_x, actual_y = self.get_actual_position()
        mouse_over = (actual_x <= inputState.mouse_pos[0] <= actual_x + self.width and 
                    actual_y <= inputState.mouse_pos[1] <= actual_y + self.height)
        
        if mouse_over:
            if inputState.mouse_just_pressed:
                self.state = UIState.PRESSED
                # Mark event as consumed to prevent other elements from using it
                inputState.consume_event(self.element_id)
                self.on_click()
            elif inputState.mouse_buttons_pressed.left and self.state == UIState.PRESSED:
                # Keep pressed state while mouse is held down
                self.state = UIState.PRESSED
            else:
                self.state = UIState.HOVERED
                self.on_hover()
        else:
            self.state = UIState.NORMAL
        
        for child in self.children:
            if hasattr(child, 'update'):
                child.update(dt)
    
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
    
    def render(self, renderer:Renderer|OpenGLRenderer):
        """
        Render this element using OpenGL backend.  
        Override this in subclasses for OpenGL-specific rendering.
        """
        
        for child in self._global_engine.layer_manager.get_elements_in_order_from(self.children):
            if hasattr(child, 'render'):
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
    
    def set_text_color(self, color: Tuple[int, int, int]):
        """
        Set the text color.
        
        Args:
            color (Tuple[int, int, int]): RGB color tuple.
        """
        self.custom_color = color
    
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
            
    def render(self, renderer:'Renderer'):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        text_color = self._get_text_color()
        
        renderer.draw_text(self.text, actual_x, actual_y, text_color, self.font)
        
        super().render(renderer)

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
    
    def render(self, renderer):
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
        
        self.background_color = ThemeManager.get_theme(self.theme_type).button_normal
        self.text_color = ThemeManager.get_theme(self.theme_type).button_text
    
    def set_background_color(self, color:Tuple[int, int, int]):
        if color is None:
            self.background_color = ThemeManager.get_theme(self.theme_type).button_normal
            return
        self.background_color = color
        
    def set_text_color(self, color:Tuple[int, int, int]):
        if color is None:
            self.text_color = ThemeManager.get_theme(self.theme_type).button_text
            return
        self.text_color = color
        
    def set_text(self, text:str):
        self.text = text
    
    def update_theme(self, theme_type):
        super().update_theme(theme_type)
        self.background_color = ThemeManager.get_theme(self.theme_type).button_normal
        self.text_color = ThemeManager.get_theme(self.theme_type).button_text
    
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
    
    def update(self, dt: float, inputState:InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        mouse_over = (actual_x <= inputState.mouse_pos[0] <= actual_x + self.width and 
                     actual_y <= inputState.mouse_pos[1] <= actual_y + self.height)
        if mouse_over:
            if inputState.mouse_buttons_pressed.left:
                self.state = UIState.PRESSED
                if not self._was_pressed and self.on_click_callback:
                    self.on_click_callback()
                self._was_pressed = True
            else:
                self.on_hover()
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False
    
        return super().update(dt, inputState)
    
    def _get_color_for_state(self) -> Tuple[int, int, int]:
        """
        Get the appropriate color for the current button state.
        
        Returns:
            Tuple[int, int, int]: RGB color tuple for the current state.
        """
        theme = self._get_colors()
        
        if self.state == UIState.NORMAL:
            return self.background_color
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
        return self.text_color
            
    def render(self, renderer:'Renderer'):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = self._get_colors()
        
        # First: Draw the border if applicable
        if theme.button_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                            theme.button_border, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # SECOND: Draw the button background
        color = self._get_color_for_state()
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, color, corner_radius=self.corner_radius)
        
        # Finally: Draw the text on top
        if self.text:
            text_color = self._get_text_color()
            center_x, center_y =  actual_x + self.width // 2, actual_y + self.height // 2
            renderer.draw_text(self.text, center_x, center_y, text_color, self.font, anchor_point=(0.5, 0.5))
                    
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
    
    def update(self, dt:float, inputState:InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        mouse_over = (actual_x <= inputState.mouse_pos[0] <= actual_x + self.width and 
                     actual_y <= inputState.mouse_pos[1] <= actual_y + self.height)
        if mouse_over:
            if inputState.mouse_buttons_pressed.left:
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
    
        return super().update(dt, inputState)
    
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
                
        super().render(renderer)

class TextBox(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str = "", font_size: int = 20, font_name: Optional[str] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 max_length: int = 0,  # NOVO: 0 means no limit
                 element_id: Optional[str] = None):
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
        self.max_length = max_length
        self._backspace_timer = 0.0 
        self._backspace_initial_delay = 0.5
        self._backspace_repeat_delay = 0.05
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
    @property
    def font(self):
        """Get the font object with lazy loading."""
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    def get_text(self) -> str:
        return str(self.text)
    
    def has_focus(self) -> bool:
        return self.focused
    
    def on_key_down(self, event:pygame.event.Event):
        """
        Handle keyboard input when focused - UPDATED with max_length support
        
        Args:
            event: Pygame keyboard event.
        """
        if not self.focused or event.type != pygame.KEYDOWN:
            return
        text_changed = False
        cursor_moved = False
        
        if event.key == pygame.K_BACKSPACE:
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
                self._needs_redraw = True
                text_changed = True
                
        elif event.key == pygame.K_DELETE:
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                self._needs_redraw = True
                text_changed = True
                
        elif event.key == pygame.K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            self._needs_redraw = True
            cursor_moved = True
            
        elif event.key == pygame.K_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            self._needs_redraw = True
            cursor_moved = True
        elif event.key == pygame.K_HOME:
            self.cursor_pos = 0
            self._needs_redraw = True
            cursor_moved = True
        elif event.key == pygame.K_END:
            self.cursor_pos = len(self.text)
            self._needs_redraw = True
            cursor_moved = True
            
        # Update rendering if needed
        if text_changed:
            self._update_text_surface()
        elif cursor_moved:
            self.cursor_visible = True
            self.cursor_timer = 0
            self._needs_redraw = True
        
    def on_key_up(self, event:pygame.event.Event):
        """
        Handle keyboard input when focused - UPDATED with max_length support
        
        Args:
            event: Pygame keyboard event.
        """
        if not self.focused or event.type != pygame.KEYUP:
            return
        
        text_changed = False
        cursor_moved = False
        
        # Handle special keys
        if event.key in [pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END]:
            # This ones are handled in on_key_down
            pass
        elif event.unicode and event.unicode.isprintable():
            # NEW: Check max_length before inserting
            if self.max_length > 0 and len(self.text) >= self.max_length:
                # At max length, don't add more characters
                pass
            else:
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
    
    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            self.focused = False
            return
        
        actual_x, actual_y = self.get_actual_position()
        mouse_over = (
            actual_x <= inputState.mouse_pos[0] <= actual_x + self.width and 
            actual_y <= inputState.mouse_pos[1] <= actual_y + self.height
        )
        
        # Handle focus changes
        old_focused = self.focused
        if inputState.mouse_buttons_pressed.left:
            self.focused = mouse_over
            if mouse_over:
                self.state = UIState.PRESSED
                self._needs_redraw = True
            else:
                self.state = UIState.NORMAL
                self._needs_redraw = True
        else:
            self.state = UIState.HOVERED if mouse_over else UIState.NORMAL
    
    def focus(self):
        """
        This will focus the textbox, like as of the user pass the mouse and click on it
        """
        self.focused = True
        self.state = UIState.PRESSED
        self._needs_redraw = True
        
    def unfocus(self):
        """
        This will unfocus the textbox, like as of the user pass the mouse and click on it
        """
        self.focused = False
        self.state = UIState.NORMAL
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
    
    def render(self, renderer):
        """Render using OpenGL backend - FIXED cursor visibility"""
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # FIRST: Draw border
        if theme.dropdown_border:
            border_color = theme.text_primary if self.focused else theme.dropdown_border
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # THEN: Draw background
        bg_color = self._get_background_color()
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color, corner_radius=self.corner_radius)
        
        # Draw text
        self._render_text_content(renderer, actual_x, actual_y, theme)
        
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
    
    def _render_text_content(self, renderer, actual_x: int, actual_y: int, theme):
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
                        if hasattr(renderer, 'render_surface'):
                            renderer.render_surface(clipped_surface, actual_x + 5, text_y)
                        else:
                            renderer.draw_surface(clipped_surface, actual_x + 5, text_y)
                    else:
                        # Fallback: render without clipping if bounds are invalid
                        if hasattr(renderer, 'render_surface'):
                            renderer.render_surface(self._text_surface, actual_x + 5, text_y)
                        else:
                            renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
                else:
                    # Text fits without scrolling
                    if hasattr(renderer, 'render_surface'):
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
                    if hasattr(renderer, 'render_surface'):
                        renderer.render_surface(clipped_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(clipped_surface, actual_x + 5, text_y)
                else:
                    # Fallback: render without clipping
                    if hasattr(renderer, 'render_surface'):
                        renderer.render_surface(self._text_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
        else:
            # Text fits normally
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(self._text_surface, actual_x + 5, text_y)
            else:
                renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
                
class DialogBox(UIElement):
    """
    RPG-style dialog box with multiple display styles and text animations.
    Supports typewriter effect, fade-in, and character-by-character display.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 style: Literal['default', 'rpg','pokemon','modern'] = "default",  # "default", "rpg", "pokemon", "modern"
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        """
        Initialize a dialog box.
        
        Args:
            x (int): X coordinate position
            y (int): Y coordinate position
            width (int): Width of dialog box
            height (int): Height of dialog box
            style (str): Visual style ("default", "rpg", "pokemon", "modern")
            theme (ThemeType): Theme to use for styling
            element_id (Optional[str]): Custom element ID
        """
        super().__init__(x, y, width, height, (0, 0), element_id)
        self.style = style
        self.theme_type = theme or ThemeManager.get_current_theme()
        
        # Text properties
        self.text = ""
        self.displayed_text = ""
        self.speaker_name = ""
        self.font_size = 20
        self.font = FontManager.get_font(None, self.font_size)
        self.name_font = FontManager.get_font(None, self.font_size - 2)
        
        # Animation properties
        self.animation_type = "typewriter"  # "typewriter", "fade", "instant"
        self.animation_speed = 30  # characters per second for typewriter
        self.animation_progress = 0.0
        self.is_animating = False
        self.is_complete = False
        
        # Visual properties based on style
        self.padding = 20
        self.name_padding = 10
        self.corner_radius = 8 if style in ["modern", "pokemon"] else 0
        self.show_continue_indicator = True
        self.continue_indicator_blink = True
        self.continue_timer = 0.0
        
        # Callbacks
        self.on_complete_callback = None
        self.on_advance_callback = None
        
        # NEW: Track if we're waiting for user input after animation completes
        self.waiting_for_advance = False
    
    def set_text(self, text: str, speaker_name: str = "", instant: bool = False):
        """
        Set dialog text and optionally a speaker name.
        
        Args:
            text (str): The dialog text to display
            speaker_name (str): Name of the speaker (optional)
            instant (bool): Whether to display text instantly
        """
        self.text = text
        self.speaker_name = speaker_name
        self.displayed_text = ""
        self.animation_progress = 0.0
        self.is_animating = not instant
        self.is_complete = instant
        self.waiting_for_advance = False  # Reset waiting state
        
        if instant:
            self.displayed_text = text
            self.waiting_for_advance = True
        else:
            self.displayed_text = ""
    
    def set_animation(self, animation_type: str, speed: int = 30):
        """
        Set text animation type and speed.
        
        Args:
            animation_type (str): "typewriter", "fade", or "instant"
            speed (int): Animation speed (characters per second for typewriter)
        """
        self.animation_type = animation_type
        self.animation_speed = speed
    
    def skip_animation(self):
        """Skip current text animation and show complete text."""
        if self.is_animating:
            self.is_animating = False
            self.is_complete = True
            self.displayed_text = self.text
            self.waiting_for_advance = True  # Now waiting for user to advance
            if self.on_complete_callback:
                self.on_complete_callback()
    
    def advance(self):
        """
        Advance to next dialog or close if complete.
        Returns True if there's more dialog, False if done.
        """
        if self.is_animating:
            self.skip_animation()
            return True
        elif self.waiting_for_advance:
            self.waiting_for_advance = False
            self.is_complete = False
            self.displayed_text = ""
            if self.on_advance_callback:
                self.on_advance_callback()
            return False
        return True
    
    def set_on_complete(self, callback: Callable):
        """Set callback for when text animation completes."""
        self.on_complete_callback = callback
    
    def set_on_advance(self, callback: Callable):
        """Set callback for when dialog is advanced."""
        self.on_advance_callback = callback
    
    def update(self, dt: float, inputState: InputState):
        """Update dialog box animations."""
        if not self.visible or not self.enabled:
            return
            
        actual_x, actual_y = self.get_actual_position()
        mouse_over = (actual_x <= inputState.mouse_pos[0] <= actual_x + self.width and 
                     actual_y <= inputState.mouse_pos[1] <= actual_y + self.height)
        
        # Only advance on mouse click when we're waiting for advance
        if mouse_over and inputState.mouse_buttons_pressed.left and self.waiting_for_advance:
            self.advance()
        
        self.state = UIState.HOVERED if mouse_over else UIState.NORMAL
            
        # Update text animation
        if self.is_animating and self.animation_type == "typewriter":
            self.animation_progress += dt * self.animation_speed
            chars_to_show = min(len(self.text), int(self.animation_progress))
            self.displayed_text = self.text[:chars_to_show]
            
            if chars_to_show >= len(self.text):
                self.is_animating = False
                self.is_complete = True
                self.waiting_for_advance = True  # Now waiting for user input
                if self.on_complete_callback:
                    self.on_complete_callback()
        
        # Update continue indicator blink - only blink when waiting for advance
        if self.show_continue_indicator and self.waiting_for_advance:
            self.continue_timer += dt
            if self.continue_timer >= 0.5:  # Blink every 0.5 seconds (faster)
                self.continue_timer = 0.0
                self.continue_indicator_blink = not self.continue_indicator_blink
                
    def render(self, renderer):
        """Render dialog box using OpenGL backend."""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        # Draw border
        if theme.dialog_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                             theme.dialog_border, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)

        # Draw main dialog box (simplified for OpenGL)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.dialog_background, 
                          corner_radius=self.corner_radius)

        # Draw speaker name
        if self.speaker_name:
            name_width = self.name_font.size(self.speaker_name)[0] + self.name_padding * 2
            name_height = self.name_font.get_height() + self.name_padding
            name_x = actual_x + 10
            name_y = actual_y - name_height // 2
            
            renderer.draw_rect(name_x, name_y, name_width, name_height, theme.dialog_name_bg, 
                              corner_radius=self.corner_radius)
            
            name_surface = self.name_font.render(self.speaker_name, True, theme.dialog_name_text)
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(name_surface, name_x + self.name_padding, name_y + self.name_padding // 2)
            else:
                renderer.draw_surface(name_surface, name_x + self.name_padding, name_y + self.name_padding // 2)
        
        # Draw text
        text_area_width = self.width - self.padding * 2
        text_area_height = self.height - self.padding * 2
        text_x = actual_x + self.padding
        text_y = actual_y + self.padding
        
        self._render_wrapped_text(renderer, text_x, text_y, text_area_width, text_area_height, theme)
        
        # Continue indicator
        if self.show_continue_indicator and self.waiting_for_advance and self.continue_indicator_blink:
            indicator_size = 10
            indicator_x = actual_x + self.width - self.padding - indicator_size
            indicator_y = actual_y + self.height - self.padding - indicator_size
            
            # Draw triangle for continue indicator
            points = [
                (indicator_x, indicator_y),
                (indicator_x + indicator_size, indicator_y),
                (indicator_x + indicator_size // 2, indicator_y + indicator_size)
            ]
            
            if hasattr(renderer, 'draw_polygon'):
                renderer.draw_polygon(points, theme.dialog_continue_indicator)
            else:
                # Fallback: draw a rectangle
                renderer.draw_rect(indicator_x, indicator_y, indicator_size, indicator_size, 
                                 theme.dialog_continue_indicator)
    
    def _render_wrapped_text(self, renderer, x: int, y: int, width: int, height: int, theme):
        """Render text with word wrapping."""
        if not self.displayed_text:
            return
            
        words = self.displayed_text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = self.font.size(test_line)[0]
            
            if test_width <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word] if self.font.size(word)[0] <= width else [word[:len(word)//2]]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Render lines
        line_height = self.font.get_height()
        max_lines = height // line_height
        
        for i, line in enumerate(lines[:max_lines]):
            line_y = y + i * line_height
            
            renderer.draw_text(line, x, line_y, theme.dialog_text, self.font)
            
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
        
        self.draw_value:bool = False
        self.font_size:int = int(self.height * 0.8)
        self.font_draw:str = None
        
        theme = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme.slider_track
        self.foreground_color = theme.button_normal
        self.font_color = theme.slider_text
        self.border_color = theme.border
        
    def set_background_color(self, color):
        self.background_color = color
        
    def set_foreground_color(self, color):
        self.foreground_color = color
        
    def set_font_color(self, color):
        self.font_color = color
        
    def set_font(self, font_name:str, font_size:int):
        self.font_size = font_size
        self.font_draw = font_name
        self.font_draw = True
    
    def set_border_color(self, color):
        self.border_color = color
        
    def update_theme(self, theme_type):
        super().update_theme(theme_type)
        theme = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme.slider_track
        self.foreground_color = theme.button_normal
        self.font_color = theme.slider_text
        self.border_color = theme.border
        
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
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw border
        if theme.border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, self.border_color, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, self.background_color, fill=True, corner_radius=self.corner_radius)
        
        # Draw progress
        progress_width = int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        if progress_width > 0:
            renderer.draw_rect(actual_x, actual_y, progress_width, self.height, self.foreground_color, fill=True, corner_radius=self.corner_radius)
        
        # Draw text
        if self.draw_value:
            font = FontManager.get_font(self.font_draw, self.font_size)
            renderer.draw_text(f"{self.get_percentage():.1f}%", actual_x, actual_y, self.font_color, font, anchor_point=(0.5, 0.5))
                
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

    def update(self, dt:float, inputState:InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
            
        mouse_pos, mouse_pressed = inputState.mouse_pos, inputState.mouse_buttons_pressed.left
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
    
    def render(self, renderer):
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
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.button_border, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
            
        # Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, color, fill=True, corner_radius=self.corner_radius)
        
        
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
        """Generate the gradient surface with cross-platform consistency"""
        self._gradient_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Use numpy for consistent color interpolation across platforms
        colors_array = np.array(self.colors, dtype=np.float32)
        
        if self.direction == "horizontal":
            for x in range(self.width):
                ratio = x / (self.width - 1) if self.width > 1 else 0
                # Use linear interpolation for consistent results
                color = self._interpolate_colors_linear(ratio)
                pygame.draw.line(self._gradient_surface, color, (x, 0), (x, self.height))
        else:  # vertical
            for y in range(self.height):
                ratio = y / (self.height - 1) if self.height > 1 else 0
                color = self._interpolate_colors_linear(ratio)
                pygame.draw.line(self._gradient_surface, color, (0, y), (self.width, y))

    def _interpolate_colors_linear(self, ratio: float) -> Tuple[int, int, int]:
        """
        Linear color interpolation for consistent cross-platform results
        
        Args:
            ratio (float): Interpolation ratio (0-1)
            
        Returns:
            Tuple[int, int, int]: Interpolated color
        """
        if len(self.colors) == 1:
            return self.colors[0]
        
        # Calculate the exact segment and ratio
        exact_position = ratio * (len(self.colors) - 1)
        segment_index = int(exact_position)
        segment_ratio = exact_position - segment_index
        
        if segment_index >= len(self.colors) - 1:
            return self.colors[-1]
        
        color1 = np.array(self.colors[segment_index], dtype=np.float32)
        color2 = np.array(self.colors[segment_index + 1], dtype=np.float32)
        
        # Linear interpolation
        interpolated = color1 + (color2 - color1) * segment_ratio
        
        return tuple(np.clip(interpolated, 0, 255).astype(int))
    
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
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if hasattr(renderer, 'render_surface'):
            renderer.render_surface(self._gradient_surface, actual_x, actual_y)
        else:
            renderer.draw_surface(self._gradient_surface, actual_x, actual_y)
                
        super().render(renderer)

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
        self._click_cooldown = time.time()
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
    
    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        mouse_pos = inputState.mouse_pos
        mouse_pressed = inputState.mouse_buttons_pressed.left
            
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
        if mouse_pressed and time.time() - self._click_cooldown > self._click_delay:
            if left_arrow_hover:
                self.previous_option()
                self._click_cooldown = time.time()
            elif right_arrow_hover:
                self.next_option()
                self._click_cooldown = time.time()
        
        self.state = UIState.HOVERED if (left_arrow_hover or right_arrow_hover) else UIState.NORMAL
    
    def render(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # FIRST: Draw border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                            theme.dropdown_border, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # THEN: Draw background
        if self.state == UIState.NORMAL:
            bg_color = theme.dropdown_normal
        else:
            bg_color = theme.dropdown_hover
            
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color, corner_radius=self.corner_radius)
        
        # FINALLY: Draw arrows and text
        self._render_select_content(renderer, actual_x, actual_y, theme)
        
        # Render children
        super().render(renderer)
    
    def _render_select_content(self, renderer, actual_x: int, actual_y: int, theme):
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
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(left_arrow_colored, left_arrow_x, left_arrow_y)
                renderer.render_surface(right_arrow_colored, right_arrow_x, right_arrow_y)
            else:
                # Fallback for OpenGL renderers without render_surface
                renderer.draw_surface(left_arrow_colored, left_arrow_x, left_arrow_y)
                renderer.draw_surface(right_arrow_colored, right_arrow_x, right_arrow_y)
        else:
            # Fallback: draw simple triangles if surfaces aren't available
            self._draw_fallback_arrows(renderer, actual_x, actual_y, arrow_color)
        
        # Draw selected text
        if self.options:
            text = self.options[self.selected_index]
            if len(text) > 15:
                text = text[:15] + "..."
            text_surface = self.font.render(text, True, theme.dropdown_text)
            text_x = actual_x + (self.width - text_surface.get_width()) // 2
            text_y = actual_y + (self.height - text_surface.get_height()) // 2
            
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(text_surface, text_x, text_y)
            else:
                renderer.draw_surface(text_surface, text_x, text_y)
    
    def _draw_fallback_arrows(self, renderer, actual_x: int, actual_y: int, arrow_color):
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
    
    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
            
        mouse_pos = inputState.mouse_pos
        mouse_pressed = inputState.mouse_buttons_pressed.left
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

    def render(self, renderer):
        """Render using OpenGL backend - CONSISTENT with Pygame"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        track_color, thumb_color = self._get_colors()
        
        # First, draw the border
        border_color = (150, 150, 150)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color, 
                        fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # Then, draw the track
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, track_color, 
                        fill=True, border_width=0, corner_radius=self.corner_radius)
        
        # Then draw the thumb
        thumb_size = max(10, int(self.height * 0.7))
        thumb_margin = max(2, (self.height - thumb_size) // 2)
        max_thumb_travel = max(10, self.width - thumb_size - (thumb_margin * 2))
        
        thumb_x = actual_x + thumb_margin + int(max_thumb_travel * self.animation_progress)
        thumb_y = actual_y + thumb_margin
        
        renderer.draw_rect(thumb_x, thumb_y, thumb_size, thumb_size, thumb_color, 
                        fill=True, border_width=0, corner_radius=thumb_size // 2)
        
        super().render(renderer)

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
    
    def set_value(self, value: float):
        self.value = max(self.min_val, min(self.max_val, value))
        if self.on_value_changed:
            self.on_value_changed(self.value)
    
    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
        
        mouse_pos, mouse_pressed = inputState.get_mouse_state()
        actual_x, actual_y = self.get_actual_position()
            
        thumb_x = actual_x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        thumb_rect = (thumb_x - 5, actual_y, 10, self.height)
        
        mouse_over_thumb = (thumb_rect[0] <= mouse_pos[0] <= thumb_rect[0] + thumb_rect[2] and 
                           thumb_rect[1] <= mouse_pos[1] <= thumb_rect[1] + thumb_rect[3])
        
        if mouse_pressed.left and (mouse_over_thumb or self.dragging):
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
    
    def render(self, renderer):
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        theme = self._get_colors()
        actual_x, actual_y = self.get_actual_position()
        
        # Draw track
        renderer.draw_rect(actual_x, actual_y + self.height//2 - 2, 
                         self.width, 4, theme.slider_track, 
                        fill=True, corner_radius=self.corner_radius)
        
        # Draw thumb
        thumb_x = actual_x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        
        if self.state == UIState.PRESSED:
            thumb_color = theme.slider_thumb_pressed
        elif self.state == UIState.HOVERED:
            thumb_color = theme.slider_thumb_hover
        else:
            thumb_color = theme.slider_thumb_normal
            
        renderer.draw_rect(thumb_x - 5, actual_y, 10, self.height, thumb_color, 
                        fill=True, corner_radius=self.corner_radius)
        
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
    
    def set_options(self, options: List[str], selected_index: int = 0):
        self.options = options
        self.selected_index = max(0, min(selected_index, len(options) - 1))
        
        # Reset dropdown
        self.expanded = False
        self.scroll_offset = 0
        self.is_scrolling = False
        self._just_opened = False
        
    def set_theme(self, theme_type: ThemeType):
        """Set dropdown theme"""
        self.theme_type = theme_type
    
    def _get_colors(self):
        """Get colors from current theme"""
        return ThemeManager.get_theme(self.theme_type)
    
    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        mouse_pos, mouse_pressed = inputState.get_mouse_state()
        actual_x, actual_y = self.get_actual_position()
            
        # Check if mouse is over main dropdown
        main_rect = (actual_x, actual_y, self.width, self.height)
        mouse_over_main = (main_rect[0] <= mouse_pos[0] <= main_rect[0] + main_rect[2] and 
                          main_rect[1] <= mouse_pos[1] <= main_rect[1] + main_rect[3])
        
        if self.expanded:
            self.render_layer = LayerType.POPUP
        else:
            self.render_layer = LayerType.NORMAL
        
        # Handle scrollbar interaction
        if self.expanded and len(self.options) > self.max_visible_options:
            scrollbar_rect = self._get_scrollbar_rect(actual_x, actual_y)
            if mouse_pressed.left and scrollbar_rect[0] <= mouse_pos[0] <= scrollbar_rect[0] + scrollbar_rect[2] and \
               scrollbar_rect[1] <= mouse_pos[1] <= scrollbar_rect[1] + scrollbar_rect[3]:
                self.is_scrolling = True
            elif not mouse_pressed:
                self.is_scrolling = False
            
            if self.is_scrolling and mouse_pressed.left:
                # Calculate scroll position based on mouse Y
                options_height = len(self.options) * self._option_height
                visible_height = self.max_visible_options * self._option_height
                scroll_area_height = visible_height - (self.scrollbar_width * 2)
                
                relative_y = mouse_pos[1] - (actual_y + self.height + self.scrollbar_width)
                scroll_ratio = max(0, min(1, relative_y / scroll_area_height))
                max_scroll = max(0, len(self.options) - self.max_visible_options)
                self.scroll_offset = int(scroll_ratio * max_scroll)
        
        # Handle mouse press
        if mouse_pressed.left and not self._just_opened and not self.is_scrolling:
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
            if not mouse_pressed.left:
                self._just_opened = False
                self.is_scrolling = False
            
            if mouse_over_main or self.expanded:
                self.state = UIState.HOVERED
            else:
                self.state = UIState.NORMAL
    
    def on_scroll(self, event: pygame.event.Event):
        """Handle mouse wheel scrolling"""
        if not self.expanded or len(self.options) <= self.max_visible_options or self.visible == False or self.enabled == False:
            return
        
        scroll_y = event.y
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
        """Render using OpenGL backend"""
        if not self.visible:
            return
            
        theme = self._get_colors()
        actual_x, actual_y = self.get_actual_position()
        
        # First: draw border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                            theme.dropdown_border, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # Then: draw main box
        if self.state == UIState.NORMAL:
            main_color = theme.dropdown_normal
        else:
            main_color = theme.dropdown_hover
            
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, main_color, corner_radius=self.corner_radius)
        
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
            self._render_expanded_options(renderer, actual_x, actual_y, theme)
        
        super().render(renderer)
    
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
    
    def _render_expanded_options(self, renderer:OpenGLRenderer, actual_x: int, actual_y: int, theme):
        """Helper method to render expanded options - WITH OPTION SEPARATORS"""
        visible_options = self._get_visible_options()
        total_options_height = self.max_visible_options * self._option_height
        
        # Calculate width for options area
        options_bg_width = self.width - (self.scrollbar_width if len(self.options) > self.max_visible_options else 0)
        
        # FIRST: Draw the main expanded options container border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y + self.height, options_bg_width, total_options_height, 
                            theme.dropdown_border, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # SECOND: Draw the main expanded options background (inset by border)
        renderer.draw_rect(actual_x, actual_y + self.height, options_bg_width, total_options_height, 
                        theme.dropdown_expanded, fill=True, border_width=self.border_width, corner_radius=self.corner_radius)
        
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
            renderer.draw_rect(actual_x, option_y, options_bg_width, self._option_height, option_color, fill=True, border_width=0, corner_radius=0)
            
            # Draw subtle separator line between options (except for the last one)
            if i < len(visible_options) - 1 and theme.dropdown_border:
                separator_y = option_y + self._option_height - 1
                separator_color = (theme.dropdown_border[0]//2, theme.dropdown_border[1]//2, theme.dropdown_border[2]//2)
                renderer.draw_rect(actual_x + 1, separator_y, options_bg_width - 2, 1, separator_color)
            
            # Draw option text
            option_text = self.options[option_index]
            if len(option_text) > 20:
                option_text = option_text[:20] + "..."
            
            text_x = actual_x + 5 + 1
            
            renderer.draw_text(option_text, text_x, option_y+int(self._option_height*0.9), theme.dropdown_text, self.font, anchor_point=(0, 1))
        
        # FOURTH: Draw scrollbar if needed
        if len(self.options) > self.max_visible_options:
            scrollbar_rect = self._get_scrollbar_rect(actual_x, actual_y)
            scrollbar_color = (150, 150, 150) if self.is_scrolling else (100, 100, 100)
            renderer.draw_rect(scrollbar_rect[0], scrollbar_rect[1], 
                            scrollbar_rect[2], scrollbar_rect[3], scrollbar_color, fill=True, border_width=0, corner_radius=self.corner_radius)
    
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
        self.corner_radius = 0
        
    def add_child(self, child: UIElement):
        """
        Add a child element to the frame.
        
        Args:
            child (UIElement): Child element to add.
        """
        super().add_child(child)
        
        
    def set_background_color(self, color: Optional[Tuple[int, int, int]]):
        """
        Set the background color of the frame.
        
        Args:
            color (Optional[Tuple[int, int, int]]): RGB color tuple or None for transparent.
        """
        self.background_color = color
        
    def set_border_color(self, color: Optional[Tuple[int, int, int]]):
        """
        Set the border color of the frame.
        
        Args:
            color (Optional[Tuple[int, int, int]]): RGB color tuple or None for no border.
        """
        self.border_color = color
        
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
        
    def set_corner_radius(self, radius: int|Tuple[int, int, int, int]):
        self.corner_radius = radius
        
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
    
    def update(self, dt, inputState):
        for child in self.children:
            if hasattr(child, 'update'):
                child.update(dt, inputState)
    
    def render(self, renderer):
        """Render frame using OpenGL backend"""
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw border first (if any)
        border_color = self.border_color or (theme.border if theme.border else None)
        if border_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             border_color, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # Draw background
        bg_color = self.background_color or theme.background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color, corner_radius=self.corner_radius)
        
        # Render children
        super().render(renderer)
    
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
        
class NumberSelector(UIElement):
    """
    UI element that allows a user to select a number within a specified range 
    using increment and decrement controls.
    
    This element manages its value internally, ensuring it stays within 
    the defined min_value and max_value. It also handles formatting with 
    a minimum number of digits (min_length) using padding.
    
    Attributes:
        min_value (int): The lowest allowed value.
        max_value (int): The highest allowed value.
        min_length (int): Minimum number of digits for display padding (e.g., 5 -> '05').
        max_length (int): Maximum number of digits allowed.
        
    Internal Attributes:
        _value (int): The current selected value.
        _font (pygame.font.Font): Cached font object used for rendering the number.
        _up_rect (pygame.Rect): Rectangular area for the increment button (relative position).
        _down_rect (pygame.Rect): Rectangular area for the decrement button (relative position).
        _is_up_pressed (bool): True if the increment button is currently pressed.
        _is_down_pressed (bool): True if the decrement button is currently pressed.
        _last_mouse_pos_rel (Tuple[int, int]): Last mouse position relative to the element (for state update).
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, min_value: int, max_value: int, 
                 value: int, min_length: int = 1, max_length: int = 10,
                 root_point: Tuple[float, float] = (0, 0),theme: ThemeType = None, element_id: Optional[str] = None):
        """
        Initialize the NumberSelector element.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            width (int): Width of the number selector.
            height (int): Height of the number selector.
            min_value (int): Minimum selectable value.
            max_value (int): Maximum selectable value.
            value (int): Initial value for the number selector.
            min_length (int): Minimum number of digits for display padding (defaults to 1).
            max_length (int): Maximum number of digits allowed (defaults to 10).
            root_point (Tuple[float, float]): Anchor point for positioning.
            theme (ThemeType): Theme to use for styling.
            element_id (Optional[str]): Custom element ID.
        """
        # Initialize base UIElement
        super().__init__(x, y, width, height, root_point, element_id)
        
        # Store properties
        self.min_value = min_value
        self.max_value = max_value
        self.min_length = min_length
        self.max_length = max_length
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.font_size = int(height * 0.6) # Dynamic font size based on element height
        
        # Clamp and set initial value
        self._value = max(self.min_value, min(self.max_value, value))
        self._font = FontManager.get_font(None, self.font_size) # Use FontManager
        
        # Internal state for mouse interaction
        self._is_up_pressed = False
        self._is_down_pressed = False
        self._up_rect = None
        self._down_rect = None
        self._last_mouse_pos_rel = (0, 0)
        
        # Setup the control button areas
        self._setup_control_areas()
        
    @property
    def value(self) -> int:
        """
        Get the current selected value.
        
        Returns:
            int: The current numeric value.
        """
        return self._value
    
    def get_value(self) -> int:
        return self.value

    @value.setter
    def value(self, new_value: int):
        """
        Set the value, ensuring it stays within min/max bounds.
        
        Args:
            new_value (int): The new value to set.
        """
        self._value = max(self.min_value, min(self.max_value, new_value))

    def _format_value(self) -> str:
        """
        Formats the current value with padding based on min_length.
        
        Returns:
            str: The formatted string representation of the value (e.g., '007').
        """
        # Uses zfill for optimal performance
        padding = max(1, self.min_length)
        return str(self.value).zfill(padding)

    def increment(self):
        """Increments the value, respecting max_value."""
        if self._value < self.max_value:
            self.value += 1
            
    def decrement(self):
        """Decrements the value, respecting min_value."""
        if self._value > self.min_value:
            self.value -= 1
            
    def _setup_control_areas(self):
        """
        Defines the rectangular areas for the increment (up) and decrement (down) buttons.
        These are relative to the element's top-left corner (0, 0).
        """
        # Use 1/4 of the total width for the control area, or the full height if smaller
        control_width = min(self.height, self.width // 4) 
        
        # Control area is located on the right side of the element
        control_x = self.width - control_width
        
        # Down button (Bottom half of control area)
        self._down_rect = pygame.Rect(
            control_x,
            self.height // 2,
            control_width,
            self.height // 2
        )
        
        # Up button (Top half of control area)
        self._up_rect = pygame.Rect(
            control_x,
            0,
            control_width,
            self.height // 2
        )
        
    def _get_button_colors(self, theme):
        """
        Determines the colors for the buttons based on the current state and theme.
        
        Args:
            theme: The current theme object from ThemeManager.
            
        Returns:
            Tuple: (up_color, down_color, text_color, border_color, background_color)
        """
        # Default colors from theme
        up_color = theme.button_normal
        down_color = theme.button_normal
        text_color = theme.button_text
        border_color = theme.button_border
        background_color = theme.background
        
        # Check for hover state over specific buttons
        if self.state == UIState.HOVERED or self.state == UIState.PRESSED:
            up_over = self._up_rect.collidepoint(self._last_mouse_pos_rel)
            down_over = self._down_rect.collidepoint(self._last_mouse_pos_rel)
            
            if up_over:
                up_color = theme.button_hover
            if down_over:
                down_color = theme.button_hover

            # Check for pressed state
            if self._is_up_pressed:
                up_color = theme.button_pressed
            if self._is_down_pressed:
                down_color = theme.button_pressed
            
        return up_color, down_color, text_color, border_color, background_color
    
    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        mouse_pos, mouse_pressed = inputState.get_mouse_state()
        actual_x, actual_y = self.get_actual_position()
        
        # Mouse position relative to the element
        mouse_rel_x = mouse_pos[0] - actual_x
        mouse_rel_y = mouse_pos[1] - actual_y
        self._last_mouse_pos_rel = (mouse_rel_x, mouse_rel_y)
        
        mouse_over_main = (0 <= mouse_rel_x <= self.width and 0 <= mouse_rel_y <= self.height)
        
        self._is_up_pressed = False
        self._is_down_pressed = False
        
        if mouse_over_main:
            self.state = UIState.HOVERED
            
            up_over = self._up_rect.collidepoint(self._last_mouse_pos_rel)
            down_over = self._down_rect.collidepoint(self._last_mouse_pos_rel)
            
            # The logic relies on a single-frame "just pressed" state which is not available 
            # in the base UIElement._update_with_mouse signature.
            # We use _was_pressed to simulate a single action per click (Regra 1: optimization/functionality).
            if not hasattr(self, '_was_pressed'):
                 self._was_pressed = False
            
            if mouse_pressed.left:
                if up_over:
                    self._is_up_pressed = True
                    self.state = UIState.PRESSED
                    if not self._was_pressed:
                        self.increment()
                        self._was_pressed = True
                
                elif down_over:
                    self._is_down_pressed = True
                    self.state = UIState.PRESSED
                    if not self._was_pressed:
                        self.decrement()
                        self._was_pressed = True
                else:
                    self._was_pressed = False
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False # Reset for the next click
                
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False

    def render(self, renderer):
        """
        Render the NumberSelector using OpenGL backend.
        
        Args:
            renderer: The OpenGL renderer object.
        """
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        up_color, down_color, text_color, border_color, background_color = self._get_button_colors(theme)
        
        # 1. Draw the border around the main element
        if border_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color, fill=False)
        
        # 2. Draw main background rectangle
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, background_color)
        
        # 3. Draw UP button area
        renderer.draw_rect(actual_x + self._up_rect.x, actual_y + self._up_rect.y, 
                           self._up_rect.width, self._up_rect.height, up_color)
        
        # 4. Draw DOWN button area
        renderer.draw_rect(actual_x + self._down_rect.x, actual_y + self._down_rect.y, 
                           self._down_rect.width, self._down_rect.height, down_color)

        # 5. Draw the value text
        formatted_value = self._format_value()
        
        # Center text in the number area
        text_area_width = self.width - self._up_rect.width
        center_x = actual_x + text_area_width // 2
        center_y = actual_y + self.height // 2

        renderer.draw_text(formatted_value, center_x, center_y, text_color, self._font, anchor_point=(0.5, 0.5))
        
        # 6. Draw increment/decrement symbols (Triangles)
        up_rect_abs = (actual_x + self._up_rect.x, actual_y + self._up_rect.y, self._up_rect.width, self._up_rect.height)
        center_up = (up_rect_abs[0] + up_rect_abs[2] // 2, up_rect_abs[1] + up_rect_abs[3] // 2)
        triangle_size = min(up_rect_abs[2], up_rect_abs[3]) // 3
        up_triangle_points = [
            (center_up[0], center_up[1] - triangle_size), 
            (center_up[0] - triangle_size, center_up[1] + triangle_size // 2),
            (center_up[0] + triangle_size, center_up[1] + triangle_size // 2)
        ]
        renderer.draw_polygon(up_triangle_points, text_color)
        
        down_rect_abs = (actual_x + self._down_rect.x, actual_y + self._down_rect.y, self._down_rect.width, self._down_rect.height)
        center_down = (down_rect_abs[0] + down_rect_abs[2] // 2, down_rect_abs[1] + down_rect_abs[3] // 2)
        down_triangle_points = [
            (center_down[0], center_down[1] + triangle_size),
            (center_down[0] - triangle_size, center_down[1] - triangle_size // 2),
            (center_down[0] + triangle_size, center_down[1] - triangle_size // 2)
        ]
        renderer.draw_polygon(down_triangle_points, text_color)
        
class Checkbox(UIElement):
    """
    A binary state control element that allows a user to select a boolean value (checked or unchecked).
    
    The Checkbox is typically rendered as a small square box that can be toggled by clicking.
    
    Attributes:
        checked (bool): The current state of the checkbox (True if checked, False otherwise).
        label (Optional[str]): The text label to display next to the checkbox.
        label_position (str): Position of the label relative to the box ('right' or 'left').
        box_size (int): The size (width and height) of the square checkbox box.
        
    Internal Attributes:
        _font (pygame.font.Font): Cached font object for rendering the label.
    """
    on_toggle: Callable[[bool], None] = None
    
    def __init__(self, x: int, y: int, width: int, height: int, checked: bool,
                 label: Optional[str] = None, label_position: str = 'right',
                 root_point: Tuple[float, float] = (0, 0), theme: ThemeType = None, element_id: Optional[str] = None):
        """
        Initialize the Checkbox element.
        
        The width and height define the overall bounding box, including the label.
        The actual checkbox box size is calculated based on the height.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            width (int): Total width of the element (box + label).
            height (int): Total height of the element (usually the box size).
            checked (bool): Initial state of the checkbox.
            theme_type (ThemeType): Theme type for styling.
            label (Optional[str]): Text label displayed next to the box.
            label_position (str): Where to place the label ('right' or 'left').
            root_point (Tuple[float, float]): Anchor point for positioning.
            element_id (Optional[str]): Custom element ID.
        """
        # Initialize base UIElement
        super().__init__(x, y, width, height, root_point, element_id)
        
        # Store properties
        self.checked = checked
        self.label = label
        self.label_position = label_position.lower()
        self.theme_type = theme or ThemeManager.get_current_theme()
        
        # The box size is determined by the element's height to keep it square and proportional
        self.box_size = height 
        
        # Dynamic font size for the label
        self.font_size = int(height * 0.8) 
        self._font = FontManager.get_font(None, self.font_size) # Use FontManager

    def set_on_toggle(self, callback: Callable[[bool], None]):
        self.on_toggle = callback
    
    def get_state(self) -> bool:
        return self.checked
    
    def value(self) -> bool:
        return self.checked
    
    def _get_colors(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]:
        """
        Determines the colors for the checkbox based on the current state and theme.
        
        Args:
            theme: The current theme object from ThemeManager.
            
        Returns:
            Tuple: (box_color, check_color, border_color, label_color)
        """
        theme = ThemeManager.get_theme(self.theme_type)
        # Default colors from theme
        box_color = theme.border2
        border_color = theme.button_border
        check_color = theme.button_text
        label_color = theme.button_text
        
        # Apply hover/pressed effects
        if self.state == UIState.HOVERED:
            # Subtle change for hover on the border or box
            border_color = theme.border
        elif self.state == UIState.PRESSED:
            # Change for pressed state
            box_color = theme.border
        elif self.state == UIState.DISABLED:
            box_color = theme.button_disabled
        if border_color is None:
            print(f"Border color is None\n{self.theme_type}\n{theme.button_border}")
            border_color = (0,0,0)
        return box_color, check_color, border_color, label_color

    def toggle(self):
        """
        Toggles the state of the checkbox (True -> False, False -> True).
        """
        self.checked = not self.checked
        if self.on_toggle:
            if callable(self.on_toggle):
                self.on_toggle(self.checked)

    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
        
        mouse_pos, mouse_pressed = inputState.get_mouse_state()    
        actual_x, actual_y = self.get_actual_position()
        
        # Mouse position relative to the element
        mouse_rel_x = mouse_pos[0] - actual_x
        mouse_rel_y = mouse_pos[1] - actual_y
        
        mouse_over_main = (0 <= mouse_rel_x <= self.width and 0 <= mouse_rel_y <= self.height)
        
        # The logic relies on a single-frame "just pressed" state.
        if not hasattr(self, '_was_pressed'):
             self._was_pressed = False
            
        if mouse_over_main:
            self.state = UIState.HOVERED
            
            if mouse_pressed.left:
                self.state = UIState.PRESSED
                if not self._was_pressed:
                    self.toggle()
                    self._was_pressed = True
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False # Reset for the next click
                
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False

    def render(self, renderer):
        """
        Render the Checkbox and its label using OpenGL backend.
        
        Args:
            renderer: The OpenGL renderer object.
        """
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        box_color, check_color, border_color, label_color = self._get_colors()
        
        # 1. Determine Box Position
        box_x = actual_x
        label_surface = None
        
        if self.label:
            # Assume OpenGL renderer has a way to measure text or you pre-render
            label_width, label_height = self._font.size(self.label)
            
            if self.label_position == 'right':
                box_x = actual_x # Box is on the left
                label_x = actual_x + self.box_size + 5
            else: # 'left'
                box_x = actual_x + self.width - self.box_size
                label_x = actual_x

        # 2. Draw the border
        renderer.draw_rect(box_x, actual_y, self.box_size, self.box_size, border_color, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # 3. Draw the main box background
        renderer.draw_rect(box_x, actual_y, self.box_size, self.box_size, box_color, corner_radius=self.corner_radius)
        
        # 4. Draw the checkmark if checked
        if self.checked:
            # Since OpenGL triangle drawing details are unknown, we use a simple generic line draw
            
            # Simple X mark (for illustration, assuming draw_line exists)
            padding = self.box_size // 4
            x1, y1 = box_x + padding, actual_y + padding
            x2, y2 = box_x + self.box_size - padding, actual_y + self.box_size - padding
            
            # Checkmark points:
            check_points = [
                ((box_x + self.box_size * 0.2, actual_y + self.box_size * 0.5), (box_x + self.box_size * 0.4, actual_y + self.box_size * 0.8)), 
                ((box_x + self.box_size * 0.4, actual_y + self.box_size * 0.8), (box_x + self.box_size * 0.8, actual_y + self.box_size * 0.2)), 
            ]
            renderer.draw_lines(check_points, check_color, width=3)


        # 5. Draw the label
        if self.label:
            label_y = actual_y + self.height // 2 # Center vertically
            
            if self.label_position == 'left':
                label_x = box_x - label_width - 5
            
            # Assumes the OpenGL renderer supports text drawing with center anchoring (0, 0.5)
            # or bottom left anchoring and we calculate the Y offset for vertical center.
            renderer.draw_text(self.label, label_x, label_y, label_color, self._font, anchor_point=(0.0, 0.5))

class ScrollingFrame(UiFrame):
    """
    A frame container with scrollable content.
    
    Supports both horizontal and vertical scrolling with scrollbars.
    Automatically handles clipping of child elements to visible area.
    
    Attributes:
        content_width (int): Total width of scrollable content area.
        content_height (int): Total height of scrollable content area.
        scroll_x (int): Current horizontal scroll position.
        scroll_y (int): Current vertical scroll position.
        scrollbar_size (int): Width/height of scrollbars.
        dragging_vertical (bool): Whether vertical scrollbar is being dragged.
        dragging_horizontal (bool): Whether horizontal scrollbar is being dragged.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 content_width: int, content_height: int,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        """
        Initialize a scrolling frame.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            width (int): Visible width of the frame.
            height (int): Visible height of the frame.
            content_width (int): Total width of scrollable content.
            content_height (int): Total height of scrollable content.
            root_point (Tuple[float, float]): Anchor point for positioning.
            theme (ThemeType): Theme to use for styling.
            element_id (Optional[str]): Custom element ID.
        """
        super().__init__(x, y, width, height, root_point, theme, element_id)
        
        self.content_width = content_width
        self.content_height = content_height
        self.scroll_x = 0
        self.scroll_y = 0
        self.scrollbar_size = 15
        self.dragging_vertical = False
        self.dragging_horizontal = False
        self.scroll_drag_start = (0, 0)
        
        # Override default padding from UiFrame
        self.padding = 0
        
        # Store original background color
        self._background_color_override = None
        
    def set_background_color(self, color: Tuple[int, int, int]):
        """
        Set background color for the scrolling frame.
        
        Args:
            color (Tuple[int, int, int]): RGB color tuple.
        """
        self._background_color_override = color
        
    def update_theme(self, theme_type):
        """
        Update theme for scrolling frame.
        
        Args:
            theme_type (ThemeType): New theme to apply.
        """
        super().update_theme(theme_type)
        
    def clear_children(self):
        """
        Remove all child elements from the scrolling frame.
        """
        self.children.clear()

    def update(self, dt, inputState):
        """
        Update scrolling frame state and handle user interaction.
        
        Args:
            dt (float): Delta time in seconds.
            inputState (InputState): Current input state.
        """
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        # Calculate actual position
        mouse_pos = inputState.mouse_pos
        actual_x, actual_y = self.get_actual_position()
        
        mouse_over:bool = (
            actual_x <= mouse_pos[0] <= actual_x + self.width and
            actual_y <= mouse_pos[1] <= actual_y + self.height
        )
        
        # Update state
        if mouse_over:
            self.state = UIState.HOVERED
        else:
            self.state = UIState.NORMAL
        
        # Get mouse state
        mouse_pos = inputState.mouse_pos
        mouse_pressed = inputState.mouse_buttons_pressed.left
        
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
        # Adjusted mouse position relative to scrolled content
        scrolled_mouse_pos = (mouse_pos[0] + self.scroll_x - actual_x, 
                             mouse_pos[1] + self.scroll_y - actual_y)
        
        # Update children manually since we're overriding the update method
        for child in self.children:
            if hasattr(child, 'update'):
                # Create a modified input state with adjusted mouse position
                # This is a simplified approach - in a real implementation,
                # you might want to create a proper InputState proxy
                child.update(dt, inputState)
        
        # self.state = UIState.NORMAL
        
    def on_scroll(self, event: pygame.event.Event):
        """
        Handle mouse wheel scrolling.
        
        Args:
            scroll_y (int): Scroll amount (positive for up, negative for down).
        """
        if event.type != pygame.MOUSEWHEEL or self.state != UIState.HOVERED or not self.enabled:
            return
        max_scroll_y = max(0, self.content_height - self.height)
        self.scroll_y = max(0, min(max_scroll_y, self.scroll_y - event.y * 30))
        max_scroll_x = max(0, self.content_width - self.width)
        self.scroll_x = max(0, min(max_scroll_x, self.scroll_x - event.y * 30))

    def render(self, renderer):
        """
        Render scrolling frame and its content.
        
        Args:
            renderer (Renderer): Renderer object for drawing.
        """
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Get background color (use override if set, otherwise from theme)
        bg_color = self._background_color_override or theme.background
        
        # FIRST: Draw border (inherited from UiFrame)
        border_color = self.border_color or (theme.border if theme.border else None)
        if border_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             border_color, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # THEN: Draw background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color, corner_radius=self.corner_radius)
        
        # Enable clipping for content area
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
            child.render(renderer)
            
            # Restore original position immediately
            child.x, child.y = original_x, original_y
        
        # Disable scissor test
        if hasattr(renderer, 'disable_scissor'):
            renderer.disable_scissor()
        
        # Draw scrollbars on top (outside of clipping region)
        if self.content_width > self.width:
            self._draw_horizontal_scrollbar(renderer, actual_x, actual_y, theme)
        
        if self.content_height > self.height:
            self._draw_vertical_scrollbar(renderer, actual_x, actual_y, theme)
    
    def _get_vertical_scrollbar_rect(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """
        Get the vertical scrollbar rectangle.
        
        Args:
            x (int): X position of frame.
            y (int): Y position of frame.
            
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height) of scrollbar thumb.
        """
        if self.content_height <= self.height:
            return (0, 0, 0, 0)
        
        scrollbar_width = self.scrollbar_size
        scrollbar_height = self.height - (self.scrollbar_size if self.content_width > self.width else 0)
        
        scrollbar_x = x + self.width - scrollbar_width
        scrollbar_y = y
        
        # Calculate thumb height and position
        max_scroll_y = max(1, self.content_height - self.height)
        thumb_height = max(20, int((self.height / self.content_height) * scrollbar_height))
        
        available_height = scrollbar_height - thumb_height
        scroll_ratio = self.scroll_y / max_scroll_y
        thumb_y = scrollbar_y + int(scroll_ratio * available_height)
        
        return (scrollbar_x, thumb_y, scrollbar_width, thumb_height)

    def _get_horizontal_scrollbar_rect(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """
        Get the horizontal scrollbar rectangle.
        
        Args:
            x (int): X position of frame.
            y (int): Y position of frame.
            
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height) of scrollbar thumb.
        """
        if self.content_width <= self.width:
            return (0, 0, 0, 0)
        
        scrollbar_width = self.width - (self.scrollbar_size if self.content_height > self.height else 0)
        scrollbar_height = self.scrollbar_size
        
        scrollbar_x = x
        scrollbar_y = y + self.height - scrollbar_height
        
        # Calculate thumb width and position
        max_scroll_x = max(1, self.content_width - self.width)
        thumb_width = max(20, int((self.width / self.content_width) * scrollbar_width))
        
        available_width = scrollbar_width - thumb_width
        scroll_ratio = self.scroll_x / max_scroll_x
        thumb_x = scrollbar_x + int(scroll_ratio * available_width)
        
        return (thumb_x, scrollbar_y, thumb_width, scrollbar_height)
    
    def _draw_horizontal_scrollbar(self, renderer, x: int, y: int, theme):
        """
        Draw horizontal scrollbar.
        
        Args:
            renderer (Renderer): Renderer object.
            x (int): X position of frame.
            y (int): Y position of frame.
            theme: Current theme.
        """
        scrollbar_width = self.width - (self.scrollbar_size if self.content_height > self.height else 0)
        scrollbar_height = self.scrollbar_size
        
        scrollbar_x = x
        scrollbar_y = y + self.height - scrollbar_height
        
        # Track
        renderer.draw_rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, theme.slider_track)
        
        # Thumb
        max_scroll_x = max(1, self.content_width - self.width)
        thumb_width = max(20, int((self.width / self.content_width) * scrollbar_width))
        
        available_width = scrollbar_width - thumb_width
        scroll_ratio = self.scroll_x / max_scroll_x
        thumb_x = scrollbar_x + int(scroll_ratio * available_width)
        
        thumb_color = theme.slider_thumb_pressed if self.dragging_horizontal else theme.slider_thumb_normal
        renderer.draw_rect(thumb_x, scrollbar_y, thumb_width, scrollbar_height, thumb_color)

    def _draw_vertical_scrollbar(self, renderer, x: int, y: int, theme):
        """
        Draw vertical scrollbar.
        
        Args:
            renderer (Renderer): Renderer object.
            x (int): X position of frame.
            y (int): Y position of frame.
            theme: Current theme.
        """
        scrollbar_width = self.scrollbar_size
        scrollbar_height = self.height - (self.scrollbar_size if self.content_width > self.width else 0)
        
        scrollbar_x = x + self.width - scrollbar_width
        scrollbar_y = y
        
        # Track
        renderer.draw_rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, theme.slider_track)
        
        # Thumb
        max_scroll_y = max(1, self.content_height - self.height)
        thumb_height = max(20, int((self.height / self.content_height) * scrollbar_height))
        
        available_height = scrollbar_height - thumb_height
        scroll_ratio = self.scroll_y / max_scroll_y
        thumb_y = scrollbar_y + int(scroll_ratio * available_height)
        
        thumb_color = theme.slider_thumb_pressed if self.dragging_vertical else theme.slider_thumb_normal
        renderer.draw_rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height, thumb_color)   
            
class Tabination(UiFrame):
    """
    A tabbed interface element that organizes content into multiple tabs.
    
    Displays clickable tabs at the top with their content below.
    Supports alternating background colors for tabs and theme-based styling.
    
    Attributes:
        tabs (List[Dict]): List of tab information dictionaries.
        current_tab (int): Index of currently active tab.
        tab_height (int): Height of the tab headers.
        font_size (int): Font size for tab titles.
        font_name (str): Font name for tab titles.
        tab_padding (int): Padding inside tabs.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 font_size: int = 20, font_name: Optional[str] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        """
        Initialize a Tabination element.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            width (int): Width of the tabination element.
            height (int): Height of the tabination element.
            font_size (int): Font size for tab titles.
            font_name (Optional[str]): Font name for tab titles.
            root_point (Tuple[float, float]): Anchor point for positioning.
            theme (ThemeType): Theme to use for styling.
            element_id (Optional[str]): Custom element ID.
        """
        super().__init__(x, y, width, height, root_point, theme, element_id)
        
        self.tabs = []  # List of dicts: {'name': str, 'frame': Frame, 'visible': bool}
        self.current_tab = None  # Index of currently active tab
        
        # Tab header properties
        self.tab_height = 30  # Height of tab headers
        self.font_size = font_size
        self.font_name = font_name
        self.tab_padding = 10  # Padding inside tabs
        self.tab_spacing = 2   # Space between tabs
        
        # Font for tab titles
        self._font = None
        
        # Background colors for alternating tabs
        self.even_tab_bg = None
        self.odd_tab_bg = None
        self._calculate_tab_colors()
        
        # Override default padding for content area
        self.padding = 0
        
    def _calculate_tab_colors(self):
        """Calculate alternating background colors for tabs based on theme."""
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Base color from theme
        base_color = theme.button_normal
        
        # Create lighter and darker variations
        if base_color:
            # Even tabs (lighter)
            self.even_tab_bg = tuple(min(255, c + 20) for c in base_color)
            # Odd tabs (darker)
            self.odd_tab_bg = tuple(max(0, c - 10) for c in base_color)
        else:
            # Fallback colors
            self.even_tab_bg = (220, 220, 220)
            self.odd_tab_bg = (200, 200, 200)
    
    @property
    def font(self):
        """Get the font object with lazy loading."""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    def update_theme(self, theme_type: ThemeType):
        """
        Update theme for tabination and recalculate tab colors.
        
        Args:
            theme_type (ThemeType): The new theme to apply.
        """
        super().update_theme(theme_type)
        self._calculate_tab_colors()
        
        # Update theme for all tab frames
        for tab in self.tabs:
            if hasattr(tab['frame'], 'update_theme'):
                tab['frame'].update_theme(theme_type)
    
    def add_tab(self, tab_name: str) -> bool:
        """
        Add a new tab to the tabination.
        
        Args:
            tab_name (str): Name/title of the new tab.
            
        Returns:
            bool: True if tab was added successfully, False if tab already exists.
        """
        # Check if tab already exists
        for tab in self.tabs:
            if tab['name'].lower() == tab_name.lower():
                return False
        
        # Calculate content area dimensions
        content_height = self.height - self.tab_height
        content_width = self.width
        
        # Create a frame for this tab's content
        tab_frame = UiFrame(0, self.tab_height, content_width, content_height, 
                           theme=self.theme_type)
        tab_frame.visible = False  # Hide by default
        
        # Add frame as a child
        super().add_child(tab_frame)
        
        # Store tab information
        tab_info = {
            'name': tab_name,
            'frame': tab_frame,
            'visible': False
        }
        
        self.tabs.append(tab_info)
        
        # If this is the first tab, make it active
        if self.current_tab is None:
            self.current_tab = 0
            self.tabs[0]['visible'] = True
            self.tabs[0]['frame'].visible = True
        
        return True
    
    def add_to_tab(self, tab_name: str, ui_element: UIElement) -> bool:
        """
        Add a UI element to a specific tab.
        
        Args:
            tab_name (str): Name of the tab to add element to.
            ui_element (UIElement): The UI element to add.
            
        Returns:
            bool: True if element was added successfully, False if tab doesn't exist.
        """
        # Find the tab
        tab_index = -1
        for i, tab in enumerate(self.tabs):
            if tab['name'].lower() == tab_name.lower():
                tab_index = i
                break
        
        if tab_index == -1:
            return False
        
        # Add element to the tab's frame
        self.tabs[tab_index]['frame'].add_child(ui_element)
        return True
    
    def switch_tab(self, tab_index: int) -> bool:
        """
        Switch to a different tab by index.
        
        Args:
            tab_index (int): Index of tab to switch to.
            
        Returns:
            bool: True if switched successfully, False if index is invalid.
        """
        if tab_index < 0 or tab_index >= len(self.tabs):
            return False
        
        # Hide current tab
        if self.current_tab is not None:
            self.tabs[self.current_tab]['visible'] = False
            self.tabs[self.current_tab]['frame'].visible = False
        
        # Show new tab
        self.current_tab = tab_index
        self.tabs[tab_index]['visible'] = True
        self.tabs[tab_index]['frame'].visible = True
        
        return True
    
    def get_tab_index(self, tab_name: str) -> int:
        """
        Get the index of a tab by name.
        
        Args:
            tab_name (str): Name of the tab.
            
        Returns:
            int: Index of the tab, or -1 if not found.
        """
        for i, tab in enumerate(self.tabs):
            if tab['name'].lower() == tab_name.lower():
                return i
        return -1
    
    def remove_tab(self, tab_name: str) -> bool:
        """
        Remove a tab and all its contents.
        
        Args:
            tab_name (str): Name of the tab to remove.
            
        Returns:
            bool: True if tab was removed, False if tab doesn't exist.
        """
        tab_index = self.get_tab_index(tab_name)
        if tab_index == -1:
            return False
        
        # If removing the current tab, switch to another if available
        if tab_index == self.current_tab:
            # Try to switch to next tab, or previous if no next
            if len(self.tabs) > 1:
                new_index = (tab_index + 1) % len(self.tabs)
                if new_index == tab_index:  # Only one tab
                    new_index = -1
                if new_index != -1:
                    self.switch_tab(new_index)
            else:
                self.current_tab = None
        
        # Remove the tab's frame from children
        tab_frame = self.tabs[tab_index]['frame']
        if tab_frame in self.children:
            self.children.remove(tab_frame)
        
        # Remove tab from list
        self.tabs.pop(tab_index)
        
        # If we removed the tab we were going to switch to, adjust current_tab
        if self.current_tab is not None and self.current_tab >= len(self.tabs):
            self.current_tab = max(0, len(self.tabs) - 1)
            if self.tabs:
                self.tabs[self.current_tab]['visible'] = True
                self.tabs[self.current_tab]['frame'].visible = True
        
        return True
    
    def get_tab(self, tab_name:str) -> Optional[Dict[str, Any]]:
        """
        Get information about a tab by name.
        
        Args:
            tab_name (str): Name of the tab.
            
        Returns:
            Optional[Dict[str, Any]]: Tab information dictionary, or None if tab doesn't exist.
        """
        tab_index = self.get_tab_index(tab_name)
        if tab_index == -1:
            return None
        return self.tabs[tab_index]
    
    def get_tab_frame(self, tab_name: str) -> Optional[UiFrame]:
        """
        Get the frame associated with a tab.
        
        Args:
            tab_name (str): Name of the tab.
            
        Returns:
            Optional[UiFrame]: The tab's frame, or None if tab doesn't exist.
        """
        tab_index = self.get_tab_index(tab_name)
        if tab_index == -1:
            return None
        return self.tabs[tab_index]['frame']
    
    def _get_tab_colors(self, tab_index: int, is_active: bool, is_hovered: bool) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """
        Get colors for a tab based on its state.
        
        Args:
            tab_index (int): Index of the tab.
            is_active (bool): Whether tab is currently active.
            is_hovered (bool): Whether tab is being hovered.
            
        Returns:
            Tuple[Tuple[int, int, int], Tuple[int, int, int]]: (bg_color, text_color)
        """
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Text color
        if is_active:
            text_color = theme.button_text
        else:
            text_color = tuple(max(0, c - 50) for c in theme.button_text)
        
        # Background color
        if is_active:
            bg_color = theme.button_normal
        elif is_hovered:
            bg_color = theme.button_hover
        else:
            # Alternating colors for inactive tabs
            if tab_index % 2 == 0:  # Even index
                bg_color = self.even_tab_bg
            else:  # Odd index
                bg_color = self.odd_tab_bg
        
        return bg_color, text_color
    
    def _get_tab_rect(self, tab_index: int, actual_x: int, actual_y: int) -> Tuple[int, int, int, int]:
        """
        Calculate the rectangle for a tab header.
        
        Args:
            tab_index (int): Index of the tab.
            actual_x (int): Actual X position of tabination.
            actual_y (int): Actual Y position of tabination.
            
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height) of tab rectangle.
        """
        if not self.tabs:
            return (0, 0, 0, 0)
        
        # Calculate tab width based on number of tabs
        total_tab_width = self.width - (len(self.tabs) - 1) * self.tab_spacing
        tab_width = total_tab_width // len(self.tabs)
        
        # Calculate tab position
        tab_x = actual_x + tab_index * (tab_width + self.tab_spacing)
        tab_y = actual_y
        
        return (tab_x, tab_y, tab_width, self.tab_height)
    
    def update(self, dt, inputState):
        """
        Update tabination state and handle tab clicks.
        
        Args:
            dt (float): Delta time in seconds.
            inputState (InputState): Current input state.
        """
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
        
        actual_x, actual_y = self.get_actual_position()
        mouse_pos = inputState.mouse_pos
        mouse_pressed = inputState.mouse_buttons_pressed.left
        
        # Check for tab clicks
        if mouse_pressed:
            for i, tab in enumerate(self.tabs):
                tab_rect = self._get_tab_rect(i, actual_x, actual_y)
                
                # Check if mouse is over this tab
                if (tab_rect[0] <= mouse_pos[0] <= tab_rect[0] + tab_rect[2] and
                    tab_rect[1] <= mouse_pos[1] <= tab_rect[1] + tab_rect[3]):
                    
                    # Switch to this tab if not already active
                    if i != self.current_tab:
                        self.switch_tab(i)
                    break
        
        # Update the visible tab's frame
        if self.current_tab is not None:
            active_frame = self.tabs[self.current_tab]['frame']
            if hasattr(active_frame, 'update'):
                active_frame.update(dt, inputState)
    
    def render(self, renderer:OpenGLRenderer):
        """
        Render the tabination element with tabs and active content.
        
        Args:
            renderer (Renderer): Renderer object for drawing.
        """
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # 1. Draw main border (inherited from UiFrame)
        border_color = self.border_color or (theme.border if theme.border else None)
        if border_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                             border_color, fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
        
        # 2. Draw main background
        bg_color = self.background_color or theme.background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color, corner_radius=self.corner_radius)
        
        # 3. Draw tab headers area background
        tab_area_bg = tuple(min(255, c + 30) for c in bg_color) if bg_color else (240, 240, 240)
        renderer.draw_rect(actual_x, actual_y, self.width, self.tab_height, tab_area_bg, corner_radius=self.corner_radius)
        
        # 4. Draw tab headers
        for i, tab in enumerate(self.tabs):
            is_active = (i == self.current_tab)
            
            # Check if mouse is hovering over this tab
            tab_rect = self._get_tab_rect(i, actual_x, actual_y)
            mouse_pos = pygame.mouse.get_pos() if hasattr(pygame, 'mouse') else (0, 0)
            is_hovered = (tab_rect[0] <= mouse_pos[0] <= tab_rect[0] + tab_rect[2] and
                         tab_rect[1] <= mouse_pos[1] <= tab_rect[1] + tab_rect[3])
            
            # Get colors for this tab
            bg_color, text_color = self._get_tab_colors(i, is_active, is_hovered)
            # Draw tab border
            if is_active:
                # Active tab has border on top and sides
                renderer.draw_rect(tab_rect[0], tab_rect[1], tab_rect[2], tab_rect[3], 
                                 theme.border or (0, 0, 0), fill=False, border_width=self.border_width, corner_radius=self.corner_radius)
            else:
                # Inactive tabs have bottom border only
                renderer.draw_rect(tab_rect[0], tab_rect[1] + tab_rect[3] - 1, 
                                 tab_rect[2], 1, theme.border or (200, 200, 200), border_width=self.border_width, corner_radius=self.corner_radius)
            
            # Draw tab background
            renderer.draw_rect(tab_rect[0], tab_rect[1], tab_rect[2], tab_rect[3], bg_color, corner_radius=self.corner_radius)
            
            # Draw tab text
            text_surface = self.font.render(tab['name'], True, text_color)
            text_x = tab_rect[0] + (tab_rect[2] - text_surface.get_width()) // 2
            text_y = tab_rect[1] + (tab_rect[3] - text_surface.get_height()) // 2
            
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(text_surface, text_x, text_y)
            else:
                renderer.draw_surface(text_surface, text_x, text_y)
        
        # 5. Draw content separator line
        separator_y = actual_y + self.tab_height - 1
        separator_color = theme.border or (200, 200, 200)
        renderer.draw_rect(actual_x, separator_y, self.width, 1, separator_color)
        
        # 6. Draw active tab content
        if self.current_tab is not None:
            active_frame:UiFrame = self.tabs[self.current_tab]['frame']
            active_frame.render(renderer)
            
class Clock(UIElement):
    """
    A clock UI element that can display both analog and digital time.
    
    Supports both 12-hour and 24-hour formats, real-time or custom time,
    and various customization options.
    
    Attributes:
        diameter (int): Diameter of the analog clock face.
        use_real_time (bool): Whether to use the system's real time.
        show_numbers (bool): Whether to show numbers on the analog clock.
        time_style (str): '12hr' or '24hr' format.
        mode (str): 'analog', 'digital', or 'both'.
        custom_time (datetime): Custom time to display (if not using real time).
    """
    
    def __init__(self, x: int, y: int, diameter: int = 100, 
                 font_name: Optional[str] = None, font_size: int = 16,
                 use_real_time: bool = True, show_numbers: bool = True,
                 time_style: Literal['12hr', '24hr'] = '24hr',
                 mode: Literal['analog', 'digital', 'both'] = 'analog',
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        """
        Initialize a Clock element.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            diameter (int): Diameter of the analog clock face.
            font_name (Optional[str]): Font for digital display and numbers.
            font_size (int): Font size for digital display.
            use_real_time (bool): Whether to use system time.
            show_numbers (bool): Whether to show numbers on analog clock.
            time_style (str): '12hr' or '24hr' format.
            mode (str): 'analog', 'digital', or 'both'.
            root_point (Tuple[float, float]): Anchor point for positioning.
            theme (ThemeType): Theme for styling.
            element_id (Optional[str]): Custom element ID.
        """
        # Calculate width and height based on mode
        if mode == 'analog':
            width = height = diameter
        elif mode == 'digital':
            width = 120  # Default width for digital clock
            height = 40  # Default height for digital clock
        else:  # 'both'
            width = max(diameter, 120)
            height = diameter + 50  # Clock face + digital display
        
        super().__init__(x, y, width, height, root_point, element_id)
        
        # Clock properties
        self.diameter = diameter
        self.use_real_time = use_real_time
        self.show_numbers = show_numbers
        self.time_style = time_style
        self.mode = mode
        self.font_name = font_name
        self.font_size = font_size
        
        # Time properties
        self.custom_time = None
        self.current_time = time.time()
        self.last_update = 0
        
        # Styling
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.face_color = None
        self.border_color = None
        self.hour_hand_color = None
        self.minute_hand_color = None
        self.second_hand_color = None
        self.number_color = None
        self.digital_text_color = None
        
        # Font
        self._font = None
        self._small_font = None  # For numbers on analog clock
        
        # Update colors from theme
        self.update_theme(self.theme_type)
        
        # If not using real time, set to current time
        if not use_real_time:
            self.set_time(time.localtime())
    
    @property
    def font(self):
        """Get the main font object."""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    @property
    def small_font(self):
        """Get the smaller font for analog clock numbers."""
        if self._small_font is None:
            FontManager.initialize()
            self._small_font = FontManager.get_font(self.font_name, max(10, self.font_size - 4))
        return self._small_font
    
    def update_theme(self, theme_type: ThemeType):
        """Update theme colors for the clock."""
        super().update_theme(theme_type)
        theme = ThemeManager.get_theme(theme_type)
        
        # Set default colors from theme
        self.face_color = theme.background if hasattr(theme, 'background') else (240, 240, 240)
        self.border_color = theme.border if hasattr(theme, 'border') else (100, 100, 100)
        self.hour_hand_color = theme.button_pressed if hasattr(theme, 'button_pressed') else (0, 0, 0)
        self.minute_hand_color = theme.button_hover if hasattr(theme, 'button_hover') else (50, 50, 50)
        self.second_hand_color = theme.button_normal if hasattr(theme, 'button_normal') else (255, 0, 0)
        self.number_color = theme.text_primary if hasattr(theme, 'text_primary') else (0, 0, 0)
        self.digital_text_color = theme.text_primary if hasattr(theme, 'text_primary') else (0, 0, 0)
    
    def set_face_color(self, color: Tuple[int, int, int]):
        """Set the clock face color."""
        self.face_color = color
    
    def set_border_color(self, color: Tuple[int, int, int]):
        """Set the clock border color."""
        self.border_color = color
    
    def set_hand_colors(self, hour: Tuple[int, int, int], 
                        minute: Tuple[int, int, int], 
                        second: Tuple[int, int, int]):
        """Set the colors for clock hands."""
        self.hour_hand_color = hour
        self.minute_hand_color = minute
        self.second_hand_color = second
    
    def set_number_color(self, color: Tuple[int, int, int]):
        """Set the color for analog clock numbers."""
        self.number_color = color
    
    def set_digital_text_color(self, color: Tuple[int, int, int]):
        """Set the color for digital display text."""
        self.digital_text_color = color
    
    def set_time(self, time_struct: time.struct_time):
        """
        Set a custom time for the clock.
        
        Args:
            time_struct (time.struct_time): Time structure from time.localtime()
        """
        self.custom_time = time_struct
        self.current_time = time.mktime(time_struct)
    
    def set_time_from_string(self, time_str: str, format_str: str = "%H:%M:%S"):
        """
        Set time from a string.
        
        Args:
            time_str (str): Time string.
            format_str (str): Format string for parsing.
        """
        try:
            import datetime
            dt = datetime.datetime.strptime(time_str, format_str)
            self.set_time(dt.timetuple())
        except ValueError:
            print(f"Invalid time string: {time_str}")
    
    def get_time_string(self) -> str:
        """Get the current time as a formatted string."""
        if self.custom_time:
            tm = self.custom_time
        else:
            tm = time.localtime(self.current_time)
        
        if self.time_style == '12hr':
            # Convert to 12-hour format
            hour = tm.tm_hour % 12
            if hour == 0:
                hour = 12
            am_pm = "AM" if tm.tm_hour < 12 else "PM"
            return f"{hour:02d}:{tm.tm_min:02d}:{tm.tm_sec:02d} {am_pm}"
        else:
            # 24-hour format
            return f"{tm.tm_hour:02d}:{tm.tm_min:02d}:{tm.tm_sec:02d}"
    
    def update(self, dt: float, inputState: InputState):
        """Update the clock time."""
        super().update(dt, inputState)
        
        # Update time if using real time
        if self.use_real_time and not self.custom_time:
            current = time.time()
            # Only update if at least 0.1 seconds have passed (for performance)
            if current - self.last_update >= 0.1:
                self.current_time = current
                self.last_update = current
    
    def render(self, renderer: Renderer):
        """Render the clock."""
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        
        if self.mode in ['analog', 'both']:
            self._render_analog_clock(renderer, actual_x, actual_y)
        
        if self.mode in ['digital', 'both']:
            self._render_digital_clock(renderer, actual_x, actual_y)
        
        # Render children
        super().render(renderer)
    
    def _render_analog_clock(self, renderer: Renderer, x: int, y: int):
        """Render the analog clock face and hands."""
        # Calculate center and radius
        center_x = x + self.diameter // 2
        center_y = y + self.diameter // 2
        radius = self.diameter // 2
        
        # Draw clock face
        renderer.draw_circle(center_x, center_y, radius, self.face_color)
        
        # Draw border
        if self.border_color:
            renderer.draw_circle(center_x, center_y, radius, self.border_color, 
                               fill=False, border_width=2)
        
        # Draw numbers if enabled
        if self.show_numbers:
            self._draw_clock_numbers(renderer, center_x, center_y, radius)
        
        # Draw tick marks
        self._draw_tick_marks(renderer, center_x, center_y, radius)
        
        # Get current time
        if self.custom_time:
            tm = self.custom_time
        else:
            tm = time.localtime(self.current_time)
        
        # Calculate hand angles (in radians)
        # Convert to radians: 0 radians is at 3 o'clock, we want 0 at 12 o'clock
        # So subtract 90 degrees (π/2 radians)
        
        # Second hand: 6 degrees per second
        second_angle = math.radians(tm.tm_sec * 6 - 90)
        
        # Minute hand: 6 degrees per minute + 0.1 degrees per second
        minute_angle = math.radians(tm.tm_min * 6 + tm.tm_sec * 0.1 - 90)
        
        # Hour hand: 30 degrees per hour + 0.5 degrees per minute
        hour_angle = math.radians((tm.tm_hour % 12) * 30 + tm.tm_min * 0.5 - 90)
        
        # Draw hands
        self._draw_hand(renderer, center_x, center_y, hour_angle, 
                       radius * 0.5, 6, self.hour_hand_color)  # Hour hand
        self._draw_hand(renderer, center_x, center_y, minute_angle, 
                       radius * 0.7, 4, self.minute_hand_color)  # Minute hand
        self._draw_hand(renderer, center_x, center_y, second_angle, 
                       radius * 0.9, 2, self.second_hand_color)  # Second hand
        
        # Draw center dot
        renderer.draw_circle(center_x, center_y, 4, self.second_hand_color)
    
    def _draw_clock_numbers(self, renderer: Renderer, center_x: int, center_y: int, radius: int):
        """Draw numbers around the clock face."""
        for hour in range(1, 13):
            # Calculate angle for this hour (in radians)
            angle = math.radians(hour * 30 - 90)  # 30 degrees per hour, offset by -90
            
            # Calculate position (slightly inside the border)
            num_radius = radius * 0.8
            x = center_x + num_radius * math.cos(angle)
            y = center_y + num_radius * math.sin(angle)
            
            renderer.draw_text(str(hour), x, y, self.number_color, self.small_font, anchor_point=(0.5, 0.5))
    
    def _draw_tick_marks(self, renderer: Renderer, center_x: int, center_y: int, radius: int):
        """Draw tick marks for minutes/seconds."""
        for minute in range(0, 60):
            angle = math.radians(minute * 6 - 90)  # 6 degrees per minute
            
            # Calculate start and end points for tick mark
            outer_radius = radius * 0.95
            inner_radius = radius * 0.9 if minute % 5 == 0 else radius * 0.92
            
            x1 = center_x + inner_radius * math.cos(angle)
            y1 = center_y + inner_radius * math.sin(angle)
            x2 = center_x + outer_radius * math.cos(angle)
            y2 = center_y + outer_radius * math.sin(angle)
            
            # Draw thicker lines for 5-minute marks
            thickness = 2 if minute % 5 == 0 else 1
            color = self.number_color
            
            if hasattr(renderer, 'draw_line'):
                renderer.draw_line(int(x1), int(y1), int(x2), int(y2), color, thickness)
            else:
                # Fallback: draw a thin rectangle
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    # Calculate perpendicular vector for thickness
                    perp_x = -dy / length * thickness / 2
                    perp_y = dx / length * thickness / 2
                    
                    # Create polygon points
                    points = [
                        (x1 + perp_x, y1 + perp_y),
                        (x1 - perp_x, y1 - perp_y),
                        (x2 - perp_x, y2 - perp_y),
                        (x2 + perp_x, y2 + perp_y)
                    ]
                    
                    if hasattr(renderer, 'draw_polygon'):
                        renderer.draw_polygon(points, color)
    
    def _draw_hand(self, renderer: Renderer, center_x: int, center_y: int, 
                  angle: float, length: float, width: int, color: Tuple[int, int, int]):
        """Draw a clock hand."""
        # Calculate end point
        x = center_x + length * math.cos(angle)
        y = center_y + length * math.sin(angle)
        
        if hasattr(renderer, 'draw_line'):
            # Draw line from center to end point
            renderer.draw_line(center_x, center_y, int(x), int(y), color, width)
        else:
            # Draw as polygon for better quality
            # Calculate perpendicular vector for width
            dx = x - center_x
            dy = y - center_y
            hand_length = math.sqrt(dx*dx + dy*dy)
            
            if hand_length > 0:
                # Normalize direction vector
                dx /= hand_length
                dy /= hand_length
                
                # Calculate perpendicular vector
                perp_x = -dy * width / 2
                perp_y = dx * width / 2
                
                # Create polygon points
                points = [
                    (center_x + perp_x, center_y + perp_y),
                    (center_x - perp_x, center_y - perp_y),
                    (x - perp_x * 0.5, y - perp_y * 0.5),  # Taper the end
                    (x + perp_x * 0.5, y + perp_y * 0.5)
                ]
                
                if hasattr(renderer, 'draw_polygon'):
                    renderer.draw_polygon(points, color)
    
    def _render_digital_clock(self, renderer: Renderer, x: int, y: int):
        """Render the digital clock display."""
        time_str = self.get_time_string()
        
        if self.mode == 'digital':
            # Center in the element
            center_x = x + self.width // 2
            center_y = y + self.height // 2
            
            # Draw background
            renderer.draw_rect(x, y, self.width, self.height, self.face_color)
            
            # Draw border
            if self.border_color:
                renderer.draw_rect(x, y, self.width, self.height, 
                                 self.border_color, fill=False, border_width=1)
            
            # Draw time text
            renderer.draw_text(time_str, center_x, center_y, 
                             self.digital_text_color, self.font, 
                             anchor_point=(0.5, 0.5))
        
        elif self.mode == 'both':
            # Position below analog clock
            digital_y = y + self.diameter + 10
            digital_x = x + self.diameter // 2
            
            # Draw time text
            renderer.draw_text(time_str, digital_x, digital_y, 
                             self.digital_text_color, self.font, 
                             anchor_point=(0.5, 0))
        