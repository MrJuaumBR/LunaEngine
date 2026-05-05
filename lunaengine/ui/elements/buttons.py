# buttons.py
import pygame
from typing import Optional, Callable, Tuple
from .base import *
from ..themes import ThemeManager, ThemeType, UITheme
from ...core.renderer import Renderer

class Button(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, text: str = "", 
                 font_size: int = 20, font_name: Optional[str] = None, 
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.text = text
        self.font_size = font_size
        self.font_name = font_name
        self.on_click_callback = None
        self.on_click_args = None
        self.on_click_kwargs = None
        self._font = None
        self._was_pressed = False
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme_obj.button_normal.color   # tuple
        self.text_color = theme_obj.button_text.color          # tuple
    
    def set_background_color(self, color: Optional[Tuple[int, int, int]]):
        if color is None:
            self.background_color = ThemeManager.get_theme(self.theme_type).button_normal.color
            return
        self.background_color = color
        
    def set_text_color(self, color: Optional[Tuple[int, int, int]]):
        if color is None:
            self.text_color = ThemeManager.get_theme(self.theme_type).button_text.color
            return
        self.text_color = color
        
    def set_text(self, text: str):
        self.text = text
        
    def get_text(self) -> str:
        return self.text
    
    def update_theme(self, theme_type):
        super().update_theme(theme_type)
        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme_obj.button_normal.color
        self.text_color = theme_obj.button_text.color
    
    @property
    def font(self):
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
        
    def set_on_click(self, callback: Callable, *args, **kwargs):
        self.on_click_callback = callback
        self.on_click_args = args
        self.on_click_kwargs = kwargs
        
    def set_theme(self, theme_type: ThemeType):
        self.theme_type = theme_type
    
    def _get_colors(self) -> UITheme:
        return ThemeManager.get_theme(self.theme_type)
    
    def update(self, dt: float, inputState: InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
        
        if self.mouse_over(inputState):
            if inputState.mouse_buttons_pressed.left:
                self.state = UIState.PRESSED
                if not self._was_pressed and self.on_click_callback:
                    if self.on_click_args or self.on_click_kwargs:
                        try:
                            self.on_click_callback(*self.on_click_args, **self.on_click_kwargs)
                        except:
                            self.on_click_callback()
                    else:
                        self.on_click_callback()
                self._was_pressed = True
            else:
                self.on_hover()
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False
    
        return super().update(dt, inputState)
    
    def _get_color_for_state(self) -> Tuple[int, int, int]:
        theme = self._get_colors()
        if self.state == UIState.NORMAL:
            return self.background_color
        elif self.state == UIState.HOVERED:
            return theme.button_hover.color
        elif self.state == UIState.PRESSED:
            return theme.button_pressed.color
        else:
            return theme.button_disabled.color
    
    def _get_text_color(self) -> Tuple[int, int, int]:
        return self.text_color
            
    def render(self, renderer: 'Renderer'):
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = self._get_colors()
        
        # Determine border parameters from theme
        border_color = None
        border_width = 0
        if theme.button_border and theme.button_border.border_width > 0:
            border_color = theme.button_border.color
            border_width = theme.button_border.border_width
        
        # Draw button with border and fill in one call
        color = self._get_color_for_state()
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, color,
                           fill=True,
                           border_color=border_color,
                           border_width=border_width,
                           corner_radius=self.corner_radius)
        
        # Draw text
        if self.text:
            text_color = self._get_text_color()
            center_x, center_y = actual_x + self.width // 2, actual_y + self.height // 2
            renderer.draw_text(self.text, center_x, center_y, text_color, self.font,
                               anchor_point=(0.5, 0.5))
                    
        super().render(renderer)


class ImageButton(UIElement):
    def __init__(self, x: int, y: int, image_path: str | pygame.Surface, 
                 width: Optional[int] = None, height: Optional[int] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.image_path = image_path
        self._image = None
        self._load_image()
        
        if width is None:
            width = self._image.get_width()
        if height is None:
            height = self._image.get_height()
            
        self.on_click_callback = None
        self.on_click_args = None
        self.on_click_kwargs = None
        self._was_pressed = False
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
    def _load_image(self):
        if self.image_path is None:
            self._image = pygame.Surface((self.width, self.height))
            self._image.fill((0, 0, 0))
            return
        elif type(self.image_path) == str:
            self._image = pygame.image.load(self.image_path).convert_alpha()
            self._image = pygame.transform.scale(self._image, (self.width, self.height))
        elif type(self.image_path) == pygame.Surface:
            self._image = self.image_path
            self._image = pygame.transform.scale(self._image, (self.width, self.height))
        
    def set_on_click(self, callback: Callable, *args, **kwargs):
        self.on_click_callback = callback
        self.on_click_args = args
        self.on_click_kwargs = kwargs
        
    def get_image(self):
        return self._image
    
    def set_image(self, image_path: str | pygame.Surface):
        if type(image_path) == str:
            self.image_path = image_path
            self._load_image()
        elif type(image_path) == pygame.Surface:
            self.image_path = None
            self._image = image_path
    
    def update(self, dt:float, inputState:InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
        
        if self.mouse_over(inputState):
            if inputState.mouse_buttons_pressed.left:
                self.state = UIState.PRESSED
                if not self._was_pressed and self.on_click_callback:
                    if self.on_click_args or self.on_click_kwargs:
                        try:
                            self.on_click_callback(*self.on_click_args, **self.on_click_kwargs)
                        except:
                            self.on_click_callback()
                    else:
                        self.on_click_callback()
                self._was_pressed = True
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False
    
        return super().update(dt, inputState)
    
    def _get_overlay_color(self) -> Optional[Tuple[int, int, int, int]]:
        if self.state == UIState.HOVERED:
            return (255, 255, 255, 50)
        elif self.state == UIState.PRESSED:
            return (0, 0, 0, 50)
        return None
    
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
        
        overlay_color = self._get_overlay_color()
        if overlay_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, overlay_color,
                               fill=True, border_width=0, corner_radius=self.corner_radius)
                
        super().render(renderer)