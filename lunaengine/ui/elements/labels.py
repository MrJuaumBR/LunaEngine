# labels.py
import pygame
import os
import re
from typing import Optional, Tuple, Dict, Any, Union, List
from ...backend.opengl import FilterType, OpenGLRenderer
from .base import UIElement, FontManager, Color, ColorKeys
from ..themes import ThemeManager, ThemeType, ThemeStyle, UiShadow
from pathlib import Path
from ...storage.atlas import AtlasItem
from OpenGL import GL as gl

# ============================================================================
# Rich Text Parser
# ============================================================================

class RichTextSegment:
    """
    Represents a segment of rich text with its formatting.
    
    Attributes:
        text (str): The text content.
        color (Optional[Union[Tuple[int, int, int], Color, ThemeStyle]]): 
            Text color (RGB tuple, Color object, or ThemeStyle). 
            If None, uses default color.
        bold (bool): Whether text is bold.
        italic (bool): Whether text is italic.
        underline (bool): Whether text is underlined.
    """
    def __init__(self, text: str, 
                 color: Optional[Union[Tuple[int, int, int], Color, ThemeStyle]] = None,
                 bold: bool = False, italic: bool = False, underline: bool = False):
        self.text = text
        self.color = color
        self.bold = bold
        self.italic = italic
        self.underline = underline
    
    def __repr__(self):
        return f"RichTextSegment('{self.text}', color={self.color}, bold={self.bold})"


def parse_rich_text(text: str) -> List[RichTextSegment]:
    """
    Parse rich text markup into a list of segments.
    
    Supported tags:
        <b>bold</b> - Bold text
        <i>italic</i> - Italic text
        <u>underline</u> - Underlined text
        <red>text</red> - Colored text (predefined colors)
        <#FF0000>text</#FF0000> - Hex color text
        <br> or \n - Line break (handled by renderer)
    
    Args:
        text: The rich text string to parse
        
    Returns:
        List of RichTextSegment objects
    """
    if not text:
        return [RichTextSegment("")]
    
    # Define color mappings
    COLOR_MAP = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'gray': (128, 128, 128),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'pink': (255, 192, 203),
    }
    
    segments = []
    current_text = ""
    current_color = None
    current_bold = False
    current_italic = False
    current_underline = False
    
    class FormatState:
        def __init__(self):
            self.bold = False
            self.italic = False
            self.underline = False
            self.color = None  # will hold tuple or None
    
    stack = [FormatState()]  # Base state
    
    def flush_text():
        nonlocal current_text
        if current_text:
            state = stack[-1]
            segments.append(RichTextSegment(
                current_text,
                color=state.color,
                bold=state.bold,
                italic=state.italic,
                underline=state.underline
            ))
            current_text = ""
    
    # Normalize line breaks
    text = text.replace('\\n', '\n')
    
    # Split by tags while keeping delimiters
    pattern = r'(<[biu]>|</[biu]>|<(?:[a-zA-Z]+|#[0-9A-Fa-f]{6})>|</(?:[a-zA-Z]+|#[0-9A-Fa-f]{6})>|<br>|\n)'
    parts = re.split(pattern, text)
    
    for part in parts:
        if not part:
            continue
        
        # Line break
        if part == '<br>' or part == '\n':
            flush_text()
            segments.append(RichTextSegment("\n"))
            continue
        
        # Opening tags
        if part == '<b>':
            flush_text()
            new_state = FormatState()
            new_state.bold = True
            new_state.italic = stack[-1].italic
            new_state.underline = stack[-1].underline
            new_state.color = stack[-1].color
            stack.append(new_state)
            continue
        elif part == '<i>':
            flush_text()
            new_state = FormatState()
            new_state.bold = stack[-1].bold
            new_state.italic = True
            new_state.underline = stack[-1].underline
            new_state.color = stack[-1].color
            stack.append(new_state)
            continue
        elif part == '<u>':
            flush_text()
            new_state = FormatState()
            new_state.bold = stack[-1].bold
            new_state.italic = stack[-1].italic
            new_state.underline = True
            new_state.color = stack[-1].color
            stack.append(new_state)
            continue
        
        # Closing tags
        if part == '</b>' or part == '</i>' or part == '</u>':
            flush_text()
            if len(stack) > 1:
                stack.pop()
            continue
        
        # Color tags: <red> or <#FF0000>
        color_match = re.match(r'<([a-zA-Z]+|#[0-9A-Fa-f]{6})>', part)
        if color_match:
            flush_text()
            color_name = color_match.group(1)
            if color_name.startswith('#'):
                try:
                    hex_str = color_name.lstrip('#')
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    new_state = FormatState()
                    new_state.bold = stack[-1].bold
                    new_state.italic = stack[-1].italic
                    new_state.underline = stack[-1].underline
                    new_state.color = (r, g, b)
                    stack.append(new_state)
                except ValueError:
                    # Invalid hex, copy current state
                    new_state = FormatState()
                    new_state.bold = stack[-1].bold
                    new_state.italic = stack[-1].italic
                    new_state.underline = stack[-1].underline
                    new_state.color = stack[-1].color
                    stack.append(new_state)
            else:
                color = COLOR_MAP.get(color_name.lower())
                if color is not None:
                    new_state = FormatState()
                    new_state.bold = stack[-1].bold
                    new_state.italic = stack[-1].italic
                    new_state.underline = stack[-1].underline
                    new_state.color = color
                    stack.append(new_state)
                else:
                    # Unknown color, copy current state
                    new_state = FormatState()
                    new_state.bold = stack[-1].bold
                    new_state.italic = stack[-1].italic
                    new_state.underline = stack[-1].underline
                    new_state.color = stack[-1].color
                    stack.append(new_state)
            continue
        
        # Closing color tags
        color_close_match = re.match(r'</([a-zA-Z]+|#[0-9A-Fa-f]{6})>', part)
        if color_close_match:
            flush_text()
            if len(stack) > 1:
                stack.pop()
            continue
        
        # Regular text
        current_text += part
    
    # Flush any remaining text
    flush_text()
    
    # Collapse any leftover states
    while len(stack) > 1:
        stack.pop()
    
    return segments


