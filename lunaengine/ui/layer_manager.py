"""
layer_manager.py - UI Layer Management System for LunaEngine

ENGINE PATH:
lunaengine -> ui -> layer_manager.py

DESCRIPTION:
This module provides a layer management system for UI elements, ensuring
proper rendering order especially for interactive elements like dropdowns,
tooltips, and modal dialogs that need to appear above other content.

MAIN CLASSES:
1. UILayerManager: Manages UI elements across different render layers
2. LayerType (Enum): Defines different render layers for UI elements
"""

from enum import Enum
from typing import List, Dict, TYPE_CHECKING
from .elements import UIElement
from ..backend.types import LayerType

if TYPE_CHECKING:
    from ..core.engine import LunaEngine

class UILayerManager:
    """
    Manages UI elements across different render layers to ensure proper
    visual hierarchy and interaction.
    
    Attributes:
        layers (Dict[LayerType, List[UIElement]]): Elements organized by layer
        layer_order (List[LayerType]): Order in which layers should be rendered
    """
    
    def __init__(self):
        """Initialize the layer manager with empty layers."""
        self.layers: Dict[LayerType, List[UIElement]] = {
            LayerType.BACKGROUND: [],
            LayerType.NORMAL: [],
            LayerType.ABOVE_NORMAL: [],
            LayerType.POPUP: [],
            LayerType.MODAL: [],
            LayerType.TOP: []
        }
        
        # Render order: background -> normal -> above normal -> popup -> modal -> top
        self.layer_order = [
            LayerType.BACKGROUND,
            LayerType.NORMAL,
            LayerType.ABOVE_NORMAL,
            LayerType.POPUP,
            LayerType.MODAL,
            LayerType.TOP
        ]
    
    def get_all_elements(self):
        """
        Get all UI elements across all layers.
        
        Returns:
            List[UIElement]: A list of all UI elements
        """
        return [element for layer_elements in self.layers.values() for element in layer_elements]
    
    def add_element(self, element: UIElement, layer: LayerType = None):
        """
        Add a UI element to the appropriate layer.
        
        Args:
            element (UIElement): The UI element to add
            layer (LayerType, optional): Specific layer to add to. If None,
                determines layer based on element properties.
        """
        if layer is None:
            layer = self._determine_layer(element)
        
        # Remove element from any existing layer first
        self.remove_element(element)
        
        # Add to the specified layer
        self.layers[layer].append(element)
    
    def remove_element(self, element: UIElement):
        """
        Remove a UI element from all layers.
        
        Args:
            element (UIElement): The UI element to remove
        """
        for layer_elements in self.layers.values():
            if element in layer_elements:
                layer_elements.remove(element)
                break
    
    def clear_layer(self, layer: LayerType):
        """
        Clear all elements from a specific layer.
        
        Args:
            layer (LayerType): The layer to clear
        """
        self.layers[layer].clear()
    
    def clear_all(self):
        """Clear all elements from all layers."""
        for layer in self.layers:
            self.layers[layer].clear()
    
    def _determine_layer(self, element: UIElement) -> LayerType:
        """
        Determine the appropriate render layer for a UI element.
        
        Args:
            element (UIElement): The element to classify
            
        Returns:
            LayerType: The appropriate render layer
        """
        # Check for always_on_top property
        if hasattr(element, 'always_on_top') and element.always_on_top:
            return LayerType.TOP
        
        # Check element type
        from .elements import Dropdown, DialogBox
        from .tooltips import Tooltip
        
        if isinstance(element, Dropdown):
            if element.expanded:
                return LayerType.POPUP
            else:
                return LayerType.NORMAL
        elif isinstance(element, Tooltip):
            return LayerType.POPUP
        elif isinstance(element, DialogBox):
            return LayerType.MODAL
        
        # Check render_layer property
        if hasattr(element, 'render_layer'):
            if element.render_layer == 2:
                return LayerType.POPUP
            elif element.render_layer == 1:
                return LayerType.ABOVE_NORMAL
        
        # Default to normal layer
        return LayerType.NORMAL
    
    def determine_list_layers(self, element_list: List[UIElement]) -> Dict[LayerType, List[UIElement]]:
        """
        Determine the appropriate render layers for a list of UI elements.
        
        Args:
            element_list (List[UIElement]): The list of elements to classify
            
        Returns:
            Dict[LayerType, List[UIElement]]: A dictionary mapping layers to elements
        """
        layers: Dict[LayerType, List[UIElement]] = {
            LayerType.BACKGROUND: [],
            LayerType.NORMAL: [],
            LayerType.ABOVE_NORMAL: [],
            LayerType.POPUP: [],
            LayerType.MODAL: [],
            LayerType.TOP: []
        }
        
        for element in element_list:
            layer = self._determine_layer(element)
            layers[layer].append(element)
        
        return layers
    
    def get_elements_in_order_from(self, elements:List[UIElement]) -> List[UIElement]:
        """
        Get elements in the correct render order from a dictionary of layers.
        
        Args:
            layers (Dict[LayerType, List[UIElement]]): A dictionary mapping layers to elements
            
        Returns:
            List[UIElement]: Elements sorted by render layer and z-index
        """
        ordered_elements = []
        
        layers = self.determine_list_layers(elements)
        
        for layer_type in layers:
            layer_elements = layers[layer_type]
                
            # Sort within layer by z-index
            layer_elements.sort(key=lambda e: e.z_index)
            ordered_elements.extend(layer_elements)
        
        return ordered_elements
    
    def get_elements_in_order(self) -> List[UIElement]:
        """
        Get all elements in the correct render order.
        
        Returns:
            List[UIElement]: Elements sorted by render layer and z-index
        """
        ordered_elements = []
        
        for layer_type in self.layer_order:
            layer_elements = self.layers[layer_type]
            
            # Sort within layer by z-index
            layer_elements.sort(key=lambda e: e.z_index)
            ordered_elements.extend(layer_elements)
            
        return ordered_elements
    
    def update(self, dt: float, input_state):
        """
        Update all elements in the layer manager.
        
        Args:
            dt (float): Delta time in seconds
            input_state: Current input state
        """
        # Update elements in reverse order (top to bottom) for proper event handling
        for layer_type in reversed(self.layer_order):
            for element in self.layers[layer_type]:
                if hasattr(element, 'update'):
                    element.update(dt, input_state)