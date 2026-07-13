# Introduction to LunaEngine

LunaEngine is a 2D game framework built with Python, Pygame, OpenGL, and OpenAL.

## Key Features

| Feature | Description |
|---------|-------------|
| Advanced UI | Roblox Studio‑like UI components |
| OpenGL Rendering | Hardware‑accelerated graphics |
| Themes | 58+ pre‑built themes |
| Particles | Optimized particle system |
| Modular Architecture | Easy to extend |

## Core Concepts

### The Engine Class

```python
from lunaengine.core import LunaEngine
engine = LunaEngine()
engine.run()
```

### Scenes

```python
from lunaengine.core import Scene
class MyScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
    def on_enter(self): pass
    def update(self, dt): pass
```

### UI Elements

```python
from lunaengine.ui import Button
button = Button(x=100, y=100, width=200, height=50, text="Click")
```
### Themes

```python
engine.set_global_theme("neon")
```

### Hellow World Examples

```python
from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import TextLabel

class HelloScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)

    def on_enter(self):
        label = TextLabel(x=400, y=300, text="Hello, LunaEngine!")
        self.add_ui_element(label)

engine = LunaEngine()
engine.add_scene("hello", HelloScene)
engine.set_scene("hello")
engine.run()
```