def _extract_rgb_from_color(color: Union[Tuple[int, int, int], Color, ThemeStyle, None]) -> Tuple[int, int, int]:
    """
    Extract RGB tuple from a color object (Tuple, Color, ThemeStyle, or None).
    If None, returns (255, 255, 255) as fallback.
    """
    if color is None:
        return (255, 255, 255)
    if isinstance(color, tuple):
        if len(color) >= 3:
            return (color[0], color[1], color[2])
        else:
            return (255, 255, 255)
    elif isinstance(color, Color):
        return (color.r, color.g, color.b)
    elif isinstance(color, ThemeStyle):
        return color.color  # ThemeStyle.color is a tuple (r,g,b)
    else:
        return (255, 255, 255)


def _get_segment_font(seg: RichTextSegment, base_font: pygame.font.Font) -> pygame.font.Font:
    """
    Return a font for the segment with bold/italic applied if needed.
    Uses FontManager to get the styled font.
    """
    if seg.bold or seg.italic:
        # We need the font name and size from the base font.
        # For system fonts, we can get the name via SysFont, but for file fonts,
        # we may not know the family. We'll try to extract the name or file path.
        # FontManager.get_font can accept a font name or file path.
        # We'll try to get the name from the base font's `name` attribute (if it's a SysFont)
        # or we'll use the path if it's a file font.
        font_name = None
        if hasattr(base_font, 'name'):
            # This might be the font name if it's a SysFont (but not guaranteed)
            font_name = base_font.name
        # If base_font is a file font, we might not have the name.
        # We'll just use None (default system font) and rely on bold/italic.
        # Alternatively, we could store the original font_name used to create it
        # but we don't have that info.
        # So we'll use FontManager.get_font with the same size and style.
        # We'll pass the font_name if we have it, else None.
        font = FontManager.get_font(font_name, base_font.get_height(), seg.bold, seg.italic)
        return font
    else:
        return base_font


