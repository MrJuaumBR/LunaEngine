import pygame
import numpy as np
from typing import List, Tuple, Optional

class SpriteSheet:
    def __init__(self, filename: str, sprite_width: int, sprite_height: int):
        self.sheet = pygame.image.load(filename).convert_alpha()
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.columns = self.sheet.get_width() // sprite_width
        self.rows = self.sheet.get_height() // sprite_height
        self.sprites = []
        
        self._extract_sprites()
        
    def _extract_sprites(self):
        """Extract individual sprites from the spritesheet"""
        for row in range(self.rows):
            for col in range(self.columns):
                rect = pygame.Rect(
                    col * self.sprite_width,
                    row * self.sprite_height,
                    self.sprite_width,
                    self.sprite_height
                )
                sprite = self.sheet.subsurface(rect)
                self.sprites.append(sprite)
                
    def get_sprite(self, index: int) -> Optional[pygame.Surface]:
        """Get sprite by index"""
        if 0 <= index < len(self.sprites):
            return self.sprites[index]
        return None
        
    def get_animation_frames(self, start: int, end: int) -> List[pygame.Surface]:
        """Get a sequence of frames for animation"""
        return self.sprites[start:end+1]
        
    def get_sprite_by_position(self, row: int, col: int) -> Optional[pygame.Surface]:
        """Get sprite by grid position"""
        index = row * self.columns + col
        return self.get_sprite(index)