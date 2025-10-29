# lighting

## Overview

*File: `lunaengine\graphics\lighting.py`*
*Lines: 63*

## Classes

### Light

Brief Description:
This class represents a light source in a 2D space. It has a position (x and y coordinates), radius, color, and intensity.

Parameters:

* x: The x-coordinate of the light's position.
* y: The y-coordinate of the light's position.
* radius: The radius of the light source.
* color: A tuple representing the RGB color of the light.
* intensity: The intensity of the light source, a value between 0 and 1.

Returns:
The initialized Light object.

*Line: 6*

#### Methods

##### Method `__init__`

Private method.

*Line: 7*

---

### LightSystem

```
class LightSystem:
    def __init__(self, screen_width: int, screen_height: int):
        """Initialize the light system with a screen width and height."""
    
    def add_light(self, light: Light):
        """Add a light to the system."""
    
    def remove_light(self, light: Light):
        """Remove a light from the system."""
    
    def calculate_lighting(self, surface: pygame.Surface) -> pygame.Surface:
        """Calculate lighting for a surface and return the result as a new surface."""
```

*Line: 15*

#### Methods

##### Method `add_light`

Add a light to the system

*Line: 23*

##### Method `remove_light`

Remove a light from the system

*Line: 27*

##### Method `__init__`

Private method.

*Line: 16*

##### Method `calculate_lighting`

Calculate lighting for a surface

*Line: 32*

---

## Functions

### Function `__init__`

Private method.

*Line: 16*

### Function `calculate_lighting`

Calculate lighting for a surface

*Line: 32*

### Function `remove_light`

Remove a light from the system

*Line: 27*

### Function `add_light`

Add a light to the system

*Line: 23*

### Function `__init__`

Private method.

*Line: 7*

