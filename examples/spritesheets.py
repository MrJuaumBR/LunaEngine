"""
Sprite Sheets Example - Testing SpriteSheet and Animation System with LunaEngine
Now with Fade-in and Fade-out support!

LOCATION: examples/spritesheets.py

DESCRIPTION:
Simple test scene to demonstrate the sprite sheet and animation system
using the tiki_texture.png file. Now includes fade effects for smooth transitions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine
from lunaengine.ui import *
from lunaengine.backend.pygame_backend import PygameRenderer
from lunaengine.graphics.spritesheet import Animation
import pygame

class SpriteSheetTestScene(Scene):
    """
    Test scene for sprite sheet and animation system with fade effects.
    
    Demonstrates how to use the Animation class with fade-in and fade-out
    within a LunaEngine scene.
    """
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.CurrentTheme = ThemeType.DEFAULT
        
        # Animation instances
        self.walk_animation = None
        self.idle_animation = None
        self.current_animation = None
        
        # Animation state
        self.animation_scale = 2.0
        self.animation_speed = 1.0
        self.current_animation_name = "Walk"
        
        # Fade effect settings
        self.fade_in_duration = 1.0
        self.fade_out_duration = 1.0
        self.auto_fade_transitions = True
        
        # Setup UI
        self.setup_ui()
        
        # Register key events
        @engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
    
    def on_enter(self, previous_scene=None):
        """
        Called when scene becomes active.
        
        Args:
            previous_scene: Name of the previous scene
        """
        super().on_enter(previous_scene)
        print("Entered SpriteSheet Test Scene")
        
        # Load animations
        self.load_animations()
        
        # Reset animations when entering scene
        if self.current_animation:
            self.current_animation.reset()
            self.current_animation.play()
            
    
    def on_exit(self, next_scene=None):
        """
        Called when scene is being exited.
        
        Args:
            next_scene: Name of the next scene
        """
        super().on_exit(next_scene)
        print("Exiting SpriteSheet Test Scene")
    
    def load_animations(self):
        """Load the tiki texture animations with fade support"""
        try:
            texture_path = './examples/tiki_texture.png'
            
            # Walk animation - 6 frames starting at (0, 0)
            self.walk_animation = Animation(
                spritesheet_file=texture_path,
                size=(70, 70),
                start_pos=(0, 0),
                frame_count=6,
                scale=(self.animation_scale, self.animation_scale),
                duration=1.0 / self.animation_speed,
                loop=True,
                fade_in_duration=self.fade_in_duration,
                fade_out_duration=self.fade_out_duration
            )
            
            # Idle animation - 6 frames starting at (0, 70)
            self.idle_animation = Animation(
                spritesheet_file=texture_path,
                size=(70, 70),
                start_pos=(0, 70),
                frame_count=6,
                scale=(self.animation_scale, self.animation_scale),
                duration=1.5 / self.animation_speed,
                loop=True,
                fade_in_duration=self.fade_in_duration,
                fade_out_duration=self.fade_out_duration
            )
            
            # Set current animation
            self.current_animation = self.walk_animation
            self.current_animation_name = "Walk"
            
            print("Successfully loaded tiki texture animations with fade support!")
            print(f"Walk animation: {self.walk_animation.get_frame_count()} frames")
            print(f"Idle animation: {self.idle_animation.get_frame_count()} frames")
            
        except Exception as e:
            print(f"Error loading animations: {e}")
            # Create placeholder animations if loading fails
            self.create_placeholder_animations()
    
    def reload_animations_with_new_settings(self):
        """Reload animations with current scale, speed and fade settings"""
        if hasattr(self, 'walk_animation') and self.walk_animation:
            # Store current animation state
            was_walk = (self.current_animation == self.walk_animation)
            current_frame_index = self.current_animation.current_frame_index if self.current_animation else 0
            
            # Reload animations
            self.load_animations()
            
            # Restore animation state
            if was_walk:
                self.current_animation = self.walk_animation
            else:
                self.current_animation = self.idle_animation
            
            if self.current_animation:
                self.current_animation.current_frame_index = min(current_frame_index, self.current_animation.get_frame_count() - 1)
                self.current_animation.play()
    
    def create_placeholder_animations(self):
        """Create placeholder animations if tiki texture is not available"""
        # Create simple colored squares as placeholders
        placeholder_frames = []
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
        
        for color in colors:
            surface = pygame.Surface((70, 70), pygame.SRCALPHA)
            pygame.draw.rect(surface, color, (0, 0, 70, 70))
            pygame.draw.rect(surface, (255, 255, 255), (0, 0, 70, 70), 2)
            # Apply scaling to placeholder frames
            if self.animation_scale != 1.0:
                new_size = (int(70 * self.animation_scale), int(70 * self.animation_scale))
                surface = pygame.transform.scale(surface, new_size)
            placeholder_frames.append(surface)
        
        # Create simple animation object with fade support
        class PlaceholderAnimation:
            def __init__(self, frames, duration=1.0, fade_in_duration=0.0, fade_out_duration=0.0):
                self.frames = frames
                self.duration = duration
                self.frame_duration = duration / len(frames) if frames else 0
                self.current_frame_index = 0
                self.last_update_time = pygame.time.get_ticks() / 1000.0
                self.accumulated_time = 0.0
                self.playing = True
                self.loop = True
                
                # Fade effect properties
                self.fade_in_duration = fade_in_duration
                self.fade_out_duration = fade_out_duration
                self.fade_alpha = 0 if fade_in_duration > 0 else 255
                self.fade_mode = 'in' if fade_in_duration > 0 else None
                self.fade_start_time = pygame.time.get_ticks() / 1000.0 if fade_in_duration > 0 else None
                self.fade_progress = 0.0
            
            def _apply_fade_effect(self, surface):
                """Apply current fade alpha to a surface"""
                if self.fade_alpha == 255:
                    return surface
                    
                faded_surface = surface.copy()
                temp_surface = pygame.Surface(faded_surface.get_size(), pygame.SRCALPHA)
                temp_surface.fill((255, 255, 255, self.fade_alpha))
                faded_surface.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                return faded_surface
            
            def update_fade(self):
                """Update fade-in and fade-out effects"""
                current_time = pygame.time.get_ticks() / 1000.0
                
                if self.fade_mode == 'in':
                    if self.fade_start_time is None:
                        self.fade_start_time = current_time
                        return
                        
                    elapsed = current_time - self.fade_start_time
                    self.fade_progress = min(elapsed / self.fade_in_duration, 1.0)
                    self.fade_alpha = int(self.fade_progress * 255)
                    
                    if self.fade_progress >= 1.0:
                        self.fade_alpha = 255
                        self.fade_mode = None
                        self.fade_start_time = None
                        
                elif self.fade_mode == 'out':
                    if self.fade_start_time is None:
                        self.fade_start_time = current_time
                        return
                        
                    elapsed = current_time - self.fade_start_time
                    self.fade_progress = min(elapsed / self.fade_out_duration, 1.0)
                    self.fade_alpha = int((1.0 - self.fade_progress) * 255)
                    
                    if self.fade_progress >= 1.0:
                        self.fade_alpha = 0
                        self.fade_mode = None
                        self.fade_start_time = None
                        self.playing = False
            
            def update(self):
                """Update animation with fade effects"""
                # Update fade effects first
                if self.fade_mode:
                    self.update_fade()
                
                if not self.playing or len(self.frames) <= 1:
                    return
                
                current_time = pygame.time.get_ticks() / 1000.0
                delta_time = current_time - self.last_update_time
                self.last_update_time = current_time
                
                self.accumulated_time += delta_time
                frames_to_advance = int(self.accumulated_time / self.frame_duration)
                
                if frames_to_advance > 0:
                    self.accumulated_time -= frames_to_advance * self.frame_duration
                    if self.loop:
                        self.current_frame_index = (self.current_frame_index + frames_to_advance) % len(self.frames)
                    else:
                        self.current_frame_index = min(self.current_frame_index + frames_to_advance, len(self.frames) - 1)
            
            def get_current_frame(self):
                """Get current frame with fade effect applied"""
                if not self.frames:
                    blank = pygame.Surface((1, 1), pygame.SRCALPHA)
                    blank.fill((0, 0, 0, 0))
                    return blank
                
                frame = self.frames[self.current_frame_index]
                
                # Apply fade effect if needed
                if self.fade_mode or self.fade_alpha != 255:
                    return self._apply_fade_effect(frame)
                
                return frame
            
            def reset(self):
                """Reset animation and fade effects"""
                self.current_frame_index = 0
                self.accumulated_time = 0.0
                self.last_update_time = pygame.time.get_ticks() / 1000.0
                self.playing = True
                
                # Reset fade effects
                if self.fade_in_duration > 0:
                    self.fade_mode = 'in'
                    self.fade_alpha = 0
                else:
                    self.fade_mode = None
                    self.fade_alpha = 255
                    
                self.fade_start_time = pygame.time.get_ticks() / 1000.0 if self.fade_mode else None
                self.fade_progress = 0.0
            
            def play(self):
                """Start or resume animation"""
                self.playing = True
                self.last_update_time = pygame.time.get_ticks() / 1000.0
            
            def pause(self):
                """Pause animation"""
                self.playing = False
            
            def get_frame_count(self):
                return len(self.frames)
            
            def set_duration(self, new_duration):
                self.duration = new_duration
                self.frame_duration = new_duration / len(self.frames) if self.frames else 0
            
            def start_fade_in(self, duration=None):
                """Start fade-in effect"""
                if duration is not None:
                    self.fade_in_duration = duration
                    
                if self.fade_in_duration > 0:
                    self.fade_mode = 'in'
                    self.fade_alpha = 0
                    self.fade_start_time = pygame.time.get_ticks() / 1000.0
                    self.fade_progress = 0.0
                    self.playing = True
            
            def start_fade_out(self, duration=None):
                """Start fade-out effect"""
                if duration is not None:
                    self.fade_out_duration = duration
                    
                if self.fade_out_duration > 0:
                    self.fade_mode = 'out'
                    self.fade_alpha = 255
                    self.fade_start_time = pygame.time.get_ticks() / 1000.0
                    self.fade_progress = 0.0
            
            def set_fade_alpha(self, alpha):
                """Manually set fade alpha"""
                self.fade_alpha = max(0, min(255, alpha))
                self.fade_mode = None
            
            def is_fade_complete(self):
                """Check if fade effect is complete"""
                return self.fade_mode is None
        
        self.walk_animation = PlaceholderAnimation(
            placeholder_frames, 
            1.0 / self.animation_speed,
            self.fade_in_duration,
            self.fade_out_duration
        )
        self.idle_animation = PlaceholderAnimation(
            placeholder_frames[::-1], 
            1.5 / self.animation_speed,
            self.fade_in_duration,
            self.fade_out_duration
        )
        self.current_animation = self.walk_animation
        self.current_animation_name = "Walk (Placeholder)"
        
        print("Using placeholder animations with fade support - tiki_texture.png not found!")
    
    def setup_ui(self):
        """Setup user interface elements with fade controls"""
        
        # Title
        title = TextLabel(512, 30, "Sprite Sheet System Test", 48, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(title)
        
        # Animation info
        self.info_label = TextLabel(512, 80, "Press SPACE to switch animations", 24, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(self.info_label)
        
        # Current animation display
        self.anim_name_label = TextLabel(512, 110, f"Current: {self.current_animation_name}", 32, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(self.anim_name_label)
        
        # Frame counter
        self.frame_label = TextLabel(512, 150, "Frame: 1/6", 24, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(self.frame_label)
        
        # Speed control
        speed_label = TextLabel(200, 200, "Animation Speed:", 24, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(speed_label)
        
        self.speed_slider = Slider(200, 230, 200, 20, 0.1, 3.0, self.animation_speed, root_point=(0, 0), theme=self.CurrentTheme)
        self.speed_slider.on_value_changed = self.on_speed_changed
        self.ui_elements.append(self.speed_slider)
        
        self.speed_value_label = TextLabel(410, 230, f"{self.animation_speed:.1f}x", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(self.speed_value_label)
        
        # Zoom control
        zoom_label = TextLabel(200, 270, "Zoom Level:", 24, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(zoom_label)
        
        self.zoom_slider = Slider(200, 300, 200, 20, 0.5, 4.0, self.animation_scale, root_point=(0, 0), theme=self.CurrentTheme)
        self.zoom_slider.on_value_changed = self.on_zoom_changed
        self.ui_elements.append(self.zoom_slider)
        
        self.zoom_value_label = TextLabel(410, 300, f"{self.animation_scale:.1f}x", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(self.zoom_value_label)
        
        # Fade-in control
        fade_in_label = TextLabel(200, 340, "Fade-in Duration:", 24, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(fade_in_label)
        
        self.fade_in_slider = Slider(200, 370, 200, 20, 0.0, 3.0, self.fade_in_duration, root_point=(0, 0), theme=self.CurrentTheme)
        self.fade_in_slider.on_value_changed = self.on_fade_in_changed
        self.ui_elements.append(self.fade_in_slider)
        
        self.fade_in_value_label = TextLabel(410, 370, f"{self.fade_in_duration:.1f}s", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(self.fade_in_value_label)
        
        # Fade-out control
        fade_out_label = TextLabel(200, 410, "Fade-out Duration:", 24, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(fade_out_label)
        
        self.fade_out_slider = Slider(200, 440, 200, 20, 0.0, 3.0, self.fade_out_duration, root_point=(0, 0), theme=self.CurrentTheme)
        self.fade_out_slider.on_value_changed = self.on_fade_out_changed
        self.ui_elements.append(self.fade_out_slider)
        
        self.fade_out_value_label = TextLabel(410, 440, f"{self.fade_out_duration:.1f}s", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(self.fade_out_value_label)
        
        # Auto-fade toggle
        self.auto_fade_toggle = Switch(200, 490, 40, 20, self.auto_fade_transitions, root_point=(0, 0), theme=self.CurrentTheme)
        self.auto_fade_toggle.set_on_toggle(self.on_auto_fade_changed)
        self.ui_elements.append(self.auto_fade_toggle)
        
        auto_fade_label = TextLabel(230, 480, "Auto fade on switch", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(auto_fade_label)
        
        # Control buttons
        play_btn = Button(200, 520, 80, 30, "Play", 20, root_point=(0, 0), theme=self.CurrentTheme)
        play_btn.set_on_click(self.play_animation)
        self.ui_elements.append(play_btn)
        
        pause_btn = Button(290, 520, 80, 30, "Pause", 20, root_point=(0, 0), theme=self.CurrentTheme)
        pause_btn.set_on_click(self.pause_animation)
        self.ui_elements.append(pause_btn)
        
        reset_btn = Button(380, 520, 80, 30, "Reset", 20, root_point=(0, 0), theme=self.CurrentTheme)
        reset_btn.set_on_click(self.reset_animation)
        self.ui_elements.append(reset_btn)
        
        # Fade effect buttons
        fade_in_btn = Button(470, 520, 100, 30, "Fade In", 18, root_point=(0, 0), theme=self.CurrentTheme)
        fade_in_btn.set_on_click(self.trigger_fade_in)
        self.ui_elements.append(fade_in_btn)
        
        fade_out_btn = Button(580, 520, 100, 30, "Fade Out", 18, root_point=(0, 0), theme=self.CurrentTheme)
        fade_out_btn.set_on_click(self.trigger_fade_out)
        self.ui_elements.append(fade_out_btn)
        
        # Apply settings button
        apply_btn = Button(200, 560, 120, 30, "Apply Settings", 20, root_point=(0, 0), theme=self.CurrentTheme)
        apply_btn.set_on_click(self.apply_settings)
        self.ui_elements.append(apply_btn)
        
        # Back to menu button
        back_btn = Button(50, 50, 120, 30, "← Main Menu", 20, root_point=(0, 0), theme=self.CurrentTheme)
        back_btn.set_on_click(lambda: self.engine.set_scene("MainMenu"))
        self.ui_elements.append(back_btn)
    
    def on_speed_changed(self, value):
        """Handle speed slider change"""
        self.animation_speed = value
        self.speed_value_label.set_text(f"{value:.1f}x")
    
    def on_zoom_changed(self, value):
        """Handle zoom slider change"""
        self.animation_scale = value
        self.zoom_value_label.set_text(f"{value:.1f}x")
    
    def on_fade_in_changed(self, value):
        """Handle fade-in slider change"""
        self.fade_in_duration = value
        self.fade_in_value_label.set_text(f"{value:.1f}s")
    
    def on_fade_out_changed(self, value):
        """Handle fade-out slider change"""
        self.fade_out_duration = value
        self.fade_out_value_label.set_text(f"{value:.1f}s")
    
    def on_auto_fade_changed(self, value):
        """Handle auto-fade toggle change"""
        self.auto_fade_transitions = value
        print(f"Auto fade transitions: {'ON' if value else 'OFF'}")
    
    def apply_settings(self):
        """Apply current speed, zoom and fade settings"""
        print(f"Applying settings - Speed: {self.animation_speed}x, Zoom: {self.animation_scale}x, Fade-in: {self.fade_in_duration}s, Fade-out: {self.fade_out_duration}s")
        self.reload_animations_with_new_settings()
    
    def switch_animation(self):
        """Switch between walk and idle animations with optional fade effects"""
        if self.current_animation and self.auto_fade_transitions:
            # Start fade out on current animation
            self.current_animation.start_fade_out(self.fade_out_duration)
            
            # Wait for fade out to complete before switching
            # In a real game, you'd use a callback or state machine
            # For this demo, we'll switch immediately but the fade will continue
            pass
        
        # Switch animation
        if self.current_animation == self.walk_animation:
            self.current_animation = self.idle_animation
            self.current_animation_name = "Idle"
        else:
            self.current_animation = self.walk_animation
            self.current_animation_name = "Walk"
        
        if self.current_animation and self.auto_fade_transitions:
            # Start fade in on new animation
            self.current_animation.start_fade_in(self.fade_in_duration)
        
        self.current_animation.reset()
        self.current_animation.play()
        self.anim_name_label.set_text(f"Current: {self.current_animation_name}")
        print(f"Switched to {self.current_animation_name} animation")
    
    def trigger_fade_in(self):
        """Trigger fade-in effect on current animation"""
        if self.current_animation:
            self.current_animation.start_fade_in(self.fade_in_duration)
            print("Triggered fade-in effect")
    
    def trigger_fade_out(self):
        """Trigger fade-out effect on current animation"""
        if self.current_animation:
            self.current_animation.start_fade_out(self.fade_out_duration)
            print("Triggered fade-out effect")
    
    def play_animation(self):
        """Play the current animation"""
        if self.current_animation:
            self.current_animation.play()
            print("Animation playing")
    
    def pause_animation(self):
        """Pause the current animation"""
        if self.current_animation:
            self.current_animation.pause()
            print("Animation paused")
    
    def reset_animation(self):
        """Reset the current animation"""
        if self.current_animation:
            self.current_animation.reset()
            print("Animation reset")
    
    def handle_key_press(self, key):
        """Handle keyboard input"""
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
        elif key == pygame.K_a:
            # Apply settings with keyboard shortcut
            self.apply_settings()
        elif key == pygame.K_i:
            # Trigger fade-in with keyboard
            self.trigger_fade_in()
        elif key == pygame.K_o:
            # Trigger fade-out with keyboard
            self.trigger_fade_out()
        elif key == pygame.K_f:
            # Toggle auto-fade
            self.auto_fade_transitions = not self.auto_fade_transitions
            self.auto_fade_toggle.set_value(self.auto_fade_transitions)
            print(f"Auto fade transitions: {'ON' if self.auto_fade_transitions else 'OFF'}")
    
    def update(self, dt):
        """Update scene logic"""
        # Update current animation
        if self.current_animation:
            self.current_animation.update()
            
            # Update frame counter
            frame_count = self.current_animation.get_frame_count()
            current_frame = self.current_animation.current_frame_index + 1
            self.frame_label.set_text(f"Frame: {current_frame}/{frame_count}")
            
            # Update fade status display
            fade_status = ""
            if hasattr(self.current_animation, 'fade_mode') and self.current_animation.fade_mode:
                fade_status = f" | Fade: {self.current_animation.fade_mode.upper()} ({self.current_animation.fade_alpha}/255)"
            self.frame_label.set_text(f"Frame: {current_frame}/{frame_count}{fade_status}")
    
    def render(self, renderer: PygameRenderer):
        """Render the scene"""
        # Draw background
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw current animation centered
        if self.current_animation:
            frame = self.current_animation.get_current_frame()
            if frame:
                x = 700 - frame.get_width() // 2
                y = 400 - frame.get_height() // 2
                
                # Draw bounding box
                renderer.draw_rect(x, y, frame.get_width(), frame.get_height(), (255, 255, 255), fill=False)
                
                # Draw the frame (with fade effect already applied)
                renderer.draw_surface(frame, x, y)
                
                # Draw animation info below the sprite
                fade_info = ""
                if hasattr(self.current_animation, 'fade_alpha') and self.current_animation.fade_alpha < 255:
                    fade_info = f" | Alpha: {self.current_animation.fade_alpha}/255"
                
                info_text = f"{self.current_animation_name} - {self.animation_speed:.1f}x speed - {self.animation_scale:.1f}x zoom{fade_info}"
                font = pygame.font.Font(None, 24)
                text_surface = font.render(info_text, True, (255, 255, 255))
                renderer.draw_surface(text_surface, x, y + frame.get_height() + 10)
        
        # Draw UI elements
        for element in self.ui_elements:
            element.render(renderer)


class MainMenuScene(Scene):
    """
    Simple main menu for the sprite sheet test.
    """
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.CurrentTheme = ThemeType.DEFAULT
        
        # Title
        title = TextLabel(512, 150, "Sprite Sheet Test", 72, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(title)
        
        subtitle = TextLabel(512, 220, "LunaEngine Animation System", 36, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(subtitle)
        
        subtitle2 = TextLabel(512, 260, "Now with Fade Effects!", 28, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(subtitle2)
        
        # Demo button
        spritesheet_btn = Button(512, 320, 250, 40, "Start Test", 28, root_point=(0.5, 0), theme=self.CurrentTheme)
        spritesheet_btn.set_on_click(lambda: engine.set_scene("SpriteSheetTest"))
        self.ui_elements.append(spritesheet_btn)
        
        exit_btn = Button(512, 380, 250, 40, "Exit", 28, root_point=(0.5, 0), theme=self.CurrentTheme)
        exit_btn.set_on_click(lambda: setattr(engine, 'running', False))
        self.ui_elements.append(exit_btn)
    
    def on_enter(self, previous_scene=None):
        super().on_enter(previous_scene)
        print("Entered Main Menu")
    
    def on_exit(self, next_scene=None):
        super().on_exit(next_scene)
        print("Exiting Main Menu")
    
    def update(self, dt):
        pass
    
    def render(self, renderer: PygameRenderer):
        # Draw background
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw UI
        for element in self.ui_elements:
            element.render(renderer)


def main():
    """Main entry point for the sprite sheet test"""
    engine = LunaEngine("LunaEngine - Sprite Sheet Test with Fade Effects", 1024, 720, True)
    engine.fps = 60
    
    # Add scenes
    engine.add_scene("MainMenu", MainMenuScene)
    engine.add_scene("SpriteSheetTest", SpriteSheetTestScene)
    
    # Start with main menu
    engine.set_scene("MainMenu")
    engine.run()


if __name__ == "__main__":
    main()