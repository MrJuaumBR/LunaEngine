"""
Enhanced Audio Demo - Testing OpenAL Audio with Dynamic Control and Smooth Transitions

LOCATION: examples/audio_demo.py

Updated to use the new OpenAL audio system with:
- OpenAL backend with pygame fallback
- Smooth volume and pitch transitions
- Stereo panning support
- Optimized resource management
- Tab-based interface
- Audio visualizer integration
"""

import sys
import os
import time
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine
from lunaengine.core.audio import AudioSystem, AudioChannel, AudioEvent
from lunaengine.ui.elements import *
from lunaengine.ui.tween import Tween, EasingType, AnimationHandler
import pygame
import numpy as np

class AudioDemoScene(Scene):
    """
    Enhanced audio system demonstration with OpenAL support and tab interface.
    """
    
    def on_enter(self, previous_scene=None):
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
        
        # Sound names (not paths)
        self.explosion_sound_name = "explosion"
        self.music_sound_name = "music"
        
        # Transition controls
        self.volume_transition_duration = 1.0
        self.speed_transition_duration = 1.5
        
        # Visual feedback
        self.visual_effects = []
        self.audio_events_log = []
        
        # Audio information
        self.audio_info = {
            'music_duration': 0.0,
            'sound_duration': 0.0,
            'current_position': 0.0
        }
        
        # Animation handler
        self.animation_handler = AnimationHandler(engine)
        self.animations = {}
        
        # Visualizer state
        self.visualizer_style = 'bars'
        self.visualizer_sensitivity = 1.5
        self.visualizer_smoothing = 0.7
        self.visualizer_source = 'music'  # 'music' or 'sfx'
        
        # Setup audio system
        self.setup_audio_system()
        
        # Setup UI with tabs
        self.setup_ui()
        
        # Load audio files
        self.load_audio_files()
        
        # Register key events
        @engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
    
    def setup_audio_system(self):
        """Setup audio system with OpenAL support."""
        try:
            # Initialize audio system
            self.audio_system = AudioSystem(num_channels=16)
            print(f"Audio system initialized: OpenAL={self.audio_system.use_openal}")
        except Exception as e:
            print(f"Failed to initialize audio system: {e}")
            # Fallback: create basic system
            self.audio_system = None
    
    def load_audio_files(self):
        """Load audio files for testing."""
        if not self.audio_system:
            print("Audio system not available")
            return
        
        try:
            # Load explosion sound effect
            explosion_path = "./examples/explosion.wav"
            if os.path.exists(explosion_path):
                self.audio_system.load_sound(self.explosion_sound_name, explosion_path)
                sound_info = self.audio_system.get_sound_info(self.explosion_sound_name)
                if sound_info:
                    self.audio_info['sound_duration'] = sound_info.duration
                    print(f"Loaded explosion.wav successfully (duration: {self.audio_info['sound_duration']:.2f}s)")
            else:
                print(f"Warning: explosion.wav not found at {explosion_path}")
                self.create_placeholder_sounds()
            
            # Load music file
            music_path = "./examples/music.mp3"
            if os.path.exists(music_path):
                self.audio_system.load_sound(self.music_sound_name, music_path)
                sound_info = self.audio_system.get_sound_info(self.music_sound_name)
                if sound_info:
                    self.audio_info['music_duration'] = sound_info.duration
                    print(f"Loaded music.mp3 successfully (duration: {self.audio_info['music_duration']:.2f}s)")
            else:
                print(f"Warning: music.mp3 not found at {music_path}")
                # Create placeholder music
                self.create_placeholder_music()
                self.audio_info['music_duration'] = 120.0
                
        except Exception as e:
            print(f"Error loading audio files: {e}")
            self.create_placeholder_sounds()

    def create_placeholder_music(self):
        """Create placeholder music if file is not available."""
        try:
            # Try to use explosion sound as placeholder for music too
            if os.path.exists("./examples/explosion.wav"):
                self.audio_system.load_sound(self.music_sound_name, "./examples/explosion.wav")
                sound_info = self.audio_system.get_sound_info(self.music_sound_name)
                if sound_info:
                    self.audio_info['music_duration'] = sound_info.duration
                print("Using explosion sound as placeholder music")
            else:
                # Create a simple tone as placeholder
                self.create_sine_wave_tone(self.music_sound_name, duration=2.0, frequency=440.0)
                sound_info = self.audio_system.get_sound_info(self.music_sound_name)
                if sound_info:
                    self.audio_info['music_duration'] = sound_info.duration
                print("Created sine wave tone as placeholder music")
        except Exception as e:
            print(f"Error creating placeholder music: {e}")

    def create_sine_wave_tone(self, name: str, duration: float = 1.0, frequency: float = 440.0):
        """Create a simple sine wave tone as placeholder audio."""
        try:
            import numpy as np
            
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            # Generate sine wave
            tone = np.sin(2 * np.pi * frequency * t)
            
            # Convert to 16-bit PCM
            tone = (tone * 32767).astype(np.int16)
            
            # Create stereo audio (2 channels)
            stereo_tone = np.column_stack((tone, tone))
            
            # Create a temporary WAV file
            import tempfile
            import wave
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                with wave.open(tmp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(2)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(stereo_tone.tobytes())
                
                # Load the temporary file
                self.audio_system.load_sound(name, tmp_file.name)
                
                # Clean up temporary file
                import os
                os.unlink(tmp_file.name)
                
        except Exception as e:
            print(f"Failed to create sine wave tone: {e}")
    
    def create_placeholder_sounds(self):
        """Create placeholder sounds if files are not available."""
        try:
            # Create a simple sound programmatically
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
            self.explosion_sound = sound
            self.audio_info['sound_duration'] = duration
            
            print("Created placeholder explosion sound")
            
        except Exception as e:
            print(f"Error creating placeholder sounds: {e}")
    
    def setup_ui(self):
        """Setup comprehensive audio controls UI with tabs."""
        # Title and basic info
        title = TextLabel(512, 20, "OpenAL Audio Demo", 48, root_point=(0.5, 0))
        self.ui_elements.append(title)
        
        subtitle_text = "OpenAL Backend" if self.audio_system and self.audio_system.use_openal else "Pygame Fallback"
        subtitle = TextLabel(512, 65, f"{subtitle_text} - Smooth Transitions", 20, root_point=(0.5, 0))
        self.ui_elements.append(subtitle)
        
        # Create main tabs container
        self.main_tabs = Tabination(25, 100, 980, 600, 20)
        
        # Add tabs
        self.main_tabs.add_tab('Sound Effects')
        self.setup_sound_effects_tab()
        
        self.main_tabs.add_tab('Music')
        self.setup_music_tab()
        
        self.main_tabs.add_tab('Transitions')
        self.setup_transitions_tab()
        
        self.main_tabs.add_tab('Visualizer')
        self.setup_visualizer_tab()
        
        self.main_tabs.add_tab('Monitor')
        self.setup_monitor_tab()
        
        # Add tabs to UI
        self.ui_elements.append(self.main_tabs)
        
        # Add corner radius to tabs
        self.main_tabs.set_corner_radius((10, 10, 10, 10))
        
        # FPS display
        self.fps_display = TextLabel(self.engine.width - 10, 20, "FPS: --", 16, (100, 255, 100), root_point=(1, 0))
        self.ui_elements.append(self.fps_display)
    
    def setup_sound_effects_tab(self):
        """Setup sound effects controls tab."""
        # Tab title
        self.main_tabs.add_to_tab('Sound Effects', TextLabel(10, 10, "Multi-Channel Sound Effects", 28, (255, 255, 0)))
        
        # Sound duration info
        duration_label = TextLabel(10, 45, f"Sound Duration: {self.audio_info['sound_duration']:.2f}s", 16, 
                                 (150, 170, 190))
        self.main_tabs.add_to_tab('Sound Effects', duration_label)
        
        # Channel 1 controls
        self.main_tabs.add_to_tab('Sound Effects', TextLabel(10, 75, "Channel 1:", 20))
        
        ch1_play = Button(110, 70, 120, 30, "Play", 18)
        ch1_play.set_on_click(lambda: self.play_channel_sound(1, 1.0, 1.0, 0.0))
        self.main_tabs.add_to_tab('Sound Effects', ch1_play)
        
        ch1_slow = Button(240, 70, 120, 30, "Slow (0.5x)", 18)
        ch1_slow.set_on_click(lambda: self.play_channel_sound(1, 1.0, 0.5, 0.0))
        self.main_tabs.add_to_tab('Sound Effects', ch1_slow)
        
        ch1_fast = Button(370, 70, 120, 30, "Fast (2.0x)", 18)
        ch1_fast.set_on_click(lambda: self.play_channel_sound(1, 1.0, 2.0, 0.0))
        self.main_tabs.add_to_tab('Sound Effects', ch1_fast)
        
        # Channel 2 controls
        self.main_tabs.add_to_tab('Sound Effects', TextLabel(10, 115, "Channel 2:", 20))
        
        ch2_play = Button(110, 110, 120, 30, "Play", 18)
        ch2_play.set_on_click(lambda: self.play_channel_sound(2, 0.7, 1.0, 0.0))
        self.main_tabs.add_to_tab('Sound Effects', ch2_play)
        
        ch2_quiet = Button(240, 110, 120, 30, "Quiet (0.3x)", 18)
        ch2_quiet.set_on_click(lambda: self.play_channel_sound(2, 0.3, 1.0, 0.0))
        self.main_tabs.add_to_tab('Sound Effects', ch2_quiet)
        
        ch2_loop = Button(370, 110, 120, 30, "Loop", 18)
        ch2_loop.set_on_click(lambda: self.play_channel_sound(2, 0.7, 1.0, 0.0, True))
        self.main_tabs.add_to_tab('Sound Effects', ch2_loop)
        
        # Pan controls
        pan_label = TextLabel(10, 155, "Pan Controls:", 20)
        self.main_tabs.add_to_tab('Sound Effects', pan_label)
        
        pan_left = Button(130, 150, 80, 30, "Left", 16)
        pan_left.set_on_click(lambda: self.play_channel_sound(3, 0.8, 1.0, -1.0))
        self.main_tabs.add_to_tab('Sound Effects', pan_left)
        
        pan_center = Button(230, 150, 80, 30, "Center", 16)
        pan_center.set_on_click(lambda: self.play_channel_sound(3, 0.8, 1.0, 0.0))
        self.main_tabs.add_to_tab('Sound Effects', pan_center)
        
        pan_right = Button(330, 150, 80, 30, "Right", 16)
        pan_right.set_on_click(lambda: self.play_channel_sound(3, 0.8, 1.0, 1.0))
        self.main_tabs.add_to_tab('Sound Effects', pan_right)
        
        # Dynamic controls
        self.main_tabs.add_to_tab('Sound Effects', TextLabel(10, 195, "Dynamic Control & Transitions", 20))
        
        # Dynamic control for channel 1
        ch1_dynamic = Button(10, 220, 140, 30, "Speed Change", 16)
        ch1_dynamic.set_on_click(lambda: self.dynamic_speed_change(1))
        self.main_tabs.add_to_tab('Sound Effects', ch1_dynamic)
        
        # Smooth volume change for channel 2
        ch2_smooth_vol = Button(160, 220, 140, 30, "Volume Fade", 16)
        ch2_smooth_vol.set_on_click(lambda: self.smooth_volume_change(2))
        self.main_tabs.add_to_tab('Sound Effects', ch2_smooth_vol)
        
        # Stop all channels
        stop_all = Button(310, 220, 140, 30, "Stop All SFX", 16)
        stop_all.set_on_click(self.stop_all_channels)
        self.main_tabs.add_to_tab('Sound Effects', stop_all)
        
        # Channel status display
        self.main_tabs.add_to_tab('Sound Effects', TextLabel(10, 270, "Channel Status:", 20, (255, 200, 100)))
        
        self.channel_status = TextLabel(10, 300, "No active channels", 16, (150, 170, 190))
        self.main_tabs.add_to_tab('Sound Effects', self.channel_status)
    
    def setup_music_tab(self):
        """Setup music controls tab."""
        # Tab title
        self.main_tabs.add_to_tab('Music', TextLabel(10, 10, "Music Controls", 28, (255, 255, 0)))
        
        # Music duration info
        music_duration_label = TextLabel(10, 45, f"Music Duration: {self.audio_info['music_duration']:.2f}s", 16, 
                                       (150, 170, 190))
        self.main_tabs.add_to_tab('Music', music_duration_label)
        
        # Current position display
        self.music_position_label = TextLabel(250, 45, "Position: 0.00s", 16, (150, 170, 190))
        self.main_tabs.add_to_tab('Music', self.music_position_label)
        
        # Music speed controls
        self.main_tabs.add_to_tab('Music', TextLabel(10, 75, "Music Speed:", 20))
        
        self.music_speed_slider = Slider(130, 70, 200, 20, 0.5, 2.0, 1.0)
        self.music_speed_slider.on_value_changed = self.on_music_speed_changed
        self.main_tabs.add_to_tab('Music', self.music_speed_slider)
        
        self.music_speed_value = TextLabel(340, 75, "1.0x", 20)
        self.main_tabs.add_to_tab('Music', self.music_speed_value)
        
        # Music volume controls
        self.main_tabs.add_to_tab('Music', TextLabel(10, 105, "Music Volume:", 20))
        
        self.music_volume_slider = Slider(130, 100, 200, 20, 0.0, 1.0, 0.8)
        self.music_volume_slider.on_value_changed = self.on_music_volume_changed
        self.main_tabs.add_to_tab('Music', self.music_volume_slider)
        
        self.music_volume_value = TextLabel(340, 105, "0.8", 20)
        self.main_tabs.add_to_tab('Music', self.music_volume_value)
        
        # Music control buttons
        play_music = Button(10, 140, 100, 30, "Play", 18)
        play_music.set_on_click(self.play_music)
        self.main_tabs.add_to_tab('Music', play_music)
        
        pause_music = Button(120, 140, 100, 30, "Pause", 18)
        pause_music.set_on_click(self.pause_music)
        self.main_tabs.add_to_tab('Music', pause_music)
        
        resume_music = Button(230, 140, 100, 30, "Resume", 18)
        resume_music.set_on_click(self.resume_music)
        self.main_tabs.add_to_tab('Music', resume_music)
        
        stop_music = Button(340, 140, 100, 30, "Stop", 18)
        stop_music.set_on_click(self.stop_music)
        self.main_tabs.add_to_tab('Music', stop_music)
        
        # Apply speed with transition
        apply_speed_smooth = Button(450, 140, 150, 30, "Smooth Speed", 16)
        apply_speed_smooth.set_on_click(self.apply_music_speed_smooth)
        self.main_tabs.add_to_tab('Music', apply_speed_smooth)
        
        # Music status
        self.main_tabs.add_to_tab('Music', TextLabel(10, 190, "Music Status:", 20, (255, 200, 100)))
        
        self.music_status_label = TextLabel(10, 220, "Stopped", 18, (255, 100, 100))
        self.main_tabs.add_to_tab('Music', self.music_status_label)
    
    def setup_transitions_tab(self):
        """Setup transition controls tab."""
        # Tab title
        self.main_tabs.add_to_tab('Transitions', TextLabel(10, 10, "Smooth Transition Controls", 28, (255, 255, 0)))
        
        # Volume transition controls
        self.main_tabs.add_to_tab('Transitions', TextLabel(10, 50, "Volume Transition:", 18))
        
        self.vol_transition_slider = Slider(170, 45, 150, 20, 0.1, 3.0, self.volume_transition_duration)
        self.vol_transition_slider.on_value_changed = self.on_volume_transition_changed
        self.main_tabs.add_to_tab('Transitions', self.vol_transition_slider)
        
        self.vol_transition_value = TextLabel(330, 50, f"{self.volume_transition_duration:.1f}s", 18)
        self.main_tabs.add_to_tab('Transitions', self.vol_transition_value)
        
        # Speed transition controls
        self.main_tabs.add_to_tab('Transitions', TextLabel(10, 85, "Speed Transition:", 18))
        
        self.speed_transition_slider = Slider(170, 80, 150, 20, 0.1, 3.0, self.speed_transition_duration)
        self.speed_transition_slider.on_value_changed = self.on_speed_transition_changed
        self.main_tabs.add_to_tab('Transitions', self.speed_transition_slider)
        
        self.speed_transition_value = TextLabel(330, 85, f"{self.speed_transition_duration:.1f}s", 18)
        self.main_tabs.add_to_tab('Transitions', self.speed_transition_value)
        
        # Transition demo buttons
        fade_in_music = Button(10, 120, 140, 30, "Fade In Music", 16)
        fade_in_music.set_on_click(self.fade_in_music_demo)
        self.main_tabs.add_to_tab('Transitions', fade_in_music)
        
        fade_out_music = Button(160, 120, 140, 30, "Fade Out Music", 16)
        fade_out_music.set_on_click(self.fade_out_music_demo)
        self.main_tabs.add_to_tab('Transitions', fade_out_music)
        
        smooth_volume_test = Button(310, 120, 160, 30, "Volume Test", 16)
        smooth_volume_test.set_on_click(self.smooth_volume_test)
        self.main_tabs.add_to_tab('Transitions', smooth_volume_test)
        
        # Advanced transitions
        self.main_tabs.add_to_tab('Transitions', TextLabel(10, 170, "Advanced Transitions:", 20, (255, 200, 100)))
        
        # Crossfade example
        crossfade_btn = Button(10, 200, 150, 30, "Crossfade Demo", 16)
        crossfade_btn.set_on_click(self.crossfade_demo)
        self.main_tabs.add_to_tab('Transitions', crossfade_btn)
        
        # Speed ramp example
        speed_ramp_btn = Button(170, 200, 150, 30, "Speed Ramp Demo", 16)
        speed_ramp_btn.set_on_click(self.speed_ramp_demo)
        self.main_tabs.add_to_tab('Transitions', speed_ramp_btn)
        
        # Transition log
        self.main_tabs.add_to_tab('Transitions', TextLabel(10, 250, "Transition Log:", 20, (200, 200, 255)))
        
        self.transition_log = TextLabel(10, 280, "No transitions yet", 14, (150, 170, 190))
        self.main_tabs.add_to_tab('Transitions', self.transition_log)
    
    def setup_visualizer_tab(self):
        """Setup audio visualizer tab."""
        # Tab title
        self.main_tabs.add_to_tab('Visualizer', TextLabel(10, 10, "Audio Visualizer", 28, (255, 255, 0)))
        
        # Create visualizer container frame
        visualizer_frame = UiFrame(10, 50, 450, 200)
        visualizer_frame.set_background_color((30, 30, 40))
        visualizer_frame.set_border((60, 60, 80), 2)
        self.main_tabs.add_to_tab('Visualizer', visualizer_frame)
        
        # Create the audio visualizer
        self.audio_visualizer = AudioVisualizer(
            x=15, 
            y=55, 
            width=440, 
            height=190,
            style=self.visualizer_style,
            source=None,  # Will be set dynamically
            color_gradient=[
                (100, 0, 200),    # Purple
                (0, 150, 255),    # Blue
                (0, 255, 200),    # Cyan
                (100, 255, 100)   # Green
            ]
        )
        
        # Set initial source based on what's playing
        self.update_visualizer_source()
        self.main_tabs.add_to_tab('Visualizer', self.audio_visualizer)
        
        # Controls section
        controls_frame = UiFrame(470, 50, 280, 200)
        controls_frame.set_background_color((40, 40, 50, 200))
        controls_frame.set_border((80, 80, 100), 1)
        self.main_tabs.add_to_tab('Visualizer', controls_frame)
        
        # Visualizer style selection
        self.main_tabs.add_to_tab('Visualizer', TextLabel(475, 55, "Visualization Style:", 16, (200, 200, 255)))
        
        self.style_dropdown = Dropdown(475, 80, 150, 30, 
                                      ['Bars', 'Waveform', 'Circle', 'Particles', 'Spectrum'])
        self.style_dropdown.set_on_selection_changed(lambda i, v: self.change_visualizer_style(v.lower()))
        self.style_dropdown.set_simple_tooltip("Change visualization style")
        self.main_tabs.add_to_tab('Visualizer', self.style_dropdown)
        
        # Audio source selection
        self.main_tabs.add_to_tab('Visualizer', TextLabel(475, 120, "Audio Source:", 16, (200, 200, 255)))
        
        self.source_dropdown = Dropdown(475, 145, 150, 30, 
                                       ['Music', 'Sound Effects', 'Mixed'])
        self.source_dropdown.set_on_selection_changed(lambda i, v: self.change_visualizer_source(v))
        self.source_dropdown.set_simple_tooltip("Select which audio to visualize")
        self.main_tabs.add_to_tab('Visualizer', self.source_dropdown)
        
        # Sensitivity control
        self.main_tabs.add_to_tab('Visualizer', TextLabel(475, 185, "Sensitivity:", 16, (200, 200, 255)))
        
        self.sensitivity_slider = Slider(560, 185, 120, 20, 0.5, 3.0, self.visualizer_sensitivity)
        self.sensitivity_slider.on_value_changed = lambda v: self.change_visualizer_sensitivity(v)
        self.main_tabs.add_to_tab('Visualizer', self.sensitivity_slider)
        
        self.sensitivity_value = TextLabel(690, 190, f"{self.visualizer_sensitivity:.1f}", 14)
        self.main_tabs.add_to_tab('Visualizer', self.sensitivity_value)
        
        # Smoothing control
        self.main_tabs.add_to_tab('Visualizer', TextLabel(475, 215, "Smoothing:", 16, (200, 200, 255)))
        
        self.smoothing_slider = Slider(560, 215, 120, 20, 0.1, 0.9, self.visualizer_smoothing)
        self.smoothing_slider.on_value_changed = lambda v: self.change_visualizer_smoothing(v)
        self.main_tabs.add_to_tab('Visualizer', self.smoothing_slider)
        
        self.smoothing_value = TextLabel(690, 220, f"{self.visualizer_smoothing:.1f}", 14)
        self.main_tabs.add_to_tab('Visualizer', self.smoothing_value)
        
        # Preset buttons
        preset_label = TextLabel(10, 260, "Preset Themes:", 18, (255, 200, 100))
        self.main_tabs.add_to_tab('Visualizer', preset_label)
        
        # Color gradient presets
        fire_btn = Button(10, 290, 100, 30, "Fire", 14)
        fire_btn.set_on_click(lambda: self.apply_color_preset([
            (50, 10, 10),    # Dark red
            (200, 50, 0),    # Orange-red
            (255, 150, 0),   # Orange
            (255, 255, 100)  # Yellow
        ]))
        fire_btn.set_simple_tooltip("Fire color theme")
        self.main_tabs.add_to_tab('Visualizer', fire_btn)
        
        ocean_btn = Button(120, 290, 100, 30, "Ocean", 14)
        ocean_btn.set_on_click(lambda: self.apply_color_preset([
            (0, 20, 40),     # Deep blue
            (0, 80, 120),    # Medium blue
            (0, 180, 200),   # Cyan-blue
            (100, 220, 255)  # Light cyan
        ]))
        ocean_btn.set_simple_tooltip("Ocean color theme")
        self.main_tabs.add_to_tab('Visualizer', ocean_btn)
        
        neon_btn = Button(230, 290, 100, 30, "Neon", 14)
        neon_btn.set_on_click(lambda: self.apply_color_preset([
            (255, 0, 200),   # Pink
            (200, 0, 255),   # Purple
            (0, 200, 255),   # Cyan
            (0, 255, 150)    # Green
        ]))
        neon_btn.set_simple_tooltip("Neon color theme")
        self.main_tabs.add_to_tab('Visualizer', neon_btn)
        
        # Visualizer info
        info_text = "The visualizer responds to audio in real-time.\nTry different styles and sources!"
        info_label = TextLabel(10, 330, info_text, 14, (150, 200, 255))
        self.main_tabs.add_to_tab('Visualizer', info_label)
    
    def setup_monitor_tab(self):
        """Setup audio monitoring tab."""
        # Tab title
        self.main_tabs.add_to_tab('Monitor', TextLabel(10, 10, "Audio System Monitor", 28, (255, 255, 0)))
        
        # System info
        backend_text = f"Backend: {'OpenAL' if self.audio_system and self.audio_system.use_openal else 'Pygame'}"
        self.main_tabs.add_to_tab('Monitor', TextLabel(10, 50, backend_text, 16, (150, 170, 190)))
        
        # Active channels display
        self.active_channels_label = TextLabel(10, 80, "Active Channels: 0", 16, (200, 200, 200))
        self.main_tabs.add_to_tab('Monitor', self.active_channels_label)
        
        # Channel grid visualization
        self.main_tabs.add_to_tab('Monitor', TextLabel(10, 110, "Channel Grid (0-15):", 20, (255, 200, 100)))
        
        # Create channel grid
        self.channel_grid_elements = []
        for i in range(16):
            x = 10 + (i % 8) * 60
            y = 140 + (i // 8) * 60
            
            # Channel box background
            channel_bg = UiFrame(x, y, 50, 50)
            channel_bg.set_background_color((40, 40, 50))
            channel_bg.set_border((100, 100, 120), 1)
            self.channel_grid_elements.append(channel_bg)
            self.main_tabs.add_to_tab('Monitor', channel_bg)
            
            # Channel number
            channel_num = TextLabel(x + 20, y + 15, str(i), 20, (200, 200, 200))
            self.channel_grid_elements.append(channel_num)
            self.main_tabs.add_to_tab('Monitor', channel_num)
            
            # Status indicator (will be updated)
            status_indicator = UiFrame(x + 10, y + 35, 30, 10)
            status_indicator.set_background_color((60, 60, 80))
            self.channel_grid_elements.append(status_indicator)
            self.main_tabs.add_to_tab('Monitor', status_indicator)
        
        # Pan visualization
        self.main_tabs.add_to_tab('Monitor', TextLabel(10, 320, "Stereo Pan Visualization:", 20, (255, 200, 100)))
        
        # Pan visualization background
        pan_bg = UiFrame(10, 350, 300, 40)
        pan_bg.set_background_color((40, 40, 50))
        self.main_tabs.add_to_tab('Monitor', pan_bg)
        
        # Center line
        center_line = UiFrame(160, 350, 2, 40)
        center_line.set_background_color((100, 100, 120))
        self.main_tabs.add_to_tab('Monitor', center_line)
        
        # Labels
        left_label = TextLabel(20, 360, "L", 16, (200, 200, 200))
        self.main_tabs.add_to_tab('Monitor', left_label)
        
        right_label = TextLabel(290, 360, "R", 16, (200, 200, 200))
        self.main_tabs.add_to_tab('Monitor', right_label)
        
        # Audio events log
        self.main_tabs.add_to_tab('Monitor', TextLabel(350, 50, "Audio Events Log:", 20, (255, 200, 100)))
        
        self.event_log_labels = []
        for i in range(6):
            event_label = TextLabel(350, 80 + i * 25, "", 14, (200, 200, 200))
            self.event_log_labels.append(event_label)
            self.main_tabs.add_to_tab('Monitor', event_label)
        
        # Performance info
        self.main_tabs.add_to_tab('Monitor', TextLabel(350, 250, "Performance Info:", 20, (255, 200, 100)))
        
        self.performance_label = TextLabel(350, 280, "CPU Usage: --\nMemory: --", 14, (200, 200, 200))
        self.main_tabs.add_to_tab('Monitor', self.performance_label)
    
    def change_visualizer_style(self, style: str):
        """Change visualizer style."""
        self.visualizer_style = style
        if hasattr(self, 'audio_visualizer'):
            self.audio_visualizer.set_style(style)
        self.add_audio_event(f"Visualizer style: {style}")
    
    def change_visualizer_source(self, source: str):
        """Change visualizer audio source."""
        self.visualizer_source = source.lower()
        self.update_visualizer_source()
        self.add_audio_event(f"Visualizer source: {source}")
    
    def change_visualizer_sensitivity(self, sensitivity: float):
        """Change visualizer sensitivity."""
        self.visualizer_sensitivity = sensitivity
        self.sensitivity_value.set_text(f"{sensitivity:.1f}")
        if hasattr(self, 'audio_visualizer'):
            self.audio_visualizer.set_sensitivity(sensitivity)
    
    def change_visualizer_smoothing(self, smoothing: float):
        """Change visualizer smoothing."""
        self.visualizer_smoothing = smoothing
        self.smoothing_value.set_text(f"{smoothing:.1f}")
        if hasattr(self, 'audio_visualizer'):
            self.audio_visualizer.set_smoothing(smoothing)
    
    def apply_color_preset(self, gradient):
        """Apply a color gradient preset to the visualizer."""
        if hasattr(self, 'audio_visualizer'):
            self.audio_visualizer.set_color_gradient(gradient)
        self.add_audio_event(f"Applied color preset")
    
    def update_visualizer_source(self):
        """Update the visualizer's audio source based on current state."""
        if not hasattr(self, 'audio_visualizer'):
            return
        
        if self.visualizer_source == 'music':
            # Use music channel (channel 0)
            if self.audio_system and self.audio_system.channels and len(self.audio_system.channels) > 0:
                music_channel = self.audio_system.channels[0]
                if hasattr(music_channel, 'is_playing') and music_channel.is_playing():
                    self.audio_visualizer.set_source(music_channel)
                else:
                    self.audio_visualizer.set_source(None)
        elif self.visualizer_source == 'sound effects':
            # Use the first active sound effect channel
            if self.active_channels:
                first_channel = next(iter(self.active_channels.values()))
                self.audio_visualizer.set_source(first_channel)
            else:
                self.audio_visualizer.set_source(None)
        elif self.visualizer_source == 'mixed':
            # For mixed, we'd ideally combine audio from multiple sources
            # For simplicity, use music if available, otherwise SFX
            if self.audio_system and self.audio_system.channels and len(self.audio_system.channels) > 0:
                music_channel = self.audio_system.channels[0]
                if hasattr(music_channel, 'is_playing') and music_channel.is_playing():
                    self.audio_visualizer.set_source(music_channel)
                elif self.active_channels:
                    first_channel = next(iter(self.active_channels.values()))
                    self.audio_visualizer.set_source(first_channel)
                else:
                    self.audio_visualizer.set_source(None)
            else:
                self.audio_visualizer.set_source(None)
    
    def play_channel_sound(self, channel_num: int, volume: float, speed: float, pan: float, loop: bool = False):
        """Play sound on specific channel with custom settings."""
        if not self.audio_system:
            self.add_audio_event("Audio system not available")
            return
        
        channel_key = f"explosion_{channel_num}"
        
        # Stop existing sound on this channel if any
        if channel_key in self.active_channels:
            self.active_channels[channel_key].stop()
            del self.active_channels[channel_key]
        
        # Play new sound - note: we subtract 1 because channels are 0-indexed
        channel = self.audio_system.play(
            sound_name=self.explosion_sound_name,
            channel=channel_num - 1,  # Convert to 0-indexed
            volume=volume,
            pitch=speed,
            pan=pan,
            loop=loop
        )
        
        if channel:
            self.active_channels[channel_key] = channel
            self.add_audio_event(f"Channel {channel_num}: vol={volume}, speed={speed}x, pan={pan}")
            
            # Update visualizer if using SFX source
            if self.visualizer_source == 'sound effects' or self.visualizer_source == 'mixed':
                self.update_visualizer_source()
            
            # Update channel status
            self.update_channel_status()
        else:
            self.add_audio_event(f"Failed to play on channel {channel_num}")
    
    def play_music(self):
        """Play background music."""
        if not self.audio_system:
            self.add_audio_event("Audio system not available")
            return
        
        volume = self.music_volume_slider.value
        speed = self.music_speed_slider.value
        
        # Play music - uses channel 0 automatically
        channel = self.audio_system.play_music(
            sound_name=self.music_sound_name,
            volume=volume,
            pitch=speed,
            loop=True
        )
        
        if channel:
            self.add_audio_event(f"Music started (vol: {volume:.1f}, speed: {speed:.1f}x)")
            self.music_status_label.set_text("Playing")
            self.music_status_label.color = (100, 255, 100)
            
            # Update visualizer if using music source
            if self.visualizer_source == 'music' or self.visualizer_source == 'mixed':
                self.update_visualizer_source()
        else:
            self.add_audio_event("Failed to play music")
    
    def pause_music(self):
        """Pause music."""
        if self.audio_system:
            # Get music channel (channel 0)
            if self.audio_system.channels and len(self.audio_system.channels) > 0:
                music_channel = self.audio_system.channels[0]
                if music_channel.is_playing():
                    music_channel.pause()
                    self.add_audio_event("Music paused")
                    self.music_status_label.set_text("Paused")
                    self.music_status_label.color = (255, 255, 100)
    
    def resume_music(self):
        """Resume paused music."""
        if self.audio_system:
            # Get music channel (channel 0)
            if self.audio_system.channels and len(self.audio_system.channels) > 0:
                music_channel = self.audio_system.channels[0]
                if music_channel.is_paused():
                    music_channel.resume()
                    self.add_audio_event("Music resumed")
                    self.music_status_label.set_text("Playing")
                    self.music_status_label.color = (100, 255, 100)
    
    def stop_music(self):
        """Stop music."""
        if self.audio_system:
            # Get music channel (channel 0)
            if self.audio_system.channels and len(self.audio_system.channels) > 0:
                music_channel = self.audio_system.channels[0]
                music_channel.stop()
                self.add_audio_event("Music stopped")
                self.music_status_label.set_text("Stopped")
                self.music_status_label.color = (255, 100, 100)
                
                # Update visualizer
                self.update_visualizer_source()
    
    def dynamic_speed_change(self, channel_num: int):
        """Change speed dynamically with smooth transition."""
        channel_key = f"explosion_{channel_num}"
        if channel_key in self.active_channels:
            channel = self.active_channels[channel_key]
            
            # Cycle through different speeds
            current_pitch = 1.0
            if hasattr(channel, 'pitch'):
                current_pitch = channel.pitch
            
            if current_pitch >= 2.0:
                new_speed = 0.5
            elif current_pitch >= 1.0:
                new_speed = 2.0
            else:
                new_speed = 1.0
            
            # Apply smooth speed transition
            channel.set_pitch(new_speed, self.speed_transition_duration)
            self.add_audio_event(f"Speed transition: {current_pitch:.1f}x → {new_speed:.1f}x")
            self.add_transition_log(f"Ch{channel_num}: Speed {current_pitch:.1f}→{new_speed:.1f}x")
    
    def smooth_volume_change(self, channel_num: int):
        """Demonstrate smooth volume transition."""
        channel_key = f"explosion_{channel_num}"
        if channel_key in self.active_channels and self.active_channels[channel_key].is_playing():
            channel = self.active_channels[channel_key]
            current_volume = channel.volume if hasattr(channel, 'volume') else 1.0
            
            # Cycle through different volumes
            if current_volume >= 0.8:
                new_volume = 0.2
            elif current_volume >= 0.5:
                new_volume = 0.8
            else:
                new_volume = 0.5
            
            # Apply smooth volume transition
            channel.set_volume(new_volume, self.volume_transition_duration)
            self.add_audio_event(f"Ch{channel_num} volume: {current_volume:.1f} → {new_volume:.1f}")
            self.add_transition_log(f"Ch{channel_num}: Volume {current_volume:.1f}→{new_volume:.1f}")
        else:
            self.add_audio_event(f"Channel {channel_num} not active")
    
    def on_music_speed_changed(self, value):
        """Handle music speed slider change."""
        self.playback_speed = value
        self.music_speed_value.set_text(f"{value:.1f}x")
    
    def on_music_volume_changed(self, value):
        """Handle music volume slider change."""
        self.music_volume = value
        self.music_volume_value.set_text(f"{value:.1f}")
        
        # Apply volume change immediately if music is playing on channel 0
        if self.audio_system and self.audio_system.channels and len(self.audio_system.channels) > 0:
            music_channel = self.audio_system.channels[0]
            if music_channel.is_playing() or music_channel.is_paused():
                music_channel.set_volume(value)
    
    def apply_music_speed_smooth(self):
        """Apply speed change with smooth transition."""
        if self.audio_system and self.audio_system.channels and len(self.audio_system.channels) > 0:
            music_channel = self.audio_system.channels[0]
            if music_channel.is_playing():
                new_speed = self.music_speed_slider.value
                music_channel.set_pitch(new_speed, self.speed_transition_duration)
                self.add_audio_event(f"Music speed: {new_speed:.1f}x ({self.speed_transition_duration:.1f}s)")
                self.add_transition_log(f"Music: Speed → {new_speed:.1f}x")
            else:
                self.add_audio_event("No music playing")
    
    def on_volume_transition_changed(self, value):
        """Handle volume transition duration change."""
        self.volume_transition_duration = value
        self.vol_transition_value.set_text(f"{value:.1f}s")
    
    def on_speed_transition_changed(self, value):
        """Handle speed transition duration change."""
        self.speed_transition_duration = value
        self.speed_transition_value.set_text(f"{value:.1f}s")
    
    def fade_in_music_demo(self):
        """Demonstrate music fade in."""
        if not self.audio_system:
            self.add_audio_event("Audio system not available")
            return
        
        volume = self.music_volume_slider.value
        speed = self.music_speed_slider.value
        
        # Play music with fade in
        channel = self.audio_system.play_music(
            sound_name=self.music_sound_name,
            volume=0.0,  # Start silent
            pitch=speed,
            loop=True,
            fade_in=self.volume_transition_duration
        )
        
        if channel:
            # Set target volume after starting (with fade)
            channel.set_volume(volume, self.volume_transition_duration)
            self.add_audio_event(f"Music fade in ({self.volume_transition_duration:.1f}s)")
            self.add_transition_log(f"Music: Fade in {self.volume_transition_duration:.1f}s")
            self.music_status_label.set_text("Playing (Fade in)")
            self.music_status_label.color = (100, 255, 100)
            
            # Update visualizer
            self.update_visualizer_source()
        else:
            self.add_audio_event("Failed to fade in music")
    
    def fade_out_music_demo(self):
        """Demonstrate music fade out."""
        if self.audio_system and self.audio_system.channels and len(self.audio_system.channels) > 0:
            music_channel = self.audio_system.channels[0]
            if music_channel.is_playing() or music_channel.is_paused():
                # Fade out and stop
                music_channel.set_volume(0.0, self.volume_transition_duration)
                # Schedule stop after fade
                import threading
                threading.Timer(self.volume_transition_duration, music_channel.stop).start()
                self.add_audio_event(f"Music fade out ({self.volume_transition_duration:.1f}s)")
                self.add_transition_log(f"Music: Fade out {self.volume_transition_duration:.1f}s")
                self.music_status_label.set_text("Fading out")
                self.music_status_label.color = (255, 200, 100)
            else:
                self.add_audio_event("No music playing")
    
    def smooth_volume_test(self):
        """Test smooth volume transitions on music."""
        if self.audio_system and self.audio_system.channels and len(self.audio_system.channels) > 0:
            music_channel = self.audio_system.channels[0]
            if music_channel.is_playing():
                current_volume = self.music_volume
                new_volume = 0.3 if current_volume > 0.5 else 0.8
                
                music_channel.set_volume(new_volume, self.volume_transition_duration)
                self.music_volume = new_volume
                self.music_volume_slider.value = new_volume
                self.music_volume_value.set_text(f"{new_volume:.1f}")
                
                self.add_audio_event(f"Music volume: {current_volume:.1f} → {new_volume:.1f}")
                self.add_transition_log(f"Music: Volume {current_volume:.1f}→{new_volume:.1f}")
            else:
                self.add_audio_event("No music playing")
    
    def crossfade_demo(self):
        """Demonstrate crossfade between two sounds."""
        self.add_transition_log("Crossfade demo: Not implemented yet")
        self.add_audio_event("Crossfade demo requires additional audio files")
    
    def speed_ramp_demo(self):
        """Demonstrate speed ramping."""
        if self.audio_system and self.audio_system.channels and len(self.audio_system.channels) > 0:
            music_channel = self.audio_system.channels[0]
            if music_channel.is_playing():
                # Ramp speed up and down
                original_speed = music_channel.pitch
                music_channel.set_pitch(2.0, 1.0)
                # Schedule ramp back down
                import threading
                threading.Timer(1.5, lambda: music_channel.set_pitch(original_speed, 1.0)).start()
                self.add_transition_log(f"Speed ramp: {original_speed:.1f}→2.0→{original_speed:.1f}x")
            else:
                self.add_transition_log("No music playing for speed ramp")
    
    def stop_all_channels(self):
        """Stop all sound effect channels."""
        for channel_key in list(self.active_channels.keys()):
            if channel_key.startswith('explosion_'):
                self.active_channels[channel_key].stop()
                del self.active_channels[channel_key]
        
        if self.audio_system:
            self.audio_system.stop_all()
        self.add_audio_event("All channels stopped")
        self.update_channel_status()
        
        # Update visualizer
        self.update_visualizer_source()
    
    def add_audio_event(self, event_text):
        """Add event to log."""
        self.audio_events_log.append(event_text)
        if len(self.audio_events_log) > 6:
            self.audio_events_log.pop(0)
        
        # Update event log display
        for i, label in enumerate(self.event_log_labels):
            if i < len(self.audio_events_log):
                label.set_text(self.audio_events_log[i])
            else:
                label.set_text("")
        
        # Print to console
        print(f"Audio Event: {event_text}")
    
    def add_transition_log(self, event_text):
        """Add transition event to log."""
        current_text = self.transition_log.text
        if current_text == "No transitions yet":
            new_text = event_text
        else:
            new_text = current_text + "\n" + event_text
        
        # Keep only last 3 lines
        lines = new_text.split('\n')
        if len(lines) > 3:
            new_text = '\n'.join(lines[-3:])
        
        self.transition_log.set_text(new_text)
    
    def update_channel_status(self):
        """Update channel status display."""
        active_channels = len(self.active_channels)
        if active_channels == 0:
            self.channel_status.set_text("No active channels")
            self.channel_status.color = (150, 150, 150)
        else:
            self.channel_status.set_text(f"{active_channels} active channel(s)")
            self.channel_status.color = (100, 255, 100)
    
    def handle_key_press(self, key):
        """Enhanced keyboard input with new features."""
        if key == pygame.K_ESCAPE:
            self.engine.set_scene("MainMenu")
        elif key == pygame.K_1:
            self.play_channel_sound(1, 1.0, 1.0, 0.0)
        elif key == pygame.K_2:
            self.play_channel_sound(2, 0.7, 1.0, 0.0)
        elif key == pygame.K_3:
            self.dynamic_speed_change(1)
        elif key == pygame.K_4:
            self.smooth_volume_change(2)
        elif key == pygame.K_5:
            self.fade_in_music_demo()
        elif key == pygame.K_6:
            self.fade_out_music_demo()
        elif key == pygame.K_p:
            self.pause_music()
        elif key == pygame.K_r:
            self.resume_music()
        elif key == pygame.K_LEFT:
            self.play_channel_sound(3, 0.8, 1.0, -1.0)
        elif key == pygame.K_RIGHT:
            self.play_channel_sound(3, 0.8, 1.0, 1.0)
        elif key == pygame.K_UP:
            self.play_channel_sound(3, 0.8, 1.0, 0.0)
        elif key == pygame.K_TAB:
            # Cycle through tabs (if we have a reference to main_tabs)
            if hasattr(self, 'main_tabs'):
                current_index = self.main_tabs.current_tab_index
                next_index = (current_index + 1) % len(self.main_tabs.tabs)
                self.main_tabs.switch_tab(next_index)
        elif key == pygame.K_v:
            # Switch to visualizer tab
            if hasattr(self, 'main_tabs'):
                self.main_tabs.switch_tab(3)  # Visualizer tab is index 3
        elif key == pygame.K_c:
            # Cycle through visualizer styles
            styles = ['bars', 'waveform', 'circle', 'particles', 'spectrum']
            current_idx = styles.index(self.visualizer_style) if self.visualizer_style in styles else 0
            next_idx = (current_idx + 1) % len(styles)
            self.change_visualizer_style(styles[next_idx])
    
    def update(self, dt):
        """Update scene logic with enhanced audio information."""
        # Update visual effects
        for effect in self.visual_effects[:]:
            effect['timer'] += dt
            if effect['timer'] >= effect['max_time']:
                self.visual_effects.remove(effect)
        
        # Update audio system
        if self.audio_system:
            self.audio_system.update()
        
        # Update visualizer source if needed
        if hasattr(self, 'audio_visualizer'):
            # Update the visualizer's source periodically
            current_time = time.time()
            if not hasattr(self, '_last_source_update'):
                self._last_source_update = 0
            
            if current_time - self._last_source_update > 0.5:  # Update every 0.5 seconds
                self.update_visualizer_source()
                self._last_source_update = current_time
        
        # Update real-time audio information
        self.update_audio_info()
        
        # Update FPS display
        fps_stats = self.engine.get_fps_stats()
        self.fps_display.set_text(f"FPS: {fps_stats['current_fps']:.1f}")
        
        # Update performance info (simulated)
        import random
        cpu_usage = random.randint(5, 25)
        memory_usage = random.randint(100, 300)
        self.performance_label.set_text(f"CPU Usage: {cpu_usage}%\nMemory: {memory_usage}MB")
    
    def update_audio_info(self):
        """Update real-time audio information display."""
        if not self.audio_system:
            return
        
        # Update active channels count
        active_count = 0
        if self.audio_system.channels:
            active_count = sum(1 for channel in self.audio_system.channels 
                            if channel.is_playing() or channel.is_paused())
        
        self.active_channels_label.set_text(f"Active Channels: {active_count}")
        
        # Update channel grid
        for i, channel in enumerate(self.audio_system.channels[:16]):
            if i * 3 + 2 < len(self.channel_grid_elements):
                status_indicator = self.channel_grid_elements[i * 3 + 2]
                if channel.is_playing():
                    status_indicator.set_background_color((50, 200, 50))
                elif hasattr(channel, 'is_paused') and channel.is_paused():
                    status_indicator.set_background_color((200, 200, 50))
                else:
                    status_indicator.set_background_color((60, 60, 80))
        
        # Music state - get channel 0 for music
        if self.audio_system.channels and len(self.audio_system.channels) > 0:
            music_channel = self.audio_system.channels[0]
            if music_channel.is_playing():
                # Music position (if playing)
                position = music_channel.get_playback_position()
                # Get duration from sound info
                sound_info = self.audio_system.get_sound_info(self.music_sound_name)
                if sound_info:
                    duration = sound_info.duration
                    self.music_position_label.set_text(f"Position: {position:.2f}s / {duration:.2f}s")
                else:
                    self.music_position_label.set_text(f"Position: {position:.2f}s")
            else:
                self.music_position_label.set_text("Position: 0.00s")
        else:
            self.music_position_label.set_text("Position: 0.00s")
    
    def render(self, renderer):
        """Render the scene with enhanced visualizations."""
        # Draw background
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw header background
        renderer.draw_rect(0, 0, 1024, 90, current_theme.background2)
        
        # Draw UI elements
        for element in self.ui_elements:
            element.render(renderer)

# Main function
def main():
    """Main entry point."""
    engine = LunaEngine("LunaEngine - OpenAL Audio Demo", 1024, 720, False)
    engine.fps = 60
    
    # Audio system is now initialized in the scene
    print("=== OpenAL Audio System Demo ===")
    print("KEY FEATURES:")
    print("- OpenAL backend with pygame fallback")
    print("- Smooth volume and pitch transitions")
    print("- Stereo panning (left/right)")
    print("- Real-time audio state monitoring")
    print("- Multi-channel sound effects")
    print("- Tab-based interface")
    print("- Audio visualizer with 5 styles")
    print("\nKEYBOARD CONTROLS:")
    print("1-2: Play sounds on channels 1-2")
    print("3: Dynamic speed change (Channel 1)")
    print("4: Smooth volume change (Channel 2)")
    print("5: Fade in music")
    print("6: Fade out music")
    print("P: Pause music")
    print("R: Resume music")
    print("← → ↑: Test panning (left, right, center)")
    print("TAB: Cycle through tabs")
    print("V: Jump to Visualizer tab")
    print("C: Cycle visualizer styles")
    print("ESC: Back to menu")
    
    # Add and start scene
    engine.add_scene("AudioDemo", AudioDemoScene)
    engine.set_scene("AudioDemo")
    
    engine.run()

if __name__ == "__main__":
    main()