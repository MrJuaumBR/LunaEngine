import pygame
from typing import Tuple, Optional
from ..core.renderer import Renderer

class PygameRenderer(Renderer):
    """
    Pygame-based software renderer for LunaEngine
    
    LOCATION: lunaengine/backend/pygame_backend.py
    
    DESCRIPTION:
    Provides a simple, reliable software renderer using Pygame's built-in
    drawing functions. Serves as a fallback when OpenGL is not available
    or for development purposes.
    
    FEATURES:
    - Software-based 2D rendering
    - Basic shape drawing (rectangles, circles, lines)
    - Surface blitting and composition
    - Cross-platform compatibility
    
    LIBRARIES USED:
    - pygame: Core graphics, surface management, and drawing primitives
    
    INHERITS FROM:
    - Renderer: Base renderer class from core module
    
    USAGE:
    >>> renderer = PygameRenderer(800, 600)
    >>> renderer.initialize()
    >>> renderer.draw_rect(100, 100, 50, 50, (255, 0, 0))
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize Pygame renderer with specified dimensions
        
        ARGS:
            width: Screen width in pixels
            height: Screen height in pixels
        """
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        
    def initialize(self):
        """Initialize the renderer - create main surface"""
        self.surface = pygame.Surface((self.width, self.height))
        
    def begin_frame(self):
        """Begin rendering frame - clear the surface with black"""
        self.surface.fill((0, 0, 0))
        
    def end_frame(self):
        """End rendering frame - no additional processing needed"""
        pass
        
    def get_surface(self) -> pygame.Surface:
        """
        Get the underlying pygame surface
        
        RETURNS:
            pygame.Surface: The main rendering surface
        """
        return self.surface
        
    def draw_surface(self, surface: pygame.Surface, x: int, y: int):
        """
        Draw a pygame surface onto the renderer
        
        ARGS:
            surface: Pygame surface to draw
            x: X coordinate for drawing
            y: Y coordinate for drawing
        """
        if surface is not None:
            self.surface.blit(surface, (x, y))
        
    def draw_rect(self, x: int, y: int, width: int, height: int, 
                  color: Tuple[int, int, int], fill: bool = True):
        """
        Draw a colored rectangle
        
        ARGS:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Rectangle width
            height: Rectangle height
            color: RGB color tuple
            fill: Whether to fill the rectangle (default: True)
        """
        rect = pygame.Rect(x, y, width, height)
        if fill:
            pygame.draw.rect(self.surface, color, rect)
        else:
            pygame.draw.rect(self.surface, color, rect, 1)
        
    def draw_circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int]):
        """
        Draw a circle
        
        ARGS:
            x: Center X coordinate
            y: Center Y coordinate
            radius: Circle radius
            color: RGB color tuple
        """
        pygame.draw.circle(self.surface, color, (x, y), radius)
        
    def draw_line(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                  color: Tuple[int, int, int], width: int = 1):
        """
        Draw a line
        
        ARGS:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            color: RGB color tuple
            width: Line width (default: 1)
        """
        pygame.draw.line(self.surface, color, (start_x, start_y), (end_x, end_y), width)