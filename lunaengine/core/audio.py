"""
Audio Manager for LunaEngine - Named channels, curves, device selection, event system
"""

import os
import time
import threading
import math
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from enum import Enum, auto

# Import OpenAL backend
from ..backend.openal import (
    OpenALBackend,
    OpenALSource,
    OpenALBuffer,
    OpenALDevice,
    OPENAL_AVAILABLE,
    EFX_AVAILABLE,
    al,
)

# Pygame fallback
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: PyGame not available, audio loading may be limited.")


class AudioEvent(Enum):
    """
    Audio events emitted by the audio system or channels.
    """
    PLAYBACK_STARTED = auto()
    PLAYBACK_STOPPED = auto()
    PLAYBACK_PAUSED = auto()
    PLAYBACK_RESUMED = auto()
    PLAYBACK_COMPLETED = auto()   # non-looping sound finished
    FADE_COMPLETE = auto()
    LOOP = auto()
    CURVE_FINISHED = auto()
    ERROR = auto()


class AudioState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class SoundData:
    """Metadata and buffer reference for a loaded sound."""
    def __init__(self, name: str, filepath: str, category: str = "sfx"):
        self.name = name
        self.filepath = filepath
        self.category = category
        self.duration = 0.0
        self.ref_count = 0
        self.loaded_time = time.time()
        self._buffer = None   # OpenALBuffer, lazy-loaded

    def get_buffer(self, backend: OpenALBackend) -> Optional[OpenALBuffer]:
        """Get or create the OpenAL buffer for this sound."""
        if self._buffer is None:
            self._buffer = OpenALBuffer.get_or_create(self.filepath, backend.device)
            if self._buffer:
                self.duration = self._buffer.duration
        return self._buffer


class AudioCurve:
    """
    Keyframe-based animation for a single audio property (volume, pitch, pan, balance).
    """
    def __init__(self, property_name: str, keyframes: List[Tuple[float, float]],
                 interpolation: str = 'linear', loop: bool = False):
        """
        Args:
            property_name: 'volume', 'pitch', 'pan', or 'balance'
            keyframes: list of (time, value) pairs, time in seconds.
            interpolation: 'linear' or 'smoothstep'
            loop: if True, restart animation when finished.
        """
        self.property = property_name
        self.keyframes = sorted(keyframes, key=lambda x: x[0])
        self.interpolation = interpolation
        self.loop = loop
        self.duration = self.keyframes[-1][0] if self.keyframes else 0.0
        self.elapsed = 0.0
        self.active = False
        self._finished_callback = None
        self._channel = None  # set by channel when applied

    def evaluate(self, t: float) -> float:
        """Return interpolated value at time t (0..duration)."""
        if not self.keyframes:
            return 0.0
        if t <= self.keyframes[0][0]:
            return self.keyframes[0][1]
        if t >= self.keyframes[-1][0]:
            return self.keyframes[-1][1]
        for i in range(len(self.keyframes) - 1):
            t0, v0 = self.keyframes[i]
            t1, v1 = self.keyframes[i + 1]
            if t0 <= t <= t1:
                frac = (t - t0) / (t1 - t0)
                if self.interpolation == 'linear':
                    return v0 + (v1 - v0) * frac
                elif self.interpolation == 'smoothstep':
                    frac = frac * frac * (3 - 2 * frac)
                    return v0 + (v1 - v0) * frac
                # add more easing here if desired
        return self.keyframes[-1][1]

    def update(self, dt: float) -> bool:
        """Advance animation; returns True if finished (and not looping)."""
        if not self.active:
            return True
        self.elapsed += dt
        if self.elapsed >= self.duration:
            if self.loop:
                self.elapsed = self.elapsed % self.duration
            else:
                self.active = False
                if self._finished_callback:
                    self._finished_callback()
                return True
        return False

    def on_finished(self, callback: Callable):
        self._finished_callback = callback


