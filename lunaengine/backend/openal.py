"""
OpenAL Audio Backend for LunaEngine - Cross-platform (Linux/Windows)
Supports device selection, stereo balance, and immediate property changes.
Now includes optional stereo→mono conversion for panning support.
EFX extension support for reverb and effects.
Extended to load audio from bytes (bundle support).
"""

import ctypes
import os
import time
import wave
import io
import threading
import math
from typing import Dict, List, Optional, Tuple, Any, Callable

# Try to import OpenAL
try:
    from openal import al, alc, ALuint, ALint, ALfloat
    OPENAL_AVAILABLE = True
except ImportError:
    OPENAL_AVAILABLE = False
    print("Warning: PyOpenAL not installed. Using pygame fallback.")
    class DummyOpenAL:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    al = DummyOpenAL()
    alc = DummyOpenAL()
    ALuint = int
    ALint = int
    ALfloat = float

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: PyGame not installed. Audio loading limited.")

# Check for EFX extension (reverb, etc.)
EFX_AVAILABLE = False
try:
    # Attempt to access EFX constants and functions
    if OPENAL_AVAILABLE:
        # Try to get EFX function pointers
        # We'll assume that if alGenEffects exists, EFX is available
        if hasattr(al, 'alGenEffects'):
            EFX_AVAILABLE = True
        else:
            # On some platforms, EFX functions are available via alcGetProcAddress
            # We'll try to load them dynamically
            # For simplicity, we'll just check if we can call alGenEffects
            pass
except:
    EFX_AVAILABLE = False

# Define EFX constants if not available in openal module
if not hasattr(al, 'AL_EFFECT_REVERB'):
    # These are standard EFX constants
    al.AL_EFFECT_REVERB = 0x0001
    al.AL_EFFECT_ECHO = 0x0002
    al.AL_EFFECT_DISTORTION = 0x0003
    al.AL_EFFECT_CHORUS = 0x0004
    al.AL_EFFECT_FLANGER = 0x0005
    al.AL_EFFECT_FREQUENCY_SHIFTER = 0x0006
    al.AL_EFFECT_VOCAL_MORPHER = 0x0007
    al.AL_EFFECT_PITCH_SHIFTER = 0x0008
    al.AL_EFFECT_RING_MODULATOR = 0x0009
    al.AL_EFFECT_AUTOWAH = 0x000A
    al.AL_EFFECT_COMPRESSOR = 0x000B
    al.AL_EFFECT_EQUALIZER = 0x000C

# Reverb parameters
if not hasattr(al, 'AL_REVERB_DENSITY'):
    al.AL_REVERB_DENSITY = 0x0001
    al.AL_REVERB_DIFFUSION = 0x0002
    al.AL_REVERB_GAIN = 0x0003
    al.AL_REVERB_GAINHF = 0x0004
    al.AL_REVERB_DECAY_TIME = 0x0005
    al.AL_REVERB_DECAY_HFRATIO = 0x0006
    al.AL_REVERB_REFLECTIONS_GAIN = 0x0007
    al.AL_REVERB_REFLECTIONS_DELAY = 0x0008
    al.AL_REVERB_LATE_REVERB_GAIN = 0x0009
    al.AL_REVERB_LATE_REVERB_DELAY = 0x000A
    al.AL_REVERB_AIR_ABSORPTION_GAINHF = 0x000B
    al.AL_REVERB_ROOM_ROLLOFF_FACTOR = 0x000C
    al.AL_REVERB_DECAY_HFLIMIT = 0x000D

# Effect slot constants
if not hasattr(al, 'AL_EFFECTSLOT_EFFECT'):
    al.AL_EFFECTSLOT_EFFECT = 0x0001
    al.AL_EFFECTSLOT_GAIN = 0x0002
    al.AL_EFFECTSLOT_AUXILIARY_SEND = 0x0003


class OpenALError(Exception):
    pass


