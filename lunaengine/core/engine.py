"""
LunaEngine Main Engine - Core Game Loop and Management System

LOCATION: lunaengine/core/engine.py

DESCRIPTION:
The central engine class that orchestrates the entire game lifecycle. Manages
scene transitions, rendering pipeline, event handling, performance monitoring,
and UI system integration. This is the primary interface for game developers.

KEY RESPONSIBILITIES:
- Game loop execution with fixed timestep
- Scene management and lifecycle control
- Event distribution to scenes and UI elements
- Performance monitoring and optimization
- Theme management across the entire application
- Resource initialization and cleanup

LIBRARIES USED:
- pygame: Window management, event handling, timing, and surface operations
- numpy: Mathematical operations for game calculations
- threading: Background task management (if needed)
- typing: Type hints for better code documentation

DEPENDENCIES:
- ..backend.pygame_backend: Default rendering backend
- ..ui.elements: UI component system
- ..utils.performance: Performance monitoring utilities
- .scene: Scene management base class
"""

import pygame, threading
import numpy as np
from typing import Dict, List, Tuple, Callable, Optional, Type, TYPE_CHECKING, Any
from ..ui.layer_manager import UILayerManager
from ..ui.notifications import (NotificationManager, NotificationPosition, NotificationType, notification_manager, show_notification, show_error, show_warning, show_success, show_info)
from ..ui import *
from .scene import Scene
from ..utils import PerformanceMonitor, GarbageCollector
from ..backend import OpenGLRenderer, EVENTS, InputState, MouseButtonPressed, LayerType, LExceptions, ControllerManager
from .renderer import Renderer
from .window import Window
from dataclasses import dataclass

