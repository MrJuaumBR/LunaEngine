"""Scenes used by hot_reload_demo.py.

Edit this file while the demo is running to exercise scene reconstruction.
The engine calls the old scene's on_exit(), creates a fresh scene instance,
and calls the new scene's on_enter() without preserving scene state.
"""
from lunaengine.core import Scene
from lunaengine.ui import Button, TextLabel, UiFrame
import stats


class MenuScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self.add_ui_element(TextLabel(512, 120, "Hot Reload Demo", 42, pivot=(0.5, 0)))
        self.add_ui_element(TextLabel(
            512, 185,
            "Edit hot_reload_scenes.py to rebuild this scene while running.",
            18, pivot=(0.5, 0), color=(190, 200, 220),
        ))
        button = Button(412, 250, 200, 48, "Open Game", 20)
        button.set_on_click(lambda: self.engine.set_scene("game"))
        self.add_ui_element(button)


class GameScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        self._build_ui()

    def _build_ui(self):
        self.add_ui_element(TextLabel(512, 70, "Game Scene", 34, pivot=(0.5, 0)))
        self.stats_label = TextLabel(512, 150, "", 24, pivot=(0.5, 0))
        self.add_ui_element(self.stats_label)
        self.help_label = TextLabel(
            512, 215,
            "Edit examples/stats.py and watch these values update.",
            18, pivot=(0.5, 0), color=(190, 200, 220),
        )
        self.add_ui_element(self.help_label)
        back = Button(412, 290, 200, 44, "Back to Menu", 18)
        back.set_on_click(lambda: self.engine.set_scene("menu"))
        self.add_ui_element(back)
        self.refresh_stats(stats)

    def refresh_stats(self, module):
        """Refresh the visible constants after stats.py is reloaded."""
        self.stats_label.set_text(
            f"PLAYER_SPEED = {module.PLAYER_SPEED}    "
            f"MAX_HEALTH = {module.MAX_HEALTH}    "
            f"STARTING_GOLD = {module.STARTING_GOLD}"
        )

    def on_enter(self, previous_scene=None):
        super().on_enter(previous_scene)
        self.refresh_stats(stats)
