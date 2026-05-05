import pygame
import time
import math
import numpy as np
from typing import Optional, List, Tuple, Literal
from .base import *

class ChartVisualizer(UIElement):
    """
    A versatile data visualization component that can display various chart types:
    bar charts (vertical/horizontal), pie charts, line charts, scatter plots, and radar charts.
    
    Gradient support:
    - For line charts: each segment between two points is drawn with a color interpolated
      between the colors of those two points.
    - For radar charts: each edge is drawn with a color interpolated between the colors
      of its two vertices.
    
    Gradient parameters (passed as kwargs to __init__):
        use_gradient (bool): Enable gradient coloring. Default False.
        gradient_colors (List[Tuple[int,int,int]]): List of colors per data point.
            If provided, overrides start/end.
        gradient_start (Tuple[int,int,int]): Start color for interpolation (default red).
        gradient_end (Tuple[int,int,int]): End color for interpolation (default green).
    """

    def __init__(self, x: int, y: int, width: int, height: int,
                 data: Optional[List[float]] = None,
                 labels: Optional[List[str]] = None,
                 colors: Optional[List[Tuple[int, int, int]]] = None,
                 chart_type: Literal['bar', 'pie', 'line', 'scatter', 'radar'] = 'bar',
                 orientation: Literal['vertical', 'horizontal'] = 'vertical',
                 title: str = "",
                 show_labels: bool = True,
                 show_legend: bool = False,
                 min_value: Optional[float] = None,
                 max_value: Optional[float] = None,
                 radar_max_value: float = 1.0,
                 radar_axis_labels: Optional[List[str]] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None,
                 **kwargs):
        super().__init__(x, y, width, height, root_point, element_id)

        self.data = data if data is not None else []
        self.labels = labels if labels is not None else [f"Item {i+1}" for i in range(len(self.data))]
        self.colors = colors or self._default_colors()

        self.chart_type = chart_type
        self.orientation = orientation
        self.title = title
        self.show_labels = show_labels
        self.show_legend = show_legend
        self.min_value = min_value
        self.max_value = max_value
        self.padding = 10
        self.bar_spacing = 2
        self.line_width = 2
        self.point_radius = 3

        self.radar_max_value = radar_max_value
        self.radar_axis_labels = radar_axis_labels if radar_axis_labels is not None else self.labels

        self.use_gradient = kwargs.get('use_gradient', False)
        self.gradient_colors = kwargs.get('gradient_colors', None)
        self.gradient_start = kwargs.get('gradient_start', (255, 0, 0))
        self.gradient_end = kwargs.get('gradient_end', (0, 255, 0))

        self.theme_type = theme or ThemeManager.get_current_theme()

        self._title_font = None
        self._label_font = None
        self._legend_font = None

        self._needs_recalc = True
        self._normalized_data = []
        self._angles = []
        self._bar_positions = []
        self._legend_items = []

        self._anim_target_data = None
        self._anim_target_labels = None
        self._anim_start_data = []
        self._anim_start_labels = []
        self._anim_progress = 0.0
        self._anim_duration = 0.5
        self._anim_elapsed = 0.0
        self._anim_active = False
        self._current_display_data = list(self.data) if self.data else []

    def _default_colors(self) -> List[Tuple[int, int, int]]:
        return [
            (255, 99, 132), (54, 162, 235), (255, 206, 86),
            (75, 192, 192), (153, 102, 255), (255, 159, 64),
            (199, 199, 199), (83, 102, 255), (255, 99, 255)
        ]

    @property
    def title_font(self):
        if self._title_font is None:
            FontManager.initialize()
            self._title_font = FontManager.get_font(None, 20)
        return self._title_font

    @property
    def label_font(self):
        if self._label_font is None:
            FontManager.initialize()
            self._label_font = FontManager.get_font(None, 12)
        return self._label_font

    @property
    def legend_font(self):
        if self._legend_font is None:
            FontManager.initialize()
            self._legend_font = FontManager.get_font(None, 10)
        return self._legend_font

    def set_data(self, data: List[float], labels: Optional[List[str]] = None,
                 animate: bool = False, duration: float = 0.5):
        if not animate:
            self.data = data
            if labels is not None:
                self.labels = labels
            self._current_display_data = list(data)
            self._needs_recalc = True
        else:
            self._anim_target_data = data
            self._anim_target_labels = labels
            self._anim_duration = duration
            self._anim_elapsed = 0.0
            self._anim_active = True
            self._anim_start_data = list(self._current_display_data)
            self._anim_start_labels = list(self.labels) if labels else None

    def update(self, dt: float, inputState: InputState):
        super().update(dt, inputState)
        if self._anim_active:
            self._anim_elapsed += dt
            self._anim_progress = min(1.0, self._anim_elapsed / self._anim_duration)
            if self._anim_target_data is not None:
                self._current_display_data = [
                    start + (target - start) * self._anim_progress
                    for start, target in zip(self._anim_start_data, self._anim_target_data)
                ]
            if self._anim_progress >= 1.0:
                self.data = self._anim_target_data
                if self._anim_target_labels:
                    self.labels = self._anim_target_labels
                self._current_display_data = list(self.data)
                self._anim_active = False
            self._needs_recalc = True

    def _recalc(self):
        data_to_use = self._current_display_data if self._anim_active else self.data
        if not data_to_use:
            self._normalized_data = []
            return

        if self.chart_type != 'pie' and self.chart_type != 'radar':
            data_min = min(data_to_use) if self.min_value is None else self.min_value
            data_max = max(data_to_use) if self.max_value is None else self.max_value
            if data_max == data_min:
                self._normalized_data = [0.5] * len(data_to_use)
            else:
                self._normalized_data = [(v - data_min) / (data_max - data_min) for v in data_to_use]

        if self.chart_type == 'pie':
            total = sum(data_to_use)
            if total == 0:
                self._angles = [0] * len(data_to_use)
            else:
                self._angles = [v / total * 360 for v in data_to_use]

        self._needs_recalc = False

    def _get_color(self, index: int) -> Tuple[int, int, int]:
        if index < len(self.colors):
            return self.colors[index]
        return self.colors[index % len(self.colors)]

    def _get_point_color(self, index: int, t: float = None) -> Tuple[int, int, int]:
        if not self.use_gradient:
            return self._get_color(index)

        if self.gradient_colors is not None and index < len(self.gradient_colors):
            return self.gradient_colors[index]

        n = len(self.data)
        if n <= 1:
            return self.gradient_start
        t = index / (n - 1) if t is None else t
        r = int(self.gradient_start[0] + (self.gradient_end[0] - self.gradient_start[0]) * t)
        g = int(self.gradient_start[1] + (self.gradient_end[1] - self.gradient_start[1]) * t)
        b = int(self.gradient_start[2] + (self.gradient_end[2] - self.gradient_start[2]) * t)
        return (r, g, b)

    def render(self, renderer: Renderer):
        if not self.visible or not self.data:
            return

        if self._needs_recalc:
            self._recalc()

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        renderer.draw_rect(actual_x, actual_y, self.width, self.height, theme.background.color,
                           border_width=self.border_width)

        title_height = self.title_font.get_height() + 5 if self.title else 0
        legend_height = 20 if self.show_legend else 0

        chart_top = actual_y + self.padding + title_height
        chart_bottom = actual_y + self.height - self.padding - legend_height
        chart_left = actual_x + self.padding
        chart_right = actual_x + self.width - self.padding
        chart_height = chart_bottom - chart_top
        chart_width = chart_right - chart_left

        if self.title:
            title_x = actual_x + self.width // 2
            title_y = actual_y + self.padding
            renderer.draw_text(self.title, title_x, title_y, theme.text_primary.color,
                               self.title_font, anchor_point=(0.5, 0))

        if self.chart_type == 'bar':
            self._render_bar(renderer, chart_left, chart_top, chart_width, chart_height, theme)
        elif self.chart_type == 'pie':
            self._render_pie(renderer, chart_left, chart_top, chart_width, chart_height, theme)
        elif self.chart_type == 'line':
            self._render_line(renderer, chart_left, chart_top, chart_width, chart_height, theme)
        elif self.chart_type == 'scatter':
            self._render_scatter(renderer, chart_left, chart_top, chart_width, chart_height, theme)
        elif self.chart_type == 'radar':
            self._render_radar(renderer, chart_left, chart_top, chart_width, chart_height, theme)

        if self.show_legend:
            self._render_legend(renderer, actual_x, actual_y + self.height - 18, theme)

        super().render(renderer)

    def _render_bar(self, renderer, left, top, width, height, theme):
        n = len(self.data)
        if n == 0:
            return

        data_to_use = self._current_display_data if self._anim_active else self.data

        if self.orientation == 'vertical':
            bar_width = (width - (n - 1) * self.bar_spacing) / n
            max_val = max(data_to_use) if self.max_value is None else self.max_value
            min_val = min(data_to_use) if self.min_value is None else self.min_value
            val_range = max_val - min_val if max_val != min_val else 1

            for i, val in enumerate(data_to_use):
                bar_height = ((val - min_val) / val_range) * (height - 20)
                bar_x = left + i * (bar_width + self.bar_spacing)
                bar_y = top + height - 10 - bar_height

                color = self._get_point_color(i) if self.use_gradient else self._get_color(i)
                renderer.draw_rect(bar_x, bar_y, bar_width, bar_height, color, border_width=0)

                if self.show_labels:
                    label = self.labels[i] if i < len(self.labels) else str(i)
                    label_x = bar_x + bar_width // 2
                    label_y = top + height - 5
                    renderer.draw_text(label, label_x, label_y, theme.text_secondary.color,
                                       self.label_font, anchor_point=(0.5, 1))

        else:
            bar_height = (height - (n - 1) * self.bar_spacing) / n
            max_val = max(data_to_use) if self.max_value is None else self.max_value
            min_val = min(data_to_use) if self.min_value is None else self.min_value
            val_range = max_val - min_val if max_val != min_val else 1

            for i, val in enumerate(data_to_use):
                bar_width = ((val - min_val) / val_range) * (width - 40)
                bar_x = left + 40
                bar_y = top + i * (bar_height + self.bar_spacing)

                color = self._get_point_color(i) if self.use_gradient else self._get_color(i)
                renderer.draw_rect(bar_x, bar_y, bar_width, bar_height, color, border_width=0)

                if self.show_labels:
                    label = self.labels[i] if i < len(self.labels) else str(i)
                    label_x = left + 35
                    label_y = bar_y + bar_height // 2
                    renderer.draw_text(label, label_x, label_y, theme.text_secondary.color,
                                       self.label_font, anchor_point=(1, 0.5))

    def _render_pie(self, renderer, left, top, width, height, theme):
        center_x = left + width // 2
        center_y = top + height // 2
        radius = min(width, height) // 2 - 10

        start_angle = 0
        for i, angle in enumerate(self._angles):
            if angle <= 0:
                continue
            color = self._get_point_color(i) if self.use_gradient else self._get_color(i)
            end_angle = start_angle + angle

            points = [(center_x, center_y)]
            steps = max(3, int(angle / 5))
            for step in range(steps + 1):
                a = math.radians(start_angle + (step / steps) * angle)
                x = center_x + radius * math.cos(a)
                y = center_y + radius * math.sin(a)
                points.append((x, y))
            renderer.draw_polygon(points, color)

            if self.show_labels:
                mid_angle = math.radians(start_angle + angle / 2)
                label_x = center_x + (radius + 15) * math.cos(mid_angle)
                label_y = center_y + (radius + 15) * math.sin(mid_angle)
                label = self.labels[i] if i < len(self.labels) else str(i)
                renderer.draw_text(label, label_x, label_y, theme.text_primary.color,
                                   self.label_font, anchor_point=(0.5, 0.5))

            start_angle = end_angle

    def _render_line(self, renderer, left, top, width, height, theme):
        if len(self.data) < 2:
            return

        data_to_use = self._current_display_data if self._anim_active else self.data
        max_val = max(data_to_use) if self.max_value is None else self.max_value
        min_val = min(data_to_use) if self.min_value is None else self.min_value
        val_range = max_val - min_val if max_val != min_val else 1

        points = []
        for i, val in enumerate(data_to_use):
            x = left + (i / (len(data_to_use) - 1)) * width
            y = top + height - ((val - min_val) / val_range) * height
            points.append((x, y))

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i+1]
            if self.use_gradient:
                seg_len = math.hypot(x2 - x1, y2 - y1)
                num_sub = max(10, int(seg_len / 5))
                for sub in range(num_sub):
                    t1 = sub / num_sub
                    t2 = (sub + 1) / num_sub
                    global_t1 = (i + t1) / (len(points) - 1)
                    color1 = self._get_point_color(i, global_t1)
                    sub_x1 = x1 + (x2 - x1) * t1
                    sub_y1 = y1 + (y2 - y1) * t1
                    sub_x2 = x1 + (x2 - x1) * t2
                    sub_y2 = y1 + (y2 - y1) * t2
                    renderer.draw_line(sub_x1, sub_y1, sub_x2, sub_y2, color1, self.line_width)
            else:
                renderer.draw_line(x1, y1, x2, y2, self._get_color(i), self.line_width)

        for i, (x, y) in enumerate(points):
            color = self._get_point_color(i, i/(len(points)-1)) if self.use_gradient else self._get_color(i)
            renderer.draw_circle(x, y, self.point_radius, color)
            if self.show_labels:
                label = f"{data_to_use[i]:.1f}"
                if y - 15 > top:
                    label_y = y - 10
                    anchor = (0.5, 1)
                else:
                    label_y = y + 15
                    anchor = (0.5, 0)
                renderer.draw_text(label, x, label_y, theme.text_secondary.color,
                                self.label_font, anchor_point=anchor)

    def _render_scatter(self, renderer, left, top, width, height, theme):
        if len(self.data) < 1:
            return

        data_to_use = self._current_display_data if self._anim_active else self.data
        max_val = max(data_to_use) if self.max_value is None else self.max_value
        min_val = min(data_to_use) if self.min_value is None else self.min_value
        val_range = max_val - min_val if max_val != min_val else 1

        for i, val in enumerate(data_to_use):
            x = left + (i / (len(data_to_use) - 1)) * width
            y = top + height - ((val - min_val) / val_range) * height
            color = self._get_point_color(i) if self.use_gradient else self._get_color(i)
            renderer.draw_circle(x, y, self.point_radius, color)

            if self.show_labels:
                label = f"{data_to_use[i]:.1f}"
                if y - 15 > top:
                    label_y = y - 10
                    anchor = (0.5, 1)
                else:
                    label_y = y + 15
                    anchor = (0.5, 0)
                renderer.draw_text(label, x, label_y, theme.text_secondary.color,
                                   self.label_font, anchor_point=anchor)

    def _render_radar(self, renderer, left, top, width, height, theme):
        if not self.data:
            return

        center_x = left + width // 2
        center_y = top + height // 2
        radius = min(width, height) // 2 - 20

        num_axes = len(self.data)
        if num_axes < 3:
            return

        angles = [math.radians(-90 + 360 * i / num_axes) for i in range(num_axes)]

        grid_color = theme.border.color if theme.border else (80, 80, 100)
        grid_levels = 4
        for level in range(1, grid_levels + 1):
            r = radius * level / grid_levels
            points = []
            for angle in angles:
                x = center_x + r * math.cos(angle)
                y = center_y + r * math.sin(angle)
                points.append((x, y))
            if len(points) > 2:
                renderer.draw_polygon(points, grid_color, fill=False, border_width=1)

        axis_color = theme.border.color if theme.border else (120, 120, 140)
        for angle in angles:
            end_x = center_x + radius * math.cos(angle)
            end_y = center_y + radius * math.sin(angle)
            renderer.draw_line(center_x, center_y, end_x, end_y, axis_color, 1)

        if self.show_labels:
            label_radius = radius + 15
            for i, angle in enumerate(angles):
                label = self.radar_axis_labels[i] if i < len(self.radar_axis_labels) else str(i)
                x = center_x + label_radius * math.cos(angle)
                y = center_y + label_radius * math.sin(angle)
                renderer.draw_text(label, x, y, theme.text_secondary.color, self.label_font, anchor_point=(0.5, 0.5))

        data_to_use = self._current_display_data if self._anim_active else self.data
        data_points = []
        for i, val in enumerate(data_to_use):
            norm = min(1.0, max(0.0, val / self.radar_max_value))
            r = radius * norm
            x = center_x + r * math.cos(angles[i])
            y = center_y + r * math.sin(angles[i])
            data_points.append((x, y))

        if len(data_points) > 2:
            fill_color = self._get_point_color(0) if self.use_gradient else self._get_color(0)
            fill_color = (*fill_color, 100)
            renderer.draw_polygon(data_points, fill_color, fill=True)

            for i in range(len(data_points)):
                j = (i + 1) % len(data_points)
                x1, y1 = data_points[i]
                x2, y2 = data_points[j]
                if self.use_gradient:
                    seg_len = math.hypot(x2 - x1, y2 - y1)
                    num_sub = max(10, int(seg_len / 5))
                    for sub in range(num_sub):
                        t1 = sub / num_sub
                        t2 = (sub + 1) / num_sub
                        global_t1 = (i + t1) / num_axes
                        global_t2 = (i + t2) / num_axes
                        color1 = self._get_point_color(i, global_t1)
                        sub_x1 = x1 + (x2 - x1) * t1
                        sub_y1 = y1 + (y2 - y1) * t1
                        sub_x2 = x1 + (x2 - x1) * t2
                        sub_y2 = y1 + (y2 - y1) * t2
                        renderer.draw_line(sub_x1, sub_y1, sub_x2, sub_y2, color1, 2)
                else:
                    renderer.draw_line(x1, y1, x2, y2, self._get_color(i), 2)

            for i, (x, y) in enumerate(data_points):
                color = self._get_point_color(i, i/num_axes) if self.use_gradient else self._get_color(i)
                renderer.draw_circle(x, y, 4, color)

    def _render_legend(self, renderer, x, y, theme):
        item_width = 80
        start_x = x + self.padding
        for i, label in enumerate(self.labels[:5]):
            color = self._get_point_color(i) if self.use_gradient else self._get_color(i)
            renderer.draw_rect(start_x + i * item_width, y, 12, 12, color)
            renderer.draw_text(label[:10], start_x + i * item_width + 15, y + 6,
                               theme.text_secondary.color, self.legend_font, anchor_point=(0, 0.5))        


