# elements

## Overview

*File: `lunaengine\ui\elements.py`*
*Lines: 1930*

## Classes

### ImageLabel

UI element for displaying images.

*Line: 369*

#### Methods

##### Method `_load_image`

Load and prepare the image.

*Line: 397*

##### Method `set_image`

Change the displayed image.

Args:
    image_path (str): Path to the new image file.

*Line: 405*

##### Method `__init__`

Initialize an image label element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    image_path (str): Path to the image file.
    width (Optional[int]): Width of the image (None for original size).
    height (Optional[int]): Height of the image (None for original size).
    root_point (Tuple[float, float]): Anchor point for positioning.

*Line: 372*

##### Method `render`

Render the image label.

*Line: 415*

---

### ScrollingFrame

Container element with scrollable content.

*Line: 1436*

#### Methods

##### Method `render`

Render the scrolling frame.

*Line: 1478*

##### Method `_draw_horizontal_scrollbar`

Draw horizontal scrollbar.

*Line: 1515*

##### Method `handle_scroll`

Handle scroll input.

Args:
    scroll_y (int): Vertical scroll amount.

*Line: 1465*

##### Method `__init__`

Initialize a scrolling frame.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Visible width.
    height (int): Visible height.
    content_width (int): Total content width.
    content_height (int): Total content height.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 1439*

##### Method `_draw_vertical_scrollbar`

Draw vertical scrollbar.

*Line: 1531*

---

### Select

Selection element with arrow buttons to cycle through options.

*Line: 1166*

#### Methods

##### Method `_update_with_mouse`

Update select element with mouse interaction.

*Line: 1246*

##### Method `previous_option`

Select the previous option.

*Line: 1219*

##### Method `next_option`

Select the next option.

*Line: 1212*

##### Method `set_on_selection_changed`

Set selection change callback.

Args:
    callback (Callable): Function called when selection changes.

*Line: 1237*

##### Method `__init__`

Initialize a select element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the element.
    height (int): Height of the element.
    options (List[str]): Available options.
    font_size (int): Font size.
    font_name (Optional[str]): Font to use.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 1169*

##### Method `font`

Get the font object.

*Line: 1205*

##### Method `set_selected_index`

Set selected option by index.

Args:
    index (int): Index of option to select.

*Line: 1226*

##### Method `render`

Render the select element.

*Line: 1281*

---

### UIDraggable

UI element that can be dragged around the screen.

*Line: 1006*

#### Methods

##### Method `_update_with_mouse`

Update draggable element with mouse interaction.

*Line: 1029*

##### Method `__init__`

Initialize a draggable UI element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the element.
    height (int): Height of the element.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 1009*

##### Method `render`

Render the draggable element.

*Line: 1056*

---

### TextBox

Interactive text input field - OPTIMIZED

*Line: 682*

#### Methods

##### Method `_update_with_mouse`

Update text box with mouse interaction - OPTIMIZED

*Line: 770*

##### Method `_update_text_surface`

Update text surface cache when text changes.

*Line: 726*

##### Method `set_text`

Set the text content.

Args:
    text (str): New text content.

*Line: 758*

##### Method `_get_background_color`

Get background color based on state.

*Line: 748*

##### Method `font`

Get the font object with lazy loading.

*Line: 720*

##### Method `_get_text_color`

Get appropriate text color based on state.

*Line: 740*

##### Method `__init__`

Initialize a text box element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the text box.
    height (int): Height of the text box.
    text (str): Initial text content (acts as placeholder).
    font_size (int): Size of the font.
    font_name (Optional[str]): Font to use.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 685*

##### Method `handle_key_input`

Handle keyboard input when focused - OPTIMIZED

Args:
    event: Pygame keyboard event.

*Line: 811*

##### Method `_get_cursor_position`

Calculate cursor position - OPTIMIZED

*Line: 868*

##### Method `render`

Render the text box - FIXED

*Line: 878*

---

### Button

Interactive button element that responds to clicks.

*Line: 430*

#### Methods

##### Method `_update_with_mouse`

Update button with mouse interaction.

*Line: 496*

##### Method `_get_text_color`

Get the text color from the current theme.

Returns:
    Tuple[int, int, int]: RGB color tuple for the text.

*Line: 540*

##### Method `_get_color_for_state`

Get the appropriate color for the current button state.

Returns:
    Tuple[int, int, int]: RGB color tuple for the current state.

*Line: 522*

##### Method `font`

Get the font object (lazy loading).

*Line: 462*

##### Method `set_theme`

