"""
debug.py – Debug overlay system with draggable panels, Live Inspector, and performance monitoring.

Refactored for 0.2.6:
- Vertical sidebar (tabs on the left) with reduced width (80px).
- Merged Performance and Console into a single "System" tab with two scrolling frames side‑by‑side.
- Console now properly scrolls and doesn't overflow.
- Added "Tasks" tab for background task monitoring.
- Cleaned up duplicated drag logic (now a mixin).
- Improved code organization and readability.
- Removed dependency on Tabination.get_tab_by_name() for compatibility.
- Added "Storage" tab with sub‑tabs for Atlas, Savedata, and Encryption.
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
from .. import __version__, __status__

if TYPE_CHECKING:
    from ..core.engine import LunaEngine

# ----------------------------------------------------------------------
# UI imports
# ----------------------------------------------------------------------
from ..ui.elements import *
from ..ui.themes import ThemeManager, ThemeStyle

# Storage imports
from ..storage import Atlas, AtlasCategory, AtlasItem, Savedata, MachineEncryption


# ----------------------------------------------------------------------
# Base draggable overlay (with common drag logic)
# ----------------------------------------------------------------------

class DraggableMixin:
    """Mixin to add drag‑and‑drop behavior to any overlay."""

    def _init_drag(self):
        self._dragging = False
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._fixed = False

    def _handle_drag(self, input_state: InputState, header_rect: pygame.Rect, lock_btn_rect: pygame.Rect, close_btn_rect: pygame.Rect):
        """Call this in update() to handle dragging."""
        mouse_pos = input_state.mouse_pos
        left_held = input_state.mouse_buttons_pressed.left
        left_just = input_state.mouse_just_pressed and left_held

        # Close and lock buttons
        if left_just and close_btn_rect.collidepoint(mouse_pos):
            self.close()
            return
        if left_just and lock_btn_rect.collidepoint(mouse_pos):
            self.toggle_fixed()
            return

        if not self._fixed:
            if left_just and not self._dragging:
                if header_rect.collidepoint(mouse_pos) and not lock_btn_rect.collidepoint(mouse_pos) and not close_btn_rect.collidepoint(mouse_pos):
                    self._dragging = True
                    self._drag_offset_x = self.x - mouse_pos[0]
                    self._drag_offset_y = self.y - mouse_pos[1]
            if self._dragging:
                if left_held:
                    new_x = mouse_pos[0] + self._drag_offset_x
                    new_y = mouse_pos[1] + self._drag_offset_y
                    screen_w, screen_h = self.engine.window.width, self.engine.window.height
                    new_x = max(0, min(new_x, screen_w - self.width))
                    new_y = max(0, min(new_y, screen_h - self.height))
                    self.x, self.y = new_x, new_y
                else:
                    self._dragging = False

    def toggle_fixed(self):
        self._fixed = not self._fixed

    def close(self):
        self.visible = False


class DebugOverlay(DraggableMixin):
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
        self.scale = self.engine.height / 600 or 1.0
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

        self.lock_btn_rect = pygame.Rect(0, 0, self.button_size, self.button_size)
        self.close_btn_rect = pygame.Rect(0, 0, self.button_size, self.button_size)

        self._init_drag()

    def refresh(self, dt: float) -> None:
        pass

    def render_content(self, renderer: OpenGLRenderer) -> None:
        pass

    def update(self, dt: float, input_state: InputState) -> None:
        if not self.visible:
            return

        header_rect = pygame.Rect(self.x, self.y, self.width, self.header_height)
        self.close_btn_rect.topleft = (
            self.x + self.width - self.button_size - self.button_margin,
            self.y + (self.header_height - self.button_size) // 2,
        )
        self.lock_btn_rect.topleft = (
            self.close_btn_rect.left - self.button_size - self.button_margin,
            self.y + (self.header_height - self.button_size) // 2,
        )

        self._handle_drag(input_state, header_rect, self.lock_btn_rect, self.close_btn_rect)
        self.refresh(dt)

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return
        renderer.draw_rect(self.x, self.y, self.width, self.height, self.background_color, corner_radius=self.corner_radius)
        renderer.draw_rect(self.x, self.y, self.width, self.header_height, self.header_color, corner_radius=self.corner_radius)
        renderer.draw_text(self.title, int(self.x + 8 * self.scale), int(self.y + 6 * self.scale), self.text_color, self.header_font)

        lock_char = 'L' if self._fixed else 'U'
        renderer.draw_text(lock_char, int(self.lock_btn_rect.x + 4 * self.scale), self.lock_btn_rect.y, self.text_color, self.font)
        renderer.draw_text('X', int(self.close_btn_rect.x + 4 * self.scale), self.close_btn_rect.y, (255, 100, 100), self.font)

        self.render_content(renderer)


# ----------------------------------------------------------------------
# Simple overlays (FPS, Scene Stats, Sound, Clock, Version)
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
        renderer.draw_text(f"{self.current_fps:.1f} fps", self.x + 10 * self.scale, y, self.text_color, self.font)
        renderer.draw_text(f"Avg: {self.avg_fps:.1f} fps", self.x + 10 * self.scale, y + 18 * self.scale, self.text_color, self.font)
        renderer.draw_text(f"Frame: {self.frame_time:.2f} ms", self.x + 10 * self.scale, y + 36 * self.scale, self.text_color, self.font)


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
        y = self.y + self.header_height + 5 * self.scale
        renderer.draw_text(f"UI: {self.ui_count}", self.x + 10 * self.scale, y, self.text_color, self.font)
        renderer.draw_text(f"Particles: {self.particle_count}", self.x + 10 * self.scale, y + 24 * self.scale, self.text_color, self.font)
        renderer.draw_text(f"Camera: ({self.cam_pos[0]:.0f}, {self.cam_pos[1]:.0f})", self.x + 10 * self.scale, y + 48 * self.scale, self.text_color, self.font)
        renderer.draw_text(f"Scene Update: {self.scene_update_ms:.2f} ms", self.x + 10 * self.scale, y + 72 * self.scale, self.text_color, self.font)
        renderer.draw_text(f"Scene Render: {self.scene_render_ms:.2f} ms", self.x + 10 * self.scale, y + 96 * self.scale, self.text_color, self.font)


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
        y = self.y + self.header_height + 5 * self.scale
        renderer.draw_text(f"Master: {self.master_volume:.2f}", self.x + 10 * self.scale, y, self.text_color, self.font)
        renderer.draw_text(f"Sources: {self.source_count}", self.x + 10 * self.scale, y + 24 * self.scale, self.text_color, self.font)
        renderer.draw_text(f"Playing: {self.playing_count}", self.x + 10 * self.scale, y + 48 * self.scale, self.text_color, self.font)


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
        y = self.y + self.header_height + 5 * self.scale
        renderer.draw_text(self.time_str, self.x + 10 * self.scale, y, self.text_color, self.font)
        renderer.draw_text(self.date_str, self.x + 10 * self.scale, y + 24 * self.scale, self.text_color, self.font)


class VersionOverlay(DebugOverlay):
    def __init__(self, engine: 'LunaEngine', x: int = 180, y: int = 110) -> None:
        super().__init__(engine, x, y, width=200, height=120, title="Version")
        self.luna_version = __version__
        self.luna_status = __status__
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
        y = self.y + self.header_height + 5 * self.scale
        renderer.draw_text(f"Framework: {self.luna_version} - {self.luna_status}", self.x + 10 * self.scale, y, self.text_color, self.font)
        renderer.draw_text(f"Python: {self.python_version}", self.x + 10 * self.scale, y + 24 * self.scale, self.text_color, self.font)
        renderer.draw_text(f"Pygame: {self.pygame_version}", self.x + 10 * self.scale, y + 48 * self.scale, self.text_color, self.font)
        renderer.draw_text(f"OpenGL: {self.opengl_version}", self.x + 10 * self.scale, y + 72 * self.scale, self.text_color, self.font)

class StorageOverlay(DebugOverlay):
    """
    A compact overlay showing storage system status:
    - Atlas: root path, item count, bundle status
    - Savedata: file path, table count, total rows
    """
    def __init__(self, engine: 'LunaEngine', x: int = 10, y: int = 230) -> None:
        super().__init__(engine, x, y, width=260, height=140, title="Storage")
        self._last_update = 0
        self._atlas_info = ""
        self._savedata_info = ""

    def refresh(self, dt: float) -> None:
        # Update at most every 0.5 seconds to avoid constant string re‑creation
        self._last_update += dt
        if self._last_update < 0.5:
            return
        self._last_update = 0

        atlas = self.engine.atlas
        if atlas:
            count = len(atlas.atlas)
            bundle = "Yes" if atlas.is_bundle_loaded() else "No"
            root = str(atlas.root_path)
            if len(root) > 30:
                root = "..." + root[-27:]
            self._atlas_info = f"Atlas: {count} items  (bundle: {bundle})  root: {root}"
        else:
            self._atlas_info = "Atlas: not available"

        savedata = getattr(self.engine, 'savedata', None)
        if savedata and savedata.tables:
            table_count = len(savedata.tables)
            total_rows = sum(len(t.rows) for t in savedata.tables.values())
            filepath = str(savedata.filepath) if savedata.filepath else "None"
            if len(filepath) > 25:
                filepath = "..." + filepath[-22:]
            self._savedata_info = f"Savedata: {table_count} tables, {total_rows} rows  (file: {filepath})"
        else:
            self._savedata_info = "Savedata: none"

    def render_content(self, renderer: OpenGLRenderer) -> None:
        y = self.y + self.header_height + 5 * self.scale
        # Atlas line
        renderer.draw_text(self._atlas_info, self.x + 10 * self.scale, y,
                           self.text_color, self.font)
        y += 24 * self.scale
        # Savedata line
        renderer.draw_text(self._savedata_info, self.x + 10 * self.scale, y,
                           self.text_color, self.font)
        y += 24 * self.scale
        # Optional: show bundle size if loaded
        if self.engine.atlas and self.engine.atlas.is_bundle_loaded():
            try:
                bundle_size = self.engine.atlas._bundle_path.stat().st_size
                size_str = self._human_size(bundle_size)
                renderer.draw_text(f"Bundle size: {size_str}", self.x + 10 * self.scale, y,
                                   self.text_color, self.font)
            except:
                pass

    @staticmethod
    def _human_size(num: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if num < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} TB"

# ----------------------------------------------------------------------
# Console Log Manager
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


# ----------------------------------------------------------------------
# LiveInspector – Main debug panel with modular tabs (vertical sidebar)
# ----------------------------------------------------------------------

class LiveInspector(UiFrame):
    """
    Main debugging panel. Organised into tabs on the left side:
    - Elements: hierarchy + properties
    - Custom Function: user‑defined test functions
    - System: performance + console (merged)
    - Audio: master volume, effects, source list
    - Overlays: manage debug overlays
    - Settings: theme, dark mode, utilities
    - Tasks: background task status
    - Storage: sub‑tabs for Atlas, Savedata, Encryption
    """

    def __init__(self, engine: 'LunaEngine', x: int = 100, y: int = 100) -> None:
        self._perf_labels = {}
        self._last_back_time = 0
        self._last_element_click_time = 0
        # Store the actual parent path instead of copied lists. This survives
        # refreshes caused by rebuilding the hierarchy scrolling frame.
        self.hierarchy_stack: List[UIElement] = []
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
        self.visible = False
        self._scene_name = None

        # Console
        self.console_log_manager = ConsoleLogManager()
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._redirect_console_output()

        # Custom functions
        self.custom_functions = {}
        self._current_custom_func = None

        # Build the UI
        self._setup_content(engine)
        self._registered = False

        # Tab registry: name -> (setup_function, update_function)
        self._tabs = {
            "Elements": (self._setup_elements_tab, self._update_elements_tab),
            "Custom Function": (self._setup_custom_tab, None),
            "System": (self._setup_system_tab, self._update_system_tab),
            "Audio": (self._setup_audio_tab, self._update_audio_tab),
            "Overlays": (self._setup_overlays_tab, None),
            "Settings": (self._setup_settings_tab, None),
            "Tasks": (self._setup_tasks_tab, self._update_tasks_tab),
            "Storage": (self._setup_storage_tab, self._update_storage_tab),
        }

        # Build all tabs
        for name, (setup_func, _) in self._tabs.items():
            self.tabs.add_tab(name)
            setup_func()

        # Initial update for all tabs
        self._build_root_hierarchy()

    # ------------------------------------------------------------------
    # Helper to get a tab's frame (compatibility with older Tabination)
    # ------------------------------------------------------------------

    def _get_tab_frame(self, tab_name: str) -> Optional[UiFrame]:
        """Return the frame (UiFrame) of the tab with the given name, or None."""
        idx = self.tabs.get_tab_index(tab_name)
        if idx == -1:
            return None
        return self.tabs.tabs[idx]['frame']

    # ------------------------------------------------------------------
    # Scene registration
    # ------------------------------------------------------------------

    def _update_scene_registration(self):
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
        if self.visible == visible:
            return
        self.visible = visible
        self._update_scene_registration()

    def close(self):
        self.set_visible(False)
        self._restore_console()

    def toggle_fixed(self):
        self.pinned = not self.pinned
        self.draggable = not self.pinned

    def on_scene_changed(self):
        self._update_scene_registration()
        self._build_root_hierarchy()

    # ------------------------------------------------------------------
    # Main UI setup (common for all tabs) – vertical sidebar, reduced width
    # ------------------------------------------------------------------

    def _setup_content(self, engine: 'LunaEngine'):
        usable = self.usable_space
        scale = self.engine.height / 600
        self.scale = scale

        # Vertical tabs on the left side – reduced width to 80px
        self.tabs = Tabination(
            0, self.header_height,
            self.width, self.height - self.header_height,
            font_size=int(max(14 * scale, 14)),
            orientation='vertical1',
            tab_width=int(55 * scale),
            tab_height=int(30 * scale),
            pivot=(0, 0)
        )
        self.add_child(self.tabs)

    # ------------------------------------------------------------------
    # Tab: Elements
    # ------------------------------------------------------------------

    def _setup_elements_tab(self):
        tab_frame = self._get_tab_frame("Elements")
        if tab_frame is None:
            return
        scale = self.scale
        tab_width = tab_frame.width
        tab_height = tab_frame.height

        # Toolbar
        reset_btn = Button(5, 5, 60, 24, "Reset", 14)
        reset_btn.set_on_click(self._build_root_hierarchy)
        tab_frame.add_child(reset_btn)

        refresh_btn = Button(70, 5, 70, 24, "Refresh", 14)
        refresh_btn.set_on_click(self._build_root_hierarchy)
        tab_frame.add_child(refresh_btn)

        hierarchy_y = 35
        hierarchy_height = tab_height - hierarchy_y - 40
        self.hierarchy_scrolling = ScrollingFrame(
            5, hierarchy_y,
            tab_width // 2 - 5,
            hierarchy_height,
            tab_width // 2 - 5,
            2000,
            scrollbar_size=5
        )
        tab_frame.add_child(self.hierarchy_scrolling)

        self.properties_frame = ScrollingFrame(
            tab_width // 2 + 5, hierarchy_y,
            tab_width // 2 - 7,
            hierarchy_height,
            tab_width // 2 - 7,
            2000,
            scrollbar_size=3,
            auto_arrange_y=True,
            arrange_spacing=10
        )
        self.properties_frame.add_child(TextLabel(5, 5, "Properties", int(18 * scale), color=self.style.text_color))
        tab_frame.add_child(self.properties_frame)

    def _update_elements_tab(self):
        pass

    # ------------------------------------------------------------------
    # Tab: Custom Function
    # ------------------------------------------------------------------

    def _setup_custom_tab(self):
        tab_frame = self._get_tab_frame("Custom Function")
        if tab_frame is None:
            return
        scale = self.scale
        tab_width = tab_frame.width
        tab_height = tab_frame.height

        self.custom_dropdown = Dropdown(
            5, 5, 180, 24, ["No functions"], int(16 * scale)
        )
        self.custom_dropdown.set_on_selection_changed(self._on_custom_func_selected)
        tab_frame.add_child(self.custom_dropdown)

        self.custom_desc_label = TextLabel(5, 35, "Select a function above", int(14 * scale), color=(200, 200, 200))
        tab_frame.add_child(self.custom_desc_label)

        self.custom_params_frame = ScrollingFrame(
            5, 60,
            tab_width - 10, 120,
            tab_width - 10, 200,
            scrollbar_size=6
        )
        tab_frame.add_child(self.custom_params_frame)

        self.custom_execute_btn = Button(5, 190, 100, 28, "Execute", int(16 * scale))
        self.custom_execute_btn.set_on_click(self._execute_custom_func)
        tab_frame.add_child(self.custom_execute_btn)

        self.custom_result_label = TextLabel(115, 195, "", int(14 * scale), color=(100, 255, 100))
        tab_frame.add_child(self.custom_result_label)

        self._refresh_custom_dropdown()

    # ------------------------------------------------------------------
    # Tab: System (merged Performance + Console)
    # ------------------------------------------------------------------

    def _setup_system_tab(self):
        tab_frame = self._get_tab_frame("System")
        if tab_frame is None:
            return
        scale = self.scale
        tab_width = tab_frame.width
        tab_height = tab_frame.height

        # Split: 45% performance, 55% console
        left_w = int(tab_width * 0.45)
        right_w = tab_width - left_w

        # Performance scrolling frame (left)
        self.perf_scrolling = ScrollingFrame(
            0, 0,
            left_w, tab_height,
            left_w, 2000,   # large content height
            scrollbar_size=8
        )
        self.perf_scrolling.set_background_color((30, 30, 40, 180))
        tab_frame.add_child(self.perf_scrolling)

        # Console scrolling frame (right)
        self.console_scrolling = ScrollingFrame(
            left_w, 0,
            right_w, tab_height,
            right_w, 2000,
            scrollbar_size=8
        )
        self.console_scrolling.set_background_color((20, 20, 30, 180))
        tab_frame.add_child(self.console_scrolling)

        # ---- Performance content ----
        y = 5
        line_h = int(16 * scale)
        self._perf_labels = {}

        def add_perf_label(text, init="0.0"):
            nonlocal y
            label = TextLabel(5, y, text, int(14 * scale), color=self.style.text_color)
            self.perf_scrolling.add_child(label)
            val = TextLabel(120, y, init, int(14 * scale), color=(220, 220, 100))
            self.perf_scrolling.add_child(val)
            self._perf_labels[text.strip(':')] = val
            y += line_h

        add_perf_label("FPS:", "0.0")
        add_perf_label("Avg FPS:", "0.0")
        add_perf_label("1% Low:", "0.0")
        add_perf_label("0.1% Low:", "0.0")
        add_perf_label("Frame Time:", "0.00 ms")
        y += 5
        add_perf_label("Scene Update:", "0.00 ms")
        add_perf_label("Scene Render:", "0.00 ms")
        y += 5
        add_perf_label("UI Elements:", "0")
        add_perf_label("Particles:", "0")
        y += 5
        add_perf_label("Text Cache:", "0 B")
        add_perf_label("Texture Cache:", "0 B")
        add_perf_label("Total Cache:", "0 B")
        add_perf_label("Circle Cache:", "0 B")
        add_perf_label("Polygon Cache:", "0 B")

        y += 10
        hw_label = TextLabel(5, y, "Hardware Info", int(16 * scale), color=(200, 200, 255))
        self.perf_scrolling.add_child(hw_label)
        y += line_h
        for key, label_text in [
            ("os", "OS:"),
            ("cpu", "CPU:"),
            ("gpu", "GPU:"),
            ("ram_total", "RAM Total:"),
            ("ram_avail", "RAM Available:"),
            ("python", "Python:"),
            ("pygame", "Pygame:"),
            ("cpu_cores", "CPU Cores:"),
        ]:
            lbl = TextLabel(5, y, label_text, int(14 * scale), color=(200, 200, 200))
            self.perf_scrolling.add_child(lbl)
            val = TextLabel(120, y, "N/A", int(14 * scale), color=(200, 200, 200))
            self.perf_scrolling.add_child(val)
            self._perf_labels[key] = val
            y += line_h

        # Update content height
        self.perf_scrolling.content_height = max(y + 10, self.perf_scrolling.height)

        # ---- Console content ----
        self.console_log_manager.on_logs_changed = self._update_console_view_system
        self._update_console_view_system()

    def _update_console_view_system(self):
        """Update the console view in the System tab."""
        self.console_scrolling.clear_content()
        logs = self.console_log_manager.get_filtered()[-40:]
        y = 5
        for entry in logs:
            timestamp = datetime.datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S")
            display_text = f"[{timestamp}] {entry.message}"
            color = {
                LogLevel.INFO: (200, 200, 200),
                LogLevel.WARNING: (255, 255, 100),
                LogLevel.ERROR: (255, 100, 100),
                LogLevel.DEBUG: (150, 150, 150)
            }.get(entry.level, (200, 200, 200))
            label = TextLabel(5, y, display_text, int(14 * self.scale), color=color)
            self.console_scrolling.add_child(label)
            y += 22
        self.console_scrolling.content_height = max(self.console_scrolling.height, y + 10)
        self.console_scrolling.scroll_y = self.console_scrolling.content_height - self.console_scrolling.height

    def _update_system_tab(self):
        """Update performance metrics and console (called every frame)."""
        if not self.visible or not hasattr(self, '_perf_labels'):
            return

        # Update performance labels
        pm = self.engine.performance_monitor
        stats = pm.get_stats()
        self._perf_labels['FPS'].set_text(f"{stats.get('current_fps', 0):.1f}")
        self._perf_labels['Avg FPS'].set_text(f"{stats.get('average_fps', 0):.1f}")
        self._perf_labels['1% Low'].set_text(f"{stats.get('percentile_1', 0):.1f}")
        self._perf_labels['0.1% Low'].set_text(f"{stats.get('percentile_01', 0):.1f}")
        self._perf_labels['Frame Time'].set_text(f"{stats.get('frame_time_ms', 0):.2f} ms")

        scene = self.engine.current_scene
        if scene:
            self._perf_labels['UI Elements'].set_text(str(len(scene.ui_elements)))
            if hasattr(scene, 'particle_system'):
                self._perf_labels['Particles'].set_text(str(scene.particle_system.active_particles))
            else:
                self._perf_labels['Particles'].set_text("0")
            scene_update = pm.get_timing('scene')
            scene_render = pm.get_timing('render')
            self._perf_labels['Scene Update'].set_text(f"{scene_update.duration:.2f} ms" if scene_update else "0.00 ms")
            self._perf_labels['Scene Render'].set_text(f"{scene_render.duration:.2f} ms" if scene_render else "0.00 ms")
        else:
            self._perf_labels['UI Elements'].set_text("0")
            self._perf_labels['Particles'].set_text("0")
            self._perf_labels['Scene Update'].set_text("0.00 ms")
            self._perf_labels['Scene Render'].set_text("0.00 ms")

        renderer = self.engine.renderer
        if isinstance(renderer, OpenGLRenderer):
            cache = renderer.get_cache_usage('all', humanize=True)
            self._perf_labels['Text Cache'].set_text(cache.get('text', '0 B'))
            self._perf_labels['Texture Cache'].set_text(cache.get('texture', '0 B'))
            self._perf_labels['Circle Cache'].set_text(cache.get('circle', '0 B'))
            self._perf_labels['Polygon Cache'].set_text(cache.get('polygon', '0 B'))
            self._perf_labels['Total Cache'].set_text(cache.get('total', '0 B'))
        else:
            self._perf_labels['Text Cache'].set_text("N/A")
            self._perf_labels['Texture Cache'].set_text("N/A")
            self._perf_labels['Circle Cache'].set_text("N/A")
            self._perf_labels['Polygon Cache'].set_text("N/A")
            self._perf_labels['Total Cache'].set_text("N/A")

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

    # ------------------------------------------------------------------
    # Tab: Audio
    # ------------------------------------------------------------------

    def _setup_audio_tab(self):
        tab_frame = self._get_tab_frame("Audio")
        if tab_frame is None:
            return
        scale = self.scale
        tab_width = tab_frame.width
        tab_height = tab_frame.height

        # Title
        title = TextLabel(5, 5, "Audio Controls", int(20 * scale), color=self.style.text_color)
        tab_frame.add_child(title)

        # Master Volume
        self._add_label("Master Vol:", 10, 28 * scale, tab_frame)
        self.master_volume_slider = Slider(90 * scale, 28 * scale, 150, 16, 0.0, 1.0, 1.0, pivot=(0, 0))
        self.master_volume_slider.set_on_value_changed(self._on_master_volume_changed)
        tab_frame.add_child(self.master_volume_slider)
        self.master_volume_label = self._add_value_label("1.00", 250 * scale, 28 * scale, tab_frame)

        # Effects
        self._add_label("Effects:", 10, 44 * scale, tab_frame, font_size=int(16 * scale))
        effect_types = ["Reverb", "Echo", "Chorus", "Flanger", "Distortion", "Pitch Shift"]
        self.effect_dropdown = Dropdown(10, 60, 100, 20, effect_types, int(16 * scale), pivot=(0, 0))
        tab_frame.add_child(self.effect_dropdown)

        self._add_label("Intensity:", 120, 60, tab_frame)
        self.effect_slider = Slider(180, 70, 90, 16, 0.0, 1.0, 0.5, pivot=(0, 0))
        tab_frame.add_child(self.effect_slider)
        self.effect_label = self._add_value_label("0.50", 280, 60, tab_frame)

        apply_effect_btn = Button(310, 65, 70, 24, "Apply", int(14 * scale))
        apply_effect_btn.set_on_click(self._apply_effect)
        tab_frame.add_child(apply_effect_btn)

        # Source list
        self._add_label("Audio Sources:", 10, 85 * scale, tab_frame, font_size=int(14 * scale))
        self.audio_sources_frame = ScrollingFrame(
            10, 95,
            tab_width - 20, 135,
            tab_width - 20, 400,
            scrollbar_size=8
        )
        tab_frame.add_child(self.audio_sources_frame)

        refresh_sources_btn = Button(10, 240, 80, 24, "Refresh", int(12 * scale))
        refresh_sources_btn.set_on_click(self._force_refresh_audio_sources)
        tab_frame.add_child(refresh_sources_btn)

        # Initialize state
        self._audio_source_widgets = []      # list of (frame, vol_slider, pan_slider, status_label)
        self._audio_source_count = -1        # force initial rebuild
        self._audio_dirty = True

        # Build once
        self._update_audio_sources()

    def _update_audio_tab(self):
        """Update audio source values without rebuilding the entire list."""
        if not self.visible:
            return

        # Check if the source count has changed; if so, rebuild.
        audio = self.engine.audio
        current_count = 0
        if audio and hasattr(audio, 'backend') and audio.backend.is_initialized():
            current_count = len(audio.backend.sources) if hasattr(audio.backend, 'sources') else 0

        if current_count != self._audio_source_count:
            self._audio_dirty = True
            self._audio_source_count = current_count

        if self._audio_dirty:
            self._update_audio_sources()
            self._audio_dirty = False

        # Update existing widgets (sliders and status) without recreating.
        if not self._audio_source_widgets:
            return

        sources = audio.backend.sources if audio and hasattr(audio, 'backend') and audio.backend.is_initialized() else []
        for idx, (frame, vol_slider, pan_slider, status_label) in enumerate(self._audio_source_widgets):
            if idx >= len(sources):
                # Extra widget? Should not happen if we rebuild correctly.
                continue
            src = sources[idx]
            # Update volume slider without triggering callbacks
            vol_slider.set_value(src.volume if hasattr(src, 'volume') else 1.0, silent=True)
            pan_slider.set_value(src.pan if hasattr(src, 'pan') else 0.0, silent=True)
            # Update status
            is_playing = src.is_playing() if hasattr(src, 'is_playing') else False
            status_label.set_text("Playing" if is_playing else "Stopped")
            status_label.color = (100, 255, 100) if is_playing else (200, 200, 200)

    def _update_audio_sources(self):
        """Rebuild the source list from scratch (called when source count changes)."""
        self.audio_sources_frame.clear_content()
        self._audio_source_widgets.clear()

        y = 5
        audio = self.engine.audio
        if not audio or not hasattr(audio, 'backend') or not audio.backend.is_initialized():
            label = TextLabel(5, 5, "Audio backend not available", int(14 * self.scale), (200, 100, 100))
            self.audio_sources_frame.add_child(label)
            return

        sources = audio.backend.sources if hasattr(audio.backend, 'sources') else []
        if not sources:
            label = TextLabel(5, 5, "No audio sources", int(14 * self.scale), (200, 200, 200))
            self.audio_sources_frame.add_child(label)
            return

        for idx, src in enumerate(sources):
            frame = UiFrame(5, y, self.audio_sources_frame.width - 20, 30)
            frame.set_background_color((40, 40, 50, 180))
            frame.set_corner_radius(3)

            label = TextLabel(5, 15, f"Source {idx}", int(16 * self.scale), (200, 200, 200), pivot=(0, 0.5))
            frame.add_child(label)

            vol_label = TextLabel(70, 15, "Vol:", int(14 * self.scale), (200, 200, 200), pivot=(0, 0.5))
            frame.add_child(vol_label)
            vol_slider = Slider(100, 10, 40, 14, 0.0, 1.0, src.volume if hasattr(src, 'volume') else 1.0, pivot=(0, 0.5))
            vol_slider.set_on_value_changed(lambda v, s=src: self._on_source_volume_changed(s, v))
            frame.add_child(vol_slider)

            pan_label = TextLabel(155, 15, "Pan:", int(14 * self.scale), (200, 200, 200), pivot=(0, 0.5))
            frame.add_child(pan_label)
            pan_slider = Slider(175, 10, 40, 14, -1.0, 1.0, src.pan if hasattr(src, 'pan') else 0.0, pivot=(0, 0.5))
            pan_slider.set_on_value_changed(lambda v, s=src: self._on_source_pan_changed(s, v))
            frame.add_child(pan_slider)

            is_playing = src.is_playing() if hasattr(src, 'is_playing') else False
            status_label = TextLabel(230, 15, "Playing" if is_playing else "Stopped",
                                     int(14 * self.scale), (100, 255, 100) if is_playing else (200, 200, 200),
                                     pivot=(0, 0.5))
            frame.add_child(status_label)

            self.audio_sources_frame.add_child(frame)
            self._audio_source_widgets.append((frame, vol_slider, pan_slider, status_label))
            y += 32

        self.audio_sources_frame.content_height = max(self.audio_sources_frame.height, y + 10)

    def _force_refresh_audio_sources(self):
        """Force a rebuild (called by Refresh button)."""
        self._audio_dirty = True
        self._audio_source_count = -1

    def _on_master_volume_changed(self, value: float):
        if self.engine.audio and hasattr(self.engine.audio, 'set_master_volume'):
            self.engine.audio.set_master_volume(value)
            self.master_volume_label.set_text(f"{value:.2f}")

    def _on_source_volume_changed(self, source, value: float):
        if hasattr(source, 'set_volume_immediate'):
            source.set_volume_immediate(value)

    def _on_source_pan_changed(self, source, value: float):
        if hasattr(source, 'set_pan_immediate'):
            source.set_pan_immediate(value)

    def _apply_effect(self):
        audio = self.engine.audio
        if not audio:
            return
        effect_name = self.effect_dropdown.get_selected()[1]
        intensity = self.effect_slider.value
        self.effect_label.set_text(f"{intensity:.2f}")

        if effect_name == "Reverb" and hasattr(audio, 'set_global_reverb'):
            audio.set_global_reverb(intensity)
        elif effect_name == "Echo" and hasattr(audio, 'set_global_echo'):
            audio.set_global_echo(intensity)
        elif effect_name == "Chorus" and hasattr(audio, 'set_global_chorus'):
            audio.set_global_chorus(intensity)
        elif effect_name == "Flanger" and hasattr(audio, 'set_global_flanger'):
            audio.set_global_flanger(intensity)
        elif effect_name == "Distortion" and hasattr(audio, 'set_global_distortion'):
            audio.set_global_distortion(intensity)
        elif effect_name == "Pitch Shift" and hasattr(audio, 'set_global_pitch_shift'):
            semitones = (intensity * 24) - 12
            audio.set_global_pitch_shift(semitones)

    # ------------------------------------------------------------------
    # Tab: Overlays
    # ------------------------------------------------------------------

    def _setup_overlays_tab(self):
        tab_frame = self._get_tab_frame("Overlays")
        if tab_frame is None:
            return
        scale = self.scale
        tab_width = tab_frame.width
        tab_height = tab_frame.height

        self.overlays_dropdown = Dropdown(5, 5, 110, 23, self.getOverlays(), int(16 * scale))
        tab_frame.add_child(self.overlays_dropdown)

        self.add_overlay_btn = Button(120, 5, 80, 23, "Add Overlay", int(16 * scale))
        self.add_overlay_btn.set_on_click(self._add_overlay)
        tab_frame.add_child(self.add_overlay_btn)

        self.overlays_scrolling = ScrollingFrame(5, 35, tab_width - 10, 200, tab_width - 10, 400)
        tab_frame.add_child(self.overlays_scrolling)

        self.update_overlays_scrolling()

    # ------------------------------------------------------------------
    # Tab: Settings
    # ------------------------------------------------------------------

    def _setup_settings_tab(self):
        tab_frame = self._get_tab_frame("Settings")
        if tab_frame is None:
            return
        scale = self.scale
        tab_width = tab_frame.width

        # Theme dropdown
        self.themes_dropdown = Dropdown(5, 5, 150, 23, list(self.engine.get_all_themes().keys()), int(16 * scale))
        self.themes_dropdown.set_on_selection_changed(lambda index, name: (self.engine.set_global_theme(name), self.dark_mode_toggle.__setattr__('checked', ThemeManager.get_dark_mode())))
        tab_frame.add_child(self.themes_dropdown)

        # Dark mode toggle
        self.dark_mode_toggle = Checkbox(
            165, 5, 20, 20,
            ThemeManager.get_dark_mode(),
            label="Dark"
        )
        self.dark_mode_toggle.set_on_toggle(lambda val: ThemeManager.set_dark_mode(val))
        tab_frame.add_child(self.dark_mode_toggle)

        # Set dropdown to current theme
        current_theme_name = ThemeManager.get_current_theme().value
        theme_names = list(self.engine.get_all_themes().keys())
        if current_theme_name in theme_names:
            self.themes_dropdown.selected_index = theme_names.index(current_theme_name)

        # Force Kill
        self.force_kill_btn = Button(5, 35, 120, 23, "Force Kill", int(16 * scale))
        self.force_kill_btn.set_on_click(self._force_kill)
        tab_frame.add_child(self.force_kill_btn)

        # Re-init
        self.reinit_btn = Button(5, 65, 120, 23, "Re-init Game", int(16 * scale))
        self.reinit_btn.set_on_click(self._reinit_game)
        tab_frame.add_child(self.reinit_btn)

        # Clear cache
        self.clear_cache_btn = Button(5, 95, 120, 23, "Clear Cache", int(16 * scale))
        self.clear_cache_btn.set_on_click(self._clear_all_caches)
        tab_frame.add_child(self.clear_cache_btn)
        
        # Frame Per Second Select
        self.fps_selector = NumberSelector(
            5, 125, 120, 23, 15, 520, self.engine.fps, label='FPS', label_position='left', label_size=int(16*scale))
        self.fps_selector.set_on_value_changed(lambda value: self.engine.__setattr__('fps',  min(max(value, 15), 520)))
        tab_frame.add_child(self.fps_selector)

    def _force_kill(self):
        self.engine.running = False

    def _reinit_game(self):
        scene = self.engine.current_scene
        if scene:
            scene.clear_ui_elements()
            if hasattr(scene, 'setup_ui'):
                scene.setup_ui()
            self._build_root_hierarchy()

    def _clear_all_caches(self):
        renderer = self.engine.renderer
        if isinstance(renderer, OpenGLRenderer):
            renderer._text_cache.clear()
            renderer._text_cache_last_used.clear()
            renderer._texture_cache.clear()
            renderer._circle_cache.clear()
            renderer._polygon_cache.clear()

    # ------------------------------------------------------------------
    # Tab: Tasks (new)
    # ------------------------------------------------------------------

    def _setup_tasks_tab(self):
        tab_frame = self._get_tab_frame("Tasks")
        if tab_frame is None:
            return
        scale = self.scale
        tab_width = tab_frame.width
        tab_height = tab_frame.height

        # Refresh button
        refresh_btn = Button(5, 5, 80, 24, "Refresh", int(14 * scale))
        refresh_btn.set_on_click(self._update_tasks_view)
        tab_frame.add_child(refresh_btn)

        # Scrollable task list
        self.tasks_scrolling = ScrollingFrame(
            5, 35,
            tab_width - 10,
            tab_height - 45,
            tab_width - 10,
            400,
            scrollbar_size=8
        )
        tab_frame.add_child(self.tasks_scrolling)

        self._update_tasks_view()

    def _update_tasks_tab(self):
        self._update_tasks_view()

    def _update_tasks_view(self):
        self.tasks_scrolling.clear_content()
        tasks_status = self.engine.background_tasks.get_status() if hasattr(self.engine, 'background_tasks') else {}

        if not tasks_status:
            label = TextLabel(5, 5, "No background tasks", int(14 * self.scale), color=(150, 150, 150))
            self.tasks_scrolling.add_child(label)
            self.tasks_scrolling.content_height = 30
            return

        y = 5
        for tid, info in tasks_status.items():
            # Build a small frame per task
            frame = UiFrame(5, y, self.tasks_scrolling.width - 20, 30)
            frame.set_background_color((40, 40, 50, 180))
            frame.set_corner_radius(3)

            # Task name and priority
            name_label = TextLabel(5, 15, f"{info['name']} (prio:{info['priority']})", int(14 * self.scale), (220, 220, 220), pivot=(0, 0.5))
            frame.add_child(name_label)

            # Runs and CPU time
            runs_label = TextLabel(200, 15, f"runs:{info['runs']} cpu:{info['cpu_ms']:.1f}ms", int(12 * self.scale), (180, 180, 180), pivot=(0, 0.5))
            frame.add_child(runs_label)

            # Status indicator
            color = (100, 255, 100) if info['active'] else (200, 100, 100)
            status_text = "Active" if info['active'] else "Inactive"
            status_label = TextLabel(350, 15, status_text, int(12 * self.scale), color, pivot=(0, 0.5))
            frame.add_child(status_label)

            self.tasks_scrolling.add_child(frame)
            y += 32

        self.tasks_scrolling.content_height = max(self.tasks_scrolling.height, y + 10)
        self.tasks_scrolling.scroll_y = 0

    # ==================================================================
    # NEW TAB: Storage (with sub-tabs for Atlas, Savedata, Encryption)
    # ==================================================================

    def _setup_storage_tab(self):
        """Create the Storage tab with sub-tabs for Atlas, Savedata, and Encryption."""
        tab_frame = self._get_tab_frame("Storage")
        if tab_frame is None:
            return

        scale = self.scale
        tab_width = tab_frame.width
        tab_height = tab_frame.height

        # Create a Tabination inside this tab for the sub-tabs
        self.storage_sub_tabs = Tabination(
            0, 0,
            tab_width, tab_height,
            font_size=int(max(14 * scale, 14)),
            orientation='vertical1',
            tab_width=int(55 * scale),
            tab_height=int(30 * scale),
            pivot=(0, 0)
        )
        tab_frame.add_child(self.storage_sub_tabs)

        # Sub-tab names
        sub_tabs = ["Atlas", "Savedata", "Encryption"]

        # We'll store the scrolling frames for each sub-tab
        self.storage_frames = {}

        for sub_name in sub_tabs:
            self.storage_sub_tabs.add_tab(sub_name)

            # Create a ScrollingFrame for the content of this sub-tab
            frame = ScrollingFrame(
                0, 0,
                self.storage_sub_tabs.width - self.storage_sub_tabs.tab_width,
                self.storage_sub_tabs.height,
                self.storage_sub_tabs.width - self.storage_sub_tabs.tab_width,
                2000,
                scrollbar_size=8
            )
            frame.set_background_color((30, 30, 40, 180))
            # Add the frame to the sub-tab (by adding it to the tab's frame)
            sub_frame = self.storage_sub_tabs.get_tab_frame(sub_name)
            if sub_frame:
                sub_frame.add_child(frame)
                self.storage_frames[sub_name] = frame

        # Initial population
        self._update_storage_tab()

    def _update_storage_tab(self):
        """Update the Storage tab views (called every frame when visible)."""
        if not self.visible:
            return

        self._update_atlas_view()
        self._update_savedata_view()
        self._update_encryption_view()

    def _update_atlas_view(self):
        """Update the Atlas sub-tab content."""
        frame = self.storage_frames.get("Atlas")
        if not frame:
            return

        # Clear and rebuild content
        frame.clear_content()
        atlas = self.engine.atlas

        if not atlas:
            label = TextLabel(5, 5, "Atlas not available", int(14 * self.scale), color=(200, 100, 100))
            frame.add_child(label)
            frame.content_height = 30
            return

        y = 5

        # Bundle info
        bundle_text = f"Bundle loaded: {atlas.is_bundle_loaded()}"
        if atlas.is_bundle_loaded():
            bundle_text += f"  (path: {atlas._bundle_path})"
        label = TextLabel(5, y, bundle_text, int(14 * self.scale), color=(220, 220, 220))
        frame.add_child(label)
        y += 25

        # List all items
        items = list(atlas.atlas.items())
        if not items:
            label = TextLabel(5, y, "No items in atlas", int(14 * self.scale), color=(150, 150, 150))
            frame.add_child(label)
            y += 25
        else:
            # Header
            header = TextLabel(5, y, "Name | Category | Path", int(14 * self.scale), color=(255, 255, 255))
            frame.add_child(header)
            y += 25

            for name, item in items:
                cat = item.category.value if isinstance(item.category, Enum) else str(item.category)
                path = str(item.path)
                if len(path) > 50:
                    path = "..." + path[-47:]
                line_text = f"{name} | {cat} | {path}"
                label = TextLabel(5, y, line_text, int(12 * self.scale), color=(200, 200, 200))
                frame.add_child(label)
                y += 22

                # If bundle loaded, show size/CRC from manifest
                if atlas.is_bundle_loaded() and atlas._bundle_manifest:
                    res_info = atlas._bundle_manifest.get("resources", {}).get(name)
                    if res_info:
                        size = res_info.get("size", 0)
                        crc = res_info.get("crc32", "")
                        info_text = f"  size: {size} bytes, CRC: {crc}"
                        info_label = TextLabel(10, y, info_text, int(11 * self.scale), color=(150, 150, 150))
                        frame.add_child(info_label)
                        y += 18

        frame.content_height = max(frame.height, y + 10)

    def _update_savedata_view(self):
        """Update the Savedata sub-tab content."""
        frame = self.storage_frames.get("Savedata")
        if not frame:
            return

        frame.clear_content()
        savedata = getattr(self.engine, 'savedata', None)

        y = 5

        if savedata is None:
            label = TextLabel(5, y, "No Savedata instance attached to engine", int(14 * self.scale), color=(200, 100, 100))
            frame.add_child(label)
            frame.content_height = 30
            return

        # Show filepath
        if savedata.filepath:
            label = TextLabel(5, y, f"File: {savedata.filepath}", int(14 * self.scale), color=(220, 220, 220))
            frame.add_child(label)
            y += 25

        # List tables
        tables = savedata.tables
        if not tables:
            label = TextLabel(5, y, "No tables", int(14 * self.scale), color=(150, 150, 150))
            frame.add_child(label)
            y += 25
        else:
            for name, table in tables.items():
                line = f"Table: {name}  (rows: {len(table)}, columns: {table.columns})"
                label = TextLabel(5, y, line, int(14 * self.scale), color=(200, 200, 200))
                frame.add_child(label)
                y += 22

                # Show first few rows
                sample_rows = table.rows[:3]
                if sample_rows:
                    for i, row in enumerate(sample_rows):
                        row_str = str(row)
                        if len(row_str) > 60:
                            row_str = row_str[:57] + "..."
                        row_label = TextLabel(10, y, f"  {row_str}", int(12 * self.scale), color=(180, 180, 180))
                        frame.add_child(row_label)
                        y += 18
                    if len(table.rows) > 3:
                        more_label = TextLabel(10, y, f"  ... and {len(table.rows)-3} more rows", int(12 * self.scale), color=(150, 150, 150))
                        frame.add_child(more_label)
                        y += 18
                y += 5

        frame.content_height = max(frame.height, y + 10)

    def _update_encryption_view(self):
        """Update the Encryption sub-tab content."""
        frame = self.storage_frames.get("Encryption")
        if not frame:
            return

        frame.clear_content()
        y = 5

        # Show MachineEncryption info
        try:
            enc = MachineEncryption()
            hwid = enc.get_hwid_key(16)
            hwid_hex = hwid.hex()
            label = TextLabel(5, y, f"HWID (16 bytes): {hwid_hex}", int(14 * self.scale), color=(220, 220, 220))
            frame.add_child(label)
            y += 25

            # Test encryption/decryption with a sample string
            test_data = b"LunaEngine test data"
            encrypted = enc.xor_cipher(test_data)
            decrypted = enc.xor_cipher(encrypted)
            if decrypted == test_data:
                status = "OK"
                color = (100, 255, 100)
            else:
                status = "FAIL"
                color = (255, 100, 100)
            label = TextLabel(5, y, f"Encryption test: {status}", int(14 * self.scale), color=color)
            frame.add_child(label)
            y += 22

            label = TextLabel(5, y, f"Original: {test_data[:20]}", int(12 * self.scale), color=(180, 180, 180))
            frame.add_child(label)
            y += 18
            label = TextLabel(5, y, f"Encrypted: {encrypted[:20]}...", int(12 * self.scale), color=(180, 180, 180))
            frame.add_child(label)
            y += 18
            label = TextLabel(5, y, f"Decrypted: {decrypted[:20]}", int(12 * self.scale), color=(180, 180, 180))
            frame.add_child(label)
            y += 25

        except Exception as e:
            label = TextLabel(5, y, f"Encryption error: {e}", int(14 * self.scale), color=(255, 100, 100))
            frame.add_child(label)
            y += 25

        frame.content_height = max(frame.height, y + 10)

    # ------------------------------------------------------------------
    # Helper methods for UI elements
    # ------------------------------------------------------------------

    def _add_label(self, text, x, y, tab_frame, font_size=None):
        if font_size is None:
            font_size = int(14 * self.scale)
        label = TextLabel(x, y, text, font_size, color=self.style.text_color)
        tab_frame.add_child(label)
        return label

    def _add_value_label(self, initial_text, x, y, tab_frame):
        label = TextLabel(x, y, initial_text, int(14 * self.scale), color=(220, 220, 100))
        tab_frame.add_child(label)
        return label

    def _get_cpu_model(self) -> str:
        proc_str = platform.processor()
        if not proc_str:
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
                return match.group(0).strip()[:26]
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
            return cleaned[:40] if len(cleaned) > 40 else cleaned
        except Exception:
            return "OpenGL (unknown)"

    # ------------------------------------------------------------------
    # Custom Function management
    # ------------------------------------------------------------------

    def add_custom_function(self, name: str, callable_obj: Callable, parameters: List[Tuple[str, type]], description: str = ""):
        self.custom_functions[name] = {
            'callable': callable_obj,
            'parameters': parameters,
            'description': description
        }
        self._refresh_custom_dropdown()
        if self.custom_functions:
            first_name = list(self.custom_functions.keys())[0]
            self.custom_dropdown.set_selected_index(0)
            self._on_custom_func_selected(0, first_name)

    def _refresh_custom_dropdown(self):
        names = list(self.custom_functions.keys())
        if not names:
            names = ["No functions"]
        self.custom_dropdown.set_options(names, 0)
        if names and names[0] != "No functions":
            self._on_custom_func_selected(0, names[0])

    def _on_custom_func_selected(self, index: int, name: str):
        self.custom_params_frame.clear_content()
        self.custom_desc_label.set_text("")
        self.custom_result_label.set_text("")

        if name == "No functions" or name not in self.custom_functions:
            return

        func_info = self.custom_functions[name]
        self.custom_desc_label.set_text(func_info['description'])

        y = 5
        self._param_inputs = {}
        for param_name, param_type in func_info['parameters']:
            label = TextLabel(5, y, f"{param_name} ({param_type.__name__}):", int(14 * self.scale), color=(200, 200, 200))
            self.custom_params_frame.add_child(label)

            if param_type is int:
                widget = NumberSelector(150, y, 100, 22, min_value=-1000, max_value=1000, value=0, label="", label_size=0)
            elif param_type is float:
                widget = NumberSelector(150, y, 100, 22, min_value=-1000.0, max_value=1000.0, value=0.0, label="", label_size=0, step=0.1)
            elif param_type is str:
                widget = TextBox(150, y, 100, 22, font_size=int(16 * self.scale), label="", label_size=0)
            elif param_type is bool:
                widget = Checkbox(150, y, 20, 20, False, label="")
            else:
                widget = TextLabel(150, y + 2, "Unsupported type", int(14 * self.scale), color=(255, 100, 100))

            self.custom_params_frame.add_child(widget)
            self._param_inputs[param_name] = (widget, param_type)
            y += 28

        self.custom_params_frame.content_height = max(self.custom_params_frame.height, y + 10)
        self.custom_params_frame.scroll_y = 0

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
            self.console_log_manager.add_log(LogLevel.INFO, f"Custom function '{func_name}' returned: {result}")
        except Exception as e:
            self.custom_result_label.set_text(f"[x] > Error: {e}")
            self.console_log_manager.add_log(LogLevel.ERROR, f"Custom function '{func_name}' error: {e}")

    # ------------------------------------------------------------------
    # Hierarchy and properties
    # ------------------------------------------------------------------

    def _build_root_hierarchy(self):
        self.hierarchy_stack.clear()
        root_elements = self.engine.current_scene.ui_elements if self.engine.current_scene else []
        self._current_display_elements = root_elements.copy()
        self._build_hierarchy_view(root_elements)

    def recharge(self):
        # UI mutation callbacks can call recharge while the inspector is open.
        # Preserve the current path rather than silently jumping back to root.
        if self.hierarchy_stack:
            parent = self.hierarchy_stack[-1]
            if parent not in self.engine.current_scene.ui_elements and not parent.parent:
                self._build_root_hierarchy()
                return
            self._build_hierarchy_view(parent.children)
        else:
            root_elements = self.engine.current_scene.ui_elements if self.engine.current_scene else []
            self._build_hierarchy_view(root_elements)

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
            self.hierarchy_stack.pop()
            if self.hierarchy_stack:
                self._build_hierarchy_view(self.hierarchy_stack[-1].children)
            else:
                root_elements = self.engine.current_scene.ui_elements if self.engine.current_scene else []
                self._build_hierarchy_view(root_elements)
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
            self.hierarchy_stack.append(element)
            self._build_hierarchy_view(element.children)

    def _show_element_properties(self, element: UIElement):
        self.properties_frame.clear_content()
        scale = self.scale

        title = TextLabel(int(5 * scale), 0, f"Properties of {element.element_type} [{element.element_id}]",
                          int(16 * scale), color=self.style.text_color)
        self.properties_frame.add_child(title)

        props = getattr(element, '_properties', {})
        spacing = 25
        total_props = 0
        for prop_name, prop_info in props.items():
            total_props += 1
            prop_type = prop_info.get('type', None)
            if prop_type is bool:
                value = getattr(element, prop_info.get('key', prop_name), False)
                line = Checkbox(int(5 * scale), int((total_props * spacing) * scale), int(100 * scale), int(18 * scale), value, f"{prop_info.get('name', prop_name)}")
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
                line = NumberSelector(int(5 * scale), int((total_props * spacing) * scale), int(120 * scale), int(18 * scale),
                                      min_value=min_val, max_value=max_val, value=value,
                                      label=prop_info.get('name', prop_name), label_size=int(14 * scale))
                line.set_on_value_changed(lambda val, e=element, k=prop_info.get('key', prop_name): setattr(e, k, val))
            elif prop_type is Literal:
                value = getattr(element, prop_info.get('key', prop_name), None)
                options = prop_info.get('options', [])
                if isinstance(options, list) and all(isinstance(opt, str) for opt in options):
                    line = Dropdown(int(5 * scale), int((total_props * spacing) * scale), int(150 * scale), int(18 * scale),
                                    options, int(14 * scale), label=prop_info.get('name', prop_name), label_size=int(14 * scale))
                    if value in options:
                        line.selected_index = options.index(value)
                    line.set_on_selection_changed(lambda index, name, e=element, k=prop_info.get('key', prop_name), opts=options: setattr(e, k, opts[index]))
                else:
                    display_name = prop_info.get('name', prop_name)
                    value_str = repr(value) if value is not None else "None"
                    line = TextLabel(int(5 * scale), int((total_props * spacing) * scale), f"{display_name}: {value_str}",
                                     int(18 * scale), color=(200, 200, 200))
            elif prop_type is str:
                value = getattr(element, prop_info.get('key', prop_name), "")
                line = TextBox(int(5 * scale), int((total_props * spacing) * scale), int(150 * scale), int(18 * scale),
                               font_size=int(16 * scale), label=prop_info.get('name', str(prop_name).capitalize()), label_size=int(14 * scale))
                line.set_text(text=value)
                line.set_on_text_changed(lambda text, e=element, k=prop_info.get('key', prop_name): setattr(e, k, text))
            elif prop_type is ThemeStyle:
                # Skip style editing for now – just display the style name
                value = getattr(element, prop_info.get('key', prop_name), None)
                line = TextLabel(int(5 * scale), int((total_props * spacing) * scale),
                                f"{prop_info.get('name', prop_name)}: <ThemeStyle>",
                                int(18 * scale), color=(200, 200, 200))
            elif prop_type in (tuple, Color, Tuple[int, int, int]):
                value = getattr(element, prop_info.get('key', prop_name), None)
                if value is None:
                    value = (0, 0, 0)
                if isinstance(value, Color):
                    value = value.to_rgb_tuple()
                if len(value) >= 3:
                    line = ColorPicker(int(5 * scale), int((total_props * spacing) * scale), int(150 * scale), int(22 * scale), int(150 * scale),
                                       color_system='rgb', initial_color=value[:3])
                    line.set_on_color_changed(lambda color, e=element, k=prop_info.get('key', prop_name): setattr(e, k, color))
                else:
                    continue
            else:
                display_name = prop_info.get('name', prop_name)
                value = getattr(element, prop_info.get('key', prop_name), None)
                value_str = repr(value) if value is not None else "None"
                line = TextLabel(int(5 * scale), int((total_props * spacing) * scale), f"{display_name}: {value_str}",
                                 int(18 * scale), color=(200, 200, 200))
            line.add_group('live-inspector-ignore')
            self.properties_frame.add_child(line)

        if not props or total_props <= 0:
            msg = TextLabel(int(5 * scale), 0, "No editable properties", int(16 * scale), color=(150, 150, 150))
            self.properties_frame.add_child(msg)
        else:
            kill_button = Button(int(5 * scale), int((total_props * spacing + 20) * scale), int(80 * scale), int(18 * scale), "Remove", int(14 * scale))
            kill_button.set_on_click(lambda: element.kill())
            self.properties_frame.add_child(kill_button)

            restart_button = Button(int(95 * scale), int((total_props * spacing + 20) * scale), int(80 * scale), int(18 * scale), "Restart", int(14 * scale))
            restart_button.set_on_click(lambda: self._show_element_properties(element.restart()))
            self.properties_frame.add_child(restart_button)

        self.properties_frame._needs_rearrange = True
        self.properties_frame.scroll_y = 0

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
        if self.debug_manager is None: return
        self.overlays_scrolling.clear_content()
        y = 0
        for ovr in self.debug_manager.overlays:
            if isinstance(ovr, LiveInspector):
                continue
            fr = UiFrame(10, y, self.overlays_scrolling.width - 20, 32)
            fr.add_child(TextLabel(5, 16, str(type(ovr).__name__), int(18 * self.scale), pivot=(0, 0.5)))
            hide_btn = Button(fr.width - 5, 16, 50, 24, "Hide", int(16 * self.scale), pivot=(1, 0.5))
            hide_btn.set_on_click(lambda ovr=ovr: setattr(ovr, 'visible', not ovr.visible))
            fr.add_child(hide_btn)
            delete_btn = Button(fr.width - 60, 16, 50, 24, "Remove", int(16 * self.scale), pivot=(1, 0.5))
            delete_btn.set_on_click(lambda ovr=ovr: self.debug_manager.remove_overlay(ovr, callback=self.update_overlays_scrolling))
            fr.add_child(delete_btn)
            self.overlays_scrolling.add_child(fr)
            y += 32

    def set_debug_manager(self, dm: 'DebugManager'):
        self.debug_manager = dm
        self.update_overlays_scrolling()

    # ------------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------------

    def update(self, dt: float, input_state: InputState):
        if not self.visible:
            return
        super().update(dt, input_state)
        # Update all tabs that have an update function
        for name, (_, update_func) in self._tabs.items():
            if update_func:
                update_func()

    # ------------------------------------------------------------------
    # Console redirection
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
                    msg = self.buffer.rstrip('\n')
                    if msg:
                        self.log_manager.add_log(self.level, msg)
                    self.buffer = ""

            def flush(self):
                self.original.flush()

        sys.stdout = ConsoleStream(self.console_log_manager, self._original_stdout, LogLevel.INFO)
        sys.stderr = ConsoleStream(self.console_log_manager, self._original_stderr, LogLevel.ERROR)

    def _restore_console(self):
        if hasattr(self, '_original_stdout'):
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr


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

    def add_overlay(self, overlay: DebugOverlay) -> None:
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
        if callback:
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
