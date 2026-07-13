# 06 - Themes and Styling

LunaEngine provides a powerful, pre-built theming system for UI customization. A Theme in LunaEngine contains styling rules for different UI elements (like colors, borders, shadows, and text settings) allowing you to change the look of your entire game with one line of code.

## Setting a Global Theme

The easiest way to style your UI is to apply a global theme to the engine. This will automatically update all UI elements currently on screen, and any new ones you create.

```python
from lunaengine.core.engine import LunaEngine

engine = LunaEngine()

# LunaEngine comes with many built-in themes (e.g. "neon", "dark", "light", "retro")
engine.set_global_theme("neon")
```

## Why Themes Matter

Themes let you:
- **Keep UI consistent:** All buttons, panels, and labels will share the same design language.
- **Quickly restyle menus:** Switching between "light" and "dark" modes is trivial.
- **Improve readability:** Themes define appropriate contrast and spacing automatically.

## Checking Available Themes

If you want to see a list of all themes (including any custom themes you've created), you can fetch them from the engine:

```python
# Returns a list of strings like ["dark", "light", "neon", ...]
available_themes = engine.get_theme_names()
print("Available Themes:", available_themes)
```

## Individual Element Styling

While a global theme styles everything, you can always override specific style properties on individual UI elements. For example, if you want a specific "Quit" button to be red regardless of the theme:

```python
from lunaengine.ui.elements import Button

quit_btn = Button(x=100, y=100, width=150, height=40, text="Quit")

# You can overwrite the background color directly
quit_btn.set_background_color((255, 50, 50))
```

For most cases, it is recommended to rely on the global theme and create a custom theme if you need extensive changes.