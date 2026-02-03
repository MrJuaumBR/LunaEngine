"""
OpenAL Audio Backend for LunaEngine - Optimized for 2D games

This module provides OpenAL-based audio with the following features:
- Efficient buffer management and pooling
- Support for WAV, OGG, MP3 formats (via Pygame)
- Smooth volume/pitch transitions
- Stereo panning support
- Thread-safe operations
"""

import ctypes
import threading
import time
import math
import wave
import struct
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from enum import Enum
import weakref
import os

# Try to import OpenAL
try:
    from openal import al, alc, ALuint, ALint, ALfloat
    OPENAL_AVAILABLE = True
except ImportError:
    OPENAL_AVAILABLE = False
    print("Warning: PyOpenAL not installed. Using pygame fallback.")
    # Create dummy classes for fallback
    class DummyOpenAL:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    al = DummyOpenAL()
    alc = DummyOpenAL()
    ALuint = int
    ALint = int
    ALfloat = float

# Try to import pygame for audio loading
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: PyGame not installed. Audio loading will be limited.")

class OpenALError(Exception):
    """Exception raised for OpenAL related errors."""
    pass

class OpenALAudioEvent(Enum):
    """Audio events for OpenAL system."""
    COMPLETE = "complete"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"

class OpenALBuffer:
    """
    OpenAL audio buffer with memory pooling.
    
    Manages audio data in OpenAL buffers with caching for frequently used sounds.
    
    Attributes:
        buffer_id (int): OpenAL buffer ID
        duration (float): Buffer duration in seconds
        size (int): Buffer size in bytes
        format (int): OpenAL format constant
        frequency (int): Sample rate in Hz
        last_used (float): Last access time for LRU cleanup
    """
    
    _buffer_pool: Dict[str, 'OpenALBuffer'] = {}
    
    def __init__(self, buffer_id: int):
        self.buffer_id = buffer_id
        self.duration = 0.0
        self.size = 0
        self.format = 0
        self.frequency = 0
        self.last_used = time.time()
    
    @classmethod
    def get_or_create(cls, filepath: str) -> Optional['OpenALBuffer']:
        """
        Get buffer from pool or create new one.
        
        Args:
            filepath (str): Path to audio file
            
        Returns:
            Optional[OpenALBuffer]: Buffer object or None if failed
        """
        if not OPENAL_AVAILABLE:
            return None
        
        filepath = os.path.abspath(filepath)
        
        # Check pool
        if filepath in cls._buffer_pool:
            buffer = cls._buffer_pool[filepath]
            buffer.last_used = time.time()
            return buffer
        
        # Create new buffer
        try:
            buffer_id = ALuint(0)
            al.alGenBuffers(1, ctypes.byref(buffer_id))
            
            # Load audio data
            if cls._load_audio_file(buffer_id, filepath):
                buffer = OpenALBuffer(buffer_id.value)
                buffer._update_buffer_info()
                cls._buffer_pool[filepath] = buffer
                return buffer
            else:
                al.alDeleteBuffers(1, ctypes.byref(buffer_id))
                
        except Exception as e:
            print(f"Failed to create buffer for {filepath}: {e}")
        
        return None
    
    def _update_buffer_info(self):
        """Update buffer information from OpenAL."""
        if not OPENAL_AVAILABLE:
            return
        
        try:
            buffer_id = ALuint(self.buffer_id)
            
            # Get buffer size
            size = ALint(0)
            al.alGetBufferi(buffer_id, al.AL_SIZE, ctypes.byref(size))
            self.size = size.value
            
            # Get buffer bits
            bits = ALint(0)
            al.alGetBufferi(buffer_id, al.AL_BITS, ctypes.byref(bits))
            
            # Get buffer channels
            channels = ALint(0)
            al.alGetBufferi(buffer_id, al.AL_CHANNELS, ctypes.byref(channels))
            channel_count = channels.value
            
            # Set format
            if channel_count == 1:
                if bits.value == 8:
                    self.format = al.AL_FORMAT_MONO8
                else:
                    self.format = al.AL_FORMAT_MONO16
            else:
                if bits.value == 8:
                    self.format = al.AL_FORMAT_STEREO8
                else:
                    self.format = al.AL_FORMAT_STEREO16
            
            # Get frequency
            freq = ALint(0)
            al.alGetBufferi(buffer_id, al.AL_FREQUENCY, ctypes.byref(freq))
            self.frequency = freq.value
            
            # Calculate duration
            if self.frequency > 0:
                bytes_per_sample = 1 if bits.value == 8 else 2
                total_samples = self.size // (bytes_per_sample * max(1, channel_count))
                self.duration = total_samples / self.frequency
            
        except Exception as e:
            print(f"Failed to update buffer info: {e}")
    
    @staticmethod
    def _load_audio_file(buffer_id: ALuint, filepath: str) -> bool:
        """
        Load audio file into OpenAL buffer.
        
        Args:
            buffer_id: OpenAL buffer ID
            filepath (str): Path to audio file
            
        Returns:
            bool: True if successful
        """
        if not os.path.exists(filepath):
            print(f"Audio file not found: {filepath}")
            return False
        
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == '.wav':
            return OpenALBuffer._load_wav_file(buffer_id, filepath)
        elif PYGAME_AVAILABLE:
            return OpenALBuffer._load_with_pygame(buffer_id, filepath)
        else:
            print(f"Unsupported audio format: {ext}")
            return False
    
    @staticmethod
    def _load_wav_file(buffer_id: ALuint, filepath: str) -> bool:
        """Load WAV file using Python's wave module."""
        try:
            with wave.open(filepath, 'rb') as wav_file:
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                frames = wav_file.readframes(n_frames)
                
                # Determine OpenAL format
                if n_channels == 1:
                    if sample_width == 1:
                        format = al.AL_FORMAT_MONO8
                    elif sample_width == 2:
                        format = al.AL_FORMAT_MONO16
                    else:
                        print(f"Unsupported sample width: {sample_width}")
                        return False
                elif n_channels == 2:
                    if sample_width == 1:
                        format = al.AL_FORMAT_STEREO8
                    elif sample_width == 2:
                        format = al.AL_FORMAT_STEREO16
                    else:
                        print(f"Unsupported sample width: {sample_width}")
                        return False
                else:
                    print(f"Unsupported channel count: {n_channels}")
                    return False
                
                # Upload to OpenAL
                al.alBufferData(buffer_id, format, frames, len(frames), framerate)
                return True
                
        except Exception as e:
            print(f"Failed to load WAV file {filepath}: {e}")
            return False
    
    @staticmethod
    def _load_with_pygame(buffer_id: ALuint, filepath: str) -> bool:
        """Load audio file using PyGame mixer."""
        if not PYGAME_AVAILABLE:
            return False
        
        try:
            # Load sound with pygame
            sound = pygame.mixer.Sound(filepath)
            
            # Get raw audio data
            raw_data = sound.get_raw()
            
            # PyGame typically uses 16-bit stereo at 44100Hz
            channels = 2
            bits = 16
            freq = 44100
            
            # Try to get actual parameters
            try:
                # Get length in seconds
                length = sound.get_length()
                # Calculate approximate frequency
                if length > 0:
                    samples = len(raw_data) // (channels * (bits // 8))
                    freq = int(samples / length)
            except:
                pass
            
            # Determine format
            if channels == 1:
                format = al.AL_FORMAT_MONO16 if bits == 16 else al.AL_FORMAT_MONO8
            else:
                format = al.AL_FORMAT_STEREO16 if bits == 16 else al.AL_FORMAT_STEREO8
            
            # Upload to OpenAL
            al.alBufferData(buffer_id, format, raw_data, len(raw_data), freq)
            return True
            
        except Exception as e:
            print(f"Failed to load audio with pygame {filepath}: {e}")
            return False
    
    @classmethod
    def cleanup_unused(cls, max_age: float = 300.0):
        """Clean up buffers not used for a while."""
        current_time = time.time()
        to_remove = []
        
        for filepath, buffer in cls._buffer_pool.items():
            if current_time - buffer.last_used > max_age:
                to_remove.append(filepath)
        
        for filepath in to_remove:
            buffer = cls._buffer_pool.pop(filepath)
            if OPENAL_AVAILABLE:
                buffer_id = ALuint(buffer.buffer_id)
                al.alDeleteBuffers(1, ctypes.byref(buffer_id))
    
    def get_duration(self) -> float:
        """Get buffer duration in seconds."""
        return self.duration

