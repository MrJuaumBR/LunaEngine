"""
Scene Management System - Game State and UI Container

LOCATION: lunaengine/core/scene.py

DESCRIPTION:
Provides the foundation for organizing game content into manageable states.
Each scene represents a distinct game state (menu, gameplay, pause screen)
with its own logic, rendering, and UI elements. Supports seamless transitions
between scenes with proper lifecycle management.

KEY FEATURES:
- Scene lifecycle hooks (on_enter/on_exit)
- UI element management with unique identifiers
- Type-based element filtering and retrieval
- Scene transition state tracking

LIBRARIES USED:
- abc: Abstract base class for scene interface
- typing: Type hints for collections and optional values
- TYPE_CHECKING: For circular import resolution

USAGE PATTERN:
1. Inherit from Scene class
2. Implement abstract methods (on_enter, on_exit, update, render)
3. Add UI elements in on_enter method
4. Manage scene-specific logic in update method
"""

import pygame
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from ..ui import UIElement, UiFrame, ScrollingFrame, Tabination
from ..graphics import Camera, ParticleConfig, ParticleSystem, ParticleType, ShadowSystem
from ..core.audio import AudioSystem
from ..backend.opengl import OpenGLRenderer
from ..core.renderer import Renderer
from ..backend.types import ElementsList, ElementsListEvents

if TYPE_CHECKING:
    from ..core.engine import LunaEngine

