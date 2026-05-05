# selectors.py
# selectors.py (updated for draw_rect changes)

import pygame
import time
import math
from typing import Optional, List, Callable, Tuple, Literal, Union
from .base import *
from .textinputs import TextBox    
from .containers import UiFrame, Tabination    
from .buttons import Button              
from .labels import TextLabel, ImageLabel
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
import re

class Select(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 options: List[str], font_size: int = 20, font_name: Optional[str] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.options = options
        self.selected_index = 0
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self.on_selection_changed = None
        
        self._click_cooldown = time.time()
        self._click_delay = 0.3
        
        self.theme_type = theme or ThemeManager.get_current_theme()
        
        self.arrow_width = 20
        
        self._left_arrow_surface = None
        self._right_arrow_surface = None
        self._create_arrow_surfaces()
        
    def _create_arrow_surfaces(self):
        self._left_arrow_surface = pygame.Surface((15, 10), pygame.SRCALPHA)
        left_arrow_points = [(10, 0), (0, 5), (10, 10)]
        pygame.draw.polygon(self._left_arrow_surface, (255, 255, 255), left_arrow_points)
        
        self._right_arrow_surface = pygame.Surface((15, 10), pygame.SRCALPHA)
        right_arrow_points = [(0, 0), (10, 5), (0, 10)]
        pygame.draw.polygon(self._right_arrow_surface, (255, 255, 255), right_arrow_points)
        
    @property
    def font(self):
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font
    
    def next_option(self):
        if self.options:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            if self.on_selection_changed:
                self.on_selection_changed(self.selected_index, self.options[self.selected_index])
    
    def previous_option(self):
        if self.options:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            if self.on_selection_changed:
                self.on_selection_changed(self.selected_index, self.options[self.selected_index])
    
    def set_selected_index(self, index: int):
        if 0 <= index < len(self.options):
            self.selected_index = index
    
    def set_on_selection_changed(self, callback: Callable[[int, str], None]):
        self.on_selection_changed = callback
    
    def update(self, dt, inputState):
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
    
    def render(self, renderer):
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Border
        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                               theme.dropdown_border.color, fill=False,
                               border_width=self.border_width, corner_radius=self.corner_radius)
        
        # Background
        if self.state == UIState.NORMAL:
            bg_color = theme.dropdown_normal.color
        else:
            bg_color = theme.dropdown_hover.color
            
        renderer.draw_rect(actual_x, actual_y, self.width, self.height, bg_color,
                           fill=True, border_width=self.border_width, corner_radius=self.corner_radius)
        
        self._render_select_content(renderer, actual_x, actual_y, theme)
        
        super().render(renderer)
    
    def _render_select_content(self, renderer, actual_x: int, actual_y: int, theme):
        arrow_color = theme.dropdown_text.color

        left_arrow_x = actual_x + 5
        left_arrow_y = actual_y + (self.height - 10) // 2
        right_arrow_x = actual_x + self.width - 20
        right_arrow_y = actual_y + (self.height - 10) // 2

        if hasattr(renderer, 'draw_polygon'):
            left_points = [
                (left_arrow_x + 10, left_arrow_y),
                (left_arrow_x,       left_arrow_y + 5),
                (left_arrow_x + 10, left_arrow_y + 10)
            ]
            renderer.draw_polygon(left_points, arrow_color)

            right_points = [
                (right_arrow_x,          right_arrow_y),
                (right_arrow_x + 10,      right_arrow_y + 5),
                (right_arrow_x,          right_arrow_y + 10)
            ]
            renderer.draw_polygon(right_points, arrow_color)
        else:
            self._draw_fallback_arrows(renderer, actual_x, actual_y, arrow_color)
        
        renderer.draw_text(str(self.options[self.selected_index]), actual_x + self.width//2, actual_y + self.height//2, theme.dropdown_text.color, self.font, anchor_point=(0.5, 0.5))
    
    def _draw_fallback_arrows(self, renderer, actual_x: int, actual_y: int, arrow_color):
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
                    start_point = points[i]
                    end_point = points[(i + 1) % len(points)]
                    renderer.draw_line(start_point[0], start_point[1], 
                                        end_point[0], end_point[1], arrow_color, 2)

class Switch(UIElement):
    def __init__(self, x: int, y: int, width: int = 60, height: int = 30,
                 checked: bool = False, root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.checked = checked
        self.animation_progress = 1.0 if checked else 0.0
        self.on_toggle = None
        self._was_pressed = False
        
        self.theme_type = theme or ThemeManager.get_current_theme()
    
    def toggle(self):
        self.checked = not self.checked
        if self.on_toggle:
            self.on_toggle(self.checked)
    
    def set_checked(self, checked: bool):
        self.checked = checked
    
    def set_on_toggle(self, callback: Callable[[bool], None]):
        self.on_toggle = callback
    
    def update(self, dt, inputState):
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
            
        target_progress = 1.0 if self.checked else 0.0
        if self.animation_progress != target_progress:
            self.animation_progress += (target_progress - self.animation_progress) * 0.2
            if abs(self.animation_progress - target_progress) < 0.01:
                self.animation_progress = target_progress
    
    def _get_colors(self):
        theme = ThemeManager.get_theme(self.theme_type)
        
        if self.checked:
            track_color = theme.switch_track_on.color
            thumb_color = theme.switch_thumb_on.color
        else:
            track_color = theme.switch_track_off.color
            thumb_color = theme.switch_thumb_off.color
        
        if self.state == UIState.HOVERED:
            track_color = tuple(min(255, c + 20) for c in track_color)
        
        return track_color, thumb_color

    def render(self, renderer):
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        track_color, thumb_color = self._get_colors()
        
        border_color = (150, 150, 150)
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           border_color, fill=False, border_width=self.border_width,
                           corner_radius=self.corner_radius)
        
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           track_color, fill=True, border_width=self.border_width,
                           corner_radius=self.corner_radius)
        
        thumb_size = max(10, int(self.height * 0.7))
        thumb_margin = max(2, (self.height - thumb_size) // 2)
        max_thumb_travel = max(10, self.width - thumb_size - (thumb_margin * 2))
        
        thumb_x = actual_x + thumb_margin + int(max_thumb_travel * self.animation_progress)
        thumb_y = actual_y + thumb_margin
        
        renderer.draw_rect(thumb_x, thumb_y, thumb_size, thumb_size,
                           thumb_color, fill=True, border_width=self.border_width,
                           corner_radius=thumb_size // 2)
        
        super().render(renderer)

class Slider(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 min_val: float = 0, max_val: float = 100, value: float = 50,
                 orientation: Literal['horizontal', 'vertical'] = 'horizontal',
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.orientation = orientation.lower()
        self.dragging = False
        self.on_value_changed = None

        self.theme_type = theme or ThemeManager.get_current_theme()
        self.thumb_size = 10

    def set_on_value_changed(self, callback:Callable[[float], None]):
        self.on_value_changed = callback

    def set_theme(self, theme_type: ThemeType):
        self.theme_type = theme_type

    def _get_colors(self):
        return ThemeManager.get_theme(self.theme_type)

    def set_value(self, value: float):
        self.value = max(self.min_val, min(self.max_val, value))
        if self.on_value_changed:
            self.on_value_changed(self.value)

    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        mouse_pos, mouse_pressed = inputState.get_mouse_state()
        actual_x, actual_y = self.get_actual_position()

        if self.orientation == 'horizontal':
            thumb_x = actual_x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
            thumb_rect = (thumb_x - self.thumb_size // 2, actual_y, self.thumb_size, self.height)
        else:
            thumb_y = actual_y + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.height)
            thumb_rect = (actual_x, thumb_y - self.thumb_size // 2, self.width, self.thumb_size)

        mouse_over_thumb = (thumb_rect[0] <= mouse_pos[0] <= thumb_rect[0] + thumb_rect[2] and
                            thumb_rect[1] <= mouse_pos[1] <= thumb_rect[1] + thumb_rect[3])

        if mouse_pressed.left and (mouse_over_thumb or self.dragging):
            self.dragging = True
            self.state = UIState.PRESSED

            if self.orientation == 'horizontal':
                relative_x = max(0, min(self.width, mouse_pos[0] - actual_x))
                new_value = self.min_val + (relative_x / self.width) * (self.max_val - self.min_val)
            else:
                relative_y = max(0, min(self.height, mouse_pos[1] - actual_y))
                new_value = self.min_val + (relative_y / self.height) * (self.max_val - self.min_val)

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

    def render(self, renderer):
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

        font = pygame.font.Font(None, 12)
        value_text = f"{self.value:.1f}"
        text_surface = font.render(value_text, True, theme.slider_text.color)

        if self.orientation == 'horizontal':
            text_x = thumb_x + self.thumb_size // 2 - text_surface.get_width() // 2
            text_y = actual_y + self.height + 5
        else:
            text_x = actual_x + self.width + 5
            text_y = thumb_y + self.thumb_size // 2 - text_surface.get_height() // 2

        if hasattr(renderer, 'render_surface'):
            renderer.render_surface(text_surface, text_x, text_y)
        else:
            renderer.draw_surface(text_surface, text_x, text_y)

        super().render(renderer)

class Dropdown(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int,
                 options: List[str] = None, font_size: int = 20,
                 font_name: Optional[str] = None,
                 root_point: Tuple[float, float] = (0, 0),
                 theme: ThemeType = None,
                 max_visible_options: int = 10,
                 element_id: Optional[str] = None,
                 searchable: bool = False):
        super().__init__(x, y, width, height, root_point, element_id)

        self.options = options or []
        self.selected_index = 0
        self.expanded = False
        self.font_size = font_size
        self.font_name = font_name
        self._font = None
        self._option_height = 25
        self.on_selection_changed = None
        self._just_opened = False
        self.text_anchor_point = (0.5, 0.5)

        self.max_visible_options = max_visible_options
        self.scroll_offset = 0
        self.scrollbar_width = 10
        self.is_scrolling = False

        self.searchable = searchable
        self.search_text = ""
        self.filtered_options: Optional[List[int]] = None
        self.search_box: Optional[TextBox] = None
        self._search_box_height = 25 if searchable else 0

        self.theme_type = theme or ThemeManager.get_current_theme()

        if self.searchable:
            self._create_search_box()

    def get_selected(self) -> Tuple[int, str]:
        return self.selected_index, self.options[self.selected_index]

    def _create_search_box(self):
        self.search_box = TextBox(
            0, 0,
            self.width - self.scrollbar_width,
            self._search_box_height,
            text="",
            font_size=self.font_size,
            font_name=self.font_name,
            theme=self.theme_type,
            element_id=f"{self.element_id}_search"
        )
        self.search_box.visible = False
        self.search_box.on_text_changed = self._on_search_text_changed
        self.add_child(self.search_box)

    def _on_search_text_changed(self, text: str):
        self.search_text = text
        self._update_filtered_options()
        self.scroll_offset = 0

    def _update_filtered_options(self):
        if not self.search_text:
            self.filtered_options = None
        else:
            lower = self.search_text.lower()
            self.filtered_options = [i for i, opt in enumerate(self.options) if lower in opt.lower()]
        total = len(self.filtered_options) if self.filtered_options else len(self.options)
        max_scroll = max(0, total - self.max_visible_options)
        self.scroll_offset = min(self.scroll_offset, max_scroll)

    @property
    def font(self):
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def set_options(self, options: List[str], selected_index: int = 0):
        self.options = options
        self.selected_index = max(0, min(selected_index, len(options) - 1))
        self.search_text = ""
        self.filtered_options = None
        if self.search_box:
            self.search_box.set_text("")
        self.scroll_offset = 0
        self.expanded = False
        self.is_scrolling = False
        self._just_opened = False

    def set_theme(self, theme_type: ThemeType):
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

    def on_scroll(self, event: pygame.event.Event):
        if not self.visible or not self.enabled or (not self.expanded and not self.mouse_over(pygame.mouse.get_pos())):
            return
        
        if self.expanded:
            options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
            total = len(options_to_use)
            if total <= self.max_visible_options:
                return
            self.scroll_offset = max(0, min(total - self.max_visible_options, self.scroll_offset - event.y))
        else:
            self.selected_index = max(0, min(len(self.options) - 1, self.selected_index - event.y))

    def _get_scrollbar_track_rect(self, actual_x: int, actual_y: int) -> Tuple[int, int, int, int]:
        if len(self.options) <= self.max_visible_options:
            return (0, 0, 0, 0)
        track_x = actual_x + self.width - self.scrollbar_width
        track_y = actual_y + self.height + (self._search_box_height if self.searchable else 0)
        track_height = self.max_visible_options * self._option_height
        return (track_x, track_y, self.scrollbar_width, track_height)

    def _get_scrollbar_thumb_rect(self, actual_x: int, actual_y: int) -> Tuple[int, int, int, int]:
        options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
        total = len(options_to_use)
        if total <= self.max_visible_options:
            return (0, 0, 0, 0)

        visible_count = min(self.max_visible_options, total)
        visible_height = visible_count * self._option_height
        visible_ratio = self.max_visible_options / total
        thumb_height = max(20, int(visible_height * visible_ratio))

        max_scroll = max(0, total - self.max_visible_options)
        scroll_ratio = self.scroll_offset / max_scroll if max_scroll > 0 else 0

        thumb_x = actual_x + self.width - self.scrollbar_width
        thumb_y = (actual_y + self.height +
                   (self._search_box_height if self.searchable else 0) +
                   int((visible_height - thumb_height) * scroll_ratio))
        return (thumb_x, thumb_y, self.scrollbar_width, thumb_height)

    def update(self, dt: float, inputState: InputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        actual_x, actual_y = self.get_actual_position()
        mouse_pos = inputState.mouse_pos
        mouse_pressed = inputState.mouse_buttons_pressed.left

        mouse_over_search = False
        if self.expanded and self.searchable and self.search_box:
            self.search_box.x = 0
            self.search_box.y = self.height
            self.search_box.width = self.width - (self.scrollbar_width if len(self.options) > self.max_visible_options else 0)
            self.search_box.height = self._search_box_height
            self.search_box.visible = True
            self.search_box.update(dt, inputState)
            if self.search_box.mouse_over(inputState):
                mouse_over_search = True
        elif self.search_box:
            self.search_box.visible = False

        mouse_over_main = self.mouse_over(inputState)

        track_rect = self._get_scrollbar_track_rect(actual_x, actual_y)
        thumb_rect = self._get_scrollbar_thumb_rect(actual_x, actual_y)

        if self.expanded and track_rect[2] > 0 and track_rect[3] > 0:
            if mouse_pressed and not self._just_opened:
                if (thumb_rect[0] <= mouse_pos[0] <= thumb_rect[0] + thumb_rect[2] and
                    thumb_rect[1] <= mouse_pos[1] <= thumb_rect[1] + thumb_rect[3]):
                    self.is_scrolling = True
                    inputState.consume_global_mouse()
                elif (track_rect[0] <= mouse_pos[0] <= track_rect[0] + track_rect[2] and
                      track_rect[1] <= mouse_pos[1] <= track_rect[1] + track_rect[3]):
                    inputState.consume_global_mouse()
            elif not mouse_pressed:
                self.is_scrolling = False

            if self.is_scrolling and mouse_pressed:
                options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
                total = len(options_to_use)
                scroll_area_top = actual_y + self.height + (self._search_box_height if self.searchable else 0)
                scroll_area_height = self.max_visible_options * self._option_height
                relative_y = mouse_pos[1] - scroll_area_top
                scroll_ratio = max(0, min(1, relative_y / scroll_area_height))
                max_scroll = max(0, total - self.max_visible_options)
                self.scroll_offset = int(scroll_ratio * max_scroll)
                inputState.consume_global_mouse()

        if mouse_pressed and not self._just_opened and not self.is_scrolling:
            if mouse_over_main:
                self.expanded = not self.expanded
                self._just_opened = self.expanded
                inputState.consume_global_mouse()
            elif self.expanded:
                if (track_rect[2] > 0 and
                    track_rect[0] <= mouse_pos[0] <= track_rect[0] + track_rect[2] and
                    track_rect[1] <= mouse_pos[1] <= track_rect[1] + track_rect[3]):
                    inputState.consume_global_mouse()
                else:
                    option_clicked = False
                    visible_indices = self._get_visible_options()
                    options_start_y = actual_y + self.height + (self._search_box_height if self.searchable else 0)

                    for i, opt_index in enumerate(visible_indices):
                        option_rect = (
                            actual_x,
                            options_start_y + i * self._option_height,
                            self.width - (self.scrollbar_width if len(self.options) > self.max_visible_options else 0),
                            self._option_height
                        )
                        if (option_rect[0] <= mouse_pos[0] <= option_rect[0] + option_rect[2] and
                            option_rect[1] <= mouse_pos[1] <= option_rect[1] + option_rect[3]):
                            old_index = self.selected_index
                            self.selected_index = opt_index
                            self.expanded = False
                            self._just_opened = False
                            if old_index != opt_index and self.on_selection_changed:
                                self.on_selection_changed(opt_index, self.options[opt_index])
                            option_clicked = True
                            inputState.consume_global_mouse()
                            break

                    if not option_clicked and not mouse_over_search:
                        self.expanded = False
                        self._just_opened = False
        else:
            if not mouse_pressed:
                self._just_opened = False

        if mouse_over_main or (self.expanded and (mouse_over_search or self.is_scrolling)):
            self.state = UIState.HOVERED
        else:
            self.state = UIState.NORMAL

    def render(self, renderer: Renderer):
        if not self.visible:
            return

        theme = self._get_colors()
        actual_x, actual_y = self.get_actual_position()

        if theme.dropdown_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                               theme.dropdown_border.color, fill=False,
                               border_width=self.border_width,
                               corner_radius=self.corner_radius)

        if self.state == UIState.NORMAL:
            main_color = theme.dropdown_normal.color
        else:
            main_color = theme.dropdown_hover.color
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           main_color, fill=True, border_width=self.border_width, corner_radius=self.corner_radius)

        if self.options:
            text = self.options[self.selected_index]
            if len(text) > 15:
                text = text[:15] + "..."
            renderer.draw_text(text, actual_x + self.width // 2, actual_y + self.height // 2, theme.dropdown_text.color, self.font, anchor_point=self.text_anchor_point)

        arrow_color = theme.dropdown_text.color
        arrow_points = [
            (actual_x + self.width - 15, actual_y + self.height // 2 - 3),
            (actual_x + self.width - 5,  actual_y + self.height // 2 - 3),
            (actual_x + self.width - 10, actual_y + self.height // 2 + 3)
        ]
        self._draw_arrow_polygon(renderer, arrow_points, arrow_color)

        if self.expanded:
            self._render_expanded_options(renderer, actual_x, actual_y, theme)

        super().render(renderer)

    def _draw_arrow_polygon(self, renderer, points, color):
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
            except:
                renderer.draw_rect(points[0][0] - 5, points[0][1] - 2, 10, 5, color)

    def _render_expanded_options(self, renderer, actual_x, actual_y, theme):
        options_to_use = self.filtered_options if self.filtered_options is not None else list(range(len(self.options)))
        visible_indices = self._get_visible_options()
        if not visible_indices:
            return

        options_start_y = actual_y + self.height + (self._search_box_height if self.searchable else 0)
        total_options_height = self.max_visible_options * self._option_height
        bg_width = self.width - (self.scrollbar_width if len(options_to_use) > self.max_visible_options else 0)

        if theme.dropdown_border:
            renderer.draw_rect(actual_x, options_start_y, bg_width, total_options_height,
                               theme.dropdown_border.color, fill=False,
                               border_width=self.border_width,
                               corner_radius=self.corner_radius)

        renderer.draw_rect(actual_x, options_start_y, bg_width, total_options_height,
                           theme.dropdown_expanded.color, fill=True,
                           border_width=self.border_width,
                           corner_radius=self.corner_radius)

        for i, opt_index in enumerate(visible_indices):
            option_y = options_start_y + i * self._option_height
            is_selected = (opt_index == self.selected_index)

            if is_selected:
                option_color = theme.dropdown_option_selected.color
            else:
                option_color = theme.dropdown_option_normal.color

            mouse_pos = pygame.mouse.get_pos()
            option_rect = (actual_x, option_y, bg_width, self._option_height)
            if (option_rect[0] <= mouse_pos[0] <= option_rect[0] + option_rect[2] and
                option_rect[1] <= mouse_pos[1] <= option_rect[1] + option_rect[3]):
                option_color = theme.dropdown_option_hover.color

            renderer.draw_rect(actual_x, option_y, bg_width, self._option_height,
                               option_color, fill=True, border_width=self.border_width, corner_radius=0)

            if i < len(visible_indices) - 1 and theme.dropdown_border:
                sep_y = option_y + self._option_height - 1
                sep_color = tuple(c // 2 for c in theme.dropdown_border.color)
                renderer.draw_rect(actual_x + 1, sep_y, bg_width - 2, 1, sep_color)

            option_text = str(self.options[opt_index])
            if len(option_text) > 20:
                option_text = option_text[:20] + "..."
            text_x = actual_x + 5
            renderer.draw_text(option_text, text_x, option_y + int(self._option_height * 0.9),
                               theme.dropdown_text.color, self.font, anchor_point=(0, 1))

        if len(options_to_use) > self.max_visible_options:
            thumb_rect = self._get_scrollbar_thumb_rect(actual_x, actual_y)
            scrollbar_color = (150, 150, 150) if self.is_scrolling else (100, 100, 100)
            renderer.draw_rect(thumb_rect[0], thumb_rect[1],
                               thumb_rect[2], thumb_rect[3],
                               scrollbar_color, fill=True, border_width=self.border_width,
                               corner_radius=self.corner_radius)

    def add_option(self, option: str):
        self.options.append(option)
        self._update_filtered_options()

    def remove_option(self, option: str):
        if option in self.options:
            index = self.options.index(option)
            self.options.remove(option)
            if self.selected_index > index:
                self.selected_index -= 1
            elif self.selected_index == index:
                self.selected_index = max(0, len(self.options) - 1)
            self._update_filtered_options()

    def set_selected_index(self, index: int):
        if 0 <= index < len(self.options):
            old_index = self.selected_index
            self.selected_index = index
            if old_index != index and self.on_selection_changed:
                self.on_selection_changed(index, self.options[index])

    def set_on_selection_changed(self, callback: Callable[[int, str], None]):
        self.on_selection_changed = callback

class NumberSelector(UIElement):
    def __init__(self, x: int, y: int, width: int, height: int, min_value: int, max_value: int, 
                 value: int, min_length: int = 1, max_length: int = 10, step:int=1,
                 root_point: Tuple[float, float] = (0, 0),theme: ThemeType = None, element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        
        self.min_value = min_value
        self.max_value = max_value
        self.min_length = min_length
        self.max_length = max_length
        self.step = step
        self.theme_type = theme or ThemeManager.get_current_theme()
        self.font_size = int(height * 0.6)
        
        self._value = max(self.min_value, min(self.max_value, value))
        self._font = FontManager.get_font(None, self.font_size)
        
        self._is_up_pressed = False
        self._is_down_pressed = False
        self._up_rect = None
        self._down_rect = None
        self._last_mouse_pos_rel = (0, 0)
        
        self._setup_control_areas()
        
    @property
    def value(self) -> int:
        return self._value
    
    def get_value(self) -> int:
        return self.value

    @value.setter
    def value(self, new_value: int):
        self._value = max(self.min_value, min(self.max_value, new_value))

    def _format_value(self) -> str:
        padding = max(1, self.min_length)
        return str(self.value).zfill(padding)

    def increment(self):
        if self._value < self.max_value:
            self.value += self.step
            
    def decrement(self):
        if self._value > self.min_value:
            self.value -= self.step
            
    def _setup_control_areas(self):
        control_width = min(self.height, self.width // 4) 
        control_x = self.width - control_width
        
        self._down_rect = pygame.Rect(
            control_x,
            self.height // 2,
            control_width,
            self.height // 2
        )
        
        self._up_rect = pygame.Rect(
            control_x,
            0,
            control_width,
            self.height // 2
        )
        
    def _get_button_colors(self, theme):
        up_color = theme.button_normal.color
        down_color = theme.button_normal.color
        text_color = theme.button_text.color
        border_color = theme.button_border.color if theme.button_border else None
        background_color = theme.background.color
        
        if self.state == UIState.HOVERED or self.state == UIState.PRESSED:
            up_over = self._up_rect.collidepoint(self._last_mouse_pos_rel)
            down_over = self._down_rect.collidepoint(self._last_mouse_pos_rel)
            
            if up_over:
                up_color = theme.button_hover.color
            if down_over:
                down_color = theme.button_hover.color

            if self._is_up_pressed:
                up_color = theme.button_pressed.color
            if self._is_down_pressed:
                down_color = theme.button_pressed.color
            
        return up_color, down_color, text_color, border_color, background_color
    
    def update(self, dt, inputState):
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return
            
        mouse_pos, mouse_pressed = inputState.get_mouse_state()
        actual_x, actual_y = self.get_actual_position()
        
        mouse_rel_x = mouse_pos[0] - actual_x
        mouse_rel_y = mouse_pos[1] - actual_y
        self._last_mouse_pos_rel = (mouse_rel_x, mouse_rel_y)
        
        mouse_over_main = self.mouse_over(inputState)
        
        self._is_up_pressed = False
        self._is_down_pressed = False
        
        if mouse_over_main:
            self.state = UIState.HOVERED
            
            up_over = self._up_rect.collidepoint(self._last_mouse_pos_rel)
            down_over = self._down_rect.collidepoint(self._last_mouse_pos_rel)
            
            if not hasattr(self, '_was_pressed'):
                 self._was_pressed = False
            
            if mouse_pressed.left:
                if up_over:
                    self._is_up_pressed = True
                    self.state = UIState.PRESSED
                    if not self._was_pressed:
                        self.increment()
                        self._was_pressed = True
                
                elif down_over:
                    self._is_down_pressed = True
                    self.state = UIState.PRESSED
                    if not self._was_pressed:
                        self.decrement()
                        self._was_pressed = True
                else:
                    self._was_pressed = False
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False

    def render(self, renderer):
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        up_color, down_color, text_color, border_color, background_color = self._get_button_colors(theme)
        
        if border_color:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                               border_color, fill=False, border_width=self.border_width)
        
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           background_color, fill=True, border_width=self.border_width)
        
        renderer.draw_rect(actual_x + self._up_rect.x, actual_y + self._up_rect.y, 
                           self._up_rect.width, self._up_rect.height,
                           up_color, fill=True, border_width=max(1, self.border_width))
        
        renderer.draw_rect(actual_x + self._down_rect.x, actual_y + self._down_rect.y, 
                           self._down_rect.width, self._down_rect.height,
                           down_color, fill=True, border_width=max(1, self.border_width))

        formatted_value = self._format_value()
        
        text_area_width = self.width - self._up_rect.width
        center_x = actual_x + text_area_width // 2
        center_y = actual_y + self.height // 2

        renderer.draw_text(formatted_value, center_x, center_y, text_color, self._font, anchor_point=(0.5, 0.5))
        
        up_rect_abs = (actual_x + self._up_rect.x, actual_y + self._up_rect.y, self._up_rect.width, self._up_rect.height)
        center_up = (up_rect_abs[0] + up_rect_abs[2] // 2, up_rect_abs[1] + up_rect_abs[3] // 2)
        triangle_size = min(up_rect_abs[2], up_rect_abs[3]) // 3
        up_triangle_points = [
            (center_up[0], center_up[1] - triangle_size), 
            (center_up[0] - triangle_size, center_up[1] + triangle_size // 2),
            (center_up[0] + triangle_size, center_up[1] + triangle_size // 2)
        ]
        renderer.draw_polygon(up_triangle_points, text_color)
        
        down_rect_abs = (actual_x + self._down_rect.x, actual_y + self._down_rect.y, self._down_rect.width, self._down_rect.height)
        center_down = (down_rect_abs[0] + down_rect_abs[2] // 2, down_rect_abs[1] + down_rect_abs[3] // 2)
        down_triangle_points = [
            (center_down[0], center_down[1] + triangle_size),
            (center_down[0] - triangle_size, center_down[1] - triangle_size // 2),
            (center_down[0] + triangle_size, center_down[1] - triangle_size // 2)
        ]
        renderer.draw_polygon(down_triangle_points, text_color)
        
class Checkbox(UIElement):
    on_toggle: Callable[[bool], None] = None
    
    def __init__(self, x: int, y: int, width: int, height: int, checked: bool,
                 label: Optional[str] = None, label_position: str = 'right',
                 root_point: Tuple[float, float] = (0, 0), theme: ThemeType = None, element_id: Optional[str] = None):
        super().__init__(x, y, width, height, root_point, element_id)
        
        self.checked = checked
        self.label = label
        self.label_position = label_position.lower()
        self.theme_type = theme or ThemeManager.get_current_theme()
        
        self.box_size = height 
        self.font_size = int(height * 0.8) 
        self._font = FontManager.get_font(None, self.font_size)

    def set_on_toggle(self, callback: Callable[[bool], None]):
        self.on_toggle = callback
    
    def get_state(self) -> bool:
        return self.checked
    
    def value(self) -> bool:
        return self.checked
    
    def _get_colors(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]:
        theme = ThemeManager.get_theme(self.theme_type)
        box_color = theme.border2.color if theme.border2 else (100,100,100)
        border_color = theme.button_border.color if theme.button_border else (0,0,0)
        check_color = theme.button_text.color if theme.button_text else (255,255,255)
        label_color = theme.button_text.color if theme.button_text else (255,255,255)
        
        if self.state == UIState.HOVERED:
            border_color = theme.border.color if theme.border else (200,200,200)
        elif self.state == UIState.PRESSED:
            box_color = theme.border.color if theme.border else (150,150,150)
        elif self.state == UIState.DISABLED:
            box_color = theme.button_disabled.color if theme.button_disabled else (120,120,120)
        return box_color, check_color, border_color, label_color

    def toggle(self):
        self.checked = not self.checked
        if self.on_toggle:
            if callable(self.on_toggle):
                self.on_toggle(self.checked)

    def update(self, dt, inputState):
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

    def render(self, renderer):
        if not self.visible:
            return
            
        actual_x, actual_y = self.get_actual_position()
        box_color, check_color, border_color, label_color = self._get_colors()
        
        box_x = actual_x
        label_surface = None
        
        if self.label:
            label_width, label_height = self._font.size(self.label)
            
            if self.label_position == 'right':
                box_x = actual_x
                label_x = actual_x + self.box_size + 5
            else:
                box_x = actual_x + self.width - self.box_size
                label_x = actual_x

        # Draw border (outline) for checkbox
        renderer.draw_rect(box_x, actual_y, self.box_size, self.box_size,
                           border_color, fill=False, border_width=self.border_width,
                           corner_radius=self.corner_radius)
        
        # Draw fill background
        renderer.draw_rect(box_x, actual_y, self.box_size, self.box_size,
                           box_color, fill=True, border_width=self.border_width,
                           corner_radius=self.corner_radius)
        
        if self.checked:
            padding = self.box_size // 4
            check_points = [
                ((box_x + self.box_size * 0.2, actual_y + self.box_size * 0.5), (box_x + self.box_size * 0.4, actual_y + self.box_size * 0.8)), 
                ((box_x + self.box_size * 0.4, actual_y + self.box_size * 0.8), (box_x + self.box_size * 0.8, actual_y + self.box_size * 0.2)), 
            ]
            renderer.draw_lines(check_points, check_color, width=3)

        if self.label:
            label_y = actual_y + self.height // 2
            if self.label_position == 'left':
                label_x = box_x - label_width - 5
            renderer.draw_text(self.label, label_x, label_y, label_color, self._font, anchor_point=(0.0, 0.5))

class ColorPicker(UIElement):
    """
    A compact/expandable color picker supporting RGB, HSL, or HSV.
    Fully theme‑aware.
    """
    _properties = {
        **UIElement._properties,
        'color': {'name': 'color', 'key': 'color', 'type': Color, 'editable': True,
                  'description': 'Current selected color'},
        'color_system': {'name': 'color system', 'key': 'color_system', 'type': str, 'editable': False,
                         'description': 'RGB, HSL or HSV'},
        'expanded': {'name': 'expanded', 'key': 'expanded', 'type': bool, 'editable': True,
                     'description': 'Show expanded panel'},
        'show_alpha': {'name': 'show alpha', 'key': 'show_alpha', 'type': bool, 'editable': True,
                       'description': 'Show alpha slider'},
    }

    def __init__(self, x: int, y: int, width: int = 280,
                 closed_height: int = 32, expanded_height: int = 196,
                 color_system: Literal['rgb', 'hsl', 'hsv'] = 'rgb',
                 initial_color: Optional[Color] = None, show_alpha: bool = False,
                 root_point: Tuple[float, float] = (0, 0), theme: ThemeType = None,
                 element_id: Optional[str] = None):
        # Start collapsed
        self._closed_height = closed_height
        self._expanded_height = expanded_height
        self._expanded = False
        super().__init__(x, y, width, closed_height+expanded_height, root_point, element_id)
        
        self.color_system = color_system.lower()
        self.show_alpha = show_alpha
        self.on_color_changed: Optional[Callable[[Color], None]] = None
        self._updating = False
        
        self._color = initial_color or Color(255, 255, 255, 255)
        self.theme_type = theme or ThemeManager.get_current_theme()
        
        # UI children
        self._toggle_btn = None
        self._color_label = None
        self._preview_rect = None          # store preview position/size
        self._sliders = {}
        self._hex_input = None
        self._expanded_preview_rect = None
        self._gradient_image = None
        self._expanded_children = []       # list of children that belong to expanded panel
        
        self._build_ui()
        self._apply_theme_to_children()
        self._update_closed_display()
        self._sync_sliders_from_color()
    
    def _build_ui(self):
        """Create child UI elements."""
        # ---- Toggle button (always visible) ----
        btn_width = 24
        btn_height = self._closed_height - 8
        self._toggle_btn = Button(self.width - btn_width - 4, 4,
                                  btn_width, btn_height, "+")
        self._toggle_btn.set_on_click(self._toggle_expanded)
        self.add_child(self._toggle_btn)
        
        # ---- Color preview (small square) ----
        preview_size = min(22, self._closed_height - 6)
        self._preview_x = 4
        self._preview_y = (self._closed_height - preview_size) // 2
        self._preview_w = preview_size
        self._preview_h = preview_size
        
        # ---- Color label ----
        label_x = self._preview_x + preview_size + 6
        label_y = self._closed_height // 2
        self._color_label = TextLabel(label_x, label_y, "", 13,
                                      (220,220,220), anchor_point=(0,0.5))
        self.add_child(self._color_label)
        
        # ---- Expanded panel elements (initially hidden) ----
        # All expanded content is placed below the closed bar
        expanded_top_margin = self._closed_height + 8
        y_offset = expanded_top_margin
        slider_h = 20 * (self._expanded_height / 196)                # taller for better visibility
        spacing = 15 * (self._expanded_height / 196)
        panel_width = self.width
        
        def add_slider(comp, label, minv, maxv, init):
            nonlocal y_offset
            lbl = TextLabel(8, y_offset, f"{label}:", 13, (220,220,220))
            self._add_child_to_expanded(lbl)
            slider = Slider(58, y_offset, panel_width - 86, slider_h,
                            minv, maxv, init, 'horizontal', theme=self.theme_type)
            slider.set_on_value_changed(lambda v, cn=comp: self._on_slider_changed(cn, v))
            self._add_child_to_expanded(slider)
            self._sliders[comp] = slider
            y_offset += slider_h + spacing
        
        if self.color_system == 'rgb':
            add_slider('r', 'Red', 0, 255, self._color.r)
            add_slider('g', 'Green', 0, 255, self._color.g)
            add_slider('b', 'Blue', 0, 255, self._color.b)
        elif self.color_system == 'hsl':
            h, s, l = self._rgb_to_hsl(self._color.r, self._color.g, self._color.b)
            add_slider('h', 'Hue', 0, 360, h)
            add_slider('s', 'Sat', 0, 100, s)
            add_slider('l', 'Light', 0, 100, l)
        else:  # hsv
            h, s, v = self._rgb_to_hsv(self._color.r, self._color.g, self._color.b)
            add_slider('h', 'Hue', 0, 360, h)
            add_slider('s', 'Sat', 0, 100, s)
            add_slider('v', 'Value', 0, 100, v)
        
        # Rainbow gradient for Hue slider
        if 'h' in self._sliders:
            self._create_hue_gradient(expanded_top_margin)
        
        if self.show_alpha:
            add_slider('a', 'Alpha', 0, 255, int(self._color.a * 255))
        
        # Hex input
        hex_lbl = TextLabel(8, y_offset + 2, "Hex:", 13, (220,220,220))
        self._add_child_to_expanded(hex_lbl)
        self._hex_input = TextBox(58, y_offset, 100, slider_h, self._color_to_hex(),
                                  font_size=13, theme=self.theme_type)
        self._hex_input.on_text_changed = self._on_hex_changed
        self._add_child_to_expanded(self._hex_input)
        
        y_offset += slider_h + spacing
        
        # Expanded preview (larger swatch)
        self._expanded_preview_rect = (panel_width - 68, y_offset-(24*(self._expanded_height / 196)), 60, 60)
        
        # Initially hide all expanded children
        self._set_expanded_visible(False)
    
    def _add_child_to_expanded(self, child: UIElement):
        """Add a child that belongs to the expanded panel."""
        child.visible = self._expanded
        self.add_child(child)
        self._expanded_children.append(child)
    
    def _set_expanded_visible(self, visible: bool):
        for child in self._expanded_children:
            child.visible = visible
        if self._gradient_image:
            self._gradient_image.visible = visible
    
    def _create_hue_gradient(self, expanded_top_margin: int):
        """Create rainbow gradient surface as an ImageLabel."""
        slider = self._sliders['h']
        surf = self._create_rainbow_surface(slider.width, slider.height)
        self._gradient_image = ImageLabel(slider.x, slider.y, surf,
                                          slider.width, slider.height)
        self._gradient_image.z_index = -1
        self._gradient_image.visible = self._expanded
        self.add_child(self._gradient_image)
        self._expanded_children.append(self._gradient_image)
    
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
    
    def _apply_theme_to_children(self):
        """Propagate theme to all child elements."""
        theme = ThemeManager.get_theme(self.theme_type)
        for child in self.children:
            if hasattr(child, 'update_theme'):
                child.update_theme(self.theme_type)
        if self._hex_input:
            self._hex_input.update_theme(self.theme_type)
        for slider in self._sliders.values():
            if hasattr(slider, 'update_theme'):
                slider.update_theme(self.theme_type)
        # Button text colour
        self._toggle_btn.set_text_color(theme.button_text.color)
        self._color_label.set_color(theme.label_text.color)
    
    def update_theme(self, theme_type: ThemeType):
        self.theme_type = theme_type
        self._apply_theme_to_children()
    
    def _toggle_expanded(self):
        self._expanded = not self._expanded
        # Change element's total height
        if self._expanded:
            self.height = self._closed_height + self._expanded_height
        else:
            self.height = self._closed_height
        self._toggle_btn.set_text("-" if self._expanded else "+")
        self._set_expanded_visible(self._expanded)
        if self._gradient_image and self._expanded:
            self._update_gradient_position()
    
    def _update_gradient_position(self):
        if not self._gradient_image:
            return
        slider = self._sliders['h']
        if (self._gradient_image.width != slider.width or
            self._gradient_image.height != slider.height):
            new_surf = self._create_rainbow_surface(slider.width, slider.height)
            self._gradient_image.set_image(new_surf)
            self._gradient_image.width = slider.width
            self._gradient_image.height = slider.height
        self._gradient_image.x = slider.x
        self._gradient_image.y = slider.y
    
    def _update_closed_display(self):
        """Update the text label (preview colour is drawn in render)."""
        if self.color_system == 'rgb':
            text = f"RGB({self._color.r},{self._color.g},{self._color.b})"
            if self.show_alpha:
                text += f"  A:{int(self._color.a * 255)}"
        elif self.color_system == 'hsl':
            h, s, l = self._rgb_to_hsl(self._color.r, self._color.g, self._color.b)
            text = f"HSL({h:.0f}°,{s:.0f}%,{l:.0f}%)"
            if self.show_alpha:
                text += f"  A:{int(self._color.a * 255)}"
        else:  # hsv
            h, s, v = self._rgb_to_hsv(self._color.r, self._color.g, self._color.b)
            text = f"HSV({h:.0f}°,{s:.0f}%,{v:.0f}%)"
            if self.show_alpha:
                text += f"  A:{int(self._color.a * 255)}"
        self._color_label.set_text(text)
    
    def _sync_sliders_from_color(self):
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
    
    def _on_slider_changed(self, component: str, value: float):
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
        else:  # hsv
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
    
    def _on_hex_changed(self, hex_str: str):
        if self._updating:
            return
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
    
    # ------------------- Colour conversion (static) -------------------
    @staticmethod
    def _rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        maxc = max(r, g, b)
        minc = min(r, g, b)
        l = (maxc + minc) / 2.0
        if maxc == minc:
            h = s = 0.0
        else:
            d = maxc - minc
            s = d / (1.0 - abs(2.0 * l - 1.0))
            if maxc == r:
                h = (g - b) / d + (6.0 if g < b else 0.0)
            elif maxc == g:
                h = (b - r) / d + 2.0
            else:
                h = (r - g) / d + 4.0
            h /= 6.0
        return h * 360.0, s * 100.0, l * 100.0
    
    @staticmethod
    def _hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
        h = h / 360.0
        s = s / 100.0
        l = l / 100.0
        if s == 0:
            r = g = b = l
        else:
            def hue(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1 / 6: return p + (q - p) * 6 * t
                if t < 1 / 2: return q
                if t < 2 / 3: return p + (q - p) * (2 / 3 - t) * 6
                return p
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue(p, q, h + 1 / 3)
            g = hue(p, q, h)
            b = hue(p, q, h - 1 / 3)
        return int(r * 255), int(g * 255), int(b * 255)
    
    @staticmethod
    def _rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        maxc = max(r, g, b)
        minc = min(r, g, b)
        v = maxc
        if maxc == 0:
            s = 0
        else:
            s = (maxc - minc) / maxc
        if maxc == minc:
            h = 0
        elif maxc == r:
            h = (g - b) / (maxc - minc) % 6
        elif maxc == g:
            h = (b - r) / (maxc - minc) + 2
        else:
            h = (r - g) / (maxc - minc) + 4
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
    
    # ------------------- Rendering -------------------
    def render(self, renderer):
        if not self.visible:
            return
        
        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)
        
        # Draw closed bar background (uses theme.background2)
        renderer.draw_rect(actual_x, actual_y, self.width, self._closed_height,
                           theme.background2.color, fill=True,
                           corner_radius=4, border_width=1,
                           border_color=theme.border.color if theme.border else None)
        
        # Draw colour preview square
        preview_abs_x = actual_x + self._preview_x
        preview_abs_y = actual_y + self._preview_y
        renderer.draw_rect(preview_abs_x, preview_abs_y,
                           self._preview_w, self._preview_h,
                           self._color.to_rgb_tuple(), fill=True,
                           corner_radius=2, border_width=1,
                           border_color=theme.border2.color if theme.border2 else (200, 200, 200))
        
        # Draw expanded panel background if expanded
        if self._expanded:
            panel_x = actual_x
            panel_y = actual_y + self._closed_height
            renderer.draw_rect(panel_x, panel_y, self.width, self._expanded_height,
                               theme.background2.color, fill=True,
                               corner_radius=4, border_width=1,
                               border_color=theme.border.color if theme.border else None)
            
            # Draw expanded preview swatch
            if self._expanded_preview_rect:
                ex, ey, ew, eh = self._expanded_preview_rect
                renderer.draw_rect(actual_x + ex, actual_y + ey, ew, eh,
                                   self._color.to_rgb_tuple(), fill=True,
                                   corner_radius=4, border_width=1,
                                   border_color=theme.border2.color if theme.border2 else (200, 200, 200))
        
        # Render all children (button, labels, sliders, textbox, gradient image)
        super().render(renderer)
    
    # ------------------- Public API -------------------
    @property
    def color(self) -> Color:
        return self._color
    
    @color.setter
    def color(self, new_color: Color):
        if new_color == self._color:
            return
        self._color = new_color
        self._sync_sliders_from_color()
        self._update_closed_display()
        if self.on_color_changed:
            self.on_color_changed(self._color)
    
    def set_on_color_changed(self, callback: Callable[[Color], None]):
        self.on_color_changed = callback
    
    def expand(self):
        if not self._expanded:
            self._toggle_expanded()
    
    def collapse(self):
        if self._expanded:
            self._toggle_expanded()
    
    def update(self, dt: float, inputState: InputState):
        super().update(dt, inputState)
        if self._expanded and self._gradient_image:
            self._update_gradient_position()