class AudioVisualizer(UIElement):
    """
    Real-time audio visualization element that displays audio data in various styles.
    
    Supports multiple visualization modes and can connect to OpenAL audio sources.
    
    Attributes:
        style (str): Visualization style ('bars', 'waveform', 'circle', 'particles', 'spectrum')
        source: OpenAL audio source to visualize
        color_gradient (List[Tuple[int, int, int]]): Colors for gradient visualization
        bar_width (int): Width of bars in bar mode
        bar_spacing (int): Spacing between bars
        sensitivity (float): Audio sensitivity/amplification
        smoothing (float): Smoothing factor for transitions
    """
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 style: Literal['bars', 'waveform', 'circle', 'particles', 'spectrum'] = 'bars',
                 source = None,
                 color_gradient: Optional[List[Tuple[int, int, int]]] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        
        self.style = style
        self.source = source
        self.theme_type = theme or ThemeManager.get_current_theme()
        
        self.audio_data = []
        self.fft_data = []
        self.peak_history = []
        self.smoothed_data = []
        
        self.num_bars = 64
        self.bar_width = max(2, width // self.num_bars)
        self.bar_spacing = 1
        self.circle_radius = min(width, height) // 2 - 10
        self.circle_thickness = 2
        self.num_particles = 100
        self.sensitivity = 1.5
        self.smoothing = 0.7
        self.decay_rate = 0.95
        self.max_history = 30
        
        if color_gradient:
            self.color_gradient = color_gradient
        else:
            theme_obj = ThemeManager.get_theme(self.theme_type)
            # Get button_normal color (RGB tuple)
            if hasattr(theme_obj, 'button_normal') and theme_obj.button_normal:
                base_color = theme_obj.button_normal.color
            else:
                base_color = (100, 150, 255)
            self.color_gradient = [
                tuple(max(0, c - 100) for c in base_color),
                base_color,
                tuple(min(255, c + 100) for c in base_color)
            ]
        
        self._last_update = 0
        self._update_interval = 0.016
        
        self._initialize_audio_data()
        self._gradient_surface = None
        self._generate_gradient_surface()
    
    def _initialize_audio_data(self):
        self.audio_data = [0.0] * self.num_bars
        self.fft_data = [0.0] * self.num_bars
        self.peak_history = []
        self.smoothed_data = [0.0] * self.num_bars
    
    def _generate_gradient_surface(self):
        height = 100
        self._gradient_surface = pygame.Surface((1, height), pygame.SRCALPHA)
        for y in range(height):
            ratio = y / height
            color = self._interpolate_gradient(ratio)
            self._gradient_surface.set_at((0, y), color)
    
    def _interpolate_gradient(self, ratio: float) -> Tuple[int, int, int]:
        if len(self.color_gradient) == 1:
            return self.color_gradient[0]
        
        exact_pos = ratio * (len(self.color_gradient) - 1)
        segment = int(exact_pos)
        segment_ratio = exact_pos - segment
        
        if segment >= len(self.color_gradient) - 1:
            return self.color_gradient[-1]
        
        color1 = np.array(self.color_gradient[segment], dtype=np.float32)
        color2 = np.array(self.color_gradient[segment + 1], dtype=np.float32)
        interpolated = color1 + (color2 - color1) * segment_ratio
        return tuple(np.clip(interpolated, 0, 255).astype(int))
    
    def set_style(self, style: str):
        self.style = style
        self._initialize_audio_data()
    
    def set_source(self, source):
        self.source = source
    
    def set_color_gradient(self, gradient: List[Tuple[int, int, int]]):
        self.color_gradient = gradient
        self._generate_gradient_surface()
    
    def set_sensitivity(self, sensitivity: float):
        self.sensitivity = max(0.1, min(5.0, sensitivity))
    
    def set_smoothing(self, smoothing: float):
        self.smoothing = max(0.0, min(1.0, smoothing))
    
    def _get_audio_data(self) -> List[float]:
        current_time = pygame.time.get_ticks() / 1000.0
        
        if self.source and hasattr(self.source, 'is_playing') and self.source.is_playing():
            data = []
            for i in range(self.num_bars):
                base_freq = 0.1 + (i / self.num_bars) * 2.0
                value = (math.sin(current_time * base_freq * math.pi * 2) * 0.5 + 0.5)
                value *= (1.0 - (i / self.num_bars) * 0.3)
                value += np.random.uniform(-0.05, 0.05)
                data.append(max(0.0, min(1.0, value * self.sensitivity)))
        else:
            data = []
            for i in range(self.num_bars):
                idle_freq = 0.5
                idle_value = (math.sin(current_time * idle_freq + i * 0.1) * 0.2 + 0.3)
                data.append(idle_value)
        
        return data
    
    def _process_audio_data(self, raw_data: List[float]):
        for i in range(len(raw_data)):
            smoothed = self.smoothed_data[i] * self.smoothing + raw_data[i] * (1 - self.smoothing)
            self.smoothed_data[i] = smoothed
        
        self.peak_history.append(raw_data[:])
        if len(self.peak_history) > self.max_history:
            self.peak_history.pop(0)
        
        if len(self.peak_history) > 1:
            for i in range(self.num_bars):
                decayed_value = self.peak_history[-2][i] * self.decay_rate
                self.peak_history[-1][i] = max(self.peak_history[-1][i], decayed_value)
    
    def update(self, dt: float, inputState: InputState):
        super().update(dt, inputState)
        current_time = time.time()
        if current_time - self._last_update >= self._update_interval:
            audio_data = self._get_audio_data()
            self._process_audio_data(audio_data)
            self._last_update = current_time
    
    def render(self, renderer: Renderer):
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        border_color = theme.border.color if theme.border else (50, 50, 70)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, 
                         border_color, fill=False, border_width=self.border_width)
        
        bg_color = theme.background.color if theme.background else (20, 20, 30)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color, border_width=self.border_width)
        
        if self.style == 'bars':
            self._render_bars(renderer, actual_x, actual_y)
        elif self.style == 'waveform':
            self._render_waveform(renderer, actual_x, actual_y)
        elif self.style == 'circle':
            self._render_circle(renderer, actual_x, actual_y)
        elif self.style == 'particles':
            self._render_particles(renderer, actual_x, actual_y)
        elif self.style == 'spectrum':
            self._render_spectrum(renderer, actual_x, actual_y)
        
        super().render(renderer)
    
    def _render_bars(self, renderer: Renderer, x: int, y: int):
        if not self.smoothed_data:
            return
        
        total_bars = min(self.num_bars, len(self.smoothed_data))
        available_width = self.width - (total_bars - 1) * self.bar_spacing
        bar_width = available_width // total_bars
        
        for i in range(total_bars):
            value = self.smoothed_data[i]
            bar_height = int(value * self.height)
            
            bar_x = x + i * (bar_width + self.bar_spacing)
            bar_y = y + self.height - bar_height
            
            color = self._get_bar_color(value)
            renderer.draw_rect(bar_x, bar_y, bar_width, bar_height, color, border_width=0)
            
            if bar_height > 2:
                highlight_color = tuple(min(255, c + 30) for c in color)
                renderer.draw_rect(bar_x, bar_y, bar_width, 2, highlight_color)
    
    def _render_waveform(self, renderer: Renderer, x: int, y: int):
        if not self.smoothed_data:
            return
        
        center_y = y + self.height // 2
        points = []
        
        for i, value in enumerate(self.smoothed_data):
            point_x = x + (i / len(self.smoothed_data)) * self.width
            point_y = center_y - (value - 0.5) * self.height
            points.append((point_x, point_y))
        
        if len(points) > 1:
            for i in range(len(points) - 1):
                color = self._get_waveform_color(i / len(points))
                renderer.draw_line(points[i][0], points[i][1], 
                                 points[i + 1][0], points[i + 1][1], 
                                 color, 2)
        
        center_color = tuple(c // 2 for c in self.color_gradient[1])
        renderer.draw_line(x, center_y, x + self.width, center_y, center_color, 1)
    
    def _render_circle(self, renderer: Renderer, x: int, y: int):
        if not self.smoothed_data:
            return
        
        center_x = x + self.width // 2
        center_y = y + self.height // 2
        radius = min(self.circle_radius, min(self.width, self.height) // 2 - 10)
        
        base_color = tuple(c // 4 for c in self.color_gradient[1])
        renderer.draw_circle(center_x, center_y, radius, base_color, fill=False, border_width=1)
        
        points = []
        num_points = len(self.smoothed_data)
        
        for i, value in enumerate(self.smoothed_data):
            angle = (i / num_points) * 2 * math.pi
            response_radius = radius + value * radius * 0.5
            point_x = center_x + response_radius * math.cos(angle)
            point_y = center_y + response_radius * math.sin(angle)
            points.append((point_x, point_y))
        
        if len(points) > 2:
            for i in range(len(points)):
                color = self._get_circle_color(i / len(points))
                start_point = points[i]
                end_point = points[(i + 1) % len(points)]
                renderer.draw_line(start_point[0], start_point[1],
                                 end_point[0], end_point[1],
                                 color, self.circle_thickness)
        
        dot_radius = 3
        center_value = sum(self.smoothed_data) / len(self.smoothed_data)
        dot_color = self._get_circle_color(center_value)
        renderer.draw_circle(center_x, center_y, dot_radius, dot_color)
    
    def _render_particles(self, renderer: Renderer, x: int, y: int):
        if not self.smoothed_data:
            return
        
        center_x = x + self.width // 2
        center_y = y + self.height // 2
        max_radius = min(self.width, self.height) // 2 - 10
        
        for i in range(self.num_particles):
            data_index = int((i / self.num_particles) * len(self.smoothed_data))
            value = self.smoothed_data[data_index]
            angle = (i / self.num_particles) * 2 * math.pi
            radius = value * max_radius
            particle_x = center_x + radius * math.cos(angle)
            particle_y = center_y + radius * math.sin(angle)
            particle_size = max(1, int(value * 5))
            particle_color = self._get_particle_color(value, i)
            renderer.draw_circle(particle_x, particle_y, particle_size, particle_color)
            
            if i > 0:
                prev_index = int(((i - 1) / self.num_particles) * len(self.smoothed_data))
                prev_value = self.smoothed_data[prev_index]
                prev_radius = prev_value * max_radius
                prev_x = center_x + prev_radius * math.cos((i - 1) / self.num_particles * 2 * math.pi)
                prev_y = center_y + prev_radius * math.sin((i - 1) / self.num_particles * 2 * math.pi)
                trail_color = tuple(min(255, c + 50) for c in particle_color)
                renderer.draw_line(prev_x, prev_y, particle_x, particle_y, trail_color, 1)
    
    def _render_spectrum(self, renderer: Renderer, x: int, y: int):
        if not self.smoothed_data:
            return
        
        spectrum_data = sorted(self.smoothed_data)
        points = [(x, y + self.height)]
        
        for i, value in enumerate(spectrum_data):
            point_x = x + (i / len(spectrum_data)) * self.width
            point_y = y + self.height - (value * self.height)
            points.append((point_x, point_y))
        
        points.append((x + self.width, y + self.height))
        
        if len(points) > 2:
            fill_color = tuple(min(255, c + 30) for c in self.color_gradient[1])
            renderer.draw_polygon(points, fill_color)
        
        line_points = points[1:-1]
        if len(line_points) > 1:
            for i in range(len(line_points) - 1):
                color = self._get_spectrum_color(i / len(line_points))
                renderer.draw_line(line_points[i][0], line_points[i][1],
                                 line_points[i + 1][0], line_points[i + 1][1],
                                 color, 2)
    
    def _get_bar_color(self, value: float) -> Tuple[int, int, int]:
        if self._gradient_surface:
            y_pos = int((1.0 - value) * (self._gradient_surface.get_height() - 1))
            color = self._gradient_surface.get_at((0, y_pos))
            return color[:3]
        else:
            return self._interpolate_gradient(1.0 - value)
    
    def _get_waveform_color(self, position: float) -> Tuple[int, int, int]:
        base_color = self.color_gradient[1]
        variation = math.sin(position * math.pi * 2) * 30
        return tuple(max(0, min(255, c + int(variation))) for c in base_color)
    
    def _get_circle_color(self, position: float) -> Tuple[int, int, int]:
        gradient_pos = (position + time.time() * 0.1) % 1.0
        return self._interpolate_gradient(gradient_pos)
    
    def _get_particle_color(self, value: float, index: int) -> Tuple[int, int, int]:
        base_color = self.color_gradient[index % len(self.color_gradient)]
        pulse = (math.sin(time.time() * 2 + index * 0.1) * 0.3 + 0.7)
        return tuple(int(c * pulse * value) for c in base_color)
    
    def _get_spectrum_color(self, frequency: float) -> Tuple[int, int, int]:
        if frequency < 0.33:
            r = 0
            g = int(frequency * 3 * 255)
            b = 255 - int(frequency * 3 * 255)
        elif frequency < 0.66:
            r = int((frequency - 0.33) * 3 * 255)
            g = 255
            b = 0
        else:
            r = 255
            g = 255 - int((frequency - 0.66) * 3 * 255)
            b = 0
        return (r, g, b)