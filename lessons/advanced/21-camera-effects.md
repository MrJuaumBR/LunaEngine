# 18 - Camera Effects

The camera isn't just for framing the world — it's a game-feel tool. Subtle screen shakes, zooms, and trauma effects communicate impact, danger, and excitement to the player. LunaEngine's camera effect system handles all of this with a stackable, extensible architecture.

---

## Camera Shake

The simplest effect. Use `camera.shake()` after an explosion, a hit, or a boss slam.

```python
from lunaengine.graphics.camera import CameraShakeType

class GameScene(Scene):
    def explosion_at(self, pos):
        # Positional shake: random offset added to camera position each frame
        self.camera.shake(
            intensity=1.0,   # 0.0 (none) to 1.0 (max)
            duration=0.5,    # Lasts half a second
            shake_type=CameraShakeType.POSITIONAL
        )

    def boss_stomp(self):
        # Rotational shake: randomly rotates the camera instead
        self.camera.shake(
            intensity=0.6,
            duration=0.8,
            shake_type=CameraShakeType.ROTATIONAL
        )

    def catastrophic_event(self):
        # Trauma shake: combines positional AND rotational shaking
        self.camera.shake(
            intensity=1.0,
            duration=1.5,
            shake_type=CameraShakeType.TRAUMA
        )
```

All shake effects **decay linearly** over their duration — starting strong and fading out naturally.

---

## Trauma System

For systems where multiple events stack (e.g. getting hit repeatedly), the **Trauma system** is better than calling `shake()` repeatedly. Trauma accumulates and decays over time.

```python
    def player_hit(self):
        # Add 0.4 trauma. Trauma is clamped to 1.0.
        # Each hit stacks, so 3 rapid hits = max shake
        self.camera.add_trauma(0.4)
```

The `TraumaEffect` inside the camera automatically decays trauma at `1.5 units/second` by default, so heavy hits produce prolonged shaking.

---

## Custom Camera Effects

You can create your own stackable effects by subclassing `CameraEffect`:

```python
from lunaengine.graphics.camera import CameraEffect
import math

class PulseZoomEffect(CameraEffect):
    """Rapidly pulses the camera zoom in and out."""
    def __init__(self, amplitude=0.1, frequency=10.0, duration=1.0):
        self.amplitude = amplitude
        self.frequency = frequency
        self.duration = duration
        self.time_left = duration

    def update(self, dt: float) -> bool:
        self.time_left -= dt
        return self.time_left > 0  # Returns False when finished

    def apply(self, camera) -> None:
        t = (self.duration - self.time_left) / self.duration
        pulse = math.sin(t * self.frequency * 2 * math.pi) * self.amplitude
        camera.zoom += pulse

# Usage in your scene
class GameScene(Scene):
    def player_leveled_up(self):
        self.camera.add_effect(PulseZoomEffect(amplitude=0.05, frequency=8, duration=0.8))
```

---

## Smooth Zoom Transitions

```python
    def zoom_in_on_boss(self):
        # Smoothly zoom to 2x over the next frames (interpolated by smooth_speed)
        self.camera.set_zoom(2.0, smooth=True)
    
    def zoom_back_out(self):
        self.camera.set_zoom(1.0, smooth=True)
```

The zoom is interpolated using the camera's `smooth_speed` and `interpolation_type`, so the transition is gradual and natural.

---

## Combining Effects

The real power of the camera effect system is in **combining** effects for complex moments:

```python
    def final_boss_death(self):
        # A dramatic sequence: trauma shake + zoom out + sepia tone (from OpenGL filter)
        self.camera.add_trauma(1.0)
        self.camera.set_zoom(0.7, smooth=True)
        
        from lunaengine.backend import FilterType
        self.engine.renderer.add_sepia(intensity=0.5)
        self.engine.renderer.add_vignette(intensity=0.9)
```

These small technical details create the cinematic moments that players remember.