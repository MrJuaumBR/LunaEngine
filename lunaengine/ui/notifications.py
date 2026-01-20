"""
notifications.py - Advanced Notification System for LunaEngine

A sophisticated notification system with queue management, multiple positioning options,
animations, and theme integration.
"""

import pygame
import time
import math
from typing import Optional, List, Tuple, Callable, Dict, Any, Union
from enum import Enum, auto
from dataclasses import dataclass
from .elements import UIElement, TextLabel, UiFrame, Button, FontManager, UIState
from .layer_manager import LayerType
from .themes import ThemeManager, ThemeType
from ..backend.types import InputState
from ..misc.icons import IconFactory, Icons, get_icon


class NotificationType(Enum):
    """Types of notifications with different visual styles."""
    SUCCESS = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CUSTOM = auto()


class NotificationPosition(Enum):
    """Pre-defined notification positions."""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    CUSTOM = "custom"  # For custom coordinates


@dataclass
class NotificationStyle:
    """Style configuration for different notification types."""
    
    def __init__(self, 
                 bg_color: Tuple[int, int, int],
                 border_color: Tuple[int, int, int],
                 text_color: Tuple[int, int, int],
                 icon_type: Optional[Icons] = None,
                 duration: float = 5.0,
                 show_icon: bool = True):
        """
        Initialize notification style.
        
        Args:
            bg_color: Background color (RGB)
            border_color: Border color (RGB)
            text_color: Text color (RGB)
            icon_type: Optional icon type from Icons enum
            duration: Default duration in seconds
            show_icon: Whether to show icon
        """
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color
        self.icon_type = icon_type
        self.duration = duration
        self.show_icon = show_icon


@dataclass
class NotificationConfig:
    def __init__(self,
                 text: str,
                 notification_type: NotificationType = NotificationType.INFO,
                 duration: Optional[float] = None,
                 position: Union[NotificationPosition, Tuple[int, int]] = NotificationPosition.TOP_RIGHT,
                 width: int = 300,
                 height: int = 60,
                 show_close_button: bool = True,
                 auto_close: bool = True,
                 animation_speed: float = 0.3,
                 show_progress_bar: bool = False,
                 on_close: Optional[Callable] = None,
                 on_click: Optional[Callable] = None,
                 metadata: Any = None,
                 custom_icon: Optional[Icons] = None):
        """
        Initialize notification configuration.
        
        Args:
            text: Notification text
            notification_type: Type of notification
            duration: Display duration in seconds (None for default based on type)
            position: Position (NotificationPosition enum or custom (x, y) tuple)
            width: Width of notification
            height: Height of notification
            show_close_button: Whether to show close button
            auto_close: Whether notification auto-closes after duration
            animation_speed: Speed of slide/fade animations in seconds
            show_progress_bar: Whether to show progress bar for remaining time
            on_close: Callback when notification is closed
            on_click: Callback when notification is clicked
            metadata: Optional metadata attached to notification
            custom_icon: Optional custom icon
        """
        self.text = text
        self.notification_type = notification_type
        self.duration = duration
        self.position = position
        self.width = width
        self.height = height
        self.show_close_button = show_close_button
        self.auto_close = auto_close
        self.animation_speed = animation_speed
        self.show_progress_bar = show_progress_bar
        self.on_close = on_close
        self.on_click = on_click
        self.metadata = metadata


