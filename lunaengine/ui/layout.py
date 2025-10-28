from typing import List
from .elements import UIElement

class UILayout:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y
        self.elements = []
        self.spacing = 10
        
    def add_element(self, element: UIElement):
        """Add an element to the layout"""
        self.elements.append(element)
        self._update_layout()
        
    def remove_element(self, element: UIElement):
        """Remove an element from the layout"""
        if element in self.elements:
            self.elements.remove(element)
            self._update_layout()
            
    def _update_layout(self):
        """Update element positions based on layout rules"""
        pass

class VerticalLayout(UILayout):
    def __init__(self, x: int = 0, y: int = 0, spacing: int = 10):
        super().__init__(x, y)
        self.spacing = spacing
        
    def _update_layout(self):
        current_y = self.y
        for element in self.elements:
            element.x = self.x
            element.y = current_y
            current_y += element.height + self.spacing

class HorizontalLayout(UILayout):
    def __init__(self, x: int = 0, y: int = 0, spacing: int = 10):
        super().__init__(x, y)
        self.spacing = spacing
        
    def _update_layout(self):
        current_x = self.x
        for element in self.elements:
            element.x = current_x
            element.y = self.y
            current_x += element.width + self.spacing