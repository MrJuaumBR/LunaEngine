"""
lunaengine/backend/types.py

A collection of types used in lunaengine
"""

import pygame.locals
from dataclasses import dataclass, field
from typing import Callable, Optional, Literal, Tuple, Dict, Any, List, Union
from numbers import Number
from enum import Enum
import random

class EVENTS:
    QUIT = pygame.QUIT
    KEYDOWN = pygame.KEYDOWN
    KEYUP = pygame.KEYUP
    MOUSEWHEEL = pygame.MOUSEWHEEL
    MOUSEMOTION = pygame.MOUSEMOTION
    MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
    MOUSEBUTTONUP = pygame.MOUSEBUTTONUP
    JOYAXISMOTION = pygame.JOYAXISMOTION
    VIDEORESIZE = pygame.VIDEORESIZE
    WINDOWFOCUSGAINED = pygame.WINDOWFOCUSGAINED
    WINDOWFOCUSLOST = pygame.WINDOWFOCUSLOST
    ACTIVEEVENT = pygame.ACTIVEEVENT
    
@dataclass
class MouseButtonPressed(dict):
    left:bool = False
    middle:bool = False
    right:bool = False
    extra_button_1:bool = False
    extra_button_2:bool = False

@dataclass
class InputState:
    """
    Tracks input state with proper click detection
    """
    mouse_pos: tuple = (0, 0)
    mouse_buttons_pressed: MouseButtonPressed = None
    mouse_just_pressed: bool = False
    mouse_just_released: bool = False
    mouse_wheel: float = 0
    consumed_events: set = None
    
    # Controller-related
    active_controller: Optional['Controller'] = None
    controller_count: int = 0
    using_controller: bool = False
    
    def __post_init__(self):
        self._prev_mouse_buttons = MouseButtonPressed()
        self._global_mouse_consumed = False
        
        if self.mouse_buttons_pressed is None:
            self.mouse_buttons_pressed = MouseButtonPressed()
            
        if self.consumed_events is None:
            self.consumed_events = set()
            
    
    def consume_global_mouse(self):
        """Mark that a mouse event has been handled globally."""
        self._global_mouse_consumed = True

    def is_global_mouse_consumed(self):
        """Check if any element has consumed the current mouse event."""
        return self._global_mouse_consumed
    
    def update(self, mouse_pos, mouse_pressed, mouse_wheel=0):
        # Store previous state
        self._prev_mouse_buttons.left = self.mouse_buttons_pressed.left
        self._prev_mouse_buttons.middle = self.mouse_buttons_pressed.middle
        self._prev_mouse_buttons.right = self.mouse_buttons_pressed.right

        # Update current
        self.mouse_buttons_pressed.left = mouse_pressed[0]
        self.mouse_buttons_pressed.middle = mouse_pressed[1]
        self.mouse_buttons_pressed.right = mouse_pressed[2]
        self.mouse_buttons_pressed.extra_button_1 = mouse_pressed[3] if len(mouse_pressed) > 3 else False
        self.mouse_buttons_pressed.extra_button_2 = mouse_pressed[4] if len(mouse_pressed) > 4 else False
        self.mouse_pos = mouse_pos

        # Compute just_pressed (any button that wasn't pressed before)
        self.mouse_just_pressed = (self.mouse_buttons_pressed.left and not self._prev_mouse_buttons.left) or \
                                (self.mouse_buttons_pressed.middle and not self._prev_mouse_buttons.middle) or \
                                (self.mouse_buttons_pressed.right and not self._prev_mouse_buttons.right)

        self.mouse_just_released = (not self.mouse_buttons_pressed.left and self._prev_mouse_buttons.left) or \
                                (not self.mouse_buttons_pressed.middle and self._prev_mouse_buttons.middle) or \
                                (not self.mouse_buttons_pressed.right and self._prev_mouse_buttons.right)

        
        if mouse_wheel != 0:
            self.mouse_wheel += mouse_wheel
            
        if self.mouse_wheel != 0:
            self.mouse_wheel *= 0.6
        
    def consume_event(self, element_id):
        """Mark an event as consumed by a specific element"""
        self.consumed_events.add(element_id)
    
    def is_event_consumed(self, element_id):
        """Check if event was already consumed"""
        return element_id in self.consumed_events
    
    def clear_consumed(self):
        """Clear consumed events for new frame"""
        self._global_mouse_consumed = False
        self.consumed_events.clear()
        
    def get_mouse_state(self) -> Tuple[Tuple[int, int], MouseButtonPressed]:
        return self.mouse_pos, self.mouse_buttons_pressed

