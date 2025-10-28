from abc import ABC, abstractmethod
import pygame
from typing import Tuple

class Renderer(ABC):
    """Abstract base class for renderers"""
    
    @abstractmethod
    def initialize(self):
        pass
        
    @abstractmethod
    def begin_frame(self):
        pass
        
    @abstractmethod
    def end_frame(self):
        pass
        
    @abstractmethod
    def draw_surface(self, surface: pygame.Surface, x: int, y: int):
        pass
        
    @abstractmethod
    def draw_rect(self, x: int, y: int, width: int, height: int, color: Tuple[int, int, int]):
        pass
        
    @abstractmethod
    def draw_circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int]):
        pass
        
    @abstractmethod
    def draw_line(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                  color: Tuple[int, int, int], width: int = 1):
        pass