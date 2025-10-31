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

LIBRARIES USED:
- pygame: Display system, surface creation, and window flags
- typing: Type hints for coordinates and optional parameters

WINDOW FLAGS SUPPORTED:
- OPENGL: OpenGL context creation
- FULLSCREEN: Fullscreen display mode
- RESIZABLE: User-resizable window
- DOUBLEBUF: Double buffering for smooth rendering
"""

import pygame
from typing import Tuple, Optional

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