# engine

## Overview

*File: `lunaengine\core\engine.py`*
*Lines: 362*

## Classes

### LunaEngine

LunaEngine
==========

The LunaEngine class is a high-level game engine that provides an easy-to-use interface for creating games using the Pygame library. It allows developers to create scenes, add UI elements, and handle events with minimal code.

### Initialization

The `__init__` method initializes the LunaEngine object with the specified title, width, height, and whether to use OpenGL for rendering. The default values are "LunaEngine Game", 800, 600, and False, respectively.

### Scene Management

The `initialize` method initializes the engine. The `add_scene` method adds a scene to the engine with the specified name and scene object. The `set_scene` method sets the current active scene with the specified name.

### Event Handling

The `on_event` decorator registers event handlers for Pygame events. It takes an event type as an argument and returns a callable function that can be used to handle events.

### Theme Management

The `get_all_themes` method gets all available themes, including user custom ones. The `get_theme_names` method gets a list of all available theme names. The `set_global_theme` method sets the global theme for the entire engine and updates all UI elements.

### FPS Statistics

The `get_fps_stats` method gets comprehensive FPS statistics, including average, minimum, maximum, and standard deviation.

### Hardware Information

The `get_hardware_info` method gets hardware information about the system.

### Main Game Loop

The `run` method is the main game loop that handles events, updates UI elements, and renders the scene. It also includes optimized versions of `_handle_mouse_scroll`, `_handle_keyboard_event`, `_update_ui_elements`, and `_render_ui_elements`.

### Cleanup

The `shutdown` method cleans up resources used by the engine.

*Line: 9*

#### Methods

##### Method `_handle_keyboard_event`

Handle keyboard events for focused UI elements - OPTIMIZED

*Line: 294*

##### Method `add_scene`

Add a scene to the engine

Args:
    name (str): The name of the scene
    scene: The scene object
Returns:
    None

*Line: 53*

##### Method `_update_all_ui_themes`

Update all UI elements in the current scene to use the new theme

Args:
    theme_enum: The theme enum to apply

*Line: 170*

##### Method `_handle_mouse_scroll`

Handle mouse wheel scrolling for UI elements - OPTIMIZED

*Line: 262*

##### Method `get_fps_stats`

Get comprehensive FPS statistics (optimized)

Returns:
    dict: A dictionary containing FPS statistics

*Line: 190*

##### Method `get_theme_names`

Get list of all available theme names

Returns:
    List[str]: List of theme names

*Line: 137*

##### Method `get_all_themes`

Get all available themes including user custom ones

Returns:
    Dict[str, any]: Dictionary with theme names as keys and theme objects as values

*Line: 102*

##### Method `set_scene`

Set the current active scene

Args:
    name (str): The name of the scene to set as current
Returns:
    None

*Line: 65*

##### Method `run`

Main game loop - OPTIMIZED

*Line: 203*

##### Method `initialize`

Initialize the engine

*Line: 39*

##### Method `set_global_theme`

Set the global theme for the entire engine and update all UI elements

Args:
    theme_name (str): Name of the theme to set
    
Returns:
    bool: True if theme was set successfully, False otherwise

*Line: 147*

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

##### Method `get_hardware_info`

Get hardware information

*Line: 199*

##### Method `on_event`

Decorator to register event handlers

Args:
    event_type (int): The Pygame event type to listen for
Returns:
    Callable: The decorator function

*Line: 79*

##### Method `_update_ui_elements`

Update UI elements with mouse interaction - OPTIMIZED

*Line: 307*

##### Method `_render_ui_elements`

Render UI elements in correct order - OPTIMIZED

*Line: 330*

##### Method `shutdown`

Cleanup resources

*Line: 358*

---

## Functions

### Function `get_fps_stats`

Get comprehensive FPS statistics (optimized)

Returns:
    dict: A dictionary containing FPS statistics

*Line: 190*

### Function `initialize`

Initialize the engine

*Line: 39*

### Function `_update_ui_elements`

Update UI elements with mouse interaction - OPTIMIZED

*Line: 307*

### Function `_handle_mouse_scroll`

Handle mouse wheel scrolling for UI elements - OPTIMIZED

*Line: 262*

### Function `get_theme_names`

Get list of all available theme names

Returns:
    List[str]: List of theme names

*Line: 137*

### Function `set_scene`

Set the current active scene

Args:
    name (str): The name of the scene to set as current
Returns:
    None

*Line: 65*

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

### Function `set_global_theme`

Set the global theme for the entire engine and update all UI elements

Args:
    theme_name (str): Name of the theme to set
    
Returns:
    bool: True if theme was set successfully, False otherwise

*Line: 147*

### Function `_update_all_ui_themes`

Update all UI elements in the current scene to use the new theme

Args:
    theme_enum: The theme enum to apply

*Line: 170*

### Function `get_all_themes`

Get all available themes including user custom ones

Returns:
    Dict[str, any]: Dictionary with theme names as keys and theme objects as values

*Line: 102*

### Function `add_scene`

Add a scene to the engine

Args:
    name (str): The name of the scene
    scene: The scene object
Returns:
    None

*Line: 53*

### Function `get_hardware_info`

Get hardware information

*Line: 199*

### Function `_handle_keyboard_event`

Handle keyboard events for focused UI elements - OPTIMIZED

*Line: 294*

### Function `run`

Main game loop - OPTIMIZED

*Line: 203*

### Function `on_event`

Decorator to register event handlers

Args:
    event_type (int): The Pygame event type to listen for
Returns:
    Callable: The decorator function

*Line: 79*

### Function `_render_ui_elements`

Render UI elements in correct order - OPTIMIZED

*Line: 330*

### Function `shutdown`

Cleanup resources

*Line: 358*

### Function `decorator`

Decorator to register the event handler
Args:
    func (Callable): The event handler function
Returns:
    Callable: The original function

*Line: 88*

