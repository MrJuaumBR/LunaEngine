"""
Advanced Audio System - Enhanced with Dynamic Control and Smooth Transitions

LOCATION: lunaengine/core/audio.py


"""

import pygame, threading, time, os, math
from typing import Dict, List, Callable, Optional, Union, Any, Tuple
from enum import Enum
import numpy as np

class AudioState(Enum):
    """Enumeration for audio playback states."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    FADING_IN = "fading_in"
    FADING_OUT = "fading_out"
    SPEED_CHANGING = "speed_changing"
    VOLUME_CHANGING = "volume_changing"

class AudioEvent(Enum):
    """Enumeration for audio events."""
    COMPLETE = "complete"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    FADE_START = "fade_start"
    FADE_COMPLETE = "fade_complete"
    LOOP = "loop"
    SPEED_CHANGE = "speed_change"
    VOLUME_CHANGE = "volume_change"
    SPEED_CHANGE_START = "speed_change_start"
    SPEED_CHANGE_COMPLETE = "speed_change_complete"

class AudioChannel:
    """
    Enhanced audio channel with dynamic control and smooth transitions.
    
    NEW FEATURES:
    - Dynamic speed changes without stopping playback
    - Smooth transitions for volume and speed
    - Audio duration information
    - Improved state management
    """
    
    def __init__(self, channel_id: int):
        """
        Initialize an enhanced audio channel.
        
        Args:
            channel_id (int): Pygame mixer channel number
        """
        self.channel_id = channel_id
        self.sound: Optional[pygame.mixer.Sound] = None
        self.original_sound: Optional[pygame.mixer.Sound] = None  # Store original for speed changes
        self.volume = 1.0
        self.target_volume = 1.0
        self.speed = 1.0
        self.target_speed = 1.0
        self.loop = False
        self.state = AudioState.STOPPED
        self._event_handlers: Dict[AudioEvent, List[Callable]] = {}
        self._fade_thread: Optional[threading.Thread] = None
        self._speed_thread: Optional[threading.Thread] = None
        self._stop_threads = threading.Event()
        
        # NEW: For smooth transitions
        self._transition_lock = threading.Lock()
        
    def get_duration(self) -> float:
        """
        Get the duration of the loaded sound in seconds.
        
        Returns:
            float: Duration in seconds, or 0.0 if no sound loaded
        """
        if self.sound:
            try:
                # Pygame Sound objects have get_length() method
                return self.sound.get_length()
            except AttributeError:
                # Fallback calculation based on buffer size
                return getattr(self.sound, '_length', 0.0) / 1000.0  # Convert ms to seconds
        return 0.0
    
    def get_playback_position(self) -> float:
        """
        Get current playback position in seconds.
        
        Note: This is an approximation since pygame doesn't provide exact position.
        
        Returns:
            float: Current playback position in seconds
        """
        if not self.is_playing() or not self.sound:
            return 0.0
        
        # This is a rough approximation - pygame doesn't provide exact playback position
        channel = pygame.mixer.Channel(self.channel_id)
        if hasattr(channel, 'get_position'):
            try:
                return channel.get_position() / 1000.0  # Convert ms to seconds
            except:
                pass
        
        # Fallback: estimate based on elapsed time (less accurate)
        return 0.0
    
    def play(self, sound: pygame.mixer.Sound, loop: bool = False) -> bool:
        """
        Play a sound on this channel with enhanced state management.
        
        Args:
            sound (pygame.mixer.Sound): Sound to play
            loop (bool, optional): Whether to loop. Defaults to False.
            
        Returns:
            bool: True if playback started successfully
        """
        try:
            self._stop_threads.set()  # Stop any ongoing transitions
            time.sleep(0.01)  # Brief pause to ensure thread stops
            self._stop_threads.clear()
            
            self.sound = sound
            self.original_sound = sound  # Store original for speed changes
            self.loop = loop
            self.volume = 1.0
            self.target_volume = 1.0
            self.speed = 1.0
            self.target_speed = 1.0
            
            channel = pygame.mixer.Channel(self.channel_id)
            loops = -1 if loop else 0
            channel.play(sound, loops=loops)
            channel.set_volume(self.volume)
            
            self.state = AudioState.PLAYING
            return True
            
        except Exception as e:
            print(f"Error playing sound on channel {self.channel_id}: {e}")
            return False
    
    def pause(self) -> None:
        """Pause playback on this channel with state verification."""
        if self.state == AudioState.PLAYING:
            channel = pygame.mixer.Channel(self.channel_id)
            channel.pause()
            self.state = AudioState.PAUSED
            self._trigger_event(AudioEvent.PAUSE)
    
    def resume(self) -> None:
        """Resume playback on this channel with state verification."""
        if self.state == AudioState.PAUSED:
            channel = pygame.mixer.Channel(self.channel_id)
            channel.unpause()
            self.state = AudioState.PLAYING
            self._trigger_event(AudioEvent.RESUME)
    
    def set_volume(self, volume: float, duration: float = 0.0) -> None:
        """
        Set channel volume with optional smooth transition.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
            duration (float): Transition duration in seconds. 0 for immediate change.
        """
        volume = max(0.0, min(1.0, volume))
        
        if duration <= 0:
            # Immediate change
            self.volume = volume
            self.target_volume = volume
            channel = pygame.mixer.Channel(self.channel_id)
            channel.set_volume(self.volume)
            self._trigger_event(AudioEvent.VOLUME_CHANGE)
        else:
            # Smooth transition
            self._stop_threads.set()
            time.sleep(0.01)
            self._stop_threads.clear()
            
            self.target_volume = volume
            self._fade_thread = threading.Thread(
                target=self._transition_volume,
                args=(self.volume, volume, duration)
            )
            self._fade_thread.daemon = True
            self._fade_thread.start()
    
    def set_speed(self, speed: float, duration: float = 0.0) -> None:
        """Change the speed of the sound playback."""
        if duration <= 0:
            self.speed = speed
            self.target_speed = speed
            self._trigger_event(AudioEvent.SPEED_CHANGE)
        else:
            self._smooth_speed_transition(self.speed, speed, duration)
    
    def _change_speed_immediate(self, speed: float) -> None:
        """
        Change playback speed immediately using pitch adjustment.
        
        Args:
            speed (float): Target speed multiplier
        """
        self.speed = speed
        self.target_speed = speed
        
        if self.sound and self.original_sound:
            try:
                # Only repitch if significantly different from 1.0
                if abs(speed - 1.0) > 0.05:
                    # Get sound array from original sound
                    array = pygame.sndarray.array(self.original_sound)
                    
                    # Resample based on speed
                    length = int(len(array) / speed)
                    indices = (np.arange(length) * speed).astype(int)
                    indices = np.clip(indices, 0, len(array) - 1)
                    resampled = array[indices]
                    
                    # Create new sound
                    new_sound = pygame.sndarray.make_sound(resampled)
                    
                    # Replace the sound if currently playing
                    was_playing = self.is_playing()
                    was_paused = self.is_paused()
                    
                    if was_playing or was_paused:
                        channel = pygame.mixer.Channel(self.channel_id)
                        channel.stop()
                        self.sound = new_sound
                        if was_playing:
                            channel.play(new_sound, loops=loops)
                else:
                    # Use original sound for normal speed
                    if self.sound != self.original_sound:
                        was_playing = self.is_playing()
                        was_paused = self.is_paused()
                        
                        if was_playing or was_paused:
                            channel = pygame.mixer.Channel(self.channel_id)
                            channel.stop()
                            self.sound = self.original_sound
                            
                            if was_playing:
                                loops = -1 if self.loop else 0
                                channel.play(self.original_sound, loops=loops)
                                channel.set_volume(self.volume)
                
                self._trigger_event(AudioEvent.SPEED_CHANGE)
                
            except Exception as e:
                print(f"Error adjusting speed: {e}")
                
    
    def _smooth_speed_transition(self, start: float, end: float, duration: float):
        """Smoothly transition between speeds."""
        self.state = AudioState.SPEED_CHANGING
        self._trigger_event(AudioEvent.SPEED_CHANGE_START)
        
        steps = int(duration * 30)  # 30 updates per second
        step_duration = duration / steps
        
        for step in range(steps):
            if self._stop_threads.is_set():
                break
                
            progress = step / steps
            eased_progress = 1 - (1 - progress) * (1 - progress)  # easeOutQuad
            current_speed = start + (end - start) * eased_progress
            
            self.speed = current_speed
            time.sleep(step_duration)
        
        if not self._stop_threads.is_set():
            self.speed = end
        
        self.state = AudioState.PLAYING if self.is_playing() else self.state
        self._trigger_event(AudioEvent.SPEED_CHANGE_COMPLETE)    
    
    def _transition_speed(self, target_speed: float, duration: float) -> None:
        """
        Smoothly transition between speeds.
        
        Args:
            target_speed (float): Target speed multiplier
            duration (float): Transition duration in seconds
        """
        self._stop_threads.set()
        time.sleep(0.01)
        self._stop_threads.clear()
        
        self.target_speed = target_speed
        self._speed_thread = threading.Thread(
            target=self._smooth_speed_change,
            args=(self.speed, target_speed, duration)
        )
        self._speed_thread.daemon = True
        self._speed_thread.start()
    
    def _smooth_speed_change(self, start_speed: float, end_speed: float, duration: float) -> None:
        """
        Smoothly change speed over time.
        
        Args:
            start_speed (float): Starting speed
            end_speed (float): Target speed
            duration (float): Transition duration in seconds
        """
        self.state = AudioState.SPEED_CHANGING
        self._trigger_event(AudioEvent.SPEED_CHANGE_START)
        
        steps = max(1, int(duration * 30))  # 30 updates per second for smooth transition
        step_duration = duration / steps
        speed_step = (end_speed - start_speed) / steps
        
        current_speed = start_speed
        
        for step in range(steps):
            if self._stop_threads.is_set():
                break
                
            # Use easing for smooth transition
            progress = step / steps
            # Quadratic ease out
            eased_progress = 1 - (1 - progress) * (1 - progress)
            current_speed = start_speed + (end_speed - start_speed) * eased_progress
            
            # Apply speed change
            self._change_speed_immediate(current_speed)
            time.sleep(step_duration)
        
        if not self._stop_threads.is_set():
            # Ensure final speed is set
            self._change_speed_immediate(end_speed)
        
        self.state = AudioState.PLAYING if self.is_playing() else self.state
        self._trigger_event(AudioEvent.SPEED_CHANGE_COMPLETE)
    
    def _transition_volume(self, start_volume: float, end_volume: float, duration: float) -> None:
        """
        Enhanced volume transition with better state management.
        
        Args:
            start_volume (float): Starting volume
            end_volume (float): Ending volume
            duration (float): Transition duration in seconds
        """
        self.state = AudioState.VOLUME_CHANGING
        
        steps = max(1, int(duration * 60))  # 60 updates per second
        step_duration = duration / steps
        
        for step in range(steps + 1):  # +1 to ensure we reach the target
            if self._stop_threads.is_set():
                break
                
            # Calculate progress with easing
            progress = step / steps
            # Cubic ease in-out for smoother transitions
            if progress < 0.5:
                eased_progress = 4 * progress * progress * progress
            else:
                eased_progress = 1 - math.pow(-2 * progress + 2, 3) / 2
                
            current_volume = start_volume + (end_volume - start_volume) * eased_progress
            
            # Update volume
            self.volume = current_volume
            channel = pygame.mixer.Channel(self.channel_id)
            channel.set_volume(self.volume)
            
            time.sleep(step_duration)
        
        if not self._stop_threads.is_set():
            # Ensure final volume is set
            self.volume = end_volume
            channel = pygame.mixer.Channel(self.channel_id)
            channel.set_volume(self.volume)
        
        self.state = AudioState.PLAYING if self.is_playing() else self.state
        self._trigger_event(AudioEvent.VOLUME_CHANGE)
    
    def fade_in(self, duration: float, target_volume: float = 1.0) -> None:
        """
        Enhanced fade in with better state management.
        
        Args:
            duration (float): Fade duration in seconds
            target_volume (float, optional): Target volume. Defaults to 1.0.
        """
        self._stop_threads.clear()
        self.set_volume(0.0)  # Start from silence
        self._fade_thread = threading.Thread(
            target=self._transition_volume,
            args=(0.0, target_volume, duration)
        )
        self._fade_thread.daemon = True
        self._fade_thread.start()
    
    def fade_out(self, duration: float) -> None:
        """
        Enhanced fade out with better state management.
        
        Args:
            duration (float): Fade duration in seconds
        """
        self._stop_threads.clear()
        self._fade_thread = threading.Thread(
            target=self._fade_volume_out,
            args=(self.volume, 0.0, duration)
        )
        self._fade_thread.daemon = True
        self._fade_thread.start()
    
    def _fade_volume_out(self, start_volume: float, end_volume: float, duration: float) -> None:
        """
        Special fade out that stops playback after completion.
        
        Args:
            start_volume (float): Starting volume
            end_volume (float): Ending volume
            duration (float): Fade duration in seconds
        """
        self.state = AudioState.FADING_OUT
        self._trigger_event(AudioEvent.FADE_START)
        
        self._transition_volume(start_volume, end_volume, duration)
        
        if not self._stop_threads.is_set():
            self.stop()
        
        self._trigger_event(AudioEvent.FADE_COMPLETE)
    
    # Rest of the methods remain largely the same but with improved error handling
    def stop(self) -> None:
        """Enhanced stop with thread management."""
        self._stop_threads.set()
        channel = pygame.mixer.Channel(self.channel_id)
        channel.stop()
        self.state = AudioState.STOPPED
        self._trigger_event(AudioEvent.STOP)
    
    def is_playing(self) -> bool:
        """
        Enhanced play state check.
        
        Returns:
            bool: True if playing, False otherwise
        """
        channel = pygame.mixer.Channel(self.channel_id)
        return channel.get_busy() and self.state in [AudioState.PLAYING, AudioState.FADING_IN, AudioState.FADING_OUT, AudioState.SPEED_CHANGING, AudioState.VOLUME_CHANGING]
    
    def is_paused(self) -> bool:
        """
        Enhanced pause state check.
        
        Returns:
            bool: True if paused, False otherwise
        """
        return self.state == AudioState.PAUSED
    
    # Event handling methods remain the same
    def on_event(self, event_type: AudioEvent) -> Callable:
        """Decorator to register event handlers."""
        def decorator(func: Callable) -> Callable:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(func)
            return func
        return decorator
    
    def _trigger_event(self, event_type: AudioEvent) -> None:
        """Trigger all handlers for the given event type."""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(self)
                except Exception as e:
                    print(f"Error in audio channel event handler: {e}")

# Enhanced SoundEffect class with duration support
class SoundEffect:
    """
    Enhanced sound effect with duration information.
    """
    
    def __init__(self, sound: pygame.mixer.Sound):
        """
        Initialize a sound effect with duration tracking.
        
        Args:
            sound (pygame.mixer.Sound): The sound object
        """
        self.sound = sound
        self.channels: List[AudioChannel] = []
        self._duration = self._calculate_duration(sound)
    
    def _calculate_duration(self, sound: pygame.mixer.Sound) -> float:
        """
        Calculate sound duration.
        
        Args:
            sound (pygame.mixer.Sound): Sound to calculate duration for
            
        Returns:
            float: Duration in seconds
        """
        try:
            return sound.get_length()
        except AttributeError:
            # Fallback for sounds without get_length method
            return getattr(sound, '_length', 0.0) / 1000.0
    
    def get_duration(self) -> float:
        """
        Get the duration of this sound effect.
        
        Returns:
            float: Duration in seconds
        """
        return self._duration
    
    def play(self, audio_system: 'AudioSystem', 
             volume: float = 1.0, speed: float = 1.0, 
             loop: bool = False) -> Optional[AudioChannel]:
        """
        Play the sound effect on an available channel.
        
        Args:
            audio_system (AudioSystem): The audio system to get channels from
            volume (float, optional): Volume level. Defaults to 1.0.
            speed (float, optional): Playback speed. Defaults to 1.0.
            loop (bool, optional): Whether to loop. Defaults to False.
            
        Returns:
            Optional[AudioChannel]: The channel playing the sound, or None if failed
        """
        channel = audio_system.get_available_channel()
        if channel:
            if channel.play(self.sound, loop):
                channel.set_volume(volume)
                channel.set_speed(speed)
                self.channels.append(channel)
                
                # Remove channel from list when it stops
                @channel.on_event(AudioEvent.STOP)
                def on_channel_stop(ch):
                    if ch in self.channels:
                        self.channels.remove(ch)
                
                return channel
        return None
    
    def stop_all(self) -> None:
        """Stop all instances of this sound effect."""
        for channel in self.channels[:]:
            channel.stop()
        self.channels.clear()
        
class AudioSystem:
    """
    Advanced audio system with multi-channel support and real speed control.
    
    Attributes:
        music_volume (float): Global music volume
        sfx_volume (float): Global sound effects volume
        channels (List[AudioChannel]): All available audio channels
        sound_effects (Dict[str, SoundEffect]): Loaded sound effects
        music_channel (AudioChannel): Dedicated music channel
    """
    
    def __init__(self, num_channels: int = 16):
        """
        Initialize the advanced audio system.
        
        Args:
            num_channels (int, optional): Number of audio channels. Defaults to 16.
        """
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        
        # Ensure we have enough channels
        current_channels = pygame.mixer.get_num_channels()
        if current_channels < num_channels:
            pygame.mixer.set_num_channels(num_channels)
        
        # Create channel objects
        self.channels: List[AudioChannel] = []
        for i in range(num_channels):
            self.channels.append(AudioChannel(i))
        
        # Dedicated music channel (usually channel 0)
        self.music_channel = self.channels[0]
        
        self.sound_effects: Dict[str, SoundEffect] = {}
        self.music_tracks: Dict[str, str] = {}  # Store file paths for music
    
    def get_available_channel(self) -> Optional[AudioChannel]:
        """
        Get an available audio channel.
        
        Returns:
            Optional[AudioChannel]: Available channel, or None if all busy
        """
        for channel in self.channels[1:]:  # Skip music channel
            if not channel.is_playing() and not channel.is_paused():
                return channel
        return None
    
    def load_sound_effect(self, name: str, file_path: str) -> bool:
        """
        Load a sound effect from file.
        
        Args:
            name (str): Unique name for the sound effect
            file_path (str): Path to the sound file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            if not os.path.exists(file_path):
                print(f"Sound file not found: {file_path}")
                return False
            
            sound = pygame.mixer.Sound(file_path)
            self.sound_effects[name] = SoundEffect(sound)
            return True
            
        except Exception as e:
            print(f"Error loading sound effect {name}: {e}")
            return False
    
    def load_music(self, name: str, file_path: str) -> bool:
        """
        Load a music track (store path for later use).
        
        Args:
            name (str): Unique name for the music track
            file_path (str): Path to the music file
            
        Returns:
            bool: True if file exists
        """
        if os.path.exists(file_path):
            self.music_tracks[name] = file_path
            return True
        else:
            print(f"Music file not found: {file_path}")
            return False
    
    def play_sound(self, name: str, volume: float = None, 
                  speed: float = 1.0, loop: bool = False) -> Optional[AudioChannel]:
        """
        Play a sound effect on an available channel.
        
        Args:
            name (str): Name of the sound effect
            volume (float, optional): Volume level. Uses SFX volume if None.
            speed (float, optional): Playback speed. Defaults to 1.0.
            loop (bool, optional): Whether to loop. Defaults to False.
            
        Returns:
            Optional[AudioChannel]: The channel playing the sound
        """
        if name in self.sound_effects:
            if volume is None:
                volume = self.sfx_volume
            
            return self.sound_effects[name].play(
                self, volume, speed, loop
            )
        else:
            print(f"Sound effect not found: {name}")
            return None
    
    def play_music(self, name: str, volume: float = None,
                  speed: float = 1.0, loop: bool = True) -> bool:
        """
        Play a music track on the dedicated music channel.
        
        Args:
            name (str): Name of the music track
            volume (float, optional): Volume level. Uses music volume if None.
            speed (float, optional): Playback speed. Defaults to 1.0.
            loop (bool, optional): Whether to loop. Defaults to True.
            
        Returns:
            bool: True if playback started successfully
        """
        if name in self.music_tracks:
            try:
                if volume is None:
                    volume = self.music_volume
                
                sound = pygame.mixer.Sound(self.music_tracks[name])
                if self.music_channel.play(sound, loop):
                    self.music_channel.set_volume(volume)
                    self.music_channel.set_speed(speed)
                    return True
                    
            except Exception as e:
                print(f"Error playing music {name}: {e}")
        
        else:
            print(f"Music track not found: {name}")
        
        return False
    
    def stop_music(self) -> None:
        """Stop the currently playing music."""
        self.music_channel.stop()
    
    def pause_music(self) -> None:
        """Pause the currently playing music."""
        self.music_channel.pause()
    
    def resume_music(self) -> None:
        """Resume the paused music."""
        self.music_channel.resume()
    
    def set_music_volume(self, volume: float) -> None:
        """
        Set global music volume.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        self.music_channel.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume: float) -> None:
        """
        Set global sound effects volume.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        # Note: Individual sound effects maintain their own volume ratios
    
    def fade_in_music(self, name: str, duration: float = 2.0,
                     target_volume: float = None, speed: float = 1.0) -> bool:
        """
        Fade in a music track.
        
        Args:
            name (str): Name of the music track
            duration (float, optional): Fade duration. Defaults to 2.0.
            target_volume (float, optional): Target volume. Uses music volume if None.
            speed (float, optional): Playback speed. Defaults to 1.0.
            
        Returns:
            bool: True if fade started successfully
        """
        if target_volume is None:
            target_volume = self.music_volume
        
        if self.play_music(name, 0.0, speed):  # Start at volume 0
            self.music_channel.fade_in(duration, target_volume)
            return True
        return False
    
    def fade_out_music(self, duration: float = 2.0) -> None:
        """
        Fade out the current music.
        
        Args:
            duration (float, optional): Fade duration. Defaults to 2.0.
        """
        self.music_channel.fade_out(duration)
    
    def stop_all_sounds(self) -> None:
        """Stop all playing sound effects."""
        for sound_effect in self.sound_effects.values():
            sound_effect.stop_all()
    
    def get_channel_info(self) -> Dict[str, Any]:
        """
        Get information about all channels.
        
        Returns:
            Dict[str, Any]: Channel information
        """
        info = {
            'total_channels': len(self.channels),
            'busy_channels': 0,
            'channels': []
        }
        
        for channel in self.channels:
            channel_info = {
                'id': channel.channel_id,
                'state': channel.state.value,
                'volume': channel.volume,
                'speed': channel.speed,
                'playing': channel.is_playing(),
                'paused': channel.is_paused()
            }
            info['channels'].append(channel_info)
            
            if channel.is_playing() or channel.is_paused():
                info['busy_channels'] += 1
        
        return info
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        self.stop_music()
        self.stop_all_sounds()
        pygame.mixer.quit()
    
    def get_sound_duration(self, name: str) -> float:
        """
        Get the duration of a loaded sound effect.
        
        Args:
            name (str): Name of the sound effect
            
        Returns:
            float: Duration in seconds, or 0.0 if not found
        """
        if name in self.sound_effects:
            return self.sound_effects[name].get_duration()
        return 0.0
    
    def get_music_duration(self, name: str) -> float:
        """
        Get the duration of a loaded music track.
        
        Args:
            name (str): Name of the music track
            
        Returns:
            float: Duration in seconds, or 0.0 if not found
        """
        if name in self.music_tracks:
            try:
                sound = pygame.mixer.Sound(self.music_tracks[name])
                return sound.get_length()
            except:
                pass
        return 0.0
    
    def get_current_music_position(self) -> float:
        """
        Get current playback position of music.
        
        Returns:
            float: Current position in seconds
        """
        return self.music_channel.get_playback_position()