def render_rich_text(text: str, renderer, x: int, y: int, 
                     default_color: Union[Color, Tuple[int, int, int], ThemeStyle],
                     font: pygame.font.Font,
                     pivot: Tuple[float, float] = (0.0, 0.0),
                     **kwargs) -> None:
    """
    Render rich text using the provided renderer.
    """
    if not text:
        return
    
    segments = parse_rich_text(text)
    if not segments:
        return
    
    # Calculate total size for anchor positioning
    total_width = 0
    max_height = 0
    
    for seg in segments:
        if seg.text == "\n":
            continue
        seg_font = _get_segment_font(seg, font)
        if seg.text != "\n":
            surf = seg_font.render(seg.text, True, (255, 255, 255))
            total_width += surf.get_width()
            max_height = max(max_height, surf.get_height())
    
    # Adjust position by anchor
    actual_x = x - int(pivot[0] * total_width)
    actual_y = y - int(pivot[1] * max_height)
    
    # Render each segment
    current_x = actual_x
    line_y = actual_y
    
    for seg in segments:
        if seg.text == "\n":
            current_x = actual_x
            line_y += max_height + 4
            continue
        
        color_tuple = _extract_rgb_from_color(seg.color) if seg.color is not None else _extract_rgb_from_color(default_color)
        seg_font = _get_segment_font(seg, font)
        
        # Render the text
        renderer.draw_text(seg.text, current_x, line_y, color_tuple, seg_font, pivot=(0, 0), **kwargs)
        
        # If underlined, draw a line under the text
        if seg.underline:
            surf = seg_font.render(seg.text, True, (255, 255, 255))
            text_width = surf.get_width()
            text_height = surf.get_height()
            # Draw a line 2px below the baseline
            line_y_pos = line_y + text_height + 1
            renderer.draw_line(current_x, line_y_pos, current_x + text_width, line_y_pos, color_tuple, 2)
        
        # Advance x
        surf = seg_font.render(seg.text, True, (255, 255, 255))
        current_x += surf.get_width()


def render_rich_text_line(line: List[RichTextSegment], renderer, x: int, y: int,
                          default_color: Union[Color, Tuple[int, int, int], ThemeStyle],
                          font: pygame.font.Font) -> None:
    """
    Render a pre-parsed rich text line (for LongTextLabel).
    """
    if not line:
        return
    
    current_x = x
    for seg in line:
        if seg.text == "\n":
            continue
        
        color_tuple = _extract_rgb_from_color(seg.color) if seg.color is not None else _extract_rgb_from_color(default_color)
        seg_font = _get_segment_font(seg, font)
        
        renderer.draw_text(seg.text, current_x, y, color_tuple, seg_font, pivot=(0, 0))
        
        if seg.underline:
            surf = seg_font.render(seg.text, True, (255, 255, 255))
            text_width = surf.get_width()
            text_height = surf.get_height()
            line_y = y + text_height + 1
            renderer.draw_line(current_x, line_y, current_x + text_width, line_y, color_tuple, 2)
        
        surf = seg_font.render(seg.text, True, (255, 255, 255))
        current_x += surf.get_width()


# ============================================================================
# TextLabel
# ============================================================================

