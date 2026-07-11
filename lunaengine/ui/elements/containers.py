# containers.py
import pygame
import os
from typing import Optional, List, Tuple, Union, Literal, Dict, Any, Callable
from dataclasses import dataclass
from .base import *
from .buttons import Button
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
from ...backend.types import InputState
from ...backend.controller import JButton, Axis, FocusOrder
from ...backend.opengl import OpenGLRenderer
from .labels import TextLabel


@dataclass
class _ChildLayoutInfo:
    """Internal layout data for a child UI element under auto-arrange."""
    _OriginalPos:Union[Tuple[int, int], Tuple[float, float]]
    _CurrentPos:Union[Tuple[int, int], Tuple[float, float]]
    _OriginalSize:Union[Tuple[int, int], Tuple[float, float]]
    _CurrentSize:Union[Tuple[int, int], Tuple[float, float]]
    
    @property
    def CurrentPos(self) -> pygame.Vector2:
        return pygame.Vector2(self._CurrentPos)
    
    @property
    def CurrentSize(self) -> pygame.Vector2:
        return pygame.Vector2(self._CurrentSize)
    
    def get_below_elements(self, children: List[UIElement]) -> List[UIElement]:
        below = []
        for child in children:
            if child.visible:
                if (child.y >= self.CurrentPos.y + self.CurrentSize.y) and (child.x >= self.CurrentPos.x or child.x + child.width <= self.CurrentPos.x + self.CurrentSize.x):
                    below.append(child)
        return below


