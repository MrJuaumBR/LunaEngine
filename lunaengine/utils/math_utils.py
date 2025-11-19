"""
Math Utilities - Essential Mathematical Functions for Game Development

LOCATION: lunaengine/utils/math_utils.py

DESCRIPTION:
Collection of fundamental mathematical functions commonly used in game
development. Provides optimized implementations for interpolation,
clamping, distance calculations, and vector operations.

KEY FUNCTIONS:
- lerp: Linear interpolation for smooth transitions
- clamp: Value constraint within specified ranges
- distance: Euclidean distance between points
- normalize_vector: Vector normalization for movement calculations
- angle_between_points: Angle calculation for directional systems

LIBRARIES USED:
- math: Core mathematical operations and trigonometric functions
- numpy: High-performance numerical operations (optional)
- typing: Type annotations for coordinates and return values

USAGE:
>>> smoothed_value = lerp(start, end, 0.5)
>>> constrained_value = clamp(value, 0, 100)
>>> dist = distance((x1, y1), (x2, y2))
>>> direction = normalize_vector(dx, dy)
>>> angle = angle_between_points(point_a, point_b)
"""
import math
import numpy as np
from typing import Tuple

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b"""
    return a + (b - a) * t

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))

def distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate distance between two points"""
    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def normalize_vector(x: float, y: float) -> Tuple[float, float]:
    """Normalize a 2D vector"""
    length = math.sqrt(x*x + y*y)
    if length > 0:
        return (x/length, y/length)
    return (0, 0)

def angle_between_points(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """Calculate angle between two points in radians"""
    return math.atan2(point2[1] - point1[1], point2[0] - point1[0])

def rgba_brightness(rgba: Tuple[int, int, int, float]) -> float:
    if len(rgba) >= 4:
        r,g,b,a = rgba
    elif len(rgba) == 3:
        r,g,b = rgba
        a = 1.0
    else:
        print("Invalid RGBA format. Expected (r, g, b, a) or (r, g, b)")
        return 0.0
    return ((r/255 + g/255 + b/255)/3) * a

def individual_rgba_brightness(rgba: Tuple[int, int, int, float]) -> Tuple[float, float, float, float]:
    if len(rgba) >= 4:
        r,g,b,a = rgba
    elif len(rgba) == 3:
        r,g,b = rgba
        a = 1.0
    else:
        print("Invalid RGBA format. Expected (r, g, b, a) or (r, g, b)")
        return (0.0, 0.0, 0.0, 0.0)
    return (r/255, g/255, b/255, a)