class OpenALDevice:
    _instance = None

    def __new__(cls, device_name: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, device_name: Optional[str] = None):
        if self._initialized:
            return
        self.device_name = device_name
        self.device = None
        self.context = None
        self._initialized = False
        self._init(device_name)

    def _init(self, device_name: Optional[str] = None):
        if not OPENAL_AVAILABLE:
            return
        try:
            if device_name:
                self.device = alc.alcOpenDevice(device_name.encode())
            else:
                self.device = alc.alcOpenDevice(None)
            if not self.device:
                raise OpenALError("Failed to open OpenAL device")
            self.context = alc.alcCreateContext(self.device, None)
            if not self.context:
                alc.alcCloseDevice(self.device)
                raise OpenALError("Failed to create OpenAL context")
            alc.alcMakeContextCurrent(self.context)
            self._initialized = True
            print(f"OpenAL device initialized: {device_name or 'default'}")
        except Exception as e:
            print(f"OpenAL init error: {e}")
            self._initialized = False

    @staticmethod
    def list_devices() -> List[str]:
        if not OPENAL_AVAILABLE:
            return []
        try:
            default = alc.alcGetString(None, alc.ALC_DEFAULT_DEVICE_SPECIFIER)
            devices = alc.alcGetString(None, alc.ALC_DEVICE_SPECIFIER)
            if devices:
                dev_list = [d for d in devices.split('\0') if d]
                if default and default not in dev_list:
                    dev_list.insert(0, default)
                return dev_list
            else:
                return [default] if default else []
        except:
            return ["default"]

    def close(self):
        if self._initialized:
            if self.context:
                alc.alcMakeContextCurrent(None)
                alc.alcDestroyContext(self.context)
                self.context = None
            if self.device:
                alc.alcCloseDevice(self.device)
                self.device = None
            self._initialized = False

    def is_initialized(self) -> bool:
        return self._initialized


