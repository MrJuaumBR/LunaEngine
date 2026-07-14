"""
Debug overlay system - draggable panels, live inspector, and performance monitoring.

LOCATION: 'LunaEngine'/misc/debug.py
"""

import json
import time
import inspect
import re
import platform
import sys
import datetime
from typing import Callable, List, Dict, Any, Literal, Optional, Tuple, Union, TYPE_CHECKING, Type
from dataclasses import dataclass, field
from enum import Enum

import pygame

from ..backend.opengl import OpenGLRenderer
from ..backend.types import InputState, Color
from .. import __version__

if TYPE_CHECKING:
    from ..core.engine import LunaEngine


# ----------------------------------------------------------------------
# Base draggable overlay
# ----------------------------------------------------------------------

from ..ui.elements.base import UIElement, FontManager, UIState, ElementStyle
from ..ui.elements.containers import UiFrame, ScrollingFrame, Tabination, ColorPicker
from ..ui.elements.selectors import Dropdown, Checkbox, Slider, NumberSelector
from ..ui.elements.buttons import Button
from ..ui.elements.labels import TextLabel
from ..ui.elements.textinputs import TextBox
from ..ui.themes import ThemeManager, ThemeStyle


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
        text_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        self.engine = engine
        self.theme = ThemeManager.get_theme()
        self.scale:float = self.engine.height / 600 or 1.0
        self.x = x
        self.y = y
        self.width = int(width * self.scale)
        self.height = int(height * self.scale)
        self.title = title
        self.background_color = (*self.theme.background.color, 0.5)
        self.header_color = (*self.theme.accent1.color, 0.75)
        self.text_color = self.theme.text_primary.color
        self.corner_radius = self.theme.background.corner_radius
        self.visible = True

        self.font = FontManager.get_font(None, int(15 * self.scale))
        self.header_font = FontManager.get_font(None, int(17 * self.scale))
        self.header_height = int(28 * self.scale)
        self.button_size = int(18 * self.scale)
        self.button_margin = int(6 * self.scale)

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
        renderer.draw_rect(self.x, self.y, self.width, self.height, self.background_color, corner_radius=self.corner_radius)
        renderer.draw_rect(self.x, self.y, self.width, self.header_height, self.header_color, corner_radius=self.corner_radius)
        renderer.draw_text(self.title, int(self.x + 8 * self.scale), int(self.y + 6*self.scale), self.text_color, self.header_font)

        lock_char = 'L' if self._fixed else 'U'
        renderer.draw_text(lock_char, int(self.lock_btn_rect.x + 4 * self.scale), self.lock_btn_rect.y, self.text_color, self.font)
        renderer.draw_text('X', int(self.close_btn_rect.x + 4 * self.scale), self.close_btn_rect.y, (255, 100, 100), self.font)

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
        y = self.y + self.header_height + 5 * self.scale
        renderer.draw_text(f"{self.current_fps:.1f} fps", self.x + (10 * self.scale), y, self.text_color, self.font)
        renderer.draw_text(f"Avg: {self.avg_fps:.1f} fps", self.x + (10 * self.scale), y + 18*self.scale, self.text_color, self.font)
        renderer.draw_text(f"Frame: {self.frame_time:.2f} ms", self.x + (10 * self.scale), y + 36*self.scale, self.text_color, self.font)

    def update(self, dt: float, input_state: InputState) -> None:
        if not self.visible:
            return

        mouse_pos = input_state.mouse_pos
        left_held = input_state.mouse_buttons_pressed.left
        left_just = input_state.mouse_just_pressed and left_held

        header_rect = pygame.Rect(self.x, self.y, int(self.width * self.scale), int(self.header_height * self.scale))
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
# Sound Overlay
# ----------------------------------------------------------------------

class SoundOverlay(DebugOverlay):
    def __init__(self, engine: 'LunaEngine', x: int = 420, y: int = 10) -> None:
        super().__init__(engine, x, y, width=200, height=90, title="Sound")
        self.master_volume = 1.0
        self.source_count = 0
        self.playing_count = 0

    def refresh(self, dt: float) -> None:
        audio = self.engine.audio
        if audio and hasattr(audio, 'backend') and audio.backend:
            self.master_volume = audio.master_volume if hasattr(audio, 'master_volume') else 1.0
            self.source_count = len(audio.backend.sources) if hasattr(audio.backend, 'sources') else 0
            self.playing_count = sum(1 for s in audio.backend.sources if s.is_playing()) if hasattr(audio.backend, 'sources') else 0
        else:
            self.master_volume = 1.0
            self.source_count = 0
            self.playing_count = 0

    def render_content(self, renderer: OpenGLRenderer) -> None:
        y = self.y + self.header_height + 5
        renderer.draw_text(f"Master: {self.master_volume:.2f}", self.x + 10, y, self.text_color, self.font)
        renderer.draw_text(f"Sources: {self.source_count}", self.x + 10, y + 24, self.text_color, self.font)
        renderer.draw_text(f"Playing: {self.playing_count}", self.x + 10, y + 48, self.text_color, self.font)

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
# Clock Overlay
# ----------------------------------------------------------------------

