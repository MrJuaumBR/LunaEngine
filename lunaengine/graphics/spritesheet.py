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

import pygame
from typing import List, Tuple, Optional
import time

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
        self.filename = filename
        # Load image with alpha channel support
        self.sheet = pygame.image.load(filename).convert_alpha()
        self.width = self.sheet.get_width()
        self.height = self.sheet.get_height()
    
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
        # Validate rect bounds
        if (rect.x < 0 or rect.y < 0 or 
            rect.x + rect.width > self.width or 
            rect.y + rect.height > self.height):
            raise ValueError(f"Rect {rect} is outside sprite sheet bounds {self.width}x{self.height}")
        
        # Extract the sprite using subsurface (no memory copy)
        return self.sheet.subsurface(rect)
    
    def get_sprites_at_regions(self, regions: List[pygame.Rect]) -> List[pygame.Surface]:
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
    
    def get_sprite_grid(self, cell_size: Tuple[int, int], 
                       grid_pos: Tuple[int, int]) -> pygame.Surface:
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
        
        rect = pygame.Rect(
            col * cell_width,
            row * cell_height,
            cell_width,
            cell_height
        )
        
        return self.get_sprite_at_rect(rect)


class Animation:
    """
    Time-based animation system for sprite sequences.
    
    This class automatically extracts frames from a sprite sheet based on
    the provided parameters and manages animation timing.
    
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
    """
    
    def __init__(self, spritesheet_file: str, size: Tuple[int, int],
                 start_pos: Tuple[int, int] = (0, 0),
                 frame_count: int = 1,
                 padding: Tuple[int, int] = (0, 0),
                 margin: Tuple[int, int] = (0, 0),
                 scale: Tuple[float, float] = (1.0, 1.0),
                 duration: float = 1.0,
                 loop: bool = True):
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
        """
        self.spritesheet = SpriteSheet(spritesheet_file)
        self.size = size
        self.start_pos = start_pos
        self.frame_count = frame_count
        self.padding = padding
        self.margin = margin
        self.scale = scale
        self.duration = duration
        self.loop = loop
        self.playing = True
        
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
    
    def update(self):
        """
        Update the animation based on elapsed time.
        
        This method uses time-based animation rather than frame-based,
        making it frame-rate independent.
        """
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
                self.current_frame_index = (self.current_frame_index + frames_to_advance) % len(self.frames)
            else:
                self.current_frame_index = min(self.current_frame_index + frames_to_advance, len(self.frames) - 1)
                
                # Stop animation if we reached the end and not looping
                if self.current_frame_index >= len(self.frames) - 1:
                    self.playing = False
    
    def get_current_frame(self) -> pygame.Surface:
        """
        Get the current animation frame.
        
        Returns:
            pygame.Surface: The current frame surface
        """
        if not self.frames:
            # Return a blank surface if no frames
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        
        return self.frames[self.current_frame_index]
    
    def reset(self):
        """Reset the animation to the first frame."""
        self.current_frame_index = 0
        self.accumulated_time = 0.0
        self.last_update_time = time.time()
        self.playing = True
    
    def is_finished(self) -> bool:
        """
        Check if a non-looping animation has finished.
        
        Returns:
            bool: True if the animation has finished, False otherwise
        """
        return not self.loop and not self.playing and self.current_frame_index >= len(self.frames) - 1
    
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