Set the theme for this button.

Args:
    theme_type (ThemeType): The theme to apply.

*Line: 478*

##### Method `set_on_click`

Set the callback function for click events.

Args:
    callback (Callable): Function to call when button is clicked.

*Line: 469*

##### Method `__init__`

Initialize a button element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the button in pixels.
    height (int): Height of the button in pixels.
    text (str): Text to display on the button.
    font_size (int): Size of the font in pixels.
    font_name (Optional[str]): Path to font file or None for default font.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for button appearance.

*Line: 433*

##### Method `_get_colors`

Get colors from the current theme.

Returns:
    UITheme: The current theme object.

*Line: 487*

##### Method `render`

Render the button.

*Line: 549*

---

### FontManager

Manages fonts and ensures Pygame font system is initialized.

*Line: 101*

#### Methods

##### Method `initialize`

Initialize the font system.

This method should be called before using any font-related functionality.
It initializes Pygame's font module if not already initialized.

*Line: 108*

##### Method `get_font`

Get a font object for rendering text.

Args:
    font_name (Optional[str]): Path to font file or None for default system font.
    font_size (int): Size of the font in pixels.
    
Returns:
    pygame.font.Font: A font object ready for text rendering.

*Line: 120*

---

### TextLabel

UI element for displaying text labels.

*Line: 273*

#### Methods

##### Method `set_theme`

Set the theme for this text label.

Args:
    theme_type (ThemeType): The theme to apply.

*Line: 336*

##### Method `set_text`

Update the displayed text and recalculate element size.

Args:
    text (str): The new text to display.

*Line: 324*

##### Method `__init__`

Initialize a text label element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    text (str): The text to display.
    font_size (int): Size of the font in pixels.
    color (Optional[Tuple[int, int, int]]): Custom text color (overrides theme).
    font_name (Optional[str]): Path to font file or None for default font.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for text color.

*Line: 276*

##### Method `font`

Get the font object (lazy loading).

Returns:
    pygame.font.Font: The font object for this label.

*Line: 313*

##### Method `_get_text_color`

Get the current text color.

Returns:
    Tuple[int, int, int]: RGB color tuple for the text.

*Line: 345*

##### Method `update_theme`

Update theme for text label.

*Line: 308*

##### Method `render`

Render the text label.

*Line: 356*

---

### Switch

Toggle switch element (like checkbox but with sliding animation).

*Line: 1329*

#### Methods

##### Method `__init__`

Initialize a switch element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the switch.
    height (int): Height of the switch.
    checked (bool): Initial state.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 1332*

##### Method `set_checked`

Set the switch state.

Args:
    checked (bool): New state.

*Line: 1360*

##### Method `set_on_toggle`

Set toggle callback.

Args:
    callback (Callable): Function called when switch is toggled.

*Line: 1369*

##### Method `toggle`

Toggle the switch state.

*Line: 1354*

##### Method `_update_with_mouse`

Update switch with mouse interaction.

*Line: 1378*

##### Method `render`

Render the switch.

*Line: 1409*

---

### ProgressBar

Visual progress indicator for loading or health display.

*Line: 930*

#### Methods

##### Method `set_value`

Set the current progress value.

Args:
    value (float): New progress value.

*Line: 958*

##### Method `get_percentage`

Get progress as percentage.

Returns:
    float: Progress percentage (0-100).

*Line: 967*

##### Method `__init__`

Initialize a progress bar element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the progress bar.
    height (int): Height of the progress bar.
    min_val (float): Minimum value.
    max_val (float): Maximum value.
    value (float): Current value.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 933*

##### Method `render`

Render the progress bar.

*Line: 976*

---

### ImageButton

Interactive button that displays an image instead of text.

*Line: 573*

#### Methods

##### Method `__init__`

Initialize an image button element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    image_path (str): Path to the image file.
    width (Optional[int]): Width of the button.
    height (Optional[int]): Height of the button.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for button states.

*Line: 576*

##### Method `_get_overlay_color`

Get overlay color based on button state.

Returns:
    Optional[Tuple[int, int, int]]: Overlay color or None for no overlay.

*Line: 650*

##### Method `_load_image`

Load the button image.

*Line: 607*

##### Method `render`

Render the image button.

*Line: 663*

##### Method `set_on_click`

Set the callback function for click events.

Args:
    callback (Callable): Function to call when button is clicked.

*Line: 615*

##### Method `_update_with_mouse`

Update image button with mouse interaction.

*Line: 624*

---

### UIGradient

UI element with gradient background.