class TextLabel(UIElement):
    """
    A text label with optional rich text support and shadow.
    """
    
    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'text': {'name': 'text', 'key': 'text', 'type': str, 'editable': True,
                 'description': 'The text content of the label.'},
        'color': {'name': 'color', 'key': 'custom_color', 'type': Tuple[int, int, int], 'editable': True,
                  'description': 'Custom text color (RGB). Overrides theme color.'},
        'font_size': {'name': 'font size', 'key': 'font_size', 'type': int, 'editable': True,
                      'description': 'Size of the font in pixels.'},
        'font_name': {'name': 'font name', 'key': 'font_name', 'type': Optional[str], 'editable': True,
                      'description': 'Path to font file or None for default font.'},
        'rich_text': {'name': 'rich text', 'key': 'rich_text', 'type': bool, 'editable': True,
                      'description': 'Use rich text formatting.'},
        'use_theme_color': {'name': 'use theme color', 'key': 'use_theme_color', 'type': bool, 'editable': True,
                            'description': 'Use theme color instead of custom color.'},
    }

    def __init__(
        self,
        x: Union[int, float],
        y: Union[int, float],
        text: str,
        font_size: int|float = 24,
        color: Optional[Union[Tuple[int, int, int], Color, ThemeStyle]] = None,
        font_name: Optional[str] = None,
        rich_text: bool = False,
        use_theme_color: bool = True,
        shadow: Optional[UiShadow] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None,
        **kwargs
    ) -> None:
        FontManager.initialize()
        self._font = FontManager.get_font(font_name, int(font_size))
        self.rich_text = rich_text
        self.use_theme_color = use_theme_color
        self.shadow = shadow or ThemeManager.get_shadow('text_primary')

        # Calculate size based on text
        if rich_text:
            segments = parse_rich_text(text)
            total_width = 0
            max_height = 0
            for seg in segments:
                if seg.text == "\n":
                    continue
                # Use base font for measurement (we don't need bold/italic for measurement)
                surf = self._font.render(seg.text, True, (255, 255, 255))
                total_width += surf.get_width()
                max_height = max(max_height, surf.get_height())
            width, height = total_width, max_height
        else:
            text_surface = self._font.render(text, True, (255, 255, 255))
            width, height = text_surface.get_width(), text_surface.get_height()
        
        super().__init__(x, y, width, height, pivot, element_id)

        self.text = text
        self.font_size = int(font_size)
        self.custom_color: Optional[Color] = None
        if color is not None:
            self.set_text_color(color)
        self.font_name = font_name

        self.theme_type = theme or ThemeManager.get_current_theme()

    @property
    def can_focus(self) -> bool:
        return False

    def _get_init_args(self) -> Dict[str, Any]:
        args = {
            'x': self.x,
            'y': self.y,
            'text': self.text,
            'font_size': self.font_size,
            'font_name': self.font_name,
            'rich_text': self.rich_text,
            'use_theme_color': self.use_theme_color,
            'shadow': self.shadow,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }
        if self.custom_color:
            args['color'] = self.custom_color.to_tuple() if isinstance(self.custom_color, Color) else self.custom_color
        return args

    def set_shadow(self, shadow: Optional[UiShadow]) -> None:
        """Set or remove text shadow."""
        self.shadow = shadow

    def get_text(self) -> str:
        return self.text

    def update_theme(self, theme_type: ThemeType) -> None:
        super().update_theme(theme_type)

    def set_text_color(self, color: Union[Tuple[int, int, int], Color, ThemeStyle]) -> None:
        if isinstance(color, Color):
            self.custom_color = color
        elif isinstance(color, ThemeStyle):
            self.custom_color = Color(*color.color)
        else:
            self.custom_color = Color(*color)

    def set_color(self, color: Union[Tuple[int, int, int], Color]) -> None:
        self.set_text_color(color)

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def set_text(self, text: str) -> None:
        self.text = text
        if self.rich_text:
            segments = parse_rich_text(text)
            total_width = 0
            max_height = 0
            for seg in segments:
                if seg.text == "\n":
                    continue
                surf = self.font.render(seg.text, True, (255, 255, 255))
                total_width += surf.get_width()
                max_height = max(max_height, surf.get_height())
            self.width = total_width
            self.height = max_height
        else:
            text_surface = self.font.render(text, True, (255, 255, 255))
            self.width = text_surface.get_width()
            self.height = text_surface.get_height()

    def set_theme(self, theme_type: ThemeType) -> None:
        self.theme_type = theme_type

    def _get_text_color(self) -> Union[Color, ThemeStyle, Tuple[int, int, int]]:
        if self.use_theme_color:
            theme = ThemeManager.get_theme(self.theme_type)
            return theme.label_text
        elif self.custom_color:
            return self.custom_color
        theme = ThemeManager.get_theme(self.theme_type)
        return theme.label_text

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        style = {}
        if self.shadow:
            style['shadow'] = self.shadow

        if self.rich_text:
            # Rich text does not support shadow yet (skip it)
            default_color = self._get_text_color()
            render_rich_text(
                self.text,
                renderer,
                actual_x, actual_y,
                default_color,
                self.font,
                pivot=(0, 0)
            )
        else:
            text_color = self._get_text_color()
            if isinstance(text_color, ThemeStyle):
                color_tuple = text_color.color
            elif isinstance(text_color, Color):
                color_tuple = (text_color.r, text_color.g, text_color.b)
            else:
                color_tuple = text_color
        
            renderer.draw_text(self.text, actual_x, actual_y, color_tuple, self.font, style=style)

        super().render(renderer)


