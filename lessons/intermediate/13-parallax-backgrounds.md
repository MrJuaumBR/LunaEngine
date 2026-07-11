# 12 - Parallax Backgrounds

The Camera system in LunaEngine v0.2.5 includes a powerful, optimized `ParallaxBackground` manager built-in. It allows you to create depth in your scenes by having multiple background layers that scroll at different speeds relative to the camera.

## Understanding the Parallax System

Every `Camera` instance automatically has a `parallax` attribute, which is a `ParallaxBackground` manager. 
You can add `ParallaxLayer` objects to this manager. A layer can render in two modes:
1. **Tiled Texture** (Efficient, great for repeating backgrounds like sky, distant mountains).
2. **Sprite Collection** (Flexible, great for individual elements like floating clouds, trees, with individual animations).

## Basic Tiled Parallax

The simplest way to use parallax is with a repeating tiled texture.

```python
import pygame
from lunaengine.core import Scene

class LevelScene(Scene):
    def on_enter(self, previous_scene):
        # 1. Load your background image
        bg_surface = pygame.image.load("assets/sky.png").convert_alpha()
        
        # 2. Add a layer to the camera's parallax manager. 
        # speed=(0.1, 0.1) means it moves at 10% the speed of the camera (appears very far away)
        # z_index=-10 ensures it draws behind everything else.
        bg_layer = self.camera.parallax.add_layer(speed=(0.1, 0.1), z_index=-10)
        
        # 3. Set the layer to use the tiled texture
        bg_layer.set_tiled_texture(bg_surface)
```

By default, tiled textures repeat on both the X and Y axes (`repeat_x=True`, `repeat_y=True`). The engine will automatically render enough tiles to cover the screen, shifting them smoothly as the camera moves.

## Advanced Parallax: Sprite Collections

If you want individual sprites in your background (e.g. animated clouds that move independently), you can populate a layer with `ParallaxSprite` objects.

```python
from lunaengine.graphics.camera import ParallaxSprite
import pygame

class LevelScene(Scene):
    def on_enter(self, previous_scene):
        cloud_surf = pygame.image.load("assets/cloud.png").convert_alpha()
        
        # Create a layer that moves at half the camera speed
        clouds_layer = self.camera.parallax.add_layer(speed=(0.5, 0.5), z_index=-5)
        
        # Add an individual sprite
        # We can apply independent oscillation (wind movement) to the sprite
        sprite = ParallaxSprite(
            surface=cloud_surf,
            base_pos=pygame.Vector2(100, 150),  # World position
            scale=1.5,
            alpha=0.8,
            oscillate_x=20.0,    # Will move back and forth 20 units
            oscillate_speed=0.2  # Slow oscillation
        )
        clouds_layer.add_sprite(sprite)
```

### Auto-Populating Sprites

You can also ask the layer to randomly scatter sprites within a given world area:

```python
        # Scatter 50 clouds randomly in a 2000x1000 area
        area = pygame.Rect(0, 0, 2000, 1000)
        clouds_layer.populate_random(
            surface=cloud_surf,
            count=50,
            area=area,
            scale_range=(0.8, 1.5),
            alpha_range=(0.5, 0.9),
            oscillate_x_range=(10.0, 50.0),
            oscillate_speed_range=(0.1, 0.5)
        )
```

## Tips for Parallax

- **Speed values**: A speed of `(1.0, 1.0)` means the layer moves exactly with the camera (appears to be in the foreground with your player). A speed of `(0.0, 0.0)` means the layer is fixed to the camera (like a static UI or a distant static sky). Values between 0 and 1 create the illusion of depth.
- **Layer Order**: Always use the `z_index` argument in `add_layer()` to ensure your backgrounds draw in the correct order (lower `z_index` draws first/furthest back).

This built-in system entirely removes the need to write your own math for scrolling backgrounds, keeping your game loop clean and performant!
