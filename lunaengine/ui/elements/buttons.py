# buttons.py
import pygame
from typing import Optional, Callable, Tuple, Dict, Any, Union
from .base import *
from ..themes import ThemeManager, ThemeType, UITheme
from ...core.renderer import Renderer

class Button(UIElement):
    """
    A clickable button with text and theming support.
    """
    category: str = 'button'
    
    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'text': {'name': 'text', 'key': 'text', 'type': str, 'editable': True,
                 'description': 'Text displayed on the button.'},
        'font_size': {'name': 'font size', 'key': 'font_size', 'type': int, 'editable': True,
                      'description': 'Size of the text in pixels.'},
        'font_name': {'name': 'font name', 'key': 'font_name', 'type': Optional[str], 'editable': True,
                      'description': 'Path to a custom font file.'},
        'background_color': {'name': 'background color', 'key': 'background_color', 'type': Tuple[int, int, int], 'editable': True,
                             'description': 'Custom RGB background color (overrides theme).'},
        'text_color': {'name': 'text color', 'key': 'text_color', 'type': Tuple[int, int, int], 'editable': True,
                       'description': 'Custom RGB text color (overrides theme).'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str = "",
        font_size: int = 20,
        font_name: Optional[str] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: ThemeType = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)
        self.text = text
        self.font_size = font_size
        self.font_name = font_name
        self.on_click_callback: Optional[Callable] = None
        self.on_click_args: Tuple = ()
        self.on_click_kwargs: Dict = {}
        self._font: Optional[pygame.font.Font] = None
        self._was_pressed: bool = False

        self.theme_type = theme or ThemeManager.get_current_theme()
        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color: Tuple[int, int, int] = theme_obj.button_normal.color
        self.text_color: Tuple[int, int, int] = theme_obj.button_text.color

    # ---- NEW: can_focus override ----
    @property
    def can_focus(self) -> bool:
        """Buttons are focusable for controller navigation."""
        return True

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'text': self.text,
            'font_size': self.font_size,
            'font_name': self.font_name,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def set_background_color(self, color: Optional[Tuple[int, int, int]]) -> None:
        self.background_color = color or ThemeManager.get_theme(self.theme_type).button_normal.color

    def set_text_color(self, color: Optional[Tuple[int, int, int]]) -> None:
        self.text_color = color or ThemeManager.get_theme(self.theme_type).button_text.color

    def set_text(self, text: str) -> None:
        self.text = text

    def get_text(self) -> str:
        return self.text

    def update_theme(self, theme_type: ThemeType) -> None:
        super().update_theme(theme_type)
        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color = theme_obj.button_normal.color
        self.text_color = theme_obj.button_text.color

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            FontManager.initialize()
            self._font = FontManager.get_font(self.font_name, self.font_size)
        return self._font

    def set_on_click(self, callback: Callable, *args, **kwargs) -> None:
        self.on_click_callback = callback
        self.on_click_args = args
        self.on_click_kwargs = kwargs

    def set_theme(self, theme_type: ThemeType) -> None:
        self.theme_type = theme_type

    def _get_colors(self) -> UITheme:
        return ThemeManager.get_theme(self.theme_type)

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        if self.mouse_over(inputState):
            if inputState.mouse_buttons_pressed.left:
                self.state = UIState.PRESSED
                if not self._was_pressed and self.on_click_callback:
                    if self.on_click_args or self.on_click_kwargs:
                        try:
                            self.on_click_callback(*self.on_click_args, **self.on_click_kwargs)
                        except Exception:
                            self.on_click_callback()
                    else:
                        self.on_click_callback()
                self._was_pressed = True
            else:
                self.on_hover()
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False

        super().update(dt, inputState)

    def _get_color_for_state(self) -> Tuple[int, int, int]:
        theme = self._get_colors()
        if self.state == UIState.NORMAL:
            return self.background_color
        elif self.state == UIState.HOVERED:
            return theme.button_hover.color
        elif self.state == UIState.PRESSED:
            return theme.button_pressed.color
        else:
            return theme.button_disabled.color

    def _get_text_color(self) -> Tuple[int, int, int]:
        return self.text_color

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = self._get_colors()

        border_color = None
        border_width = 0
        if theme.button_border and theme.button_border.border_width > 0:
            border_color = theme.button_border.color
            border_width = theme.button_border.border_width

        color = self._get_color_for_state()
        renderer.draw_rect(
            actual_x, actual_y, self.width, self.height, color,
            fill=True,
            border_color=border_color,
            border_width=border_width,
            corner_radius=self.corner_radius
        )

        if self.text:
            text_color = self._get_text_color()
            center_x = actual_x + self.width // 2
            center_y = actual_y + self.height // 2
            renderer.draw_text(
                self.text, center_x, center_y, text_color, self.font,
                pivot=(0.5, 0.5)
            )

        super().render(renderer)