class UiFrame(UIElement):
    """
    A container frame that can have an optional draggable header with title and icon.
    Supports automatic vertical arrangement of children when their sizes change.
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
        'auto_arrange_y': {'name': 'auto arrange y', 'key': 'auto_arrange_y', 'type': bool, 'editable': True,
                           'description': 'Automatically reposition child elements vertically when their heights change'},
        'arrange_spacing': {'name': 'arrange spacing', 'key': 'arrange_spacing', 'type': int, 'editable': True,
                            'description': 'Spacing between arranged children (pixels)'},
        'arrange_align': {'name': 'arrange align', 'key': 'arrange_align', 'type': str, 'editable': True,
                          'description': 'Alignment for arranged children: left, center, right'},
    }
    category:str = 'container'
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None,
        header_enabled: bool = False,
        header_title: str = "",
        header_icon: Optional[Union[str, pygame.Surface]] = None,
        header_height: int = 30,
        draggable: bool = False,
        **kwargs
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)

        self.theme_type = theme or ThemeManager.get_current_theme()
        self.background_color = kwargs.get('background_color', None)
        self.border_color = kwargs.get('border_color', None)
        self.border_width = kwargs.get('border_width', 1)
        self.padding = kwargs.get('padding', 5)
        self.corner_radius = kwargs.get('corner_radius', 0)
        self.auto_arrange_y = kwargs.get('auto_arrange_y', False)
        self.arrange_spacing = kwargs.get('arrange_spacing', 5)
        self.arrange_align = kwargs.get('arrange_align', 'left')

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

        # Auto‑arrangement state
        self._child_layout_data: Dict[UIElement, _ChildLayoutInfo] = {}
        self._needs_rearrange = False

    @property
    def header_font(self) -> Optional[pygame.font.Font]:
        if self._header_font is None and self.header_enabled:
            FontManager.initialize()
            self._header_font = FontManager.get_font(None, int(self.header_height * 0.6))
        return self._header_font

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
            'header_enabled': self.header_enabled,
            'header_title': self.header_title,
            'header_icon': self.header_icon,
            'header_height': self.header_height,
            'draggable': self.draggable,
            'background_color': self.background_color,
            'border_color': self.border_color,
            'border_width': self.border_width,
            'padding': self.padding,
            'corner_radius': self.corner_radius,
            'auto_arrange_y': self.auto_arrange_y,
            'arrange_spacing': self.arrange_spacing,
            'arrange_align': self.arrange_align,
        }

    @property
    def usable_space(self) -> Tuple[int, int]:
        usable_w = self.width - (self.padding * 2)
        usable_h = self.height - (self.padding * 2) - self.header_height
        return (usable_w, usable_h)

    def get_header_rect(self) -> pygame.Rect:
        actual_x, actual_y = self.get_actual_position()
        return pygame.Rect(actual_x, actual_y, self.width, self.header_height)

    def set_background_color(self, color: Optional[Tuple[int, int, int]]) -> None:
        self.background_color = color

    def set_border_color(self, color: Optional[Tuple[int, int, int]]) -> None:
        self.border_color = color

    def set_border(self, color: Optional[Tuple[int, int, int]], width: int = 1) -> None:
        self.border_color = color
        self.border_width = width

    def set_padding(self, padding: int) -> None:
        self.padding = padding
        self._needs_rearrange = True

    def set_corner_radius(self, radius: Union[int, Tuple[int, int, int, int]]) -> None:
        self.corner_radius = radius

    def get_content_rect(self) -> Tuple[int, int, int, int]:
        actual_x, actual_y = self.get_actual_position()
        content_x = actual_x + self.padding
        content_y = actual_y + self.header_height + self.padding
        content_w = self.width - (self.padding * 2)
        content_h = self.height - self.header_height - (self.padding * 2)
        return (content_x, content_y, content_w, content_h)

    def add_child(self, child: UIElement) -> None:
        super().add_child(child)
        self._child_layout_data[child] = _ChildLayoutInfo(
            (child.x, child.y), (child.x, child.y),
            (child.width, child.height), (child.width, child.height)
        )
        self._needs_rearrange = True

    def remove_child(self, child: UIElement) -> None:
        super().remove_child(child)
        if child in self._child_layout_data:
            del self._child_layout_data[child]
        self._needs_rearrange = True

    def clear_children(self) -> None:
        for child in self.children:
            child.parent = None
        self.children.clear()
        self._child_layout_data.clear()
        self._needs_rearrange = True

    def update_theme(self, theme_type: ThemeType) -> None:
        self.theme_type = theme_type
        super().update_theme(theme_type)

    def update(self, dt: float, input_state: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        # Dragging logic
        if self.header_enabled and self.draggable:
            mouse_pos = input_state.mouse_pos
            header_rect = self.get_header_rect()
            if not self._dragging and input_state.mouse_just_pressed:
                if header_rect.collidepoint(mouse_pos):
                    self._dragging = True
                    self._drag_start_mouse = mouse_pos
                    self._drag_start_pos = (self.x, self.y)
                    input_state.consume_global_mouse()
            if self._dragging:
                if input_state.mouse_buttons_pressed.left:
                    dx = mouse_pos[0] - self._drag_start_mouse[0]
                    dy = mouse_pos[1] - self._drag_start_mouse[1]
                    self.x = self._drag_start_pos[0] + dx
                    self.y = self._drag_start_pos[1] + dy
                else:
                    self._dragging = False

        # Update children
        for child in self.children:
            if hasattr(child, 'update'):
                child.update(dt, input_state)

        # Auto‑arrange Y: check if any child's height changed
        if self.auto_arrange_y:
            needs_rearrange = self._needs_rearrange
            if not needs_rearrange:
                for child, layout in self._child_layout_data.items():
                    if child.height != layout._CurrentSize[1]:
                        needs_rearrange = True
                        break
            if needs_rearrange:
                self._arrange_children()
                self._needs_rearrange = False

    def _rearrange_children_if_needed(self) -> None:
        if self._needs_rearrange and self.auto_arrange_y:
            self._arrange_children()
            self._needs_rearrange = False

    def get_arranged_position(self, child: UIElement) -> Union[Tuple[int, int], Tuple[float, float]]:
        if child in self._child_layout_data:
            return self._child_layout_data[child]._CurrentPos
        return (child.x, child.y)

    def _arrange_children(self) -> int|float:
        if not self.auto_arrange_y:
            return 0

        visible_children = [c for c in self.children if c.visible]
        visible_children.sort(key=lambda c: c.y)

        current_y = self.padding + self.header_height
        max_width = self.width - 2 * self.padding
        new_x = 0
        for child in visible_children:
            if child not in self._child_layout_data:
                self._child_layout_data[child] = _ChildLayoutInfo(
                    (child.x, child.y), (child.x, child.y),
                    (child.width, child.height), (child.width, child.height)
                )

            if self.arrange_align == 'left':
                new_x = self.padding
            elif self.arrange_align == 'center':
                new_x = self.padding + (max_width - child.width) // 2
            elif self.arrange_align == 'right':
                new_x = self.padding + max_width - child.width
            else:
                orig_x = self._child_layout_data[child]._OriginalPos[0]
                new_x = max(self.padding, min(orig_x, self.width - self.padding - child.width))

            self._child_layout_data[child]._CurrentPos = (new_x, current_y)
            self._child_layout_data[child]._CurrentSize = (child.width, child.height)
            child.x = new_x
            child.y = current_y

            current_y += child.height + self.arrange_spacing
            
            return current_y
        return 0

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        bg_color = self.background_color or theme.background.color
        border_color = self.border_color or (theme.border.color if theme.border else (0,0,0))
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
                renderer.draw_text(self.header_title, actual_x + (self.header_icon.get_width() + 10 if self.header_icon else 5), actual_y, self.style.text_color, self.header_font)

        for child in self._global_engine.layer_manager.get_elements_in_order_from(self.children):
            if child.visible:
                layout = self._child_layout_data.get(child)
                if layout and self.auto_arrange_y:
                    child.x = layout.CurrentPos.x
                    child.y = layout.CurrentPos.y
                child.render(renderer)


# ----------------------------------------------------------------------
# ScrollingFrame – inherits from UiFrame
# ----------------------------------------------------------------------

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

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        content_width: int,
        content_height: int,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None,
        header_enabled: bool = False,
        header_title: str = "",
        header_icon: Optional[Union[str, pygame.Surface]] = None,
        header_height: int = 30,
        draggable: bool = False,
        **kwargs
    ) -> None:
        super().__init__(x, y, width, height, pivot, theme, element_id,
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

    def _get_init_args(self) -> Dict[str, Any]:
        args = super()._get_init_args()
        args.update({
            'content_width': self.content_width,
            'content_height': self.content_height,
            'scrollbar_size': self.scrollbar_size,
        })
        return args

    # ---- NEW: scrolling control methods for controller ----
    def scroll_by(self, dx: float, dy: float) -> None:
        """
        Scroll the content by the given delta amounts (in pixels).
        Useful for controller joystick input.
        """
        max_scroll_x = max(0, self.content_width - self.width)
        max_scroll_y = max(0, self.content_height - (self.height - self.header_height))
        self.scroll_x = max(0, min(max_scroll_x, self.scroll_x + int(dx)))
        self.scroll_y = max(0, min(max_scroll_y, self.scroll_y + int(dy)))

    def set_scroll(self, x: int, y: int) -> None:
        """Set the exact scroll offset, clamped to valid range."""
        max_scroll_x = max(0, self.content_width - self.width)
        max_scroll_y = max(0, self.content_height - (self.height - self.header_height))
        self.scroll_x = max(0, min(max_scroll_x, x))
        self.scroll_y = max(0, min(max_scroll_y, y))

    def clear_content(self, reset_scroll: bool = True) -> None:
        self.clear_children()
        if reset_scroll:
            self.scroll_x = 0
            self.scroll_y = 0

    def set_background_color(self, color: Tuple[int, int, int]) -> None:
        self._background_color_override = color

    def _arrange_children(self) -> int|float:
        current_y = super()._arrange_children()
        total_height = current_y - self.arrange_spacing + self.padding
        if total_height > self.content_height:
            self.content_height = total_height
        return current_y

    def update(self, dt: float, input_state: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        super().update(dt, input_state)   # handles header drag, etc.
        if self._dragging:
            return

        # ---- Scrollbar dragging (unchanged) ----
        actual_x, actual_y = self.get_actual_position()
        mouse_pos = input_state.mouse_pos
        mouse_pressed = input_state.mouse_buttons_pressed.left

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

        self._rearrange_children_if_needed()
    
    def on_scroll(self, event: pygame.event.Event) -> None:
        if not self.visible or not self.enabled:
            return

        max_scroll_y = max(0, self.content_height - (self.height - self.header_height))
        self.scroll_y = max(0, min(max_scroll_y, self.scroll_y - event.y * 30))
        max_scroll_x = max(0, self.content_width - self.width)
        self.scroll_x = max(0, min(max_scroll_x, self.scroll_x - event.x * 30))

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

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

        # Draw header (if any)
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
                text_surf = self.header_font.render(self.header_title, True, theme.button_text.color)
                text_x = actual_x + (self.header_icon.get_width() + 10 if self.header_icon else 5)
                text_y = actual_y + (self.header_height - text_surf.get_height()) // 2
                renderer.blit(text_surf, (text_x, text_y))

        content_top = actual_y + self.header_height
        content_height = self.height - self.header_height
        if hasattr(renderer, 'enable_scissor'):
            renderer.enable_scissor(actual_x, content_top, self.width, content_height)

        # Render children with scroll offset applied via their own get_actual_position
        for child in self._global_engine.layer_manager.get_elements_in_order_from(self.children):
            if not child.visible:
                continue
            layout = self._child_layout_data.get(child)
            if layout and self.auto_arrange_y:
                child.x = layout.CurrentPos.x - self.scroll_x
                child.y = layout.CurrentPos.y - self.scroll_y
            else:
                child.x -= self.scroll_x
                child.y -= self.scroll_y

            child.render(renderer)

            # Restore original positions
            if layout and self.auto_arrange_y:
                child.x = layout.CurrentPos.x
                child.y = layout.CurrentPos.y
            else:
                child.x += self.scroll_x
                child.y += self.scroll_y

        if hasattr(renderer, 'disable_scissor'):
            renderer.disable_scissor()

        # Draw scrollbars if needed
        if self.content_width > self.width:
            self._draw_horizontal_scrollbar(renderer, actual_x, content_top, theme)
        if self.content_height > content_height:
            self._draw_vertical_scrollbar(renderer, actual_x, content_top, theme)

    # --- Scrollbar helper methods (unchanged) ---
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

    def _draw_horizontal_scrollbar(self, renderer: OpenGLRenderer, fx: int, fy: int, theme: Any) -> None:
        sb_w = self.width - (self.scrollbar_size if self.content_height > self.height - self.header_height else 0)
        sb_h = self.scrollbar_size
        sb_x = fx
        sb_y = fy + (self.height - self.header_height) - sb_h
        renderer.draw_rect(sb_x, sb_y, sb_w, sb_h, theme.slider_track.color, fill=True)
        thumb = self._get_horizontal_scrollbar_rect(fx, fy)
        color = theme.slider_thumb_pressed.color if self.dragging_horizontal else theme.slider_thumb_normal.color
        renderer.draw_rect(thumb.x, thumb.y, thumb.width, thumb.height, color, fill=True)

    def _draw_vertical_scrollbar(self, renderer: OpenGLRenderer, fx: int, fy: int, theme: Any) -> None:
        sb_w = self.scrollbar_size
        sb_h = self.height - self.header_height - (self.scrollbar_size if self.content_width > self.width else 0)
        sb_x = fx + self.width - sb_w
        sb_y = fy
        renderer.draw_rect(sb_x, sb_y, sb_w, sb_h, theme.slider_track.color, fill=True)
        thumb = self._get_vertical_scrollbar_rect(fx, fy)
        color = theme.slider_thumb_pressed.color if self.dragging_vertical else theme.slider_thumb_normal.color
        renderer.draw_rect(thumb.x, thumb.y, thumb.width, thumb.height, color, fill=True)


# ----------------------------------------------------------------------
# Tabination – does not use auto_arrange_y because tabs are managed separately.
# ----------------------------------------------------------------------

class Tabination(UiFrame):
    """
    Tabbed container. Does not use auto_arrange_y because tabs are managed separately.
    """

    _properties = {
        **UiFrame._properties,
        'orientation': {'name': 'orientation', 'key': 'orientation', 'type': Literal, 'editable': True,
                        'description': 'Tab layout: horizontal, vertical1, vertical2', 'options': ['horizontal', 'vertical1', 'vertical2']},
        'tab_height': {'name': 'tab height', 'key': 'tab_height', 'type': int, 'editable': True,
                       'description': 'Height of each tab (vertical) or tab bar (horizontal)'},
        'tab_width': {'name': 'tab width', 'key': 'tab_width', 'type': int, 'editable': True,
                      'description': 'Width of each tab (horizontal) or tab bar (vertical)'},
        'current_tab': {'name': 'current tab', 'key': 'current_tab', 'type': int, 'editable': False,
                        'description': 'Index of active tab'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font_size: int = 20,
        font_name: Optional[str] = None,
        orientation: Literal['horizontal', 'vertical1', 'vertical2'] = 'horizontal',
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(x, y, width, height, pivot, theme, element_id, **kwargs)

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

    def _get_init_args(self) -> Dict[str, Any]:
        args = super()._get_init_args()
        args.update({
            'font_size': self.font_size,
            'font_name': self.font_name,
            'orientation': self.orientation,
            'tab_height': self.tab_height,
            'tab_width': self.tab_width,
        })
        return args

    def _calculate_tab_colors(self) -> None:
        theme = ThemeManager.get_theme(self.theme_type)
        base = theme.button_normal.color if theme.button_normal else (100, 100, 100)
        self._even_tab_bg = tuple(min(255, c + 20) for c in base)
        self._odd_tab_bg = tuple(max(0, c - 10) for c in base)

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def update_theme(self, theme_type: ThemeType) -> None:
        super().update_theme(theme_type)
        self._calculate_tab_colors()
        for tab in self.tabs:
            tab['frame'].update_theme(theme_type)

    # ---- NEW: methods for controller tab switching ----
    def next_tab(self) -> bool:
        """Switch to the next tab (cyclic). Returns True if successful."""
        if not self.tabs:
            return False
        current_idx = self.current_tab if self.current_tab is not None else -1
        new_idx = (current_idx + 1) % len(self.tabs)
        return self.switch_tab(new_idx)

    def previous_tab(self) -> bool:
        """Switch to the previous tab (cyclic). Returns True if successful."""
        if not self.tabs:
            return False
        current_idx = self.current_tab if self.current_tab is not None else 0
        new_idx = (current_idx - 1) % len(self.tabs)
        return self.switch_tab(new_idx)

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
        # Ensure the new tab is in view (scroll to it)
        self._update_tab_scroll()
        if self._global_engine and self.current_tab is not None:
            frame = self.tabs[self.current_tab]['frame']
            # Collect focusable children inside this frame (global visibility already true because frame is visible)
            focusable_children = []
            def collect_children(elem):
                if elem.is_globally_visible() and elem.enabled and elem.can_focus:
                    focusable_children.append(elem)
                for child in elem.children:
                    collect_children(child)
            collect_children(frame)
            if focusable_children:
                # Sort them by current focus order for consistency
                if self._global_engine.focus_order == FocusOrder.SO_X_Y:
                    focusable_children.sort(key=lambda e: (e.selection_order, e.x, e.y))
                else:
                    focusable_children.sort(key=lambda e: (e.selection_order, e.y, e.x))
                self._global_engine.focused_ui_element = focusable_children[0]
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

    def _update_tab_scroll(self) -> None:
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

    def _draw_arrow(self, renderer: OpenGLRenderer, x: int, y: int, direction: str, hover: bool) -> None:
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

    def update(self, dt: float, input_state: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        actual_x, actual_y = self.get_actual_position()
        mouse_pos = input_state.mouse_pos
        mouse_pressed = input_state.mouse_buttons_pressed.left

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
        if tab_area.collidepoint(mouse_pos) and input_state.mouse_wheel != 0:
            delta = -input_state.mouse_wheel * self._scroll_speed
            max_scroll = max(0, self._total_tab_size - self._get_visible_size())
            self._scroll_offset = max(0, min(max_scroll, self._scroll_offset + delta))
            self._update_tab_scroll()

        if self.current_tab is not None:
            self.tabs[self.current_tab]['frame'].update(dt, input_state)

    def _get_visible_size(self) -> int:
        return self.width if self.orientation == 'horizontal' else self.height

    def _get_tab_area_rect(self, fx: int, fy: int) -> pygame.Rect:
        if self.orientation == 'horizontal':
            return pygame.Rect(fx, fy, self.width, self.tab_height)
        else:
            return pygame.Rect(fx, fy, self.tab_width, self.height)

    def render(self, renderer: OpenGLRenderer) -> None:
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
                           tuple(min(255, c + 20) for c in bg_color), fill=True,
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
                                   pivot=(0, 0), rotate=0.0)
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
                                       pivot=(0.5, 0.5), rotate=rotate_angle)
                else:
                    text_x = rect.x + (rect.width - self.font.size(text)[0]) // 2
                    renderer.draw_text(text, text_x, text_y, text_color,
                                       (self.font_name, self.font_size),
                                       pivot=(0, 0), rotate=0.0)

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


# ----------------------------------------------------------------------
# Pagination – does not use auto_arrange_y.
# ----------------------------------------------------------------------

class Pagination(UiFrame):
    """
    Page navigation container (does not use auto_arrange_y).
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        total_pages: int = 1,
        current_page: int = 1,
        max_visible_pages: int = 7,
        show_prev_next: bool = True,
        show_first_last: bool = True,
        button_style: Literal['numbers', 'dots', 'compact'] = 'numbers',
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width, height, pivot, theme, element_id)

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

    def _get_init_args(self) -> Dict[str, Any]:
        args = super()._get_init_args()
        args.update({
            'total_pages': self.total_pages,
            'current_page': self.current_page,
            'max_visible_pages': self.max_visible_pages,
            'show_prev_next': self.show_prev_next,
            'show_first_last': self.show_first_last,
            'button_style': self.button_style,
        })
        return args

    def set_page(self, page: int) -> None:
        self.set_current_page(page)

    def set_total_pages(self, total_pages: int) -> None:
        old_total = self.total_pages
        self.total_pages = max(1, total_pages)
        if self.current_page > self.total_pages:
            old_page = self.current_page
            self.current_page = self.total_pages
            self._trigger_page_change(old_page)
        if old_total != self.total_pages:
            self._create_buttons()

    def set_current_page(self, page: int) -> None:
        if 1 <= page <= self.total_pages and page != self.current_page:
            old_page = self.current_page
            self.current_page = page
            self._update_button_states()
            self._trigger_page_change(old_page)

    def next_page(self) -> None:
        if self.current_page < self.total_pages:
            self.set_current_page(self.current_page + 1)

    def previous_page(self) -> None:
        if self.current_page > 1:
            self.set_current_page(self.current_page - 1)

    def first_page(self) -> None:
        self.set_current_page(1)

    def last_page(self) -> None:
        self.set_current_page(self.total_pages)

    def set_on_page_change(self, callback: Callable[[int, int], None]) -> None:
        self.on_page_change = callback

    def _trigger_page_change(self, old_page: int) -> None:
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

    def _create_buttons(self) -> None:
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
                ellipsis_label = TextLabel(current_x, button_y + button_height // 2 - 8,
                                           self.ellipsis_text, font_size=14,
                                           theme=self.theme_type)
                ellipsis_label.pivot = (0, 0.5)
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

    def _update_button_states(self) -> None:
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

    def update(self, dt: float, input_state: InputState) -> None:
        super().update(dt, input_state)
        self._update_button_states()

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return
        super().render(renderer)


