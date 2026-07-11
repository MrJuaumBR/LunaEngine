import pygame
import time
import math
from typing import Optional, Tuple, Literal, Dict, Any, Union
from .base import *
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer

class Clock(UIElement):
    """
    A clock UI element that can display both analog and digital time.
    
    Supports both 12-hour and 24-hour formats, real-time or custom time,
    and various customization options.
    """
    
    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'diameter': {'name': 'diameter', 'key': 'diameter', 'type': int, 'editable': True,
                     'description': 'Diameter of the analog clock face in pixels.'},
        'use_real_time': {'name': 'use real time', 'key': 'use_real_time', 'type': bool, 'editable': True,
                          'description': 'If True, uses system time. If False, use custom time set via set_time().'},
        'show_numbers': {'name': 'show numbers', 'key': 'show_numbers', 'type': bool, 'editable': True,
                         'description': 'Whether to show hour numbers on the analog clock face.'},
        'time_style': {'name': 'time style', 'key': 'time_style', 'type': str, 'editable': True,
                       'description': 'Format: "12hr" or "24hr".', 'options': ['12hr', '24hr']},
        'mode': {'name': 'mode', 'key': 'mode', 'type': str, 'editable': True,
                 'description': 'Display mode: "analog", "digital", or "both".', 'options': ['analog', 'digital', 'both']},
        'font_size': {'name': 'font size', 'key': 'font_size', 'type': int, 'editable': True,
                      'description': 'Font size for digital display and numbers.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        diameter: int = 100,
        font_name: Optional[str] = None,
        font_size: int = 16,
        use_real_time: bool = True,
        show_numbers: bool = True,
        time_style: Literal['12hr', '24hr'] = '24hr',
        mode: Literal['analog', 'digital', 'both'] = 'analog',
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        """
        Initialize a Clock element.

        Args:
            x: X coordinate (before anchor).
            y: Y coordinate (before anchor).
            diameter: Diameter of the analog clock face.
            font_name: Path to a custom font file.
            font_size: Font size for digital display.
            use_real_time: Whether to use system time.
            show_numbers: Whether to show numbers on analog clock.
            time_style: '12hr' or '24hr' format.
            mode: 'analog', 'digital', or 'both'.
            pivot: Anchor point.
            theme: Theme to apply.
            element_id: Optional custom ID.
        """
        # Calculate width and height based on mode
        if mode == 'analog':
            width = height = diameter
        elif mode == 'digital':
            width = 120   # default width for digital clock
            height = 40   # default height for digital clock
        else:  # 'both'
            width = max(diameter, 120)
            height = diameter + 50   # clock face + digital display

        super().__init__(x, y, width, height, pivot, element_id)

        # Clock properties
        self.diameter = diameter
        self.use_real_time = use_real_time
        self.show_numbers = show_numbers
        self.time_style = time_style
        self.mode = mode
        self.font_name = font_name
        self.font_size = font_size

        # Time properties
        self.custom_time: Optional[time.struct_time] = None
        self.current_time = time.time()
        self.last_update = 0.0

        # Styling
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.face_color: Optional[Tuple[int, int, int]] = None
        self.border_color: Optional[Tuple[int, int, int]] = None
        self.hour_hand_color: Optional[Tuple[int, int, int]] = None
        self.minute_hand_color: Optional[Tuple[int, int, int]] = None
        self.second_hand_color: Optional[Tuple[int, int, int]] = None
        self.number_color: Optional[Tuple[int, int, int]] = None
        self.digital_text_color: Optional[Tuple[int, int, int]] = None

        # Fonts
        self._font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None   # for analog clock numbers

        # Update colors from theme
        self.update_theme(self.theme_type)

        # If not using real time, set to current time as initial custom time
        if not use_real_time:
            self.set_time(time.localtime())

    def _get_init_args(self) -> Dict[str, Any]:
        """Return constructor arguments for restarting."""
        return {
            'x': self.x,
            'y': self.y,
            'diameter': self.diameter,
            'font_name': self.font_name,
            'font_size': self.font_size,
            'use_real_time': self.use_real_time,
            'show_numbers': self.show_numbers,
            'time_style': self.time_style,
            'mode': self.mode,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    @property
    def font(self) -> pygame.font.Font:
        """Get the main font object (digital display)."""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    @property
    def small_font(self) -> pygame.font.Font:
        """Get the smaller font for analog clock numbers."""
        if self._small_font is None:
            FontManager.initialize()
            self._small_font = FontManager.get_font(self.font_name, max(10, self.font_size - 4))
        return self._small_font

    def update_theme(self, theme_type: ThemeType) -> None:
        """Update theme colors for the clock."""
        super().update_theme(theme_type)
        theme = ThemeManager.get_theme(theme_type)

        # Set default colors from theme
        self.face_color = theme.background.color if hasattr(theme, 'background') else (240, 240, 240)
        self.border_color = theme.border.color if (hasattr(theme, 'border') and theme.border) else (100, 100, 100)
        self.hour_hand_color = theme.button_pressed.color if hasattr(theme, 'button_pressed') else (0, 0, 0)
        self.minute_hand_color = theme.button_hover.color if hasattr(theme, 'button_hover') else (50, 50, 50)
        self.second_hand_color = theme.button_normal.color if hasattr(theme, 'button_normal') else (255, 0, 0)
        self.number_color = theme.text_primary.color if hasattr(theme, 'text_primary') else (0, 0, 0)
        self.digital_text_color = theme.text_primary.color if hasattr(theme, 'text_primary') else (0, 0, 0)

    def set_face_color(self, color: Tuple[int, int, int]) -> None:
        """Set the clock face color (RGB)."""
        self.face_color = color

    def set_border_color(self, color: Tuple[int, int, int]) -> None:
        """Set the clock border color (RGB)."""
        self.border_color = color

    def set_hand_colors(self, hour: Tuple[int, int, int], minute: Tuple[int, int, int], second: Tuple[int, int, int]) -> None:
        """Set the colors for clock hands (hour, minute, second) as RGB tuples."""
        self.hour_hand_color = hour
        self.minute_hand_color = minute
        self.second_hand_color = second

    def set_number_color(self, color: Tuple[int, int, int]) -> None:
        """Set the color for analog clock numbers (RGB)."""
        self.number_color = color

    def set_digital_text_color(self, color: Tuple[int, int, int]) -> None:
        """Set the color for digital display text (RGB)."""
        self.digital_text_color = color

    def set_time(self, time_struct: time.struct_time) -> None:
        """
        Set a custom time for the clock.

        Args:
            time_struct: Time structure from time.localtime().
        """
        self.custom_time = time_struct
        self.current_time = time.mktime(time_struct)

    def set_time_from_string(self, time_str: str, format_str: str = "%H:%M:%S") -> None:
        """
        Set time from a string.

        Args:
            time_str: Time string (e.g., "14:30:00").
            format_str: Format string for parsing (default "%H:%M:%S").
        """
        try:
            import datetime
            dt = datetime.datetime.strptime(time_str, format_str)
            self.set_time(dt.timetuple())
        except ValueError:
            print(f"Invalid time string: {time_str}")

    def get_time_string(self) -> str:
        """Get the current time as a formatted string according to time_style."""
        if self.custom_time:
            tm = self.custom_time
        else:
            tm = time.localtime(self.current_time)

        if self.time_style == '12hr':
            hour = tm.tm_hour % 12
            if hour == 0:
                hour = 12
            am_pm = "AM" if tm.tm_hour < 12 else "PM"
            return f"{hour:02d}:{tm.tm_min:02d}:{tm.tm_sec:02d} {am_pm}"
        else:   # 24-hour format
            return f"{tm.tm_hour:02d}:{tm.tm_min:02d}:{tm.tm_sec:02d}"

    def update(self, dt: float, inputState: InputState) -> None:
        """Update the clock time."""
        super().update(dt, inputState)

        if self.use_real_time and not self.custom_time:
            current = time.time()
            # Update only if at least 0.1 seconds have passed (for performance)
            if current - self.last_update >= 0.1:
                self.current_time = current
                self.last_update = current

    def render(self, renderer: Renderer) -> None:
        """Render the clock."""
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()

        if self.mode in ['analog', 'both']:
            self._render_analog_clock(renderer, actual_x, actual_y)

        if self.mode in ['digital', 'both']:
            self._render_digital_clock(renderer, actual_x, actual_y)

        super().render(renderer)

    def _render_analog_clock(self, renderer: Renderer, x: int, y: int) -> None:
        """Render the analog clock face and hands."""
        center_x = x + self.diameter // 2
        center_y = y + self.diameter // 2
        radius = self.diameter // 2

        # Draw border
        if self.border_color:
            renderer.draw_circle(center_x, center_y, radius, self.border_color,
                                 fill=False, border_width=self.border_width)
        # Draw clock face
        renderer.draw_circle(center_x, center_y, radius, self.face_color, border_width=self.border_width)

        # Draw numbers if enabled
        if self.show_numbers:
            self._draw_clock_numbers(renderer, center_x, center_y, radius)

        # Draw tick marks
        self._draw_tick_marks(renderer, center_x, center_y, radius)

        # Get current time
        if self.custom_time:
            tm = self.custom_time
        else:
            tm = time.localtime(self.current_time)

        # Calculate hand angles (in radians)
        # 0 radians = 3 o'clock, subtract 90° (π/2) to have 0 at 12 o'clock
        second_angle = math.radians(tm.tm_sec * 6 - 90)
        minute_angle = math.radians(tm.tm_min * 6 + tm.tm_sec * 0.1 - 90)
        hour_angle = math.radians((tm.tm_hour % 12) * 30 + tm.tm_min * 0.5 - 90)

        # Draw hands
        self._draw_hand(renderer, center_x, center_y, hour_angle,
                        radius * 0.5, 6, self.hour_hand_color)   # hour
        self._draw_hand(renderer, center_x, center_y, minute_angle,
                        radius * 0.7, 4, self.minute_hand_color)  # minute
        self._draw_hand(renderer, center_x, center_y, second_angle,
                        radius * 0.9, 2, self.second_hand_color)  # second

        # Center dot
        renderer.draw_circle(center_x, center_y, 4, self.second_hand_color)

    def _draw_clock_numbers(self, renderer: Renderer, center_x: int, center_y: int, radius: int) -> None:
        """Draw numbers 1-12 around the clock face."""
        for hour in range(1, 13):
            angle = math.radians(hour * 30 - 90)   # 30° per hour, offset -90°
            num_radius = radius * 0.8
            x = center_x + num_radius * math.cos(angle)
            y = center_y + num_radius * math.sin(angle)
            renderer.draw_text(str(hour), x, y, self.number_color, self.small_font, pivot=(0.5, 0.5))

    def _draw_tick_marks(self, renderer: Renderer, center_x: int, center_y: int, radius: int) -> None:
        """Draw tick marks for minutes/seconds."""
        for minute in range(0, 60):
            angle = math.radians(minute * 6 - 90)   # 6° per minute
            outer_radius = radius * 0.95
            inner_radius = radius * 0.9 if minute % 5 == 0 else radius * 0.92

            x1 = center_x + inner_radius * math.cos(angle)
            y1 = center_y + inner_radius * math.sin(angle)
            x2 = center_x + outer_radius * math.cos(angle)
            y2 = center_y + outer_radius * math.sin(angle)

            thickness = 2 if minute % 5 == 0 else 1
            color = self.number_color

            if hasattr(renderer, 'draw_line'):
                renderer.draw_line(int(x1), int(y1), int(x2), int(y2), color, thickness)
            else:
                # Fallback: draw a thin rectangle
                dx = x2 - x1
                dy = y2 - y1
                length = math.hypot(dx, dy)
                if length > 0:
                    perp_x = -dy / length * thickness / 2
                    perp_y = dx / length * thickness / 2
                    points = [
                        (x1 + perp_x, y1 + perp_y),
                        (x1 - perp_x, y1 - perp_y),
                        (x2 - perp_x, y2 - perp_y),
                        (x2 + perp_x, y2 + perp_y)
                    ]
                    if hasattr(renderer, 'draw_polygon'):
                        renderer.draw_polygon(points, color)

    def _draw_hand(self, renderer: Renderer, center_x: int, center_y: int,
                   angle: float, length: float, width: int, color: Tuple[int, int, int]) -> None:
        """Draw a single clock hand."""
        x = center_x + length * math.cos(angle)
        y = center_y + length * math.sin(angle)

        if hasattr(renderer, 'draw_line'):
            renderer.draw_line(center_x, center_y, int(x), int(y), color, width)
        else:
            dx = x - center_x
            dy = y - center_y
            hand_length = math.hypot(dx, dy)
            if hand_length > 0:
                dx /= hand_length
                dy /= hand_length
                perp_x = -dy * width / 2
                perp_y = dx * width / 2
                points = [
                    (center_x + perp_x, center_y + perp_y),
                    (center_x - perp_x, center_y - perp_y),
                    (x - perp_x * 0.5, y - perp_y * 0.5),
                    (x + perp_x * 0.5, y + perp_y * 0.5)
                ]
                if hasattr(renderer, 'draw_polygon'):
                    renderer.draw_polygon(points, color)

    def _render_digital_clock(self, renderer: Renderer, x: int, y: int) -> None:
        """Render the digital clock display."""
        time_str = self.get_time_string()

        if self.mode == 'digital':
            center_x = x + self.width // 2
            center_y = y + self.height // 2

            if self.border_color:
                renderer.draw_rect(x, y, self.width, self.height,
                                   self.border_color, fill=False, border_width=self.border_width)
            renderer.draw_rect(x, y, self.width, self.height, self.face_color, border_width=self.border_width)
            renderer.draw_text(time_str, center_x, center_y, self.digital_text_color,
                               self.font, pivot=(0.5, 0.5))

        elif self.mode == 'both':
            digital_y = y + self.diameter + 10
            digital_x = x + self.diameter // 2
            renderer.draw_text(time_str, digital_x, digital_y, self.digital_text_color,
                               self.font, pivot=(0.5, 0))