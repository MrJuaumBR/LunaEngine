import pygame
import numpy as np
from typing import Dict, List, Callable, Optional
import threading
from ..backend.pygame_backend import PygameRenderer
from ..ui.elements import FontManager
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
        """Main game loop - optimized performance tracking"""
        self.initialize()
        
        while self.running:
            # Update performance monitoring
            self.performance_monitor.update_frame()
            
            dt = self.clock.tick(self.fps) / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Call registered event handlers
                if event.type in self._event_handlers:
                    for handler in self._event_handlers[event.type]:
                        handler(event)
            
            # Update current scene
            if self.current_scene:
                self.current_scene.update(dt)
            
            # Update UI elements with proper mouse position
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()[0]
            
            # Get UI elements from current scene
            if self.current_scene and hasattr(self.current_scene, 'ui_elements'):
                # Separate dropdowns for proper rendering order
                from ..ui.elements import Dropdown
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
                
                # Update dropdowns last
                for dropdown in dropdowns:
                    dropdown._update_with_mouse(mouse_pos, mouse_pressed, dt)
            
            # RENDER EVERYTHING
            self.renderer.begin_frame()
            
            # 1. Render scene
            if self.current_scene:
                self.current_scene.render(self.renderer)
            
            # 2. Render UI elements
            if self.current_scene and hasattr(self.current_scene, 'ui_elements'):
                from ..ui.elements import Dropdown
                regular_elements = []
                dropdowns = []
                
                for ui_element in self.current_scene.ui_elements:
                    if isinstance(ui_element, Dropdown):
                        dropdowns.append(ui_element)
                    else:
                        regular_elements.append(ui_element)
                
                # Render regular elements
                for ui_element in regular_elements:
                    ui_element.render(self.renderer)
                
                # Render dropdowns last (expanded options on top)
                for dropdown in dropdowns:
                    dropdown.render(self.renderer)
            
            # 3. Update display
            self.screen.blit(self.renderer.get_surface(), (0, 0))
            pygame.display.flip()
            
            # Periodic garbage collection
            self.garbage_collector.cleanup()
        
        self.shutdown()
    
    def shutdown(self):
        """Cleanup resources"""
        # Force final garbage collection
        self.garbage_collector.cleanup(force=True)
        pygame.quit()