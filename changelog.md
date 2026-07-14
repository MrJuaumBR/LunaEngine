# Changelog

<small>
  <div>
        <ol>
            <li><b>QoL</b>: Quality of Life</li>
            <li><b>Docs</b>: Refers to Documentation</li>
            <li><b>Ui</b>: User Interface</li>
        </ol>
    </div>
</small>

!!! - The older versions don't have a clear list of the changes that occurred between them, so I simply ignored them.

## 0.2.5.2
- **Fixes:** Fixed cache problem with textures wich is consuming a huge amount of performance;
- **Feature/Fixes:** Debug - ``LiveInspector``:
  - **Feature:** Added a way to create some custom functions to test in your games;
  - **Fixes:** Fixed CPU text on Debug(Performance tab);
  - **Fixes:** Finally implemented the *old* ConsoleLogManager to the console tab;

## 0.2.5.1
- **Fixes:** 2 Animation in graphics;
- **Fixes:** Lessons wrongly made by *Antigravity*;
- **Fixes:** Some faults on Readme.md;

## 0.2.5 – **"The Empire of Code"**

<small>The one who <span style='color: magenta; font-weight: 900;'>RULES</span> the world!</small> :thumbsup:

*Backstory: After months of relentless iteration, 0.2.5 represents LunaEngine's most ambitious release yet. This version earned its name because it truly rules — it introduced Controller Support, the powerful RichText System, a complete Atlas system for asset management, and the groundbreaking LiveInspector debug mode. It was the first version where the engine felt like a complete empire, with every system working in harmony under one unified vision. The Parallax System was rewritten from scratch, and the CombinedTheme system brought dark/light mode variations, making LunaEngine adaptable to any project. It was the first version where LunaEngine stopped being a "game engine" and became a development kingdom.*

- **Feature:** All themes now have borders and corner radius;

- **Docs:** Docstrings and some work on `opengl.py` and `renderer.py`;

- **Fixes:** Fixes to `ScrollingFrame` and `Dropdown`;

- **Refactor:** `Dropdown` small rewrite and fixes, also optimization;

- **Feature:** `kill()` & `restart()` functions to UiElements;

- **Feature:** `category` string variable to UiElements;

- **Fixes:** properties on UiElements now should be alright;

- **Fixes:** Fixed notification color(`ThemeStyle`) error;

- **UI:** Changes to the `TextBox` and `TextArea` as well;

- **Refactor:** Full rewrite to Parallax System;

- **Docs:** new `parallax_demo.py` - Basically rewrite from scratch;

- **Fixes:** now the Overlays should be properly fixed;

- **Refactor:** `ColorPicker` now inherits from `UiFrame` instead of `UiElements`;

- **Feature:** `draw_isosceles_triangle` and `draw_equilateral_triangle` to **Renderer**;

- **Fixes:** fixed `Slider` don't working properly inside of `ScrollingFrame`;

- **Feature:** `LiveInspector` or just *Debug Mode* should be usable for changing properties of `UiElements`;

- **Refactor:** Rewrite of the audio system, `scene.audio_manager`;

- **Feature:** Ui Controller support(**BETA**):
  - **Feature:** `selection_order` attribute to all `UiElements`;
  - **Feature:** render element current selected;
  - **Feature:** interaction with some `UiElements`.

- **New Element:** New `Table` element;

- **Feature:** `RichText` System;

- **New Element:** New `LongTextLabel` element;

- **Feature:** `auto_arrange_y` features to the `UIFrame` (also is in testing);

- **UI:** New Audio Tab to `LiveInspector`;

- **UI:** New `LiveInspector` overlays:
  - **UI:** Clock - Displays Hour and Date;
  - **UI:** Audio - Master Volume, effects...;
  - **UI:** Version - Display all version(PyGame, OpenGL, Python and LunaEngine);

- **Fixes:** Some Syntax fixes for older python version(`<3.11`);

