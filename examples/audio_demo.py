"""
Advanced Audio Demo - Testing Multi-Channel Audio with Real Speed Control

LOCATION: examples/audio_demo.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine, AudioSystem, AudioEvent, AudioState
from lunaengine.ui.elements import *
import pygame
import math

class AudioDemoScene(Scene):
    """
    Advanced audio system demonstration with multi-channel support.
    """
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.CurrentTheme = ThemeType.DEFAULT
        
        # Advanced audio system
        self.audio_system = AudioSystem(num_channels=16)
        
        # Channel management
        self.active_channels = {}
        self.channel_counters = {
            'explosion': 0,
            'music': 0
        }
        
        # Audio state
        self.music_volume = 0.8
        self.sfx_volume = 0.9
        self.playback_speed = 1.0
        self.fade_duration = 2.0
        
        # Visual feedback
        self.visual_effects = []
        self.audio_events_log = []
        
        # Setup UI
        self.setup_ui()
        
        # Load audio files
        self.load_audio_files()
        
        # Register key events
        @engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
    
    def load_audio_files(self):
        """Load audio files for testing"""
        try:
            # Load explosion sound effect
            explosion_path = "./examples/explosion.wav"
            if os.path.exists(explosion_path):
                self.audio_system.load_sound_effect("explosion", explosion_path)
                print("Loaded explosion.wav successfully")
            else:
                print(f"Warning: explosion.wav not found at {explosion_path}")
                self.create_placeholder_sounds()
            
            # Load music file
            music_path = "./examples/music.mp3"
            if os.path.exists(music_path):
                self.audio_system.load_music("background", music_path)
                print("Loaded music.mp3 successfully")
            else:
                print(f"Warning: music.mp3 not found at {music_path}")
                
        except Exception as e:
            print(f"Error loading audio files: {e}")
            self.create_placeholder_sounds()
    
    def create_placeholder_sounds(self):
        """Create placeholder sounds if files are not available"""
        # Similar to previous implementation but for advanced system
        pass
    
    def setup_ui(self):
        """Setup comprehensive audio controls UI"""
        # Title and basic controls (similar to before but enhanced)
        title = TextLabel(512, 30, "Advanced Audio Demo", 48, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(title)
        
        subtitle = TextLabel(512, 80, "Multi-Channel Audio with Speed Control", 24, root_point=(0.5, 0), theme=self.CurrentTheme)
        self.ui_elements.append(subtitle)
        
        # Multi-channel explosion controls
        self.setup_multi_channel_ui()
        
        # Music controls with speed
        self.setup_music_ui()
        
        # Channel monitor
        self.setup_channel_monitor()
        
        # Back button
        back_btn = Button(50, 50, 120, 30, "← Main Menu", 20, root_point=(0, 0), theme=self.CurrentTheme)
        back_btn.set_on_click(lambda: self.engine.set_scene("MainMenu"))
        self.ui_elements.append(back_btn)
    
    def setup_multi_channel_ui(self):
        """Setup multi-channel sound effect controls"""
        sfx_title = TextLabel(200, 130, "Multi-Channel Sound Effects", 28, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(sfx_title)
        
        # Channel 1 controls
        ch1_label = TextLabel(200, 170, "Channel 1:", 20, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(ch1_label)
        
        ch1_play = Button(300, 170, 120, 30, "Play", 18, root_point=(0, 0), theme=self.CurrentTheme)
        ch1_play.set_on_click(lambda: self.play_channel_sound(1, 1.0, 1.0))
        self.ui_elements.append(ch1_play)
        
        ch1_slow = Button(430, 170, 120, 30, "Slow (0.5x)", 18, root_point=(0, 0), theme=self.CurrentTheme)
        ch1_slow.set_on_click(lambda: self.play_channel_sound(1, 1.0, 0.5))
        self.ui_elements.append(ch1_slow)
        
        ch1_fast = Button(560, 170, 120, 30, "Fast (2.0x)", 18, root_point=(0, 0), theme=self.CurrentTheme)
        ch1_fast.set_on_click(lambda: self.play_channel_sound(1, 1.0, 2.0))
        self.ui_elements.append(ch1_fast)
        
        # Channel 2 controls
        ch2_label = TextLabel(200, 210, "Channel 2:", 20, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(ch2_label)
        
        ch2_play = Button(300, 210, 120, 30, "Play", 18, root_point=(0, 0), theme=self.CurrentTheme)
        ch2_play.set_on_click(lambda: self.play_channel_sound(2, 0.7, 1.0))
        self.ui_elements.append(ch2_play)
        
        ch2_quiet = Button(430, 210, 120, 30, "Quiet (0.3x)", 18, root_point=(0, 0), theme=self.CurrentTheme)
        ch2_quiet.set_on_click(lambda: self.play_channel_sound(2, 0.3, 1.0))
        self.ui_elements.append(ch2_quiet)
        
        ch2_loop = Button(560, 210, 120, 30, "Loop", 18, root_point=(0, 0), theme=self.CurrentTheme)
        ch2_loop.set_on_click(lambda: self.play_channel_sound(2, 0.7, 1.0, True))
        self.ui_elements.append(ch2_loop)
        
        # Stop all channels
        stop_all = Button(200, 250, 200, 35, "Stop All Channels", 20, root_point=(0, 0), theme=self.CurrentTheme)
        stop_all.set_on_click(self.stop_all_channels)
        self.ui_elements.append(stop_all)
    
    def setup_music_ui(self):
        """Setup music controls with speed adjustment"""
        music_title = TextLabel(200, 300, "Music Controls with Speed", 28, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(music_title)
        
        # Music speed controls
        speed_label = TextLabel(200, 340, "Music Speed:", 20, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(speed_label)
        
        self.music_speed_slider = Slider(320, 340, 200, 20, 0.5, 2.0, 1.0, root_point=(0, 0), theme=self.CurrentTheme)
        self.music_speed_slider.on_value_changed = self.on_music_speed_changed
        self.ui_elements.append(self.music_speed_slider)
        
        self.music_speed_value = TextLabel(530, 340, "1.0x", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(self.music_speed_value)
        
        # Music controls
        play_music = Button(200, 380, 100, 30, "Play", 18, root_point=(0, 0), theme=self.CurrentTheme)
        play_music.set_on_click(self.play_music)
        self.ui_elements.append(play_music)
        
        pause_music = Button(310, 380, 100, 30, "Pause", 18, root_point=(0, 0), theme=self.CurrentTheme)
        pause_music.set_on_click(self.pause_music)
        self.ui_elements.append(pause_music)
        
        stop_music = Button(420, 380, 100, 30, "Stop", 18, root_point=(0, 0), theme=self.CurrentTheme)
        stop_music.set_on_click(self.stop_music)
        self.ui_elements.append(stop_music)
        
        # Apply speed to current music
        apply_speed = Button(530, 380, 120, 30, "Apply Speed", 18, root_point=(0, 0), theme=self.CurrentTheme)
        apply_speed.set_on_click(self.apply_music_speed)
        self.ui_elements.append(apply_speed)
    
    def setup_channel_monitor(self):
        """Setup channel monitoring display"""
        monitor_title = TextLabel(200, 430, "Channel Monitor", 28, root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(monitor_title)
        
        self.channel_monitor = TextLabel(200, 470, "Channels: 0/16 active", 18, (200, 230, 255), root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(self.channel_monitor)
        
        self.channel_details = TextLabel(200, 500, "No active channels", 14, (180, 200, 220), root_point=(0, 0), theme=self.CurrentTheme)
        self.ui_elements.append(self.channel_details)
    
    def play_channel_sound(self, channel_num: int, volume: float, speed: float, loop: bool = False):
        """Play sound on specific channel with custom settings"""
        channel_key = f"explosion_{channel_num}"
        
        # Stop existing sound on this channel if any
        if channel_key in self.active_channels:
            self.active_channels[channel_key].stop()
        
        # Play new sound
        channel = self.audio_system.play_sound("explosion", volume, speed, loop)
        if channel:
            self.active_channels[channel_key] = channel
            self.add_audio_event(f"Channel {channel_num}: vol={volume}, speed={speed}x")
            
            # Create visual effect
            self.create_channel_effect(channel_num, volume, speed)
    
    def play_music(self):
        """Play background music"""
        if self.audio_system.play_music("background", self.music_volume, self.playback_speed):
            self.add_audio_event(f"Music started (speed: {self.playback_speed}x)")
        else:
            self.add_audio_event("Failed to play music")
    
    def pause_music(self):
        """Pause music"""
        self.audio_system.pause_music()
        self.add_audio_event("Music paused")
    
    def stop_music(self):
        """Stop music"""
        self.audio_system.stop_music()
        self.add_audio_event("Music stopped")
    
    def on_music_speed_changed(self, value):
        """Handle music speed slider change"""
        self.playback_speed = value
        self.music_speed_value.set_text(f"{value:.1f}x")
    
    def apply_music_speed(self):
        """Apply speed change to current music"""
        if self.audio_system.music_channel.is_playing():
            self.audio_system.music_channel.set_speed(self.playback_speed)
            self.add_audio_event(f"Music speed: {self.playback_speed}x")
    
    def stop_all_channels(self):
        """Stop all sound effect channels"""
        for channel_key in list(self.active_channels.keys()):
            if channel_key.startswith('explosion_'):
                self.active_channels[channel_key].stop()
                del self.active_channels[channel_key]
        
        self.audio_system.stop_all_sounds()
        self.add_audio_event("All channels stopped")
    
    def create_channel_effect(self, channel_num: int, volume: float, speed: float):
        """Create visual effect for channel playback"""
        x = 700 + (channel_num - 1) * 60
        y = 200
        
        self.visual_effects.append({
            'type': 'channel',
            'channel': channel_num,
            'x': x,
            'y': y,
            'volume': volume,
            'speed': speed,
            'timer': 0,
            'max_time': 2.0
        })
    
    def add_audio_event(self, event_text):
        """Add event to log"""
        self.audio_events_log.append(event_text)
        if len(self.audio_events_log) > 4:
            self.audio_events_log.pop(0)
        
        events_text = " | ".join(self.audio_events_log)
        # Update some UI element to show events
    
    def handle_key_press(self, key):
        """Handle keyboard input"""
        if key == pygame.K_ESCAPE:
            self.engine.set_scene("MainMenu")
        elif key == pygame.K_1:
            self.play_channel_sound(1, 1.0, 1.0)
        elif key == pygame.K_2:
            self.play_channel_sound(2, 0.7, 1.0)
        elif key == pygame.K_3:
            self.play_channel_sound(1, 1.0, 0.5)  # Slow
        elif key == pygame.K_4:
            self.play_channel_sound(2, 0.3, 2.0)  # Fast and quiet
    
    def update(self, dt):
        """Update scene logic"""
        # Update visual effects
        for effect in self.visual_effects[:]:
            effect['timer'] += dt
            if effect['timer'] >= effect['max_time']:
                self.visual_effects.remove(effect)
        
        # Update channel monitor
        channel_info = self.audio_system.get_channel_info()
        active_count = channel_info['busy_channels']
        self.channel_monitor.set_text(f"Channels: {active_count}/{len(self.audio_system.channels)} active")
        
        # Show details of active channels
        details = []
        for chan_info in channel_info['channels']:
            if chan_info['playing'] or chan_info['paused']:
                status = "PLAYING" if chan_info['playing'] else "PAUSED"
                details.append(f"Ch{chan_info['id']}: {status} (vol:{chan_info['volume']:.1f}, spd:{chan_info['speed']:.1f}x)")
        
        if details:
            self.channel_details.set_text(" | ".join(details[:3]))  # Show first 3
        else:
            self.channel_details.set_text("No active channels")
    
    def render(self, renderer):
        """Render the scene"""
        # Draw background
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw channel visualizations
        self.draw_channel_visualizations(renderer)
        
        # Draw UI elements
        for element in self.ui_elements:
            element.render(renderer)
    
    def draw_channel_visualizations(self, renderer):
        """Draw channel activity visualization"""
        # Draw channel grid
        for i in range(16):
            x = 700 + (i % 4) * 60
            y = 300 + (i // 4) * 60
            
            # Channel box
            color = (60, 60, 80)
            renderer.draw_rect(x, y, 50, 50, color)
            renderer.draw_rect(x, y, 50, 50, (100, 100, 120), fill=False)
            
            # Channel number
            font = pygame.font.Font(None, 20)
            text = font.render(str(i), True, (200, 200, 200))
            renderer.draw_surface(text, x + 20, y + 15)
            
            # Activity indicator
            if i < len(self.audio_system.channels):
                channel = self.audio_system.channels[i]
                if channel.is_playing():
                    # Green for playing
                    renderer.draw_rect(x + 5, y + 35, 40, 10, (50, 200, 50))
                elif channel.is_paused():
                    # Yellow for paused
                    renderer.draw_rect(x + 5, y + 35, 40, 10, (200, 200, 50))

# Main function and menu scene similar to previous example
def main():
    """Main entry point"""
    engine = LunaEngine("LunaEngine - Advanced Audio Demo", 1024, 720, True)
    engine.fps = 60
    
    # Initialize advanced audio system
    engine.audio_system = AudioSystem(num_channels=16)
    
    # Add scenes (you'd need to create a main menu scene)
    engine.add_scene("AudioDemo", AudioDemoScene)
    engine.set_scene("AudioDemo")
    
    print("=== Advanced Audio System Demo ===")
    print("Features:")
    print("- 16 independent audio channels")
    print("- Real speed control (pitch adjustment)")
    print("- Individual volume per channel")
    print("- Channel monitoring")
    print("- Visual feedback")
    
    engine.run()

if __name__ == "__main__":
    main()