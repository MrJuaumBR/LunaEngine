# containers.py
import pygame
import os
from typing import Optional, List, Tuple, Union, Literal
from .base import *
from .buttons import Button
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
from ...backend.types import InputState
from ...backend.opengl import OpenGLRenderer
from .labels import TextLabel


class UiFrame(UIElement):
    """
    A container frame that can have an optional draggable header with title and icon.
    """

    _properties = {
        **UIElement._properties,
        'header_enabled': {'name': 'header enabled', 'key': 'header_enabled', 'type': bool, 'editable': True,
                           'description': 'Show header bar with title/icon'},
        'header_title': {'name': 'header title', 'key': 'header_title', 'type': str, 'editable': True,
                         'description': 'Text displayed in header'},
        'header_height': {'name': 'header height', 'key': 'header_height', 'type': int, 'editable': True,
                          'description': 'Height of header bar in pixels'},
        'draggable': {'name': 'draggable', 'key': 'draggable', 'type': bool, 'editable': True,
                      'description': 'Allow frame to be dragged by its header'},
        'padding': {'name': 'padding', 'key': 'padding', 'type': int, 'editable': True,
                    'description': 'Padding inside frame'},
        'background_color': {'name': 'background color', 'key': 'background_color', 'type': tuple, 'editable': True,
                             'description': 'RGB background color (None = transparent)'},
        'border_color': {'name': 'border color', 'key': 'border_color', 'type': tuple, 'editable': True,
                         'description': 'RGB border color (None = no border)'},
        'corner_radius': {'name': 'corner radius', 'key': 'corner_radius', 'type': (int, tuple), 'editable': True,
                          'description': 'Radius for rounded corners'},
    }

    def __init__(self, x: int, y: int, width: int, height: int,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None,
                 header_enabled: bool = False,
                 header_title: str = "",
                 header_icon: Optional[Union[str, pygame.Surface]] = None,
                 header_height: int = 30,
                 draggable: bool = False,
                 **kwargs):
        super().__init__(x, y, width, height, root_point, element_id)

        self.theme_type = theme or ThemeManager.get_current_theme()
        self.background_color = kwargs.get('background_color', None)
        self.border_color = kwargs.get('border_color', None)
        self.border_width = kwargs.get('border_width', 1)
        self.padding = kwargs.get('padding', 5)
        self.corner_radius = kwargs.get('corner_radius', 0)

        self.header_enabled = header_enabled
        self.header_title = header_title
        self.header_height = header_height if header_enabled else 0
        self.draggable = draggable and header_enabled

        self.header_icon = None
        if header_icon and header_enabled:
            if isinstance(header_icon, str) and os.path.exists(header_icon):
                self.header_icon = pygame.image.load(header_icon).convert_alpha()
            elif isinstance(header_icon, pygame.Surface):
                self.header_icon = header_icon

        self._dragging = False
        self._drag_start_mouse = (0, 0)
        self._drag_start_pos = (self.x, self.y)
        self._header_font = None

    @property
    def header_font(self):
        if self._header_font is None and self.header_enabled:
            FontManager.initialize()
            self._header_font = FontManager.get_font(None, int(self.header_height * 0.6))
        return self._header_font

    @property
    def usable_space(self) -> Tuple[int, int]:
        usable_w = self.width - (self.padding * 2)
        usable_h = self.height - (self.padding * 2) - self.header_height
        return (usable_w, usable_h)

    def get_header_rect(self) -> pygame.Rect:
        actual_x, actual_y = self.get_actual_position()
        return pygame.Rect(actual_x, actual_y, self.width, self.header_height)

    def set_background_color(self, color: Optional[Tuple[int, int, int]]):
        self.background_color = color

    def set_border_color(self, color: Optional[Tuple[int, int, int]]):
        self.border_color = color

    def set_border(self, color: Optional[Tuple[int, int, int]], width: int = 1):
        self.border_color = color
        self.border_width = width

    def set_padding(self, padding: int):
        self.padding = padding

    def set_corner_radius(self, radius: Union[int, Tuple[int, int, int, int]]):
        self.corner_radius = radius

    def get_content_rect(self) -> Tuple[int, int, int, int]:
        actual_x, actual_y = self.get_actual_position()
        content_x = actual_x + self.padding
        content_y = actual_y + self.header_height + self.padding
        content_w = self.width - (self.padding * 2)
        content_h = self.height - self.header_height - (self.padding * 2)
        return (content_x, content_y, content_w, content_h)

    def update_theme(self, theme_type: ThemeType):
        self.theme_type = theme_type
        super().update_theme(theme_type)

    def update(self, dt: float, inputState: InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        if self.header_enabled and self.draggable:
            mouse_pos = inputState.mouse_pos
            header_rect = self.get_header_rect()

            if not self._dragging and inputState.mouse_just_pressed:
                if header_rect.collidepoint(mouse_pos):
                    self._dragging = True
                    self._drag_start_mouse = mouse_pos
                    self._drag_start_pos = (self.x, self.y)
                    inputState.consume_global_mouse()

            if self._dragging:
                if inputState.mouse_buttons_pressed.left:
                    dx = mouse_pos[0] - self._drag_start_mouse[0]
                    dy = mouse_pos[1] - self._drag_start_mouse[1]
                    self.x = self._drag_start_pos[0] + dx
                    self.y = self._drag_start_pos[1] + dy
                else:
                    self._dragging = False
                return

        for child in self.children:
            if hasattr(child, 'update'):
                child.update(dt, inputState)

    def render(self, renderer: OpenGLRenderer):
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        # Draw border and background in one call (if background present)
        bg_color = self.background_color or theme.background.color
        border_color = self.border_color or (theme.border.color if theme.border else None)
        if bg_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color,
                               fill=True,
                               border_color=border_color,
                               border_width=self.border_width,
                               corner_radius=self.corner_radius)
        elif border_color:
            # Only border, no fill
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color,
                               fill=False,
                               border_width=self.border_width,
                               corner_radius=self.corner_radius)

        # Header
        if self.header_enabled:
            header_bg = theme.button_normal.color if theme.button_normal else (80, 80, 100)
            renderer.draw_rect(actual_x, actual_y, self.width, self.header_height,
                               header_bg, fill=True,
                               corner_radius=(self.corner_radius, self.corner_radius, 0, 0))

            if self.header_icon:
                icon_h = self.header_height - 6
                icon_w = int(self.header_icon.get_width() * (icon_h / self.header_icon.get_height()))
                icon_scaled = pygame.transform.smoothscale(self.header_icon, (icon_w, icon_h))
                renderer.blit(icon_scaled, (actual_x + 5, actual_y + 3))

            if self.header_title and self.header_font:
                text_color = theme.button_text.color if theme.button_text else (255, 255, 255)
                text_surf = self.header_font.render(self.header_title, True, text_color)
                text_x = actual_x + (self.header_icon.get_width() + 10 if self.header_icon else 5)
                text_y = actual_y + (self.header_height - text_surf.get_height()) // 2
                renderer.blit(text_surf, (text_x, text_y))

        super().render(renderer)

    def arrange_children_vertically(self, spacing: int = 5, align: str = "left"):
        cx, cy, cw, ch = self.get_content_rect()
        current_y = cy
        for child in self.children:
            if align == "center":
                child.x = cx + (cw - child.width) // 2
            elif align == "right":
                child.x = cx + cw - child.width
            else:
                child.x = cx
            child.y = current_y
            child.root_point = (0, 0)
            current_y += child.height + spacing

    def arrange_children_horizontally(self, spacing: int = 5, align: str = "top"):
        cx, cy, cw, ch = self.get_content_rect()
        current_x = cx
        for child in self.children:
            if align == "center":
                child.y = cy + (ch - child.height) // 2
            elif align == "bottom":
                child.y = cy + ch - child.height
            else:
                child.y = cy
            child.x = current_x
            child.root_point = (0, 0)
            current_x += child.width + spacing

    def clear_children(self):
        for child in self.children:
            child.parent = None
        self.children.clear()


