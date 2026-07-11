"""Backend module for LunaEngine

LOCATION: lunaengine/backend/__init__.py

DESCRIPTION:
Initialization file for the backend module. This module provides rendering 
backends, audio systems, input handling, and networking for the LunaEngine.

MODULES PROVIDED:
- opengl: OpenGL-based renderer for hardware-accelerated graphics (instanced particles)
- openal: OpenAL-based audio system with EFX support (reverb, echo, etc.)
- types: Common types and event definitions
- network: Networking components for client-server architecture (experimental)
- controller: Game controller support with hot-plug, gyro, touchpad

LIBRARIES USED:
- pygame: Core graphics and window management
- OpenGL: 3D graphics rendering (optional)
- OpenAL: Audio system (optional)
- numpy: Numerical operations for graphics math
"""

from .opengl import (
    OpenGLRenderer,
    Filter,
    FilterType,
    FilterRegionType,
)
from .openal import (
    # Core OpenAL classes
    OpenALDevice,
    OpenALBackend,
    OpenALSource,
    OpenALBuffer,
    OpenALError,
    # EFX support flag
    EFX_AVAILABLE,
    # Low-level OpenAL bindings (for advanced use)
    al,
    alc,
    ALuint,
    ALint,
    ALfloat,
)
# Legacy alias for compatibility (old name points to new backend)
from .openal import OpenALBackend as OpenALAudioSystem

from .types import (
    EVENTS,
    InputState,
    MouseButtonPressed,
    LayerType,
    WindowEventData,
    WindowEventType,
    Ratio,
    Color,
)
from .network import (
    NetworkHost,
    NetworkServer,
    NetworkClient,
    NetworkMessage,
    UserType,
    generate_id,
)
from .controller import (
    Controller,
    ControllerManager,
    ControllerState,
    ControllerType,
    ConnectionType,
    TouchPoint,
    JButton,
    Axis,
    FocusOrder,
    sort_elements_for_focus,
)
from . import exceptions as LExceptions
from OpenGL.GL import glEnable, glDisable, GL_DEPTH_TEST

__all__ = [
    # OpenGL renderer and related classes
    "OpenGLRenderer",
    "Filter",
    "FilterType",
    "FilterRegionType",
    # Input and events
    "InputState",
    "MouseButtonPressed",
    "EVENTS",
    "LayerType",
    "WindowEventData",
    "WindowEventType",
    "Ratio",
    "Color",
    # Controllers
    "Controller",
    "ControllerManager",
    "ControllerState",
    "ControllerType",
    "ConnectionType",
    "TouchPoint",
    "JButton",
    "Axis",
    "FocusOrder",
    "sort_elements_for_focus",
    # Networking
    "NetworkHost",
    "NetworkServer",
    "NetworkClient",
    "NetworkMessage",
    "UserType",
    "generate_id",
    # OpenAL audio
    "OpenALDevice",
    "OpenALBackend",
    "OpenALSource",
    "OpenALBuffer",
    "OpenALError",
    "EFX_AVAILABLE",
    "al",
    "alc",
    "ALuint",
    "ALint",
    "ALfloat",
    # Legacy alias
    "OpenALAudioSystem",
    # Exceptions and GL utilities
    "LExceptions",
    "glEnable",
    "glDisable",
    "GL_DEPTH_TEST",
]