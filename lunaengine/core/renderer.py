"""
Renderer Abstraction Layer - Graphics Backend Interface

LOCATION: lunaengine/core/renderer.py

DESCRIPTION:
Defines the abstract interface for all rendering backends in LunaEngine.
Provides a unified API for 2D graphics operations regardless of the underlying
graphics technology (Pygame, OpenGL, etc.). Ensures consistent rendering
behavior across different platforms and hardware.

KEY FEATURES:
- Abstract base class for renderer implementations
- Standardized drawing primitives (shapes, surfaces, lines)
- Frame lifecycle management (begin/end frame)
- Hardware abstraction for graphics operations

LIBRARIES USED:
- abc: Abstract base class functionality
- pygame: Surface and rendering type definitions
- typing: Type hints for method signatures

IMPLEMENTATIONS:
- PygameRenderer (backend/pygame_backend.py): Software-based fallback
- OpenGLRenderer (backend/opengl.py): Hardware-accelerated rendering
"""

from abc import ABC, abstractmethod
import pygame
from typing import Tuple

class Renderer(ABC):
    """Abstract base class for all renderers in LunaEngine."""
    
    @abstractmethod
    def initialize(self):
        """Initialize the renderer and required resources."""
        pass
        
    @abstractmethod
    def begin_frame(self):
        """Begin a new rendering frame (clear screen, etc.)."""
        pass
        
    @abstractmethod
    def end_frame(self):
        """End the current rendering frame (swap buffers, etc.)."""
        pass
        
    @abstractmethod
    def draw_surface(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw a pygame surface at specified coordinates.
        
        Args:
            surface (pygame.Surface): The surface to draw
            x (int): X coordinate
            y (int): Y coordinate
        """
        pass
        
    @abstractmethod
    def draw_rect(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int]):
        """
        Draw a rectangle.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Rectangle width
            height (int): Rectangle height
            color (Tuple[int, int, int]): RGB color tuple
        """
        pass
        
    @abstractmethod
    def draw_circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int]):
        """
        Draw a circle.
        
        Args:
            x (int): Center X coordinate
            y (int): Center Y coordinate
            radius (int): Circle radius
            color (Tuple[int, int, int]): RGB color tuple
        """
        pass
        
    @abstractmethod
    def draw_line(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                  color: Tuple[int, int, int], width: int = 1):
        """
        Draw a line.
        
        Args:
            start_x (int): Start X coordinate
            start_y (int): Start Y coordinate
            end_x (int): End X coordinate
            end_y (int): End Y coordinate
            color (Tuple[int, int, int]): RGB color tuple
            width (int): Line width (default: 1)
        """
        pass
    