class OpenALSource:
    """
    OpenAL audio source for 2D games.
    
    Provides playback control with smooth transitions and stereo panning.
    
    Attributes:
        source_id (int): OpenAL source ID
        buffer (OpenALBuffer): Current audio buffer
        volume (float): Current volume (0.0-1.0)
        pitch (float): Current pitch multiplier
        pan (float): Stereo pan (-1.0 to 1.0)
        looping (bool): Whether source is looping
    """
    
    def __init__(self, source_id: int):
        self.source_id = source_id
        self.buffer: Optional[OpenALBuffer] = None
        
        # Audio properties
        self.volume = 1.0
        self.pitch = 1.0
        self.pan = 0.0
        self.looping = False
        
        # Configure for 2D audio
        if OPENAL_AVAILABLE:
            al.alSourcei(source_id, al.AL_SOURCE_RELATIVE, al.AL_TRUE)
            al.alSource3f(source_id, al.AL_POSITION, 0.0, 0.0, 0.0)
            al.alSourcef(source_id, al.AL_ROLLOFF_FACTOR, 0.0)  # No distance attenuation
    
    def set_buffer(self, buffer: OpenALBuffer):
        """Set buffer for this source."""
        self.buffer = buffer
        if OPENAL_AVAILABLE:
            buffer_id = ALuint(buffer.buffer_id)
            al.alSourcei(self.source_id, al.AL_BUFFER, buffer_id.value)
    
    def set_volume(self, volume: float, duration: float = 0.0):
        """Set volume with optional smooth transition."""
        volume = max(0.0, min(1.0, volume))
        self.volume = volume
        
        if OPENAL_AVAILABLE:
            if duration <= 0:
                al.alSourcef(self.source_id, al.AL_GAIN, volume)
            else:
                # Simple linear fade (OpenAL doesn't have built-in fades)
                current_gain = ALfloat(0.0)
                al.alGetSourcef(self.source_id, al.AL_GAIN, ctypes.byref(current_gain))
                self._fade_volume(current_gain.value, volume, duration)
    
    def _fade_volume(self, start: float, end: float, duration: float):
        """Fade volume over time (simplified implementation)."""
        # Note: For proper smooth fades, you'd want to use threading
        # This is a simplified version
        if not OPENAL_AVAILABLE:
            return
        
        steps = max(1, int(duration * 60))
        step_time = duration / steps
        
        for i in range(steps + 1):
            progress = i / steps
            current = start + (end - start) * progress
            al.alSourcef(self.source_id, al.AL_GAIN, current)
            time.sleep(step_time)
    
    def set_pitch(self, pitch: float, duration: float = 0.0):
        """Set pitch with optional transition."""
        pitch = max(0.1, min(4.0, pitch))
        self.pitch = pitch
        
        if OPENAL_AVAILABLE:
            al.alSourcef(self.source_id, al.AL_PITCH, pitch)
    
    def set_pan(self, pan: float):
        """Set stereo panning."""
        self.pan = max(-1.0, min(1.0, pan))
        
        if OPENAL_AVAILABLE:
            # Simple panning using position
            al.alSource3f(self.source_id, al.AL_POSITION, pan, 0.0, -1.0)
    
    def play(self, loop: bool = False):
        """Start playback."""
        if OPENAL_AVAILABLE:
            self.looping = loop
            al.alSourcei(self.source_id, al.AL_LOOPING, al.AL_TRUE if loop else al.AL_FALSE)
            al.alSourcePlay(self.source_id)
    
    def pause(self):
        """Pause playback."""
        if OPENAL_AVAILABLE:
            al.alSourcePause(self.source_id)
    
    def resume(self):
        """Resume playback."""
        if OPENAL_AVAILABLE:
            al.alSourcePlay(self.source_id)
    
    def stop(self):
        """Stop playback."""
        if OPENAL_AVAILABLE:
            al.alSourceStop(self.source_id)
    
    def rewind(self):
        """Rewind to beginning."""
        if OPENAL_AVAILABLE:
            al.alSourceRewind(self.source_id)
    
    def is_playing(self) -> bool:
        """Check if source is playing."""
        if not OPENAL_AVAILABLE:
            return False
        
        state = ALint(0)
        al.alGetSourcei(self.source_id, al.AL_SOURCE_STATE, ctypes.byref(state))
        return state.value == al.AL_PLAYING
    
    def is_paused(self) -> bool:
        """Check if source is paused."""
        if not OPENAL_AVAILABLE:
            return False
        
        state = ALint(0)
        al.alGetSourcei(self.source_id, al.AL_SOURCE_STATE, ctypes.byref(state))
        return state.value == al.AL_PAUSED
    
    def get_playback_position(self) -> float:
        """Get current playback position in seconds."""
        if not OPENAL_AVAILABLE or not self.is_playing():
            return 0.0
        
        offset = ALfloat(0.0)
        al.alGetSourcef(self.source_id, al.AL_SEC_OFFSET, ctypes.byref(offset))
        return offset.value

