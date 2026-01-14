"""Backend module for LunaEngine

LOCATION: lunaengine/backend/__init__.py

DESCRIPTION:
Initialization file for the backend module. This module provides rendering 
backends and graphics system implementations for the LunaEngine.

MODULES PROVIDED:
- opengl: OpenGL-based renderer for hardware-accelerated graphics
- pygame_backend: Pygame-based fallback renderer for compatibility
- types: Common types and event definitions
- network: Networking components for client-server architecture (experimental)

LIBRARIES USED:
- pygame: Core graphics and window management
- OpenGL: 3D graphics rendering (optional)
- numpy: Numerical operations for graphics math
"""

from .opengl import OpenGLRenderer, TextureShader, ParticleShader, ShaderProgram, Filter, FilterRegionType, FilterShader, FilterType
from .types import EVENTS, InputState, MouseButtonPressed, LayerType
from .network import NetworkEventType, NetworkEvent, HostClientMode, ConnectionQuality, NetworkMetrics, NetworkMessage, ClientInfo, ServerScript, PerformanceMonitor, RegionDetector, Server, NetworkClient, HostClient, NetworkDiscovery, NetworkMessages, get_local_ip, is_port_available, find_available_port

__all__ = [
    "OpenGLRenderer", "TextureShader", "ParticleShader", "ShaderProgram", "InputState", "MouseButtonPressed", "EVENTS", 'NetworkEventType', 'LayerType'
    'NetworkEvent', 'HostClientMode', 'ConnectionQuality', 'NetworkMetrics', 'NetworkMessage', 'ClientInfo', 'ServerScript', 'PerformanceMonitor', 'RegionDetector',
    'Server', 'NetworkClient', 'HostClient', 'NetworkDiscovery', 'NetworkMessages', 'get_local_ip', 'is_port_available', 'find_available_port',
    'Filter', 'FilterRegionType', 'FilterShader', 'FilterType'
]