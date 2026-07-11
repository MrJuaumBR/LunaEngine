# dialogs.py
import pygame
from typing import Optional, Callable, Literal, Dict, Any, Tuple
from .base import UIElement, FontManager, UIState, Color
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
from ...backend.types import InputState

class DialogBox(UIElement):
    """
    RPG-style dialog box with multiple display styles and text animations.
    Supports typewriter effect, fade-in, and character-by-character display.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'style': {'name': 'style', 'key': 'style', 'type': str, 'editable': True,
                  'description': 'Visual style: "default", "rpg", "pokemon", "modern".',
                  'options': ['default', 'rpg', 'pokemon', 'modern']},
        'text': {'name': 'text', 'key': 'text', 'type': str, 'editable': True,
                 'description': 'The dialog text content.'},
        'speaker_name': {'name': 'speaker name', 'key': 'speaker_name', 'type': str, 'editable': True,
                         'description': 'Name of the speaker displayed above the box.'},
        'animation_type': {'name': 'animation type', 'key': 'animation_type', 'type': str, 'editable': True,
                           'description': 'Type of text animation: "typewriter".'},
        'animation_speed': {'name': 'animation speed', 'key': 'animation_speed', 'type': int, 'editable': True,
                            'description': 'Characters per second for typewriter effect.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        style: Literal['default', 'rpg', 'pokemon', 'modern'] = "default",
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        """
        Initialize a dialog box.

        Args:
            x: X coordinate (before anchor).
            y: Y coordinate (before anchor).
            width: Width of dialog box.
            height: Height of dialog box.
            style: Visual style ("default", "rpg", "pokemon", "modern").
            theme: Theme to apply.
            element_id: Custom element ID.
        """
        super().__init__(x, y, width, height, (0, 0), element_id)
        self.style = style
        self.theme_type = theme or ThemeManager.get_current_theme()

        # Text properties
        self.text: str = ""
        self.displayed_text: str = ""
        self.speaker_name: str = ""
        self.font_size = 20
        self.font = FontManager.get_font(None, self.font_size)
        self.name_font = FontManager.get_font(None, self.font_size - 2)

        # Animation properties
        self.animation_type: str = "typewriter"
        self.animation_speed: int = 30   # characters per second
        self.animation_progress: float = 0.0
        self.is_animating: bool = False
        self.is_complete: bool = False

        # Visual properties based on style
        self.padding = 20
        self.name_padding = 10
        self.corner_radius = 8 if style in ["modern", "pokemon"] else 0
        self.show_continue_indicator = True
        self.continue_indicator_blink = True
        self.continue_timer = 0.0

        # Callbacks
        self.on_complete_callback: Optional[Callable[[], None]] = None
        self.on_advance_callback: Optional[Callable[[], None]] = None

        self.waiting_for_advance: bool = False

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'style': self.style,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def set_text(self, text: str, speaker_name: str = "", instant: bool = False) -> None:
        """
        Set the dialog text and start animation.

        Args:
            text: The full text to display.
            speaker_name: Name of the speaker (shown above box).
            instant: If True, show all text immediately without animation.
        """
        self.text = text
        self.speaker_name = speaker_name
        self.displayed_text = ""
        self.animation_progress = 0.0
        self.is_animating = not instant
        self.is_complete = instant
        self.waiting_for_advance = False

        if instant:
            self.displayed_text = text
            self.waiting_for_advance = True

    def set_animation(self, animation_type: str, speed: int = 30) -> None:
        """
        Configure text animation.

        Args:
            animation_type: Currently only "typewriter" is supported.
            speed: Characters per second.
        """
        self.animation_type = animation_type
        self.animation_speed = speed

    def skip_animation(self) -> None:
        """Immediately finish the text animation and mark as complete."""
        if self.is_animating:
            self.is_animating = False
            self.is_complete = True
            self.displayed_text = self.text
            self.waiting_for_advance = True
            if self.on_complete_callback:
                self.on_complete_callback()

    def advance(self) -> bool:
        """
        Advance the dialog (skip animation or move to next dialog).
        Returns True if the dialog is still active, False if it should be closed.
        """
        if self.is_animating:
            self.skip_animation()
            return True
        elif self.waiting_for_advance:
            self.waiting_for_advance = False
            self.is_complete = False
            self.displayed_text = ""
            if self.on_advance_callback:
                self.on_advance_callback()
            return False
        return True

    def set_on_complete(self, callback: Callable[[], None]) -> None:
        """Register a callback called when text animation finishes."""
        self.on_complete_callback = callback

    def set_on_advance(self, callback: Callable[[], None]) -> None:
        """Register a callback called when the user advances to the next dialog (after completion)."""
        self.on_advance_callback = callback

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            return

        mouse_over = self.mouse_over(inputState)

        if mouse_over and inputState.mouse_buttons_pressed.left and self.waiting_for_advance:
            self.advance()

        self.state = UIState.HOVERED if mouse_over else UIState.NORMAL

        if self.is_animating and self.animation_type == "typewriter":
            self.animation_progress += dt * self.animation_speed
            chars_to_show = min(len(self.text), int(self.animation_progress))
            self.displayed_text = self.text[:chars_to_show]

            if chars_to_show >= len(self.text):
                self.is_animating = False
                self.is_complete = True
                self.waiting_for_advance = True
                if self.on_complete_callback:
                    self.on_complete_callback()

        if self.show_continue_indicator and self.waiting_for_advance:
            self.continue_timer += dt
            if self.continue_timer >= 0.5:
                self.continue_timer = 0.0
                self.continue_indicator_blink = not self.continue_indicator_blink

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = ThemeManager.get_theme(self.theme_type)

        # Draw border
        if theme.dialog_border:
            renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                               theme.dialog_border.color, fill=False, border_width=self.border_width,
                               corner_radius=self.corner_radius)

        # Draw main dialog box background
        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           theme.dialog_background.color, fill=True,
                           border_width=self.border_width, corner_radius=self.corner_radius)

        # Draw speaker name
        if self.speaker_name:
            name_width = self.name_font.size(self.speaker_name)[0] + self.name_padding * 2
            name_height = self.name_font.get_height() + self.name_padding
            name_x = actual_x + 10
            name_y = actual_y - name_height // 2

            renderer.draw_rect(name_x, name_y, name_width, name_height,
                               theme.dialog_name_bg.color, fill=True,
                               corner_radius=self.corner_radius)

            name_surf = self.name_font.render(self.speaker_name, True, theme.dialog_name_text.color)
            renderer.draw_surface(name_surf, name_x + self.name_padding, name_y + self.name_padding // 2)

        # Draw text with word wrapping
        text_area_width = self.width - self.padding * 2
        text_area_height = self.height - self.padding * 2
        text_x = actual_x + self.padding
        text_y = actual_y + self.padding

        self._render_wrapped_text(renderer, text_x, text_y, text_area_width, text_area_height, theme)

        # Continue indicator (blinking arrow)
        if self.show_continue_indicator and self.waiting_for_advance and self.continue_indicator_blink:
            indicator_size = 10
            indicator_x = actual_x + self.width - self.padding - indicator_size
            indicator_y = actual_y + self.height - self.padding - indicator_size

            points = [
                (indicator_x, indicator_y),
                (indicator_x + indicator_size, indicator_y),
                (indicator_x + indicator_size // 2, indicator_y + indicator_size)
            ]

            if hasattr(renderer, 'draw_polygon'):
                renderer.draw_polygon(points, theme.dialog_continue_indicator.color)
            else:
                renderer.draw_rect(indicator_x, indicator_y, indicator_size, indicator_size,
                                   theme.dialog_continue_indicator.color)

    def _render_wrapped_text(self, renderer: Renderer, x: int, y: int, width: int, height: int, theme) -> None:
        if not self.displayed_text:
            return

        words = self.displayed_text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = self.font.size(test_line)[0]

            if test_width <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                # Handle words longer than the width
                if self.font.size(word)[0] <= width:
                    current_line = [word]
                else:
                    # Break long word
                    chars = list(word)
                    sub_line = ""
                    for ch in chars:
                        if self.font.size(sub_line + ch)[0] <= width:
                            sub_line += ch
                        else:
                            if sub_line:
                                lines.append(sub_line)
                            sub_line = ch
                    if sub_line:
                        current_line = [sub_line]
                    else:
                        current_line = []
        if current_line:
            lines.append(' '.join(current_line))

        line_height = self.font.get_height()
        max_lines = height // line_height

        for i, line in enumerate(lines[:max_lines]):
            line_y = y + i * line_height
            renderer.draw_text(line, x, line_y, theme.dialog_text.color, self.font)