# elements

## Overview

*File: `lunaengine\ui\elements.py`*
*Lines: 421*

## Classes

### FontManager

Manages fonts and ensures Pygame font system is initialized

*Line: 12*

#### Methods

##### Method `initialize`

Initialize the font system

*Line: 18*

##### Method `get_font`

Get a font, initializing the system if needed

*Line: 25*

---

### UIState

```
UIState
=======

Brief Description
-----------------
A class representing the current state of the user interface.

Parameters
----------
None

Returns
-------
An instance of the UIState class.
```

*Line: 6*

---

### UIElement

UIElement
=========

A UIElement is a base class for creating user interface elements in Python. It provides methods for adding child elements, updating the element's state based on mouse input, rendering the element, and handling click and hover events.

Parameters:
------------

* `x`: The x-coordinate of the top-left corner of the element.
* `y`: The y-coordinate of the top-left corner of the element.
* `width`: The width of the element.
* `height`: The height of the element.

Returns:
--------

An instance of the UIElement class.

Methods:
-------

### add_child(child)
Add a child element to this element.

Parameters:
------------

* `child`: The child element to be added.

### update(dt)
Update the element's state based on mouse input.

Parameters:
------------

* `dt`: The time since the last frame in seconds.

### _update_with_mouse(mouse_pos, mouse_pressed, dt)
Update the element with current mouse state.

Parameters:
------------

* `mouse_pos`: The position of the mouse cursor.
* `mouse_pressed`: Whether the left mouse button is pressed or not.
* `dt`: The time since the last frame in seconds.

### render(renderer)
Render the element.

Parameters:
------------

* `renderer`: The renderer to use for rendering the element.

### on_click()
Called when the element is clicked.

### on_hover()
Called when the mouse hovers over the element.

*Line: 39*

#### Methods

##### Method `on_click`

Called when element is clicked

*Line: 91*

##### Method `_update_with_mouse`

Update element with current mouse state

*Line: 60*

##### Method `update`

Update element state - kept for compatibility

*Line: 56*

##### Method `add_child`

Add a child element

*Line: 51*

##### Method `render`

Render the element

*Line: 83*

##### Method `__init__`

Private method.

*Line: 40*

##### Method `on_hover`

Called when mouse hovers over element

*Line: 95*

---

### TextLabel

TextLabel
=========

A class for rendering text with a specified font and color.

Parameters
----------

* `x`: The x-coordinate of the top-left corner of the text.
* `y`: The y-coordinate of the top-left corner of the text.
* `text`: The text to be rendered.
* `font_size`: The size of the font in points.
* `color`: A tuple of three integers representing the RGB color values.
* `font_name`: The name of the font to use, or None for the default font.

Returns
-------

An instance of TextLabel.

Methods
-------

### __init__

Initializes a new TextLabel object with the specified parameters.

### font

Lazy font loading.

### set_text

Updates the text and recalculates the size of the label.

### render

Renders the text using the specified renderer.

*Line: 99*

#### Methods

##### Method `set_text`

Update the text and recalculate size

*Line: 122*

##### Method `font`

Lazy font loading

*Line: 116*

##### Method `__init__`

Private method.

*Line: 100*

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

This docstring provides a brief description of what the `render` method does, as well as information about its parameters and return value. It is concise and easy to read, with each section on a separate line for easier scanning.

*Line: 129*

---

### Button

Button Class
=============

The `Button` class is a graphical representation of a button that can be clicked on and responds to mouse clicks. It has the following methods:

### Initialization

* `__init__(self, x: int, y: int, width: int, height: int, text: str, font_size: int, font_name: Optional[str])` - Initialize the button with the specified position, size, and text. The `font_name` parameter is optional and defaults to None.

### Properties

* `font` - A lazy font loading method that loads the font only when it is needed.
* `on_click` - A property that sets the click callback function for the button.

### Methods

* `_update_with_mouse(self, mouse_pos: Tuple[int, int], mouse_pressed: bool, dt: float)` - Update the button with proper click handling when the mouse is pressed or released.
* `render(self, renderer)` - Render the button on the screen using the specified renderer.

### Returns

The `Button` class returns a `Button` object that can be used to interact with the button graphically and programmatically.

*Line: 139*

#### Methods

##### Method `__init__`

Private method.

*Line: 140*

##### Method `set_on_click`

Set the click callback

*Line: 164*

##### Method `font`

Lazy font loading

*Line: 157*

##### Method `_update_with_mouse`

Update button with proper click handling

*Line: 168*

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

*Line: 194*

---

### Slider

Slider
======

A widget for selecting a value within a range.

Parameters
----------

* `x`: The x-coordinate of the top-left corner of the slider.
* `y`: The y-coordinate of the top-left corner of the slider.
* `width`: The width of the slider.
* `height`: The height of the slider.
* `min_val`: The minimum value that can be selected by the slider.
* `max_val`: The maximum value that can be selected by the slider.
* `value`: The current value of the slider.

Returns
-------

None

Updates the slider with mouse interaction and renders it on the screen.

*Line: 211*

#### Methods

##### Method `__init__`

Private method.

