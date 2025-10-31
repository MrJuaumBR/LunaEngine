"""
Image Converter - Embedded Image Management and Conversion System

LOCATION: lunaengine/utils/image_converter.py

DESCRIPTION:
Provides comprehensive image conversion and embedding capabilities for
including images directly in Python code. Supports multiple encoding
methods and allows games to be distributed as single files without
external image dependencies.

KEY FEATURES:
- Multiple encoding methods (pixel array, base64, compressed)
- Automatic image resizing with aspect ratio preservation
- Embedded image reconstruction without external dependencies
- Alpha channel support for transparent images
- Fallback mechanisms for robust error handling

LIBRARIES USED:
- pygame: Image loading, surface manipulation, and pixel operations
- base64: Data encoding for compact image storage
- zlib: Image compression for reduced code size
- numpy: Optional performance optimizations
- typing: Type hints for image parameters and return values

USAGE:
>>> converter = ImageConverter()
>>> python_code = converter.image_to_python_code("sprite.png", "sprite_data")
>>> embedded_image = EmbeddedImage(sprite_data)
>>> embedded_image.draw(renderer, 100, 100)
"""
import pygame, base64, zlib, os
import numpy as np
from typing import Tuple, List, Optional

class ImageConverter:
    """
    Converts images to Python code for embedding in games
    Uses Pygame for image loading - NO PILLOW REQUIRED
    """
    
    @staticmethod
    def image_to_python_code(image_path: str, 
                           output_var_name: str = "image_data",
                           max_size: Optional[Tuple[int, int]] = None,
                           method: str = "pixel_array") -> str:
        """
        Convert an image to Python code
        """
        try:
            # Load image with alpha channel preserved
            surface = pygame.image.load(image_path).convert_alpha()
            
            # Store original size for reference
            original_width, original_height = surface.get_size()
            
            # Resize if needed
            if max_size and (max_size[0] or max_size[1]):
                surface = ImageConverter._resize_surface(surface, max_size)
            
            width, height = surface.get_size()
            
            if method == "pixel_array":
                return ImageConverter._to_pixel_array(surface, width, height, output_var_name)
            elif method == "base64":
                return ImageConverter._to_base64(surface, width, height, output_var_name)
            elif method == "compressed":
                return ImageConverter._to_compressed(surface, width, height, output_var_name)
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            return f"# Error converting image: {e}"
    
    @staticmethod
    def _resize_surface(surface: pygame.Surface, max_size: Tuple[int, int]) -> pygame.Surface:
        """Resize surface while maintaining aspect ratio"""
        original_width, original_height = surface.get_size()
        max_width, max_height = max_size
        
        # Handle cases where only one dimension is specified
        if max_width == 0:
            max_width = original_width
        if max_height == 0:
            max_height = original_height
        
        # Calculate new dimensions maintaining aspect ratio
        ratio = min(max_width / original_width, max_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        return pygame.transform.smoothscale(surface, (new_width, new_height))
    
    @staticmethod
    def _to_pixel_array(surface: pygame.Surface, width: int, height: int, var_name: str) -> str:
        """Convert to Python pixel array code - FIXED COLOR BUG"""
        pixels = []
        
        # Extract pixel data - FIXED: Properly get all pixels
        for y in range(height):
            row = []
            for x in range(width):
                color = surface.get_at((x, y))
                # Store as (r, g, b, a) tuple
                row.append((color.r, color.g, color.b, color.a))
            pixels.append(row)
        
        # Generate Python code
        code = [
            f"{var_name} = {{",
            f"    'width': {width},",
            f"    'height': {height},",
            f"    'pixels': ["
        ]
        
        for y, row in enumerate(pixels):
            row_str = "        [" + ", ".join(f"({r}, {g}, {b}, {a})" for r, g, b, a in row) + "]"
            if y < len(pixels) - 1:
                row_str += ","
            code.append(row_str)
        
        code.extend([
            "    ]",
            "}"
        ])
        
        return "\n".join(code)
    
    @staticmethod
    def _to_base64(surface: pygame.Surface, width: int, height: int, var_name: str) -> str:
        """Convert to base64 encoded string"""
        try:
            # Convert surface to bytes
            image_data = pygame.image.tostring(surface, "RGBA")
            
            # Verify data length matches expected
            expected_length = width * height * 4
            actual_length = len(image_data)
            
            if actual_length != expected_length:
                # Fall back to pixel array method
                return ImageConverter._to_pixel_array(surface, width, height, var_name)
            
            # Encode to base64
            encoded = base64.b64encode(image_data).decode('ascii')
            
            code = [
                f"{var_name} = {{",
                f"    'width': {width},",
                f"    'height': {height},",
                f"    'format': 'RGBA',",
                f"    'data': '{encoded}'",
                f"}}"
            ]
            
            return "\n".join(code)
            
        except Exception:
            # Fall back to pixel array method
            return ImageConverter._to_pixel_array(surface, width, height, var_name)
    
    @staticmethod
    def _to_compressed(surface: pygame.Surface, width: int, height: int, var_name: str) -> str:
        """Convert to compressed base64 string"""
        try:
            # Convert surface to bytes
            image_data = pygame.image.tostring(surface, "RGBA")
            
            # Verify data length
            expected_length = width * height * 4
            actual_length = len(image_data)
            
            if actual_length != expected_length:
                return ImageConverter._to_pixel_array(surface, width, height, var_name)
            
            # Compress and encode
            compressed = zlib.compress(image_data, level=6)
            encoded = base64.b64encode(compressed).decode('ascii')
            
            code = [
                f"{var_name} = {{",
                f"    'width': {width},",
                f"    'height': {height},",
                f"    'format': 'RGBA',",
                f"    'compressed': True,",
                f"    'data': '{encoded}'",
                f"}}"
            ]
            
            return "\n".join(code)
            
        except Exception:
            # Fall back to pixel array method
            return ImageConverter._to_pixel_array(surface, width, height, var_name)
    
    @staticmethod
    def create_image_from_code(image_data: dict) -> pygame.Surface:
        """
        Create a pygame Surface from converted image data
        """
        try:
            if 'pixels' in image_data:
                # Pixel array method - FIXED COLOR RECONSTRUCTION
                return ImageConverter._from_pixel_array(image_data)
            elif 'data' in image_data:
                # Base64 or compressed method
                return ImageConverter._from_encoded_data(image_data)
            else:
                raise ValueError("Invalid image data format")
        except Exception as e:
            # Return a fallback surface
            print(f"Error creating image: {e}")
            fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
            fallback.fill((255, 0, 0, 128))
            return fallback
    
    @staticmethod
    def _from_pixel_array(image_data: dict) -> pygame.Surface:
        """Create surface from pixel array - FIXED COLOR BUG"""
        width = image_data['width']
        height = image_data['height']
        pixels = image_data['pixels']
        
        # Create surface with alpha channel
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Set each pixel individually - FIXED: Proper color assignment
        for y in range(height):
            if y < len(pixels):
                for x in range(width):
                    if x < len(pixels[y]):
                        r, g, b, a = pixels[y][x]
                        # Use pygame.Color to ensure proper color
                        surface.set_at((x, y), (r, g, b, a))
        
        return surface
    
    @staticmethod
    def _from_encoded_data(image_data: dict) -> pygame.Surface:
        """Create surface from encoded data"""
        width = image_data['width']
        height = image_data['height']
        encoded_data = image_data['data']
        
        try:
            # Decode base64
            decoded = base64.b64decode(encoded_data)
            
            # Decompress if needed
            if image_data.get('compressed', False):
                decoded = zlib.decompress(decoded)
            
            # Verify data length
            expected_length = width * height * 4
            if len(decoded) != expected_length:
                # Create a fallback surface
                fallback = pygame.Surface((width, height), pygame.SRCALPHA)
                fallback.fill((255, 255, 0, 128))
                return fallback
            
            # Create surface from bytes
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            image_surface = pygame.image.fromstring(decoded, (width, height), "RGBA")
            surface.blit(image_surface, (0, 0))
            return surface
            
        except Exception as e:
            print(f"Error decoding image: {e}")
            # Return fallback surface
            fallback = pygame.Surface((width, height), pygame.SRCALPHA)
            fallback.fill((0, 255, 0, 128))
            return fallback

class EmbeddedImage:
    """
    Helper class for working with embedded images
    """
    
    def __init__(self, image_data: dict):
        self.image_data = image_data
        self._surface = None
    
    @property
    def surface(self) -> pygame.Surface:
        """Get the pygame Surface (lazy loading)"""
        if self._surface is None:
            self._surface = ImageConverter.create_image_from_code(self.image_data)
        return self._surface
    
    @property
    def width(self) -> int:
        return self.image_data.get('width', 64)
    
    @property
    def height(self) -> int:
        return self.image_data.get('height', 64)
    
    def draw(self, renderer, x: int, y: int):
        """Draw the image using a renderer"""
        try:
            renderer.draw_surface(self.surface, x, y)
        except Exception:
            # Draw a fallback rectangle
            renderer.draw_rect(x, y, self.width, self.height, (255, 0, 0))