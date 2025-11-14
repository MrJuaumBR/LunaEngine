"""
Advanced Shadow System - Optimized for OpenGL Rendering

LOCATION: lunaengine/graphics/shadows.py
"""

import pygame
import numpy as np
import math
import hashlib
import time
from typing import List, Tuple, Optional, Dict, Any, Set
from enum import Enum

class ShadowTechnique(Enum):
    GEOMETRY_FAST = "geometry_fast"
    OCCLUSION_MAP = "occlusion_map" 
    GEOMETRY_QUALITY = "geometry_quality"
    HYBRID = "hybrid"

class PerformanceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"

class Light:
    """Light source for shadow casting"""
    
    def __init__(self, x: float, y: float, radius: float, color: Tuple[int, int, int] = (255, 255, 255), intensity: float = 1.0):
        self.position = pygame.math.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self._visible = True
        
    def get_hash(self) -> str:
        return f"{self.position.x:.1f},{self.position.y:.1f},{self.radius:.1f},{self.intensity:.1f}"

class ShadowCaster:
    """Object that can cast shadows"""
    
    def __init__(self, vertices: List[Tuple[float, float]]):
        self.vertices = vertices
        self._bounds = self._calculate_bounds()
        
    def _calculate_bounds(self) -> pygame.Rect:
        if not self.vertices:
            return pygame.Rect(0, 0, 0, 0)
        min_x = min(v[0] for v in self.vertices)
        min_y = min(v[1] for v in self.vertices)
        max_x = max(v[0] for v in self.vertices)
        max_y = max(v[1] for v in self.vertices)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def get_hash(self) -> str:
        return hashlib.md5(str(tuple(self.vertices)).encode()).hexdigest()
    
    @property
    def bounds(self) -> pygame.Rect:
        return self._bounds