*Line: 1077*

#### Methods

##### Method `_interpolate_colors`

Interpolate between gradient colors.

Args:
    ratio (float): Interpolation ratio (0-1).
    
Returns:
    Tuple[int, int, int]: Interpolated color.

*Line: 1117*

##### Method `__init__`

Initialize a gradient UI element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the element.
    height (int): Height of the element.
    colors (List[Tuple[int, int, int]]): List of colors for the gradient.
    direction (str): Gradient direction ("horizontal" or "vertical").
    root_point (Tuple[float, float]): Anchor point for positioning.

*Line: 1080*

##### Method `_generate_gradient`

Generate the gradient surface.

*Line: 1102*

##### Method `set_colors`

Set new gradient colors.

Args:
    colors (List[Tuple[int, int, int]]): New gradient colors.

*Line: 1146*

##### Method `render`

Render the gradient element.

*Line: 1156*

---

### UIElement

Base class for all UI elements providing common functionality.

*Line: 142*

#### Methods

##### Method `update_theme`

Update the theme for this element and all its children.

Args:
    theme_type (ThemeType): The new theme to apply.

*Line: 210*

##### Method `__init__`

Initialize a UI element with position and dimensions.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the element in pixels.
    height (int): Height of the element in pixels.
    root_point (Tuple[float, float]): Anchor point for positioning where (0,0) is top-left 
                                    and (1,1) is bottom-right.

*Line: 145*

##### Method `on_click`

Called when element is clicked by the user.

*Line: 265*

##### Method `update`

Update element state.

Args:
    dt (float): Delta time in seconds since last update.

*Line: 201*

##### Method `add_child`

Add a child element to this UI element.

Args:
    child: The child UI element to add.

*Line: 191*

##### Method `render`

Render the element to the screen.

Args:
    renderer: The renderer object used for drawing.

*Line: 252*

##### Method `get_actual_position`

Calculate actual screen position based on root_point anchor.

Args:
    parent_width (int): Width of parent element if applicable.
    parent_height (int): Height of parent element if applicable.
    
Returns:
    Tuple[int, int]: The actual (x, y) screen coordinates.

*Line: 168*

##### Method `_update_with_mouse`

Update element with current mouse state for interaction.

Args:
    mouse_pos (Tuple[int, int]): Current mouse position (x, y).
    mouse_pressed (bool): Whether mouse button is currently pressed.
    dt (float): Delta time in seconds.

*Line: 222*

##### Method `on_hover`

Called when mouse hovers over the element.

*Line: 269*

---

### UIState

Enumeration of possible UI element states.

*Line: 94*

---

### Slider

Interactive slider for selecting numeric values

*Line: 1547*

#### Methods

##### Method `_update_with_mouse`

Update slider with mouse interaction

*Line: 1584*

##### Method `set_theme`

Set slider theme

*Line: 1576*

##### Method `__init__`

Initialize a slider element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the slider track in pixels.
    height (int): Height of the slider in pixels.
    min_val (float): Minimum value of the slider.
    max_val (float): Maximum value of the slider.
    value (float): Initial value of the slider.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for slider appearance.

*Line: 1549*

##### Method `_get_colors`

Get colors from current theme

*Line: 1580*

##### Method `render`

```
def render(self, renderer):
    """
    Renders the object using the given renderer.

    Parameters:
        renderer (Renderer): The renderer to use for rendering.

    Returns:
        None
    """
    if not self.visible:
        return
```

This docstring provides a brief description of what the `render` method does, as well as information about its parameters and return value. It is concise and easy to read, with each section separated by a blank line for clarity. The code preview shows the relevant part of the method body that implements the visibility check.

*Line: 1619*

---

### Dropdown

Dropdown menu for selecting from a list of options

*Line: 1651*

#### Methods

##### Method `_update_with_mouse`

Update dropdown with mouse interaction and scroll support

*Line: 1709*

##### Method `_get_visible_options`

Get the list of option indices that are currently visible

*Line: 1795*

##### Method `font`

Lazy font loading

*Line: 1694*

##### Method `add_option`

Add an option to the dropdown

*Line: 1908*

##### Method `handle_scroll`

Handle mouse wheel scrolling

*Line: 1787*

##### Method `_get_colors`

Get colors from current theme

*Line: 1705*

##### Method `set_theme`

Set dropdown theme

*Line: 1701*

##### Method `__init__`