class ScrollingFrame(UiFrame):
    _properties = {
        **UiFrame._properties,
        'content_width': {'name': 'content width', 'key': 'content_width', 'type': int, 'editable': True,
                          'description': 'Total width of scrollable content'},
        'content_height': {'name': 'content height', 'key': 'content_height', 'type': int, 'editable': True,
                           'description': 'Total height of scrollable content'},
        'scroll_x': {'name': 'scroll x', 'key': 'scroll_x', 'type': int, 'editable': False,
                     'description': 'Horizontal scroll offset'},
        'scroll_y': {'name': 'scroll y', 'key': 'scroll_y', 'type': int, 'editable': False,
                     'description': 'Vertical scroll offset'},
        'scrollbar_size': {'name': 'scrollbar size', 'key': 'scrollbar_size', 'type': int, 'editable': True,
                           'description': 'Width/height of scrollbars'},
    }

    def __init__(self, x: int, y: int, width: int, height: int,
                 content_width: int, content_height: int,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None,
                 header_enabled: bool = False,
                 header_title: str = "",
                 header_icon: Optional[Union[str, pygame.Surface]] = None,
                 header_height: int = 30,
                 draggable: bool = False,
                 **kwargs):
        super().__init__(x, y, width, height, root_point, theme, element_id,
                         header_enabled, header_title, header_icon, header_height, draggable, **kwargs)

        self.content_width = content_width
        self.content_height = content_height
        self.scroll_x = 0
        self.scroll_y = 0
        self.scrollbar_size = kwargs.get('scrollbar_size', 15)
        self.dragging_vertical = False
        self.dragging_horizontal = False
        self.scroll_drag_start = (0, 0)
        self._background_color_override = None
        self.padding = 0
        
    def clear_content(self, reset_scroll: bool = True):
        self.clear_children()
        if reset_scroll:
            self.scroll_x = 0
            self.scroll_y = 0

    def set_background_color(self, color: Tuple[int, int, int]):
        self._background_color_override = color

    def get_mouse_position(self, input_state) -> Tuple[int, int]:
        x, y = input_state.mouse_pos
        return (x + self.scroll_x, y + self.scroll_y)

    def mouse_over(self, input_state: InputState) -> bool:
        mouse_pos = self.get_mouse_position(input_state)
        return self.getCollideRect().collidepoint(mouse_pos)

    def update(self, dt: float, inputState: InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        super().update(dt, inputState)
        if self._dragging:
            return

        actual_x, actual_y = self.get_actual_position()
        mouse_pos = inputState.mouse_pos
        mouse_pressed = inputState.mouse_buttons_pressed.left

        max_scroll_x = max(0, self.content_width - self.width)
        max_scroll_y = max(0, self.content_height - (self.height - self.header_height))

        if mouse_pressed:
            if not (self.dragging_vertical or self.dragging_horizontal):
                if max_scroll_y > 0:
                    v_rect = self._get_vertical_scrollbar_rect(actual_x, actual_y)
                    if v_rect.collidepoint(mouse_pos):
                        self.dragging_vertical = True
                        self.scroll_drag_start = mouse_pos
                        self.scroll_start_y = self.scroll_y
                if max_scroll_x > 0:
                    h_rect = self._get_horizontal_scrollbar_rect(actual_x, actual_y)
                    if h_rect.collidepoint(mouse_pos):
                        self.dragging_horizontal = True
                        self.scroll_drag_start = mouse_pos
                        self.scroll_start_x = self.scroll_x
        else:
            self.dragging_vertical = False
            self.dragging_horizontal = False

        if self.dragging_vertical and max_scroll_y > 0:
            drag_delta = mouse_pos[1] - self.scroll_drag_start[1]
            scroll_area_h = (self.height - self.header_height) - (self.scrollbar_size if self.content_width > self.width else 0)
            ratio = drag_delta / max(1, scroll_area_h)
            self.scroll_y = max(0, min(max_scroll_y, self.scroll_start_y + int(ratio * max_scroll_y)))
        if self.dragging_horizontal and max_scroll_x > 0:
            drag_delta = mouse_pos[0] - self.scroll_drag_start[0]
            scroll_area_w = self.width - (self.scrollbar_size if self.content_height > self.height - self.header_height else 0)
            ratio = drag_delta / max(1, scroll_area_w)
            self.scroll_x = max(0, min(max_scroll_x, self.scroll_start_x + int(ratio * max_scroll_x)))

        original_mouse = inputState.mouse_pos
        inputState.mouse_pos = (original_mouse[0] + self.scroll_x, original_mouse[1] + self.scroll_y)
        for child in self.children:
            if hasattr(child, 'update'):
                child.update(dt, inputState)
        inputState.mouse_pos = original_mouse

    def on_scroll(self, event: pygame.event.Event):
        if event.type != pygame.MOUSEWHEEL or self.state != UIState.HOVERED or not self.enabled:
            return
        max_scroll_y = max(0, self.content_height - (self.height - self.header_height))
        self.scroll_y = max(0, min(max_scroll_y, self.scroll_y - event.y * 30))
        max_scroll_x = max(0, self.content_width - self.width)
        self.scroll_x = max(0, min(max_scroll_x, self.scroll_x - event.x * 30))

    def render(self, renderer: OpenGLRenderer):
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        # Border and background
        border_color = self.border_color or (theme.border.color if theme.border else None)
        bg_color = self._background_color_override or theme.background.color
        if bg_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color,
                               fill=True,
                               border_color=border_color,
                               border_width=self.border_width,
                               corner_radius=self.corner_radius)
        elif border_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color,
                               fill=False,
                               border_width=self.border_width,
                               corner_radius=self.corner_radius)

        # Header (if enabled)
        if self.header_enabled:
            header_bg = theme.button_normal.color if theme.button_normal else (80, 80, 100)
            renderer.draw_rect(actual_x, actual_y, self.width, self.header_height,
                               header_bg, fill=True,
                               corner_radius=(self.corner_radius, self.corner_radius, 0, 0))
            if self.header_icon:
                icon_h = self.header_height - 6
                icon_w = int(self.header_icon.get_width() * (icon_h / self.header_icon.get_height()))
                icon_scaled = pygame.transform.smoothscale(self.header_icon, (icon_w, icon_h))
                renderer.blit(icon_scaled, (actual_x + 5, actual_y + 3))
            if self.header_title and self.header_font:
                text_color = theme.button_text.color if theme.button_text else (255, 255, 255)
                text_surf = self.header_font.render(self.header_title, True, text_color)
                text_x = actual_x + (self.header_icon.get_width() + 10 if self.header_icon else 5)
                text_y = actual_y + (self.header_height - text_surf.get_height()) // 2
                renderer.blit(text_surf, (text_x, text_y))

        content_top = actual_y + self.header_height
        content_height = self.height - self.header_height
        if hasattr(renderer, 'enable_scissor'):
            renderer.enable_scissor(actual_x, content_top, self.width, content_height)

        for child in self.children:
            orig_x, orig_y = child.x, child.y
            child.x -= self.scroll_x
            child.y -= self.scroll_y
            child.render(renderer)
            child.x, child.y = orig_x, orig_y

        if hasattr(renderer, 'disable_scissor'):
            renderer.disable_scissor()

        if self.content_width > self.width:
            self._draw_horizontal_scrollbar(renderer, actual_x, content_top, theme)
        if self.content_height > content_height:
            self._draw_vertical_scrollbar(renderer, actual_x, content_top, theme)

    def _get_vertical_scrollbar_rect(self, fx: int, fy: int) -> pygame.Rect:
        if self.content_height <= self.height - self.header_height:
            return pygame.Rect(0, 0, 0, 0)
        sb_w = self.scrollbar_size
        sb_h = self.height - self.header_height - (self.scrollbar_size if self.content_width > self.width else 0)
        sb_x = fx + self.width - sb_w
        sb_y = fy + self.header_height
        max_scroll = max(1, self.content_height - (self.height - self.header_height))
        thumb_h = max(20, int(((self.height - self.header_height) / self.content_height) * sb_h))
        avail = sb_h - thumb_h
        ratio = self.scroll_y / max_scroll
        thumb_y = sb_y + int(ratio * avail)
        return pygame.Rect(sb_x, thumb_y, sb_w, thumb_h)

    def _get_horizontal_scrollbar_rect(self, fx: int, fy: int) -> pygame.Rect:
        if self.content_width <= self.width:
            return pygame.Rect(0, 0, 0, 0)
        sb_w = self.width - (self.scrollbar_size if self.content_height > self.height - self.header_height else 0)
        sb_h = self.scrollbar_size
        sb_x = fx
        sb_y = fy + self.header_height + (self.height - self.header_height) - sb_h
        max_scroll = max(1, self.content_width - self.width)
        thumb_w = max(20, int((self.width / self.content_width) * sb_w))
        avail = sb_w - thumb_w
        ratio = self.scroll_x / max_scroll
        thumb_x = sb_x + int(ratio * avail)
        return pygame.Rect(thumb_x, sb_y, thumb_w, sb_h)

    def _draw_horizontal_scrollbar(self, renderer, fx: int, fy: int, theme):
        sb_w = self.width - (self.scrollbar_size if self.content_height > self.height - self.header_height else 0)
        sb_h = self.scrollbar_size
        sb_x = fx
        sb_y = fy + (self.height - self.header_height) - sb_h
        renderer.draw_rect(sb_x, sb_y, sb_w, sb_h, theme.slider_track.color, fill=True)
        thumb = self._get_horizontal_scrollbar_rect(fx, fy)
        color = theme.slider_thumb_pressed.color if self.dragging_horizontal else theme.slider_thumb_normal.color
        renderer.draw_rect(thumb.x, thumb.y, thumb.width, thumb.height, color, fill=True)

    def _draw_vertical_scrollbar(self, renderer, fx: int, fy: int, theme):
        sb_w = self.scrollbar_size
        sb_h = self.height - self.header_height - (self.scrollbar_size if self.content_width > self.width else 0)
        sb_x = fx + self.width - sb_w
        sb_y = fy
        renderer.draw_rect(sb_x, sb_y, sb_w, sb_h, theme.slider_track.color, fill=True)
        thumb = self._get_vertical_scrollbar_rect(fx, fy)
        color = theme.slider_thumb_pressed.color if self.dragging_vertical else theme.slider_thumb_normal.color
        renderer.draw_rect(thumb.x, thumb.y, thumb.width, thumb.height, color, fill=True)


