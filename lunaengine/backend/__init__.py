"""Backend module for LunaEngine

LOCATION: lunaengine/backend/__init__.py

DESCRIPTION:
Initialization file for the backend module. This module provides rendering 
backends and graphics system implementations for the LunaEngine.

MODULES PROVIDED:
- opengl: OpenGL-based renderer for hardware-accelerated graphics (instanced particles)
- openal: OpenAL-based audio system
- types: Common types and event definitions
- network: Networking components for client-server architecture (experimental)

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
    OpenALAudioSystem,
    OpenALAudioEvent,
    OpenALSource,
    OpenALBuffer,
    OpenALError,
)
from .types import (
    EVENTS,
    InputState,
    MouseButtonPressed,
    LayerType,
    WindowEventData,
    WindowEventType,
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
    # Controllers
    "Controller",
    "ControllerManager",
    "ControllerState",
    "ControllerType",
    "ConnectionType",
    "TouchPoint",
    "JButton",
    "Axis",
    # Networking
    "NetworkHost",
    "NetworkServer",
    "NetworkClient",
    "NetworkMessage",
    "UserType",
    "generate_id",
    # OpenAL audio
    "OpenALAudioSystem",
    "OpenALAudioEvent",
    "OpenALSource",
    "OpenALBuffer",
    "OpenALError",
    # Exceptions and GL utilities
    "LExceptions",
    "glEnable",
    "glDisable",
    "GL_DEPTH_TEST",
]