Initialize a dropdown menu element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the dropdown in pixels.
    height (int): Height of the dropdown in pixels.
    options (List[str]): List of available options.
    font_size (int): Size of the font in pixels.
    font_name (Optional[str]): Path to font file or None for default font.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for dropdown appearance.
    max_visible_options (int): Maximum number of options to show before scrolling.

*Line: 1653*

##### Method `_get_scrollbar_rect`

Get the scrollbar rectangle

*Line: 1804*

##### Method `remove_option`

Remove an option from the dropdown

*Line: 1912*

##### Method `set_selected_index`

Set the selected option by index

*Line: 1920*

##### Method `set_on_selection_changed`

Set callback for when selection changes

*Line: 1928*

##### Method `render`

```
def render(self, renderer):
    """
    Renders the widget using the given renderer.

    Parameters:
        renderer (Renderer): The renderer to use for rendering the widget.

    Returns:
        None
    """
    if not self.visible:
        return
    if self.state == UIState.NORMAL:
        # Code preview
```

*Line: 1818*

---

## Functions

### Function `on_hover`

Called when mouse hovers over the element.

*Line: 269*

### Function `set_image`

Change the displayed image.

Args:
    image_path (str): Path to the new image file.

*Line: 405*

### Function `on_click`

Called when element is clicked by the user.

*Line: 265*

### Function `_load_image`

Load and prepare the image.

*Line: 397*

### Function `set_theme`

Set the theme for this text label.

Args:
    theme_type (ThemeType): The theme to apply.

*Line: 336*

### Function `render`

Render the text label.

*Line: 356*

### Function `__init__`

Initialize an image label element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    image_path (str): Path to the image file.
    width (Optional[int]): Width of the image (None for original size).
    height (Optional[int]): Height of the image (None for original size).
    root_point (Tuple[float, float]): Anchor point for positioning.

*Line: 372*

### Function `render`

Render the element to the screen.

Args:
    renderer: The renderer object used for drawing.

*Line: 252*

### Function `_update_with_mouse`

Update element with current mouse state for interaction.

Args:
    mouse_pos (Tuple[int, int]): Current mouse position (x, y).
    mouse_pressed (bool): Whether mouse button is currently pressed.
    dt (float): Delta time in seconds.

*Line: 222*

### Function `set_text`

Update the displayed text and recalculate element size.

Args:
    text (str): The new text to display.

*Line: 324*

### Function `update`

Update element state.

Args:
    dt (float): Delta time in seconds since last update.

*Line: 201*

### Function `_get_text_color`

Get the current text color.

Returns:
    Tuple[int, int, int]: RGB color tuple for the text.

*Line: 345*

### Function `__init__`

Initialize a UI element with position and dimensions.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the element in pixels.
    height (int): Height of the element in pixels.
    root_point (Tuple[float, float]): Anchor point for positioning where (0,0) is top-left 
                                    and (1,1) is bottom-right.

*Line: 145*

### Function `update_theme`

Update the theme for this element and all its children.

Args:
    theme_type (ThemeType): The new theme to apply.

*Line: 210*

### Function `font`

Get the font object (lazy loading).

Returns:
    pygame.font.Font: The font object for this label.

*Line: 313*

### Function `add_child`

Add a child element to this UI element.

Args:
    child: The child UI element to add.

*Line: 191*

### Function `update_theme`

Update theme for text label.

*Line: 308*

### Function `get_actual_position`

Calculate actual screen position based on root_point anchor.

Args:
    parent_width (int): Width of parent element if applicable.
    parent_height (int): Height of parent element if applicable.
    
Returns:
    Tuple[int, int]: The actual (x, y) screen coordinates.

*Line: 168*

### Function `get_font`

Get a font object for rendering text.

Args:
    font_name (Optional[str]): Path to font file or None for default system font.
    font_size (int): Size of the font in pixels.
    
Returns:
    pygame.font.Font: A font object ready for text rendering.

*Line: 120*

### Function `initialize`

Initialize the font system.

This method should be called before using any font-related functionality.
It initializes Pygame's font module if not already initialized.

*Line: 108*

### Function `__init__`

Initialize a text label element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    text (str): The text to display.
    font_size (int): Size of the font in pixels.
    color (Optional[Tuple[int, int, int]]): Custom text color (overrides theme).
    font_name (Optional[str]): Path to font file or None for default font.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for text color.

*Line: 276*

### Function `render`

Render the image label.

*Line: 415*

### Function `_update_with_mouse`

Update button with mouse interaction.

*Line: 496*

### Function `_get_color_for_state`

Get the appropriate color for the current button state.