class Tabination(UiFrame):
    _properties = {
        **UiFrame._properties,
        'orientation': {'name': 'orientation', 'key': 'orientation', 'type': str, 'editable': True,
                        'description': 'Tab layout: horizontal, vertical1, vertical2'},
        'tab_height': {'name': 'tab height', 'key': 'tab_height', 'type': int, 'editable': True,
                       'description': 'Height of each tab (vertical) or tab bar (horizontal)'},
        'tab_width': {'name': 'tab width', 'key': 'tab_width', 'type': int, 'editable': True,
                      'description': 'Width of each tab (horizontal) or tab bar (vertical)'},
        'current_tab': {'name': 'current tab', 'key': 'current_tab', 'type': int, 'editable': False,
                        'description': 'Index of active tab'},
    }

    def __init__(self, x: int, y: int, width: int, height: int,
                 font_size: int = 20, font_name: Optional[str] = None,
                 orientation: Literal['horizontal', 'vertical1', 'vertical2'] = 'horizontal',
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None,
                 **kwargs):
        super().__init__(x, y, width, height, root_point, theme, element_id)

        self.orientation = orientation
        self.tabs = []
        self.current_tab = None

        if orientation == 'horizontal':
            default_tab_height = 30
            default_tab_width = 100
        else:
            default_tab_height = 80
            default_tab_width = 120

        self.tab_height = kwargs.get('tab_height', default_tab_height)
        self.tab_width = kwargs.get('tab_width', default_tab_width)
        self.font_size = font_size
        self.font_name = font_name
        self.tab_padding = 10
        self.tab_spacing = 2

        self._font = None
        self._even_tab_bg = None
        self._odd_tab_bg = None
        self._calculate_tab_colors()

        self._scroll_offset = 0
        self._scroll_speed = 30
        self._total_tab_size = 0
        self._show_prev_arrow = False
        self._show_next_arrow = False
        self._prev_arrow_hover = False
        self._next_arrow_hover = False
        self._arrow_size = 20
        self.padding = 0

    def _calculate_tab_colors(self):
        theme = ThemeManager.get_theme(self.theme_type)
        base = theme.button_normal.color if theme.button_normal else (100, 100, 100)
        self._even_tab_bg = tuple(min(255, c + 20) for c in base)
        self._odd_tab_bg = tuple(max(0, c - 10) for c in base)

    @property
    def font(self):
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def update_theme(self, theme_type):
        super().update_theme(theme_type)
        self._calculate_tab_colors()
        for tab in self.tabs:
            tab['frame'].update_theme(theme_type)

    def add_tab(self, tab_name: str, icon: Optional[Union[str, pygame.Surface]] = None) -> bool:
        for tab in self.tabs:
            if tab['name'].lower() == tab_name.lower():
                return False

        icon_surface = None
        if icon:
            if isinstance(icon, str) and os.path.exists(icon):
                icon_surface = pygame.image.load(icon).convert_alpha()
            elif isinstance(icon, pygame.Surface):
                icon_surface = icon

        if self.orientation == 'horizontal':
            cx, cy, cw, ch = 0, self.tab_height, self.width, self.height - self.tab_height
        else:
            cx, cy, cw, ch = self.tab_width, 0, self.width - self.tab_width, self.height

        tab_frame = UiFrame(cx, cy, cw, ch, theme=self.theme_type)
        tab_frame.visible = False
        super().add_child(tab_frame)

        self.tabs.append({
            'name': tab_name,
            'frame': tab_frame,
            'icon': icon_surface,
            'visible': False
        })

        if self.current_tab is None:
            self.current_tab = 0
            self.tabs[0]['visible'] = True
            self.tabs[0]['frame'].visible = True

        self._update_tab_scroll()
        return True

    def add_to_tab(self, tab_name: str, ui_element: UIElement) -> bool:
        for tab in self.tabs:
            if tab['name'].lower() == tab_name.lower():
                tab['frame'].add_child(ui_element)
                return True
        return False

    def switch_tab(self, tab_index: int) -> bool:
        if tab_index < 0 or tab_index >= len(self.tabs):
            return False
        if self.current_tab is not None:
            self.tabs[self.current_tab]['visible'] = False
            self.tabs[self.current_tab]['frame'].visible = False
        self.current_tab = tab_index
        self.tabs[tab_index]['visible'] = True
        self.tabs[tab_index]['frame'].visible = True
        return True

    def get_tab_index(self, tab_name: str) -> int:
        for i, tab in enumerate(self.tabs):
            if tab['name'].lower() == tab_name.lower():
                return i
        return -1

    def remove_tab(self, tab_name: str) -> bool:
        idx = self.get_tab_index(tab_name)
        if idx == -1:
            return False
        if idx == self.current_tab:
            if len(self.tabs) > 1:
                new_idx = 0 if idx != 0 else 1
                self.switch_tab(new_idx)
            else:
                self.current_tab = None
        tab_frame = self.tabs[idx]['frame']
        if tab_frame in self.children:
            self.children.remove(tab_frame)
        self.tabs.pop(idx)
        if self.current_tab is not None and self.current_tab >= len(self.tabs):
            self.current_tab = len(self.tabs) - 1
        self._update_tab_scroll()
        return True

    def _update_tab_scroll(self):
        if not self.tabs:
            return
        if self.orientation == 'horizontal':
            tab_size = self._get_tab_width()
            total = len(self.tabs) * (tab_size + self.tab_spacing) - self.tab_spacing
            self._total_tab_size = total
            max_scroll = max(0, total - self.width)
            self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))
            self._show_prev_arrow = self._scroll_offset > 0
            self._show_next_arrow = self._scroll_offset < max_scroll
        else:
            tab_heights = [self._get_tab_height_for_name(tab['name']) for tab in self.tabs]
            total = sum(tab_heights) + (len(self.tabs) - 1) * self.tab_spacing
            self._total_tab_size = total
            max_scroll = max(0, total - self.height)
            self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))
            self._show_prev_arrow = self._scroll_offset > 0
            self._show_next_arrow = self._scroll_offset < max_scroll

    def _get_tab_width(self) -> int:
        if not self.tabs:
            return 0
        max_text = max(self.font.size(tab['name'])[0] for tab in self.tabs)
        max_icon = 0
        for tab in self.tabs:
            if tab['icon']:
                max_icon = max(max_icon, tab['icon'].get_width())
        return max_text + max_icon + self.tab_padding * 2 + 10

    def _get_tab_height_for_name(self, tab_name: str) -> int:
        text_h = self.font.size(tab_name)[1]
        icon_h = 0
        for tab in self.tabs:
            if tab['name'] == tab_name and tab['icon']:
                icon_h = tab['icon'].get_height()
                max_icon_w = self.tab_width - 8
                if icon_h > 0:
                    scale = max_icon_w / tab['icon'].get_width()
                    icon_h = int(icon_h * scale)
                break
        content_h = max(text_h, icon_h) + self.tab_padding * 2
        return max(content_h, self.tab_height)

    def _get_tab_rect(self, idx: int, fx: int, fy: int) -> pygame.Rect:
        if self.orientation == 'horizontal':
            tab_w = self._get_tab_width()
            x = fx + idx * (tab_w + self.tab_spacing) - self._scroll_offset
            y = fy
            w, h = tab_w, self.tab_height
        else:
            y = fy
            for i in range(idx):
                y += self._get_tab_height_for_name(self.tabs[i]['name']) + self.tab_spacing
            y -= self._scroll_offset
            x = fx
            h = self._get_tab_height_for_name(self.tabs[idx]['name'])
            w = self.tab_width
        return pygame.Rect(x, y, w, h)

    def _draw_arrow(self, renderer, x: int, y: int, direction: str, hover: bool):
        theme = ThemeManager.get_theme(self.theme_type)
        color = theme.button_hover.color if hover else theme.button_normal.color
        renderer.draw_rect(x, y, self._arrow_size, self._arrow_size, color, fill=True, corner_radius=4)
        cx = x + self._arrow_size // 2
        cy = y + self._arrow_size // 2
        if direction == 'prev':
            pts = [(cx + 4, cy - 5), (cx - 4, cy), (cx + 4, cy + 5)]
        else:
            pts = [(cx - 4, cy - 5), (cx + 4, cy), (cx - 4, cy + 5)]
        renderer.draw_polygon(pts, theme.button_text.color)

    def update(self, dt: float, inputState: InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        actual_x, actual_y = self.get_actual_position()
        mouse_pos = inputState.mouse_pos
        mouse_pressed = inputState.mouse_buttons_pressed.left

        self._prev_arrow_hover = False
        self._next_arrow_hover = False
        if self._show_prev_arrow:
            if self.orientation == 'horizontal':
                arrow_rect = pygame.Rect(actual_x, actual_y, self._arrow_size, self.tab_height)
            else:
                arrow_rect = pygame.Rect(actual_x, actual_y, self.tab_width, self._arrow_size)
            if arrow_rect.collidepoint(mouse_pos):
                self._prev_arrow_hover = True
                if mouse_pressed:
                    self._scroll_offset = max(0, self._scroll_offset - self._scroll_speed)
                    self._update_tab_scroll()
        if self._show_next_arrow:
            if self.orientation == 'horizontal':
                arrow_rect = pygame.Rect(actual_x + self.width - self._arrow_size,
                                         actual_y, self._arrow_size, self.tab_height)
            else:
                arrow_rect = pygame.Rect(actual_x, actual_y + self.height - self._arrow_size,
                                         self.tab_width, self._arrow_size)
            if arrow_rect.collidepoint(mouse_pos):
                self._next_arrow_hover = True
                if mouse_pressed:
                    max_scroll = max(0, self._total_tab_size - self._get_visible_size())
                    self._scroll_offset = min(max_scroll, self._scroll_offset + self._scroll_speed)
                    self._update_tab_scroll()

        if mouse_pressed and not (self._prev_arrow_hover or self._next_arrow_hover):
            for i, tab in enumerate(self.tabs):
                rect = self._get_tab_rect(i, actual_x, actual_y)
                if rect.collidepoint(mouse_pos):
                    if i != self.current_tab:
                        self.switch_tab(i)
                    break

        tab_area = self._get_tab_area_rect(actual_x, actual_y)
        if tab_area.collidepoint(mouse_pos) and inputState.mouse_wheel != 0:
            delta = -inputState.mouse_wheel * self._scroll_speed
            max_scroll = max(0, self._total_tab_size - self._get_visible_size())
            self._scroll_offset = max(0, min(max_scroll, self._scroll_offset + delta))
            self._update_tab_scroll()

        if self.current_tab is not None:
            self.tabs[self.current_tab]['frame'].update(dt, inputState)

    def _get_visible_size(self) -> int:
        if self.orientation == 'horizontal':
            return self.width
        else:
            return self.height

    def _get_tab_area_rect(self, fx: int, fy: int) -> pygame.Rect:
        if self.orientation == 'horizontal':
            return pygame.Rect(fx, fy, self.width, self.tab_height)
        else:
            return pygame.Rect(fx, fy, self.tab_width, self.height)

    def render(self, renderer: OpenGLRenderer):
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        # Draw border and background
        bg_color = self.background_color or theme.background.color
        border_color = self.border_color or (theme.border.color if theme.border else None)
        if bg_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color,
                               fill=True,
                               border_color=border_color,
                               border_width=self.border_width,
                               corner_radius=self.corner_radius)
        elif border_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height, border_color,
                               fill=False,
                               border_width=self.border_width,
                               corner_radius=self.corner_radius)

        tab_area = self._get_tab_area_rect(actual_x, actual_y)
        renderer.draw_rect(tab_area.x, tab_area.y, tab_area.width, tab_area.height,
                           tuple(min(255, c+20) for c in bg_color), fill=True,
                           corner_radius=self.corner_radius)

        if hasattr(renderer, 'enable_scissor'):
            renderer.enable_scissor(tab_area.x, tab_area.y, tab_area.width, tab_area.height)

        for i, tab in enumerate(self.tabs):
            rect = self._get_tab_rect(i, actual_x, actual_y)
            if self.orientation == 'horizontal':
                if rect.right < tab_area.left or rect.left > tab_area.right:
                    continue
            else:
                if rect.bottom < tab_area.top or rect.top > tab_area.bottom:
                    continue

            is_active = (i == self.current_tab)
            is_hovered = rect.collidepoint(pygame.mouse.get_pos())

            def to_pygame_color(color_val):
                if isinstance(color_val, pygame.Color):
                    return color_val
                if isinstance(color_val, Color):
                    return pygame.Color(color_val.r, color_val.g, color_val.b, int(color_val.a * 255))
                if isinstance(color_val, (tuple, list)):
                    if len(color_val) >= 3:
                        return pygame.Color(int(color_val[0]), int(color_val[1]), int(color_val[2]),
                                            int(color_val[3]) if len(color_val) > 3 else 255)
                return pygame.Color(200, 200, 200)

            if is_active:
                bg = theme.button_normal.color
                text_color_obj = to_pygame_color(theme.button_text.color)
                text_color = (text_color_obj.r, text_color_obj.g, text_color_obj.b)
            elif is_hovered:
                bg = theme.button_hover.color
                text_color_obj = to_pygame_color(theme.button_text.color)
                text_color = (text_color_obj.r, text_color_obj.g, text_color_obj.b)
            else:
                bg = self._even_tab_bg if i % 2 == 0 else self._odd_tab_bg
                base = to_pygame_color(theme.button_text.color)
                text_color = (max(0, base.r - 50), max(0, base.g - 50), max(0, base.b - 50))

            renderer.draw_rect(rect.x, rect.y, rect.width, rect.height, bg, fill=True,
                               corner_radius=self.corner_radius)

            icon_surf = tab['icon']
            text = tab['name']

            if self.orientation == 'horizontal':
                icon_x = rect.x + 5
                icon_y = rect.y + (rect.height - (icon_surf.get_height() if icon_surf else 0)) // 2
                if icon_surf:
                    max_icon_h = rect.height - 8
                    if icon_surf.get_height() > max_icon_h:
                        scale = max_icon_h / icon_surf.get_height()
                        new_w = int(icon_surf.get_width() * scale)
                        new_h = max_icon_h
                        icon_surf = pygame.transform.smoothscale(icon_surf, (new_w, new_h))
                    renderer.blit(icon_surf, (icon_x, icon_y))
                    text_x = icon_x + icon_surf.get_width() + 5
                else:
                    text_x = rect.x + (rect.width - self.font.size(text)[0]) // 2
                text_y = rect.y + (rect.height - self.font.get_height()) // 2
                renderer.draw_text(text, text_x, text_y, text_color,
                                   FontManager.get_font(self.font_name, self.font_size),
                                   anchor_point=(0, 0), rotate=0.0)
            else:
                rotate_angle = -90.0 if self.orientation == 'vertical2' else 0.0
                max_icon_w = rect.width - 12
                if icon_surf and icon_surf.get_width() > max_icon_w:
                    scale = max_icon_w / icon_surf.get_width()
                    new_w = max_icon_w
                    new_h = int(icon_surf.get_height() * scale)
                    icon_surf = pygame.transform.smoothscale(icon_surf, (new_w, new_h))
                if rotate_angle != 0 and icon_surf:
                    icon_surf = pygame.transform.rotate(icon_surf, rotate_angle)
                if icon_surf:
                    icon_x = rect.x + (rect.width - icon_surf.get_width()) // 2
                    icon_y = rect.y + 5
                    renderer.blit(icon_surf, (icon_x, icon_y))
                    text_y = icon_y + icon_surf.get_height() + 5
                else:
                    text_y = rect.y + (rect.height - self.font.get_height()) // 2
                if rotate_angle != 0:
                    text_x = rect.x + rect.width // 2
                    text_y = rect.y + rect.height // 2
                    renderer.draw_text(text, text_x, text_y, text_color,
                                       (self.font_name, self.font_size),
                                       anchor_point=(0.5, 0.5), rotate=rotate_angle)
                else:
                    text_x = rect.x + (rect.width - self.font.size(text)[0]) // 2
                    renderer.draw_text(text, text_x, text_y, text_color,
                                       (self.font_name, self.font_size),
                                       anchor_point=(0, 0), rotate=0.0)

        if hasattr(renderer, 'disable_scissor'):
            renderer.disable_scissor()

        if self._show_prev_arrow:
            if self.orientation == 'horizontal':
                self._draw_arrow(renderer, actual_x, actual_y, 'prev', self._prev_arrow_hover)
            else:
                self._draw_arrow(renderer, actual_x, actual_y, 'prev', self._prev_arrow_hover)
        if self._show_next_arrow:
            if self.orientation == 'horizontal':
                self._draw_arrow(renderer, actual_x + self.width - self._arrow_size,
                                 actual_y, 'next', self._next_arrow_hover)
            else:
                self._draw_arrow(renderer, actual_x, actual_y + self.height - self._arrow_size,
                                 'next', self._next_arrow_hover)

        if self.current_tab is not None:
            self.tabs[self.current_tab]['frame'].render(renderer)


