"""
Utilities Module - Core Utility Functions and Systems for LunaEngine

LOCATION: lunaengine/utils/__init__.py

DESCRIPTION:
Initialization file for the utilities module. This module provides essential
utility functions, performance monitoring, threading systems, and helper
classes that support the core functionality of LunaEngine.

MODULES PROVIDED:
- image_converter: Image embedding and conversion utilities
- math_utils: Mathematical helper functions and calculations
- performance: Performance monitoring and optimization systems
- threading: Thread pool management and task execution
- timer: Timer management and callback scheduling

LIBRARIES USED:
- pygame: Image processing and surface operations
- numpy: Mathematical calculations and array operations
- threading: Concurrent task execution
- psutil: System performance monitoring (optional)
- base64/zlib: Data encoding and compression

This module provides the foundational utilities that enable efficient
game development, performance optimization, and resource management.
"""

from .image_converter import ImageConverter, EmbeddedImage
from .performance import PerformanceMonitor, GarbageCollector
from .math_utils import (clamp, lerp, normalize_vector, angle_between_points,
                         distance, rgba_brightness, individual_rgba_brightness, get_rgba_common,
                         humanize_number, humanize_time, humanize_size, generate_matrix)
from .timer import Timer, TimeCounter, get_global_timer

__all__ = [
    "ImageConverter",
    "EmbeddedImage",
    "PerformanceMonitor",
    "GarbageCollector",
    "clamp",
    "lerp",
    "normalize_vector",
    "angle_between_points",
    "distance",
    "rgba_brightness",
    "individual_rgba_brightness",
    "get_rgba_common",
    "humanize_number",
    "humanize_time",
    "humanize_size",
    "generate_matrix",
    "Timer",
    "TimeCounter", 
    "get_global_timer"
]