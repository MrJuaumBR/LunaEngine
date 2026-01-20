"""
Image Converter - Embedded Image Management and Conversion System
LOCATION: lunaengine/utils/image_converter.py
DESCRIPTION: Comprehensive image conversion and embedding system

Probably you will never use this shit :)
"""

import pygame
import base64
import zlib
from typing import Tuple, Optional

class ImageConverter:
    """
    Converts images to Python code for embedding in games
    Uses Pygame for image loading - NO PILLOW REQUIRED
    """
    
    @staticmethod
    def image_to_python_code(image_path: str, 
                           output_var_name: str = "image_data",
                           max_size: Optional[Tuple[int, int]] = None,
                           method: str = "compressed",
                           quality: float = 1.0) -> str:
        """
        Convert an image to Python code with quality compression
        
        Args:
            image_path: Path to the image file
            output_var_name: Name for the output variable
            max_size: Maximum dimensions (width, height)
            method: Conversion method ('pixel_array', 'base64', 'compressed')
            quality: Image quality (1.0 = original, 0.5 = half size, 0.25 = quarter size)
        """
        try:
            surface = pygame.image.load(image_path).convert_alpha()
            original_width, original_height = surface.get_size()
            
            # Apply quality scaling
            if quality < 1.0:
                quality = max(0.1, min(1.0, quality))  # Clamp between 0.1 and 1.0
                quality_size = (int(original_width * quality), int(original_height * quality))
                surface = ImageConverter._resize_surface(surface, quality_size)
            
            # Apply max size constraints
            if max_size and (max_size[0] or max_size[1]):
                surface = ImageConverter._resize_surface(surface, max_size)
            
            width, height = surface.get_size()
            
            if method == "pixel_array":
                return ImageConverter._to_pixel_array(surface, width, height, output_var_name)
            elif method == "base64":
                return ImageConverter._to_base64(surface, width, height, output_var_name)
            elif method == "compressed":
                return ImageConverter._to_compressed_optimized(surface, width, height, output_var_name)
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            return f"# Error converting image: {e}"
    
    @staticmethod
    def _resize_surface(surface: pygame.Surface, target_size: Tuple[int, int]) -> pygame.Surface:
        original_width, original_height = surface.get_size()
        target_width, target_height = target_size
        
        # If target is 0 in one dimension, calculate based on aspect ratio
        if target_width == 0:
            target_width = int(original_width * (target_height / original_height))
        if target_height == 0:
            target_height = int(original_height * (target_width / original_width))
        
        return pygame.transform.smoothscale(surface, (target_width, target_height))
    
    @staticmethod
    def _to_pixel_array(surface: pygame.Surface, width: int, height: int, var_name: str) -> str:
        pixels = []
        
        for y in range(height):
            row = []
            for x in range(width):
                color = surface.get_at((x, y))
                row.append((color.r, color.g, color.b, color.a))
            pixels.append(row)
        
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
        try:
            image_data = pygame.image.tostring(surface, "RGBA")
            expected_length = width * height * 4
            
            if len(image_data) != expected_length:
                return ImageConverter._to_pixel_array(surface, width, height, var_name)
            
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
            return ImageConverter._to_pixel_array(surface, width, height, var_name)
    
    @staticmethod
    def _to_compressed_optimized(surface: pygame.Surface, width: int, height: int, var_name: str) -> str:
        try:
            image_bytes = pygame.image.tostring(surface, "RGBA")
            expected_size = width * height * 4
            
            if len(image_bytes) != expected_size:
                return ImageConverter._to_base64(surface, width, height, var_name)
            
            compressed_data = zlib.compress(image_bytes, level=9)
            encoded_data = base64.b64encode(compressed_data).decode('ascii')
            
            chunk_size = 80
            chunks = [encoded_data[i:i+chunk_size] for i in range(0, len(encoded_data), chunk_size)]
            encoded_data_formatted = '\\\n        '.join(['"' + chunk + '"' for chunk in chunks])
            
            code = [
                f"{var_name} = {{",
                f"    'width': {width},",
                f"    'height': {height},",
                f"    'format': 'RGBA',",
                f"    'compressed': True,",
                f"    'data': {encoded_data_formatted}",
                f"}}"
            ]
            
            return "\n".join(code)
            
        except Exception:
            return ImageConverter._to_base64(surface, width, height, var_name)
    
    @staticmethod
    def create_image_from_code(image_data: dict) -> pygame.Surface:
        try:
            if 'pixels' in image_data:
                return ImageConverter._from_pixel_array(image_data)
            elif 'data' in image_data:
                return ImageConverter._from_encoded_data(image_data)
            else:
                raise ValueError("Invalid image data format")
        except Exception as e:
            fallback = pygame.Surface((64, 64), pygame.SRCALPHA)
            fallback.fill((255, 0, 0, 128))
            return fallback
    
    @staticmethod
    def _from_pixel_array(image_data: dict) -> pygame.Surface:
        width = image_data['width']
        height = image_data['height']
        pixels = image_data['pixels']
        
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        for y in range(height):
            if y < len(pixels):
                row = pixels[y]
                for x in range(width):
                    if x < len(row):
                        r, g, b, a = row[x]
                        surface.set_at((x, y), (r, g, b, a))
        
        return surface
    
    @staticmethod
    def _from_encoded_data(image_data: dict) -> pygame.Surface:
        width = image_data['width']
        height = image_data['height']
        encoded_data = image_data['data']
        
        try:
            decoded = base64.b64decode(encoded_data)
            
            if image_data.get('compressed', False):
                decoded = zlib.decompress(decoded)
            
            expected_length = width * height * 4
            if len(decoded) != expected_length:
                fallback = pygame.Surface((width, height), pygame.SRCALPHA)
                fallback.fill((255, 255, 0, 128))
                return fallback
            
            surface = pygame.Surface((width, height), pygame.SRCALPHA)
            image_surface = pygame.image.fromstring(decoded, (width, height), "RGBA")
            surface.blit(image_surface, (0, 0))
            return surface
            
        except Exception:
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
        try:
            renderer.draw_surface(self.surface, x, y)
        except Exception:
            renderer.draw_rect(x, y, self.width, self.height, (255, 0, 0))