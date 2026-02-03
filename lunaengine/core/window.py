"""
Window Management System - Display and Surface Control

LOCATION: lunaengine/core/window.py

DESCRIPTION:
Handles the creation, configuration, and management of the game window.
Provides functionality for display mode changes, window properties, and
surface management. Supports both windowed and fullscreen modes with
dynamic resizing capabilities.

KEY FEATURES:
- Window creation with customizable flags
- Fullscreen/windowed mode switching
- Dynamic window resizing support
- Display surface management
- Window property configuration
- Window event decorators

LIBRARIES USED:
- pygame: Display system, surface creation, and window flags
- typing: Type hints for coordinates and optional parameters
- functools: Decorator utilities

WINDOW FLAGS SUPPORTED:
- OPENGL: OpenGL context creation
- FULLSCREEN: Fullscreen display mode
- RESIZABLE: User-resizable window
- DOUBLEBUF: Double buffering for smooth rendering
"""

import pygame
from typing import Tuple, Optional, Callable, Dict, List, Any
from functools import wraps
from ..backend.types import WindowEventType, WindowEventData

class Window:
    """
    Manages the game window and display settings.
    
    This class handles window creation, resizing, fullscreen mode,
    and provides utility methods for window information.
    
    Attributes:
        title (str): Window title
        width (int): Window width
        height (int): Window height
        fullscreen (bool): Whether window is in fullscreen mode
        resizable (bool): Whether window is resizable
        surface (pygame.Surface): The window surface
        _event_handlers (Dict): Registered event handlers
    """
    
    def __init__(self, title: str = "LunaEngine", width: int = 800, height: int = 600, 
                 fullscreen: bool = False, resizable: bool = True):
        """
        Initialize window settings.
        
        Args:
            title (str): Window title (default: "LunaEngine")
            width (int): Window width (default: 800)
            height (int): Window height (default: 600)
            fullscreen (bool): Start in fullscreen mode (default: False)
            resizable (bool): Allow window resizing (default: True)
        """
        self.title = title
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.resizable = resizable
        self.surface = None
        self._original_size = (width, height)
        
        # Event handling
        self._event_handlers: Dict[WindowEventType, List[Callable]] = {}
        self._window_state = {
            'focused': True,
            'visible': True,
            'minimized': False,
            'maximized': False,
            'position': (0, 0),
            'size': (width, height)
        }
        
    def create(self):
        """Create the game window with specified settings."""
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
        if self.resizable:
            flags |= pygame.RESIZABLE
            
        self.surface = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(self.title)
        
    def set_title(self, title: str):
        """
        Set window title.
        
        Args:
            title (str): New window title
        """
        self.title = title
        pygame.display.set_caption(title)
        
    def set_size(self, width: int, height: int):
        """
        Resize the window.
        
        Args:
            width (int): New window width
            height (int): New window height
        """
        self.width = width
        self.height = height
        if self.surface:
            self.surface = pygame.display.set_mode((width, height), self.surface.get_flags())
            
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        self.create()
        
    def get_size(self) -> Tuple[int, int]:
        """
        Get current window size.
        
        Returns:
            Tuple[int, int]: (width, height) of the window
        """
        return (self.width, self.height)
        
    def get_center(self) -> Tuple[int, int]:
        """
        Get window center coordinates.
        
        Returns:
            Tuple[int, int]: (x, y) coordinates of window center
        """
        return (self.width // 2, self.height // 2)
    
    # Event handling methods
    def _register_event_handler(self, event_type: WindowEventType, func: Callable):
        """Register an event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(func)
        return func
    
    def handle_pygame_event(self, event: pygame.event.Event):
        """
        Handle pygame window events and call registered handlers.
        
        Args:
            event (pygame.event.Event): Pygame event to handle
        """
        # Map pygame events to our WindowEventType
        event_map = {
            pygame.WINDOWFOCUSGAINED: WindowEventType.FOCUS_GAINED,
            pygame.WINDOWFOCUSLOST: WindowEventType.FOCUS_LOST,
            pygame.WINDOWRESIZED: WindowEventType.RESIZED,
            pygame.WINDOWMOVED: WindowEventType.MOVED,
            pygame.WINDOWENTER: WindowEventType.ENTER,
            pygame.WINDOWLEAVE: WindowEventType.LEAVE,
            pygame.QUIT: WindowEventType.CLOSE,
            pygame.WINDOWMINIMIZED: WindowEventType.MINIMIZED,
            pygame.WINDOWRESTORED: WindowEventType.RESTORED,
            pygame.WINDOWMAXIMIZED: WindowEventType.MAXIMIZED,
            pygame.WINDOWSHOWN: WindowEventType.SHOWN,
            pygame.WINDOWHIDDEN: WindowEventType.HIDDEN,
            pygame.WINDOWEXPOSED: WindowEventType.EXPOSED,
        }
        
        event_type = event_map.get(event.type)
        if not event_type or event_type not in self._event_handlers:
            return
        
        # Create event data
        event_data = WindowEventData(
            event_type=event_type,
            timestamp=event.timestamp if hasattr(event, 'timestamp') else pygame.time.get_ticks(),
            window_id=getattr(event, 'window_id', 0),
            data=self._extract_event_data(event, event_type)
        )
        
        # Call all registered handlers
        for handler in self._event_handlers[event_type]:
            try:
                handler(event_data)
            except Exception as e:
                print(f"Error in window event handler: {e}")
    
    def _extract_event_data(self, event: pygame.event.Event, event_type: WindowEventType) -> Dict[str, Any]:
        """Extract relevant data from pygame event."""
        data = {}
        
        if event_type == WindowEventType.RESIZED:
            data['size'] = (event.x, event.y)
            data['old_size'] = self._window_state['size']
            self._window_state['size'] = data['size']
        elif event_type == WindowEventType.MOVED:
            data['position'] = (event.x, event.y)
            self._window_state['position'] = data['position']
        elif event_type == WindowEventType.FOCUS_GAINED:
            self._window_state['focused'] = True
        elif event_type == WindowEventType.FOCUS_LOST:
            self._window_state['focused'] = False
        elif event_type == WindowEventType.MINIMIZED:
            self._window_state['minimized'] = True
            self._window_state['maximized'] = False
        elif event_type == WindowEventType.MAXIMIZED:
            self._window_state['maximized'] = True
            self._window_state['minimized'] = False
        elif event_type == WindowEventType.RESTORED:
            self._window_state['minimized'] = False
            self._window_state['maximized'] = False
        elif event_type == WindowEventType.HIDDEN:
            self._window_state['visible'] = False
        elif event_type == WindowEventType.SHOWN:
            self._window_state['visible'] = True
        
        return data
    
    # Decorator methods for window events
    def on_resize(self, func: Callable):
        """
        Decorator to register window resize event handler.
        
        Args:
            func (Callable): The resize event handler function.
        """
        return self._register_event_handler(WindowEventType.RESIZED, func)
    
    def on_close(self, func: Callable):
        """
        Decorator to register window close event handler.
        
        Args:
            func (Callable): The window close event handler function.
        """
        return self._register_event_handler(WindowEventType.CLOSE, func)
    
    def on_focus(self, func: Callable):
        """
        Decorator to register window focus gained event handler.
        
        Args:
            func (Callable): The window focus event handler function.
        """
        return self._register_event_handler(WindowEventType.FOCUS_GAINED, func)
    
    def on_blur(self, func: Callable):
        """
        Decorator to register window blur (focus lost) event handler.
        
        Args:
            func (Callable): The window blur event handler function.
        """
        return self._register_event_handler(WindowEventType.FOCUS_LOST, func)
    
    def on_move(self, func: Callable):
        """
        Decorator to register window move event handler.
        
        Args:
            func (Callable): The window move event handler function.
        """
        return self._register_event_handler(WindowEventType.MOVED, func)
    
    def on_minimize(self, func: Callable):
        """
        Decorator to register window minimize event handler.
        
        Args:
            func (Callable): The window minimize event handler function.
        """
        return self._register_event_handler(WindowEventType.MINIMIZED, func)
    
    def on_maximize(self, func: Callable):
        """
        Decorator to register window maximize event handler.
        
        Args:
            func (Callable): The window maximize event handler function.
        """
        return self._register_event_handler(WindowEventType.MAXIMIZED, func)
    
    def on_restore(self, func: Callable):
        """
        Decorator to register window restore event handler.
        
        Args:
            func (Callable): The window restore event handler function.
        """
        return self._register_event_handler(WindowEventType.RESTORED, func)
    
    def on_enter(self, func: Callable):
        """
        Decorator to register mouse entering window event handler.
        
        Args:
            func (Callable): The window enter event handler function.
        """
        return self._register_event_handler(WindowEventType.ENTER, func)
    
    def on_leave(self, func: Callable):
        """
        Decorator to register mouse leaving window event handler.
        
        Args:
            func (Callable): The window leave event handler function.
        """
        return self._register_event_handler(WindowEventType.LEAVE, func)
    
    def get_window_state(self) -> Dict[str, Any]:
        """
        Get current window state.
        
        Returns:
            Dict[str, Any]: Current window state
        """
        return self._window_state.copy()
    
    def is_focused(self) -> bool:
        """
        Check if window is focused.
        
        Returns:
            bool: True if window is focused
        """
        return self._window_state['focused']
    
    def is_visible(self) -> bool:
        """
        Check if window is visible.
        
        Returns:
            bool: True if window is visible
        """
        return self._window_state['visible']
    
    def is_minimized(self) -> bool:
        """
        Check if window is minimized.
        
        Returns:
            bool: True if window is minimized
        """
        return self._window_state['minimized']
    
    def is_maximized(self) -> bool:
        """
        Check if window is maximized.
        
        Returns:
            bool: True if window is maximized
        """
        return self._window_state['maximized']