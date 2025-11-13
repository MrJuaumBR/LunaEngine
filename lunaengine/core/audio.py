"""
Advanced Audio System - Multi-Channel Audio with Real Speed Control

LOCATION: lunaengine/core/audio.py

DESCRIPTION:
Advanced audio system with individual channel control, real speed adjustment,
and enhanced effects. Uses pygame.mixer.Channel for precise control.

KEY FEATURES:
- Multi-channel audio management
- Real playback speed control using pitch shifting
- Individual volume per channel
- Advanced fade effects with custom curves
- Event system with detailed callbacks
- Music and SFX with separate channel groups
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

class AudioChannel:
    """
    Individual audio channel with full control.
    
    Attributes:
        channel_id (int): Pygame mixer channel number
        sound (pygame.mixer.Sound): The sound object
        volume (float): Current volume (0.0 to 1.0)
        speed (float): Playback speed multiplier
        loop (bool): Whether to loop the sound
        state (AudioState): Current playback state
    """
    
    def __init__(self, channel_id: int):
        """
        Initialize an audio channel.
        
        Args:
            channel_id (int): Pygame mixer channel number
        """
        self.channel_id = channel_id
        self.sound: Optional[pygame.mixer.Sound] = None
        self.volume = 1.0
        self.speed = 1.0
        self.loop = False
        self.state = AudioState.STOPPED
        self._event_handlers: Dict[AudioEvent, List[Callable]] = {}
        self._fade_thread: Optional[threading.Thread] = None
        self._stop_fade = threading.Event()
        
    def play(self, sound: pygame.mixer.Sound, loop: bool = False) -> bool:
        """
        Play a sound on this channel.
        
        Args:
            sound (pygame.mixer.Sound): Sound to play
            loop (bool, optional): Whether to loop. Defaults to False.
            
        Returns:
            bool: True if playback started successfully
        """
        try:
            self.sound = sound
            self.loop = loop
            self.volume = 1.0
            
            channel = pygame.mixer.Channel(self.channel_id)
            loops = -1 if loop else 0
            channel.play(sound, loops=loops)
            channel.set_volume(self.volume)
            
            self.state = AudioState.PLAYING
            return True
            
        except Exception as e:
            print(f"Error playing sound on channel {self.channel_id}: {e}")
            return False
    
    def stop(self) -> None:
        """Stop playback on this channel."""
        self._stop_fade.set()
        channel = pygame.mixer.Channel(self.channel_id)
        channel.stop()
        self.state = AudioState.STOPPED
        self._trigger_event(AudioEvent.STOP)
    
    def pause(self) -> None:
        """Pause playback on this channel."""
        if self.state == AudioState.PLAYING:
            channel = pygame.mixer.Channel(self.channel_id)
            channel.pause()
            self.state = AudioState.PAUSED
            self._trigger_event(AudioEvent.PAUSE)
    
    def resume(self) -> None:
        """Resume playback on this channel."""
        if self.state == AudioState.PAUSED:
            channel = pygame.mixer.Channel(self.channel_id)
            channel.unpause()
            self.state = AudioState.PLAYING
            self._trigger_event(AudioEvent.RESUME)
    
    def set_volume(self, volume: float) -> None:
        """
        Set channel volume.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        channel = pygame.mixer.Channel(self.channel_id)
        channel.set_volume(self.volume)
        self._trigger_event(AudioEvent.VOLUME_CHANGE)
    
    def set_speed(self, speed: float) -> None:
        """
        Set playback speed using pitch adjustment.
        
        Note: This is a simulated effect since pygame doesn't support native speed control.
        We adjust the playback rate by manipulating the sound buffer.
        
        Args:
            speed (float): Speed multiplier (0.5 for half speed, 2.0 for double)
        """
        self.speed = max(0.1, min(5.0, speed))
        
        if self.sound:
            try:
                # Get sound array
                array = pygame.sndarray.array(self.sound)
                
                # Resample based on speed (simplified approach)
                if self.speed != 1.0:
                    # This is a basic implementation - for real projects consider using libraries like pydub
                    length = int(len(array) / self.speed)
                    # Simple resampling (nearest neighbor)
                    indices = (np.arange(length) * self.speed).astype(int)
                    indices = np.clip(indices, 0, len(array) - 1)
                    resampled = array[indices]
                    
                    # Create new sound
                    new_sound = pygame.sndarray.make_sound(resampled)
                    
                    # Replace the sound if currently playing
                    if self.state == AudioState.PLAYING:
                        was_playing = True
                        self.stop()
                        self.play(new_sound, self.loop)
                    else:
                        self.sound = new_sound
                
                self._trigger_event(AudioEvent.SPEED_CHANGE)
                
            except Exception as e:
                print(f"Error adjusting speed: {e}")
                # Fallback: just change the speed value without actual effect
                pass
    
    def fade_in(self, duration: float, target_volume: float = 1.0) -> None:
        """
        Fade in the channel volume.
        
        Args:
            duration (float): Fade duration in seconds
            target_volume (float, optional): Target volume. Defaults to 1.0.
        """
        self._stop_fade.clear()
        self._fade_thread = threading.Thread(
            target=self._fade_volume,
            args=(0.0, target_volume, duration, AudioState.FADING_IN)
        )
        self._fade_thread.daemon = True
        self._fade_thread.start()
    
    def fade_out(self, duration: float) -> None:
        """
        Fade out the channel volume.
        
        Args:
            duration (float): Fade duration in seconds
        """
        self._stop_fade.clear()
        self._fade_thread = threading.Thread(
            target=self._fade_volume,
            args=(self.volume, 0.0, duration, AudioState.FADING_OUT)
        )
        self._fade_thread.daemon = True
        self._fade_thread.start()
    
    def _fade_volume(self, start_volume: float, end_volume: float, 
                    duration: float, fade_state: AudioState) -> None:
        """
        Internal method to handle volume fading.
        
        Args:
            start_volume (float): Starting volume
            end_volume (float): Ending volume
            duration (float): Fade duration in seconds
            fade_state (AudioState): Current fade state
        """
        self.state = fade_state
        self._trigger_event(AudioEvent.FADE_START)
        
        steps = int(duration * 60)  # 60 updates per second for smooth fade
        step_duration = duration / steps
        volume_step = (end_volume - start_volume) / steps
        
        current_volume = start_volume
        
        for step in range(steps):
            if self._stop_fade.is_set():
                break
                
            # Use easing function for smoother fade
            progress = step / steps
            # Cubic ease in-out
            eased_progress = 2 * progress * progress if progress < 0.5 else 1 - math.pow(-2 * progress + 2, 2) / 2
            current_volume = start_volume + (end_volume - start_volume) * eased_progress
            
            self.set_volume(current_volume)
            time.sleep(step_duration)
        
        if not self._stop_fade.is_set():
            self.set_volume(end_volume)
            if fade_state == AudioState.FADING_OUT:
                self.stop()
        
        self.state = AudioState.PLAYING if self.is_playing() else AudioState.STOPPED
        self._trigger_event(AudioEvent.FADE_COMPLETE)
    
    def is_playing(self) -> bool:
        """
        Check if the channel is playing.
        
        Returns:
            bool: True if playing, False otherwise
        """
        channel = pygame.mixer.Channel(self.channel_id)
        return channel.get_busy() and self.state == AudioState.PLAYING
    
    def is_paused(self) -> bool:
        """
        Check if the channel is paused.
        
        Returns:
            bool: True if paused, False otherwise
        """
        return self.state == AudioState.PAUSED
    
    def on_event(self, event_type: AudioEvent) -> Callable:
        """
        Decorator to register event handlers.
        
        Args:
            event_type (AudioEvent): The event type to listen for
            
        Returns:
            Callable: The decorator function
        """
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

class SoundEffect:
    """
    Sound effect that can be played on multiple channels simultaneously.
    
    Attributes:
        sound (pygame.mixer.Sound): The sound object
        channels (List[AudioChannel]): Channels currently playing this sound
    """
    
    def __init__(self, sound: pygame.mixer.Sound):
        """
        Initialize a sound effect.
        
        Args:
            sound (pygame.mixer.Sound): The sound object
        """
        self.sound = sound
        self.channels: List[AudioChannel] = []
    
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