Returns:
    Tuple[int, int, int]: RGB color tuple for the current state.

*Line: 522*

### Function `_get_text_color`

Get the text color from the current theme.

Returns:
    Tuple[int, int, int]: RGB color tuple for the text.

*Line: 540*

### Function `render`

Render the button.

*Line: 549*

### Function `__init__`

Initialize an image button element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    image_path (str): Path to the image file.
    width (Optional[int]): Width of the button.
    height (Optional[int]): Height of the button.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for button states.

*Line: 576*

### Function `_load_image`

Load the button image.

*Line: 607*

### Function `set_on_click`

Set the callback function for click events.

Args:
    callback (Callable): Function to call when button is clicked.

*Line: 615*

### Function `_update_with_mouse`

Update image button with mouse interaction.

*Line: 624*

### Function `_get_overlay_color`

Get overlay color based on button state.

Returns:
    Optional[Tuple[int, int, int]]: Overlay color or None for no overlay.

*Line: 650*

### Function `render`

Render the image button.

*Line: 663*

### Function `__init__`

Initialize a text box element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the text box.
    height (int): Height of the text box.
    text (str): Initial text content (acts as placeholder).
    font_size (int): Size of the font.
    font_name (Optional[str]): Font to use.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 685*

### Function `font`

Get the font object with lazy loading.

*Line: 720*

### Function `_update_text_surface`

Update text surface cache when text changes.

*Line: 726*

### Function `_get_text_color`

Get appropriate text color based on state.

*Line: 740*

### Function `_get_background_color`

Get background color based on state.

*Line: 748*

### Function `set_text`

Set the text content.

Args:
    text (str): New text content.

*Line: 758*

### Function `_update_with_mouse`

Update text box with mouse interaction - OPTIMIZED

*Line: 770*

### Function `handle_key_input`

Handle keyboard input when focused - OPTIMIZED

Args:
    event: Pygame keyboard event.

*Line: 811*

### Function `_get_cursor_position`

Calculate cursor position - OPTIMIZED

*Line: 868*

### Function `render`

Render the text box - FIXED

*Line: 878*

### Function `__init__`

Initialize a progress bar element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the progress bar.
    height (int): Height of the progress bar.
    min_val (float): Minimum value.
    max_val (float): Maximum value.
    value (float): Current value.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 933*

### Function `set_value`

Set the current progress value.

Args:
    value (float): New progress value.

*Line: 958*

### Function `get_percentage`

Get progress as percentage.

Returns:
    float: Progress percentage (0-100).

*Line: 967*

### Function `render`

Render the progress bar.

*Line: 976*

### Function `__init__`

Initialize a draggable UI element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the element.
    height (int): Height of the element.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 1009*

### Function `_update_with_mouse`

Update draggable element with mouse interaction.

*Line: 1029*

### Function `render`

Render the draggable element.

*Line: 1056*

### Function `__init__`

Initialize a gradient UI element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the element.
    height (int): Height of the element.
    colors (List[Tuple[int, int, int]]): List of colors for the gradient.
    direction (str): Gradient direction ("horizontal" or "vertical").
    root_point (Tuple[float, float]): Anchor point for positioning.

*Line: 1080*

### Function `_generate_gradient`

Generate the gradient surface.

*Line: 1102*

### Function `_interpolate_colors`

Interpolate between gradient colors.

Args:
    ratio (float): Interpolation ratio (0-1).
    
Returns:
    Tuple[int, int, int]: Interpolated color.

*Line: 1117*

### Function `set_colors`

Set new gradient colors.

Args:
    colors (List[Tuple[int, int, int]]): New gradient colors.

*Line: 1146*

### Function `render`

Render the gradient element.

*Line: 1156*

### Function `__init__`

Initialize a select element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the element.
    height (int): Height of the element.
    options (List[str]): Available options.
    font_size (int): Font size.
    font_name (Optional[str]): Font to use.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 1169*

### Function `font`

Get the font object.

*Line: 1205*

### Function `next_option`

Select the next option.

*Line: 1212*

### Function `previous_option`

Select the previous option.

*Line: 1219*

### Function `set_selected_index`

Set selected option by index.

Args:
    index (int): Index of option to select.

*Line: 1226*

### Function `set_on_selection_changed`

Set selection change callback.

Args:
    callback (Callable): Function called when selection changes.

*Line: 1237*

### Function `_update_with_mouse`

Update select element with mouse interaction.

*Line: 1246*

### Function `render`

Render the select element.

*Line: 1281*

### Function `__init__`

