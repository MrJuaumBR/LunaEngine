# 05 - Camera Basics

The Camera system controls what part of the world is visible on the screen. In LunaEngine v0.2.5, every `Scene` automatically comes with a built-in `Camera` instance (`self.camera`), so you don't even need to create one manually!

## The Unified Coordinate System

The camera's `position` represents the **center of the viewport** in world coordinates.

```python
from lunaengine.core import Scene
import pygame

class LevelScene(Scene):
    def on_enter(self, previous_scene):
        # Move the camera center to (500, 500)
        self.camera.position = pygame.Vector2(500, 500)
```

## Moving the Camera

You can adjust the camera's position by modifying the `Vector2` directly:

```python
    def update(self, dt):
        # Pan the camera to the right by 100 units per second
        self.camera.position.x += 100 * dt
```

## Zoom and Rotation

The camera also supports zooming and rotation natively.

```python
        # Zoom in (values > 1.0 zoom in, < 1.0 zoom out)
        self.camera.set_zoom(1.5, smooth=True) 
        
        # Rotate the camera by 45 degrees
        self.camera.rotation = 45.0
```

## Following a Target

Instead of manually updating the camera position every frame, the Camera system has built-in Follow Strategies! You can assign a target object (like a Player class) and the camera will track it.

To be a valid target, the object just needs to have an `x` and `y` attribute or a `rect`.

```python
class Player:
    def __init__(self):
        self.x = 100
        self.y = 100

class LevelScene(Scene):
    def on_enter(self, previous_scene):
        self.player = Player()
        
        # Tell the camera to follow the player
        self.camera.set_target(self.player)
```

*(We will cover more advanced follow strategies, like Platformer deadzones or RPG look-ahead, in the Intermediate lessons!)*