# progress.py
import pygame
from typing import Optional, Literal, Tuple, Dict, Any
from .base import UIElement, FontManager
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer

class ProgressBar(UIElement):
    """
    A progress bar widget that displays a value as a filled bar.
    Supports horizontal/vertical orientation and a 'soundpad' segmented style.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'min_val': {'name': 'minimum value', 'key': 'min_val', 'type': float, 'editable': True,
                    'description': 'Minimum value (0% progress).'},
        'max_val': {'name': 'maximum value', 'key': 'max_val', 'type': float, 'editable': True,
                    'description': 'Maximum value (100% progress).'},
        'value': {'name': 'current value', 'key': 'value', 'type': float, 'editable': True,
                  'description': 'Current progress value.'},
        'orientation': {'name': 'orientation', 'key': 'orientation', 'type': str, 'editable': True,
                        'description': '"horizontal" or "vertical".', 'options': ['horizontal', 'vertical']},
        'style': {'name': 'style', 'key': 'style', 'type': str, 'editable': True,
                  'description': '"default" or "soundpad".', 'options': ['default', 'soundpad']},
        'draw_value': {'name': 'draw value', 'key': 'draw_value', 'type': bool, 'editable': True,
                       'description': 'Show percentage text inside the bar.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        min_val: float = 0,
        max_val: float = 100,
        value: float = 0,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        orientation: Literal['vertical', 'horizontal'] = "horizontal",
        element_id: Optional[str] = None,
        style: str = 'default',
        **kwargs
    ) -> None:
        """
        Initialize a progress bar.

        Args:
            x, y: Position (before anchor).
            width, height: Dimensions.
            min_val: Minimum value (0%).
            max_val: Maximum value (100%).
            value: Current value.
            pivot: Anchor point.
            theme: Theme to apply.
            orientation: 'horizontal' or 'vertical'.
            element_id: Custom ID.
            style: 'default' or 'soundpad' (segmented with gradient colors).
            **kwargs: Additional parameters:
                draw_value (bool): Show percentage text.
                font_size (int): Font size for text.
                font_draw (str): Font name for text.
                segment_count (int): Number of segments for soundpad style.
                segment_gap (int): Gap between segments.
        """
        super().__init__(x, y, width, height, pivot, element_id)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value

        self.theme_type = theme or ThemeManager.get_current_theme()
        self.orientation = orientation.lower()

        self.draw_value: bool = kwargs.get('draw_value', False)
        self.font_size: int = kwargs.get('font_size', int(self.height * 0.8))
        self.font_draw: Optional[str] = kwargs.get('font_draw', None)

        self.style: str = style
        self.segment_count: int = kwargs.get('segment_count', 20)
        self.segment_gap: int = kwargs.get('segment_gap', 2)

        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme_obj.slider_track.color
        self.foreground_color = theme_obj.accent1.color
        self.font_color = theme_obj.slider_text.color
        self.border_color = theme_obj.border.color if theme_obj.border else (120, 120, 140)

    def _get_init_args(self) -> Dict[str, Any]:
        """Return constructor arguments for restarting."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'min_val': self.min_val,
            'max_val': self.max_val,
            'value': self.value,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'orientation': self.orientation,
            'element_id': self.element_id,
            'style': self.style,
            'draw_value': self.draw_value,
            'font_size': self.font_size,
            'font_draw': self.font_draw,
            'segment_count': self.segment_count,
            'segment_gap': self.segment_gap,
        }

    def set_background_color(self, color: Tuple[int, int, int]) -> None:
        """Set the background (empty part) color."""
        self.background_color = color

    def set_foreground_color(self, color: Tuple[int, int, int]) -> None:
        """Set the foreground (filled part) color."""
        self.foreground_color = color

    def set_font_color(self, color: Tuple[int, int, int]) -> None:
        """Set the color of the percentage text."""
        self.font_color = color

    def set_font(self, font_name: str, font_size: int) -> None:
        """Set a custom font for the percentage text."""
        self.font_size = font_size
        self.font_draw = font_name
        self.draw_value = True

    def set_border_color(self, color: Tuple[int, int, int]) -> None:
        """Set the border color (only used in default style)."""
        self.border_color = color

    def update_theme(self, theme_type: ThemeType) -> None:
        """Apply a new theme to the progress bar."""
        super().update_theme(theme_type)
        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme_obj.slider_track.color
        self.foreground_color = theme_obj.accent1.color
        self.font_color = theme_obj.slider_text.color
        self.border_color = theme_obj.border.color if theme_obj.border else (120, 120, 140)

    def set_value(self, value: float) -> None:
        """Update the current progress value (clamped to min/max)."""
        self.value = max(self.min_val, min(self.max_val, value))
    
    def set_max_value(self, value: float) -> None:
        """Update the maximum progress value (clamped to min/max)."""
        self.max_val = value
        
    def set_min_value(self, value: float) -> None:
        """Update the minimum progress value (clamped to min/max)."""
        self.min_val = value

    def get_percentage(self) -> float:
        """Return the current progress as a percentage (0-100)."""
        if self.max_val == self.min_val:
            return 0.0
        return (self.value - self.min_val) / (self.max_val - self.min_val) * 100

    def _get_soundpad_color(self, t: float) -> Tuple[int, int, int]:
        """Get a gradient color for soundpad style (t in [0,1])."""
        if t < 0.5:
            r = int(255 * (t / 0.5))
            g = 255
            b = 0
        else:
            r = 255
            g = int(255 * (1 - (t - 0.5) / 0.5))
            b = 0
        return (r, g, b)

    def render(self, renderer: Renderer) -> None:
        """Render the progress bar."""
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        if self.style == 'soundpad':
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                               self.background_color, fill=True,
                               corner_radius=self.corner_radius, border_color=self.border_color, border_width=self.border_width)

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
                                           seg_color, fill=True, corner_radius=self.corner_radius, border_color=self.border_color, border_width=self.segment_gap*0.5)
            else:  # vertical
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
            # Skip default drawing for soundpad
            if self.draw_value:
                font = FontManager.get_font(self.font_draw, self.font_size)
                renderer.draw_text(
                    f"{self.get_percentage():.1f}%",
                    actual_x + self.width // 2,
                    actual_y + self.height // 2,
                    self.font_color,
                    font,
                    pivot=(0.5, 0.5)
                )
        else:# Default style
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                            self.background_color, fill=True,
                            corner_radius=self.corner_radius, border_width=self.border_width, border_color=self.border_color or None)

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
            else:  # horizontal
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
                    pivot=(0.5, 0.5)
                )