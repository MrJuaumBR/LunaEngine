"""
Basic Icons for LunaEngine(All them need to be made in Python to be compiled with the Engine/Framework)

LOCATION: lunaengine/misc/icons.py
"""

import pygame as pg
from enum import Enum
import math

# Color palette for consistent styling
class Colors:
    # Primary colors
    PRIMARY = (70, 130, 180)      # Steel Blue
    PRIMARY_LIGHT = (100, 149, 237)  # Cornflower Blue
    PRIMARY_DARK = (30, 100, 150)   # Darker Blue
    
    # Status colors
    SUCCESS = (50, 205, 50)       # Lime Green
    SUCCESS_LIGHT = (144, 238, 144)  # Light Green
    ERROR = (220, 20, 60)         # Crimson
    ERROR_LIGHT = (255, 200, 200) # Light Red
    WARNING = (255, 165, 0)       # Orange (better visibility than gold)
    WARNING_LIGHT = (255, 215, 0) # Gold
    
    # Neutral colors
    WHITE = (255, 255, 255)
    LIGHT_GRAY = (240, 240, 240)
    DARK_GRAY = (100, 100, 100)
    BLACK = (40, 40, 40)
    
    # Accent colors
    FOLDER = (255, 215, 0)        # Gold for folder
    KEY = (184, 134, 11)          # Dark Goldenrod
    LOCK = (139, 0, 0)           # Dark Red
    UNLOCK = (0, 139, 0)         # Dark Green
    HOME = (138, 43, 226)        # Blue Violet
    SAVE = (34, 139, 34)         # Forest Green
    LOAD = (65, 105, 225)        # Royal Blue

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
        # Draw outer circle with outline
        pg.draw.circle(self.icon, Colors.PRIMARY_DARK, (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, Colors.PRIMARY, (self.size//2, self.size//2), self.size//2 - 4)
        pg.draw.circle(self.icon, Colors.WHITE, (self.size//2, self.size//2), self.size//2 - 6)
        
        # Draw question mark
        font_size = max(12, self.size // 2)
        font = pg.font.Font(None, font_size)
        text = font.render("?", True, Colors.PRIMARY)
        text_rect = text.get_rect(center=(self.size//2, self.size//2))
        self.icon.blit(text, text_rect)

class IconCheck(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw thicker checkmark with better visibility
        thickness = max(3, self.size//8)
        offset = self.size // 12
        
        points = [
            (self.size//4 + offset, self.size//2),
            (self.size//2, 3*self.size//4 - offset),
            (3*self.size//4 - offset, self.size//4 + offset)
        ]
        pg.draw.lines(self.icon, Colors.SUCCESS, False, points, thickness)

class IconCross(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw X with consistent thickness
        thickness = max(3, self.size//8)
        margin = self.size // 4
        
        pg.draw.line(self.icon, Colors.ERROR, 
                    (margin, margin), 
                    (self.size - margin, self.size - margin), 
                    thickness)
        pg.draw.line(self.icon, Colors.ERROR, 
                    (self.size - margin, margin), 
                    (margin, self.size - margin), 
                    thickness)

class IconWarn(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw triangle for warning with outline
        points = [
            (self.size//2, self.size//4 + 2),
            (self.size//4 + 2, 3*self.size//4 - 2),
            (3*self.size//4 - 2, 3*self.size//4 - 2)
        ]
        pg.draw.polygon(self.icon, Colors.WARNING, points)
        
        # Draw exclamation mark
        ex_height = self.size // 2
        ex_width = max(3, self.size // 10)
        
        # Draw stem
        pg.draw.rect(self.icon, Colors.WHITE, 
                    (self.size//2 - ex_width//2, self.size//4 + self.size//6, 
                     ex_width, ex_height))
        # Draw dot
        pg.draw.circle(self.icon, Colors.WHITE, 
                      (self.size//2, 3*self.size//4 - self.size//8), 
                      ex_width)

class IconError(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw circle with X
        pg.draw.circle(self.icon, Colors.ERROR, (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, Colors.ERROR_LIGHT, (self.size//2, self.size//2), self.size//2 - 4)
        pg.draw.circle(self.icon, Colors.WHITE, (self.size//2, self.size//2), self.size//2 - 6)
        
        # Draw X inside
        margin = self.size // 4
        thickness = max(3, self.size//10)
        pg.draw.line(self.icon, Colors.ERROR, 
                    (margin, margin), 
                    (self.size - margin, self.size - margin), 
                    thickness)
        pg.draw.line(self.icon, Colors.ERROR, 
                    (self.size - margin, margin), 
                    (margin, self.size - margin), 
                    thickness)

class IconSuccess(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw circle with checkmark
        pg.draw.circle(self.icon, Colors.SUCCESS, (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, Colors.SUCCESS_LIGHT, (self.size//2, self.size//2), self.size//2 - 4)
        pg.draw.circle(self.icon, Colors.WHITE, (self.size//2, self.size//2), self.size//2 - 6)
        
        # Draw checkmark inside
        thickness = max(3, self.size//10)
        offset = self.size // 12
        
        points = [
            (self.size//4 + offset, self.size//2),
            (self.size//2, 3*self.size//4 - offset),
            (3*self.size//4 - offset, self.size//4 + offset)
        ]
        pg.draw.lines(self.icon, Colors.SUCCESS, False, points, thickness)

class IconTriangleUp(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        points = [
            (self.size//2, self.size//4),
            (self.size//4, 3*self.size//4),
            (3*self.size//4, 3*self.size//4)
        ]
        pg.draw.polygon(self.icon, Colors.PRIMARY, points)
        pg.draw.polygon(self.icon, Colors.PRIMARY_LIGHT, points, 2)  # Outline

class IconTriangleDown(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        points = [
            (self.size//4, self.size//4),
            (3*self.size//4, self.size//4),
            (self.size//2, 3*self.size//4)
        ]
        pg.draw.polygon(self.icon, Colors.PRIMARY, points)
        pg.draw.polygon(self.icon, Colors.PRIMARY_LIGHT, points, 2)  # Outline

class IconTriangleLeft(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        points = [
            (3*self.size//4, self.size//4),
            (3*self.size//4, 3*self.size//4),
            (self.size//4, self.size//2)
        ]
        pg.draw.polygon(self.icon, Colors.PRIMARY, points)
        pg.draw.polygon(self.icon, Colors.PRIMARY_LIGHT, points, 2)  # Outline

class IconTriangleRight(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        points = [
            (self.size//4, self.size//4),
            (self.size//4, 3*self.size//4),
            (3*self.size//4, self.size//2)
        ]
        pg.draw.polygon(self.icon, Colors.PRIMARY, points)
        pg.draw.polygon(self.icon, Colors.PRIMARY_LIGHT, points, 2)  # Outline

class IconPlus(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw plus sign with circle background
        pg.draw.circle(self.icon, Colors.PRIMARY, (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, Colors.WHITE, (self.size//2, self.size//2), self.size//2 - 4)
        
        center = self.size // 2
        thickness = max(3, self.size // 10)
        length = self.size // 3
        
        pg.draw.rect(self.icon, Colors.PRIMARY, 
                    (center - thickness//2, center - length, 
                     thickness, length * 2))
        pg.draw.rect(self.icon, Colors.PRIMARY, 
                    (center - length, center - thickness//2, 
                     length * 2, thickness))

class IconMinus(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw minus sign with circle background
        pg.draw.circle(self.icon, Colors.ERROR, (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, Colors.WHITE, (self.size//2, self.size//2), self.size//2 - 4)
        
        center = self.size // 2
        thickness = max(3, self.size // 10)
        length = self.size // 3
        
        pg.draw.rect(self.icon, Colors.ERROR, 
                    (center - length, center - thickness//2, 
                     length * 2, thickness))

class IconCircle(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        pg.draw.circle(self.icon, Colors.PRIMARY, 
                      (self.size//2, self.size//2), 
                      self.size//2 - 2)
        pg.draw.circle(self.icon, Colors.PRIMARY_LIGHT, 
                      (self.size//2, self.size//2), 
                      self.size//2 - 4)

class IconSquare(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        margin = 2
        pg.draw.rect(self.icon, Colors.PRIMARY, 
                    (margin, margin, self.size - 2*margin, self.size - 2*margin))
        pg.draw.rect(self.icon, Colors.PRIMARY_LIGHT, 
                    (margin + 2, margin + 2, self.size - 2*margin - 4, self.size - 2*margin - 4))

class IconGear(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        center = (self.size//2, self.size//2)
        radius = self.size//2 - 2
        
        # Draw outer circle
        pg.draw.circle(self.icon, Colors.PRIMARY_DARK, center, radius)
        pg.draw.circle(self.icon, Colors.PRIMARY, center, radius - 2)
        
        # Draw gear teeth
        for i in range(8):
            angle = i * math.pi / 4
            x1 = center[0] + (radius - self.size//6) * math.cos(angle)
            y1 = center[1] + (radius - self.size//6) * math.sin(angle)
            x2 = center[0] + (radius + self.size//12) * math.cos(angle)
            y2 = center[1] + (radius + self.size//12) * math.sin(angle)
            
            pg.draw.line(self.icon, Colors.WHITE, (x1, y1), (x2, y2), max(2, self.size//16))
        
        # Draw center circle
        pg.draw.circle(self.icon, Colors.WHITE, center, radius - self.size//3)

# NEW ICONS START HERE

class IconFolder(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw folder shape
        # Folder tab
        pg.draw.rect(self.icon, Colors.FOLDER,
                    (self.size//4, self.size//4, self.size//2, self.size//8))
        # Folder body
        pg.draw.rect(self.icon, Colors.FOLDER,
                    (self.size//6, self.size//3, 
                     self.size - 2*(self.size//6), 2*self.size//3 - self.size//6))
        
        # Add highlight/details
        pg.draw.rect(self.icon, Colors.WARNING_LIGHT,
                    (self.size//4 + 2, self.size//4 + 2, 
                     self.size//2 - 4, self.size//8 - 4))
        pg.draw.rect(self.icon, Colors.WARNING_LIGHT,
                    (self.size//6 + 2, self.size//3 + 2, 
                     self.size - 2*(self.size//6) - 4, 2*self.size//3 - self.size//6 - 4), 1)

class IconKey(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw key handle (circle)
        pg.draw.circle(self.icon, Colors.KEY, 
                      (self.size//3, self.size//2), 
                      self.size//6)
        
        # Draw key shaft
        pg.draw.rect(self.icon, Colors.KEY,
                    (self.size//3, self.size//2 - self.size//16,
                     self.size//2, self.size//8))
        
        # Draw key teeth (notches)
        tooth_height = self.size // 6
        pg.draw.rect(self.icon, Colors.KEY,
                    (2*self.size//3, self.size//2 - tooth_height//2,
                     self.size//12, tooth_height))

class IconLockLocked(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw lock body
        lock_width = self.size // 2
        lock_height = self.size // 2
        x = (self.size - lock_width) // 2
        y = self.size // 3
        
        pg.draw.rect(self.icon, Colors.LOCK,
                    (x, y, lock_width, lock_height))
        pg.draw.rect(self.icon, Colors.ERROR,
                    (x + 2, y + 2, lock_width - 4, lock_height - 4))
        
        # Draw shackle (U-shaped top)
        shackle_height = self.size // 6
        shackle_width = lock_width + self.size // 6
        shackle_x = (self.size - shackle_width) // 2
        
        pg.draw.rect(self.icon, Colors.LOCK,
                    (shackle_x, y - shackle_height//2,
                     shackle_width, shackle_height))
        pg.draw.rect(self.icon, Colors.ERROR,
                    (shackle_x + 2, y - shackle_height//2 + 2,
                     shackle_width - 4, shackle_height - 4))

class IconLockUnlocked(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw lock body (open)
        lock_width = self.size // 2
        lock_height = self.size // 2
        x = (self.size - lock_width) // 2
        y = self.size // 3
        
        pg.draw.rect(self.icon, Colors.UNLOCK,
                    (x, y, lock_width, lock_height))
        pg.draw.rect(self.icon, Colors.SUCCESS,
                    (x + 2, y + 2, lock_width - 4, lock_height - 4))
        
        # Draw open shackle (just the sides, not connected)
        shackle_height = self.size // 6
        shackle_width = lock_width + self.size // 6
        shackle_x = (self.size - shackle_width) // 2
        
        # Left side
        pg.draw.rect(self.icon, Colors.UNLOCK,
                    (shackle_x, y - shackle_height//2,
                     shackle_width // 4, shackle_height))
        # Right side
        pg.draw.rect(self.icon, Colors.UNLOCK,
                    (shackle_x + 3*shackle_width//4, y - shackle_height//2,
                     shackle_width // 4, shackle_height))

class IconHome(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw house shape
        # Roof (triangle)
        roof_points = [
            (self.size//2, self.size//4),
            (self.size//4, self.size//2),
            (3*self.size//4, self.size//2)
        ]
        pg.draw.polygon(self.icon, Colors.HOME, roof_points)
        
        # House body
        pg.draw.rect(self.icon, Colors.HOME,
                    (self.size//3, self.size//2,
                     self.size//3, self.size//3))
        
        # Door
        pg.draw.rect(self.icon, Colors.PRIMARY_DARK,
                    (self.size//2 - self.size//12, 2*self.size//3,
                     self.size//6, self.size//6))
        
        # Window
        pg.draw.rect(self.icon, Colors.PRIMARY_LIGHT,
                    (self.size//3 + self.size//12, self.size//2 + self.size//12,
                     self.size//12, self.size//12))

class IconSave(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw floppy disk shape
        # Main body
        pg.draw.rect(self.icon, Colors.SAVE,
                    (self.size//4, self.size//6,
                     2*self.size//4, 3*self.size//4))
        
        # Metal slide
        pg.draw.rect(self.icon, Colors.DARK_GRAY,
                    (self.size//4, self.size//6,
                     2*self.size//4, self.size//8))
        
        # Label area
        pg.draw.rect(self.icon, Colors.WHITE,
                    (self.size//4 + self.size//12, self.size//3,
                     2*self.size//4 - 2*(self.size//12), self.size//3))
        
        # Write "SAVE" text if size is large enough
        if self.size >= 24:
            font_size = max(8, self.size // 4)
            font = pg.font.Font(None, font_size)
            text = font.render("SAVE", True, Colors.SAVE)
            text_rect = text.get_rect(center=(self.size//2, self.size//2))
            self.icon.blit(text, text_rect)

class IconLoad(Icon):
    def generate(self):
        self.icon = pg.Surface((self.size, self.size), pg.SRCALPHA)
        
        # Draw download/load arrow
        # Circle background
        pg.draw.circle(self.icon, Colors.LOAD, (self.size//2, self.size//2), self.size//2 - 2)
        pg.draw.circle(self.icon, Colors.WHITE, (self.size//2, self.size//2), self.size//2 - 4)
        
        # Arrow pointing down
        arrow_size = self.size // 3
        center_x = self.size // 2
        center_y = self.size // 2
        
        # Arrow head (pointing down)
        points = [
            (center_x, center_y + arrow_size//2),  # Bottom point
            (center_x - arrow_size//2, center_y - arrow_size//4),  # Left
            (center_x + arrow_size//2, center_y - arrow_size//4)   # Right
        ]
        pg.draw.polygon(self.icon, Colors.LOAD, points)
        
        # Arrow stem
        stem_height = arrow_size // 2
        pg.draw.rect(self.icon, Colors.LOAD,
                    (center_x - arrow_size//6, center_y - arrow_size//4 - stem_height,
                     arrow_size//3, stem_height))

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
    FOLDER = "folder"
    KEY = "key"
    LOCK_LOCKED = "lock_locked"
    LOCK_UNLOCKED = "lock_unlocked"
    HOME = "home"
    SAVE = "save"
    LOAD = "load"

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
            Icons.FOLDER: IconFolder,
            Icons.KEY: IconKey,
            Icons.LOCK_LOCKED: IconLockLocked,
            Icons.LOCK_UNLOCKED: IconLockUnlocked,
            Icons.HOME: IconHome,
            Icons.SAVE: IconSave,
            Icons.LOAD: IconLoad,
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

# Quick test function (optional)
if __name__ == "__main__":
    pg.init()
    screen = pg.display.set_mode((800, 600))
    
    # Test rendering all icons
    icons = get_all_icons(32)
    
    x, y = 10, 10
    for name, icon in icons.items():
        screen.blit(icon, (x, y))
        x += 40
        if x > 700:
            x = 10
            y += 40
    
    pg.display.flip()
    
    # Keep window open
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
    pg.quit()