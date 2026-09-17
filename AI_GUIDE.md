# LunaEngine Guide for AI Coding Agents

This document gives AI assistants, LLM-based tools, and automated coding agents the framework-wide context needed to understand and modify LunaEngine safely. It is not limited to one release or feature batch.

## Framework identity

LunaEngine is a Python 2D game framework. The runtime combines a pygame-oriented application layer with backend services for OpenGL rendering, OpenAL audio, input devices, transitions, networking, and resource handling. Public projects commonly build games from an engine instance, registered scenes, UI elements, graphics resources, and update/render methods.

A minimal application normally follows this shape:

```python
from lunaengine.core import LunaEngine, Scene

class GameScene(Scene):
    def update(self, dt):
        pass

    def render(self, renderer):
        renderer.fill_screen((20, 20, 30))

engine = LunaEngine("My Game", 1024, 720)
engine.add_scene("game", GameScene)
engine.set_scene("game")
engine.run()
```

## Repository map

| Area | Read this area for |
| --- | --- |
| `lunaengine/core` | Engine loop, window lifecycle, scenes, and the high-level audio manager |
| `lunaengine/backend` | OpenGL/OpenAL implementation, transitions, controller input, networking, and low-level types |
| `lunaengine/graphics` | `Image`, `SpriteSheet`, `Animation`, camera, particles, shadows, and paperdolls |
| `lunaengine/ui` | UI elements, layouts, themes, styles, tweening, notifications, tooltips, and layer management |
| `lunaengine/storage` | Atlas/resource lookup, saved data, and encryption |
| `lunaengine/utils` | Image conversion, timers, math, performance, and threading helpers |
| `lunaengine/misc` | Icons and debugging utilities |
| `lunaengine/tools` | Developer and asset tools |
| `examples` | Runnable usage patterns and integration references |
| `lessons` | User-facing explanations and supported workflows |
| `tests` | Compatibility and behavioral contracts |

Start with the smallest relevant subsystem, then trace its public exports and tests. The package `__init__.py` files are useful for determining what the project considers public.

## Core architectural model

The engine owns the application loop, window, active scene, event processing, and renderer coordination. Scenes own game-specific state and UI elements. Backend renderers consume low-level drawing inputs; many paths remain compatible with `pygame.Surface`.

Graphics resources generally have a source asset, an extracted or transformed representation, and optionally a cached variant. `Image` is the higher-level surface-backed abstraction for scale, size, alpha, filters, and masks. `SpriteSheet` and `Animation` retain legacy Surface-oriented APIs as well as Image-oriented extraction. Do not assume every renderer path accepts an Image directly; resolve it to a Surface at the existing boundary when necessary.

UI is hierarchical. Elements can contain children, participate in layouts, receive input, use themes, and render through the scene. Changes to coordinates, visibility, parenting, event propagation, serialization, or theme lookup can affect many controls.

Audio is layered: the manager owns named channels and groups, channels own playback state, and the OpenAL backend owns sources, buffers, spatial state, and optional EFX resources. Hardware support is not uniform.

Storage and atlas systems are resource boundaries. Preserve path handling, cached data behavior, serialized formats, and explicit failure behavior when changing them.

## Public API and compatibility rules

Do not remove, rename, or subtly change an existing public method without an explicit migration plan. Prefer additive methods, aliases, optional parameters, and compatibility adapters.

Preserve these contracts unless a task explicitly changes them:

- `pygame.Surface` remains a valid input/output at established renderer and UI boundaries.

- Existing `SpriteSheet.get_sprite_at_rect()` and `get_sprite_grid()` remain Surface APIs.

- Existing icon factories and `Icon.get_surface()` continue to work.

- Scene registration and switching names remain stable.

- Audio playback, looping, pause/resume, volume, pitch, and balance/pan semantics remain compatible.

- Pagination page numbers remain one-based and large page counts use bounded visible controls.

- Saved-data, atlas, and theme file formats remain readable.

For normalized values, use `0.0 = 0%`, `0.5 = 50%`, and `1.0 = 100%` unless the established API uses another unit. Coordinates and sizes are pixels, durations are seconds, and page numbers are integers.

## Safe implementation patterns

### Images and sprites

Use `graphics.Image` for new image features instead of creating a second image abstraction. Reuse cached variants. Avoid CPU transformations inside a per-frame render loop. Preserve source surfaces and make masks/filters explicit about whether they copy or mutate data.

### UI

Integrate new controls into the existing `UIElement` hierarchy, theme system, layout/parenting model, layer manager, and event conventions. Match constructor patterns and preserve serialization where other elements provide it.

### Audio

Use `AudioManager`, `AudioChannel`, and channel groups. Route effective volume through the established hierarchy. Treat OpenAL EFX as optional. Check actual hardware/backend success, clean up replaced resources, and do not claim an effect is active when the device rejects it. Spatial tests are most reliable with mono sources.

### Scenes and transitions

Use registered scene names and the public transition API. Keep scene lifecycle behavior explicit. Do not block the main loop with loading, network calls, or long computations; use the existing utility/threading patterns when appropriate.

### Resources and errors

Fail clearly for invalid assets, malformed JSON, unsupported devices, and missing optional dependencies. Do not catch broad exceptions merely to hide a broken state. If a fallback is intentional, document it and test both the normal and fallback path.

## Agent workflow

1. Read the relevant implementation, exports, tests, examples, README, changelog, and lesson.

1. Identify existing conventions and compatibility constraints before designing a new API.

1. Make the smallest complete change at the narrowest extension point.

1. Add deterministic tests for normal, boundary, failure, and compatibility cases.

1. Update an example and user-facing documentation when behavior is public.

1. Run:

   ```bash
   python -m pytest -q
   python -m compileall -q lunaengine tests examples
   ```

1. Perform manual display/audio/controller/network tests when the feature depends on real hardware or a live backend.

1. Review the diff for generated files, accidental API changes, stale documentation, and resource leaks.

## Common mistakes to avoid

Do not create a parallel renderer, mixer, theme registry, image wrapper, or scene system when the framework already provides one. Do not return a different type from an existing method without a compatibility mechanism. Do not transform images, rebuild UI controls, allocate OpenAL effects, or create pagination buttons unnecessarily every frame. Do not assume OpenGL, OpenAL EFX, an audio device, or a display exists in CI. Do not update version claims or documentation for behavior that has not been implemented and tested.

When uncertain, inspect the nearest existing example and test before inventing a pattern. Preserve the framework's public behavior first; optimize or refactor only when the task explicitly includes that goal.