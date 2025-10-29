from typing import Dict, Tuple
from enum import Enum

class UIState(Enum):
    """Enumeration of possible UI element states."""
    NORMAL = "normal"
    HOVERED = "hovered"
    PRESSED = "pressed"
    DISABLED = "disabled"

class UIStyle:
    """Defines the visual style for UI elements."""
    
    def __init__(self):
        """
        Initialize a UI style with default values.
        """
        self.colors = {}
        self.font_size = 16
        self.font_name = None
        self.padding = 5
        
    def get_color(self, state: UIState) -> Tuple[int, int, int]:
        """
        Get the color for a specific UI state.
        
        Args:
            state (UIState): The UI state to get color for.
            
        Returns:
            Tuple[int, int, int]: RGB color tuple for the specified state.
        """
        return self.colors.get(state, (255, 255, 255))

class Theme:
    """Collection of styles for different UI elements forming a complete theme."""
    
    def __init__(self):
        """
        Initialize a theme with default styles for all UI elements.
        """
        self.button_style = UIStyle()
        self.button_style.colors = {
            UIState.NORMAL: (100, 100, 200),
            UIState.HOVERED: (120, 120, 220),
            UIState.PRESSED: (80, 80, 180),
            UIState.DISABLED: (100, 100, 100)
        }
        
        self.label_style = UIStyle()
        self.label_style.colors = {
            UIState.NORMAL: (255, 255, 255)
        }
        
        self.slider_style = UIStyle()
        self.slider_style.colors = {
            UIState.NORMAL: (150, 150, 150),
            UIState.HOVERED: (170, 170, 170),
            UIState.PRESSED: (130, 130, 130)
        }

# Default theme
default_theme = Theme()