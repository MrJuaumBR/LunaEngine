# 25 - Audio Groups

LunaEngine's audio system has three layers: the **manager** (owned by the scene), **channels** (individual playback streams), and **groups** (volume/mute/effect buses that channels belong to). Groups landed in 0.2.6.2 and are how you implement "music volume", "SFX volume", "mute everything except voice", and similar controls without tracking every channel yourself.

## The hierarchy

```
AudioManager
  ├── master (implicit)
  ├── default
  ├── music
  ├── sfx
  ├── voice
  └── ui
```

Groups nest. A group inherits volume and mute from its parent and from `master`. The effective volume of a channel is:

```
channel_volume × group_volume × parent_group_volume × master_volume
```

You set volume in one place and every channel that belongs to that group follows.

## Getting a group

```python
audio = self.engine.audio

music = audio.get_group("music")
sfx   = audio.get_group("sfx")
```

`master`, `default`, and `music` are created automatically. Others are created on first `get_group` call.

## Volume

```python
music.set_volume(0.5)          # 50%
sfx.set_volume(1.0)
audio.set_master_volume(0.8)   # affects everything
```

To read:

```python
current = music.get_volume()
```

Volume is a scalar from `0.0` to `1.0`, matching the framework convention for normalized values.

## Mute

```python
audio.set_group_mute("music", True)    # silence the music group
audio.set_group_mute("music", False)   # restore
```

Muting a group is independent of its volume. Unmute and the previous volume is back.

Master mute:

```python
audio.set_master_mute(True)
```

## Effects

Groups can host an OpenAL EFX effect that applies to every channel routed through them.

```python
audio.set_group_effect("music", "reverb", 0.4)
audio.set_group_effect("music", "echo", 0.3)
audio.set_group_effect("music", "chorus", 0.5)
```

Supported names: `reverb`, `echo`, `chorus`, `flanger`, `distortion`, `pitch_shift`.

To remove:

```python
audio.clear_group_effect("music")
```

**EFX availability is device-dependent.** OpenAL's EFX extension isn't present on every platform. When a device rejects an effect, the backend records the failure in the source's diagnostic state instead of silently claiming success. Check before relying on it:

```python
success = audio.set_group_effect("music", "reverb", 0.5)
if not success:
    # fall back: no reverb on this device
    pass
```

## Assigning channels to groups

Channels are obtained per-playback. You can name them or let the manager assign them.

```python
# Named channel, routed to a group
music_channel = audio.get_channel("music")
music_channel.set_group(music)

# Play and route in one step
sfx_channel = audio.play("sfx_hit", volume=0.8, group="sfx")
```

Channels retain their own volume, pan, pitch, and loop settings — those are per-channel. Group volume multiplies on top of the channel's own value.

## A complete example

```python
class GameScene(Scene):
    def on_enter(self, previous_scene):
        audio = self.engine.audio

        # Configure the buses once
        audio.set_master_volume(1.0)
        audio.get_group("music").set_volume(0.4)
        audio.get_group("sfx").set_volume(0.9)
        audio.get_group("ui").set_volume(0.6)

        # Start background music through the music bus
        audio.play_music("bgm_game", fade_in=1.5)

    def play_hit(self):
        self.engine.audio.play("sfx_hit", volume=0.8, group="sfx")

    def play_click(self):
        self.engine.audio.play("sfx_click", volume=1.0, group="ui")

    def toggle_music(self):
        audio = self.engine.audio
        muted = audio.get_group_mute("music")
        audio.set_group_mute("music", not muted)
```

The scene only ever sets the group volumes once. Every subsequent `play` call routes through the right bus automatically.

## Settings-menu integration

Groups are the right abstraction for a settings menu:

```python
def on_master_slider(self, value):
    self.engine.audio.set_master_volume(value)

def on_music_slider(self, value):
    self.engine.audio.get_group("music").set_volume(value)

def on_sfx_slider(self, value):
    self.engine.audio.get_group("sfx").set_volume(value)
```

Save them to your `Savedata` and reapply at startup. No per-channel bookkeeping.

## LiveInspector

The Audio tab in the LiveInspector shows every active source with its current volume, pan, and playing state. Useful for tracking down a stuck channel or finding which group is silencing a sound.

## Notes on OpenAL

- Sources are pooled. Playing a sound grabs a free source; when the pool is exhausted, the oldest finished source is reused.
- EFX effects allocate a slot and an effect object. Replacing an effect cleans up the previous slot and effect first.
- Sources with a mono buffer support true pan. Stereo buffers pan via balance instead, which is approximate.

If audio fails to initialize (no device, missing native library), `engine.audio` is still a valid object but playback calls become no-ops. The engine doesn't crash on headless CI or in a browser without an audio device.

## Common patterns

**Ducking music during dialogue:**

```python
music = self.engine.audio.get_group("music")
music.set_volume(0.15)   # low during dialogue
# ... dialogue ends ...
music.set_volume(0.4)    # restore
```

**Muting everything except voice:**

```python
audio.set_group_mute("music", True)
audio.set_group_mute("sfx", True)
audio.set_group_mute("voice", False)
```

**Per-scene volume presets:**

```python
class MenuScene(Scene):
    def on_enter(self, previous_scene):
        self.engine.audio.get_group("music").set_volume(0.3)
        self.engine.audio.get_group("sfx").set_volume(0.8)

class BossScene(Scene):
    def on_enter(self, previous_scene):
        self.engine.audio.get_group("music").set_volume(0.6)
        self.engine.audio.get_group("sfx").set_volume(1.0)
```

The group API is small on purpose. Volume and mute are the two knobs you reach for 95% of the time; effects are for the other 5%.