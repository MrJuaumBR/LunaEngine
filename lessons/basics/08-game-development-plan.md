# 08 - Game Development Plan

Before writing a single line of code, the best investment you can make is planning. A game without a plan usually becomes a never-ending project that never ships. This lesson walks you through how to approach building a LunaEngine game from idea to release.

---

## Phase 1: Concept (The Big Idea)

Start by answering these questions simply and concisely:

| Question | Example Answer |
|---|---|
| **What is the genre?** | Top-down RPG |
| **What is the core gameplay loop?** | Explore dungeon → fight enemies → get loot → repeat |
| **What is the player goal?** | Defeat the final boss and escape the dungeon |
| **What is the art style?** | Pixel art, 16x16 tiles |
| **What is the target scope?** | 1 dungeon, 3 enemy types, 1 boss, 5 items |

> **Tip:** The scope question is the most important. A small, polished game is infinitely better than a large, unfinished one.

---

## Phase 2: Architecture (How to Build It)

Now you plan how the code will be organized. With LunaEngine, the natural structure is **Scenes** and **Systems**.

### Recommended Scene Structure

```
GameEngine
├── BootScene      (loading screen, asset registration)
├── MainMenuScene  (play, settings, quit)
├── GameScene      (the actual game world)
│   ├── Camera
│   ├── Player
│   ├── EnemyManager
│   └── UILayer (HUD: health bar, score)
├── PauseScene     (overlay over GameScene)
└── GameOverScene
```

### Asset & Atlas Setup

Plan your asset folders and register them in `BootScene`:

```python
from lunaengine.core import Scene

class BootScene(Scene):
    def on_enter(self, previous_scene):
        # Register all assets into the Atlas
        self.engine.add_texture_to_atlas("player_run", "assets/player_run.png")
        self.engine.add_texture_to_atlas("tileset",    "assets/tileset.png")
        self.engine.add_audio_to_atlas("bgm",          "assets/bgm.ogg")
        self.engine.add_audio_to_atlas("sfx_hurt",     "assets/sfx_hurt.wav")
        self.engine.add_font_to_atlas("pixel_font",    "assets/PixelFont.ttf")
        
        # Once loading is done, switch to the main menu
        self.engine.set_scene("main_menu")
```

---

## Phase 3: Development Milestones

Break the project into milestones. Each milestone should be a **playable version** of the game.

**Milestone 0 – Technical Foundation (Day 1-2)**
- [ ] Engine initializes
- [ ] Scenes are wired up (boot → menu → game)
- [ ] Atlas loaded
- [ ] Basic player movement works in `GameScene`

**Milestone 1 – Core Loop (Week 1)**
- [ ] Player can move, attack
- [ ] 1 enemy type with basic AI
- [ ] Camera follows player

**Milestone 2 – Content (Week 2-3)**
- [ ] All 3 enemy types
- [ ] Loot system
- [ ] UI HUD (health bar, inventory)

**Milestone 3 – Polish (Week 4)**
- [ ] Particle effects for attacks and deaths
- [ ] Camera shake on impact
- [ ] Sound effects and background music
- [ ] Main menu and game over screen

**Milestone 4 – Release**
- [ ] Playtest and balance
- [ ] Package and release

---

## Phase 4: LunaEngine Checklist

Before starting to code, use this quick checklist:

- [ ] `LunaEngine` configured (title, resolution)
- [ ] All Scenes planned and files created
- [ ] Asset folder structure decided
- [ ] Atlas registration planned (in BootScene)
- [ ] `engine.set_scene()` flow mapped out
- [ ] Version number in `pyproject.toml` set

---

## Example: Minimal Skeleton

This is the minimal skeleton for a well-structured LunaEngine project:

```python
from lunaengine.core.engine import LunaEngine
from lunaengine.core.scene import Scene

class BootScene(Scene):
    def on_enter(self, prev):
        # TODO: Register atlas assets here
        self.engine.set_scene("menu")

class MenuScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        # TODO: Add buttons

class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        # TODO: Build the game world
    
    def update(self, dt):
        pass # Game logic

engine = LunaEngine(title="My Game", width=1280, height=720)
engine.add_scene("boot", BootScene)
engine.add_scene("menu", MenuScene)
engine.add_scene("game", GameScene)
engine.set_scene("boot")
engine.run()
```

Planning before coding will save you hours of refactoring later!
