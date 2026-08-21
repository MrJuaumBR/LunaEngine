"""
Atlas Demo - Resource Bundle & Asset Catalog Test
"""

import sys
import os
import random
import io
import pygame
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine
from lunaengine.ui import *
from lunaengine.ui.elements.base import FontManager
from lunaengine.graphics.spritesheet import SpriteSheet, Animation
from lunaengine.misc import AtlasCategory

# ------------------------------------------------------------
# Placeholder asset generators
# ------------------------------------------------------------

def generate_placeholder_texture(name: str, size: int = 128) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
    surf.fill(color)
    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 4)
    pygame.draw.line(surf, (255, 255, 255), (0, 0), (size, size), 3)
    try:
        font = pygame.font.SysFont(None, max(14, size // 8))
        text = font.render(name[:8], True, (0, 0, 0))
        surf.blit(text, (size//2 - text.get_width()//2, size//2 - text.get_height()//2))
    except:
        pass
    return surf

def generate_placeholder_audio(name: str, duration: float = 0.5, freq: float = 440.0) -> bytes:
    import numpy as np
    import wave
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * freq * t)
    tone = (tone * 32767).astype(np.int16)
    with io.BytesIO() as wav_io:
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(tone.tobytes())
        return wav_io.getvalue()

# ------------------------------------------------------------
# Main Demo Scene
# ------------------------------------------------------------

class AtlasDemoScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.engine = engine
        self.atlas = engine.atlas

        self.selected_asset_name = None
        self.preview_image = None
        self.preview_text_label = None
        self.preview_audio_button = None
        self.preview_spritesheet_anim = None

        self.setup_ui()
        self.register_default_assets()
        self.refresh_asset_list()

        self.bundle_loaded = self.atlas.is_bundle_loaded()
        self.update_bundle_status()

    def on_enter(self, previous_scene=None):
        self.bundle_loaded = self.atlas.is_bundle_loaded()
        self.update_bundle_status()
        self.refresh_asset_list()

    # ------------------------------------------------------------
    # Asset Registration
    # ------------------------------------------------------------

    def register_default_assets(self):
        examples_dir = Path(__file__).parent

        # Texture
        texture_file = examples_dir / "tiki_texture.png"
        if texture_file.exists():
            self.atlas.add_texture("tiki", texture_file)
        else:
            import tempfile
            surf = generate_placeholder_texture("Tiki", 128)
            tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            pygame.image.save(surf, tmp.name)
            self.atlas.add_texture("tiki", tmp.name)

        # Font
        font_file = examples_dir / "fonts" / "OpenSans.ttf"
        if font_file.exists():
            self.atlas.add_font("opensans", font_file)

        # Audio
        audio_file = examples_dir / "explosion.wav"
        if audio_file.exists():
            self.atlas.add_audio("explosion", audio_file)
        else:
            import tempfile
            data = generate_placeholder_audio("explosion", 0.5, 440)
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            tmp.write(data)
            tmp.close()
            self.atlas.add_audio("explosion", tmp.name)

        self.refresh_asset_list()

    def add_asset_from_file(self, path: str):
        path = Path(path)
        if not path.exists():
            return False
        try:
            self.atlas.add_to_atlas(path.stem, path, auto_detect=True)
            self.refresh_asset_list()
            return True
        except Exception as e:
            print(f"Failed to add asset: {e}")
            return False

    # ------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------

    def setup_ui(self):
        self.engine.set_global_theme(ThemeType.DEFAULT)

        title = TextLabel(512, 30, "Atlas Resource Demo", 36, pivot=(0.5, 0))
        self.add_ui_element(title)

        self.main_tabs = Tabination(25, 80, 980, 650, 20)
        self.main_tabs.add_tab("Assets")
        self.main_tabs.add_tab("Preview")
        self.main_tabs.add_tab("Bundle")

        self.setup_assets_tab()
        self.setup_preview_tab()
        self.setup_bundle_tab()

        self.add_ui_element(self.main_tabs)

        self.fps_label = TextLabel(self.engine.width - 10, 10, "FPS: --", 14, (100, 255, 100), pivot=(1, 0))
        self.add_ui_element(self.fps_label)

    def setup_assets_tab(self):
        tab = "Assets"
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Registered Assets", 24, (255, 255, 0)))

        add_btn = Button(10, 50, 120, 30, "Add File...")
        add_btn.set_on_click(self.prompt_add_file)
        self.main_tabs.add_to_tab(tab, add_btn)

        refresh_btn = Button(140, 50, 100, 30, "Refresh")
        refresh_btn.set_on_click(self.refresh_asset_list)
        self.main_tabs.add_to_tab(tab, refresh_btn)

        clear_btn = Button(250, 50, 100, 30, "Clear All")
        clear_btn.set_on_click(self.clear_all_assets)
        self.main_tabs.add_to_tab(tab, clear_btn)

        self.asset_list_frame = ScrollingFrame(10, 90, 600, 500, 590, 2000)
        self.main_tabs.add_to_tab(tab, self.asset_list_frame)

        self.asset_count_label = TextLabel(10, 600, "Total assets: 0", 14, (200, 200, 200))
        self.main_tabs.add_to_tab(tab, self.asset_count_label)

    def setup_preview_tab(self):
        tab = "Preview"
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Asset Preview", 24, (255, 255, 0)))
        self.main_tabs.add_to_tab(tab, TextLabel(10, 50, "Select an asset from the 'Assets' tab to preview here.", 16, (200, 200, 200)))

        preview_frame = UiFrame(10, 80, 400, 400)
        preview_frame.set_background_color((30, 30, 40, 200))
        preview_frame.set_border((80, 80, 100), 2)
        preview_frame.set_corner_radius(8)
        self.main_tabs.add_to_tab(tab, preview_frame)

        self.preview_image = ImageLabel(200, 200, None, 200, 200, pivot=(0.5, 0.5))
        preview_frame.add_child(self.preview_image)

        self.preview_text_label = TextLabel(200, 200, "Sample Text", 24, (255, 255, 255), pivot=(0.5, 0.5))
        preview_frame.add_child(self.preview_text_label)

        self.preview_audio_button = Button(200, 300, 120, 30, "Play Audio", pivot=(0.5, 0))
        preview_frame.add_child(self.preview_audio_button)

        self.main_tabs.add_to_tab(tab, TextLabel(10, 490, "Asset Details:", 16, (200, 200, 255)))
        self.details_text = TextLabel(10, 515, "No asset selected", 14, (200, 200, 200))
        self.main_tabs.add_to_tab(tab, self.details_text)

        self.preview_image.visible = False
        self.preview_text_label.visible = False
        self.preview_audio_button.visible = False

    def setup_bundle_tab(self):
        tab = "Bundle"
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Resource Bundle (.res)", 24, (255, 255, 0)))

        self.bundle_status_label = TextLabel(10, 50, "Bundle not loaded", 18, (255, 100, 100))
        self.main_tabs.add_to_tab(tab, self.bundle_status_label)

        self.main_tabs.add_to_tab(tab, TextLabel(10, 100, "Create Bundle:", 18, (200, 200, 255)))

        self.obfuscate_checkbox = Checkbox(10, 130, 150, 25, False, "Obfuscate")
        self.main_tabs.add_to_tab(tab, self.obfuscate_checkbox)

        self.bundle_key_input = TextBox(180, 128, 150, 30, "my_secret_key")
        self.main_tabs.add_to_tab(tab, self.bundle_key_input)

        create_btn = Button(10, 170, 150, 35, "Create Bundle")
        create_btn.set_on_click(self.create_bundle)
        self.main_tabs.add_to_tab(tab, create_btn)

        self.main_tabs.add_to_tab(tab, TextLabel(10, 230, "Load Bundle:", 18, (200, 200, 255)))

        load_btn = Button(10, 260, 150, 35, "Load game.res")
        load_btn.set_on_click(self.load_bundle)
        self.main_tabs.add_to_tab(tab, load_btn)

        info_text = (
            "• Create a .res file from all registered assets.\n"
            "• The bundle is a ZIP archive with a manifest.\n"
            "• Obfuscation uses XOR with a key.\n"
            "• To test loading, restart the demo with the bundle in the working directory,\n"
            "  or use the 'Load game.res' button.\n"
            "• The engine automatically loads 'game.res' on startup if present."
        )
        info_label = LongTextLabel(10, 320, info_text, width=500, height=200, font_size=14, line_spacing=4)
        self.main_tabs.add_to_tab(tab, info_label)

    # ------------------------------------------------------------
    # Asset List Management
    # ------------------------------------------------------------

    def refresh_asset_list(self):
        for child in self.asset_list_frame.children.copy():
            self.asset_list_frame.remove_child(child)

        y_pos = 10
        for name, item in self.atlas.atlas.items():
            row_frame = UiFrame(10, y_pos, 580, 30)
            row_frame.set_background_color((40, 40, 50, 200) if y_pos % 60 == 10 else (30, 30, 40, 200))
            row_frame.set_border((80, 80, 100), 1)

            name_label = TextLabel(10, 5, name, 16, (255, 255, 255))
            row_frame.add_child(name_label)

            cat_label = TextLabel(180, 5, f"({item.category.value})", 14, (200, 200, 200))
            row_frame.add_child(cat_label)

            path_str = str(item.path)
            if len(path_str) > 30:
                path_str = "..." + path_str[-27:]
            path_label = TextLabel(280, 5, path_str, 12, (150, 150, 150))
            row_frame.add_child(path_label)

            preview_btn = Button(500, 2, 70, 26, "Preview")
            preview_btn.set_on_click(lambda n=name: self.select_asset(n))
            row_frame.add_child(preview_btn)

            self.asset_list_frame.add_child(row_frame)
            y_pos += 35

        self.asset_count_label.set_text(f"Total assets: {len(self.atlas.atlas)}")
        self.asset_list_frame.total_height = max(200, y_pos + 20)

    def select_asset(self, name: str):
        self.selected_asset_name = name
        item = self.atlas.get_item(name)
        if not item:
            return

        self.details_text.set_text(f"Name: {item.name}\nCategory: {item.category.value}\nPath: {item.path}")

        self.preview_image.visible = False
        self.preview_text_label.visible = False
        self.preview_audio_button.visible = False

        if item.category == AtlasCategory.TEXTURE:
            try:
                data = self.atlas.get_bytes(name)
                if data is not None:
                    surf = pygame.image.load(io.BytesIO(data))
                else:
                    surf = pygame.image.load(str(item.path))
                max_w, max_h = 180, 180
                w, h = surf.get_size()
                scale = min(max_w/w, max_h/h, 1.0)
                if scale < 1.0:
                    surf = pygame.transform.smoothscale(surf, (int(w*scale), int(h*scale)))
                self.preview_image.set_image(surf)
                self.preview_image.visible = True
                self.preview_image.width = surf.get_width()
                self.preview_image.height = surf.get_height()
            except Exception as e:
                print(f"Error loading texture: {e}")

        elif item.category == AtlasCategory.FONT:
            try:
                font = FontManager.get_font(name, 24)
                self.preview_text_label.set_font(font)
                self.preview_text_label.set_text("Sample Text 123")
                self.preview_text_label.visible = True
            except Exception as e:
                print(f"Error loading font: {e}")

        elif item.category == AtlasCategory.AUDIO:
            self.preview_audio_button.visible = True
            self.preview_audio_button.set_text("Play Audio")
            self.preview_audio_button.set_on_click(lambda: self.play_audio_preview(name))

    def play_audio_preview(self, name: str):
        try:
            ch = self.engine.audio.get_channel('preview')
            if not ch:
                ch = self.engine.audio.create_channel('preview', volume=0.8, loop=False)

            data = self.atlas.get_bytes(name)
            if data is not None:
                import tempfile
                tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                tmp.write(data)
                tmp.close()
                self.engine.audio.load_sound(f"preview_{name}", tmp.name)
                ch.play(f"preview_{name}")
            else:
                item = self.atlas.get_item(name)
                if item:
                    self.engine.audio.load_sound(f"preview_{name}", str(item.path))
                    ch.play(f"preview_{name}")
        except Exception as e:
            print(f"Audio playback error: {e}")

    # ------------------------------------------------------------
    # Bundle Operations (FIXED - calling .value() method)
    # ------------------------------------------------------------

    def create_bundle(self):
        if not self.atlas.atlas:
            self.show_notification("No assets to bundle!", "warning")
            return

        # Call the .value() method to get the boolean state
        obfuscate = self.obfuscate_checkbox.value()
        key = self.bundle_key_input.get_text().strip()

        if obfuscate and not key:
            self.show_notification("Please enter a non-empty key for obfuscation.", "error")
            return

        try:
            output = Path("game.res")
            self.atlas.create_bundle(output, obfuscate=obfuscate, obfuscation_key=key)
            self.show_notification(f"Bundle created: {output}", "success")
        except Exception as e:
            self.show_notification(f"Bundle creation failed: {e}", "error")

    def load_bundle(self):
        bundle_path = Path("game.res")
        if not bundle_path.exists():
            self.show_notification("game.res not found!", "error")
            return

        try:
            # Clear existing assets
            self.atlas.atlas.clear()
            self.atlas._bundle_data.clear()
            self.atlas._use_bundle = False

            # Call .value() to get the boolean state
            key = self.bundle_key_input.get_text().strip() if self.obfuscate_checkbox.value() else None
            self.atlas.load_from_bundle(bundle_path, obfuscation_key=key)
            self.bundle_loaded = True
            self.update_bundle_status()
            self.refresh_asset_list()
            self.show_notification("Bundle loaded successfully!", "success")
        except Exception as e:
            self.show_notification(f"Bundle load failed: {e}", "error")

    def update_bundle_status(self):
        if self.atlas.is_bundle_loaded():
            self.bundle_status_label.set_text("Bundle loaded")
            self.bundle_status_label.color = (100, 255, 100)
        else:
            self.bundle_status_label.set_text("No bundle loaded")
            self.bundle_status_label.color = (255, 100, 100)

    def clear_all_assets(self):
        if self.atlas.is_bundle_loaded():
            self.show_notification("Cannot clear assets from a loaded bundle.", "warning")
            return
        self.atlas.atlas.clear()
        self.refresh_asset_list()
        self.show_notification("All assets cleared.", "info")

    def prompt_add_file(self):
        if not hasattr(self, '_file_finder_dialog'):
            self._file_finder_dialog = FileFinder(0, 0, 1, 1, file_filter=['*'], dialog_title="Select Asset File")
            self._file_finder_dialog.on_file_selected = self._on_file_selected
            self._file_finder_dialog.visible = False
            self.add_ui_element(self._file_finder_dialog)
        self._file_finder_dialog._open_dialog()

    def _on_file_selected(self, path):
        if path:
            self.add_asset_from_file(path)
            self.show_notification(f"Added: {Path(path).name}", "success")

    def show_notification(self, text, type="info"):
        print(f"[Notification] {type.upper()}: {text}")
        type_map = {
            "info": NotificationType.INFO,
            "success": NotificationType.SUCCESS,
            "warning": NotificationType.WARNING,
            "error": NotificationType.ERROR,
        }
        self.engine.show_notification(text, type_map.get(type, NotificationType.INFO), duration=3.0)

    def update(self, dt):
        self.fps_label.set_text(f"FPS: {self.engine.get_fps_stats()['current_fps']:.1f}")
        if self.preview_spritesheet_anim:
            self.preview_spritesheet_anim.update()

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        renderer.draw_rect(0, 0, self.engine.width, 70, ThemeManager.get_color('background2'))


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    engine = LunaEngine("Atlas Resource Demo", 1024, 720, debug=True, show_splash=True)
    engine.fps = 60

    engine.add_scene("AtlasDemo", AtlasDemoScene)
    engine.set_scene("AtlasDemo")

    print("\n=== Atlas Demo ===")
    print("This demo shows how to use the Atlas resource catalog and bundle system.")
    print("You can register assets, create a .res bundle, and load from it.")
    print("Check the 'Bundle' tab for bundle operations.\n")

    engine.run()


if __name__ == "__main__":
    main()