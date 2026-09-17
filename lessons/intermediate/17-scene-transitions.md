# 17 - Scene Transitions

LunaEngine scenes can transition without manually coordinating a fade overlay. Register scene classes with the engine, select a starting scene, and call `transition_to()` with a public `TransitionType`.

## Registering scenes

```python
from lunaengine.core import LunaEngine, Scene
from lunaengine.backend.transition import TransitionType

class BlueScene(Scene):
    def render(self, renderer):
        renderer.fill_screen((80, 130, 220))

class RedScene(Scene):
    def render(self, renderer):
        renderer.fill_screen((220, 80, 100))

engine = LunaEngine("Transitions", 1024, 720)
engine.add_scene("blue", BlueScene)
engine.add_scene("red", RedScene)
engine.set_scene("blue")
```

## Starting a transition

```python
self.engine.transition_to(
    "red",
    effect=TransitionType.FADE,
    duration=0.8,
)
```

Available effects include fade, slide, zoom, orbital, morph, and flash variants. Keep the registered scene name stable; transition calls use that name rather than the class name.

## Transition controls in a UI

A button callback is a natural place to trigger a transition:

```python
from lunaengine.ui import Button

button = Button(20, 20, 180, 40, "Open Red Scene")
button.set_on_click(lambda: self.engine.transition_to(
    "red", effect=TransitionType.SLIDE_LEFT, duration=0.6
))
self.add_ui_element(button)
```

The complete interactive example is `examples/scenes_transitions_demo.py`. It demonstrates target-scene selection, transition-effect selection, and multiple registered scenes.

## Lifecycle guidance

Keep scene construction and persistent resources in the scene class. Use `on_enter()` to reset transient state when a scene becomes active and `on_exit()` to release scene-specific effects or subscriptions. Do not assume that a transition is instantaneous when updating gameplay state.
