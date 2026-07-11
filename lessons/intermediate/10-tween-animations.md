# 09 - Tween Animations

Tweening (short for "in-betweening") allows you to smoothly transition properties of objects from one value to another over time. Instead of instantly snapping a UI panel into place, you can tween its `x` coordinate to make it slide in beautifully.

The LunaEngine Tween system is heavily inspired by Roblox Studio and offers an incredible amount of control!

## Basic Tween Example

```python
from lunaengine.ui.tween import Tween, EasingType
from lunaengine.ui.elements import Button
from lunaengine.core import Scene

class MenuScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        
        self.button = Button(x=-200, y=100, width=200, height=50, text="Play")
        self.add_ui_element(self.button)
        
        # Slide the button in from the left side of the screen
        tween = Tween.create(self.button)
        tween.to(x=100, duration=1.0, easing=EasingType.QUAD_OUT)
        tween.play()
```

## The Power of the Tween API

You can animate virtually *any* numeric, tuple (like RGB colors), or list property. The API also supports method chaining for incredibly concise code!

```python
# 1. Animate multiple properties at once
Tween.create(my_panel).to(
    x=400, 
    y=300, 
    background_color=(255, 0, 0), # Fade to red
    duration=2.0, 
    easing=EasingType.ELASTIC_OUT
).play()
```

## Loops, Yoyos, and Callbacks

Tweens aren't just fire-and-forget; they give you deep control over the animation lifecycle.

```python
warning_label = TextLabel(x=100, y=100, text="WARNING!", color=(255, 0, 0))

# Make the label pulse repeatedly
Tween.create(warning_label)\
    .to(font_size=48, duration=0.5, easing=EasingType.SINE_IN_OUT)\
    .set_loops(-1, yoyo=True)\
    .set_callbacks(
        on_start=lambda: print("Warning started!"),
        on_loop=lambda loop_num: print(f"Pulsed {loop_num} times!")
    )\
    .play()
```
- `set_loops(-1, yoyo=True)`: `-1` means infinite loops. `yoyo=True` means the animation plays forwards, then reverses perfectly!

## Easing Types

LunaEngine supports over 25 easing functions (like `LINEAR`, `QUAD_IN_OUT`, `BOUNCE_OUT`, `ELASTIC_OUT`). Experiment with them to give your game a professional, polished feel.