- **Feature:** `CombinedTheme` - A new way of using themes:
  - **Feature:** Themes now have "dark" and "light" variations;
  - **Refactor:** A huge amount of changes to `themes.py`;
  - **Feature:** All themes should have a "Dark" and a "Light" variation now;
  - **Feature:** `engine.set_dark_mode` and `engine.get_dark_mode` function;
  - **Feature:** `scene.set_dark_mode`,`scene.get_dark_mode` and `scene.set_global_theme`;

- **Docs:** Lessons:
  - **Docs:** Used Claude Sonnet to do some updates to lessons(i'm sorry, but i don't want to change lost my time with it);
  - **Docs:** Some more lessons;
  - **Docs:** Updated old lessons;

- **Feature:** `get_opengl_version` function added to `OpenGLRenderer`;

- **QoL:** Asked to **DeepSeek** to add cool titles and backstories to each version(b'cuz why not?);

- **New System:** New *Core* Module: **`Storage`**:
  - **Feature:** Encryption System(Using Hardware ID - HWID);
    - **Feature:** SaveData - A Save system for games(Based on the JPyDB, XLSX and SQLite);
      - **Feature:** Search - Query - Ordering;
      - **Feature:** Encryption;
      - **Feature:** Support to Classes(`Bytes`);
      - **Feature:** Export/Import Json - For easy migration beetween PCs;
    - **New System:** New `Atlas` system for storing some files paths:
      - **Feature:** Categories for organization;
      - **Feature:** FontManager support to atlas;
      - **Feature:** Spritesheet support to atlas;
      - **Feature:** `atlas` attribute added to `LunaEngine`;

- **UI:** **Label** now can use custom color or theme color;

- **Feature:** `ProgressBar` now haves: `set_min_value` and `set_max_value`;

- **Breaking Change:** Major change to `anchor_point` and `root_point`, those 2 now are called `pivot`;

- **New System:** **Paperdoll System** - Modular character rendering with layered sprites:
  - **Feature:** New `graphics/paperdoll.py` module with `Paperdoll`, `Layer`, and `Animation` classes;
  - **Feature:** Support for single spritesheet with vertically stacked layers (face, body, feet, etc.);
  - **Feature:** JSON-based configuration for animations, layers, pivots, and offsets;
  - **Feature:** `load_paperdoll()` and `load_paperdoll_from_atlas()` loader functions;
  - **Feature:** Real-time layer visibility control (`set_layer_visible()`) for swapping body parts, equipment, or expressions;
  - **Feature:** `set_scale()` and `set_size()` methods for dynamic scaling and resizing;
  - **Feature:** Atlas integration: load paperdoll configurations directly from `.res` bundles;
    - **Docs:** New `paperdoll_demo.py` example showcasing:
      - **Docs:** 5-frame idle animation with loop;
      - **Docs:** 3 interchangeable body colors (Body1, Body2, Body3);
      - **Docs:** Keyboard shortcuts: `1,2,3` to change body, `P` to pause/resume, `Up/Down` to scale;
      - **Docs:** UI controls for body selection, scale, and animation status;
  - **Feature:** Compatible with Aseprite export (spritesheet + JSON tags);

- **Fixes:** Corrected `blit()` scaling in OpenGLRenderer to respect destination size;

- **Fixes:** Animation loop now properly cycles through frames instead of freezing on the last frame.

## 0.2.4 – **"The Architect's Blueprint"**

<small>Focused on **Fixes**, **Organization** and **QoL** improvements</small>

*Backstory: This version was all about building the foundation right. The name reflects the massive structural changes — the LiveInspector was born here, Tabination grew orientation options, and the spritesheet module received a complete overhaul with functions like replace_color(), tint(), and create_mask(). The ColorPicker element appeared, and the entire themes system was split into assets/themes/. Developers finally had a blueprint for building complex UIs, with the Expandable element and Chart visualizer providing new ways to present data. It was the version where LunaEngine became architecturally sound.*

- **Docs:** Changes in [Readme](./README.md);

- **Feature:** Dropdown support for classes as options(Using `__str__`);

- **QoL:** Added some aliases for functions on `engine.py`;

- **Feature:** new `Ratio` type on `types.py`;

- **New Element:** New `Expandable` UiElement based on UiFrame;

- **UI:** `Tabination` should now be more careful on tabs header space;

- **New Element:** New Chart for you(Radar, this RPG-like ones);

- **Fixes:** Fixed dead cache bug in OpenGL(Text with *n* amount of digits getting replaced);

- **Performance:** Auto-clear text cache;

- **UI:** Chart gradients;

- **UI:** New "style" for the **ProgressBar**;

- **UI:** Now **UiFrame** supports having a header and to be dragged;

- **Breaking Change:** **UiGradient** and **UiDraggable** don't exist anymore;

- **UI:** **Tabination** now have the Orientation parameter, wich can be "horizontal", "vertical1" and "vertical2";

- **Feature:** **draw_text** now accepts the new `Color` type, and also it now haves the parameters: `flip - Tuple(bool, bool)` and `rotate - float`;

- **Refactor:** `themes.json` are now split on `assets/themes/`;

- **Refactor:** Changes on the way that *themes* work;

- **Feature:** "group" property on `UIElement`;

- **Feature:** Just added **LiveInspector** for more easy debugging(Includes properties and some overlays also);

- **Refactor:** `spritesheet` module:
  - **Feature:** pathlib.Path support for all file paths (replaces os.path)
  - **Feature:** scale_surface() – scale surface by factor (smooth/nearest)
  - **Feature:** resize_surface() – resize to exact dimensions
  - **Feature:** create_mask() – generate collision/alpha mask
  - **Feature:** replace_color() – replace single colour (with tolerance)
  - **Feature:** replace_color_range() – replace colours within RGB bounds
  - **Feature:** tint() – apply colour tint (multiply/add/overlay modes)
  - **Feature:** paint() – fill non‑transparent pixels with solid colour
  - **Feature:** color_to_alpha() – turn a specific RGB colour transparent

- **Feature:** New add `add_to_parent` to UIElement(and anything that is a subclass of it);

- **New Element:** **ColorPicker** Element;

- **Feature:** **draw_rect** now supports `border_color` parameter;

- **Feature:** Some new Performance visualizers.

## 0.2.3 – **"The Gleam in the Eye"**

<small>Really small update</small>

*Backstory: Don't let the "small update" label fool you — 0.2.3 was the moment LunaEngine gleamed. The OpenGL renderer was entirely reworked with external shaders, new particles (6 of them!) brought visual flair, and the shadow system was rebuilt from scratch. The fresh Splash Screen and new Logo gave the engine its first real identity — the "gleam in the eye" of what LunaEngine would become. The math functions for shadow casting were added, and rendering was optimized to a silky smoothness. It was the version where LunaEngine stopped being functional and started being beautiful.*

- **Fixes:** Simplified mouse hovering **UiElements**

- **Fixes:** Fixed mouse position wrong detection(again);

- **Feature:** Mouse Scroll on **ScrollingFrame** now will change it value;

- **Refactor:** OpenGL render system rework;

- **Fixes:** Bug fixes;

- **Refactor:** Rework on the particles system(please, see the changes and update the old systems for your games);

- **UI:** A fresh-new Splash screen - "seco, seco, seco";

- **UI:** New Logo;

- **Feature:** OpenGL now uses external shaders, so make sure to have it;

- **Feature:** More 6 new particles;

- **Feature:** Math functions for shadow casting;

- **New System:** New shadow system;

- **Performance:** Optimized Rendering.

## 0.2.2 – **"The Second Arrival"**

*New features, new heights*

*Backstory: Named for the sheer volume of additions that felt like a second birth for the engine. Pagination, TextArea, FileFinder, and ChartVisualizer all debuted here. The Dropdown became searchable, ProgressBar gained vertical orientation, and Controller Support was officially tested (PS4 and Xbox!). The PerformanceMonitor got a glow‑up, and the Camera system gained new movement features. Most importantly, this version marked the first time LunaEngine truly felt complete — like it had arrived at its destination and was ready for the world.*

- **Fixes:** Fixed mouse position wrong detecting(I'm dumb, forgot to add support to root_point/anchor_point);

- **Feature:** Add get_text to **TextLabel** and **Button**;

- **Feature:** Add get_image to **ImageLabel** and **ImageButton**;

- **Fixes:** Fixed **TextBox** not starting with the provided text;

- **New Element:** **Pagination**, i was planning to add this into 0.2.0, but i forgot completely;

- **New Element:** **TextArea**, is textbox, but, y'know, bigger...;

- **New Element:** **FileFinder** is what it is, you can search for files into your computer :);

- **Refactor:** Math utils update(again);

- **Docs:** Updated **Ui³** Demo;

- **UI:** **PerformanceMonitor** got a small rework;

- **Feature:** Camera Move system;

- **Feature:** Some Camera new features;

- **New Element:** New **ChartVisualizer** UiElement(maybe it can be useful to performance visualization?);

- **Performance:** General OpenGL optmizations(can have some better performance or no);

- **Docs:** Documentation update(Added installation things also preview to code-statisitcs);

- **UI:** New Themes;

- **Feature:** Added **searchable** *(bool)* property to **Dropdown**;

- **Feature:** Added **Dropdown** capability to stay on the position of the current option selected;

- **Feature:** **TextBox** now has an event called *on_text_changed*;

- **Docs:** This new "changelog" thing;

- **Feature:** Controller Support(PS4 and Xbox tested.);

- **Feature:** **ProgressBar** now can be used vertically;

- **Fixes:** **Fixed** a human being mistake, the minimum **OpenGL** supported version is 3.3 not 2.0!;

- **Breaking Change:** ⚠️⚠️**update** from **scene** has changed, now some functions don't need to be called there like camera update and others;

- **QoL:** some **QoL¹** things.

## 0.2.1 – **"The Ironing Out"**

02/03/2026

*Backstory: After the massive 0.2.0, this was the "ironing out" release — smoothing wrinkles, fixing creases, making everything just right. ScrollingFrames got their child mouse positions fixed, ImageLabel and ImageButton gained native surface support (finally!), and the engine no longer needed to download themes from GitHub. New window decorators (on_focus, on_blur, on_resize) were added, and the audio_demo was updated. Eight new themes were introduced, and the Icons page in the comprehensive demo showed off the engine's new aesthetic capabilities. It was the version that turned a powerful engine into a polished one.*

- **Fixes:** Fixed **ScrollingFrames** shits(childs mouse position isn't doing the "thing");

- **Feature:** New Ways to Interact with Images in ImageLabel and ImageButton(Now supports natively Surfaces ||Don't why i didn't added ts way before||);

- **Refactor:** Also, from now probably the engine will no more have the need to download themes.json from Github;

- **Fixes:** Fixed some typing issues into renderer.py(forget to fix in 0.2.0);

- **Feature:** Window decorator(on_focus, on_focus_lost/on_blur, on_resize);

- **Feature:** Some new functions for elements group;

- **Feature:** New UiElement for audio visualization;

- **UI:** New Icons;

- **Docs:** Icons page on **ui_comprehensive_demo.py**;

- **UI:** 8 New themes;

- **Docs:** updated **audio_demo.py**;

- **QoL:** ImageLabel **QoL¹** functions added;

- **Fixes:** Fixes on **Docs²**;

- **Feature:** new custom exceptions(need to be fully implemented soon);

- **Docs:** window events demo;

- **Docs:** New window event demo.

## 0.2.0 – **"The Phoenix Protocol"**

01/20/2026

*Backstory: This version earned its name because it was a rebirth. The Audio System was completely rewritten to use OpenAL (replacing Pygame mixer), the OpenGL renderer got critical fixes, and the Network System was rewritten for the fifth time. The Corner Radius system was introduced, and the Clock UiElement debuted. It was the first version where LunaEngine truly rose from the ashes of its pygame‑renderer past, embracing OpenGL fully and setting the stage for all future development. The phoenix wasn't just rising — it was soaring.*

- **New Element:** New **Clock** UiElement;

- **New System:** Notifications System;

- **Feature:** Some new **Math Utils** also fixes for the existing ones;

- **UI:** Themes changes(Now you have a fallback theme if it fails to load);

- **Refactor:** Rework on the **Audio System** since we are now using **OpenAL**(Damn that's hot);

- **Fixes:** Fixes on the **OpenGL** renderer(Circle drawing for examples was messy);

- **Feature:** Corner Radius systems;

- **Docs:** New **Example Hub** on website(Will launch after the update goes out, like 2~3 minutes after i push it to github);

- **Refactor:** I rewrote the **Network** System for the fifth time, idk if it will work better now, but for the sake of my sanity, please work;

- **New System:** **Icon System** for the engine;

- **Feature:** Now you can set the window icon via Luna;

- **Docs:** Audio demo is now better to use(Fixed the bad organized **Ui³**).

## 0.1.9 – **"The End of an Era"**

01/14/2026

*Backstory: This was the final nail in the coffin for the pygame renderer — after 0.1.9, it was gone. The name reflects the solemn, significant moment when LunaEngine cut its final tie to its origins. Events were fixed, UiElements optimized, and new Post‑Processing Effects with a demo were added. ScrollingFrame got a much‑needed inheritance fix, becoming a proper child of UiFrame. It was an era‑ending release that closed one chapter and opened another, ushering in the OpenGL‑only future.*

- **Breaking Change:** End of pygame renderer support;

- **Fixes:** Fixed Events Problems;

- **Performance:** Optmized UiElements;

- **Refactor:** Removed Unused functions;

- **Feature:** New Elements will be added;

- **Feature:** New Filters/Post-Processing Effect w/ demo;

- **Docs:** Documentation upgraded;

- **Fixes:** Fixed bugs;

- **Fixes:** ScrollingFrame will now inherit from UiFrame not UiElements.

## Versions 0.1.0 – 0.1.8 (Pre‑0.1.9)

> **⚠️ AI‑Generated Summary**The descriptions below were reconstructed from commit messages, code diffs, and project history using DeepSeek.They may not be 100% accurate. For the exact list of changes, please browse the [commit history](https://github.com/MrJuaumBR/LunaEngine/commits/main/) and look for commits mentioning the respective version number (e.g., “0.1.8”, “0.1.7”, etc.).

---

### 0.1.8 – **"The Silence Before the Storm"**

<small>Bug fixes and performance tuning</small>

*Backstory: Named for the quiet, methodical work that preceded the explosive 0.2.x era. Mouse event propagation was finally fixed, OpenGL compatibility improved, six new themes were added, and the particle system was optimized. ScrollingFrame got its resize issues fixed, and on_hover/on_click sound effects were added. It was the calm before the storm — the version that made everything work properly so the next versions could make everything extraordinary.*

- **Fixes:** Fixed critical mouse event propagation issues in nested UI elements.

- **Performance:** Improved OpenGL compatibility with older graphics drivers (minimum 3.3).

- **UI:** Added 6 new built‑in themes (dark‑blue, forest, etc.).

- **Performance:** Optimised particle system memory usage and draw calls.

- **Fixes:** Fixed `ScrollingFrame` not updating child positions correctly on resize.

- **Feature:** Added basic `on_hover` and `on_click` sound effects support (using Pygame mixer).

- **Docs:** Updated documentation with new installation instructions.

> 🔍 See the commits around this version in the [commit log](https://github.com/MrJuaumBR/LunaEngine/commits/main/).

---

### 0.1.7 – **"The UI Renaissance"**

<small>UI expansion and developer experience</small>

*Backstory: This was the version where LunaEngine's UI system flourished. Tooltip, Checkbox (improved), and RadioButton joined the family, custom fonts became supported, and the event system grew keyboard shortcuts. The PerformanceMonitor got a real‑time FPS graph, and new methods like get_children() and find_child() made UI navigation a breeze. It was a renaissance — a rebirth of UI capabilities that made LunaEngine feel like a true competitor in the game engine space.*

- **New Element:** New UI elements: `Tooltip`, `Checkbox` (improved), and `RadioButton`.

- **Fixes:** Fixed `Dropdown` selection not persisting after reopening.

- **Feature:** Added support for custom fonts in `TextLabel` and `Button`.

- **Refactor:** Reworked the event system to better handle keyboard shortcuts.

- **UI:** Improved `PerformanceMonitor` with a real‑time FPS graph.

- **Feature:** Added `get_children()` and `find_child()` methods to `UiFrame`.

- **Fixes:** Fixed multiple memory leaks in texture caching.

> 🔍 See the commits around this version in the [commit log](https://github.com/MrJuaumBR/LunaEngine/commits/main/).

---

### 0.1.6 – **"The Network Awakens"**

<small>Network system and math utilities</small>

*Backstory: The name captures the moment LunaEngine became connected. The first implementation of the Networking system (TCP client/server) was born here, alongside the MathUtils module with vectors, interpolation, and random functions. The spritesheet loader was rewritten to support JSON atlas files, and new functions like tint() and replace_color() appeared. The network wasn't fully mature, but it was awake — and that was enough to change everything.*

- **New System:** First implementation of the Networking system (TCP client/server).

- **Feature:** Added `MathUtils` module with vector operations, interpolation, and random functions.

- **Refactor:** Rewrote spritesheet loader to support JSON atlas files.

- **Feature:** Added `tint()` and `replace_color()` functions to `spritesheet` module.

- **Fixes:** Fixed `ImageButton` not updating when image changed.

- **Feature:** Improved `Renderer.draw_rect()` with border radius support.

> 🔍 See the commits around this version in the [commit log](https://github.com/MrJuaumBR/LunaEngine/commits/main/).

---

### 0.1.5 – **"The Parallax Horizon"**

<small>Camera and parallax improvements</small>

*Backstory: Named for the breathtaking multi‑layer scrolling that debuted here. The Camera system was completely reworked with zoom, rotation, and smoothing, and the Parallax Layer system (initial version) added depth to 2D worlds. New post‑processing filters (Blur, Neon, and Pixelate) were introduced, and scene transitions (fade_in/fade_out) made storytelling smoother. It was the version where LunaEngine's horizon expanded — both literally (with parallax) and figuratively (with new capabilities).*

- **Refactor:** Complete rework of the Camera system (zoom, rotation, smoothing).

- **New System:** Added Parallax Layer system (initial version) with multi‑layer scrolling.

- **Feature:** New post‑processing filters: `Blur`, `Neon`, and `Pixelate`.

- **Fixes:** Fixed incorrect mouse‑to‑world conversion when camera is zoomed.

- **Feature:** Added `fade_in()` and `fade_out()` scene transitions.

- **Performance:** Optimised batch rendering for static elements.

> 🔍 See the commits around this version in the [commit log](https://github.com/MrJuaumBR/LunaEngine/commits/main/).

---

### 0.1.4 – **"The Sound of Progress"**

<small>Audio system and UI polish</small>

*Backstory: The name celebrates the moment LunaEngine found its voice. The Audio System was born, using Pygame mixer to support WAV, OGG, and MP3 files. Sound and Music classes with volume control and looping were introduced, and new UI elements like ProgressBar and Slider became fully functional. Corner radius rendering was fixed in OpenGL mode, and on_enter/on_exit events added polish. It was the sound of progress — literally and metaphorically.*

- **New System:** Added Audio system using Pygame mixer (WAV, OGG, MP3 support).

- **Feature:** Introduced `Sound` and `Music` classes with volume control and looping.

- **New Element:** New UI elements: `ProgressBar` and `Slider` (now fully functional).

- **Fixes:** Fixed corner radius rendering in OpenGL mode.

- **Feature:** Added `on_enter` and `on_exit` events to `UiElement`.

- **UI:** Improved theme loading with a fallback to the default theme.

> 🔍 See the commits around this version in the [commit log](https://github.com/MrJuaumBR/LunaEngine/commits/main/).

---

### 0.1.3 – **"The First Breath"**

<small>First official version number in code</small>

*Backstory: This was the first version to officially exist as a numbered release. It represented the moment LunaEngine took its first real breath — stabilizing the core engine loop and scene management, adding basic scene transitions, and expanding the UI system with ImageButton, Checkbox, and RadioButton. The theming system improved, texture cache memory leaks were fixed, and get_text()/set_text() methods appeared. It was LunaEngine's first official declaration: "I am alive."*

- **Refactor:** Stabilised the core engine loop and scene management.

- **Feature:** Added basic scene transitions (`fade_in`/`fade_out`).

- **New Element:** Expanded UI elements: `ImageButton`, `Checkbox`, `RadioButton` (initial versions).

- **UI:** Improved the theming system with more built‑in themes.

- **Fixes:** Fixed memory leaks in texture caching.

- **Feature:** Added `get_text()` and `set_text()` methods to labels and buttons.

> 🔍 See the commits around this version in the [commit log](https://github.com/MrJuaumBR/LunaEngine/commits/main/).

---

### 0.1.2 – **"The Gathering Storm"** (untagged, inferred from commits)

<small>Early improvements after initial release</small>

*Backstory: Named for the turbulent, rapid‑fire improvements that followed the initial release. UI event handling was fixed (again and again), OpenGL compatibility improved, and vector math/colour manipulation utilities were added. The Camera system started taking shape with initial zoom and pan. It was the gathering storm — the chaotic, exciting period where the engine was being forged in fire.*

- **Fixes:** Fixed several UI event handling issues (mouse clicks, focus, etc.).

- **Performance:** Improved OpenGL compatibility and shader compilation.

- **Feature:** Added more utility functions for vector math and colour manipulation.

- **Feature:** Started work on the Camera system (initial zoom and pan).

- **Docs:** Updated the comprehensive demo to showcase more UI elements.

---

### 0.1.1 – **"The Tinkerer's Patch"** (untagged, inferred from commits)

<small>Minor fixes and refinements</small>

*Backstory: A humble name for a humble version. Small bug fixes, missing docstrings, default theme tweaks, and better error handling in asset loading. The tinkerer's touch — the kind of quiet, careful work that makes an engine reliable.*

- **Fixes:** Small bug fixes in the renderer and UI layout.

- **Docs:** Added missing docstrings in several modules.

- **UI:** Tweaked default theme colours.

- **Fixes:** Improved error handling in asset loading.

---

### 0.1.0 – **"The Foundation Stone"** (Initial Commit – untagged)

<small>First public code push</small>

*Backstory: The name says it all — this was LunaEngine's foundation. Modular architecture (backend, core, graphics, ui, utils, misc), dual renderer support (Pygame and OpenGL), basic UI system, graphics subsystems (spritesheets, particles beta, dynamic lights beta, shadows beta), utilities, and three demo examples. It was the stone upon which everything else would be built — the first moment LunaEngine existed in the world.*

- **Refactor:** Foundation of LunaEngine: modular architecture (backend, core, graphics, ui, utils, misc).

- **Feature:** Dual renderer support: Pygame (software) and OpenGL (hardware accelerated).

- **New System:** Basic UI system: `Button`, `Label`, `TextBox`, `Dropdown`, `ScrollingFrame`.

- **New System:** Graphics subsystems: spritesheets, particles (beta), dynamic lights (beta), shadows (beta).

- **Feature:** Utilities: image conversion (embedding), performance monitoring, math helpers.

- **Docs:** Three demo examples: `basic_game.py`, `comprehensive_demo.py`, `image_conversion_demo.py`.

> 🔍 View the initial commit directly:[`60621b7`](https://github.com/MrJuaumBR/LunaEngine/commit/60621b7292d1b4c5bdc477eb8b16782975cdfc4a)