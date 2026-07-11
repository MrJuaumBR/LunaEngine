"""
Base UI elements and core classes for LunaEngine UI system.

LOCATION: lunaengine/ui/elements/base.py

DESCRIPTION:
Defines the foundational UIElement class and supporting components:
- FontManager: central font loading and caching, now with atlas integration.
- UIState and ElementStyle: state handling and theming.
- UIElement: base class for all interactive UI components.

KEY FEATURES:
- Pygame font system initialization and caching.
- Support for system fonts and file fonts.
- Atlas-based font resolution (via engine's atlas).
- UI state machine (normal, hover, pressed, disabled).
- Theming with ThemeManager.
- Unique ID generation for each element.
- Hierarchical parent-child relationships.
- Mouse and controller input handling.
- Tooltip integration.

DEPENDENCIES:
- pygame: For font rendering and surface operations.
- ..themes: Theme management for colors and styles.
- ...core.renderer: OpenGL-based rendering backend.
- ...backend.types: Input state and layer types.
"""

import pygame
import os
import io
from typing import Optional, List, Tuple, Any, Dict, TYPE_CHECKING, Union
from enum import Enum
from abc import ABC

from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
from ...backend.types import InputState, ElementsList, LayerType, Color
from ...backend.opengl import OpenGLRenderer

if TYPE_CHECKING:
    from ..tooltips import Tooltip
    from ..core import LunaEngine, Scene


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
            if style.normal_color:
                style.border_color = tuple(max(0, c - 30) for c in style.normal_color)
        
        # Style properties from normal state (can be changed per-element later)
        style.alpha = ThemeManager.get_alpha('button_normal', theme_type)
        style.border_radius = ThemeManager.get_corner_radius('button_normal', theme_type)
        style.border_width = ThemeManager.get_border_width('button_normal', theme_type)
        style.blur = ThemeManager.get_blur('button_normal', theme_type)
        
        return style


