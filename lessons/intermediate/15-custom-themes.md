# 15 - Custom Themes

LunaEngine's theme system is designed for extensibility. While the 50+ built-in themes cover most needs, you can create your own theme that perfectly matches your game's visual identity — from a gritty sci-fi look to a cozy pastel adventure.

---

## Understanding the Theme Structure

A `UITheme` is a dataclass where every field is a `ThemeStyle`. A `ThemeStyle` holds:
- `color`: An `(R, G, B)` tuple (0–255).
- `alpha`: Opacity from `0.0` (transparent) to `1.0` (opaque).
- `corner_radius`: How rounded the corners of elements are (pixels).
- `border_width`: Width of the element border (pixels).
- `blur`: Blur amount (pixels).

---

## Creating a Custom Theme in Python

The cleanest way to create a theme in Python is to construct a `UITheme` directly using `ThemeStyle`.

```python
from lunaengine.ui.themes import ThemeManager, ThemeType, UITheme, ThemeStyle

# Helper function to keep things tidy
def s(rgb, alpha=1.0, radius=0, border=0, blur=0):
    return ThemeStyle(color=rgb, alpha=alpha, corner_radius=radius,
                      border_width=border, blur=blur)

# Define the full theme
MY_CYBER_THEME = UITheme(
    # Buttons: Glowing teal style
    button_normal=s((0, 200, 200), radius=4),
    button_hover=s((0, 230, 230), radius=4),
    button_pressed=s((0, 160, 160), radius=4),
    button_disabled=s((80, 80, 80)),
    button_text=s((10, 10, 10)),
    button_border=s((0, 255, 255), border=2),

    # Dropdowns
    dropdown_normal=s((30, 30, 50), radius=4),
    dropdown_hover=s((40, 40, 65), radius=4),
    dropdown_expanded=s((20, 20, 40), radius=4),
    dropdown_text=s((200, 255, 255)),
    dropdown_option_normal=s((25, 25, 45)),
    dropdown_option_hover=s((35, 35, 60)),
    dropdown_option_selected=s((0, 180, 180)),
    dropdown_border=s((0, 200, 200), border=1),

    # Sliders
    slider_track=s((30, 30, 50)),
    slider_thumb_normal=s((0, 200, 200), radius=8),
    slider_thumb_hover=s((0, 230, 230), radius=8),
    slider_thumb_pressed=s((0, 160, 160), radius=8),
    slider_text=s((200, 255, 255)),

    # Labels & Background
    label_text=s((200, 255, 255)),
    background=s((10, 10, 25)),
    background2=s((15, 15, 35)),
    text_primary=s((200, 255, 255)),
    text_secondary=s((100, 200, 200)),

    # Switches
    switch_track_on=s((0, 200, 200)),
    switch_track_off=s((60, 60, 80)),
    switch_thumb_on=s((255, 255, 255)),
    switch_thumb_off=s((180, 180, 200)),

    # Dialogs
    dialog_background=s((15, 15, 35), radius=8),
    dialog_border=s((0, 200, 200), border=2),
    dialog_text=s((200, 255, 255)),
    dialog_name_bg=s((0, 150, 150)),
    dialog_name_text=s((255, 255, 255)),
    dialog_continue_indicator=s((0, 200, 200)),

    # Tooltips
    tooltip_background=s((10, 10, 25), alpha=0.9, radius=4),
    tooltip_border=s((0, 200, 200), border=1),
    tooltip_text=s((200, 255, 255)),

    # Notifications
    notification_success_background=s((0, 150, 100)),
    notification_success_border=s((0, 200, 130)),
    notification_success_text=s((255, 255, 255)),
    notification_info_background=s((0, 100, 180)),
    notification_info_border=s((0, 150, 230)),
    notification_info_text=s((255, 255, 255)),
    notification_warning_background=s((200, 150, 0)),
    notification_warning_border=s((255, 200, 0)),
    notification_warning_text=s((0, 0, 0)),
    notification_custom_background=s((100, 0, 200)),
    notification_custom_border=s((150, 0, 255)),
    notification_custom_text=s((255, 255, 255)),
    notification_error_background=s((180, 0, 50)),
    notification_error_border=s((230, 0, 70)),
    notification_error_text=s((255, 255, 255)),

    # Borders & Accents
    border=s((0, 200, 200), border=1),
    border2=s((0, 150, 150), border=1),
    accent1=s((0, 200, 200)),
    accent2=s((255, 50, 150)),
)
```

---

## Registering and Using the Custom Theme

Once defined, register it with the `ThemeManager` and apply it with the engine:

```python
from lunaengine.core.engine import LunaEngine
from lunaengine.core.scene import Scene

# Register under a custom key (use any unused ThemeType, e.g. CYBERPUNK is already built-in,
# so use one that doesn't exist yet, or add a new Enum entry for production projects)
# For quick testing, we can register directly in the _themes dict:
ThemeManager._themes["cyber"] = MY_CYBER_THEME

# Now apply it to the entire engine
engine = LunaEngine(title="Cyber Game", width=1280, height=720)

class MenuScene(Scene):
    def on_enter(self, prev):
        # Apply your theme — all UI elements will adopt it instantly
        self.engine.set_global_theme("cyber")
```

> **Note:** For a production game, you should also create a JSON theme file (see below) so the theme can be hot-reloaded without changing Python code.

---

## Creating a Theme as a JSON File

You can also define themes as JSON files and place them in `lunaengine/assets/themes/`. The engine auto-discovers them on startup.

```json
{
  "variants": {
    "dark": {
      "button_normal":  { "color": [0, 200, 200, 1.0], "cornerRadius": 4 },
      "button_hover":   { "color": [0, 230, 230, 1.0], "cornerRadius": 4 },
      "button_pressed": { "color": [0, 160, 160, 1.0], "cornerRadius": 4 },
      "button_text":    { "color": [10, 10, 10, 1.0] },
      "background":     { "color": [10, 10, 25, 1.0] },
      "accent1":        { "color": [0, 200, 200, 1.0] },
      "accent2":        { "color": [255, 50, 150, 1.0] }
    },
    "light": {
      "button_normal":  { "color": [0, 180, 180, 1.0], "cornerRadius": 4 },
      "background":     { "color": [230, 240, 250, 1.0] },
      "accent1":        { "color": [0, 150, 150, 1.0] }
    }
  }
}
```

Save this as `CYBER.json` in your themes directory. It will be auto-loaded as `ThemeType.CYBER` (if you add `CYBER = "cyber"` to the `ThemeType` enum).

---

## Switching Between Dark and Light Mode

If your custom JSON theme has both `dark` and `light` variants, you can toggle between them at runtime:

```python
from lunaengine.ui.themes import ThemeManager

# Toggle dark/light globally
ThemeManager.set_dark_mode(True)   # Use "dark" variant
ThemeManager.set_dark_mode(False)  # Use "light" variant
```

This is perfect for a settings screen where the player can choose their preferred display mode!