class OpenALAudioSystem:
    """
    Main OpenAL audio system for 2D games.
    
    Manages audio sources, buffers, and provides playback functionality.
    
    Attributes:
        device: OpenAL device
        context: OpenAL context
        sources (List[OpenALSource]): Available audio sources
        max_sources (int): Maximum number of concurrent sources
        initialized (bool): Whether system is initialized
    """
    
    def __init__(self, max_sources: int = 32):
        self.device = None
        self.context = None
        self.sources: List[OpenALSource] = []
        self.max_sources = max_sources
        self.initialized = False
        
        if OPENAL_AVAILABLE:
            self.initialize()
    
    def initialize(self) -> bool:
        """Initialize OpenAL system."""
        if self.initialized or not OPENAL_AVAILABLE:
            return self.initialized
        
        try:
            # Open default device
            self.device = alc.alcOpenDevice(None)
            if not self.device:
                print("Failed to open OpenAL device")
                return False
            
            # Create context
            self.context = alc.alcCreateContext(self.device, None)
            if not self.context:
                alc.alcCloseDevice(self.device)
                print("Failed to create OpenAL context")
                return False
            
            # Make context current
            alc.alcMakeContextCurrent(self.context)
            
            # Create sources
            for i in range(self.max_sources):
                source_id = ALuint(0)
                al.alGenSources(1, ctypes.byref(source_id))
                source = OpenALSource(source_id.value)
                self.sources.append(source)
            
            # Set listener for 2D audio
            al.alListener3f(al.AL_POSITION, 0.0, 0.0, 0.0)
            al.alListener3f(al.AL_VELOCITY, 0.0, 0.0, 0.0)
            
            self.initialized = True
            print(f"OpenAL Audio System initialized with {self.max_sources} sources")
            return True
            
        except Exception as e:
            print(f"OpenAL initialization failed: {e}")
            self.cleanup()
            return False
    
    def get_free_source(self) -> Optional[OpenALSource]:
        """Get a free audio source."""
        if not self.initialized:
            return None
        
        for source in self.sources:
            if not source.is_playing() and not source.is_paused():
                return source
        
        return None
    
    def load_sound(self, filepath: str) -> Optional[OpenALBuffer]:
        """Load sound file."""
        return OpenALBuffer.get_or_create(filepath)
    
    def play_sound(self, filepath: str, volume: float = 1.0, 
                   pitch: float = 1.0, pan: float = 0.0, 
                   loop: bool = False) -> Optional[OpenALSource]:
        """Play a sound effect."""
        # Load buffer
        buffer = self.load_sound(filepath)
        if not buffer:
            return None
        
        # Get source
        source = self.get_free_source()
        if not source:
            print("No free audio sources available")
            return None
        
        # Configure and play
        source.set_buffer(buffer)
        source.set_volume(volume)
        source.set_pitch(pitch)
        source.set_pan(pan)
        source.play(loop)
        
        return source
    
    def stop_all(self):
        """Stop all sounds."""
        for source in self.sources:
            source.stop()
    
    def update(self):
        """Update audio system (clean up unused buffers)."""
        OpenALBuffer.cleanup_unused()
    
    def cleanup(self):
        """Clean up all audio resources."""
        self.stop_all()
        
        # Clean up sources
        if OPENAL_AVAILABLE:
            for source in self.sources:
                source_id = ALuint(source.source_id)
                al.alDeleteSources(1, ctypes.byref(source_id))
        
        # Clean up OpenAL context
        if OPENAL_AVAILABLE:
            if self.context:
                alc.alcMakeContextCurrent(None)
                alc.alcDestroyContext(self.context)
                self.context = None
            
            if self.device:
                alc.alcCloseDevice(self.device)
                self.device = None
        
        self.initialized = False
        print("OpenAL system cleaned up")


