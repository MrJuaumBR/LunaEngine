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
- Particle system rendering with dynamic buffers
- Scissor testing for clipping regions
- Geometry caching for performance optimization

LIBRARIES USED:
- abc: Abstract base class functionality
- pygame: Surface and rendering type definitions
- typing: Type hints for method signatures
- numpy: Array operations for particle systems

IMPLEMENTATIONS:
- PygameRenderer (backend/pygame_backend.py): Software-based fallback
- OpenGLRenderer (backend/opengl.py): Hardware-accelerated rendering
"""

from abc import ABC, abstractmethod
import pygame
from typing import Tuple, Dict, Any, List, Optional
import numpy as np

class Renderer(ABC):
    """Abstract base class for all renderers in LunaEngine."""
    
    # Camera position for coordinate transformations
    camera_position: pygame.math.Vector2 = pygame.math.Vector2(0, 0)
    
    @property
    @abstractmethod
    def max_particles(self) -> int:
        """
        Get the maximum number of particles supported by the renderer.
        
        Returns:
            int: Maximum number of particles
        """
        pass
    
    @max_particles.setter
    @abstractmethod
    def max_particles(self, value: int):
        """
        Set the maximum number of particles and trigger resize callbacks.
        
        Args:
            value (int): New maximum particle count
        """
        pass
    
    @abstractmethod
    def initialize(self):
        """
        Initialize the renderer and required resources.
        
        This method should set up the rendering context, create shaders (if applicable),
        allocate buffers, and prepare the renderer for drawing operations.
        """
        pass
        
    @abstractmethod
    def begin_frame(self):
        """
        Begin a new rendering frame.
        
        This typically involves clearing the screen, resetting render states,
        and preparing for new drawing commands.
        """
        pass
        
    @abstractmethod
    def end_frame(self):
        """
        End the current rendering frame.
        
        This typically involves swapping buffers, finalizing rendering operations,
        and preparing for display.
        """
        pass
    
    @abstractmethod
    def get_surface(self) -> pygame.Surface:
        """
        Get the main rendering surface.
        
        Returns:
            pygame.Surface: The current rendering surface
        """
        pass
    
    @abstractmethod
    def set_surface(self, surface: pygame.Surface):
        """
        Set a custom surface for rendering.
        
        Args:
            surface (pygame.Surface): Surface to use as render target
        """
        pass
    
    @abstractmethod
    def draw_surface(self, x: int, y: int, surface: pygame.Surface = None):
        """
        Draw a pygame surface at specified coordinates.
        
        Args:
            surface (pygame.Surface): The surface to draw
            x (int): X coordinate
            y (int): Y coordinate
        """
        pass
    
    @abstractmethod
    def render_surface(self, surface: pygame.Surface, x: int, y: int):
        """
        Alternative method for drawing surfaces (OpenGL compatibility).
        
        Args:
            surface (pygame.Surface): The surface to draw
            x (int): X coordinate
            y (int): Y coordinate
        """
        pass
        
    @abstractmethod
    def draw_rect(self, x: int, y: int, width: int, height: int, 
                color: Tuple[int, int, int, float], fill: bool = True, 
                anchor_point: Tuple[float, float] = (0.0, 0.0), 
                border_width: int = 1, surface: Optional[pygame.Surface] = None,
                corner_radius: Tuple[int, int, int, int]|int = 0):
        """
        Draw a colored rectangle with optional rounded corners.
        
        Args:
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Rectangle width
            height (int): Rectangle height
            color (Tuple[int, int, int, float]): RGBA color tuple
            fill (bool): Whether to fill the rectangle (default: True)
            anchor_point (Tuple[float, float]): Anchor point (default: (0.0, 0.0))
            border_width (int): Border width for hollow rectangles (default: 1)
            corner_radius: Radius of rounded corners in pixels (default: 0 = sharp corners)
        """
        pass
        
    @abstractmethod
    def draw_circle(self, center_x: int, center_y: int, radius: int, 
                    color: Tuple[int, int, int], fill: bool = True, border_width: int = 1, surface: Optional[pygame.Surface] = None):
        """
        Draw a circle with specified center, radius and color.
        
        Args:
            center_x (int): Center X coordinate
            center_y (int): Center Y coordinate
            radius (int): Circle radius
            color (Tuple[int, int, int]): RGB color tuple
            fill (bool): Whether to fill the circle (default: True)
            border_width (int): Border width for hollow circles (default: 1)
        """
        pass
        
    @abstractmethod
    def draw_line(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                  color: Tuple[int, int, int], width: int = 1, surface: Optional[pygame.Surface] = None):
        """
        Draw a line between two points with specified width.
        
        Args:
            start_x (int): Start X coordinate
            start_y (int): Start Y coordinate
            end_x (int): End X coordinate
            end_y (int): End Y coordinate
            color (Tuple[int, int, int]): RGB color tuple
            width (int): Line width (default: 1)
        """
        pass
    
    @abstractmethod
    def draw_lines(self, points: List[Tuple[int, int]], color: Tuple[int, int, int], width: int = 1, surface: Optional[pygame.Surface] = None):
        """
        Draw multiple lines beetween the points specified.
        
        Args:
            points (List[Tuple[int, int]]): List of (x, y) points defining the lines
            color (Tuple[int, int, int]): RGB color tuple
            width (int): Line width (default: 1)
            surface (Optional[pygame.Surface]): Surface to draw
        """
        pass
    
    @abstractmethod
    def draw_polygon(self, points: List[Tuple[int, int]], color: Tuple[int, int, int], 
                     fill: bool = True, border_width: int = 1, surface: Optional[pygame.Surface] = None):
        """
        Draw a polygon from a list of points.
        
        Args:
            points (List[Tuple[int, int]]): List of (x, y) points defining the polygon
            color (Tuple[int, int, int]): RGB color tuple
            fill (bool): Whether to fill the polygon (default: True)
            border_width (int): Border width for hollow polygons (default: 1)
        """
        pass
    
    @abstractmethod
    def draw_text(self, text:str, x:int, y:int, color:Tuple[int, int, int], font:pygame.font.FontType, surface: Optional[pygame.Surface] = None, anchor_point: tuple = (0.0, 0.0)):
        """
        Draw text using pygame font rendering
        """
        pass
    
    @abstractmethod
    def enable_scissor(self, x: int, y: int, width: int, height: int):
        """
        Enable scissor test for clipping region.
        
        Args:
            x (int): X position from left (pygame coordinate system)
            y (int): Y position from top (pygame coordinate system)  
            width (int): Width of scissor region
            height (int): Height of scissor region
        """
        pass
    
    @abstractmethod
    def disable_scissor(self):
        """
        Disable scissor test.
        """
        pass
    
    @abstractmethod
    def render_particles(self, particle_data: Dict[str, Any], camera: Any):
        """
        Render particle systems with optimized batch processing.
        
        Args:
            particle_data (Dict[str, Any]): Particle system data containing:
                - positions: Array of particle positions
                - sizes: Array of particle sizes
                - colors: Array of particle colors
                - alphas: Array of particle alpha values
                - active_count: Number of active particles
            camera (Any): Camera object for coordinate transformations
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """
        Clean up rendering resources and shutdown the renderer.
        
        This method should release all allocated resources, delete shaders,
        buffers, and perform any necessary cleanup operations.
        """
        pass
    
    @abstractmethod
    def blit(self, source_surface: pygame.Surface, dest_rect: pygame.Rect, area: Optional[pygame.Rect] = None, 
         special_flags: int = 0):
        """
        Blit a source surface onto the current render target.
        Works similarly to pygame.Surface.blit().
        
        Args:
            source_surface: Surface to blit from
            dest_rect: Destination rectangle (x, y, width, height) or (x, y)
            area: Source area to blit from (None for entire surface)
            special_flags: Additional blitting flags (currently unused)
        """
        pass
    
    @abstractmethod
    def fill_screen(self, color: Tuple[int, int, int, float]):
        """
        Fill the screen background with the color
        
        R,G,B,A = (0~255, 0~255, 0~255, 0.0~1.0)
        
        Args:
            color (Tuple[int, int, int, float]): RGBA color tuple
        """
        if len(color) == 4:
            r, g, b, a = color
        elif len(color) == 3:
            r, g, b = color
            a = 1
        else:
            print("Invalid RGBA format. Expected (r, g, b, a) or (r, g, b)")
            return
        
        win_w, win_h = pygame.display.get_window_size()
        self.draw_rect(0,0,win_w, win_h, (r, g, b, a), fill=True, surface=self.screen)
        
    def resize(self, surface: pygame.Surface, width: int, height: int):
        """
        Resize a surface
        
        Args:
            surface (pygame.Surface): Surface to resize
            width (int): New width
            height (int): New height
        """
        return pygame.transform.scale(surface, (width, height))
    
    
    def scale(self, surface:pygame.Surface, width:float, height:float):
        """
        Scale a surface by a percentage
        
        Args:
            surface (pygame.Surface): Surface to scale
            width (float): Percentage to scale width
            height (float): Percentage to scale height
        """
        size = surface.get_size()
        return self.resize(surface, int(size[0] * width), int(size[1] * height))