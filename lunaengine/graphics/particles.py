"""
Particle System - Fixed Version with Colors and Rendering
"""

import pygame
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union
import math
from enum import Enum
from dataclasses import dataclass
import warnings

class ParticleType(Enum):
    """Built-in particle types"""
    FIRE = "fire"
    WATER = "water" 
    SMOKE = "smoke"
    DUST = "dust"
    SPARK = "spark"
    CUSTOM = "custom"

class ExitPoint(Enum):
    """Emission exit points for particles"""
    TOP = "top"
    BOTTOM = "bottom" 
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    CIRCULAR = "circular"

class PhysicsType(Enum):
    """Physics simulation types"""
    TOPDOWN = "topdown"      # For top-down games
    PLATFORMER = "platformer" # For side-view platformers

@dataclass
class ParticleConfig:
    """
    Configuration for particle behavior and appearance
    """
    color_start: Tuple[int, int, int] = (255, 255, 255)
    color_end: Tuple[int, int, int] = (255, 255, 255)
    size_start: float = 4.0
    size_end: float = 4.0
    lifetime: float = 1.0
    speed: float = 100.0
    gravity: float = 98.0
    damping: float = 0.98
    fade_out: bool = True
    grow: bool = False
    spread: float = 45.0

class ParticleSystem:
    """
    Optimized particle system with support for custom particles
    """
    
    # Pre-defined particle configurations - CORRIGIDO: sem propriedade 'colors'
    PARTICLE_CONFIGS: Dict[ParticleType, ParticleConfig] = {
        ParticleType.FIRE: ParticleConfig(
            color_start=(255, 100, 0),
            color_end=(255, 255, 0),
            size_start=8.0,
            size_end=2.0,
            lifetime=1.5,
            speed=150.0,
            gravity=-100.0,
            spread=60.0,
            fade_out=True,
            grow=False
        ),
        ParticleType.WATER: ParticleConfig(
            color_start=(0, 100, 255),
            color_end=(0, 200, 255),
            size_start=6.0,
            size_end=4.0,
            lifetime=2.0,
            speed=80.0,
            gravity=300.0,
            spread=30.0,
            damping=0.9,
            fade_out=True
        ),
        ParticleType.SMOKE: ParticleConfig(
            color_start=(100, 100, 100),
            color_end=(50, 50, 50),
            size_start=4.0,
            size_end=12.0,
            lifetime=3.0,
            speed=60.0,
            gravity=-50.0,
            spread=120.0,
            fade_out=True,
            grow=True
        ),
        ParticleType.DUST: ParticleConfig(
            color_start=(200, 200, 150),
            color_end=(150, 150, 100),
            size_start=3.0,
            size_end=1.0,
            lifetime=1.0,
            speed=40.0,
            gravity=50.0,
            spread=180.0,
            fade_out=True
        ),
        ParticleType.SPARK: ParticleConfig(
            color_start=(255, 255, 200),
            color_end=(255, 100, 0),
            size_start=2.0,
            size_end=1.0,
            lifetime=0.5,
            speed=200.0,
            gravity=200.0,
            spread=15.0,
            fade_out=True
        )
    }
    
    def __init__(self, max_particles: int = 10000):
        """
        Initialize the particle system
        """
        self.max_particles = max_particles
        self.active_particles = 0
        
        # Pre-allocate NumPy arrays for maximum performance
        self._init_arrays()
        
        # Surface cache for rendered particles
        self._surface_cache: Dict[Tuple[int, int, Tuple[int, int, int]], pygame.Surface] = {}
        
        # Object pooling system
        self._free_indices = list(range(max_particles))
        
        # Custom particle registry
        self._custom_configs: Dict[str, ParticleConfig] = {}
    
    def _init_arrays(self):
        """Initialize NumPy arrays for particle data storage"""
        # Position and velocity (2D vectors)
        self.positions = np.zeros((self.max_particles, 2), dtype=np.float32)
        self.velocities = np.zeros((self.max_particles, 2), dtype=np.float32)
        
        # Particle properties
        self.lifetimes = np.zeros(self.max_particles, dtype=np.float32)
        self.max_lifetimes = np.zeros(self.max_particles, dtype=np.float32)
        self.sizes = np.zeros(self.max_particles, dtype=np.float32)
        self.size_starts = np.zeros(self.max_particles, dtype=np.float32)
        self.size_ends = np.zeros(self.max_particles, dtype=np.float32)
        
        # Color data (RGB)
        self.colors_start = np.zeros((self.max_particles, 3), dtype=np.uint8)
        self.colors_end = np.zeros((self.max_particles, 3), dtype=np.uint8)
        self.colors_current = np.zeros((self.max_particles, 3), dtype=np.uint8)
        
        # Physics properties
        self.gravities = np.zeros(self.max_particles, dtype=np.float32)
        self.dampings = np.zeros((self.max_particles, 2), dtype=np.float32)
        
        # State flags
        self.active = np.zeros(self.max_particles, dtype=bool)
        self.fade_outs = np.zeros(self.max_particles, dtype=bool)
        self.grows = np.zeros(self.max_particles, dtype=bool)
    
    def register_custom_particle(self, name: str, config: ParticleConfig) -> bool:
        """
        Register a custom particle type for user-defined effects
        """
        if name in self._custom_configs:
            raise ValueError(f"Custom particle '{name}' is already registered")
        
        self._custom_configs[name] = config
        return True
    
    def get_custom_particle(self, name: str) -> Optional[ParticleConfig]:
        """
        Get configuration for a custom particle
        """
        return self._custom_configs.get(name)
    
    def emit(
        self,
        x: float,
        y: float,
        particle_type: Union[ParticleType, str],
        count: int = 1,
        exit_point: ExitPoint = ExitPoint.CENTER,
        physics_type: PhysicsType = PhysicsType.TOPDOWN,
        spread: Optional[float] = None,
        angle: float = 0.0,
        custom_config: Optional[ParticleConfig] = None
    ):
        """
        Emit particles from specified position with given parameters
        """
        # Resolve particle configuration
        config = self._resolve_particle_config(particle_type, custom_config)
        if not config:
            warnings.warn(f"Particle type '{particle_type}' not found")
            return
        
        # Use provided spread or default from config
        actual_spread = spread if spread is not None else config.spread
        
        for _ in range(count):
            if not self._free_indices:
                break  # No free slots available
                
            idx = self._free_indices.pop()
            self.active_particles += 1
            
            # Set initial position based on exit point
            pos_x, pos_y = self._get_exit_position(x, y, exit_point)
            self.positions[idx] = [pos_x, pos_y]
            
            # Set velocity with spread
            vel_x, vel_y = self._get_initial_velocity(
                exit_point, config.speed, actual_spread, angle
            )
            self.velocities[idx] = [vel_x, vel_y]
            
            # Set particle properties
            self._setup_particle_properties(idx, config, physics_type)
    
    def _resolve_particle_config(
        self, 
        particle_type: Union[ParticleType, str], 
        custom_config: Optional[ParticleConfig]
    ) -> Optional[ParticleConfig]:
        """Resolve particle configuration from various sources"""
        if custom_config:
            return custom_config
        
        if isinstance(particle_type, ParticleType):
            return self.PARTICLE_CONFIGS.get(particle_type)
        elif isinstance(particle_type, str):
            # Try to convert string to ParticleType enum
            try:
                particle_enum = ParticleType(particle_type)
                return self.PARTICLE_CONFIGS.get(particle_enum)
            except ValueError:
                # If not a built-in type, try custom particles
                return self._custom_configs.get(particle_type)
        
        return None
    
    def _get_exit_position(self, x: float, y: float, exit_point: ExitPoint) -> Tuple[float, float]:
        """
        Calculate initial position based on exit point
        """
        if exit_point == ExitPoint.CENTER:
            return x, y
        elif exit_point == ExitPoint.TOP:
            return x, y - 10
        elif exit_point == ExitPoint.BOTTOM:
            return x, y + 10
        elif exit_point == ExitPoint.LEFT:
            return x - 10, y
        elif exit_point == ExitPoint.RIGHT:
            return x + 10, y
        elif exit_point == ExitPoint.CIRCULAR:
            angle = np.random.uniform(0, 2 * math.pi)
            radius = np.random.uniform(5, 15)
            return x + math.cos(angle) * radius, y + math.sin(angle) * radius
        else:
            return x, y
    
    def _get_initial_velocity(
        self, 
        exit_point: ExitPoint, 
        speed: float, 
        spread: float, 
        base_angle: float
    ) -> Tuple[float, float]:
        """
        Calculate initial velocity vector with spread
        """
        # Set base angle based on exit point
        if exit_point == ExitPoint.TOP:
            exit_angle = 90  # Downward
        elif exit_point == ExitPoint.BOTTOM:
            exit_angle = 270  # Upward  
        elif exit_point == ExitPoint.LEFT:
            exit_angle = 0   # Right
        elif exit_point == ExitPoint.RIGHT:
            exit_angle = 180 # Left
        else:
            exit_angle = base_angle
        
        # Apply spread randomization
        final_angle = exit_angle + np.random.uniform(-spread/2, spread/2)
        angle_rad = math.radians(final_angle)
        
        # Random speed variation for natural look
        actual_speed = speed * np.random.uniform(0.8, 1.2)
        
        return (
            math.cos(angle_rad) * actual_speed,
            math.sin(angle_rad) * actual_speed
        )
    
    def _setup_particle_properties(self, idx: int, config: ParticleConfig, physics_type: PhysicsType):
        """Setup all properties for a new particle"""
        # Basic properties
        self.lifetimes[idx] = config.lifetime
        self.max_lifetimes[idx] = config.lifetime
        self.sizes[idx] = config.size_start
        self.size_starts[idx] = config.size_start
        self.size_ends[idx] = config.size_end
        
        # Colors
        self.colors_start[idx] = config.color_start
        self.colors_end[idx] = config.color_end
        self.colors_current[idx] = config.color_start
        
        # Physics
        self.gravities[idx] = config.gravity
        self.dampings[idx] = [config.damping, config.damping]
        
        # Adjust physics for platformer mode
        if physics_type == PhysicsType.PLATFORMER:
            self.gravities[idx] *= 1.5  # Stronger gravity
            self.dampings[idx] = [0.95, 0.95]   # Less damping
        
        # Flags
        self.active[idx] = True
        self.fade_outs[idx] = config.fade_out
        self.grows[idx] = config.grow
    
    def update(self, dt: float):
        """
        Update all active particles
        """
        if self.active_particles == 0:
            return
        
        # Get active indices
        active_mask = self.active
        active_indices = np.where(active_mask)[0]
        
        if len(active_indices) == 0:
            return
        
        # Update lifetimes
        self.lifetimes[active_indices] -= dt
        
        # Kill dead particles
        dead_mask = self.lifetimes[active_indices] <= 0
        dead_indices = active_indices[dead_mask]
        
        for idx in dead_indices:
            self.active[idx] = False
            self._free_indices.append(idx)
            self.active_particles -= 1
        
        # Update remaining active particles
        active_mask = self.active
        active_indices = np.where(active_mask)[0]
        
        if len(active_indices) == 0:
            return
        
        # Vectorized physics update
        self._update_physics(active_indices, dt)
        
        # Vectorized property updates
        self._update_properties(active_indices)
    
    def _update_physics(self, indices: np.ndarray, dt: float):
        """Update physics using vectorized NumPy operations"""
        # Apply gravity to vertical velocity
        self.velocities[indices, 1] += self.gravities[indices] * dt
        
        # Apply damping
        self.velocities[indices] *= self.dampings[indices]
        
        # Update positions
        self.positions[indices] += self.velocities[indices] * dt
    
    def _update_properties(self, indices: np.ndarray):
        """Update particle properties using vectorized operations"""
        # Calculate life ratio (0.0 to 1.0)
        life_ratios = 1.0 - (self.lifetimes[indices] / self.max_lifetimes[indices])
        
        # Update sizes for growing particles
        grow_mask = self.grows[indices]
        if np.any(grow_mask):
            grow_indices = indices[grow_mask]
            self.sizes[grow_indices] = (
                self.size_starts[grow_indices] + 
                (self.size_ends[grow_indices] - self.size_starts[grow_indices]) * 
                life_ratios[grow_mask]
            )
        
        # Update colors with interpolation
        self.colors_current[indices] = (
            self.colors_start[indices] + 
            (self.colors_end[indices] - self.colors_start[indices]) * 
            life_ratios[:, np.newaxis]
        ).astype(np.uint8)
    
    def render(self, surface: pygame.Surface):
        """
        Render all active particles to the target surface
        """
        if self.active_particles == 0:
            return
        
        active_indices = np.where(self.active)[0]
        
        for idx in active_indices:
            pos = self.positions[idx]
            size = int(max(1, self.sizes[idx]))  # Garantir tamanho mínimo
            color = tuple(self.colors_current[idx])
            life_ratio = 1.0 - (self.lifetimes[idx] / self.max_lifetimes[idx])
            
            # Handle fade out
            alpha = 255
            if self.fade_outs[idx]:
                alpha = int(255 * (1.0 - life_ratio))
            
            # Skip fully transparent particles
            if alpha <= 0:
                continue
            
            # DEBUG: Print para verificar se as partículas estão sendo processadas
            # print(f"Particle at {pos}, size: {size}, color: {color}, alpha: {alpha}")
            
            # Create surface for this particle (simples, sem cache por enquanto)
            try:
                particle_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                final_color = (*color, alpha)
                pygame.draw.circle(
                    particle_surface, 
                    final_color, 
                    (size // 2, size // 2), 
                    max(1, size // 2)  # Garantir raio mínimo
                )
                
                # Blit particle
                surface.blit(
                    particle_surface, 
                    (int(pos[0] - size // 2), int(pos[1] - size // 2))
                )
            except Exception as e:
                print(f"Error rendering particle: {e}")
                continue
    
    def clear(self):
        """Clear all particles and reset the system"""
        self.active.fill(False)
        self._free_indices = list(range(self.max_particles))
        self.active_particles = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics
        """
        return {
            'active_particles': self.active_particles,
            'max_particles': self.max_particles,
            'memory_usage_mb': (self.positions.nbytes + self.velocities.nbytes + 
                              self.lifetimes.nbytes + self.sizes.nbytes) / (1024 * 1024),
            'custom_particles_registered': len(self._custom_configs)
        }