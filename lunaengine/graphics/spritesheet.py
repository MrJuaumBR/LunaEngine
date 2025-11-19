"""
Sprite Sheet System with Alpha Support and Time-Based Animations

LOCATION: lunaengine/graphics/spritesheet.py

DESCRIPTION:
Advanced sprite sheet management system with alpha channel support and
time-based animation system. Provides efficient sprite extraction from
texture atlases with flexible positioning and frame-rate independent animations.

KEY FEATURES:
- Full alpha channel support for transparent sprites
- Flexible sprite extraction using Rect coordinates
- Batch sprite extraction for multiple regions
- Time-based animation system (frame-rate independent)
- Support for padding, margin, and scaling
- Animation sequencing with configurable durations
- Automatic frame extraction based on parameters

LIBRARIES USED:
- pygame: Image loading, surface manipulation, and alpha processing
- typing: Type hints for better code documentation
- time: Animation timing calculations

! WARN:
- Ensure pygame is initialized before using this module

USAGE:
>>> # Basic sprite sheet
>>> spritesheet = SpriteSheet("characters.png")
>>> single_sprite = spritesheet.get_sprite_at_rect(pygame.Rect(0, 0, 64, 64))
>>>
>>> # Multiple sprites
>>> regions = [pygame.Rect(0, 0, 64, 64), pygame.Rect(64, 0, 64, 64)]
>>> sprites = spritesheet.get_sprites_at_regions(regions)
>>>
>>> # Animation - automatically extracts frames
>>> walk_animation = Animation("tiki_texture.png", (70, 70), (0, 0), frame_count=6,
>>>                           scale=(2, 2), duration=1.0)
>>> current_frame = walk_animation.get_current_frame()
"""

import pygame, time, os
from typing import List, Tuple, Optional


class SpriteSheet:
    """
    Main sprite sheet class for managing and extracting sprites from texture atlases.

    This class handles loading sprite sheets with alpha support and provides
    multiple methods for extracting individual sprites or sprite sequences.

    Attributes:
        sheet (pygame.Surface): The loaded sprite sheet surface with alpha
        filename (str): Path to the sprite sheet file
        width (int): Width of the sprite sheet
        height (int): Height of the sprite sheet
    """

    def __init__(self, filename: str):
        """
        Initialize the sprite sheet with alpha support.

        Args:
            filename (str): Path to the sprite sheet image file
        """
        self.filename = os.path.abspath(filename)
        if os.path.exists(filename):
            self.sheet = pygame.image.load(filename).convert_alpha()
            self.width = self.sheet.get_width()
            self.height = self.sheet.get_height()
            return

        raise FileNotFoundError(f"Sprite sheet file not found: {filename}")

    def get_sprite_at_rect(self, rect: pygame.Rect) -> pygame.Surface:
        """
        Extract a sprite from a specific rectangular region.

        Args:
            rect (pygame.Rect): Rectangle defining the sprite region (x, y, width, height)

        Returns:
            pygame.Surface: The extracted sprite surface with alpha

        Raises:
            ValueError: If the rect is outside the sprite sheet bounds
        """
        # Accepts tuples on rect
        if isinstance(rect, tuple) and len(rect) == 4:
            rect = pygame.Rect(*rect)
        
        # Validate rect bounds
        if (
            rect.x < 0
            or rect.y < 0
            or rect.x + rect.width > self.width
            or rect.y + rect.height > self.height
        ):
            raise ValueError(
                f"Rect {rect} is outside sprite sheet bounds {self.width}x{self.height}"
            )

        # Extract the sprite using subsurface (no memory copy)
        return self.sheet.subsurface(rect)

    def get_sprites_at_regions(
        self, regions: List[pygame.Rect]
    ) -> List[pygame.Surface]:
        """
        Extract multiple sprites from a list of rectangular regions.

        Args:
            regions (List[pygame.Rect]): List of rectangles defining sprite regions

        Returns:
            List[pygame.Surface]: List of extracted sprite surfaces
        """
        sprites = []
        for rect in regions:
            try:
                sprite = self.get_sprite_at_rect(rect)
                sprites.append(sprite)
            except ValueError as e:
                print(f"Warning: Skipping invalid region {rect}: {e}")

        return sprites

    def get_sprite_grid(
        self, cell_size: Tuple[int, int], grid_pos: Tuple[int, int]
    ) -> pygame.Surface:
        """
        Extract a sprite from a grid-based sprite sheet.

        Args:
            cell_size (Tuple[int, int]): Width and height of each grid cell
            grid_pos (Tuple[int, int]): Grid coordinates (col, row)

        Returns:
            pygame.Surface: The extracted sprite surface
        """
        cell_width, cell_height = cell_size
        col, row = grid_pos

        rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)

        return self.get_sprite_at_rect(rect)

    def get_surface_drawn_area(
        self, surface: pygame.Surface, threshold: int = 1
    ) -> pygame.Rect:
        """
        Get the bounding rectangle of the non-transparent (drawn) area of a surface.

        This function analyzes the alpha channel of the surface to find the smallest
        rectangle that contains all non-transparent pixels, creating a tight hitbox.

        Args:
            surface (pygame.Surface): Surface to analyze (must have alpha channel)
            threshold (int): Alpha threshold value (0-255). Pixels with alpha >= threshold
                            are considered drawn. Default is 1 (any non-fully-transparent).

        Returns:
            pygame.Rect: Tight bounding rectangle around the non-transparent area.
                        Returns empty Rect (0,0,0,0) if surface is fully transparent.

        Raises:
            ValueError: If surface doesn't have per-pixel alpha
        """
        if (
            not surface.get_flags() & pygame.SRCALPHA
        ):  # Verify surface has alpha channel
            raise ValueError(
                "Surface must have per-pixel alpha for drawn area detection"
            )

        width, height = surface.get_size()
        if width == 0 or height == 0:
            return pygame.Rect(0, 0, 0, 0)
        # Lock surface for pixel access
        surface.lock()
        try:
            # Initialize bounds to extreme values
            left, top = width, height
            right, bottom = -1, -1
            # Iterate through all pixels to find non-transparent bounds
            for y in range(height):
                for x in range(width):
                    # Get alpha value at current pixel
                    alpha = surface.get_at((x, y))[3]  # Index 3 is alpha channel
                    # Check if pixel is non-transparent (above threshold)
                    if alpha >= threshold:  # Update bounds
                        if x < left:
                            left = x
                        if x > right:
                            right = x
                        if y < top:
                            top = y
                        if y > bottom:
                            bottom = y
            # Check if any non-transparent pixels were found
            if left <= right and top <= bottom:
                return pygame.Rect(left, top, right - left + 1, bottom - top + 1)
            else:
                return pygame.Rect(0, 0, 0, 0)  # Fully transparent surface
        finally:
            # Always unlock the surface
            surface.unlock()


