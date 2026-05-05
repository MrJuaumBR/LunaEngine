# textinputs.py
import pygame
import time
from typing import Optional, Callable, Tuple, List
from .base import UIElement, UIState, FontManager
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
from ...backend.types import InputState

class TextBox(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, 
                 text: str = "", font_size: int = 20, font_name: Optional[str] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 max_length: int = 0,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.placeholder_text = text
        self.text = ""
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
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
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.set_text(self.text)
        
        self.on_text_changed: Optional[Callable[[str,], None]] = None
        
    @property
    def font(self):
        if self._font is None:
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    def get_text(self) -> str:
        return str(self.text)
    
    def has_focus(self) -> bool:
        return self.focused
    
    def on_key_down(self, event: pygame.event.Event):
        if not self.focused or event.type != pygame.KEYDOWN:
            return
        text_changed = False
        cursor_moved = False
        
        if event.key == pygame.K_BACKSPACE:
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
                self._needs_redraw = True
                text_changed = True
                
        elif event.key == pygame.K_DELETE:
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
                self._needs_redraw = True
                text_changed = True
                
        elif event.key == pygame.K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            self._needs_redraw = True
            cursor_moved = True
            
        elif event.key == pygame.K_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            self._needs_redraw = True
            cursor_moved = True
        elif event.key == pygame.K_HOME:
            self.cursor_pos = 0
            self._needs_redraw = True
            cursor_moved = True
        elif event.key == pygame.K_END:
            self.cursor_pos = len(self.text)
            self._needs_redraw = True
            cursor_moved = True
            
        if text_changed:
            self._update_text_surface()
        elif cursor_moved:
            self.cursor_visible = True
            self.cursor_timer = 0
            self._needs_redraw = True
        
    def on_key_up(self, event: pygame.event.Event):
        if not self.focused or event.type != pygame.KEYUP:
            return
        
        text_changed = False
        cursor_moved = False
        
        if event.key in [pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_HOME, pygame.K_END]:
            pass
        elif event.unicode and event.unicode.isprintable():
            if self.max_length > 0 and len(self.text) >= self.max_length:
                pass
            else:
                self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                self.cursor_pos += len(event.unicode)
                text_changed = True
                cursor_moved = True
        
        if text_changed:
            self._update_text_surface()
            if self.on_text_changed and callable(self.on_text_changed):
                self.on_text_changed(self.text)
        elif cursor_moved:
            self.cursor_visible = True
            self.cursor_timer = 0
            self._needs_redraw = True
    
    def _update_text_surface(self):
        display_text = self.text if self.text else self.placeholder_text
        text_color = self._get_text_color()
        
        if display_text:
            self._text_surface = self.font.render(display_text, True, text_color)
            self._text_rect = self._text_surface.get_rect()
        else:
            self._text_surface = None
            self._text_rect = None
        
        self._needs_redraw = True
    
    def _get_text_color(self):
        theme = ThemeManager.get_theme(self.theme_type)
        if not self.text and self.placeholder_text:
            # Lighter color for placeholder
            main_color = theme.dropdown_text.color if theme.dropdown_text else (200, 200, 200)
            return tuple(max(0, c - 80) for c in main_color)
        return theme.dropdown_text.color if theme.dropdown_text else (255, 255, 255)
    
    def _get_background_color(self):
        theme = ThemeManager.get_theme(self.theme_type)
        if self.state == UIState.DISABLED:
            return (100, 100, 100)
        elif self.focused:
            return theme.dropdown_expanded.color if theme.dropdown_expanded else (60, 60, 80)
        else:
            return theme.dropdown_normal.color if theme.dropdown_normal else (90, 90, 110)
    
    def set_text(self, text: str):
        if self.text != text:
            self.text = text
            self.cursor_pos = len(text)
            self._update_text_surface()
            if self.on_text_changed:
                self.on_text_changed(self.text)
    
    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            self.focused = False
            return
        
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
    
    def focus(self):
        self.focused = True
        self.state = UIState.PRESSED
        self._needs_redraw = True
        
    def unfocus(self):
        self.focused = False
        self.state = UIState.NORMAL
        self._needs_redraw = True
    
    def _get_cursor_position(self, actual_x: int, actual_y: int) -> Tuple[int, int]:
        base_x = actual_x + 5
        base_y = actual_y + (self.height - self.font.get_height()) // 2
        
        if not self.text or self.cursor_pos == 0:
            return base_x, base_y
        
        text_before_cursor = self.text[:self.cursor_pos]
        text_width = self.font.size(text_before_cursor)[0]
        
        cursor_x = base_x + text_width
        
        if self._text_surface and self._text_rect.width > self.width - 10:
            clip_width = self.width - 10
            if text_width > clip_width:
                scroll_offset = text_width - clip_width + 5
                cursor_x = base_x + text_width - scroll_offset
        
        return cursor_x, base_y
    
    def render(self, renderer):
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        if theme.dropdown_border:
            border_color = theme.text_primary.color if self.focused else theme.dropdown_border.color
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                               border_color, fill=False, border_width=self.border_width,
                               corner_radius=self.corner_radius)
        
        bg_color = self._get_background_color()
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           bg_color, fill=True, border_width=self.border_width,
                           corner_radius=self.corner_radius)
        
        self._render_text_content(renderer, actual_x, actual_y, theme)
        
        if self.focused and self.cursor_visible:
            cursor_x, cursor_y = self._get_cursor_position(actual_x, actual_y)
            cursor_height = self.font.get_height()
            cursor_y = actual_y + (self.height - cursor_height) // 2
            
            cursor_color = theme.text_primary.color if theme.text_primary else (255, 255, 255)
            
            if cursor_x < actual_x + self.width - 2:
                renderer.draw_rect(cursor_x, cursor_y, 5, cursor_height, cursor_color)
        
        self._needs_redraw = False
        
        for child in self.children:
            child.render(renderer)
    
    def _render_text_content(self, renderer, actual_x: int, actual_y: int, theme):
        if self._text_surface is None:
            return
            
        text_y = actual_y + (self.height - self._text_rect.height) // 2
        
        if self._text_rect.width > self.width - 10:
            clip_width = self.width - 10
            
            if self.focused and self.text:
                cursor_x = self.font.size(self.text[:self.cursor_pos])[0]
                if cursor_x > clip_width:
                    scroll_offset = cursor_x - clip_width + 10
                    source_rect = pygame.Rect(
                        max(0, min(scroll_offset, self._text_rect.width - clip_width)),
                        0,
                        min(clip_width, self._text_rect.width),
                        self._text_rect.height
                    )
                    if (source_rect.width > 0 and source_rect.height > 0 and 
                        source_rect.right <= self._text_rect.width and 
                        source_rect.bottom <= self._text_rect.height):
                        clipped_surface = self._text_surface.subsurface(source_rect)
                        if hasattr(renderer, 'render_surface'):
                            renderer.render_surface(clipped_surface, actual_x + 5, text_y)
                        else:
                            renderer.draw_surface(clipped_surface, actual_x + 5, text_y)
                    else:
                        if hasattr(renderer, 'render_surface'):
                            renderer.render_surface(self._text_surface, actual_x + 5, text_y)
                        else:
                            renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
                else:
                    if hasattr(renderer, 'render_surface'):
                        renderer.render_surface(self._text_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
            else:
                source_rect = pygame.Rect(0, 0, min(clip_width, self._text_rect.width), self._text_rect.height)
                if (source_rect.width > 0 and source_rect.height > 0 and 
                    source_rect.right <= self._text_rect.width and 
                    source_rect.bottom <= self._text_rect.height):
                    clipped_surface = self._text_surface.subsurface(source_rect)
                    if hasattr(renderer, 'render_surface'):
                        renderer.render_surface(clipped_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(clipped_surface, actual_x + 5, text_y)
                else:
                    if hasattr(renderer, 'render_surface'):
                        renderer.render_surface(self._text_surface, actual_x + 5, text_y)
                    else:
                        renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
        else:
            if hasattr(renderer, 'render_surface'):
                renderer.render_surface(self._text_surface, actual_x + 5, text_y)
            else:
                renderer.draw_surface(self._text_surface, actual_x + 5, text_y)
    
    
class TextArea(UIElement):
    """
    Multi-line text input area with word wrapping and scrollbars.
    
    Supports text editing, selection, copy/paste, and line numbers.
    
    Attributes:
        text (str): The text content.
        line_numbers (bool): Whether to show line numbers.
        word_wrap (bool): Whether to wrap long lines.
        read_only (bool): Whether text is read-only.
        tab_size (int): Number of spaces for tab character.
    """
    
    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str = "", font_size: int = 16, font_name: Optional[str] = None,
                 line_numbers: bool = True, word_wrap: bool = True,
                 read_only: bool = False, tab_size: int = 4,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        
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
        self.line_height = font_size + 4
        self.char_width = 8
        
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
        
        self._update_text_buffer()
    
    @property
    def font(self):
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    def get_text(self) -> str:
        return self.text
    
    def set_text(self, text: str):
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
    
    def _update_dimensions(self):
        if self.line_numbers:
            max_lines = len(self.lines)
            digits = len(str(max_lines))
            self.line_number_width = self.font.size(" " * digits)[0] + self.line_number_padding * 2
        else:
            self.line_number_width = 0
        
        self.text_area_x = self.line_number_width
        self.text_area_y = 0
        self.text_area_width = self.width - self.line_number_width
        self.text_area_height = self.height
        
        char_surface = self.font.render("M", True, (255, 255, 255))
        self.char_width = char_surface.get_width()
    
    def _update_text_buffer(self):
        self.lines = self.text.split('\n')
        self._update_dimensions()
    
    def _save_to_undo_stack(self):
        self._undo_stack.append(self.text)
        self._redo_stack.clear()
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
    
    def undo(self):
        if self._undo_stack:
            self._redo_stack.append(self.text)
            self.text = self._undo_stack.pop()
            self._update_text_buffer()
            self._scroll_to_cursor()
    
    def redo(self):
        if self._redo_stack:
            self._undo_stack.append(self.text)
            self.text = self._redo_stack.pop()
            self._update_text_buffer()
            self._scroll_to_cursor()
    
    def _get_visible_lines(self) -> List[int]:
        start_line = self.scroll_y // self.line_height
        visible_lines = self.text_area_height // self.line_height + 1
        end_line = min(len(self.lines), start_line + visible_lines)
        return list(range(start_line, end_line))
    
    def _get_cursor_screen_pos(self) -> Tuple[int, int]:
        line_y = self.text_area_y + (self.cursor_line * self.line_height) - self.scroll_y
        
        line_before_cursor = self.lines[self.cursor_line][:self.cursor_column]
        column_x = 0
        for char in line_before_cursor:
            if char == '\t':
                column_x += self.tab_size * self.char_width
            else:
                column_x += self.char_width
        
        column_x = self.text_area_x + column_x - self.scroll_x
        
        return column_x, line_y
    
    def _scroll_to_cursor(self):
        cursor_x, cursor_y = self._get_cursor_screen_pos()
        
        visible_x1 = self.text_area_x
        visible_x2 = self.text_area_x + self.text_area_width
        visible_y1 = self.text_area_y
        visible_y2 = self.text_area_y + self.text_area_height
        
        if cursor_x < visible_x1:
            self.scroll_x -= (visible_x1 - cursor_x)
        elif cursor_x > visible_x2 - self.char_width:
            self.scroll_x += (cursor_x - (visible_x2 - self.char_width))
        
        if cursor_y < visible_y1:
            self.scroll_y -= (visible_y1 - cursor_y)
        elif cursor_y + self.line_height > visible_y2:
            self.scroll_y += (cursor_y + self.line_height - visible_y2)
        
        self.scroll_x = max(0, self.scroll_x)
        max_scroll_y = max(0, len(self.lines) * self.line_height - self.text_area_height)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll_y))
    
    def _insert_text(self, text: str):
        if self.read_only:
            return
        
        self._save_to_undo_stack()
        text = text.replace('\t', ' ' * self.tab_size)
        
        current_line = self.lines[self.cursor_line]
        new_line = current_line[:self.cursor_column] + text + current_line[self.cursor_column:]
        
        if '\n' in text:
            lines = text.split('\n')
            self.lines[self.cursor_line] = current_line[:self.cursor_column] + lines[0]
            for i in range(1, len(lines)):
                self.lines.insert(self.cursor_line + i, lines[i])
            if current_line[self.cursor_column:]:
                self.lines[self.cursor_line + len(lines) - 1] += current_line[self.cursor_column:]
            self.cursor_line += len(lines) - 1
            self.cursor_column = len(lines[-1])
        else:
            self.lines[self.cursor_line] = new_line
            self.cursor_column += len(text)
        
        self.text = '\n'.join(self.lines)
        self._scroll_to_cursor()
    
    def _delete_selection(self):
        if not self.selection_start or not self.selection_end:
            return
        
        start_line, start_col = self.selection_start
        end_line, end_col = self.selection_end
        
        if (end_line < start_line) or (end_line == start_line and end_col < start_col):
            start_line, start_col, end_line, end_col = end_line, end_col, start_line, start_col
        
        self._save_to_undo_stack()
        
        if start_line == end_line:
            line = self.lines[start_line]
            self.lines[start_line] = line[:start_col] + line[end_col:]
        else:
            first_part = self.lines[start_line][:start_col]
            last_part = self.lines[end_line][end_col:]
            self.lines[start_line] = first_part + last_part
            del self.lines[start_line + 1:end_line + 1]
        
        self.cursor_line = start_line
        self.cursor_column = start_col
        self.selection_start = None
        self.selection_end = None
        
        self.text = '\n'.join(self.lines)
        self._scroll_to_cursor()
    
    def _get_selection_text(self) -> str:
        if not self.selection_start or not self.selection_end:
            return ""
        
        start_line, start_col = self.selection_start
        end_line, end_col = self.selection_end
        
        if (end_line < start_line) or (end_line == start_line and end_col < start_col):
            start_line, start_col, end_line, end_col = end_line, end_col, start_line, start_col
        
        if start_line == end_line:
            return self.lines[start_line][start_col:end_col]
        else:
            result = []
            result.append(self.lines[start_line][start_col:])
            for line_num in range(start_line + 1, end_line):
                result.append(self.lines[line_num])
            result.append(self.lines[end_line][:end_col])
            return '\n'.join(result)
    
    def copy(self):
        if self.selection_start and self.selection_end:
            self._clipboard = self._get_selection_text()
    
    def cut(self):
        if self.selection_start and self.selection_end:
            self._clipboard = self._get_selection_text()
            self._delete_selection()
    
    def paste(self):
        if self._clipboard:
            self._insert_text(self._clipboard)
    
    def select_all(self):
        self.selection_start = (0, 0)
        self.selection_end = (len(self.lines) - 1, len(self.lines[-1]))
    
    def _move_cursor(self, line_delta: int, column_delta: int, extend_selection: bool = False):
        if not extend_selection:
            self.selection_start = None
            self.selection_end = None
        elif self.selection_start is None:
            self.selection_start = (self.cursor_line, self.cursor_column)
        
        new_line = max(0, min(len(self.lines) - 1, self.cursor_line + line_delta))
        
        if column_delta != 0:
            current_line = self.lines[new_line]
            new_column = max(0, min(len(current_line), self.cursor_column + column_delta))
            self.cursor_column = new_column
        
        self.cursor_line = new_line
        
        if extend_selection:
            self.selection_end = (self.cursor_line, self.cursor_column)
        
        self._scroll_to_cursor()
    
    def update(self, dt: float, inputState: InputState):
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
            else:
                self.focused = False
        
        if self._dragging and inputState.mouse_buttons_pressed.left:
            drag_end_pos = self._get_cursor_from_mouse(inputState.mouse_pos)
            self.selection_end = drag_end_pos
            self.cursor_line, self.cursor_column = drag_end_pos
        elif not inputState.mouse_buttons_pressed.left:
            self._dragging = False
        
        if self.focused:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.cursor_visible = not self.cursor_visible
    
    def on_key_down(self, event: pygame.event.Event):
        if not self.focused or event.type != pygame.KEYDOWN:
            return
        pass
    
    def on_key_up(self, event: pygame.event.Event):
        if not self.focused or event.type != pygame.KEYUP:
            return
        self.handle_key_event(event)    

    def _get_cursor_from_mouse(self, mouse_pos: Tuple[int, int]) -> Tuple[int, int]:
        actual_x, actual_y = self.get_actual_position()
        rel_x = mouse_pos[0] - actual_x - self.text_area_x + self.scroll_x
        rel_y = mouse_pos[1] - actual_y - self.text_area_y + self.scroll_y
        
        line = min(len(self.lines) - 1, max(0, rel_y // self.line_height))
        
        line_text = self.lines[line]
        column = 0
        current_x = 0
        
        for char in line_text:
            char_width = self.tab_size * self.char_width if char == '\t' else self.char_width
            if current_x + char_width / 2 > rel_x:
                break
            current_x += char_width
            column += 1
        
        return line, column
    
    def handle_key_event(self, event):
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_BACKSPACE:
                if self.selection_start and self.selection_end:
                    self._delete_selection()
                elif self.cursor_column > 0:
                    self._save_to_undo_stack()
                    line = self.lines[self.cursor_line]
                    self.lines[self.cursor_line] = line[:self.cursor_column - 1] + line[self.cursor_column:]
                    self.cursor_column -= 1
                    self.text = '\n'.join(self.lines)
                    self._scroll_to_cursor()
                elif self.cursor_line > 0:
                    self._save_to_undo_stack()
                    prev_line = self.lines[self.cursor_line - 1]
                    current_line = self.lines[self.cursor_line]
                    self.lines[self.cursor_line - 1] = prev_line + current_line
                    del self.lines[self.cursor_line]
                    self.cursor_line -= 1
                    self.cursor_column = len(prev_line)
                    self.text = '\n'.join(self.lines)
                    self._scroll_to_cursor()
            
            elif event.key == pygame.K_DELETE:
                if self.selection_start and self.selection_end:
                    self._delete_selection()
                elif self.cursor_column < len(self.lines[self.cursor_line]):
                    self._save_to_undo_stack()
                    line = self.lines[self.cursor_line]
                    self.lines[self.cursor_line] = line[:self.cursor_column] + line[self.cursor_column + 1:]
                    self.text = '\n'.join(self.lines)
                elif self.cursor_line < len(self.lines) - 1:
                    self._save_to_undo_stack()
                    current_line = self.lines[self.cursor_line]
                    next_line = self.lines[self.cursor_line + 1]
                    self.lines[self.cursor_line] = current_line + next_line
                    del self.lines[self.cursor_line + 1]
                    self.text = '\n'.join(self.lines)
                    self._scroll_to_cursor()
            
            elif event.key == pygame.K_RETURN:
                self._insert_text('\n')
            
            elif event.key == pygame.K_TAB:
                self._insert_text(' ' * self.tab_size)
            
            elif event.key == pygame.K_LEFT:
                extend = pygame.key.get_mods() & pygame.KMOD_SHIFT
                if self.cursor_column > 0:
                    self._move_cursor(0, -1, extend)
                elif self.cursor_line > 0:
                    self.cursor_line -= 1
                    self.cursor_column = len(self.lines[self.cursor_line])
                    self._scroll_to_cursor()
            
            elif event.key == pygame.K_RIGHT:
                extend = pygame.key.get_mods() & pygame.KMOD_SHIFT
                if self.cursor_column < len(self.lines[self.cursor_line]):
                    self._move_cursor(0, 1, extend)
                elif self.cursor_line < len(self.lines) - 1:
                    self.cursor_line += 1
                    self.cursor_column = 0
                    self._scroll_to_cursor()
            
            elif event.key == pygame.K_UP:
                extend = pygame.key.get_mods() & pygame.KMOD_SHIFT
                self._move_cursor(-1, 0, extend)
            
            elif event.key == pygame.K_DOWN:
                extend = pygame.key.get_mods() & pygame.KMOD_SHIFT
                self._move_cursor(1, 0, extend)
            
            elif event.key == pygame.K_HOME:
                extend = pygame.key.get_mods() & pygame.KMOD_SHIFT
                self.cursor_column = 0
                if extend:
                    self.selection_end = (self.cursor_line, self.cursor_column)
                else:
                    self.selection_start = None
                    self.selection_end = None
                self._scroll_to_cursor()
            
            elif event.key == pygame.K_END:
                extend = pygame.key.get_mods() & pygame.KMOD_SHIFT
                self.cursor_column = len(self.lines[self.cursor_line])
                if extend:
                    self.selection_end = (self.cursor_line, self.cursor_column)
                else:
                    self.selection_start = None
                    self.selection_end = None
                self._scroll_to_cursor()
            
            elif event.key == pygame.K_PAGEUP:
                visible_lines = self.text_area_height // self.line_height
                self._move_cursor(-visible_lines, 0, False)
            
            elif event.key == pygame.K_PAGEDOWN:
                visible_lines = self.text_area_height // self.line_height
                self._move_cursor(visible_lines, 0, False)
            
            elif pygame.key.get_mods() & pygame.KMOD_CTRL:
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
            elif self.focused and not self.read_only:
                self._insert_text(event.unicode)
        elif event.type == pygame.TEXTINPUT and self.focused and not self.read_only:
            self._insert_text(event.text)
    
    def render(self, renderer: Renderer):
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        border_color = theme.button_border.color if (self.focused and theme.button_border) else (theme.border.color if theme.border else (120, 120, 140))
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           border_color, fill=False, border_width=self.border_width)
        
        bg_color = theme.background.color if self.focused else (theme.button_disabled.color if theme.button_disabled else (100, 100, 100))
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           bg_color, fill=True, border_width=self.border_width)
        
        if hasattr(renderer, 'enable_scissor'):
            renderer.enable_scissor(actual_x, actual_y, self.width, self.height)
        
        if self.line_numbers:
            visible_lines = self._get_visible_lines()
            for line_num in visible_lines:
                line_y = actual_y + (line_num * self.line_height) - self.scroll_y
                number_text = str(line_num + 1)
                number_x = actual_x + self.line_number_width - self.line_number_padding - self.font.size(number_text)[0]
                renderer.draw_text(number_text, number_x, line_y, theme.text_secondary.color, self.font)
            
            separator_x = actual_x + self.line_number_width - 1
            renderer.draw_rect(separator_x, actual_y, 1, self.height,
                               theme.border.color, fill=True, border_width=0)
        
        visible_lines = self._get_visible_lines()
        for line_num in visible_lines:
            if line_num < len(self.lines):
                line_text = self.lines[line_num]
                line_y = actual_y + (line_num * self.line_height) - self.scroll_y
                text_x = actual_x + self.text_area_x - self.scroll_x
                
                if self.selection_start and self.selection_end:
                    self._draw_selection_highlight(renderer, actual_x, actual_y, line_num, line_y)
                
                renderer.draw_text(line_text, text_x, line_y, theme.text_primary.color, self.font)
        
        if self.focused and self.cursor_visible:
            cursor_x, cursor_y = self._get_cursor_screen_pos()
            cursor_actual_x = actual_x + cursor_x
            cursor_actual_y = actual_y + cursor_y
            renderer.draw_rect(cursor_actual_x, cursor_actual_y, 2, self.line_height,
                               theme.text_primary.color, fill=True)
        
        if hasattr(renderer, 'disable_scissor'):
            renderer.disable_scissor()
    
    def _draw_selection_highlight(self, renderer: Renderer, actual_x: int, actual_y: int,
                                 line_num: int, line_y: int):
        start_line, start_col = self.selection_start
        end_line, end_col = self.selection_end
        
        if (end_line < start_line) or (end_line == start_line and end_col < start_col):
            start_line, start_col, end_line, end_col = end_line, end_col, start_line, start_col
        
        if line_num < start_line or line_num > end_line:
            return
        
        highlight_color = (100, 150, 255, 100)
        
        if line_num == start_line and line_num == end_line:
            sel_start_col = start_col
            sel_end_col = end_col
        elif line_num == start_line:
            sel_start_col = start_col
            sel_end_col = len(self.lines[line_num])
        elif line_num == end_line:
            sel_start_col = 0
            sel_end_col = end_col
        else:
            sel_start_col = 0
            sel_end_col = len(self.lines[line_num])
        
        text_before_start = self.lines[line_num][:sel_start_col]
        text_before_end = self.lines[line_num][:sel_end_col]
        
        start_x = self._calculate_text_width(text_before_start)
        end_x = self._calculate_text_width(text_before_end)
        
        highlight_x = actual_x + self.text_area_x + start_x - self.scroll_x
        highlight_width = end_x - start_x
        
        if highlight_width > 0:
            renderer.draw_rect(highlight_x, actual_y + line_y, highlight_width, self.line_height,
                               highlight_color, fill=True)
    
    def _calculate_text_width(self, text: str) -> int:
        width = 0
        for char in text:
            if char == '\t':
                width += self.tab_size * self.char_width
            else:
                width += self.char_width
        return width