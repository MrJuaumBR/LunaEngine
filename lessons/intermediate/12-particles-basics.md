# 11 - Particle Systems Basics

Particles are a cornerstone of game feel. They are used for effects like smoke, sparks, fire, explosions, and magic spells.

## Creating a Particle Emitter

LunaEngine provides a highly optimized `ParticleEmitter` class to handle spawning and rendering thousands of particles efficiently.

```python
from lunaengine.graphics.particles import ParticleEmitter
from lunaengine.core import Scene

class LevelScene(Scene):
    def on_enter(self, previous_scene):
        
        # Create an emitter at position (300, 300)
        self.emitter = ParticleEmitter(x=300, y=300)
        
        # Configure the particle properties
        # This makes red/orange particles that fade and shrink
        self.emitter.color_start = (255, 100, 0)
        self.emitter.color_end = (50, 0, 0)
        self.emitter.size_start = 10
        self.emitter.size_end = 0
        self.emitter.lifetime = 1.0 # Particles live for 1 second
```

## Emitting Particles

You can either emit particles continuously (like a campfire) or in bursts (like an explosion).

```python
    def update(self, dt):
        # Continuous emission: 10 particles per frame
        self.emitter.emit(10)
        
        # Important: You must call update() on the emitter!
        self.emitter.update(dt)
        
    def player_died(self):
        # Burst emission: 500 particles instantly!
        self.emitter.emit(500)
```

## Rendering

Just like `Camera` or `UIElements`, particles need to be rendered. Since particles usually exist in the game world, they are often drawn relative to the camera.

```python
    def render(self, renderer):
        # Render the particles to the screen
        self.emitter.render(renderer, self.camera)
```

By tweaking gravity, velocity, color, and size properties on the `ParticleEmitter`, you can create vastly different effects, from gentle falling snow to aggressive shotgun blasts.