class FontManager:
    """
    Manages fonts and ensures Pygame font system is initialized.
    Supports both system fonts (by name) and file fonts (by path).
    Caches fonts with style variants (bold/italic).
    Also supports resolving font names via the engine's Atlas resource catalog,
    and loading fonts from a bundled resource (using io.BytesIO).
    
    Usage:
        # Basic usage
        font = FontManager.get_font("Arial", 24)
        
        # Using an atlas-registered font
        FontManager.set_atlas(engine.atlas)
        font = FontManager.get_font("main_font", 24)  # looks up "main_font" in atlas
        
        # File font
        font = FontManager.get_font("path/to/font.ttf", 16)
    """
    
    _initialized = False
    _font_cache: Dict[Tuple[str, int, bool, bool], pygame.font.Font] = {}
    _atlas = None   # Atlas instance for font resolution
    
    @classmethod
    def initialize(cls):
        """Initialize the font system (call once before using fonts)."""
        if not cls._initialized:
            pygame.font.init()
            cls._initialized = True
    
    @classmethod
    def set_atlas(cls, atlas):
        """
        Set the Atlas instance to use for font resolution.
        
        Args:
            atlas: An Atlas instance (from ..misc.atlas) or None to disable.
        """
        cls._atlas = atlas
    
    @classmethod
    def get_font(cls, font_name: Optional[str] = None, font_size: int = 24,
                 bold: bool = False, italic: bool = False) -> pygame.font.Font:
        """
        Get a font object with the given name, size, and style.
        
        Resolution order:
        1. Check internal cache.
        2. If atlas is set and the name exists in atlas:
           a. If atlas is in bundle mode and has bytes for this font, load from bytes.
           b. Otherwise load from file path.
        3. If `font_name` exists as a file path, load it directly.
        4. Otherwise, treat as a system font name (or None for default).
        
        Args:
            font_name (Optional[str]): 
                - If None, uses the default system font.
                - If it's a path to a font file (e.g., "path/to/font.ttf"), loads it.
                - Otherwise, treats it as a system font name (e.g., "Arial", "Times New Roman").
            font_size (int): Size of the font in pixels.
            bold (bool): Whether the font should be bold.
            italic (bool): Whether the font should be italic.
            
        Returns:
            pygame.font.Font: A font object ready for text rendering.
        """
        if not cls._initialized:
            cls.initialize()
            
        from ...storage.atlas import AtlasCategory
        
        name_key = font_name if font_name is not None else None
        font_size = int(font_size)
        cache_key = (name_key, font_size, bold, italic)
        if cache_key in cls._font_cache:
            return cls._font_cache[cache_key]
        
        # --- Try atlas resolution (both bundle and file) ---
        if cls._atlas is not None and font_name is not None:
            item = cls._atlas.get_item(font_name)
            if item and item.category == AtlasCategory.FONT:
                # Attempt to get bytes from bundle
                data = cls._atlas.get_bytes(font_name)
                if data is not None:
                    try:
                        font = pygame.font.Font(io.BytesIO(data), font_size)
                        cls._font_cache[cache_key] = font
                        return font
                    except Exception as e:
                        print(f"Error loading font from bundle: {e}")
                # Fallback to file path
                font_path = str(item.path)
                if os.path.exists(font_path):
                    try:
                        font = pygame.font.Font(font_path, font_size)
                        cls._font_cache[cache_key] = font
                        return font
                    except Exception:
                        pass  # fall through to system font
        
        # --- Fallback to direct file path ---
        if font_name is not None and os.path.exists(font_name):
            try:
                font = pygame.font.Font(font_name, font_size)
                cls._font_cache[cache_key] = font
                return font
            except Exception:
                # fallback to default
                font = pygame.font.SysFont(None, font_size, bold=bold, italic=italic)
                cls._font_cache[cache_key] = font
                return font
        else:
            # System font name or None
            font = pygame.font.SysFont(font_name, font_size, bold=bold, italic=italic)
            cls._font_cache[cache_key] = font
            return font

    @classmethod
    def get_system_fonts(cls) -> List[str]:
        """Return a list of available system font names."""
        return pygame.font.get_fonts()