ElementsListEvents = Literal['append', 'insert', 'extend', 'remove', 'pop']

class ElementsList(list['UiElement']):
    def __init__(self, *args, on_change:Callable[[ElementsListEvents, any, Optional[int]], None]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_element:'UiElement' = None
        self.on_change = on_change
        
    def set_on_change(self, on_change:Callable[[ElementsListEvents, any, Optional[int]], None], parent_element:'UiElement' = None):
        self.parent_element = parent_element
        self.on_change = on_change
        if self.parent_element:
            for child in self.parent_element.children:
                child.children.set_on_change(on_change, child)
        
    def append(self, item):
        super().append(item)
        if self.on_change:
            self.on_change('append', item)
    
    def insert(self, index, item):
        super().insert(index, item)
        if self.on_change:
            self.on_change('insert', item, index)
    
    def extend(self, iterable):
        super().extend(iterable)
        if self.on_change:
            self.on_change('extend', iterable)
    
    def remove(self, item):
        super().remove(item)
        if self.on_change:
            self.on_change('remove', item)
    
    def pop(self, index=-1):
        item = super().pop(index)
        if self.on_change:
            self.on_change('pop', item, index)
        return item

class LayerType(Enum):
    """Enumeration of UI render layers."""
    BACKGROUND = 0      # Background elements
    NORMAL = 1         # Regular UI elements
    ABOVE_NORMAL = 2   # Elements that should appear above regular ones
    POPUP = 3          # Dropdowns, tooltips, context menus
    MODAL = 4          # Modal dialogs, alerts
    TOP = 5            # Always on top elements (cursors, debug info)
    
class WindowEventType(Enum):
    """Types of window events supported."""
    FOCUS_GAINED = "window_focus_gained"
    FOCUS_LOST = "window_focus_lost"
    RESIZED = "window_resized"
    MOVED = "window_moved"
    ENTER = "window_enter"
    LEAVE = "window_leave"
    CLOSE = "window_close"
    MINIMIZED = "window_minimized"
    RESTORED = "window_restored"
    MAXIMIZED = "window_maximized"
    SHOWN = "window_shown"
    HIDDEN = "window_hidden"
    EXPOSED = "window_exposed"

@dataclass
class WindowEventData:
    """Data container for window events."""
    event_type: WindowEventType
    timestamp: int
    window_id: int
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def size(self) -> Optional[Tuple[int, int]]:
        """Get window size from resize event."""
        if 'size' in self.data:
            return self.data['size']
        return None
    
    @property
    def position(self) -> Optional[Tuple[int, int]]:
        """Get window position from move event."""
        if 'position' in self.data:
            return self.data['position']
        return None
    
class Ratio(tuple):
    """Represents a width/height ratio (x, y). Supports arithmetic and scaling."""

    def __new__(cls, x: Union[Number, Tuple[Number, Number]], y: Number = None):
        if y is None:
            # assume x is a tuple or pair
            x, y = x
        return super().__new__(cls, (float(x), float(y)))

    @property
    def width(self) -> float:
        return self[0]

    @property
    def height(self) -> float:
        return self[1]

    x = width
    y = height

    @property
    def med(self) -> float:
        return (self.width + self.height) / 2

    def scale(self, factor: float) -> 'Ratio':
        """Return a new Ratio multiplied by factor."""
        return Ratio(self.width * factor, self.height * factor)

    def clamp(self, min_ratio: 'Ratio' = None, max_ratio: 'Ratio' = None) -> 'Ratio':
        """Clamp each component between min and max (if provided)."""
        w, h = self.width, self.height
        if min_ratio:
            w = max(min_ratio.width, w)
            h = max(min_ratio.height, h)
        if max_ratio:
            w = min(max_ratio.width, w)
            h = min(max_ratio.height, h)
        return Ratio(w, h)

    def as_int(self) -> Tuple[int, int]:
        return (int(self.width), int(self.height))

    # Arithmetic operators
    def __add__(self, other: Union[Number, Tuple, 'Ratio']) -> 'Ratio':
        if isinstance(other, (int, float)):
            return Ratio(self.width + other, self.height + other)
        return Ratio(self.width + other[0], self.height + other[1])

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            return Ratio(self.width - other, self.height - other)
        return Ratio(self.width - other[0], self.height - other[1])

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Ratio(self.width * other, self.height * other)
        return Ratio(self.width * other[0], self.height * other[1])

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return Ratio(self.width / other, self.height / other)
        return Ratio(self.width / other[0], self.height / other[1])

    # Reverse operators
    def __radd__(self, other): return self.__add__(other)
    def __rmul__(self, other): return self.__mul__(other)

    def __repr__(self):
        return f"Ratio({self.width}, {self.height})"
    
@dataclass
class Color:
    r:int
    g:int
    b:int
    a:float
    
    def __init__(self, r:int, g:int, b:int, a:float = 1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
        self.validate()
        
    def random(self) -> 'Color':
        return Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
    def __repr__(self):
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"
    
    def __str__(self):
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"
    
    def __add__(self, other: 'Color'|Tuple[int, int, int, float]) -> 'Color':
        if isinstance(other, tuple):
            other = Color(*other)
        return Color(self.r + other.r, self.g + other.g, self.b + other.b, self.a + other.a)
    
    def __sub__(self, other: 'Color'|Tuple[int, int, int, float]) -> 'Color':
        if isinstance(other, tuple):
            other = Color(*other)
        return Color(self.r - other.r, self.g - other.g, self.b - other.b, self.a - other.a)
        
    def __mul__(self, other: 'Color'|Tuple[int, int, int, float]) -> 'Color':
        if isinstance(other, tuple):
            other = Color(*other)
        return Color(self.r * other.r, self.g * other.g, self.b * other.b, self.a * other.a)
    
    def __mod__(self, other: 'Color'|Tuple[int, int, int, float]) -> 'Color':
        if isinstance(other, tuple):
            other = Color(*other)
        return Color(self.r % other.r, self.g % other.g, self.b % other.b, self.a % other.a)
    
    def __truediv__(self, other: 'Color'|Tuple[int, int, int, float]) -> 'Color':
        if isinstance(other, tuple):
            other = Color(*other)
        return Color(self.r / other.r, self.g / other.g, self.b / other.b, self.a / other.a)
    
    @classmethod
    def from_rgb(cls, r: int, g: int, b: int, a: float = 1.0) -> 'Color':
        """Create a Color from RGB 0-255 values."""
        return cls(r, g, b, a)

    @classmethod
    def from_hex(cls, hex_str: str, a: float = 1.0) -> Optional['Color']:
        """Create a Color from a hex string like '#FF0000' or 'FF0000'."""
        hex_str = hex_str.lstrip('#').upper()
        if len(hex_str) != 6:
            return None
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return cls(r, g, b, a)
        except ValueError:
            return None

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float, a: float = 1.0) -> 'Color':
        """Create a Color from HSV (h:0-360, s:0-1, v:0-1)."""
        r, g, b = hsv_to_rgb(h, s, v)   # using existing conversion function
        return cls(r, g, b, a)

    @classmethod
    def from_hsl(cls, h: float, s: float, l: float, a: float = 1.0) -> 'Color':
        """Create a Color from HSL (h:0-360, s:0-1, l:0-1)."""
        r, g, b = hsl_to_rgb(h, s, l)   # using existing conversion function
        return cls(r, g, b, a)

    def to_rgb_tuple(self) -> Tuple[int, int, int]:
        """Return (r, g, b) as integers 0‑255, ignoring alpha."""
        return (self.r, self.g, self.b)

    def to_rgba_tuple(self) -> Tuple[int, int, int, int]:
        """Return (r, g, b, a) with alpha as 0‑255."""
        return self.toTuple()
    
    def validate(self):
        """Ensure that color values are within valid ranges."""
        self.r = max(0, min(255, int(self.r)))
        self.g = max(0, min(255, int(self.g)))
        self.b = max(0, min(255, int(self.b)))
        self.a = max(0.0, min(1.0, float(self.a)))
        
    def toTuple(self) -> Tuple[int, int, int, int]:
        """Convert to RGBA tuple with alpha as 0-255."""
        self.validate()
        return (self.r, self.g, self.b, int(self.a * 255))
    
    def toHex(self) -> str:
        """Convert to hex string."""
        self.validate()
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
    
    def toHSL(self) -> Tuple[float, float, float]:
        """Convert to HSL tuple."""
        self.validate()
        r, g, b = self.r / 255.0, self.g / 255.0, self.b / 255.0
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2
        
        if max_c == min_c:
            h = s = 0  # achromatic
        else:
            d = max_c - min_c
            s = d / (1 - abs(2 * l - 1))
            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6
        
        return (h * 360, s * 100, l * 100)