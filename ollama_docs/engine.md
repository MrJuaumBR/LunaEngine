# engine

## Overview

*File: `lunaengine\core\engine.py`*
*Lines: 202*

## Classes

### LunaEngine

LunaEngine
==========

The LunaEngine class is a game engine that provides a simple and efficient way to create games using Python. It allows developers to focus on the game logic without worrying about low-level details such as window management, event handling, and rendering.

### Initialization

The `LunaEngine` class can be initialized with several optional parameters:

* `title`: The title of the game window (default: "LunaEngine Game")
* `width`: The width of the game window (default: 800)
* `height`: The height of the game window (default: 600)
* `use_opengl`: Use OpenGL for rendering (default: False)

### Methods

The following methods are available on the `LunaEngine` class:

* `initialize()`: Initialize the engine.
* `add_scene(name, scene)`: Add a scene to the engine.
* `set_scene(name)`: Set the current active scene.
* `on_event(event_type)`: Decorator to register event handlers.
* `get_fps_stats()`: Get comprehensive FPS statistics (optimized).
* `get_hardware_info()`: Get hardware information.
* `run()`: Main game loop - optimized performance tracking.
* `shutdown()`: Cleanup resources.

*Line: 9*

#### Methods

##### Method `on_event`

Decorator to register event handlers

Args:
    event_type (int): The Pygame event type to listen for
Returns:
    Callable: The decorator function

*Line: 77*

##### Method `get_fps_stats`

Get comprehensive FPS statistics (optimized)

Returns:
    dict: A dictionary containing FPS statistics

*Line: 100*

##### Method `__init__`

Initialize the LunaEngine
Args:
    title (str) *Optional: The title of the game window (default: "LunaEngine Game")
    width (int) *Optional: The width of the game window (default: 800)
    height (int) *Optional: The height of the game window (default: 600)
    use_opengl (bool) *Optional: Use OpenGL for rendering (default: False)
Returns:
    None

*Line: 10*

##### Method `run`

Main game loop - optimized performance tracking

*Line: 113*

##### Method `set_scene`

Set the current active scene

Args:
    name (str): The name of the scene to set as current
Returns:
    None

*Line: 65*

##### Method `add_scene`

Add a scene to the engine

Args:
    name (str): The name of the scene
    scene: The scene object
Returns:
    None

*Line: 53*

##### Method `get_hardware_info`

Get hardware information

*Line: 109*

##### Method `initialize`

Initialize the engine

*Line: 39*

##### Method `shutdown`

Cleanup resources

*Line: 198*

---

## Functions

### Function `get_hardware_info`

Get hardware information

*Line: 109*

### Function `add_scene`

Add a scene to the engine

Args:
    name (str): The name of the scene
    scene: The scene object
Returns:
    None

*Line: 53*

### Function `get_fps_stats`

Get comprehensive FPS statistics (optimized)

Returns:
    dict: A dictionary containing FPS statistics

*Line: 100*

### Function `on_event`

Decorator to register event handlers

Args:
    event_type (int): The Pygame event type to listen for
Returns:
    Callable: The decorator function

*Line: 77*

### Function `shutdown`

Cleanup resources

*Line: 198*

### Function `set_scene`

Set the current active scene

Args:
    name (str): The name of the scene to set as current
Returns:
    None

*Line: 65*

### Function `initialize`

Initialize the engine

*Line: 39*

### Function `__init__`

Initialize the LunaEngine
Args:
    title (str) *Optional: The title of the game window (default: "LunaEngine Game")
    width (int) *Optional: The width of the game window (default: 800)
    height (int) *Optional: The height of the game window (default: 600)
    use_opengl (bool) *Optional: Use OpenGL for rendering (default: False)
Returns:
    None

*Line: 10*

### Function `run`

Main game loop - optimized performance tracking

*Line: 113*

### Function `decorator`

Decorator to register the event handler
Args:
    func (Callable): The event handler function
Returns:
    Callable: The original function

*Line: 86*

