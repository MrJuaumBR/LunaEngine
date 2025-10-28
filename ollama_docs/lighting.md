# lighting

## Overview

*File: `lunaengine\graphics\lighting.py`*
*Lines: 63*

## Classes

### Light

```
class Light(object):
    """
    Initialize a light source with position, radius, color, and intensity.

    Parameters:
        x (float): The x-coordinate of the light source.
        y (float): The y-coordinate of the light source.
        radius (float): The radius of the light source.
        color (Tuple[int, int, int]): The RGB color of the light source.
        intensity (float): The intensity of the light source.

    Returns:
        None
    """
```

*Line: 6*

#### Methods

##### Method `__init__`

Private method.

*Line: 7*

---

### LightSystem

```
class LightSystem:
    """Manages the lighting in a scene."""

    def __init__(self, screen_width: int, screen_height: int):
        """Initializes the light system with the given screen dimensions."""

    def add_light(self, light: Light):
        """Adds a light to the system."""

    def remove_light(self, light: Light):
        """Removes a light from the system."""

    def calculate_lighting(self, surface: pygame.Surface) -> pygame.Surface:
        """Calculates the lighting for a given surface and returns it as a new surface."""
```

*Line: 15*

#### Methods

##### Method `__init__`

Private method.

*Line: 16*

##### Method `remove_light`

Remove a light from the system

*Line: 27*

##### Method `add_light`

Add a light to the system

*Line: 23*

##### Method `calculate_lighting`

Calculate lighting for a surface

*Line: 32*

---

## Functions

### Function `remove_light`

Remove a light from the system

*Line: 27*

### Function `add_light`

Add a light to the system

*Line: 23*

### Function `calculate_lighting`

Calculate lighting for a surface

*Line: 32*

### Function `__init__`

Private method.

*Line: 7*

### Function `__init__`

Private method.

*Line: 16*