# ============================================================================
# LongTextLabel
# ============================================================================

class LongTextLabel(UIElement):
    """
    A multi-line text label with optional rich text support, word wrapping, and shadow.
    """
    
    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'text': {'name': 'text', 'key': 'text', 'type': str, 'editable': True,
                 'description': 'The text content of the label.'},
        'color': {'name': 'color', 'key': 'custom_color', 'type': Tuple[int, int, int], 'editable': True,
                  'description': 'Custom text color (RGB). Overrides theme color.'},
        'font_size': {'name': 'font size', 'key': 'font_size', 'type': int, 'editable': True,
                      'description': 'Size of the font in pixels.'},
        'font_name': {'name': 'font name', 'key': 'font_name', 'type': Optional[str], 'editable': True,
                      'description': 'Path to font file or None for default font.'},
        'rich_text': {'name': 'rich text', 'key': 'rich_text', 'type': bool, 'editable': True,
                      'description': 'Use rich text formatting.'},
        'line_spacing': {'name': 'line spacing', 'key': 'line_spacing', 'type': int, 'editable': True,
                         'description': 'Additional spacing between lines in pixels.'},
        'wrap_width': {'name': 'wrap width', 'key': 'wrap_width', 'type': int, 'editable': True,
                       'description': 'Maximum width before wrapping (0 = no wrap).'},
    }

    def __init__(
        self,
        x: Union[int, float],
        y: Union[int, float],
        text: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        font_size: int = 24,
        color: Optional[Union[Tuple[int, int, int], Color, ThemeStyle]] = None,
        font_name: Optional[str] = None,
        rich_text: bool = False,
        line_spacing: int = 4,
        wrap_width: int = 0,
        shadow: Optional[UiShadow] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None,
        **kwargs
    ) -> None:
        FontManager.initialize()
        self._font = FontManager.get_font(font_name, font_size)
        self.rich_text = rich_text
        self.line_spacing = line_spacing
        self.wrap_width = wrap_width
        self.shadow = shadow
        self.custom_color: Optional[Color] = None
        if color is not None:
            self.set_text_color(color)
        self.font_name = font_name
        self.font_size = font_size
        
        self._raw_text = text
        
        if width is None or height is None:
            calc_width, calc_height = self._calculate_text_size(text, wrap_width or 800)
            width = width if width is not None else calc_width
            height = height if height is not None else calc_height
        
        super().__init__(x, y, width, height, pivot, element_id)
        self.theme_type = theme or ThemeManager.get_current_theme()
        self._lines_cache = []
        self._cache_dirty = True

    def _calculate_text_size(self, text: str, max_width: int) -> Tuple[int, int]:
        if self.rich_text:
            lines = self._wrap_rich_text(text, max_width)
            if not lines:
                return (max_width, self.font.get_height())
            max_line_width = 0
            total_height = 0
            for line in lines:
                line_width = self._measure_rich_text_line(line)
                max_line_width = max(max_line_width, line_width)
                total_height += self.font.get_height() + self.line_spacing
            return (max_line_width, total_height - self.line_spacing)
        else:
            lines = self._wrap_plain_text(text, max_width)
            if not lines:
                return (max_width, self.font.get_height())
            max_line_width = max(self.font.size(line)[0] for line in lines)
            total_height = len(lines) * (self.font.get_height() + self.line_spacing) - self.line_spacing
            return (max_line_width, total_height)

    def _wrap_plain_text(self, text: str, max_width: int) -> List[str]:
        if max_width <= 0:
            return text.split('\n')
        words = text.replace('\n', ' \n ').split()
        lines = []
        current_line = []
        current_width = 0
        for word in words:
            if word == '\n':
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = []
                    current_width = 0
                continue
            word_width = self.font.size(word)[0]
            if current_width + word_width + (len(current_line) > 0) * self.font.size(' ')[0] > max_width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    lines.append(word)
                    current_width = 0
            else:
                current_line.append(word)
                current_width += word_width + (len(current_line) > 1) * self.font.size(' ')[0]
        if current_line:
            lines.append(' '.join(current_line))
        return lines or [text]

    def _wrap_rich_text(self, text: str, max_width: int) -> List[List[RichTextSegment]]:
        if max_width <= 0:
            segments = parse_rich_text(text)
            lines = []
            current_line = []
            for seg in segments:
                if seg.text == '\n':
                    if current_line:
                        lines.append(current_line)
                        current_line = []
                else:
                    current_line.append(seg)
            if current_line:
                lines.append(current_line)
            return lines
        
        segments = parse_rich_text(text)
        lines = []
        current_line = []
        current_width = 0
        
        for seg in segments:
            if seg.text == '\n':
                if current_line:
                    lines.append(current_line)
                    current_line = []
                    current_width = 0
                continue
            
            words = seg.text.split(' ')
            for i, word in enumerate(words):
                if word == '':
                    continue
                seg_font = _get_segment_font(seg, self.font)
                word_width = seg_font.size(word)[0]
                space_width = seg_font.size(' ')[0] if i < len(words) - 1 else 0
                
                if current_width + word_width + (len(current_line) > 0) * space_width > max_width:
                    if current_line:
                        lines.append(current_line)
                        current_line = []
                        current_width = 0
                    current_line.append(RichTextSegment(word, seg.color, seg.bold, seg.italic, seg.underline))
                    current_width = word_width
                else:
                    if current_line and i > 0:
                        current_line.append(RichTextSegment(' ', seg.color, seg.bold, seg.italic, seg.underline))
                        current_width += space_width
                    current_line.append(RichTextSegment(word, seg.color, seg.bold, seg.italic, seg.underline))
                    current_width += word_width
        
        if current_line:
            lines.append(current_line)
        return lines

    def _measure_rich_text_line(self, line: List[RichTextSegment]) -> int:
        total = 0
        for seg in line:
            seg_font = _get_segment_font(seg, self.font)
            total += seg_font.size(seg.text)[0]
        return total

    def set_shadow(self, shadow: Optional[UiShadow]) -> None:
        """Set or remove text shadow."""
        self.shadow = shadow

    def set_text_color(self, color: Union[Tuple[int, int, int], Color, ThemeStyle]) -> None:
        if isinstance(color, Color):
            self.custom_color = color
        elif isinstance(color, ThemeStyle):
            self.custom_color = Color(*color.color)
        else:
            self.custom_color = Color(*color)
        self._cache_dirty = True

    def set_text(self, text: str) -> None:
        self._raw_text = text
        self._cache_dirty = True
        if self.wrap_width > 0:
            calc_width, calc_height = self._calculate_text_size(text, self.wrap_width)
            self.width = calc_width
            self.height = calc_height

    def get_text(self) -> str:
        return self._raw_text

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def _get_text_color(self) -> Union[Color, ThemeStyle, Tuple[int, int, int]]:
        if self.custom_color:
            return self.custom_color
        theme = ThemeManager.get_theme(self.theme_type)
        return theme.label_text

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        default_color = self._get_text_color()
        style = {}
        if self.shadow:
            style['shadow'] = self.shadow

        if self._cache_dirty:
            if self.rich_text:
                self._lines_cache = self._wrap_rich_text(self._raw_text, self.wrap_width or self.width)
            else:
                plain_lines = self._wrap_plain_text(self._raw_text, self.wrap_width or self.width)
                self._lines_cache = [[RichTextSegment(line)] for line in plain_lines]
            self._cache_dirty = False

        current_y = actual_y
        for line in self._lines_cache:
            if self.rich_text:
                # Rich text does not support shadow yet; render without it.
                render_rich_text_line(line, renderer, actual_x, current_y, default_color, self.font)
            else:
                # Plain text line: we can apply shadow
                text = ''.join(seg.text for seg in line)
                if isinstance(default_color, ThemeStyle):
                    color_tuple = default_color.color
                elif isinstance(default_color, Color):
                    color_tuple = (default_color.r, default_color.g, default_color.b)
                else:
                    color_tuple = default_color
                renderer.draw_text(text, actual_x, current_y, color_tuple, self.font, style=style)
            current_y += self.font.get_height() + self.line_spacing

        super().render(renderer)


