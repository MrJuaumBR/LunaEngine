# Creating and Handling Scenes

## Creating a Scene

```python
from lunaengine.core import Scene

class MyScene(Scene):
    def on_enter(self):
        print("Scene entered")
    
    def update(self, dt):
        print(f"Delta time: {dt}")
    
    def on_exit(self):
        print("Scene exited")
```

### Adding UI Elements

```python
class MenuScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.play_button = Button(text="Play", position=(400,350), size=(200,50))
        self.play_button.on_click = self.start_game
        self.add_ui_element(self.play_button)

    def on_enter(self):
        """As on_enter is triggered every time the user changes to it, creating UiElements here isn't a smart thing"""
    
    def start_game(self):
        self.engine.set_scene("game")
```
### Switching Scenes

```python
engine = LunaEngine()
engine.add_scene("menu", MenuScene)
engine.add_scene("game", GameScene)
engine.set_scene("menu")
engine.run()
```
### Complete Example

```python
from lunaengine.core.engine import Engine
from lunaengine.core.scene import Scene
from lunaengine.ui.elements import Button, TextLabel

class MenuScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.title = TextLabel(x=400, y=200, text="My Game", font_size=32, color=(255, 255, 255))
        self.start_btn = Button(x=400, y=350, width=200,  height=50, text="Start")
        self.start_btn.on_click = lambda: self.engine.set_scene("game")
        self.add_ui_element(self.title)
        self.add_ui_element(self.start_btn)
        

class GameScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.back_btn = Button(x=400, y=550, width=150, height=40, text="Menu")
        self.back_btn.on_click = lambda: self.engine.set_scene("menu")
        self.add_ui_element(self.back_btn)

engine = LunaEngine()
engine.add_scene("menu", MenuScene)
engine.add_scene("game", GameScene)
engine.set_scene("menu")
engine.run()
```