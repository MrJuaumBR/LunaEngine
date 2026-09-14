"""
LunaEngine Main Engine - Core Game Loop and Management System

LOCATION: lunaengine/core/engine.py

DESCRIPTION:
The central engine class that orchestrates the entire game lifecycle. Manages
scene transitions, rendering pipeline, event handling, performance monitoring,
and UI system integration. This is the primary interface for game developers.

KEY RESPONSIBILITIES:
- Game loop execution with fixed timestep
- Scene management and lifecycle control
- Event distribution to scenes and UI elements
- Performance monitoring and optimization
- Theme management across the entire application
- Resource initialization and cleanup
- Atlas-based resource catalog for asset management
- Resource bundle loading (optional, with progress bar)

LIBRARIES USED:
- pygame: Window management, event handling, timing, and surface operations
- numpy: Mathematical operations for game calculations
- threading: Background task management for bundle loading
- typing: Type hints for better code documentation

DEPENDENCIES:
- ..backend.pygame_backend: Default rendering backend
- ..ui.elements: UI component system
- ..utils.performance: Performance monitoring utilities
- .scene: Scene management base class
- ..misc.atlas: Resource catalog system
"""

import pygame
import time
import os
import threading
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Callable, Optional, Type, Any, Union

from ..ui.layer_manager import UILayerManager
from ..ui.notifications import NotificationPosition, NotificationType, notification_manager
from ..ui.themes import ThemeManager, ThemeType, ThemeKey
from ..utils.timer import Timer, get_global_timer
from .scene import Scene
from ..utils import PerformanceMonitor, GarbageCollector, BackgroundTaskManager
from ..misc.debug import DebugManager, LiveInspector
from ..backend import OpenGLRenderer, EVENTS, InputState, LExceptions, ControllerManager, Ratio, FocusOrder, JButton, Axis
from ..storage.savedata import Savedata
from .window import Window
from .. import __version__, ui, __status__

from .audio import AudioManager

from ..storage import Atlas, AtlasCategory, AtlasItem
from ..misc import Icon, Icons

# ---- SCENE TRANSITION SYSTEM (CPU surface version) ----
from ..backend.transition import Transition, TransitionType


