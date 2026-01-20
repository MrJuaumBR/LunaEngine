"""
Basic Icons for LunaEngine(All them need to be made in Python to be compiled with the Engine/Framework)

LOCATION: lunaengine/misc/icons.py
"""

import pygame as pg
from enum import Enum
import math

class Icon:
    name:str
    icon:pg.Surface
    def __init__(self, name:str, size:int=32):
        self.name = name
        self.size = size
        self.generate()
        
    def generate(self):
        pass
    
    def get_icon(self):
        return self.icon

class IconInfo(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        pg.draw.circle(self.icon, (70, 130, 180), (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, (255, 255, 255), (self.size//2, self.size//2), self.size//2 - 4)
        
        # Draw question mark
        font_size = max(12, self.size // 2)
        font = pg.font.Font(None, font_size)
        text = font.render("?", True, (70, 130, 180))
        text_rect = text.get_rect(center=(self.size//2, self.size//2))
        self.icon.blit(text, text_rect)

class IconCheck(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw checkmark
        points = [
            (self.size//4, self.size//2),
            (self.size//2, 3*self.size//4),
            (3*self.size//4, self.size//4)
        ]
        pg.draw.lines(self.icon, (50, 205, 50), False, points, max(3, self.size//8))

class IconCross(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw X
        pg.draw.line(self.icon, (220, 20, 60), 
                    (self.size//4, self.size//4), 
                    (3*self.size//4, 3*self.size//4), 
                    max(3, self.size//8))
        pg.draw.line(self.icon, (220, 20, 60), 
                    (3*self.size//4, self.size//4), 
                    (self.size//4, 3*self.size//4), 
                    max(3, self.size//8))

class IconWarn(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw triangle for warning
        points = [
            (self.size//2, self.size//4),
            (self.size//4, 3*self.size//4),
            (3*self.size//4, 3*self.size//4)
        ]
        pg.draw.polygon(self.icon, (255, 215, 0), points)
        
        # Draw exclamation mark
        pg.draw.rect(self.icon, (139, 69, 19), 
                    (self.size//2 - self.size//16, self.size//2 - self.size//8, 
                     self.size//8, self.size//2))
        pg.draw.circle(self.icon, (139, 69, 19), 
                      (self.size//2, 3*self.size//4), self.size//16)

class IconError(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw circle with X
        pg.draw.circle(self.icon, (220, 20, 60), (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, (255, 240, 240), (self.size//2, self.size//2), self.size//2 - 4)
        
        # Draw X inside
        margin = self.size // 4
        pg.draw.line(self.icon, (220, 20, 60), 
                    (margin, margin), 
                    (self.size - margin, self.size - margin), 
                    max(3, self.size//10))
        pg.draw.line(self.icon, (220, 20, 60), 
                    (self.size - margin, margin), 
                    (margin, self.size - margin), 
                    max(3, self.size//10))

class IconSuccess(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw circle with checkmark
        pg.draw.circle(self.icon, (50, 205, 50), (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, (240, 255, 240), (self.size//2, self.size//2), self.size//2 - 4)
        
        # Draw checkmark inside
        points = [
            (self.size//4, self.size//2),
            (self.size//2, 3*self.size//4),
            (3*self.size//4, self.size//4)
        ]
        pg.draw.lines(self.icon, (50, 205, 50), False, points, max(3, self.size//10))

class IconTriangleUp(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        points = [
            (self.size//2, self.size//4),
            (self.size//4, 3*self.size//4),
            (3*self.size//4, 3*self.size//4)
        ]
        pg.draw.polygon(self.icon, (100, 149, 237), points)

class IconTriangleDown(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        points = [
            (self.size//4, self.size//4),
            (3*self.size//4, self.size//4),
            (self.size//2, 3*self.size//4)
        ]
        pg.draw.polygon(self.icon, (100, 149, 237), points)

class IconTriangleLeft(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        points = [
            (3*self.size//4, self.size//4),
            (3*self.size//4, 3*self.size//4),
            (self.size//4, self.size//2)
        ]
        pg.draw.polygon(self.icon, (100, 149, 237), points)

class IconTriangleRight(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        points = [
            (self.size//4, self.size//4),
            (self.size//4, 3*self.size//4),
            (3*self.size//4, self.size//2)
        ]
        pg.draw.polygon(self.icon, (100, 149, 237), points)

class IconPlus(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw plus sign
        center = self.size // 2
        thickness = max(3, self.size // 8)
        length = self.size // 3
        
        pg.draw.rect(self.icon, (70, 130, 180), 
                    (center - thickness//2, center - length, 
                     thickness, length * 2))
        pg.draw.rect(self.icon, (70, 130, 180), 
                    (center - length, center - thickness//2, 
                     length * 2, thickness))

class IconMinus(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw minus sign
        center = self.size // 2
        thickness = max(3, self.size // 8)
        length = self.size // 3
        
        pg.draw.rect(self.icon, (220, 20, 60), 
                    (center - length, center - thickness//2, 
                     length * 2, thickness))

class IconCircle(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        pg.draw.circle(self.icon, (70, 130, 180), 
                      (self.size//2, self.size//2), 
                      self.size//2 - 2)

class IconSquare(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        margin = 2
        pg.draw.rect(self.icon, (70, 130, 180), 
                    (margin, margin, self.size - 2*margin, self.size - 2*margin))

class IconGear(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        center = (self.size//2, self.size//2)
        radius = self.size//2 - 2
        
        # Draw gear teeth
        for i in range(8):
            angle = i * math.pi / 4
            x1 = center[0] + (radius - self.size//8) * math.cos(angle)
            y1 = center[1] + (radius - self.size//8) * math.sin(angle)
            x2 = center[0] + (radius + self.size//8) * math.cos(angle)
            y2 = center[1] + (radius + self.size//8) * math.sin(angle)
            
            pg.draw.line(self.icon, (70, 130, 180), (x1, y1), (x2, y2), max(2, self.size//12))
        
        # Draw center circle
        pg.draw.circle(self.icon, (70, 130, 180), center, radius - self.size//4)
        pg.draw.circle(self.icon, (240, 248, 255), center, radius - self.size//4 - 2)

class Icons(Enum):
    INFO = "info"
    CHECK = "check"
    CROSS = "cross"
    WARN = "warn"
    ERROR = "error"
    SUCCESS = "success"
    TRIANGLE_UP = "triangle_up"
    TRIANGLE_DOWN = "triangle_down"
    TRIANGLE_LEFT = "triangle_left"
    TRIANGLE_RIGHT = "triangle_right"
    PLUS = "plus"
    MINUS = "minus"
    CIRCLE = "circle"
    SQUARE = "square"
    GEAR = "gear"

class IconFactory:
    @staticmethod
    def get_icon(icon_type: Icons, size: int = 32) -> pg.Surface:
        """Factory method to get icon by type"""
        icon_classes = {
            Icons.INFO: IconInfo,
            Icons.CHECK: IconCheck,
            Icons.CROSS: IconCross,
            Icons.WARN: IconWarn,
            Icons.ERROR: IconError,
            Icons.SUCCESS: IconSuccess,
            Icons.TRIANGLE_UP: IconTriangleUp,
            Icons.TRIANGLE_DOWN: IconTriangleDown,
            Icons.TRIANGLE_LEFT: IconTriangleLeft,
            Icons.TRIANGLE_RIGHT: IconTriangleRight,
            Icons.PLUS: IconPlus,
            Icons.MINUS: IconMinus,
            Icons.CIRCLE: IconCircle,
            Icons.SQUARE: IconSquare,
            Icons.GEAR: IconGear,
        }
        
        if icon_type in icon_classes:
            return icon_classes[icon_type](icon_type.value, size).get_icon()
        else:
            # Fallback to INFO icon
            return IconInfo("info", size).get_icon()

# Convenience functions
def get_icon(name: str, size: int = 32) -> pg.Surface:
    """Get icon by name string"""
    try:
        icon_type = Icons(name.lower())
        return IconFactory.get_icon(icon_type, size)
    except ValueError:
        return IconFactory.get_icon(Icons.INFO, size)

def get_all_icons(size: int = 32) -> dict:
    """Get dictionary of all icons"""
    icons_dict = {}
    for icon_type in Icons:
        icons_dict[icon_type.value] = IconFactory.get_icon(icon_type, size)
    return icons_dict