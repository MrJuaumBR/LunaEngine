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

!!! The older versions don't have a clear list of the changes that occurred between them, so I simply ignored them.

## 0.2.4
<small>Focused on **Fixes**, **Organization** and **QoL** improvments</small>
- Changes in [Readme](./README.md);
- Dropdown support for classes as options(Using `__str__`);
- Added some aliases for functions on `engine.py`;
- new `Ratio` type on `types.py`;
- New `Expandable` UiElement based on UiFrame;
- `Tabination` should now be more careful on tabs header space;
- New Chart for you(Radar, this RPG-like ones);
- Fixed dead cache bug in OpenGL(Text with *n* amount of digits getting replaced);
- Auto-clear text cache;
- Chart gradients;
- New "style" for the **ProgressBar**;
- Now **UiFrame** supports having a header and to be dragged;
- **UiGradient** and **UiDraggable** don't exist anymore;
- **Tabination** now have the Orientation parameter, wich can be "horizontal", "vertical1" and "vertical2";
- **draw_text** now accepts the new ``Color`` type, and also it now haves the parameters: ``flip - Tuple(bool, bool)`` and ``rotate - float``;
- ``themes.json`` are now split on ``assets/themes/``;
- Changes on the way that *themes* work;
- "group" property on `UIElement`;
- Just added **LiveInspector** for more easy debugging(Includes properties and some overlays also);
- ``spritesheet`` module:
  - pathlib.Path support for all file paths (replaces os.path)
  - scale_surface() – scale surface by factor (smooth/nearest)
  - resize_surface() – resize to exact dimensions
  - create_mask() – generate collision/alpha mask
  - replace_color() – replace single colour (with tolerance)
  - replace_color_range() – replace colours within RGB bounds
  - tint() – apply colour tint (multiply/add/overlay modes)
  - paint() – fill non‑transparent pixels with solid colour
  - color_to_alpha() – turn a specific RGB colour transparent
- New add ``add_to_parent`` to UIElement(and anything that is a subclass of it);
- **ColorPicker** Element;
- **draw_rect** now supports ``border_color`` parameter;
- Some new Performance visualizers.

## 0.2.3 
<small>Really small update</small>
- Simplified mouse hovering **UiElements**
- Fixed mouse position wrong detection(again);
- Mouse Scroll on **ScrollingFrame** now will change it value;
- OpenGL render system rework;
- Bug fixes;
- Rework on the particles system(please, see the changes and update the old systems for your games);
- A fresh-new Splash screen - "seco, seco, seco";
- New Logo;
- OpenGL now uses external shaders, so make sure to have it;
- More 6 new particles;
- Math functions for shadow casting;
- New shadow system;
- Optimized Rendering.

## 0.2.2
- Fixed mouse position wrong detecting(I'm dumb, forgot to add support to root_point/anchor_point);
- Add get_text to **TextLabel** and **Button**;
- Add get_image to **ImageLabel** and **ImageButton**;
- Fixed **TextBox** not starting with the provided text;
- **Pagination**, i was planning to add this into 0.2.0, but i forgot completely;
- **TextArea**, is textbox, but, y'know, bigger...;
- **FileFinder** is what it is, you can search for files into your computer :);
- Math utils update(again);
- Updated **Ui³** Demo;
- **PerformanceMonitor** got a small rework;
- Camera Move system;
- Some Camera new features;
- New **ChartVisualizer** UiElement(maybe it can be useful to performance visualization?);
- General OpenGL optmizations(can have some better performance or no);
- Documentation update(Added installation things also preview to code-statisitcs);
- New Themes;
- Added **searchable** *(bool)* property to **Dropdown**;
- Added **Dropdown** capability to stay on the position of the current option selected;
- **TextBox** now has an event called *on_text_changed*;
- This new "changelog" thing;
- Controller Support(PS4 and Xbox tested.);
- **ProgressBar** now can be used vertically;
- **Fixed** a human being mistake, the minimum **OpenGL** supported version is 3.3 not 2.0!
- ⚠️⚠️**update** from **scene** has changed, now some functions don't need to be called there like camera update and others;
- some **QoL¹** things.

## 0.2.1
02/03/2026

- Fixed **ScrollingFrames** shits(childs mouse position isn't doing the "thing");
- New Ways to Interact with Images in ImageLabel and ImageButton(Now supports natively Surfaces ||Don't why i didn't added ts way before||);
- Also, from now probably the engine will no more have the need to download themes.json from Github;
- Fixed some typing issues into renderer.py(forget to fix in 0.2.0);
- Window decorator(on_focus, on_focus_lost/on_blur, on_resize);
- Some new functions for elements group;
- New UiElement for audio visualization;
- New Icons;
- Icons page on **ui_comprehensive_demo.py**;
- 8 New themes;
- updated **audio_demo.py**;
- ImageLabel **QoL¹** functions added;
- Fixes on **Docs²**;
- new custom exceptions(need to be fully implemented soon);
- window events demo;
- New window event demo.

## 0.2.0
01/20/2026

- New **Clock** UiElement;
- Notifications System;
- Some new **Math Utils** also fixes for the existing ones;
- Themes changes(Now you have a fallback theme if it fails to load);
- Rework on the **Audio System** since we are now using **OpenAL**(Damn that's hot);
- Fixes on the **OpenGL** renderer(Circle drawing for examples was messy);
- Corner Radius systems;
- New **Example Hub** on website(Will launch after the update goes out, like 2~3 minutes after i push it to github);
- I rewrote the **Network** System for the fifth time, idk if it will work better now, but for the sake of my sanity, please work;
- **Icon System** for the engine;
- Now you can set the window icon via Luna;
- Audio demo is now better to use(Fixed the bad organized  **Ui³**).

## 0.1.9
01/14/2026

- End of pygame renderer support;
- Fixed Events Problems;
- Optmized UiElements;
- Removed Unused functions;
- New Elements will be added;
- New Filters/Post-Processing Effect w/ demo;
- Documentation upgraded;
- Fixed bugs;
- ScrollingFrame will now inherit from UiFrame not UiElements.