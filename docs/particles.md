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

```
class ParticleSystem:
    """A system for managing and updating a collection of particle emitters."""

    def __init__(self):
        """Initialize the particle system with an empty list of emitters."""

    def add_emitter(self, emitter: ParticleEmitter):
        """Add an emitter to the system.

        Parameters:
            emitter (ParticleEmitter): The emitter to add.
        """

    def remove_emitter(self, emitter: ParticleEmitter):
        """Remove an emitter from the system.

        Parameters:
            emitter (ParticleEmitter): The emitter to remove.
        """

    def update(self, dt: float):
        """Update all emitters in the system.

        Parameters:
            dt (float): The time step for the update.
        """

    def draw(self, surface: pygame.Surface):
        """Draw all particles from all emitters in the system.

        Parameters:
            surface (pygame.Surface): The surface to draw on.
        """
```

*Line: 104*

#### Methods

##### Method `add_emitter`

Add an emitter to the system

*Line: 108*

##### Method `__init__`

Private method.

*Line: 105*

##### Method `remove_emitter`

Remove an emitter

*Line: 112*

##### Method `update`

Update all emitters

*Line: 117*

##### Method `draw`

Draw all particles from all emitters

*Line: 122*

---

### ParticleEmitter

ParticleEmitter
==============

Brief Description
-----------------

The ParticleEmitter class is responsible for managing a group of particles and updating their positions over time. It also provides methods for emitting new particles and drawing them on the screen.

Parameters
----------

* `x`: The x-coordinate of the emitter's position.
* `y`: The y-coordinate of the emitter's position.

Returns
-------

* None

Methods
-------

### `__init__`

The constructor for the ParticleEmitter class, which initializes the emitter's position and creates an empty list to store particles.

### `update`

Updates the emitter and all particles, including updating their positions and checking for collisions.

Parameters:

* `dt`: The time step between updates.

Returns:

* None

### `emit_particle`

Emits a new particle at the emitter's position.

Parameters:

* None

Returns:

* None

### `draw`

Draws all particles on the screen.

Parameters:

* `surface`: The surface to draw on.

Returns:

* None

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

### Function `remove_emitter`

Remove an emitter

*Line: 112*

### Function `draw`

Draw all particles

*Line: 85*

### Function `emit_particle`

Emit a new particle

*Line: 67*

### Function `__init__`

Private method.

*Line: 32*

### Function `__init__`

Private method.

*Line: 8*

### Function `update`

Update all emitters

*Line: 117*

### Function `add_emitter`

Add an emitter to the system

*Line: 108*

### Function `__init__`

Private method.

*Line: 105*

### Function `update`

Update particle position and state

*Line: 20*

### Function `is_alive`

Check if particle is still alive

*Line: 27*

### Function `update`

Update emitter and all particles

*Line: 49*

### Function `draw`

Draw all particles from all emitters

*Line: 122*