# ============================================================================
# ImageLabel (with Icon support via duck typing)
# ============================================================================

class ImageLabel(UIElement):
    """
    A simple label that displays an image (non‑interactive).
    Supports Icon objects (detected by presence of 'get_surface' method).
    """
    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'image_path': {'name': 'image path', 'key': 'image_path', 'type': Union[str, pygame.Surface, 'Icon'], 'editable': False,
                       'description': 'Path to image file, Surface, or Icon object.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        image_path: Union[str, pygame.Surface, Path, AtlasItem, 'Icon'],
        width: Optional[int] = None,
        height: Optional[int] = None,
        pivot: Tuple[float, float] = (0, 0),
        element_id: Optional[str] = None,
        **kwargs
    ) -> None:
        if isinstance(image_path, Path):
            image_path = str(image_path)
        if isinstance(image_path, AtlasItem):
            image_path = str(image_path.path)
        self.image_path = image_path
        self.image_color = kwargs.get('image_color', None)  # optional color for Icon
        self._image: Optional[pygame.Surface] = None
        self._load_image()

        if width is None:
            width = self._image.get_width()
        if height is None:
            height = self._image.get_height()

        self._effect: Optional[FilterType] = None
        self._effect_intensity: float = 1.0
        self._filtered_image: Optional[pygame.Surface] = None
        self._effect_dirty: bool = True

        super().__init__(x, y, width, height, pivot, element_id)

    @property
    def can_focus(self) -> bool:
        return False

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'image_path': self.image_path,
            'width': self.width,
            'height': self.height,
            'pivot': self.pivot,
            'element_id': self.element_id,
            'image_color': self.image_color,
        }

    def _is_icon_like(self, obj) -> bool:
        """Detect if an object is an Icon by checking for the get_surface method."""
        return hasattr(obj, 'get_surface') and callable(getattr(obj, 'get_surface'))

    def _load_image(self) -> None:
        """
        Load or reload the image from the current image_path and image_color.
        Supports:
        - str (file path)
        - Path
        - pygame.Surface
        - Icon instance (has get_surface() method)
        - AtlasItem
        - Callable returning any of the above
        """
        if self.image_path is None:
            self._image = pygame.Surface((100, 100))
            self._image.fill((255, 0, 255))
            return

        # Resolve callable sources first
        source = self.image_path
        if callable(source):
            try:
                source = source()
            except Exception as e:
                raise TypeError(f"Callable image_path failed: {e}") from e

        # Now handle the resolved source
        if isinstance(source, pygame.Surface):
            self._image = source
        elif hasattr(source, 'get_surface') and callable(source.get_surface):
            try:
                self._image = source.get_surface()
            except TypeError:
                self._image = source.get_surface(color=self.image_color if self.image_color is not None else (255, 255, 255))

        elif self._is_icon_like(source):
            # It's an Icon-like object; call get_surface with the stored color
            color = self.image_color if self.image_color is not None else (255, 255, 255)
            self._image = source.get_surface(color=color)

        elif isinstance(source, str):
            if not os.path.exists(source):
                self._image = pygame.Surface((100, 100))
                self._image.fill((255, 0, 255))
            else:
                self._image = pygame.image.load(source).convert_alpha()

        elif isinstance(source, Path):
            source_str = str(source)
            if not os.path.exists(source_str):
                self._image = pygame.Surface((100, 100))
                self._image.fill((255, 0, 255))
            else:
                self._image = pygame.image.load(source_str).convert_alpha()

        elif isinstance(source, AtlasItem):
            path_str = str(source.path)
            if not os.path.exists(path_str):
                self._image = pygame.Surface((100, 100))
                self._image.fill((255, 0, 255))
            else:
                self._image = pygame.image.load(path_str).convert_alpha()

        else:
            raise TypeError(
                f"image_path must be str, Path, pygame.Surface, Icon-like, AtlasItem, "
                f"or callable returning such; got {type(source)}"
            )

        # Mark effect dirty so any active filter (blur, etc.) is reapplied
        self._effect_dirty = True

    def set_image(self, image_path: Union[str, pygame.Surface, Path, AtlasItem, 'Icon']) -> None:
        if isinstance(image_path, str):
            self.image_path = image_path
            self._load_image()
        elif isinstance(image_path, pygame.Surface):
            self.image_path = None
            self._image = image_path
        elif isinstance(image_path, Path):
            self.image_path = str(image_path)
            self._load_image()
        elif isinstance(image_path, AtlasItem):
            self.image_path = str(image_path.path)
            self._load_image()
        elif self._is_icon_like(image_path):
            self.image_path = image_path
            self._load_image()
        else:
            raise TypeError("Unsupported image type")

    def set_image_color(self, color: Union[Tuple[int, int, int], Color, ThemeStyle, ColorKeys]) -> None:
        if isinstance(color, ThemeStyle):
            color = color.color
        self.image_color = color
        # Reload icon if current image_path is an Icon-like object
        if self._is_icon_like(self.image_path):
            self._load_image()

    def get_image(self) -> pygame.Surface:
        return self._image

    def set_size(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        
    def set_effect(self, filter_type: FilterType, intensity: float = 1.0) -> None:
        """
        Apply a visual effect (filter) to the image.

        Args:
            filter_type: A FilterType enum (e.g., FilterType.BLUR).
            intensity: Strength of the effect (0.0 - 1.0).
        """
        self._effect = filter_type
        self._effect_intensity = max(0.0, min(1.0, intensity))
        self._effect_dirty = True

    def clear_effect(self) -> None:
        """Remove any applied effect."""
        self._effect = None
        self._effect_intensity = 1.0
        self._effect_dirty = True
        if self._filtered_image:
            self._filtered_image = None

    def _apply_effect(self, renderer: OpenGLRenderer) -> pygame.Surface:
        """
        Apply the current effect to the original image and return a filtered surface.
        This uses the renderer's OpenGL filter capabilities.
        """
        if not self._effect or self._image is None:
            return self._image

        # Convert the image to a texture
        tex_id = renderer._surface_to_texture(self._image)
        if tex_id == 0:
            return self._image

        # Apply filter and get a new texture
        w, h = self._image.get_size()
        filtered_tex = renderer.apply_filter_to_texture(
            tex_id, w, h, self._effect, self._effect_intensity
        )

        # Clean up the original texture (we no longer need it)
        gl.glDeleteTextures(1, [tex_id])

        # Convert the filtered texture back to a pygame surface
        # We need to read pixels from the filtered texture.
        fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                  gl.GL_TEXTURE_2D, filtered_tex, 0)
        pixel_data = gl.glReadPixels(0, 0, w, h, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
        gl.glDeleteFramebuffers(1, [fbo])
        gl.glDeleteTextures(1, [filtered_tex])

        # Create a pygame surface from the pixel data (note: OpenGL reads from bottom-left)
        surf = pygame.image.fromstring(pixel_data, (w, h), 'RGBA')
        surf = pygame.transform.flip(surf, False, True)  # flip vertically
        return surf

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()

        # If effect is active and dirty, reapply
        if self._effect is not None and self._effect_dirty:
            if isinstance(renderer, OpenGLRenderer):
                self._filtered_image = self._apply_effect(renderer)
                self._effect_dirty = False
            else:
                # Fallback: no effect for software renderer
                self._filtered_image = self._image
                self._effect_dirty = False

        # Choose which image to draw
        image_to_draw = self._filtered_image if self._filtered_image is not None else self._image

        if image_to_draw.get_width() != self.width or image_to_draw.get_height() != self.height:
            scaled_image = pygame.transform.scale(image_to_draw, (self.width, self.height))
            renderer.draw_surface(scaled_image, actual_x, actual_y)
        else:
            renderer.draw_surface(image_to_draw, actual_x, actual_y)

        super().render(renderer)
