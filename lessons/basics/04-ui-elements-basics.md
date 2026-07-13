# 04 - UI Elements Basics

LunaEngine includes a powerful, Roblox Studio‑like built-in UI system with reusable components such as buttons, labels, and containers.

## Creating UI Elements

To create UI elements, you instantiate them with a size, position, and any properties specific to the element.

```python
from lunaengine.ui.elements import Button, TextLabel
from lunaengine.core import Scene

class MenuScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        
        # 1. Create a Label
        self.title_label = TextLabel(
            x=400, y=100
            text="Welcome to LunaEngine!",
            font_size=32
        )
        
        # 2. Create a Button
        self.play_button = Button(
            x=400, y=300, width=200, height=60
            text="Play Game"
        )
```

## Event Handling (Callbacks)

UI Elements in LunaEngine use direct assignment of functions for their events. You can assign any callable (a function, a lambda, or a class method).

```python
        # Using a simple lambda
        self.play_button.set_on_click(lambda: print("Button clicked!"))
        
        # Or using a method
        self.play_button.set_on_click(self.start_game)
        
    def start_game(self):
        print("Starting game...")
        self.engine.set_scene("game")
```

## Adding to the Scene

A UI Element will not render or receive input until it is added to the scene's UI tree. 
**Important:** You should typically add UI elements in your scene's `__init__` method, NOT in `on_enter`, because `on_enter` is called every time the scene is switched to, which would create duplicate elements.

```python
    def __init__(self, engine):
        # ... (element creation from above) ...
        
        # Add elements to the scene so they render and receive events
        self.add_ui_element(self.title_label)
        self.add_ui_element(self.play_button)
```

## Common Built-In Elements

Here are some of the most common UI elements you'll use:

- **Button**: A standard clickable button.
- **TextLabel**: Displays static or dynamic text.
- **TextBox**: Allows the user to type and input text.
- **ImageLabel**: Displays an image or texture.
- **Dropdown**: A dropdown selection menu.
- **ProgressBar**: A visual bar showing completion percentage.
- **Slider**: A draggable handle along a track to select a value.

You can import all of these from `lunaengine.ui.elements`. By learning to combine these elements, you can build complex menus, HUDs, and inventories without having to manually manage rendering and input.