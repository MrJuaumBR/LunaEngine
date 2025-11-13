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
from typing import Dict, List, Callable, Optional, Type, TYPE_CHECKING
from ..ui.elements import *
from .scene import Scene
from ..utils.performance import PerformanceMonitor, GarbageCollector
from ..backend.pygame_backend import PygameRenderer
from dataclasses import dataclass

if TYPE_CHECKING:
    from . import Renderer

@dataclass
class mouse_buttons_schem(dict):
    left:bool = False
    middle:bool = False
    right:bool = False
    extra_button_1:bool = False
    extra_button_2:bool = False

class LunaEngine:
    """
    Main game engine class for LunaEngine.
    
    This class manages the entire game lifecycle including initialization,
    scene management, event handling, rendering, and shutdown.
    
    Attributes:
        title (str): Window title
        width (int): Window width
        height (int): Window height
        running (bool): Whether the engine is running
        clock (pygame.time.Clock): Game clock for FPS control
        scenes (Dict[str, Scene]): Registered scenes
        current_scene (Scene): Currently active scene
    """
    _mouse_pos:tuple[int,int] = (0,0)
    _mouse_buttons:mouse_buttons_schem = mouse_buttons_schem()
    _mouse_wheel:float = 0
    def __init__(self, title: str = "LunaEngine Game", width: int = 800, height: int = 600, use_opengl: bool = False):
        """
        Initialize the LunaEngine.
        
        Args:
            title (str): The title of the game window (default: "LunaEngine Game")
            width (int): The width of the game window (default: 800)
            height (int): The height of the game window (default: 600)
            use_opengl (bool): Use OpenGL for rendering (default: False)
        """
        self.title = title
        self.width = width
        self.height = height
        self.running = False
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[Scene] = None
        self.previous_scene_name: Optional[str] = None
        self._event_handlers = {}
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        self.garbage_collector = GarbageCollector()
        
        # Choose rendering backend
        self.use_opengl = use_opengl
        if use_opengl:
            from ..backend.opengl import OpenGLRenderer
            self.renderer: Renderer = OpenGLRenderer(width, height)
        else:
            self.renderer:Renderer = PygameRenderer(width, height)
        
        self.screen = None
        
    def initialize(self):
        """Initialize the engine and create the game window."""
        pygame.init()
        
        # Initialize font system early
        FontManager.initialize()
        
        print(f"Initializing engine with OpenGL: {self.use_opengl}")
        
        # Create the display based on renderer type
        if self.use_opengl:
            # Set OpenGL attributes BEFORE creating display
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
            
            try:
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF)
                print("OpenGL display created successfully")
            except Exception as e:
                print(f"Failed to create OpenGL display: {e}")
                print("Falling back to Pygame rendering")
                self.use_opengl = False
                self.screen = pygame.display.set_mode((self.width, self.height))
        else:
            self.screen = pygame.display.set_mode((self.width, self.height))
        
        pygame.display.set_caption(self.title)
        
        # Initialize both renderers
        print("Initializing renderers...")
        renderer_success = self.renderer.initialize()
        
        if self.use_opengl and not renderer_success:
            print("OpenGL renderer failed to initialize, falling back to Pygame")
            self.use_opengl = False
            self.renderer: Renderer = self.ui_renderer
        
        self.running = True
        print("Engine initialization complete")
        
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
        """Main game loop - CORRECTED"""
        self.initialize()
        
        # Pre-cache frequently used values
        mouse_btn_left = 0
        
        while self.running:
            # Update performance monitoring
            self.performance_monitor.update_frame()
            
            dt = self.clock.tick(self.fps) / 1000.0
            
            self.update_mouse()
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Process both KEYDOWN and KEYUP for better text input
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
            self._update_ui_elements(self.mouse_pos, self._mouse_buttons, dt)
            
            # CORRECTED: Unified rendering pipeline
            if self.use_opengl:
                # OPENGL MODE - Hybrid rendering
                self._render_opengl_mode()
            else:
                # PYGAME MODE - Traditional rendering
                self._render_pygame_mode()
            
            # Periodic garbage collection
            self.garbage_collector.cleanup()
        
        self.shutdown()
        
    def update_mouse(self):
        """Update mouse position and button state"""
        self._mouse_pos = pygame.mouse.get_pos()
        m_pressed = pygame.mouse.get_pressed(num_buttons=5)
        self._mouse_buttons.left = m_pressed[0]
        self._mouse_buttons.middle = m_pressed[1]
        self._mouse_buttons.right = m_pressed[2]
        if len(m_pressed) >= 5:
            self._mouse_buttons.extra_button_1 = m_pressed[3]
            self._mouse_buttons.extra_button_2 = m_pressed[4]
            
        if self._mouse_wheel != 0:
            self._mouse_wheel *= 0.6
            
    def visibility_change(self, element: UIElement, visible: bool):
        if type(element) in [list, tuple]:
            [self.visibility_change(e, visible) for e in element]
        else:
            element.visible = visible
            
    @property
    def mouse_pos(self):
        return self._mouse_pos
    
    @property
    def mouse_pressed(self):
        return [self._mouse_buttons.left, self._mouse_buttons.middle, self._mouse_buttons.right, self._mouse_buttons.extra_button_1, self._mouse_buttons.extra_button_2]
    
    @property
    def mouse_wheel(self):
        return self._mouse_wheel

    def _render_opengl_mode(self):
        """Rendering pipeline for OpenGL mode - CORRECTED"""
        try:
            # 1. Start OpenGL frame
            self.renderer.begin_frame()
            
            # 2. Render main scene objects
            if self.current_scene:
                self.current_scene.render(self.renderer)
            
            # 3. Render particles using OpenGL
            self.render_particles()
            
            # 4. Render UI elements using OpenGL
            self._render_ui_elements_opengl()
            
            # 5. Finalize OpenGL frame
            self.renderer.end_frame()
            
        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            import traceback
            traceback.print_exc()

    def _render_ui_elements_opengl(self):
        """Render UI elements using OpenGL renderer - SKIP elements with ScrollingFrame parent"""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
        
        # Sort elements for optimal rendering order, skipping ScrollingFrame children
        regular_elements = []
        closed_dropdowns = []
        open_dropdowns = []
        
        for ui_element in self.current_scene.ui_elements:
            # Skip elements that have ScrollingFrame as parent
            if hasattr(ui_element, 'parent') and ui_element.parent and isinstance(ui_element.parent, ScrollingFrame):
                continue
                
            if isinstance(ui_element, Dropdown):
                if ui_element.expanded:
                    open_dropdowns.append(ui_element)
                else:
                    closed_dropdowns.append(ui_element)
            else:
                regular_elements.append(ui_element)
        
        # Render in correct z-order
        for ui_element in regular_elements + closed_dropdowns:
            ui_element.render(self.renderer)
        
        for dropdown in open_dropdowns:
            dropdown.render(self.renderer)

    def _render_pygame_mode(self):
        """Rendering pipeline for Pygame mode - SIMPLIFIED"""
        try:
            # 1. Clear screen
            self.screen.fill((30, 30, 50))
            
            # 2. Set the screen as render target
            if hasattr(self.renderer, 'set_surface'):
                self.renderer.set_surface(self.screen)
            self.renderer.begin_frame()
            
            # 3. Render main scene
            if self.current_scene:
                self.current_scene.render(self.renderer)
            
            # 3. Render particles using Pygame
            self.render_particles()
            
            # 4. Render UI elements
            self._render_ui_elements(self.renderer)
            
            # 5. Finalize Pygame frame
            pygame.display.flip()
            
        except Exception as e:
            print(f"Pygame rendering error: {e}")

    def _render_ui_elements(self, renderer):
        """Render UI elements - SKIP elements with ScrollingFrame parent"""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
        
        # Filter out elements that have ScrollingFrame as parent
        root_elements = []
        regular_elements = []
        closed_dropdowns = []
        open_dropdowns = []
        
        for ui_element in self.current_scene.ui_elements:
            # Skip elements that have ScrollingFrame as parent (they will be rendered by their parent)
            if hasattr(ui_element, 'parent') and ui_element.parent and isinstance(ui_element.parent, ScrollingFrame):
                continue
                
            if isinstance(ui_element, Dropdown):
                if ui_element.expanded:
                    open_dropdowns.append(ui_element)
                else:
                    closed_dropdowns.append(ui_element)
            else:
                regular_elements.append(ui_element)
        
        # Render in correct z-order
        for ui_element in regular_elements + closed_dropdowns:
            ui_element.render(renderer)
        
        for dropdown in open_dropdowns:
            dropdown.render(renderer)

    def _render_ui_direct(self):
        """Render UI directly to screen in Pygame mode"""
        # Set UI renderer to use main screen
        self.ui_renderer.set_surface(self.screen)
        self.ui_renderer.begin_frame()
        
        # Render UI elements
        self._render_ui_elements(self.ui_renderer)

    def render_particles(self):
        if self.use_opengl:
            self._render_particles_opengl()
        else:
            self.current_scene.particle_system.render(self.renderer.get_surface(), self.current_scene.camera)
            
    def _render_particles_opengl(self):
        """Render particles using OpenGL - FIXED"""
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

    def _handle_mouse_scroll(self, event):
        """Handle mouse wheel scrolling for UI elements - OPTIMIZED"""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
            
        self._mouse_wheel = event.y
        
        for ui_element in self.current_scene.ui_elements:
            if not hasattr(ui_element, 'handle_scroll'):
                continue
                
            actual_x, actual_y = ui_element.get_actual_position()
            
            # For expanded dropdowns, check expanded area
            if hasattr(ui_element, 'expanded') and ui_element.expanded:
                expanded_height = (ui_element.height + 
                                 ui_element.max_visible_options * ui_element._option_height)
                mouse_over = (
                    actual_x <= self.mouse_pos[0] <= actual_x + ui_element.width and 
                    actual_y <= self.mouse_pos[1] <= actual_y + expanded_height
                )
            else:
                # Normal behavior for other elements
                mouse_over = (
                    actual_x <= self.mouse_pos[0] <= actual_x + ui_element.width and 
                    actual_y <= self.mouse_pos[1] <= actual_y + ui_element.height
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

    def _update_ui_elements(self, mouse_pos, mouse_pressed: mouse_buttons_schem, dt):
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
            ui_element._update_with_mouse(mouse_pos, mouse_pressed.left, dt)
        
        # Update dropdowns last (for proper focus handling)
        for dropdown in dropdowns:
            dropdown._update_with_mouse(mouse_pos, mouse_pressed.left, dt)
    
    def shutdown(self):
        """Cleanup resources"""
        # Force final garbage collection
        self.garbage_collector.cleanup(force=True)
        pygame.quit()