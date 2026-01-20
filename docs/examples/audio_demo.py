"""
Enhanced Audio Demo - Testing OpenAL Audio with Dynamic Control and Smooth Transitions

LOCATION: examples/audio_demo.py

Updated to use the new OpenAL audio system with:
- OpenAL backend with pygame fallback
- Smooth volume and pitch transitions
- Stereo panning support
- Optimized resource management
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine
from lunaengine.core.audio import AudioSystem, AudioChannel, AudioEvent  # Nova importação
from lunaengine.ui.elements import *
import pygame
import numpy as np

class AudioDemoScene(Scene):
    """
    Enhanced audio system demonstration with OpenAL support.
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
        
        # Setup audio system
        self.setup_audio_system()
        
        # Setup UI
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
            # Inicializar o sistema de áudio
            self.audio_system = AudioSystem(num_channels=16)
            print(f"Audio system initialized: OpenAL={self.audio_system.use_openal}")
        except Exception as e:
            print(f"Failed to initialize audio system: {e}")
            # Fallback: criar um sistema básico
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
            
            # Create visual effect
            self.create_channel_effect(channel_num, volume, speed, pan)
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
        else:
            self.add_audio_event("Failed to play music")
    
    def get_sound_duration(self, filepath):
        """Get approximate duration of a sound file."""
        try:
            # Tentar carregar o som para obter duração
            if hasattr(pygame.mixer.Sound, 'get_length'):
                sound = pygame.mixer.Sound(filepath)
                return sound.get_length()
        except:
            pass
        
        # Fallback: estimativa baseada em tamanho de arquivo
        try:
            size = os.path.getsize(filepath)
            # Estimativa grosseira: 1MB ≈ 6 segundos de áudio stereo 44.1kHz
            return size / (1024 * 1024) * 6
        except:
            return 1.0  # Default
    
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
            # Criar um som simples programaticamente
            sample_rate = 44100
            duration = 1.0  # seconds
            frames = int(duration * sample_rate)
            
            # Gerar uma onda quadrada simples
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
        """Setup comprehensive audio controls UI."""
        # Title and basic controls
        title = TextLabel(512, 30, "OpenAL Audio Demo", 48, root_point=(0.5, 0))
        self.ui_elements.append(title)
        
        subtitle_text = "OpenAL Backend" if self.audio_system and self.audio_system.use_openal else "Pygame Fallback"
        subtitle = TextLabel(512, 80, f"{subtitle_text} - Smooth Transitions", 24, root_point=(0.5, 0))
        self.ui_elements.append(subtitle)
        
        # Multi-channel explosion controls
        self.setup_multi_channel_ui()
        
        # Music controls with enhanced features
        self.setup_music_ui()
        
        # Transition controls section
        self.setup_transition_controls()
        
        # Audio information display
        self.setup_audio_info_display()
        
        # Channel monitor
        self.setup_channel_monitor()
    
    def setup_multi_channel_ui(self):
        """Setup multi-channel sound effect controls."""
        self.ui_elements.append(TextLabel(100, 130, "Multi-Channel Sound Effects", 28, root_point=(0, 0)))
        
        # Sound duration info
        duration_label = TextLabel(100, 160, f"Sound Duration: {self.audio_info['sound_duration']:.2f}s", 16, 
                                 (150, 170, 190), root_point=(0, 0))
        self.ui_elements.append(duration_label)
        
        # Channel 1 controls
        self.ui_elements.append(TextLabel(100, 190, "Channel 1:", 20, root_point=(0, 0)))
        
        ch1_play = Button(200, 190, 120, 30, "Play", 18, root_point=(0, 0))
        ch1_play.set_on_click(lambda: self.play_channel_sound(1, 1.0, 1.0, 0.0))
        self.ui_elements.append(ch1_play)
        
        ch1_slow = Button(330, 190, 120, 30, "Slow (0.5x)", 18, root_point=(0, 0))
        ch1_slow.set_on_click(lambda: self.play_channel_sound(1, 1.0, 0.5, 0.0))
        self.ui_elements.append(ch1_slow)
        
        ch1_fast = Button(460, 190, 120, 30, "Fast (2.0x)", 18, root_point=(0, 0))
        ch1_fast.set_on_click(lambda: self.play_channel_sound(1, 1.0, 2.0, 0.0))
        self.ui_elements.append(ch1_fast)
        
        # Channel 2 controls
        self.ui_elements.append(TextLabel(100, 230, "Channel 2:", 20, root_point=(0, 0)))
        
        ch2_play = Button(200, 230, 120, 30, "Play", 18, root_point=(0, 0))
        ch2_play.set_on_click(lambda: self.play_channel_sound(2, 0.7, 1.0, 0.0))
        self.ui_elements.append(ch2_play)
        
        ch2_quiet = Button(330, 230, 120, 30, "Quiet (0.3x)", 18, root_point=(0, 0))
        ch2_quiet.set_on_click(lambda: self.play_channel_sound(2, 0.3, 1.0, 0.0))
        self.ui_elements.append(ch2_quiet)
        
        ch2_loop = Button(460, 230, 120, 30, "Loop", 18, root_point=(0, 0))
        ch2_loop.set_on_click(lambda: self.play_channel_sound(2, 0.7, 1.0, 0.0, True))
        self.ui_elements.append(ch2_loop)
        
        # Pan controls
        pan_label = TextLabel(100, 270, "Pan Controls:", 20, root_point=(0, 0))
        self.ui_elements.append(pan_label)
        
        pan_left = Button(220, 270, 80, 30, "Left", 16, root_point=(0, 0))
        pan_left.set_on_click(lambda: self.play_channel_sound(3, 0.8, 1.0, -1.0))
        self.ui_elements.append(pan_left)
        
        pan_center = Button(330, 270, 80, 30, "Center", 16, root_point=(0, 0))
        pan_center.set_on_click(lambda: self.play_channel_sound(3, 0.8, 1.0, 0.0))
        self.ui_elements.append(pan_center)
        
        pan_right = Button(440, 270, 80, 30, "Right", 16, root_point=(0, 0))
        pan_right.set_on_click(lambda: self.play_channel_sound(3, 0.8, 1.0, 1.0))
        self.ui_elements.append(pan_right)
        
        self.add_ui_element(TextLabel(100,  310, "Dynamic Control & Transitions", 20, root_point=(0, 0)))
        
        # Dynamic control for channel 1
        ch1_dynamic = Button(200, 335, 140, 30, "Speed Change", 16, root_point=(0, 0))
        ch1_dynamic.set_on_click(lambda: self.dynamic_speed_change(1))
        self.ui_elements.append(ch1_dynamic)
        
        # Smooth volume change for channel 2
        ch2_smooth_vol = Button(360, 335, 140, 30, "Volume Fade", 16, root_point=(0, 0))
        ch2_smooth_vol.set_on_click(lambda: self.smooth_volume_change(2))
        self.ui_elements.append(ch2_smooth_vol)
        
        # Stop all channels
        stop_all = Button(520, 335, 140, 30, "Stop All SFX", 16, root_point=(0, 0))
        stop_all.set_on_click(self.stop_all_channels)
        self.ui_elements.append(stop_all)
    
    def setup_music_ui(self):
        """Setup music controls with enhanced features."""
        self.ui_elements.append(TextLabel(100, 375, "Music Controls", 28, root_point=(0, 0)))
        
        # Music duration info
        music_duration_label = TextLabel(100, 410, f"Music Duration: {self.audio_info['music_duration']:.2f}s", 16, 
                                       (150, 170, 190), root_point=(0, 0))
        self.ui_elements.append(music_duration_label)
        
        # Current position display
        self.music_position_label = TextLabel(300, 410, "Position: 0.00s", 16, (150, 170, 190), root_point=(0, 0))
        self.ui_elements.append(self.music_position_label)
        
        # Music speed controls
        self.ui_elements.append(TextLabel(100, 430, "Music Speed:", 20, root_point=(0, 0)))
        
        self.music_speed_slider = Slider(220, 430, 200, 20, 0.5, 2.0, 1.0, root_point=(0, 0))
        self.music_speed_slider.on_value_changed = self.on_music_speed_changed
        self.ui_elements.append(self.music_speed_slider)
        
        self.music_speed_value = TextLabel(430, 430, "1.0x", 20, root_point=(0, 0.5))
        self.ui_elements.append(self.music_speed_value)
        
        # Music volume controls
        self.ui_elements.append(TextLabel(100, 460, "Music Volume:", 20, root_point=(0, 0)))
        
        self.music_volume_slider = Slider(220, 460, 200, 20, 0.0, 1.0, 0.8, root_point=(0, 0))
        self.music_volume_slider.on_value_changed = self.on_music_volume_changed
        self.ui_elements.append(self.music_volume_slider)
        
        self.music_volume_value = TextLabel(430, 460, "0.8", 20, root_point=(0, 0.5))
        self.ui_elements.append(self.music_volume_value)
        
        # Music controls
        play_music = Button(100, 495, 100, 30, "Play", 18, root_point=(0, 0))
        play_music.set_on_click(self.play_music)
        self.ui_elements.append(play_music)
        
        pause_music = Button(210, 495, 100, 30, "Pause", 18, root_point=(0, 0))
        pause_music.set_on_click(self.pause_music)
        self.ui_elements.append(pause_music)
        
        resume_music = Button(320, 495, 100, 30, "Resume", 18, root_point=(0, 0))
        resume_music.set_on_click(self.resume_music)
        self.ui_elements.append(resume_music)
        
        stop_music = Button(430, 495, 100, 30, "Stop", 18, root_point=(0, 0))
        stop_music.set_on_click(self.stop_music)
        self.ui_elements.append(stop_music)
        
        # Apply speed with transition
        apply_speed_smooth = Button(540, 495, 150, 30, "Smooth Speed", 16, root_point=(0, 0))
        apply_speed_smooth.set_on_click(self.apply_music_speed_smooth)
        self.ui_elements.append(apply_speed_smooth)
    
    def setup_transition_controls(self):
        """Setup controls for smooth transitions."""
        self.ui_elements.append(TextLabel(100, 530, "Smooth Transition Controls", 28, root_point=(0, 0)))
        
        # Volume transition controls
        self.ui_elements.append(TextLabel(100, 570, "Volume Transition:", 18, root_point=(0, 0)))
        
        self.vol_transition_slider = Slider(260, 570, 150, 20, 0.1, 3.0, self.volume_transition_duration, root_point=(0, 0))
        self.vol_transition_slider.on_value_changed = self.on_volume_transition_changed
        self.ui_elements.append(self.vol_transition_slider)
        
        self.vol_transition_value = TextLabel(420, 575, f"{self.volume_transition_duration:.1f}s", 18, root_point=(0, 0.5))
        self.ui_elements.append(self.vol_transition_value)
        
        # Speed transition controls
        self.ui_elements.append(TextLabel(100, 605, "Speed Transition:", 18, root_point=(0, 0)))
        
        self.speed_transition_slider = Slider(260, 605, 150, 20, 0.1, 3.0, self.speed_transition_duration, root_point=(0, 0))
        self.speed_transition_slider.on_value_changed = self.on_speed_transition_changed
        self.ui_elements.append(self.speed_transition_slider)
        
        self.speed_transition_value = TextLabel(420, 610, f"{self.speed_transition_duration:.1f}s", 18, root_point=(0, 0.5))
        self.ui_elements.append(self.speed_transition_value)
        
        # Transition demo buttons
        fade_in_music = Button(100, 645, 140, 30, "Fade In Music", 16, root_point=(0, 0))
        fade_in_music.set_on_click(self.fade_in_music_demo)
        self.ui_elements.append(fade_in_music)
        
        fade_out_music = Button(250, 645, 140, 30, "Fade Out Music", 16, root_point=(0, 0))
        fade_out_music.set_on_click(self.fade_out_music_demo)
        self.ui_elements.append(fade_out_music)
        
        smooth_volume_test = Button(400, 645, 160, 30, "Volume Test", 16, root_point=(0, 0))
        smooth_volume_test.set_on_click(self.smooth_volume_test)
        self.ui_elements.append(smooth_volume_test)
    
    def setup_audio_info_display(self):
        """Setup real-time audio information display."""
        self.ui_elements.append(TextLabel(700, 130, "Real-time Audio Info", 24, root_point=(0, 0)))
        
        self.ui_elements.append(TextLabel(700, 160, f"Backend: {'OpenAL' if self.audio_system and self.audio_system.use_openal else 'Pygame'}", 
                                           16, (150, 170, 190), root_point=(0, 0)))
        
        self.music_state_label = TextLabel(700, 180, "Music: Stopped", 16, (200, 200, 200), root_point=(0, 0))
        self.ui_elements.append(self.music_state_label)
        
        self.music_speed_label = TextLabel(700, 200, "Speed: 1.0x", 16, (200, 200, 200), root_point=(0, 0))
        self.ui_elements.append(self.music_speed_label)
        
        self.music_volume_label = TextLabel(700, 220, "Volume: 0.0", 16, (200, 200, 200), root_point=(0, 0))
        self.ui_elements.append(self.music_volume_label)
        
        self.active_channels_label = TextLabel(700, 240, "Active Channels: 0", 16, (200, 200, 200), root_point=(0, 0))
        self.ui_elements.append(self.active_channels_label)
    
    def setup_channel_monitor(self):
        """Setup channel monitoring display."""
        self.ui_elements.append(TextLabel(700, 570, "Channel Monitor", 24, root_point=(0, 0)))
        
        self.channel_monitor = TextLabel(700, 600, "Channels: 0/16 active", 18, (150, 170, 190), root_point=(0, 0))
        self.ui_elements.append(self.channel_monitor)
        
        self.channel_details = TextLabel(700, 620, "No active channels", 14, (150, 170, 190), root_point=(0, 0))
        self.ui_elements.append(self.channel_details)
    
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
        else:
            self.add_audio_event(f"Channel {channel_num} not active")
    
    def pause_music(self):
        """Pause music."""
        if self.audio_system:
            # Get music channel (channel 0)
            if self.audio_system.channels and len(self.audio_system.channels) > 0:
                music_channel = self.audio_system.channels[0]
                if music_channel.is_playing():
                    music_channel.pause()
                    self.add_audio_event("Music paused")
    
    def resume_music(self):
        """Resume paused music."""
        if self.audio_system:
            # Get music channel (channel 0)
            if self.audio_system.channels and len(self.audio_system.channels) > 0:
                music_channel = self.audio_system.channels[0]
                if music_channel.is_paused():
                    music_channel.resume()
                    self.add_audio_event("Music resumed")
    
    def stop_music(self):
        """Stop music."""
        if self.audio_system:
            # Get music channel (channel 0)
            if self.audio_system.channels and len(self.audio_system.channels) > 0:
                music_channel = self.audio_system.channels[0]
                music_channel.stop()
                self.add_audio_event("Music stopped")
    
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
            else:
                self.add_audio_event("No music playing")
    
    def stop_all_channels(self):
        """Stop all sound effect channels."""
        for channel_key in list(self.active_channels.keys()):
            if channel_key.startswith('explosion_'):
                self.active_channels[channel_key].stop()
                del self.active_channels[channel_key]
        
        if self.audio_system:
            self.audio_system.stop_all_sounds()
        self.add_audio_event("All channels stopped")
    
    def create_channel_effect(self, channel_num: int, volume: float, speed: float, pan: float):
        """Create visual effect for channel playback."""
        x = 700 + (channel_num - 1) * 60
        y = 280
        
        self.visual_effects.append({
            'type': 'channel',
            'channel': channel_num,
            'x': x,
            'y': y,
            'volume': volume,
            'speed': speed,
            'pan': pan,
            'timer': 0,
            'max_time': 2.0
        })
    
    def add_audio_event(self, event_text):
        """Add event to log."""
        self.audio_events_log.append(event_text)
        if len(self.audio_events_log) > 4:
            self.audio_events_log.pop(0)
        
        # Print to console
        print(f"Audio Event: {event_text}")
    
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
        
        # Update real-time audio information
        self.update_audio_info()
        
        # Update channel monitor
        self.update_channel_monitor()
    
    def update_audio_info(self):
        """Update real-time audio information display."""
        if not self.audio_system:
            return
        
        # Music state - get channel 0 for music
        if self.audio_system.channels and len(self.audio_system.channels) > 0:
            music_channel = self.audio_system.channels[0]
            if music_channel.is_playing():
                music_state = "Playing"
                color = (100, 255, 100)  # Green
            elif music_channel.is_paused():
                music_state = "Paused"
                color = (255, 255, 100)  # Yellow
            else:
                music_state = "Stopped"
                color = (255, 100, 100)  # Red
            
            self.music_state_label.set_text(f"Music: {music_state}")
            self.music_state_label.color = color
            
            # Music speed and volume
            self.music_speed_label.set_text(f"Speed: {music_channel.pitch:.1f}x")
            self.music_volume_label.set_text(f"Volume: {music_channel.volume:.1f}")
            
            # Music position (if playing)
            if music_channel.is_playing():
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
            self.music_state_label.set_text("Music: Stopped")
            self.music_state_label.color = (255, 100, 100)
            self.music_speed_label.set_text("Speed: 1.0x")
            self.music_volume_label.set_text("Volume: 0.0")
            self.music_position_label.set_text("Position: 0.00s")
        
        # Active channels count
        active_count = 0
        if self.audio_system.channels:
            active_count = sum(1 for channel in self.audio_system.channels 
                            if channel.is_playing() or channel.is_paused())
        
        self.active_channels_label.set_text(f"Active Channels: {active_count}")
    
    def update_channel_monitor(self):
        """Update channel monitor display."""
        if not self.audio_system:
            return
        
        # Count active channels
        active_count = 0
        channel_details = []
        
        for i, channel in enumerate(self.audio_system.channels[:8]):  # Mostrar só os primeiros 8
            if channel.is_playing() or (hasattr(channel, 'is_paused') and channel.is_paused()):
                active_count += 1
                status = "PLAY" if channel.is_playing() else "PAUS"
                volume = getattr(channel, 'volume', 0.0)
                pitch = getattr(channel, 'pitch', 1.0)
                channel_details.append(f"Ch{i}:{status} v:{volume:.1f} p:{pitch:.1f}")
        
        self.channel_monitor.set_text(f"Channels: {active_count}/{len(self.audio_system.channels)} active")
        
        if channel_details:
            self.channel_details.set_text(", ".join(channel_details[:4]))  # Show first 4
        else:
            self.channel_details.set_text("No active channels")
    
    def render(self, renderer):
        """Render the scene with enhanced visualizations."""
        # Draw background
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw channel visualizations
        self.draw_channel_visualizations(renderer)
        
        # Draw pan visualization
        self.draw_pan_visualization(renderer)
        
        # Draw UI elements
        for element in self.ui_elements:
            element.render(renderer)
        
        # Draw visual effects
        self.draw_visual_effects(renderer)
    
    def draw_channel_visualizations(self, renderer:OpenGLRenderer):
        """Draw channel activity visualization."""
        # Draw channel grid
        for i in range(16):
            x = 700 + (i % 4) * 60
            y = 320 + (i // 4) * 60
            
            # Channel box
            color = (60, 60, 80)
            renderer.draw_rect(x, y, 50, 50, color)
            renderer.draw_rect(x, y, 50, 50, (100, 100, 120), fill=False)
            
            # Channel number
            renderer.draw_text(str(i), x+20, y+15, (200, 200, 200), FontManager.get_font(None, 20))
            
            # Activity indicator
            if self.audio_system and i < len(self.audio_system.channels):
                channel = self.audio_system.channels[i]
                if channel.is_playing():
                    # Green for playing
                    renderer.draw_rect(x + 5, y + 35, 40, 10, (50, 200, 50))
                elif hasattr(channel, 'is_paused') and channel.is_paused():
                    # Yellow for paused
                    renderer.draw_rect(x + 5, y + 35, 40, 10, (200, 200, 50))
    
    def draw_pan_visualization(self, renderer:OpenGLRenderer):
        """Draw stereo pan visualization."""
        x, y = 700, 270
        width, height = 200, 40
        
        # Background
        renderer.draw_rect(x, y, width, height, (40, 40, 50))
        
        # Center line
        renderer.draw_rect(x + width/2 - 1, y, 2, height, (100, 100, 120))
        
        # Labels
        renderer.draw_text("L", x + 10, y + height//2 - 8, (200, 200, 200), FontManager.get_font(None, 16))
        renderer.draw_text("R", x + width - 20, y + height//2 - 8, (200, 200, 200), FontManager.get_font(None, 16))
        
        # Active pan indicators
        for effect in self.visual_effects:
            if effect['type'] == 'channel' and effect['timer'] < effect['max_time']:
                pan = effect['pan']
                pan_x = x + width/2 + (pan * width/2)
                pan_y = y + height//2
                radius = 8
                
                # Color based on channel
                colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]
                color_idx = (effect['channel'] - 1) % len(colors)
                
                renderer.draw_circle(pan_x, pan_y, radius, colors[color_idx])
    
    def draw_visual_effects(self, renderer):
        """Draw visual effects for channel playback."""
        for effect in self.visual_effects:
            if effect['type'] == 'channel':
                x, y = effect['x'], effect['y']
                progress = effect['timer'] / effect['max_time']
                
                # Draw expanding circle
                radius = 20 + progress * 30
                alpha = int(255 * (1 - progress))
                
                # Color based on speed
                speed = effect['speed']
                if speed > 1.5:
                    color = (255, 100, 100, alpha)  # Red for fast
                elif speed < 0.7:
                    color = (100, 100, 255, alpha)  # Blue for slow
                else:
                    color = (100, 255, 100, alpha)  # Green for normal
                
                # Draw the effect
                renderer.draw_circle(x, y, int(radius), color, fill=False)
                
                # Draw channel number
                font = pygame.font.Font(None, 24)
                text = font.render(str(effect['channel']), True, (255, 255, 255))
                renderer.draw_surface(text, x - 6, y - 12)

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
    print("\nKEYBOARD CONTROLS:")
    print("1-2: Play sounds on channels 1-2")
    print("3: Dynamic speed change (Channel 1)")
    print("4: Smooth volume change (Channel 2)")
    print("5: Fade in music")
    print("6: Fade out music")
    print("P: Pause music")
    print("R: Resume music")
    print("← → ↑: Test panning (left, right, center)")
    print("ESC: Back to menu")
    
    # Add and start scene
    engine.add_scene("AudioDemo", AudioDemoScene)
    engine.set_scene("AudioDemo")
    
    engine.run()

if __name__ == "__main__":
    main()