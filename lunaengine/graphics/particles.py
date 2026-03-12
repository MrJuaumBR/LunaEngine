"""
Particle System - CPU-based with threaded physics and renderer integration
v0.2.3
"""

import numpy as np
import math, threading, time, pygame
from typing import Dict, Any, List, Tuple, Optional, Union
from enum import Enum
from dataclasses import dataclass

# ----------------------------------------------------------------------
# Enums (same as before)
# ----------------------------------------------------------------------

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
    ANTIMATTER = "antimatter"
    RADIOACTIVE = "radioactive"
    MAGIC = "magic"           
    BUBBLE = "bubble"         
    LEAF = "leaf"             
    RAIN = "rain"             
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

# ----------------------------------------------------------------------
# Particle Configuration
# ----------------------------------------------------------------------

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

# Built‑in configurations (identical to before)
PARTICLE_CONFIGS: Dict[ParticleType, ParticleConfig] = {
    ParticleType.FIRE: ParticleConfig(
        color_start=(255, 100, 0),
        color_end=(255, 255, 0),
        size_start=28.0,
        size_end=20.0,
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
    ),
     ParticleType.ANTIMATTER: ParticleConfig(
        color_start=(180, 0, 255),       
        color_end=(50, 0,  90),       
        size_start=10.0,
        size_end=2.0,
        lifetime=1.2,
        speed=250.0,
        gravity=-50.0,                   
        spread=360.0,
        fade_out=True,
        grow=False,
        damping=0.95
    ),
    ParticleType.RADIOACTIVE: ParticleConfig(
        color_start=(0, 255, 0),         
        color_end=(255, 255, 0),        
        size_start=6.0,
        size_end=12.0,                    
        lifetime=2.5,
        speed=60.0,
        gravity=0.0,
        spread=360.0,
        fade_out=True,
        grow=True,
        damping=0.98
    ),
    ParticleType.MAGIC: ParticleConfig(
        color_start=(255, 0, 255),       
        color_end=(0, 255, 255),         
        size_start=5.0,
        size_end=1.0,
        lifetime=1.0,
        speed=150.0,
        gravity=-50.0,                    
        spread=180.0,
        fade_out=True,
        grow=False,
        damping=0.96
    ),
    ParticleType.BUBBLE: ParticleConfig(
        color_start=(200, 255, 255),      
        color_end=(255, 255, 255),       
        size_start=10.0,
        size_end=15.0,                    
        lifetime=3.0,
        speed=20.0,
        gravity=-10.0,                    
        spread=360.0,
        fade_out=True,
        grow=True,
        damping=0.99
    ),
    ParticleType.LEAF: ParticleConfig(
        color_start=(139, 69, 19),        
        color_end=(34, 139, 34),          
        size_start=4.0,
        size_end=4.0,
        lifetime=5.0,
        speed=30.0,
        gravity=50.0,
        spread=180.0,
        fade_out=False,
        grow=False,
        damping=0.99
    ),
    ParticleType.RAIN: ParticleConfig(
        color_start=(0, 100, 255),        
        color_end=(173, 216, 230),        
        size_start=2.0,
        size_end=2.0,
        lifetime=1.5,
        speed=400.0,
        gravity=500.0,
        spread=10.0,
        fade_out=False,
        grow=False,
        damping=0.95
    )
}

# ----------------------------------------------------------------------
# Core Particle System (CPU, single‑threaded)
# ----------------------------------------------------------------------

