# Contributing to LunaEngine

Thank you for contributing to LunaEngine. This document describes how to work on the framework as a whole: its architecture, development workflow, compatibility expectations, tests, documentation, examples, and pull requests.

## What LunaEngine is

LunaEngine is a Python 2D game framework built around pygame-compatible surfaces and a modular backend. It provides a game loop, scenes, rendering, UI, audio, input, asset management, animation, effects, storage, and developer tools.

The framework is organized into these main areas:

| Package | Responsibility |
| --- | --- |
| `lunaengine/core` | Engine lifecycle, scenes, window integration, and audio management |
| `lunaengine/backend` | OpenGL rendering, OpenAL audio, transitions, controllers, networking, and backend types |
| `lunaengine/graphics` | Images, spritesheets, animations, cameras, particles, shadows, and paperdolls |
| `lunaengine/ui` | Elements, layouts, themes, styles, tweening, notifications, tooltips, and UI layers |
| `lunaengine/storage` | Texture atlases, saved data, encryption, and resource-oriented helpers |
| `lunaengine/utils` | Image conversion, timers, math, performance, and threading utilities |
| `lunaengine/misc` | Icons, debugging helpers, and miscellaneous public conveniences |
| `lunaengine/tools` | Project and asset support tools |

## Development setup

Use Python 3.11 or newer for the current development configuration. From the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

Keep examples runnable from the repository root because many examples load assets with paths relative to their own files or the project.

## Development workflow

Before changing code, identify the public API and the relevant subsystem. Read the implementation, existing tests, examples, README, changelog, and related lessons. Prefer a small, focused change over a broad refactor.

For a normal feature:

1. Define the intended public behavior and compatibility requirements.

1. Locate the narrowest existing extension point.

1. Implement the behavior with docstrings and type hints where appropriate.

1. Add focused automated tests.

1. Update or add a runnable example when the behavior is user-facing.

1. Update the relevant lesson, README section, and changelog entry.

1. Run the complete validation commands below.

1. Describe platform-specific manual testing separately from automated testing.

## Validation commands

Run these from the repository root:

```bash
python -m pytest -q
python -m compileall -q lunaengine tests examples
```

Validate new JSON or other data files with an appropriate parser. For window, OpenGL, OpenAL, controller, networking, or filesystem behavior, perform a manual test on a supported target environment in addition to headless tests.

## Framework compatibility principles

LunaEngine is evolving, but existing projects should not break unnecessarily. Prefer additive APIs, aliases, adapters, and deprecation paths over removing or renaming public methods.

The renderer and many UI components accept `pygame.Surface` objects. Preserve that compatibility even when introducing higher-level abstractions such as `graphics.Image`. Existing Surface-returning spritesheet methods, icon factories, `Icon.get_surface()`, scene registration, audio channel methods, and UI constructors must remain usable unless a breaking change is explicitly planned and documented.

Normalized values use `0.0` for 0% and `1.0` for 100% unless an existing API explicitly defines another unit. This includes alpha, volume, intensity, and percentage-style scale. Pixel dimensions, coordinates, durations, and page numbers retain their explicit units. Pagination uses one-based page numbers.

## Subsystem guidance

### Engine and scenes

Keep scene registration and switching compatible with existing `add_scene()`, `set_scene()`, and transition APIs. Put transient state initialization in scene lifecycle methods and release scene-specific subscriptions, effects, and resources during exit. Avoid blocking the main loop.

### Rendering and graphics

Respect the distinction between source assets, cached variants, and per-frame output. Reuse images, textures, masks, and transformed surfaces whenever possible. Do not perform expensive CPU filters or image conversions every frame unless the behavior explicitly requires it. OpenGL resources must have deterministic cleanup paths where the backend supports them.

### UI

Preserve parent-child positioning, event propagation, theme lookup, layout behavior, visibility, and serialization expectations. New controls should work with the existing element hierarchy and should not bypass theme and layer-management conventions.

### Audio

Use `AudioManager`, named `AudioChannel` objects, channel groups, and the OpenAL backend instead of creating an unrelated mixer path. Preserve volume, pitch, balance/pan, looping, pause/resume, and playback lifecycle behavior. OpenAL EFX and device capabilities vary by platform; optional effects must fail truthfully and release resources when replaced or destroyed.

### Storage and resources

Keep atlas lookup, saved-data formats, and resource caching backward compatible. Avoid silently changing serialization or encryption behavior. Document migration requirements when a data format must change.

### Tools and examples

Tools should remain safe to run against a project and should avoid modifying source assets unexpectedly. Examples should be concise enough to understand, use real public APIs, resolve their assets reliably, and include a short entry in `examples/examples.md`.

## Tests

Tests should be deterministic, focused, and independent of a physical display or audio device whenever possible. Use dummy SDL drivers for pygame-backed tests when appropriate. Test both the new API and compatibility with the old API. Include boundary cases such as empty resources, invalid paths, zero/one normalized values, large page counts, missing optional hardware, and repeated resource replacement.

## Documentation requirements

Public behavior belongs in documentation. Update the most specific lesson or README section, the examples catalog when applicable, and `changelog.md` for user-visible changes. Keep code samples synchronized with actual signatures. Do not document experimental behavior as stable without marking it clearly.

## Pull requests

A pull request should explain:

- the user-visible problem and solution;

- the affected packages and public APIs;

- compatibility and migration impact;

- tests and commands run;

- manual or hardware tests performed;

- known limitations and platform-specific behavior;

- documentation and examples added or updated.

Keep unrelated formatting changes, generated caches, compiled bytecode, and opportunistic refactors out of feature pull requests. If a breaking change is necessary, propose it explicitly and include a migration path.