# ----------------------------------------------------------------------
# Expandable – inherits from UiFrame. Its content frame can have its own auto_arrange.
# ----------------------------------------------------------------------

class Expandable(UiFrame):
    """
    Expandable panel that toggles visibility of its content frame.
    The content frame can have its own auto_arrange_y.
    """

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

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str = "Expand",
        expanded: bool = False,
        allow_multiple: bool = False,
        accordion_group: Optional[str] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None,
        auto_arrange_content: bool = False,
        arrange_spacing: int = 5,
        arrange_align: str = "left"
    ) -> None:
        super().__init__(x, y, width, 30 if not expanded else 30 + height,
                         pivot, theme, element_id)
        self.header_height = 30
        self._expanded = expanded
        self.allow_multiple = allow_multiple
        self.accordion_group = accordion_group
        self.title = title

        self.content_frame = UiFrame(0, self.header_height, width, height,
                                     theme=theme,
                                     auto_arrange_y=auto_arrange_content,
                                     arrange_spacing=arrange_spacing,
                                     arrange_align=arrange_align)
        self.content_frame.visible = expanded
        self.add_child(self.content_frame)

        self.setupIcons()

        self.header_button = Button(0, 0, width, self.header_height, title,
                                    theme=theme, pivot=(0, 0))
        self.header_button_icon = self.expanded_icon if expanded else self.collapsed_icon
        self.header_button.set_on_click(self._toggle)
        self.add_child(self.header_button)

    def setupIcons(self) -> None:
        self.expanded_icon = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.polygon(self.expanded_icon, ThemeManager.get_color('text_primary'),
                            [(0, 0), (7, 15), (15, 0)])
        self.collapsed_icon = pygame.Surface((15, 15), pygame.SRCALPHA)
        pygame.draw.polygon(self.collapsed_icon, ThemeManager.get_color('text_primary'),
                            [(0, 0), (0, 15), (15, 7)])

    def _get_init_args(self) -> Dict[str, Any]:
        args = super()._get_init_args()
        args.update({
            'title': self.title,
            'expanded': self._expanded,
            'allow_multiple': self.allow_multiple,
            'accordion_group': self.accordion_group,
            'auto_arrange_content': self.content_frame.auto_arrange_y,
            'arrange_spacing': self.content_frame.arrange_spacing,
            'arrange_align': self.content_frame.arrange_align,
        })
        return args

    def _toggle(self) -> None:
        if self._expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self) -> None:
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
            if self.parent and hasattr(self.parent, '_needs_rearrange'):
                self.parent._needs_rearrange = True
        self.header_button_icon = self.expanded_icon

    def collapse(self) -> None:
        if self._expanded:
            self._expanded = False
            self.header_button.set_text(f"{self.title}")
            self.content_frame.visible = False
            self.height = self.header_height
            if self.parent and hasattr(self.parent, '_needs_rearrange'):
                self.parent._needs_rearrange = True
        self.header_button_icon = self.collapsed_icon

    def is_expanded(self) -> bool:
        return self._expanded

    def add_to_content(self, element: UIElement) -> None:
        self.content_frame.add_child(element)

    def update(self, dt: float, input_state: InputState) -> None:
        if self._expanded:
            self.height = self.header_height + self.content_frame.height
        else:
            self.height = self.header_height
        super().update(dt, input_state)

    def render(self, renderer: OpenGLRenderer) -> None:
        super().render(renderer)
        if self.header_button_icon:
            x, y = self.header_button.get_actual_position()
            renderer.draw_surface(self.header_button_icon, x + 10, y + 5)
            
            
