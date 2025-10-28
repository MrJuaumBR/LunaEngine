import pygame
import numpy as np
from typing import Optional, Callable, List, Tuple
from enum import Enum

class UIState(Enum):
    NORMAL = 0
    HOVERED = 1
    PRESSED = 2
    DISABLED = 3

class FontManager:
    """Manages fonts and ensures Pygame font system is initialized"""
    _initialized = False
    _default_fonts = {}
    
    @classmethod
    def initialize(cls):
        """Initialize the font system"""
        if not cls._initialized:
            pygame.font.init()
            cls._initialized = True
    
    @classmethod
    def get_font(cls, font_name: Optional[str] = None, font_size: int = 24):
        """Get a font, initializing the system if needed"""
        if not cls._initialized:
            cls.initialize()
            
        # Use default font if None specified
        if font_name is None:
            key = (None, font_size)
            if key not in cls._default_fonts:
                cls._default_fonts[key] = pygame.font.Font(None, font_size)
            return cls._default_fonts[key]
        else:
            return pygame.font.Font(font_name, font_size)

class UIElement:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.state = UIState.NORMAL
        self.visible = True
        self.enabled = True
        self.children = []
        self.parent = None
        
    def add_child(self, child):
        """Add a child element"""
        child.parent = self
        self.children.append(child)
        
    def update(self, dt: float):
        """Update element state - kept for compatibility"""
        pass
        
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update element with current mouse state"""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        # Check if mouse is over element
        if (self.x <= mouse_pos[0] <= self.x + self.width and 
            self.y <= mouse_pos[1] <= self.y + self.height):
            
            if mouse_pressed:
                self.state = UIState.PRESSED
                self.on_click()
            else:
                self.state = UIState.HOVERED
                self.on_hover()
        else:
            self.state = UIState.NORMAL
            
        # Update children
        for child in self.children:
            child._update_with_mouse(mouse_pos, mouse_pressed, dt)
    
    def render(self, renderer):
        """Render the element"""
        if not self.visible:
            return
            
        for child in self.children:
            child.render(renderer)
    
    def on_click(self):
        """Called when element is clicked"""
        pass
        
    def on_hover(self):
        """Called when mouse hovers over element"""
        pass

class TextLabel(UIElement):
    def __init__(self, x: int, y: int, text: str, font_size: int = 24, 
                 color: Tuple[int, int, int] = (255, 255, 255), 
                 font_name: Optional[str] = None):
        # Calculate initial size based on text
        FontManager.initialize()
        font = FontManager.get_font(font_name, font_size)
        text_surface = font.render(text, True, color)
        
        super().__init__(x, y, text_surface.get_width(), text_surface.get_height())
        self.text = text
        self.font_size = font_size
        self.color = color
        self.font_name = font_name
        self._font = None
        
    @property
    def font(self):
        """Lazy font loading"""
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
        
    def set_text(self, text: str):
        """Update the text and recalculate size"""
        self.text = text
        text_surface = self.font.render(text, True, self.color)
        self.width = text_surface.get_width()
        self.height = text_surface.get_height()
        
    def render(self, renderer):
        if not self.visible:
            return
            
        # Render the text
        text_surface = self.font.render(self.text, True, self.color)
        renderer.draw_surface(text_surface, self.x, self.y)
        
        super().render(renderer)

class Button(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, text: str = "", 
                 font_size: int = 20, font_name: Optional[str] = None):
        super().__init__(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.font_name = font_name
        self.on_click_callback = None
        self.colors = {
            UIState.NORMAL: (100, 100, 200),    # Blue
            UIState.HOVERED: (120, 120, 220),   # Lighter Blue
            UIState.PRESSED: (80, 80, 180),     # Darker Blue
            UIState.DISABLED: (100, 100, 100)   # Gray
        }
        self._font = None
        self._was_pressed = False  # Track press state
        
    @property
    def font(self):
        """Lazy font loading"""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
        
    def set_on_click(self, callback: Callable):
        """Set the click callback"""
        self.on_click_callback = callback
        
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update button with proper click handling"""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        # Check if mouse is over element
        mouse_over = (self.x <= mouse_pos[0] <= self.x + self.width and 
                     self.y <= mouse_pos[1] <= self.y + self.height)
        
        if mouse_over:
            if mouse_pressed:
                self.state = UIState.PRESSED
                # Only trigger click once when first pressed
                if not self._was_pressed and self.on_click_callback:
                    self.on_click_callback()
                self._was_pressed = True
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False
            
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
            
    def render(self, renderer):
        if not self.visible:
            return
            
        # Draw button background
        color = self.colors[self.state]
        renderer.draw_rect(self.x, self.y, self.width, self.height, color)
        
        # Draw button text
        if self.text:
            text_surface = self.font.render(self.text, True, (255, 255, 255))
            text_x = self.x + (self.width - text_surface.get_width()) // 2
            text_y = self.y + (self.height - text_surface.get_height()) // 2
            renderer.draw_surface(text_surface, text_x, text_y)
            
        super().render(renderer)