class OpenALBuffer:
    _buffer_pool: Dict[str, 'OpenALBuffer'] = {}

    @classmethod
    def get_or_create(cls, filepath: str, device: OpenALDevice, force_mono: bool = False, force_8bit: bool = False) -> Optional['OpenALBuffer']:
        """
        Load a sound from a file path. Uses a cache.
        """
        if not OPENAL_AVAILABLE or not device.is_initialized():
            return None
        filepath = os.path.abspath(filepath)
        if filepath in cls._buffer_pool:
            buf = cls._buffer_pool[filepath]
            buf.last_used = time.time()
            return buf
        try:
            buffer_id = ALuint(0)
            al.alGenBuffers(1, ctypes.byref(buffer_id))
            if not cls._load_audio_file(buffer_id, filepath, force_mono, force_8bit):
                al.alDeleteBuffers(1, ctypes.byref(buffer_id))
                return None
            buffer_obj = OpenALBuffer(buffer_id.value)
            buffer_obj._update_info()
            cls._buffer_pool[filepath] = buffer_obj
            return buffer_obj
        except Exception as e:
            print(f"Buffer creation failed: {e}")
            return None

    @classmethod
    def from_bytes(cls, data: bytes, name: str, device: OpenALDevice,
                   force_mono: bool = False, force_8bit: bool = False) -> Optional['OpenALBuffer']:
        """
        Create a buffer from raw bytes (useful for bundle loading).
        'name' is used for caching (e.g., the atlas name).
        """
        if not OPENAL_AVAILABLE or not device.is_initialized():
            return None
        # Use a special cache key to avoid collisions with file paths
        cache_key = f"bytes:{name}"
        if cache_key in cls._buffer_pool:
            buf = cls._buffer_pool[cache_key]
            buf.last_used = time.time()
            return buf
        try:
            buffer_id = ALuint(0)
            al.alGenBuffers(1, ctypes.byref(buffer_id))
            if not cls._load_audio_from_bytes(buffer_id, data, force_mono, force_8bit):
                al.alDeleteBuffers(1, ctypes.byref(buffer_id))
                return None
            buffer_obj = OpenALBuffer(buffer_id.value)
            buffer_obj._update_info()
            cls._buffer_pool[cache_key] = buffer_obj
            return buffer_obj
        except Exception as e:
            print(f"Buffer creation from bytes failed: {e}")
            return None

    def __init__(self, buffer_id: int):
        self.buffer_id = buffer_id
        self.duration = 0.0
        self.frequency = 0
        self.channels = 0
        self.bits = 0
        self.size = 0
        self.last_used = time.time()

    def _update_info(self):
        if not OPENAL_AVAILABLE:
            return
        try:
            buf = ALuint(self.buffer_id)
            self.size = ALint(0)
            al.alGetBufferi(buf, al.AL_SIZE, ctypes.byref(self.size))
            self.bits = ALint(0)
            al.alGetBufferi(buf, al.AL_BITS, ctypes.byref(self.bits))
            self.channels = ALint(0)
            al.alGetBufferi(buf, al.AL_CHANNELS, ctypes.byref(self.channels))
            self.frequency = ALint(0)
            al.alGetBufferi(buf, al.AL_FREQUENCY, ctypes.byref(self.frequency))
            if self.frequency.value > 0:
                bytes_per_sample = self.bits.value // 8
                total_samples = self.size.value // (bytes_per_sample * max(1, self.channels.value))
                self.duration = total_samples / self.frequency.value
        except Exception:
            pass

    @staticmethod
    def _load_audio_file(buffer_id: ALuint, filepath: str, force_mono: bool, force_8bit: bool) -> bool:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.wav':
            return OpenALBuffer._load_wav(buffer_id, filepath, force_mono, force_8bit)
        elif PYGAME_AVAILABLE:
            return OpenALBuffer._load_with_pygame(buffer_id, filepath, force_mono, force_8bit)
        else:
            print(f"Unsupported format: {ext}")
            return False

    @staticmethod
    def _load_wav(buffer_id: ALuint, filepath: str, force_mono: bool, force_8bit: bool) -> bool:
        try:
            with wave.open(filepath, 'rb') as wf:
                nch = wf.getnchannels()
                sw = wf.getsampwidth()
                fr = wf.getframerate()
                data = wf.readframes(wf.getnframes())
                # Convert to mono if requested and stereo
                if force_mono and nch == 2:
                    data = OpenALBuffer._convert_stereo_to_mono(data, sw)
                    nch = 1
                # Convert to 8-bit if requested
                if force_8bit and sw == 2:
                    data = OpenALBuffer._convert_16bit_to_8bit(data)
                    sw = 1
                if nch == 1:
                    fmt = al.AL_FORMAT_MONO16 if sw == 2 else al.AL_FORMAT_MONO8
                elif nch == 2:
                    fmt = al.AL_FORMAT_STEREO16 if sw == 2 else al.AL_FORMAT_STEREO8
                else:
                    return False
                al.alBufferData(buffer_id, fmt, data, len(data), fr)
                return True
        except Exception as e:
            print(f"WAV load error: {e}")
            return False

    @staticmethod
    def _load_audio_from_bytes(buffer_id: ALuint, data: bytes, force_mono: bool, force_8bit: bool) -> bool:
        """
        Load audio from raw bytes. Attempts to detect format.
        Currently supports WAV only (using wave.open on BytesIO).
        """
        try:
            with wave.open(io.BytesIO(data), 'rb') as wf:
                nch = wf.getnchannels()
                sw = wf.getsampwidth()
                fr = wf.getframerate()
                audio_data = wf.readframes(wf.getnframes())
                if force_mono and nch == 2:
                    audio_data = OpenALBuffer._convert_stereo_to_mono(audio_data, sw)
                    nch = 1
                if force_8bit and sw == 2:
                    audio_data = OpenALBuffer._convert_16bit_to_8bit(audio_data)
                    sw = 1
                if nch == 1:
                    fmt = al.AL_FORMAT_MONO16 if sw == 2 else al.AL_FORMAT_MONO8
                elif nch == 2:
                    fmt = al.AL_FORMAT_STEREO16 if sw == 2 else al.AL_FORMAT_STEREO8
                else:
                    return False
                al.alBufferData(buffer_id, fmt, audio_data, len(audio_data), fr)
                return True
        except Exception as e:
            print(f"Bytes audio load error: {e}")
            # Fallback to pygame if available (for other formats like OGG, MP3)
            if PYGAME_AVAILABLE:
                try:
                    # We can't load from bytes directly with pygame.mixer.Sound? Actually we can: Sound(buffer=...)
                    # but we need to convert to a file-like? Let's use a temporary file.
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as tmp:
                        tmp.write(data)
                        tmp_path = tmp.name
                    try:
                        return OpenALBuffer._load_with_pygame(buffer_id, tmp_path, force_mono, force_8bit)
                    finally:
                        os.unlink(tmp_path)
                except Exception as e2:
                    print(f"Pygame fallback for bytes failed: {e2}")
            return False

    @staticmethod
    def _load_with_pygame(buffer_id: ALuint, filepath: str, force_mono: bool, force_8bit: bool) -> bool:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            sound = pygame.mixer.Sound(filepath)
            raw = sound.get_raw()
            freq = 44100
            if sound.get_length() > 0:
                # Guess frequency
                samples = len(raw) // (2 * 2)  # assume stereo 16-bit
                freq = int(samples / sound.get_length())
            # We don't know channels here; we assume stereo.
            nch = 2
            sw = 2
            if force_mono:
                raw = OpenALBuffer._convert_stereo_to_mono(raw, 2)
                nch = 1
            if force_8bit and sw == 2:
                raw = OpenALBuffer._convert_16bit_to_8bit(raw)
                sw = 1
            if nch == 1:
                fmt = al.AL_FORMAT_MONO16 if sw == 2 else al.AL_FORMAT_MONO8
            else:
                fmt = al.AL_FORMAT_STEREO16 if sw == 2 else al.AL_FORMAT_STEREO8
            al.alBufferData(buffer_id, fmt, raw, len(raw), freq)
            return True
        except Exception as e:
            print(f"Pygame load error: {e}")
            return False

    @staticmethod
    def _convert_stereo_to_mono(data: bytes, sample_width: int) -> bytes:
        """Convert 2-channel PCM to mono by averaging samples."""
        if sample_width == 2:
            import array
            samples = array.array('h', data)
            frames = len(samples) // 2
            mono = array.array('h')
            for i in range(frames):
                left = samples[i*2]
                right = samples[i*2 + 1]
                mono.append((left + right) // 2)
            return mono.tobytes()
        else:
            # 8-bit
            import array
            samples = array.array('b', data)
            frames = len(samples) // 2
            mono = array.array('b')
            for i in range(frames):
                left = samples[i*2]
                right = samples[i*2 + 1]
                mono.append((left + right) // 2)
            return mono.tobytes()

    @staticmethod
    def _convert_16bit_to_8bit(data: bytes) -> bytes:
        """Convert 16-bit PCM to 8-bit (linear)."""
        import array
        samples = array.array('h', data)
        # Convert to signed 8-bit: divide by 256 and offset to unsigned? We'll use signed 8-bit.
        eight = array.array('b')
        for s in samples:
            # clamp
            val = s // 256
            if val > 127:
                val = 127
            elif val < -128:
                val = -128
            eight.append(val)
        return eight.tobytes()

    @classmethod
    def cleanup_unused(cls, max_age: float = 300.0):
        now = time.time()
        to_remove = [p for p, b in cls._buffer_pool.items() if now - b.last_used > max_age]
        for p in to_remove:
            buf = cls._buffer_pool.pop(p)
            if OPENAL_AVAILABLE:
                al.alDeleteBuffers(1, ctypes.byref(ALuint(buf.buffer_id)))


class OpenALSource:
    def __init__(self, source_id: int):
        self.source_id = source_id
        self.buffer = None
        self.volume = 1.0
        self.pitch = 1.0
        self.pan = 0.0
        self.balance = 0.0
        self.loop = False
        # Effect slot for reverb/echo (if EFX available)
        self.effect_slot = None
        if OPENAL_AVAILABLE:
            al.alSourcei(source_id, al.AL_SOURCE_RELATIVE, al.AL_TRUE)
            al.alSource3f(source_id, al.AL_POSITION, 0.0, 0.0, 0.0)
            al.alSourcef(source_id, al.AL_ROLLOFF_FACTOR, 0.0)

    def set_buffer(self, buffer: OpenALBuffer):
        self.buffer = buffer
        if OPENAL_AVAILABLE and buffer:
            al.alSourcei(self.source_id, al.AL_BUFFER, buffer.buffer_id)

    def set_volume_immediate(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        if OPENAL_AVAILABLE:
            al.alSourcef(self.source_id, al.AL_GAIN, self.volume)

    def set_balance_immediate(self, balance: float):
        self.balance = max(-1.0, min(1.0, balance))
        if OPENAL_AVAILABLE:
            al.alSource3f(self.source_id, al.AL_POSITION, self.balance, 0.0, 0.0)

    def set_pan_immediate(self, pan: float):
        self.pan = max(-1.0, min(1.0, pan))
        self.set_balance_immediate(self.pan)

    def set_pitch_immediate(self, pitch: float):
        self.pitch = max(0.1, min(4.0, pitch))
        if OPENAL_AVAILABLE:
            al.alSourcef(self.source_id, al.AL_PITCH, self.pitch)

    def set_effect(self, effect_type: int, params: Optional[Dict[str, float]] = None) -> bool:
        """
        Apply an EFX effect (reverb, echo, etc.) to this source.
        Returns True if successful.
        Requires EFX_AVAILABLE.
        """
        if not EFX_AVAILABLE or not OPENAL_AVAILABLE:
            return False
        try:
            # Create effect
            effect = ALuint(0)
            al.alGenEffects(1, ctypes.byref(effect))
            if effect.value == 0:
                return False
            # Set effect type
            al.alEffecti(effect, al.AL_EFFECT_TYPE, effect_type)
            # Apply parameters (if any)
            if params:
                for key, val in params.items():
                    al.alEffectf(effect, key, val)
            # Create effect slot
            slot = ALuint(0)
            al.alGenAuxiliaryEffectSlots(1, ctypes.byref(slot))
            if slot.value == 0:
                al.alDeleteEffects(1, ctypes.byref(effect))
                return False
            al.alAuxiliaryEffectSloti(slot, al.AL_EFFECTSLOT_EFFECT, effect)
            # Attach to source
            al.alSource3i(self.source_id, al.AL_AUXILIARY_SEND_FILTER, slot, 0, 0)
            self.effect_slot = slot
            return True
        except Exception:
            return False

    def remove_effect(self):
        """Remove any attached effect."""
        if self.effect_slot and OPENAL_AVAILABLE:
            try:
                al.alSource3i(self.source_id, al.AL_AUXILIARY_SEND_FILTER, 0, 0, 0)
                al.alDeleteAuxiliaryEffectSlots(1, ctypes.byref(ALuint(self.effect_slot)))
            except:
                pass
            self.effect_slot = None

    def play(self, loop: bool = False):
        self.loop = loop
        if OPENAL_AVAILABLE:
            al.alSourcei(self.source_id, al.AL_LOOPING, al.AL_TRUE if loop else al.AL_FALSE)
            al.alSourcePlay(self.source_id)

    def pause(self):
        if OPENAL_AVAILABLE:
            al.alSourcePause(self.source_id)

    def resume(self):
        if OPENAL_AVAILABLE:
            al.alSourcePlay(self.source_id)

    def stop(self):
        if OPENAL_AVAILABLE:
            al.alSourceStop(self.source_id)
            self.remove_effect()

    def rewind(self):
        if OPENAL_AVAILABLE:
            al.alSourceRewind(self.source_id)

    def is_playing(self) -> bool:
        if not OPENAL_AVAILABLE:
            return False
        state = ALint(0)
        al.alGetSourcei(self.source_id, al.AL_SOURCE_STATE, ctypes.byref(state))
        return state.value == al.AL_PLAYING

    def is_paused(self) -> bool:
        if not OPENAL_AVAILABLE:
            return False
        state = ALint(0)
        al.alGetSourcei(self.source_id, al.AL_SOURCE_STATE, ctypes.byref(state))
        return state.value == al.AL_PAUSED

    def get_position(self) -> float:
        if not OPENAL_AVAILABLE:
            return 0.0
        offset = ALfloat(0.0)
        al.alGetSourcef(self.source_id, al.AL_SEC_OFFSET, ctypes.byref(offset))
        return offset.value

    def delete(self):
        self.remove_effect()
        if OPENAL_AVAILABLE:
            al.alDeleteSources(1, ctypes.byref(ALuint(self.source_id)))


class OpenALBackend:
    def __init__(self, max_sources: int = 32, device_name: Optional[str] = None):
        self.device = OpenALDevice(device_name)
        self.sources: List[OpenALSource] = []
        self.max_sources = max_sources
        if self.device.is_initialized():
            if OPENAL_AVAILABLE:
                al.alListener3f(al.AL_POSITION, 0.0, 0.0, 0.0)
                al.alListener3f(al.AL_VELOCITY, 0.0, 0.0, 0.0)
                orientation = (ALfloat * 6)(0.0, 0.0, -1.0, 0.0, 1.0, 0.0)
                al.alListenerfv(al.AL_ORIENTATION, orientation)
            for _ in range(max_sources):
                sid = ALuint(0)
                al.alGenSources(1, ctypes.byref(sid))
                self.sources.append(OpenALSource(sid.value))

    def get_free_source(self) -> Optional[OpenALSource]:
        for src in self.sources:
            if not src.is_playing() and not src.is_paused():
                return src
        return None

    def cleanup(self):
        for src in self.sources:
            src.stop()
            src.delete()
        self.device.close()

    def is_initialized(self) -> bool:
        return self.device.is_initialized()