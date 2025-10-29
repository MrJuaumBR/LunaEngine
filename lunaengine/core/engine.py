import pygame
import numpy as np
from typing import Dict, List, Callable, Optional
import threading
from ..backend.pygame_backend import PygameRenderer
from ..ui.elements import *
from ..utils.performance import PerformanceMonitor, GarbageCollector

class LunaEngine:
    def __init__(self, title: str = "LunaEngine Game", width: int = 800, height: int = 600, use_opengl: bool = False):
        """
        Initialize the LunaEngine
        Args:
            title (str) *Optional: The title of the game window (default: "LunaEngine Game")
            width (int) *Optional: The width of the game window (default: 800)
            height (int) *Optional: The height of the game window (default: 600)
            use_opengl (bool) *Optional: Use OpenGL for rendering (default: False)
        Returns:
            None
        """
        self.title = title
        self.width = width
        self.height = height
        self.running = False
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.scenes = {}
        self.current_scene = None
        self._event_handlers = {}
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        self.garbage_collector = GarbageCollector()
        
        # Use Pygame renderer for now (more reliable for 2D)
        self.renderer = PygameRenderer(width, height)
        self.screen = None
        
    def initialize(self):
        """Initialize the engine"""
        pygame.init()
        # Initialize font system early
        FontManager.initialize()
        
        # Create display
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        
        # Initialize renderer
        self.renderer.initialize()
        self.running = True
        
    def add_scene(self, name: str, scene):
        """
        Add a scene to the engine
        
        Args:
            name (str): The name of the scene
            scene: The scene object
        Returns:
            None
        """
        self.scenes[name] = scene
        
    def set_scene(self, name: str):
        """
        Set the current active scene
        
        Args:
            name (str): The name of the scene to set as current
        Returns:
            None
        """
        if name in self.scenes:
            self.current_scene = self.scenes[name]
    
    
    
    def on_event(self, event_type: int):
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
            self._event_handlers[event_type].append(func)
            return func
        return decorator
    
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

    def set_global_theme(self, theme_name: str) -> bool:
        """
        Set the global theme for the entire engine and update all UI elements
        
        Args:
            theme_name (str): Name of the theme to set
            
        Returns:
            bool: True if theme was set successfully, False otherwise
        """
        from ..ui.themes import ThemeManager, ThemeType
        
        themes = self.get_all_themes()
        if theme_name in themes:
            theme_data = themes[theme_name]
            ThemeManager.set_current_theme(theme_data['enum'])
            
            # Update all UI elements in current scene
            self._update_all_ui_themes(theme_data['enum'])
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
    
    def run(self):
        """Main game loop - OPTIMIZED"""
        self.initialize()
        
        # Pre-cache frequently used values
        mouse_btn_left = 0
        
        while self.running:
            # Update performance monitoring
            self.performance_monitor.update_frame()
            
            dt = self.clock.tick(self.fps) / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # FIX: Process both KEYDOWN and KEYUP for better text input
                elif event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                    self._handle_keyboard_event(event)
                
                # Handle mouse wheel scrolling
                elif event.type == pygame.MOUSEWHEEL:
                    self._handle_mouse_scroll(event)
                
                # Call registered event handlers
                if event.type in self._event_handlers:
                    for handler in self._event_handlers[event.type]:
                        handler(event)
            
            # Update current scene
            if self.current_scene:
                self.current_scene.update(dt)
            
            # Update UI elements
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()[mouse_btn_left]
            self._update_ui_elements(mouse_pos, mouse_pressed, dt)
            
            # RENDER EVERYTHING
            self.renderer.begin_frame()
            
            # 1. Render scene
            if self.current_scene:
                self.current_scene.render(self.renderer)
            
            # 2. Render UI elements
            self._render_ui_elements(self.renderer)
            
            # 3. Update display
            self.screen.blit(self.renderer.get_surface(), (0, 0))
            pygame.display.flip()
            
            # Periodic garbage collection
            self.garbage_collector.cleanup()
        
        self.shutdown()

    def _handle_mouse_scroll(self, event):
        """Handle mouse wheel scrolling for UI elements - OPTIMIZED"""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
            
        mouse_pos = pygame.mouse.get_pos()
        
        for ui_element in self.current_scene.ui_elements:
            if not hasattr(ui_element, 'handle_scroll'):
                continue
                
            actual_x, actual_y = ui_element.get_actual_position()
            
            # For expanded dropdowns, check expanded area
            if hasattr(ui_element, 'expanded') and ui_element.expanded:
                expanded_height = (ui_element.height + 
                                 ui_element.max_visible_options * ui_element._option_height)
                mouse_over = (
                    actual_x <= mouse_pos[0] <= actual_x + ui_element.width and 
                    actual_y <= mouse_pos[1] <= actual_y + expanded_height
                )
            else:
                # Normal behavior for other elements
                mouse_over = (
                    actual_x <= mouse_pos[0] <= actual_x + ui_element.width and 
                    actual_y <= mouse_pos[1] <= actual_y + ui_element.height
                )
            
            if mouse_over:
                ui_element.handle_scroll(event.y)
                break  # Only handle scroll for one element at a time
    
    def _handle_keyboard_event(self, event):
        """Handle keyboard events for focused UI elements - OPTIMIZED"""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
            
        # FIX: Process all focused elements, not just one
        for ui_element in self.current_scene.ui_elements:
            if (hasattr(ui_element, 'focused') and ui_element.focused and 
                hasattr(ui_element, 'handle_key_input')):
                ui_element.handle_key_input(event)
                # Remove the 'break' to allow multiple elements to receive events if needed
                break  # Only one element can be focused at a time

    def _update_ui_elements(self, mouse_pos, mouse_pressed, dt):
        """Update UI elements with mouse interaction - OPTIMIZED"""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
            
        # Pre-sort elements for optimal processing
        regular_elements = []
        dropdowns = []
        
        for ui_element in self.current_scene.ui_elements:
            if isinstance(ui_element, Dropdown):
                dropdowns.append(ui_element)
            else:
                regular_elements.append(ui_element)
        
        # Update regular elements first
        for ui_element in regular_elements:
            ui_element._update_with_mouse(mouse_pos, mouse_pressed, dt)
        
        # Update dropdowns last (for proper focus handling)
        for dropdown in dropdowns:
            dropdown._update_with_mouse(mouse_pos, mouse_pressed, dt)
            
    def _render_ui_elements(self, renderer):
        """Render UI elements in correct order - OPTIMIZED"""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
            
        # Sort elements for optimal rendering order
        regular_elements = []
        closed_dropdowns = []
        open_dropdowns = []
        
        for ui_element in self.current_scene.ui_elements:
            if isinstance(ui_element, Dropdown):
                if ui_element.expanded:
                    open_dropdowns.append(ui_element)
                else:
                    closed_dropdowns.append(ui_element)
            else:
                regular_elements.append(ui_element)
        
        # Render in correct z-order:
        # 1. Regular elements and closed dropdowns
        for ui_element in regular_elements + closed_dropdowns:
            ui_element.render(renderer)
        
        # 2. Open dropdowns (on top)
        for dropdown in open_dropdowns:
            dropdown.render(renderer)
    
    def shutdown(self):
        """Cleanup resources"""
        # Force final garbage collection
        self.garbage_collector.cleanup(force=True)
        pygame.quit()