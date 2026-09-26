# 19 - OpenGL Post-Processing Effects

LunaEngine's OpenGL renderer supports 19 real-time, GPU-accelerated post-processing effects through its `Filter` system (`lunaengine.backend.opengl`). These filters run as GLSL fragment shaders applied to the entire rendered frame (or a specific region of it), giving your game a cinematic, polished feel with minimal CPU cost.

---

## How Filters Work

After all your game content is rendered, the renderer passes the final frame through a filter shader before displaying it. You configure filters using the `Filter` class and apply them via `engine.renderer`.

```python
from lunaengine.backend import FilterType, Filter, FilterRegionType

# Apply a vignette filter at full intensity to the whole screen
vignette = engine.renderer.add_vignette(intensity=0.8)
```

All filter methods return a `Filter` object that you can store, update (e.g. change intensity), or remove later.

---

## All 19 Available Effects

### 🎨 Color & Tone Effects

#### 1. VIGNETTE
Darkens the corners of the screen toward a circular center, focusing the player's gaze inward. Essential for horror and cinematic scenes.
```python
# intensity: how dark the corners get (0.0 = none, 1.0 = full black corners)
engine.renderer.add_vignette(intensity=0.7)
```

#### 2. SEPIA
Applies a warm, brownish-orange tone shift, making the scene look like an old photograph. Great for flashback sequences.
```python
# intensity: 0.0 = original color, 1.0 = fully sepia
engine.renderer.add_sepia(intensity=0.9)
```

#### 3. GRAYSCALE
Removes all color from the screen. Perfect for "game paused", death sequences, or a black-and-white art style.
```python
engine.renderer.add_grayscale(intensity=1.0)
```

#### 4. INVERT
Inverts all RGB channels (like a photographic negative). Useful for psychedelic effects or special abilities.
```python
engine.renderer.add_invert(intensity=1.0)
```

#### 5. TEMPERATURE_WARM
Tints the screen with warm tones (orange/red), simulating a sunset or fire-lit environment.
```python
engine.renderer.add_temperature_warm(intensity=0.6)
```

#### 6. TEMPERATURE_COLD
Tints the screen with cold tones (blue), simulating a frozen tundra or deep-sea environment.
```python
engine.renderer.add_temperature_cold(intensity=0.7)
```

#### 7. POSTERIZE
Reduces the number of distinct color levels, creating a cartoon-like, flat-color aesthetic.
```python
# Higher intensity = fewer color levels = more stylized
engine.renderer.add_posterize(intensity=0.8)
```

---

### ✨ Glow & Edge Effects

#### 8. BLOOM
Brightens pixels that are already very bright, creating a soft, glowing halo around light sources. Makes neon signs, magic spells, and explosions look spectacular.
```python
engine.renderer.add_bloom(intensity=0.6)
```

#### 9. NEON
Detects edges in the scene and colorizes them with the original hue at full saturation, making everything look like it's outlined with glowing neon lights.
```python
engine.renderer.add_neon(intensity=0.8)
```

#### 10. EDGE_DETECT
Uses a Sobel kernel to draw only the edges of objects, turning your game into a sketch or wireframe view.
```python
engine.renderer.add_edge_detect(intensity=1.0)
```

#### 11. EMBOSS
Creates a raised, chiseled stone or metallic look by computing luminance differences between neighboring pixels.
```python
engine.renderer.add_emboss(intensity=0.9)
```

#### 12. SHARPEN
Increases local contrast to make textures appear crisper. Useful when the game world feels soft or blurry.
```python
engine.renderer.add_sharpen(intensity=0.5)
```

---

### 🌊 Blur & Distortion Effects

#### 13. BLUR
Applies a 5x5 Gaussian blur, softening the entire scene. Ideal for depth-of-field effects or "drunk" visual states.
```python
# You can restrict blur to a specific region:
engine.renderer.add_blur(intensity=1.0, x=0, y=0, width=engine.width, height=engine.height)
```

#### 14. RADIAL_BLUR
Blurs outward from the screen center, simulating high-speed motion or a rushing camera zoom effect.
```python
engine.renderer.add_radial_blur(intensity=0.7)
```

#### 15. FISHEYE
Distorts the UV coordinates in a barrel shape, creating the wide-angle "fisheye lens" look. Fun for comedic moments or tiny-world perspectives.
```python
engine.renderer.add_fisheye(intensity=0.5)
```

#### 16. TWIRL
Rotates pixels around the screen center by an angle proportional to their distance from the center, creating a swirling vortex effect.
```python
engine.renderer.add_twirl(intensity=0.5)
```

---

### 🖥️ Retro & Stylized Effects

#### 17. NIGHT_VISION
Converts the frame to a green monochrome with animated scanlines and film grain noise, perfectly simulating a military-style night-vision goggle display.
```python
engine.renderer.add_night_vision(intensity=1.0)
```

#### 18. CRT
Simulates an old CRT (cathode-ray tube) television, complete with horizontal scanlines, a chromatic aberration (RGB color fringing), and a vignette. Excellent for retro or lo-fi games.
```python
engine.renderer.add_crt(intensity=0.9)
```

#### 19. PIXELATE
Downsamples the screen to large blocks of color and upsamples back, creating a 8-bit/16-bit pixelated aesthetic. Great for retro games or a "loading" transition effect.
```python
engine.renderer.add_pixelate(intensity=0.8)
```

---

## Regional Filters

Instead of applying an effect to the full screen, you can apply it to a specific **rectangle** or **circle** region. This is great for localized blur effects (like blurring only the background behind a UI panel).

```python
from lunaengine.backend import Filter, FilterType, FilterRegionType

# Blur only a 200x200 area centered at (300, 250)
blurred_area = Filter(
    filter_type=FilterType.BLUR,
    intensity=1.0,
    region_type=FilterRegionType.RECTANGLE,
    region_pos=(200, 150),
    region_size=(200, 200),
    feather=20.0  # Soften the edges of the affected region
)
engine.renderer.add_filter(blurred_area)
```

---

## Dynamic Filters (Changing Intensity at Runtime)

Filters are objects. Store the reference and mutate their `intensity` every frame for animated effects:

```python
class GameScene(Scene):
    def on_enter(self, prev):
        self.damage_vignette = engine.renderer.add_vignette(intensity=0.0)

    def player_took_damage(self):
        # Flash a red-hot vignette, then fade it out
        self.damage_vignette.intensity = 1.0

    def update(self, dt):
        # Gradually fade the vignette back to 0
        if self.damage_vignette.intensity > 0:
            self.damage_vignette.intensity = max(0.0, self.damage_vignette.intensity - dt * 2.0)
```

This technique creates a satisfying "flash red on damage" effect without any heavy CPU code.
