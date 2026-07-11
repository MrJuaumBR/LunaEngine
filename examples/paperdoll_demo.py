"""
Paperdoll Demo - 5 frames idle, Face + 3 body colors (16x64 spritesheet)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pygame
from lunaengine.core import Scene, LunaEngine
from lunaengine.ui import *
from lunaengine.graphics.paperdoll import load_paperdoll


class PaperdollDemoScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.engine = engine

        # Load the paperdoll from the atlas
        self.hero = load_paperdoll(self.engine.atlas.get_item('paperdoll_config'))
        self.hero_x = self.engine.width // 2 + 100
        self.hero_y = self.engine.height // 2 + 32

        # Set initial scale (2x for visibility)
        self.hero.set_scale(2.0)

        # Make sure all layers are visible (face is always visible)
        self.hero.set_layer_visible("face", True)
        self.active_body = 1
        self.update_body_visibility()

        # Ensure animation is playing
        self.hero.play("idle")
        self.hero.speed = 1.0

        # UI
        self.setup_ui()

        # Keyboard shortcuts
        @engine.on_event(pygame.KEYDOWN)
        def on_key(event):
            self.handle_key(event.key)

    def setup_ui(self):
        self.engine.set_global_theme(ThemeType.DEFAULT)

        title = TextLabel(10, 10, "Paperdoll Demo (16x64, scaled 2x)", 28, (255, 255, 0))
        self.add_ui_element(title)

        # Use LongTextLabel for multi-line text with \n
        info_text = (
            "1, 2, 3: change body color\n"
            "P: pause/resume animation\n"
            "Up/Down: increase/decrease scale"
        )
        info_label = LongTextLabel(
            10, 50, info_text,
            width=400, height=60,
            font_size=18,
            line_spacing=4
        )
        self.add_ui_element(info_label)

        self.body_label = TextLabel(10, 120, "Body: Body1", 20, (100, 200, 255))
        self.add_ui_element(self.body_label)

        self.scale_label = TextLabel(10, 150, "Scale: 2.0x", 20, (100, 255, 100))
        self.add_ui_element(self.scale_label)

        self.frame_label = TextLabel(10, 180, "Frame: 0/5", 16, (200, 200, 200))
        self.add_ui_element(self.frame_label)

        # Buttons to change body
        btn_y = 210
        for i in range(1, 4):
            btn = Button(10 + (i-1)*100, btn_y, 80, 30, f"Body{i}")
            btn.set_on_click(lambda idx=i: self.set_body(idx))
            self.add_ui_element(btn)

        # Pause button
        self.pause_btn = Button(10, btn_y + 50, 120, 30, "Pause")
        self.pause_btn.set_on_click(self.toggle_pause)
        self.add_ui_element(self.pause_btn)

        # Scale buttons
        scale_btn_small = Button(10, btn_y + 100, 80, 30, "Scale 0.5x")
        scale_btn_small.set_on_click(lambda: self.change_scale(0.5))
        self.add_ui_element(scale_btn_small)

        scale_btn_normal = Button(100, btn_y + 100, 80, 30, "Scale 1x")
        scale_btn_normal.set_on_click(lambda: self.change_scale(1.0))
        self.add_ui_element(scale_btn_normal)

        scale_btn_large = Button(190, btn_y + 100, 80, 30, "Scale 3x")
        scale_btn_large.set_on_click(lambda: self.change_scale(3.0))
        self.add_ui_element(scale_btn_large)

    def handle_key(self, key):
        if key == pygame.K_1:
            self.set_body(1)
        elif key == pygame.K_2:
            self.set_body(2)
        elif key == pygame.K_3:
            self.set_body(3)
        elif key == pygame.K_p:
            self.toggle_pause()
        elif key == pygame.K_UP:
            self.change_scale(self.hero.scale + 0.25)
        elif key == pygame.K_DOWN:
            self.change_scale(max(0.25, self.hero.scale - 0.25))

    def set_body(self, body_id: int):
        self.active_body = body_id
        self.update_body_visibility()
        self.body_label.set_text(f"Body: Body{body_id}")

    def update_body_visibility(self):
        # Face always visible
        self.hero.set_layer_visible("face", True)

        # Only the active body is visible
        for i in range(1, 4):
            layer_id = f"body{i}"
            self.hero.set_layer_visible(layer_id, i == self.active_body)

    def change_scale(self, new_scale: float):
        self.hero.set_scale(new_scale)
        self.scale_label.set_text(f"Scale: {new_scale:.2f}x")

    def toggle_pause(self):
        if self.hero.current_anim in self.hero.animations:
            if self.hero.speed > 0:
                self.hero.speed = 0.0
                self.pause_btn.set_text("Resume")
            else:
                self.hero.speed = 1.0
                self.pause_btn.set_text("Pause")

    def update(self, dt):
        # Update animation
        self.hero.update(dt)

        # Update frame counter
        if self.hero.current_anim:
            anim = self.hero.animations[self.hero.current_anim]
            total = anim.total_frames
            current = self.hero.current_frame
            self.frame_label.set_text(f"Frame: {current}/{total}")

    def render(self, renderer):
        renderer.fill_screen((40, 40, 60))

        # Draw the character
        self.hero.draw(renderer, self.hero_x, self.hero_y)

        # Draw UI elements
        for el in self.ui_elements:
            el.render(renderer)


def main():
    engine = LunaEngine("Paperdoll Demo", 600, 400, debug=True)
    engine.fps = 60

    # Register assets in atlas
    root_path = os.path.dirname(os.path.abspath(__file__))
    engine.atlas.add_folder('root', root_path)
    config_path = engine.get_atlas_item('root').path / 'paperdoll_config.json'
    engine.atlas.add_datastore('paperdoll_config', config_path)

    engine.add_scene("paperdoll_demo", PaperdollDemoScene)
    engine.set_scene("paperdoll_demo")

    engine.run()


if __name__ == "__main__":
    main()