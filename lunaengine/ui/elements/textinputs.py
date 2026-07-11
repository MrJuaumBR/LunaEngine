# textinputs.py
import pygame
import time
from typing import Optional, Callable, Tuple, List, Dict, Any, Literal
from .base import UIElement, UIState, FontManager
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
from ...backend.types import InputState

class TextBox(UIElement):
    """
    Single-line text input field with optional label.
    Supports placeholder text, max length, and focus management.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'text': {'name': 'text', 'key': 'text', 'type': str, 'editable': True,
                 'description': 'Current text content.'},
        'placeholder_text': {'name': 'placeholder', 'key': 'placeholder_text', 'type': str, 'editable': True,
                             'description': 'Text shown when empty.'},
        'font_size': {'name': 'font size', 'key': 'font_size', 'type': int, 'editable': True,
                      'description': 'Font size in pixels.'},
        'max_length': {'name': 'max length', 'key': 'max_length', 'type': int, 'editable': True,
                       'description': 'Maximum characters allowed (0 = unlimited).'},
        'focused': {'name': 'focused', 'key': 'focused', 'type': bool, 'editable': False,
                    'description': 'Whether the text box has keyboard focus.'},
        'label': {'name': 'label', 'key': 'label', 'type': str, 'editable': True,
                  'description': 'Label text displayed next to or above the input.'},
        'label_position': {'name': 'label position', 'key': 'label_position', 'type': str, 'editable': True,
                           'description': '"left" or "top".', 'options': ['left', 'top']},
        'label_size': {'name': 'label size', 'key': 'label_size', 'type': int, 'editable': True,
                       'description': 'Font size of the label (0 = auto).'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str = "",
        font_size: int = 20,
        font_name: Optional[str] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        max_length: int = 0,
        element_id: Optional[str] = None,
        label: Optional[str] = None,
        label_position: Literal['left', 'top'] = 'left',
        label_size: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)

        # Core text properties
        self.placeholder_text = kwargs.get('placeholder_text', 'Type here...')          # hint text (stored separately)
        self.text = ''        # actual user text
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self._placeholder_font = None
        self._text_surface = None
        self._text_rect = None
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.focused = False
        self._needs_redraw = True
        self.max_length = max_length
        self._backspace_timer = 0.0
        self._backspace_initial_delay = 0.5
        self._backspace_repeat_delay = 0.05

        # Label support
        self.label = label
        self.label_position = label_position.lower()
        self.label_size = label_size or int(height * 0.7)
        self._label_font = None
        self._label_rect = pygame.Rect(0, 0, 0, 0)
        self._input_rect = pygame.Rect(0, 0, width, height)
        self._label_padding = 5

        self.theme_type = theme or ThemeManager.get_current_theme()

        self.on_text_changed: Optional[Callable[[str], None]] = None
        self.set_text(self.text)
        self._update_layout()

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'text': self.placeholder_text,
            'font_size': self.font_size,
            'font_name': self.font_name,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'max_length': self.max_length,
            'element_id': self.element_id,
            'label': self.label,
            'label_position': self.label_position,
            'label_size': self.label_size,
        }

    def set_on_text_changed(self, callback: Callable[[str], None]) -> None:
        """Set a callback to be invoked when the text changes."""
        self.on_text_changed = callback

    # ------------------------------------------------------------------
    # Properties and fonts
    # ------------------------------------------------------------------
    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    @property
    def placeholder_font(self) -> pygame.font.Font:
        if self._placeholder_font is None:
            placeholder_size = max(8, self.font_size - 2)
            self._placeholder_font = FontManager.get_font(self.font_name, placeholder_size)
        return self._placeholder_font

    @property
    def label_font(self) -> pygame.font.Font:
        if self._label_font is None:
            self._label_font = FontManager.get_font(self.font_name, self.label_size)
        return self._label_font

    # ------------------------------------------------------------------
    # Layout update
    # ------------------------------------------------------------------
    def _update_layout(self) -> None:
        """Recalculate label and input rectangles based on current settings."""
        total_w = self.width
        total_h = self.height

        if self.label and self.label_position == 'left':
            label_width = self.label_font.size(self.label)[0] + self._label_padding * 2
            input_width = max(40, total_w - label_width)
            self._label_rect = pygame.Rect(0, 0, label_width, total_h)
            self._input_rect = pygame.Rect(label_width, 0, input_width, total_h)
        elif self.label and self.label_position == 'top':
            label_height = self.label_font.get_height() + self._label_padding * 2
            input_height = max(20, total_h - label_height)
            self._label_rect = pygame.Rect(0, 0, total_w, label_height)
            self._input_rect = pygame.Rect(0, label_height, total_w, input_height)
        else:
            self._label_rect = pygame.Rect(0, 0, 0, 0)
            self._input_rect = pygame.Rect(0, 0, total_w, total_h)

    # ------------------------------------------------------------------
    # Text management
    # ------------------------------------------------------------------
    def get_text(self) -> str:
        return str(self.text)

    def has_focus(self) -> bool:
        return self.focused

    def set_text(self, text: str) -> None:
        if self.text != text:
            self.text = text
            self.cursor_pos = len(text)
            self._update_text_surface()
            if self.on_text_changed:
                self.on_text_changed(self.text)

    def _update_text_surface(self) -> None:
        if self.text:
            text_color = self._get_text_color()
            self._text_surface = self.font.render(self.text, True, text_color)
            self._text_rect = self._text_surface.get_rect()
        else:
            self._text_surface = None
            self._text_rect = None
        self._needs_redraw = True

    # ------------------------------------------------------------------
    # Colors (theme-aware)
    # ------------------------------------------------------------------
    def _get_text_color(self) -> Tuple[int, int, int]:
        theme = ThemeManager.get_theme(self.theme_type)
        return theme.dropdown_text.color if theme.dropdown_text else (255, 255, 255)

    def _get_placeholder_color(self) -> Tuple[int, int, int, int]:
        theme = ThemeManager.get_theme(self.theme_type)
        base = theme.dropdown_text.color if theme.dropdown_text else (200, 200, 200)
        return (base[0], base[1], base[2], 160)

    def _get_background_color(self) -> Tuple[int, int, int]:
        theme = ThemeManager.get_theme(self.theme_type)
        if self.state == UIState.DISABLED:
            return (100, 100, 100)
        elif self.focused:
            return theme.dropdown_expanded.color if theme.dropdown_expanded else (60, 60, 80)
        else:
            return theme.dropdown_normal.color if theme.dropdown_normal else (90, 90, 110)

    # ------------------------------------------------------------------
    # Keyboard events
    # ------------------------------------------------------------------
    def on_key_down(self, event: pygame.event.Event) -> None:
        if not self.focused or event.type != pygame.KEYDOWN:
            return
        text_changed = False
        cursor_moved = False

        if event.key == pygame.K_BACKSPACE:
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
                if self.on_text_changed and callable(self.on_text_changed):
                    self.on_text_changed(self.text)
                text_changed = True
        elif event.key == pygame.K_DELETE:
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                if self.on_text_changed and callable(self.on_text_changed):
                    self.on_text_changed(self.text)
                text_changed = True    
        elif event.key == pygame.K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            cursor_moved = True
        elif event.key == pygame.K_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            cursor_moved = True
        elif event.key == pygame.K_HOME:
            self.cursor_pos = 0
            cursor_moved = True
        elif event.key == pygame.K_END:
            self.cursor_pos = len(self.text)
            cursor_moved = True

        if text_changed:
            self._update_text_surface()
        elif cursor_moved:
            self.cursor_visible = True
            self.cursor_timer = 0
            self._needs_redraw = True

    def on_key_up(self, event: pygame.event.Event) -> None:
        if not self.focused or event.type != pygame.KEYUP:
            return
        text_changed = False
        cursor_moved = False

        if event.key in [pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_LEFT, pygame.K_RIGHT,
                         pygame.K_HOME, pygame.K_END]:
            pass
        elif event.unicode and event.unicode.isprintable():
            if self.max_length == 0 or len(self.text) < self.max_length:
                self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                self.cursor_pos += len(event.unicode)
                text_changed = True
                cursor_moved = True

        if text_changed:
            self._update_text_surface()
            if self.on_text_changed:
                self.on_text_changed(self.text)
        elif cursor_moved:
            self.cursor_visible = True
            self.cursor_timer = 0
            self._needs_redraw = True

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            self.focused = False
            return

        # Check mouse over the entire element (or only input rect? we use entire element)
        mouse_over = self.mouse_over(inputState)

        if inputState.mouse_buttons_pressed.left:
            if mouse_over:
                self.focused = True
                inputState.consume_global_mouse()
                self._needs_redraw = True
            else:
                self.focused = False
                self.state = UIState.NORMAL
                self._needs_redraw = True
        else:
            self.state = UIState.HOVERED if mouse_over else UIState.NORMAL

        # Cursor blink
        if self.focused:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible

    def focus(self) -> None:
        self.focused = True
        self.state = UIState.PRESSED
        self._needs_redraw = True

    def unfocus(self) -> None:
        self.focused = False
        self.state = UIState.NORMAL
        self._needs_redraw = True

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------
    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        # Background for the entire element (optional, but we draw it for consistency)
        # We'll draw a transparent background to unify the look, or we can skip.
        # To keep it similar to before, we'll draw the input background only.
        # We'll draw the input background rect.
        input_abs_x = actual_x + self._input_rect.x
        input_abs_y = actual_y + self._input_rect.y

        bg_color = self._get_background_color()
        renderer.draw_rect(input_abs_x, input_abs_y,
                           self._input_rect.width, self._input_rect.height,
                           bg_color, fill=True,
                           border_width=self.border_width,
                           corner_radius=self.corner_radius,
                           border_color=theme.text_primary.color if self.focused else theme.dropdown_border.color)

        # Clip text to the input box bounds
        if hasattr(renderer, 'enable_scissor'):
            renderer.enable_scissor(input_abs_x, input_abs_y,
                                    self._input_rect.width, self._input_rect.height)

        # Render text content inside input rect
        self._render_text_content(renderer, input_abs_x, input_abs_y, theme)

        if self.focused and self.cursor_visible:
            cursor_x, cursor_y = self._get_cursor_position(input_abs_x, input_abs_y)
            cursor_height = self.font.get_height()
            cursor_actual_y = input_abs_y + (self._input_rect.height - cursor_height) // 2
            cursor_color = theme.text_primary.color if theme.text_primary else (255, 255, 255)
            if cursor_x < input_abs_x + self._input_rect.width - 2:
                renderer.draw_rect(cursor_x, cursor_actual_y, 2, cursor_height, cursor_color)

        if hasattr(renderer, 'disable_scissor'):
            renderer.disable_scissor()

        # Render label if present
        if self.label and self._label_rect.width > 0:
            label_abs_x = actual_x + self._label_rect.x
            label_abs_y = actual_y + self._label_rect.y
            label_color = theme.label_text.color if theme.label_text else (220, 220, 220)
            # Center label vertically or horizontally depending on position
            if self.label_position == 'left':
                text_y = label_abs_y + (self._label_rect.height - self.label_font.get_height()) // 2
                renderer.draw_text(self.label, label_abs_x + self._label_padding, text_y,
                                   label_color, self.label_font, pivot=(0, 0))
            else:  # top
                text_x = label_abs_x + (self._label_rect.width // 2)
                text_y = label_abs_y + self._label_padding
                renderer.draw_text(self.label, text_x, text_y,
                                   label_color, self.label_font, pivot=(0.5, 0))

        self._needs_redraw = False

        # Render children (if any)
        for child in self.children:
            child.render(renderer)

    # ------------------------------------------------------------------
    # Helper rendering methods
    # ------------------------------------------------------------------
    def _render_text_content(self, renderer: Renderer, input_abs_x: int, input_abs_y: int, theme) -> None:
        """Render actual text or placeholder inside the input area."""
        if self.text and self._text_surface is not None:
            text_y = input_abs_y + (self._input_rect.height - self._text_rect.height) // 2
            # Scrolling logic if text overflows
            if self._text_rect.width > self._input_rect.width - 10:
                clip_width = self._input_rect.width - 10
                if self.focused and self.text:
                    cursor_x = self.font.size(self.text[:self.cursor_pos])[0]
                    if cursor_x > clip_width:
                        scroll_offset = cursor_x - clip_width + 10
                        source_rect = pygame.Rect(
                            max(0, min(scroll_offset, self._text_rect.width - clip_width)), 0,
                            min(clip_width, self._text_rect.width), self._text_rect.height
                        )
                        if (source_rect.width > 0 and source_rect.height > 0 and
                            source_rect.right <= self._text_rect.width and
                            source_rect.bottom <= self._text_rect.height):
                            clipped = self._text_surface.subsurface(source_rect)
                            if hasattr(renderer, 'render_surface'):
                                renderer.render_surface(clipped, input_abs_x + 5, text_y)
                            else:
                                renderer.draw_surface(clipped, input_abs_x + 5, text_y)
                        else:
                            if hasattr(renderer, 'render_surface'):
                                renderer.render_surface(self._text_surface, input_abs_x + 5, text_y)
                            else:
                                renderer.draw_surface(self._text_surface, input_abs_x + 5, text_y)
                    else:
                        if hasattr(renderer, 'render_surface'):
                            renderer.render_surface(self._text_surface, input_abs_x + 5, text_y)
                        else:
                            renderer.draw_surface(self._text_surface, input_abs_x + 5, text_y)
                else:
                    source_rect = pygame.Rect(0, 0, min(clip_width, self._text_rect.width), self._text_rect.height)
                    if source_rect.width > 0 and source_rect.height > 0:
                        clipped = self._text_surface.subsurface(source_rect)
                        if hasattr(renderer, 'render_surface'):
                            renderer.render_surface(clipped, input_abs_x + 5, text_y)
                        else:
                            renderer.draw_surface(clipped, input_abs_x + 5, text_y)
            else:
                if hasattr(renderer, 'render_surface'):
                    renderer.render_surface(self._text_surface, input_abs_x + 5, text_y)
                else:
                    renderer.draw_surface(self._text_surface, input_abs_x + 5, text_y)

        elif self.placeholder_text:
            # Placeholder: smaller font, semi-transparent
            placeholder_color = self._get_placeholder_color()
            placeholder_y = input_abs_y + (self._input_rect.height - self.placeholder_font.get_height()) // 2
            renderer.draw_text(
                self.placeholder_text,
                input_abs_x + 5,
                placeholder_y,
                placeholder_color,
                self.placeholder_font
            )

    def _get_cursor_position(self, input_abs_x: int, input_abs_y: int) -> Tuple[int, int]:
        """Compute screen position of the cursor."""
        base_x = input_abs_x + 5
        base_y = input_abs_y + (self._input_rect.height - self.font.get_height()) // 2
        if not self.text or self.cursor_pos == 0:
            return base_x, base_y
        text_before = self.text[:self.cursor_pos]
        text_width = self.font.size(text_before)[0]
        cursor_x = base_x + text_width
        if self._text_surface and self._text_rect.width > self._input_rect.width - 10:
            clip_width = self._input_rect.width - 10
            if text_width > clip_width:
                scroll_offset = text_width - clip_width + 5
                cursor_x = base_x + text_width - scroll_offset
        return cursor_x, base_y

    # ------------------------------------------------------------------
    # Theme update
    # ------------------------------------------------------------------
    def update_theme(self, theme_type: ThemeType) -> None:
        self.theme_type = theme_type
        self._update_text_surface()
        self._needs_redraw = True
        for child in self.children:
            if hasattr(child, 'update_theme'):
                child.update_theme(theme_type)

class TextArea(UIElement):
    """
    Multi-line text input area with word wrapping and scrollbars.
    Supports text editing, selection, copy/paste, and line numbers.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'text': {'name': 'text', 'key': 'text', 'type': str, 'editable': True,
                 'description': 'The text content.'},
        'line_numbers': {'name': 'line numbers', 'key': 'line_numbers', 'type': bool, 'editable': True,
                         'description': 'Show line numbers on the left.'},
        'word_wrap': {'name': 'word wrap', 'key': 'word_wrap', 'type': bool, 'editable': True,
                      'description': 'Automatically wrap long lines.'},
        'read_only': {'name': 'read only', 'key': 'read_only', 'type': bool, 'editable': True,
                      'description': 'If True, text cannot be edited.'},
        'tab_size': {'name': 'tab size', 'key': 'tab_size', 'type': int, 'editable': True,
                     'description': 'Number of spaces per tab.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str = "",
        font_size: int = 16,
        font_name: Optional[str] = None,
        line_numbers: bool = True,
        word_wrap: bool = True,
        read_only: bool = False,
        tab_size: int = 4,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)

        self.text = text
        self.lines = text.split('\n')
        self.font_size = font_size
        self.font_name = font_name
        self.line_numbers = line_numbers
        self.word_wrap = word_wrap
        self.read_only = read_only
        self.tab_size = tab_size

        self.theme_type = theme or ThemeManager.get_current_theme()

        self.cursor_line = 0
        self.cursor_column = 0
        self.selection_start = None
        self.selection_end = None
        self.cursor_visible = True
        self.cursor_timer = 0.0

        self.scroll_x = 0
        self.scroll_y = 0
        self._line_height_cache = 0

        self.line_number_width = 0
        self.line_number_padding = 10

        self.text_area_x = 0
        self.text_area_y = 0
        self.text_area_width = width
        self.text_area_height = height

        self._font = None
        self._update_dimensions()

        self.focused = False
        self._dragging = False
        self._drag_start_pos = None
        self._clipboard = ""

        self._undo_stack = []
        self._redo_stack = []
        self._last_text = text

        self.on_text_changed: Optional[Callable[[str], None]] = None

        self._update_text_buffer()

    # ------------------------------------------------------------------
    @property
    def line_height(self) -> int:
        if self._line_height_cache == 0:
            self._line_height_cache = self.font.get_height() + 2
        return self._line_height_cache

    # ------------------------------------------------------------------
    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'text': self.text,
            'font_size': self.font_size,
            'font_name': self.font_name,
            'line_numbers': self.line_numbers,
            'word_wrap': self.word_wrap,
            'read_only': self.read_only,
            'tab_size': self.tab_size,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def get_text(self) -> str:
        return self.text

    def set_text(self, text: str) -> None:
        if text != self.text:
            self._save_to_undo_stack()
            self.text = text
            self.lines = text.split('\n')
            self._update_text_buffer()
            self.cursor_line = 0
            self.cursor_column = 0
            self.selection_start = None
            self.selection_end = None
            self._scroll_to_cursor()
            if self.on_text_changed:
                self.on_text_changed(text)

    def _update_dimensions(self) -> None:
        if self.line_numbers:
            max_lines = max(1, len(self.lines))
            digits = len(str(max_lines))
            self.line_number_width = self.font.size(" " * digits)[0] + self.line_number_padding * 2
        else:
            self.line_number_width = 0
        self.text_area_x = self.line_number_width
        self.text_area_y = 0
        self.text_area_width = self.width - self.line_number_width
        self.text_area_height = self.height

    def _update_text_buffer(self) -> None:
        self.lines = self.text.split('\n')
        self._update_dimensions()

    def _save_to_undo_stack(self) -> None:
        self._undo_stack.append(self.text)
        self._redo_stack.clear()
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)

    def undo(self) -> None:
        if self._undo_stack:
            self._redo_stack.append(self.text)
            self.text = self._undo_stack.pop()
            self.lines = self.text.split('\n')
            self._update_dimensions()
            self._scroll_to_cursor()
            if self.on_text_changed:
                self.on_text_changed(self.text)

    def redo(self) -> None:
        if self._redo_stack:
            self._undo_stack.append(self.text)
            self.text = self._redo_stack.pop()
            self.lines = self.text.split('\n')
            self._update_dimensions()
            self._scroll_to_cursor()
            if self.on_text_changed:
                self.on_text_changed(self.text)

    def _get_visible_lines(self) -> List[int]:
        start_line = self.scroll_y // self.line_height
        visible_lines = self.text_area_height // self.line_height + 1
        end_line = min(len(self.lines), start_line + visible_lines)
        return list(range(start_line, end_line))

    # ---------- Accurate text width measurement ----------
    def _get_text_width(self, text: str) -> int:
        """Return the exact pixel width of a string using the current font."""
        if not text:
            return 0
        # Replace tabs with spaces for width calculation
        expanded = text.replace('\t', ' ' * self.tab_size)
        return self.font.size(expanded)[0]

    def _get_char_width_at_position(self, line: str, col: int) -> int:
        """Return the pixel width of the character at the given column."""
        if col >= len(line):
            return 0
        ch = line[col]
        if ch == '\t':
            ch = ' ' * self.tab_size
        return self.font.size(ch)[0]

    def _get_cursor_screen_pos(self) -> Tuple[int, int]:
        line_y = self.text_area_y + (self.cursor_line * self.line_height) - self.scroll_y
        text_before = self.lines[self.cursor_line][:self.cursor_column]
        column_x = self._get_text_width(text_before)
        column_x = self.text_area_x + column_x - self.scroll_x
        return column_x, line_y

    def _scroll_to_cursor(self) -> None:
        cursor_x, cursor_y = self._get_cursor_screen_pos()
        vx1 = self.text_area_x
        vx2 = self.text_area_x + self.text_area_width
        vy1 = self.text_area_y
        vy2 = self.text_area_y + self.text_area_height
        if cursor_x < vx1:
            self.scroll_x -= (vx1 - cursor_x)
        elif cursor_x > vx2 - 10:   # keep a small margin
            self.scroll_x += (cursor_x - (vx2 - 10))
        if cursor_y < vy1:
            self.scroll_y -= (vy1 - cursor_y)
        elif cursor_y + self.line_height > vy2:
            self.scroll_y += (cursor_y + self.line_height - vy2)
        self.scroll_x = max(0, self.scroll_x)
        max_scroll_y = max(0, len(self.lines) * self.line_height - self.text_area_height)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll_y))

    def _insert_text(self, text: str) -> None:
        if self.read_only:
            return
        self._save_to_undo_stack()
        text = text.replace('\t', ' ' * self.tab_size)
        cur_line = self.lines[self.cursor_line]
        new_line = cur_line[:self.cursor_column] + text + cur_line[self.cursor_column:]
        if '\n' in text:
            parts = text.split('\n')
            self.lines[self.cursor_line] = cur_line[:self.cursor_column] + parts[0]
            for i in range(1, len(parts)):
                self.lines.insert(self.cursor_line + i, parts[i])
            if cur_line[self.cursor_column:]:
                self.lines[self.cursor_line + len(parts) - 1] += cur_line[self.cursor_column:]
            self.cursor_line += len(parts) - 1
            self.cursor_column = len(parts[-1])
        else:
            self.lines[self.cursor_line] = new_line
            self.cursor_column += len(text)
        self.text = '\n'.join(self.lines)
        self._scroll_to_cursor()
        if self.on_text_changed:
            self.on_text_changed(self.text)

    def _delete_selection(self) -> None:
        if not self.selection_start or not self.selection_end:
            return
        sl, sc = self.selection_start
        el, ec = self.selection_end
        if (el < sl) or (el == sl and ec < sc):
            sl, sc, el, ec = el, ec, sl, sc
        self._save_to_undo_stack()
        if sl == el:
            line = self.lines[sl]
            self.lines[sl] = line[:sc] + line[ec:]
        else:
            first = self.lines[sl][:sc]
            last = self.lines[el][ec:]
            self.lines[sl] = first + last
            del self.lines[sl+1:el+1]
        self.cursor_line = sl
        self.cursor_column = sc
        self.selection_start = None
        self.selection_end = None
        self.text = '\n'.join(self.lines)
        self._scroll_to_cursor()
        if self.on_text_changed:
            self.on_text_changed(self.text)

    def _get_selection_text(self) -> str:
        if not self.selection_start or not self.selection_end:
            return ""
        sl, sc = self.selection_start
        el, ec = self.selection_end
        if (el < sl) or (el == sl and ec < sc):
            sl, sc, el, ec = el, ec, sl, sc
        if sl == el:
            return self.lines[sl][sc:ec]
        result = [self.lines[sl][sc:]]
        for i in range(sl+1, el):
            result.append(self.lines[i])
        result.append(self.lines[el][:ec])
        return '\n'.join(result)

    def copy(self) -> None:
        if self.selection_start and self.selection_end:
            self._clipboard = self._get_selection_text()

    def cut(self) -> None:
        if self.selection_start and self.selection_end:
            self._clipboard = self._get_selection_text()
            self._delete_selection()

    def paste(self) -> None:
        if self._clipboard:
            self._insert_text(self._clipboard)

    def select_all(self) -> None:
        self.selection_start = (0, 0)
        self.selection_end = (len(self.lines) - 1, len(self.lines[-1]))

    def _move_cursor(self, line_delta: int, column_delta: int, extend_selection: bool = False) -> None:
        if not extend_selection:
            self.selection_start = None
            self.selection_end = None
        elif self.selection_start is None:
            self.selection_start = (self.cursor_line, self.cursor_column)
        new_line = max(0, min(len(self.lines) - 1, self.cursor_line + line_delta))
        if column_delta != 0:
            cur = self.lines[new_line]
            new_col = max(0, min(len(cur), self.cursor_column + column_delta))
            self.cursor_column = new_col
        self.cursor_line = new_line
        if extend_selection:
            self.selection_end = (self.cursor_line, self.cursor_column)
        self._scroll_to_cursor()

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible:
            return
        mouse_over = self.mouse_over(inputState)
        if inputState.mouse_buttons_pressed.left:
            if mouse_over:
                self.focused = True
                self._dragging = True
                self._drag_start_pos = self._get_cursor_from_mouse(inputState.mouse_pos)
                self.selection_start = self._drag_start_pos
                self.selection_end = self._drag_start_pos
                self.cursor_line, self.cursor_column = self._drag_start_pos
                self._scroll_to_cursor()
            else:
                self.focused = False
        if self._dragging and inputState.mouse_buttons_pressed.left:
            drag_end = self._get_cursor_from_mouse(inputState.mouse_pos)
            self.selection_end = drag_end
            self.cursor_line, self.cursor_column = drag_end
            self._scroll_to_cursor()
        elif not inputState.mouse_buttons_pressed.left:
            self._dragging = False
        if self.focused:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible

    def on_key_down(self, event: pygame.event.Event) -> None:
        if not self.focused:
            return
        pass

    def on_key_up(self, event: pygame.event.Event) -> None:
        if not self.focused or event.type != pygame.KEYUP:
            return
        self._handle_key_event(event)

    # ---------- ACCURATE CURSOR FROM MOUSE ----------
    def _get_cursor_from_mouse(self, mouse_pos: Tuple[int, int]) -> Tuple[int, int]:
        ax, ay = self.get_actual_position()
        rel_x = mouse_pos[0] - ax - self.text_area_x + self.scroll_x
        rel_y = mouse_pos[1] - ay - self.text_area_y + self.scroll_y

        # Vertical: find line
        line = min(len(self.lines) - 1, max(0, rel_y // self.line_height))
        line_text = self.lines[line]

        # Horizontal: find column by measuring accumulated widths
        col = 0
        # If the click is beyond the end of the line, put cursor at end
        if rel_x > self._get_text_width(line_text):
            return line, len(line_text)

        # Binary search for the correct column
        low, high = 0, len(line_text)
        while low < high:
            mid = (low + high) // 2
            width_before = self._get_text_width(line_text[:mid])
            width_after = self._get_text_width(line_text[:mid+1])
            if rel_x < width_before:
                high = mid
            elif rel_x > width_after:
                low = mid + 1
            else:
                # Between two characters – choose the closer one
                if rel_x - width_before < width_after - rel_x:
                    col = mid
                else:
                    col = mid + 1
                return line, col
        col = low
        return line, col

    def _handle_key_event(self, event: pygame.event.Event) -> None:
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL
        shift = mods & pygame.KMOD_SHIFT

        if event.key == pygame.K_BACKSPACE:
            if self.selection_start and self.selection_end:
                self._delete_selection()
            elif self.cursor_column > 0:
                self._save_to_undo_stack()
                line = self.lines[self.cursor_line]
                self.lines[self.cursor_line] = line[:self.cursor_column-1] + line[self.cursor_column:]
                self.cursor_column -= 1
                self.text = '\n'.join(self.lines)
                self._scroll_to_cursor()
                if self.on_text_changed:
                    self.on_text_changed(self.text)
            elif self.cursor_line > 0:
                self._save_to_undo_stack()
                prev = self.lines[self.cursor_line-1]
                cur = self.lines[self.cursor_line]
                self.lines[self.cursor_line-1] = prev + cur
                del self.lines[self.cursor_line]
                self.cursor_line -= 1
                self.cursor_column = len(prev)
                self.text = '\n'.join(self.lines)
                self._scroll_to_cursor()
            if self.on_text_changed and callable(self.on_text_changed):
                self.on_text_changed(self.text)
            return

        if event.key == pygame.K_DELETE:
            if self.selection_start and self.selection_end:
                self._delete_selection()
            elif self.cursor_column < len(self.lines[self.cursor_line]):
                self._save_to_undo_stack()
                line = self.lines[self.cursor_line]
                self.lines[self.cursor_line] = line[:self.cursor_column] + line[self.cursor_column+1:]
                self.text = '\n'.join(self.lines)
                if self.on_text_changed:
                    self.on_text_changed(self.text)
            elif self.cursor_line < len(self.lines)-1:
                self._save_to_undo_stack()
                cur = self.lines[self.cursor_line]
                nxt = self.lines[self.cursor_line+1]
                self.lines[self.cursor_line] = cur + nxt
                del self.lines[self.cursor_line+1]
                self.text = '\n'.join(self.lines)
                self._scroll_to_cursor()
            if self.on_text_changed and callable(self.on_text_changed):
                self.on_text_changed(self.text)
            return

        if event.key == pygame.K_RETURN:
            self._insert_text('\n')
            return

        if event.key == pygame.K_TAB:
            self._insert_text(' ' * self.tab_size)
            return

        if ctrl:
            if event.key == pygame.K_a:
                self.select_all()
            elif event.key == pygame.K_c:
                self.copy()
            elif event.key == pygame.K_x:
                self.cut()
            elif event.key == pygame.K_v:
                self.paste()
            elif event.key == pygame.K_z:
                self.undo()
            elif event.key == pygame.K_y:
                self.redo()
            return

        if event.key == pygame.K_LEFT:
            if self.cursor_column > 0:
                self._move_cursor(0, -1, shift)
            elif self.cursor_line > 0:
                self.cursor_line -= 1
                self.cursor_column = len(self.lines[self.cursor_line])
                if not shift:
                    self.selection_start = self.selection_end = None
                self._scroll_to_cursor()
        elif event.key == pygame.K_RIGHT:
            if self.cursor_column < len(self.lines[self.cursor_line]):
                self._move_cursor(0, 1, shift)
            elif self.cursor_line < len(self.lines)-1:
                self.cursor_line += 1
                self.cursor_column = 0
                if not shift:
                    self.selection_start = self.selection_end = None
                self._scroll_to_cursor()
        elif event.key == pygame.K_UP:
            self._move_cursor(-1, 0, shift)
        elif event.key == pygame.K_DOWN:
            self._move_cursor(1, 0, shift)
        elif event.key == pygame.K_HOME:
            self.cursor_column = 0
            if not shift:
                self.selection_start = self.selection_end = None
            self._scroll_to_cursor()
        elif event.key == pygame.K_END:
            self.cursor_column = len(self.lines[self.cursor_line])
            if not shift:
                self.selection_start = self.selection_end = None
            self._scroll_to_cursor()
        elif event.key == pygame.K_PAGEUP:
            visible = self.text_area_height // self.line_height
            self._move_cursor(-visible, 0, shift)
        elif event.key == pygame.K_PAGEDOWN:
            visible = self.text_area_height // self.line_height
            self._move_cursor(visible, 0, shift)
        elif event.unicode and event.unicode.isprintable() and not self.read_only:
            self._insert_text(event.unicode)

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return
        ax, ay = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        border_color = theme.button_border.color if (self.focused and theme.button_border) else (theme.border.color if theme.border else (120,120,140))
        bg = theme.background.color if self.focused else (theme.button_disabled.color if theme.button_disabled else (100,100,100))
        renderer.draw_rect(ax, ay, self.width, self.height, bg, fill=True, border_width=self.border_width, border_color=border_color, corner_radius=self.corner_radius)
        if hasattr(renderer, 'enable_scissor'):
            renderer.enable_scissor(ax, ay, self.width, self.height)
        if self.line_numbers:
            for ln in self._get_visible_lines():
                line_y = ay + (ln * self.line_height) - self.scroll_y
                num_text = str(ln+1)
                num_x = ax + self.line_number_width - self.line_number_padding - self.font.size(num_text)[0]
                renderer.draw_text(num_text, num_x, line_y, theme.text_secondary.color, self.font)
            sep_x = ax + self.line_number_width - 1
            renderer.draw_rect(sep_x, ay, 1, self.height, theme.border.color, fill=True)
        for ln in self._get_visible_lines():
            if ln < len(self.lines):
                line_text = self.lines[ln]
                line_y = ay + (ln * self.line_height) - self.scroll_y
                text_x = ax + self.text_area_x - self.scroll_x
                if self.selection_start and self.selection_end:
                    self._draw_selection_highlight(renderer, ax, ay, ln, line_y)
                renderer.draw_text(line_text, text_x, line_y, theme.text_primary.color, self.font)
        if self.focused and self.cursor_visible:
            cx, cy = self._get_cursor_screen_pos()
            renderer.draw_rect(ax + cx, ay + cy, 2, self.line_height, theme.text_primary.color, fill=True)
        if hasattr(renderer, 'disable_scissor'):
            renderer.disable_scissor()

    def _draw_selection_highlight(self, renderer: Renderer, ax: int, ay: int, line_num: int, line_y: int) -> None:
        sl, sc = self.selection_start
        el, ec = self.selection_end
        if (el < sl) or (el == sl and ec < sc):
            sl, sc, el, ec = el, ec, sl, sc
        if line_num < sl or line_num > el:
            return
        if line_num == sl and line_num == el:
            start_col, end_col = sc, ec
        elif line_num == sl:
            start_col, end_col = sc, len(self.lines[line_num])
        elif line_num == el:
            start_col, end_col = 0, ec
        else:
            start_col, end_col = 0, len(self.lines[line_num])

        start_x = self._get_text_width(self.lines[line_num][:start_col])
        end_x = self._get_text_width(self.lines[line_num][:end_col])
        hx = ax + self.text_area_x + start_x - self.scroll_x
        hw = end_x - start_x
        if hw > 0:
            renderer.draw_rect(hx, ay + line_y, hw, self.line_height, (100,150,255,100), fill=True) 