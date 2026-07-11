# 22 - Combining Systems

This is where everything comes together. Real games are not a collection of isolated features — they are a coherent experience where the camera, UI, audio, particles, tweens, and scenes all communicate with each other.

---

## The Architecture of a Combined Game

The key insight is that each system should react to **events** rather than being polled in a single monolithic `update()`:

```
Player.take_damage(amount)
  ├── camera.add_trauma(0.5)           # Camera shake
  ├── engine.audio.play("sfx_hit")     # Sound effect
  ├── self.particles.emit(50)          # Blood particles
  ├── tween health_bar down            # HUD update
  └── engine.show_warning("Low HP!")   # Notification (if < 20%)
```

---

## A Complete Example: Player Taking Damage

This example wires the camera, audio, particles, tweens, and notifications together through one method call.

```python
from lunaengine.core import Scene, LunaEngine
from lunaengine.core.engine import LunaEngine
from lunaengine.ui.elements import ProgressBar
from lunaengine.ui.tween import Tween, EasingType
from lunaengine.graphics.camera import CameraShakeType
from lunaengine.backend import FilterType

class GameScene(Scene):
    MAX_HEALTH = 100
    
    def __init__(self, engine):
        super().__init__(engine)
        self.player_health = self.MAX_HEALTH
        
        # HUD
        self.health_bar = ProgressBar(x=20, y=20, width=200, height=18, value=1.0)
        self.add_ui_element(self.health_bar)
        
        # Damage vignette (start invisible)
        self.damage_filter = engine.renderer.add_vignette(intensity=0.0)

    def player_take_damage(self, amount: int):
        self.player_health = max(0, self.player_health - amount)
        ratio = self.player_health / self.MAX_HEALTH

        # 1. Camera shake — intensity scales with damage
        trauma = amount / self.MAX_HEALTH
        self.camera.add_trauma(trauma)

        # 2. Sound effect
        self.engine.audio.play("sfx_hit", volume=0.8)

        # 3. Animate HUD health bar
        Tween.create(self.health_bar)\
             .to(value=ratio, duration=0.4, easing=EasingType.CUBIC_OUT)\
             .play()

        # 4. Flash the screen red
        self.damage_filter.intensity = 0.8

        # 5. Conditional warning notification
        if ratio < 0.2:
            self.engine.show_warning("Critical Health!", duration=2.0)
        
        # 6. Death check
        if self.player_health <= 0:
            self.player_die()

    def player_die(self):
        # Dramatic death: grayscale + music fade out + scene switch after delay
        self.engine.renderer.add_grayscale(intensity=1.0)
        self.engine.audio.get_channel("music").set_volume(0.0, duration=2.0)
        
        # Switch to game over after 2 seconds
        from lunaengine.ui.tween import Tween
        class _Delayed:
            x = 0.0
        dummy = _Delayed()
        Tween.create(dummy)\
             .to(x=1.0, duration=2.0)\
             .set_callbacks(on_complete=lambda: self.engine.set_scene("game_over"))\
             .play()

    def update(self, dt):
        # Fade out the damage vignette
        if self.damage_filter.intensity > 0:
            self.damage_filter.intensity = max(0.0, self.damage_filter.intensity - dt * 3.0)
        
        # Update audio (required each frame)
        self.engine.audio.update(dt)
```

---

## Scene Transition Checklist

When designing scene transitions (e.g. Menu → Game), follow this pattern:

1. **`on_exit` of outgoing scene**: Stop music, clean up timers.
2. **`on_enter` of incoming scene**: Reset state, start music with fade-in, slide in UI elements.

```python
class MenuScene(Scene):
    def on_exit(self, next_scene):
        # Fade music out before leaving
        self.engine.audio.get_channel("music").set_volume(0.0, duration=0.5)

class GameScene(Scene):
    def on_enter(self, previous_scene):
        # Fade music in when arriving
        self.engine.audio.play_music("bgm_game", fade_in=1.5)
        
        # Slide camera from top
        self.camera.position.y = -500
        from lunaengine.graphics.camera import InterpolationType
        self.camera.interpolation_type = InterpolationType.CUBIC_OUT
```

---

By thinking of your game as **a network of systems reacting to events**, you'll write code that is modular, easy to extend, and a joy to maintain. LunaEngine's modular design is built exactly for this.