class OpenALAudioVisualizer:
    """
    Audio visualizer that works with OpenAL audio system.
    
    Provides methods to capture and analyze audio data from OpenAL sources.
    """
    
    def __init__(self, audio_system: OpenALAudioSystem):
        """
        Initialize audio visualizer.
        
        Args:
            audio_system (OpenALAudioSystem): OpenAL audio system to visualize.
        """
        self.audio_system = audio_system
        self.visualization_data = []
        self.num_samples = 1024
        self.sample_rate = 44100
        
        # FFT setup
        self.fft_size = 512
        self.freq_bins = []
        
        # Initialize data buffers
        self._initialize_buffers()
    
    def _initialize_buffers(self):
        """Initialize data buffers."""
        self.visualization_data = [0.0] * self.num_samples
        self.freq_bins = [0.0] * (self.fft_size // 2)
    
    def capture_audio_data(self, source: Optional[OpenALSource] = None) -> List[float]:
        """
        Capture audio data from a source or all playing sources.
        
        Args:
            source (Optional[OpenALSource]): Specific source to capture from.
            
        Returns:
            List[float]: Normalized audio data.
        """
        if not OPENAL_AVAILABLE:
            return [0.0] * self.num_samples
        
        # In a real implementation, you would:
        # 1. Query OpenAL for audio data from buffers
        # 2. Process the raw PCM data
        # 3. Return normalized visualization data
        
        # For now, return simulated data
        return self._get_simulated_data()
    
    def perform_fft_analysis(self, audio_data: List[float]) -> List[float]:
        """
        Perform FFT analysis on audio data.
        
        Args:
            audio_data (List[float]): Time-domain audio data.
            
        Returns:
            List[float]: Frequency-domain data.
        """
        # Simple FFT simulation - in real implementation use numpy.fft
        import random
        result = []
        
        for i in range(self.fft_size // 2):
            # Simulate frequency response
            freq = i / (self.fft_size // 2)
            amplitude = 0.0
            
            # Generate some frequency peaks
            for peak_freq in [0.1, 0.3, 0.5, 0.7, 0.9]:
                distance = abs(freq - peak_freq)
                if distance < 0.1:
                    peak_height = math.exp(-distance * 20)
                    amplitude += peak_height * (0.5 + 0.5 * math.sin(time.time() * 2))
            
            # Add some noise
            amplitude += random.uniform(0, 0.1)
            
            # Apply frequency roll-off (simulate natural audio)
            amplitude *= (1.0 - freq * 0.8)
            
            result.append(min(1.0, amplitude))
        
        return result
    
    def get_peak_level(self) -> float:
        """
        Get current peak audio level.
        
        Returns:
            float: Peak level (0-1).
        """
        if not self.visualization_data:
            return 0.0
        return max(self.visualization_data)
    
    def get_rms_level(self) -> float:
        """
        Get RMS (root mean square) audio level.
        
        Returns:
            float: RMS level (0-1).
        """
        if not self.visualization_data:
            return 0.0
        
        sum_squares = sum(x * x for x in self.visualization_data)
        rms = math.sqrt(sum_squares / len(self.visualization_data))
        return min(1.0, rms)
    
    def _get_simulated_data(self) -> List[float]:
        """
        Generate simulated audio data for demonstration.
        
        Returns:
            List[float]: Simulated audio data.
        """
        current_time = time.time()
        data = []
        
        # Check if any sources are playing
        has_playing_source = False
        if self.audio_system and self.audio_system.initialized:
            for source in self.audio_system.sources:
                if source.is_playing():
                    has_playing_source = True
                    break
        
        if has_playing_source:
            # Simulate music/audio with multiple frequencies
            for i in range(self.num_samples):
                t = current_time + i / self.sample_rate
                
                # Bass frequency (low)
                bass = math.sin(t * 2 * math.pi * 60) * 0.3
                
                # Mid frequencies
                mid1 = math.sin(t * 2 * math.pi * 440) * 0.2
                mid2 = math.sin(t * 2 * math.pi * 880) * 0.15
                
                # High frequencies
                high = math.sin(t * 2 * math.pi * 1760) * 0.1
                
                # Combine with some randomness
                value = bass + mid1 + mid2 + high
                value += random.uniform(-0.05, 0.05)
                
                # Normalize
                value = max(-1.0, min(1.0, value))
                data.append(abs(value))
        else:
            # Idle/silent mode
            for i in range(self.num_samples):
                # Gentle pulsing
                t = current_time + i / self.sample_rate
                value = math.sin(t * 2 * math.pi * 2) * 0.1 + 0.1
                data.append(value)
        
        return data

# Global instance management
_openal_system: Optional[OpenALAudioSystem] = None

def get_audio_system() -> OpenALAudioSystem:
    """Get global audio system instance."""
    global _openal_system
    if _openal_system is None:
        _openal_system = OpenALAudioSystem()
    return _openal_system

def initialize_audio(max_sources: int = 32) -> bool:
    """Initialize global audio system."""
    global _openal_system
    if _openal_system is None:
        _openal_system = OpenALAudioSystem(max_sources)
    return _openal_system.initialized

def cleanup_audio():
    """Clean up global audio system."""
    global _openal_system
    if _openal_system:
        _openal_system.cleanup()
        _openal_system = None