class Animation:
    """
    Time-based animation system for sprite sequences with fade effects.

    This class automatically extracts frames from a sprite sheet based on
    the provided parameters and manages animation timing with alpha transitions.

    Attributes:
        spritesheet (SpriteSheet): The source sprite sheet
        frames (List[pygame.Surface]): List of animation frames
        frame_count (int): Total number of frames in the animation
        current_frame_index (int): Current frame index in the animation
        duration (float): Total animation duration in seconds
        frame_duration (float): Duration of each frame in seconds
        last_update_time (float): Last time the animation was updated
        scale (Tuple[float, float]): Scale factors for the animation
        loop (bool): Whether the animation should loop
        playing (bool): Whether the animation is currently playing
        fade_in_duration (float): Duration of fade-in effect in seconds
        fade_out_duration (float): Duration of fade-out effect in seconds
        fade_alpha (int): Current alpha value for fade effects (0-255)
        fade_mode (str): Current fade mode: 'in', 'out', or None
        flip (Tuple[bool, bool]): Flip flags for horizontal and vertical flipping
    """

    def __init__(
        self,
        spritesheet_file: str,
        size: Tuple[int, int],
        start_pos: Tuple[int, int] = (0, 0),
        frame_count: int = 1,
        padding: Tuple[int, int] = (0, 0),
        margin: Tuple[int, int] = (0, 0),
        scale: Tuple[float, float] = (1.0, 1.0),
        duration: float = 1.0,
        loop: bool = True,
        fade_in_duration: float = 0.0,
        fade_out_duration: float = 0.0,
        flip: tuple = (False, False),
    ):
        """
        Initialize the animation and automatically extract frames from sprite sheet.

        Args:
            spritesheet_file (str): Path to the sprite sheet file
            size (Tuple[int, int]): Size of each sprite (width, height)
            start_pos (Tuple[int, int]): Starting position in the sprite sheet (x, y)
            frame_count (int): Number of frames to extract for the animation
            padding (Tuple[int, int]): Padding between sprites (x, y)
            margin (Tuple[int, int]): Margin around the sprite sheet (x, y)
            scale (Tuple[float, float]): Scale factors for the animation
            duration (float): Total animation duration in seconds
            loop (bool): Whether the animation should loop
            fade_in_duration (float): Duration of fade-in effect in seconds
            fade_out_duration (float): Duration of fade-out effect in seconds
            flip (Tuple[bool, bool]): Flip the animation horizontally and vertically
        """
        if type(spritesheet_file) == str:
            self.spritesheet = SpriteSheet(spritesheet_file)
        elif type(spritesheet_file) == SpriteSheet:
            self.spritesheet = spritesheet_file
        self.size = size
        self.start_pos = start_pos
        self.frame_count = frame_count
        self.padding = padding
        self.margin = margin
        self.scale = scale
        self.duration = duration
        self.loop = loop
        self.playing = True
        self.flip = flip

        # Fade effect properties
        self.fade_in_duration = fade_in_duration
        self.fade_out_duration = fade_out_duration
        self.fade_alpha = 0 if fade_in_duration > 0 else 255
        self.fade_mode = "in" if fade_in_duration > 0 else None
        self.fade_start_time = time.time() if fade_in_duration > 0 else None
        self.fade_progress = 0.0

        # Extract frames automatically based on parameters
        self.frames = self._extract_animation_frames()

        # Animation timing
        self.frame_duration = duration / len(self.frames) if self.frames else 0
        self.current_frame_index = 0
        self.last_update_time = time.time()
        self.accumulated_time = 0.0

        # Apply scaling to frames if needed
        if scale != (1.0, 1.0):
            self._apply_scaling()

    def _extract_animation_frames(self) -> List[pygame.Surface]:
        """
        Automatically extract animation frames based on parameters.

        Creates a sequence of rectangles and extracts the corresponding sprites
        from the sprite sheet.

        Returns:
            List[pygame.Surface]: List of extracted frames
        """
        frames = []
        sprite_width, sprite_height = self.size
        start_x, start_y = self.start_pos
        pad_x, pad_y = self.padding
        margin_x, margin_y = self.margin
        current_x = start_x + margin_x
        current_y = start_y + margin_y
        for i in range(self.frame_count):
            # Create rect for current frame
            rect = pygame.Rect(current_x, current_y, sprite_width, sprite_height)
            try:
                frame = self.spritesheet.get_sprite_at_rect(rect)
                if self.flip[0]:
                    frame = pygame.transform.flip(frame, True, False)
                if self.flip[1]:
                    frame = pygame.transform.flip(frame, False, True)
                frames.append(frame)
            except ValueError as e:
                print(f"Warning: Could not extract frame {i} at {rect}: {e}")
                break

            # Move to next frame position (horizontal layout)
            current_x += sprite_width + pad_x
            # Check if we need to move to next row (if frame goes beyond sheet width)
            if current_x + sprite_width > self.spritesheet.width:
                current_x = margin_x
                current_y += sprite_height + pad_y

        print(f"Animation: Extracted {len(frames)}/{self.frame_count} frames from {self.spritesheet.filename}")

        return frames
    
    def _apply_scaling(self):
        """Apply scaling to all animation frames."""
        if self.scale == (1.0, 1.0):
            return
            
        scaled_frames = []
        scale_x, scale_y = self.scale
        
        for frame in self.frames:
            new_width = int(frame.get_width() * scale_x)
            new_height = int(frame.get_height() * scale_y)
            scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
            scaled_frames.append(scaled_frame)
        
        self.frames = scaled_frames

    def set_duration(self, new_duration: float):
        """
        Change the animation duration.
        
        Args:
            new_duration (float): New total duration in seconds
        """
        self.duration = new_duration
        self.frame_duration = new_duration / len(self.frames) if self.frames else 0
    
    def play(self):
        """Start or resume the animation."""
        self.playing = True
        self.last_update_time = time.time()
    
    def pause(self):
        """Pause the animation."""
        self.playing = False

    

    def get_frame_count(self) -> int:
        """
        Get the number of frames in the animation.
        
        Returns:
            int: Number of frames
        """
        return len(self.frames)

    

    def get_progress(self) -> float:
        """
        Get the current progress of the animation (0.0 to 1.0).
        
        Returns:
            float: Animation progress from start (0.0) to end (1.0)
        """
        if len(self.frames) <= 1:
            return 0.0
        return self.current_frame_index / (len(self.frames) - 1)

    def _apply_fade_effect(self, surface: pygame.Surface) -> pygame.Surface:
        """
        Apply current fade alpha to a surface.

        Args:
            surface (pygame.Surface): Original surface

        Returns:
            pygame.Surface: Surface with fade effect applied
        """
        if self.fade_alpha == 255:  # No fade needed
            return surface

        # Create a copy to avoid modifying original frames
        faded_surface = surface.copy()

        # Create a temporary surface for alpha operations
        temp_surface = pygame.Surface(faded_surface.get_size(), pygame.SRCALPHA)
        temp_surface.fill((255, 255, 255, self.fade_alpha))

        # Apply alpha using blend operation
        faded_surface.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return faded_surface

    def update_fade(self):
        """
        Update fade-in and fade-out effects based on elapsed time.
        """
        current_time = time.time()

        if self.fade_mode == "in":
            if self.fade_start_time is None:
                self.fade_start_time = current_time
                return

            elapsed = current_time - self.fade_start_time
            self.fade_progress = min(elapsed / self.fade_in_duration, 1.0)

            # Calculate alpha from progress (0 to 255)
            self.fade_alpha = int(self.fade_progress * 255)

            # Check if fade-in is complete
            if self.fade_progress >= 1.0:
                self.fade_alpha = 255
                self.fade_mode = None
                self.fade_start_time = None

        elif self.fade_mode == "out":
            if self.fade_start_time is None:
                self.fade_start_time = current_time
                return

            elapsed = current_time - self.fade_start_time
            self.fade_progress = min(elapsed / self.fade_out_duration, 1.0)

            # Calculate alpha from progress (255 to 0)
            self.fade_alpha = int((1.0 - self.fade_progress) * 255)

            # Check if fade-out is complete
            if self.fade_progress >= 1.0:
                self.fade_alpha = 0
                self.fade_mode = None
                self.fade_start_time = None
                self.playing = False

    def update(self):
        """
        Update the animation based on elapsed time including fade effects.

        This method uses time-based animation rather than frame-based,
        making it frame-rate independent.
        """
        # Update fade effects first
        if self.fade_mode:
            self.update_fade()

        if not self.playing or len(self.frames) <= 1:
            return

        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        # Accumulate time and advance frames
        self.accumulated_time += delta_time

        # Calculate how many frames to advance
        frames_to_advance = int(self.accumulated_time / self.frame_duration)

        if frames_to_advance > 0:
            self.accumulated_time -= frames_to_advance * self.frame_duration

            if self.loop:
                self.current_frame_index = (
                    self.current_frame_index + frames_to_advance
                ) % len(self.frames)
            else:
                self.current_frame_index = min(
                    self.current_frame_index + frames_to_advance, len(self.frames) - 1
                )

                # Start fade-out if we reached the end and fade-out is configured
                if (
                    self.current_frame_index >= len(self.frames) - 1
                    and self.fade_out_duration > 0
                    and self.fade_mode is None
                ):
                    self.start_fade_out()

                # Stop animation if we reached the end and not looping
                if (
                    self.current_frame_index >= len(self.frames) - 1
                    and not self.loop
                    and self.fade_out_duration == 0
                ):
                    self.playing = False

    def get_current_frame(self) -> pygame.Surface:
        """
        Get the current animation frame with fade effects applied.

        Returns:
            pygame.Surface: The current frame surface with fade alpha
        """
        if not self.frames:
            # Return a blank surface if no frames
            blank = pygame.Surface((1, 1), pygame.SRCALPHA)
            blank.fill((0, 0, 0, 0))
            return blank

        frame = self.frames[self.current_frame_index]

        # Apply fade effect if needed
        if self.fade_mode or self.fade_alpha != 255:
            return self._apply_fade_effect(frame)

        return frame

    def start_fade_in(self, duration: Optional[float] = None):
        """
        Start a fade-in effect.

        Args:
            duration (float, optional): Override fade-in duration. If None, uses initialized value.
        """
        if duration is not None:
            self.fade_in_duration = duration

        if self.fade_in_duration > 0:
            self.fade_mode = "in"
            self.fade_alpha = 0
            self.fade_start_time = time.time()
            self.fade_progress = 0.0
            self.playing = True

    def start_fade_out(self, duration: Optional[float] = None):
        """
        Start a fade-out effect.

        Args:
            duration (float, optional): Override fade-out duration. If None, uses initialized value.
        """
        if duration is not None:
            self.fade_out_duration = duration

        if self.fade_out_duration > 0:
            self.fade_mode = "out"
            self.fade_alpha = 255
            self.fade_start_time = time.time()
            self.fade_progress = 0.0

    def set_fade_alpha(self, alpha: int):
        """
        Manually set the fade alpha value.

        Args:
            alpha (int): Alpha value from 0 (transparent) to 255 (opaque)
        """
        self.fade_alpha = max(0, min(255, alpha))
        self.fade_mode = None  # Disable automatic fade when manually setting

    def is_fade_complete(self) -> bool:
        """
        Check if the current fade effect is complete.

        Returns:
            bool: True if no fade effect is active or fade is complete
        """
        return self.fade_mode is None

    def reset(self):
        """Reset the animation to the first frame and reset fade effects."""
        self.current_frame_index = 0
        self.accumulated_time = 0.0
        self.last_update_time = time.time()
        self.playing = True

        # Reset fade effects based on initialization
        if self.fade_in_duration > 0:
            self.fade_mode = "in"
            self.fade_alpha = 0
        else:
            self.fade_mode = None
            self.fade_alpha = 255

        self.fade_start_time = time.time() if self.fade_mode else None
        self.fade_progress = 0.0
