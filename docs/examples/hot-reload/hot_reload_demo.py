"""LunaEngine hot-reload demonstration.

Run from the repository root:
    python examples/hot_reload_demo.py

While running, edit ``examples/stats.py`` and save it. The game label updates
on the next stable hot-reload poll (normally within about one second). To
trigger a scene reload, edit ``examples/hot_reload_scenes.py`` and save it;
the active scene is reconstructed from its new class with fresh state.
"""
from pathlib import Path
import sys

# Keep this example runnable directly from the repository root.
EXAMPLES_DIR = Path(__file__).resolve().parent
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))
REPO_ROOT = EXAMPLES_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lunaengine.core import LunaEngine
from lunaengine.misc.icons import Icons
import hot_reload_scenes
import stats


def main():
    engine = LunaEngine(
        "LunaEngine Hot Reload Demo",
        1024,
        600,
        icon=Icons.ENGINE,
        show_splash=False,
        hot_reload=True,
    )
    engine.add_scene("menu", hot_reload_scenes.MenuScene)
    engine.add_scene("game", hot_reload_scenes.GameScene)
    engine.watch_scene("menu")
    engine.watch_scene("game")
    engine.watch_module("stats")

    def refresh_stats(reloaded_module):
        # Update the imported module binding too, so a later scene reload sees
        # the same fresh constants rather than its old module object.
        hot_reload_scenes.stats = reloaded_module
        current_game = engine.scenes.get("game")
        if current_game is not None and hasattr(current_game, "refresh_stats"):
            current_game.refresh_stats(reloaded_module)

    engine.on_module_reload("stats", refresh_stats)
    engine.set_scene("menu")
    engine.run()


if __name__ == "__main__":
    main()
