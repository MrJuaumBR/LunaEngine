from enum import Enum
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass
import pygame

if TYPE_CHECKING:
    from ..core.scene import Scene
    from .opengl import OpenGLRenderer

class TransitionType(Enum):
    NONE = 0
    FADE = 1
    SLIDE_LEFT = 2
    SLIDE_RIGHT = 3
    SLIDE_UP = 4
    SLIDE_DOWN = 5
    ZOOM_IN = 6
    ZOOM_OUT = 7
    IRIS = 8
    ORBITAL_LEFT = 9
    ORBITAL_RIGHT = 10
    MORPH = 11
    FLASH = 12
    
@dataclass
class Transition:
    from_scene: 'Scene'
    to_scene: 'Scene'
    effect: TransitionType
    duration: float
    progress: float = 0.0
    finished: bool = False

    from_surface: Optional[pygame.Surface] = None
    to_surface: Optional[pygame.Surface] = None

    def __post_init__(self) -> None:
        """Keep transition state safe even when callers provide bad values."""
        self.duration = max(0.0, float(self.duration))

    @property
    def eased_progress(self) -> float:
        """Smooth-step progress for less abrupt movement and fades."""
        p = max(0.0, min(1.0, self.progress))
        return p * p * (3.0 - 2.0 * p)
