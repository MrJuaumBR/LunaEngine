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

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.engine import LunaEngine

from ..ui.elements import UIElement

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
    
    def __init__(self, engine: 'LunaEngine', *args:tuple, **kwargs:dict):
        """
        Initialize a new scene with empty UI elements list.
        
        Args:
            engine (LunaEngine): Reference to the game engine
        """
        self.ui_elements: List[UIElement] = []
        self._initialized = False
        self.engine: LunaEngine = engine
        
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
        
        Called every frame to update game logic, animations, and interactions.
        
        Args:
            dt (float): Delta time in seconds since last frame
        """
        pass
        
    def render(self, renderer) -> None:
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
        
    def get_all_ui_elements(self) -> List[UIElement]:
        """
        Get all UI elements in the scene.
        
        Returns:
            List[UIElement]: All UI elements in the scene
        """
        return self.ui_elements.copy()
        
    def clear_ui_elements(self) -> None:
        """Remove all UI elements from the scene."""
        self.ui_elements.clear()