class AudioChannel:
    """
    Named audio channel with individual volume, pitch, pan, balance, and curves.
    Now supports effects: reverb, echo (via effect slot if EFX available).
    """
    def __init__(self, name: str, manager: 'AudioManager',
                 volume: float = 1.0, pitch: float = 1.0, pan: float = 0.0,
                 balance: float = 0.0, loop: bool = False):
        self.name = name
        self.manager = manager
        self.volume = volume
        self.pitch = pitch
        self.pan = pan
        self.balance = balance
        self.loop = loop
        self.state = AudioState.STOPPED
        self.current_sound: Optional[str] = None
        self.source: Optional[OpenALSource] = None
        self._curves: List[AudioCurve] = []
        self._lock = threading.RLock()
        self._event_handlers: Dict[AudioEvent, List[Callable]] = {e: [] for e in AudioEvent}
        # Effects
        self.reverb_amount = 0.0
        self.echo_amount = 0.0
        self.chorus_amount = 0.0
        self.flanger_amount = 0.0
        self.distortion_amount = 0.0
        self.pitch_shift = 0.0  # semitones? We'll use a multiplier later
        self._effect_applied = False

    def _get_source(self) -> Optional[OpenALSource]:
        """Get a free OpenAL source, reusing the current one if still playing."""
        if self.source is None or not self.source.is_playing():
            self.source = self.manager.backend.get_free_source()
        return self.source

    def _emit_event(self, event: AudioEvent, **kwargs):
        for cb in self._event_handlers.get(event, []):
            try:
                cb(self, **kwargs)
            except Exception as e:
                print(f"Error in event handler for {event}: {e}")

    def on_event(self, event: AudioEvent, callback: Callable):
        """Register a callback for a specific event."""
        self._event_handlers[event].append(callback)

    def _apply_effects(self):
        """Apply all active effects to the source if EFX available."""
        if not EFX_AVAILABLE or not self.source:
            return

        # Determine which effect to apply (priority: reverb > echo > chorus > flanger > distortion > pitch shift)
        # We can only apply one effect slot per source, so we choose the most significant.
        # For simplicity, we'll apply reverb if any reverb, else echo, etc.
        effect_type = None
        params = {}

        if self.reverb_amount > 0.01:
            effect_type = al.AL_EFFECT_REVERB
            params = {
                al.AL_REVERB_GAIN: 0.1 + self.reverb_amount * 0.9,
                al.AL_REVERB_DECAY_TIME: 0.5 + self.reverb_amount * 2.0,
                al.AL_REVERB_DENSITY: 0.3 + self.reverb_amount * 0.6,
            }
        elif self.echo_amount > 0.01:
            effect_type = al.AL_EFFECT_ECHO
            params = {
                # Echo parameters (approximate)
                # We need to map echo_amount to some meaningful params
                # These constants may not be defined; we'll use a generic approach
            }
        elif self.chorus_amount > 0.01:
            effect_type = al.AL_EFFECT_CHORUS
            params = {
                # Chorus params
            }
        elif self.flanger_amount > 0.01:
            effect_type = al.AL_EFFECT_FLANGER
            params = {
                # Flanger params
            }
        elif self.distortion_amount > 0.01:
            effect_type = al.AL_EFFECT_DISTORTION
            params = {
                # Distortion params
            }

        if effect_type is not None:
            self.source.set_effect(effect_type, params)
            self._effect_applied = True
        else:
            if self._effect_applied:
                self.source.remove_effect()
                self._effect_applied = False

    # ---- Effect setters ----
    def set_reverb(self, amount: float):
        self.reverb_amount = max(0.0, min(1.0, amount))
        self._apply_effects()

    def set_echo(self, amount: float):
        self.echo_amount = max(0.0, min(1.0, amount))
        self._apply_effects()

    def set_chorus(self, amount: float):
        self.chorus_amount = max(0.0, min(1.0, amount))
        self._apply_effects()

    def set_flanger(self, amount: float):
        self.flanger_amount = max(0.0, min(1.0, amount))
        self._apply_effects()

    def set_distortion(self, amount: float):
        self.distortion_amount = max(0.0, min(1.0, amount))
        self._apply_effects()

    def set_pitch_shift(self, semitones: float):
        """Shift pitch by semitones (positive = higher pitch)."""
        # Convert semitones to pitch multiplier: 2^(semitones/12)
        self.pitch_shift = semitones
        if self.source:
            multiplier = 2.0 ** (semitones / 12.0)
            self.source.set_pitch_immediate(max(0.1, min(4.0, multiplier)))

    def play(self, sound_name: str, loop: bool = False, fade_in: float = 0.0,
             curve: Optional[AudioCurve] = None) -> bool:
        """
        Play a sound on this channel.
        Returns True if playback started successfully.
        """
        with self._lock:
            self.stop()
            sound = self.manager.sounds.get(sound_name)
            if not sound:
                print(f"Sound '{sound_name}' not loaded")
                return False
            source = self._get_source()
            if not source:
                print("No free audio source")
                return False
            buf = sound.get_buffer(self.manager.backend)
            if not buf:
                return False

            source.set_buffer(buf)
            # Apply master volume
            master_vol = self.manager.master_volume
            initial_vol = 0.0 if fade_in > 0 else self.volume * master_vol
            source.set_volume_immediate(initial_vol)
            # Apply pitch shift if any
            if self.pitch_shift != 0.0:
                multiplier = 2.0 ** (self.pitch_shift / 12.0)
                source.set_pitch_immediate(max(0.1, min(4.0, multiplier * self.pitch)))
            else:
                source.set_pitch_immediate(self.pitch)
            source.set_balance_immediate(self.balance)
            source.set_pan_immediate(self.pan)
            source.play(loop)
            self.source = source
            self.current_sound = sound_name
            self.state = AudioState.PLAYING
            sound.ref_count += 1

            self._emit_event(AudioEvent.PLAYBACK_STARTED, sound=sound_name)

            if fade_in > 0:
                # Create a curve from 0 to self.volume * master_vol
                target_vol = self.volume * master_vol
                curve_vol = AudioCurve('volume', [(0.0, 0.0), (fade_in, target_vol)], 'smoothstep')
                self.apply_curve(curve_vol)

            if curve:
                self.apply_curve(curve)

            # Apply effects
            self._apply_effects()

            return True

    def stop(self):
        with self._lock:
            if self.source:
                self.source.stop()
                self.source = None
            if self.state != AudioState.STOPPED:
                self._emit_event(AudioEvent.PLAYBACK_STOPPED, sound=self.current_sound)
            self.state = AudioState.STOPPED
            if self.current_sound:
                sound = self.manager.sounds.get(self.current_sound)
                if sound:
                    sound.ref_count = max(0, sound.ref_count - 1)
                self.current_sound = None
            self._curves.clear()
            self._effect_applied = False

    def pause(self):
        if self.source and self.state == AudioState.PLAYING:
            self.source.pause()
            self.state = AudioState.PAUSED
            self._emit_event(AudioEvent.PLAYBACK_PAUSED)

    def resume(self):
        if self.source and self.state == AudioState.PAUSED:
            self.source.resume()
            self.state = AudioState.PLAYING
            self._emit_event(AudioEvent.PLAYBACK_RESUMED)

    def set_volume(self, volume: float, duration: float = 0.0, curve_type: str = 'linear'):
        """Set target volume, optionally with a smooth transition."""
        self.volume = max(0.0, min(1.0, volume))
        master_vol = self.manager.master_volume
        target = self.volume * master_vol
        if duration > 0:
            current = self.source.volume if self.source else target
            curve = AudioCurve('volume', [(0.0, current), (duration, target)], curve_type)
            self.apply_curve(curve)
        else:
            if self.source:
                self.source.set_volume_immediate(target)

    def set_pitch(self, pitch: float, duration: float = 0.0, curve_type: str = 'linear'):
        self.pitch = max(0.1, min(4.0, pitch))
        if duration > 0:
            current = self.source.pitch if self.source else self.pitch
            curve = AudioCurve('pitch', [(0.0, current), (duration, self.pitch)], curve_type)
            self.apply_curve(curve)
        else:
            if self.source:
                self.source.set_pitch_immediate(self.pitch)

    def set_balance(self, balance: float, duration: float = 0.0, curve_type: str = 'linear'):
        self.balance = max(-1.0, min(1.0, balance))
        if duration > 0:
            current = self.source.balance if self.source else self.balance
            curve = AudioCurve('balance', [(0.0, current), (duration, self.balance)], curve_type)
            self.apply_curve(curve)
        else:
            if self.source:
                self.source.set_balance_immediate(self.balance)

    def set_pan(self, pan: float, duration: float = 0.0, curve_type: str = 'linear'):
        self.pan = max(-1.0, min(1.0, pan))
        if duration > 0:
            current = self.source.pan if self.source else self.pan
            curve = AudioCurve('pan', [(0.0, current), (duration, self.pan)], curve_type)
            self.apply_curve(curve)
        else:
            if self.source:
                self.source.set_pan_immediate(self.pan)

    def apply_curve(self, curve: AudioCurve):
        """Apply a curve to this channel."""
        curve.active = True
        curve.elapsed = 0.0
        curve._channel = self
        with self._lock:
            self._curves.append(curve)

    def update(self, dt: float):
        """Update active curves and emit completion events."""
        with self._lock:
            for curve in self._curves[:]:
                if curve.update(dt):
                    self._curves.remove(curve)
                    self._emit_event(AudioEvent.CURVE_FINISHED, curve=curve)
                else:
                    # Apply current value to source
                    val = curve.evaluate(curve.elapsed)
                    if curve.property == 'volume':
                        if self.source:
                            self.source.set_volume_immediate(val)
                    elif curve.property == 'pitch':
                        if self.source:
                            self.source.set_pitch_immediate(val)
                    elif curve.property == 'balance':
                        if self.source:
                            self.source.set_balance_immediate(val)
                    elif curve.property == 'pan':
                        if self.source:
                            self.source.set_pan_immediate(val)

            # Check if sound finished (non-looping)
            if self.state == AudioState.PLAYING and self.source and not self.source.is_playing():
                # Sound stopped naturally
                self.state = AudioState.STOPPED
                self._emit_event(AudioEvent.PLAYBACK_COMPLETED, sound=self.current_sound)
                # Decrement ref count
                if self.current_sound:
                    sound = self.manager.sounds.get(self.current_sound)
                    if sound:
                        sound.ref_count = max(0, sound.ref_count - 1)
                    self.current_sound = None
                self.source = None

    def is_playing(self) -> bool:
        return self.source is not None and self.source.is_playing()

    def is_paused(self) -> bool:
        return self.source is not None and self.source.is_paused()

    def get_position(self) -> float:
        return self.source.get_position() if self.source else 0.0


