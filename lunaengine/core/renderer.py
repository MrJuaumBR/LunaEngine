"""
Renderer Abstraction Layer - Graphics Backend Interface

LOCATION: lunaengine/core/renderer.py

DESCRIPTION:
Defines the abstract interface for all rendering backends in LunaEngine.
Provides a unified API for 2D graphics operations regardless of the underlying
graphics technology (Pygame, OpenGL, etc.). Ensures consistent rendering
behavior across different platforms and hardware.

KEY FEATURES:
- Abstract base class for renderer implementations
- Standardized drawing primitives (shapes, surfaces, lines)
- Frame lifecycle management (begin/end frame)
- Hardware abstraction for graphics operations
- Particle system rendering with dynamic buffers
- Scissor testing for clipping regions
- Geometry caching for performance optimization
- Post‑processing filter system
"""

from abc import ABC, abstractmethod
from typing import (
    Tuple, Dict, Any, List, Optional, Union, Callable
)
import pygame
import numpy as np

from ..backend.types import Color
from ..backend.opengl import Filter, FilterType, FilterRegionType


class Renderer(ABC):
    """
    Abstract base class for all renderers in LunaEngine.

    All drawing operations are defined here; concrete implementations
    (e.g., OpenGLRenderer, PygameRenderer) must implement these methods.
    """

    # Camera position for coordinate transformations (shared across instances)
    camera_position: pygame.math.Vector2 = pygame.math.Vector2(0, 0)

    # List of callbacks triggered when max_particles changes
    on_max_particles_change: List[Callable[[int], None]] = []

    @property
    @abstractmethod
    def max_particles(self) -> int:
        """
        Get the maximum number of particles supported by the renderer.

        Returns:
            Maximum number of particles that can be rendered simultaneously.
        """
        pass

    @max_particles.setter
    @abstractmethod
    def max_particles(self, value: int) -> None:
        """
        Set the maximum number of particles and trigger any necessary resize.

        Args:
            value: New maximum particle count.
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the renderer and required resources (shaders, buffers, etc.).

        Returns:
            True if initialisation succeeded, False otherwise.
        """
        pass

    @abstractmethod
    def begin_frame(self) -> None:
        """
        Begin a new rendering frame.

        Clears buffers, prepares the render target, and resets internal states.
        """
        pass

    @abstractmethod
    def end_frame(self) -> None:
        """
        End the current rendering frame.

        Applies post‑processing (filters) and swaps buffers (if applicable).
        """
        pass

    @abstractmethod
    def get_surface(self) -> pygame.Surface:
        """
        Get the main rendering surface (the display surface).

        Returns:
            The pygame Surface that is currently being rendered to.
        """
        pass

    @abstractmethod
    def set_surface(self, surface: Optional[pygame.Surface]) -> None:
        """
        Set a custom surface as the render target.

        Args:
            surface: Target surface, or None to reset to the main display.
        """
        pass

    @abstractmethod
    def draw_rect(
        self,
        x: Union[int, float],
        y: Union[int, float],
        width: Union[int, float],
        height: Union[int, float],
        color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'  # forward reference; can be imported if needed
        ],
        fill: bool = True,
        pivot: Tuple[float, float] = (0.0, 0.0),
        border_width: int = 1,
        surface: Optional[pygame.Surface] = None,
        corner_radius: Union[
            int, float,
            Tuple[int, int, int, int],
            Tuple[float, float, float, float]
        ] = 0,
        border_color: Optional[
            Union[
                Tuple[int, int, int, float],
                Tuple[int, int, int],
                Color,
                Tuple[float, float, float, float],
                'ThemeStyle'
            ]
        ] = None
    ) -> None:
        """
        Draw a rectangle (filled or outline) with optional rounded corners.

        Args:
            x, y: Position (before anchor adjustment).
            width, height: Rectangle dimensions.
            color: Fill colour (if fill=True).
            fill: If True, draw filled rectangle; otherwise only the outline.
            pivot: Anchor (fx, fy) relative to width/height.
            border_width: Thickness of the border (used when border_color given or fill=False).
            surface: Optional target surface (defaults to current target).
            corner_radius: Radius for all corners (int/float) or per‑corner (tl, tr, br, bl).
            border_color: Colour of the border (if None and fill=False, uses `color` for outline).
        """
        pass

    @abstractmethod
    def draw_isosceles_triangle(
        self,
        x: Union[int, float],
        y: Union[int, float],
        width: Union[int, float],
        height: Union[int, float],
        color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        fill: bool = True,
        border_width: int = 1,
        border_color: Optional[
            Union[
                Tuple[int, int, int, float],
                Tuple[int, int, int],
                Color,
                Tuple[float, float, float, float],
                'ThemeStyle'
            ]
        ] = None
    ) -> None:
        """
        Draw an isosceles triangle with a horizontal base at the bottom.

        The triangle is defined by a bounding box:
            top vertex at (x + width/2, y)
            bottom-left at (x, y + height)
            bottom-right at (x + width, y + height)

        Args:
            x, y: Top‑left corner of the bounding box.
            width, height: Bounding box dimensions.
            color: Fill colour (if fill=True) or outline colour (if no border_color).
            fill: If True, fills the triangle; otherwise draws only the outline.
            border_width: Thickness of the outline (used when fill=False or border_color given).
            border_color: Colour for the outline; if provided, an outline is drawn
                        on top of the fill (if fill=True) or as the only outline
                        (if fill=False). If None and fill=False, `color` is used.
        """
        pass

    @abstractmethod
    def draw_equilateral_triangle(
        self,
        x: Union[int, float],
        y: Union[int, float],
        width: Union[int, float],
        color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        fill: bool = True,
        border_width: int = 1,
        border_color: Optional[
            Union[
                Tuple[int, int, int, float],
                Tuple[int, int, int],
                Color,
                Tuple[float, float, float, float],
                'ThemeStyle'
            ]
        ] = None
    ) -> None:
        """
        Draw an equilateral triangle with a horizontal base at the bottom.

        The triangle is defined by the side length `width`. The bounding box
        has width = side length and height = side * sqrt(3)/2, with top-left at (x, y).

        Args:
            x, y: Top‑left corner of the bounding box.
            width: Side length of the equilateral triangle.
            color: Fill colour (if fill=True) or outline colour (if no border_color).
            fill: If True, fills the triangle; otherwise draws only the outline.
            border_width: Thickness of the outline (used when fill=False or border_color given).
            border_color: Colour for the outline; if provided, an outline is drawn
                        on top of the fill (if fill=True) or as the only outline
                        (if fill=False). If None and fill=False, `color` is used.
        """
        pass

    @abstractmethod
    def draw_circle(
        self,
        center_x: Union[int, float],
        center_y: Union[int, float],
        radius: Union[int, float],
        color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        fill: bool = True,
        border_width: int = 1,
        surface: Optional[pygame.Surface] = None,
        pivot: Tuple[float, float] = (0.5, 0.5)
    ) -> None:
        """
        Draw a circle (filled or outline).

        Args:
            center_x, center_y: Centre point (before anchor adjustment).
            radius: Circle radius.
            color: Fill or outline colour.
            fill: If True, filled circle; otherwise outline.
            border_width: Outline thickness (only when fill=False).
            surface: Optional target surface.
            pivot: Anchor point for positioning (default centre).
        """
        pass

    @abstractmethod
    def draw_line(
        self,
        start_x: Union[int, float],
        start_y: Union[int, float],
        end_x: Union[int, float],
        end_y: Union[int, float],
        color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        width: int = 2,
        surface: Optional[pygame.Surface] = None
    ) -> None:
        """
        Draw a thick line between two points.

        Args:
            start_x, start_y: Start point.
            end_x, end_y: End point.
            color: Line colour.
            width: Thickness in pixels.
            surface: Optional target surface.
        """
        pass

    @abstractmethod
    def draw_lines(
        self,
        points: List[Tuple[Tuple[int, int], Tuple[int, int]]],
        color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        width: int = 2,
        surface: Optional[pygame.Surface] = None
    ) -> None:
        """
        Draw multiple line segments.

        Args:
            points: List of ((x1, y1), (x2, y2)) pairs.
            color: Line colour.
            width: Thickness in pixels.
            surface: Optional target surface.
        """
        pass

    @abstractmethod
    def draw_polygon(
        self,
        points: List[Tuple[float, float]],
        color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        fill: bool = True,
        border_width: int = 1,
        surface: Optional[pygame.Surface] = None,
        pivot: Tuple[float, float] = (0.0, 0.0)
    ) -> None:
        """
        Draw a convex polygon (filled or outline).

        Args:
            points: List of (x, y) vertices.
            color: Fill or outline colour.
            fill: If True, filled polygon; otherwise outline.
            border_width: Outline thickness (used only when fill=False).
            surface: Optional target surface.
            pivot: Offset applied to all vertices.
        """
        pass

    @abstractmethod
    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        font: pygame.font.Font,
        surface: Optional[pygame.Surface] = None,
        pivot: Tuple[float, float] = (0.0, 0.0),
        flip: Tuple[bool, bool] = (False, False),
        rotate: float = 0.0,
        *args,
        **kwargs
    ) -> None:
        """
        Draw text using a pygame font, with optional flip and rotation.

        Args:
            text: String to render.
            x, y: Position (before anchor).
            color: Any colour format accepted (pygame.Color, tuple, etc.).
            font: Pygame font object.
            surface: Optional target surface.
            pivot: Anchor (fx, fy) relative to text size.
            flip: (flip_horizontal, flip_vertical).
            rotate: Rotation angle in degrees (clockwise).
            *args, **kwargs: Additional arguments (e.g., bold, italic) passed to font rendering.
        """
        pass

    @abstractmethod
    def draw_rich_text(
        self,
        text: str,
        x: int,
        y: int,
        default_color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        font: pygame.font.Font,
        surface: Optional[pygame.Surface] = None,
        pivot: Tuple[float, float] = (0.0, 0.0),
        **kwargs
    ) -> None:
        """
        Draw rich text using the rich text parser.

        Args:
            text: Rich text string with markup
            x, y: Position
            default_color: Default text color (can be Color, ThemeStyle, or tuple)
            font: Base font
            surface: Optional target surface
            pivot: Anchor point
            **kwargs: Additional arguments for draw_text
        """
        pass

    @abstractmethod
    def draw_rich_text_line(
        self,
        line: List['RichTextSegment'],
        x: int,
        y: int,
        default_color: Union[
            Tuple[int, int, int, float],
            Tuple[int, int, int],
            Color,
            Tuple[float, float, float, float],
            'ThemeStyle'
        ],
        font: pygame.font.Font,
        surface: Optional[pygame.Surface] = None
    ) -> None:
        """
        Draw a pre-parsed rich text line.

        Args:
            line: List of RichTextSegment objects
            x, y: Position
            default_color: Default text color (can be Color, ThemeStyle, or tuple)
            font: Base font
            surface: Optional target surface
        """
        pass

    def draw_surface(self, surface: pygame.Surface, x: int, y: int) -> None:
        """
        Alias for blit – draws a surface at (x, y) with default anchor (0,0).
        """
        self.blit(surface, (x, y), pivot=(0.0, 0.0))

    @abstractmethod
    def blit(
        self,
        source: pygame.Surface,
        dest: Union[Tuple[int, int], pygame.Rect],
        area: Optional[pygame.Rect] = None,
        special_flags: int = 0,
        pivot: Tuple[float, float] = (0.0, 0.0)
    ) -> None:
        """
        Blit a source surface onto the current render target.

        Args:
            source: Surface to draw.
            dest: Destination position (x,y) or rectangle.
            area: Sub‑region of the source surface to draw.
            special_flags: Additional blitting flags (implementation dependent).
            pivot: Anchor (fx, fy) relative to the source size.
        """
        pass

    @abstractmethod
    def fill_screen(
        self,
        color: Union[Tuple[int, int, int, float], Tuple[int, int, int]]
    ) -> None:
        """
        Fill the entire screen (or current framebuffer) with a solid colour.

        Args:
            color: RGBA tuple with RGB 0‑255 and alpha 0‑1, or RGB tuple.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the current render target (colour and depth buffers)."""
        pass

    @abstractmethod
    def render_particles(self, particle_data: Dict[str, Any], camera: Any) -> None:
        """
        Render particle systems with batch processing.

        Args:
            particle_data: Dictionary containing particle arrays:
                - 'active_count': int
                - 'positions': np.ndarray (N,2) world positions
                - 'sizes': np.ndarray (N,) sizes
                - 'colors': np.ndarray (N,3) uint8 RGB
                - 'alphas': np.ndarray (N,) uint8 alpha
            camera: Camera object providing world_to_screen and convert_size_zoom.
        """
        pass

    @abstractmethod
    def enable_scissor(
        self,
        x: Union[int, float],
        y: Union[int, float],
        width: Union[int, float],
        height: Union[int, float]
    ) -> None:
        """
        Enable scissor test to restrict drawing to a rectangular region.

        Coordinates follow the pygame system (origin top‑left).

        Args:
            x, y: Top‑left corner.
            width, height: Size of the scissor rectangle.
        """
        pass

    @abstractmethod
    def disable_scissor(self) -> None:
        """Disable the scissor test (no clipping)."""
        pass

    # ------------------------------------------------------------------------
    # Filter System
    # ------------------------------------------------------------------------

    @abstractmethod
    def add_filter(self, filter_obj: Filter) -> None:
        """Add a filter to the active filter stack."""
        pass

    @abstractmethod
    def remove_filter(self, filter_obj: Filter) -> None:
        """Remove a specific filter from the stack."""
        pass

    @abstractmethod
    def clear_filters(self) -> None:
        """Remove all active filters."""
        pass

    @abstractmethod
    def create_quick_filter(
        self,
        filter_type: FilterType,
        intensity: float = 1.0,
        x: float = 0,
        y: float = 0,
        width: Optional[float] = None,
        height: Optional[float] = None,
        radius: float = 50.0,
        feather: float = 10.0
    ) -> Filter:
        """
        Create and add a filter with common sensible defaults.

        Args:
            filter_type: Type of filter effect.
            intensity: Strength (0.0 to 1.0).
            x, y: Position of the region.
            width, height: Dimensions of rectangular region (if None, uses screen size).
            radius: Circle radius (if circular region).
            feather: Edge softness.

        Returns:
            The created Filter object (already added to the stack).
        """
        pass

    @abstractmethod
    def apply_vignette(self, intensity: float = 0.7, feather: float = 100.0) -> Filter:
        """Add a vignette (darkened edges) effect."""
        pass

    @abstractmethod
    def apply_blur(
        self,
        intensity: float = 0.5,
        x: float = 0,
        y: float = 0,
        width: Optional[float] = None,
        height: Optional[float] = None
    ) -> Filter:
        """Add a gaussian‑like blur effect, optionally within a rectangle."""
        pass

    @abstractmethod
    def apply_sepia(self, intensity: float = 1.0) -> Filter:
        """Add a sepia tone (warm brownish) effect."""
        pass

    @abstractmethod
    def apply_grayscale(self, intensity: float = 1.0) -> Filter:
        """Convert colours to grayscale."""
        pass

    @abstractmethod
    def apply_invert(self, intensity: float = 1.0) -> Filter:
        """Invert colours (negative)."""
        pass

    @abstractmethod
    def apply_warm_temperature(self, intensity: float = 0.5) -> Filter:
        """Increase warm colours (orange/red)."""
        pass

    @abstractmethod
    def apply_cold_temperature(self, intensity: float = 0.5) -> Filter:
        """Increase cold colours (blue)."""
        pass

    @abstractmethod
    def apply_night_vision(self, intensity: float = 0.9) -> Filter:
        """Simulate night vision (green tint + noise)."""
        pass

    @abstractmethod
    def apply_crt_effect(self, intensity: float = 0.8) -> Filter:
        """Add CRT monitor scanlines and curvature."""
        pass

    @abstractmethod
    def apply_pixelate(self, intensity: float = 0.7) -> Filter:
        """Pixelate the image (lower resolution)."""
        pass

    @abstractmethod
    def apply_bloom(self, intensity: float = 0.5) -> Filter:
        """Add a bloom (glow) effect around bright areas."""
        pass

    @abstractmethod
    def apply_edge_detect(self, intensity: float = 0.8) -> Filter:
        """Detect and highlight edges."""
        pass

    @abstractmethod
    def apply_emboss(self, intensity: float = 0.7) -> Filter:
        """Apply an emboss (raised edges) effect."""
        pass

    @abstractmethod
    def apply_sharpen(self, intensity: float = 0.5) -> Filter:
        """Sharpen the image."""
        pass

    @abstractmethod
    def apply_posterize(self, intensity: float = 0.6) -> Filter:
        """Reduce the number of colour bands."""
        pass

    @abstractmethod
    def apply_neon(self, intensity: float = 0.7) -> Filter:
        """Add a neon glow effect."""
        pass

    @abstractmethod
    def apply_radial_blur(self, intensity: float = 0.5) -> Filter:
        """Blur outward from the centre."""
        pass

    @abstractmethod
    def apply_fisheye(self, intensity: float = 0.4) -> Filter:
        """Apply a fisheye lens distortion."""
        pass

    @abstractmethod
    def apply_twirl(self, intensity: float = 0.3) -> Filter:
        """Twirl (swirl) the image around its centre."""
        pass

    @abstractmethod
    def apply_circular_grayscale(
        self,
        center_x: float,
        center_y: float,
        radius: float = 100.0,
        intensity: float = 1.0
    ) -> Filter:
        """
        Apply grayscale inside a circular region.

        Args:
            center_x, center_y: Centre of the circle.
            radius: Radius of the circle.
            intensity: Effect strength.
        """
        pass

    @abstractmethod
    def apply_rectangular_blur(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        intensity: float = 0.5
    ) -> Filter:
        """
        Apply blur only inside a rectangular region.

        Args:
            x, y: Top‑left corner of the rectangle.
            width, height: Size of the rectangle.
            intensity: Blur strength.
        """
        pass

    # ------------------------------------------------------------------------
    # Blending and Utilities
    # ------------------------------------------------------------------------

    @abstractmethod
    def set_blend_mode(self, mode: str) -> None:
        """
        Set the blending mode.

        Args:
            mode: One of 'normal', 'add', 'multiply', 'screen'.
        """
        pass

    @abstractmethod
    def set_text_cache_timeout(self, seconds: float) -> None:
        """
        Set how long a text texture stays in cache without being used.

        Args:
            seconds: Timeout in seconds (>= 0.1).
        """
        pass

    @abstractmethod
    def get_cache_usage(
        self,
        target: str = 'all',
        humanize: bool = False
    ) -> Union[float, Dict[str, float]]:
        """
        Return cache usage as size in bytes or as a dictionary of sizes.

        Args:
            target: One of 'text', 'texture', 'circle', 'polygon', 'total', or 'all'.
            humanize: If True, return human‑readable strings (e.g., "1.2 KB").

        Returns:
            Size in bytes (or humanised string) or a dictionary of all caches.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release all rendering resources (shaders, textures, buffers)."""
        pass

    # ------------------------------------------------------------------------
    # Helper methods (already implemented in base)
    # ------------------------------------------------------------------------

    def resize(self, surface: pygame.Surface, width: int, height: int) -> pygame.Surface:
        """
        Resize a surface to exact dimensions.

        Args:
            surface: Source surface.
            width: New width.
            height: New height.

        Returns:
            The resized surface.
        """
        return pygame.transform.scale(surface, (width, height))

    def scale(self, surface: pygame.Surface, width: float, height: float) -> pygame.Surface:
        """
        Scale a surface by a percentage.

        Args:
            surface: Source surface.
            width: Horizontal scale factor (e.g., 2.0 for double).
            height: Vertical scale factor.

        Returns:
            The scaled surface.
        """
        size = surface.get_size()
        return self.resize(surface, int(size[0] * width), int(size[1] * height))