class ColorPicker(UiFrame):
    """
    A color picker widget that expands/collapses to show sliders and hex input.
    Inherits from UiFrame so that when its height changes (on expand/collapse),
    any parent with auto_arrange_y=True will automatically reposition its children.

    Attributes:
        color (Color): Currently selected color.
        expanded (bool): Whether the picker is expanded.
        color_system (str): 'rgb', 'hsl', or 'hsv'.
        show_alpha (bool): If True, an alpha slider is shown.
        on_color_changed (Callable[[Color], None]): Callback when color changes.
    """

    _properties = {
        **UiFrame._properties,
        'color': {'name': 'color', 'key': 'color', 'type': Color, 'editable': True,
                  'description': 'Current selected color'},
        'color_system': {'name': 'color system', 'key': 'color_system', 'type': str, 'editable': False,
                         'description': 'RGB, HSL or HSV'},
        'expanded': {'name': 'expanded', 'key': 'expanded', 'type': bool, 'editable': True,
                     'description': 'Show expanded panel'},
        'show_alpha': {'name': 'show alpha', 'key': 'show_alpha', 'type': bool, 'editable': True,
                       'description': 'Show alpha slider'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int = 280,
        closed_height: int = 32,
        expanded_height: int = 196,
        color_system: Literal['rgb', 'hsl', 'hsv'] = 'rgb',
        initial_color: Optional[Union[Color, Tuple[int, int, int]]] = None,
        show_alpha: bool = False,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(
            x, y, width, closed_height,
            pivot=pivot,
            theme=theme,
            element_id=element_id,
            **kwargs
        )

        self._closed_height = closed_height
        self._expanded_height = expanded_height
        self._expanded = False
        self.color_system = color_system.lower()
        self.show_alpha = show_alpha

        if initial_color is not None:
            if not isinstance(initial_color, Color):
                initial_color = Color(*initial_color)
        else:
            initial_color = Color(255, 255, 255, 255)
        self._color: Color = initial_color

        self.on_color_changed: Optional[Callable[[Color], None]] = None
        self._updating = False

        self._original_z_index = self.z_index
        self._original_always_on_top = self.always_on_top
        self._original_render_layer = self.render_layer

        # ---- Build header ----
        toggle_btn_width = 24
        toggle_btn_height = self._closed_height - 8
        self._toggle_btn = Button(
            self.width - toggle_btn_width - 4, 4,
            toggle_btn_width, toggle_btn_height,
            "+"
        )
        self._toggle_btn.set_on_click(self._toggle_expanded)
        self.add_child(self._toggle_btn)

        self._color_label = TextLabel(
            self._preview_width() + 6, self._closed_height // 2,
            "", font_size=13, color=(220, 220, 220),
            pivot=(0, 0.5)
        )
        self.add_child(self._color_label)

        # ---- Build expanded content (hidden by default) ----
        self._content_frame = UiFrame(
            0, self._closed_height,
            self.width, self._expanded_height - self._closed_height,
            theme=self.theme_type,
            auto_arrange_y=True,
            arrange_spacing=8,
            padding=8
        )
        self._content_frame.visible = False
        self.add_child(self._content_frame)

        self._sliders: Dict[str, Slider] = {}
        self._hex_input: Optional[TextBox] = None
        self._gradient_image: Optional[ImageLabel] = None

        self._build_content()
        self._sync_sliders_from_color()
        self._update_closed_display()
        self._apply_theme_to_children()
        
    def update_theme(self, theme_type: ThemeType) -> None:
        self.theme_type = theme_type
        self._apply_theme_to_children()

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'closed_height': self._closed_height,
            'expanded_height': self._expanded_height,
            'color_system': self.color_system,
            'initial_color': self._color,
            'show_alpha': self.show_alpha,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def _preview_width(self) -> int:
        return min(22, self._closed_height - 6)

    def _build_content(self) -> None:
        from .selectors import Slider, TextBox

        y_offset = 0
        slider_h = 20 * (self._expanded_height / 196)
        spacing = 15 * (self._expanded_height / 196)

        def add_slider(comp: str, label: str, minv: float, maxv: float, init: float) -> None:
            nonlocal y_offset
            lbl = TextLabel(int(self._closed_height * 0.2), y_offset, f"{label}:", 13, (220, 220, 220))
            self._content_frame.add_child(lbl)
            slider = Slider(
                58, y_offset,
                self._content_frame.width - 86, int(slider_h),
                minv, maxv, init, 'horizontal',
                theme=self.theme_type
            )
            slider.set_on_value_changed(lambda v, c=comp: self._on_slider_changed(c, v))
            self._content_frame.add_child(slider)
            self._sliders[comp] = slider
            y_offset += int(slider_h + spacing)

        if self.color_system == 'rgb':
            add_slider('r', 'Red', 0, 255, self._color.r)
            add_slider('g', 'Green', 0, 255, self._color.g)
            add_slider('b', 'Blue', 0, 255, self._color.b)
        elif self.color_system == 'hsl':
            h, s, l = self._rgb_to_hsl(self._color.r, self._color.g, self._color.b)
            add_slider('h', 'Hue', 0, 360, h)
            add_slider('s', 'Sat', 0, 100, s)
            add_slider('l', 'Light', 0, 100, l)
        else:
            h, s, v = self._rgb_to_hsv(self._color.r, self._color.g, self._color.b)
            add_slider('h', 'Hue', 0, 360, h)
            add_slider('s', 'Sat', 0, 100, s)
            add_slider('v', 'Value', 0, 100, v)

        if 'h' in self._sliders:
            self._create_hue_gradient()

        if self.show_alpha:
            add_slider('a', 'Alpha', 0, 255, int(self._color.a * 255))

        hex_lbl = TextLabel(int(self._closed_height * 0.2), y_offset + 2, "Hex:", 13, (220, 220, 220))
        self._content_frame.add_child(hex_lbl)
        self._hex_input = TextBox(
            58, y_offset,
            100, int(slider_h),
            self._color_to_hex(),
            font_size=13, theme=self.theme_type
        )
        self._hex_input.on_text_changed = self._on_hex_changed
        self._content_frame.add_child(self._hex_input)

        y_offset += int(slider_h + spacing)
        self._content_frame.height = max(self._content_frame.height, y_offset)

    def _create_hue_gradient(self) -> None:
        from .labels import ImageLabel
        slider = self._sliders['h']
        surf = self._create_rainbow_surface(slider.width, slider.height)
        self._gradient_image = ImageLabel(
            slider.x, slider.y, surf,
            slider.width, slider.height
        )
        self._gradient_image.z_index = -1
        self._content_frame.add_child(self._gradient_image)

    def _create_rainbow_surface(self, w: int, h: int) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for x in range(w):
            hue = (x / w) * 360
            r, g, b = self._hue_to_rgb(hue)
            pygame.draw.line(surf, (r, g, b), (x, 0), (x, h))
        return surf

    @staticmethod
    def _hue_to_rgb(hue: float) -> Tuple[int, int, int]:
        h = hue / 60.0
        c = 1.0
        x = c * (1 - abs(h % 2 - 1))
        m = 0.0
        if 0 <= h < 1:
            r, g, b = c, x, 0
        elif 1 <= h < 2:
            r, g, b = x, c, 0
        elif 2 <= h < 3:
            r, g, b = 0, c, x
        elif 3 <= h < 4:
            r, g, b = 0, x, c
        elif 4 <= h < 5:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

    def _apply_theme_to_children(self) -> None:
        for child in self.children:
            if hasattr(child, 'update_theme'):
                child.update_theme(self.theme_type)
        if self._hex_input:
            self._hex_input.update_theme(self.theme_type)
        for slider in self._sliders.values():
            if hasattr(slider, 'update_theme'):
                slider.update_theme(self.theme_type)

    def update(self, dt: float, inputState: InputState) -> None:
        old_height = self.height
        super().update(dt, inputState)
        if old_height != self.height:
            self._notify_parent_rearrange()

    def _notify_parent_rearrange(self) -> None:
        parent = self.parent
        while parent:
            if hasattr(parent, 'auto_arrange_y') and parent.auto_arrange_y:
                if hasattr(parent, '_needs_rearrange'):
                    parent._needs_rearrange = True
                break
            parent = parent.parent

    def _toggle_expanded(self) -> None:
        self._expanded = not self._expanded
        self._toggle_btn.set_text("-" if self._expanded else "+")
        self._content_frame.visible = self._expanded
        self.height = self._expanded_height if self._expanded else self._closed_height
        self._notify_parent_rearrange()

        from ...backend.types import LayerType
        if self._expanded:
            self.z_index = 10000
            self.always_on_top = True
            self.render_layer = LayerType.POPUP
        else:
            self.z_index = self._original_z_index
            self.always_on_top = self._original_always_on_top
            self.render_layer = self._original_render_layer

    def expand(self) -> None:
        if not self._expanded:
            self._toggle_expanded()

    def collapse(self) -> None:
        if self._expanded:
            self._toggle_expanded()

    @property
    def expanded(self) -> bool:
        return self._expanded

    @property
    def color(self) -> Color:
        return self._color

    @color.setter
    def color(self, new_color: Color) -> None:
        if new_color == self._color:
            return
        self._color = new_color
        self._sync_sliders_from_color()
        self._update_closed_display()
        if self.on_color_changed:
            self.on_color_changed(self._color)

    def set_on_color_changed(self, callback: Callable[[Color], None]) -> None:
        self.on_color_changed = callback

    def _update_closed_display(self) -> None:
        if self.color_system == 'rgb':
            text = f"RGB({self._color.r},{self._color.g},{self._color.b})"
            if self.show_alpha:
                text += f"  A:{int(self._color.a * 255)}"
        elif self.color_system == 'hsl':
            h, s, l = self._rgb_to_hsl(self._color.r, self._color.g, self._color.b)
            text = f"HSL({h:.0f}°,{s:.0f}%,{l:.0f}%)"
            if self.show_alpha:
                text += f"  A:{int(self._color.a * 255)}"
        else:
            h, s, v = self._rgb_to_hsv(self._color.r, self._color.g, self._color.b)
            text = f"HSV({h:.0f}°,{s:.0f}%,{v:.0f}%)"
            if self.show_alpha:
                text += f"  A:{int(self._color.a * 255)}"
        self._color_label.set_text(text)

    def _sync_sliders_from_color(self) -> None:
        if self._updating:
            return
        self._updating = True
        try:
            if self.color_system == 'rgb':
                self._sliders['r'].set_value(self._color.r)
                self._sliders['g'].set_value(self._color.g)
                self._sliders['b'].set_value(self._color.b)
            elif self.color_system == 'hsl':
                h, s, l = self._rgb_to_hsl(self._color.r, self._color.g, self._color.b)
                self._sliders['h'].set_value(h)
                self._sliders['s'].set_value(s)
                self._sliders['l'].set_value(l)
            else:
                h, s, v = self._rgb_to_hsv(self._color.r, self._color.g, self._color.b)
                self._sliders['h'].set_value(h)
                self._sliders['s'].set_value(s)
                self._sliders['v'].set_value(v)
            if self.show_alpha and 'a' in self._sliders:
                self._sliders['a'].set_value(int(self._color.a * 255))
            if self._hex_input:
                self._hex_input.set_text(self._color_to_hex())
        finally:
            self._updating = False

    def _on_slider_changed(self, component: str, value: float) -> None:
        if self._updating:
            return
        r, g, b, a = self._color.r, self._color.g, self._color.b, self._color.a
        if self.color_system == 'rgb':
            if component == 'r':
                r = int(value)
            elif component == 'g':
                g = int(value)
            elif component == 'b':
                b = int(value)
            elif component == 'a':
                a = int(value) / 255.0
            self._color = Color(r, g, b, a)
        elif self.color_system == 'hsl':
            h = self._sliders['h'].value
            s = self._sliders['s'].value
            l = self._sliders['l'].value
            if component == 'h':
                h = value
            elif component == 's':
                s = value
            elif component == 'l':
                l = value
            elif component == 'a':
                a = int(value) / 255.0
            r, g, b = self._hsl_to_rgb(h, s, l)
            self._color = Color(r, g, b, a)
        else:
            h = self._sliders['h'].value
            s = self._sliders['s'].value
            v = self._sliders['v'].value
            if component == 'h':
                h = value
            elif component == 's':
                s = value
            elif component == 'v':
                v = value
            elif component == 'a':
                a = int(value) / 255.0
            r, g, b = self._hsv_to_rgb(h, s, v)
            self._color = Color(r, g, b, a)
        self._sync_sliders_from_color()
        self._update_closed_display()
        if self.on_color_changed:
            self.on_color_changed(self._color)

    def _on_hex_changed(self, hex_str: str) -> None:
        if self._updating:
            return
        import re
        match = re.match(r'^#?([0-9A-Fa-f]{6})$', hex_str.strip())
        if match:
            hex_val = match.group(1)
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            self._color = Color(r, g, b, self._color.a)
            self._sync_sliders_from_color()
            self._update_closed_display()
            if self.on_color_changed:
                self.on_color_changed(self._color)

    def _color_to_hex(self) -> str:
        return f"#{self._color.r:02X}{self._color.g:02X}{self._color.b:02X}"

    @staticmethod
    def _rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
        r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
        maxc = max(r_, g_, b_)
        minc = min(r_, g_, b_)
        l = (maxc + minc) / 2.0
        if maxc == minc:
            return 0.0, 0.0, l * 100.0
        d = maxc - minc
        s = d / (1.0 - abs(2.0 * l - 1.0))
        if maxc == r_:
            h = (g_ - b_) / d + (6.0 if g_ < b_ else 0.0)
        elif maxc == g_:
            h = (b_ - r_) / d + 2.0
        else:
            h = (r_ - g_) / d + 4.0
        h /= 6.0
        return h * 360.0, s * 100.0, l * 100.0

    @staticmethod
    def _hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        if s == 0:
            return int(l * 255), int(l * 255), int(l * 255)
        def hue(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue(p, q, h + 1/3)
        g = hue(p, q, h)
        b = hue(p, q, h - 1/3)
        return int(r * 255), int(g * 255), int(b * 255)

    @staticmethod
    def _rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
        r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
        maxc = max(r_, g_, b_)
        minc = min(r_, g_, b_)
        v = maxc
        if maxc == 0:
            s = 0
        else:
            s = (maxc - minc) / maxc
        if maxc == minc:
            h = 0
        elif maxc == r_:
            h = (g_ - b_) / (maxc - minc) % 6
        elif maxc == g_:
            h = (b_ - r_) / (maxc - minc) + 2
        else:
            h = (r_ - g_) / (maxc - minc) + 4
        return h * 60.0, s * 100.0, v * 100.0

    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        h = h % 360
        s = s / 100.0
        v = v / 100.0
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return

        super().render(renderer)

        actual_x, actual_y = self.get_actual_position()

        preview_size = self._preview_width()
        preview_x = actual_x + 4
        renderer.draw_rect(
            preview_x, actual_y + (self._closed_height//2), preview_size, preview_size,
            self._color.to_rgb_tuple(), fill=True,
            corner_radius=2, border_width=1,
            border_color=(200, 200, 200), pivot=(0, 0.5)
        )