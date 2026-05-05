import pygame
import time
import math
from typing import Optional, Tuple, Literal
from .base import *
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer

class Clock(UIElement):
    """
    A clock UI element that can display both analog and digital time.
    
    Supports both 12-hour and 24-hour formats, real-time or custom time,
    and various customization options.
    
    Attributes:
        diameter (int): Diameter of the analog clock face.
        use_real_time (bool): Whether to use the system's real time.
        show_numbers (bool): Whether to show numbers on the analog clock.
        time_style (str): '12hr' or '24hr' format.
        mode (str): 'analog', 'digital', or 'both'.
        custom_time (datetime): Custom time to display (if not using real time).
    """
    
    def __init__(self, x: int, y: int, diameter: int = 100, 
                 font_name: Optional[str] = None, font_size: int = 16,
                 use_real_time: bool = True, show_numbers: bool = True,
                 time_style: Literal['12hr', '24hr'] = '24hr',
                 mode: Literal['analog', 'digital', 'both'] = 'analog',
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        """
        Initialize a Clock element.
        
        Args:
            x (int): X coordinate position.
            y (int): Y coordinate position.
            diameter (int): Diameter of the analog clock face.
            font_name (Optional[str]): Font for digital display and numbers.
            font_size (int): Font size for digital display.
            use_real_time (bool): Whether to use system time.
            show_numbers (bool): Whether to show numbers on analog clock.
            time_style (str): '12hr' or '24hr' format.
            mode (str): 'analog', 'digital', or 'both'.
            root_point (Tuple[float, float]): Anchor point for positioning.
            theme (ThemeType): Theme for styling.
            element_id (Optional[str]): Custom element ID.
        """
        # Calculate width and height based on mode
        if mode == 'analog':
            width = height = diameter
        elif mode == 'digital':
            width = 120  # Default width for digital clock
            height = 40  # Default height for digital clock
        else:  # 'both'
            width = max(diameter, 120)
            height = diameter + 50  # Clock face + digital display
        
        super().__init__(x, y, width, height, root_point, element_id)
        
        # Clock properties
        self.diameter = diameter
        self.use_real_time = use_real_time
        self.show_numbers = show_numbers
        self.time_style = time_style
        self.mode = mode
        self.font_name = font_name
        self.font_size = font_size
        
        # Time properties
        self.custom_time = None
        self.current_time = time.time()
        self.last_update = 0
        
        # Styling
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.face_color = None
        self.border_color = None
        self.hour_hand_color = None
        self.minute_hand_color = None
        self.second_hand_color = None
        self.number_color = None
        self.digital_text_color = None
        
        # Font
        self._font = None
        self._small_font = None  # For numbers on analog clock
        
        # Update colors from theme
        self.update_theme(self.theme_type)
        
        # If not using real time, set to current time
        if not use_real_time:
            self.set_time(time.localtime())
    
    @property
    def font(self):
        """Get the main font object."""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    @property
    def small_font(self):
        """Get the smaller font for analog clock numbers."""
        if self._small_font is None:
            FontManager.initialize()
            self._small_font = FontManager.get_font(self.font_name, max(10, self.font_size - 4))
        return self._small_font
    
    def update_theme(self, theme_type: ThemeType):
        """Update theme colors for the clock."""
        super().update_theme(theme_type)
        theme = ThemeManager.get_theme(theme_type)
        
        # Set default colors from theme (use .color on ThemeStyle objects)
        self.face_color = theme.background.color if hasattr(theme, 'background') else (240, 240, 240)
        self.border_color = theme.border.color if (hasattr(theme, 'border') and theme.border) else (100, 100, 100)
        self.hour_hand_color = theme.button_pressed.color if hasattr(theme, 'button_pressed') else (0, 0, 0)
        self.minute_hand_color = theme.button_hover.color if hasattr(theme, 'button_hover') else (50, 50, 50)
        self.second_hand_color = theme.button_normal.color if hasattr(theme, 'button_normal') else (255, 0, 0)
        self.number_color = theme.text_primary.color if hasattr(theme, 'text_primary') else (0, 0, 0)
        self.digital_text_color = theme.text_primary.color if hasattr(theme, 'text_primary') else (0, 0, 0)
    
    def set_face_color(self, color: Tuple[int, int, int]):
        """Set the clock face color."""
        self.face_color = color
    
    def set_border_color(self, color: Tuple[int, int, int]):
        """Set the clock border color."""
        self.border_color = color
    
    def set_hand_colors(self, hour: Tuple[int, int, int], 
                        minute: Tuple[int, int, int], 
                        second: Tuple[int, int, int]):
        """Set the colors for clock hands."""
        self.hour_hand_color = hour
        self.minute_hand_color = minute
        self.second_hand_color = second
    
    def set_number_color(self, color: Tuple[int, int, int]):
        """Set the color for analog clock numbers."""
        self.number_color = color
    
    def set_digital_text_color(self, color: Tuple[int, int, int]):
        """Set the color for digital display text."""
        self.digital_text_color = color
    
    def set_time(self, time_struct: time.struct_time):
        """
        Set a custom time for the clock.
        
        Args:
            time_struct (time.struct_time): Time structure from time.localtime()
        """
        self.custom_time = time_struct
        self.current_time = time.mktime(time_struct)
    
    def set_time_from_string(self, time_str: str, format_str: str = "%H:%M:%S"):
        """
        Set time from a string.
        
        Args:
            time_str (str): Time string.
            format_str (str): Format string for parsing.
        """
        try:
            import datetime
            dt = datetime.datetime.strptime(time_str, format_str)
            self.set_time(dt.timetuple())
        except ValueError:
            print(f"Invalid time string: {time_str}")
    
    def get_time_string(self) -> str:
        """Get the current time as a formatted string."""
        if self.custom_time:
            tm = self.custom_time
        else:
            tm = time.localtime(self.current_time)
        
        if self.time_style == '12hr':
            # Convert to 12-hour format
            hour = tm.tm_hour % 12
            if hour == 0:
                hour = 12
            am_pm = "AM" if tm.tm_hour < 12 else "PM"
            return f"{hour:02d}:{tm.tm_min:02d}:{tm.tm_sec:02d} {am_pm}"
        else:
            # 24-hour format
            return f"{tm.tm_hour:02d}:{tm.tm_min:02d}:{tm.tm_sec:02d}"
    
    def update(self, dt: float, inputState: InputState):
        """Update the clock time."""
        super().update(dt, inputState)
        
        # Update time if using real time
        if self.use_real_time and not self.custom_time:
            current = time.time()
            # Only update if at least 0.1 seconds have passed (for performance)
            if current - self.last_update >= 0.1:
                self.current_time = current
                self.last_update = current
    
    def render(self, renderer: Renderer):
        """Render the clock."""
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        
        if self.mode in ['analog', 'both']:
            self._render_analog_clock(renderer, actual_x, actual_y)
        
        if self.mode in ['digital', 'both']:
            self._render_digital_clock(renderer, actual_x, actual_y)
        
        # Render children
        super().render(renderer)
    
    def _render_analog_clock(self, renderer: Renderer, x: int, y: int):
        """Render the analog clock face and hands."""
        # Calculate center and radius
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
        # Convert to radians: 0 radians is at 3 o'clock, we want 0 at 12 o'clock
        # So subtract 90 degrees (π/2 radians)
        
        # Second hand: 6 degrees per second
        second_angle = math.radians(tm.tm_sec * 6 - 90)
        
        # Minute hand: 6 degrees per minute + 0.1 degrees per second
        minute_angle = math.radians(tm.tm_min * 6 + tm.tm_sec * 0.1 - 90)
        
        # Hour hand: 30 degrees per hour + 0.5 degrees per minute
        hour_angle = math.radians((tm.tm_hour % 12) * 30 + tm.tm_min * 0.5 - 90)
        
        # Draw hands
        self._draw_hand(renderer, center_x, center_y, hour_angle, 
                       radius * 0.5, 6, self.hour_hand_color)  # Hour hand
        self._draw_hand(renderer, center_x, center_y, minute_angle, 
                       radius * 0.7, 4, self.minute_hand_color)  # Minute hand
        self._draw_hand(renderer, center_x, center_y, second_angle, 
                       radius * 0.9, 2, self.second_hand_color)  # Second hand
        
        # Draw center dot
        renderer.draw_circle(center_x, center_y, 4, self.second_hand_color)
    
    def _draw_clock_numbers(self, renderer: Renderer, center_x: int, center_y: int, radius: int):
        """Draw numbers around the clock face."""
        for hour in range(1, 13):
            # Calculate angle for this hour (in radians)
            angle = math.radians(hour * 30 - 90)  # 30 degrees per hour, offset by -90
            
            # Calculate position (slightly inside the border)
            num_radius = radius * 0.8
            x = center_x + num_radius * math.cos(angle)
            y = center_y + num_radius * math.sin(angle)
            
            renderer.draw_text(str(hour), x, y, self.number_color, self.small_font, anchor_point=(0.5, 0.5))
    
    def _draw_tick_marks(self, renderer: Renderer, center_x: int, center_y: int, radius: int):
        """Draw tick marks for minutes/seconds."""
        for minute in range(0, 60):
            angle = math.radians(minute * 6 - 90)  # 6 degrees per minute
            
            # Calculate start and end points for tick mark
            outer_radius = radius * 0.95
            inner_radius = radius * 0.9 if minute % 5 == 0 else radius * 0.92
            
            x1 = center_x + inner_radius * math.cos(angle)
            y1 = center_y + inner_radius * math.sin(angle)
            x2 = center_x + outer_radius * math.cos(angle)
            y2 = center_y + outer_radius * math.sin(angle)
            
            # Draw thicker lines for 5-minute marks
            thickness = 2 if minute % 5 == 0 else 1
            color = self.number_color
            
            if hasattr(renderer, 'draw_line'):
                renderer.draw_line(int(x1), int(y1), int(x2), int(y2), color, thickness)
            else:
                # Fallback: draw a thin rectangle
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    # Calculate perpendicular vector for thickness
                    perp_x = -dy / length * thickness / 2
                    perp_y = dx / length * thickness / 2
                    
                    # Create polygon points
                    points = [
                        (x1 + perp_x, y1 + perp_y),
                        (x1 - perp_x, y1 - perp_y),
                        (x2 - perp_x, y2 - perp_y),
                        (x2 + perp_x, y2 + perp_y)
                    ]
                    
                    if hasattr(renderer, 'draw_polygon'):
                        renderer.draw_polygon(points, color)
    
    def _draw_hand(self, renderer: Renderer, center_x: int, center_y: int, 
                  angle: float, length: float, width: int, color: Tuple[int, int, int]):
        """Draw a clock hand."""
        # Calculate end point
        x = center_x + length * math.cos(angle)
        y = center_y + length * math.sin(angle)
        
        if hasattr(renderer, 'draw_line'):
            # Draw line from center to end point
            renderer.draw_line(center_x, center_y, int(x), int(y), color, width)
        else:
            # Draw as polygon for better quality
            # Calculate perpendicular vector for width
            dx = x - center_x
            dy = y - center_y
            hand_length = math.sqrt(dx*dx + dy*dy)
            
            if hand_length > 0:
                # Normalize direction vector
                dx /= hand_length
                dy /= hand_length
                
                # Calculate perpendicular vector
                perp_x = -dy * width / 2
                perp_y = dx * width / 2
                
                # Create polygon points
                points = [
                    (center_x + perp_x, center_y + perp_y),
                    (center_x - perp_x, center_y - perp_y),
                    (x - perp_x * 0.5, y - perp_y * 0.5),  # Taper the end
                    (x + perp_x * 0.5, y + perp_y * 0.5)
                ]
                
                if hasattr(renderer, 'draw_polygon'):
                    renderer.draw_polygon(points, color)
    
    def _render_digital_clock(self, renderer: Renderer, x: int, y: int):
        """Render the digital clock display."""
        time_str = self.get_time_string()
        
        if self.mode == 'digital':
            # Center in the element
            center_x = x + self.width // 2
            center_y = y + self.height // 2
            
            # Draw border
            if self.border_color:
                renderer.draw_rect(x, y, self.width, self.height, 
                                 self.border_color, fill=False, border_width=self.border_width)
            
            # Draw background
            renderer.draw_rect(x, y, self.width, self.height, self.face_color, border_width=self.border_width)
            
            # Draw time text
            renderer.draw_text(time_str, center_x, center_y, 
                             self.digital_text_color, self.font, 
                             anchor_point=(0.5, 0.5))
        
        elif self.mode == 'both':
            # Position below analog clock
            digital_y = y + self.diameter + 10
            digital_x = x + self.diameter // 2
            
            # Draw time text
            renderer.draw_text(time_str, digital_x, digital_y, 
                             self.digital_text_color, self.font, 
                             anchor_point=(0.5, 0))