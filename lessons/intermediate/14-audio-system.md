# 14 - Audio System

LunaEngine v0.2.5 features a powerful, OpenAL-based audio system (`lunaengine.core.audio`) with named channels, volume curves, audio effects, and a global event system.

## Core Concepts

The `AudioManager` is already created for you and is accessible via `engine.audio`. It provides:
- **Named Channels**: Isolated playback contexts (e.g., `"music"`, `"sfx"`, `"ambience"`)
- **Audio Curves**: Keyframe-based animation of volume, pitch, and pan
- **EFX Effects**: Reverb, echo, chorus, and more (if your hardware supports it)

Two channels are always created by default: `"default"` and `"music"` (which loops).

---

## 1. Loading Sounds

Before playing anything, you must load sounds into the manager. For a clean workflow, do this in your `BootScene` using the Atlas:

```python
from lunaengine.core import Scene

class BootScene(Scene):
    def on_enter(self, prev):
        # Load audio files directly
        self.engine.audio.load_sound("bgm",       "assets/bgm.ogg",       category="music")
        self.engine.audio.load_sound("sfx_jump",  "assets/sfx_jump.wav",  category="sfx")
        self.engine.audio.load_sound("sfx_hit",   "assets/sfx_hit.wav",   category="sfx")
        self.engine.audio.load_sound("ambience",  "assets/forest.ogg",    category="ambience")
        
        self.engine.set_scene("menu")
```

---

## 2. Playing Music & Sound Effects

```python
class GameScene(Scene):
    def on_enter(self, prev):
        # Play looping background music with a 2-second fade-in
        self.engine.audio.play_music("bgm", volume=0.7, fade_in=2.0)
    
    def player_jumped(self):
        # Play a one-shot sound effect on the default channel
        self.engine.audio.play("sfx_jump", volume=1.0, pitch=1.0)
    
    def player_hit(self):
        # Play with a slight pitch variation for variety
        import random
        pitch = random.uniform(0.9, 1.1)
        self.engine.audio.play("sfx_hit", volume=0.8, pitch=pitch)
```

---

## 3. Named Channels for Mixing

Named channels let you manage independent audio streams with their own volume and effects.

```python
    def on_enter(self, prev):
        # Create a dedicated ambience channel
        self.engine.audio.create_channel("ambience", volume=0.4)
        
        # Play ambient sound looping on the new channel
        self.engine.audio.play("ambience", channel="ambience", loop=True)
```

### Volume Control

```python
    def update(self, dt):
        # Adjust master volume on-the-fly
        if self.player_is_in_cave:
            # Gradually lower the music to 30% over 1 second
            self.engine.audio.get_channel("music").set_volume(0.3, duration=1.0)
        else:
            self.engine.audio.get_channel("music").set_volume(0.8, duration=1.0)
```

---

## 4. Audio Effects (EFX)

If your system has OpenAL EFX support, you can apply real-time effects:

```python
    def player_entered_cave(self):
        # Add reverb to all channels (cave atmosphere)
        self.engine.audio.set_global_reverb(0.8)
    
    def player_left_cave(self):
        # Remove reverb
        self.engine.audio.set_global_reverb(0.0)
```

Available effects: `reverb`, `echo`, `chorus`, `flanger`, `distortion`, and `pitch_shift`.

---

## 5. Audio Curves

For cinematic moments, you can animate audio properties with keyframe curves:

```python
from lunaengine.core.audio import AudioCurve

# A curve that drops volume from 1.0 to 0.0 over 3 seconds (like fading out at game over)
fade_out = AudioCurve(
    property_name='volume',
    keyframes=[(0.0, 1.0), (3.0, 0.0)],  # (time_seconds, value)
    interpolation='smoothstep'
)

music_channel = self.engine.audio.get_channel("music")
music_channel.apply_curve(fade_out)
```

---

## 6. Audio Events

React to audio events with callbacks:

```python
from lunaengine.core.audio import AudioEvent

def on_music_complete(channel, **kwargs):
    print("Music track finished! Starting next track...")
    channel.manager.play_music("bgm_level2")

music_ch = self.engine.audio.get_channel("music")
music_ch.on_event(AudioEvent.PLAYBACK_COMPLETED, on_music_complete)
```

---

## 7. Cleanup

Always call `cleanup()` when your game exits (the engine does this for you on `shutdown()`):

```python
engine.audio.cleanup()  # Stops all sounds and frees resources
```

The audio system is fully independent from the rendering pipeline — you can drive it entirely from `update()` callbacks and event handlers.
