# 16 - Advanced UI

By combining LunaEngine's layout managers, tween animations, notifications, and nested element parenting, you can build sophisticated interfaces that rival commercial game UI frameworks.

---

## Nested Elements & Containers

UI elements in LunaEngine can be nested. A parent `Frame` (or `ScrollingFrame`) controls the position and clipping of all its children. This is the foundation for things like inventory grids, stat panels, and sidebar menus.

```python
from lunaengine.ui.elements import Frame, Button, TextLabel
from lunaengine.core import Scene

class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        
        # Create a panel frame (acts as a container)
        self.inventory_panel = Frame(x=600, y=50, width=250, height=400)
        
        # Add children directly to the parent
        title = TextLabel(x=10, y=10, width=230, height=30, text="Inventory")
        slot1 = Button(x=10, y=50, width=100, height=100, text="Sword")
        slot2 = Button(x=120, y=50, width=100, height=100, text="Shield")
        
        self.inventory_panel.add_child(title)
        self.inventory_panel.add_child(slot1)
        self.inventory_panel.add_child(slot2)
        
        # Add the parent to the scene — children follow automatically
        self.add_ui_element(self.inventory_panel)
```

---

## Animated HUD Elements

A static HUD is functional. An animated HUD is memorable. Use tweens to slide health bars, fade in elements, and pulse danger indicators.

```python
from lunaengine.ui.tween import Tween, EasingType
from lunaengine.ui.elements import ProgressBar

class HUD(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.health_bar = ProgressBar(x=20, y=20, width=200, height=20, value=1.0)
        self.add_ui_element(self.health_bar)

    def player_took_damage(self, new_health_ratio: float):
        # Smoothly animate the health bar down
        Tween.create(self.health_bar)\
             .to(value=new_health_ratio, duration=0.5, easing=EasingType.CUBIC_OUT)\
             .play()
```

---

## The Notification System

LunaEngine has a built-in notification system you can use from anywhere in your game. No scene setup needed.

```python
class GameScene(Scene):
    def player_found_item(self, item_name):
        self.engine.show_success(f"Found: {item_name}!", duration=3.0)

    def player_died(self):
        self.engine.show_error("You Died!", duration=5.0)
    
    def objective_updated(self, text):
        self.engine.show_info(text, duration=4.0)
    
    def low_health_warning(self):
        self.engine.show_warning("Low Health!", duration=2.0)
```

For complex notification scenarios, use `show_notification()` for full control:

```python
from lunaengine.ui.notifications import NotificationPosition, NotificationType

self.engine.show_notification(
    text="Boss has appeared!",
    notification_type=NotificationType.WARNING,
    position=NotificationPosition.BOTTOM_CENTER,
    duration=4.0,
    show_progress_bar=True,
    on_click=lambda: self.camera.look_at_boss()
)
```

---

## Sliding Menu Patterns

A common UI pattern is a side-panel that slides in from off-screen when triggered. Combine this with the `on_complete` tween callback for chaining logic.

```python
class SettingsMenu(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        # Start the panel off-screen to the right
        self.panel = Frame(x=engine.width, y=0, width=300, height=engine.height)
        self.panel.visible = False
        self.add_ui_element(self.panel)
        self._is_open = False

    def open(self):
        self.panel.visible = True
        self._is_open = True
        Tween.create(self.panel)\
             .to(x=self.engine.width - 300, duration=0.4, easing=EasingType.CUBIC_OUT)\
             .play()

    def close(self):
        self._is_open = False
        Tween.create(self.panel)\
             .to(x=self.engine.width, duration=0.3, easing=EasingType.CUBIC_IN)\
             .set_callbacks(on_complete=lambda: setattr(self.panel, 'visible', False))\
             .play()
```

This pattern produces a clean, professional-feeling settings drawer that is commonly seen in polished commercial games.