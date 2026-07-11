"""
layer_manager.py - UI Layer Management System for LunaEngine

ENGINE PATH:
lunaengine -> ui -> layer_manager.py

DESCRIPTION:
This module provides a layer management system for UI elements, ensuring
proper rendering order especially for interactive elements like dropdowns,
tooltips, and modal dialogs that need to appear above other content.
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
        """Get all UI elements across all layers."""
        return [element for layer_elements in self.layers.values() for element in layer_elements]
    
    def add_element(self, element: UIElement, layer: LayerType = None):
        """Add a UI element to the appropriate layer."""
        if layer is None:
            layer = self._determine_layer(element)
        
        self.remove_element(element)
        self.layers[layer].append(element)
    
    def remove_element(self, element: UIElement):
        """Remove a UI element from all layers."""
        for layer_elements in self.layers.values():
            if element in layer_elements:
                layer_elements.remove(element)
                break
    
    def clear_layer(self, layer: LayerType):
        """Clear all elements from a specific layer."""
        self.layers[layer].clear()
    
    def clear_all(self):
        """Clear all elements from all layers."""
        for layer in self.layers:
            self.layers[layer].clear()
    
    def _determine_layer(self, element: UIElement) -> LayerType:
        """
        Determine the appropriate render layer for a UI element.
        """
        # First priority: explicit render_layer property
        if hasattr(element, 'render_layer'):
            if element.render_layer == LayerType.POPUP:
                return LayerType.POPUP
            elif element.render_layer == LayerType.MODAL:
                return LayerType.MODAL
            elif element.render_layer == LayerType.TOP:
                return LayerType.TOP
            elif element.render_layer == LayerType.ABOVE_NORMAL:
                return LayerType.ABOVE_NORMAL

        # Second: always_on_top flag
        if hasattr(element, 'always_on_top') and element.always_on_top:
            return LayerType.TOP

        # Third: element type detection using element_type string (avoids circular imports)
        from .elements.selectors import Dropdown
        from .tooltips import Tooltip
        from .elements import DialogBox
        from .elements.containers import ColorPicker

        if isinstance(element, ColorPicker):
            if hasattr(element, 'expanded') and element.expanded:
                return LayerType.POPUP
            else:
                return LayerType.NORMAL

        if isinstance(element, Dropdown):
            if hasattr(element, 'expanded') and element.expanded:
                return LayerType.POPUP
            else:
                return LayerType.NORMAL
        elif isinstance(element, Tooltip):
            return LayerType.POPUP
        elif isinstance(element, DialogBox):
            return LayerType.MODAL

        # Fallback to element's render_layer if it's an integer
        if hasattr(element, 'render_layer') and isinstance(element.render_layer, int):
            if element.render_layer == 2:
                return LayerType.POPUP
            elif element.render_layer == 1:
                return LayerType.ABOVE_NORMAL

        return LayerType.NORMAL
    
    def determine_list_layers(self, element_list: List[UIElement]) -> Dict[LayerType, List[UIElement]]:
        """Classify a list of elements by layer."""
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
    
    def get_elements_in_order_from(self, elements: List[UIElement]) -> List[UIElement]:
        """Get elements in correct render order from a list, using layer classification."""
        layers = self.determine_list_layers(elements)
        ordered_elements = []
        for layer_type in self.layer_order:
            layer_elements = layers[layer_type]
            layer_elements.sort(key=lambda e: e.z_index)
            ordered_elements.extend(layer_elements)
        return ordered_elements
    
    def get_elements_in_order(self) -> List[UIElement]:
        """Get all stored elements in the correct render order."""
        ordered_elements = []
        for layer_type in self.layer_order:
            layer_elements = self.layers[layer_type]
            layer_elements.sort(key=lambda e: e.z_index)
            ordered_elements.extend(layer_elements)
        return ordered_elements
    
    def update(self, dt: float, input_state):
        """Update all elements in reverse order (top to bottom) for proper event handling."""
        for layer_type in reversed(self.layer_order):
            for element in self.layers[layer_type]:
                if hasattr(element, 'update'):
                    element.update(dt, input_state)