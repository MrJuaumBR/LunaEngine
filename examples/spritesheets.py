"""
Sprite Sheets Example - Full Feature Showcase for LunaEngine

LOCATION: examples/spritesheets.py

DESCRIPTION:
Demonstrates all capabilities of the SpriteSheet and Animation system:
- Time-based animations with fade in/out
- Colour replacement, tinting, painting, colour-to-alpha
- Mask creation and visualisation
- Resizing / scaling of sprites
- Live effect preview on the running animation
- Preview uses a raw sprite sheet frame (not a copy from the animation)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pygame
from lunaengine.core import Scene, LunaEngine
from lunaengine.ui import *
from lunaengine.graphics.spritesheet import SpriteSheet, Animation

# ------------------------------------------------------------
# Main Demo Scene
# ------------------------------------------------------------
class SpriteSheetTestScene(Scene):
    """
    Full demo: animation controls + real-time sprite manipulation effects.
    """
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.CurrentTheme = ThemeType.DEFAULT

        # Animation instances
        self.walk_animation = None
        self.idle_animation = None
        self.current_animation = None
        self.current_animation_name = "Walk"

        # SpriteSheet reference for raw frames
        self.sprite_sheet = None
        self.raw_frame = None          # unmodified frame from sprite sheet
        self.raw_frame_rect = None     # (x, y, width, height) of the frame

        # Settings
        self.animation_scale = 2.0
        self.animation_speed = 1.0
        self.fade_in_duration = 1.0
        self.fade_out_duration = 1.0
        self.auto_fade_transitions = True

        # Effect management
        self.current_effect = "Original"
        self.preview_surface = None    # effect applied to raw_frame

        self.setup_ui()

        # Keyboard shortcuts
        @engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)

    def on_enter(self, previous_scene=None):
        super().on_enter(previous_scene)
        self.load_animations()
        if self.current_animation:
            self.current_animation.reset()
            self.current_animation.play()

    # ------------------------------------------------------------
    # Animation Loading (with fallback placeholders)
    # ------------------------------------------------------------
    def load_animations(self):
        """Load the tiki texture animations and store a raw frame for preview."""
        try:
            texture_path = './examples/tiki_texture.png'
            self.sprite_sheet = SpriteSheet(texture_path)   # using pathlib internally

            # Define the rectangle for the first walk frame (size 70x70 at (0,0))
            self.raw_frame_rect = pygame.Rect(0, 0, 70, 70)
            self.raw_frame = self.sprite_sheet.get_sprite_at_rect(self.raw_frame_rect)

            # Walk animation: 6 frames starting at (0,0)
            self.walk_animation = Animation(
                spritesheet_file=self.sprite_sheet,
                size=(70, 70),
                start_pos=(0, 0),
                frame_count=6,
                scale=(self.animation_scale, self.animation_scale),
                duration=1.0 / self.animation_speed,
                loop=True,
                fade_in_duration=self.fade_in_duration,
                fade_out_duration=self.fade_out_duration
            )

            # Idle animation: 6 frames starting at (0,70)
            self.idle_animation = Animation(
                spritesheet_file=self.sprite_sheet,
                size=(70, 70),
                start_pos=(0, 70),
                frame_count=6,
                scale=(self.animation_scale, self.animation_scale),
                duration=1.5 / self.animation_speed,
                loop=True,
                fade_in_duration=self.fade_in_duration,
                fade_out_duration=self.fade_out_duration
            )

            self.current_animation = self.walk_animation
            self.current_animation_name = "Walk"

            # Update preview using the raw frame
            self.update_preview()

            print("Animations loaded - full sprite features ready.")

        except Exception as e:
            print(f"Warning: Could not load tiki_texture.png: {e}")
            self.create_placeholder_animations()

    def create_placeholder_animations(self):
        """Fallback: coloured squares if texture is missing."""
        # Create a placeholder raw frame
        self.raw_frame = pygame.Surface((70, 70), pygame.SRCALPHA)
        self.raw_frame.fill((255, 0, 255))  # magenta
        pygame.draw.rect(self.raw_frame, (255, 255, 255), self.raw_frame.get_rect(), 2)

        colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]
        frames = []
        for color in colors:
            surf = pygame.Surface((70,70), pygame.SRCALPHA)
            surf.fill(color)
            pygame.draw.rect(surf, (255,255,255), surf.get_rect(), 2)
            if self.animation_scale != 1.0:
                surf = pygame.transform.scale(surf, (int(70*self.animation_scale), int(70*self.animation_scale)))
            frames.append(surf)

        class DummyAnimation:
            def __init__(self, frames, duration, fade_in, fade_out):
                self.frames = frames
                self.duration = duration
                self.frame_duration = duration / len(frames)
                self.current_frame_index = 0
                self.last_update = pygame.time.get_ticks()/1000
                self.acc_time = 0.0
                self.playing = True
                self.loop = True
                self.fade_in_duration = fade_in
                self.fade_out_duration = fade_out
                self.fade_alpha = 0 if fade_in>0 else 255
                self.fade_mode = 'in' if fade_in>0 else None
                self.fade_start = pygame.time.get_ticks()/1000 if fade_in>0 else None

            def update(self):
                if not self.playing or len(self.frames)<=1:
                    return
                now = pygame.time.get_ticks()/1000
                dt = now - self.last_update
                self.last_update = now
                self.acc_time += dt
                adv = int(self.acc_time / self.frame_duration)
                if adv:
                    self.acc_time -= adv * self.frame_duration
                    if self.loop:
                        self.current_frame_index = (self.current_frame_index + adv) % len(self.frames)
                    else:
                        self.current_frame_index = min(self.current_frame_index+adv, len(self.frames)-1)

            def get_current_frame(self):
                return self.frames[self.current_frame_index]

            def reset(self):
                self.current_frame_index = 0
                self.acc_time = 0.0
                self.playing = True

            def play(self):
                self.playing = True

            def pause(self):
                self.playing = False

            def get_frame_count(self):
                return len(self.frames)

            def set_duration(self, d):
                self.duration = d

            def start_fade_in(self, d=None):
                pass

            def start_fade_out(self, d=None):
                pass

        self.walk_animation = DummyAnimation(frames, 1.0/self.animation_speed, self.fade_in_duration, self.fade_out_duration)
        self.idle_animation = DummyAnimation(frames[::-1], 1.5/self.animation_speed, self.fade_in_duration, self.fade_out_duration)
        self.current_animation = self.walk_animation
        self.current_animation_name = "Walk (Placeholder)"
        self.update_preview()

    # ------------------------------------------------------------
    # Effect Application (using raw frame for preview)
    # ------------------------------------------------------------
    def update_preview(self):
        """Apply selected effect to the raw sprite sheet frame."""
        if self.raw_frame is None:
            return
        frame = self.raw_frame.copy()   # copy for preview (safe, only once per effect change)
        effect = self.current_effect

        if effect == "Original":
            pass
        elif effect == "Replace Color (red->green)":
            frame = SpriteSheet.replace_color(frame, (255,0,0), (0,255,0), tolerance=30)
        elif effect == "Tint (blue 50%)":
            frame = SpriteSheet.tint(frame, (50,100,255), intensity=0.5, blend_mode="multiply")
        elif effect == "Paint (solid yellow)":
            frame = SpriteSheet.paint(frame, (255,255,0), preserve_alpha=True)
        elif effect == "Color to Alpha (remove green)":
            frame = SpriteSheet.color_to_alpha(frame, (0,255,0), threshold=40)
        elif effect == "Resize (2x)":
            frame = SpriteSheet.resize_surface(frame, frame.get_width()*2, frame.get_height()*2, smooth=True)
        elif effect == "Scale (0.5x)":
            frame = SpriteSheet.scale_surface(frame, 0.5, 0.5, smooth=True)
        elif effect == "Mask Outline":
            mask = SpriteSheet.create_mask(frame, threshold=10)
            w, h = frame.get_size()
            # Use a separate surface to avoid modifying during iteration
            outline_surface = frame.copy()
            for x in range(w):
                for y in range(h):
                    if not mask.get_at((x, y)):
                        continue
                    # Check neighbours (with bounds checking)
                    left = mask.get_at((x-1, y)) if x > 0 else False
                    right = mask.get_at((x+1, y)) if x < w-1 else False
                    top = mask.get_at((x, y-1)) if y > 0 else False
                    bottom = mask.get_at((x, y+1)) if y < h-1 else False
                    if not (left and right and top and bottom):
                        outline_surface.set_at((x, y), (255, 0, 0, 255))
            frame = outline_surface

        self.preview_surface = frame

    def apply_effect_to_surface(self, surface):
        """Apply current effect to a live animation frame."""
        if self.current_effect == "Original":
            return surface
        result = surface.copy()
        effect = self.current_effect

        if effect == "Replace Color (red->green)":
            result = SpriteSheet.replace_color(result, (255,0,0), (0,255,0), tolerance=30)
        elif effect == "Tint (blue 50%)":
            result = SpriteSheet.tint(result, (50,100,255), intensity=0.5)
        elif effect == "Paint (solid yellow)":
            result = SpriteSheet.paint(result, (255,255,0), preserve_alpha=True)
        elif effect == "Color to Alpha (remove green)":
            result = SpriteSheet.color_to_alpha(result, (0,255,0), threshold=40)
        elif effect == "Resize (2x)":
            result = SpriteSheet.resize_surface(result, result.get_width()*2, result.get_height()*2, smooth=True)
        elif effect == "Scale (0.5x)":
            result = SpriteSheet.scale_surface(result, 0.5, 0.5, smooth=True)
        elif effect == "Mask Outline":
            mask = SpriteSheet.create_mask(result, threshold=10)
            w, h = result.get_size()
            outline_surface = result.copy()
            for x in range(w):
                for y in range(h):
                    if not mask.get_at((x, y)):
                        continue
                    left = mask.get_at((x-1, y)) if x > 0 else False
                    right = mask.get_at((x+1, y)) if x < w-1 else False
                    top = mask.get_at((x, y-1)) if y > 0 else False
                    bottom = mask.get_at((x, y+1)) if y < h-1 else False
                    if not (left and right and top and bottom):
                        outline_surface.set_at((x, y), (255, 0, 0, 255))
            result = outline_surface
        return result

    # ------------------------------------------------------------
    # UI Setup (Tabs)
    # ------------------------------------------------------------
    def setup_ui(self):
        title = TextLabel(512, 30, "Sprite Sheet System - Full Feature Demo", 36,
                          root_point=(0.5,0), theme=self.CurrentTheme)
        self.add_ui_element(title)

        # Adjusted width to 920 (was 980) to prevent overlap, and height 580 (was 650)
        self.main_tabs = Tabination(25, 90, 700, 580, 20)
        self.main_tabs.add_tab("Animation")
        self.main_tabs.add_tab("Sprite Effects")
        self.setup_animation_tab()
        self.setup_effects_tab()
        self.add_ui_element(self.main_tabs)

        # Back button
        back_btn = Button(50, 50, 120, 30, "<- Main Menu", 20,
                          root_point=(0,0), theme=self.CurrentTheme)
        back_btn.set_on_click(lambda: self.engine.set_scene("MainMenu"))
        self.add_ui_element(back_btn)

    def setup_animation_tab(self):
        """Traditional animation controls (speed, zoom, fade, switch)."""
        tab = "Animation"
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Animation Controls", 24, (255,255,0)))

        # Animation info
        self.anim_name_label = TextLabel(10, 50, f"Current: {self.current_animation_name}", 20, (200,200,255))
        self.main_tabs.add_to_tab(tab, self.anim_name_label)
        self.frame_label = TextLabel(10, 80, "Frame: 0/0", 16)
        self.main_tabs.add_to_tab(tab, self.frame_label)

        # Speed slider
        speed_label = TextLabel(10, 120, "Animation Speed:", 16, (200,200,255))
        self.main_tabs.add_to_tab(tab, speed_label)
        speed_slider = Slider(180, 115, 200, 25, 0.5, 3.0, self.animation_speed)
        speed_slider.on_value_changed = self.on_speed_changed
        self.main_tabs.add_to_tab(tab, speed_slider)
        self.speed_val = TextLabel(390, 120, f"{self.animation_speed:.1f}x", 16)
        self.main_tabs.add_to_tab(tab, self.speed_val)

        # Zoom slider
        zoom_label = TextLabel(10, 165, "Zoom Level:", 16, (200,200,255))
        self.main_tabs.add_to_tab(tab, zoom_label)
        zoom_slider = Slider(180, 160, 200, 25, 0.5, 4.0, self.animation_scale)
        zoom_slider.on_value_changed = self.on_zoom_changed
        self.main_tabs.add_to_tab(tab, zoom_slider)
        self.zoom_val = TextLabel(390, 165, f"{self.animation_scale:.1f}x", 16)
        self.main_tabs.add_to_tab(tab, self.zoom_val)

        # Fade sliders
        fade_in_label = TextLabel(10, 210, "Fade-in Duration:", 16, (200,200,255))
        self.main_tabs.add_to_tab(tab, fade_in_label)
        fade_in_slider = Slider(180, 205, 200, 25, 0.0, 3.0, self.fade_in_duration)
        fade_in_slider.on_value_changed = self.on_fade_in_changed
        self.main_tabs.add_to_tab(tab, fade_in_slider)
        self.fade_in_val = TextLabel(390, 210, f"{self.fade_in_duration:.1f}s", 16)
        self.main_tabs.add_to_tab(tab, self.fade_in_val)

        fade_out_label = TextLabel(10, 255, "Fade-out Duration:", 16, (200,200,255))
        self.main_tabs.add_to_tab(tab, fade_out_label)
        fade_out_slider = Slider(180, 250, 200, 25, 0.0, 3.0, self.fade_out_duration)
        fade_out_slider.on_value_changed = self.on_fade_out_changed
        self.main_tabs.add_to_tab(tab, fade_out_slider)
        self.fade_out_val = TextLabel(390, 255, f"{self.fade_out_duration:.1f}s", 16)
        self.main_tabs.add_to_tab(tab, self.fade_out_val)

        # Auto-fade toggle
        auto_fade_switch = Switch(10, 295, 60, 30, self.auto_fade_transitions)
        auto_fade_switch.set_on_toggle(lambda v: setattr(self, 'auto_fade_transitions', v))
        self.main_tabs.add_to_tab(tab, auto_fade_switch)
        auto_label = TextLabel(80, 300, "Auto fade on switch", 16)
        self.main_tabs.add_to_tab(tab, auto_label)

        # Buttons
        btn_y = 340
        play_btn = Button(10, btn_y, 80, 30, "Play")
        play_btn.set_on_click(self.play_animation)
        self.main_tabs.add_to_tab(tab, play_btn)

        pause_btn = Button(100, btn_y, 80, 30, "Pause")
        pause_btn.set_on_click(self.pause_animation)
        self.main_tabs.add_to_tab(tab, pause_btn)

        reset_btn = Button(190, btn_y, 80, 30, "Reset")
        reset_btn.set_on_click(self.reset_animation)
        self.main_tabs.add_to_tab(tab, reset_btn)

        switch_anim_btn = Button(280, btn_y, 120, 30, "Switch Anim")
        switch_anim_btn.set_on_click(self.switch_animation)
        self.main_tabs.add_to_tab(tab, switch_anim_btn)

        apply_btn = Button(410, btn_y, 120, 30, "Apply Settings")
        apply_btn.set_on_click(self.reload_animations)
        self.main_tabs.add_to_tab(tab, apply_btn)

        # Info (split into multiple lines)
        info_y = 400
        info1 = TextLabel(10, info_y, "Keyboard shortcuts:", 14, (150,150,200))
        info2 = TextLabel(10, info_y+20, "SPACE - switch animation", 14, (150,150,200))
        info3 = TextLabel(10, info_y+40, "R - reset", 14, (150,150,200))
        info4 = TextLabel(10, info_y+60, "P - play/pause", 14, (150,150,200))
        info5 = TextLabel(10, info_y+80, "I/O - fade in/out", 14, (150,150,200))
        info6 = TextLabel(10, info_y+100, "F - toggle auto fade", 14, (150,150,200))
        self.main_tabs.add_to_tab(tab, info1)
        self.main_tabs.add_to_tab(tab, info2)
        self.main_tabs.add_to_tab(tab, info3)
        self.main_tabs.add_to_tab(tab, info4)
        self.main_tabs.add_to_tab(tab, info5)
        self.main_tabs.add_to_tab(tab, info6)

    def setup_effects_tab(self):
        """Tab for sprite manipulation effects, with preview on the right side."""
        tab = "Sprite Effects"
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Sprite Manipulation", 24, (255,255,0)))

        # Effect selector
        effect_label = TextLabel(20, 50, "Select Effect:", 18, (200,200,255))
        self.main_tabs.add_to_tab(tab, effect_label)

        effect_options = [
            "Original",
            "Replace Color (red->green)",
            "Tint (blue 50%)",
            "Paint (solid yellow)",
            "Color to Alpha (remove green)",
            "Resize (2x)",
            "Scale (0.5x)",
            "Mask Outline"
        ]
        effect_dropdown = Dropdown(180, 45, 250, 35, effect_options)
        effect_dropdown.set_on_selection_changed(lambda i, val: self.set_effect(val))
        self.main_tabs.add_to_tab(tab, effect_dropdown)

        # --- Preview placed on the right side (using absolute positioning inside tab) ---
        preview_container = UiFrame(425, 90, 200, 220)
        preview_container.set_background_color((30,30,40))
        preview_container.set_border((100,100,150), 2)
        preview_container.set_corner_radius(8)
        self.main_tabs.add_to_tab(tab, preview_container)

        # Label inside container
        preview_label = TextLabel(100, 10, "Effect Preview", 16, (220,220,255), root_point=(0.5,0))
        preview_container.add_child(preview_label)

        # This ImageLabel will hold the preview image; updated in update()
        self.preview_image = ImageLabel(100, 110, None, 100, 100, root_point=(0.5,0.5))
        preview_container.add_child(self.preview_image)

        # Explanation text on the left side
        explanation = UiFrame(20, 100, 380, 450)
        explanation.set_background_color((20,20,30, 200))
        explanation.set_corner_radius(5)
        self.main_tabs.add_to_tab(tab, explanation)

        exp_y = 10
        exp1 = TextLabel(10, exp_y, "SpriteSheet static methods:", 14, (180,180,200))
        explanation.add_child(exp1)
        exp2 = TextLabel(10, exp_y+20, "replace_color() - change one colour to another", 12, (180,180,200))
        explanation.add_child(exp2)
        exp3 = TextLabel(10, exp_y+40, "tint() - apply colour tint (multiply/add/overlay)", 12, (180,180,200))
        explanation.add_child(exp3)
        exp4 = TextLabel(10, exp_y+60, "paint() - fill sprite with solid colour (preserves alpha)", 12, (180,180,200))
        explanation.add_child(exp4)
        exp5 = TextLabel(10, exp_y+80, "color_to_alpha() - turn a colour transparent", 12, (180,180,200))
        explanation.add_child(exp5)
        exp6 = TextLabel(10, exp_y+100, "resize_surface() / scale_surface()", 12, (180,180,200))
        explanation.add_child(exp6)
        exp7 = TextLabel(10, exp_y+120, "create_mask() - generate collision mask", 12, (180,180,200))
        explanation.add_child(exp7)
        exp8 = TextLabel(10, exp_y+160, "The selected effect is applied LIVE to the running animation.", 12, (200,200,255))
        explanation.add_child(exp8)
        exp9 = TextLabel(10, exp_y+180, "Preview window shows the effect on a static raw frame.", 12, (200,200,255))
        explanation.add_child(exp9)

    # ------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------
    def set_effect(self, effect_name):
        self.current_effect = effect_name
        self.update_preview()
        print(f"Effect changed to: {effect_name}")

    def on_speed_changed(self, val):
        self.animation_speed = val
        self.speed_val.set_text(f"{val:.1f}x")
        if self.current_animation:
            new_dur = (1.0 if self.current_animation == self.walk_animation else 1.5) / val
            self.current_animation.set_duration(new_dur)

    def on_zoom_changed(self, val):
        self.animation_scale = val
        self.zoom_val.set_text(f"{val:.1f}x")
        self.reload_animations()

    def on_fade_in_changed(self, val):
        self.fade_in_duration = val
        self.fade_in_val.set_text(f"{val:.1f}s")

    def on_fade_out_changed(self, val):
        self.fade_out_duration = val
        self.fade_out_val.set_text(f"{val:.1f}s")

    def reload_animations(self):
        """Reload animations with current scale, speed and fade settings."""
        was_walk = (self.current_animation == self.walk_animation) if self.current_animation else True
        self.load_animations()
        if was_walk:
            self.current_animation = self.walk_animation
            self.current_animation_name = "Walk"
        else:
            self.current_animation = self.idle_animation
            self.current_animation_name = "Idle"
        self.anim_name_label.set_text(f"Current: {self.current_animation_name}")
        if self.current_animation:
            self.current_animation.reset()
            self.current_animation.play()

    def switch_animation(self):
        if self.auto_fade_transitions and self.current_animation:
            self.current_animation.start_fade_out(self.fade_out_duration)
        # Switch
        if self.current_animation == self.walk_animation:
            self.current_animation = self.idle_animation
            self.current_animation_name = "Idle"
        else:
            self.current_animation = self.walk_animation
            self.current_animation_name = "Walk"
        if self.auto_fade_transitions:
            self.current_animation.start_fade_in(self.fade_in_duration)
        self.current_animation.reset()
        self.current_animation.play()
        self.anim_name_label.set_text(f"Current: {self.current_animation_name}")

    def play_animation(self):
        if self.current_animation:
            self.current_animation.play()

    def pause_animation(self):
        if self.current_animation:
            self.current_animation.pause()

    def reset_animation(self):
        if self.current_animation:
            self.current_animation.reset()

    def handle_key_press(self, key):
        if key == pygame.K_ESCAPE:
            self.engine.set_scene("MainMenu")
        elif key == pygame.K_SPACE:
            self.switch_animation()
        elif key == pygame.K_r:
            self.reset_animation()
        elif key == pygame.K_p:
            if self.current_animation and self.current_animation.playing:
                self.pause_animation()
            else:
                self.play_animation()
        elif key == pygame.K_i:
            if self.current_animation:
                self.current_animation.start_fade_in(self.fade_in_duration)
        elif key == pygame.K_o:
            if self.current_animation:
                self.current_animation.start_fade_out(self.fade_out_duration)
        elif key == pygame.K_f:
            self.auto_fade_transitions = not self.auto_fade_transitions

    # ------------------------------------------------------------
    # Update and Render
    # ------------------------------------------------------------
    def update(self, dt):
        if self.current_animation:
            self.current_animation.update()
            # Frame counter
            fc = self.current_animation.get_frame_count()
            if fc > 0:
                cur = self.current_animation.current_frame_index + 1
                self.frame_label.set_text(f"Frame: {cur}/{fc}")
            # Get frame and apply effect
            frame = self.current_animation.get_current_frame()
            self.effected_frame = self.apply_effect_to_surface(frame)

        # Update preview image with the static preview surface
        if hasattr(self, 'preview_surface') and self.preview_surface:
            preview = self.preview_surface
            # Fit into 200x200 (the container is 250x250, image area ~200x200)
            max_w, max_h = 200, 200
            scale = min(max_w/preview.get_width(), max_h/preview.get_height())
            if scale != 1.0:
                preview = SpriteSheet.scale_surface(preview, scale, scale, smooth=True)
            self.preview_image.set_image(preview)
            self.preview_image.width = preview.get_width()
            self.preview_image.height = preview.get_height()

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))

        # Draw the animated sprite with effect applied (positioned to the right of tabs)
        if hasattr(self, 'effected_frame') and self.effected_frame:
            frame = self.effected_frame
            # Place it near the right edge (centered between tab end and window edge)
            x = self.engine.width - frame.get_width() - 50
            y = (self.engine.height - frame.get_height()) // 2
            renderer.draw_rect(x, y, frame.get_width(), frame.get_height(),
                               (255,255,255), fill=False)
            renderer.draw_surface(frame, x, y)

            # Effect name text
            font = pygame.font.Font(None, 24)
            info_surf = font.render(f"Effect: {self.current_effect}", True, (255,255,255))
            renderer.draw_surface(info_surf, x, y + frame.get_height() + 10)

        # Render UI
        for element in self.ui_elements:
            element.render(renderer)


# ------------------------------------------------------------
# Main Menu Scene
# ------------------------------------------------------------
class MainMenuScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.CurrentTheme = ThemeType.DEFAULT
        title = TextLabel(512, 150, "Sprite Sheet Full Demo", 72, root_point=(0.5,0), theme=self.CurrentTheme)
        self.add_ui_element(title)
        subtitle = TextLabel(512, 220, "LunaEngine - Animation + Sprite Effects", 32, root_point=(0.5,0), theme=self.CurrentTheme)
        self.add_ui_element(subtitle)
        start_btn = Button(512, 300, 250, 40, "Start Demo", 28, root_point=(0.5,0), theme=self.CurrentTheme)
        start_btn.set_on_click(lambda: engine.set_scene("SpriteSheetTest"))
        self.add_ui_element(start_btn)
        exit_btn = Button(512, 360, 250, 40, "Exit", 28, root_point=(0.5,0), theme=self.CurrentTheme)
        exit_btn.set_on_click(lambda: setattr(engine, 'running', False))
        self.add_ui_element(exit_btn)

    def update(self, dt):
        pass

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        for el in self.ui_elements:
            el.render(renderer)


def main():
    engine = LunaEngine("LunaEngine - Sprite Sheet Full Demo", 1024, 720)
    engine.fps = 60
    engine.add_scene("MainMenu", MainMenuScene)
    engine.add_scene("SpriteSheetTest", SpriteSheetTestScene)
    engine.set_scene("MainMenu")
    engine.run()

if __name__ == "__main__":
    main()