# buttons.py
import pygame
from typing import Optional, Callable, Tuple, Dict, Any, Union, Literal
from .base import *
from ..themes import ThemeManager, ThemeType, UITheme, ThemeStyle
from ...backend.opengl import OpenGLRenderer
from pathlib import Path

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
        'icon': {'name': 'icon', 'key': 'icon', 'type': Optional[Union[str, pygame.Surface, Path, 'Icon']], 'editable': True,
                 'description': 'Path to image file, Surface, or Icon object.'},
        'icon_position': {'name': 'icon position', 'key': 'icon_position', 'type': Optional[Literal['left', 'right']], 'editable': True,
                          'description': 'Position of the icon relative to the text.'},
    }

    def __init__(
        self,
        x: int|float,
        y: int|float,
        width: int|float,
        height: int|float,
        text: str = "",
        font_size: int|float = 20,
        font_name: Optional[str] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: ThemeType|None = None,
        element_id: Optional[str] = None,
        icon: Optional[Union[str, pygame.Surface, Path, 'Icon']] = None,
        icon_position: Optional[Literal['left', 'right']] = 'left',
        icon_padding: int|float = 10
    ) -> None:
        super().__init__(x, y, width, height, pivot, element_id)
        self.text = str(text)
        self.font_size = font_size
        self.font_name = font_name
        self.on_click_callback: Optional[Callable] = None
        self.on_click_args: Tuple = ()
        self.on_click_kwargs: Dict = {}
        self._font: Optional[pygame.font.Font] = None
        self._was_pressed: bool = False
        
        # Icon storage
        self.icon = icon                 # raw: Icon, Surface, str, Path, or callable
        self.icon_position = icon_position if icon_position is not None else 'left'
        self._icon_surface: Optional[pygame.Surface] = None
        self._icon_padding = icon_padding


        # Theme
        self.theme_type = theme or ThemeManager.get_current_theme()
        theme_obj = ThemeManager.get_theme(self.theme_type)
        self.background_color: Tuple[int, int, int] = theme_obj.button_normal.color
        self.text_color: Tuple[int, int, int] = theme_obj.button_text.color
        
        # Generate the initial icon surface
        self._refresh_icon_surface()
        
    @property
    def icon_padding(self):
        return self._icon_padding

    @icon_padding.setter
    def icon_padding(self, value):
        self._icon_padding = value
        self._refresh_icon_surface()
        
    def _refresh_icon_surface(self) -> None:
        """Create or update the cached icon surface based on current size and color."""
        if self.icon is None:
            self._icon_surface = None
            return

        from ...misc.icons import Icon, Icons

        # Resolve icon
        icon_obj = self.icon() if callable(self.icon) else self.icon
        raw_surf = None
        if isinstance(icon_obj, Icon):
            raw_surf = icon_obj.get_surface(color=self.text_color)
        elif isinstance(icon_obj, pygame.Surface):
            raw_surf = icon_obj
        else:
            self._icon_surface = None
            return

        # Compute safe margins
        margin = max(4, self.border_width + 2)  # keep inside border
        available_w = self.width - 2 * margin
        available_h = self.height - 2 * margin
        max_icon_size = min(available_w, available_h, self.font_size * 1.5)
        icon_size = max(8, int(max_icon_size))

        # If there's text, we may need to reduce icon size further if combined width exceeds button width
        if self.text:
            # We'll get text width later, but we can pre-check roughly
            dummy_surf = self.font.render(self.text, True, (255,255,255))
            text_w = dummy_surf.get_width()
            # Estimate total width with current icon_size and padding
            total_w = icon_size + self.icon_padding + text_w
            if total_w > self.width - 2*margin:
                # Shrink icon to fit
                new_icon_size = max(8, int((self.width - 2*margin - self.icon_padding - text_w) * 0.9))
                if new_icon_size < icon_size:
                    icon_size = max(8, new_icon_size)

        # Scale surface
        if raw_surf.get_width() != icon_size or raw_surf.get_height() != icon_size:
            self._icon_surface = pygame.transform.smoothscale(raw_surf, (icon_size, icon_size))
        else:
            self._icon_surface = raw_surf

    @property
    def can_focus(self) -> bool:
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
        """Override if needed (no icon change, but keep for consistency)."""
        self.background_color = color or ThemeManager.get_theme(self.theme_type).button_normal.color

    def set_text_color(self, color: Optional[Tuple[int, int, int]]) -> None:
        """Override to refresh icon colour."""
        self.text_color = color or ThemeManager.get_theme(self.theme_type).button_text.color
        self._refresh_icon_surface()   # icon may use text_color

    def set_icon(self, icon: Union[str, pygame.Surface, Path, 'Icon', Callable[[], 'Icon']]) -> None:
        """Change the icon and refresh."""
        self.icon = icon
        self._refresh_icon_surface()

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

    def _get_state_style(self) -> ThemeStyle:
        """Return the theme style for the current state."""
        theme = self._get_colors()
        if self.state == UIState.NORMAL:
            return theme.button_normal
        elif self.state == UIState.HOVERED:
            return theme.button_hover
        elif self.state == UIState.PRESSED:
            return theme.button_pressed
        else:
            return theme.button_disabled

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

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        theme = self._get_colors()
        state_style = self._get_state_style()

        # Build style dict with shadow from the current state
        style = {}
        if state_style.shadow and state_style.shadow.distance > 0:
            style['shadow'] = state_style.shadow

        # Border from theme
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
            corner_radius=self.corner_radius,
            style=style
        )

        # ------------------------------------------------------------
        # Icon + text layout (using cached surfaces)
        # ------------------------------------------------------------
        icon_surf = self._icon_surface
        icon_size = icon_surf.get_width() if icon_surf else 0

        # 2. Text dimensions (if any)
        text_width = text_height = 0
        if self.text:
            dummy_surf = self.font.render(self.text, True, (255, 255, 255))
            text_width, text_height = dummy_surf.get_size()

        # 3. Calculate positions
        padding = self.icon_padding
        has_icon = icon_surf is not None and self.icon_position is not None
        has_text = bool(self.text)

        if has_icon and has_text:
            total_width = icon_size + padding + text_width
            start_x = actual_x + (self.width - total_width) // 2
            if self.icon_position == 'left':
                icon_x, text_x = start_x, start_x + icon_size + padding
            else:  # 'right'
                text_x, icon_x = start_x, start_x + text_width + padding
        elif has_icon:
            icon_x = actual_x + (self.width - icon_size) // 2
            text_x = None
        elif has_text:
            text_x = actual_x + (self.width - text_width) // 2
            icon_x = None
        else:
            super().render(renderer)
            return

        # 4. Draw icon
        if has_icon and icon_surf is not None:
            icon_y = actual_y + (self.height - icon_size) // 2
            renderer.draw_surface(icon_surf, icon_x, icon_y)

        # 5. Draw text
        if has_text:
            text_color = self._get_text_color()
            if text_x is not None:
                text_y = actual_y + (self.height - text_height) // 2
                renderer.draw_text(
                    self.text, text_x, text_y, text_color, self.font,
                    pivot=(0.0, 0.0)
                )
            else:
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
    Supports Icon objects and theme shadows.
    """
    category: str = 'button'

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'image_path': {'name': 'image path', 'key': 'image_path', 'type': Union[str, pygame.Surface, Path, 'Icon'], 'editable': False,
                       'description': 'Path to image file, Surface, or Icon object.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        image_path: Union[str, pygame.Surface, Path, 'Icon'],
        width: Optional[int] = None,
        height: Optional[int] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: ThemeType|None = None,
        element_id: Optional[str] = None
    ) -> None:
        super().__init__(x, y, width or 0, height or 0, pivot, element_id)
        self.image_path = image_path
        self._image: Optional[pygame.Surface] = None
        self._load_image()

        if width is None and self._image:
            self.width = self._image.get_width()
        if height is None and self._image:
            self.height = self._image.get_height()

        self.on_click_callback: Optional[Callable] = None
        self.on_click_args: Tuple = ()
        self.on_click_kwargs: Dict = {}
        self._was_pressed: bool = False

        self.theme_type = theme or ThemeManager.get_current_theme()

    @property
    def can_focus(self) -> bool:
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
        """Load image from path, Surface, or Icon."""
        if self.image_path is None:
            self._image = pygame.Surface((self.width or 100, self.height or 100))
            self._image.fill((0, 0, 0))
            return
        from ...misc.icons import Icon
        if isinstance(self.image_path, pygame.Surface):
            self._image = self.image_path
        elif isinstance(self.image_path, Icon):
            # Use Icon's get_surface with a default color (white) or we can later allow custom color
            self._image = self.image_path.get_surface(color=(255, 255, 255))
        elif isinstance(self.image_path, str):
            self._image = pygame.image.load(self.image_path).convert_alpha()
        else:
            raise TypeError(f"image_path must be str, pygame.Surface, or Icon, got {type(self.image_path)}")

        if self.width and self.height:
            self._image = pygame.transform.scale(self._image, (self.width, self.height))

    def set_on_click(self, callback: Callable, *args, **kwargs) -> None:
        self.on_click_callback = callback
        self.on_click_args = args
        self.on_click_kwargs = kwargs

    def get_image(self) -> pygame.Surface:
        return self._image

    def set_image(self, image_path: Union[str, pygame.Surface, 'Icon']) -> None:
        """Update the image, accepting Icon objects."""
        self.image_path = image_path
        self._load_image()
        # Adjust size if needed
        if self.width and self.height:
            self._image = pygame.transform.scale(self._image, (self.width, self.height))

    def _get_state_style(self):
        """Return the theme style for the current state."""
        theme = ThemeManager.get_theme(self.theme_type)
        if self.state == UIState.NORMAL:
            return theme.button_normal
        elif self.state == UIState.HOVERED:
            return theme.button_hover
        elif self.state == UIState.PRESSED:
            return theme.button_pressed
        else:
            return theme.button_disabled

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

    def render(self, renderer: OpenGLRenderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()
        state_style = self._get_state_style()

        # Build style dict with shadow from the current state
        style = {}
        if state_style.shadow and state_style.shadow.distance > 0:
            style['shadow'] = state_style.shadow

        if style:
            renderer.draw_rect(
                actual_x, actual_y, self.width, self.height,
                color=None,
                fill=False,
                border_width=0,
                corner_radius=self.corner_radius,
                style=style
            )

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