class LunaEngine:
    """
    Main game engine class for LunaEngine.
    
    This class manages the entire game lifecycle including initialization,
    scene management, event handling, rendering, and shutdown.
    
    Attributes:
        title (str): Window title
        width (int): Window width
        height (int): Window height
        fullscreen (bool): Whether to start in fullscreen mode
        running (bool): Whether the engine is running
        clock (pygame.time.Clock): Game clock for FPS control
        scenes (Dict[str, Scene]): Registered scenes
        current_scene (Scene): Currently active scene
        atlas (Atlas): Resource catalog for all assets
        bundle_path (Optional[Path]): Path to resource bundle (.res) if any
    """
    def __init__(self, title: str = "LunaEngine Game", width: int = 800, height: int = 600, fullscreen: bool = False, icon: Optional[Union[str, Path, pygame.Surface, Icon, AtlasItem, Callable[[], Icon], None]] = None, **kwargs):
        """
        Initialize the LunaEngine.
        
        Args:
            title (str): The title of the game window (default: "LunaEngine Game")
            width (int): The width of the game window (default: 800)
            height (int): The height of the game window (default: 600)
            fullscreen (bool): Start in fullscreen mode (default: False)
            icon (str|pygame.Surface): Window icon
            **kwargs: Additional options:
                - show_splash (bool): Show splash screen (default: True)
                - splash_logo (pygame.Surface): Custom logo surface
                - splash_logo_size (int): Logo size for splash (default: 64)
                - debug (bool): Enable debug mode (default: False)
                - enable_performance_profiling (bool): Enable profiling (default: True)
                - atlas_root (str|Path): Root path for the atlas (default: current directory)
                - bundle_path (str|Path): Path to resource bundle (.res file) (default: auto-detect "game.res")
                - bundle_key (str): Obfuscation key for the bundle (if encrypted)
        """
        self.title = title
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.icon = icon
        self.show_splash = kwargs.get('show_splash', True)
        self.splash_logo = kwargs.get('splash_logo', None)
        self.splash_logo_size = kwargs.get('splash_logo_size', 64)
        self.Ratio: Ratio = Ratio(width, height)
        
        # Resource bundle options
        self.bundle_path = kwargs.get('bundle_path', None)
        self.bundle_obfuscation_key = kwargs.get('bundle_key', None)
        
        # Window
        self.window = Window(title=title, width=width, height=height, fullscreen=fullscreen, resizable=False)
        self.monitor_size: Union[pygame.display._VidInfo, None] = None
        self._last_window_size = (width, height)
        self._last_window_pos = (0, 0)
        self._window_focused = True
        self._window_minimized = False
        self._window_maximized = False
        
        self.running = False
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[Scene] = None
        self.previous_scene_name: Optional[str] = None
        self._event_handlers: Dict[str, List[Dict[str, Callable[[pygame.event.Event], None]]]] = {}
        self.input_state = InputState()
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        self.garbage_collector = GarbageCollector()
        self.background_tasks = BackgroundTaskManager(monitor=self.performance_monitor)
        
        # Performance profiling settings
        self.enable_performance_profiling(kwargs.get('enable_performance_profiling', True))
        
        # Render
        self.renderer: Union[Renderer, OpenGLRenderer, None] = None
        self.screen = None
        
        # Notification system
        self.notification_manager = notification_manager
        self.notification_manager.set_engine(self)
        
        # Notification configuration
        self.notification_max_concurrent = 5
        self.notification_margin = 20
        self.notification_spacing = 10
        
        # Atlas resource catalog
        atlas_root = kwargs.get('atlas_root', None)
        self.atlas = Atlas(root_path=atlas_root)
        # Let FontManager use this atlas for font resolution
        ui.FontManager.set_atlas(self.atlas)
        
        # Automatically initialize
        self.initialize()
        self.animation_handler = ui.AnimationHandler(self)
        self.layer_manager = UILayerManager()
        
        # Controller System
        self.controller_manager = ControllerManager(self)
        self.focused_ui_element: Optional[ui.UIElement] = None
        self.controller_ui_mode: bool = False
        self.focus_order: FocusOrder = FocusOrder.SO_Y_X
        
        # Global Audio
        self.audio = AudioManager()
        
        # Debug
        self.debug_enabled = kwargs.get('debug', False)
        self.debug_manager = DebugManager(self)
        if self.debug_enabled:
            self.debug_manager.add_overlay(LiveInspector(self))
        
        # Timer system
        self.timer = Timer()
        
        if kwargs.get('has_savedata', False) and kwargs.get('savedata_path', None) is not None:
            self.savedata = Savedata(str(kwargs['savedata_path']), encryption_key=kwargs.get('savedata_key', None))
        
        # Version
        self.version = __version__
        self.status = __status__

        # ---- SCENE TRANSITION SYSTEM ----
        self._transition: Optional[Transition] = None
        self._transitioning: bool = False

    def _auto_discover_assets(self) -> None:
        """Scan the atlas root for common asset folders and add them automatically."""
        root = self.atlas.root_path
        if root is None:
            return
        # For example, look for an "assets" folder
        assets_dir = root / "assets"
        if assets_dir.exists() and assets_dir.is_dir():
            for file_path in assets_dir.rglob("*"):
                if file_path.is_file():
                    # Use the file stem as name, but you might want a relative name
                    try:
                        self.atlas.add_to_atlas(file_path.stem, file_path, auto_detect=True)
                    except Exception as e:
                        print(f"Warning: Could not auto-add {file_path}: {e}")
    
    def update_ratio(self, base_width: int | float, base_height: int | float):
        """Update the aspect ratio scaling factor."""
        self.Ratio = Ratio(self.width / base_width, self.height / base_height)
    updateRatio = update_ratio
        
    @property
    def ratio(self) -> Ratio:
        return self.Ratio
    
    def initialize(self):
        """Initialize the engine and create the game window."""
        pygame.init()
        
        self.monitor_size: Union[pygame.display._VidInfo, None] = pygame.display.Info()
        
        # Initialize font system early
        ui.FontManager.initialize()
        
        # Create the display based on renderer type
        # Set OpenGL attributes BEFORE creating display
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        
        try:
            code = pygame.OPENGL | pygame.DOUBLEBUF
            if self.fullscreen:
                self.width, self.height = self.monitor_size.current_w, self.monitor_size.current_h
                code |= pygame.FULLSCREEN | pygame.SCALED
                print(f"Setting fullscreen mode: {self.width}x{self.height}")
            self.window.create()
            self.screen = self.window.surface
        except Exception as e:
            raise LExceptions.OpenGLInitializationError(e)
        
        self.set_title(self.title)
        self.set_icon(self.icon)
        
        # Create renderer
        self.renderer: Union[Renderer, OpenGLRenderer, None] = OpenGLRenderer(self.width, self.height)
        
        self.update_camera_renderer()
        
        # Initialize both renderers
        renderer_success = self.renderer.initialize()
        
        self.running = True
        self.start_time = time.time()
        print("Engine initialization complete")
        
        from ..ui.elements import UIElement
        UIElement._global_engine = self
        
        self.splash_logo = self.get_logo_surface() or None
        
        if self.show_splash:
            self._show_splash()
        
    def get_logo_surface(self) -> Optional[pygame.Surface]:
        """Return the engine logo surface if available."""
        cur_path = os.path.dirname(os.path.abspath(__file__))
        logo_file = os.path.join(cur_path, '..', 'assets', 'lunaengine-icon.png')
        if os.path.exists(logo_file):
            return pygame.image.load(logo_file).convert_alpha()
        return None
    getLogoSurface = get_logo_surface
            
    def _show_splash(self):
        """Display an animated splash screen with logo, title, subtitle, version, and progress bar."""
        if not self.running: return
        if not self.renderer: return

        version = __version__
        status = __status__
        splash_duration = 2.0
        anim_duration = 0.5
        start_time = time.time()
        clock = pygame.time.Clock()

        # Load logo if provided
        logo_surf = None
        if self.splash_logo:
            orig_w, orig_h = self.splash_logo.get_size()
            scale = self.splash_logo_size / orig_h
            new_w = int(orig_w * (scale * 1.1))
            new_h = self.splash_logo_size
            logo_surf = pygame.transform.smoothscale(self.splash_logo, (new_w, new_h))

        # Pre‑render text surfaces
        title_font = ui.FontManager.get_font(font_size=int(self.splash_logo_size*0.9))
        subtitle_font = ui.FontManager.get_font(font_size=int(self.splash_logo_size*0.65))
        version_font = ui.FontManager.get_font(font_size=int(self.splash_logo_size*0.45))

        title_surf = title_font.render("LunaEngine", True, (255, 255, 255))
        subtitle_surf = subtitle_font.render("It is a Framework, not an engine", True, (200, 200, 200))
        version_surf = version_font.render(f"Version {version}-{str(status).upper()[0:2]}", True, (150, 150, 150))

        # Pre‑compute final positions
        screen_center_x = self.width // 2
        screen_center_y = self.height // 2

        # Title final position (centered, but shifted right if logo exists)
        title_final_x = screen_center_x + (logo_surf.get_width() // 2 if logo_surf else 0)
        title_final_y = screen_center_y - self.splash_logo_size * 0.8
        title_final_rect = title_surf.get_rect(center=(title_final_x, title_final_y))

        # Logo final position (to the left of title)
        if logo_surf:
            logo_final_x = title_final_rect.left - logo_surf.get_width() - 10
            logo_final_y = title_final_y - logo_surf.get_height() // 2

        # Subtitle and version final positions (centered)
        sub_final_rect = subtitle_surf.get_rect(center=(screen_center_x, screen_center_y + 10))
        ver_final_rect = version_surf.get_rect(center=(screen_center_x, screen_center_y + 60))

        # Progress bar dimensions
        bar_width = 300
        bar_height = 20
        bar_x = (self.width - bar_width) // 2
        bar_y = self.height - 80

        # --- Bundle loading state ---
        bundle_load_complete = False
        bundle_progress = 0.0
        bundle_error = None
        load_thread = None

        def load_bundle_thread():
            nonlocal bundle_load_complete, bundle_progress, bundle_error
            try:
                if self.bundle_path is None:
                    default_bundle = Path.cwd() / "game.res"
                    if default_bundle.exists():
                        self.bundle_path = default_bundle
                    else:
                        bundle_load_complete = True
                        return

                def progress_callback(current, total):
                    nonlocal bundle_progress
                    bundle_progress = current / total if total > 0 else 1.0

                self.atlas.load_from_bundle(self.bundle_path,
                                            obfuscation_key=self.bundle_obfuscation_key,
                                            progress_callback=progress_callback)
                bundle_load_complete = True
            except Exception as e:
                bundle_error = e
                bundle_load_complete = True
                print(f"Failed to load bundle: {e}")

        if self.bundle_path is not None or (Path.cwd() / "game.res").exists():
            load_thread = threading.Thread(target=load_bundle_thread, daemon=True)
            load_thread.start()
        else:
            bundle_load_complete = True

        # --- Splash loop ---
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    # Allow skip only after bundle loaded or after 1 second
                    if bundle_load_complete or time.time() - start_time > 1.0:
                        # Break out of the loop gracefully
                        pass

            elapsed = time.time() - start_time
            t = min(1.0, elapsed / anim_duration)

            self.renderer.begin_frame()
            self.renderer.fill_screen((30, 30, 40, 255))

            # --- Animate logo, title, subtitle, version (same as before) ---
            if logo_surf:
                logo_scale = 0.5 + 0.5 * t
                logo_w = int(logo_surf.get_width() * logo_scale)
                logo_h = int(logo_surf.get_height() * logo_scale)
                logo_x = int((-logo_w) + (logo_final_x + logo_w) * t)
                logo_y = int(logo_final_y - (logo_h - logo_surf.get_height()) / 2)
                self.renderer.blit(logo_surf, pygame.Rect(logo_x, logo_y, logo_w, logo_h))

            title_scale = 0.5 + 0.5 * t
            title_w = int(title_surf.get_width() * title_scale)
            title_h = int(title_surf.get_height() * title_scale)
            start_title_x = self.width
            end_title_x = title_final_rect.centerx - title_w // 2
            title_x = int(start_title_x + (end_title_x - start_title_x) * t)
            title_y = int(title_final_rect.centery - title_h // 2)
            self.renderer.blit(title_surf, pygame.Rect(title_x, title_y, title_w, title_h))

            if t > 0:
                alpha = int(255 * t)
                faded_sub = subtitle_surf.copy()
                faded_sub.set_alpha(alpha)
                self.renderer.blit(faded_sub, sub_final_rect)
                faded_ver = version_surf.copy()
                faded_ver.set_alpha(alpha)
                self.renderer.blit(faded_ver, ver_final_rect)

            # --- Progress bar ---
            if not bundle_load_complete:
                prog_width = int(bar_width * bundle_progress)
                self.renderer.draw_rect(bar_x, bar_y, bar_width, bar_height,
                                        (60, 60, 80), fill=True, border_width=1, border_color=(100,100,120))
                if prog_width > 0:
                    self.renderer.draw_rect(bar_x, bar_y, prog_width, bar_height,
                                            (70, 130, 180), fill=True, corner_radius=4)
                font = pygame.font.SysFont(None, 24)
                text_surf = font.render("Loading resources...", True, (200, 200, 200))
                self.renderer.blit(text_surf, (bar_x + 10, bar_y - 30))
            elif bundle_error:
                font = pygame.font.SysFont(None, 24)
                text_surf = font.render(f"Bundle error: {bundle_error}", True, (255, 100, 100))
                self.renderer.blit(text_surf, (bar_x + 10, bar_y - 30))
            else:
                # Load complete – show full bar
                self.renderer.draw_rect(bar_x, bar_y, bar_width, bar_height,
                                        (60, 60, 80), fill=True, border_width=1, border_color=(100,100,120))
                self.renderer.draw_rect(bar_x, bar_y, bar_width, bar_height,
                                        (70, 130, 180), fill=True, corner_radius=4)

            self.renderer.end_frame()
            clock.tick(60)

            if bundle_load_complete and elapsed > 1.0:
                break
            if elapsed >= splash_duration and bundle_load_complete:
                break

        if load_thread and load_thread.is_alive():
            load_thread.join(timeout=0.5)

        if bundle_error:
            print(f"Bundle loading failed: {bundle_error}. Continuing without bundle.")
        
    def set_title(self, title: str):
        """Set the window title."""
        pygame.display.set_caption(title)
    setTitle = set_title
        
    def set_icon(self, icon: Optional[Union[str, Path, pygame.Surface, Icon, AtlasItem, Callable[[], Icon], None]]):
        """
        Set the window icon.

        Supports:
            - file path (str or Path)
            - pygame.Surface
            - Icon (from icons.py)
            - AtlasItem (from the resource atlas)
            - callable returning an Icon (e.g. Icons.BRAIN)

        The icon is automatically scaled to 64×64 for best window compatibility.
        """
        if icon is None:
            return

        # If it's a callable (like Icons.BRAIN), call it to get the Icon
        if callable(icon) and not isinstance(icon, type):
            try:
                result = icon()
                if isinstance(result, Icon):
                    icon = result
            except Exception:
                # If calling fails, we'll treat it as an unsupported type
                pass

        surf = None

        if isinstance(icon, (str, Path)):
            try:
                surf = pygame.image.load(str(icon)).convert_alpha()
            except pygame.error:
                surf = pygame.image.load(str(icon)).convert()

        elif isinstance(icon, pygame.Surface):
            surf = icon

        elif isinstance(icon, Icon):
            # Default to white colour for the window icon
            surf = icon.get_surface(color=(255, 255, 255))

        elif isinstance(icon, AtlasItem):
            # Try to load from bundle memory first
            data = self.atlas.get_bytes(icon.name)
            if data:
                surf = pygame.image.load(io.BytesIO(data)).convert_alpha()
            else:
                # Fallback to reading from disk
                try:
                    surf = pygame.image.load(str(icon.path)).convert_alpha()
                except pygame.error:
                    surf = pygame.image.load(str(icon.path)).convert()
            if surf is None:
                raise ValueError(f"Could not load icon from {icon.path}")

        else:
            raise TypeError(f"Unsupported icon type: {type(icon)}")

        # Scale to 64×64 if not already
        if surf.get_size() != (64, 64):
            surf = pygame.transform.smoothscale(surf, (64, 64))

        pygame.display.set_icon(surf)
    setIcon = set_icon
    
    def update_camera_renderer(self):
        """Update all scene cameras with the current renderer."""
        for scene in self.scenes.values():
            if hasattr(scene, 'camera'):
                scene.camera.renderer = self.renderer
    
    def get_focusable_elements(self) -> List[ui.UIElement]:
        """Return all focusable UI elements that are globally visible and enabled."""
        if not self.current_scene:
            return []
        if self.input_state.active_controller is None:
            return []
        focusable = []
        def collect(elem):
            if elem.is_globally_visible() and elem.enabled and elem.can_focus:
                focusable.append(elem)
            for child in elem.children:
                collect(child)
        for elem in self.current_scene.ui_elements:
            collect(elem)
        # Sort by current focus order
        if self.focus_order == FocusOrder.SO_X_Y:
            focusable.sort(key=lambda e: (e.selection_order, e.x, e.y))
        else:
            focusable.sort(key=lambda e: (e.selection_order, e.y, e.x))
        return focusable
    
    def move_focus(self, direction: str) -> bool:
        """
        Move focus to the next/previous element in the focusable list.
        Direction: 'up', 'down', 'left', 'right' (uses spatial logic) or 'next', 'prev'.
        """
        elems = self.get_focusable_elements()
        if not elems:
            return False
        
        if self.focused_ui_element is None or self.focused_ui_element not in elems:
            self.focused_ui_element = elems[0]
            return True
        
        if direction in ('next', 'prev'):
            current_index = elems.index(self.focused_ui_element)
            step = 1 if direction == 'next' else -1
            self.focused_ui_element = elems[(current_index + step) % len(elems)]
        else:
            vectors = {'left': (-1.0, 0.0), 'right': (1.0, 0.0),
                       'up': (0.0, -1.0), 'down': (0.0, 1.0)}
            if direction not in vectors:
                return False
            return self.move_focus_vector(*vectors[direction], _elements=elems)

        self._ensure_focus_visible(self.focused_ui_element)
        return True

    def move_focus_vector(self, dx: float, dy: float, _elements=None) -> bool:
        """Focus the nearest visible element in an arbitrary screen-space direction."""
        elems = _elements if _elements is not None else self.get_focusable_elements()
        if not elems:
            return False
        if self.focused_ui_element is None or self.focused_ui_element not in elems:
            self.focused_ui_element = elems[0]
            self._ensure_focus_visible(self.focused_ui_element)
            return True
        magnitude = (dx * dx + dy * dy) ** 0.5
        if magnitude <= 0.001:
            return False
        ux, uy = dx / magnitude, dy / magnitude
        current_rect = self.focused_ui_element.getCollideRect()
        cx, cy = current_rect.center
        candidates = []
        for elem in elems:
            if elem is self.focused_ui_element:
                continue
            ex, ey = elem.getCollideRect().center
            vx, vy = ex - cx, ey - cy
            distance = (vx * vx + vy * vy) ** 0.5
            if distance <= 0.001:
                continue
            alignment = (vx * ux + vy * uy) / distance
            if alignment <= 0.05:
                continue
            # Prefer elements in the stick direction, then the nearest one.
            score = distance * (1.0 + (1.0 - alignment) * 1.75)
            candidates.append((score, distance, elem))
        if not candidates:
            return False
        candidates.sort(key=lambda item: (item[0], item[1]))
        self.focused_ui_element = candidates[0][2]
        self._ensure_focus_visible(self.focused_ui_element)
        return True

    def handle_controller_vector(self, dx: float, dy: float) -> bool:
        """Dispatch an arbitrary analog-stick vector to the focused widget."""
        elem = self.focused_ui_element
        direction = None
        if abs(dx) >= abs(dy):
            direction = 'right' if dx > 0 else 'left'
        else:
            direction = 'down' if dy > 0 else 'up'
        if elem and elem.is_globally_visible() and elem.enabled:
            if hasattr(elem, 'on_directional_input') and elem.on_directional_input(direction):
                return True
        return self.move_focus_vector(dx, dy)

    def _ensure_focus_visible(self, element: Optional['ui.UIElement']) -> None:
        """Scroll every ancestor until a newly focused element is visible."""
        if element is None:
            return
        from ..ui.elements.containers import ScrollingFrame
        current = element
        while current:
            parent = current.parent
            if isinstance(parent, ScrollingFrame):
                child_rect = parent._get_child_screen_rect(current)
                view = parent._get_visible_rect()
                dx = 0
                dy = 0
                if child_rect.left < view.left:
                    dx = child_rect.left - view.left
                elif child_rect.right > view.right:
                    dx = child_rect.right - view.right
                if child_rect.top < view.top:
                    dy = child_rect.top - view.top
                elif child_rect.bottom > view.bottom:
                    dy = child_rect.bottom - view.bottom
                if dx or dy:
                    parent.scroll_by(dx, dy)
            current = parent
    
    def update_controller_ui_navigation(self, dt: float):
        """Handle all controller-based UI navigation: focus, scrolling, tab switching, and activation."""
        if not self.controller_ui_mode:
            return
        if not self.controller_manager.is_using_controller():
            return
        
        controller = self.controller_manager.get_first_connected()
        if not controller or self.input_state.active_controller is None:
            return
        
        # ---- State tracking for "just pressed" detection ----
        if not hasattr(self, '_prev_controller_state'):
            self._prev_controller_state = {
                'a': False, 'b': False, 'lb': False, 'rb': False,
                'lx': 0, 'ly': 0, 'rx': 0, 'ry': 0,
                'dpad_up': False, 'dpad_down': False, 'dpad_left': False, 'dpad_right': False
            }
        prev = self._prev_controller_state
        
        # ---- Read current inputs ----
        a_pressed = controller.get_button_pressed(JButton.A)
        b_pressed = controller.get_button_pressed(JButton.B)
        lb_pressed = controller.get_button_pressed(JButton.LEFT_BUMPER)
        rb_pressed = controller.get_button_pressed(JButton.RIGHT_BUMPER)
        
        hat_x, hat_y = controller.get_hat()
        dpad_up = hat_y == 1
        dpad_down = hat_y == -1
        dpad_left = hat_x == -1
        dpad_right = hat_x == 1
        
        lx = controller.get_axis(Axis.LEFT_X)
        ly = controller.get_axis(Axis.LEFT_Y)
        rx = controller.get_axis(Axis.RIGHT_X)
        ry = controller.get_axis(Axis.RIGHT_Y)
        
        THRESHOLD = 0.4
        lx_active = abs(lx) > THRESHOLD
        ly_active = abs(ly) > THRESHOLD
        rx_active = abs(rx) > THRESHOLD
        ry_active = abs(ry) > THRESHOLD
        
        # ---- 1. ACTIVATION / BACK ----
        if a_pressed and not prev['a']:
            self.activate_focused_element()
        if b_pressed and not prev['b']:
            # Roblox-style back behavior: close an open selector first, then
            # leave the current tab when possible. Do not invoke the focused
            # element's action accidentally with the back button.
            elem = self.focused_ui_element
            if elem and getattr(elem, 'expanded', False):
                elem.expanded = False
            elif elem:
                tab = self._find_tabination_ancestor(elem)
                if tab:
                    tab.previous_tab()
        
        # ---- 2. TAB SWITCHING (LB / RB) ----
        if lb_pressed and not prev['lb']:
            if self.focused_ui_element:
                tab = self._find_tabination_ancestor(self.focused_ui_element)
                if tab:
                    tab.previous_tab()
        if rb_pressed and not prev['rb']:
            if self.focused_ui_element:
                tab = self._find_tabination_ancestor(self.focused_ui_element)
                if tab:
                    tab.next_tab()
        
        # ---- 3. FOCUS MOVEMENT (Left stick or D-pad) ----
        moved = False
        if dpad_left and not prev['dpad_left']:
            moved = self.handle_controller_direction('left')
        elif dpad_right and not prev['dpad_right']:
            moved = self.handle_controller_direction('right')
        elif dpad_up and not prev['dpad_up']:
            moved = self.handle_controller_direction('up')
        elif dpad_down and not prev['dpad_down']:
            moved = self.handle_controller_direction('down')
        
        if not moved and (lx_active or ly_active):
            if lx_active and prev['lx'] == 0:
                moved = self.handle_controller_vector(lx, -ly if ly_active else 0.0)
            elif ly_active and prev['ly'] == 0:
                moved = self.handle_controller_vector(lx if lx_active else 0.0, -ly)
        
        # ---- 4. SCROLLING (Right stick) ----
        if self.focused_ui_element:
            scrollable = self._find_scrollable_ancestor(self.focused_ui_element)
            if scrollable:
                scroll_speed = 300 * dt
                dx = rx * scroll_speed if rx_active else 0
                dy = ry * scroll_speed if ry_active else 0
                if dx != 0 or dy != 0:
                    scrollable.scroll_by(dx, dy)
        
        # ---- Update previous state ----
        prev['a'] = a_pressed
        prev['b'] = b_pressed
        prev['lb'] = lb_pressed
        prev['rb'] = rb_pressed
        prev['lx'] = lx if lx_active else 0
        prev['ly'] = ly if ly_active else 0
        prev['rx'] = rx if rx_active else 0
        prev['ry'] = ry if ry_active else 0
        prev['dpad_up'] = dpad_up
        prev['dpad_down'] = dpad_down
        prev['dpad_left'] = dpad_left
        prev['dpad_right'] = dpad_right
    
    def _find_tabination_ancestor(self, element: 'ui.UIElement') -> Optional['ui.Tabination']:
        """Traverse parents to find the nearest Tabination container."""
        from ..ui.elements.containers import Tabination
        current = element
        while current:
            if isinstance(current, Tabination):
                return current
            current = current.parent
        return None

    def _find_scrollable_ancestor(self, element: 'ui.UIElement') -> Optional['ui.ScrollingFrame']:
        """Traverse parents to find the nearest ScrollingFrame."""
        from ..ui.elements.containers import ScrollingFrame
        current = element
        while current:
            if isinstance(current, ScrollingFrame):
                return current
            current = current.parent
        return None

    def activate_focused_element(self) -> bool:
        """
        Activate (click/toggle) the currently focused UI element.
        Returns True if something was activated.
        """
        if not self.focused_ui_element:
            return False
        elem: ui.UIElement = self.focused_ui_element
        if not elem.enabled:
            return False
        if not elem.is_globally_visible():
            return False
        # Give widgets such as Select, Dropdown, Slider, and Checkbox a
        # controller-specific activation hook before callback fallback.
        if hasattr(elem, 'on_activate'):
            elem.on_activate()
        if hasattr(elem, 'on_click_callback'):
            if elem.on_click_callback is not None:
                if elem.on_click_args or elem.on_click_kwargs:
                    try:
                        elem.on_click_callback(*elem.on_click_args, **elem.on_click_kwargs)
                    except Exception:
                        elem.on_click_callback()
                else:
                    elem.on_click_callback()
                return True
        
        if hasattr(elem, 'focused'):
            elem.focused = True
            return True
        
        if hasattr(elem, 'on_click'):
            elem.on_click()
            return True
            
        return False

    def handle_controller_direction(self, direction: str) -> bool:
        """Let the focused widget consume direction before moving focus."""
        elem = self.focused_ui_element
        if elem and elem.is_globally_visible() and elem.enabled:
            if hasattr(elem, 'on_directional_input') and elem.on_directional_input(direction):
                return True
        return self.move_focus(direction)

    def get_clipboard(self, default: str = "") -> str:
        """Return text from the system clipboard, or ``default`` if unavailable."""
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            data = pygame.scrap.get(pygame.SCRAP_TEXT)
            if data is None:
                return default
            if isinstance(data, bytes):
                return data.decode('utf-8', errors='replace').rstrip('\x00')
            return str(data)
        except (pygame.error, AttributeError, TypeError):
            return default

    def set_clipboard(self, text: Any) -> bool:
        """Set text in the system clipboard; return False if unavailable."""
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, str(text).encode('utf-8'))
            return True
        except (pygame.error, AttributeError, TypeError):
            return False

    def add_scene(self, name: str, scene_class: Type[Scene], *args, **kwargs):
        """
        Add a scene to the engine by class (the engine will instantiate it).
        
        Args:
            name (str): The name of the scene
            scene_class (Type[Scene]): The scene class to instantiate
            *args: Arguments to pass to scene constructor
            **kwargs: Keyword arguments to pass to scene constructor
        """
        if callable(scene_class):
            scene_instance = scene_class(self, *args, **kwargs)
        else:
            scene_instance = scene_class
        self.scenes[name] = scene_instance
        scene_instance.name = name
    addScene = add_scene
        
    def _switch_scene_immediate(self, name: str):
        """
        Immediately switch to a scene without any transition effect.
        This is the core logic extracted from the old set_scene.
        """
        if name in self.scenes:
            # Call on_exit for current scene
            if self.current_scene:
                self.current_scene.on_exit(name)
                
            # Store previous scene name
            previous_name = None
            for scene_name, scene_obj in self.scenes.items():
                if scene_obj == self.current_scene:
                    previous_name = scene_name
                    break
            self.previous_scene_name = previous_name
            
            # Set new scene and call on_enter
            self.current_scene = self.scenes[name]
            if hasattr(self, 'debug_manager') and self.debug_manager:
                self.debug_manager.on_scene_changed()
            self.current_scene.on_enter(self.previous_scene_name)
            # The main loop rebuilds this cache before event/update processing.
            # Refresh it here as well so an immediate scene switch cannot render
            # the previous scene's controls for one extra frame.
            self._rebuild_ui_layers()
    
    def set_scene(self, name: str, effect: Optional[TransitionType] = None, duration: float = 0.5):
        """
        Set the current active scene, optionally with a transition effect.

        Args:
            name (str): The name of the scene to set as current.
            effect (TransitionType, optional): Type of transition effect.
                If None or TransitionType.NONE, switch immediately.
            duration (float): Duration of the transition in seconds (default 0.5).
        """
        if effect is None or effect == TransitionType.NONE:
            self._switch_scene_immediate(name)
        else:
            self.transition_to(name, effect, duration)
    setScene = set_scene
    
    def find_event_handlers(self, event: int, rep_id: str) -> bool:
        # Placeholder for future event handler management
        return False
    
    def on_event(self, event_type: int, rep_id: Optional[str] = None):
        """
        Decorator to register event handlers
        
        Args:
            event_type (int): The Pygame event type to listen for
            rep_id (str, optional): A representative ID for the handler
        Returns:
            Callable: The decorator function
        """
        def decorator(func):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append({'callable': func, 'rep_id': rep_id})
            return func
        return decorator
    
    def setup_notifications(self, max_concurrent: int = 5, margin: int = 20, spacing: int = 10):
        """
        Setup notification system configuration.
        
        Args:
            max_concurrent: Maximum concurrent notifications to show
            margin: Margin from screen edges
            spacing: Spacing between stacked notifications
        """
        self.notification_max_concurrent = max_concurrent
        self.notification_margin = margin
        self.notification_spacing = spacing
        
        self.notification_manager.set_max_concurrent(max_concurrent)
        self.notification_manager.set_default_margin(margin)
        self.notification_manager.set_spacing(spacing)
    
    def show_notification(self, text: str, 
                         notification_type: NotificationType = NotificationType.INFO,
                         duration: Optional[float] = None,
                         position=NotificationPosition.TOP_RIGHT,
                         width: int = 300,
                         height: int = 60,
                         show_close_button: bool = True,
                         auto_close: bool = True,
                         animation_speed: float = 0.3,
                         show_progress_bar: bool = False,
                         on_close: Optional[Callable] = None,
                         on_click: Optional[Callable] = None):
        """
        Show a notification with advanced options.
        
        Args:
            text: Notification text
            notification_type: Type of notification
            duration: Display duration in seconds
            position: Position (NotificationPosition or custom (x, y) tuple)
            width: Width of notification
            height: Height of notification
            show_close_button: Whether to show close button
            auto_close: Whether notification auto-closes
            animation_speed: Speed of slide/fade animations
            show_progress_bar: Whether to show progress bar
            on_close: Callback when notification is closed
            on_click: Callback when notification is clicked
            
        Returns:
            The created Notification object
        """
        from ..ui.notifications import NotificationConfig
        
        config = NotificationConfig(
            text=text,
            notification_type=notification_type,
            duration=duration,
            position=position,
            width=width,
            height=height,
            show_close_button=show_close_button,
            auto_close=auto_close,
            animation_speed=animation_speed,
            show_progress_bar=show_progress_bar,
            on_close=on_close,
            on_click=on_click
        )
        
        return self.notification_manager.show_notification(config)
    
    def show_info(self, text: str, duration: Optional[float] = None,
                  position=NotificationPosition.TOP_RIGHT) -> 'Notification':
        """Show an info notification."""
        return self.show_notification(text, NotificationType.INFO, duration, position)
    
    def show_success(self, text: str, duration: Optional[float] = None,
                     position=NotificationPosition.TOP_RIGHT) -> 'Notification':
        """Show a success notification."""
        return self.show_notification(text, NotificationType.SUCCESS, duration, position)
    
    def show_warning(self, text: str, duration: Optional[float] = None,
                     position=NotificationPosition.TOP_RIGHT) -> 'Notification':
        """Show a warning notification."""
        return self.show_notification(text, NotificationType.WARNING, duration, position)
    
    def show_error(self, text: str, duration: Optional[float] = None,
                   position=NotificationPosition.TOP_RIGHT) -> 'Notification':
        """Show an error notification."""
        return self.show_notification(text, NotificationType.ERROR, duration, position)
    
    def clear_all_notifications(self):
        """Clear all notifications."""
        self.notification_manager.clear_all()
    
    def get_notification_count(self) -> int:
        """Get current number of active notifications."""
        return self.notification_manager.get_notification_count()
    
    def get_notification_queue_length(self) -> int:
        """Get current notification queue length."""
        return self.notification_manager.get_queue_length()
    
    def has_notifications(self) -> bool:
        """Check if there are any active notifications."""
        return self.notification_manager.has_notifications()
    
    def has_queued_notifications(self) -> bool:
        """Check if there are any queued notifications."""
        return self.notification_manager.has_queued_notifications()
    
    def get_all_themes(self) -> Dict[str, any]:
        """
        Get all available themes including user custom ones
        
        Returns:
            Dict[str, any]: Dictionary with theme names as keys and theme objects as values
        """
        
        all_themes = {}
        
        for theme_enum in ThemeType:
            theme = ThemeManager.get_theme(theme_enum)
            all_themes[theme_enum.value] = {
                'enum': theme_enum,
                'theme': theme,
                'type': 'builtin'
            }
        
        for theme_key, theme_value in ThemeManager._themes.items():
            if theme_key not in all_themes:
                theme_name = theme_key.value if hasattr(theme_key, 'value') else str(theme_key)
                all_themes[theme_name] = {
                    'enum': theme_key,
                    'theme': theme_value,
                    'type': 'custom'
                }
        
        return all_themes

    def get_theme_names(self) -> List[str]:
        """
        Get list of all available theme names
        
        Returns:
            List[str]: List of theme names
        """
        themes = self.get_all_themes()
        return list(themes.keys())

    def set_global_theme(self, theme: Union[ThemeType, str], dark:Optional[bool] = True) -> bool:
        """
        Set the global theme for the entire engine and update all UI elements
        
        Args:
            theme_name (str): Name of the theme to set
            
        Returns:
            bool: True if theme was set successfully, False otherwise
        """
        
        
        if type(theme) is ThemeType:
            theme_name = theme.value
        else:
            theme_name = theme
        
        themes = self.get_theme_names()
        if theme_name in themes:
            theme_data = ThemeManager.get_theme_type_by_name(theme_name)
            ThemeManager.set_current_theme(theme_data)
            self.set_dark_mode(dark)
            self._update_all_ui_themes(theme_data)
            return True
        
        return False
    
    def set_dark_mode(self, dark: bool|None):
        """
        Set the global dark mode for the engine and update all UI elements
        
        Args:
            dark (bool): True
        """
        if dark is None: return
        ThemeManager.set_dark_mode(dark)
        current_theme = ThemeManager.get_current_theme()
        self._update_all_ui_themes(current_theme)
        from ..ui.tooltips import UITooltipManager
        UITooltipManager.update_all_themes(current_theme)
        
    def get_dark_mode(self) -> bool:
        """
        Get the global dark mode for the engine
        
        Returns:
            bool: True if dark mode is enabled, False otherwise
        """
        return ThemeManager.get_dark_mode()

    def _update_all_ui_themes(self, theme_enum):
        """Update all UI elements in the current scene to use the new theme."""
        if self.current_scene and hasattr(self.current_scene, 'ui_elements'):
            for ui_element in self.current_scene.ui_elements:
                if hasattr(ui_element, 'update_theme'):
                    ui_element.update_theme(theme_enum)
        
        if self.current_scene:
            for attr_name in dir(self.current_scene):
                attr = getattr(self.current_scene, attr_name)
                if hasattr(attr, 'update_theme'):
                    attr.update_theme(theme_enum) 
    
    def get_fps_stats(self) -> dict:
        """
        Get comprehensive FPS statistics (optimized)
        
        Returns:
            dict: A dictionary containing FPS statistics
        """
        return self.performance_monitor.get_stats()
    getFpsStats = get_fps_stats
    
    def get_hardware_info(self) -> dict:
        """Get hardware information"""
        return self.performance_monitor.get_hardware_info()
    getHardwareInfo = get_hardware_info
    
    def ScaleSize(self, width: float, height: float) -> Tuple[float, float] | Tuple[int, int]:
        """
        Scale size is a function that will convert scales size to a pixel size
        
        e.g.:
        - 1.0, 1.0 = Full Screen
        - 0.5, 0.5 = Half Screen
        - 0.5, 1.0 = Half Screen Width, Full Screen Height
        
        Args:
            width (float): Width scale
            height (float): Height scale
        Returns:
            Tuple[float, float]|Tuple[int, int]: Pixel size
        """
        size = self.screen.get_size()
        size = (size[0] * width, size[1] * height)
        return size
    
    def ScalePos(self, x: float, y: float) -> Tuple[float, float] | Tuple[int, int]:
        """
        Scale position is a function that will convert scales position to a pixel position
        
        e.g.:
        - 1.0, 1.0 = Bottom Right
        - 0.0, 0.0 = Top Left
        - 0.5, 0.5 = Center
        
        Args:
            x (float): X position
            y (float): Y position
        Returns:
            Tuple[float, float]|Tuple[int, int]: Pixel position
        """
        size = self.screen.get_size()
        size = (size[0] * x, size[1] * y)
        return size

    def _rebuild_ui_layers(self):
        """Rebuild the UI layer manager from the current scene's UI elements."""
        self.layer_manager.clear_all()
        if self.current_scene and hasattr(self.current_scene, 'ui_elements'):
            for ui_element in self.current_scene.ui_elements:
                self.layer_manager.add_element(ui_element)

    def _find_scrollable_under_mouse(self, elements, mouse_pos):
        """
        Recursively search UI elements (and their children) for the topmost
        visible, enabled element that has an 'on_scroll' method and contains the mouse.
        """
        sorted_elements = sorted(elements, key=lambda e: e.z_index, reverse=True)
        for elem in sorted_elements:
            if not elem.visible or not elem.enabled:
                continue
            if str(elem.type) == 'scrollingframe' and elem.mouse_over(mouse_pos, is_for_scroll_event=True) and hasattr(elem, 'on_scroll'):
                return elem
            elif hasattr(elem, 'on_scroll') and elem.mouse_over(mouse_pos):
                return elem
            if hasattr(elem, 'children') and elem.children:
                found = self._find_scrollable_under_mouse(elem.children, mouse_pos)
                if found:
                    return found
        return None

    def _dispatch_mouse_wheel(self, event):
        """Dispatch MOUSEWHEEL event to the topmost scrollable UI element under the mouse."""
        mouse_pos = self.mouse_pos
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return False
        root_elements = self.current_scene.ui_elements
        target = self._find_scrollable_under_mouse(root_elements, mouse_pos)
        if target:
            target.on_scroll(event)
            return True
        return False

    def run(self):
        """Main game loop."""
        if self.renderer is None:
            self.initialize()

        while self.running:
            self.performance_monitor.start_timer('frame')
            self.performance_monitor.update_frame()

            dt = self.clock.tick(self.fps) / 1000.0

            self.input_state.clear_consumed()
            
            # Rebuild UI layers once per frame (before mouse/event handling)
            self._rebuild_ui_layers()

            # Profile mouse update
            self.performance_monitor.start_timer("mouse")
            self.update_mouse()
            ui.UITooltipManager.update(self, dt)
            self.performance_monitor.end_timer("mouse")
            
            # Profile notification update
            self.performance_monitor.start_timer("notifications")
            self.notification_manager.update(dt, self.input_state)
            self.performance_monitor.end_timer("notifications")
            
            # Profile event handling
            self.performance_monitor.start_timer("events")
            events = pygame.event.get()
            
            # Handle controller events
            self.controller_manager.handle_events(events)
            
            # Update input state with controller info
            self.input_state.using_controller = self.controller_manager.is_using_controller()
            self.input_state.active_controller = self.controller_manager.get_first_connected()
            self.input_state.controller_count = len(self.controller_manager)
            if self.controller_manager.is_using_controller():
                self.controller_ui_mode = True
            if self.input_state.active_controller:
                self.update_controller_ui_navigation(dt)
            
            for event in events:
                if event.type == EVENTS.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEWHEEL:
                    self.input_state.mouse_wheel += event.y
                    self._dispatch_mouse_wheel(event)
                    continue
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        self.controller_ui_mode = not self.controller_ui_mode
                        if not self.controller_ui_mode:
                            self.focused_ui_element = None
                    elif event.key == pygame.K_TAB:
                        direction = 'prev' if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 'next'
                        self.move_focus(direction)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.activate_focused_element()
                        
                elif event.type == pygame.JOYBUTTONDOWN and self.input_state.active_controller:
                    if event.button == JButton.START.value or event.button == JButton.GUIDE.value:
                        self.controller_ui_mode = not self.controller_ui_mode
                        if not self.controller_ui_mode:
                            self.focused_ui_element = None
                    
                # Handle window events
                self.window.handle_pygame_event(event)
                
                # Call registered event handlers
                if event.type in self._event_handlers:
                    for handler in self._event_handlers[event.type]:
                        handler['callable'](event)
            self.performance_monitor.end_timer("events")
            
            # Update current scene with profiling
            if self.current_scene:
                self.performance_monitor.start_timer("scene")
                self.current_scene._update(dt)
                self.performance_monitor.end_timer("scene")
                
            # Update all animations with profiling
            self.performance_monitor.start_timer("animations")
            self.animation_handler.update(dt)
            self.performance_monitor.end_timer("animations")
            
            # Update UI elements with profiling
            self.performance_monitor.start_timer("ui")
            self._update_ui_elements(dt)
            self.debug_manager.update(dt, self.input_state)
            self.performance_monitor.end_timer("ui")
            
            # Update timers
            self.performance_monitor.start_timer("timers")
            self.timer.update()
            self.performance_monitor.end_timer("timers")
            
            # Update background tasks
            self.background_tasks.update(dt)

            # ---- SCENE TRANSITION UPDATE ----
            if self._transitioning:
                self._update_transition(dt)
            
            # Render with profiling
            self.performance_monitor.start_timer("render")
            if self._transitioning and self._transition:
                self._render_transition()
            else:
                self._render()
            self.performance_monitor.end_timer("render")
            
            self.performance_monitor.end_timer('frame')
            
            # End frame profiling
            self.performance_monitor.end_frame()
            
            # Periodic garbage collection
            self.garbage_collector.cleanup()
        
        self.shutdown()
        
    # ---- SCENE TRANSITION SYSTEM (CPU SURFACE VERSION) ----

    def transition_to(self, scene_name: str,
                      effect: TransitionType = TransitionType.NONE,
                      duration: float = 0.5):
        """
        Start a transition using immutable snapshots of both scenes.
        """
        if self._transitioning:
            return

        from_scene = self.current_scene
        to_scene = self.scenes.get(scene_name)
        if not to_scene:
            raise ValueError(f"Scene '{scene_name}' not found")

        if effect == TransitionType.NONE:
            self._switch_scene_immediate(scene_name)
            return

        if from_scene is to_scene:
            return

        # Prepare the target before capturing it, so enter-time setup is visible
        # in the snapshot. It is not updated until the transition completes.
        to_scene.on_enter(from_scene.name if from_scene else None)

        # Capture both scenes as surfaces
        from_surf = self._capture_scene_surface(from_scene)
        to_surf = self._capture_scene_surface(to_scene)

        self._transition = Transition(
            from_scene=from_scene,
            to_scene=to_scene,
            effect=effect,
            duration=duration,
            from_surface=from_surf,
            to_surface=to_surf
        )
        self._transitioning = True

    def _capture_scene_surface(self, scene: 'Scene') -> pygame.Surface:
        """
        Render the given scene (including UI and particles) to a pygame.Surface.
        """
        if scene is None:
            surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
            surf.fill((0, 0, 0, 255))
            return surf

        def draw_scene():
            if scene.shadow_system_enabled and hasattr(scene, 'shadow_system'):
                scene.shadow_system.render(self.renderer)
            scene.render(self.renderer)
            if hasattr(scene, 'particle_system') and scene.particle_system:
                scene.particle_system.render(scene.camera)
            self._render_ui_elements_for_scene(scene)

        return self.renderer.capture_to_surface(draw_scene)

    def _render_ui_elements_for_scene(self, scene):
        """Render all UI elements of a given scene (sorted by z_index)."""
        if not scene or not hasattr(scene, 'ui_elements'):
            return
        # Sort by z_index (ascending)
        elements = sorted(scene.ui_elements, key=lambda e: getattr(e, 'z_index', 0))
        for elem in elements:
            elem.render(self.renderer)

    def _update_transition(self, dt: float):
        if not self._transitioning or not self._transition:
            return

        tr = self._transition
        if tr.duration == 0.0:
            tr.progress = 1.0
        else:
            tr.progress += dt / tr.duration

        if tr.progress >= 1.0:
            tr.progress = 1.0
            tr.finished = True

            # Finalise scene switch
            if tr.from_scene:
                tr.from_scene.on_exit(tr.to_scene.name if tr.to_scene else None)
            self.current_scene = tr.to_scene
            if hasattr(self, 'debug_manager') and self.debug_manager:
                self.debug_manager.on_scene_changed()
            # Transition completion happens after the frame's normal layer
            # rebuild, so refresh now before the first full target-scene render.
            self._rebuild_ui_layers()
            if self.focused_ui_element not in self.get_focusable_elements():
                self.focused_ui_element = None

            # Clean up surfaces
            tr.from_surface = None
            tr.to_surface = None

            self._transitioning = False
            self._transition = None

    def _render_transition(self):
        tr = self._transition
        if not tr or tr.from_surface is None or tr.to_surface is None:
            return

        progress = tr.eased_progress
        old, new = tr.from_surface, tr.to_surface
        blended = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
        blended.fill((0, 0, 0, 255))

        if tr.effect == TransitionType.FADE:
            blended.blit(old, (0, 0))
            new_copy = new.copy(); new_copy.set_alpha(int(progress * 255)); blended.blit(new_copy, (0, 0))
        elif tr.effect in (TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT,
                           TransitionType.SLIDE_UP, TransitionType.SLIDE_DOWN):
            dx, dy = 0, 0
            if tr.effect == TransitionType.SLIDE_LEFT: dx = -self.width
            if tr.effect == TransitionType.SLIDE_RIGHT: dx = self.width
            if tr.effect == TransitionType.SLIDE_UP: dy = -self.height
            if tr.effect == TransitionType.SLIDE_DOWN: dy = self.height
            blended.blit(old, (int(dx * progress), int(dy * progress)))
            blended.blit(new, (int(-dx * (1.0 - progress)), int(-dy * (1.0 - progress))))
        elif tr.effect in (TransitionType.ZOOM_IN, TransitionType.ZOOM_OUT):
            if tr.effect == TransitionType.ZOOM_IN:
                # Target scene starts small at the center and grows to full size.
                blended.blit(old, (0, 0))
                scale = max(0.01, progress)
                zoom = pygame.transform.smoothscale(new, (max(1, int(self.width * scale)), max(1, int(self.height * scale))))
                blended.blit(zoom, zoom.get_rect(center=(self.width // 2, self.height // 2)))
            else:
                # Target is already visible while the outgoing scene shrinks away.
                blended.blit(new, (0, 0))
                scale = 1.0 - progress
                zoom = pygame.transform.smoothscale(old, (max(1, int(self.width * scale)), max(1, int(self.height * scale))))
                blended.blit(zoom, zoom.get_rect(center=(self.width // 2, self.height // 2)))
        elif tr.effect in (TransitionType.ORBITAL_LEFT, TransitionType.ORBITAL_RIGHT):
            # Rotate both snapshots around the screen center. Alpha handoff
            # keeps the outgoing image exact at t=0 and the incoming image
            # exact at t=1, while preserving transparent rotated corners.
            direction = -1 if tr.effect == TransitionType.ORBITAL_LEFT else 1
            old_spin = pygame.transform.rotate(old, direction * 180.0 * progress)
            new_spin = pygame.transform.rotate(new, direction * 180.0 * (progress - 1.0))
            old_spin.set_alpha(int((1.0 - progress) * 255))
            new_spin.set_alpha(int(progress * 255))
            blended.blit(old_spin, old_spin.get_rect(center=(self.width // 2, self.height // 2)))
            blended.blit(new_spin, new_spin.get_rect(center=(self.width // 2, self.height // 2)))
        elif tr.effect == TransitionType.MORPH:
            # A surface snapshot cannot perform semantic pixel morphing, but a
            # cross-dissolve with a small scale change gives a stable, useful
            # morph-like result without requiring a shader or scene changes.
            old_scale = 1.0 + (0.06 * progress)
            new_scale = 0.94 + (0.06 * progress)
            old_morph = pygame.transform.smoothscale(old, (int(self.width * old_scale), int(self.height * old_scale)))
            new_morph = pygame.transform.smoothscale(new, (int(self.width * new_scale), int(self.height * new_scale)))
            old_morph.set_alpha(int((1.0 - progress) * 255))
            new_morph.set_alpha(int(progress * 255))
            blended.blit(old_morph, old_morph.get_rect(center=(self.width // 2, self.height // 2)))
            blended.blit(new_morph, new_morph.get_rect(center=(self.width // 2, self.height // 2)))
        elif tr.effect == TransitionType.FLASH:
            # White flash peaks at the midpoint, with the scene change hidden
            # inside the flash so the result reads as a camera-flash cut.
            if progress < 0.5:
                blended.blit(old, (0, 0))
                white_alpha = int(progress * 2.0 * 255)
            else:
                blended.blit(new, (0, 0))
                white_alpha = int((1.0 - progress) * 2.0 * 255)
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
            flash.fill((255, 255, 255, max(0, min(255, white_alpha))))
            blended.blit(flash, (0, 0))
        else:
            blended.blit(old, (0, 0))
            new_copy = new.copy(); new_copy.set_alpha(int(progress * 255)); blended.blit(new_copy, (0, 0))

        # Draw the blended result to the screen
        self.renderer.clear()
        self.renderer.begin_frame()
        self.renderer.draw_surface(blended, 0, 0)
        self.renderer.end_frame()

    # ---- END SCENE TRANSITION SYSTEM ----

    def add_timer(self, name: str, duration: float, callback: Optional[Callable] = None,
              callback_args: tuple = (), callback_kwargs: dict = None,
              repeats: bool = False) -> bool:
        """Add a timer. Returns True if added successfully."""
        return self.timer.add(name, duration, callback, callback_args, callback_kwargs, repeats)

    def add_anonymous_timer(self, duration: float, callback: Callable,
                            callback_args: tuple = (), callback_kwargs: dict = None,
                            repeats: bool = False) -> str:
        """Add a timer with an auto‑generated name and return its name."""
        return self.timer.add_timer_to(duration, callback, callback_args, callback_kwargs, repeats)

    def remove_timer(self, name: str) -> bool:
        """Remove a timer immediately."""
        return self.timer.remove(name)

    def destroy_timer(self, name: str) -> bool:
        """Mark a timer for destruction (removed on next update)."""
        return self.timer.destroy(name)

    def pause_timer(self, name: str) -> bool:
        """Pause a timer."""
        return self.timer.pause(name)

    def resume_timer(self, name: str) -> bool:
        """Resume a paused timer."""
        return self.timer.resume(name)

    def reset_timer(self, name: str) -> bool:
        """Reset a timer to start counting from now."""
        return self.timer.reset(name)

    def timer_elapsed(self, name: str) -> Optional[float]:
        """Get elapsed time for a timer."""
        return self.timer.get_elapsed(name)

    def timer_remaining(self, name: str) -> Optional[float]:
        """Get remaining time for a timer."""
        return self.timer.get_remaining(name)

    def timer_done(self, name: str) -> Optional[bool]:
        """Check if a timer has completed."""
        return self.timer.is_done(name)

    def timer_exists(self, name: str) -> bool:
        """Check if a timer exists."""
        return self.timer.exists(name)

    def timer_paused(self, name: str) -> Optional[bool]:
        """Check if a timer is paused."""
        return self.timer.is_paused(name)

    def clear_timers(self) -> None:
        """Remove all timers."""
        self.timer.clear()

    def get_all_timers(self) -> List[str]:
        """Get names of all active timers."""
        return self.timer.get_all_timers()

    def get_timer_count(self) -> int:
        """Get the number of active timers."""
        return self.timer.get_timer_count()
        
    def on_window_resize(self, func: Callable):
        """Decorator for window resize event."""
        return self.window.on_resize(func)
    
    def on_window_close(self, func: Callable):
        """Decorator for window close event."""
        return self.window.on_close(func)
    
    def on_window_focus(self, func: Callable):
        """Decorator for window focus gained event."""
        return self.window.on_focus(func)
    
    def on_window_blur(self, func: Callable):
        """Decorator for window blur (focus lost) event."""
        return self.window.on_blur(func)
    
    def on_window_move(self, func: Callable):
        """Decorator for window move event."""
        return self.window.on_move(func)
    
    def on_window_minimize(self, func: Callable):
        """Decorator for window minimize event."""
        return self.window.on_minimize(func)
    
    def on_window_maximize(self, func: Callable):
        """Decorator for window maximize event."""
        return self.window.on_maximize(func)
    
    def on_window_restore(self, func: Callable):
        """Decorator for window restore event."""
        return self.window.on_restore(func)
    
    def on_window_enter(self, func: Callable):
        """Decorator for mouse entering window event."""
        return self.window.on_enter(func)
    
    def on_window_leave(self, func: Callable):
        """Decorator for mouse leaving window event."""
        return self.window.on_leave(func)
    
    def get_window_state(self) -> Dict[str, Any]:
        """Get current window state."""
        return self.window.get_window_state()
    
    def is_window_focused(self) -> bool:
        """Check if window is focused."""
        return self.window.is_focused()
    
    def is_window_minimized(self) -> bool:
        """Check if window is minimized."""
        return self.window.is_minimized()
    
    def is_window_maximized(self) -> bool:
        """Check if window is maximized."""
        return self.window.is_maximized()
        
    def get_controllers(self) -> List['Controller']:
        return self.controller_manager.get_all_controllers()
    getControllers = get_controllers

    def get_controller(self, index: int) -> Optional['Controller']:
        return self.controller_manager.get_controller(index)
    getController = get_controller

    def is_using_controller(self) -> bool:
        return self.controller_manager.is_using_controller()

    def on_controller_connect(self, callback: Callable[['Controller'], None]):
        """Register callback when a controller connects."""
        self.controller_manager.on_connect.append(callback)

    def on_controller_disconnect(self, callback: Callable[['Controller'], None]):
        """Register callback when a controller disconnects."""
        self.controller_manager.on_disconnect.append(callback)
        
    def update_mouse(self):
        """Update mouse position and button state with proper click detection."""
        mouse_pos = pygame.mouse.get_pos()
        m_pressed = pygame.mouse.get_pressed(num_buttons=5)
        self.input_state.update(mouse_pos, m_pressed)
            
    def visibility_change(self, element: ui.UIElement, visible: bool):
        """Change visibility of an element or list of elements."""
        if type(element) in [list, tuple]:
            [self.visibility_change(e, visible) for e in element]
        else:
            element.visible = visible
            
    @property
    def mouse_pos(self) -> tuple:
        return self.input_state.mouse_pos
    
    @property
    def mouse_pressed(self) -> list:
        return [self.input_state.mouse_buttons_pressed.values() for i in range(5)]
    
    @property
    def mouse_wheel(self) -> float:
        return self.input_state.mouse_wheel

    def _render_focus_rect(self):
        """Render a yellow outline around the focused UI element."""
        if not self.focused_ui_element or not self.focused_ui_element.is_globally_visible() or self.input_state.active_controller is None:
            return
        elem = self.focused_ui_element
        x, y = elem.get_actual_position()
        w, h = elem.width, elem.height
        self.renderer.draw_rect(x, y, w, h, (255, 255, 0), fill=False, border_width=2)

    def _render(self):
        """Rendering with GPU particles and shadows."""
        try:
            self.renderer.clear()
            self.renderer.begin_frame()

            curr_scene = self.current_scene
            if curr_scene:
                if curr_scene.shadow_system_enabled and hasattr(curr_scene, 'shadow_system'):
                    self.performance_monitor.start_timer("shadows")
                    curr_scene.shadow_system.render(self.renderer)
                    self.performance_monitor.end_timer("shadows")
                
                self.performance_monitor.start_timer("scene_render")
                curr_scene.render(self.renderer)
                self.performance_monitor.end_timer("scene_render")
            
            self.performance_monitor.start_timer("particles")
            if curr_scene and hasattr(curr_scene, 'particle_system'):
                curr_scene.particle_system.render(curr_scene.camera)
            self.performance_monitor.end_timer("particles")

            self.performance_monitor.start_timer("ui_render")
            self._render_ui_elements()
            self.notification_manager.render(self.renderer)
            self.performance_monitor.end_timer("ui_render")
            
            self._render_focus_rect()
            
            self.debug_manager.render(self.renderer)

            self.renderer.end_frame()

        except Exception as e:
            print(f"OpenGL rendering error: {e}")
            import traceback
            traceback.print_exc()
            
    def live_inspector(self) -> Union[LiveInspector, None]:
        return self.debug_manager.live_inspector
    
    def add_function_to_live_inspector(self, name:str, callable_obj: Callable, parameters: List[Tuple[str, type]], description: str = "") -> None:
        if self.debug_manager:
            if self.debug_manager.live_inspector:
                self.debug_manager.live_inspector.add_custom_function(name, callable_obj, parameters, description)
            else:
                print('No live inspector to add function to.')
        else:
            print('No debug manager to add function to.')
    
    def _render_ui_elements(self):
        """Render UI elements with individual profiling if enabled."""
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return
        
        elements_to_render = self.layer_manager.get_elements_in_order()
        
        self.performance_monitor.start_timer("ui_total")
        
        for ui_element in elements_to_render:
            if hasattr(ui_element, 'parent') and ui_element.parent:
                continue
            ui_element.render(self.renderer)
        
        for tooltip in ui.UITooltipManager.get_tooltip_to_render(engine=self):
            tooltip.render(self.renderer)
        
        self.performance_monitor.end_timer("ui_total")
            
    def _render_particles(self):
        """Render particles using OpenGL."""
        if (self.current_scene and 
            hasattr(self.current_scene, 'particle_system') and
            hasattr(self.renderer, 'render_particles')):
            particle_data = self.current_scene.particle_system.get_render_data()
            if particle_data['active_count'] > 0:
                self.renderer.render_particles(particle_data, camera=self.current_scene.camera)
            try:
                pass
            except Exception as e:
                print(f"OpenGL particle rendering error: {e}")

    def _update_ui_elements(self, dt):
        if not self.current_scene or not hasattr(self.current_scene, 'ui_elements'):
            return

        self.performance_monitor.start_timer("ui_total")
        self.layer_manager.update(dt, self.input_state)
        self.performance_monitor.end_timer("ui_total")

    def _process_ui_element_tree(self, root_element, dt):
        """Process a UI element and all its children with proper event consumption."""
        if hasattr(root_element, 'update'):
            root_element.update(dt, self.input_state)
        for child in getattr(root_element, 'children', []):
            self._process_ui_element_tree(child, dt)
    
    def enable_performance_profiling(self, enabled: bool = True):
        """Enable/disable detailed performance profiling."""
        self.performance_monitor.create_timer("frame")
        self.performance_monitor.create_timer("mouse")
        self.performance_monitor.create_timer("events")
        self.performance_monitor.create_timer("scene")
        self.performance_monitor.create_timer("particles")
        self.performance_monitor.create_timer("ui")
        self.performance_monitor.create_timer("ui_total")
        self.performance_monitor.create_timer("notifications")
        self.performance_monitor.create_timer("frame_finalize")
        self.performance_monitor.create_timer("shadows")
        self.performance_monitor.enable_profiling(enabled)
    
    def get_frame_timing_breakdown(self) -> Dict[str, float]:
        """Get the timing breakdown (ms) for the last completed frame."""
        return self.performance_monitor.get_frame_timing_breakdown()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Return both FPS stats and frame timing breakdown."""
        stats = self.performance_monitor.get_stats()
        stats["frame_timings"] = self.get_frame_timing_breakdown()
        return stats
    
    def get_update_timing_stats(self, category: str = "all") -> Dict[str, Any]:
        """Get update timing statistics for a specific category."""
        return self.performance_monitor.get_update_timing_stats(category)
    
    def get_render_timing_stats(self, category: str = "all") -> Dict[str, Any]:
        """Get render timing statistics for a specific category."""
        return self.performance_monitor.get_render_timing_stats(category)
    
    def get_ui_update_stats(self) -> Dict[str, Any]:
        """Get UI update timing statistics."""
        return self.performance_monitor.get_update_timing_stats("ui")
    
    def get_ui_render_stats(self) -> Dict[str, Any]:
        """Get UI render timing statistics."""
        return self.performance_monitor.get_render_timing_stats("ui")
    
    def get_individual_ui_update_stats(self) -> Dict[str, float]:
        """Get individual UI element update timing statistics."""
        stats = self.performance_monitor.get_update_timing_stats("ui_individual")
        return stats.get("individual_times", {})
    
    def get_individual_ui_render_stats(self) -> Dict[str, float]:
        """Get individual UI element render timing statistics."""
        stats = self.performance_monitor.get_render_timing_stats("ui_individual")
        return stats.get("individual_times", {})
    
    def get_scene_update_stats(self) -> Dict[str, Any]:
        """Get scene update timing statistics."""
        return self.performance_monitor.get_update_timing_stats("scene")
    
    def get_scene_render_stats(self) -> Dict[str, Any]:
        """Get scene render timing statistics."""
        return self.performance_monitor.get_render_timing_stats("scene")
    
    def get_total_frame_time(self) -> Dict[str, float]:
        """Get total frame time breakdown."""
        update_stats = self.performance_monitor.get_all_update_timing_stats()
        render_stats = self.performance_monitor.get_all_render_timing_stats()
        
        total_update = sum(cat.get("current_ms", 0) for cat in update_stats.values())
        total_render = sum(cat.get("current_ms", 0) for cat in render_stats.values())
        
        return {
            "total_ms": total_update + total_render,
            "update_ms": total_update,
            "render_ms": total_render,
            "other_ms": self.performance_monitor.get_stats().get("frame_time_ms", 0) - (total_update + total_render)
        }
    
    # --------------------------------------------------------------------------
    # Atlas integration – convenience methods
    # --------------------------------------------------------------------------
    
    def add_to_atlas(self, name: str, path: Union[str, Path], 
                     category: Optional[Union[str, AtlasCategory]] = None,
                     auto_detect: bool = True, validate: bool = True) -> AtlasItem:
        """
        Add a file to the atlas.
        
        Args:
            name: Unique name for the resource.
            path: File path (string or Path).
            category: Explicit category (string or AtlasCategory). If None, will be auto-detected.
            auto_detect: If True and category is None, guess from extension.
            validate: If True, enforce extension rules for the category.
            
        Returns:
            AtlasItem: The created atlas item.
        """
        return self.atlas.add_to_atlas(name, path, category, auto_detect=auto_detect, validate=validate)
    
    def get_atlas_item(self, name: str) -> Optional[AtlasItem]:
        """Retrieve an atlas item by its name."""
        return self.atlas.get_item(name)
    
    def get_atlas_path(self, name: str, category: Optional[Union[str, AtlasCategory]] = None) -> Optional[Path]:
        """
        Get the file path of an atlas item, optionally checking its category.
        
        Args:
            name: Resource name.
            category: If provided, only return the path if the item's category matches.
            
        Returns:
            Path or None if not found.
        """
        item = self.get_atlas_item(name)
        if item and (category is None or item.category == category):
            return item.path
        return None
    
    def add_texture_to_atlas(self, name: str, path: Union[str, Path]) -> AtlasItem:
        """Shortcut to add a texture (image) to the atlas."""
        return self.add_to_atlas(name, path, AtlasCategory.TEXTURE)
    
    def add_font_to_atlas(self, name: str, path: Union[str, Path]) -> AtlasItem:
        """Shortcut to add a font to the atlas."""
        return self.add_to_atlas(name, path, AtlasCategory.FONT)
    
    def add_audio_to_atlas(self, name: str, path: Union[str, Path]) -> AtlasItem:
        """Shortcut to add an audio file to the atlas."""
        return self.add_to_atlas(name, path, AtlasCategory.AUDIO)
    
    def shutdown(self):
        """Cleanup resources."""
        self.garbage_collector.cleanup(force=True)
        self.background_tasks.shutdown(wait=True)
        self.audio.cleanup()
        if self.renderer:
            self.renderer.end_frame()
            self.renderer.cleanup()
        pygame.quit()
        sys.exit(0)
