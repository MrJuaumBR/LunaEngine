import pygame
from typing import Tuple, Optional
from ..core.renderer import Renderer

class PygameRenderer(Renderer):
    """Simple Pygame-based renderer for development"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height))
        
    def initialize(self):
        """Initialize the renderer"""
        self.surface = pygame.Surface((self.width, self.height))
        
    def begin_frame(self):
        """Begin rendering frame - clear the surface"""
        self.surface.fill((0, 0, 0))
        
    def end_frame(self):
        """End rendering frame"""
        pass
        
    def get_surface(self) -> pygame.Surface:
        """Get the underlying pygame surface"""
        return self.surface
        
    def draw_surface(self, surface: pygame.Surface, x: int, y: int):
        """Draw a pygame surface - FIXED: Use proper blitting"""
        if surface is not None:
            self.surface.blit(surface, (x, y))
        
    def draw_rect(self, x: int, y: int, width: int, height: int, 
                  color: Tuple[int, int, int], fill: bool = True):
        """Draw a colored rectangle"""
        rect = pygame.Rect(x, y, width, height)
        if fill:
            pygame.draw.rect(self.surface, color, rect)
        else:
            pygame.draw.rect(self.surface, color, rect, 1)
        
    def draw_circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int]):
        """Draw a circle"""
        pygame.draw.circle(self.surface, color, (x, y), radius)
        
    def draw_line(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                  color: Tuple[int, int, int], width: int = 1):
        """Draw a line"""
        pygame.draw.line(self.surface, color, (start_x, start_y), (end_x, end_y), width)