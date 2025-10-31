"""
Particle System - Dynamic Visual Effects and Emitters

LOCATION: lunaengine/graphics/particles.py

DESCRIPTION:
Comprehensive particle system for creating dynamic visual effects like
fire, smoke, magic spells, explosions, and environmental effects. Supports
multiple emitters with configurable particle properties and behaviors.

KEY FEATURES:
- Individual particle management with physics simulation
- Configurable emitters with emission rates and timing
- Particle properties: velocity, lifetime, color, size, rotation
- Smooth alpha blending and life-based fading
- Efficient particle pooling and lifecycle management

LIBRARIES USED:
- pygame: Particle rendering and surface operations
- numpy: Mathematical operations for particle physics
- random: Randomization of particle properties
- math: Trigonometric functions for particle movement
- typing: Type hints for particle parameters and collections

USAGE:
>>> emitter = ParticleEmitter(400, 300)
>>> emitter.emission_rate = 20
>>> particle_system = ParticleSystem()
>>> particle_system.add_emitter(emitter)
>>> particle_system.update(delta_time)
>>> particle_system.draw(screen_surface)
"""
import pygame, random, math
import numpy as np
from typing import List, Tuple, Optional

class Particle:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.life = 1.0
        self.max_life = 1.0
        self.color = (255, 255, 255)
        self.size = 4.0
        self.rotation = 0.0
        self.angular_velocity = 0.0
        
    def update(self, dt: float):
        """Update particle position and state"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt / self.max_life
        self.rotation += self.angular_velocity * dt
        
    def is_alive(self) -> bool:
        """Check if particle is still alive"""
        return self.life > 0

class ParticleEmitter:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.particles = []
        self.emission_rate = 10  # particles per second
        self.emission_timer = 0.0
        self.active = True
        
        # Particle properties
        self.min_lifetime = 1.0
        self.max_lifetime = 3.0
        self.min_speed = 50.0
        self.max_speed = 150.0
        self.min_size = 2.0
        self.max_size = 8.0
        self.colors = [(255, 100, 100), (255, 255, 100), (100, 255, 100)]
        
    def update(self, dt: float):
        """Update emitter and all particles"""
        # Emit new particles
        if self.active:
            self.emission_timer += dt
            particles_to_emit = int(self.emission_rate * self.emission_timer)
            
            for _ in range(particles_to_emit):
                self.emit_particle()
                
            self.emission_timer -= particles_to_emit / self.emission_rate
        
        # Update existing particles
        for particle in self.particles[:]:
            particle.update(dt)
            if not particle.is_alive():
                self.particles.remove(particle)
                
    def emit_particle(self):
        """Emit a new particle"""
        particle = Particle(self.x, self.y)
        
        # Randomize properties
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(self.min_speed, self.max_speed)
        particle.vx = math.cos(angle) * speed
        particle.vy = math.sin(angle) * speed
        
        particle.max_life = random.uniform(self.min_lifetime, self.max_lifetime)
        particle.life = particle.max_life
        particle.size = random.uniform(self.min_size, self.max_size)
        particle.color = random.choice(self.colors)
        particle.angular_velocity = random.uniform(-180, 180)
        
        self.particles.append(particle)
        
    def draw(self, surface: pygame.Surface):
        """Draw all particles"""
        for particle in self.particles:
            if particle.is_alive():
                # Calculate alpha based on life
                alpha = int(255 * particle.life)
                color = (*particle.color, alpha)
                
                # Create a surface for the particle
                particle_surface = pygame.Surface((int(particle.size), int(particle.size)), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color, 
                                 (int(particle.size//2), int(particle.size//2)), 
                                 int(particle.size//2))
                
                # Draw the particle
                surface.blit(particle_surface, 
                           (int(particle.x - particle.size//2), 
                            int(particle.y - particle.size//2)))

class ParticleSystem:
    def __init__(self):
        self.emitters = []
        
    def add_emitter(self, emitter: ParticleEmitter):
        """Add an emitter to the system"""
        self.emitters.append(emitter)
        
    def remove_emitter(self, emitter: ParticleEmitter):
        """Remove an emitter"""
        if emitter in self.emitters:
            self.emitters.remove(emitter)
            
    def update(self, dt: float):
        """Update all emitters"""
        for emitter in self.emitters:
            emitter.update(dt)
            
    def draw(self, surface: pygame.Surface):
        """Draw all particles from all emitters"""
        for emitter in self.emitters:
            emitter.draw(surface)