class ParticleSystem:
    """
    CPU-based particle system using NumPy arrays.
    All physics updates happen when you call update().
    """

    def __init__(self, max_particles: int):
        self.max_particles = max_particles
        self.active_particles = 0

        # Pre‑allocate NumPy arrays
        self._init_arrays()

        # Free list for fast particle allocation
        self._free_indices = list(range(self.max_particles))

        # Custom particle configurations
        self._custom_configs: Dict[str, ParticleConfig] = {}

        # Pre‑computed constants
        self._pi_2 = 2.0 * math.pi
        self._deg_to_rad = math.pi / 180.0

        # Render cache
        self._render_cache = None
        self._cache_dirty = True

    def _init_arrays(self):
        """(Re)initialise all particle arrays to zero size."""
        n = self.max_particles
        self.positions = np.zeros((n, 2), dtype=np.float32)
        self.velocities = np.zeros((n, 2), dtype=np.float32)
        self.lifetimes = np.zeros(n, dtype=np.float32)
        self.max_lifetimes = np.zeros(n, dtype=np.float32)
        self.sizes = np.zeros(n, dtype=np.float32)
        self.size_starts = np.zeros(n, dtype=np.float32)
        self.size_ends = np.zeros(n, dtype=np.float32)
        self.colors_start = np.zeros((n, 3), dtype=np.uint8)
        self.colors_end = np.zeros((n, 3), dtype=np.uint8)
        self.colors_current = np.zeros((n, 3), dtype=np.uint8)
        self.alphas = np.full(n, 255, dtype=np.uint8)
        self.gravities = np.zeros(n, dtype=np.float32)
        self.dampings = np.full((n, 2), 0.98, dtype=np.float32)
        self.active = np.zeros(n, dtype=bool)
        self.fade_outs = np.zeros(n, dtype=bool)
        self.grows = np.zeros(n, dtype=bool)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_particles_names(self, sort_name: bool = False, capitalize: bool = False) -> List[str]:
        names = [t.value for t in ParticleType] + list(self._custom_configs.keys())
        if sort_name:
            names.sort()
        if capitalize:
            names = [n.capitalize() for n in names]
        return names

    def get_physics_names(self, sort_name: bool = False, capitalize: bool = False) -> List[str]:
        names = [p.value for p in PhysicsType]
        if sort_name:
            names.sort()
        if capitalize:
            names = [n.capitalize() for n in names]
        return names

    def register_custom_particle(self, name: str, config: ParticleConfig):
        if name in self._custom_configs:
            raise ValueError(f"Custom particle '{name}' already exists")
        self._custom_configs[name] = config

    def get_custom_particle(self, name: str) -> Optional[ParticleConfig]:
        return self._custom_configs.get(name)

    def list_custom_particles(self) -> List[str]:
        return list(self._custom_configs.keys())

    def update_max_particles(self, new_max: int):
        """Resize internal arrays, preserving active particles."""
        if new_max == self.max_particles:
            return

        # Save currently active particles
        active_indices = np.where(self.active)[0]
        active_count = len(active_indices)

        if active_count > new_max:
            # Kill oldest particles
            kill_count = active_count - new_max
            kill_indices = active_indices[:kill_count]
            self.active[kill_indices] = False
            active_indices = active_indices[kill_count:]
            active_count = len(active_indices)

        # Backup data of surviving particles
        temp_data = {}
        if active_count > 0:
            arrays = [
                'positions', 'velocities', 'lifetimes', 'max_lifetimes',
                'sizes', 'size_starts', 'size_ends', 'colors_start',
                'colors_end', 'colors_current', 'alphas', 'gravities',
                'dampings', 'fade_outs', 'grows'
            ]
            for name in arrays:
                temp_data[name] = getattr(self, name)[active_indices].copy()

        self.max_particles = new_max
        self._init_arrays()

        if active_count > 0:
            # Restore active particles at the beginning of new arrays
            new_indices = np.arange(active_count)
            for name, data in temp_data.items():
                getattr(self, name)[new_indices] = data
            self.active[new_indices] = True
            self.active_particles = active_count
            self._free_indices = list(range(active_count, self.max_particles))
        else:
            self.active_particles = 0
            self._free_indices = list(range(self.max_particles))

        self._cache_dirty = True

    def get_render_data(self) -> Dict[str, Any]:
        """Return a copy of active particle data for rendering."""
        if self.active_particles == 0:
            return {
                'active_count': 0,
                'positions': np.array([], dtype=np.float32),
                'sizes': np.array([], dtype=np.float32),
                'colors': np.array([], dtype=np.uint8),
                'alphas': np.array([], dtype=np.uint8)
            }

        # Use cache if still valid
        if not self._cache_dirty and self._render_cache is not None:
            return self._render_cache

        active_indices = np.where(self.active)[0]

        self._render_cache = {
            'active_count': len(active_indices),
            'positions': self.positions[active_indices].copy(),
            'sizes': self.sizes[active_indices].copy(),
            'colors': self.colors_current[active_indices].copy(),
            'alphas': self.alphas[active_indices].copy()
        }

        self._cache_dirty = False
        return self._render_cache

    def emit(self,
             x: float, y: float,
             particle_type: Union[ParticleType, str],
             count: int = 1,
             exit_point: ExitPoint = ExitPoint.CENTER,
             physics_type: PhysicsType = PhysicsType.TOPDOWN,
             spread: Optional[float] = None,
             angle: float = 0.0,
             custom_config: Optional[ParticleConfig] = None):
        """Emit new particles."""
        config = self._resolve_config(particle_type, custom_config)
        if not config:
            return

        actual_spread = spread if spread is not None else config.spread
        exit_offset = 10.0

        # Apply physics modifiers
        if physics_type == PhysicsType.PLATFORMER:
            gravity = config.gravity * 1.5
            damping = 0.95
        elif physics_type == PhysicsType.SPACESHOOTER:
            gravity = 0.0
            damping = 0.99
        else:  # TOPDOWN
            gravity = config.gravity
            damping = config.damping

        # Limit emission to avoid overload
        count = min(count, 100, len(self._free_indices))

        for _ in range(count):
            if not self._free_indices:
                break
            idx = self._free_indices.pop()
            self.active_particles += 1
            self._cache_dirty = True

            # Position
            pos_x, pos_y = self._get_exit_position(x, y, exit_point, exit_offset)
            self.positions[idx] = (pos_x, pos_y)

            # Velocity
            vel_x, vel_y = self._get_initial_velocity(
                config, exit_point, actual_spread, angle
            )
            self.velocities[idx] = (vel_x, vel_y)

            # Lifetime
            self.lifetimes[idx] = config.lifetime
            self.max_lifetimes[idx] = config.lifetime

            # Size
            self.sizes[idx] = config.size_start
            self.size_starts[idx] = config.size_start
            self.size_ends[idx] = config.size_end

            # Color
            self.colors_start[idx] = config.color_start
            self.colors_end[idx] = config.color_end
            self.colors_current[idx] = config.color_start
            self.alphas[idx] = 255

            # Physics
            self.gravities[idx] = gravity
            self.dampings[idx] = (damping, damping)
            self.fade_outs[idx] = config.fade_out
            self.grows[idx] = config.grow

            self.active[idx] = True

    def update(self, dt: float):
        """Update particle physics (called from main thread in single‑threaded mode)."""
        if self.active_particles == 0:
            return

        active_indices = np.where(self.active)[0]
        if len(active_indices) == 0:
            return

        # Age particles
        self.lifetimes[active_indices] -= dt

        # Remove dead ones
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

        # Physics: gravity and damping
        self.velocities[active_indices, 1] += self.gravities[active_indices] * dt
        self.velocities[active_indices] *= self.dampings[active_indices]
        self.positions[active_indices] += self.velocities[active_indices] * dt

        # Update size and color
        self._update_properties(active_indices)

    def clear(self):
        """Deactivate all particles."""
        self.active.fill(False)
        self._free_indices = list(range(self.max_particles))
        self.active_particles = 0
        self._cache_dirty = True

    def get_stats(self) -> Dict[str, Any]:
        total_memory = sum(
            arr.nbytes for arr in [
                self.positions, self.velocities, self.lifetimes, self.max_lifetimes,
                self.sizes, self.size_starts, self.size_ends, self.colors_start,
                self.colors_end, self.colors_current, self.alphas, self.gravities,
                self.dampings, self.active, self.fade_outs, self.grows
            ]
        )
        return {
            'active_particles': self.active_particles,
            'max_particles': self.max_particles,
            'memory_usage_mb': total_memory / (1024 * 1024),
            'free_slots': len(self._free_indices),
            'custom_particles_registered': len(self._custom_configs)
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_config(self, particle_type: Union[ParticleType, str],
                        custom_config: Optional[ParticleConfig]) -> Optional[ParticleConfig]:
        if custom_config:
            return custom_config
        if isinstance(particle_type, ParticleType):
            return PARTICLE_CONFIGS.get(particle_type)
        if isinstance(particle_type, str):
            try:
                enum_type = ParticleType(particle_type)
                return PARTICLE_CONFIGS.get(enum_type)
            except ValueError:
                return self._custom_configs.get(particle_type)
        return None

    def _get_exit_position(self, x: float, y: float,
                           exit_point: ExitPoint,
                           offset: float) -> Tuple[float, float]:
        if exit_point == ExitPoint.CENTER:
            return x, y
        elif exit_point == ExitPoint.TOP:
            return x, y - offset
        elif exit_point == ExitPoint.BOTTOM:
            return x, y + offset
        elif exit_point == ExitPoint.LEFT:
            return x - offset, y
        elif exit_point == ExitPoint.RIGHT:
            return x + offset, y
        elif exit_point == ExitPoint.CIRCULAR:
            angle = np.random.uniform(0, self._pi_2)
            radius = np.random.uniform(5, 15)
            return x + math.cos(angle) * radius, y + math.sin(angle) * radius
        return x, y

    def _get_initial_velocity(self,
                              config: ParticleConfig,
                              exit_point: ExitPoint,
                              spread: float,
                              base_angle: float) -> Tuple[float, float]:
        if exit_point == ExitPoint.TOP:
            exit_angle = 270
        elif exit_point == ExitPoint.BOTTOM:
            exit_angle = 90
        elif exit_point == ExitPoint.LEFT:
            exit_angle = 180
        elif exit_point == ExitPoint.RIGHT:
            exit_angle = 0
        else:
            exit_angle = base_angle

        spread_rad = spread * self._deg_to_rad
        final_angle = exit_angle + np.random.uniform(-spread/2, spread/2)
        angle_rad = math.radians(final_angle)
        speed = config.speed * np.random.uniform(0.8, 1.2)
        return (math.cos(angle_rad) * speed, math.sin(angle_rad) * speed)

    def _update_properties(self, indices: np.ndarray):
        """Update particle color and size based on remaining life."""
        life_ratios = 1.0 - (self.lifetimes[indices] / self.max_lifetimes[indices])

        # Size for growing particles
        grow_mask = self.grows[indices]
        if np.any(grow_mask):
            grow_idx = indices[grow_mask]
            ratio = life_ratios[grow_mask]
            self.sizes[grow_idx] = (
                self.size_starts[grow_idx] +
                (self.size_ends[grow_idx] - self.size_starts[grow_idx]) * ratio
            )

        # Color interpolation (fixed: use float math)
        cs = self.colors_start[indices].astype(np.float32)
        ce = self.colors_end[indices].astype(np.float32)
        interp = cs + (ce - cs) * life_ratios[:, np.newaxis]
        self.colors_current[indices] = np.clip(interp, 0, 255).astype(np.uint8)

        # Alpha for fade‑out
        fade_mask = self.fade_outs[indices]
        if np.any(fade_mask):
            fade_idx = indices[fade_mask]
            self.alphas[fade_idx] = (255 * (1.0 - life_ratios[fade_mask])).astype(np.uint8)

        self._cache_dirty = True


# ----------------------------------------------------------------------
# Threaded Particle System (physics runs in background)
# ----------------------------------------------------------------------

class ThreadedParticleSystem(ParticleSystem):
    """
    ParticleSystem variant that updates physics in a separate thread.
    The main thread's update() call becomes a no‑op – the thread runs
    continuously at a fixed timestep.

    Also provides a render(camera) method that uses the renderer passed
    during construction, making it a drop‑in replacement for the old
    GPUParticleSystem.
    """

    def __init__(self, renderer, max_particles: int, target_fps: int = 60, auto_start: bool = True):
        super().__init__(max_particles)
        self.renderer = renderer
        self.target_fps = target_fps
        self._lock = threading.Lock()
        self._thread = None
        self._running = False
        self._dt_fixed = 1.0 / target_fps

        if auto_start:
            self.start_thread()

    def start_thread(self):
        """Start the background physics thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._thread_loop, daemon=True)
        self._thread.start()

    def stop_thread(self, join: bool = True):
        """Stop the background thread."""
        self._running = False
        if join and self._thread is not None:
            self._thread.join(timeout=1.0)
        self._thread = None

    def _thread_loop(self):
        """Thread main loop: run physics at fixed timestep."""
        clock = pygame.time.Clock()
        while self._running:
            dt = clock.tick(self.target_fps) / 1000.0
            with self._lock:
                super().update(dt)
            time.sleep(0.001)

    # Override methods that modify arrays to acquire the lock

    def update(self, dt: float):
        """In threaded mode, do nothing (thread handles updates)."""
        pass

    def emit(self, *args, **kwargs):
        with self._lock:
            super().emit(*args, **kwargs)

    def clear(self):
        with self._lock:
            super().clear()

    def update_max_particles(self, new_max: int):
        """Stop thread, resize, then restart."""
        self.stop_thread(join=True)
        with self._lock:
            super().update_max_particles(new_max)
        if self._running:
            self.start_thread()

    def get_render_data(self) -> Dict[str, Any]:
        """Return a copy of data while holding the lock."""
        with self._lock:
            return super().get_render_data()

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return super().get_stats()

    def render(self, camera):
        """
        Render all active particles using the stored renderer.
        This method matches the interface expected by the engine.
        """
        data = self.get_render_data()
        if data['active_count'] > 0:
            self.renderer.render_particles(data, camera)

    def __del__(self):
        self.stop_thread(join=False)