# 03 - Creating and Handling Scenes

In LunaEngine, a `Scene` represents a distinct state or screen of your game. For example, you might have a `MenuScene`, a `Level1Scene`, and a `GameOverScene`. The Engine handles switching between these scenes and ensures that only the active scene is updated and rendered.

## Creating a Scene

To create a scene, you inherit from the base `Scene` class. The most important methods to override are `__init__`, `on_enter`, `update`, and `on_exit`.

```python
from lunaengine.core import Scene

class MyScene(Scene):
    def __init__(self, engine):
        # Always call super().__init__ passing the engine!
        super().__init__(engine)
        
        # This is where you should instantiate UI elements and initial data.
        self.score = 0

    def on_enter(self, previous_scene_name):
        # Triggered every time the engine switches to this scene.
        # Useful for resetting timers, music, or game state.
        print(f"Entering MyScene from {previous_scene_name}!")
    
    def update(self, dt):
        # Called every frame. 'dt' is delta time (seconds since last frame).
        # Put your game logic here!
        self.score += dt * 10
    
    def on_exit(self, next_scene_name):
        # Triggered when leaving this scene.
        print(f"Leaving MyScene to go to {next_scene_name}!")
```

## Adding UI Elements

As noted in the `__init__` example, UI elements should be created and added to the scene in `__init__`, not in `on_enter`. If you add them in `on_enter`, you'll create duplicate buttons every time the player enters the scene!

```python
from lunaengine.ui.elements import Button

class MenuScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        
        self.play_button = Button(text="Play", position=(400, 350), size=(200, 50))
        self.play_button.on_click = self.start_game
        
        # You MUST add the element to the scene for it to render and work
        self.add_ui_element(self.play_button)

    def start_game(self):
        # Tell the engine to switch to the "game" scene
        self.engine.set_scene("game")
```

## Registering and Switching Scenes

Before the engine can switch to a scene, it needs to be added via `add_scene`. You pass a string name and the scene class itself (the engine will handle instantiation).

```python
from lunaengine.core.engine import LunaEngine
from lunaengine.core.scene import Scene
from lunaengine.ui.elements import Button, TextLabel

class MenuScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.title = TextLabel(x=400, y=200, text="My Game", font_size=32)
        self.start_btn = Button(x=400, y=350, width=200, height=50, text="Start")
        
        # Lambda function to switch scenes
        self.start_btn.on_click = lambda: self.engine.set_scene("game")
        
        self.add_ui_element(self.title)
        self.add_ui_element(self.start_btn)

class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.back_btn = Button(x=400, y=550, width=150, height=40, text="Menu")
        self.back_btn.on_click = lambda: self.engine.set_scene("menu")
        self.add_ui_element(self.back_btn)

# 1. Create the Engine
engine = LunaEngine()

# 2. Add Scenes (String name, Class reference)
engine.add_scene("menu", MenuScene)
engine.add_scene("game", GameScene)

# 3. Set the starting scene
engine.set_scene("menu")

# 4. Start the game loop
engine.run()
```