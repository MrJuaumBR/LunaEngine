# selectors.py

import pygame
import time
import math
import re
from typing import Optional, List, Callable, Tuple, Literal, Union, Dict, Any

from .base import *
from .textinputs import TextBox
from .containers import UiFrame, Tabination
from .buttons import Button
from .labels import TextLabel, ImageLabel
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
from ...backend.opengl import OpenGLRenderer


class Select(UIElement):
    """
    A cycle selection widget with left/right arrows to scroll through options.
    Requires activation (A) to enter manipulation mode.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'options': {'name': 'options', 'key': 'options', 'type': List[str], 'editable': True,
                    'description': 'List of selectable strings.'},
        'selected_index': {'name': 'selected index', 'key': 'selected_index', 'type': int, 'editable': True,
                           'description': 'Currently selected index.'},
        'font_size': {'name': 'font size', 'key': 'font_size', 'type': int, 'editable': True,
                      'description': 'Text size.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        options: List[str],
        font_size: int = 20,
        font_name: Optional[str] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)
        self.options = options
        self.selected_index = 0
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self.on_selection_changed: Optional[Callable[[int, str], None]] = None

        self._click_cooldown = time.time()
        self._click_delay = 0.3

        self.theme_type = theme or ThemeManager.get_current_theme()

        self.arrow_width = 20

        self._left_arrow_surface = None
        self._right_arrow_surface = None
        self._create_arrow_surfaces()

        # ---- Controller manipulation state ----
        self._manipulating = False

    # ---- CONTROLLER NAVIGATION ----
    @property
    def can_focus(self) -> bool:
        return True

    def on_activate(self) -> None:
        """Enter or exit manipulation mode."""
        self._manipulating = not self._manipulating

    def on_directional_input(self, direction: str) -> bool:
        if not self._manipulating:
            return False
        if direction in ('left', 'right'):
            if direction == 'left':
                self.previous_option()
            else:
                self.next_option()
            return True
        return False

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'options': self.options,
            'font_size': self.font_size,
            'font_name': self.font_name,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def _create_arrow_surfaces(self) -> None:
        self._left_arrow_surface = pygame.Surface((15, 10), pygame.SRCALPHA)
        left_arrow_points = [(10, 0), (0, 5), (10, 10)]
        pygame.draw.polygon(self._left_arrow_surface, (255, 255, 255), left_arrow_points)

        self._right_arrow_surface = pygame.Surface((15, 10), pygame.SRCALPHA)
        right_arrow_points = [(0, 0), (10, 5), (0, 10)]
        pygame.draw.polygon(self._right_arrow_surface, (255, 255, 255), right_arrow_points)

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def next_option(self) -> None:
        if self.options:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            if self.on_selection_changed:
                self.on_selection_changed(self.selected_index, self.options[self.selected_index])

    def previous_option(self) -> None:
        if self.options:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            if self.on_selection_changed:
                self.on_selection_changed(self.selected_index, self.options[self.selected_index])

    def set_selected_index(self, index: int) -> None:
        if 0 <= index < len(self.options):
            self.selected_index = index

    def set_on_selection_changed(self, callback: Callable[[int, str], None]) -> None:
        self.on_selection_changed = callback

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        mouse_pos = inputState.mouse_pos
        mouse_pressed = inputState.mouse_buttons_pressed.left

        actual_x, actual_y = self.get_actual_position()

        left_arrow_rect = (actual_x, actual_y, self.arrow_width, self.height)
        left_arrow_hover = (left_arrow_rect[0] <= mouse_pos[0] <= left_arrow_rect[0] + left_arrow_rect[2] and
                            left_arrow_rect[1] <= mouse_pos[1] <= left_arrow_rect[1] + left_arrow_rect[3])

        right_arrow_rect = (actual_x + self.width - self.arrow_width, actual_y, self.arrow_width, self.height)
        right_arrow_hover = (right_arrow_rect[0] <= mouse_pos[0] <= right_arrow_rect[0] + right_arrow_rect[2] and
                             right_arrow_rect[1] <= mouse_pos[1] <= right_arrow_rect[1] + right_arrow_rect[3])

        if mouse_pressed and time.time() - self._click_cooldown > self._click_delay:
            if left_arrow_hover:
                self.previous_option()
                self._click_cooldown = time.time()
            elif right_arrow_hover:
                self.next_option()
                self._click_cooldown = time.time()

        self.state = UIState.HOVERED if (left_arrow_hover or right_arrow_hover) else UIState.NORMAL

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        if self.state == UIState.NORMAL:
            bg_color = theme.dropdown_normal.color
        else:
            bg_color = theme.dropdown_hover.color

        # Highlight when manipulating
        if self._manipulating:
            bg_color = theme.dropdown_option_selected.color  # or a brighter color

        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color,
                           fill=True, border_width=self.border_width, corner_radius=self.corner_radius, border_color=theme.dropdown_border.color or (0,0,0))

        self._render_select_content(renderer, actual_x, actual_y, theme)

        super().render(renderer)

    def _render_select_content(self, renderer: Renderer, actual_x: int, actual_y: int, theme) -> None:
        arrow_color = theme.dropdown_text.color

        left_arrow_x = actual_x + 5
        left_arrow_y = actual_y + (self.height - 10) // 2
        right_arrow_x = actual_x + self.width - 20
        right_arrow_y = actual_y + (self.height - 10) // 2

        if hasattr(renderer, 'draw_polygon'):
            left_points = [
                (left_arrow_x + 10, left_arrow_y),
                (left_arrow_x, left_arrow_y + 5),
                (left_arrow_x + 10, left_arrow_y + 10)
            ]
            renderer.draw_polygon(left_points, arrow_color)

            right_points = [
                (right_arrow_x, right_arrow_y),
                (right_arrow_x + 10, right_arrow_y + 5),
                (right_arrow_x, right_arrow_y + 10)
            ]
            renderer.draw_polygon(right_points, arrow_color)
        else:
            self._draw_fallback_arrows(renderer, actual_x, actual_y, arrow_color)

        renderer.draw_text(str(self.options[self.selected_index]), actual_x + self.width // 2, actual_y + self.height // 2,
                           theme.dropdown_text.color, self.font, pivot=(0.5, 0.5))

    def _draw_fallback_arrows(self, renderer: Renderer, actual_x: int, actual_y: int, arrow_color) -> None:
        left_arrow_points = [
            (actual_x + 15, actual_y + self.height // 2 - 5),
            (actual_x + 5, actual_y + self.height // 2),
            (actual_x + 15, actual_y + self.height // 2 + 5)
        ]
        right_arrow_points = [
            (actual_x + self.width - 15, actual_y + self.height // 2 - 5),
            (actual_x + self.width - 5, actual_y + self.height // 2),
            (actual_x + self.width - 15, actual_y + self.height // 2 + 5)
        ]

        if hasattr(renderer, 'draw_polygon'):
            renderer.draw_polygon(left_arrow_points, arrow_color)
            renderer.draw_polygon(right_arrow_points, arrow_color)
        elif hasattr(renderer, 'draw_line'):
            for points in [left_arrow_points, right_arrow_points]:
                for i in range(len(points)):
                    start = points[i]
                    end = points[(i + 1) % len(points)]
                    renderer.draw_line(start[0], start[1], end[0], end[1], arrow_color, 2)


class Switch(UIElement):
    """
    A toggle switch with animated sliding thumb.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'checked': {'name': 'checked', 'key': 'checked', 'type': bool, 'editable': True,
                    'description': 'Switch state (ON/OFF).'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int = 60,
        height: int = 30,
        checked: bool = False,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)
        self.checked = checked
        self.animation_progress = 1.0 if checked else 0.0
        self.on_toggle: Optional[Callable[[bool], None]] = None
        self._was_pressed = False

        self.theme_type = theme or ThemeManager.get_current_theme()

    # ---- CONTROLLER NAVIGATION ----
    @property
    def can_focus(self) -> bool:
        return True

    def on_activate(self) -> None:
        self.toggle()
        
    def set_value(self, value: bool) -> None:
        self.checked = value
        self.animation_progress = 1.0 if value else 0.0

    def on_directional_input(self, direction: str) -> bool:
        # No directional interaction; let focus move
        return False

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'checked': self.checked,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def toggle(self) -> None:
        self.checked = not self.checked
        if self.on_toggle:
            self.on_toggle(self.checked)

    def set_checked(self, checked: bool) -> None:
        self.checked = checked

    def set_on_toggle(self, callback: Callable[[bool], None]) -> None:
        self.on_toggle = callback

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        mouse_pressed = inputState.mouse_buttons_pressed.left
        mouse_over = self.mouse_over(inputState)

        if mouse_pressed and mouse_over and not self._was_pressed:
            self.toggle()
            self._was_pressed = True
        elif not mouse_pressed:
            self._was_pressed = False

        if mouse_over:
            self.state = UIState.HOVERED
        else:
            self.state = UIState.NORMAL

        target = 1.0 if self.checked else 0.0
        if self.animation_progress != target:
            self.animation_progress += (target - self.animation_progress) * 0.2
            if abs(self.animation_progress - target) < 0.01:
                self.animation_progress = target

    def _get_colors(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        theme = ThemeManager.get_theme(self.theme_type)
        if self.checked:
            track = theme.switch_track_on.color
            thumb = theme.switch_thumb_on.color
        else:
            track = theme.switch_track_off.color
            thumb = theme.switch_thumb_off.color
        if self.state == UIState.HOVERED:
            track = tuple(min(255, c + 20) for c in track)
        return track, thumb

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        track_color, thumb_color = self._get_colors()

        border_color = ThemeManager.get_color('border') or (150, 150, 150)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           track_color, fill=True, border_width=self.border_width,
                           corner_radius=self.corner_radius, border_color=border_color)

        thumb_size = max(10, int(self.height * 0.7))
        thumb_margin = max(2, (self.height - thumb_size) // 2)
        max_travel = max(10, self.width - thumb_size - (thumb_margin * 2))

        thumb_x = actual_x + thumb_margin + int(max_travel * self.animation_progress)
        thumb_y = actual_y + thumb_margin

        renderer.draw_rect(thumb_x, thumb_y, thumb_size, thumb_size,
                           thumb_color, fill=True, border_width=self.border_width,
                           corner_radius=thumb_size // 2)

        super().render(renderer)


class Slider(UIElement):
    """
    A horizontal or vertical slider with draggable thumb.
    Requires activation (A) to enter manipulation mode.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'min_val': {'name': 'min value', 'key': 'min_val', 'type': float, 'editable': True,
                    'description': 'Minimum value.'},
        'max_val': {'name': 'max value', 'key': 'max_val', 'type': float, 'editable': True,
                    'description': 'Maximum value.'},
        'value': {'name': 'value', 'key': 'value', 'type': float, 'editable': True,
                  'description': 'Current value.'},
        'orientation': {'name': 'orientation', 'key': 'orientation', 'type': str, 'editable': True,
                        'description': '"horizontal" or "vertical".',
                        'options': ['horizontal', 'vertical']},
        'render_text': {'name': 'render text', 'key': 'render_text', 'type': bool, 'editable': True,
                        'description': 'Render value as text.'},
    }

    def __init__(
        self,
        x: int | float,
        y: int | float,
        width: int,
        height: int,
        min_val: float = 0,
        max_val: float = 100,
        value: float = 50,
        orientation: Literal['horizontal', 'vertical'] = 'horizontal',
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.orientation = orientation.lower()
        self.dragging = False
        self.on_value_changed: Optional[Callable[[float], None]] = None
        self.render_text: bool = True

        self.theme_type = theme or ThemeManager.get_current_theme()
        self.thumb_size = 10
        self.step = (max_val - min_val) / 100  # 1% step for controller navigation

        # ---- Controller manipulation state ----
        self._manipulating = False

    # ---- CONTROLLER NAVIGATION ----
    @property
    def can_focus(self) -> bool:
        return True

    def on_activate(self) -> None:
        """Enter or exit manipulation mode."""
        self._manipulating = not self._manipulating

    def on_directional_input(self, direction: str) -> bool:
        if not self._manipulating:
            return False
        if self.orientation == 'horizontal':
            if direction == 'left':
                self.set_value(self.value - self.step)
                return True
            elif direction == 'right':
                self.set_value(self.value + self.step)
                return True
        else:  # vertical
            if direction == 'up':
                self.set_value(self.value + self.step)
                return True
            elif direction == 'down':
                self.set_value(self.value - self.step)
                return True
        return False

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'min_val': self.min_val,
            'max_val': self.max_val,
            'value': self.value,
            'orientation': self.orientation,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def set_on_value_changed(self, callback: Callable[[float], None]) -> None:
        self.on_value_changed = callback

    def set_theme(self, theme_type: ThemeType) -> None:
        self.theme_type = theme_type

    def _get_colors(self) -> 'UITheme':
        return ThemeManager.get_theme(self.theme_type)

    def set_value(self, value: float) -> None:
        self.value = max(self.min_val, min(self.max_val, value))
        if self.on_value_changed:
            self.on_value_changed(self.value)

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        # If manipulating, we don't want to handle mouse dragging (but we keep the logic for mouse)
        mouse_pos, mouse_pressed = inputState.get_mouse_state()
        actual_x, actual_y = self.get_actual_position()
        scroll_x, scroll_y = self.get_scroll_offset()

        if self.orientation == 'horizontal':
            thumb_x = actual_x - scroll_x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
            thumb_rect = (thumb_x - self.thumb_size // 2, actual_y - scroll_y, self.thumb_size, self.height)
        else:
            thumb_y = actual_y - scroll_y + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.height)
            thumb_rect = (actual_x - scroll_x, thumb_y - self.thumb_size // 2, self.width, self.thumb_size)

        mouse_over_thumb = self.mouse_over(mouse_pos, rect=thumb_rect)

        if mouse_pressed.left and (mouse_over_thumb or self.dragging):
            self.dragging = True
            self.state = UIState.PRESSED

            if self.orientation == 'horizontal':
                rel = max(0, min(self.width, mouse_pos[0] - actual_x))
                new_value = self.min_val + (rel / self.width) * (self.max_val - self.min_val)
            else:
                rel = max(0, min(self.height, mouse_pos[1] - actual_y))
                new_value = self.min_val + (rel / self.height) * (self.max_val - self.min_val)

            if new_value != self.value:
                self.value = new_value
                if self.on_value_changed:
                    self.on_value_changed(self.value)
        else:
            self.dragging = False
            if mouse_over_thumb:
                self.state = UIState.HOVERED
            else:
                self.state = UIState.NORMAL

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        theme = self._get_colors()
        actual_x, actual_y = self.get_actual_position()

        if self.orientation == 'horizontal':
            track_y = actual_y + self.height // 2 - 2
            renderer.draw_rect(actual_x, track_y, self.width, 4,
                               theme.slider_track.color, fill=True,
                               corner_radius=self.corner_radius)
        else:
            track_x = actual_x + self.width // 2 - 2
            renderer.draw_rect(track_x, actual_y, 4, self.height,
                               theme.slider_track.color, fill=True,
                               corner_radius=self.corner_radius)

        thumb_color = theme.slider_thumb_normal.color
        if self.state == UIState.PRESSED:
            thumb_color = theme.slider_thumb_pressed.color
        elif self.state == UIState.HOVERED:
            thumb_color = theme.slider_thumb_hover.color
        elif self._manipulating:
            # Highlight when in manipulation mode
            thumb_color = theme.slider_thumb_hover.color  # or a special color

        if self.orientation == 'horizontal':
            thumb_x = actual_x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
            thumb_x -= self.thumb_size // 2
            renderer.draw_rect(thumb_x, actual_y, self.thumb_size, self.height,
                               thumb_color, fill=True, corner_radius=self.corner_radius)
        else:
            thumb_y = actual_y + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.height)
            thumb_y -= self.thumb_size // 2
            renderer.draw_rect(actual_x, thumb_y, self.width, self.thumb_size,
                               thumb_color, fill=True, corner_radius=self.corner_radius)

        font = FontManager.get_font(None, 12)
        value_text = f"{self.value:.1f}"
        text_w, text_h = font.size(value_text)

        if self.orientation == 'horizontal':
            text_x = thumb_x + self.thumb_size // 2 - text_w // 2
            text_y = actual_y + self.height + 5
        else:
            text_x = actual_x + self.width + 5
            text_y = thumb_y + self.thumb_size // 2 - text_h // 2
        if font and self.render_text:
            renderer.draw_text(value_text, text_x, text_y, theme.slider_text.color, font)
        super().render(renderer)


class Dropdown(UIElement):
    """
    Dropdown selection widget. When expanded, its height changes to include the
    expanded options area. Supports an optional label, search functionality,
    and scrollable options. Handles parent scrolling and auto-arrangement correctly.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'options': {'name': 'options', 'key': 'options', 'type': List[str], 'editable': True,
                    'description': 'Selectable options.'},
        'selected_index': {'name': 'selected index', 'key': 'selected_index', 'type': int, 'editable': True,
                           'description': 'Currently selected option index.'},
        'expanded': {'name': 'expanded', 'key': 'expanded', 'type': bool, 'editable': False,
                     'description': 'Whether the dropdown is expanded.'},
        'searchable': {'name': 'searchable', 'key': 'searchable', 'type': bool, 'editable': True,
                       'description': 'Show search box when expanded.'},
        'max_visible_options': {'name': 'max visible options', 'key': 'max_visible_options', 'type': int, 'editable': True,
                                'description': 'Maximum options shown before scrolling.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        options: Optional[List[str]] = None,
        font_size: int = 20,
        font_name: Optional[str] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        max_visible_options: int = 10,
        element_id: Optional[str] = None,
        searchable: bool = False,
        label: Optional[str] = None,
        label_size: Optional[int] = None,
        label_position: Literal['left', 'top'] = 'left',
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)

        self.options = options or []
        self.selected_index = 0
        self._highlighted_index = 0  # For controller navigation
        self.expanded = False
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self._option_height = 25
        self.on_selection_changed: Optional[Callable[[int, str], None]] = None
        self._just_opened = False
        self.text_pivot = (0.5, 0.5)

        self.max_visible_options = max_visible_options
        self.scroll_offset = 0
        self.scrollbar_width = 10
        self.is_scrolling = False

        self.searchable = searchable
        self.search_text = ""
        self.filtered_options: Optional[List[int]] = None
        self.search_box: Optional[TextBox] = None
        self._search_box_height = 25 if searchable else 0

        # Label support
        self.label = label
        self.label_position = label_position
        self.label_size = label_size or int(height * 0.7)
        self._label_font = FontManager.get_font(None, self.label_size)

        self._collapsed_height = height
        self._expanded_height = self._collapsed_height + self._get_expanded_height()

        self.theme_type = theme or ThemeManager.get_current_theme()

        self._label_rect = pygame.Rect(0, 0, 0, 0)
        self._button_rect = pygame.Rect(0, 0, width, height)
        self._update_layout()

        # Layering and auto‑arrange attributes
        self._original_z_index = self.z_index
        self._expanded_z_index = 10000
        self._auto_parent = None
        self._parent_auto_arrange = None

        self._on_expanded_callback: Optional[Callable[[bool], None]] = None

        from ...backend.types import LayerType
        self.render_layer = LayerType.NORMAL

        if self.searchable:
            self._create_search_box()

    # ---- CONTROLLER NAVIGATION ----
    @property
    def can_focus(self) -> bool:
        return True

    def on_activate(self) -> None:
        if self.expanded:
            # Select the highlighted option and collapse
            if hasattr(self, '_highlighted_index'):
                old_index = self.selected_index
                self.selected_index = self._highlighted_index
                if old_index != self.selected_index and self.on_selection_changed:
                    self.on_selection_changed(self.selected_index, self.options[self.selected_index])
            # Collapse
            self.expanded = False
            self.height = self._collapsed_height
            self._notify_parent_rearrange()
            self.z_index = self._original_z_index
            self.always_on_top = False
            self.render_layer = LayerType.NORMAL
            self._trigger_expanded_callback(False)
        else:
            # Expand
            self.expanded = True
            self.height = self._expanded_height
            self._notify_parent_rearrange()
            self.z_index = self._expanded_z_index
            self.always_on_top = True
            self.render_layer = LayerType.POPUP
            self._trigger_expanded_callback(True)
            # Highlight the currently selected option
            self._highlighted_index = self.selected_index

    def on_directional_input(self, direction: str) -> bool:
        if self.expanded:
            # Navigate options
            if direction in ('up', 'down'):
                options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
                if not options_to_use:
                    return True
                # Get current position in options_to_use list
                if self.filtered_options is not None:
                    try:
                        pos = self.filtered_options.index(self._highlighted_index)
                    except ValueError:
                        pos = 0
                else:
                    pos = self._highlighted_index
                if direction == 'up':
                    pos = (pos - 1) % len(options_to_use)
                else:
                    pos = (pos + 1) % len(options_to_use)
                self._highlighted_index = options_to_use[pos]
                # Ensure it's visible (scroll into view)
                self._ensure_highlight_visible(pos)
                return True
            elif direction in ('left', 'right'):
                # No horizontal navigation in expanded state
                return False
        return False

    def _ensure_highlight_visible(self, pos: int) -> None:
        total_options = len(self.filtered_options) if self.filtered_options is not None else len(self.options)
        if total_options <= self.max_visible_options:
            return
        if pos < self.scroll_offset:
            self.scroll_offset = pos
        elif pos >= self.scroll_offset + self.max_visible_options:
            self.scroll_offset = pos - self.max_visible_options + 1
        self.scroll_offset = max(0, min(self.scroll_offset, total_options - self.max_visible_options))

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'options': self.options,
            'font_size': self.font_size,
            'font_name': self.font_name,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'max_visible_options': self.max_visible_options,
            'element_id': self.element_id,
            'searchable': self.searchable,
            'label': self.label,
            'label_size': self.label_size,
            'label_position': self.label_position,
        }

    def set_on_expanded(self, callback: Callable[[bool], None]) -> None:
        """Register a callback that is called when the dropdown expands or collapses."""
        self._on_expanded_callback = callback

    def _trigger_expanded_callback(self, expanded: bool) -> None:
        from ...backend.types import LayerType
        if expanded:
            self.z_index = self._expanded_z_index
            self.always_on_top = True
            self.render_layer = LayerType.POPUP
        else:
            self.z_index = self._original_z_index
            self.always_on_top = False
            self.render_layer = LayerType.NORMAL
        if self._on_expanded_callback and callable(self._on_expanded_callback):
            self._on_expanded_callback(expanded)

    def _update_layout(self) -> None:
        total_w = self.width
        total_h = self.height if not self.expanded else self._collapsed_height

        if self.label and self.label_position == 'left':
            label_width = self._label_font.size(self.label)[0] + 10
            button_width = max(60, total_w - label_width)
            self._label_rect = pygame.Rect(0, 0, label_width, total_h)
            self._button_rect = pygame.Rect(label_width, 0, button_width, total_h)
        elif self.label and self.label_position == 'top':
            label_height = self._label_font.get_height() + 4
            button_height = total_h - label_height
            self._label_rect = pygame.Rect(0, 0, total_w, label_height)
            self._button_rect = pygame.Rect(0, label_height, total_w, button_height)
        else:
            self._label_rect = pygame.Rect(0, 0, 0, 0)
            self._button_rect = pygame.Rect(0, 0, total_w, total_h)

    def _get_expanded_height(self) -> int:
        visible = min(self.max_visible_options, len(self.options)) if self.options else 0
        return visible * self._option_height + self._search_box_height

    def _update_expanded_height(self) -> None:
        """Recalculate the expanded height based on options and search box."""
        visible_count = len(self.filtered_options) if self.filtered_options is not None else len(self.options)
        visible = min(self.max_visible_options, visible_count)
        new_expanded = self._collapsed_height + visible * self._option_height + self._search_box_height
        if new_expanded != self._expanded_height:
            self._expanded_height = new_expanded
            if self.expanded:
                self.height = self._expanded_height
                self._notify_parent_rearrange()

    def _notify_parent_rearrange(self) -> None:
        """Mark the nearest parent with auto_arrange_y as dirty."""
        parent = self.parent
        while parent:
            if hasattr(parent, 'auto_arrange_y') and parent.auto_arrange_y:
                if hasattr(parent, '_needs_rearrange'):
                    parent._needs_rearrange = True
                break
            parent = parent.parent

    def get_selected(self) -> Tuple[int, str]:
        return self.selected_index, self.options[self.selected_index]

    def _create_search_box(self) -> None:
        from ...backend.types import LayerType
        self.search_box = TextBox(
            0, 0,
            self._button_rect.width - self.scrollbar_width,
            self._search_box_height,
            text="",
            font_size=self.font_size,
            font_name=self.font_name,
            theme=self.theme_type,
            element_id=f"{self.element_id}_search"
        )
        self.search_box.visible = False
        self.search_box.on_text_changed = self._on_search_text_changed
        self.search_box.render_layer = LayerType.NORMAL
        self.add_child(self.search_box)

    def _on_search_text_changed(self, text: str) -> None:
        self.search_text = text
        self._update_filtered_options()
        self.scroll_offset = 0

    def _update_filtered_options(self) -> None:
        if not self.search_text:
            self.filtered_options = None
        else:
            lower = self.search_text.lower()
            self.filtered_options = [i for i, opt in enumerate(self.options) if lower in opt.lower()]
        total = len(self.filtered_options) if self.filtered_options else len(self.options)
        max_scroll = max(0, total - self.max_visible_options)
        self.scroll_offset = min(self.scroll_offset, max_scroll)

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def set_options(self, options: List[str], selected_index: int = 0) -> None:
        self.options = options
        self.selected_index = max(0, min(selected_index, len(options) - 1))
        self._highlighted_index = self.selected_index
        self.search_text = ""
        self.filtered_options = None
        if self.search_box:
            self.search_box.set_text("")
        self.scroll_offset = 0
        self.expanded = False
        self.is_scrolling = False
        self._just_opened = False
        self._update_expanded_height()
        self.height = self._collapsed_height
        self._update_layout()

    def set_theme(self, theme_type: ThemeType) -> None:
        self.theme_type = theme_type
        if self.search_box:
            self.search_box.update_theme(theme_type)

    def _get_colors(self):
        return ThemeManager.get_theme(self.theme_type)

    def _get_visible_options(self) -> List[int]:
        options_to_show = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
        total = len(options_to_show)
        if total <= self.max_visible_options:
            return options_to_show
        start = self.scroll_offset
        end = min(start + self.max_visible_options, total)
        return options_to_show[start:end]

    def _find_auto_arrange_parent(self) -> Optional[UIElement]:
        current = self.parent
        while current:
            if hasattr(current, 'auto_arrange_y') and current.auto_arrange_y is True:
                return current
            current = current.parent
        return None

    def on_scroll(self, event: pygame.event.Event) -> None:
        if not self.visible or not self.enabled:
            return
        engine = self.get_engine()
        mouse_pos = engine.mouse_pos if engine else pygame.mouse.get_pos()
        btn_x, btn_y = self.get_actual_position()
        btn_rect = pygame.Rect(btn_x + self._button_rect.x, btn_y + self._button_rect.y,
                               self._button_rect.width, self._button_rect.height)
        over_btn = self.mouse_over(mouse_pos, btn_rect)
        over_exp = False
        if self.expanded:
            exp_rect = self._get_expanded_screen_rect()
            over_exp = self.mouse_over(mouse_pos, exp_rect)
        if not (over_btn or over_exp):
            return

        if self.expanded:
            options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
            total = len(options_to_use)
            if total > self.max_visible_options:
                delta = -event.y
                new_offset = self.scroll_offset + delta
                max_offset = total - self.max_visible_options
                self.scroll_offset = max(0, min(max_offset, new_offset))
        else:
            delta = -event.y
            new_index = self.selected_index + delta
            old_index = self.selected_index
            self.selected_index = max(0, min(len(self.options) - 1, new_index))
            self._highlighted_index = self.selected_index
            if self.on_selection_changed and old_index != self.selected_index:
                self.on_selection_changed(self.selected_index, self.options[self.selected_index])

    def _get_button_screen_rect(self) -> pygame.Rect:
        x, y = self.get_actual_position()
        return pygame.Rect(x + self._button_rect.x, y + self._button_rect.y,
                           self._button_rect.width, self._button_rect.height)

    def _get_expanded_screen_rect(self) -> pygame.Rect:
        btn_rect = self._get_button_screen_rect()
        exp_y = btn_rect.y + self._button_rect.height + self._search_box_height
        exp_h = self.max_visible_options * self._option_height
        exp_w = self._button_rect.width - (self.scrollbar_width if len(self.options) > self.max_visible_options else 0)
        return pygame.Rect(btn_rect.x, exp_y, exp_w, exp_h)

    def _get_scrollbar_track_rect(self, btn_rect: pygame.Rect) -> pygame.Rect:
        if len(self.options) <= self.max_visible_options:
            return pygame.Rect(0, 0, 0, 0)
        exp_rect = self._get_expanded_screen_rect()
        track_x = exp_rect.right - self.scrollbar_width
        track_y = exp_rect.y
        track_h = exp_rect.height
        return pygame.Rect(track_x, track_y, self.scrollbar_width, track_h)

    def _get_scrollbar_thumb_rect(self, btn_rect: pygame.Rect) -> pygame.Rect:
        options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
        total = len(options_to_use)
        if total <= self.max_visible_options:
            return pygame.Rect(0, 0, 0, 0)
        exp_rect = self._get_expanded_screen_rect()
        track = self._get_scrollbar_track_rect(btn_rect)
        visible_ratio = self.max_visible_options / total
        thumb_h = max(20, int(track.height * visible_ratio))
        max_scroll = max(0, total - self.max_visible_options)
        scroll_ratio = self.scroll_offset / max_scroll if max_scroll > 0 else 0
        thumb_y = track.y + int((track.height - thumb_h) * scroll_ratio)
        return pygame.Rect(track.x, thumb_y, track.width, thumb_h)

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        self._update_expanded_height()
        self._update_layout()

        mouse_pos = self.get_mouse_position(inputState)
        mouse_pressed = inputState.mouse_buttons_pressed.left

        actual_pos = self.get_actual_position()
        btn_rect = pygame.Rect(actual_pos[0], actual_pos[1], self.width, self._collapsed_height)
        mouse_over_btn = self.mouse_over(inputState, btn_rect)

        mouse_over_search = False
        if self.expanded and self.searchable and self.search_box:
            self.search_box.x = self._button_rect.x
            self.search_box.y = self._button_rect.y + self._button_rect.height
            self.search_box.width = self._button_rect.width - (self.scrollbar_width if len(self.options) > self.max_visible_options else 0)
            self.search_box.height = self._search_box_height
            self.search_box.visible = True
            self.search_box.update(dt, inputState)
            search_abs = self.search_box.getCollideRect()
            if self.mouse_over(inputState, search_abs):
                mouse_over_search = True
        elif self.search_box:
            self.search_box.visible = False

        track_rect = self._get_scrollbar_track_rect(btn_rect)
        thumb_rect = self._get_scrollbar_thumb_rect(btn_rect)
        if self.expanded and track_rect.width > 0 and track_rect.height > 0:
            if mouse_pressed and not self._just_opened:
                if thumb_rect.collidepoint(mouse_pos):
                    self.is_scrolling = True
                    inputState.consume_global_mouse()
                elif track_rect.collidepoint(mouse_pos):
                    inputState.consume_global_mouse()
            elif not mouse_pressed:
                self.is_scrolling = False

            if self.is_scrolling and mouse_pressed:
                options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
                total = len(options_to_use)
                if total > self.max_visible_options:
                    scroll_ratio = (mouse_pos[1] - track_rect.y) / max(1, track_rect.height)
                    max_scroll = total - self.max_visible_options
                    self.scroll_offset = int(scroll_ratio * max_scroll)
                    self.scroll_offset = max(0, min(max_scroll, self.scroll_offset))
                    inputState.consume_global_mouse()

        if mouse_pressed and not self._just_opened and not self.is_scrolling:
            if mouse_over_btn:
                self.expanded = not self.expanded
                self._just_opened = self.expanded

                # Update height and notify parent
                self.height = self._expanded_height if self.expanded else self._collapsed_height
                self._notify_parent_rearrange()

                if self.expanded:
                    self.z_index = self._expanded_z_index
                    self.always_on_top = True
                    self.render_layer = LayerType.POPUP
                else:
                    self.z_index = self._original_z_index
                    self.always_on_top = False
                    self.render_layer = LayerType.NORMAL

                inputState.consume_global_mouse()
                self._trigger_expanded_callback(self.expanded)

            elif self.expanded:
                exp_rect = self._get_expanded_screen_rect()
                mouse_in_expanded = self.mouse_over(inputState, rect=exp_rect)
                on_scrollbar = (track_rect.width > 0 and track_rect.collidepoint(mouse_pos))

                if not mouse_in_expanded and not on_scrollbar and not mouse_over_search:
                    self.expanded = False
                    self._just_opened = False
                    self.height = self._collapsed_height
                    self._notify_parent_rearrange()
                    self.z_index = self._original_z_index
                    self.always_on_top = False
                    self.render_layer = LayerType.NORMAL
                    self._trigger_expanded_callback(False)
                elif mouse_in_expanded:
                    visible_indices = self._get_visible_options()
                    exp_rect = self._get_expanded_screen_rect()
                    base_y = exp_rect.y
                    for i, opt_index in enumerate(visible_indices):
                        opt_rect = pygame.Rect(
                            exp_rect.x,
                            base_y + i * self._option_height,
                            exp_rect.width,
                            self._option_height
                        )
                        if self.mouse_over(inputState, rect=opt_rect):
                            old_index = self.selected_index
                            self.selected_index = opt_index
                            self._highlighted_index = opt_index
                            self.expanded = False
                            self._just_opened = False
                            self.height = self._collapsed_height
                            self._notify_parent_rearrange()
                            self.z_index = self._original_z_index
                            self.always_on_top = False
                            self.render_layer = LayerType.NORMAL
                            self._trigger_expanded_callback(False)
                            if old_index != opt_index and self.on_selection_changed:
                                self.on_selection_changed(opt_index, self.options[opt_index])
                            inputState.consume_global_mouse()
                            break
        else:
            if not mouse_pressed:
                self._just_opened = False

        # Handle mouse wheel to collapse if scrolled outside
        if self.expanded and inputState.mouse_wheel != 0:
            # Check if mouse is inside the dropdown area; if not, collapse
            if not self.mouse_over(inputState, self.getCollideRect()):
                self.expanded = False
                self.height = self._collapsed_height
                self._notify_parent_rearrange()
                self._just_opened = False
                self.z_index = self._original_z_index
                self.always_on_top = False
                self.render_layer = LayerType.NORMAL
                self._trigger_expanded_callback(False)
            inputState.mouse_wheel = 0

        # Update state based on mouse over
        if mouse_over_btn or (self.expanded and (mouse_over_search or self.is_scrolling)):
            self.state = UIState.HOVERED
        else:
            self.state = UIState.NORMAL

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        theme = self._get_colors()
        btn_rect = self._get_button_screen_rect()

        if self.label and self._label_rect.width > 0:
            label_abs_x = btn_rect.x - self._button_rect.x + self._label_rect.x
            label_abs_y = btn_rect.y - self._button_rect.y + self._label_rect.y
            text_color = theme.label_text.color if theme.label_text else (220, 220, 220)
            label_text_y = label_abs_y + (self._label_rect.height - self._label_font.get_height()) // 2
            renderer.draw_text(
                self.label,
                label_abs_x + 5,
                label_text_y,
                text_color,
                self._label_font,
                pivot=(0, 0)
            )

        if self.state == UIState.NORMAL:
            main_color = theme.dropdown_normal.color
        else:
            main_color = theme.dropdown_hover.color
        renderer.draw_rect(
            btn_rect.x, btn_rect.y, btn_rect.width, btn_rect.height,
            main_color, fill=True,
            border_color=theme.dropdown_border.color,
            border_width=theme.dropdown_border.border_width,
            corner_radius=self.corner_radius
        )

        if self.options:
            text = self.options[self.selected_index]
            if len(text) > 15:
                text = text[:15] + "..."
            renderer.draw_text(
                text,
                btn_rect.x + btn_rect.width // 2,
                btn_rect.y + btn_rect.height // 2,
                theme.dropdown_text.color,
                self.font,
                pivot=self.text_pivot
            )

        arrow_color = theme.dropdown_text.color
        arrow_points = [
            (btn_rect.x + btn_rect.width - 15, btn_rect.y + btn_rect.height // 2 - 3),
            (btn_rect.x + btn_rect.width - 5, btn_rect.y + btn_rect.height // 2 - 3),
            (btn_rect.x + btn_rect.width - 10, btn_rect.y + btn_rect.height // 2 + 3)
        ]
        self._draw_arrow_polygon(renderer, arrow_points, arrow_color)

        if self.expanded:
            self._render_expanded_options(renderer, theme)

        super().render(renderer)

    def _draw_arrow_polygon(self, renderer, points, color) -> None:
        if hasattr(renderer, 'draw_polygon'):
            renderer.draw_polygon(points, color)
        elif hasattr(renderer, 'draw_line'):
            for i in range(len(points)):
                start = points[i]
                end = points[(i + 1) % len(points)]
                renderer.draw_line(start[0], start[1], end[0], end[1], color, 2)
        else:
            try:
                arrow_surface = pygame.Surface((20, 10), pygame.SRCALPHA)
                pygame.draw.polygon(arrow_surface, color, [(5, 0), (15, 0), (10, 5)])
                arrow_x = points[0][0] - 10
                arrow_y = points[0][1] - 2
                if hasattr(renderer, 'render_surface'):
                    renderer.render_surface(arrow_surface, arrow_x, arrow_y)
                else:
                    renderer.draw_surface(arrow_surface, arrow_x, arrow_y)
            except Exception:
                renderer.draw_rect(points[0][0] - 5, points[0][1] - 2, 10, 5, color)

    def _render_expanded_options(self, renderer: OpenGLRenderer, theme) -> None:
        options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
        visible_indices = self._get_visible_options()
        if not visible_indices:
            return

        exp_rect = self._get_expanded_screen_rect()
        renderer.draw_rect(
            exp_rect.x, exp_rect.y, exp_rect.width, exp_rect.height,
            theme.dropdown_expanded.color, fill=True,
            border_width=self.border_width,
            border_color=theme.dropdown_border.color,
            corner_radius=self.corner_radius
        )

        for i, opt_index in enumerate(visible_indices):
            option_y = exp_rect.y + i * self._option_height
            is_selected = (opt_index == self.selected_index)
            is_highlighted = (opt_index == self._highlighted_index)

            if is_highlighted and self.expanded:
                option_color = theme.dropdown_option_selected.color
            elif is_selected:
                option_color = theme.dropdown_option_selected.color
            else:
                option_color = theme.dropdown_option_normal.color

            mouse_pos = pygame.mouse.get_pos()
            opt_rect = pygame.Rect(exp_rect.x, option_y, exp_rect.width, self._option_height)
            if opt_rect.collidepoint(mouse_pos):
                option_color = theme.dropdown_option_hover.color

            renderer.draw_rect(
                exp_rect.x, option_y, exp_rect.width, self._option_height,
                option_color, fill=True,
                border_width=self.border_width * 0.5,
                border_color=theme.dropdown_border.color if theme.dropdown_border else None,
                corner_radius=theme.dropdown_border.corner_radius * 0.1
            )

            if i < len(visible_indices) - 1 and theme.dropdown_border:
                sep_y = option_y + self._option_height - 1
                sep_color = tuple(c // 2 for c in theme.dropdown_border.color)
                renderer.draw_rect(exp_rect.x + 1, sep_y, exp_rect.width - 2, 1, sep_color)

            option_text = str(self.options[opt_index])
            if len(option_text) > 20:
                option_text = option_text[:20] + "..."
            renderer.draw_text(
                option_text,
                exp_rect.x + 5,
                option_y + int(self._option_height * 0.9),
                theme.dropdown_text.color,
                self.font,
                pivot=(0, 1)
            )

        if len(options_to_use) > self.max_visible_options:
            btn_rect = self._get_button_screen_rect()
            track_rect = self._get_scrollbar_track_rect(btn_rect)
            thumb_rect = self._get_scrollbar_thumb_rect(btn_rect)
            renderer.draw_rect(track_rect.x, track_rect.y, track_rect.width, track_rect.height,
                               theme.slider_track.color, fill=True)
            color = theme.slider_thumb_pressed.color if self.is_scrolling else theme.slider_thumb_normal.color
            renderer.draw_rect(thumb_rect.x, thumb_rect.y, thumb_rect.width, thumb_rect.height,
                               color, fill=True, corner_radius=4)

    def add_option(self, option: str) -> None:
        self.options.append(option)
        self._update_filtered_options()
        self._update_expanded_height()

    def remove_option(self, option: str) -> None:
        if option in self.options:
            index = self.options.index(option)
            self.options.remove(option)
            if self.selected_index > index:
                self.selected_index -= 1
            elif self.selected_index == index:
                self.selected_index = max(0, len(self.options) - 1)
            self._highlighted_index = self.selected_index
            self._update_filtered_options()
            self._update_expanded_height()

    def set_selected_index(self, index: int) -> None:
        if 0 <= index < len(self.options):
            old_index = self.selected_index
            self.selected_index = index
            self._highlighted_index = index
            if old_index != index and self.on_selection_changed:
                self.on_selection_changed(index, self.options[index])

    def set_on_selection_changed(self, callback: Callable[[int, str], None]) -> None:
        self.on_selection_changed = callback


class NumberSelector(UIElement):
    """
    A numeric spinner with optional label. Supports min/max, step, and value change callbacks.
    Requires activation (A) to enter manipulation mode.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'value': {'name': 'value', 'key': 'value', 'type': int, 'editable': True,
                  'description': 'Current numeric value.'},
        'min_value': {'name': 'min value', 'key': 'min_value', 'type': int, 'editable': True,
                      'description': 'Minimum allowed value.'},
        'max_value': {'name': 'max value', 'key': 'max_value', 'type': int, 'editable': True,
                      'description': 'Maximum allowed value.'},
        'step': {'name': 'step', 'key': 'step', 'type': int, 'editable': True,
                 'description': 'Increment/decrement step.'},
        'min_length': {'name': 'min length', 'key': 'min_length', 'type': int, 'editable': True,
                       'description': 'Minimum number of digits (zero padding).'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        min_value: int,
        max_value: int,
        value: int,
        min_length: int = 1,
        max_length: int = 10,
        step: int = 1,
        label: Optional[str] = None,
        label_size: Optional[int] = None,
        label_position: Literal['left', 'top'] = 'left',
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)

        self.min_value = min_value
        self.max_value = max_value
        self.min_length = min_length
        self.max_length = max_length
        self.step = step
        self.label = label
        self.label_position = label_position
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.font_size = int(height * 0.6)
        self._value = max(self.min_value, min(self.max_value, value))

        self.label_size = label_size or int(height * 0.7)
        self._label_font = FontManager.get_font(None, self.label_size)
        self._value_font = FontManager.get_font(None, self.font_size)

        self._is_up_pressed = False
        self._is_down_pressed = False
        self._last_mouse_pos_rel = (0, 0)
        self._on_value_changed: Optional[Callable[[int], None]] = None

        self._up_rect = None
        self._down_rect = None
        self._control_rect = None
        self._label_rect = None

        # ---- Controller manipulation state ----
        self._manipulating = False

    # ---- CONTROLLER NAVIGATION ----
    @property
    def can_focus(self) -> bool:
        return True

    def on_activate(self) -> None:
        """Enter or exit manipulation mode."""
        self._manipulating = not self._manipulating

    def on_directional_input(self, direction: str) -> bool:
        if not self._manipulating:
            return False
        if direction == 'up' or direction == 'right':
            self.increment()
            return True
        elif direction == 'down' or direction == 'left':
            self.decrement()
            return True
        return False

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'value': self.value,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'step': self.step,
            'label': self.label,
            'label_size': self.label_size,
            'label_position': self.label_position,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, new_value: int) -> None:
        clamped = max(self.min_value, min(self.max_value, new_value))
        if clamped != self._value:
            self._value = clamped
            if self._on_value_changed:
                self._on_value_changed(self._value)

    def get_value(self) -> int:
        return self.value

    def set_on_value_changed(self, callback: Callable[[int], None]) -> None:
        self._on_value_changed = callback

    def increment(self, multiplier: float = 1.0) -> None:
        if self._value < self.max_value:
            self.value += int(self.step * multiplier)

    def decrement(self, multiplier: float = 1.0) -> None:
        if self._value > self.min_value:
            self.value -= int(self.step * multiplier)

    def _calculate_rects(self):
        total_w = self.width
        total_h = self.height

        if self.label and self.label_position == 'left':
            label_width = self._label_font.size(self.label)[0] + 10
            control_width = max(60, total_w - label_width)
            label_rect = pygame.Rect(0, 0, label_width, total_h)
            control_rect = pygame.Rect(label_width, 0, control_width, total_h)
        elif self.label and self.label_position == 'top':
            label_height = self._label_font.get_height() + 4
            control_height = total_h - label_height
            label_rect = pygame.Rect(0, 0, total_w, label_height)
            control_rect = pygame.Rect(0, label_height, total_w, control_height)
        else:
            label_rect = pygame.Rect(0, 0, 0, 0)
            control_rect = pygame.Rect(0, 0, total_w, total_h)

        if control_rect.width > 0 and control_rect.height > 0:
            btn_width = min(control_rect.width // 3, control_rect.height)
            up_rect = pygame.Rect(
                control_rect.x + control_rect.width - btn_width,
                control_rect.y,
                btn_width,
                control_rect.height // 2
            )
            down_rect = pygame.Rect(
                control_rect.x + control_rect.width - btn_width,
                control_rect.y + control_rect.height // 2,
                btn_width,
                control_rect.height - control_rect.height // 2
            )
        else:
            up_rect = down_rect = pygame.Rect(0, 0, 0, 0)

        return label_rect, control_rect, up_rect, down_rect

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        label_rect, control_rect, up_rect, down_rect = self._calculate_rects()
        self._label_rect = label_rect
        self._control_rect = control_rect
        self._up_rect = up_rect
        self._down_rect = down_rect

        mouse_pos, mouse_pressed = inputState.get_mouse_state()
        actual_x, actual_y = self.get_actual_position()
        scroll_x, scroll_y = self.get_scroll_offset(is_for_scroll_event=False)
        mouse_rel = (mouse_pos[0] - actual_x + scroll_x, mouse_pos[1] - actual_y + scroll_y)

        up_over = self.mouse_over(mouse_rel, rect=up_rect)
        down_over = self.mouse_over(mouse_rel, rect=down_rect)
        mouse_over_control = up_over or down_over

        self._is_up_pressed = False
        self._is_down_pressed = False

        if not hasattr(self, '_was_pressed'):
            self._was_pressed = False

        if mouse_over_control:
            self.state = UIState.HOVERED
            if mouse_pressed.left:
                self.state = UIState.PRESSED
                multiplier = self._get_multiplier(inputState)
                if up_over:
                    self._is_up_pressed = True
                    if not self._was_pressed:
                        self.increment(multiplier)
                        self._was_pressed = True
                elif down_over:
                    self._is_down_pressed = True
                    if not self._was_pressed:
                        self.decrement(multiplier)
                        self._was_pressed = True
            else:
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False

    def _get_multiplier(self, inputState: InputState) -> float:
        if inputState.keyPressed(pygame.K_LSHIFT) or inputState.keyPressed(pygame.K_RSHIFT):
            return 5.0
        elif inputState.keyPressed(pygame.K_LCTRL) or inputState.keyPressed(pygame.K_RCTRL):
            return 2.0
        elif inputState.keyPressed(pygame.K_LALT) or inputState.keyPressed(pygame.K_RALT):
            return 10.0
        return 1.0

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        label_rect, control_rect, up_rect, down_rect = self._calculate_rects()

        bg_color = theme.background2.color if theme.background2 else (30, 30, 40)

        # Highlight when manipulating
        if self._manipulating:
            bg_color = theme.dropdown_option_selected.color  # or a brighter color

        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           bg_color, fill=True, border_width=1,
                           border_color=theme.border.color if theme.border else (80, 80, 90),
                           corner_radius=self.corner_radius)

        if self.label and label_rect.width > 0:
            label_abs_x = actual_x + label_rect.x
            label_abs_y = actual_y + label_rect.y
            text_color = theme.text_primary.color if theme.text_primary else (220, 220, 220)
            label_text_y = label_abs_y + (label_rect.height - self._label_font.get_height()) // 2
            renderer.draw_text(
                self.label,
                label_abs_x + 5,
                label_text_y,
                text_color,
                self._label_font,
                pivot=(0, 0)
            )

        if up_rect.width > 0 and up_rect.height > 0:
            up_abs_x = actual_x + up_rect.x
            up_abs_y = actual_y + up_rect.y
            up_color = theme.button_normal.color
            down_color = theme.button_normal.color
            if self.state in (UIState.HOVERED, UIState.PRESSED):
                if self._is_up_pressed:
                    up_color = theme.button_pressed.color
                elif self._is_down_pressed:
                    down_color = theme.button_pressed.color
                else:
                    up_color = theme.button_hover.color
                    down_color = theme.button_hover.color

            renderer.draw_rect(up_abs_x, up_abs_y, up_rect.width, up_rect.height,
                               up_color, fill=True, border_width=1,
                               border_color=theme.button_border.color if theme.button_border else (0,0,0),
                               corner_radius=self.corner_radius // 2)

            down_abs_x = actual_x + down_rect.x
            down_abs_y = actual_y + down_rect.y
            renderer.draw_rect(down_abs_x, down_abs_y, down_rect.width, down_rect.height,
                               down_color, fill=True, border_width=1,
                               border_color=theme.button_border.color if theme.button_border else (0,0,0),
                               corner_radius=self.corner_radius // 2)

            # Up arrow
            center_up = (up_abs_x + up_rect.width // 2, up_abs_y + up_rect.height // 2)
            tri_size = min(up_rect.width, up_rect.height) // 3
            up_points = [
                (center_up[0], center_up[1] - tri_size),
                (center_up[0] - tri_size, center_up[1] + tri_size // 2),
                (center_up[0] + tri_size, center_up[1] + tri_size // 2),
            ]
            renderer.draw_polygon(up_points, theme.text_primary.color)

            # Down arrow
            center_down = (down_abs_x + down_rect.width // 2, down_abs_y + down_rect.height // 2)
            down_points = [
                (center_down[0], center_down[1] + tri_size),
                (center_down[0] - tri_size, center_down[1] - tri_size // 2),
                (center_down[0] + tri_size, center_down[1] - tri_size // 2),
            ]
            renderer.draw_polygon(down_points, theme.text_primary.color)

        value_str = str(self.value).zfill(self.min_length)
        value_area_w = control_rect.width - up_rect.width
        if value_area_w > 0:
            text_x = actual_x + control_rect.x + value_area_w // 2
            text_y = actual_y + control_rect.y + control_rect.height // 2
            renderer.draw_text(
                value_str,
                text_x,
                text_y,
                theme.text_primary.color,
                self._value_font,
                pivot=(0.5, 0.5)
            )

        super().render(renderer)

    def _format_value(self) -> str:
        return str(self.value).zfill(self.min_length)


class Checkbox(UIElement):
    """
    A clickable checkbox with optional label.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'checked': {'name': 'checked', 'key': 'checked', 'type': bool, 'editable': True,
                    'description': 'Checkbox state.'},
        'label': {'name': 'label', 'key': 'label', 'type': str, 'editable': True,
                  'description': 'Text displayed next to checkbox.'},
        'label_position': {'name': 'label position', 'key': 'label_position', 'type': str, 'editable': True,
                           'description': '"left" or "right".', 'options': ['left', 'right']},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        checked: bool,
        label: Optional[str] = None,
        label_position: str = 'right',
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)

        self.checked = checked
        self.label = label
        self.label_position = label_position.lower()
        self.theme_type = theme or ThemeManager.get_current_theme()

        self.box_size = height
        self.font_size = int(height * 0.8)
        self._font = FontManager.get_font(None, self.font_size)

        self.on_toggle: Optional[Callable[[bool], None]] = None

    # ---- CONTROLLER NAVIGATION ----
    @property
    def can_focus(self) -> bool:
        return True

    def on_activate(self) -> None:
        self.toggle()

    def on_directional_input(self, direction: str) -> bool:
        return False

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'checked': self.checked,
            'label': self.label,
            'label_position': self.label_position,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def set_on_toggle(self, callback: Callable[[bool], None]) -> None:
        self.on_toggle = callback

    def get_state(self) -> bool:
        return self.checked

    def value(self) -> bool:
        return self.checked

    def _get_colors(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]:
        theme = ThemeManager.get_theme(self.theme_type)
        box_color = theme.border2.color if theme.border2 else (100, 100, 100)
        border_color = theme.border.color if theme.border else (200, 200, 200)
        check_color = theme.text_primary.color if theme.text_primary else (255, 255, 255)
        label_color = theme.text_primary.color if theme.text_primary else (255, 255, 255)

        if self.state == UIState.HOVERED:
            border_color = theme.button_border.color if theme.button_border else (0, 0, 0)
        elif self.state == UIState.PRESSED:
            box_color = theme.border.color if theme.border else (150, 150, 150)
        elif self.state == UIState.DISABLED:
            box_color = theme.button_disabled.color if theme.button_disabled else (120, 120, 120)
        return box_color, check_color, border_color, label_color

    def toggle(self) -> None:
        self.checked = not self.checked
        if self.on_toggle and callable(self.on_toggle):
            self.on_toggle(self.checked)

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        mouse_pos, mouse_pressed = inputState.get_mouse_state()
        actual_x, actual_y = self.get_actual_position()
        mouse_rel_x = mouse_pos[0] - actual_x
        mouse_rel_y = mouse_pos[1] - actual_y

        mouse_over_main = self.mouse_over(inputState)

        if not hasattr(self, '_was_pressed'):
            self._was_pressed = False

        if mouse_over_main:
            self.state = UIState.HOVERED
            if mouse_pressed.left:
                self.state = UIState.PRESSED
                if not self._was_pressed:
                    self.toggle()
                    self._was_pressed = True
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        box_color, check_color, border_color, label_color = self._get_colors()

        box_x = actual_x
        if self.label:
            label_width, label_height = self._font.size(self.label)
            if self.label_position == 'right':
                box_x = actual_x
                label_x = actual_x + self.box_size + 5
            else:
                box_x = actual_x + self.width - self.box_size
                label_x = actual_x

        renderer.draw_rect(box_x, actual_y, self.box_size, self.box_size,
                           box_color, fill=True, border_width=self.border_width,
                           corner_radius=self.corner_radius, border_color=border_color)

        if self.checked:
            check_points = [
                ((box_x + self.box_size * 0.2, actual_y + self.box_size * 0.5),
                 (box_x + self.box_size * 0.4, actual_y + self.box_size * 0.8)),
                ((box_x + self.box_size * 0.4, actual_y + self.box_size * 0.8),
                 (box_x + self.box_size * 0.8, actual_y + self.box_size * 0.2)),
            ]
            renderer.draw_lines(check_points, check_color, width=3)

        if self.label:
            label_y = actual_y + self.height // 2
            if self.label_position == 'left':
                label_x = box_x - label_width - 5
            else:
                label_x = actual_x + self.box_size + 5
            renderer.draw_text(self.label, label_x, label_y, label_color, self._font, pivot=(0.0, 0.5))