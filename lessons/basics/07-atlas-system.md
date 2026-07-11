# 07 - Atlas System

The **Atlas System** in LunaEngine v0.2.5 provides a centralized resource catalog for managing all your game's assets (textures, fonts, audio, and more). It acts as a single point of reference to load and retrieve files, automatically detecting their types, ensuring that you don't have to sprinkle hardcoded file paths throughout your code.

## Introduction to the Atlas

The `Atlas` class (found in `lunaengine.misc.atlas`) manages `AtlasItem` objects. Each item has a `name`, a `path`, and a `category` (like `TEXTURE`, `FONT`, `AUDIO`). 

By default, every `LunaEngine` instance creates its own `Atlas` upon initialization, accessible via `engine.atlas`.

### File Categories

When you add a file to the atlas, it checks the extension to determine its category automatically:
- **TEXTURE**: `.png`, `.jpg`, `.bmp`, `.dds`, etc.
- **FONT**: `.ttf`, `.otf`, `.woff`
- **AUDIO**: `.mp3`, `.wav`, `.ogg`
- **DATASTORE**: `.json`, `.db`, `.yaml`

## Using the Atlas

### 1. Adding Assets Manually

You can add items manually to the atlas via the engine's convenience methods:

```python
from lunaengine.core.engine import LunaEngine

engine = LunaEngine()

# Adding resources manually
engine.add_texture_to_atlas("player_sprite", "assets/player.png")
engine.add_font_to_atlas("main_font", "assets/fonts/Roboto.ttf")
engine.add_audio_to_atlas("bg_music", "assets/audio/bgm.ogg")
```

### 2. Auto-Discovery

A common pattern is to have the engine auto-discover everything inside an `assets` folder. You can add entire folders, or just iterate through files and add them with auto-detection:

```python
from pathlib import Path

assets_dir = Path("assets")
for file_path in assets_dir.rglob("*"):
    if file_path.is_file():
        # Using the file's name (without extension) as the atlas key
        engine.add_to_atlas(file_path.stem, file_path, auto_detect=True)
```

*(Note: LunaEngine also supports setting an `atlas_root` when creating the engine instance to help with default path resolution).*

## Retrieving Assets from the Atlas

Once assets are registered, other engine systems can load them effortlessly.

### Loading Textures & Spritesheets

The `SpriteSheet` class natively supports loading directly from the atlas:

```python
from lunaengine.graphics.spritesheet import SpriteSheet

# Retrieves "player_sprite" from the atlas, ensuring it is a TEXTURE
player_sheet = SpriteSheet.from_atlas("player_sprite", engine.atlas)
```

### Loading Fonts

The `FontManager` uses the engine's atlas to resolve custom font names. Once a font is added to the atlas, you can just use its name anywhere in the UI!

```python
from lunaengine.ui import FontManager

# Assuming "main_font" was added as an AtlasCategory.FONT
title_font = FontManager.get_font("main_font", font_size=32)
```

### General Retrieval

If you need the raw path or the `AtlasItem` object for your own purposes, you can use:

```python
item = engine.get_atlas_item("bg_music")
print(f"Loaded item {item.name} of category {item.category} at {item.path}")

# Or just get the path directly:
music_path = engine.get_atlas_path("bg_music", category="audio")
```

## Summary

The Atlas System simplifies asset management by:
1. Providing a centralized registry for all resources.
2. Auto-detecting resource types.
3. Tying directly into UI (fonts) and graphics (spritesheets) modules.

Using the Atlas from the very beginning of your project will make managing assets much cleaner as your game grows!
