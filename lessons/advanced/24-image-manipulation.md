# 24 - Image Manipulation

LunaEngine v0.2.6.2 introduced `graphics.Image`, a surface-backed abstraction that handles scaling, alpha, filters, masks, and geometry transforms with lazy cached variants. If you're still calling `pygame.transform.*` in your render loop, this class replaces all of it.

## Why Image exists

A `pygame.Surface` is a raw pixel buffer. Every time you want it at a different size, tinted, or flipped, you call a transform and hope the result isn't recomputed next frame. `Image` wraps a Surface and:

- Caches every variant by (revision, scale, size, alpha, flip, rotation, filters, mask)
- Invalidates the cache when you change a property
- Lazily computes — nothing is generated until `get_surface()` is called
- Accepts `pygame.Surface`, a file path, another `Image`, or an `AtlasItem` as source

```python
from lunaengine.graphics import Image

image = Image("assets/hero.png")
# Nothing has been scaled, tinted, or transformed yet.
surface = image.get_surface()  # first call generates and caches
surface = image.get_surface()  # second call is a dict lookup
```

## Source types
```python
from lunaengine.graphics import Image
from lunaengine.storage import AtlasItem

img1 = Image(pygame_surface)                    # from a live Surface
img2 = Image("assets/hero.png")                 # from a path
img3 = Image(Path("assets/hero.png"))           # pathlib works too
img4 = Image(atlas_item)                        # resolved via item.path
img5 = Image(other_image)                       # copies the source Surface
```
``Image`` does not hold a reference to the file, only to the loaded Surface. If you need to reload from disk, create a new ``Image``.

## Scale and size
Two ways to size an image. **Explicit size wins** if both are set.
```python
# Normalized scale: 0.5 = half, 1.0 = 100%, 2.0 = double
img = Image("hero.png").set_scale(0.5)

# Non-uniform scale
img.set_scale((2.0, 1.5))

# Exact pixels (overrides scale)
img.set_size((128, 128))

# Remove the size override, fall back to scale
img.set_size(None)
```
For UI elements this maps directly to the ``Ratio`` system - ``set_scale(ratio.x)`` gives you resolution-independent scaling without touching pixel values.

## Alpha
```python
img.set_alpha(0.8)   # 80% opacity, 0.0 to 1.0
```
Alpha is stored as a float and applied at surface-generation time. The source Surface is never mutated.

## Filters
Filters stack. Each ``set_filter`` call appends to a list; the list is applied in order every time the surface is regenerated.
```python
img.set_filter("tint", color=(100, 150, 255), intensity=0.6)
img.set_filter("grayscale")
img.set_filter("brightness", amount=1.2)
img.set_filter("contrast", factor=1.5)
img.set_filter("replace_color", old=(255, 0, 0), new=(0, 255, 0), tolerance=20)
img.set_filter("silhouette", color=(255, 255, 255))
img.set_filter("paint", color=(200, 100, 50))
```
Supported filter names: ``tint``, ``replace``, ``replace_color``, ``paint``, ``silhouette``, ``grayscale``, ``brightness``, ``contrast``.
To reset:

```python
img.clear_filters()
```
Filters are applied before geometry transforms (flip, rotate) and before scaling, so a tinted, flipped, scaled image is generated in the correct order.

## Masks
A mask is a second image whose alpha multiplies the source alpha, pixel by pixel.
```python
mask = Image("assets/vignette_mask.png")
img.set_mask(mask)
img.set_mask(None)  # remove
```
Masks are rescaled to match the source if their sizes differ. Use them for soft edges, spotlight effects, and shaped fades.

## Flip and rotate
```python
img.set_flip(flip_x=True, flip_y=False)
img.set_rotation(45, "Degree")   # counter-clockwise, "Degree" or "Radian"
img.clear_transform()            # resets both
```
Rotation is applied after flip and before scaling. This means ``set_size((128, 128))`` always produces exactly 128×128, even if the rotation would have changed the bounding box.

