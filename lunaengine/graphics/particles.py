"""
Particle System - Optimized Version
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Union
import math, pygame, warnings
from enum import Enum
from dataclasses import dataclass

class ParticleType(Enum):
    FIRE = "fire"
    WATER = "water" 
    SMOKE = "smoke"
    DUST = "dust"
    SPARK = "spark"
    SNOW = "snow"
    SAND = "sand"
    EXHAUST = "exhaust"
    STARFIELD = "starfield"
    EXPLOSION = "explosion"
    ENERGY = "energy"
    PLASMA = "plasma"
    CUSTOM = "custom"

class ExitPoint(Enum):
    TOP = "top"
    BOTTOM = "bottom" 
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    CIRCULAR = "circular"

class PhysicsType(Enum):
    TOPDOWN = "topdown"
    PLATFORMER = "platformer"
    SPACESHOOTER = "spaceshooter"

@dataclass
class ParticleConfig:
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
    """Particle System"""
    
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
        ),
        ParticleType.SNOW: ParticleConfig(
            color_start=(250, 250, 255),
            color_end=(225, 225, 235),
            size_start=3.0,
            size_end=1.0,
            lifetime=1.0,
            speed=50.0,
            gravity=100.0,
            spread=180.0,
            fade_out=True
        ),
        ParticleType.SAND: ParticleConfig(
            color_start=(230, 230, 0),
            color_end=(255, 255, 0),
            size_start=1.0,
            size_end=1.0,
            lifetime=5.0,
            speed=200.0,
            gravity=100.0,
            spread=180.0,
            fade_out=True
        ),
        ParticleType.EXHAUST: ParticleConfig(
            color_start=(0, 100, 255),
            color_end=(255, 50, 0),
            size_start=4.0,
            size_end=1.0,
            lifetime=0.3,
            speed=100.0,
            gravity=0.0,
            spread=30.0,
            fade_out=True,
            grow=False
        ),
        ParticleType.EXPLOSION: ParticleConfig(
            color_start=(255, 200, 0),
            color_end=(255, 50, 0),
            size_start=10.0,
            size_end=2.0,
            lifetime=1.0,
            speed=300.0,
            gravity=0.0,
            spread=360.0,
            fade_out=True,
            grow=False
        ),
        ParticleType.ENERGY: ParticleConfig(
            color_start=(0, 255, 255),
            color_end=(0, 100, 255),
            size_start=6.0,
            size_end=2.0,
            lifetime=1.2,
            speed=150.0,
            gravity=0.0,
            spread=90.0,
            fade_out=True,
            grow=False
        ),
        ParticleType.PLASMA: ParticleConfig(
            color_start=(255, 0, 255),
            color_end=(100, 0, 255),
            size_start=5.0,
            size_end=1.0,
            lifetime=0.8,
            speed=250.0,
            gravity=0.0,
            spread=45.0,
            fade_out=True,
            grow=False
        )
    }
    
    def __init__(self, max_particles: int):
        self.max_particles = max_particles
        self.active_particles = 0
        
        # Pre-allocate NumPy arrays
        self._init_arrays()
        
        # Object pooling
        self._free_indices = list(range(self.max_particles))
        self._custom_configs: Dict[str, ParticleConfig] = {}
        
        # Pre-computed values
        self._pi_2 = 2.0 * math.pi
        self._deg_to_rad = math.pi / 180.0
        
        # Render cache
        self._render_cache = None
        self._cache_dirty = True
        
        # Camera Support
        self._camera_position = np.array([0.0,0.0], dtype=np.float32)
        
    def get_particles_names(self, sort_name:bool=False, capitalize:bool=False) -> List[str]:
        """Get list of all registered particle names"""
        p = list(self.PARTICLE_CONFIGS.keys() | self._custom_configs.keys())
        if sort_name:
            p.sort(key=lambda x: x.name)
        return [(str(x.name).capitalize() if capitalize else str(x.name)) for x in p]
    
    def get_physics_names(self, sort_name:bool=False, capitalize:bool=False) -> List[str]:
        """
        Get a list of physics names
        """
        p = list(PhysicsType.__dict__['_member_names_'])
        if sort_name:
            p.sort(key=lambda x: x)
        return [(str(x).capitalize() if capitalize else str(x)) for x in p]

    def update_max_particles(self, value: int):
        """
        Callback for the renderer update max_particles.
        Preserves active particles during resize.
        """
        if value == self.max_particles:
            return
        
        
        # Save current active particles state
        active_indices = np.where(self.active)[0]
        active_count = len(active_indices)
        
        if active_count > value:
            # Kill oldest particles first
            kill_count = active_count - value
            kill_indices = active_indices[:kill_count]
            self.active[kill_indices] = False
            active_indices = active_indices[kill_count:]
            active_count = len(active_indices)
        
        # Create temporary arrays to save active particle data
        temp_data = {}
        if active_count > 0:
            arrays_to_save = [
                'positions', 'velocities', 'lifetimes', 'max_lifetimes',
                'sizes', 'size_starts', 'size_ends', 'colors_start',
                'colors_end', 'colors_current', 'alphas', 'gravities',
                'dampings', 'fade_outs', 'grows'
            ]
            
            for array_name in arrays_to_save:
                array = getattr(self, array_name)
                temp_data[array_name] = array[active_indices].copy()
        
        # Update max size
        self.max_particles = value
        
        # Re-initialize arrays with new size
        self._init_arrays()
        
        # Restore active particles to new arrays
        if active_count > 0:
            # Active particles will occupy the first indices
            new_active_indices = np.arange(active_count)
            
            for array_name, data in temp_data.items():
                array = getattr(self, array_name)
                array[new_active_indices] = data
            
            # Mark as active
            self.active[new_active_indices] = True
            
            # Update counter and free indices list
            self.active_particles = active_count
            self._free_indices = list(range(active_count, self.max_particles))
            
        else:
            # No active particles, just reset
            self.active_particles = 0
            self._free_indices = list(range(self.max_particles))
        
        # Mark cache as dirty
        self._cache_dirty = True
    
    def _init_arrays(self):
        """Initialize optimized NumPy arrays using current max_particles"""
        # Position and velocity
        self.positions = np.zeros((self.max_particles, 2), dtype=np.float32)
        self.velocities = np.zeros((self.max_particles, 2), dtype=np.float32)
        
        # Particle properties
        self.lifetimes = np.zeros(self.max_particles, dtype=np.float32)
        self.max_lifetimes = np.zeros(self.max_particles, dtype=np.float32)
        self.sizes = np.zeros(self.max_particles, dtype=np.float32)
        self.size_starts = np.zeros(self.max_particles, dtype=np.float32)
        self.size_ends = np.zeros(self.max_particles, dtype=np.float32)
        
        # Color data
        self.colors_start = np.zeros((self.max_particles, 3), dtype=np.uint8)
        self.colors_end = np.zeros((self.max_particles, 3), dtype=np.uint8)
        self.colors_current = np.zeros((self.max_particles, 3), dtype=np.uint8)
        
        # Alpha/transparency
        self.alphas = np.full(self.max_particles, 255, dtype=np.uint8)
        
        # Physics properties
        self.gravities = np.zeros(self.max_particles, dtype=np.float32)
        self.dampings = np.full((self.max_particles, 2), 0.98, dtype=np.float32)
        
        # State flags
        self.active = np.zeros(self.max_particles, dtype=bool)
        self.fade_outs = np.zeros(self.max_particles, dtype=bool)
        self.grows = np.zeros(self.max_particles, dtype=bool)

    def register_custom_particle(self, name: str, config: ParticleConfig) -> bool:
        """
        Register a custom particle type for user-defined effects
        
        Args:
            name (str): Unique name for the custom particle type
            config (ParticleConfig): Configuration for the custom particle
            
        Returns:
            bool: True if registration was successful
            
        Raises:
            ValueError: If particle name is already registered
        """
        if name in self._custom_configs:
            raise ValueError(f"Custom particle '{name}' is already registered")
        
        # Validate the name doesn't conflict with built-in types
        try:
            ParticleType(name)  # This will raise ValueError if name is not a built-in
            raise ValueError(f"Particle name '{name}' conflicts with built-in particle type")
        except ValueError:
            # Name is not a built-in type, so it's valid for custom registration
            pass
        
        self._custom_configs[name] = config
        print(f"Registered custom particle: '{name}'")
        return True

    def get_custom_particle(self, name: str) -> Optional[ParticleConfig]:
        """
        Get configuration for a custom particle
        
        Args:
            name (str): Name of the custom particle type
            
        Returns:
            Optional[ParticleConfig]: The particle configuration or None if not found
        """
        return self._custom_configs.get(name)

    def list_custom_particles(self) -> List[str]:
        """
        Get list of all registered custom particle names
        
        Returns:
            List[str]: List of custom particle names
        """
        return list(self._custom_configs.keys())
    
    def get_render_data(self) -> Dict[str, Any]:
        """Get particle data for rendering with caching"""
        if self.active_particles == 0:
            return {
                'active_count': 0,
                'positions': np.array([], dtype=np.float32),
                'sizes': np.array([], dtype=np.float32),
                'colors': np.array([], dtype=np.uint8),
                'alphas': np.array([], dtype=np.uint8)
            }
        
        # Use cache if available and not dirty
        if not self._cache_dirty and self._render_cache is not None:
            return self._render_cache
        
        active_indices = np.where(self.active)[0]
        
        self._render_cache = {
            'active_count': len(active_indices),
            'positions': self.positions[active_indices],
            'sizes': self.sizes[active_indices],
            'colors': self.colors_current[active_indices],
            'alphas': self.alphas[active_indices]
        }
        
        self._cache_dirty = False
        return self._render_cache
    
    def _resolve_particle_config(
        self, 
        particle_type: Union[ParticleType, str], 
        custom_config: Optional[ParticleConfig]
    ) -> Optional[ParticleConfig]:
        """
        Resolve particle configuration from various sources
        
        Args:
            particle_type: The particle type identifier
            custom_config: Optional custom configuration
            
        Returns:
            ParticleConfig or None if not found
        """
        # If custom config provided directly, use it
        if custom_config:
            return custom_config
        
        # Handle ParticleType enum
        if isinstance(particle_type, ParticleType):
            return self.PARTICLE_CONFIGS.get(particle_type)
        
        # Handle string type
        elif isinstance(particle_type, str):
            # First try to convert string to ParticleType enum
            try:
                particle_enum = ParticleType(particle_type)
                return self.PARTICLE_CONFIGS.get(particle_enum)
            except ValueError:
                # If not a built-in type, try custom particles
                if particle_type in self._custom_configs:
                    return self._custom_configs[particle_type]
                else:
                    # Try case-insensitive match
                    for custom_name in self._custom_configs.keys():
                        if custom_name.lower() == particle_type.lower():
                            return self._custom_configs[custom_name]
        
        # Return None if not found
        return None
    
    def _get_exit_offset(self, exit_point: ExitPoint) -> float:
        """Get offset distance for exit points"""
        return 10.0  # Fixed offset distance

    def _get_exit_position(self, x: float, y: float, exit_point: ExitPoint, offset: float) -> Tuple[float, float]:
        """
        Calculate initial position based on exit point
        """
        if exit_point == ExitPoint.CENTER:
            return x, y
        elif exit_point == ExitPoint.TOP:
            return x, y - offset  # TOP emits upward
        elif exit_point == ExitPoint.BOTTOM:
            return x, y + offset  # BOTTOM emits downward
        elif exit_point == ExitPoint.LEFT:
            return x - offset, y  # LEFT emits leftward
        elif exit_point == ExitPoint.RIGHT:
            return x + offset, y  # RIGHT emits rightward
        elif exit_point == ExitPoint.CIRCULAR:
            angle = np.random.uniform(0, self._pi_2)
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
            exit_angle = 270  # Upward (0° is right, 90° is down, 270° is up)
        elif exit_point == ExitPoint.BOTTOM:
            exit_angle = 90   # Downward
        elif exit_point == ExitPoint.LEFT:
            exit_angle = 180  # Leftward
        elif exit_point == ExitPoint.RIGHT:
            exit_angle = 0    # Rightward
        else:
            exit_angle = base_angle
        
        # Apply spread randomization
        spread_rad = spread * self._deg_to_rad
        final_angle = exit_angle + np.random.uniform(-spread/2, spread/2)
        angle_rad = math.radians(final_angle)
        
        # Random speed variation for natural look
        actual_speed = speed * np.random.uniform(0.8, 1.2)
        
        return (
            math.cos(angle_rad) * actual_speed,
            math.sin(angle_rad) * actual_speed
        )
    
    def emit(self, x: float, y: float, particle_type: Union[ParticleType, str], count: int = 1, exit_point: ExitPoint = ExitPoint.CENTER, physics_type: PhysicsType = PhysicsType.TOPDOWN, spread: Optional[float] = None, angle: float = 0.0, custom_config: Optional[ParticleConfig] = None):
        """
        Emit particles with optimizations
        
        Parameters:
            x: The x position of the emitter (int or float)
            y: The y position of the emitter (int or float)
            particle_type: The particle type identifier
            count: The number of particles to emit (default: 1)
            exit_point: The exit point of the particle (default: ExitPoint.CENTER)
            physics_type: The physics type of the particle (default: PhysicsType.TOPDOWN)
            spread: The spread of the particle (default: None) is in degrees
            angle: The angle of the particle (default: 0.0)
            custom_config: Optional custom configuration
        """
        config = self._resolve_particle_config(particle_type, custom_config)
        if not config:
            return
        
        actual_spread = spread if spread is not None else config.spread
        exit_offset = self._get_exit_offset(exit_point)
        
        # Limit emission rate to prevent overload
        count = min(count, 100)  # Maximum 100 particles per emission
        
        for _ in range(count):
            if not self._free_indices:
                break
                
            idx = self._free_indices.pop()
            self.active_particles += 1
            self._cache_dirty = True  # Mark cache as dirty
            
            # Set initial position
            pos_x, pos_y = self._get_exit_position(x, y, exit_point, exit_offset)
            self.positions[idx] = [pos_x, pos_y]
            
            # Set velocity
            vel_x, vel_y = self._get_initial_velocity(
                exit_point, config.speed, actual_spread, angle
            )
            self.velocities[idx] = [vel_x, vel_y]
            
            # Set particle properties
            self._setup_particle_properties(idx, config, physics_type)
    
    def _setup_particle_properties(self, idx: int, config: ParticleConfig, physics_type: PhysicsType):
        """
        Setup particle properties optimized for different physics types
        """
        self.lifetimes[idx] = config.lifetime
        self.max_lifetimes[idx] = config.lifetime
        self.sizes[idx] = config.size_start
        self.size_starts[idx] = config.size_start
        self.size_ends[idx] = config.size_end
        
        self.colors_start[idx] = config.color_start
        self.colors_end[idx] = config.color_end
        self.colors_current[idx] = config.color_start
        
        self.alphas[idx] = 255
        
        # Physics-specific configurations
        if physics_type == PhysicsType.PLATFORMER:
            # Platformer physics: stronger gravity, more damping
            self.gravities[idx] = config.gravity * 1.5
            self.dampings[idx] = [0.95, 0.95]  # More air resistance
            
        elif physics_type == PhysicsType.SPACESHOOTER:
            # Space shooter physics: zero gravity, minimal damping
            self.gravities[idx] = 0.0  # No gravity in space
            self.dampings[idx] = [0.99, 0.99]  # Minimal friction in vacuum
            
        else:  # TOPDOWN (default)
            # Topdown physics: standard gravity and damping
            self.gravities[idx] = config.gravity
            self.dampings[idx] = [config.damping, config.damping]
        
        self.active[idx] = True
        self.fade_outs[idx] = config.fade_out
        self.grows[idx] = config.grow
    
    def update(self, dt: float, camera_position=None):
        """Update particles with vectorized operations"""
        if camera_position is not None:
            self._camera_position = camera_position
        if self.active_particles == 0:
            return
        
        active_indices = np.where(self.active)[0]
        
        if len(active_indices) == 0:
            return
        
        # Update lifetimes
        self.lifetimes[active_indices] -= dt
        
        # Kill dead particles
        dead_mask = self.lifetimes[active_indices] <= 0
        dead_indices = active_indices[dead_mask]
        
        if len(dead_indices) > 0:
            self.active[dead_indices] = False
            self._free_indices.extend(dead_indices)
            self.active_particles -= len(dead_indices)
            self._cache_dirty = True
            
            active_indices = active_indices[~dead_mask]
        
        if len(active_indices) == 0:
            return
        
        # Vectorized physics update
        self.velocities[active_indices, 1] += self.gravities[active_indices] * dt
        self.velocities[active_indices] *= self.dampings[active_indices]
        self.positions[active_indices] += self.velocities[active_indices] * dt
        
        # Vectorized property updates
        self._update_properties(active_indices)
    
    def _update_properties(self, indices: np.ndarray):
        """Update particle properties using vectorized operations - FIXED COLOR BUG"""
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
        
        # FIXED COLOR TRANSITION BUG - Use proper interpolation
        # Convert to float for accurate interpolation, then back to uint8
        colors_start_float = self.colors_start[indices].astype(np.float32)
        colors_end_float = self.colors_end[indices].astype(np.float32)
        
        # Proper color interpolation
        interpolated_colors = colors_start_float + (colors_end_float - colors_start_float) * life_ratios[:, np.newaxis]
        
        # Clamp to valid color range and convert back to uint8
        self.colors_current[indices] = np.clip(interpolated_colors, 0, 255).astype(np.uint8)
        
        # Update alpha for fade out
        fade_mask = self.fade_outs[indices]
        if np.any(fade_mask):
            fade_indices = indices[fade_mask]
            self.alphas[fade_indices] = (255 * (1.0 - life_ratios[fade_mask])).astype(np.uint8)
        
        self._cache_dirty = True
    
    def clear(self):
        """Clear all particles"""
        self.active.fill(False)
        self._free_indices = list(range(self.max_particles))
        self.active_particles = 0
        self._cache_dirty = True
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive system statistics
        
        Returns:
            Dict with system statistics
        """
        total_memory = (
            self.positions.nbytes + 
            self.velocities.nbytes + 
            self.lifetimes.nbytes + 
            self.max_lifetimes.nbytes +
            self.sizes.nbytes +
            self.size_starts.nbytes +
            self.size_ends.nbytes +
            self.colors_start.nbytes +
            self.colors_end.nbytes +
            self.colors_current.nbytes +
            self.alphas.nbytes +
            self.gravities.nbytes +
            self.dampings.nbytes +
            self.active.nbytes +
            self.fade_outs.nbytes +
            self.grows.nbytes
        )
        
        return {
            'active_particles': self.active_particles,
            'max_particles': self.max_particles,
            'memory_usage_mb': total_memory / (1024 * 1024),
            'free_slots': len(self._free_indices),
            'custom_particles_registered': len(self._custom_configs),
            'cache_dirty': self._cache_dirty
        }