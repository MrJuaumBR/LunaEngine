"""
Scene Management System - Game State and UI Container

LOCATION: lunaengine/core/scene.py
"""

import pygame
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TYPE_CHECKING, Tuple
from ..ui import UIElement, UiFrame, ScrollingFrame, Tabination, AnimationHandler
from ..graphics import Camera
from ..graphics.particles import ThreadedParticleSystem, ParticleSystem
from ..graphics.shadows import ShadowSystem
from ..core.audio import AudioSystem
from ..backend.opengl import OpenGLRenderer
from ..core.renderer import Renderer
from ..backend.types import ElementsList, ElementsListEvents

if TYPE_CHECKING:
    from ..core.engine import LunaEngine

class Scene(ABC):
    name: str = ''
    WIDTH: int = 0
    HEIGHT: int = 0

    def __init__(self, engine: 'LunaEngine', *args: tuple | Any, **kwargs: dict | Any):
        self.ui_elements: ElementsList = ElementsList(on_change=self._ui_element_list)
        self._initialized = False
        self.engine: LunaEngine = engine

        self.WIDTH, self.HEIGHT = self.engine.window.width, self.engine.window.height

        self._last_update_time = 0.0
        self._last_render_time = 0.0

        # Camera
        self.camera: Camera = Camera(self, engine.width, engine.height)

        # Particle System - GPU version
        self.particle_system = ThreadedParticleSystem(
            self.engine.renderer,
            self.engine.renderer.max_particles,
            self.engine.fps,
            True
        )
        self.engine.renderer.on_max_particles_change.append(
            self.particle_system.update_max_particles
        )

        # Shadows System - GPU version
        self.shadow_system = ShadowSystem()

        # Animation System
        self.animation_handler = AnimationHandler(engine)

        # Audio System
        self.audio_system: AudioSystem = AudioSystem(num_channels=16)

        # Window Events
        self.engine.window.on_resize(self.update_window_size)

    def update_window_size(self):
        self.WIDTH, self.HEIGHT = self.engine.window.width, self.engine.window.height

    def _add_event_to_handler(self, element: UIElement):
        if element.element_type in ['textbox', 'textarea']:
            @self.engine.on_event(pygame.KEYDOWN, element.element_id)
            def on_key_down(event):
                if element.focused and element.enabled:
                    element.on_key_down(event)

            @self.engine.on_event(pygame.KEYUP, element.element_id)
            def on_key_up(event):
                if element.focused and element.enabled:
                    element.on_key_up(event)
        elif element.element_type in ['scrollingframe', 'dropdown']:
            @self.engine.on_event(pygame.MOUSEWHEEL, element.element_id)
            def on_scroll(event):
                element.on_scroll(event)

    def _update_on_change_child(self, element: UIElement):
        self._add_event_to_handler(element)
        for child in element.children:
            child.children.set_on_change(self._ui_element_list, child)
            if hasattr(child, 'on_key_down'):
                self.engine.find_event_handlers(pygame.KEYDOWN, child.element_id)
            elif hasattr(child, 'on_key_up'):
                self.engine.find_event_handlers(pygame.KEYUP, child.element_id)
            elif hasattr(child, 'on_scroll'):
                self.engine.find_event_handlers(pygame.MOUSEWHEEL, child.element_id)
            child.scene = self
            self._update_on_change_child(child)

    def _ui_element_list(self, event_type: ElementsListEvents, element: UIElement, index: Optional[int] = None):
        if event_type == 'append':
            self._update_on_change_child(element)
            element.scene = self
            element.children.set_on_change(self._ui_element_list, element)

    def on_enter(self, previous_scene: Optional[str] = None) -> None:
        self._initialized = True

    def on_exit(self, next_scene: Optional[str] = None) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def _update(self, dt: float):
        self.engine.performance_monitor.start_timer("scene_camera")
        self.camera.update(dt)
        self.engine.performance_monitor.end_timer("scene_camera")

        self.engine.performance_monitor.start_timer("scene_particles")
        self.particle_system.update(dt)
        self.engine.performance_monitor.end_timer("scene_particles")

        self.update(dt)
        self.animation_handler.update(dt)

    def render(self, renderer: Renderer | OpenGLRenderer) -> None:
        pass

    def get_scene_performance_stats(self) -> Dict[str, float]:
        return {
            "last_update_time_ms": self._last_update_time * 1000,
            "last_render_time_ms": self._last_render_time * 1000,
            "ui_element_count": len(self.ui_elements),
            "particle_count": self.particle_system.active_count if hasattr(self, 'particle_system') else 0
        }

    def add_ui_element(self, ui_element: UIElement) -> None:
        self.ui_elements.append(ui_element)

    def remove_ui_element(self, ui_element: UIElement) -> bool:
        if ui_element in self.ui_elements:
            self.ui_elements.remove(ui_element)
            return True
        return False

    def get_ui_element_by_id(self, element_id: str) -> Optional[UIElement]:
        for ui_element in self.ui_elements:
            if hasattr(ui_element, 'element_id') and ui_element.element_id == element_id:
                return ui_element
        return None

    def get_ui_elements_by_type(self, element_type: type) -> List[UIElement]:
        return [element for element in self.ui_elements if isinstance(element, element_type)]

    def get_ui_elements_by_group(self, group: str) -> List[UIElement]:
        uis = []
        for ui in self.ui_elements:
            if hasattr(ui, 'groups'):
                if ui.has_group(str(group).lower()):
                    uis.append(ui)
        return uis

    def toggle_element_group(self, group: str, visible: bool) -> None:
        for ui in self.get_ui_elements_by_group(group):
            ui.visible = visible

    def clear_element_group(self, group: str) -> None:
        for ui in self.get_ui_elements_by_group(group):
            self.remove_ui_element(ui)

    def clear_element_type(self, element_type: type) -> None:
        for ui in self.get_ui_elements_by_type(element_type):
            self.remove_ui_element(ui)

    def get_all_ui_elements(self) -> List[UIElement]:
        return self.ui_elements.copy()

    def has_element_by_id(self, element_id: str) -> bool:
        return any(hasattr(ui_element, 'element_id') and ui_element.element_id == element_id for ui_element in self.ui_elements)

    def has_element(self, element: UIElement) -> bool:
        return element in self.ui_elements

    def get_debug_stats(self) -> Dict[str, Any]:
        return {
            "custom_value": self.some_metric,
        }
    def get_ui_count(self) -> int:
        n = len(self.ui_elements)
        for element in self.ui_elements:
            n += element.getIndexedChilds()
        return n

    def clear_ui_elements(self) -> None:
        self.ui_elements.clear()