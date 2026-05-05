"""
Debug overlay system - draggable panels, live inspector, and performance monitoring.

LOCATION: 'LunaEngine'/misc/debug.py
"""

import json
import time
import inspect
import re
import platform
from typing import Callable, List, Dict, Any, Optional, Tuple, Union, TYPE_CHECKING, Type
from dataclasses import dataclass, field
from enum import Enum

import pygame

from ..ui.elements.base import UIElement, FontManager, UIState
from ..ui.elements.containers import UiFrame, ScrollingFrame, Tabination
from ..ui.elements.selectors import Dropdown, Checkbox, Slider
from ..ui.elements.buttons import Button
from ..ui.elements.labels import TextLabel
from ..ui.elements.textinputs import TextBox
from ..backend.opengl import OpenGLRenderer
from ..backend.types import InputState, Color

if TYPE_CHECKING:
    from ..core.engine import LunaEngine


# ----------------------------------------------------------------------
# Base draggable overlay
# ----------------------------------------------------------------------

class DebugOverlay:
    """Base class for a draggable, fixable, closable debug panel."""

    def __init__(
        self,
        engine: 'LunaEngine',
        x: int = 10,
        y: int = 10,
        width: int = 200,
        height: int = 100,
        title: str = "",
        background_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
        header_color: Tuple[int, int, int, int] = (60, 60, 70, 220),
        text_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        self.engine = engine
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        self.background_color = background_color
        self.header_color = header_color
        self.text_color = text_color
        self.visible = True

        self.font = FontManager.get_font(None, 15)
        self.header_font = FontManager.get_font(None, 17)
        self.header_height = 28
        self.button_size = 18
        self.button_margin = 6

        self._fixed = False

        self.lock_btn_rect = pygame.Rect(0, 0, self.button_size, self.button_size)
        self.close_btn_rect = pygame.Rect(0, 0, self.button_size, self.button_size)

    def refresh(self, dt: float) -> None:
        pass

    def render_content(self, renderer: OpenGLRenderer) -> None:
        pass

    def toggle_fixed(self) -> None:
        self._fixed = not self._fixed

    def close(self) -> None:
        self.visible = False

    def update(self, dt: float, input_state: InputState) -> None:
        pass

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return
        renderer.draw_rect(self.x, self.y, self.width, self.height, self.background_color)
        renderer.draw_rect(self.x, self.y, self.width, self.header_height, self.header_color)
        renderer.draw_text(self.title, self.x + 8, self.y + 6, self.text_color, self.header_font)

        lock_char = 'L' if self._fixed else 'U'
        renderer.draw_text(lock_char, self.lock_btn_rect.x + 4, self.lock_btn_rect.y, self.text_color, self.font)
        renderer.draw_text('X', self.close_btn_rect.x + 4, self.close_btn_rect.y, (255, 100, 100), self.font)

        self.render_content(renderer)


# ----------------------------------------------------------------------
# Simple overlays (FPS, Scene Stats)
# ----------------------------------------------------------------------

class FPSOverlay(DebugOverlay):
    def __init__(self, engine: 'LunaEngine', x: int = 10, y: int = 10) -> None:
        super().__init__(engine, x, y, width=180, height=85, title="FPS")
        self.current_fps = 0.0
        self.avg_fps = 0.0
        self.frame_time = 0.0

    def refresh(self, dt: float) -> None:
        stats = self.engine.performance_monitor.get_stats()
        self.current_fps = stats.get('current_fps', 0)
        self.avg_fps = stats.get('average_fps', 0)
        self.frame_time = stats.get('frame_time_ms', 0)

    def render_content(self, renderer: OpenGLRenderer) -> None:
        y = self.y + self.header_height + 5
        renderer.draw_text(f"{self.current_fps:.1f} fps", self.x + 10, y, self.text_color, self.font)
        renderer.draw_text(f"Avg: {self.avg_fps:.1f} fps", self.x + 10, y + 24, self.text_color, self.font)
        renderer.draw_text(f"Frame: {self.frame_time:.2f} ms", self.x + 10, y + 48, self.text_color, self.font)

    def update(self, dt: float, input_state: InputState) -> None:
        if not self.visible:
            return

        mouse_pos = input_state.mouse_pos
        left_held = input_state.mouse_buttons_pressed.left
        left_just = input_state.mouse_just_pressed and left_held

        header_rect = pygame.Rect(self.x, self.y, self.width, self.header_height)
        self.close_btn_rect.topleft = (
            self.x + self.width - self.button_size - self.button_margin,
            self.y + (self.header_height - self.button_size) // 2,
        )
        self.lock_btn_rect.topleft = (
            self.close_btn_rect.left - self.button_size - self.button_margin,
            self.y + (self.header_height - self.button_size) // 2,
        )

        if left_just and self.close_btn_rect.collidepoint(mouse_pos):
            self.close()
            return
        if left_just and self.lock_btn_rect.collidepoint(mouse_pos):
            self.toggle_fixed()
            return

        if not self._fixed:
            if left_just and not hasattr(self, '_dragging'):
                if header_rect.collidepoint(mouse_pos) and not self.lock_btn_rect.collidepoint(mouse_pos) and not self.close_btn_rect.collidepoint(mouse_pos):
                    self._dragging = True
                    self._drag_offset_x = self.x - mouse_pos[0]
                    self._drag_offset_y = self.y - mouse_pos[1]
            if getattr(self, '_dragging', False):
                if left_held:
                    new_x = mouse_pos[0] + self._drag_offset_x
                    new_y = mouse_pos[1] + self._drag_offset_y
                    screen_w, screen_h = self.engine.window.width, self.engine.window.height
                    new_x = max(0, min(new_x, screen_w - self.width))
                    new_y = max(0, min(new_y, screen_h - self.height))
                    self.x, self.y = new_x, new_y
                else:
                    self._dragging = False

        self.refresh(dt)


class SceneStatsOverlay(DebugOverlay):
    def __init__(self, engine: 'LunaEngine', x: int = 200, y: int = 10) -> None:
        super().__init__(engine, x, y, width=300, height=140, title="Scene Stats")
        self.ui_count = 0
        self.particle_count = 0
        self.cam_pos = (0, 0)
        self.scene_update_ms = 0.0
        self.scene_render_ms = 0.0

    def refresh(self, dt: float) -> None:
        scene = self.engine.current_scene
        if scene:
            self.ui_count = len(scene.ui_elements)
            if hasattr(scene, 'particle_system'):
                self.particle_count = scene.particle_system.active_particles
            if hasattr(scene, 'camera'):
                self.cam_pos = (scene.camera.position.x, scene.camera.position.y)
            self.scene_update_ms = self.engine.performance_monitor.get_timing('scene').duration
            self.scene_render_ms = self.engine.performance_monitor.get_timing('render').duration

    def render_content(self, renderer: OpenGLRenderer) -> None:
        y = self.y + self.header_height + 5
        renderer.draw_text(f"UI: {self.ui_count}", self.x + 10, y, self.text_color, self.font)
        renderer.draw_text(f"Particles: {self.particle_count}", self.x + 10, y + 24, self.text_color, self.font)
        renderer.draw_text(f"Camera: ({self.cam_pos[0]:.0f}, {self.cam_pos[1]:.0f})", self.x + 10, y + 48, self.text_color, self.font)
        renderer.draw_text(f"Scene Update: {self.scene_update_ms:.2f} ms", self.x + 10, y + 72, self.text_color, self.font)
        renderer.draw_text(f"Scene Render: {self.scene_render_ms:.2f} ms", self.x + 10, y + 96, self.text_color, self.font)

    def update(self, dt: float, input_state: InputState) -> None:
        if not self.visible:
            return

        mouse_pos = input_state.mouse_pos
        left_held = input_state.mouse_buttons_pressed.left
        left_just = input_state.mouse_just_pressed and left_held

        header_rect = pygame.Rect(self.x, self.y, self.width, self.header_height)
        self.close_btn_rect.topleft = (
            self.x + self.width - self.button_size - self.button_margin,
            self.y + (self.header_height - self.button_size) // 2,
        )
        self.lock_btn_rect.topleft = (
            self.close_btn_rect.left - self.button_size - self.button_margin,
            self.y + (self.header_height - self.button_size) // 2,
        )

        if left_just and self.close_btn_rect.collidepoint(mouse_pos):
            self.close()
            return
        if left_just and self.lock_btn_rect.collidepoint(mouse_pos):
            self.toggle_fixed()
            return

        if not self._fixed:
            if left_just and not hasattr(self, '_dragging'):
                if header_rect.collidepoint(mouse_pos) and not self.lock_btn_rect.collidepoint(mouse_pos) and not self.close_btn_rect.collidepoint(mouse_pos):
                    self._dragging = True
                    self._drag_offset_x = self.x - mouse_pos[0]
                    self._drag_offset_y = self.y - mouse_pos[1]
            if getattr(self, '_dragging', False):
                if left_held:
                    new_x = mouse_pos[0] + self._drag_offset_x
                    new_y = mouse_pos[1] + self._drag_offset_y
                    screen_w, screen_h = self.engine.window.width, self.engine.window.height
                    new_x = max(0, min(new_x, screen_w - self.width))
                    new_y = max(0, min(new_y, screen_h - self.height))
                    self.x, self.y = new_x, new_y
                else:
                    self._dragging = False

        self.refresh(dt)


# ----------------------------------------------------------------------
# Live Inspector – now a UiFrame (draggable, with header)
# ----------------------------------------------------------------------

class LogLevel(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    DEBUG = 3


@dataclass
class LogEntry:
    level: LogLevel
    message: str
    timestamp: float = field(default_factory=time.time)


class ConsoleLogManager:
    def __init__(self, max_logs: int = 200):
        self.logs: List[LogEntry] = []
        self.max_logs = max_logs
        self.filter = LogLevel.INFO
        self.on_logs_changed = None

    def add_log(self, level: LogLevel, message: str) -> None:
        self.logs.append(LogEntry(level, message))
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
        if self.on_logs_changed:
            self.on_logs_changed()

    def clear(self) -> None:
        self.logs.clear()
        if self.on_logs_changed:
            self.on_logs_changed()

    def get_filtered(self) -> List[LogEntry]:
        return [l for l in self.logs if l.level.value >= self.filter.value]


class LiveInspector(UiFrame):
    def __init__(self, engine: 'LunaEngine', x: int = 100, y: int = 100) -> None:
        # Initialize performance labels dict BEFORE _setup_content
        self._perf_labels = {}
        # Cooldown timers for back and element clicks
        self._last_back_time = 0
        self._last_element_click_time = 0
        # Stack stores previous UI element lists for navigation
        self.hierarchy_stack: List[List[UIElement]] = []
        self._current_display_elements: List[UIElement] = []
        super().__init__(
            x, y, int(engine.width * 0.5), int(engine.height * 0.55),
            header_enabled=True,
            draggable=True,
            header_title="Live Inspector",
            header_height=34,
            background_color=(26, 26, 26, 0.75),
            border_color=(80, 80, 100),
            border_width=1,
            corner_radius=8
        )
        self.engine = engine
        self.debug_manager = None
        self.pinned = False
        self.visible = False  # Start hidden
        self._setup_content(engine)

    def _setup_content(self, engine: 'LunaEngine'):
        usable = self.usable_space
        scale = (self.engine.height / 600)
        self.scale = scale

        self.tabs = Tabination(
            self.width // 2, self.height - 6,
            usable[0] - 2, usable[1] - 2,
            int(max(18 * scale, 18)),
            root_point=(0.5, 1)
        )
        self.add_child(self.tabs)

        self.tabs.add_tab("Elements")
        self.tabs.add_tab("Console")
        self.tabs.add_tab("Performance")
        self.tabs.add_tab("Settings")
        self.tabs.add_tab("Overlays")

        self.tabs.add_to_tab("Elements", TextLabel(5, 5, "Scene Elements", int(18*scale), color=self.style.text_color))
        self.tabs.add_to_tab("Console", TextLabel(5, 5, "Console", int(18*scale), color=self.style.text_color))
        self.tabs.add_to_tab("Settings", TextLabel(5, 5, "Settings", int(18*scale), color=self.style.text_color))
        self.tabs.add_to_tab("Overlays", TextLabel(5, 5, "Overlays", int(18*scale), color=self.style.text_color))

        # ---------- Elements tab: toolbar + hierarchy + properties ----------
        toolbar_y = 35
        toolbar_height = 30
        reset_btn = Button(5, toolbar_y, 60, 24, "Reset", 14)
        reset_btn.set_on_click(self._build_root_hierarchy)
        self.tabs.add_to_tab("Elements", reset_btn)

        refresh_btn = Button(70, toolbar_y, 70, 24, "Refresh", 14)
        refresh_btn.set_on_click(self._build_root_hierarchy)
        self.tabs.add_to_tab("Elements", refresh_btn)

        hierarchy_y = toolbar_y + toolbar_height + 5
        hierarchy_height = self.tabs.height - hierarchy_y - 40
        self.hierarchy_scrolling = ScrollingFrame(
            5, hierarchy_y,
            self.tabs.width // 2 - 5,
            hierarchy_height,
            self.tabs.width // 2 - 5,
            (2 * self.scale) * self.height,
            scrollbar_size=5
        )
        self.tabs.add_to_tab("Elements", self.hierarchy_scrolling)

        self.properties_frame = ScrollingFrame(
            self.tabs.width // 2 + 5, hierarchy_y,
            self.tabs.width // 2 - 7,
            hierarchy_height,
            self.tabs.width // 2 - 7,
            (2 * self.scale) * self.height,
            scrollbar_size=5
        )
        self.properties_frame.add_child(TextLabel(5, 5, "Properties", int(18*scale), color=self.style.text_color))
        self.tabs.add_to_tab("Elements", self.properties_frame)

        # ---------- Console tab ----------
        self.console_scrolling = ScrollingFrame(5, 35, self.tabs.width - 10, self.tabs.height - 100, self.tabs.width - 10, 400)
        self.tabs.add_to_tab("Console", self.console_scrolling)
        self.clear_console_btn = Button(5, 5, 80, 24, "Clear", int(16*scale))
        self.clear_console_btn.set_on_click(lambda: self.console_scrolling.clear_content())
        self.tabs.add_to_tab("Console", self.clear_console_btn)

        # ---------- Performance Tab (no scrolling frame) ----------
        self._setup_performance_tab()

        # ---------- Settings tab ----------
        self.themes_dropdown = Dropdown(5, 35, 150, 23, list(self.engine.get_all_themes().keys()), int(16*scale))
        self.themes_dropdown.set_on_selection_changed(lambda index, name: self.engine.set_global_theme(name))
        self.tabs.add_to_tab("Settings", self.themes_dropdown)
        self.force_kill_btn = Button(160, 35, 120, 23, "Force Kill", int(16*scale))
        self.force_kill_btn.set_on_click(lambda: print("ToDo"))
        self.tabs.add_to_tab("Settings", self.force_kill_btn)

        # ---------- Overlays tab ----------
        self.overlays_dropdown = Dropdown(5, 35, 110, 23, self.getOverlays(), int(16*scale))
        self.add_overlay_btn = Button(120, 35, 80, 23, "Add Overlay", int(16*scale))
        self.add_overlay_btn.set_on_click(self._add_overlay)
        self.tabs.add_to_tab("Overlays", self.overlays_dropdown)
        self.tabs.add_to_tab("Overlays", self.add_overlay_btn)
        self.overlays_scrolling = ScrollingFrame(5, 70, self.tabs.width - 10, 200, self.tabs.width - 10, 400)
        self.tabs.add_to_tab("Overlays", self.overlays_scrolling)

        self._build_root_hierarchy()

    def _setup_performance_tab(self):
        """Create the performance monitoring tab without scrolling."""
        scale = self.scale
        tab_width = self.tabs.width

        # Title
        title = TextLabel(5, 5, "Performance Metrics", int(20*scale), color=self.style.text_color)
        self.tabs.add_to_tab("Performance", title)

        # Left column metrics
        left_x = 10
        right_x = tab_width // 2 + 10
        line_height = int(17 * scale)   # adjusted scaling
        y_offset = 33                    # start position

        # FPS block
        self._add_label("FPS:", left_x, y_offset, "Performance")
        self._perf_labels['fps'] = self._add_value_label("0.0", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Avg FPS:", left_x, y_offset, "Performance")
        self._perf_labels['avg_fps'] = self._add_value_label("0.0", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("1% Low FPS:", left_x, y_offset, "Performance")
        self._perf_labels['p1_fps'] = self._add_value_label("0.0", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("0.1% Low FPS:", left_x, y_offset, "Performance")
        self._perf_labels['p01_fps'] = self._add_value_label("0.0", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Frame Time:", left_x, y_offset, "Performance")
        self._perf_labels['frame_time'] = self._add_value_label("0.00 ms", left_x + 80, y_offset, "Performance")
        y_offset += line_height + 5

        # Scene timings
        self._add_label("Scene Update:", left_x, y_offset, "Performance")
        self._perf_labels['scene_update'] = self._add_value_label("0.00 ms", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Scene Render:", left_x, y_offset, "Performance")
        self._perf_labels['scene_render'] = self._add_value_label("0.00 ms", left_x + 80, y_offset, "Performance")
        y_offset += line_height + 5

        # Scene stats
        self._add_label("UI Elements:", left_x, y_offset, "Performance")
        self._perf_labels['ui_count'] = self._add_value_label("0", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Particles:", left_x, y_offset, "Performance")
        self._perf_labels['particles'] = self._add_value_label("0", left_x + 80, y_offset, "Performance")
        y_offset += line_height + 5

        # Cache stats - left column: Text, Texture, Total
        self._add_label("Text Cache:", left_x, y_offset, "Performance")
        self._perf_labels['text_cache'] = self._add_value_label("0 B", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Texture Cache:", left_x, y_offset, "Performance")
        self._perf_labels['texture_cache'] = self._add_value_label("0 B", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Total Cache:", left_x, y_offset, "Performance")
        self._perf_labels['total_cache'] = self._add_value_label("0 B", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        # Right column: Hardware Info and remaining caches
        hw_y = 33  # same as left start
        self._add_label("Hardware Info", right_x, hw_y, "Performance", font_size=int(18*scale))
        hw_y += line_height

        self._add_label("OS:", right_x, hw_y, "Performance")
        self._perf_labels['os'] = self._add_value_label("N/A", right_x + 80, hw_y, "Performance")
        hw_y += line_height

        self._add_label("CPU:", right_x, hw_y, "Performance")
        self._perf_labels['cpu'] = self._add_value_label("N/A", right_x + 80, hw_y, "Performance")
        hw_y += line_height

        self._add_label("GPU:", right_x, hw_y, "Performance")
        self._perf_labels['gpu'] = self._add_value_label("N/A", right_x + 80, hw_y, "Performance")
        hw_y += line_height

        self._add_label("RAM Total:", right_x, hw_y, "Performance")
        self._perf_labels['ram_total'] = self._add_value_label("N/A", right_x + 80, hw_y, "Performance")
        hw_y += line_height

        self._add_label("RAM Available:", right_x, hw_y, "Performance")
        self._perf_labels['ram_avail'] = self._add_value_label("N/A", right_x + 80, hw_y, "Performance")
        hw_y += line_height

        self._add_label("Python:", right_x, hw_y, "Performance")
        self._perf_labels['python'] = self._add_value_label("N/A", right_x + 80, hw_y, "Performance")
        hw_y += line_height

        self._add_label("Pygame:", right_x, hw_y, "Performance")
        self._perf_labels['pygame'] = self._add_value_label("N/A", right_x + 80, hw_y, "Performance")
        hw_y += line_height

        self._add_label("CPU Cores:", right_x, hw_y, "Performance")
        self._perf_labels['cpu_cores'] = self._add_value_label("N/A", right_x + 80, hw_y, "Performance")
        hw_y += line_height + 5

        # Circle and Polygon caches on right column below hardware
        self._add_label("Circle Cache:", right_x, hw_y, "Performance")
        self._perf_labels['circle_cache'] = self._add_value_label("0 B", right_x + 80, hw_y, "Performance")
        hw_y += line_height

        self._add_label("Polygon Cache:", right_x, hw_y, "Performance")
        self._perf_labels['polygon_cache'] = self._add_value_label("0 B", right_x + 80, hw_y, "Performance")

    def _add_label(self, text, x, y, tab_name, font_size=None):
        if font_size is None:
            font_size = int(14 * self.scale)
        label = TextLabel(x, y, text, font_size, color=self.style.text_color)
        self.tabs.add_to_tab(tab_name, label)
        return label

    def _add_value_label(self, initial_text, x, y, tab_name):
        label = TextLabel(x, y, initial_text, int(14 * self.scale), color=(220, 220, 100))
        self.tabs.add_to_tab(tab_name, label)
        return label

    def _update_performance_tab(self):
        """Refresh all performance metrics and hardware info."""
        if not self.visible or not hasattr(self, '_perf_labels'):
            return

        pm = self.engine.performance_monitor
        stats = pm.get_stats()

        self._perf_labels['fps'].set_text(f"{stats.get('current_fps', 0):.1f}")
        self._perf_labels['avg_fps'].set_text(f"{stats.get('average_fps', 0):.1f}")
        self._perf_labels['p1_fps'].set_text(f"{stats.get('percentile_1', 0):.1f}")
        self._perf_labels['p01_fps'].set_text(f"{stats.get('percentile_01', 0):.1f}")
        self._perf_labels['frame_time'].set_text(f"{stats.get('frame_time_ms', 0):.2f} ms")

        scene = self.engine.current_scene
        if scene:
            self._perf_labels['ui_count'].set_text(str(len(scene.ui_elements)))
            if hasattr(scene, 'particle_system'):
                self._perf_labels['particles'].set_text(str(scene.particle_system.active_particles))
            else:
                self._perf_labels['particles'].set_text("0")
            scene_update = pm.get_timing('scene')
            scene_render = pm.get_timing('render')
            self._perf_labels['scene_update'].set_text(f"{scene_update.duration:.2f} ms" if scene_update else "0.00 ms")
            self._perf_labels['scene_render'].set_text(f"{scene_render.duration:.2f} ms" if scene_render else "0.00 ms")
        else:
            self._perf_labels['ui_count'].set_text("0")
            self._perf_labels['particles'].set_text("0")
            self._perf_labels['scene_update'].set_text("0.00 ms")
            self._perf_labels['scene_render'].set_text("0.00 ms")

        # Cache stats
        renderer = self.engine.renderer
        if isinstance(renderer, OpenGLRenderer):
            cache = renderer.get_cache_usage('all', humanize=True)
            self._perf_labels['text_cache'].set_text(cache.get('text', '0 B'))
            self._perf_labels['texture_cache'].set_text(cache.get('texture', '0 B'))
            self._perf_labels['circle_cache'].set_text(cache.get('circle', '0 B'))
            self._perf_labels['polygon_cache'].set_text(cache.get('polygon', '0 B'))
            self._perf_labels['total_cache'].set_text(cache.get('total', '0 B'))
        else:
            self._perf_labels['text_cache'].set_text("N/A")
            self._perf_labels['texture_cache'].set_text("N/A")
            self._perf_labels['circle_cache'].set_text("N/A")
            self._perf_labels['polygon_cache'].set_text("N/A")
            self._perf_labels['total_cache'].set_text("N/A")

        # Hardware info
        hw = pm.get_hardware_info()
        self._perf_labels['os'].set_text(f"{hw.get('system', 'N/A')} {hw.get('release', '')}")
        self._perf_labels['cpu'].set_text(self._get_cpu_model())
        self._perf_labels['gpu'].set_text(self._get_gpu_info())
        self._perf_labels['ram_total'].set_text(hw.get('memory_total_gb', 'N/A'))
        self._perf_labels['ram_avail'].set_text(hw.get('memory_available_gb', 'N/A'))
        self._perf_labels['python'].set_text(hw.get('python_version', 'N/A'))
        self._perf_labels['pygame'].set_text(hw.get('pygame_version', 'N/A'))
        cores = hw.get('cpu_cores', 'N/A')
        logical = hw.get('cpu_logical_cores', '')
        self._perf_labels['cpu_cores'].set_text(f"{cores} ({logical})")

    def _get_cpu_model(self) -> str:
        """Extract a friendly CPU model name from platform.processor() or other sources."""
        proc_str = platform.processor()
        if not proc_str or proc_str == "":
            proc_str = platform.uname().processor or "Unknown CPU"

        # Patterns for common CPU families
        patterns = [
            # AMD Ryzen
            r'Ryzen\s+\d+\s+\d+[A-Z]*',
            r'Ryzen\s+\d+\s+Threadripper',
            r'Ryzen\s+Threadripper',
            r'Ryzen\s+\d+',
            # AMD older
            r'FX[-\s]?\d+',
            r'Athlon[-\s]?\d+',
            # Intel Core
            r'Core\s+[iI]\d+[-\s]?\d+[A-Z]*',
            r'Core\s+[iI]\d+',
            r'Celeron\s+[A-Za-z0-9]+',
            r'Pentium\s+[A-Za-z0-9]+',
            # Intel Xeon
            r'Xeon\s+[A-Za-z0-9]+[\-\s]+\d+v\d+',
            r'Xeon\s+[A-Za-z0-9]+',
            # Generic patterns
            r'AMD\s+[A-Za-z0-9\-\s]+',
            r'Intel[()]+\s+[A-Za-z0-9\-\s]+',
        ]
        for pattern in patterns:
            match = re.search(pattern, proc_str, re.IGNORECASE)
            if match:
                model = match.group(0).strip()
                model = re.sub(r'\s+', ' ', model)
                return model[:40]
        return proc_str[:40] if proc_str else "Unknown CPU"

    def _get_gpu_info(self) -> str:
        """Extract clean GPU model name from OpenGL renderer string."""
        try:
            from OpenGL.GL import glGetString, GL_RENDERER
            renderer_str = glGetString(GL_RENDERER).decode()
            patterns = [
                r'GeForce\s+RTX\s+\d+\s*[A-Z]*',
                r'GeForce\s+GTX\s+\d+',
                r'Radeon\s+RX\s+\d+\s*[A-Z]*',
                r'Radeon\s+HD\s+\d+',
                r'Intel[)]*\s+[A-Za-z]+\s+Graphics\s+\d+',
                r'Arc\s+[A-Za-z0-9]+',
            ]
            for pattern in patterns:
                match = re.search(pattern, renderer_str, re.IGNORECASE)
                if match:
                    return match.group(0).strip()
            cleaned = renderer_str.replace('NVIDIA Corporation - ', '').replace('NVidia ', '')
            cleaned = cleaned.split('/')[0].split('(')[0].strip()
            if len(cleaned) > 40:
                cleaned = cleaned[:40]
            return cleaned
        except Exception:
            return "OpenGL (unknown)"

    # ------------------------------------------------------------------
    # Hierarchy navigation methods (fixed)
    # ------------------------------------------------------------------
    def _build_root_hierarchy(self):
        """Reset stack and show top‑level UI elements from current scene."""
        self.hierarchy_stack.clear()
        root_elements = self.engine.current_scene.ui_elements if self.engine.current_scene else []
        self._current_display_elements = root_elements.copy()
        self._build_hierarchy_view(root_elements)

    def _build_hierarchy_view(self, elements: List[UIElement]):
        self._current_display_elements = elements.copy()
        self.hierarchy_scrolling.clear_content()

        y_offset = 5

        if self.hierarchy_stack:
            back_btn = Button(5, y_offset, 50, 24, "..", 14, root_point=(0, 0))
            back_btn.set_on_click(self._navigate_back)
            self.hierarchy_scrolling.add_child(back_btn)
            y_offset += 30

        for elem in elements:
            btn_text = f"{elem.element_type} [{elem.element_id}]"
            btn = Button(5, y_offset, self.hierarchy_scrolling.width - 20, 28, btn_text, 14, root_point=(0, 0))
            btn.set_on_click(lambda e=elem: self._on_element_click_with_cooldown(e))
            self.hierarchy_scrolling.add_child(btn)
            y_offset += 32

        self.hierarchy_scrolling.content_height = max(self.hierarchy_scrolling.height, y_offset + 10)

    def _navigate_back(self):
        """Navigate back one level in hierarchy (with cooldown)."""
        now = time.time()
        if now - self._last_back_time < 0.2:
            return
        self._last_back_time = now

        if self.hierarchy_stack:
            previous_list = self.hierarchy_stack.pop()
            self._build_hierarchy_view(previous_list)
        else:
            # Should not happen because back button only shown when stack not empty
            self._build_root_hierarchy()

    def _on_element_click_with_cooldown(self, element: UIElement):
        now = time.time()
        if now - self._last_element_click_time < 0.2:
            return
        self._last_element_click_time = now
        self._on_element_click(element)

    def _on_element_click(self, element: UIElement):
        self._show_element_properties(element)
        if element.children:
            # Save current list before descending
            self.hierarchy_stack.append(self._current_display_elements)
            self._build_hierarchy_view(element.children)

    # ------------------------------------------------------------------
    # Properties display
    # ------------------------------------------------------------------
    def _show_element_properties(self, element: UIElement):
        self.properties_frame.clear_content()
        title = TextLabel(5, 5, f"Properties of {element.element_type} [{element.element_id}]",
                          int(16*self.scale), color=self.style.text_color)
        self.properties_frame.add_child(title)

        y = 35
        props = getattr(element, '_properties', {})
        for prop_name, prop_info in props.items():
            display_name = prop_info.get('name', prop_name)
            value = getattr(element, prop_info.get('key', prop_name), None)
            value_str = repr(value) if value is not None else "None"
            line = TextLabel(5, y, f"{display_name}: {value_str}", int(14*self.scale), color=(200,200,200))
            self.properties_frame.add_child(line)
            y += 25

        if not props:
            msg = TextLabel(5, y, "No editable properties", int(14*self.scale), color=(150,150,150))
            self.properties_frame.add_child(msg)

        self.properties_frame.content_height = max(self.properties_frame.height, y + 30)

    # ------------------------------------------------------------------
    # Overlays management
    # ------------------------------------------------------------------
    def getOverlays(self) -> List[str]:
        return [str(ovr.__name__)[:16] for ovr in DebugOverlay.__subclasses__()]

    def _add_overlay(self):
        overlay_name = self.overlays_dropdown.get_selected()[1]
        overlay_cls = next((ovr for ovr in DebugOverlay.__subclasses__() if str(ovr.__name__)[:16] == overlay_name), None)
        if overlay_cls and not any(isinstance(ovr, overlay_cls) for ovr in self.debug_manager.overlays):
            overlay = overlay_cls(self.engine)
            self.debug_manager.add_overlay(overlay)
            self.update_overlays_scrolling()

    def update_overlays_scrolling(self):
        self.overlays_scrolling.clear_content()
        y = 0
        for ovr in self.debug_manager.overlays:
            if isinstance(ovr, LiveInspector):
                continue
            fr = UiFrame(10, y, self.overlays_scrolling.width - 20, 32)
            fr.add_child(TextLabel(5, 16, str(type(ovr).__name__), int(18*self.scale), root_point=(0, 0.5)))
            hide_btn = Button(fr.width - 5, 16, 50, 24, "Hide", int(16*self.scale), root_point=(1, 0.5))
            hide_btn.set_on_click(lambda ovr=ovr: setattr(ovr, 'visible', not ovr.visible))
            fr.add_child(hide_btn)
            delete_btn = Button(fr.width - 60, 16, 50, 24, "Remove", int(16*self.scale), root_point=(1, 0.5))
            delete_btn.set_on_click(lambda ovr=ovr: self.debug_manager.remove_overlay(ovr, callback=self.update_overlays_scrolling))
            fr.add_child(delete_btn)
            self.overlays_scrolling.add_child(fr)
            y += 32

    def set_debug_manager(self, dm: 'DebugManager'):
        self.debug_manager = dm

    def close(self):
        self.visible = False

    def toggle_fixed(self):
        self.pinned = not self.pinned

    def update(self, dt: float, input_state: InputState):
        if not self.visible:
            return
        super().update(dt, input_state)
        self._update_performance_tab()


# ----------------------------------------------------------------------
# DebugManager
# ----------------------------------------------------------------------

class DebugManager:
    def __init__(self, engine: 'LunaEngine') -> None:
        self.engine = engine
        self.overlays: List[DebugOverlay] = []
        self.live_inspector: Optional[LiveInspector] = None
        self.debug_enabled: bool = engine.debug_enabled

        @engine.on_event(pygame.KEYDOWN)
        def _toggle_inspector(event: pygame.event.Event) -> None:
            # Only allow toggling if debug is enabled and the LiveInspector exists
            if not self.debug_enabled:
                return
            if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_F12:
                if self.live_inspector:
                    self.live_inspector.visible = not self.live_inspector.visible

    def add_overlay(self, overlay: DebugOverlay) -> None:
        self.overlays.append(overlay)
        if isinstance(overlay, LiveInspector):
            self.live_inspector = overlay
            overlay.set_debug_manager(self)
            # Ensure LiveInspector starts hidden
            overlay.visible = False

    def remove_overlay(self, overlay: DebugOverlay, callback: Optional[Callable] = None) -> None:
        if overlay in self.overlays:
            self.overlays.remove(overlay)
        if overlay is self.live_inspector:
            self.live_inspector = None

        if callback and callable(callback):
            callback()

    def toggle_all(self) -> None:
        for overlay in self.overlays:
            overlay.visible = not overlay.visible

    def update(self, dt: float, input_state: InputState) -> None:
        # Only update overlays if debugging is enabled
        if not self.debug_enabled:
            return
        for overlay in self.overlays:
            overlay.update(dt, input_state)

    def render(self, renderer: OpenGLRenderer) -> None:
        # Only render overlays if debugging is enabled
        if not self.debug_enabled:
            return
        for overlay in self.overlays:
            overlay.render(renderer)