"""Load a theme JSON outside LunaEngine's built-in theme directory.

Run from the repository root:
    python examples/ui/external_theme_demo.py examples/ui/external_theme.json
"""
from pathlib import Path
import sys

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import Button, TextLabel, ThemeManager
from lunaengine.ui.themes import ThemeType


class ExternalThemeScene(Scene):
    def __init__(self, engine, theme_name: str):
        super().__init__(engine)
        self.engine.set_global_theme(theme_name)
        self.add_ui_element(TextLabel(512, 150, "External Theme", 42, pivot=(0.5, 0)))
        self.add_ui_element(TextLabel(512, 215, f"Loaded theme: {theme_name}", 20, pivot=(0.5, 0)))
        button = Button(512, 310, 220, 50, "Theme Loaded", 22, pivot=(0.5, 0))
        button.set_on_click(lambda: self.engine.show_success("The external theme is active!"))
        self.add_ui_element(button)

    def update(self, dt):
        pass


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("external_theme.json")
    theme_name = ThemeManager.load_custom_theme(source, "external_demo", overwrite=True)
    engine = LunaEngine("External Theme Demo", 1024, 600, debug=True)
    engine.add_scene("demo", lambda e: ExternalThemeScene(e, theme_name))
    engine.set_scene("demo")
    print(f"Loaded {source} as '{theme_name}'. Available: {ThemeManager.get_theme_names()[-3:]}")
    engine.run()


if __name__ == "__main__":
    main()
