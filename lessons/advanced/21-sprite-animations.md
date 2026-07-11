# 17 - Sprite Animations & Manipulation

LunaEngine v0.2.5 introduces a robust sprite sheet system that goes beyond simple cropping. Found in `lunaengine.graphics.spritesheet`, it supports alpha channels, time-based frame extraction, and various on-the-fly image manipulation utilities.

## The `SpriteSheet` Class

The `SpriteSheet` class is used to load and parse texture atlases. You can initialize it with a direct file path or seamlessly fetch it from the engine's `Atlas`.

```python
from lunaengine.graphics.spritesheet import SpriteSheet
from lunaengine.core.engine import LunaEngine

engine = LunaEngine()
engine.add_texture_to_atlas("hero", "assets/hero.png")

# Load directly from the Atlas
spritesheet = SpriteSheet.from_atlas("hero", engine.atlas)

# Extract a single sprite from the top-left (64x64 pixels)
single_sprite = spritesheet.get_sprite_at_rect((0, 0, 64, 64))

# Extract from a grid (e.g. cell width 64, height 64, at column 1, row 0)
second_frame = spritesheet.get_sprite_grid(cell_size=(64, 64), grid_pos=(1, 0))
```

## Image Manipulation

You don't always need to create new assets for different visual states (e.g., getting hit, poison status). `SpriteSheet` has static methods to modify surfaces dynamically.

```python
# 1. Color Replacement
# Replace red (255, 0, 0) with green (0, 255, 0)
recolored = SpriteSheet.replace_color(single_sprite, (255, 0, 0), (0, 255, 0), tolerance=20)

# 2. Tinting (Useful for damage effects or elemental statuses)
# Tints the sprite blue using the multiply blend mode
frozen_sprite = SpriteSheet.tint(single_sprite, tint_color=(100, 100, 255), intensity=0.8)

# 3. Painting (Solid Silhouette)
# Turn the entire non-transparent part of the sprite into solid white
flash_sprite = SpriteSheet.paint(single_sprite, color=(255, 255, 255), preserve_alpha=True)
```

## The `Animation` Class

Managing frame durations and extraction manually can be tedious. The `Animation` class automates this process entirely using a frame-rate independent timer.

It extracts frames sequentially starting from a given position in the spritesheet.

```python
from lunaengine.graphics.spritesheet import Animation

# Create an animation that automatically extracts 6 frames
# Starting at (0, 0), each frame is 70x70. Total animation takes 1.0 second.
run_anim = Animation(
    spritesheet_file="assets/hero_run.png",
    size=(70, 70),
    start_pos=(0, 0),
    frame_count=6,
    scale=(2.0, 2.0), # Scale it up 2x
    duration=1.0,
    loop=True
)

# Play the animation
run_anim.play()
```

### Updating and Rendering Animations

Because `Animation` is time-based, you only need to call `update()` every frame. 
To draw the animation, retrieve the current frame surface using its progress state.

```python
import math

class Player:
    def __init__(self):
        self.animation = run_anim
        
    def update(self, dt):
        # Update internal timer
        self.animation.update()
        
    def render(self, renderer, pos):
        # Get the total number of frames and the current progress [0.0 to 1.0]
        progress = self.animation.get_progress()
        frame_count = self.animation.get_frame_count()
        
        # Calculate which frame to show
        current_index = min(math.floor(progress * frame_count), frame_count - 1)
        current_frame = self.animation.frames[current_index]
        
        # Apply the fade effect if the animation is fading in/out
        final_frame = self.animation._apply_fade_effect(current_frame)
        
        renderer.blit(final_frame, pos)
```

*(Note: The `Animation` class also supports fade-in and fade-out effects automatically if you pass `fade_in_duration` or `fade_out_duration` during initialization!)*