class ShadowSystem:
    """
    Optimized shadow system for OpenGL rendering with stable performance
    """
    
    def __init__(self, screen_width: int, screen_height: int, engine):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.engine = engine
        
        # Core components
        self.lights: List[Light] = []
        self.shadow_casters: List[ShadowCaster] = []
        
        # Performance management
        self.frame_count = 0
        self.last_frame_time = time.time()
        self.current_fps = 60
        self.performance_level = PerformanceLevel.HIGH
        
        # Stable rendering - no frame skipping for OpenGL
        self.always_render = True
        
        # Single rendering surface (reused)
        self.shadow_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.light_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Statistics
        self.stats = {
            'technique_used': ShadowTechnique.GEOMETRY_FAST.value,
            'render_time_ms': 0,
            'visible_lights': 0,
            'visible_casters': 0
        }
        
        # Camera integration
        self.last_camera_position = pygame.math.Vector2(0, 0)
        
        # OpenGL optimization
        self._is_opengl = hasattr(engine.renderer, 'render_opengl')
        
        # Cache for stable rendering
        self._last_shadow_map = None
        self._last_scene_hash = ""
        
    def add_light(self, x: float, y: float, radius: float, color: Tuple[int, int, int] = (255, 255, 255), intensity: float = 1.0) -> Light:
        """Add a light source to the shadow system"""
        light = Light(x, y, radius, color, intensity)
        self.lights.append(light)
        return light
    
    def add_shadow_caster(self, vertices: List[Tuple[float, float]]) -> ShadowCaster:
        """Add an object that can cast shadows"""
        caster = ShadowCaster(vertices)
        self.shadow_casters.append(caster)
        return caster
    
    def add_rectangle_caster(self, x: float, y: float, width: float, height: float) -> ShadowCaster:
        """Add a rectangular shadow caster"""
        vertices = [
            (x, y), (x + width, y), (x + width, y + height), (x, y + height)
        ]
        return self.add_shadow_caster(vertices)
    
    def add_circle_caster(self, x: float, y: float, radius: float, segments: int = 12) -> ShadowCaster:
        """Add a circular shadow caster (approximated as polygon)"""
        vertices = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x + math.cos(angle) * radius
            py = y + math.sin(angle) * radius
            vertices.append((px, py))
        return self.add_shadow_caster(vertices)
    
    def clear_lights(self):
        """Remove all light sources"""
        self.lights.clear()
    
    def clear_shadow_casters(self):
        """Remove all shadow casting objects"""
        self.shadow_casters.clear()
    
    def _calculate_scene_hash(self, camera_position: pygame.math.Vector2) -> str:
        """Calculate hash of current scene state"""
        hash_data = f"cam_{camera_position.x:.0f}_{camera_position.y:.0f}"
        
        # Include lights (limited for performance)
        for light in self.lights[:4]:  # Max 4 lights for hash
            hash_data += light.get_hash()
        
        # Include shadow casters (limited for performance)
        for caster in self.shadow_casters[:20]:  # Max 20 casters for hash
            hash_data += caster.get_hash()
        
        return hashlib.md5(hash_data.encode()).hexdigest()
    
    def _get_visible_lights(self, camera_position: pygame.math.Vector2) -> List[Light]:
        """Get lights that are visible in the current viewport"""
        visible_lights = []
        viewport = self._get_current_viewport(camera_position)
        
        for light in self.lights:
            # Simple distance check with viewport
            light_rect = pygame.Rect(
                light.position.x - light.radius,
                light.position.y - light.radius,
                light.radius * 2,
                light.radius * 2
            )
            
            if viewport.colliderect(light_rect):
                visible_lights.append(light)
        
        return visible_lights[:6]  # Limit to 6 lights for performance
    
    def _get_visible_shadow_casters(self, camera_position: pygame.math.Vector2) -> List[ShadowCaster]:
        """Get shadow casters that are visible in the current viewport"""
        visible_casters = []
        viewport = self._get_current_viewport(camera_position)
        
        for caster in self.shadow_casters:
            if viewport.colliderect(caster.bounds):
                visible_casters.append(caster)
        
        return visible_casters[:30]  # Limit to 30 casters for performance
    
    def _get_current_viewport(self, camera_position: pygame.math.Vector2) -> pygame.Rect:
        """Get current camera viewport in world coordinates"""
        # Get zoom from current scene
        zoom = 1.0
        if hasattr(self.engine, 'current_scene') and hasattr(self.engine.current_scene, 'camera'):
            zoom = self.engine.current_scene.camera.zoom
            
        visible_width = self.screen_width / zoom
        visible_height = self.screen_height / zoom
        
        # Viewport in world coordinates
        return pygame.Rect(
            camera_position.x - visible_width / 2,
            camera_position.y - visible_height / 2,
            visible_width,
            visible_height
        )
    
    def _world_to_screen(self, world_pos: pygame.math.Vector2, camera_position: pygame.math.Vector2) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        zoom = self._get_current_zoom()
        screen_center_x = self.screen_width / 2
        screen_center_y = self.screen_height / 2
        
        screen_x = screen_center_x + (world_pos.x - camera_position.x) * zoom
        screen_y = screen_center_y + (world_pos.y - camera_position.y) * zoom
        
        return (int(screen_x), int(screen_y))
    
    def _get_current_zoom(self) -> float:
        """Get current camera zoom"""
        if hasattr(self.engine, 'current_scene') and hasattr(self.engine.current_scene, 'camera'):
            return self.engine.current_scene.camera.zoom
        return 1.0
    
    def _geometry_fast_technique(self, camera_position: pygame.math.Vector2) -> pygame.Surface:
        """Fast and stable shadow technique for OpenGL - FIXED"""
        result = self.shadow_surface.copy()
        result.fill((0, 0, 0, 0))  # Start transparent
        
        visible_lights = self._get_visible_lights(camera_position)
        visible_casters = self._get_visible_shadow_casters(camera_position)
        
        for light in visible_lights:
            # Create light surface with gradient
            light_surface = self.light_surface.copy()
            light_surface.fill((0, 0, 0, 0))
            
            # Draw light as simple circle - use screen coordinates
            screen_center = self._world_to_screen(light.position, camera_position)
            max_radius = int(light.radius * self._get_current_zoom())
            
            # Simple radial gradient
            for radius in range(max_radius, 0, -max_radius // 4):
                alpha = int(150 * light.intensity * (radius / max_radius))
                color = (*light.color, alpha)
                pygame.draw.circle(light_surface, color, screen_center, radius)
            
            # Draw simple shadows for each caster
            for caster in visible_casters:
                self._draw_simple_shadow(light_surface, light, caster, camera_position)
            
            # Add light to result (lighten areas)
            result.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
        # Invert to get shadows (dark areas)
        shadow_result = self.shadow_surface.copy()
        shadow_result.fill((0, 0, 0, 180))  # Base darkness
        shadow_result.blit(result, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        return shadow_result
    
    def _draw_simple_shadow(self, surface: pygame.Surface, light: Light, caster: ShadowCaster, camera_position: pygame.math.Vector2):
        """Draw simple shadow using vertex extrusion - FIXED"""
        if len(caster.vertices) < 3:
            return
        
        # Convert vertices to screen coordinates
        screen_vertices = [self._world_to_screen(pygame.math.Vector2(v), camera_position) for v in caster.vertices]
        
        # Extrude vertices away from light
        shadow_polygons = []
        light_screen_pos = self._world_to_screen(light.position, camera_position)
        
        for i, vertex in enumerate(screen_vertices):
            next_vertex = screen_vertices[(i + 1) % len(screen_vertices)]
            
            # Calculate direction from light to vertex
            to_vertex = pygame.math.Vector2(vertex[0] - light_screen_pos[0], vertex[1] - light_screen_pos[1])
            to_next = pygame.math.Vector2(next_vertex[0] - light_screen_pos[0], next_vertex[1] - light_screen_pos[1])
            
            if to_vertex.length() > 0:
                to_vertex.normalize_ip()
            if to_next.length() > 0:
                to_next.normalize_ip()
            
            # Extrude vertices
            extrude_distance = light.radius * 1.5 * self._get_current_zoom()
            extruded_vertex = (
                vertex[0] + to_vertex.x * extrude_distance,
                vertex[1] + to_vertex.y * extrude_distance
            )
            extruded_next = (
                next_vertex[0] + to_next.x * extrude_distance,
                next_vertex[1] + to_next.y * extrude_distance
            )
            
            # Create shadow quad
            shadow_poly = [vertex, next_vertex, extruded_next, extruded_vertex]
            shadow_polygons.append(shadow_poly)
        
        # Draw all shadow polygons
        for poly in shadow_polygons:
            if len(poly) >= 3:
                pygame.draw.polygon(surface, (0, 0, 0, 0), poly)
    
    def _update_performance_stats(self):
        """Update performance statistics"""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        if frame_time > 0:
            self.current_fps = 1.0 / frame_time
        
        # Simple performance adjustment
        if self.current_fps < 30:
            self.performance_level = PerformanceLevel.LOW
        elif self.current_fps < 50:
            self.performance_level = PerformanceLevel.MEDIUM
        else:
            self.performance_level = PerformanceLevel.HIGH
    
    def render(self, camera_position: pygame.math.Vector2, renderer = None) -> pygame.Surface:
        """
        Stable shadow rendering for OpenGL
        """
        start_time = time.time()
        self.frame_count += 1
        
        self._update_performance_stats()
        
        # Always use fast technique for stability
        technique = ShadowTechnique.GEOMETRY_FAST
        self.stats['technique_used'] = technique.value
        
        # Check if we can reuse the last shadow map
        current_scene_hash = self._calculate_scene_hash(camera_position)
        if (current_scene_hash == self._last_scene_hash and 
            self._last_shadow_map is not None and
            camera_position.distance_to(self.last_camera_position) < 50):  # Small movement
            self.stats['render_time_ms'] = 0
            return self._last_shadow_map
        
        # Render new shadow map
        result = self._geometry_fast_technique(camera_position)
        
        # Cache the result
        self._last_shadow_map = result
        self._last_scene_hash = current_scene_hash
        self.last_camera_position = camera_position.copy()
        
        # Update statistics
        render_time = (time.time() - start_time) * 1000
        self.stats['render_time_ms'] = render_time
        
        visible_lights = self._get_visible_lights(camera_position)
        visible_casters = self._get_visible_shadow_casters(camera_position)
        self.stats['visible_lights'] = len(visible_lights)
        self.stats['visible_casters'] = len(visible_casters)
        
        return result
    
    def render_to_screen(self, renderer, camera_position: pygame.math.Vector2, x: int = 0, y: int = 0):
        """
        Render shadows directly to screen using the provided renderer - FIXED
        """
        shadow_map = self.render(camera_position, renderer)
        
        if shadow_map and isinstance(shadow_map, pygame.Surface):
            # For OpenGL, use the renderer's blit method with proper blending
            if hasattr(renderer, 'blit'):
                renderer.blit(shadow_map, (x, y))
            elif hasattr(renderer, 'draw_surface'):
                renderer.draw_surface(shadow_map, x, y)
            else:
                # Fallback to pygame blit with proper blending
                target_surface = renderer.get_surface() if hasattr(renderer, 'get_surface') else None
                if target_surface:
                    target_surface.blit(shadow_map, (x, y), special_flags=pygame.BLEND_RGBA_MULT)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance and rendering statistics"""
        return {
            **self.stats,
            'performance_level': self.performance_level.value,
            'current_fps': self.current_fps,
            'total_lights': len(self.lights),
            'total_casters': len(self.shadow_casters),
            'renderer_type': 'opengl' if self._is_opengl else 'pygame'
        }
    
    def cleanup(self):
        """Clean up resources"""
        self._last_shadow_map = None