class Notification(UIElement):
    """Single notification element with advanced positioning and animations."""
    
    # Default styles for each notification type (will be overridden by theme)
    STYLES = {
        NotificationType.SUCCESS: NotificationStyle(
            bg_color=(46, 204, 113),
            border_color=(39, 174, 96),
            text_color=(255, 255, 255),
            icon_type=Icons.SUCCESS,  # Changed from None
            duration=3.0,
            show_icon=True
        ),
        NotificationType.INFO: NotificationStyle(
            bg_color=(52, 152, 219),
            border_color=(41, 128, 185),
            text_color=(255, 255, 255),
            icon_type=Icons.INFO,  # Changed from None
            duration=5.0,
            show_icon=True
        ),
        NotificationType.WARNING: NotificationStyle(
            bg_color=(241, 196, 15),
            border_color=(243, 156, 18),
            text_color=(0, 0, 0),
            icon_type=Icons.WARN,  # Changed from None
            duration=7.0,
            show_icon=True
        ),
        NotificationType.ERROR: NotificationStyle(
            bg_color=(231, 76, 60),
            border_color=(192, 57, 43),
            text_color=(255, 255, 255),
            icon_type=Icons.ERROR,  # Changed from None
            duration=10.0,
            show_icon=True
        ),
        NotificationType.CUSTOM: NotificationStyle(
            bg_color=(149, 165, 166),
            border_color=(127, 140, 141),
            text_color=(255, 255, 255),
            icon_type=Icons.INFO,  # Default to info icon
            duration=5.0,
            show_icon=True  # Changed from False
        )
    }
    
    def __init__(self, config: NotificationConfig, engine: 'LunaEngine', 
                 theme: ThemeType = None, element_id: Optional[str] = None):
        """
        Initialize a notification.
        
        Args:
            config: Notification configuration
            engine: Reference to the engine for screen size
            theme: Theme to use
            element_id: Custom element ID
        """
        self.engine = engine
        self.config = config
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.style = self._get_theme_based_style()
        
        # Calculate final duration
        self.duration = config.duration or self.style.duration
        self.start_time = time.time()
        
        # Animation state
        self.animation_progress = 0.0  # 0.0 to 1.0 for slide-in, 1.0 to 2.0 for slide-out
        self.animation_speed = config.animation_speed
        self.is_showing = False
        self.is_closing = False
        self.is_visible = False
        
        # Position calculation
        self.target_position = self._calculate_target_position()
        self.start_position = self._calculate_start_position()
        
        # Set initial position (off-screen)
        super().__init__(self.start_position[0], self.start_position[1], 
                        config.width, config.height, (0, 0), element_id)
        
        # Display properties
        self.always_on_top = True
        self.render_layer = LayerType.POPUP
        
        # Internal state
        self._is_hovered = False
        self._time_progress = 0.0
        
        # Create child elements
        self._create_ui()
        
        # Apply custom style if provided
        if config.notification_type == NotificationType.CUSTOM:
            self._apply_custom_style()
    
    def _get_theme_based_style(self) -> NotificationStyle:
        """Get notification style based on current theme."""
        # Get the current theme
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Map notification types to theme color names
        color_map = {
            NotificationType.SUCCESS: {
                'bg': 'notification_success_background',
                'border': 'notification_success_border',
                'text': 'notification_success_text'
            },
            NotificationType.INFO: {
                'bg': 'notification_info_background',
                'border': 'notification_info_border',
                'text': 'notification_info_text'
            },
            NotificationType.WARNING: {
                'bg': 'notification_warning_background',
                'border': 'notification_warning_border',
                'text': 'notification_warning_text'
            },
            NotificationType.ERROR: {
                'bg': 'notification_error_background',
                'border': 'notification_error_border',
                'text': 'notification_error_text'
            },
            NotificationType.CUSTOM: {
                'bg': 'notification_custom_background',
                'border': 'notification_custom_border',
                'text': 'notification_custom_text'
            }
        }
        
        # Get the color map for this notification type
        colors = color_map.get(self.config.notification_type, color_map[NotificationType.INFO])
        
        # Get colors from theme
        bg_color = getattr(theme, colors['bg'], (52, 152, 219))
        border_color = getattr(theme, colors['border'], (41, 128, 185))
        text_color = getattr(theme, colors['text'], (255, 255, 255))
        
        # Get base style for duration and show_icon settings
        base_style = self.STYLES.get(self.config.notification_type, self.STYLES[NotificationType.INFO])
        
        # Create new style with theme colors
        return NotificationStyle(
            bg_color=bg_color,
            border_color=border_color,
            text_color=text_color,
            icon_type=base_style.icon_type,
            duration=base_style.duration,
            show_icon=base_style.show_icon
        )
    
    def _calculate_target_position(self) -> Tuple[int, int]:
        """Calculate target position based on configuration."""
        screen_width = self.engine.width
        screen_height = self.engine.height
        
        if isinstance(self.config.position, tuple):
            # Custom coordinates
            return self.config.position
        elif isinstance(self.config.position, NotificationPosition):
            # Pre-defined positions
            margin = 20
            spacing = 10
            
            position = self.config.position
            
            if position == NotificationPosition.TOP_LEFT:
                return (margin, margin)
            elif position == NotificationPosition.TOP_CENTER:
                return ((screen_width - self.config.width) // 2, margin)
            elif position == NotificationPosition.TOP_RIGHT:
                return (screen_width - self.config.width - margin, margin)
            elif position == NotificationPosition.CENTER_LEFT:
                return (margin, (screen_height - self.config.height) // 2)
            elif position == NotificationPosition.CENTER:
                return ((screen_width - self.config.width) // 2, 
                       (screen_height - self.config.height) // 2)
            elif position == NotificationPosition.CENTER_RIGHT:
                return (screen_width - self.config.width - margin, 
                       (screen_height - self.config.height) // 2)
            elif position == NotificationPosition.BOTTOM_LEFT:
                return (margin, screen_height - self.config.height - margin)
            elif position == NotificationPosition.BOTTOM_CENTER:
                return ((screen_width - self.config.width) // 2,
                       screen_height - self.config.height - margin)
            elif position == NotificationPosition.BOTTOM_RIGHT:
                return (screen_width - self.config.width - margin,
                       screen_height - self.config.height - margin)
        
        # Default to top-right
        return (screen_width - self.config.width - 20, 20)
    
    def _calculate_start_position(self) -> Tuple[int, int]:
        """Calculate start position for slide animation based on target position."""
        target_x, target_y = self.target_position
        
        # Slide from outside based on position quadrant
        screen_width = self.engine.width
        screen_height = self.engine.height
        
        # Determine which side to slide from
        if isinstance(self.config.position, tuple):
            # For custom positions, slide from top
            return (target_x, -self.config.height)
        elif isinstance(self.config.position, NotificationPosition):
            position = self.config.position
            
            # Top positions slide from top
            if position in [NotificationPosition.TOP_LEFT, 
                          NotificationPosition.TOP_CENTER, 
                          NotificationPosition.TOP_RIGHT]:
                return (target_x, -self.config.height)
            
            # Bottom positions slide from bottom
            elif position in [NotificationPosition.BOTTOM_LEFT, 
                            NotificationPosition.BOTTOM_CENTER, 
                            NotificationPosition.BOTTOM_RIGHT]:
                return (target_x, screen_height)
            
            # Center positions fade in
            elif position in [NotificationPosition.CENTER_LEFT,
                            NotificationPosition.CENTER,
                            NotificationPosition.CENTER_RIGHT]:
                return (target_x, target_y)
        
        # Default: slide from top
        return (target_x, -self.config.height)
    
    def _create_ui(self):
        """Create the notification UI elements."""
        # Background frame with rounded corners
        self.frame = UiFrame(0, 0, self.config.width, self.config.height, 
                           theme=self.theme_type)
        self.frame.set_background_color(self.style.bg_color)
        self.frame.set_border(self.style.border_color, 2)
        self.frame.set_corner_radius(8)
        self.add_child(self.frame)
        
        # Create content area
        content_padding = 10
        icon_size = 24 if self.style.show_icon else 0
        text_area_x = content_padding + (icon_size + 10 if self.style.show_icon else 0)
        text_area_width = self.config.width - text_area_x - content_padding
        
        # Icon (using the new icon system)
        if self.style.show_icon and self.style.icon_type:
            try:
                # Create icon surface
                icon_surface = IconFactory.get_icon(self.style.icon_type, icon_size)
                
                # Create a simple UI element to display the icon
                self.icon_element = UIElement(
                    content_padding, 
                    (self.config.height - icon_size) // 2,  # Center vertically
                    icon_size, 
                    icon_size,
                    (0, 0)
                )
                
                # Store the icon surface to render later
                self.icon_element.icon_surface = icon_surface
                
                # Override the render method for this element
                original_render = self.icon_element.render
                def custom_render(renderer):
                    # Draw the icon surface
                    if hasattr(self.icon_element, 'icon_surface'):
                        actual_x, actual_y = self.icon_element.get_actual_position()
                        renderer.blit(self.icon_element.icon_surface, (actual_x, actual_y))
                    # Call original render if it exists
                    if original_render:
                        original_render(renderer)
                
                self.icon_element.render = custom_render
                self.frame.add_child(self.icon_element)
                
            except Exception as e:
                # Fallback to text icon if there's an error
                print(f"Failed to load icon: {e}")
                fallback_text = "!"  # Simple fallback
                self.icon_label = TextLabel(
                    content_padding, content_padding,
                    fallback_text,
                    font_size=icon_size,
                    color=self.style.text_color,
                    theme=self.theme_type
                )
                self.icon_label.height = self.config.height - (content_padding * 2)
                self.frame.add_child(self.icon_label)
        
        # Text label (rest of the code remains the same...)
        font_size = 14
        self.text_label = TextLabel(
            text_area_x, content_padding,
            self.config.text,
            font_size=font_size,
            color=self.style.text_color,
            theme=self.theme_type
        )
        self.text_label.width = text_area_width
        self.text_label.height = self.config.height - (content_padding * 2)
        self.frame.add_child(self.text_label)
        
        # Close button (update to use icon)
        if self.config.show_close_button:
            close_btn_size = 20
            
            # Create button without text initially
            self.close_button = Button(
                self.config.width - close_btn_size - 5, 5,
                close_btn_size, close_btn_size,
                "",  # Empty text - we'll use an icon
                font_size=16,
                theme=self.theme_type
            )
            self.close_button.set_background_color((255, 255, 255, 0))
            self.close_button.set_text_color(self.style.text_color)
            self.close_button.set_on_click(self.close)
            self.close_button.always_on_top = True
            
            # Add cross icon to close button
            try:
                cross_icon = IconFactory.get_icon(Icons.CROSS, close_btn_size - 4)
                self.close_button.icon_surface = cross_icon
                
                # Override button render to include icon
                original_button_render = self.close_button.render
                def button_with_icon_render(renderer):
                    # Call original button render first
                    if original_button_render:
                        original_button_render(renderer)
                    
                    # Draw icon centered in button
                    if hasattr(self.close_button, 'icon_surface'):
                        actual_x, actual_y = self.close_button.get_actual_position()
                        icon_x = actual_x + (self.close_button.width - cross_icon.get_width()) // 2
                        icon_y = actual_y + (self.close_button.height - cross_icon.get_height()) // 2
                        renderer.blit(cross_icon, (icon_x, icon_y))
                
                self.close_button.render = button_with_icon_render
            except:
                # Fallback to text "×"
                self.close_button.text = "×"
            
            self.frame.add_child(self.close_button)
    
    def _apply_custom_style(self):
        """Apply custom styling if provided in config."""
        if hasattr(self.config, 'bg_color') and self.config.bg_color:
            self.frame.set_background_color(self.config.bg_color)
        if hasattr(self.config, 'border_color') and self.config.border_color:
            self.frame.set_border_color(self.config.border_color)
        if hasattr(self.config, 'text_color') and self.config.text_color:
            self.text_label.set_text_color(self.config.text_color)
            if self.config.show_close_button:
                self.close_button.set_text_color(self.config.text_color)
            if hasattr(self, 'icon_label'):
                self.icon_label.set_text_color(self.config.text_color)
    
    def show(self):
        """Start showing the notification."""
        self.is_showing = True
        self.is_visible = True
        self.animation_progress = 0.0
    
    def close(self):
        """Close the notification with animation."""
        if not self.is_closing:
            self.is_closing = True
            self.start_time = time.time()
            
            # Call on_close callback
            if self.config.on_close:
                self.config.on_close(self)
    
    def force_close(self):
        """Force close without animation."""
        self.is_closing = True
        self.animation_progress = 2.0
        self.is_visible = False
    
    def update(self, dt: float, inputState: InputState):
        """Update notification state and animations."""
        if not self.is_visible:
            return
        
        # Update animation progress
        if self.is_showing and self.animation_progress < 1.0:
            self.animation_progress = min(1.0, self.animation_progress + (dt / self.animation_speed))
        
        elif self.is_closing and self.animation_progress < 2.0:
            self.animation_progress = min(2.0, self.animation_progress + (dt / self.animation_speed))
            if self.animation_progress >= 2.0:
                self.is_visible = False
        
        # Calculate current position with animation
        if self.animation_progress < 1.0:
            # Slide in
            progress = self._ease_out(self.animation_progress)
            start_x, start_y = self.start_position
            target_x, target_y = self.target_position
            
            self.x = start_x + (target_x - start_x) * progress
            self.y = start_y + (target_y - start_y) * progress
        elif self.animation_progress < 2.0:
            # Slide out or fade
            progress = self._ease_in(self.animation_progress - 1.0)
            
            # For top positions, slide up; for bottom, slide down; for center, fade
            if isinstance(self.config.position, NotificationPosition):
                position = self.config.position
                
                if position in [NotificationPosition.TOP_LEFT, 
                              NotificationPosition.TOP_CENTER, 
                              NotificationPosition.TOP_RIGHT]:
                    # Slide up
                    self.y = self.target_position[1] - (self.config.height * progress)
                elif position in [NotificationPosition.BOTTOM_LEFT,
                                NotificationPosition.BOTTOM_CENTER,
                                NotificationPosition.BOTTOM_RIGHT]:
                    # Slide down
                    self.y = self.target_position[1] + (self.config.height * progress)
                else:
                    # Center positions fade
                    pass
        
        # Update time progress for auto-close
        if self.config.auto_close and not self.is_closing:
            elapsed = time.time() - self.start_time
            self._time_progress = elapsed / self.duration
            
            # Check if notification has expired
            if elapsed >= self.duration:
                self.close()
            
            # Update progress bar
            if self.config.show_progress_bar and hasattr(self, 'progress_fill'):
                remaining = max(0.0, 1.0 - self._time_progress)
                self.progress_fill.width = int(self.config.width * remaining)
        
        # Update hover state
        actual_x, actual_y = self.get_actual_position()
        mouse_pos = inputState.mouse_pos
        
        mouse_over = (actual_x <= mouse_pos[0] <= actual_x + self.config.width and 
                     actual_y <= mouse_pos[1] <= actual_y + self.config.height)
        
        if mouse_over:
            self.state = UIState.HOVERED
            self._is_hovered = True
            
            # Handle click
            if inputState.mouse_just_pressed and self.config.on_click:
                self.config.on_click(self)
        else:
            self.state = UIState.NORMAL
            self._is_hovered = False
        
        # Update children
        for child in self.children:
            if hasattr(child, 'update'):
                child.update(dt, inputState)
    
    def _ease_out(self, t: float) -> float:
        """Ease out cubic function for smooth animation."""
        return 1 - pow(1 - t, 3)
    
    def _ease_in(self, t: float) -> float:
        """Ease in cubic function for smooth animation."""
        return t * t * t
    
    def should_remove(self) -> bool:
        """Check if notification should be removed."""
        return self.is_closing and not self.is_visible
    
    def get_opacity(self) -> float:
        """Get current opacity for fade animations."""
        if self.animation_progress < 1.0:
            return min(1.0, self.animation_progress * 2)
        elif self.animation_progress < 2.0:
            return max(0.0, 1.0 - ((self.animation_progress - 1.0) * 2))
        return 0.0
    
    def render(self, renderer):
        """Render notification with icon."""
        if not self.is_visible:
            return
        
        # Apply opacity for center positions
        opacity = self.get_opacity()
        if opacity <= 0:
            return
        
        # Save renderer state and apply opacity
        if hasattr(renderer, 'push_opacity'):
            renderer.push_opacity(opacity)
        
        # Render children (frame, text, etc.)
        super().render(renderer)
        
        # Manually render the icon on top
        if hasattr(self, 'icon_surface') and self.icon_surface:
            actual_x, actual_y = self.get_actual_position()
            icon_x = actual_x + self.icon_position[0]
            icon_y = actual_y + self.icon_position[1]
            renderer.blit(self.icon_surface, (icon_x, icon_y))
        
        # Restore renderer state
        if hasattr(renderer, 'pop_opacity'):
            renderer.pop_opacity()


class NotificationManager:
    """
    Manages all notifications globally with queue support.
    Handles positioning, stacking, and lifecycle of notifications.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the notification manager."""
        self.notifications: List[Notification] = []
        self.notification_queue: List[Notification] = []
        self.engine = None
        
        # Configuration
        self.max_concurrent_notifications = 5
        self.default_margin = 20
        self.spacing = 10
        
        # Position groups for stacking
        self.position_groups = {
            NotificationPosition.TOP_LEFT: [],
            NotificationPosition.TOP_CENTER: [],
            NotificationPosition.TOP_RIGHT: [],
            NotificationPosition.CENTER_LEFT: [],
            NotificationPosition.CENTER: [],
            NotificationPosition.CENTER_RIGHT: [],
            NotificationPosition.BOTTOM_LEFT: [],
            NotificationPosition.BOTTOM_CENTER: [],
            NotificationPosition.BOTTOM_RIGHT: [],
        }
    
    def set_engine(self, engine: 'LunaEngine'):
        """Set the engine reference for screen size calculations."""
        self.engine = engine
    
    def show_notification(self, config: NotificationConfig) -> Notification:
        """
        Show a new notification immediately or add to queue.
        
        Args:
            config: Notification configuration
            
        Returns:
            The created Notification object
        """
        if not self.engine:
            raise RuntimeError("NotificationManager not initialized with engine")
        
        # Create notification
        notification = Notification(config, self.engine)
        
        # Check if we can show it immediately
        if len(self.notifications) < self.max_concurrent_notifications:
            self._show_notification_immediate(notification)
        else:
            # Add to queue
            self.notification_queue.append(notification)
            print(f"Notification queued. Queue length: {len(self.notification_queue)}")
        
        return notification
    
    def _show_notification_immediate(self, notification: Notification):
        """Show a notification immediately."""
        # Add to position group if it's a pre-defined position
        if isinstance(notification.config.position, NotificationPosition):
            position = notification.config.position
            self.position_groups[position].append(notification)
            
            # Update positions for stacking
            self._update_notification_positions(position)
        
        # Add to active notifications and show it
        self.notifications.append(notification)
        notification.show()
        
        print(f"Notification shown. Active: {len(self.notifications)}")
    
    def _update_notification_positions(self, position: NotificationPosition):
        """Update positions for stacked notifications in a position group."""
        notifications = self.position_groups[position]
        
        if not notifications:
            return
        
        # Calculate stacking based on position
        for i, notification in enumerate(notifications):
            base_x, base_y = notification.target_position
            total_height = notification.config.height + self.spacing
            
            # Stack vertically for left/right positions
            if position in [NotificationPosition.TOP_LEFT, 
                          NotificationPosition.CENTER_LEFT,
                          NotificationPosition.BOTTOM_LEFT,
                          NotificationPosition.TOP_RIGHT,
                          NotificationPosition.CENTER_RIGHT,
                          NotificationPosition.BOTTOM_RIGHT]:
                notification.target_position = (base_x, base_y + (i * total_height))
            
            # Stack horizontally for top/bottom center
            elif position in [NotificationPosition.TOP_CENTER,
                            NotificationPosition.BOTTOM_CENTER]:
                total_width = notification.config.width + self.spacing
                start_x = base_x - ((len(notifications) - 1) * total_width) // 2
                notification.target_position = (start_x + (i * total_width), base_y)
    
    def show_simple_notification(self, text: str, 
                                 notification_type: NotificationType = NotificationType.INFO,
                                 duration: Optional[float] = None,
                                 position: Union[NotificationPosition, Tuple[int, int]] = NotificationPosition.TOP_RIGHT) -> Notification:
        """
        Show a simple notification with minimal configuration.
        
        Args:
            text: Notification text
            notification_type: Type of notification
            duration: Optional custom duration
            position: Position for notification
            
        Returns:
            The created Notification object
        """
        config = NotificationConfig(
            text=text,
            notification_type=notification_type,
            duration=duration,
            position=position,
            width=300,
            height=60
        )
        return self.show_notification(config)
    
    def remove_notification(self, notification: Notification):
        """Remove a specific notification."""
        if notification in self.notifications:
            # Remove from position group if applicable
            if isinstance(notification.config.position, NotificationPosition):
                position = notification.config.position
                if notification in self.position_groups[position]:
                    self.position_groups[position].remove(notification)
            
            # Remove from active notifications
            self.notifications.remove(notification)
            
            # Update positions for the group
            if isinstance(notification.config.position, NotificationPosition):
                self._update_notification_positions(notification.config.position)
            
            # Show next notification from queue
            self._process_queue()
    
    def clear_all(self):
        """Clear all notifications immediately."""
        for notification in self.notifications[:]:
            notification.force_close()
            self.notifications.remove(notification)
        
        # Clear queue
        self.notification_queue.clear()
        
        # Clear position groups
        for position in self.position_groups:
            self.position_groups[position].clear()
    
    def clear_by_type(self, notification_type: NotificationType):
        """Clear all notifications of a specific type."""
        notifications_to_remove = [
            n for n in self.notifications 
            if n.config.notification_type == notification_type
        ]
        
        for notification in notifications_to_remove:
            notification.close()
    
    def _process_queue(self):
        """Process the notification queue."""
        while (self.notification_queue and 
               len(self.notifications) < self.max_concurrent_notifications):
            next_notification = self.notification_queue.pop(0)
            self._show_notification_immediate(next_notification)
    
    def update(self, dt: float, inputState: InputState):
        """Update all notifications and process queue."""
        # Update each notification
        for notification in self.notifications[:]:  # Use copy for safe removal
            notification.update(dt, inputState)
            
            # Remove notifications that should be removed
            if notification.should_remove():
                self.remove_notification(notification)
        
        # Process queue if we have space
        self._process_queue()
    
    def render(self, renderer):
        """Render all notifications."""
        for notification in self.notifications:
            notification.render(renderer)
    
    def get_notification_count(self) -> int:
        """Get the current number of active notifications."""
        return len(self.notifications)
    
    def get_queue_length(self) -> int:
        """Get the current queue length."""
        return len(self.notification_queue)
    
    def has_notifications(self) -> bool:
        """Check if there are any active notifications."""
        return len(self.notifications) > 0
    
    def has_queued_notifications(self) -> bool:
        """Check if there are any queued notifications."""
        return len(self.notification_queue) > 0
    
    def set_max_concurrent(self, max_count: int):
        """Set maximum concurrent notifications."""
        self.max_concurrent_notifications = max_count
    
    def set_default_margin(self, margin: int):
        """Set default margin for notifications."""
        self.default_margin = margin
    
    def set_spacing(self, spacing: int):
        """Set spacing between notifications."""
        self.spacing = spacing


# Global instance
notification_manager = NotificationManager()


# Convenience functions
def show_notification(text: str, 
                      notification_type: NotificationType = NotificationType.INFO,
                      duration: Optional[float] = None,
                      position: Union[NotificationPosition, Tuple[int, int]] = NotificationPosition.TOP_RIGHT) -> Notification:
    """
    Convenience function to show a simple notification.
    
    Args:
        text: Notification text
        notification_type: Type of notification
        duration: Optional custom duration
        position: Position for notification
        
    Returns:
        The created Notification object
    """
    return notification_manager.show_simple_notification(text, notification_type, duration, position)


def show_error(text: str, duration: Optional[float] = None,
               position: Union[NotificationPosition, Tuple[int, int]] = NotificationPosition.TOP_RIGHT) -> Notification:
    """Show an error notification."""
    return show_notification(text, NotificationType.ERROR, duration, position)


def show_warning(text: str, duration: Optional[float] = None,
                 position: Union[NotificationPosition, Tuple[int, int]] = NotificationPosition.TOP_RIGHT) -> Notification:
    """Show a warning notification."""
    return show_notification(text, NotificationType.WARNING, duration, position)


def show_success(text: str, duration: Optional[float] = None,
                 position: Union[NotificationPosition, Tuple[int, int]] = NotificationPosition.TOP_RIGHT) -> Notification:
    """Show a success notification."""
    return show_notification(text, NotificationType.SUCCESS, duration, position)


def show_info(text: str, duration: Optional[float] = None,
              position: Union[NotificationPosition, Tuple[int, int]] = NotificationPosition.TOP_RIGHT) -> Notification:
    """Show an info notification."""
    return show_notification(text, NotificationType.INFO, duration, position)


def clear_all_notifications():
    """Clear all notifications."""
    notification_manager.clear_all()


def get_notification_count() -> int:
    """Get the current number of active notifications."""
    return notification_manager.get_notification_count()


def get_queue_length() -> int:
    """Get the current queue length."""
    return notification_manager.get_queue_length()