class ClockOverlay(DebugOverlay):
    def __init__(self, engine: 'LunaEngine', x: int = 10, y: int = 110) -> None:
        super().__init__(engine, x, y, width=160, height=70, title="Clock")
        self.time_str = ""
        self.date_str = ""

    def refresh(self, dt: float) -> None:
        now = datetime.datetime.now()
        self.time_str = now.strftime("%H:%M:%S")
        self.date_str = now.strftime("%Y-%m-%d")

    def render_content(self, renderer: OpenGLRenderer) -> None:
        y = self.y + self.header_height + 5
        renderer.draw_text(self.time_str, self.x + 10, y, self.text_color, self.font)
        renderer.draw_text(self.date_str, self.x + 10, y + 24, self.text_color, self.font)

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
# Version Overlay
# ----------------------------------------------------------------------

class VersionOverlay(DebugOverlay):
    def __init__(self, engine: 'LunaEngine', x: int = 180, y: int = 110) -> None:
        super().__init__(engine, x, y, width=200, height=120, title="Version")
        self.luna_version = __version__
        self.python_version = sys.version.split()[0]
        self.pygame_version = pygame.version.ver
        self.opengl_version = ""

    def refresh(self, dt: float) -> None:
        try:
            from OpenGL.GL import glGetString, GL_VERSION
            self.opengl_version = glGetString(GL_VERSION).decode().split()[0]
        except:
            self.opengl_version = "N/A"

    def render_content(self, renderer: OpenGLRenderer) -> None:
        y = self.y + self.header_height + 5
        renderer.draw_text(f"Luna: {self.luna_version}", self.x + 10, y, self.text_color, self.font)
        renderer.draw_text(f"Python: {self.python_version}", self.x + 10, y + 24, self.text_color, self.font)
        renderer.draw_text(f"Pygame: {self.pygame_version}", self.x + 10, y + 48, self.text_color, self.font)
        renderer.draw_text(f"OpenGL: {self.opengl_version}", self.x + 10, y + 72, self.text_color, self.font)

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
# Live Inspector – now a UiFrame (draggable, with header) AND auto-registers with scene
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
        self._scene_name = None
        
        # Console
        self.console_log_manager = ConsoleLogManager()
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._redirect_console_output()
        
        # Custom Functions
        self.custom_functions = {}  # name -> {callable, parameters, description}
        self._current_custom_func = None
        
        self._setup_content(engine)
        # Initially not in scene; will be added when set_visible(True)
        self._registered = False

    # ------------------------------------------------------------------
    # Scene registration
    # ------------------------------------------------------------------
    def _update_scene_registration(self):
        """Add or remove this inspector from the current scene's ui_elements."""
        scene = self.engine.current_scene
        if not scene:
            return
        if self.visible:
            if self not in scene.ui_elements:
                scene.add_ui_element(self)
                self._registered = True
        else:
            if self in scene.ui_elements:
                scene.remove_ui_element(self)
                self._registered = False

    def set_visible(self, visible: bool):
        """Override visibility to handle scene registration."""
        if self.visible == visible:
            return
        self.visible = visible
        self._update_scene_registration()

    def close(self):
        """Called by header close button."""
        self.set_visible(False)
        self._restore_console()

    def toggle_fixed(self):
        """Called by header lock button."""
        self.pinned = not self.pinned
        self.draggable = not self.pinned  # lock disables dragging

    def on_scene_changed(self):
        """Called by debug manager when the active scene changes."""
        self._update_scene_registration()
        # Refresh hierarchy for the new scene
        self._build_root_hierarchy()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _setup_content(self, engine: 'LunaEngine'):
        usable = self.usable_space
        scale = (self.engine.height / 600)
        self.scale = scale

        self.tabs = Tabination(
            self.width // 2, self.height - 6,
            usable[0] - 2, usable[1] - 2,
            int(max(18 * scale, 18)),
            pivot=(0.5, 1)
        )
        self.add_child(self.tabs)

        self.tabs.add_tab("Elements")
        self.tabs.add_tab("Console")
        self.tabs.add_tab("Custom Function")
        self.tabs.add_tab("Performance")
        self.tabs.add_tab("Audio")
        self.tabs.add_tab("Overlays")
        self.tabs.add_tab("Settings")

        self.tabs.add_to_tab("Elements", TextLabel(5, 5, "Scene Elements", int(18*scale), color=self.style.text_color))
        self.tabs.add_to_tab("Console", TextLabel(5, 5, "Console", int(18*scale), color=self.style.text_color))
        self.tabs.add_to_tab("Custom Function", TextLabel(5, 5, "Custom Function", int(18*scale), color=self.style.text_color))
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
            scrollbar_size=3,
            auto_arrange_y=True,
            arrange_spacing=10
        )
        self.properties_frame.add_child(TextLabel(5, 5, "Properties", int(18*scale), color=self.style.text_color))
        self.tabs.add_to_tab("Elements", self.properties_frame)

        # ---------- Console tab ----------
        self._setup_console_tab()
        
        # ---------- Custom Functions ----------
        self._setup_custom_tab()

        # ---------- Performance Tab ----------
        self._setup_performance_tab()

        # ---------- Settings tab ----------
        self.themes_dropdown = Dropdown(5*scale, 35*scale, 150*scale, 23*scale, list(self.engine.get_all_themes().keys()), int(16*scale))
        self.themes_dropdown.set_on_selection_changed(lambda index, name: self.engine.set_global_theme(name))
        self.tabs.add_to_tab("Settings", self.themes_dropdown)

        # Dark mode toggle
        self.dark_mode_toggle = Checkbox(
            int(160 * scale), int(35 * scale),
            int(20 * scale), int(20 * scale),
            ThemeManager.get_dark_mode(),
            label="Dark",
        )
        self.dark_mode_toggle.set_on_toggle(lambda val: ThemeManager.set_dark_mode(val))
        self.tabs.add_to_tab("Settings", self.dark_mode_toggle)

        # Set dropdown to current theme
        current_theme_name = ThemeManager.get_current_theme().value
        theme_names = list(self.engine.get_all_themes().keys())
        if current_theme_name in theme_names:
            self.themes_dropdown.selected_index = theme_names.index(current_theme_name)
        else:
            self.themes_dropdown.selected_index = 0

        # Force Kill button - now kills the engine
        self.force_kill_btn = Button(5*scale, 60*scale, 120*scale, 23*scale, "Force Kill", int(16*scale))
        self.force_kill_btn.set_on_click(self._force_kill)
        self.tabs.add_to_tab("Settings", self.force_kill_btn)

        # Re-init game button - reloads current scene
        self.reinit_btn = Button(5*scale, 85*scale, 120*scale, 23*scale, "Re-init Game", int(16*scale))
        self.reinit_btn.set_on_click(self._reinit_game)
        self.tabs.add_to_tab("Settings", self.reinit_btn)

        # Clear all caches button
        self.clear_cache_btn = Button(5*scale, 110*scale, 120*scale, 23*scale, "Clear Cache", int(16*scale))
        self.clear_cache_btn.set_on_click(self._clear_all_caches)
        self.tabs.add_to_tab("Settings", self.clear_cache_btn)

        # ---------- Overlays tab ----------
        self.overlays_dropdown = Dropdown(5*scale, 35*scale, 110*scale, 23*scale, self.getOverlays(), int(16*scale))
        self.add_overlay_btn = Button(120*scale, 35*scale, 80*scale, 23*scale, "Add Overlay", int(16*scale))
        self.add_overlay_btn.set_on_click(self._add_overlay)
        self.tabs.add_to_tab("Overlays", self.overlays_dropdown)
        self.tabs.add_to_tab("Overlays", self.add_overlay_btn)
        self.overlays_scrolling = ScrollingFrame(5*scale, 70*scale, self.tabs.width - 10, 200, self.tabs.width - 10, 400)
        self.tabs.add_to_tab("Overlays", self.overlays_scrolling)

        # ---------- Audio Tab ----------
        self._setup_audio_tab()

        self._build_root_hierarchy()

    # ------------------------------------------------------------------
    # Audio Tab Setup
    # ------------------------------------------------------------------
    def _setup_audio_tab(self):
        """Create the audio control tab with master volume, effects, and source list."""
        scale = self.scale
        tab_width = self.tabs.width

        # Title
        title = TextLabel(5, 5, "Audio Controls", int(20*scale), color=self.style.text_color)
        self.tabs.add_to_tab("Audio", title)

        # Master Volume
        self._add_label("Master Vol:", 10, 28*scale, "Audio")
        self.master_volume_slider = Slider(
            90*scale, 28*scale,
            150, 16,
            0.0, 1.0, 1.0,
            pivot=(0, 0)
        )
        self.master_volume_slider.set_on_value_changed(self._on_master_volume_changed)
        self.tabs.add_to_tab("Audio", self.master_volume_slider)
        self.master_volume_label = self._add_value_label("1.00", 250*scale, 28*scale, "Audio")

        # Effects Section
        self._add_label("Effects:", 10, 44*scale, "Audio", font_size=int(16*scale))

        # Effect type dropdown (smaller)
        effect_types = ["Reverb", "Echo", "Chorus", "Flanger", "Distortion", "Pitch Shift"]
        self.effect_dropdown = Dropdown(
            10*scale, 60*scale,
            100, 20,
            effect_types,
            int(16*scale),
            pivot=(0,0)
        )
        self.tabs.add_to_tab("Audio", self.effect_dropdown)

        # Effect intensity slider
        self._add_label("Intensity:", 120*scale, 60*scale, "Audio")
        self.effect_slider = Slider(
            180*scale, 70*scale,
            90, 16,
            0.0, 1.0, 0.5,
            pivot=(0, 0)
        )
        self.tabs.add_to_tab("Audio", self.effect_slider)
        self.effect_label = self._add_value_label("0.50", 280*scale, 60*scale, "Audio")

        # Apply effect button (smaller)
        apply_effect_btn = Button(310*scale, 65*scale, 70, 24, "Apply", int(14*scale))
        apply_effect_btn.set_on_click(self._apply_effect)
        self.tabs.add_to_tab("Audio", apply_effect_btn)

        # Source list title
        self._add_label("Audio Sources:", 10, 85*scale, "Audio", font_size=int(14*scale))

        # Scrollable frame for sources
        self.audio_sources_frame = ScrollingFrame(
            10*scale, 95*scale,
            tab_width - 20, 135*scale,
            tab_width - 20, 400*scale,
            scrollbar_size=8
        )
        self.tabs.add_to_tab("Audio", self.audio_sources_frame)

        # Refresh sources button (smaller)
        refresh_sources_btn = Button(10*scale, 240*scale, 80, 24, "Refresh", int(12*scale))
        refresh_sources_btn.set_on_click(self._update_audio_sources)
        self.tabs.add_to_tab("Audio", refresh_sources_btn)

        # Update source list initially
        self._update_audio_sources()

    def _update_audio_sources(self):
        """Refresh the list of audio sources in the scrollable frame."""
        self.audio_sources_frame.clear_content()
        y = 5
        audio = self.engine.audio

        if audio is None:
            label = TextLabel(5*self.scale, 5*self.scale, "Audio manager not available", int(14*self.scale), (200, 100, 100))
            self.audio_sources_frame.add_child(label)
            return

        if not hasattr(audio, 'backend') or audio.backend is None:
            label = TextLabel(5*self.scale, 5*self.scale, "Audio backend not initialized", int(14*self.scale), (200, 100, 100))
            self.audio_sources_frame.add_child(label)
            return

        if not audio.backend.is_initialized():
            label = TextLabel(5*self.scale, 5*self.scale, "OpenAL not available", int(14*self.scale), (200, 100, 100))
            self.audio_sources_frame.add_child(label)
            return

        sources = audio.backend.sources if hasattr(audio.backend, 'sources') else []
        if not sources:
            label = TextLabel(5*self.scale, 5*self.scale, "No audio sources available", int(14*self.scale), (200, 200, 200))
            self.audio_sources_frame.add_child(label)
            return

        for idx, src in enumerate(sources):
            # Container for each source (smaller)
            frame = UiFrame(5*self.scale, y*self.scale, self.audio_sources_frame.width - 20*self.scale, 30*self.scale)
            frame.set_background_color((40, 40, 50, 180))
            frame.set_corner_radius(3)

            # Source label
            label = TextLabel(5*self.scale, 15*self.scale, f"Source {idx}", int(16*self.scale), (200, 200, 200), pivot=(0, 0.5))
            frame.add_child(label)

            # Volume slider
            vol_label = TextLabel(70*self.scale, 15*self.scale, "Vol:", int(14 *self.scale), (200, 200, 200), pivot=(0, 0.5))
            frame.add_child(vol_label)
            vol_slider = Slider(100*self.scale, 10*self.scale, 40*self.scale, 14*self.scale, 0.0, 1.0, src.volume if hasattr(src, 'volume') else 1.0, pivot=(0, 0.5))
            vol_slider.set_on_value_changed(lambda v, s=src: self._on_source_volume_changed(s, v))
            frame.add_child(vol_slider)

            # Pan slider
            pan_label = TextLabel(155*self.scale, 15*self.scale, "Pan:", int(14*self.scale), (200, 200, 200), pivot=(0, 0.5))
            frame.add_child(pan_label)
            pan_slider = Slider(175*self.scale, 10*self.scale, 40*self.scale, 14*self.scale, -1.0, 1.0, src.pan if hasattr(src, 'pan') else 0.0, pivot=(0, 0.5))
            pan_slider.set_on_value_changed(lambda v, s=src: self._on_source_pan_changed(s, v))
            frame.add_child(pan_slider)

            # Playing indicator
            is_playing = src.is_playing() if hasattr(src, 'is_playing') else False
            status_text = "Playing" if is_playing else "Stopped"
            status_label = TextLabel(230*self.scale, 15*self.scale, status_text, int(14*self.scale), (100, 255, 100) if is_playing else (200, 200, 200), pivot=(0, 0.5))
            frame.add_child(status_label)

            self.audio_sources_frame.add_child(frame)
            y += 32

        # Set content height to allow scrolling if needed
        self.audio_sources_frame.content_height = max(self.audio_sources_frame.height, y + 10)

    def _on_master_volume_changed(self, value: float):
        """Update master volume."""
        audio = self.engine.audio
        if audio and hasattr(audio, 'set_master_volume'):
            audio.set_master_volume(value)
            if hasattr(self, 'master_volume_label'):
                self.master_volume_label.set_text(f"{value:.2f}")

    def _on_source_volume_changed(self, source, value: float):
        """Update source volume."""
        if hasattr(source, 'set_volume_immediate'):
            source.set_volume_immediate(value)

    def _on_source_pan_changed(self, source, value: float):
        """Update source pan."""
        if hasattr(source, 'set_pan_immediate'):
            source.set_pan_immediate(value)

    def _apply_effect(self):
        """Apply the selected effect with the current intensity to all channels."""
        audio = self.engine.audio
        if not audio:
            return
        effect_name = self.effect_dropdown.get_selected()[1]
        intensity = self.effect_slider.value
        self.effect_label.set_text(f"{intensity:.2f}")

        # Map effect name to method
        if effect_name == "Reverb":
            if hasattr(audio, 'set_global_reverb'):
                audio.set_global_reverb(intensity)
                print(f"Applied Reverb with intensity {intensity:.2f}")
        elif effect_name == "Echo":
            if hasattr(audio, 'set_global_echo'):
                audio.set_global_echo(intensity)
                print(f"Applied Echo with intensity {intensity:.2f}")
        elif effect_name == "Chorus":
            if hasattr(audio, 'set_global_chorus'):
                audio.set_global_chorus(intensity)
                print(f"Applied Chorus with intensity {intensity:.2f}")
        elif effect_name == "Flanger":
            if hasattr(audio, 'set_global_flanger'):
                audio.set_global_flanger(intensity)
                print(f"Applied Flanger with intensity {intensity:.2f}")
        elif effect_name == "Distortion":
            if hasattr(audio, 'set_global_distortion'):
                audio.set_global_distortion(intensity)
                print(f"Applied Distortion with intensity {intensity:.2f}")
        elif effect_name == "Pitch Shift":
            # Pitch shift uses semitones, map intensity 0-1 to -12 to +12 semitones
            semitones = (intensity * 24) - 12  # -12 to +12
            if hasattr(audio, 'set_global_pitch_shift'):
                audio.set_global_pitch_shift(semitones)
                print(f"Applied Pitch Shift with {semitones:.1f} semitones")
        else:
            print(f"Unknown effect: {effect_name}")

    # ------------------------------------------------------------------
    # Settings Tab Methods
    # ------------------------------------------------------------------
    def _force_kill(self):
        """Force kill the engine (quit the game)."""
        self.engine.running = False

    def _reinit_game(self):
        """Re-initialize the current scene (reloads all UI elements)."""
        scene = self.engine.current_scene
        if scene:
            scene.clear_ui_elements()
            if hasattr(scene, 'setup_ui'):
                scene.setup_ui()
            self._build_root_hierarchy()
            print("Game re-initialized.")

    def _clear_all_caches(self):
        renderer = self.engine.renderer
        if isinstance(renderer, OpenGLRenderer):
            renderer._text_cache.clear()
            renderer._text_cache_last_used.clear()
            renderer._texture_cache.clear()
            renderer._circle_cache.clear()
            renderer._polygon_cache.clear()
            print("All OpenGL caches cleared.")
        else:
            print("No OpenGL renderer to clear caches.")

    # ------------------------------------------------------------------
    # Custom Function Tab
    # ------------------------------------------------------------------
    def _setup_custom_tab(self):
        scale = self.scale
        tab_w = self.tabs.width

        # Dropdown for function selection
        self.custom_dropdown = Dropdown(
            5*scale, 35*scale,
            180*scale, 24*scale,
            ["No functions"], int(16*scale)
        )
        self.custom_dropdown.set_on_selection_changed(self._on_custom_func_selected)
        self.tabs.add_to_tab("Custom Function", self.custom_dropdown)

        # Description label
        self.custom_desc_label = TextLabel(
            5*scale, 65*scale,
            "Select a function above",
            int(14*scale), color=(200, 200, 200)
        )
        self.tabs.add_to_tab("Custom Function", self.custom_desc_label)

        # Parameter inputs container (will be rebuilt on selection)
        self.custom_params_frame = ScrollingFrame(
            5*scale, 90*scale,
            tab_w - 10*scale,
            120*scale,
            tab_w - 10*scale,
            200*scale,
            scrollbar_size=6
        )
        self.tabs.add_to_tab("Custom Function", self.custom_params_frame)

        # Execute button
        self.custom_execute_btn = Button(
            5*scale, 220*scale,
            100*scale, 28*scale,
            "Execute", int(16*scale)
        )
        self.custom_execute_btn.set_on_click(self._execute_custom_func)
        self.tabs.add_to_tab("Custom Function", self.custom_execute_btn)

        # Result label
        self.custom_result_label = TextLabel(
            115*scale, 225*scale,
            "",
            int(14*scale), color=(100, 255, 100)
        )
        self.tabs.add_to_tab("Custom Function", self.custom_result_label)

        self._refresh_custom_dropdown()
        
    def add_custom_function(self, name: str, callable_obj: Callable,
                        parameters: List[Tuple[str, type]], description: str = ""):
        """
        Register a test function.
        parameters: list of (param_name, param_type) where type is int, float, str, bool.
        """
        self.custom_functions[name] = {
            'callable': callable_obj,
            'parameters': parameters,
            'description': description
        }
        self._refresh_custom_dropdown()
        
        if self.custom_functions:
            first_name = list(self.custom_functions.keys())[0]
            self.custom_dropdown.selected_index = 0
            # Ensure dropdown displays the first name, not "No functions"
            if hasattr(self.custom_dropdown, '_update_display'):
                self.custom_dropdown._update_display()
            self._on_custom_func_selected(0, first_name)
    
    def _on_custom_func_selected(self, index: int, name: str):
        self.custom_params_frame.clear_content()
        self.custom_desc_label.set_text("")
        self.custom_result_label.set_text("")

        if name == "No functions" or name not in self.custom_functions:
            return

        func_info = self.custom_functions[name]
        self.custom_desc_label.set_text(func_info['description'])

        # Build parameter input fields
        y = 5
        self._param_inputs = {}  # store references to input widgets
        for param_name, param_type in func_info['parameters']:
            # Label
            label = TextLabel(5, y, f"{param_name} ({param_type.__name__}):",
                            int(14*self.scale), color=(200,200,200))
            self.custom_params_frame.add_child(label)

            # Input widget based on type
            if param_type is int:
                widget = NumberSelector(
                    150, y, 100, 22,
                    min_value=-1000, max_value=1000,
                    value=0, label="", label_size=0
                )
            elif param_type is float:
                widget = NumberSelector(
                    150, y, 100, 22,
                    min_value=-1000.0, max_value=1000.0,
                    value=0.0, label="", label_size=0, step=0.1
                )
            elif param_type is str:
                widget = TextBox(
                    150, y, 100, 22,
                    font_size=int(16*self.scale), label="", label_size=0
                )
            elif param_type is bool:
                widget = Checkbox(
                    150, y, 20, 20,
                    False, label=""
                )
            else:
                widget = TextLabel(150, y+2, "Unsupported type", int(14*self.scale), color=(255,100,100))

            self.custom_params_frame.add_child(widget)
            self._param_inputs[param_name] = (widget, param_type)
            y += 28

        self.custom_params_frame.content_height = max(self.custom_params_frame.height, y + 10)
        self.custom_params_frame.scroll_y = 0

    def _refresh_custom_dropdown(self):
        names = list(self.custom_functions.keys())
        if not names:
            names = ["No functions"]
        elif names and len(names) >= 1:
            self.custom_dropdown.set_options(names, 0)
            
            first_name = names[0] if names else "No functions"
            self._on_custom_func_selected(0, first_name)
        
    def _execute_custom_func(self):
        func_name = self.custom_dropdown.get_selected()[1]
        if func_name == "No functions" or func_name not in self.custom_functions:
            return

        func_info = self.custom_functions[func_name]
        args = []
        try:
            for param_name, (widget, ptype) in self._param_inputs.items():
                if ptype is int:
                    val = int(widget.value)
                elif ptype is float:
                    val = float(widget.value)
                elif ptype is str:
                    val = widget.text
                elif ptype is bool:
                    val = widget.value
                else:
                    val = None
                args.append(val)

            result = func_info['callable'](*args)
            self.custom_result_label.set_text(f"[s] > Result: {result}")
            # Also send to console
            self.console_log_manager.add_log(LogLevel.INFO, f"Custom function '{func_name}' returned: {result}")
        except Exception as e:
            self.custom_result_label.set_text(f"[x] > Error: {e}")
            self.console_log_manager.add_log(LogLevel.ERROR, f"Custom function '{func_name}' error: {e}")

    # ------------------------------------------------------------------
    # Performance Tab
    # ------------------------------------------------------------------
    def _setup_performance_tab(self):
        scale = self.scale
        tab_width = self.tabs.width

        title = TextLabel(5, 5, "Performance Metrics", int(20*scale), color=self.style.text_color)
        self.tabs.add_to_tab("Performance", title)

        left_x = 10
        right_x = tab_width // 2 + 10
        line_height = int(17 * scale)
        y_offset = 33

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

        self._add_label("Scene Update:", left_x, y_offset, "Performance")
        self._perf_labels['scene_update'] = self._add_value_label("0.00 ms", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Scene Render:", left_x, y_offset, "Performance")
        self._perf_labels['scene_render'] = self._add_value_label("0.00 ms", left_x + 80, y_offset, "Performance")
        y_offset += line_height + 5

        self._add_label("UI Elements:", left_x, y_offset, "Performance")
        self._perf_labels['ui_count'] = self._add_value_label("0", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Particles:", left_x, y_offset, "Performance")
        self._perf_labels['particles'] = self._add_value_label("0", left_x + 80, y_offset, "Performance")
        y_offset += line_height + 5

        self._add_label("Text Cache:", left_x, y_offset, "Performance")
        self._perf_labels['text_cache'] = self._add_value_label("0 B", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Texture Cache:", left_x, y_offset, "Performance")
        self._perf_labels['texture_cache'] = self._add_value_label("0 B", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        self._add_label("Total Cache:", left_x, y_offset, "Performance")
        self._perf_labels['total_cache'] = self._add_value_label("0 B", left_x + 80, y_offset, "Performance")
        y_offset += line_height

        hw_y = 33
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
        proc_str = platform.processor()
        if not proc_str or proc_str == "":
            proc_str = platform.uname().processor or "Unknown CPU"

        patterns = [
            r'Ryzen\s+\d+\s+\d+[A-Z]*',
            r'Ryzen\s+\d+\s+Threadripper',
            r'Ryzen\s+Threadripper',
            r'Ryzen\s+\d+',
            r'FX[-\s]?\d+',
            r'Athlon[-\s]?\d+',
            r'Core\s+[iI]\d+[-\s]?\d+[A-Z]*',
            r'Core\s+[iI]\d+',
            r'Celeron\s+[A-Za-z0-9]+',
            r'Pentium\s+[A-Za-z0-9]+',
            r'Xeon\s+[A-Za-z0-9]+[\-\s]+\d+v\d+',
            r'Xeon\s+[A-Za-z0-9]+',
            r'AMD\s+[A-Za-z0-9\-\s]+',
            r'Intel[()]+\s+[A-Za-z0-9\-\s]+',
        ]
        for pattern in patterns:
            match = re.search(pattern, proc_str, re.IGNORECASE)
            if match:
                model = match.group(0).strip()
                model = re.sub(r'\s+', ' ', model)
                return model[:26]
        return proc_str[:26] if proc_str else "Unknown CPU"

    def _get_gpu_info(self) -> str:
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
    # Hierarchy navigation methods
    # ------------------------------------------------------------------
    def _build_root_hierarchy(self):
        self.hierarchy_stack.clear()
        root_elements = self.engine.current_scene.ui_elements if self.engine.current_scene else []
        self._current_display_elements = root_elements.copy()
        self._build_hierarchy_view(root_elements)

    def recharge(self):
        self._build_root_hierarchy()

    def _build_hierarchy_view(self, elements: List[UIElement]):
        self._current_display_elements = elements.copy()
        self.hierarchy_scrolling.clear_content()

        y_offset = 5

        if self.hierarchy_stack:
            back_btn = Button(5, y_offset, 50, 24, "..", 14, pivot=(0, 0))
            back_btn.set_on_click(self._navigate_back)
            back_btn.add_group('live-inspector-ignore')
            self.hierarchy_scrolling.add_child(back_btn)
            y_offset += 30

        for elem in elements:
            if isinstance(elem, LiveInspector):
                continue
            btn_text = f"{elem.element_type} [{elem.element_id}]"
            btn = Button(5, y_offset, self.hierarchy_scrolling.width - 20, 28, btn_text, 14, pivot=(0, 0))
            btn.add_group('live-inspector-ignore')
            btn.set_on_click(lambda e=elem: self._on_element_click_with_cooldown(e))
            self.hierarchy_scrolling.add_child(btn)
            y_offset += 32

        self.hierarchy_scrolling.content_height = max(self.hierarchy_scrolling.height, y_offset + 10)

    def _navigate_back(self):
        now = time.time()
        if now - self._last_back_time < 0.2:
            return
        self._last_back_time = now

        if self.hierarchy_stack:
            previous_list = self.hierarchy_stack.pop()
            self._build_hierarchy_view(previous_list)
        else:
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
            self.hierarchy_stack.append(self._current_display_elements)
            self._build_hierarchy_view(element.children)

    # ------------------------------------------------------------------
    # Properties display
    # ------------------------------------------------------------------
    
    def _show_element_properties(self, element: UIElement):
        self.properties_frame.clear_content()
        
        title = TextLabel(int(5 * self.scale), 0, f"Properties of {element.element_type} [{element.element_id}]",
                        int(16 * self.scale), color=self.style.text_color)
        self.properties_frame.add_child(title)

        props = getattr(element, '_properties', {})
        spacing = 25
        total_props:int = 0
        for prop_name, prop_info in props.items():
            total_props += 1
            prop_type:Union[Any, None] = prop_info.get('type', None)
            if prop_type is bool:
                value = getattr(element, prop_info.get('key', prop_name), False)
                line = Checkbox(int(5 * self.scale), int((total_props * spacing) * self.scale), int(100 * self.scale), int(18 * self.scale), value, f"{prop_info.get('name', prop_name)}")
                line.set_on_toggle(lambda val, e=element, k=prop_info.get('key', prop_name): setattr(e, k, val))
            elif prop_type is int:
                value = getattr(element, prop_info.get('key', prop_name), 0)
                min_val, max_val = prop_info.get('range', (0, 100))

                if isinstance(min_val, str):
                    if min_val == '<SCREEN_WIDTH>':
                        min_val = self.engine.width
                    elif min_val == '<SCREEN_HEIGHT>':
                        min_val = self.engine.height
                    else:
                        min_val = 0
                if isinstance(max_val, str):
                    if max_val == '<SCREEN_WIDTH>':
                        max_val = self.engine.width
                    elif max_val == '<SCREEN_HEIGHT>':
                        max_val = self.engine.height
                    else:
                        max_val = 100

                line = NumberSelector(
                    int(5 * self.scale),
                    int((total_props * spacing) * self.scale),
                    int(120 * self.scale),
                    int(18 * self.scale),
                    min_value=min_val,
                    max_value=max_val,
                    value=value,
                    label=prop_info.get('name', prop_name),
                    label_size=int(14 * self.scale)
                )
                line.set_on_value_changed(
                    lambda val, e=element, k=prop_info.get('key', prop_name): setattr(e, k, val)
                )
            elif prop_type is Literal:
                value = getattr(element, prop_info.get('key', prop_name), None)
                options = prop_info.get('options', [])
                if isinstance(options, list) and all(isinstance(opt, str) for opt in options):
                    line = Dropdown(
                        int(5 * self.scale),
                        int((total_props * spacing) * self.scale),
                        int(150 * self.scale),
                        int(18 * self.scale),
                        options,
                        int(14 * self.scale),
                        label=prop_info.get('name', prop_name),
                        label_size=int(14 * self.scale)
                    )
                    if value in options:
                        line.selected_index = options.index(value)
                    line.set_on_selection_changed(
                        lambda index, name, e=element, k=prop_info.get('key', prop_name), opts=options: setattr(e, k, opts[index])
                    )
                else:
                    display_name = prop_info.get('name', prop_name)
                    value_str = repr(value) if value is not None else "None"
                    line = TextLabel(int(5 * self.scale), int((total_props * spacing) * self.scale), f"{display_name}: {value_str}",
                                    int(18 * self.scale), color=(200, 200, 200))
            elif prop_type is str:
                value = getattr(element, prop_info.get('key', prop_name), "")
                line = TextBox(int(5 * self.scale), int((total_props * spacing) * self.scale), int(150 * self.scale), int(18 * self.scale), font_size=int(16 * self.scale), label=prop_info.get('name', str(prop_name).capitalize()), label_size=int(14 * self.scale))
                line.set_text(text=value)
                line.set_on_text_changed(lambda text, e=element, k=prop_info.get('key', prop_name): setattr(e, k, text))
            elif prop_type is ElementStyle:
                value = getattr(element, prop_info.get('key', prop_name), None)
                print(value)
            elif prop_type is tuple or prop_type is Color or prop_type is Tuple[int, int, int]:
                value = getattr(element, prop_info.get('key', prop_name), None)
                if value is None:  
                    value = (0,0,0)
                
                if isinstance(value, Color):
                    value = value.to_rgb_tuple()
                if len(value) < 3:
                    continue
                elif len(value) == 3:
                    line = ColorPicker(
                        int(5 * self.scale), int((total_props * spacing) * self.scale), int(150 * self.scale), int(22 * self.scale), int(150*self.scale),
                        color_system='rgb', initial_color=value)
                    
                    line.set_on_color_changed(lambda color, e=element, k=prop_info.get('key', prop_name): setattr(e, k, color))
            else:
                display_name = prop_info.get('name', prop_name)
                value = getattr(element, prop_info.get('key', prop_name), None)
                value_str = repr(value) if value is not None else "None"
                line = TextLabel(int(5 * self.scale), int((total_props * spacing) * self.scale), f"{display_name}: {value_str}",
                                int(18 * self.scale), color=(200, 200, 200))
            line.add_group('live-inspector-ignore')
            self.properties_frame.add_child(line)

        if not props or total_props <= 0:
            msg = TextLabel(int(5 * self.scale), 0, "No editable properties",
                            int(16 * self.scale), color=(150, 150, 150))
            self.properties_frame.add_child(msg)
        else:
            kill_element_button = Button(int(5 * self.scale), int((total_props * spacing + 20) * self.scale), int(80 * self.scale), int(18 * self.scale), "Remove", int(14 * self.scale))
            self.properties_frame.add_child(kill_element_button)
            kill_element_button.set_on_click(lambda: element.kill())
            
            restart_element_button = Button(int(95 * self.scale), int((total_props * spacing + 20) * self.scale), int(80 * self.scale), int(18 * self.scale), "Restart", int(14 * self.scale))
            self.properties_frame.add_child(restart_element_button)
            def _e():
                e = element.restart()
                self._show_element_properties(e)
            restart_element_button.set_on_click(_e)

        self.properties_frame._needs_rearrange = True
        self.properties_frame.scroll_y = 0
    
    # ------------------------------------------------------------------
    # Console
    # ------------------------------------------------------------------
    def _redirect_console_output(self):
        class ConsoleStream:
            def __init__(self, log_manager, original, level):
                self.log_manager = log_manager
                self.original = original
                self.level = level
                self.buffer = ""

            def write(self, text):
                self.original.write(text)
                self.buffer += text
                if text.endswith('\n'):
                    # Remove trailing newline for display
                    msg = self.buffer.rstrip('\n')
                    if msg:
                        self.log_manager.add_log(self.level, msg)
                    self.buffer = ""

            def flush(self):
                self.original.flush()

        # Redirect stdout (INFO) and stderr (ERROR)
        sys.stdout = ConsoleStream(self.console_log_manager, self._original_stdout, LogLevel.INFO)
        sys.stderr = ConsoleStream(self.console_log_manager, self._original_stderr, LogLevel.ERROR)
    
    def _setup_console_tab(self):
        scale = self.scale
        self.console_scrolling = ScrollingFrame(
            5*scale, 35*scale,
            self.tabs.width - 10*scale,
            self.tabs.height - 100*scale,
            self.tabs.width - 10*scale,
            400*scale,
            scrollbar_size=8
        )
        self.tabs.add_to_tab("Console", self.console_scrolling)

        # Clear button
        clear_btn = Button(5*scale, 5*scale, 80*scale, 24*scale, "Clear", int(16*scale))
        clear_btn.set_on_click(self._clear_console)
        self.tabs.add_to_tab("Console", clear_btn)

        # Auto‑refresh when logs change
        self.console_log_manager.on_logs_changed = self._update_console_view
        self._update_console_view()
    
    def _update_console_view(self):
        self.console_scrolling.clear_content()
        logs = self.console_log_manager.get_filtered()
        # Keep only last 40 entries
        logs = logs[-40:]
        y = 5
        for entry in logs:
            # Format timestamp
            timestamp = datetime.datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
            display_text = f"[{timestamp}] {entry.message}"
            color = {
                LogLevel.INFO: (200, 200, 200),
                LogLevel.WARNING: (255, 255, 100),
                LogLevel.ERROR: (255, 100, 100),
                LogLevel.DEBUG: (150, 150, 150)
            }.get(entry.level, (200, 200, 200))
            label = TextLabel(5*self.scale, y*self.scale, display_text,
                            int(14*self.scale), color=color)
            self.console_scrolling.add_child(label)
            y += 22
        self.console_scrolling.content_height = max(self.console_scrolling.height, y + 10)
        # Auto‑scroll to bottom
        self.console_scrolling.scroll_y = self.console_scrolling.content_height - self.console_scrolling.height
    
    def _clear_console(self):
        self.console_log_manager.clear()
        self._update_console_view()
        
    def _restore_console(self):
        if hasattr(self, '_original_stdout'):
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
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
            fr.add_child(TextLabel(5, 16, str(type(ovr).__name__), int(18*self.scale), pivot=(0, 0.5)))
            hide_btn = Button(fr.width - 5, 16, 50, 24, "Hide", int(16*self.scale), pivot=(1, 0.5))
            hide_btn.set_on_click(lambda ovr=ovr: setattr(ovr, 'visible', not ovr.visible))
            fr.add_child(hide_btn)
            delete_btn = Button(fr.width - 60, 16, 50, 24, "Remove", int(16*self.scale), pivot=(1, 0.5))
            delete_btn.set_on_click(lambda ovr=ovr: self.debug_manager.remove_overlay(ovr, callback=self.update_overlays_scrolling))
            fr.add_child(delete_btn)
            self.overlays_scrolling.add_child(fr)
            y += 32

    def set_debug_manager(self, dm: 'DebugManager'):
        self.debug_manager = dm

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
            if not self.debug_enabled:
                return
            if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_F12:
                if self.live_inspector:
                    self.live_inspector.set_visible(not self.live_inspector.visible)

    def on_scene_changed(self):
        if self.live_inspector:
            self.live_inspector.on_scene_changed()

    def add_overlay(self, overlay: DebugOverlay|Any) -> None:
        self.overlays.append(overlay)
        if isinstance(overlay, LiveInspector):
            self.live_inspector = overlay
            overlay.set_debug_manager(self)
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
        if not self.debug_enabled:
            return
        for overlay in self.overlays:
            overlay.update(dt, input_state)

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.debug_enabled:
            return
        for overlay in self.overlays:
            overlay.render(renderer)