class UIElement(ABC):
    """
    Base class for all UI elements providing common functionality.
    
    Attributes:
        element_id (str): Unique identifier for this element in format ui_{type}_{counter}
        x (int): X coordinate position
        y (int): Y coordinate position
        width (int): Width of the element in pixels
        height (int): Height of the element in pixels
        pivot (Tuple[float, float]): Anchor point for positioning
        state (UIState): Current state of the element
        visible (bool): Whether element is visible
        enabled (bool): Whether element is enabled
        children (List[UIElement]): Child elements
        parent (UIElement): Parent element
        can_focus (bool): Whether this element can receive controller focus (override in subclasses)
    """
    _global_engine: 'LunaEngine' = None
    _properties: Dict[str, Dict[str, Any]] = {
        'x': {'name': 'x position', 'key': 'x', 'type': int, 'editable': True, 'description': 'X coordinate position of the element', 'range': (0, '<SCREEN_WIDTH>')},
        'y': {'name': 'y position', 'key': 'y', 'type': int, 'editable': True, 'description': 'Y coordinate position of the element', 'range': (0, '<SCREEN_HEIGHT>')},
        'width': {'name': 'width', 'key': 'width', 'type': int, 'editable': True, 'description': 'Width of the element in pixels', 'range': (0, '<SCREEN_WIDTH>')},
        'height': {'name': 'height', 'key': 'height', 'type': int, 'editable': True, 'description': 'Height of the element in pixels', 'range': (0, '<SCREEN_HEIGHT>')},
        'style': {'name': 'style', 'key': 'style', 'type': ElementStyle, 'editable': False, 'description': 'Style properties for the element'},
        'visible': {'name': 'visible', 'key': 'visible', 'type': bool, 'editable': True, 'description': 'Whether the element is visible'},
        'enabled': {'name': 'enabled', 'key': 'enabled', 'type': bool, 'editable': True, 'description': 'Whether the element is enabled for interaction'},
        'pivot': {'name': 'root point', 'key': 'pivot', 'type': Tuple[float, float], 'editable': True, 'description': 'Anchor point for positioning where (0,0) is top-left and (1,1) is bottom-right'},
        'selection_order': {'name': 'selection order', 'key': 'selection_order', 'type': int, 'editable': True, 'description': 'Order for controller focus navigation (lower = earlier)'},
    }
    category: str = 'None'
    
    def __init__(self, x: int, y: int, width: int, height: int, pivot: Tuple[float, float] = (0, 0),
                 element_id: Optional[str] = None):
        """
        Initialize a UI element with position and dimensions.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            width (int): Width of the element in pixels.
            height (int): Height of the element in pixels.
            pivot (Tuple[float, float]): Anchor point for positioning where (0,0) is top-left 
                                            and (1,1) is bottom-right.
            element_id (Optional[str]): Custom element ID. If None, generates automatic ID.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.pivot = pivot
        self.state = UIState.NORMAL
        self.visible: bool = True
        self.enabled: bool = True
        self.scene: 'Scene' = None
        self.children: ElementsList = ElementsList()
        self.parent: 'UIElement' | None = None
        self.z_index: int = 0  # For rendering order
        self.render_layer: LayerType = LayerType.NORMAL
        self.always_on_top: bool = False
        self.groups: List[str] = []
        self.style: ElementStyle = ElementStyle().loadFromTheme(ThemeManager.get_current_theme())
        self.corner_radius = self.style.border_radius
        self.border_width: int = self.style.border_width
        self.selection_order: int = 0   # for controller focus navigation
        
        # Generate unique ID using element type name
        self.element_type = self.__class__.__name__.lower()
        self.element_id = element_id if element_id else _uid_generator.generate_id(self.element_type)
        
    # ---- NEW: property for controller focus ----
    @property
    def can_focus(self) -> bool:
        """Override in subclasses that should be focusable (buttons, inputs, etc.)."""
        return False

    def is_globally_visible(self) -> bool:
        """
        Return True if this element and all its ancestors are visible.
        This is used to skip elements inside hidden containers (e.g., inactive tabs).
        """
        if not self.visible:
            return False
        if self.parent:
            return self.parent.is_globally_visible()
        return True

    def add_to_parent(self, parent: 'UIElement', extra: Any = None) -> None:
        """Add this element to a parent, optionally with extra data (e.g., tab name)."""
        from .containers import Tabination
        if isinstance(parent, Tabination) and extra and type(extra) is str:
            parent.add_to_tab(extra, self)
        else:
            parent.add_child(self)
        
    def getIndexedChilds(self) -> int:
        """Return the total number of descendants (including nested)."""
        n = len(self.children)
        for child in self.children:
            n += child.getIndexedChilds()
        return n

    def set_enabled(self, enabled: bool):
        """Enable or disable this element."""
        self.enabled = enabled
        
    def get_engine(self) -> 'LunaEngine':
        """Return the global engine instance."""
        return self._global_engine
    
    def set_corner_radius(self, radius: int | Tuple[int, int, int, int]):
        """Set the corner radius (can be a single int or tuple for each corner)."""
        self.corner_radius = radius
    
    @property
    def group(self) -> str:
        return ''.join(self.groups)
    
    def add_group(self, group: str):
        """Add this element to a named group."""
        if group not in self.groups:
            self.groups.append(str(group).lower())
            
    def remove_group(self, group: str):
        """Remove this element from a named group."""
        if group in self.groups:
            self.groups.remove(str(group).lower())
    
    def clear_groups(self):
        """Remove all group associations."""
        self.groups = []
        
    def has_group(self, group: str) -> bool:
        """Check if this element belongs to a given group."""
        return str(group).lower() in self.groups
    
    def __str__(self) -> str:
        return f'{str(self.element_type)}-{self.element_id}'
    
    def __repr__(self) -> str:
        return f'{str(self.element_type)}-{self.element_id}'
          
    @property
    def type(self) -> str:
        return self.element_type
            
    def get_id(self) -> str:
        """Get the unique ID of this UI element."""
        return self.element_id
        
    def set_id(self, new_id: str) -> None:
        """Set a new unique ID for this UI element."""
        self.element_id = new_id
        
    def get_scroll_offset(self, is_for_scroll_event: Optional[bool] = False) -> Union[Tuple[int, int], Tuple[float, float]]:
        """
        Get the accumulated scroll offset from this element and its ancestors.
        If is_for_scroll_event is True, scroll offsets are not applied (for hit testing).
        """
        x, y = 0, 0
        if hasattr(self, 'scroll_x') and not is_for_scroll_event:
            x = getattr(self, 'scroll_x')
        if hasattr(self, 'scroll_y') and not is_for_scroll_event:
            y = getattr(self, 'scroll_y')
            
        if self.parent:
            (px, py) = self.parent.get_scroll_offset()
            x += px
            y += py
            
        return (x, y)
                
    def get_actual_position(self, x: Union[int, float, None] = None,
                            y: Union[int, float, None] = None) -> Union[Tuple[int, int], Tuple[float, float]]:
        """
        Get the absolute screen position of this element, considering parent and pivot.
        """
        anchor_x, anchor_y = self.pivot
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        x = x - int(self.width * anchor_x)
        y = y - int(self.height * anchor_y)

        if self.parent:
            parent_x, parent_y = self.parent.get_actual_position()
            x = parent_x + x
            y = parent_y + y

        return (x, y)
    
    def mouse_over(self, input_state: InputState | Tuple[int, int], rect: pygame.Rect | pygame.Rect | None = None, 
                   is_for_scroll_event: Optional[bool] = False) -> bool:
        """
        Check if the mouse is over this element.
        
        Args:
            input_state: The current input state or mouse position tuple.
            rect: Optional custom rectangle to use for collision (otherwise uses the element's rect).
            is_for_scroll_event: If True, ignores scroll offsets.
        """
        if rect is None:
            rect = self.getCollideRect(is_for_scroll_event=is_for_scroll_event)
            
        if type(rect) is tuple or type(rect) is list:
            rect = pygame.Rect(rect[0], rect[1], rect[2], rect[3])
            
        if isinstance(input_state, InputState):
            mouse_pos: Tuple[int, int] = self.get_mouse_position(input_state)
        else:
            mouse_pos: Tuple[int, int] = input_state
        
        return rect.collidepoint(mouse_pos)

    def get_mouse_position(self, input_state: InputState | Tuple[int, int]) -> Tuple[int, int]:
        """Get the raw mouse position from the input state or tuple."""
        if isinstance(input_state, InputState):
            return input_state.mouse_pos
        elif isinstance(input_state, tuple):
            return input_state
        return (0, 0)
    
    def getCollideRect(self, rect: pygame.Rect | None = None, is_for_scroll_event: Optional[bool] = False) -> pygame.Rect:
        """
        Get the collision rectangle for this element, considering parent and scroll offsets.
        """
        offset_x, offset_y = None, None
        if self.parent:
            if self.parent.category == 'container':
                if self.parent.auto_arrange_y:
                    offset_x, offset_y = self.parent.get_arranged_position(self)
                
        scroll_offset = self.get_scroll_offset(is_for_scroll_event=is_for_scroll_event)
        x, y = self.get_actual_position(offset_x, offset_y)
        x -= scroll_offset[0]
        y -= scroll_offset[1]
        w, h = self.width, self.height
                    
        if rect and isinstance(rect, pygame.Rect):
            x += rect.x
            y += rect.y
            w = rect.width
            h = rect.height
        return pygame.Rect(x, y, w, h)
        
    def add_child(self, child):
        """Add a child element to this UI element."""
        child.parent = self
        self.children.append(child)
        
    def remove_child(self, child: 'UIElement'):
        """Remove a child element from this UI element."""
        self.children.remove(child)
        child.parent = None

    def set_tooltip(self, tooltip: 'Tooltip'):
        """
        Set tooltip for this element using a Tooltip instance.
        
        Args:
            tooltip (Tooltip): Tooltip instance to associate with this element
        """
        from ..tooltips import UITooltipManager
        UITooltipManager.register_tooltip(self, tooltip)
    
    def set_simple_tooltip(self, text: str, **kwargs):
        """
        Quick method to set a simple tooltip with text.
        
        Args:
            text (str): Tooltip text
            **kwargs: Additional arguments for TooltipConfig
        """
        from ..tooltips import Tooltip, TooltipConfig
        
        config = TooltipConfig(text=text, **kwargs)
        tooltip = Tooltip(config)
        self.set_tooltip(tooltip)
    
    def remove_tooltip(self):
        """Remove tooltip from this element."""
        from ..tooltips import UITooltipManager
        UITooltipManager.unregister_tooltip(self)
    
    def update(self, dt: float, inputState: InputState):
        """
        Update element state based on mouse interaction and input.
        
        Args:
            dt (float): Delta time in seconds since last update.
            inputState (InputState): Current input state.
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
                inputState.consume_event(self.element_id)
                self.on_click()
            elif inputState.mouse_buttons_pressed.left and self.state == UIState.PRESSED:
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
    
    def render(self, renderer: Renderer | OpenGLRenderer):
        """
        Render this element using OpenGL backend.  
        Override this in subclasses for OpenGL-specific rendering.
        """
        for child in self._global_engine.layer_manager.get_elements_in_order_from(self.children):
            if hasattr(child, 'render'):
                child.render(renderer)
    
    def kill(self):
        """
        Remove this element from the scene.
        """
        if self.parent:
            self.parent.remove_child(self)
        self.scene.remove_ui_element(self)
    
    def _get_init_args(self) -> Dict[str, Any]:
        """
        Return a dictionary of arguments to pass to the constructor when restarting.
        Subclasses can override this to include additional parameters (e.g., options, label, etc.).
        """
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'pivot': self.pivot,
            'element_id': self.element_id,
        }

    def restart(self) -> Optional['UIElement']:
        """
        Recreate the element with its current properties and replace it in the scene.
        This is useful after modifying properties that require a full rebuild
        (e.g., changing max_visible_options in a Dropdown).
        
        Returns:
            The newly created element, or None if the operation failed.
        """
        parent = self.parent
        scene = self.scene
        if not scene:
            return None

        new_elem = self.__class__(**self._get_init_args())

        new_elem.visible = self.visible
        new_elem.enabled = self.enabled
        new_elem.z_index = self.z_index
        new_elem.render_layer = self.render_layer
        new_elem.always_on_top = self.always_on_top
        new_elem.groups = self.groups.copy()
        new_elem.corner_radius = self.corner_radius
        new_elem.border_width = self.border_width
        if hasattr(self, 'theme_type'):
            new_elem.theme_type = self.theme_type
        new_elem.state = self.state
        new_elem.style = self.style

        if parent:
            parent.add_child(new_elem)
        else:
            scene.add_ui_element(new_elem)

        self.kill()
        return new_elem
    
    def on_click(self):
        """Called when element is clicked by the user."""
        pass
        
    def on_hover(self):
        """Called when mouse hovers over the element."""
        pass
    
    def on_activate(self) -> None:
        """
        Called when the element is "activated" (e.g., via controller A button or Enter key).
        Override in subclasses to perform actions like toggling, selecting, etc.
        """
        pass

    def on_directional_input(self, direction: str) -> bool:
        """
        Handle directional input (up/down/left/right) when this element is focused.
        Return True if the input was consumed (so focus won't move to another element).
        """
        return False