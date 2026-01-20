"""Backend module for LunaEngine

LOCATION: lunaengine/backend/__init__.py

DESCRIPTION:
Initialization file for the backend module. This module provides rendering 
backends and graphics system implementations for the LunaEngine.

MODULES PROVIDED:
- opengl: OpenGL-based renderer for hardware-accelerated graphics
- openal: OpenAL-based audio system
- types: Common types and event definitions
- network: Networking components for client-server architecture (experimental)

LIBRARIES USED:
- pygame: Core graphics and window management
- OpenGL: 3D graphics rendering (optional)
- OpenAL: Audio system (optional)
- numpy: Numerical operations for graphics math
"""

from .opengl import OpenGLRenderer, TextureShader, ParticleShader, ShaderProgram, Filter, FilterRegionType, FilterShader, FilterType
from .openal import OpenALAudioSystem, OpenALAudioEvent, OpenALSource, OpenALBuffer, OpenALError
from .types import EVENTS, InputState, MouseButtonPressed, LayerType
from .network import NetworkHost, NetworkServer, NetworkClient, NetworkMessage, UserType, generate_id

__all__ = [
    "OpenGLRenderer", "TextureShader", "ParticleShader", "ShaderProgram", "InputState", "MouseButtonPressed", "EVENTS", "LayerType", 'PerformanceMonitor', 'RegionDetector',
    'Filter', 'FilterRegionType', 'FilterShader', 'FilterType',
    'NetworkHost', 'NetworkServer', 'NetworkClient', 'NetworkMessage', 'UserType', 'generate_id',
    'OpenALAudioSystem', 'OpenALAudioEvent', 'OpenALSource', 'OpenALBuffer', 'OpenALError'
]