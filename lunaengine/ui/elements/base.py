import pygame, time, math, os
import numpy as np
from typing import Optional, Callable, List, Tuple, Any, Dict, Literal, TYPE_CHECKING
from enum import Enum
from abc import ABC
from ..themes import ThemeManager, ThemeType, ThemeStyle
from ...core.renderer import Renderer
from ...backend.types import InputState, ElementsList, LayerType, Color
from ...backend.opengl import OpenGLRenderer

if TYPE_CHECKING:
    from ..tooltips import Tooltip, TooltipConfig, UITooltipManager
    
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

class ElementStyle:
    """Class representing style properties for UI elements."""
    normal_color: Optional[Tuple[int, int, int]] = None
    hovered_color: Optional[Tuple[int, int, int]] = None
    pressed_color: Optional[Tuple[int, int, int]] = None
    disabled_color: Optional[Tuple[int, int, int]] = None
    
    text_color: Optional[Tuple[int, int, int]] = None
    border_color: Optional[Tuple[int, int, int]] = None
    
    # New extended style properties
    alpha: float = 1.0
    border_radius: int = 0
    border_width: int = 0
    blur: int = 0
    
    @staticmethod
    def loadFromTheme(theme_type: ThemeType) -> 'ElementStyle':
        """
        Load complete element style from the theme system.
        Uses button_* properties as base, but can be overridden for specific elements.
        """
        style = ElementStyle()
        
        # Colors (RGB only – alpha handled separately if needed)
        style.normal_color = ThemeManager.get_color('button_normal', theme_type)
        style.hovered_color = ThemeManager.get_color('button_hover', theme_type)
        style.pressed_color = ThemeManager.get_color('button_pressed', theme_type)
        style.disabled_color = ThemeManager.get_color('button_disabled', theme_type)
        style.text_color = ThemeManager.get_color('button_text', theme_type)
        
        border_color = ThemeManager.get_color('button_border', theme_type)
        if border_color != (0, 0, 0):
            style.border_color = border_color
        else:
            # fallback to using a darker version of normal color
            if style.normal_color:
                style.border_color = tuple(max(0, c - 30) for c in style.normal_color)
        
        # Style properties from normal state (can be changed per-element later)
        style.alpha = ThemeManager.get_alpha('button_normal', theme_type)
        style.border_radius = ThemeManager.get_corner_radius('button_normal', theme_type)
        style.border_width = ThemeManager.get_border_width('button_normal', theme_type)
        style.blur = ThemeManager.get_blur('button_normal', theme_type)
        
        return style

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
    _properties:Dict[str, Dict[str, Any]] = {
        'x':{'name':'x position', 'key':'x', 'type':int, 'editable':True, 'description':'X coordinate position of the element'},
        'y':{'name':'y position', 'key':'y', 'type':int, 'editable':True, 'description':'Y coordinate position of the element'},
        'width':{'name':'width', 'key':'width', 'type':int, 'editable':True, 'description':'Width of the element in pixels'},
        'height':{'name':'height', 'key':'height', 'type':int, 'editable':True, 'description':'Height of the element in pixels'},
        'style':{'name':'style', 'key':'style', 'type':ElementStyle, 'editable':True, 'description':'Style properties for the element'},
        'visible':{'name':'visible', 'key':'visible', 'type':bool, 'editable':True, 'description':'Whether the element is visible'},
        'enabled':{'name':'enabled', 'key':'enabled', 'type':bool, 'editable':True, 'description':'Whether the element is enabled for interaction'},
        'root_point':{'name':'root point', 'key':'root_point', 'type':Tuple[float, float], 'editable':True, 'description':'Anchor point for positioning where (0,0) is top-left and (1,1) is bottom-right'},
    } # Will receive some properties that can be shown on Live Inspector(New Feature coming soon)
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
        self.style:ElementStyle = ElementStyle().loadFromTheme(ThemeManager.get_current_theme())
        self.corner_radius = self.style.border_radius
        self.border_width:int = self.style.border_width
        
        # Generate unique ID using element type name
        self.element_type = self.__class__.__name__.lower()
        self.element_id = element_id if element_id else _uid_generator.generate_id(self.element_type)
        
    def add_to_parent(self, parent: 'UIElement', extra:Any=None) -> None:
        from .containers import Tabination
        if isinstance(parent, Tabination) and extra and type(extra) == str:
            parent.add_to_tab(extra, self)
        else:
            parent.add_child(self)
        
    def getIndexedChilds(self) -> int:
        n = len(self.children)
        for child in self.children:
            n += child.getIndexedChilds()
        return n

    def get_mouse_position(self, input_state:InputState) -> Tuple[int, int]:
        return input_state.mouse_pos
    
    def getCollideRect(self) -> pygame.Rect:
        if self.parent:
            self.parent_rect = self.parent.getCollideRect()
            x = self.parent_rect.x + self.x - int(self.width * self.root_point[0])
            y = self.parent_rect.y + self.y - int(self.height * self.root_point[1])
        else:
            x = self.x - int(self.width * self.root_point[0])
            y = self.y - int(self.height * self.root_point[1])
        return pygame.Rect(x, y, self.width, self.height)
    
    def mouse_over(self, input_state:InputState|Tuple) -> bool:
        if type(input_state) == InputState:
            mouse_pos = self.get_mouse_position(input_state)
        elif type(input_state) == tuple:
            mouse_pos = input_state
        is_mouse_over:bool = self.getCollideRect().collidepoint(mouse_pos)
        
        return is_mouse_over

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        
    def get_engine(self) -> 'LunaEngine':
        return self._global_engine
    
    def set_corner_radius(self, radius: int|Tuple[int, int, int, int]):
        self.corner_radius = radius
    
    @property
    def group(self) -> str:
        return ''.join(self.groups)
    
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
    
    def __repr__(self) -> str:
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
        
    def get_actual_position(self, x:int|float=None, y:int|float=None) -> Tuple[int, int]:
        """
        Calculate actual screen position based on root_point anchor.
        
        Args:
            parent_width (int): Width of parent element if applicable.
            parent_height (int): Height of parent element if applicable.
            
        Returns:
            Tuple[int, int]: The actual (x, y) screen coordinates.
        """
        anchor_x, anchor_y = self.root_point
        if not type(x) in [int, float] or x is None:
            x = self.x
        if not type(y) in [int, float] or y is None:
            y = self.y
        
        
        if self.parent:
            parent_x, parent_y = self.parent.get_actual_position()
            actual_x = parent_x + x - int(self.width * anchor_x)
            actual_y = parent_y + y - int(self.height * anchor_y)
        else:
            actual_x = x - int(self.width * anchor_x)
            actual_y = y - int(self.height * anchor_y)
            
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
        from ..tooltips import UITooltipManager
        UITooltipManager.register_tooltip(self, tooltip)
    
    def set_simple_tooltip(self, text: str, **kwargs):
        """
        Quick method to set a simple tooltip with text.
        
        Args:
            text (str): Tooltip text
            **kwargs: Additional arguments for TooltipConfig
        """
        # Import here to avoid circular imports
        from ..tooltips import Tooltip, TooltipConfig
        
        config = TooltipConfig(text=text, **kwargs)
        tooltip = Tooltip(config)
        self.set_tooltip(tooltip)
    
    def remove_tooltip(self):
        """Remove tooltip from this element."""
        # Import here to avoid circular imports
        from ..tooltips import UITooltipManager
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
        # If a global mouse event has been consumed this frame, skip all mouse logic.
        if inputState.is_global_mouse_consumed():
            self.state = UIState.NORMAL
            for child in self.children:
                child.update(dt, inputState)
            return
            
        # Check if event was already consumed by another element
        if inputState.is_event_consumed(self.element_id):
            self.state = UIState.NORMAL
            return
        
        if self.mouse_over(inputState):
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
                child.update(dt, inputState)
    
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