class ImageButton(UIElement):
    """
    A clickable button that displays an image instead of text.
    """
    category: str = 'button'

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'image_path': {'name': 'image path', 'key': 'image_path', 'type': Union[str, pygame.Surface], 'editable': False,
                       'description': 'Path to image file or Surface object.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        image_path: Union[str, pygame.Surface],
        width: Optional[int] = None,
        height: Optional[int] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: ThemeType = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width or 0, height or 0, pivot, element_id)
        self.image_path = image_path
        self._image: Optional[pygame.Surface] = None
        self._load_image()

        if width is None:
            self.width = self._image.get_width()
        if height is None:
            self.height = self._image.get_height()

        self.on_click_callback: Optional[Callable] = None
        self.on_click_args: Tuple = ()
        self.on_click_kwargs: Dict = {}
        self._was_pressed: bool = False

        self.theme_type = theme or ThemeManager.get_current_theme()

    # ---- NEW: can_focus override ----
    @property
    def can_focus(self) -> bool:
        """Image buttons are focusable."""
        return True

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'image_path': self.image_path,
            'width': self.width,
            'height': self.height,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def _load_image(self) -> None:
        if self.image_path is None:
            self._image = pygame.Surface((self.width or 100, self.height or 100))
            self._image.fill((0, 0, 0))
            return
        if isinstance(self.image_path, pygame.Surface):
            self._image = self.image_path
        elif isinstance(self.image_path, str):
            self._image = pygame.image.load(self.image_path).convert_alpha()
        else:
            raise TypeError(f"image_path must be str or pygame.Surface, got {type(self.image_path)}")
        if self.width and self.height:
            self._image = pygame.transform.scale(self._image, (self.width, self.height))

    def set_on_click(self, callback: Callable, *args, **kwargs) -> None:
        self.on_click_callback = callback
        self.on_click_args = args
        self.on_click_kwargs = kwargs

    def get_image(self) -> pygame.Surface:
        return self._image

    def set_image(self, image_path: Union[str, pygame.Surface]) -> None:
        if isinstance(image_path, str):
            self.image_path = image_path
            self._load_image()
        elif isinstance(image_path, pygame.Surface):
            self.image_path = None
            self._image = image_path
            if self.width and self.height:
                self._image = pygame.transform.scale(self._image, (self.width, self.height))

    def update(self, dt: float, inputState: InputState) -> None:
        if not self.visible or not self.enabled:
            self.state = UIState.DISABLED
            return

        if self.mouse_over(inputState):
            if inputState.mouse_buttons_pressed.left:
                self.state = UIState.PRESSED
                if not self._was_pressed and self.on_click_callback:
                    if self.on_click_args or self.on_click_kwargs:
                        try:
                            self.on_click_callback(*self.on_click_args, **self.on_click_kwargs)
                        except Exception:
                            self.on_click_callback()
                    else:
                        self.on_click_callback()
                self._was_pressed = True
            else:
                self.state = UIState.HOVERED
                self._was_pressed = False
        else:
            self.state = UIState.NORMAL
            self._was_pressed = False

        super().update(dt, inputState)

    def _get_overlay_color(self) -> Optional[Tuple[int, int, int, int]]:
        if self.state == UIState.HOVERED:
            return (255, 255, 255, 50)
        elif self.state == UIState.PRESSED:
            return (0, 0, 0, 50)
        return None

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()

        if self._image:
            if self._image.get_width() != self.width or self._image.get_height() != self.height:
                image = pygame.transform.scale(self._image, (self.width, self.height))
            else:
                image = self._image
            renderer.draw_surface(image, actual_x, actual_y)

        overlay_color = self._get_overlay_color()
        if overlay_color:
            renderer.draw_rect(
                actual_x, actual_y, self.width, self.height, overlay_color,
                fill=True, border_width=0, corner_radius=self.corner_radius
            )

        super().render(renderer)