class Pagination(UiFrame):
    def __init__(self, x: int, y: int, width: int, height: int,
                 total_pages: int = 1, current_page: int = 1,
                 max_visible_pages: int = 7,
                 show_prev_next: bool = True, show_first_last: bool = True,
                 button_style: Literal['numbers', 'dots', 'compact'] = 'numbers',
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, theme, element_id)
        
        self.total_pages = max(1, total_pages)
        self.current_page = max(1, min(current_page, self.total_pages))
        self.max_visible_pages = max_visible_pages
        self.show_prev_next = show_prev_next
        self.show_first_last = show_first_last
        self.button_style = button_style
        
        self.button_size = (30, 30)
        self.button_margin = 5
        self.ellipsis_text = "..."
        
        self.on_page_change = None
        
        self._page_buttons = {}
        self._prev_button = None
        self._next_button = None
        self._first_button = None
        self._last_button = None
        
        self._create_buttons()

    def set_page(self, page: int):
        self.set_current_page(page)
    
    def set_total_pages(self, total_pages: int):
        old_total = self.total_pages
        self.total_pages = max(1, total_pages)
        if self.current_page > self.total_pages:
            old_page = self.current_page
            self.current_page = self.total_pages
            self._trigger_page_change(old_page)
        if old_total != self.total_pages:
            self._create_buttons()
    
    def set_current_page(self, page: int):
        if 1 <= page <= self.total_pages and page != self.current_page:
            old_page = self.current_page
            self.current_page = page
            self._update_button_states()
            self._trigger_page_change(old_page)
    
    def next_page(self):
        if self.current_page < self.total_pages:
            self.set_current_page(self.current_page + 1)
    
    def previous_page(self):
        if self.current_page > 1:
            self.set_current_page(self.current_page - 1)
    
    def first_page(self):
        self.set_current_page(1)
    
    def last_page(self):
        self.set_current_page(self.total_pages)
    
    def set_on_page_change(self, callback: Callable[[int, int], None]):
        self.on_page_change = callback
    
    def _trigger_page_change(self, old_page: int):
        if self.on_page_change:
            self.on_page_change(self.current_page, old_page)
    
    def _calculate_visible_pages(self) -> List[int]:
        if self.total_pages <= self.max_visible_pages:
            return list(range(1, self.total_pages + 1))
        
        half_visible = self.max_visible_pages // 2
        start_page = max(1, self.current_page - half_visible)
        end_page = min(self.total_pages, self.current_page + half_visible)
        
        if start_page == 1:
            end_page = min(self.total_pages, self.max_visible_pages)
        elif end_page == self.total_pages:
            start_page = max(1, self.total_pages - self.max_visible_pages + 1)
        
        pages = list(range(start_page, end_page + 1))
        
        if start_page > 1:
            pages.insert(0, 1)
            if start_page > 2:
                pages.insert(1, -1)
        if end_page < self.total_pages:
            if end_page < self.total_pages - 1:
                pages.append(-1)
            pages.append(self.total_pages)
        
        return pages
    
    def _create_buttons(self):
        for btn in list(self._page_buttons.values()):
            self.remove_child(btn)
        self._page_buttons.clear()
        
        if self._prev_button:
            self.remove_child(self._prev_button)
            self._prev_button = None
        if self._next_button:
            self.remove_child(self._next_button)
            self._next_button = None
        if self._first_button:
            self.remove_child(self._first_button)
            self._first_button = None
        if self._last_button:
            self.remove_child(self._last_button)
            self._last_button = None
        
        button_width, button_height = self.button_size
        visible_pages = self._calculate_visible_pages()
        total_buttons = len([p for p in visible_pages if p != -1])
        if self.show_prev_next:
            total_buttons += 2
        if self.show_first_last:
            total_buttons += 2
        
        total_width_needed = total_buttons * button_width + (total_buttons - 1) * self.button_margin
        if total_width_needed > self.width - 20:
            available_width = self.width - 20 - (total_buttons - 1) * self.button_margin
            button_width = max(20, available_width // total_buttons)
            self.button_size = (button_width, self.button_size[1])
        
        current_x = 10
        button_y = (self.height - button_height) // 2
        
        if self.show_first_last:
            self._first_button = Button(current_x, button_y, button_width, button_height,
                                       text="«", font_size=12, theme=self.theme_type)
            self._first_button.set_on_click(self.first_page)
            self.add_child(self._first_button)
            current_x += button_width + self.button_margin
        
        if self.show_prev_next:
            self._prev_button = Button(current_x, button_y, button_width, button_height,
                                      text="‹", font_size=14, theme=self.theme_type)
            self._prev_button.set_on_click(self.previous_page)
            self.add_child(self._prev_button)
            current_x += button_width + self.button_margin
        
        for page_num in visible_pages:
            if page_num == -1:
                ellipsis_label = TextLabel(current_x, button_y + button_height//2 - 8,
                                          self.ellipsis_text, font_size=14,
                                          theme=self.theme_type)
                ellipsis_label.root_point = (0, 0.5)
                self.add_child(ellipsis_label)
                current_x += button_width + self.button_margin
            else:
                btn_text = str(page_num) if self.button_style == 'numbers' else "•"
                btn = Button(current_x, button_y, button_width, button_height,
                            text=btn_text, font_size=14 if self.button_style == 'numbers' else 18,
                            theme=self.theme_type)
                theme_obj = ThemeManager.get_theme(self.theme_type)
                if page_num == self.current_page:
                    btn.set_background_color(theme_obj.button_pressed.color)
                    btn.enabled = False
                btn.set_on_click(lambda p=page_num: self.set_current_page(p))
                self._page_buttons[page_num] = btn
                self.add_child(btn)
                current_x += button_width + self.button_margin
        
        if self.show_prev_next:
            self._next_button = Button(current_x, button_y, button_width, button_height,
                                      text="›", font_size=14, theme=self.theme_type)
            self._next_button.set_on_click(self.next_page)
            self.add_child(self._next_button)
            current_x += button_width + self.button_margin
        
        if self.show_first_last:
            self._last_button = Button(current_x, button_y, button_width, button_height,
                                      text="»", font_size=12, theme=self.theme_type)
            self._last_button.set_on_click(self.last_page)
            self.add_child(self._last_button)
        
        self._update_button_states()
    
    def _update_button_states(self):
        if self._prev_button:
            self._prev_button.enabled = self.current_page > 1
        if self._first_button:
            self._first_button.enabled = self.current_page > 1
        if self._next_button:
            self._next_button.enabled = self.current_page < self.total_pages
        if self._last_button:
            self._last_button.enabled = self.current_page < self.total_pages
        
        theme_obj = ThemeManager.get_theme(self.theme_type)
        for page_num, btn in self._page_buttons.items():
            if page_num == self.current_page:
                btn.set_background_color(theme_obj.button_pressed.color)
                btn.enabled = False
            else:
                btn.set_background_color(theme_obj.button_normal.color)
                btn.enabled = True
    
    def update(self, dt: float, inputState: InputState):
        super().update(dt, inputState)
        self._update_button_states()
    
    def render(self, renderer: Renderer):
        if not self.visible:
            return
        super().render(renderer)


class Expandable(UiFrame):
    _properties = {
        **UiFrame._properties,
        'title': {'name': 'title', 'key': 'title', 'type': str, 'editable': True,
                  'description': 'Header text'},
        'expanded': {'name': 'expanded', 'key': '_expanded', 'type': bool, 'editable': True,
                     'description': 'Whether the panel is expanded'},
        'header_height': {'name': 'header height', 'key': 'header_height', 'type': int, 'editable': False,
                          'description': 'Height of header button'},
        'allow_multiple': {'name': 'allow multiple', 'key': 'allow_multiple', 'type': bool, 'editable': True,
                           'description': 'Allow multiple expanded items in same parent'},
        'accordion_group': {'name': 'accordion group', 'key': 'accordion_group', 'type': str, 'editable': True,
                            'description': 'Group name for accordion behavior'},
    }

    def __init__(self, x: int, y: int, width: int, height: int,
                 title: str = "Expand", expanded: bool = False,
                 allow_multiple: bool = False,
                 accordion_group: str = None,
                 root_point=(0, 0), theme=None, element_id=None):
        super().__init__(x, y, width, 30 if not expanded else 30 + height,
                         root_point, theme, element_id)
        self.header_height = 30
        self._expanded = expanded
        self.allow_multiple = allow_multiple
        self.accordion_group = accordion_group
        self.title = title

        self.content_frame = UiFrame(0, self.header_height, width, height, theme=theme)
        self.content_frame.visible = expanded
        self.add_child(self.content_frame)

        self.setupIcons()

        self.header_button = Button(0, 0, width, self.header_height, title,
                                    theme=theme, root_point=(0, 0))
        self.header_button_icon = self.expanded_icon if expanded else self.collapsed_icon
        self.header_button.set_on_click(self._toggle)
        self.add_child(self.header_button)

    def setupIcons(self):
        self.expanded_icon = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.polygon(self.expanded_icon, ThemeManager.get_color('text_primary'),
                            [(0, 0), (7, 15), (15, 0)])
        self.collapsed_icon = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.polygon(self.collapsed_icon, ThemeManager.get_color('text_primary'),
                            [(0, 0), (0, 15), (15, 7)])

    def _toggle(self):
        if self._expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        if not self.allow_multiple and not self.accordion_group:
            parent = self.parent
            if parent and hasattr(parent, 'children'):
                for child in parent.children:
                    if isinstance(child, Expandable) and child is not self and child._expanded:
                        child.collapse()
        if not self._expanded:
            self._expanded = True
            self.header_button.set_text(f"{self.title}")
            self.content_frame.visible = True
            self.height = self.header_height + self.content_frame.height
            self.content_frame.y = self.header_height
        self.header_button_icon = self.expanded_icon

    def collapse(self):
        if self._expanded:
            self._expanded = False
            self.header_button.set_text(f"{self.title}")
            self.content_frame.visible = False
            self.height = self.header_height
        self.header_button_icon = self.collapsed_icon

    def is_expanded(self) -> bool:
        return self._expanded

    def add_to_content(self, element: UIElement):
        self.content_frame.add_child(element)

    def update(self, dt, inputState):
        if self._expanded:
            self.height = self.header_height + self.content_frame.height
        else:
            self.height = self.header_height
        super().update(dt, inputState)

    def render(self, renderer):
        super().render(renderer)
        if self.header_button_icon:
            x, y = self.header_button.get_actual_position()
            renderer.draw_surface(self.header_button_icon, x + 10, y + 5)