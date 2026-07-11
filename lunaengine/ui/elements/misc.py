# misc.py
import pygame
import os
from typing import Optional, List, Callable, Tuple, Dict, Any
from .base import UIElement
from .textinputs import TextBox
from .buttons import Button
from .labels import ImageLabel
from ..themes import ThemeManager, ThemeType
from ...core.renderer import Renderer
from ...backend.types import InputState

class FileFinder(UIElement):
    """
    File selection element with text field and browse button.
    Displays selected file path and allows browsing filesystem via dialog.
    Supports file filtering and custom icons.
    """

    _properties: Dict[str, Dict[str, Any]] = {
        **UIElement._properties,
        'file_path': {'name': 'file path', 'key': 'file_path', 'type': str, 'editable': True,
                      'description': 'Currently selected file path.'},
        'file_filter': {'name': 'file filter', 'key': 'file_filter', 'type': List[str], 'editable': False,
                        'description': 'List of extensions to filter (e.g., [".png", ".jpg"]).'},
        'dialog_title': {'name': 'dialog title', 'key': 'dialog_title', 'type': str, 'editable': True,
                         'description': 'Title of the file dialog window.'},
        'button_text': {'name': 'button text', 'key': 'button_text', 'type': str, 'editable': True,
                        'description': 'Text on the browse button.'},
        'show_icon': {'name': 'show icon', 'key': 'show_icon', 'type': bool, 'editable': True,
                      'description': 'Whether to display a file icon.'},
    }

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        file_path: str = "",
        file_filter: Optional[List[str]] = None,
        dialog_title: str = "Select File",
        button_text: str = "Browse...",
        show_icon: bool = True,
        icon_path: Optional[str] = None,
        pivot: Tuple[float, float] = (0, 0),
        theme: Optional[ThemeType] = None,
        element_id: Optional[str] = None
    ) -> None:
        """
        Initialize a file finder widget.

        Args:
            x, y: Position (before anchor).
            width, height: Dimensions.
            file_path: Initial file path.
            file_filter: List of allowed extensions (e.g., [".txt", ".png"]).
            dialog_title: Title of the file dialog.
            button_text: Text on the browse button.
            show_icon: Display a file icon.
            icon_path: Path to a custom icon image.
            pivot: Anchor point.
            theme: Theme to apply.
            element_id: Custom ID.
        """
        super().__init__(x, y, width, height, pivot, element_id)

        self.file_path = file_path
        self.file_filter = file_filter or []
        self.dialog_title = dialog_title
        self.button_text = button_text
        self.show_icon = show_icon
        self.icon_path = icon_path

        self.theme_type = theme or ThemeManager.get_current_theme()
        theme_obj = ThemeManager.get_theme(self.theme_type)

        self.background_color = theme_obj.background.color
        self.foreground_color = theme_obj.button_normal.color
        self.font_color = theme_obj.button_text.color
        self.border_color = theme_obj.border.color if theme_obj.border else (120, 120, 140)

        self._path_textbox: Optional[TextBox] = None
        self._browse_button: Optional[Button] = None
        self._icon_label: Optional[ImageLabel] = None

        self.on_file_selected: Optional[Callable[[str], None]] = None

        self._create_child_elements()

        self._tkinter_available = self._check_tkinter()
        if not self._tkinter_available:
            print("Warning: tkinter not available. FileFinder will use pygame's simple input.")

    def _get_init_args(self) -> Dict[str, Any]:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'file_path': self.file_path,
            'file_filter': self.file_filter,
            'dialog_title': self.dialog_title,
            'button_text': self.button_text,
            'show_icon': self.show_icon,
            'icon_path': self.icon_path,
            'pivot': self.pivot,
            'theme': self.theme_type,
            'element_id': self.element_id,
        }

    def _check_tkinter(self) -> bool:
        try:
            import tkinter as tk
            from tkinter import filedialog
            return True
        except ImportError:
            return False

    def _create_child_elements(self) -> None:
        icon_width = 0
        if self.show_icon:
            icon_width = self.height - 10

        button_width = 80
        textbox_width = self.width - icon_width - button_width - 10

        if self.show_icon:
            self._icon_label = ImageLabel(5, 5, self.icon_path or self._get_default_icon(),
                                          width=icon_width, height=self.height - 10,
                                          pivot=(0, 0))
            self.add_child(self._icon_label)

        textbox_x = icon_width + 5 if self.show_icon else 5
        self._path_textbox = TextBox(textbox_x, 5, textbox_width, self.height - 10,
                                     text=self.file_path, font_size=14,
                                     pivot=(0, 0))
        self._path_textbox.focused = False
        self.add_child(self._path_textbox)

        button_x = self.width - button_width - 5
        self._browse_button = Button(button_x, 5, button_width, self.height - 10,
                                     text=self.button_text, font_size=14,
                                     pivot=(0, 0))
        self._browse_button.set_on_click(self._open_file_dialog)
        self.add_child(self._browse_button)

    def _get_default_icon(self) -> pygame.Surface:
        icon_size = self.height - 10
        icon = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        icon.fill((0, 0, 0, 0))

        body_color = (100, 150, 255)
        pygame.draw.rect(icon, body_color, (0, 0, icon_size * 0.8, icon_size * 0.9))

        tab_color = (80, 130, 235)
        tab_points = [
            (icon_size * 0.8, 0),
            (icon_size, icon_size * 0.2),
            (icon_size * 0.8, icon_size * 0.2)
        ]
        pygame.draw.polygon(icon, tab_color, tab_points)

        line_color = (240, 240, 240)
        for i in range(3, 8):
            y_pos = icon_size * (i / 10)
            line_height = icon_size * 0.05
            pygame.draw.rect(icon, line_color,
                             (icon_size * 0.1, y_pos, icon_size * 0.6, line_height))
        return icon

    def set_file_path(self, path: str) -> None:
        """Set the current file path and update the text box."""
        self.file_path = path
        if self._path_textbox:
            self._path_textbox.set_text(path)
        self._update_icon()
        if self.on_file_selected:
            self.on_file_selected(path)

    def _update_icon(self) -> None:
        # Placeholder for future enhancement (e.g., change icon based on file type)
        pass

    def _open_file_dialog(self) -> None:
        if self._tkinter_available:
            self._open_tkinter_dialog()
        else:
            self._open_simple_dialog()

    def _open_tkinter_dialog(self) -> None:
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            filetypes = []
            if self.file_filter:
                extensions = {}
                for ext in self.file_filter:
                    if ext.startswith('.'):
                        ext_type = ext[1:].upper() + " files"
                        if ext_type not in extensions:
                            extensions[ext_type] = []
                        extensions[ext_type].append(f"*{ext}")

                for filetype, patterns in extensions.items():
                    filetypes.append((filetype, ";".join(patterns)))
            else:
                filetypes = [("All files", "*.*")]

            file_path = filedialog.askopenfilename(
                title=self.dialog_title,
                filetypes=filetypes,
                initialdir=self._get_initial_directory()
            )

            root.destroy()

            if file_path:
                self.set_file_path(file_path)

        except Exception as e:
            print(f"Error opening file dialog: {e}")
            self._open_simple_dialog()

    def _open_simple_dialog(self) -> None:
        print("Simple file dialog would open here")

    def _get_initial_directory(self) -> Optional[str]:
        if self.file_path:
            dir_path = os.path.dirname(self.file_path)
            if os.path.exists(dir_path):
                return dir_path
        return None

    def set_on_file_selected(self, callback: Callable[[str], None]) -> None:
        """Register a callback for when a file is selected."""
        self.on_file_selected = callback

    def get_file_path(self) -> str:
        """Return the current file path."""
        return self.file_path

    def update(self, dt: float, inputState: InputState) -> None:
        super().update(dt, inputState)
        if self._path_textbox and self._path_textbox.get_text() != self.file_path:
            self.file_path = self._path_textbox.get_text()
            if self.on_file_selected:
                self.on_file_selected(self.file_path)

    def render(self, renderer: Renderer) -> None:
        if not self.visible:
            return

        actual_x, actual_y = self.get_actual_position()

        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           self.border_color, fill=False, border_width=self.border_width,
                           corner_radius=self.corner_radius)

        renderer.draw_rect(actual_x, actual_y, self.width, self.height,
                           self.background_color, border_width=self.border_width,
                           corner_radius=self.corner_radius)

        super().render(renderer)