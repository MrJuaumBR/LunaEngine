import pygame
from typing import Tuple, Optional

class Window:
    def __init__(self, title: str = "LunaEngine", width: int = 800, height: int = 600, 
                 fullscreen: bool = False, resizable: bool = True):
        self.title = title
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.resizable = resizable
        self.surface = None
        self._original_size = (width, height)
        
    def create(self):
        """Create the game window"""
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
        if self.resizable:
            flags |= pygame.RESIZABLE
            
        self.surface = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(self.title)
        
    def set_title(self, title: str):
        """Set window title"""
        self.title = title
        pygame.display.set_caption(title)
        
    def set_size(self, width: int, height: int):
        """Resize the window"""
        self.width = width
        self.height = height
        if self.surface:
            self.surface = pygame.display.set_mode((width, height), self.surface.get_flags())
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        self.create()
        
    def get_size(self) -> Tuple[int, int]:
        """Get window size"""
        return (self.width, self.height)
        
    def get_center(self) -> Tuple[int, int]:
        """Get window center coordinates"""
        return (self.width // 2, self.height // 2)