class Scene(ABC):
    """
    Base class for all game scenes.
    
    Provides lifecycle methods and UI element management. 
    All custom scenes should inherit from this class.
    
    Attributes:
        ui_elements (List[UIElement]): List of UI elements in this scene
        _initialized (bool): Whether the scene has been initialized
        engine (LunaEngine): Reference to the game engine
    """
    name:str = ''
    def __init__(self, engine: 'LunaEngine', *args:tuple, **kwargs:dict):
        """
        Initialize a new scene with empty UI elements list.
        
        Args:
            engine (LunaEngine): Reference to the game engine
        """
        self.ui_elements: ElementsList = ElementsList(on_change=self._ui_element_list)
        self._initialized = False
        self.engine: LunaEngine = engine
        
        # Camera Start
        self.camera: Camera = Camera(self, engine.width, engine.height)
        
        # Particle System
        self.particle_system: ParticleSystem = ParticleSystem(self.engine.renderer.max_particles)
        self.engine.renderer.on_max_particles_change.append(self.particle_system.update_max_particles)
        
        # Shadows System
        self.shadow_system: ShadowSystem = ShadowSystem(self.engine.width, self.engine.height, engine)
        
        # Audio System
        self.audio_system: AudioSystem = AudioSystem(num_channels=16)
    
    def _add_event_to_handler(self, element: UIElement):
        if element.element_type == 'textbox': # Textbox on_key_down and on_key_up events
            @self.engine.on_event(pygame.KEYDOWN, element.element_id)
            def on_key_down(event):
                if element.focused and element.enabled:
                    element.on_key_down(event)
                
            @self.engine.on_event(pygame.KEYUP, element.element_id)
            def on_key_up(event):
                if element.focused and element.enabled:
                    element.on_key_up(event)
        elif element.element_type in ['scrollingframe', 'dropdown']: # ScrollingFrame, Dropdown on_scroll events
            @self.engine.on_event(pygame.MOUSEWHEEL, element.element_id)
            def on_scroll(event):
                element.on_scroll(event)
    
    def _update_on_change_child(self, element: UIElement):
        self._add_event_to_handler(element)
        
        for child in element.children:
            child.children.set_on_change(self._ui_element_list, child)
            # Check if all childs already have the events sets on the engine decorator
            if hasattr(child,'on_key_down'):
                self.engine.find_event_handlers(pygame.KEYDOWN, child.element_id)
            elif hasattr(child,'on_key_up'):
                self.engine.find_event_handlers(pygame.KEYUP, child.element_id)
            elif hasattr(child,'on_scroll'):
                self.engine.find_event_handlers(pygame.MOUSEWHEEL, child.element_id)
            
            child.scene = self
            self._update_on_change_child(child)
    
    def _ui_element_list(self, event_type:ElementsListEvents, element: UIElement, index: Optional[int] = None):
        if event_type == 'append':
            self._update_on_change_child(element)
            
            element.scene = self
            element.children.set_on_change(self._ui_element_list, element)
        
    def on_enter(self, previous_scene: Optional[str] = None) -> None:
        """
        Called when the scene becomes active.
        
        Use this to initialize resources, create UI elements, or reset game state.
        
        Args:
            previous_scene (str, optional): Name of the previous scene
        """
        self._initialized = True
        
    def on_exit(self, next_scene: Optional[str] = None) -> None:
        """
        Called when the scene is being replaced.
        
        Use this to clean up resources, save game state, or perform transitions.
        
        Args:
            next_scene (str, optional): Name of the next scene
        """
        pass
        
    def update(self, dt: float) -> None:
        """
        Update scene logic.
        """
        # Update Camera
        self.camera.update(dt)
        
        # Update particle system with camera position
        self.particle_system.update(dt, self.camera.position)
        
    def render(self, renderer: Renderer|OpenGLRenderer) -> None:
        """
        Render the scene.
        
        Called every frame to draw the scene content.
        
        Args:
            renderer: The renderer to use for drawing operations
        """
        pass
        
    def add_ui_element(self, ui_element: UIElement) -> None:
        """
        Add a UI element to the scene.
        
        Args:
            ui_element (UIElement): The UI element to add to the scene
        """
        self.ui_elements.append(ui_element)
        
    def remove_ui_element(self, ui_element: UIElement) -> bool:
        """
        Remove a UI element from the scene.
        
        Args:
            ui_element (UIElement): The UI element to remove
            
        Returns:
            bool: True if element was found and removed, False otherwise
        """
        if ui_element in self.ui_elements:
            self.ui_elements.remove(ui_element)
            return True
        return False
        
    def get_ui_element_by_id(self, element_id: str) -> Optional[UIElement]:
        """
        Get UI element by its unique ID.
        
        Args:
            element_id (str): The unique ID of the element to find
            
        Returns:
            UIElement: The found UI element or None if not found
        """
        for ui_element in self.ui_elements:
            if hasattr(ui_element, 'element_id') and ui_element.element_id == element_id:
                return ui_element
        return None
        
    def get_ui_elements_by_type(self, element_type: type) -> List[UIElement]:
        """
        Get all UI elements of a specific type.
        
        Args:
            element_type (type): The class type to filter by (e.g., Button, Label)
            
        Returns:
            List[UIElement]: List of UI elements matching the specified type
        """
        return [element for element in self.ui_elements if isinstance(element, element_type)]
        
    def get_ui_elements_by_group(self, group: str) -> List[UIElement]:
        """
        Get all UI elements in the scene.
        
        Returns:
            List[UIElement]: All UI elements in the scene
        """
        uis = []
        for ui in self.ui_elements:
            if hasattr(ui, 'groups'):
                if ui.has_group(str(group).lower()):
                    uis.append(ui)
        return uis
        
    def toggle_element_group(self, group: str, visible: bool) -> None:
        """
        Toggle the visibility of UI elements in a specific group.
        
        Args:
            group (str): The group to toggle
        """
        for ui in self.get_ui_elements_by_group(group):
            ui.visible = visible
        
    def get_all_ui_elements(self) -> List[UIElement]:
        """
        Get all UI elements in the scene.
        
        Returns:
            List[UIElement]: All UI elements in the scene
        """
        return self.ui_elements.copy()
    
    def has_element_by_id(self, element_id: str) -> bool:
        """
        Check if a UI element with the given ID exists in the scene.
        
        Args:
            element_id (str): The unique ID of the element to check
        Returns:
            bool: True if element exists, False otherwise
        """
        return any(hasattr(ui_element, 'element_id') and ui_element.element_id == element_id for ui_element in self.ui_elements)
    
    def has_element(self, element: UIElement) -> bool:
        """
        Check if a specific UI element exists in the scene.
        
        Args:
            element (UIElement): The UI element to check
        Returns:
            bool: True if element exists, False otherwise
        """
        return element in self.ui_elements
        
    def clear_ui_elements(self) -> None:
        """Remove all UI elements from the scene."""
        self.ui_elements.clear()