class Slider(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, 
                 min_val: float = 0, max_val: float = 100, value: float = 50):
        super().__init__(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.dragging = False
        self.on_value_changed = None
        
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update slider with mouse interaction"""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        thumb_x = self.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        thumb_rect = (thumb_x - 5, self.y, 10, self.height)
        
        mouse_over_thumb = (thumb_rect[0] <= mouse_pos[0] <= thumb_rect[0] + thumb_rect[2] and 
                           thumb_rect[1] <= mouse_pos[1] <= thumb_rect[1] + thumb_rect[3])
        
        if mouse_pressed and (mouse_over_thumb or self.dragging):
            self.dragging = True
            self.state = UIState.PRESSED
            # Update value based on mouse position
            relative_x = max(0, min(self.width, mouse_pos[0] - self.x))
            new_value = self.min_val + (relative_x / self.width) * (self.max_val - self.min_val)
            
            if new_value != self.value:
                self.value = new_value
                if self.on_value_changed:
                    self.on_value_changed(self.value)
        else:
            self.dragging = False
            if (thumb_rect[0] <= mouse_pos[0] <= thumb_rect[0] + thumb_rect[2] and 
                thumb_rect[1] <= mouse_pos[1] <= thumb_rect[1] + thumb_rect[3]):
                self.state = UIState.HOVERED
            else:
                self.state = UIState.NORMAL
                
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
            
    def render(self, renderer):
        if not self.visible:
            return
            
        # Draw track
        track_color = (100, 100, 100)
        renderer.draw_rect(self.x, self.y + self.height//2 - 2, self.width, 4, track_color)
        
        # Draw thumb
        thumb_x = self.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        thumb_color = (200, 100, 100) if self.state == UIState.PRESSED else (150, 80, 80)
        renderer.draw_rect(thumb_x - 5, self.y, 10, self.height, thumb_color)
        
        super().render(renderer)
        
class Dropdown(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, 
                 options: List[str] = None, font_size: int = 20, 
                 font_name: Optional[str] = None):
        super().__init__(x, y, width, height)
        self.options = options or []
        self.selected_index = 0
        self.expanded = False
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self._option_height = 25
        self.on_selection_changed = None
        self._just_opened = False  # Prevent immediate closing
        
    @property
    def font(self):
        """Lazy font loading"""
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
        
    def _update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float):
        """Update dropdown with mouse interaction"""
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        # Check if mouse is over main dropdown
        main_rect = (self.x, self.y, self.width, self.height)
        mouse_over_main = (main_rect[0] <= mouse_pos[0] <= main_rect[0] + main_rect[2] and 
                          main_rect[1] <= mouse_pos[1] <= main_rect[1] + main_rect[3])
        
        # Handle mouse press
        if mouse_pressed and not self._just_opened:
            if mouse_over_main:
                # Toggle expansion
                self.expanded = not self.expanded
                self._just_opened = self.expanded
            elif self.expanded:
                # Check if clicking on an option
                option_clicked = False
                for i, option in enumerate(self.options):
                    option_rect = (self.x, self.y + self.height + i * self._option_height, 
                                 self.width, self._option_height)
                    if (option_rect[0] <= mouse_pos[0] <= option_rect[0] + option_rect[2] and 
                        option_rect[1] <= mouse_pos[1] <= option_rect[1] + option_rect[3]):
                        old_index = self.selected_index
                        self.selected_index = i
                        self.expanded = False
                        self._just_opened = False
                        if old_index != i and self.on_selection_changed:
                            self.on_selection_changed(i, self.options[i])
                        option_clicked = True
                        break
                
                # Clicked outside dropdown, close it
                if not option_clicked:
                    self.expanded = False
                    self._just_opened = False
        else:
            # Reset the just_opened flag when mouse is released
            if not mouse_pressed:
                self._just_opened = False
            
            if mouse_over_main or self.expanded:
                self.state = UIState.HOVERED
            else:
                self.state = UIState.NORMAL
                
        super()._update_with_mouse(mouse_pos, mouse_pressed, dt)
            
    def render(self, renderer):
        if not self.visible:
            return
            
        # Draw main box
        main_color = (80, 80, 120) if self.state == UIState.NORMAL else (100, 100, 140)
        renderer.draw_rect(self.x, self.y, self.width, self.height, main_color)
        
        # Draw border
        renderer.draw_rect(self.x, self.y, self.width, self.height, (200, 200, 200), fill=False)
        
        # Draw selected text
        if self.options:
            text = self.options[self.selected_index]
            # Truncate text if too long
            if len(text) > 15:
                text = text[:15] + "..."
            text_surface = self.font.render(text, True, (255, 255, 255))
            renderer.draw_surface(text_surface, self.x + 5, self.y + (self.height - text_surface.get_height()) // 2)
        
        # Draw dropdown arrow
        arrow_color = (200, 200, 200)
        arrow_points = [
            (self.x + self.width - 15, self.y + self.height//2 - 3),
            (self.x + self.width - 5, self.y + self.height//2 - 3),
            (self.x + self.width - 10, self.y + self.height//2 + 3)
        ]
        # For PygameRenderer, we need to draw on the surface directly
        surface = renderer.get_surface()
        pygame.draw.polygon(surface, arrow_color, arrow_points)
        
        # Draw expanded options - these will render on top due to rendering order
        if self.expanded:
            for i, option in enumerate(self.options):
                option_y = self.y + self.height + i * self._option_height
                is_selected = i == self.selected_index
                option_color = (60, 60, 100) if not is_selected else (80, 80, 120)
                hover_color = (70, 70, 110)
                
                # Check if mouse is over this option
                mouse_pos = pygame.mouse.get_pos()
                option_rect = (self.x, option_y, self.width, self._option_height)
                mouse_over_option = (option_rect[0] <= mouse_pos[0] <= option_rect[0] + option_rect[2] and 
                                   option_rect[1] <= mouse_pos[1] <= option_rect[1] + option_rect[3])
                
                # Use hover color if mouse is over option
                final_color = hover_color if mouse_over_option else option_color
                renderer.draw_rect(self.x, option_y, self.width, self._option_height, final_color)
                
                # Draw option border
                renderer.draw_rect(self.x, option_y, self.width, self._option_height, (180, 180, 180), fill=False)
                
                text_surface = self.font.render(option, True, (255, 255, 255))
                renderer.draw_surface(text_surface, self.x + 5, option_y + (self._option_height - text_surface.get_height()) // 2)
                
        super().render(renderer)
    
    def add_option(self, option: str):
        """Add an option to the dropdown"""
        self.options.append(option)
    
    def remove_option(self, option: str):
        """Remove an option from the dropdown"""
        if option in self.options:
            self.options.remove(option)
            # Adjust selected index if needed
            if self.selected_index >= len(self.options):
                self.selected_index = max(0, len(self.options) - 1)
    
    def set_selected_index(self, index: int):
        """Set the selected option by index"""
        if 0 <= index < len(self.options):
            old_index = self.selected_index
            self.selected_index = index
            if old_index != index and self.on_selection_changed:
                self.on_selection_changed(index, self.options[index])
    
    def set_on_selection_changed(self, callback: Callable[[int, str], None]):
        """Set callback for when selection changes"""
        self.on_selection_changed = callback