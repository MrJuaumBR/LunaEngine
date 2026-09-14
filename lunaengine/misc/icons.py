"""
lunaengine/misc/icons.py

Themed Icon System for LunaEngine
- Supports PNG icons with white/transparent masks
- Flat color recoloring via BLEND_RGBA_MULT
- Gradient recoloring via ColorKeys (linear or radial)
- Optional scaling to a uniform size (square)
- Caching per (color, size) combination
- Factory class Icons with access to all built‑in icons
"""

from pathlib import Path
import os
import pygame
import math
from typing import Optional, Tuple, Union, List, Literal, Dict

from ..backend.types import ColorKeys, Color

# Path to the icons folder (assumes lunaengine/assets/icons/)
ICONS_PATH = Path(os.path.abspath(os.path.dirname(__file__))).parent / 'assets' / 'icons'


class Icon:
    """
    A theme‑aware icon that can be recoloured with a flat colour or a gradient.

    The original PNG must be a white shape on a transparent background.
    Scaling is performed once per requested size.
    """

    def __init__(self, icon_filename: str, size: Optional[int] = None):
        """
        Args:
            icon_filename: name of the PNG file inside the icons folder.
            size: if given, the icon will be scaled to a square of this size.
                  If None, the original dimensions are kept.
        """
        self.icon_path = ICONS_PATH / icon_filename
        self.name = str(icon_filename.split('.')[0]).upper()
        if not self.icon_path.exists():
            raise FileNotFoundError(f"Icon file not found: {self.icon_path}")

        # Load the original mask – white pixels on transparent background
        self._original_surface = pygame.image.load(self.icon_path).convert_alpha()
        self._original_size = self._original_surface.get_size()  # (width, height)

        self._size = size

        # Cache: key = (color_key_hash, gradient_type, gradient_angle, size)
        # value = pygame.Surface
        self._cache = {}

    def get_surface(
        self,
        color: Union[Color, Tuple[int, int, int], ColorKeys, None],
        gradient_type: Literal['linear', 'radial'] = 'linear',
        gradient_angle: float = 0.0,
    ) -> pygame.Surface:
        """
        Return a recoloured (and optionally scaled) version of the icon.

        Args:
            color: flat colour (Color or (r,g,b)) or a ColorKeys gradient.
            gradient_type: only used if color is a ColorKeys: 'linear' or 'radial'.
            gradient_angle: only used for linear gradients (degrees).
        """
        # Build a hashable cache key from the colour argument
        if isinstance(color, ColorKeys):
            # Use the sorted key-value pairs as a stable key
            key_data = tuple((k, (v.r, v.g, v.b, v.a)) for k, v in sorted(color.keys.items()))
            cache_key = (key_data, gradient_type, gradient_angle)
        elif isinstance(color, Color):
            # flat colour
            rgb = (color.r, color.g, color.b)
            cache_key = ('flat', rgb)
        elif isinstance(color, tuple):
            rgb = (color[0], color[1], color[2])
            cache_key = ('flat', rgb)
        elif color is None:
            cache_key = ('flat', (255, 255, 255))

        # Include size in the full cache key
        size_key = self._size if self._size is not None else 'original'
        full_key = (cache_key, size_key)

        if full_key in self._cache:
            return self._cache[full_key]

        # Generate the recoloured surface at original size
        if isinstance(color, ColorKeys):
            result = self._apply_gradient(color, gradient_type, gradient_angle)
        else:
            result = self._apply_flat_color(color)

        # Scale if a size is requested
        if self._size is not None:
            result = pygame.transform.smoothscale(result, (self._size, self._size))

        self._cache[full_key] = result
        return result

    def _apply_flat_color(self, color: Union[Color, Tuple[int, int, int], None]) -> pygame.Surface:
        """Recolour with a flat RGB colour using multiply blending."""
        if isinstance(color, Color):
            r, g, b = color.r, color.g, color.b
        elif color is None:
            r, g, b = 255, 255, 255
        else:
            r, g, b = color[0], color[1], color[2]

        # Create a solid colour surface (full alpha to preserve icon alpha)
        color_surf = pygame.Surface(self._original_surface.get_size(), pygame.SRCALPHA)
        color_surf.fill((r, g, b, 255))

        # Multiply: white * colour = colour, transparent areas stay transparent
        result = self._original_surface.copy()
        result.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return result

    def _apply_gradient(
        self,
        color_keys: ColorKeys,
        gradient_type: str = 'linear',
        angle: float = 0.0
    ) -> pygame.Surface:
        """
        Generate a gradient surface and multiply it with the icon mask.
        """
        w, h = self._original_surface.get_size()
        if w <= 0 or h <= 0:
            return self._original_surface.copy()

        # Create a surface for the gradient (alpha will be set to 255 later)
        grad_surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Precompute direction vector for linear gradient
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)

        # Iterate over every pixel (icons are small, so this is fine)
        for y in range(h):
            for x in range(w):
                # Normalised coordinates in [0, 1]
                u = x / max(1, w - 1)
                v = y / max(1, h - 1)

                # Compute the interpolation parameter t
                if gradient_type == 'linear':
                    # Project (u,v) onto the direction vector
                    t = u * dx + v * dy
                    # Map from [-1,1] to [0,1] (handles angles beyond 90°)
                    t = (t + 1.0) / 2.0
                else:  # radial
                    # Distance from centre (0.5, 0.5) scaled to max ~1.0
                    cx, cy = u - 0.5, v - 0.5
                    t = math.hypot(cx, cy) * 1.414  # ~ sqrt(2) to map corner distance to 1
                    t = min(1.0, t)

                t = max(0.0, min(1.0, t))
                col = color_keys.get_color(t)
                if col is None:
                    col = Color(255, 255, 255, 1.0)

                # Set pixel with full alpha (to preserve mask alpha during multiply)
                grad_surf.set_at((x, y), (col.r, col.g, col.b, 255))

        # Multiply gradient over the white mask
        result = self._original_surface.copy()
        result.blit(grad_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return result

    def clear_cache(self) -> None:
        """Clear the internal cache, forcing fresh recolouring on next get_surface()."""
        self._cache.clear()


class Icons:
    """
    Factory class for all built‑in icons.

    Each static method returns an Icon instance for the corresponding PNG.
    The optional `size` parameter sets the desired square size.
    """

    # List of all available icon names (filenames without extension)
    _ALL_ICON_NAMES = [
        'success', 'info', 'warn', 'error',
        'home', 'folder', 'plus', 'cross',
        'search', 'settings', 'save', 'load', 'picture',
        'unlock', 'lock', 'key', 'file', 'wrench', 'hammer', 'shield', 'engine', 'back',
        'steam', 'discord', 'youtube', 'github', 'audio',
        'calendar', 'clock', 'cloud', 'database', 'brain', 'link', 'location',
        'microphone', 'mute', 'unmute', 'python', 'synchronize', 'camera', 'wifi',
        'trash', 'undo', 'redo', 'cube', 'sphere', 'rocket', 'notification', 'dialog',
        'controller', 'hide', 'show', 'ranking', 'icons', 'selection', 'puzzle', 'light', 'id',
        'card', 'target', 'aim', 'click', 'debug', 'timer', 'anvil', 'browser', 'omega', 'pi', 'options',
        'plane', 'documentation', 'fire'
    ]

    @classmethod
    def SUCCESS(cls, size: Optional[int] = None) -> Icon:
        return Icon('success.png', size=size)

    @classmethod
    def INFO(cls, size: Optional[int] = None) -> Icon:
        return Icon('info.png', size=size)

    @classmethod
    def WARN(cls, size: Optional[int] = None) -> Icon:
        return Icon('warn.png', size=size)

    @classmethod
    def ERROR(cls, size: Optional[int] = None) -> Icon:
        return Icon('error.png', size=size)

    @classmethod
    def HOME(cls, size: Optional[int] = None) -> Icon:
        return Icon('home.png', size=size)

    @classmethod
    def HOUSE(cls, size: Optional[int] = None) -> Icon:
        return cls.HOME(size)

    @classmethod
    def FOLDER(cls, size: Optional[int] = None) -> Icon:
        return Icon('folder.png', size=size)

    @classmethod
    def PLUS(cls, size: Optional[int] = None) -> Icon:
        return Icon('plus.png', size=size)

    @classmethod
    def CROSS(cls, size: Optional[int] = None) -> Icon:
        return Icon('cross.png', size=size)

    @classmethod
    def SEARCH(cls, size: Optional[int] = None) -> Icon:
        return Icon('search.png', size=size)

    @classmethod
    def SETTINGS(cls, size: Optional[int] = None) -> Icon:
        return Icon('settings.png', size=size)

    @classmethod
    def SAVE(cls, size: Optional[int] = None) -> Icon:
        return Icon('save.png', size=size)

    @classmethod
    def LOAD(cls, size: Optional[int] = None) -> Icon:
        return Icon('load.png', size=size)

    @classmethod
    def PICTURE(cls, size: Optional[int] = None) -> Icon:
        return Icon('picture.png', size=size)
    
    @classmethod
    def UNLOCK(cls, size: Optional[int] = None) -> Icon:
        return Icon('unlock.png', size=size)
    
    @classmethod
    def LOCK(cls, size: Optional[int] = None) -> Icon:
        return Icon('lock.png', size=size)
            
    @classmethod
    def KEY(cls, size: Optional[int] = None) -> Icon:
        return Icon('key.png', size=size)
            
    @classmethod
    def FILE(cls, size: Optional[int] = None) -> Icon:
        return Icon('file.png', size=size)
            
    @classmethod
    def WRENCH(cls, size: Optional[int] = None) -> Icon:
        return Icon('wrench.png', size=size)
    
    @classmethod
    def HAMMER(cls, size: Optional[int] = None) -> Icon:
        return Icon('hammer.png', size=size)
        
    @classmethod
    def SHIELD(cls, size: Optional[int] = None) -> Icon:
        return Icon('shield.png', size=size)
    
    @classmethod
    def ENGINE(cls, size: Optional[int] = None) -> Icon:
        return Icon('engine.png', size=size)
    
    @classmethod
    def BACK(cls, size: Optional[int] = None) -> Icon:
        return Icon('back.png', size=size)
    
    @classmethod
    def STEAM(cls, size: Optional[int] = None) -> Icon:
        return Icon('steam.png', size=size)
    
    @classmethod
    def DISCORD(cls, size: Optional[int] = None) -> Icon:
        return Icon('discord.png', size=size)
    
    @classmethod
    def YOUTUBE(cls, size: Optional[int] = None) -> Icon:
        return Icon('youtube.png', size=size)
    
    @classmethod
    def GITHUB(cls, size: Optional[int] = None) -> Icon:
        return Icon('github.png', size=size)
    
    @classmethod
    def AUDIO(cls, size: Optional[int] = None) -> Icon:
        return Icon('audio.png', size=size)

    @classmethod
    def CALENDAR(cls, size: Optional[int] = None) -> Icon:
            return Icon('calendar.png', size=size)
    
    @classmethod
    def CLOCK(cls, size: Optional[int] = None) -> Icon:
        return Icon('clock.png', size=size)
        
    @classmethod
    def CLOUD(cls, size: Optional[int] = None) -> Icon:
        return Icon('cloud.png', size=size)
        
    @classmethod
    def DATABASE(cls, size: Optional[int] = None) -> Icon:
        return Icon('database.png', size=size)
        
    @classmethod
    def BRAIN(cls, size: Optional[int] = None) -> Icon:
        return Icon('brain.png', size=size)
        
    @classmethod
    def LINK(cls, size: Optional[int] = None) -> Icon:
        return Icon('link.png', size=size)
        
    @classmethod
    def LOCATION(cls, size: Optional[int] = None) -> Icon:
        return Icon('location.png', size=size)
        
    @classmethod
    def MICROPHONE(cls, size: Optional[int] = None) -> Icon:
        return Icon('microphone.png', size=size)
        
    @classmethod
    def MUTE(cls, size: Optional[int] = None) -> Icon:
        return Icon('mute.png', size=size)
        
    @classmethod
    def UNMUTE(cls, size: Optional[int] = None) -> Icon:
        return Icon('unmute.png', size=size)
    
    @classmethod
    def PYTHON(cls, size: Optional[int] = None) -> Icon:
        return Icon('python.png', size=size)
    
    @classmethod
    def SYNCHRONIZE(cls, size: Optional[int] = None) -> Icon:
        return Icon('synchronize.png', size=size)
    
    @classmethod
    def CAMERA(cls, size: Optional[int] = None) -> Icon:
        return Icon('camera.png', size=size)
    
    @classmethod
    def WIFI(cls, size: Optional[int] = None) -> Icon:
        return Icon('wifi.png', size=size)
    
    @classmethod
    def TRASH(cls, size: Optional[int] = None) -> Icon:
        return Icon('trash.png', size=size)
    
    @classmethod
    def UNDO(cls, size: Optional[int] = None) -> Icon:
        return Icon('undo.png', size=size)
    
    @classmethod
    def REDO(cls, size: Optional[int] = None) -> Icon:
        return Icon('redo.png', size=size)
    
    @classmethod
    def CUBE(cls, size: Optional[int] = None) -> Icon:
        return Icon('cube.png', size=size)
    
    @classmethod
    def SPHERE(cls, size: Optional[int] = None) -> Icon:
        return Icon('sphere.png', size=size)
    
    @classmethod
    def ROCKET(cls, size: Optional[int] = None) -> Icon:
        return Icon('rocket.png', size=size)

    @classmethod
    def NOTIFICATION(cls, size: Optional[int] = None) -> Icon:
        return Icon('notification.png', size=size)
    
    @classmethod
    def DIALOG(cls, size: Optional[int] = None) -> Icon:
        return Icon('dialog.png', size=size)
    
    @classmethod
    def CONTROLLER(cls, size: Optional[int] = None) -> Icon:
        return Icon('controller.png', size=size)
    
    @classmethod
    def HIDE(cls, size: Optional[int] = None) -> Icon:
        return Icon('hide.png', size=size)
    
    @classmethod
    def SHOW(cls, size: Optional[int] = None) -> Icon:
        return Icon('show.png', size=size)
    
    @classmethod
    def RANKING(cls, size: Optional[int] = None) -> Icon:
        return Icon('ranking.png', size=size)
    
    @classmethod
    def ICONS(cls, size: Optional[int] = None) -> Icon:
        return Icon('icons.png', size=size)
    
    @classmethod
    def SELECTION(cls, size: Optional[int] = None) -> Icon:
        return Icon('selection.png', size=size)
    
    @classmethod
    def PUZZLE(cls, size: Optional[int] = None) -> Icon:
        return Icon('puzzle.png', size=size)
    
    @classmethod
    def LIGHT(cls, size: Optional[int] = None) -> Icon:
        return Icon('light.png', size=size)
    
    @classmethod
    def ID(cls, size: Optional[int] = None) -> Icon:
        return Icon('id.png', size=size)
    
    @classmethod
    def CARD(cls, size: Optional[int] = None) -> Icon:
        return Icon('card.png', size=size)
    
    @classmethod
    def TARGET(cls, size: Optional[int] = None) -> Icon:
        return Icon('target.png', size=size)
    
    @classmethod
    def AIM(cls, size: Optional[int] = None) -> Icon:
        return Icon('aim.png', size=size)
    
    @classmethod
    def CLICK(cls, size: Optional[int] = None) -> Icon:
        return Icon('click.png', size=size)
    
    @classmethod
    def DEBUG(cls, size: Optional[int] = None) -> Icon:
        return Icon('debug.png', size=size)

    @classmethod
    def ANVIL(cls, size: Optional[int] = None) -> Icon:
        return Icon('anvil.png', size=size)
    
    @classmethod
    def TIMER(cls, size: Optional[int] = None) -> Icon:
        return Icon('timer.png', size=size)
    
    @classmethod
    def TIMER(cls, size: Optional[int] = None) -> Icon:
        return Icon('timer.png', size=size)
    
    @classmethod
    def PI(cls, size: Optional[int] = None) -> Icon:
        return Icon('pi.png', size=size)
    
    @classmethod
    def OPTIONS(cls, size: Optional[int] = None) -> Icon:
        return Icon('options.png', size=size)
    
    @classmethod
    def PLANE(cls, size: Optional[int] = None) -> Icon:
        return Icon('plane.png', size=size)
    
    @classmethod
    def DOCUMENTATION(cls, size: Optional[int] = None) -> Icon:
        return Icon('documentation.png', size=size)
    
    @classmethod
    def FIRE(cls, size: Optional[int] = None) -> Icon:
        return Icon('fire.png', size=size)
    

    @classmethod
    def get_icon(cls, name: str, size: Optional[int] = None) -> Icon:
        """
        Get an icon by its name (case‑insensitive).

        Example:
            icon = Icons.get_icon('home', size=32)
        """
        upper = name.upper()
        method = getattr(cls, upper, None)
        if method is not None and callable(method):
            return method(size)
        else:
            raise ValueError(f"Icon '{name}' not found. Available: {cls.get_all_names()}")

    @classmethod
    def get_all(cls, size: Optional[int] = None) -> List[Icon]:
        """
        Return a list of Icon instances for all built‑in icons, all at the given size.
        Order is: success, info, warn, error, home, folder, plus, cross,
                  search, settings, save, load, picture.
        """
        return [
            cls.SUCCESS(size),
            cls.INFO(size),
            cls.WARN(size),
            cls.ERROR(size),
            cls.HOME(size),
            cls.FOLDER(size),
            cls.PLUS(size),
            cls.CROSS(size),
            cls.SEARCH(size),
            cls.SETTINGS(size),
            cls.SAVE(size),
            cls.LOAD(size),
            cls.PICTURE(size),
            cls.UNLOCK(size),
            cls.LOCK(size),
            cls.KEY(size),
            cls.FILE(size),
            cls.WRENCH(size),
            cls.HAMMER(size),
            cls.SHIELD(size),
            cls.ENGINE(size),
            cls.BACK(size),
            cls.STEAM(size),
            cls.DISCORD(size),
            cls.YOUTUBE(size),
            cls.GITHUB(size),
            cls.AUDIO(size),
            cls.CALENDAR(size),
            cls.CLOCK(size),
            cls.CLOUD(size),
            cls.DATABASE(size),
            cls.BRAIN(size),
            cls.LINK(size),
            cls.LOCATION(size),
            cls.MICROPHONE(size),
            cls.MUTE(size),
            cls.UNMUTE(size),
            cls.PYTHON(size),
            cls.SYNCHRONIZE(size),
            cls.CAMERA(size),
            cls.WIFI(size),
            cls.TRASH(size),
            cls.REDO(size),
            cls.UNDO(size),
            cls.CUBE(size),
            cls.SPHERE(size),
            cls.ROCKET(size),
            cls.NOTIFICATION(size),
            cls.DIALOG(size),
            cls.CONTROLLER(size),
            cls.HIDE(size),
            cls.SHOW(size),
            cls.RANKING(size),
            cls.ICONS(size),
            cls.SELECTION(size),
            cls.PUZZLE(size),
            cls.LIGHT(size),
            cls.ID(size),
            cls.CARD(size),
            cls.TARGET(size),
            cls.AIM(size),
            cls.CLICK(size),
            cls.DEBUG(size),
            cls.ANVIL(size),
            cls.TIMER(size),
            cls.PI(size),
            cls.OPTIONS(size),
            cls.PLANE(size),
            cls.DOCUMENTATION(size),
            cls.FIRE(size),
        ]
        
    @classmethod
    def get_all_dict(cls, size: Optional[int] = None) -> Dict[str, Icon]:
        d = {}
        for icon in cls.get_all(size):
            d[icon.name] = icon
        return d

    @classmethod
    def get_all_names(cls) -> List[str]:
        """Return the list of available icon names (as strings)."""
        return cls._ALL_ICON_NAMES.copy()


# ----------------------------------------------------------------------
# Self‑test (run with python -m lunaengine.misc.icons)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # Quick demo: create a gradient icon and save it to disk
    try:
        pygame.init()
        display = pygame.display.set_mode((800, 600))
        icon = Icons.get_icon('home', size=64)
        gradient = ColorKeys([
            (255, 0, 0),   # red
            (0, 0, 255)    # blue
        ])
        surf = icon.get_surface(gradient, gradient_type='linear', gradient_angle=45.0)
        pygame.image.save(surf, 'home_gradient.png')
        print("Demo icon saved as 'home_gradient.png'")
    except Exception as e:
        print(f"Demo failed: {e}")