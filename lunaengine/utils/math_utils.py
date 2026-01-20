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
    """
    This function is used to calculate the overall brightness of an RGBA color
    
    Parameters:
        rgba (Tuple[int, int, int, float]): A tuple representing the RGBA color
    Returns:
        float: A float representing the brightness of the color
    """
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
    """
    This function is used to calculate the individual brightness of each color channel (R, G, B, A)
    
    Parameters:
        rgba (Tuple[int, int, int, float]): A tuple representing the RGBA color
    Returns:
        Tuple[float, float, float, float]: A tuple representing the normalized RGBA values
    """
    if len(rgba) >= 4:
        r,g,b,a = rgba
    elif len(rgba) == 3:
        r,g,b = rgba
        a = 1.0
    else:
        print("Invalid RGBA format. Expected (r, g, b, a) or (r, g, b)")
        return (0.0, 0.0, 0.0, 0.0)
    return (r/255, g/255, b/255, a)

def get_rgba_common(color1:Tuple[int,int,int,float]|Tuple[int,int,int], color2:Tuple[int,int,int,float]|Tuple[int,int,int]) -> Tuple[int,int,int,float]:
    """
    This function is used to get the common RGBA values between two colors
    
    Parameters:
        color1 (Tuple[int, int, int, float]): A tuple representing the first RGBA color
        color2 (Tuple[int, int, int, float]): A tuple representing the second RGBA color
    Returns:
        Tuple[int, int, int, float]: A tuple representing the common RGBA values
    """
    if len(color1) >= 4:
        r1,g1,b1,a1 = color1
    elif len(color1) == 3:
        r1,g1,b1 = color1
        a1 = 1.0
    else:
        print("Invalid RGBA(color1) format. Expected (r, g, b, a) or (r, g, b)")
        return (0, 0, 0, 0.0)
    
    if len(color2) >= 4:
        r2,g2,b2,a2 = color2
    elif len(color2) == 3:
        r2,g2,b2 = color2
        a2 = 1.0
    else:
        print("Invalid RGBA(color2) format. Expected (r, g, b, a) or (r, g, b)")
        return (0, 0, 0, 0.0)
    
    # Calculate common RGBA values
    r = r1/255 * r2/255 * 255
    g = g1/255 * g2/255 * 255
    b = b1/255 * b2/255 * 255
    a = a1 * a2
    
    # Clamps values
    r = int(clamp(r, 0, 255))
    g = int(clamp(g, 0, 255))
    b = int(clamp(b, 0, 255))
    a = clamp(a, 0.0, 1.0)
    
    return (r, g, b, a)

def humanize_number(number: float, decimal_places: int=2) -> str:
    """
    This function is used to format a number into a human-readable string
    Like: 1K, 1M, 1B, etc.
    Also: 1.5K, 2.34M, etc.
    Parameters:
        number (float): A float representing the number to be formatted
        decimal_places (int): Number of decimal places to include
    Returns:
        str: A string representing the formatted number
    """
    
    
    suffixes = ['', 'K', 'M', 'B', 'T', 'Qa', 'Qi', 'Sx', 'Sp', 'Oc', 'No', 'Dc']
    index = 0
    while abs(number) >= 1000 and index < len(suffixes) - 1:
        index += 1
        number /= 1000.0
    return f"{number:.{decimal_places}f}{suffixes[index]}"

def humanize_time(seconds: float) -> str:
    """
    This function is used to format a time duration in seconds into a human-readable string
    Like: 1h 30m, 2d 5h, etc.
    
    Parameters:
        seconds (float): A float representing the time duration in seconds
    Returns:
        str: A string representing the formatted time duration
    """
    
    intervals = (
        ('y', 31536000),  # 60 * 60 * 24 * 365
        ('d', 86400),     # 60 * 60 * 24
        ('h', 3600),      # 60 * 60
        ('m', 60),
        ('s', 1),
    )
    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            result.append(f"{int(value)}{name}")
    return ' '.join(result) if result else '0s'

def humanize_size(size:float) -> str:
    """
    This function will convert sizes in bytes to a human-readable format
    Parameters:
        size (float): A float representing the size in bytes
    Returns:
        str: A string representing the human-readable size
    """
    intervals = (
        'B',
        'KB',
        'MB',
        'GB',
        'TB',
        'PB',
        'EB',
        'ZB',
        'YB'
    )
    
    i = 0
    while size >= 1024:
        size /= 1024
        i += 1
    return f"{size:.2f} {intervals[i]}"

def generate_matrix(rows, cols, dtype=np.float32) -> np.ndarray:
    """
    Generate matrix of zeros
    Parameters:
        rows (int): Number of rows in the matrix
        cols (int): Number of columns in the matrix
        dtype (np.dtype): Data type of the matrix
    Returns:
        np.ndarray: Matrix of zeros
    """
    
    return np.full((rows, cols), 0.0, dtype=dtype)