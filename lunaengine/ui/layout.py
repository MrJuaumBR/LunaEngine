"""
layout.py - UI Layout Managers for LunaEngine

ENGINE PATH:
lunaengine -> ui -> layout.py

DESCRIPTION:
This module provides layout management classes that automatically arrange
UI elements according to specified rules, simplifying the process of creating
structured and responsive user interfaces.

LIBRARIES USED:
- typing: For type hints and type annotations

MAIN CLASSES:

1. UILayout:
   - Base class for all layout managers
   - Provides common functionality for element management
   - Handles element addition and removal

2. VerticalLayout:
   - Arranges elements vertically with consistent spacing
   - Automatically positions elements from top to bottom

3. HorizontalLayout:
   - Arranges elements horizontally with consistent spacing
   - Automatically positions elements from left to right

4. GridLayout:
   - Arranges elements in a grid pattern with specified columns
   - Supports custom cell dimensions and spacing
   - Automatically wraps elements to new rows

5. JustifiedLayout:
   - Distributes elements with equal spacing
   - Supports both horizontal and vertical justification
   - Fills available space evenly

This module simplifies UI composition by providing automatic positioning
and alignment of elements, reducing manual coordinate calculations.
"""

from typing import List
from enum import Enum
from .elements import UIElement

class AnimationTypes(Enum):
    LINEAR = 'LINEAR'
    BOUNCE = 'BOUNCE'
    ELASTIC = 'ELASTIC'
    BACK = 'BACK'
    EASE_IN = 'EASE_IN'
    EASE_OUT = 'EASE_OUT'
    EASE_IN_OUT = 'EASE_IN_OUT'
    EASE = 'EASE_IN_OUT'

class UILayout:
    """Base class for UI layout managers."""
    
    def __init__(self, x: int = 0, y: int = 0):
        """
        Initialize a layout manager.
        
        Args:
            x (int): Starting X coordinate for the layout.
            y (int): Starting Y coordinate for the layout.
        """
        self.x = x
        self.y = y
        self.elements = []
        self.spacing = 10
        
    def add_element(self, element: UIElement):
        """
        Add an element to the layout.
        
        Args:
            element (UIElement): The UI element to add to the layout.
        """
        self.elements.append(element)
        self._update_layout()
        
    def remove_element(self, element: UIElement):
        """
        Remove an element from the layout.
        
        Args:
            element (UIElement): The UI element to remove from the layout.
        """
        if element in self.elements:
            self.elements.remove(element)
            self._update_layout()
            
    def _update_layout(self):
        """Update element positions based on layout rules."""
        pass

class VerticalLayout(UILayout):
    """Layout that arranges elements vertically."""
    
    def __init__(self, x: int = 0, y: int = 0, spacing: int = 10):
        """
        Initialize a vertical layout.
        
        Args:
            x (int): Starting X coordinate.
            y (int): Starting Y coordinate.
            spacing (int): Space between elements in pixels.
        """
        super().__init__(x, y)
        self.spacing = spacing
        
    def _update_layout(self):
        """Arrange elements vertically with spacing."""
        current_y = self.y
        for element in self.elements:
            element.x = self.x
            element.y = current_y
            current_y += element.height + self.spacing

class HorizontalLayout(UILayout):
    """Layout that arranges elements horizontally."""
    
    def __init__(self, x: int = 0, y: int = 0, spacing: int = 10):
        """
        Initialize a horizontal layout.
        
        Args:
            x (int): Starting X coordinate.
            y (int): Starting Y coordinate.
            spacing (int): Space between elements in pixels.
        """
        super().__init__(x, y)
        self.spacing = spacing
        
    def _update_layout(self):
        """Arrange elements horizontally with spacing."""
        current_x = self.x
        for element in self.elements:
            element.x = current_x
            element.y = self.y
            current_x += element.width + self.spacing

class GridLayout(UILayout):
    """Layout that arranges elements in a grid."""
    
    def __init__(self, x: int = 0, y: int = 0, cols: int = 2, 
                 cell_width: int = 100, cell_height: int = 100,
                 h_spacing: int = 5, v_spacing: int = 5):
        """
        Initialize a grid layout.
        
        Args:
            x (int): Starting X coordinate.
            y (int): Starting Y coordinate.
            cols (int): Number of columns in the grid.
            cell_width (int): Width of each cell.
            cell_height (int): Height of each cell.
            h_spacing (int): Horizontal spacing between cells.
            v_spacing (int): Vertical spacing between cells.
        """
        super().__init__(x, y)
        self.cols = cols
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        
    def _update_layout(self):
        """Arrange elements in a grid pattern."""
        for i, element in enumerate(self.elements):
            row = i // self.cols
            col = i % self.cols
            
            element.x = self.x + col * (self.cell_width + self.h_spacing)
            element.y = self.y + row * (self.cell_height + self.v_spacing)
            element.width = self.cell_width
            element.height = self.cell_height

class JustifiedLayout(UILayout):
    """Layout that justifies elements with equal spacing."""
    
    def __init__(self, x: int = 0, y: int = 0, 
                 justify_x: bool = True, justify_y: bool = False):
        """
        Initialize a justified layout.
        
        Args:
            x (int): Starting X coordinate.
            y (int): Starting Y coordinate.
            justify_x (bool): Whether to justify horizontally.
            justify_y (bool): Whether to justify vertically.
        """
        super().__init__(x, y)
        self.justify_x = justify_x
        self.justify_y = justify_y
        
    def _update_layout(self):
        """Arrange elements with justified spacing."""
        if not self.elements:
            return
            
        if self.justify_x:
            total_width = sum(element.width for element in self.elements)
            available_space = max(0, self.width - total_width) if hasattr(self, 'width') else 0
            spacing = available_space / (len(self.elements) - 1) if len(self.elements) > 1 else 0
            
            current_x = self.x
            for element in self.elements:
                element.x = current_x
                element.y = self.y
                current_x += element.width + spacing
                
        elif self.justify_y:
            total_height = sum(element.height for element in self.elements)
            available_space = max(0, self.height - total_height) if hasattr(self, 'height') else 0
            spacing = available_space / (len(self.elements) - 1) if len(self.elements) > 1 else 0
            
            current_y = self.y
            for element in self.elements:
                element.x = self.x
                element.y = current_y
                current_y += element.height + spacing
                
class Animation:
    duration:float
    start_time:float
    end_time:float
    animation_type:AnimationTypes
    