## Spritesheet integration
``SpriteSheet.get_image_at_rect()`` and ``get_image_grid()`` return ``Image`` objects. The legacy ``get_sprite_at_rect()`` and ``get_sprite_grid()`` are unchanged and still return Surfaces.
```python
from lunaengine.graphics.spritesheet import SpriteSheet

sheet = SpriteSheet("assets/hero.png")

# Image-backed extraction
hero = sheet.get_image_at_rect((0, 0, 64, 64))
hero.set_scale(0.5)
hero.set_filter("tint", color=(100, 150, 255), intensity=0.4)

# Image grid
walk_frame = sheet.get_image_grid(cell_size=(64, 64), grid_pos=(3, 0))

# Legacy Surface API — still works
surface = sheet.get_sprite_grid(cell_size=(64, 64), grid_pos=(3, 0))
```
Image variants from a spritesheet are cached. The source sheet is never modified. Wrapping a selected frame once and reusing it is the recommended pattern:
```python
frame_image = Image(animation.get_current_frame()).set_scale(2.0)
renderer.draw_surface(frame_image.get_surface(), 320, 200)
```
Doing this every frame is fine because the variant is cached — the second call is a dict lookup, not a pixel transform.

## Serialization
``tostring()`` and ``fromstring()`` let you move an ``Image`` across process boundaries or store it inside a save file.
```python
data, size = img.tostring("RGBA")     # (str, (width, height))
restored = Image.fromstring(data, size, "RGBA")
```
Accepted formats: ``P``, ``RGB``, ``RGBX``, ``RGBA``, ``ARGB``, ``BGRA``, ``RGBA_PREMULT``, ``ARGB_PREMULT``.

## Rendering
```python
renderer.draw_surface(img.get_surface(), 100, 100)
```

Or via a UI element:
```python
from lunaengine.ui import ImageLabel

label = ImageLabel(x=100, y=100, width=64, height=64)
label.set_image(Image("assets/hero.png").set_scale(0.5))
```

``ImageLabel`` and ``ImageButton`` accept ``Image``, ``Surface``, paths, and ``AtlasItem`` uniformly.

## Caching rules - what to watch for
The cache key includes the current revision, scale, size, alpha, flip, rotation, filters, mask identity, and mask revision. Any ``set_*`` method bumps the revision and clears the cache. So:
```python
img = Image("hero.png").set_scale(0.5)
a = img.get_surface()      # generates
b = img.get_surface()      # cache hit
img.set_alpha(0.7)         # cache cleared
c = img.get_surface()      # regenerates at new alpha
```
Changing properties every frame re-generates the surface every frame. Set once, render many.

## Common patterns

**Damage flash without new assets:**
```python
flash = Image("hero.png").set_filter("silhouette", color=(255, 100, 100))
# toggle visibility between flash and normal for 0.1s
```

**Poison tint**
```python
poisoned = Image("hero.png").set_filter("tint", color=(100, 255, 100), intensity=0.5)
```

**Frozen sprite (desaturated + blue):**
```python
frozen = (
    Image("hero.png")
    .set_filter("grayscale")
    .set_filter("tint", color=(100, 150, 255), intensity=0.7)
)
```

**Reuse across many entities** - build the ``Image`` once, share the reference. The cached variant is shared too:
```python
ENEMY_IMAGE = Image("enemy.png").set_scale(0.75)

for enemy in enemies:
    renderer.draw_surface(ENEMY_IMAGE.get_surface(), enemy.x, enemy.y)
```

## Surface vs Image - when to use which
- **Surface** - direct ``pygame`` interop, custom pixel loops, anything the renderer expects as raw input.
- **Image** - everything user-facing: sprites in a scene, UI elements, anything you scale/tint/flip.

``Image`` forwards unknown attributes to its surface (``__getattr__``), so ``image.get_width()`` works. Use ``.source`` to reach the unmodified Surface if you need it.