class LunaEngine:
    """
    Main game engine class for LunaEngine.
    
    This class manages the entire game lifecycle including initialization,
    scene management, event handling, rendering, and shutdown.
    
    Attributes:
        title (str): Window title
        width (int): Window width
        height (int): Window height
        fullscreen (bool): Whether to start in fullscreen mode
        running (bool): Whether the engine is running
        clock (pygame.time.Clock): Game clock for FPS control
        scenes (Dict[str, Scene]): Registered scenes
        current_scene (Scene): Currently active scene
    """
    def __init__(self, title: str = "LunaEngine Game", width: int = 800, height: int = 600, fullscreen: bool = False,icon:str|pygame.Surface=None, **kwargs):
        """
        Initialize the LunaEngine.
        
        Args:
            title (str): The title of the game window (default: "LunaEngine Game")
            width (int): The width of the game window (default: 800)
            height (int): The height of the game window (default: 600)
            use_opengl (bool): Use OpenGL for rendering (default: True)
            fullscreen (bool): Start in fullscreen mode (default: False)
        """
        self.title = title
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.icon = icon
        
        # Window
        self.window = Window(title=title, width=width, height=height, fullscreen=fullscreen, resizable=False)
        self.monitor_size:pygame.display._VidInfo = None
        self._last_window_size = (width, height)
        self._last_window_pos = (0, 0)
        self._window_focused = True
        self._window_minimized = False
        self._window_maximized = False
        
        
        self.running = False
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[Scene] = None
        self.previous_scene_name: Optional[str] = None
        self._event_handlers:Dict[str, List[Dict[str, Callable[pygame.event.EventType, None], str, Optional[str]]]] = {}
        self.ratio:pygame.Vector2 = pygame.Vector2(1.0,1.0)
        self.input_state = InputState()
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        self.garbage_collector = GarbageCollector()
        
        # Performance profilling settings
        self.enable_performance_profiling(kwargs.get('enable_performance_profiling', True))
        
        # Render
        self.renderer: Renderer = None
        
        self.screen = None
        
        # Notification system
        self.notification_manager = notification_manager
        self.notification_manager.set_engine(self)
        
        # Notification configuration
        self.notification_max_concurrent = 5
        self.notification_margin = 20
        self.notification_spacing = 10
        
        # Automatically initialize
        self.initialize()
        self.animation_handler = AnimationHandler(self)
        self.layer_manager = UILayerManager()
        
        self.controller_manager = ControllerManager(self)
        
    def initialize(self):
        """Initialize the engine and create the game window."""
        pygame.init()
        
        self.monitor_size:pygame.display._VidInfo = pygame.display.Info()
        
        # Initialize font system early
        FontManager.initialize()
        
        # Create the display based on renderer type
        # Set OpenGL attributes BEFORE creating display
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        
        try:
            code = pygame.OPENGL | pygame.DOUBLEBUF
            if self.fullscreen:
                self.width, self.height = self.monitor_size.current_w, self.monitor_size.current_h
                code |= pygame.FULLSCREEN | pygame.SCALED
                print(f"Setting fullscreen mode: {self.width}x{self.height}")
            self.window.create()
            self.screen = self.window.surface
        except Exception as e:
            raise(LExceptions.OpenGLInitializationError(e))
        
        self.set_title(self.title)
        self.set_icon(self.icon)
        
        # Create renderer
        self.renderer: Renderer = OpenGLRenderer(self.width, self.height)
        
        self.update_camera_renderer()
        
        # Initialize both renderers
        renderer_success = self.renderer.initialize()
        
        
        self.running = True
        print("Engine initialization complete")
        
        from ..ui.elements import UIElement
        UIElement._global_engine = self
        
    def set_title(self, title:str):
        pygame.display.set_caption(title)
        
    def set_icon(self, icon:str|pygame.Surface):
        if icon is None:
            return
        if isinstance(icon, str):
            icon = pygame.image.load(icon).convert()
        pygame.display.set_icon(icon)
        
    def update_camera_renderer(self):
        for scene in self.scenes.values():
            if hasattr(scene, 'camera'):
                scene.camera.renderer = self.renderer
        
    def add_scene(self, name: str, scene_class: Type[Scene], *args, **kwargs):
        """
        Add a scene to the engine by class (the engine will instantiate it).
        
        Args:
            name (str): The name of the scene
            scene_class (Type[Scene]): The scene class to instantiate
            *args: Arguments to pass to scene constructor
            **kwargs: Keyword arguments to pass to scene constructor
        """
        if callable(scene_class): scene_instance = scene_class(self, *args, **kwargs)
        else: scene_instance = scene_class
        self.scenes[name] = scene_instance
        scene_instance.name = name
        
    def set_scene(self, name: str):
        """
        Set the current active scene.
        
        Calls on_exit on the current scene and on_enter on the new scene.
        
        Args:
            name (str): The name of the scene to set as current
        """
        if name in self.scenes:
            # Call on_exit for current scene
            if self.current_scene:
                self.current_scene.on_exit(name)
                
            # Store previous scene name
            previous_name = None
            for scene_name, scene_obj in self.scenes.items():
                if scene_obj == self.current_scene:
                    previous_name = scene_name
                    break
            self.previous_scene_name = previous_name
            
            # Set new scene and call on_enter
            self.current_scene = self.scenes[name]
            self.current_scene.on_enter(self.previous_scene_name)
    
    def find_event_handlers(self, event:int, rep_id:str) -> bool:
        return False
    
    def on_event(self, event_type: int, rep_id: Optional[str] = None):
        """
        Decorator to register event handlers
        
        Args:
            event_type (int): The Pygame event type to listen for
        Returns:
            Callable: The decorator function
        """
        def decorator(func):
            """
            Decorator to register the event handler
            Args:
                func (Callable): The event handler function
            Returns:
                Callable: The original function
            """
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append({'callable':func, 'rep_id': rep_id})
            return func
        return decorator
    
    def setup_notifications(self, max_concurrent: int = 5, margin: int = 20, spacing: int = 10):
        """
        Setup notification system configuration.
        
        Args:
            max_concurrent: Maximum concurrent notifications to show
            margin: Margin from screen edges
            spacing: Spacing between stacked notifications
        """
        self.notification_max_concurrent = max_concurrent
        self.notification_margin = margin
        self.notification_spacing = spacing
        
        self.notification_manager.set_max_concurrent(max_concurrent)
        self.notification_manager.set_default_margin(margin)
        self.notification_manager.set_spacing(spacing)
    
    def show_notification(self, text: str, 
                         notification_type: NotificationType = NotificationType.INFO,
                         duration: Optional[float] = None,
                         position = NotificationPosition.TOP_RIGHT,
                         width: int = 300,
                         height: int = 60,
                         show_close_button: bool = True,
                         auto_close: bool = True,
                         animation_speed: float = 0.3,
                         show_progress_bar: bool = False,
                         on_close: Optional[Callable] = None,
                         on_click: Optional[Callable] = None):
        """
        Show a notification with advanced options.
        
        Args:
            text: Notification text
            notification_type: Type of notification
            duration: Display duration in seconds
            position: Position (NotificationPosition or custom (x, y) tuple)
            width: Width of notification
            height: Height of notification
            show_close_button: Whether to show close button
            auto_close: Whether notification auto-closes
            animation_speed: Speed of slide/fade animations
            show_progress_bar: Whether to show progress bar
            on_close: Callback when notification is closed
            on_click: Callback when notification is clicked
            
        Returns:
            The created Notification object
        """
        from ..ui.notifications import NotificationConfig
        
        config = NotificationConfig(
            text=text,
            notification_type=notification_type,
            duration=duration,
            position=position,
            width=width,
            height=height,
            show_close_button=show_close_button,
            auto_close=auto_close,
            animation_speed=animation_speed,
            show_progress_bar=show_progress_bar,
            on_close=on_close,
            on_click=on_click
        )
        
        return self.notification_manager.show_notification(config)
    
    def show_info(self, text: str, duration: Optional[float] = None,
                  position = NotificationPosition.TOP_RIGHT) -> 'Notification':
        """Show an info notification."""
        return self.show_notification(text, NotificationType.INFO, duration, position)
    
    def show_success(self, text: str, duration: Optional[float] = None,
                     position = NotificationPosition.TOP_RIGHT) -> 'Notification':
        """Show a success notification."""
        return self.show_notification(text, NotificationType.SUCCESS, duration, position)
    
    def show_warning(self, text: str, duration: Optional[float] = None,
                     position = NotificationPosition.TOP_RIGHT) -> 'Notification':
        """Show a warning notification."""
        return self.show_notification(text, NotificationType.WARNING, duration, position)
    
    def show_error(self, text: str, duration: Optional[float] = None,
                   position = NotificationPosition.TOP_RIGHT) -> 'Notification':
        """Show an error notification."""
        return self.show_notification(text, NotificationType.ERROR, duration, position)
    
    def clear_all_notifications(self):
        """Clear all notifications."""
        self.notification_manager.clear_all()
    
    def get_notification_count(self) -> int:
        """Get current number of active notifications."""
        return self.notification_manager.get_notification_count()
    
    def get_notification_queue_length(self) -> int:
        """Get current notification queue length."""
        return self.notification_manager.get_queue_length()
    
    def has_notifications(self) -> bool:
        """Check if there are any active notifications."""
        return self.notification_manager.has_notifications()
    
    def has_queued_notifications(self) -> bool:
        """Check if there are any queued notifications."""
        return self.notification_manager.has_queued_notifications()
    
    def get_all_themes(self) -> Dict[str, any]:
        """
        Get all available themes including user custom ones
        
        Returns:
            Dict[str, any]: Dictionary with theme names as keys and theme objects as values
        """
        from ..ui.themes import ThemeManager, ThemeType
        
        all_themes = {}
        
        # Get all built-in themes from ThemeType enum
        for theme_enum in ThemeType:
            theme = ThemeManager.get_theme(theme_enum)
            all_themes[theme_enum.value] = {
                'enum': theme_enum,
                'theme': theme,
                'type': 'builtin'
            }
        
        # Get user custom themes (these would be stored in ThemeManager._themes)
        # Note: This assumes custom themes are also stored in ThemeManager._themes
        # with their own ThemeType values or custom keys
        for theme_key, theme_value in ThemeManager._themes.items():
            if theme_key not in all_themes:
                # This is a custom theme not in the built-in enum
                theme_name = theme_key.value if hasattr(theme_key, 'value') else str(theme_key)
                all_themes[theme_name] = {
                    'enum': theme_key,
                    'theme': theme_value,
                    'type': 'custom'
                }
        
        return all_themes

    def get_theme_names(self) -> List[str]:
        """
        Get list of all available theme names
        
        Returns:
            List[str]: List of theme names
        """
        themes = self.get_all_themes()
        return list(themes.keys())

    def set_global_theme(self, theme: str) -> bool:
        """
        Set the global theme for the entire engine and update all UI elements
        
        Args:
            theme_name (str): Name of the theme to set
            
        Returns:
            bool: True if theme was set successfully, False otherwise
        """
        from ..ui.themes import ThemeManager, ThemeType
        
        if type(theme) is ThemeType: theme_name = theme.value
        else: theme_name = theme
        
        themes = self.get_theme_names()
        if theme_name in themes:
            theme_data = ThemeManager.get_theme_type_by_name(theme_name)
            ThemeManager.set_current_theme(theme_data)
            
            # Update all UI elements in current scene
            self._update_all_ui_themes(theme_data)
            
            return True
        
        return False

    def _update_all_ui_themes(self, theme_enum):
        """
        Update all UI elements in the current scene to use the new theme
        
        Args:
            theme_enum: The theme enum to apply
        """
        if self.current_scene and hasattr(self.current_scene, 'ui_elements'):
            for ui_element in self.current_scene.ui_elements:
                if hasattr(ui_element, 'update_theme'):
                    ui_element.update_theme(theme_enum)
        
        # Also update any scene-specific UI that might not be in ui_elements list
        if self.current_scene:
            # Look for UI elements as attributes of the scene
            for attr_name in dir(self.current_scene):
                attr = getattr(self.current_scene, attr_name)
                if hasattr(attr, 'update_theme'):
                    attr.update_theme(theme_enum) 
    
    def get_fps_stats(self) -> dict:
        """
        Get comprehensive FPS statistics (optimized)
        
        Returns:
            dict: A dictionary containing FPS statistics
        """
        return self.performance_monitor.get_stats()
    
    def get_hardware_info(self) -> dict:
        """Get hardware information"""
        return self.performance_monitor.get_hardware_info()
    
    def ScaleSize(self, width: float, height: float) -> Tuple[float, float]|Tuple[int, int]:
        """
        Scale size is a function that will convert scales size to a pixel size
        
        e.g.:
        - 1.0, 1.0 = Full Screen
        - 0.5, 0.5 = Half Screen
        - 0.5, 1.0 = Half Screen Width, Full Screen Height
        
        Args:
            width (float): Width scale
            height (float): Height scale
        Returns:
            Tuple[float, float]|Tuple[int, int]: Pixel size
        """
        size = self.screen.get_size()
        size = (size[0] * width, size[1] * height)
        return size
    
    def ScalePos(self, x: float, y: float) -> Tuple[float, float]|Tuple[int, int]:
        """
        Scale position is a function that will convert scales position to a pixel position
        
        e.g.:
        - 1.0, 1.0 = Bottom Right
        - 0.0, 0.0 = Top Left
        - 0.5, 0.5 = Center
        
        Args:
            x (float): X position
            y (float): Y position
        Returns:
            Tuple[float, float]|Tuple[int, int]: Pixel position
        """
        size = self.screen.get_size()
        size = (size[0] * x, size[1] * y)
        return size

    def setRatio(self, base_width:int, base_height:int) -> pygame.Vector2:
        """
        Set the ratio of the window to the base size

        Args:
            base_width (int): The base width of the window
            base_height (int): The base height of the window

        Returns:
            pygame.Vector2[float, float]: The ratio of the window to the base size
        """
        self.ratio = pygame.Vector2(base_width / self.width, base_height / self.height)
        return self.ratio

    def run(self):
        """Main game loop"""
        if self.renderer is None:
            self.initialize()
        
        while self.running:
            self.performance_monitor.start_timer('frame')
            # Update performance monitoring - start of frame
            self.performance_monitor.update_frame()
            
            dt = self.clock.tick(self.fps) / 1000.0
            
            self.input_state.clear_consumed()
            
            # Profile mouse update
            self.performance_monitor.start_timer("mouse")
            self.update_mouse()
            UITooltipManager.update(self, dt)
            self.performance_monitor.end_timer("mouse")
            
            # Profile notification update
            self.performance_monitor.start_timer("notifications")
            self.notification_manager.update(dt, self.input_state)
            self.performance_monitor.end_timer("notifications")
            
            # Profile event handling
            self.performance_monitor.start_timer("events")
            events = pygame.event.get()
            
            # Handle controller events
            self.controller_manager.handle_events(events)
            
            # Update input state with controller info
            self.input_state.using_controller = self.controller_manager.is_using_controller()
            self.input_state.active_controller = self.controller_manager.get_first_connected()
            self.input_state.controller_count = len(self.controller_manager)
            
            for event in events:
                if event.type == EVENTS.QUIT:
                    self.running = False
                    
                # Handle window events
                self.window.handle_pygame_event(event)
                
                # Call registered event handlers
                if event.type in self._event_handlers:
                    for handler in self._event_handlers[event.type]:
                        handler['callable'](event)
            self.performance_monitor.end_timer("events")
            
            # Update current scene with profiling
            if self.current_scene:
                self.performance_monitor.start_timer("scene")
                self.current_scene._update(dt)
                self.performance_monitor.end_timer("scene")
                
            # Update all animations with profiling
            self.performance_monitor.start_timer("animations")
            self.animation_handler.update(dt)
            self.performance_monitor.end_timer("animations")
            
            # Update UI elements with profiling
            self.performance_monitor.start_timer("ui")
            self._update_ui_elements(dt)
            self.performance_monitor.end_timer("ui")
            
            # Render with profiling
            self.performance_monitor.start_timer("render")
            self._render()
            self.performance_monitor.end_timer("render")
            
            self.performance_monitor.end_timer('frame')
            
            # End frame profiling
            self.performance_monitor.end_frame()
            
            # Periodic garbage collection
            self.garbage_collector.cleanup()
        
        self.shutdown()
        
    def on_window_resize(self, func: Callable):
        """
        Decorator for window resize event.
        
        Args:
            func: The resize event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_resize(func)
    
    def on_window_close(self, func: Callable):
        """
        Decorator for window close event.
        
        Args:
            func: The close event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_close(func)
    
    def on_window_focus(self, func: Callable):
        """
        Decorator for window focus gained event.
        
        Args:
            func: The focus event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_focus(func)
    
    def on_window_blur(self, func: Callable):
        """
        Decorator for window blur (focus lost) event.
        
        Args:
            func: The blur event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_blur(func)
    
    def on_window_move(self, func: Callable):
        """
        Decorator for window move event.
        
        Args:
            func: The move event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_move(func)
    
    def on_window_minimize(self, func: Callable):
        """
        Decorator for window minimize event.
        
        Args:
            func: The minimize event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_minimize(func)
    
    def on_window_maximize(self, func: Callable):
        """
        Decorator for window maximize event.
        
        Args:
            func: The maximize event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_maximize(func)
    
    def on_window_restore(self, func: Callable):
        """
        Decorator for window restore event.
        
        Args:
            func: The restore event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_restore(func)
    
    def on_window_enter(self, func: Callable):
        """
        Decorator for mouse entering window event.
        
        Args:
            func: The enter event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_enter(func)
    
    def on_window_leave(self, func: Callable):
        """
        Decorator for mouse leaving window event.
        
        Args:
            func: The leave event handler function
            
        Returns:
            The decorated function
        """
        return self.window.on_leave(func)
    
    def get_window_state(self) -> Dict[str, Any]:
        """
        Get current window state.
        
        Returns:
            Dict[str, Any]: Window state information
        """
        return self.window.get_window_state()
    
    def is_window_focused(self) -> bool:
        """
        Check if window is focused.
        
        Returns:
            bool: True if window is focused
        """
        return self.window.is_focused()
    
    def is_window_minimized(self) -> bool:
        """
        Check if window is minimized.
        
        Returns:
            bool: True if window is minimized
        """
        return self.window.is_minimized()
    
    def is_window_maximized(self) -> bool:
        """
        Check if window is maximized.
        
        Returns:
            bool: True if window is maximized
        """
        return self.window.is_maximized()
        
    def get_controllers(self) -> List['Controller']:
        return self.controller_manager.get_all_controllers()

    def get_controller(self, index: int) -> Optional['Controller']:
        return self.controller_manager.get_controller(index)

    def is_using_controller(self) -> bool:
        return self.controller_manager.is_using_controller()

    def on_controller_connect(self, callback: Callable[['Controller'], None]):
        """Register callback when a controller connects."""
        self.controller_manager.on_connect.append(callback)

    def on_controller_disconnect(self, callback: Callable[['Controller'], None]):
        """Register callback when a controller disconnects."""
        self.controller_manager.on_disconnect.append(callback)
        
    def update_mouse(self):
        """Update mouse position and button state with proper click detection"""
        mouse_pos = pygame.mouse.get_pos()
        m_pressed = pygame.mouse.get_pressed(num_buttons=5)
        
        # Update input state with proper click detection
        self.input_state.update(mouse_pos, m_pressed)
            
    def visibility_change(self, element: UIElement, visible: bool):
        if type(element) in [list, tuple]:
            [self.visibility_change(e, visible) for e in element]
        else:
            element.visible = visible
            
    @property
    def mouse_pos(self) -> tuple:
        return self.input_state.mouse_pos
    
    @property
    def mouse_pressed(self) -> list:
        return [self.input_state.mouse_buttons_pressed.values() for i in range(5)]
    
    @property
    def mouse_wheel(self) -> float:
        return self.input_state.mouse_wheel

    def _render(self):
        """Rendering with performance profiling"""
        try:
            # 1. Start OpenGL frame
            self.renderer.begin_frame()
            
            # 2. Render main scene objects with profiling
            if self.current_scene:
                self.performance_monitor.start_timer("scene")
                self.current_scene.render(self.renderer)
                self.performance_monitor.end_timer("scene")
            
            # 3. Render particles with profiling
            self.performance_monitor.start_timer("particles")
            self._render_particles()
            self.performance_monitor.end_timer("particles")
            
            # 4. Render UI elements with profiling
            self.performance_monitor.start_timer("ui")
            self._render_ui_elements()
            self.performance_monitor.end_timer("ui")
            
            # 5. Render notifications with profiling
            self.performance_monitor.start_timer("notifications")
            self.notification_manager.render(self.renderer)
            self.performance_monitor.end_timer("notifications")
            
            # 6. Finalize OpenGL frame with profiling
            self.performance_monitor.start_timer("frame_finalize")
            self.renderer.end_frame()
            self.performance_monitor.end_timer("frame_finalize")
            
        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            import traceback
            traceback.print_exc()

    def _render_ui_elements(self):
        """Render UI elements with individual profiling if enabled"""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
        
        # Get elements in correct render order
        elements_to_render = self.layer_manager.get_elements_in_order()
        
        # Profile entire UI rendering
        self.performance_monitor.start_timer("ui_total")
        
        # Render elements
        for ui_element in elements_to_render:
            # Skip elements inside ScrollingFrame (they're rendered by the ScrollingFrame itself)
            if hasattr(ui_element, 'parent') and ui_element.parent and isinstance(ui_element.parent, ScrollingFrame):
                continue
            
            ui_element.render(self.renderer)
        
        # Render tooltips
        for tooltip in UITooltipManager.get_tooltip_to_render(engine=self):
            tooltip.render(self.renderer)
        
        self.performance_monitor.end_timer("ui_total")
            
    def _render_particles(self):
        """Render particles using OpenGL"""
        if (self.current_scene and 
            hasattr(self.current_scene, 'particle_system') and
            hasattr(self.renderer, 'render_particles')):
            particle_data = self.current_scene.particle_system.get_render_data()
            if particle_data['active_count'] > 0:
                self.renderer.render_particles(particle_data, camera=self.current_scene.camera)
            try:
                pass
            except Exception as e:
                print(f"OpenGL particle rendering error: {e}")

    def _update_ui_elements(self, dt):
        """
        Update UI elements with individual profiling if enabled
        """
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
        
        # Rebuild layers from current scene UI elements
        self.layer_manager.clear_all()
        
        for ui_element in self.current_scene.ui_elements:
            self.layer_manager.add_element(ui_element)
        
        # Profile entire UI update
        self.performance_monitor.start_timer("ui_total")
        
        
        self.layer_manager.update(dt, self.input_state)
        
        self.performance_monitor.end_timer("ui_total")


    def _process_ui_element_tree(self, root_element, dt):
        """
        Process a UI element and all its children with proper event consumption
        
        Args:
            root_element (UIElement): The root element to process
            dt (float): Delta time in seconds
        """
        # Process the element itself
        if hasattr(root_element, 'update'):
            root_element.update(dt,self.input_state)
        
        # Process all children recursively
        for child in getattr(root_element, 'children', []):
            self._process_ui_element_tree(child, dt)
    
    def enable_performance_profiling(self, enabled: bool = True):
        """Enable/disable detailed performance profiling."""
        # Pre-alloc timers
        self.performance_monitor.create_timer("frame")
        self.performance_monitor.create_timer("mouse")
        self.performance_monitor.create_timer("events")
        self.performance_monitor.create_timer("scene")
        self.performance_monitor.create_timer("particles")
        self.performance_monitor.create_timer("ui")
        self.performance_monitor.create_timer("ui_total")
        self.performance_monitor.create_timer("notifications")
        self.performance_monitor.create_timer("frame_finalize")
        # Actually enable/disable profiling
        self.performance_monitor.enable_profiling(enabled)
    
    def get_frame_timing_breakdown(self) -> Dict[str, float]:
        """Get the timing breakdown (ms) for the last completed frame."""
        return self.performance_monitor.get_frame_timing_breakdown()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Return both FPS stats and frame timing breakdown."""
        stats = self.performance_monitor.get_stats()
        stats["frame_timings"] = self.get_frame_timing_breakdown()
        return stats
    
    def get_update_timing_stats(self, category: str = "all") -> Dict[str, Any]:
        """Get update timing statistics for a specific category"""
        return self.performance_monitor.get_update_timing_stats(category)
    
    def get_render_timing_stats(self, category: str = "all") -> Dict[str, Any]:
        """Get render timing statistics for a specific category"""
        return self.performance_monitor.get_render_timing_stats(category)
    
    def get_ui_update_stats(self) -> Dict[str, Any]:
        """Get UI update timing statistics"""
        return self.performance_monitor.get_update_timing_stats("ui")
    
    def get_ui_render_stats(self) -> Dict[str, Any]:
        """Get UI render timing statistics"""
        return self.performance_monitor.get_render_timing_stats("ui")
    
    def get_individual_ui_update_stats(self) -> Dict[str, float]:
        """Get individual UI element update timing statistics"""
        stats = self.performance_monitor.get_update_timing_stats("ui_individual")
        return stats.get("individual_times", {})
    
    def get_individual_ui_render_stats(self) -> Dict[str, float]:
        """Get individual UI element render timing statistics"""
        stats = self.performance_monitor.get_render_timing_stats("ui_individual")
        return stats.get("individual_times", {})
    
    def get_scene_update_stats(self) -> Dict[str, Any]:
        """Get scene update timing statistics"""
        return self.performance_monitor.get_update_timing_stats("scene")
    
    def get_scene_render_stats(self) -> Dict[str, Any]:
        """Get scene render timing statistics"""
        return self.performance_monitor.get_render_timing_stats("scene")
    
    def get_total_frame_time(self) -> Dict[str, float]:
        """Get total frame time breakdown"""
        update_stats = self.performance_monitor.get_all_update_timing_stats()
        render_stats = self.performance_monitor.get_all_render_timing_stats()
        
        total_update = sum(cat.get("current_ms", 0) for cat in update_stats.values())
        total_render = sum(cat.get("current_ms", 0) for cat in render_stats.values())
        
        return {
            "total_ms": total_update + total_render,
            "update_ms": total_update,
            "render_ms": total_render,
            "other_ms": self.performance_monitor.get_stats().get("frame_time_ms", 0) - (total_update + total_render)
        }
    
    def shutdown(self):
        """Cleanup resources"""
        # Force final garbage collection
        self.garbage_collector.cleanup(force=True)
        pygame.quit()