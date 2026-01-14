"""
Enhanced Audio Demo - Testing Multi-Channel Audio with Dynamic Control and Smooth Transitions

LOCATION: examples/audio_demo.py

NEW FEATURES:
- Dynamic speed changes without stopping playback
- Smooth volume and speed transitions
- Audio duration information
- Enhanced pause/resume system
- Real-time audio information display
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine, AudioSystem, AudioEvent, AudioState
from lunaengine.ui.elements import *
import pygame

class AudioDemoScene(Scene):
    """
    Enhanced audio system demonstration with dynamic control and smooth transitions.
    """
    
    def on_enter(self, previous_scene = None):
        self.engine.set_global_theme(ThemeType.GRUVBOX_LIGHT)
        return super().on_enter(previous_scene)
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
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
        
        # NEW: Transition controls
        self.volume_transition_duration = 1.0
        self.speed_transition_duration = 1.5
        
        # Visual feedback
        self.visual_effects = []
        self.audio_events_log = []
        
        # NEW: Audio information
        self.audio_info = {
            'music_duration': 0.0,
            'sound_duration': 0.0,
            'current_position': 0.0
        }
        
        # Setup UI
        self.setup_ui()
        
        # Load audio files
        self.load_audio_files()
        
        # Register key events
        @engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
    
    def load_audio_files(self):
        """Load audio files for testing and get duration information"""
        try:
            # Load explosion sound effect
            explosion_path = "./examples/explosion.wav"
            if os.path.exists(explosion_path):
                self.audio_system.load_sound_effect("explosion", explosion_path)
                # NEW: Get sound duration
                self.audio_info['sound_duration'] = self.audio_system.get_sound_duration("explosion")
                print(f"Loaded explosion.wav successfully (duration: {self.audio_info['sound_duration']:.2f}s)")
            else:
                print(f"Warning: explosion.wav not found at {explosion_path}")
                self.create_placeholder_sounds()
            
            # Load music file
            music_path = "./examples/music.mp3"
            if os.path.exists(music_path):
                self.audio_system.load_music("background", music_path)
                # NEW: Get music duration
                self.audio_info['music_duration'] = self.audio_system.get_music_duration("background")
                print(f"Loaded music.mp3 successfully (duration: {self.audio_info['music_duration']:.2f}s)")
            else:
                print(f"Warning: music.mp3 not found at {music_path}")
                # Create placeholder music duration for demo
                self.audio_info['music_duration'] = 120.0  # 2 minutes placeholder
                
        except Exception as e:
            print(f"Error loading audio files: {e}")
            self.create_placeholder_sounds()
    
    def create_placeholder_sounds(self):
        """Create placeholder sounds if files are not available"""
        # For demo purposes, create some simple sounds programmatically
        try:
            # Create a simple beep sound
            sample_rate = 44100
            duration = 1.0  # seconds
            frames = int(duration * sample_rate)
            
            # Generate a simple square wave
            arr = np.zeros((frames, 2), dtype=np.int16)
            for i in range(frames):
                # 440 Hz square wave
                val = 16000 if (i // 50) % 2 == 0 else -16000
                arr[i] = [val, val]
            
            sound = pygame.sndarray.make_sound(arr)
            self.audio_system.sound_effects["explosion"] = SoundEffect(sound)
            self.audio_info['sound_duration'] = duration
            
            print("Created placeholder explosion sound")
            
        except Exception as e:
            print(f"Error creating placeholder sounds: {e}")
    
    def setup_ui(self):
        """Setup comprehensive audio controls UI with new features"""
        # Title and basic controls
        title = TextLabel(512, 30, "Enhanced Audio Demo", 48, root_point=(0.5, 0))
        self.ui_elements.append(title)
        
        subtitle = TextLabel(512, 80, "Dynamic Control & Smooth Transitions", 24, root_point=(0.5, 0))
        self.ui_elements.append(subtitle)
        
        # Multi-channel explosion controls
        self.setup_multi_channel_ui()
        
        # Music controls with enhanced features
        self.setup_music_ui()
        
        # NEW: Transition controls section
        self.setup_transition_controls()
        
        # NEW: Audio information display
        self.setup_audio_info_display()
        
        # Channel monitor
        self.setup_channel_monitor()
        
        # Back button
        back_btn = Button(50, 50, 120, 30, "← Main Menu", 20, root_point=(0, 0), )
        back_btn.set_on_click(lambda: self.engine.set_scene("MainMenu"))
        self.ui_elements.append(back_btn)
    
    def setup_multi_channel_ui(self):
        """Setup multi-channel sound effect controls with new features"""
        sfx_title = TextLabel(200, 130, "Multi-Channel Sound Effects", 28, root_point=(0, 0), )
        self.ui_elements.append(sfx_title)
        
        # NEW: Sound duration info
        duration_label = TextLabel(200, 160, f"Sound Duration: {self.audio_info['sound_duration']:.2f}s", 16, 
                                 (180, 200, 220), root_point=(0, 0), )
        self.ui_elements.append(duration_label)
        
        # Channel 1 controls - Enhanced with transitions
        ch1_label = TextLabel(200, 190, "Channel 1:", 20, root_point=(0, 0), )
        self.ui_elements.append(ch1_label)
        
        ch1_play = Button(300, 190, 120, 30, "Play", 18, root_point=(0, 0), )
        ch1_play.set_on_click(lambda: self.play_channel_sound(1, 1.0, 1.0))
        self.ui_elements.append(ch1_play)
        
        ch1_slow = Button(430, 190, 120, 30, "Slow (0.5x)", 18, root_point=(0, 0), )
        ch1_slow.set_on_click(lambda: self.play_channel_sound(1, 1.0, 0.5))
        self.ui_elements.append(ch1_slow)
        
        ch1_fast = Button(560, 190, 120, 30, "Fast (2.0x)", 18, root_point=(0, 0), )
        ch1_fast.set_on_click(lambda: self.play_channel_sound(1, 1.0, 2.0))
        self.ui_elements.append(ch1_fast)
        
        # Channel 2 controls - Enhanced with transitions
        ch2_label = TextLabel(200, 230, "Channel 2:", 20, root_point=(0, 0), )
        self.ui_elements.append(ch2_label)
        
        ch2_play = Button(300, 230, 120, 30, "Play", 18, root_point=(0, 0), )
        ch2_play.set_on_click(lambda: self.play_channel_sound(2, 0.7, 1.0))
        self.ui_elements.append(ch2_play)
        
        ch2_quiet = Button(430, 230, 120, 30, "Quiet (0.3x)", 18, root_point=(0, 0), )
        ch2_quiet.set_on_click(lambda: self.play_channel_sound(2, 0.3, 1.0))
        self.ui_elements.append(ch2_quiet)
        
        ch2_loop = Button(560, 230, 120, 30, "Loop", 18, root_point=(0, 0), )
        ch2_loop.set_on_click(lambda: self.play_channel_sound(2, 0.7, 1.0, True))
        self.ui_elements.append(ch2_loop)
        
        # NEW: Dynamic control for channel 1
        ch1_dynamic = Button(200, 270, 180, 30, "Dynamic Speed Change", 16, root_point=(0, 0), )
        ch1_dynamic.set_on_click(lambda: self.dynamic_speed_change(1))
        self.ui_elements.append(ch1_dynamic)
        
        # NEW: Smooth volume change for channel 2
        ch2_smooth_vol = Button(390, 270, 180, 30, "Smooth Volume Change", 16, root_point=(0, 0), )
        ch2_smooth_vol.set_on_click(lambda: self.smooth_volume_change(2))
        self.ui_elements.append(ch2_smooth_vol)
        
        # Stop all channels
        stop_all = Button(580, 270, 120, 30, "Stop All", 16, root_point=(0, 0), )
        stop_all.set_on_click(self.stop_all_channels)
        self.ui_elements.append(stop_all)
    
    def setup_music_ui(self):
        """Setup music controls with enhanced features"""
        music_title = TextLabel(200, 320, "Music Controls", 28, root_point=(0, 0), )
        self.ui_elements.append(music_title)
        
        # NEW: Music duration info
        music_duration_label = TextLabel(200, 350, f"Music Duration: {self.audio_info['music_duration']:.2f}s", 16, 
                                       (180, 200, 220), root_point=(0, 0), )
        self.ui_elements.append(music_duration_label)
        
        # NEW: Current position display
        self.music_position_label = TextLabel(400, 350, "Position: 0.00s", 16, (200, 220, 255), root_point=(0, 0), )
        self.ui_elements.append(self.music_position_label)
        
        # Music speed controls
        speed_label = TextLabel(200, 380, "Music Speed:", 20, root_point=(0, 0), )
        self.ui_elements.append(speed_label)
        
        self.music_speed_slider = Slider(320, 380, 200, 20, 0.5, 2.0, 1.0, root_point=(0, 0), )
        self.music_speed_slider.on_value_changed = self.on_music_speed_changed
        self.ui_elements.append(self.music_speed_slider)
        
        self.music_speed_value = TextLabel(530, 380, "1.0x", 20, root_point=(0, 0.5), )
        self.ui_elements.append(self.music_speed_value)
        
        # Music controls
        play_music = Button(200, 420, 100, 30, "Play", 18, root_point=(0, 0), )
        play_music.set_on_click(self.play_music)
        self.ui_elements.append(play_music)
        
        pause_music = Button(310, 420, 100, 30, "Pause", 18, root_point=(0, 0), )
        pause_music.set_on_click(self.pause_music)
        self.ui_elements.append(pause_music)
        
        resume_music = Button(420, 420, 100, 30, "Resume", 18, root_point=(0, 0), )
        resume_music.set_on_click(self.resume_music)
        self.ui_elements.append(resume_music)
        
        stop_music = Button(530, 420, 100, 30, "Stop", 18, root_point=(0, 0), )
        stop_music.set_on_click(self.stop_music)
        self.ui_elements.append(stop_music)
        
        # NEW: Apply speed with transition
        apply_speed_smooth = Button(640, 420, 150, 30, "Smooth Speed Change", 16, root_point=(0, 0), )
        apply_speed_smooth.set_on_click(self.apply_music_speed_smooth)
        self.ui_elements.append(apply_speed_smooth)
    
    def setup_transition_controls(self):
        """NEW: Setup controls for smooth transitions"""
        transition_title = TextLabel(200, 470, "Smooth Transition Controls", 28, root_point=(0, 0), )
        self.ui_elements.append(transition_title)
        
        # Volume transition controls
        vol_trans_label = TextLabel(200, 510, "Volume Transition:", 18, root_point=(0, 0), )
        self.ui_elements.append(vol_trans_label)
        
        self.vol_transition_slider = Slider(360, 510, 150, 20, 0.1, 3.0, self.volume_transition_duration, root_point=(0, 0), )
        self.vol_transition_slider.on_value_changed = self.on_volume_transition_changed
        self.ui_elements.append(self.vol_transition_slider)
        
        self.vol_transition_value = TextLabel(520, 510, f"{self.volume_transition_duration:.1f}s", 18, root_point=(0, 0.5), )
        self.ui_elements.append(self.vol_transition_value)
        
        # Speed transition controls
        speed_trans_label = TextLabel(200, 540, "Speed Transition:", 18, root_point=(0, 0), )
        self.ui_elements.append(speed_trans_label)
        
        self.speed_transition_slider = Slider(360, 540, 150, 20, 0.1, 3.0, self.speed_transition_duration, root_point=(0, 0), )
        self.speed_transition_slider.on_value_changed = self.on_speed_transition_changed
        self.ui_elements.append(self.speed_transition_slider)
        
        self.speed_transition_value = TextLabel(520, 540, f"{self.speed_transition_duration:.1f}s", 18, root_point=(0, 0.5), )
        self.ui_elements.append(self.speed_transition_value)
        
        # Transition demo buttons
        fade_in_music = Button(200, 580, 140, 30, "Fade In Music", 16, root_point=(0, 0), )
        fade_in_music.set_on_click(self.fade_in_music_demo)
        self.ui_elements.append(fade_in_music)
        
        fade_out_music = Button(350, 580, 140, 30, "Fade Out Music", 16, root_point=(0, 0), )
        fade_out_music.set_on_click(self.fade_out_music_demo)
        self.ui_elements.append(fade_out_music)
        
        smooth_volume_test = Button(500, 580, 160, 30, "Smooth Volume Test", 16, root_point=(0, 0), )
        smooth_volume_test.set_on_click(self.smooth_volume_test)
        self.ui_elements.append(smooth_volume_test)
    
    def setup_audio_info_display(self):
        """NEW: Setup real-time audio information display"""
        info_title = TextLabel(700, 130, "Real-time Audio Info", 24, root_point=(0, 0), )
        self.ui_elements.append(info_title)
        
        self.music_state_label = TextLabel(700, 160, "Music: Stopped", 16, (200, 200, 200), root_point=(0, 0), )
        self.ui_elements.append(self.music_state_label)
        
        self.music_speed_label = TextLabel(700, 180, "Speed: 1.0x", 16, (200, 200, 200), root_point=(0, 0), )
        self.ui_elements.append(self.music_speed_label)
        
        self.music_volume_label = TextLabel(700, 200, "Volume: 0.0", 16, (200, 200, 200), root_point=(0, 0), )
        self.ui_elements.append(self.music_volume_label)
        
        self.active_channels_label = TextLabel(700, 230, "Active Channels: 0", 16, (200, 200, 200), root_point=(0, 0), )
        self.ui_elements.append(self.active_channels_label)
    
    def setup_channel_monitor(self):
        """Setup channel monitoring display"""
        monitor_title = TextLabel(200, 620, "Channel Monitor", 28, root_point=(0, 0), )
        self.ui_elements.append(monitor_title)
        
        self.channel_monitor = TextLabel(200, 650, "Channels: 0/16 active", 18, (200, 230, 255), root_point=(0, 0), )
        self.ui_elements.append(self.channel_monitor)
        
        self.channel_details = TextLabel(200, 670, "No active channels", 14, (180, 200, 220), root_point=(0, 0), )
        self.ui_elements.append(self.channel_details)
    
    # NEW: Enhanced audio control methods
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
    
    def dynamic_speed_change(self, channel_num: int):
        channel_key = f"explosion_{channel_num}"
        if channel_key in self.active_channels:
            channel = self.active_channels[channel_key]
            
            if channel.speed >= 2.0:
                new_speed = 0.5
            elif channel.speed >= 1.0:
                new_speed = 2.0
            else:
                new_speed = 1.0
            
            channel.set_speed(new_speed, self.speed_transition_duration)
            self.add_audio_event(f"Speed transition: {channel.speed:.1f}x → {new_speed:.1f}x")
    def smooth_volume_change(self, channel_num: int):
        """NEW: Demonstrate smooth volume transition"""
        channel_key = f"explosion_{channel_num}"
        if channel_key in self.active_channels and self.active_channels[channel_key].is_playing():
            channel = self.active_channels[channel_key]
            current_volume = channel.volume
            
            # Cycle through different volumes
            if current_volume >= 0.8:
                new_volume = 0.2
            elif current_volume >= 0.5:
                new_volume = 0.8
            else:
                new_volume = 0.5
            
            # Apply smooth volume transition
            channel.set_volume(new_volume, self.volume_transition_duration)
            self.add_audio_event(f"Ch{channel_num} volume: {current_volume:.1f} → {new_volume:.1f} ({self.volume_transition_duration:.1f}s)")
        else:
            self.add_audio_event(f"Channel {channel_num} not active")
    
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
    
    def resume_music(self):
        """NEW: Resume paused music"""
        self.audio_system.resume_music()
        self.add_audio_event("Music resumed")
    
    def stop_music(self):
        """Stop music"""
        self.audio_system.stop_music()
        self.add_audio_event("Music stopped")
    
    def on_music_speed_changed(self, value):
        """Handle music speed slider change"""
        self.playback_speed = value
        self.music_speed_value.set_text(f"{value:.1f}x")
    
    def apply_music_speed_smooth(self):
        """NEW: Apply speed change with smooth transition"""
        if self.audio_system.music_channel.is_playing():
            self.audio_system.music_channel.set_speed(self.playback_speed, self.speed_transition_duration)
            self.add_audio_event(f"Music speed: {self.playback_speed:.1f}x ({self.speed_transition_duration:.1f}s transition)")
        else:
            self.add_audio_event("No music playing")
    
    def on_volume_transition_changed(self, value):
        """NEW: Handle volume transition duration change"""
        self.volume_transition_duration = value
        self.vol_transition_value.set_text(f"{value:.1f}s")
    
    def on_speed_transition_changed(self, value):
        """NEW: Handle speed transition duration change"""
        self.speed_transition_duration = value
        self.speed_transition_value.set_text(f"{value:.1f}s")
    
    def fade_in_music_demo(self):
        """NEW: Demonstrate music fade in"""
        if self.audio_system.fade_in_music("background", self.volume_transition_duration, self.music_volume, self.playback_speed):
            self.add_audio_event(f"Music fade in ({self.volume_transition_duration:.1f}s)")
        else:
            self.add_audio_event("Failed to fade in music")
    
    def fade_out_music_demo(self):
        """NEW: Demonstrate music fade out"""
        self.audio_system.fade_out_music(self.volume_transition_duration)
        self.add_audio_event(f"Music fade out ({self.volume_transition_duration:.1f}s)")
    
    def smooth_volume_test(self):
        """NEW: Test smooth volume transitions on music"""
        if self.audio_system.music_channel.is_playing():
            current_volume = self.audio_system.music_channel.volume
            new_volume = 0.3 if current_volume > 0.5 else 0.8
            
            self.audio_system.music_channel.set_volume(new_volume, self.volume_transition_duration)
            self.add_audio_event(f"Music volume: {current_volume:.1f} → {new_volume:.1f}")
        else:
            self.add_audio_event("No music playing")
    
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
        y = 250
        
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
        
        # Update event display (you could add a dedicated UI element for this)
        print(f"Audio Event: {event_text}")
    
    def handle_key_press(self, key):
        """Enhanced keyboard input with new features"""
        if key == pygame.K_ESCAPE:
            self.engine.set_scene("MainMenu")
        elif key == pygame.K_1:
            self.play_channel_sound(1, 1.0, 1.0)
        elif key == pygame.K_2:
            self.play_channel_sound(2, 0.7, 1.0)
        elif key == pygame.K_3:
            self.dynamic_speed_change(1)  # NEW: Dynamic speed change
        elif key == pygame.K_4:
            self.smooth_volume_change(2)  # NEW: Smooth volume change
        elif key == pygame.K_5:
            self.fade_in_music_demo()     # NEW: Fade in music
        elif key == pygame.K_6:
            self.fade_out_music_demo()    # NEW: Fade out music
        elif key == pygame.K_p:
            self.pause_music()            # NEW: Pause music
        elif key == pygame.K_r:
            self.resume_music()           # NEW: Resume music
    
    def update(self, dt):
        """Update scene logic with enhanced audio information"""
        # Update visual effects
        for effect in self.visual_effects[:]:
            effect['timer'] += dt
            if effect['timer'] >= effect['max_time']:
                self.visual_effects.remove(effect)
        
        # NEW: Update real-time audio information
        self.update_audio_info()
        
        # Update channel monitor
        channel_info = self.audio_system.get_channel_info()
        active_count = channel_info['busy_channels']
        self.channel_monitor.set_text(f"Channels: {active_count}/{len(self.audio_system.channels)} active")
        
        # Show details of active channels
        details = []
        for chan_info in channel_info['channels']:
            if chan_info['playing'] or chan_info['paused']:
                status = "PLAYING" if chan_info['playing'] else "PAUSED"
                state_info = f"({chan_info['state']})" if chan_info['state'] != 'playing' else ""
                details.append(f"Ch{chan_info['id']}: {status}{state_info} vol:{chan_info['volume']:.1f} spd:{chan_info['speed']:.1f}x")
        
        if details:
            self.channel_details.set_text(" | ".join(details[:3]))  # Show first 3
        else:
            self.channel_details.set_text("No active channels")
    
    def update_audio_info(self):
        """NEW: Update real-time audio information display"""
        # Music state
        if self.audio_system.music_channel.is_playing():
            music_state = "Playing"
            color = (100, 255, 100)  # Green
        elif self.audio_system.music_channel.is_paused():
            music_state = "Paused"
            color = (255, 255, 100)  # Yellow
        else:
            music_state = "Stopped"
            color = (255, 100, 100)  # Red
        
        self.music_state_label.set_text(f"Music: {music_state}")
        self.music_state_label.color = color
        
        # Music speed and volume
        self.music_speed_label.set_text(f"Speed: {self.audio_system.music_channel.speed:.1f}x")
        self.music_volume_label.set_text(f"Volume: {self.audio_system.music_channel.volume:.1f}")
        
        # Active channels count
        active_count = sum(1 for channel in self.audio_system.channels if channel.is_playing() or channel.is_paused())
        self.active_channels_label.set_text(f"Active Channels: {active_count}")
        
        # Music position (if playing)
        if self.audio_system.music_channel.is_playing():
            position = self.audio_system.get_current_music_position()
            self.music_position_label.set_text(f"Position: {position:.2f}s / {self.audio_info['music_duration']:.2f}s")
        else:
            self.music_position_label.set_text("Position: 0.00s")
    
    def render(self, renderer):
        """Render the scene with enhanced visualizations"""
        # Draw background
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw channel visualizations
        self.draw_channel_visualizations(renderer)
        
        # NEW: Draw transition progress bars
        self.draw_transition_progress(renderer)
        
        # Draw UI elements
        for element in self.ui_elements:
            element.render(renderer)
    
    def draw_channel_visualizations(self, renderer):
        """Draw channel activity visualization with enhanced info"""
        # Draw channel grid
        for i in range(16):
            x = 700 + (i % 4) * 60
            y = 270 + (i // 4) * 60
            
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
                    # Green for playing, different shades for different states
                    if channel.state == AudioState.SPEED_CHANGING:
                        fill_color = (100, 255, 200)  # Cyan for speed changing
                    elif channel.state == AudioState.VOLUME_CHANGING:
                        fill_color = (255, 200, 100)  # Orange for volume changing
                    else:
                        fill_color = (50, 200, 50)    # Green for normal playing
                    
                    renderer.draw_rect(x + 5, y + 35, 40, 10, fill_color)
                elif channel.is_paused():
                    # Yellow for paused
                    renderer.draw_rect(x + 5, y + 35, 40, 10, (200, 200, 50))
    
    def draw_transition_progress(self, renderer):
        """NEW: Draw visual indicators for ongoing transitions"""
        # Check music channel for transitions
        music_channel = self.audio_system.music_channel
        
        if music_channel.state == AudioState.VOLUME_CHANGING:
            # Draw volume transition indicator
            progress = abs(music_channel.volume - music_channel.target_volume)
            max_progress = abs(music_channel.target_volume - (music_channel.volume - progress))
            if max_progress > 0:
                ratio = progress / max_progress
                x, y = 700, 300
                width = 200
                renderer.draw_rect(x, y, width * ratio, 10, (255, 200, 100))
                renderer.draw_rect(x, y, width, 10, (100, 100, 100), fill=False)
                
                font = pygame.font.Font(None, 16)
                text = font.render("Volume Transition", True, (255, 255, 255))
                renderer.draw_surface(text, x, y - 20)
        
        if music_channel.state == AudioState.SPEED_CHANGING:
            # Draw speed transition indicator
            progress = abs(music_channel.speed - music_channel.target_speed)
            max_progress = abs(music_channel.target_speed - (music_channel.speed - progress))
            if max_progress > 0:
                ratio = progress / max_progress
                x, y = 700, 330
                width = 200
                renderer.draw_rect(x, y, width * ratio, 10, (100, 255, 200))
                renderer.draw_rect(x, y, width, 10, (100, 100, 100), fill=False)
                
                font = pygame.font.Font(None, 16)
                text = font.render("Speed Transition", True, (255, 255, 255))
                renderer.draw_surface(text, x, y - 20)

# Main function
def main():
    """Main entry point"""
    engine = LunaEngine("LunaEngine - Enhanced Audio Demo", 1024, 720, False)
    engine.fps = 60
    
    # Initialize enhanced audio system
    engine.audio_system = AudioSystem(num_channels=16)
    
    # Add scenes
    engine.add_scene("AudioDemo", AudioDemoScene)
    engine.set_scene("AudioDemo")
    
    print("=== Enhanced Audio System Demo ===")
    print("NEW FEATURES:")
    print("- Dynamic speed changes without stopping playback")
    print("- Smooth volume and speed transitions")
    print("- Audio duration information")
    print("- Real-time audio state monitoring")
    print("- Enhanced pause/resume system")
    print("\nKEYBOARD CONTROLS:")
    print("1-2: Play sounds on channels")
    print("3: Dynamic speed change (Channel 1)")
    print("4: Smooth volume change (Channel 2)")
    print("5: Fade in music")
    print("6: Fade out music")
    print("P: Pause music")
    print("R: Resume music")
    print("ESC: Back to menu")
    
    engine.run()

if __name__ == "__main__":
    main()