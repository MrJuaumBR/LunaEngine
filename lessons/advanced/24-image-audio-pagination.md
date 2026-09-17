# Image, Audio Groups, and Pagination in 0.2.6.2

## Images

`lunaengine.graphics.Image` wraps a `pygame.Surface` and provides lazy, cached variants. Scalar scale uses normalized semantics (`1.0` is 100% and `0.5` is 50%); explicit `size=(width, height)` takes precedence over scale. `set_alpha()` uses `0.0..1.0`. Images support `tint`, `replace_color`, `paint`, `silhouette`, `grayscale`, `brightness`, and `contrast` filters, plus alpha masks.

```python
from lunaengine.graphics import Image
image = Image(surface).set_scale(0.5).set_alpha(0.8)
image.set_filter("tint", color=(100, 150, 255), intensity=0.6)
image.set_mask(mask_image)
renderer.draw_surface(image.get_surface(), 100, 100)
```

`SpriteSheet.get_image_at_rect()` and `get_image_grid()` return Image objects. Existing `get_sprite_at_rect()` and `get_sprite_grid()` continue returning surfaces.

## Audio groups

`AudioManager` creates `master`, `default`, and `music` groups. Additional groups can be nested and assigned to channels. Effective volume is the product of channel, group, parent-group, and master volume.

```python
music = audio.get_group("music")
music.set_volume(0.5)
audio.set_group_mute("music", True)
audio.set_group_effect("music", "reverb", 0.4)
```

OpenAL EFX remains device-dependent. The backend reports failed effect attachment through the source diagnostic state rather than claiming that an unavailable effect succeeded.

## Pagination

`Pagination` retains its original constructor and navigation methods while accepting `area=(x, y, width, height)`, `alignment`, and `spacing` keyword arguments. Only the visible page window is represented, including ellipses, so large page counts do not create thousands of buttons.
