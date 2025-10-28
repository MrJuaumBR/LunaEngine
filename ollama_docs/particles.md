# particles

## Overview

*File: `lunaengine\graphics\particles.py`*
*Lines: 125*

## Classes

### Particle

```
class Particle:
    """Represents a particle with position and state.

    Attributes:
        x (float): The x-coordinate of the particle.
        y (float): The y-coordinate of the particle.

    Methods:
        update(dt: float) -> None: Update the particle's position and state.
        is_alive() -> bool: Check if the particle is still alive.
    """
```

*Line: 7*

#### Methods

##### Method `update`

Update particle position and state

*Line: 20*

##### Method `__init__`

Private method.

*Line: 8*

##### Method `is_alive`

Check if particle is still alive

*Line: 27*

---

### ParticleSystem

Brief Description:
ParticleSystem is a class that manages the emission and rendering of particles in a game or simulation. It allows for the addition and removal of emitters, as well as updating and drawing all particles.

Parameters:

* `emitter`: An instance of the ParticleEmitter class to be added to the system.
* `dt`: A float representing the time step for the update method.
* `surface`: A pygame.Surface object that will be used for drawing.

Returns:

* None

Methods:

* `__init__()`: Initializes the ParticleSystem instance.
* `add_emitter(self, emitter)`: Adds an emitter to the system.
* `remove_emitter(self, emitter)`: Removes an emitter from the system.
* `update(self, dt)`: Updates all emitters in the system.
* `draw(self, surface)`: Draws all particles from all emitters on the given surface.

*Line: 104*

#### Methods

##### Method `add_emitter`

Add an emitter to the system

*Line: 108*

##### Method `remove_emitter`

Remove an emitter

*Line: 112*

##### Method `__init__`

Private method.

*Line: 105*

##### Method `draw`

Draw all particles from all emitters

*Line: 122*

##### Method `update`

Update all emitters

*Line: 117*

---

### ParticleEmitter

```
class ParticleEmitter:
    """An emitter for particles in a 2D space.

    Parameters:
        x (float): The x-coordinate of the emitter's position.
        y (float): The y-coordinate of the emitter's position.

    Methods:
        update(dt: float): Update the emitter and all particles.
        emit_particle(): Emit a new particle.
        draw(surface: pygame.Surface): Draw all particles.
```

*Line: 31*

#### Methods

##### Method `emit_particle`

Emit a new particle

*Line: 67*

##### Method `update`

Update emitter and all particles

*Line: 49*

##### Method `__init__`

Private method.

*Line: 32*

##### Method `draw`

Draw all particles

*Line: 85*

---

## Functions

### Function `draw`

Draw all particles from all emitters

*Line: 122*

### Function `add_emitter`

Add an emitter to the system

*Line: 108*

### Function `remove_emitter`

Remove an emitter

*Line: 112*

### Function `update`

Update particle position and state

*Line: 20*

### Function `draw`

Draw all particles

*Line: 85*

### Function `emit_particle`

Emit a new particle

*Line: 67*

### Function `update`

Update all emitters

*Line: 117*

### Function `__init__`

Private method.

*Line: 105*

### Function `update`

Update emitter and all particles

*Line: 49*

### Function `__init__`

Private method.

*Line: 32*

### Function `is_alive`

Check if particle is still alive

*Line: 27*

### Function `__init__`

Private method.

*Line: 8*

