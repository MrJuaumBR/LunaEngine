# labels.py (fixed)

import pygame
from typing import Optional, Tuple, Dict, Any
from .base import UIElement, FontManager, Color
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer

class TextLabel(UIElement):
    """UI element for displaying text labels."""
    
    _properties:Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'text': {'name':'text', 'key':'text', 'type':str, 'editable':True, 'description':'The text content of the label.'},
        'color': {'name':'color', 'key':'color', 'type':Tuple[int, int, int], 'editable':True, 'description':'Custom text color (RGB). Overrides theme color.'},
        'font_size': {'name':'font_size', 'key':'font_size', 'type':int, 'editable':True, 'description':'Size of the font in pixels.'},
        'font_name': {'name':'font_name', 'key':'font_name', 'type':Optional[str], 'editable':True, 'description':'Path to font file or None for default font.'}
    }
    def __init__(self, x: int, y: int, text: str, font_size: int = 24, 
                 color: Optional[Tuple[int, int, int]] = None,
                 font_name: Optional[str] = None, 
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None, **kwargs):
        FontManager.initialize()
        text_size = FontManager.get_font(font_name, int(font_size)).size(text)
        
        super().__init__(x, y, text_size[0], text_size[1], root_point, element_id)
        self.text = text
        self.font_size = font_size
        self.custom_color:Color = color
        self.font_name = font_name
        self._font = None
        
        self.theme_type = theme or ThemeManager.get_current_theme()

    def get_text(self) -> str:
        return self.text
    
    def update_theme(self, theme_type):
        return super().update_theme(theme_type)
    
    def set_text_color(self, color: Tuple[int, int, int]|Color):
        if isinstance(color, Color):
            self.custom_color = color
        elif type(color) in [tuple, list]:
            self.custom_color = Color(*color)
        
    def set_color(self, color: Tuple[int, int, int]|Color):
        self.set_text_color(color)
    
    @property
    def font(self):
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
        
    def set_text(self, text: str):
        self.text = text
        text_surface = self.font.render(text, True, (self.custom_color.toTuple() if isinstance(self.custom_color, Color) else self.custom_color) or (255, 255, 255))
        self.width = text_surface.get_width()
        self.height = text_surface.get_height()
    
    def set_theme(self, theme_type: ThemeType):
        self.theme_type = theme_type
    
    def _get_text_color(self) -> Color:
        if self.custom_color:
            return self.custom_color
        theme = ThemeManager.get_theme(self.theme_type)
        return theme.label_text.color
            
    def render(self, renderer:'Renderer'):
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        text_color = self._get_text_color()
        
        renderer.draw_text(self.text, actual_x, actual_y, text_color, self.font)
        
        super().render(renderer)

class ImageLabel(UIElement):
    def __init__(self, x: int, y: int, image_path: str | pygame.Surface, 
                 width: Optional[int] = None, height: Optional[int] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 element_id: Optional[str] = None):
        self.image_path = image_path
        self._image = None
        self._load_image()
        
        if self._image:        
            if width is None:
                width = self._image.get_width()
            if height is None:
                height = self._image.get_height()

        super().__init__(x, y, width, height, root_point, element_id)

        
    def _load_image(self):
        if self.image_path is None:
            self._image = pygame.Surface((100, 100))
            self._image.fill((255, 0, 255))
            return
        elif type(self.image_path) == pygame.Surface:
            self._image = self.image_path
            return
        elif type(self.image_path) == str:
            if not os.path.exists(self.image_path):
                self._image = pygame.Surface((100, 100))
                self._image.fill((255, 0, 255))
                return
        
    def set_image(self, image_path: str | pygame.Surface):
        if type(image_path) == str:
            self.image_path = image_path
            self._load_image()
        elif type(image_path) == pygame.Surface:
            self.image_path = None
            self._image = pygame.transform.scale(image_path, (self.width, self.height))
    
    def get_image(self) -> pygame.Surface:
        return self._image
    
    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height
        self._image = pygame.transform.scale(self._image, (self.width, self.height))
    
    def render(self, renderer):
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        
        if self._image.get_width() != self.width or self._image.get_height() != self.height:
            scaled_image = pygame.transform.scale(self._image, (self.width, self.height))
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(scaled_image, actual_x, actual_y)
            else:
                renderer.draw_surface(scaled_image, actual_x, actual_y)
        else:
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(self._image, actual_x, actual_y)
            else:
                renderer.draw_surface(self._image, actual_x, actual_y)
                
        super().render(renderer)