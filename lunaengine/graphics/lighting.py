import pygame
import numpy as np
from typing import List, Tuple
import math

class Light:
    def __init__(self, x: float, y: float, radius: float, color: Tuple[int, int, int] = (255, 255, 255), intensity: float = 1.0):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.active = True
        
class LightSystem:
    def __init__(self, screen_width: int, screen_height: int):
        self.lights = []
        self.ambient_light = 0.1
        self.light_map = None
        self.screen_width = screen_width
        self.screen_height = screen_height
        
    def add_light(self, light: Light):
        """Add a light to the system"""
        self.lights.append(light)
        
    def remove_light(self, light: Light):
        """Remove a light from the system"""
        if light in self.lights:
            self.lights.remove(light)
            
    def calculate_lighting(self, surface: pygame.Surface) -> pygame.Surface:
        """Calculate lighting for a surface"""
        # Create a light accumulation surface
        light_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        light_surface.fill((0, 0, 0, int(255 * self.ambient_light)))
        
        for light in self.lights:
            if not light.active:
                continue
                
            # Create a temporary surface for this light
            temp_light = pygame.Surface((light.radius * 2, light.radius * 2), pygame.SRCALPHA)
            
            # Create radial gradient
            center = light.radius
            for y in range(temp_light.get_height()):
                for x in range(temp_light.get_width()):
                    dist = math.sqrt((x - center) ** 2 + (y - center) ** 2)
                    if dist <= light.radius:
                        alpha = int(255 * light.intensity * (1 - dist / light.radius))
                        temp_light.set_at((x, y), (*light.color, alpha))
            
            # Blit the light onto the light surface
            light_surface.blit(temp_light, 
                             (light.x - light.radius, light.y - light.radius), 
                             special_flags=pygame.BLEND_RGBA_ADD)
        
        # Apply lighting to the original surface
        final_surface = surface.copy()
        final_surface.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return final_surface