*Line: 212*

##### Method `_update_with_mouse`

Update slider with mouse interaction

*Line: 221*

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
```

*Line: 254*

---

### Dropdown

Dropdown
========

A dropdown is a widget that displays a list of options and allows the user to select one. It can be used to present a menu or a list of choices to the user.

Parameters:
------------

* `x`: The x-coordinate of the top-left corner of the dropdown.
* `y`: The y-coordinate of the top-left corner of the dropdown.
* `width`: The width of the dropdown.
* `height`: The height of the dropdown.
* `options`: A list of strings representing the options to display in the dropdown.
* `font_size`: The size of the font used for the options.
* `font_name`: The name of the font used for the options (optional).

Returns:
---------

An instance of the Dropdown class.

Methods:
--------

### font()

Lazy font loading.

### _update_with_mouse(mouse_pos, mouse_pressed, dt)

Update dropdown with mouse interaction.

* `mouse_pos`: The position of the mouse cursor.
* `mouse_pressed`: Whether the left mouse button is pressed.
* `dt`: The time since the last update (in seconds).

### render(renderer)

Render the dropdown to the screen.

* `renderer`: A Renderer object used for drawing.

### add_option(option)

Add an option to the dropdown.

* `option`: The string representing the option to add.

### remove_option(option)

Remove an option from the dropdown.

* `option`: The string representing the option to remove.

### set_selected_index(index)

Set the selected option by index.

* `index`: The integer index of the option to select.

### set_on_selection_changed(callback)

Set callback for when selection changes.

* `callback`: A function that takes two arguments: the new index and the new value.

*Line: 269*

#### Methods

##### Method `_update_with_mouse`

Update dropdown with mouse interaction

*Line: 292*

##### Method `__init__`

Private method.

*Line: 270*

##### Method `remove_option`

Remove an option from the dropdown

*Line: 403*

##### Method `add_option`

Add an option to the dropdown

*Line: 399*

##### Method `font`

Lazy font loading

*Line: 285*

##### Method `set_selected_index`

Set the selected option by index

*Line: 411*

##### Method `set_on_selection_changed`

Set callback for when selection changes

*Line: 419*

##### Method `render`

```
def render(self, renderer):
    """
    Renders the UI element using the given renderer.

    Parameters:
        renderer (Renderer): The renderer to use for rendering the UI element.

    Returns:
        None
    """
    if not self.visible:
        main_color = (80, 80, 120) if self.state == UIState.NORMAL else (100, 100, 140)
```

*Line: 342*

---

## Functions

### Function `update`

Update element state - kept for compatibility

*Line: 56*

### Function `get_font`

Get a font, initializing the system if needed

*Line: 25*

### Function `_update_with_mouse`

Update dropdown with mouse interaction

*Line: 292*

### Function `set_on_click`

Set the click callback

*Line: 164*

### Function `font`

Lazy font loading

*Line: 285*

### Function `font`

Lazy font loading

*Line: 157*

### Function `font`

Lazy font loading

*Line: 116*

### Function `__init__`

Private method.

*Line: 270*

### Function `add_option`

Add an option to the dropdown

*Line: 399*

### Function `_update_with_mouse`

Update button with proper click handling

*Line: 168*

### Function `__init__`

Private method.

*Line: 140*

### Function `__init__`

Private method.

*Line: 100*

### Function `initialize`

Initialize the font system

*Line: 18*

### Function `render`

Render the element

*Line: 83*

### Function `_update_with_mouse`

Update slider with mouse interaction

*Line: 221*

### Function `on_hover`

Called when mouse hovers over element

*Line: 95*

### Function `set_text`

Update the text and recalculate size

*Line: 122*

### Function `add_child`

Add a child element

*Line: 51*

### Function `__init__`

Private method.

*Line: 212*

### Function `_update_with_mouse`

Update element with current mouse state

*Line: 60*

### Function `__init__`

Private method.

*Line: 40*

### Function `on_click`

Called when element is clicked

*Line: 91*

### Function `remove_option`

Remove an option from the dropdown

*Line: 403*

### Function `set_on_selection_changed`

Set callback for when selection changes

*Line: 419*

### Function `set_selected_index`

Set the selected option by index

*Line: 411*

### Function `render`

```
def render(self, renderer):
    """
    Renders the component using the given renderer.

    Parameters:
        renderer (Renderer): The renderer to use for rendering the component.

    Returns:
        None
    """
    if not self.visible:
        return
```

*Line: 129*

### Function `render`

```
def render(self, renderer):
    """
    Renders the object using the given renderer.

    :param renderer: The renderer to use for rendering the object.
    :type renderer: Renderer
    :return: The rendered output of the object.
    :rtype: str
    """
```

*Line: 254*

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

*Line: 194*

### Function `render`

```
def render(self, renderer):
    """
    Renders the UI element using the given renderer.

    Parameters:
        renderer (Renderer): The renderer to use for rendering the UI element.

    Returns:
        None
    """
    if not self.visible:
        main_color = (80, 80, 120) if self.state == UIState.NORMAL else (100, 100, 140)
```

*Line: 342*

