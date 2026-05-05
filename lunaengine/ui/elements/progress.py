# progress.py
import pygame
from typing import Optional, Literal, Tuple
from .base import UIElement, FontManager
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer

class ProgressBar(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 min_val: float = 0, max_val: float = 100, value: float = 0,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 orientation: Literal['vertical', 'horizontal'] = "horizontal",
                 element_id: Optional[str] = None, style: str = 'default', **kwargs):
        super().__init__(x, y, width, height, root_point, element_id)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.orientation = orientation.lower()
        
        self.draw_value: bool = kwargs.get('draw_value', False)
        self.font_size: int = kwargs.get('font_size', int(self.height * 0.8))
        self.font_draw: str = kwargs.get('font_draw', None)
        
        self.style: str = style
        self.segment_count: int = kwargs.get('segment_count', 20)
        self.segment_gap: int = kwargs.get('segment_gap', 2)
        
        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme_obj.slider_track.color
        self.foreground_color = theme_obj.button_normal.color
        self.font_color = theme_obj.slider_text.color
        self.border_color = theme_obj.border.color if theme_obj.border else (120, 120, 140)
        
    def set_background_color(self, color):
        self.background_color = color
        
    def set_foreground_color(self, color):
        self.foreground_color = color
        
    def set_font_color(self, color):
        self.font_color = color
        
    def set_font(self, font_name: str, font_size: int):
        self.font_size = font_size
        self.font_draw = font_name
        self.draw_value = True
    
    def set_border_color(self, color):
        self.border_color = color
        
    def update_theme(self, theme_type):
        super().update_theme(theme_type)
        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme_obj.slider_track.color
        self.foreground_color = theme_obj.button_normal.color
        self.font_color = theme_obj.slider_text.color
        self.border_color = theme_obj.border.color if theme_obj.border else (120, 120, 140)
        
    def set_value(self, value: float):
        self.value = max(self.min_val, min(self.max_val, value))
    
    def get_percentage(self) -> float:
        return (self.value - self.min_val) / (self.max_val - self.min_val) * 100
    
    def _get_soundpad_color(self, t: float) -> Tuple[int, int, int]:
        if t < 0.5:
            r = int(255 * (t / 0.5))
            g = 255
            b = 0
        else:
            r = 255
            g = int(255 * (1 - (t - 0.5) / 0.5))
            b = 0
        return (r, g, b)
    
    def render(self, renderer):
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        if self.style == 'soundpad':
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                               self.background_color, fill=True,
                               corner_radius=self.corner_radius)
            
            percentage = self.get_percentage() / 100.0
            total_segments = self.segment_count
            filled_segments = int(percentage * total_segments)
            
            if self.orientation == 'horizontal':
                total_gap_width = (total_segments - 1) * self.segment_gap
                segment_width = (self.width - total_gap_width) / total_segments
                if segment_width < 1:
                    segment_width = 1
                for i in range(total_segments):
                    seg_x = actual_x + i * (segment_width + self.segment_gap)
                    seg_color = self._get_soundpad_color(i / total_segments)
                    if i < filled_segments:
                        renderer.draw_rect(seg_x, actual_y, segment_width, self.height,
                                           seg_color, fill=True, corner_radius=self.corner_radius)
            else:
                total_gap_height = (total_segments - 1) * self.segment_gap
                segment_height = (self.height - total_gap_height) / total_segments
                if segment_height < 1:
                    segment_height = 1
                for i in range(total_segments):
                    seg_y = actual_y + self.height - (i + 1) * (segment_height + self.segment_gap)
                    seg_color = self._get_soundpad_color(i / total_segments)
                    if i < filled_segments:
                        renderer.draw_rect(actual_x, seg_y, self.width, segment_height,
                                           seg_color, fill=True, corner_radius=self.corner_radius)
            return
        
        elif self.style == 'default':
            # Draw border if border color is set
            if self.border_color:
                renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                                   self.border_color, fill=False,
                                   border_width=self.border_width,
                                   corner_radius=self.corner_radius)
            
            # Draw background
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                               self.background_color, fill=True,
                               corner_radius=self.corner_radius)
            
            percentage = self.get_percentage() / 100.0
            
            if self.orientation == "vertical":
                progress_height = int(percentage * self.height)
                if progress_height > 0:
                    renderer.draw_rect(
                        actual_x,
                        actual_y + self.height - progress_height,
                        self.width,
                        progress_height,
                        self.foreground_color,
                        fill=True,
                        corner_radius=self.corner_radius
                    )
            else:
                progress_width = int(percentage * self.width)
                if progress_width > 0:
                    renderer.draw_rect(
                        actual_x,
                        actual_y,
                        progress_width,
                        self.height,
                        self.foreground_color,
                        fill=True,
                        corner_radius=self.corner_radius
                    )
        
        if self.draw_value:
            font = FontManager.get_font(self.font_draw, self.font_size)
            renderer.draw_text(
                f"{self.get_percentage():.1f}%",
                actual_x + self.width // 2,
                actual_y + self.height // 2,
                self.font_color,
                font,
                anchor_point=(0.5, 0.5)
            )
                
        super().render(renderer)