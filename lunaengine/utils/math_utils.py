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