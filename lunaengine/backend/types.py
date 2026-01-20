"""
lunaengine/backend/types.py

A collection of types used in lunaengine
"""

import pygame.locals
from dataclasses import dataclass
from typing import Callable, Optional, Literal, Tuple
from enum import Enum

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
    
    def __post_init__(self):
        if self.mouse_buttons_pressed is None:
            self.mouse_buttons_pressed = MouseButtonPressed()
            
        if self.consumed_events is None:
            self.consumed_events = set()
    
    def update(self, mouse_pos: tuple, mouse_pressed:tuple, mouse_wheel: float = 0):
        """Update input state with proper click detection"""
        
        self.mouse_buttons_pressed.left = mouse_pressed[0]
        self.mouse_buttons_pressed.middle = mouse_pressed[1]
        self.mouse_buttons_pressed.right = mouse_pressed[2]
        self.mouse_buttons_pressed.extra_button_1 = mouse_pressed[3]
        self.mouse_buttons_pressed.extra_button_2 = mouse_pressed[4]
        self.mouse_pos = mouse_pos
        
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
        self.consumed_events.clear()
        
    def get_mouse_state(self) -> Tuple[Tuple[int, int], MouseButtonPressed]:
        return self.mouse_pos, self.mouse_buttons_pressed

ElementsListEvents = Literal['append', 'insert', 'extend', 'remove', 'pop']

class ElementsList(list):
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