Initialize a switch element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the switch.
    height (int): Height of the switch.
    checked (bool): Initial state.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 1332*

### Function `toggle`

Toggle the switch state.

*Line: 1354*

### Function `set_checked`

Set the switch state.

Args:
    checked (bool): New state.

*Line: 1360*

### Function `set_on_toggle`

Set toggle callback.

Args:
    callback (Callable): Function called when switch is toggled.

*Line: 1369*

### Function `_update_with_mouse`

Update switch with mouse interaction.

*Line: 1378*

### Function `render`

Render the switch.

*Line: 1409*

### Function `__init__`

Initialize a scrolling frame.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Visible width.
    height (int): Visible height.
    content_width (int): Total content width.
    content_height (int): Total content height.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for appearance.

*Line: 1439*

### Function `handle_scroll`

Handle scroll input.

Args:
    scroll_y (int): Vertical scroll amount.

*Line: 1465*

### Function `render`

Render the scrolling frame.

*Line: 1478*

### Function `_draw_horizontal_scrollbar`

Draw horizontal scrollbar.

*Line: 1515*

### Function `_draw_vertical_scrollbar`

Draw vertical scrollbar.

*Line: 1531*

### Function `__init__`

Initialize a slider element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the slider track in pixels.
    height (int): Height of the slider in pixels.
    min_val (float): Minimum value of the slider.
    max_val (float): Maximum value of the slider.
    value (float): Initial value of the slider.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for slider appearance.

*Line: 1549*

### Function `set_theme`

Set slider theme

*Line: 1576*

### Function `_get_colors`

Get colors from current theme

*Line: 1580*

### Function `_update_with_mouse`

Update slider with mouse interaction

*Line: 1584*

### Function `__init__`

Initialize a button element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the button in pixels.
    height (int): Height of the button in pixels.
    text (str): Text to display on the button.
    font_size (int): Size of the font in pixels.
    font_name (Optional[str]): Path to font file or None for default font.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for button appearance.

*Line: 433*

### Function `__init__`

Initialize a dropdown menu element.

Args:
    x (int): X coordinate position.
    y (int): Y coordinate position.
    width (int): Width of the dropdown in pixels.
    height (int): Height of the dropdown in pixels.
    options (List[str]): List of available options.
    font_size (int): Size of the font in pixels.
    font_name (Optional[str]): Path to font file or None for default font.
    root_point (Tuple[float, float]): Anchor point for positioning.
    theme (ThemeType): Theme to use for dropdown appearance.
    max_visible_options (int): Maximum number of options to show before scrolling.

*Line: 1653*

### Function `font`

Lazy font loading

*Line: 1694*

### Function `set_theme`

Set dropdown theme

*Line: 1701*

### Function `_get_colors`

Get colors from current theme

*Line: 1705*

### Function `_update_with_mouse`

Update dropdown with mouse interaction and scroll support

*Line: 1709*

### Function `handle_scroll`

Handle mouse wheel scrolling

*Line: 1787*

### Function `_get_visible_options`

Get the list of option indices that are currently visible

*Line: 1795*

### Function `_get_scrollbar_rect`

Get the scrollbar rectangle

*Line: 1804*

### Function `font`

Get the font object (lazy loading).

*Line: 462*

### Function `add_option`

Add an option to the dropdown

*Line: 1908*

### Function `remove_option`

Remove an option from the dropdown

*Line: 1912*

### Function `set_selected_index`

Set the selected option by index

*Line: 1920*

### Function `set_on_selection_changed`

Set callback for when selection changes

*Line: 1928*

### Function `set_theme`

Set the theme for this button.

Args:
    theme_type (ThemeType): The theme to apply.

*Line: 478*

### Function `set_on_click`

Set the callback function for click events.

Args:
    callback (Callable): Function to call when button is clicked.

*Line: 469*

### Function `_get_colors`

Get colors from the current theme.

Returns:
    UITheme: The current theme object.

*Line: 487*

### Function `render`

```
def render(self, renderer):
    """
    Renders the widget using the given renderer.

    Parameters:
        renderer (Renderer): The renderer to use for rendering the widget.

    Returns:
        None
    """
    if not self.visible:
        return
```

*Line: 1619*

### Function `render`

```
def render(self, renderer):
    """
    Renders the widget using the provided renderer.

    Parameters:
        renderer (Renderer): The renderer to use for rendering the widget.

    Returns:
        None
    """
    if not self.visible:
        return
    if self.state == UIState.NORMAL:
        # Code preview
```

*Line: 1818*