class AudioManager:
    """
    Main audio manager with named channels, curves, device selection, and event system.
    Now includes master volume control and global effect toggles.
    """
    def __init__(self, max_sources: int = 32, device_name: Optional[str] = None):
        self.backend = OpenALBackend(max_sources, device_name)
        self.sounds: Dict[str, SoundData] = {}
        self.channels: Dict[str, AudioChannel] = {}
        self.default_channel = 'default'
        self.master_volume = 1.0  # master volume multiplier
        # Create default channel and music channel
        self.create_channel('default')
        self.create_channel('music', volume=0.8, loop=True)
        self._event_handlers: Dict[AudioEvent, List[Callable]] = {e: [] for e in AudioEvent}

    def _emit_event(self, event: AudioEvent, **kwargs):
        for cb in self._event_handlers.get(event, []):
            try:
                cb(self, **kwargs)
            except Exception as e:
                print(f"Error in global event handler {event}: {e}")

    def on_event(self, event: AudioEvent, callback: Callable):
        """Register a global audio event handler."""
        self._event_handlers[event].append(callback)

    def set_master_volume(self, volume: float):
        """Set master volume (0.0 - 1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
        # Update all channels' source volumes
        for ch in self.channels.values():
            if ch.source and ch.state == AudioState.PLAYING:
                # Adjust to new master volume
                target = ch.volume * self.master_volume
                ch.source.set_volume_immediate(target)

    # ---- Global effect setters ----
    def set_global_reverb(self, amount: float):
        for ch in self.channels.values():
            ch.set_reverb(amount)

    def set_global_echo(self, amount: float):
        for ch in self.channels.values():
            ch.set_echo(amount)

    def set_global_chorus(self, amount: float):
        for ch in self.channels.values():
            ch.set_chorus(amount)

    def set_global_flanger(self, amount: float):
        for ch in self.channels.values():
            ch.set_flanger(amount)

    def set_global_distortion(self, amount: float):
        for ch in self.channels.values():
            ch.set_distortion(amount)

    def set_global_pitch_shift(self, semitones: float):
        for ch in self.channels.values():
            ch.set_pitch_shift(semitones)

    # ---- Device and sound management ----
    def list_devices(self) -> List[str]:
        return OpenALDevice.list_devices()

    def set_device(self, device_name: str) -> bool:
        if not device_name:
            return False
        self.stop_all()
        self.backend.cleanup()
        new_backend = OpenALBackend(self.backend.max_sources, device_name)
        if new_backend.is_initialized():
            self.backend = new_backend
            for ch in self.channels.values():
                ch.source = None
                ch.state = AudioState.STOPPED
            return True
        else:
            self.backend = OpenALBackend(self.backend.max_sources)
            return False

    def create_channel(self, name: str, **kwargs) -> AudioChannel:
        if name in self.channels:
            raise ValueError(f"Channel '{name}' already exists")
        channel = AudioChannel(name, self, **kwargs)
        self.channels[name] = channel
        return channel

    def get_channel(self, name: str) -> Optional[AudioChannel]:
        return self.channels.get(name)

    def load_sound(self, name: str, filepath: str, category: str = "sfx",
                   force_mono: bool = False, force_8bit: bool = False) -> bool:
        if name in self.sounds:
            return True
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")
        sound = SoundData(name, filepath, category)
        if self.backend.is_initialized():
            buf = OpenALBuffer.get_or_create(filepath, self.backend.device,
                                             force_mono=force_mono, force_8bit=force_8bit)
            if buf:
                sound.duration = buf.duration
            else:
                print(f"Warning: Could not load '{filepath}'")
                return False
        self.sounds[name] = sound
        return True

    def play(self, sound_name: str, channel: Optional[Union[str, int]] = None,
             volume: float = 1.0, pitch: float = 1.0, pan: float = 0.0,
             balance: float = 0.0, loop: bool = False,
             fade_in: float = 0.0, curve: Optional[AudioCurve] = None,
             reverb: float = 0.0, echo: float = 0.0,
             chorus: float = 0.0, flanger: float = 0.0,
             distortion: float = 0.0, pitch_shift: float = 0.0) -> Optional[AudioChannel]:
        if sound_name not in self.sounds:
            print(f"Sound '{sound_name}' not loaded")
            return None
        if channel is None:
            ch_name = self.default_channel
        elif isinstance(channel, str):
            ch_name = channel
        else:
            ch_name = self.default_channel
        ch = self.channels.get(ch_name)
        if not ch:
            ch = self.create_channel(ch_name)
        ch.volume = volume
        ch.pitch = pitch
        ch.pan = pan
        ch.balance = balance
        ch.loop = loop
        ch.set_reverb(reverb)
        ch.set_echo(echo)
        ch.set_chorus(chorus)
        ch.set_flanger(flanger)
        ch.set_distortion(distortion)
        ch.set_pitch_shift(pitch_shift)
        if ch.play(sound_name, loop, fade_in, curve):
            self._emit_event(AudioEvent.PLAYBACK_STARTED, channel=ch, sound=sound_name)
            return ch
        return None

    def play_music(self, sound_name: str, volume: float = 0.8, pitch: float = 1.0,
                   loop: bool = True, fade_in: float = 0.0,
                   curve: Optional[AudioCurve] = None,
                   reverb: float = 0.0, echo: float = 0.0,
                   chorus: float = 0.0, flanger: float = 0.0,
                   distortion: float = 0.0, pitch_shift: float = 0.0) -> Optional[AudioChannel]:
        return self.play(sound_name, channel='music', volume=volume, pitch=pitch,
                         loop=loop, fade_in=fade_in, curve=curve,
                         reverb=reverb, echo=echo,
                         chorus=chorus, flanger=flanger,
                         distortion=distortion, pitch_shift=pitch_shift)

    def stop_all(self):
        for ch in self.channels.values():
            ch.stop()

    def update(self, dt: float):
        for ch in self.channels.values():
            ch.update(dt)
        OpenALBuffer.cleanup_unused()

    def cleanup(self):
        self.stop_all()
        self.backend.cleanup()
        self.sounds.clear()
        self.channels.clear()