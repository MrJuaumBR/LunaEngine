# 26 - Hot Reload

Hot reload lets you edit a file while the game is running and see the change within about a second, without restarting. It watches **scene files** and **module files** you explicitly opt in with `watch_scene` and `watch_module`.

Use it while iterating on balance numbers, tuning a stats file, or rebuilding a level layout. Do **not** ship it enabled — it's a development tool.

## Enabling it

Constructor:

```python
engine = LunaEngine("My Game", 1024, 720, hot_reload=True)
```

At runtime, via the LiveInspector: **Settings** tab → **Hot Reload** switch. Flipping it on starts the poll; flipping it off stops it.

The engine polls every 0.5 seconds. Polling is driven by the existing `Timer` system — no threads, no background processes. A poll is one `os.path.getmtime()` call per watched file, which the OS serves from its metadata cache. Cost is effectively zero while nothing is changing.

## Watching a scene

```python
engine.watch_scene("game")              # by registered name
engine.watch_scene(GameScene)           # by class
```

`watch_scene` accepts a registered scene name (`str`) or the scene subclass itself. Both resolve to the scene's source file.

When that file changes:

1. Old scene: `on_exit()`
2. New instance: `new_class(engine)` — full `__init__` runs again
3. New scene: `on_enter()`
4. Registered callbacks fire

**No state is preserved.** Score, position, which tab is open, focused widget — everything resets. This is intentional. State preservation is a rabbit hole (renamed fields, changed types, stale references); a fresh rebuild is honest about what happened.

If you need state to survive, expose a hook on the scene itself:

```python
class DialogueScene(Scene):
    def on_hot_reload_snapshot(self) -> dict:
        return {"node_id": self.current_node.id, "seen": self.seen_nodes}

    def on_hot_reload_restore(self, data: dict):
        self.current_node = self.nodes[data["node_id"]]
        self.seen_nodes = data["seen"]
```

That pattern is optional and lives with the scene, not the engine.

## Watching a module

```python
import stats

engine.watch_module(stats)
engine.watch_module("balance")                  # by import name
engine.watch_module("src/balance.py")           # by file path (str)
engine.watch_module(Path("src/balance.py"))     # Path
engine.watch_module(atlas_item)                 # path-backed AtlasItem
```

All six forms resolve to a source file. If the module isn't imported yet, use the path form — the engine imports it on first reload.

When the file changes, `importlib.reload(module)` runs. The module object is mutated in place, so any code that holds a reference to it sees the new values.

**Packed `.res` AtlasItems raise `ValueError`.** Files inside a bundle aren't individual on disk, so there's nothing to reload.

## Callbacks

```python
def refresh(self, module):
    self.damage = module.BASE_DAMAGE
    self.crit = module.CRIT_MULT

engine.on_module_reload("stats", refresh)


def on_scene_rebuilt(self, new_scene):
    self.engine.show_notification("Scene reloaded", "info", duration=1.0)

engine.on_scene_reload("game", on_scene_rebuilt)
```

The module callback receives the reloaded module object. The scene callback receives the new scene instance.

For a module that's just constants, you don't need a callback at all — read the values directly:

```python
import stats
# Read through the module, not through a local copy.
damage = stats.BASE_DAMAGE
```

## The `from` import trap

This will not hot-reload:

```python
from stats import BASE_DAMAGE   # snapshot, never updates
```

This will:

```python
import stats
damage = stats.BASE_DAMAGE      # reads the current module attribute
```

`from X import Y` copies the value into your namespace at import time. Reloading `stats` replaces `stats.BASE_DAMAGE`, but the local `BASE_DAMAGE` still points at the old value. Use `import module; module.NAME` for anything you want to reload.

If a scene or UI class caches a value at `__init__`, add a module-reload callback to refresh the cached copy. There's no way for the engine to know which attributes are cached.

## Watched modules don't cascade

If `stats.py` imports `curves.py` and you edit `curves.py`, reloading `stats` does **not** re-execute `curves`. Python caches imported modules.

You have two options:

1. Watch `curves` too, in dependency order.
2. Live with it — most files you edit don't have runtime imports you're also editing.

For typical balance iterations (edit `stats.py`, save, see the change) this never comes up.

## Syntax errors don't kill the game

If you save a file mid-edit and it has a syntax error, `importlib.reload` raises `SyntaxError`. The engine catches it, logs it to the LiveInspector console pane at `ERROR` level, and **keeps the old version running**. Your game doesn't crash.

```python
# What you see in the console:
# [12:34:56] File "stats.py", line 4
# [12:34:56]     BASE_DAMAGE = = 10
# [12:34:56]                   ^
# [12:34:56] SyntaxError: invalid syntax
```

Fix the file, save again, and the next poll reloads it cleanly. You'll lose a second, not the run.

## The debounce

An editor often writes a file in multiple steps: truncate, write header, write body, close. Without protection, the poll can catch a half-written file. The engine requires the file's mtime to be stable for **one full poll cycle** (~0.5s) before reloading. So a save that finishes in 50ms reloads on the next poll. A save that takes 2 seconds reloads 0.5s after it stops changing.

You can watch the console pane if you want to see reloads land.

## A working example

`examples/hot_reload_demo.py` shows the full pattern.

**`stats.py`:**

```python
PLAYER_SPEED = 200
MAX_HEALTH = 100
STARTING_GOLD = 50
```

**The scene:**

```python
import stats

class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self._apply_stats()
        self.label = TextLabel(20, 20, "", 20)
        self.add_ui_element(self.label)

    def _apply_stats(self):
        self.speed = stats.PLAYER_SPEED
        self.max_hp = stats.MAX_HEALTH
        self.gold = stats.STARTING_GOLD

    def update(self, dt):
        self.label.set_text(
            f"speed={self.speed}  hp={self.max_hp}  gold={self.gold}"
        )

class HotReloadDemo(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        engine.hot_reload = True
        engine.watch_module("stats")
        engine.on_module_reload("stats", lambda m: self.game._apply_stats())
        engine.watch_scene("game")
```

Change `STARTING_GOLD = 50` to `STARTING_GOLD = 77`, save, and the label updates within a second. Change something in `hot_reload_scenes.py`, save, and the whole scene rebuilds.

## What to watch for

- **Editors that write via rename** can confuse the mtime check on some filesystems. If a save doesn't trigger a reload, try saving twice.
- **`__pycache__`** doesn't matter — `importlib.reload` bypasses the cache for watched modules.
- **Callbacks are one-shot per reload.** If you add the same callback twice, it fires twice. Remove callbacks via the manager if you need to.
- **The whole scene rebuilds.** Scene-local data structures, cached textures, tweens in flight — all gone. That's the point.

## When not to use it

- **During a playtest you don't want to interrupt.** Turn it off. Reloading mid-boss-fight is worse than restarting.
- **On target hardware.** Polling is cheap but non-zero, and the debug hooks add surface area. Ship with `hot_reload=False`.
- **For code you didn't opt in.** Only watched files reload. Everything else is cached and unaffected.

The design is deliberate: **you choose what reloads, when.** The engine doesn't guess.