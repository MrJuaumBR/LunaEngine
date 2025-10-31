"""
Real-time Shadow System - Dynamic Shadow Casting and Occlusion

LOCATION: lunaengine/graphics/shadows.py

DESCRIPTION:
Advanced shadow system that calculates real-time shadows based on light
sources and occluding objects. Creates dynamic shadow polygons that
respond to light position and object geometry for immersive lighting.

KEY FEATURES:
- Dynamic shadow casting from multiple occluders
- Light-based shadow calculation with configurable radius
- Shadow polygon generation with proper vertex extension
- Alpha-blended shadow rendering for smooth edges
- Efficient occluder management and removal

LIBRARIES USED:
- pygame: Polygon rendering and surface operations
- numpy: Mathematical calculations for shadow geometry
- math: Vector calculations and distance measurements
- typing: Type annotations for coordinates and shapes

USAGE:
>>> shadow_system = ShadowSystem(800, 600)
>>> shadow_system.add_occluder(pygame.Rect(100, 100, 50, 50))
>>> shadow_map = shadow_system.calculate_shadows((200, 200), 300)
>>> screen.blit(shadow_map, (0, 0))
"""
import pygame, math
import numpy as np
from typing import List, Tuple

class ShadowSystem:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.shadow_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.occluders = []
        
    def add_occluder(self, rect: pygame.Rect):
        """Add an object that casts shadows"""
        self.occluders.append(rect)
        
    def remove_occluder(self, rect: pygame.Rect):
        """Remove an occluder"""
        if rect in self.occluders:
            self.occluders.remove(rect)
            
    def calculate_shadows(self, light_pos: Tuple[float, float], light_radius: float) -> pygame.Surface:
        """Calculate shadows for a light source"""
        self.shadow_surface.fill((0, 0, 0, 0))
        
        for occluder in self.occluders:
            self._draw_shadow_polygon(self.shadow_surface, light_pos, occluder, light_radius)
            
        return self.shadow_surface
    
    def _draw_shadow_polygon(self, surface: pygame.Surface, light_pos: Tuple[float, float], 
                           occluder: pygame.Rect, light_radius: float):
        """Draw shadow polygon for an occluder"""
        # Get occluder corners
        corners = [
            (occluder.left, occluder.top),
            (occluder.right, occluder.top),
            (occluder.right, occluder.bottom),
            (occluder.left, occluder.bottom)
        ]
        
        # Calculate shadow vertices
        shadow_vertices = []
        for corner in corners:
            # Vector from light to corner
            dx = corner[0] - light_pos[0]
            dy = corner[1] - light_pos[1]
            
            # Normalize and extend beyond light radius
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                dx /= length
                dy /= length
                
            # Extend to light radius + some margin
            extended_x = corner[0] + dx * light_radius * 2
            extended_y = corner[1] + dy * light_radius * 2
            
            shadow_vertices.append((extended_x, extended_y))
        
        # Create shadow polygon (alternating between occluder corners and extended vertices)
        polygon_points = []
        for i in range(4):
            polygon_points.append(corners[i])
            polygon_points.append(shadow_vertices[i])
            
        # Draw the shadow polygon
        if len(polygon_points) >= 3:
            pygame.draw.polygon(surface, (0, 0, 0, 180), polygon_points)