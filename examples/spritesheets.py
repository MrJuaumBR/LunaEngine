"""
Sprite Sheets Example - Testing SpriteSheet and Animation System with LunaEngine

LOCATION: examples/spritesheets.py

DESCRIPTION:
Simple test scene to demonstrate the sprite sheet and animation system
using the tiki_texture.png file. Follows the same structure as snake_demo.py
but focused solely on testing sprite sheet functionality.

USAGE:
Run this file to test the sprite sheet system with LunaEngine scenes.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine
from lunaengine.ui.elements import *
from lunaengine.backend.pygame_backend import PygameRenderer
from lunaengine.graphics.spritesheet import Animation
import pygame

class SpriteSheetTestScene(Scene):
    """
    Test scene for sprite sheet and animation system.
    
    Demonstrates how to use the Animation class within a LunaEngine scene
    with proper scene lifecycle methods.
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
        """Load the tiki texture animations"""
        try:
            texture_path = "./examples/tiki_texture.png"
            print(os.listdir("./examples/"))
            
            # Walk animation - 6 frames starting at (0, 0)
            self.walk_animation = Animation(
                spritesheet_file=texture_path,
                size=(70, 70),
                start_pos=(0, 0),
                frame_count=6,
                scale=(self.animation_scale, self.animation_scale),
                duration=1.0 / self.animation_speed,  # Apply speed factor
                loop=True
            )
            
            # Idle animation - 6 frames starting at (0, 70)
            self.idle_animation = Animation(
                spritesheet_file=texture_path,
                size=(70, 70),
                start_pos=(0, 70),
                frame_count=6,
                scale=(self.animation_scale, self.animation_scale),
                duration=1.5 / self.animation_speed,  # Apply speed factor
                loop=True
            )
            
            # Set current animation
            self.current_animation = self.walk_animation
            self.current_animation_name = "Walk"
            
            print("Successfully loaded tiki texture animations!")
            print(f"Walk animation: {self.walk_animation.get_frame_count()} frames")
            print(f"Idle animation: {self.idle_animation.get_frame_count()} frames")
            
        except Exception as e:
            print(f"Error loading animations: {e}")
            # Create placeholder animations if loading fails
            self.create_placeholder_animations()
    
    def reload_animations_with_new_settings(self):
        """Reload animations with current scale and speed settings"""
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
        
        # Create simple animation object
        class PlaceholderAnimation:
            def __init__(self, frames, duration=1.0):
                self.frames = frames
                self.duration = duration
                self.frame_duration = duration / len(frames) if frames else 0
                self.current_frame_index = 0
                self.last_update_time = pygame.time.get_ticks() / 1000.0
                self.accumulated_time = 0.0
                self.playing = True
                self.loop = True
            
            def update(self):
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
                if not self.frames:
                    return pygame.Surface((1, 1), pygame.SRCALPHA)
                return self.frames[self.current_frame_index]
            
            def reset(self):
                self.current_frame_index = 0
                self.accumulated_time = 0.0
                self.last_update_time = pygame.time.get_ticks() / 1000.0
                self.playing = True
            
            def play(self):
                self.playing = True
                self.last_update_time = pygame.time.get_ticks() / 1000.0
            
            def pause(self):
                self.playing = False
            
            def get_frame_count(self):
                return len(self.frames)
            
            def set_duration(self, new_duration):
                self.duration = new_duration
                self.frame_duration = new_duration / len(self.frames) if self.frames else 0
        
        self.walk_animation = PlaceholderAnimation(placeholder_frames, 1.0 / self.animation_speed)
        self.idle_animation = PlaceholderAnimation(placeholder_frames[::-1], 1.5 / self.animation_speed)
        self.current_animation = self.walk_animation
        self.current_animation_name = "Walk (Placeholder)"
        
        print("Using placeholder animations - tiki_texture.png not found!")
    
    def setup_ui(self):
        """Setup user interface elements"""
        
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
        
        # Control buttons
        play_btn = Button(200, 350, 80, 30, "Play", 20, root_point=(0, 0), theme=self.CurrentTheme)
        play_btn.set_on_click(self.play_animation)
        self.ui_elements.append(play_btn)
        
        pause_btn = Button(290, 350, 80, 30, "Pause", 20, root_point=(0, 0), theme=self.CurrentTheme)
        pause_btn.set_on_click(self.pause_animation)
        self.ui_elements.append(pause_btn)
        
        reset_btn = Button(380, 350, 80, 30, "Reset", 20, root_point=(0, 0), theme=self.CurrentTheme)
        reset_btn.set_on_click(self.reset_animation)
        self.ui_elements.append(reset_btn)
        
        # Apply settings button
        apply_btn = Button(200, 390, 120, 30, "Apply Settings", 20, root_point=(0, 0), theme=self.CurrentTheme)
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
    
    def apply_settings(self):
        """Apply current speed and zoom settings"""
        print(f"Applying settings - Speed: {self.animation_speed}x, Zoom: {self.animation_scale}x")
        self.reload_animations_with_new_settings()
    
    def switch_animation(self):
        """Switch between walk and idle animations"""
        if self.current_animation == self.walk_animation:
            self.current_animation = self.idle_animation
            self.current_animation_name = "Idle"
        else:
            self.current_animation = self.walk_animation
            self.current_animation_name = "Walk"
        
        self.current_animation.reset()
        self.current_animation.play()
        self.anim_name_label.set_text(f"Current: {self.current_animation_name}")
        print(f"Switched to {self.current_animation_name} animation")
    
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
    
    def update(self, dt):
        """Update scene logic"""
        # Update current animation
        if self.current_animation:
            self.current_animation.update()
            
            # Update frame counter
            frame_count = self.current_animation.get_frame_count()
            current_frame = self.current_animation.current_frame_index + 1
            self.frame_label.set_text(f"Frame: {current_frame}/{frame_count}")
    
    def render(self, renderer: PygameRenderer):
        """Render the scene"""
        # Draw background
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw current animation centered
        if self.current_animation:
            frame = self.current_animation.get_current_frame()
            if frame:
                x = 700 - frame.get_width() // 2  # Moved to right side for better UI layout
                y = 400 - frame.get_height() // 2
                renderer.draw_surface(frame, x, y)
                
                # Draw frame border
                renderer.draw_rect(x, y, frame.get_width(), frame.get_height(), (255, 255, 255), fill=False)
                
                # Draw animation info below the sprite
                info_text = f"{self.current_animation_name} - {self.animation_speed:.1f}x speed - {self.animation_scale:.1f}x zoom"
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
    engine = LunaEngine("LunaEngine - Sprite Sheet Test", 1024, 720)
    engine.fps = 60
    
    # Add scenes
    engine.add_scene("MainMenu", MainMenuScene)
    engine.add_scene("SpriteSheetTest", SpriteSheetTestScene)
    
    # Start with main menu
    engine.set_scene("MainMenu")
    engine.run()


if __name__ == "__main__":
    main()