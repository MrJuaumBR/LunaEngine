"""
Audio System for LunaEngine - OpenAL backend with Pygame fallback

This module provides a unified audio interface with the following features:
- OpenAL backend with Pygame fallback for compatibility
- Sound loading and management by name
- Automatic channel allocation or explicit channel selection
- Smooth volume/pitch transitions
- Stereo panning support
- Resource pooling and management

Author: [Your Name]
Version: 1.0.0
"""

import pygame
import threading
import time
import os
import math
import weakref
from typing import Dict, List, Optional, Callable, Union, Tuple, Any
from enum import Enum
import json

# Try to import OpenAL
try:
    from ..backend.openal import (
        OpenALAudioSystem, OpenALSource, OpenALAudioEvent,
        initialize_audio, cleanup_audio, get_audio_system,
        OPENAL_AVAILABLE
    )
    USE_OPENAL = OPENAL_AVAILABLE
except (ImportError, ModuleNotFoundError):
    USE_OPENAL = False
    print("OpenAL audio disabled, using pygame.mixer")

class AudioError(Exception):
    """Exception raised for audio-related errors."""
    pass

class AudioState(Enum):
    """Audio playback states."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    FADING_IN = "fading_in"
    FADING_OUT = "fading_out"

class AudioEvent(Enum):
    """Audio events."""
    PLAYBACK_STARTED = "playback_started"
    PLAYBACK_STOPPED = "playback_stopped"
    PLAYBACK_PAUSED = "playback_paused"
    PLAYBACK_RESUMED = "playback_resumed"
    PLAYBACK_COMPLETED = "playback_completed"
    FADE_COMPLETE = "fade_complete"
    LOOP = "loop"

class SoundInfo:
    """
    Information about a loaded sound.
    
    Attributes:
        name (str): Name of the sound
        filepath (str): Path to the audio file
        duration (float): Duration in seconds
        channels (int): Number of audio channels
        sample_rate (int): Sample rate in Hz
        loaded_time (float): When the sound was loaded
    """
    
    def __init__(self, name: str, filepath: str, duration: float = 0.0, 
                 channels: int = 2, sample_rate: int = 44100):
        self.name = name
        self.filepath = filepath
        self.duration = duration
        self.channels = channels
        self.sample_rate = sample_rate
        self.loaded_time = time.time()
        self.ref_count = 0  # How many channels are using this sound
    
    def __repr__(self) -> str:
        return f"SoundInfo(name='{self.name}', duration={self.duration:.2f}s, refs={self.ref_count})"

class AudioChannel:
    """
    Audio channel for playback control.
    
    Each channel can play one sound at a time with individual volume,
    pitch, and pan controls.
    
    Args:
        channel_id (int): Unique identifier for this channel
        audio_system: Reference to the parent audio system
    """
    
    def __init__(self, channel_id: int, audio_system: 'AudioSystem'):
        self.channel_id = channel_id
        self.audio_system = audio_system
        self.use_openal = audio_system.use_openal
        
        # Playback properties
        self.volume = 1.0
        self.pitch = 1.0
        self.pan = 0.0
        self.loop = False
        self.state = AudioState.STOPPED
        
        # Sound reference
        self.current_sound: Optional[str] = None
        self.current_sound_info: Optional[SoundInfo] = None
        
        # Time tracking
        self.start_time = 0.0
        self.paused_time = 0.0
        
        # Transition control
        self._fade_thread: Optional[threading.Thread] = None
        self._stop_fade_event = threading.Event()
        
        # Backend-specific objects
        if self.use_openal:
            # Get source from OpenAL system
            self._openal_source: Optional[OpenALSource] = None
            system = get_audio_system()
            self._openal_source = system.get_free_source()
        else:
            # Pygame mixer channel
            self._pygame_channel: Optional[pygame.mixer.Channel] = pygame.mixer.Channel(channel_id)
            self._pygame_sound: Optional[pygame.mixer.Sound] = None
    
    def play(self, sound_name: str, loop: bool = False) -> bool:
        """
        Play a sound on this channel.
        
        Args:
            sound_name (str): Name of the sound to play
            loop (bool): Whether to loop the sound
            
        Returns:
            bool: True if playback started successfully
        """
        # Stop any current playback
        self.stop()
        
        # Get sound info
        sound_info = self.audio_system.get_sound_info(sound_name)
        if not sound_info:
            print(f"Sound '{sound_name}' not found")
            return False
        
        self.current_sound = sound_name
        self.current_sound_info = sound_info
        self.loop = loop
        self.state = AudioState.PLAYING
        self.start_time = time.time()
        self.paused_time = 0.0
        
        # Increment reference count
        sound_info.ref_count += 1
        
        if self.use_openal and self._openal_source:
            # OpenAL playback
            try:
                # Set buffer on source
                buffer = self.audio_system.openal_system.load_sound(sound_info.filepath)
                if buffer:
                    self._openal_source.set_buffer(buffer)
                    self._openal_source.set_volume(self.volume)
                    self._openal_source.set_pitch(self.pitch)
                    self._openal_source.set_pan(self.pan)
                    self._openal_source.play(loop)
                    return True
            except Exception as e:
                print(f"OpenAL play error: {e}")
                return False
        elif not self.use_openal:
            # Pygame mixer playback
            try:
                sound = self.audio_system.get_sound_pygame(sound_name)
                if sound:
                    self._pygame_sound = sound
                    loops = -1 if loop else 0
                    self._pygame_channel.play(sound, loops=loops)
                    self._update_pygame_volume()
                    return True
            except Exception as e:
                print(f"Pygame play error: {e}")
                return False
        
        return False
    
    def set_volume(self, volume: float, duration: float = 0.0):
        """
        Set channel volume with optional fade.
        
        Args:
            volume (float): Target volume (0.0 to 1.0)
            duration (float): Fade duration in seconds
        """
        volume = max(0.0, min(1.0, volume))
        
        if duration <= 0:
            # Immediate change
            self.volume = volume
            if self.use_openal and self._openal_source:
                self._openal_source.set_volume(volume)
            elif self._pygame_channel:
                self._update_pygame_volume()
        else:
            # Start fade thread
            self._start_volume_transition(volume, duration)
    
    def _start_volume_transition(self, target_volume: float, duration: float):
        """Start smooth volume transition."""
        # Stop any existing fade
        self._stop_fade_event.set()
        if self._fade_thread and self._fade_thread.is_alive():
            self._fade_thread.join(timeout=0.1)
        self._stop_fade_event.clear()
        
        start_volume = self.volume
        
        self._fade_thread = threading.Thread(
            target=self._transition_volume,
            args=(start_volume, target_volume, duration),
            daemon=True
        )
        self._fade_thread.start()
    
    def _transition_volume(self, start: float, end: float, duration: float):
        """Smoothly transition volume."""
        steps = max(1, int(duration * 60))
        step_time = duration / steps
        
        for i in range(steps + 1):
            if self._stop_fade_event.is_set():
                break
            
            # Calculate eased progress
            progress = i / steps
            # Smooth step function
            if progress < 0.5:
                eased = 2 * progress * progress
            else:
                eased = 1 - math.pow(-2 * progress + 2, 2) / 2
            
            current_volume = start + (end - start) * eased
            self.volume = current_volume
            
            # Apply to backend
            if self.use_openal and self._openal_source:
                self._openal_source.set_volume(current_volume)
            elif self._pygame_channel:
                self._update_pygame_volume()
            
            time.sleep(step_time)
        
        if not self._stop_fade_event.is_set():
            self.volume = end
            if self.use_openal and self._openal_source:
                self._openal_source.set_volume(end)
            elif self._pygame_channel:
                self._update_pygame_volume()
    
    def set_pitch(self, pitch: float, duration: float = 0.0):
        """
        Set playback pitch.
        
        Args:
            pitch (float): Pitch multiplier (0.1 to 4.0)
            duration (float): Transition duration in seconds (OpenAL only)
        """
        pitch = max(0.1, min(4.0, pitch))
        self.pitch = pitch
        
        if self.use_openal and self._openal_source:
            self._openal_source.set_pitch(pitch, duration)
        # Pygame doesn't support pitch directly
    
    def set_pan(self, pan: float):
        """
        Set stereo panning.
        
        Args:
            pan (float): -1.0 (left) to 1.0 (right)
        """
        self.pan = max(-1.0, min(1.0, pan))
        
        if self.use_openal and self._openal_source:
            self._openal_source.set_pan(pan)
        elif self._pygame_channel:
            self._update_pygame_volume()
    
    def _update_pygame_volume(self):
        """Update pygame channel volume with panning."""
        if hasattr(self, '_pygame_channel') and self._pygame_channel:
            # Simple stereo panning
            left_vol = self.volume * (1.0 if self.pan >= 0 else 1.0 + self.pan)
            right_vol = self.volume * (1.0 if self.pan <= 0 else 1.0 - self.pan)
            self._pygame_channel.set_volume(left_vol, right_vol)
    
    def pause(self):
        """Pause playback."""
        if self.state != AudioState.PLAYING:
            return
        
        if self.use_openal and self._openal_source:
            self._openal_source.pause()
        elif self._pygame_channel:
            self._pygame_channel.pause()
        
        self.state = AudioState.PAUSED
        self.paused_time = time.time() - self.start_time
    
    def resume(self):
        """Resume playback."""
        if self.state != AudioState.PAUSED:
            return
        
        if self.use_openal and self._openal_source:
            self._openal_source.resume()
        elif hasattr(self, '_pygame_channel') and self._pygame_channel:
            self._pygame_channel.unpause()
        
        self.state = AudioState.PLAYING
        self.start_time = time.time() - self.paused_time
    
    def stop(self):
        """Stop playback."""
        self._stop_fade_event.set()
        
        if self.use_openal and self._openal_source:
            self._openal_source.stop()
            self._openal_source.rewind()
        elif hasattr(self, '_pygame_channel') and self._pygame_channel:
            self._pygame_channel.stop()
        
        # Decrement reference count
        if self.current_sound_info:
            self.current_sound_info.ref_count = max(0, self.current_sound_info.ref_count - 1)
        
        self.state = AudioState.STOPPED
        self.current_sound = None
        self.current_sound_info = None
    
    def is_playing(self) -> bool:
        """Check if channel is playing."""
        if self.use_openal and self._openal_source:
            return self._openal_source.is_playing()
        elif self._pygame_channel:
            return self._pygame_channel.get_busy() and self.state == AudioState.PLAYING
        return False
    
    def is_paused(self) -> bool:
        """Check if channel is paused."""
        return self.state == AudioState.PAUSED
    
    def get_playback_position(self) -> float:
        """Get current playback position in seconds."""
        if not self.is_playing() and not self.is_paused():
            return 0.0
        
        if self.use_openal and self._openal_source:
            return self._openal_source.get_playback_position()
        
        # Pygame doesn't support position query
        if self.state == AudioState.PAUSED:
            return self.paused_time
        elif self.state == AudioState.PLAYING:
            return time.time() - self.start_time
        
        return 0.0
    
    def cleanup(self):
        """Clean up channel resources."""
        self.stop()
        if self._fade_thread and self._fade_thread.is_alive():
            self._fade_thread.join(timeout=0.1)

class AudioSystem:
    """
    Main audio system with sound management and channel allocation.
    
    Features:
    - Load sounds by name and store for reuse
    - Automatic channel allocation or explicit channel selection
    - Resource management and cleanup
    - OpenAL backend with Pygame fallback
    
    Args:
        num_channels (int): Maximum number of concurrent audio channels
        use_openal (bool): Whether to use OpenAL backend
    """
    
    def __init__(self, num_channels: int = 16, use_openal: bool = None):
        # Determine backend
        if use_openal is None:
            self.use_openal = USE_OPENAL
        else:
            self.use_openal = use_openal and USE_OPENAL
        
        # Sound management
        self._sounds: Dict[str, SoundInfo] = {}  # name -> SoundInfo
        self._pygame_sounds: Dict[str, pygame.mixer.Sound] = {}  # name -> pygame Sound
        
        # Channel management
        self.channels: List[AudioChannel] = []
        self.num_channels = num_channels
        
        # Initialize backend
        if self.use_openal:
            self._init_openal()
        else:
            self._init_pygame()
        
        # System properties
        self.master_volume = 1.0
        self.music_volume = 0.8
        self.sfx_volume = 0.9
        
        print(f"Audio System initialized: {'OpenAL' if self.use_openal else 'Pygame'} "
              f"with {num_channels} channels")
    
    def _init_openal(self):
        """Initialize OpenAL backend."""
        try:
            if not initialize_audio(self.num_channels):
                raise AudioError("Failed to initialize OpenAL")
            
            self.openal_system = get_audio_system()
            
            # Create channels
            for i in range(self.num_channels):
                self.channels.append(AudioChannel(i, self))
            
        except Exception as e:
            print(f"OpenAL initialization failed: {e}")
            self.use_openal = False
            self._init_pygame()
    
    def _init_pygame(self):
        """Initialize Pygame mixer backend."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            
            # Set number of channels
            current_channels = pygame.mixer.get_num_channels()
            if current_channels < self.num_channels:
                pygame.mixer.set_num_channels(self.num_channels)
            
            # Create channels
            for i in range(self.num_channels):
                self.channels.append(AudioChannel(i, self))
            
        except Exception as e:
            print(f"Pygame mixer initialization failed: {e}")
            raise AudioError(f"Audio system initialization failed: {e}")
    
    def load_sound(self, name: str, filepath: str) -> bool:
        """
        Load a sound file and store it by name.
        
        Args:
            name (str): Name to assign to the sound
            filepath (str): Path to the audio file
            
        Returns:
            bool: True if sound was loaded successfully
        
        Raises:
            FileNotFoundError: If the sound file doesn't exist
            AudioError: If sound loading fails
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Sound file not found: {filepath}")
        
        # Check if already loaded
        if name in self._sounds:
            print(f"Sound '{name}' already loaded")
            return True
        
        try:
            # Get sound duration (approximate)
            duration = self._estimate_duration(filepath)
            
            # Store sound info
            sound_info = SoundInfo(name, filepath, duration)
            self._sounds[name] = sound_info
            
            # Load into Pygame if using Pygame backend
            if not self.use_openal:
                try:
                    sound = pygame.mixer.Sound(filepath)
                    self._pygame_sounds[name] = sound
                except Exception as e:
                    print(f"Warning: Could not preload '{name}' with Pygame: {e}")
            
            print(f"Loaded sound '{name}' from '{filepath}' (duration: {duration:.2f}s)")
            return True
            
        except Exception as e:
            raise AudioError(f"Failed to load sound '{name}': {e}")
    
    def _estimate_duration(self, filepath: str) -> float:
        """Estimate audio file duration."""
        try:
            # Try pygame first
            sound = pygame.mixer.Sound(filepath)
            return sound.get_length()
        except:
            pass
        
        # Fallback: estimate from file size
        try:
            size = os.path.getsize(filepath)
            # Rough estimate: 1MB ≈ 6 seconds of stereo 44.1kHz audio
            return size / (1024 * 1024) * 6
        except:
            return 1.0  # Default
    
    def get_sound_info(self, name: str) -> Optional[SoundInfo]:
        """Get information about a loaded sound."""
        return self._sounds.get(name)
    
    def get_sound_pygame(self, name: str) -> Optional[pygame.mixer.Sound]:
        """Get Pygame Sound object for a loaded sound."""
        if name in self._pygame_sounds:
            return self._pygame_sounds[name]
        
        # Try to load on demand
        sound_info = self.get_sound_info(name)
        if sound_info and os.path.exists(sound_info.filepath):
            try:
                sound = pygame.mixer.Sound(sound_info.filepath)
                self._pygame_sounds[name] = sound
                return sound
            except Exception as e:
                print(f"Failed to load sound '{name}' with Pygame: {e}")
        
        return None
    
    def play(self, sound_name: str, channel: Optional[int] = None, 
             volume: float = None, pitch: float = 1.0, pan: float = 0.0, 
             loop: bool = False) -> Optional[AudioChannel]:
        """
        Play a sound by name.
        
        Args:
            sound_name (str): Name of the sound to play
            channel (int, optional): Specific channel to use. If None, 
                                    uses first available channel
            volume (float, optional): Volume (0.0-1.0). Uses SFX volume if None
            pitch (float): Pitch multiplier
            pan (float): Stereo pan (-1.0 to 1.0)
            loop (bool): Whether to loop the sound
            
        Returns:
            Optional[AudioChannel]: Channel playing the sound, or None if failed
        """
        # Check if sound exists
        if sound_name not in self._sounds:
            print(f"Sound '{sound_name}' not found. Load it first with load_sound()")
            return None
        
        # Find channel
        if channel is not None:
            # Use specific channel
            if channel < 0 or channel >= len(self.channels):
                print(f"Invalid channel: {channel}")
                return None
            target_channel = self.channels[channel]
            
            # Stop if channel is busy
            if target_channel.is_playing() or target_channel.is_paused():
                target_channel.stop()
        else:
            # Find first available channel
            target_channel = None
            for ch in self.channels:
                if not ch.is_playing() and not ch.is_paused():
                    target_channel = ch
                    break
            
            if not target_channel:
                print("No available audio channels")
                return None
        
        # Set default volume
        if volume is None:
            volume = self.sfx_volume
        
        # Play sound
        if target_channel.play(sound_name, loop):
            target_channel.set_volume(volume)
            target_channel.set_pitch(pitch)
            target_channel.set_pan(pan)
            return target_channel
        
        return None
    
    def play_music(self, sound_name: str, volume: float = None, 
                   pitch: float = 1.0, loop: bool = True, 
                   fade_in: float = 0.0) -> Optional[AudioChannel]:
        """
        Play background music (uses channel 0).
        
        Args:
            sound_name (str): Name of the music sound
            volume (float, optional): Volume. Uses music volume if None
            pitch (float): Pitch multiplier
            loop (bool): Whether to loop
            fade_in (float): Fade-in duration in seconds
            
        Returns:
            Optional[AudioChannel]: Music channel, or None if failed
        """
        if volume is None:
            volume = self.music_volume
        
        # Use channel 0 for music
        music_channel = self.channels[0] if self.channels else None
        if not music_channel:
            print("No channels available for music")
            return None
        
        # Stop current music
        if music_channel.is_playing() or music_channel.is_paused():
            music_channel.stop()
        
        # Play music
        if music_channel.play(sound_name, loop):
            if fade_in > 0:
                # Start silent and fade in
                music_channel.volume = 0.0
                music_channel._update_pygame_volume()
                music_channel.set_volume(volume, fade_in)
            else:
                music_channel.set_volume(volume)
            
            music_channel.set_pitch(pitch)
            music_channel.set_pan(0.0)  # Center pan for music
            
            return music_channel
        
        return None
    
    def stop_all(self):
        """Stop all audio playback."""
        for channel in self.channels:
            channel.stop()
        
        if self.use_openal and hasattr(self, 'openal_system'):
            self.openal_system.stop_all()
    
    def pause_all(self):
        """Pause all audio playback."""
        for channel in self.channels:
            if channel.is_playing():
                channel.pause()
    
    def resume_all(self):
        """Resume all paused audio."""
        for channel in self.channels:
            if channel.is_paused():
                channel.resume()
    
    def set_master_volume(self, volume: float):
        """Set master volume for all audio."""
        self.master_volume = max(0.0, min(1.0, volume))
        
        # This would need to be applied to all channels
        # Implementation depends on backend capabilities
    
    def set_music_volume(self, volume: float):
        """Set music volume."""
        self.music_volume = max(0.0, min(1.0, volume))
        
        # Update music channel if playing
        if self.channels:
            music_channel = self.channels[0]
            if music_channel.is_playing() or music_channel.is_paused():
                music_channel.set_volume(volume)
    
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume."""
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def get_channel_info(self) -> List[Dict]:
        """Get information about all channels."""
        info = []
        for i, channel in enumerate(self.channels):
            info.append({
                'id': i,
                'state': channel.state.value,
                'sound': channel.current_sound,
                'volume': channel.volume,
                'pitch': channel.pitch,
                'pan': channel.pan,
                'playing': channel.is_playing(),
                'paused': channel.is_paused(),
                'position': channel.get_playback_position()
            })
        return info
    
    def unload_sound(self, name: str, force: bool = False) -> bool:
        """
        Unload a sound from memory.
        
        Args:
            name (str): Name of the sound to unload
            force (bool): Force unload even if sound is in use
            
        Returns:
            bool: True if sound was unloaded
        """
        if name not in self._sounds:
            return False
        
        sound_info = self._sounds[name]
        
        # Check if sound is in use
        if sound_info.ref_count > 0 and not force:
            print(f"Cannot unload '{name}': {sound_info.ref_count} channels are using it")
            return False
        
        # Remove from dictionaries
        self._sounds.pop(name, None)
        self._pygame_sounds.pop(name, None)
        
        print(f"Unloaded sound '{name}'")
        return True
    
    def unload_unused_sounds(self, max_age: float = 300.0):
        """
        Unload sounds that haven't been used for a while.
        
        Args:
            max_age (float): Maximum age in seconds
        """
        current_time = time.time()
        to_unload = []
        
        for name, sound_info in self._sounds.items():
            if sound_info.ref_count == 0 and (current_time - sound_info.loaded_time) > max_age:
                to_unload.append(name)
        
        for name in to_unload:
            self.unload_sound(name, force=True)
    
    def update(self):
        """Update audio system (call periodically)."""
        if self.use_openal and hasattr(self, 'openal_system'):
            self.openal_system.update()
    
    def cleanup(self):
        """Clean up all audio resources."""
        self.stop_all()
        
        # Clean up channels
        for channel in self.channels:
            channel.cleanup()
        
        # Clean up backend
        if self.use_openal and hasattr(self, 'openal_system'):
            cleanup_audio()
        
        # Clear sound dictionaries
        self._sounds.clear()
        self._pygame_sounds.clear()
        
        print("Audio system cleaned up")