# lunaengine/graphics/camera.py
"""
Camera System - 2D Camera with Smooth Movement and Effects
"""

import pygame, math
import numpy as np
from typing import Optional, Tuple, Callable, List, TYPE_CHECKING, Literal
from enum import Enum

# Type hints
if TYPE_CHECKING:
    from lunaengine.core import Scene
    from lunaengine.core import LunaEngine

class CameraMode(Enum):
    """Camera follow behavior modes"""
    FIXED = "fixed"
    FOLLOW = "follow"
    PLATFORMER = "platformer"
    TOPDOWN = "topdown"

class CameraShakeType(Enum):
    """Types of camera shake effects"""
    POSITIONAL = "positional"
    ROTATIONAL = "rotational"
    TRAUMA = "trauma"

class ParallaxLayer:
    """
    Otimizado: Camada de parallax com renderização eficiente
    """
    
    def __init__(self, surface: pygame.Surface, speed_factor: float, 
                 tile_mode: bool = True, offset: Tuple[float, float] = (0, 0)):
        """
        Inicializa uma camada de parallax.
        
        Args:
            surface: Superfície pygame para a camada
            speed_factor: Fator de velocidade (0.0 = estático, 1.0 = move com câmera)
            tile_mode: Se True, a imagem se repete infinitamente
            offset: Offset inicial da camada
        """
        self.surface = surface
        self.speed_factor = speed_factor
        self.tile_mode = tile_mode
        self.offset = pygame.math.Vector2(offset)
        self._cached_texture = None
        self._texture_size = surface.get_size()
        
        # Cache para otimização
        self._last_camera_pos = None
        self._last_zoom = None
        self._rendered_regions = {}
        
    def update(self, camera_position: pygame.math.Vector2, camera_zoom: float, dt: float):
        """
        Atualiza a posição da camada baseado na posição da câmera.
        """
        # Aplica o fator de velocidade ao movimento
        movement = camera_position * (1.0 - self.speed_factor)
        self.offset = pygame.math.Vector2(movement.x, movement.y)
        
        # Limpa cache se a câmera mudou significativamente
        current_key = (int(camera_position.x // 100), int(camera_position.y // 100), camera_zoom)
        if current_key != self._last_camera_pos:
            self._rendered_regions.clear()
            self._last_camera_pos = current_key

class ParallaxBackground:
    """
    Sistema de parallax otimizado para múltiplas camadas
    """
    
    def __init__(self, camera):
        self.camera = camera
        self.layers: List[ParallaxLayer] = []
        self.enabled = True
        
        # Otimização: cache de superfícies renderizadas
        self._composite_cache = {}
        self._cache_key = None
        self._cache_size = (0, 0)
        
    def add_layer(self, surface: pygame.Surface, speed_factor: float, 
                  tile_mode: bool = True, offset: Tuple[float, float] = (0, 0)) -> ParallaxLayer:
        """
        Adiciona uma camada ao sistema de parallax.
        
        Args:
            surface: Superfície pygame
            speed_factor: Fator de velocidade do parallax
            tile_mode: Se a imagem deve se repetir
            offset: Offset inicial
            
        Returns:
            ParallaxLayer: A camada criada
        """
        layer = ParallaxLayer(surface, speed_factor, tile_mode, offset)
        self.layers.append(layer)
        return layer
    
    def remove_layer(self, layer: ParallaxLayer):
        """Remove uma camada do sistema de parallax"""
        if layer in self.layers:
            self.layers.remove(layer)
    
    def clear_layers(self):
        """Remove todas as camadas"""
        self.layers.clear()
        self._composite_cache.clear()
    
    def update(self, dt: float):
        """Atualiza todas as camadas de parallax"""
        if not self.enabled or not self.layers:
            return
            
        for layer in self.layers:
            layer.update(self.camera.position, self.camera.zoom, dt)
    
    def render(self, renderer) -> bool:
        """
        Renderiza todas as camadas de parallax de forma otimizada.
        
        Returns:
            bool: True se o parallax foi renderizado, False caso contrário
        """
        if not self.enabled or not self.layers:
            return False
            
        try:
            # Ordena camadas por speed_factor (fundos mais lentos primeiro)
            sorted_layers = sorted(self.layers, key=lambda x: x.speed_factor)
            
            # Renderiza cada camada
            for layer in sorted_layers:
                self._render_layer(renderer, layer)
                
            return True
            
        except Exception as e:
            print(f"Erro no renderizador de parallax: {e}")
            return False
    
    def _render_layer(self, renderer, layer: ParallaxLayer):
        """Renderiza uma única camada de parallax de forma otimizada"""
        camera_pos = self.camera.position
        viewport_size = (self.camera.viewport_width, self.camera.viewport_height)
        zoom = self.camera.zoom
        
        # Calcula a posição base da camada
        base_x = -camera_pos.x * (1.0 - layer.speed_factor) + layer.offset.x
        base_y = -camera_pos.y * (1.0 - layer.speed_factor) + layer.offset.y
        
        if layer.tile_mode:
            # Modo tile: renderiza múltiplas cópias da textura
            self._render_tiled_layer(renderer, layer, base_x, base_y, viewport_size, zoom)
        else:
            # Modo único: renderiza uma única cópia
            self._render_single_layer(renderer, layer, base_x, base_y, viewport_size, zoom)
    
    def _render_tiled_layer(self, renderer, layer: ParallaxLayer, base_x: float, base_y: float, 
                           viewport_size: Tuple[int, int], zoom: float):
        """Renderiza camada em modo tile (repetição infinita)"""
        texture_width, texture_height = layer.surface.get_size()
        
        if texture_width == 0 or texture_height == 0:
            return
            
        # Calcula quantas cópias são necessárias para cobrir a tela
        start_tile_x = int(base_x // texture_width) - 1
        end_tile_x = int((base_x + viewport_size[0]) // texture_width) + 2
        
        start_tile_y = int(base_y // texture_height) - 1
        end_tile_y = int((base_y + viewport_size[1]) // texture_height) + 2
        
        # Renderiza cada tile visível
        for tile_x in range(start_tile_x, end_tile_x):
            for tile_y in range(start_tile_y, end_tile_y):
                tile_pos_x = base_x + tile_x * texture_width
                tile_pos_y = base_y + tile_y * texture_height
                
                # Verifica se o tile está visível na tela
                if (tile_pos_x + texture_width > 0 and tile_pos_x < viewport_size[0] and
                    tile_pos_y + texture_height > 0 and tile_pos_y < viewport_size[1]):
                    
                    # Usa o método de renderização apropriado baseado no renderer
                    if hasattr(renderer, 'draw_surface'):
                        renderer.draw_surface(layer.surface, int(tile_pos_x), int(tile_pos_y))
                    elif hasattr(renderer, 'render_surface'):
                        renderer.render_surface(layer.surface, int(tile_pos_x), int(tile_pos_y))
                    else:
                        # Fallback: renderização direta pygame
                        if hasattr(renderer, 'get_surface'):
                            target_surface = renderer.get_surface()
                            target_surface.blit(layer.surface, (int(tile_pos_x), int(tile_pos_y)))
    
    def _render_single_layer(self, renderer, layer: ParallaxLayer, base_x: float, base_y: float,
                            viewport_size: Tuple[int, int], zoom: float):
        """Renderiza camada em modo único (uma única cópia)"""
        texture_width, texture_height = layer.surface.get_size()
        
        # Verifica se a camada está visível na tela
        if (base_x + texture_width > 0 and base_x < viewport_size[0] and
            base_y + texture_height > 0 and base_y < viewport_size[1]):
            
            # Usa o método de renderização apropriado
            if hasattr(renderer, 'draw_surface'):
                renderer.draw_surface(layer.surface, int(base_x), int(base_y))
            elif hasattr(renderer, 'render_surface'):
                renderer.render_surface(layer.surface, int(base_x), int(base_y))
            else:
                # Fallback: renderização direta pygame
                if hasattr(renderer, 'get_surface'):
                    target_surface = renderer.get_surface()
                    target_surface.blit(layer.surface, (int(base_x), int(base_y)))

class Camera:
    """
    Advanced 2D Camera system with smooth movement and effects.
    """
    
    def __init__(self, scene, width: int, height: int):
        """
        Initialize camera with viewport dimensions.
        """
        self.scene = scene
        self.engine = self.scene.engine
        self.renderer = self.engine.renderer
        self.viewport_width = width
        self.viewport_height = height
        
        # Camera state - usando pygame.Vector2 para compatibilidade
        self._position = pygame.math.Vector2(0.0, 0.0)
        self.target_position = pygame.math.Vector2(0.0, 0.0)
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.rotation = 0.0
        
        # Follow behavior
        self.target = None
        self.mode = CameraMode.FOLLOW
        self.smooth_speed = 0.1
        self.lead_factor = 0.0
        
        # Platformer settings
        self.deadzone = pygame.Rect(0, 0, 200, 150)
        self.deadzone.center = (width // 2, height // 2)
        
        # Boundaries
        self.bounds = None
        self.limit_enabled = True
        
        # Shake effects
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_trauma = 0.0
        self.shake_type = CameraShakeType.POSITIONAL
        self.offset = pygame.math.Vector2(0.0, 0.0)
        self.rotation_offset = 0.0
        
        # Sistema de Parallax
        self.parallax = ParallaxBackground(self)
        
        # Callbacks
        self.on_shake_complete: Optional[Callable] = None
    
    @property
    def position(self) -> pygame.math.Vector2:
        """Get camera position with shake offset applied"""
        return self._position + self.offset
    
    @position.setter
    def position(self, value):
        """Set camera base position (without shake)"""
        if isinstance(value, (list, tuple, np.ndarray)):
            self._position = pygame.math.Vector2(value[0], value[1])
        elif isinstance(value, pygame.math.Vector2):
            self._position = value
        else:
            raise ValueError("Position must be tuple, list, numpy array or pygame.Vector2")
    
    @property
    def base_position(self) -> pygame.math.Vector2:
        """Get camera base position without shake offset"""
        return self._position
    
    def set_target(self, target, mode: CameraMode = CameraMode.FOLLOW):
        """
        Set camera target to follow.
        """
        self.target = target
        self.mode = mode
        
    def set_bounds(self, bounds: pygame.Rect):
        """
        Set camera movement boundaries.
        """
        self.bounds = bounds
        
    def update(self, dt: float):
        """
        Update camera position and effects.
        """
        # Update target position if following an object
        if self.target is not None:
            self._update_follow(dt)
        
        # Apply smooth movement
        self._apply_smooth_movement(dt)
        
        # Apply zoom
        self._apply_zoom(dt)
        
        # Apply camera shake
        self._apply_shake(dt)
        
        # Apply boundaries
        if self.limit_enabled and self.bounds is not None:
            self._apply_bounds()
        
        # Atualiza sistema de parallax
        self.parallax.update(dt)
        
        # ATUALIZAR POSIÇÃO DA CÂMERA NO RENDERER
        self._update_renderer_camera_position()
    
    def _update_renderer_camera_position(self):
        """Update camera position in both renderers"""
        # Atualiza no renderer principal
        self.renderer.camera_position = self.position
        
        # Atualiza no renderer de UI também (mas com offset zero para UI)
        if hasattr(self.engine, 'ui_renderer') and self.engine.ui_renderer != self.renderer:
            self.engine.ui_renderer.camera_position = pygame.math.Vector2(0, 0)
    
    def _update_follow(self, dt: float):
        """Update camera position based on follow mode"""
        target_pos = self._get_target_position()
        
        if self.mode == CameraMode.FIXED:
            self.target_position = target_pos
            
        elif self.mode == CameraMode.FOLLOW:
            self.target_position = target_pos
            
        elif self.mode == CameraMode.PLATFORMER:
            self._update_platformer_mode(target_pos)
            
        elif self.mode == CameraMode.TOPDOWN:
            self._update_topdown_mode(target_pos)
    
    def _get_target_position(self) -> pygame.math.Vector2:
        """Extract position from target object"""
        if hasattr(self.target, 'rect'):
            # Pygame sprite with rect
            return pygame.math.Vector2(self.target.rect.centerx, self.target.rect.centery)
        elif hasattr(self.target, 'position'):
            # Custom object with position
            pos = self.target.position
            if isinstance(pos, (list, tuple, np.ndarray)):
                return pygame.math.Vector2(pos[0], pos[1])
            elif isinstance(pos, pygame.math.Vector2):
                return pos
            else:
                return pygame.math.Vector2(pos[0], pos[1])
        elif isinstance(self.target, dict):
            # Is a dict
            if 'x' in self.target and 'y' in self.target: 
                return pygame.math.Vector2(self.target['x'], self.target['y'])
            elif 'position' in self.target: 
                pos = self.target['position']
                return pygame.math.Vector2(pos[0], pos[1])
        elif hasattr(self.target, '__len__') and len(self.target) >= 2 and type(self.target) in [list, tuple]:
            # Tuple/list of coordinates
            return pygame.math.Vector2(self.target[0], self.target[1])
        elif isinstance(self.target, pygame.math.Vector2):
            return self.target
        else:
            # Return current target position as fallback
            return pygame.math.Vector2(self.target_position)
    
    def _update_platformer_mode(self, target_pos: pygame.math.Vector2):
        """Platformer-style camera with deadzone"""
        # Convert target to screen space for deadzone check
        screen_target = self.world_to_screen(target_pos)
        
        move_x, move_y = 0, 0
        
        # Check horizontal deadzone
        if screen_target[0] < self.deadzone.left:
            move_x = screen_target[0] - self.deadzone.left
        elif screen_target[0] > self.deadzone.right:
            move_x = screen_target[0] - self.deadzone.right
            
        # Check vertical deadzone
        if screen_target[1] < self.deadzone.top:
            move_y = screen_target[1] - self.deadzone.top
        elif screen_target[1] > self.deadzone.bottom:
            move_y = screen_target[1] - self.deadzone.bottom
        
        # Convert screen movement back to world movement
        world_move = self.screen_to_world_vector((move_x, move_y))
        self.target_position = self._position + world_move
    
    def _update_topdown_mode(self, target_pos: pygame.math.Vector2):
        """Top-down RPG style camera"""
        # Add lead ahead based on target velocity if available
        lead_offset = pygame.math.Vector2(0.0, 0.0)
        if hasattr(self.target, 'velocity'):
            # Use player velocity for lead
            vel = self.target.velocity
            if isinstance(vel, (list, tuple, np.ndarray)):
                lead_offset = pygame.math.Vector2(vel[0] * 50, vel[1] * 50) * self.lead_factor
            elif isinstance(vel, pygame.math.Vector2):
                lead_offset = vel * 50 * self.lead_factor
        elif hasattr(self.target, 'direction'):
            # Use player direction for lead
            dir_vec = self.target.direction
            if isinstance(dir_vec, (list, tuple, np.ndarray)):
                lead_offset = pygame.math.Vector2(dir_vec[0] * 50, dir_vec[1] * 50) * self.lead_factor
            elif isinstance(dir_vec, pygame.math.Vector2):
                lead_offset = dir_vec * 50 * self.lead_factor
            
        self.target_position = target_pos + lead_offset
    
    def _apply_smooth_movement(self, dt: float):
        """Apply smooth interpolation to camera position"""
        # Always lerp towards target position
        t = min(1.0, self.smooth_speed * dt * 60.0)
        self._position = self._position * (1 - t) + self.target_position * t
    
    def _apply_zoom(self, dt: float):
        """Apply smooth zoom interpolation"""
        if abs(self.target_zoom - self.zoom) > 0.01:
            t = min(1.0, self.smooth_speed * dt * 60.0)
            self.zoom = self.zoom * (1 - t) + self.target_zoom * t
    
    def _apply_shake(self, dt: float):
        """Apply camera shake effects"""
        if self.shake_duration > 0:
            self.shake_duration -= dt
            
            if self.shake_type == CameraShakeType.TRAUMA:
                self._update_trauma_shake(dt)
            else:
                self._update_positional_shake(dt)
                
            if self.shake_duration <= 0:
                self.shake_duration = 0
                self.shake_intensity = 0
                self.shake_trauma = 0
                self.offset = pygame.math.Vector2(0.0, 0.0)
                self.rotation_offset = 0.0
                
                if self.on_shake_complete:
                    self.on_shake_complete()
    
    def _update_trauma_shake(self, dt: float):
        """Update trauma-based shake"""
        if self.shake_trauma > 0:
            self.shake_trauma = max(0, self.shake_trauma - dt * 1.5)
            intensity = self.shake_trauma ** 2
            
            self.offset.x = (np.random.random() - 0.5) * 2 * intensity * self.shake_intensity * 20
            self.offset.y = (np.random.random() - 0.5) * 2 * intensity * self.shake_intensity * 20
            self.rotation_offset = (np.random.random() - 0.5) * 2 * intensity * self.shake_intensity * 5
    
    def _update_positional_shake(self, dt: float):
        """Update simple positional shake"""
        self.offset.x = (np.random.random() - 0.5) * 2 * self.shake_intensity
        self.offset.y = (np.random.random() - 0.5) * 2 * self.shake_intensity
    
    def _apply_bounds(self):
        """Constrain camera within boundaries"""
        if self.bounds is None:
            return
            
        # Calculate visible area based on zoom
        visible_width = self.viewport_width / self.zoom
        visible_height = self.viewport_height / self.zoom
        
        min_x = self.bounds.left + visible_width / 2
        max_x = self.bounds.right - visible_width / 2
        min_y = self.bounds.top + visible_height / 2
        max_y = self.bounds.bottom - visible_height / 2
        
        # Ensure bounds are valid
        if min_x > max_x:
            min_x = max_x = (self.bounds.left + self.bounds.right) / 2
        if min_y > max_y:
            min_y = max_y = (self.bounds.top + self.bounds.bottom) / 2
        
        self._position.x = np.clip(self._position.x, min_x, max_x)
        self._position.y = np.clip(self._position.y, min_y, max_y)
    
    def shake(self, intensity: float = 1.0, duration: float = 0.5, 
              shake_type: CameraShakeType = CameraShakeType.POSITIONAL):
        """
        Start camera shake effect.
        """
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_type = shake_type
        
        if shake_type == CameraShakeType.TRAUMA:
            self.shake_trauma = 1.0
    
    def add_trauma(self, amount: float):
        """
        Add trauma for trauma-based shake.
        """
        self.shake_trauma = min(1.0, self.shake_trauma + amount)
    
    def set_zoom(self, zoom: float, smooth: bool = True):
        """
        Set camera zoom level.
        """
        self.target_zoom = max(0.1, zoom)
        if not smooth:
            self.zoom = self.target_zoom
    
    def convert_size_zoom(self, size: tuple) -> tuple:
        x = type(size)
        if x == tuple or x == list:
            return (size[0] / self.zoom, size[1] / self.zoom)
        elif x == int or x == float or x == np.float32:
            return (size / self.zoom)
        elif x == pygame.math.Vector2:
            return pygame.math.Vector2(size.x / self.zoom, size.y / self.zoom)
    
    def convert_size_zoom_list(self, sizes: tuple, return_type:Literal['list', 'nparray', 'ndarray']='list'):
        if return_type == 'list' or return_type == None:
            return [self.convert_size_zoom(s) for s in sizes]
        elif return_type == 'nparray' or return_type == 'ndarray':
            return np.array([self.convert_size_zoom(s) for s in sizes])
    
    def world_to_screen(self, world_pos:pygame.math.Vector2, vector_type:bool=True) -> pygame.math.Vector2:
        """
        Convert world coordinates to screen coordinates
        
        Parameters:
            world_pos: pygame.math.Vector2 or Tuple
            vector_type: bool = True
        Returns:
            pygame.math.Vector2 or Tuple
        """
        if type(world_pos) in [list, tuple, np.ndarray]:
            world_pos = pygame.math.Vector2(world_pos[0], world_pos[1])
        elif type(world_pos) == pygame.math.Vector2: pass
        else:
            raise ValueError(f"Invalid world position type: {type(world_pos)}")
        if self.mode == CameraMode.FIXED:
            screenX = world_pos.x - self.position.x + (self.viewport_width / 2)
            screenY = world_pos.y - self.position.y + (self.viewport_height / 2)
        elif self.mode == CameraMode.TOPDOWN or self.mode == CameraMode.FOLLOW:
            screenX = (world_pos.x - self.position.x) * self.zoom + (self.viewport_width / 2)
            screenY = (world_pos.y - self.position.y) * self.zoom + (self.viewport_height / 2)
        elif self.mode == CameraMode.PLATFORMER:
            screenX = (world_pos.x - self.position.x) * self.zoom
            screenY = (world_pos.y - self.position.y) * self.zoom
            
        return pygame.math.Vector2(screenX, screenY) if vector_type else (screenX, screenY)
    
    def world_to_screen_list(self, world_positions:list, vector_type:bool=True, return_type:Literal['list', 'nparray', 'ndarray']='list'):
        if return_type == 'list' or return_type == None:
            return [self.world_to_screen(pos, vector_type) for pos in world_positions]
        elif return_type == 'nparray' or return_type == 'ndarray':
            return np.array([self.world_to_screen(pos, vector_type) for pos in world_positions])
    
    def screen_to_world(self, screen_pos:pygame.math.Vector2) -> pygame.math.Vector2:
        """
        Converts the screen position to world position
        
        Worlds position are like: 0,0 is the center of the world
        
        Parameters:
            screen_pos: pygame.math.Vector2 or Tuple
        Returns:
            pygame.math.Vector2
        """
        if isinstance(screen_pos, (list, tuple, np.ndarray)):
            screen_vec = pygame.math.Vector2(screen_pos[0], screen_pos[1])
        elif isinstance(screen_pos, pygame.math.Vector2):
            screen_vec = screen_pos
        else:
            raise ValueError("screen_pos must be tuple, list, numpy array or pygame.Vector2")
            
        screen_center = pygame.math.Vector2(self.viewport_width / 2, self.viewport_height / 2)
        
        # Correção para todos os modos
        if self.mode == CameraMode.FIXED:
            world_pos = (screen_vec - screen_center) + self.position
        elif self.mode == CameraMode.TOPDOWN or self.mode == CameraMode.FOLLOW:
            world_pos = (screen_vec - screen_center) / self.zoom + self.position
        elif self.mode == CameraMode.PLATFORMER:
            world_pos = screen_vec / self.zoom + self.position
        
        return world_pos
    
    def screen_to_world_list(self, screen_positions:list) -> list:
        return [self.screen_to_world(pos) for pos in screen_positions]
    
    def screen_to_world_vector(self, screen_vec) -> pygame.math.Vector2:
        """
        Convert screen vector to world vector (ignores camera position).
        """
        if isinstance(screen_vec, (list, tuple, np.ndarray)):
            vec = pygame.math.Vector2(screen_vec[0], screen_vec[1])
        elif isinstance(screen_vec, pygame.math.Vector2):
            vec = screen_vec
        else:
            raise ValueError("screen_vec must be tuple, list, numpy array or pygame.Vector2")
            
        # Vectors are affected by zoom but not camera position
        return vec / self.zoom
    
    def get_visible_rect(self) -> pygame.Rect:
        """
        Get the visible world area as a rectangle.
        """
        half_width = (self.viewport_width / 2) / self.zoom
        half_height = (self.viewport_height / 2) / self.zoom
        
        return pygame.Rect(
            self.position.x - half_width,
            self.position.y - half_height,
            self.viewport_width / self.zoom,
            self.viewport_height / self.zoom
        )
    
    def is_visible(self, world_pos, margin: float = 0.0) -> bool:
        """
        Check if a world position is visible on screen.
        """
        screen_pos = self.world_to_screen(world_pos)
        return (-margin <= screen_pos.x <= self.viewport_width + margin and 
                -margin <= screen_pos.y <= self.viewport_height + margin)
    
    # Métodos do sistema de parallax
    def add_parallax_layer(self, surface: pygame.Surface, speed_factor: float, 
                          tile_mode: bool = True, offset: Tuple[float, float] = (0, 0)) -> ParallaxLayer:
        """
        Adiciona uma camada ao sistema de parallax da câmera.
        
        Args:
            surface: Superfície pygame para a camada
            speed_factor: Fator de velocidade do parallax (0.0 = estático, 1.0 = move com câmera)
            tile_mode: Se a imagem deve se repetir infinitamente
            offset: Offset inicial da camada
            
        Returns:
            ParallaxLayer: A camada criada
        """
        return self.parallax.add_layer(surface, speed_factor, tile_mode, offset)
    
    def remove_parallax_layer(self, layer: ParallaxLayer):
        """Remove uma camada do sistema de parallax"""
        self.parallax.remove_layer(layer)
    
    def clear_parallax_layers(self):
        """Remove todas as camadas de parallax"""
        self.parallax.clear_layers()
    
    def render_parallax(self, renderer) -> bool:
        """
        Renderiza o sistema de parallax.
        
        Returns:
            bool: True se o parallax foi renderizado, False caso contrário
        """
        return self.parallax.render(renderer)
    
    def enable_parallax(self, enabled: bool = True):
        """Habilita ou desabilita o sistema de parallax"""
        self.parallax.enabled = enabled
    
    def get_parallax_layer_count(self) -> int:
        """Retorna o número de camadas de parallax"""
        return len(self.parallax.layers)