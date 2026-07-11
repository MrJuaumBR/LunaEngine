# 10 - Camera Movement & Follow Strategies

In basic camera usage, you might manually set the camera's `position` to match a player's `x` and `y`. However, instantly snapping the camera every frame feels rigid. 

LunaEngine v0.2.5 includes a built-in strategy system (`FollowStrategy`) that handles advanced camera logic automatically!

## Built-In Follow Strategies

Instead of writing custom code to calculate deadzones and lead vectors, you can assign a strategy to the camera.

```python
from lunaengine.graphics.camera import PlatformerFollow, TopDownFollow, SimpleFollow
from lunaengine.core import Scene
import pygame

class LevelScene(Scene):
    def on_enter(self, previous_scene):
        self.player = Player()
        self.camera.set_target(self.player)
        
        # Strategy 1: Platformer (Deadzone)
        # The camera only moves when the player leaves the 200x150 pixel deadzone in the center
        deadzone = pygame.Rect(0, 0, 200, 150)
        self.camera.set_follow_strategy(PlatformerFollow(deadzone_rect=deadzone))
```

### Top-Down Strategy

For RPGs, you often want the camera to "look ahead" in the direction the player is moving.

```python
        # Strategy 2: Top-Down
        # The camera calculates the target's velocity and leads ahead of it
        self.camera.set_follow_strategy(TopDownFollow(lead_factor=0.5))
```

*(Note: `TopDownFollow` requires the target object to have a `velocity` or `direction` property).*

## Smooth Interpolation

Regardless of which strategy you use, the camera won't instantly snap to the target position. It uses an interpolation system!

You can configure *how* the camera catches up to its target:

```python
from lunaengine.graphics.camera import InterpolationType

# Make the camera follow quickly but smoothly using Smoothstep interpolation
self.camera.smooth_speed = 0.2
self.camera.interpolation_type = InterpolationType.SMOOTHSTEP
```

## Camera Constraints

You can also restrict the camera's movement so it never looks outside the bounds of your game world.

```python
from lunaengine.graphics.camera import CameraConstraints
import pygame

# Prevent the camera from leaving the 5000x5000 world map
world_bounds = pygame.Rect(0, 0, 5000, 5000)
self.camera.constraints = CameraConstraints(bounds=world_bounds, min_zoom=0.5, max_zoom=2.0)
```

Combining Follow Strategies, Interpolation, and Constraints allows you to create professional camera behavior with almost no custom math required.