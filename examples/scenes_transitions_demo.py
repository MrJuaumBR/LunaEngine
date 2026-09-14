"""
scenes_transitions_demo.py - Scene Transition System Demo

This demo demonstrates LunaEngine's new scene transition system.
It features:
- 4 scenes with different pastel background colors
- Dropdown to select target scene
- Dropdown to select transition effect (Fade, Slide, Zoom, etc.)
- Button to trigger the transition
- Title centered at the top of each scene
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import (
    Dropdown, Button, TextLabel, UiFrame,
    ThemeType, ThemeManager
)
from lunaengine.backend.transition import TransitionType
from lunaengine.misc.icons import Icons


# ----------------------------------------------------------------------------
# Base scene class that provides common UI: scene selector, effect selector,
# and a transition button.
# ----------------------------------------------------------------------------
class TransitionDemoScene(Scene):
    """Base scene for the transition demo."""

    def __init__(self, engine: LunaEngine, bg_color: tuple, scene_name: str):
        super().__init__(engine)
        self.bg_color = bg_color
        self.scene_name = scene_name

        # --- Title (top center) ---
        self.title = TextLabel(
            self.engine.width // 2, 30,
            f"Scene: {scene_name}",
            font_size=32,
            color=(255, 255, 255),
            pivot=(0.5, 0),
            use_theme_color=False
        )
        self.add_ui_element(self.title)

        # --- Control panel (centered, with a frame) ---
        panel_width = 400
        panel_height = 160
        panel_x = (self.engine.width - panel_width) // 2
        panel_y = (self.engine.height - panel_height) // 2 + 40

        self.panel = UiFrame(panel_x, panel_y, panel_width, panel_height)
        self.panel.set_background_color((40, 40, 50, 200))
        self.panel.set_border((100, 100, 150), 1)
        self.panel.set_corner_radius(10)
        self.add_ui_element(self.panel)

        # --- Scene selection dropdown ---
        self.scene_dropdown = Dropdown(
            20, 20, 160, 30,
            options=["Teal", "Yellow", "Green", "Red"],
            font_size=18,
            label="Target:",
            label_position="left",
            label_size=18
        )
        self.panel.add_child(self.scene_dropdown)

        # --- Effect selection dropdown ---
        effect_options = [
            "None",
            "Fade",
            "Slide Left",
            "Slide Right",
            "Slide Up",
            "Slide Down",
            "Zoom In",
            "Zoom Out",
            "Orbital Left",
            "Orbital Right",
            "Morph",
            "Flash"
        ]
        self.effect_dropdown = Dropdown(
            20, 60, 160, 30,
            options=effect_options,
            font_size=18,
            label="Effect:",
            label_position="left",
            label_size=18
        )
        self.panel.add_child(self.effect_dropdown)

        # --- Transition button ---
        self.transition_btn = Button(
            220, 20, 140, 70,
            text="Go!",
            font_size=24,
            icon=Icons.CLICK
        )
        self.transition_btn.set_on_click(self._on_transition_clicked)
        self.panel.add_child(self.transition_btn)

        # --- Info label (shows current selection) ---
        self.info_label = TextLabel(
            20, 100,
            "Select target and effect, then click Go!",
            font_size=14,
            color=(180, 200, 255),
            use_theme_color=False
        )
        self.panel.add_child(self.info_label)

        # Map dropdown text to TransitionType
        self._effect_map = {
            "None": TransitionType.NONE,
            "Fade": TransitionType.FADE,
            "Slide Left": TransitionType.SLIDE_LEFT,
            "Slide Right": TransitionType.SLIDE_RIGHT,
            "Slide Up": TransitionType.SLIDE_UP,
            "Slide Down": TransitionType.SLIDE_DOWN,
            "Zoom In": TransitionType.ZOOM_IN,
            "Zoom Out": TransitionType.ZOOM_OUT,
            "Orbital Left": TransitionType.ORBITAL_LEFT,
            "Orbital Right": TransitionType.ORBITAL_RIGHT,
            "Morph": TransitionType.MORPH,
            "Flash": TransitionType.FLASH,
        }

        # Map scene name to registered scene name (lowercase)
        self._scene_map = {
            "Teal": "teal",
            "Yellow": "yellow",
            "Green": "green",
            "Red": "red",
        }

    def _on_transition_clicked(self):
        """Handle the transition button click."""
        target_name = self.scene_dropdown.options[self.scene_dropdown.selected_index]
        effect_text = self.effect_dropdown.options[self.effect_dropdown.selected_index]
        effect = self._effect_map.get(effect_text, TransitionType.NONE)
        target_scene = self._scene_map.get(target_name)

        if target_scene:
            # Update info label
            self.info_label.set_text(f"Transitioning to {target_name} with {effect_text}...")
            # Trigger the transition
            self.engine.transition_to(target_scene, effect=effect, duration=0.8)
        else:
            self.info_label.set_text(f"Error: Unknown scene '{target_name}'")

    def render(self, renderer):
        """Fill the background with the scene's color."""
        renderer.clear()
        renderer.fill_screen(self.bg_color)

    def update(self, dt):
        """Update the control panel (no extra logic needed)."""
        pass


# ----------------------------------------------------------------------------
# Define the four concrete scenes with their background colors.
# ----------------------------------------------------------------------------
class TealScene(TransitionDemoScene):
    def __init__(self, engine):
        super().__init__(engine, (173, 216, 230), "Teal")  # Light pastel teal

class YellowScene(TransitionDemoScene):
    def __init__(self, engine):
        super().__init__(engine, (255, 255, 204), "Yellow")  # Pastel yellow

class GreenScene(TransitionDemoScene):
    def __init__(self, engine):
        super().__init__(engine, (204, 255, 204), "Green")   # Pastel green

class RedScene(TransitionDemoScene):
    def __init__(self, engine):
        super().__init__(engine, (255, 204, 204), "Red")     # Pastel red


# ----------------------------------------------------------------------------
# Main entry point.
# ----------------------------------------------------------------------------
def main():
    engine = LunaEngine(
        title="LunaEngine - Scene Transitions Demo",
        width=1024,
        height=720,
        icon=Icons.FIRE,
        debug=True
    )
    engine.fps = 60

    # Register all scenes
    engine.add_scene("teal", TealScene)
    engine.add_scene("yellow", YellowScene)
    engine.add_scene("green", GreenScene)
    engine.add_scene("red", RedScene)

    # Start with the teal scene (no transition)
    engine.set_scene("teal")

    engine.run()


if __name__ == "__main__":
    main()
