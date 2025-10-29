# layout

## Overview

*File: `lunaengine\ui\layout.py`*
*Lines: 213*

## Classes

### HorizontalLayout

Layout that arranges elements horizontally.

*Line: 111*

#### Methods

##### Method `__init__`

Initialize a horizontal layout.

Args:
    x (int): Starting X coordinate.
    y (int): Starting Y coordinate.
    spacing (int): Space between elements in pixels.

*Line: 114*

##### Method `_update_layout`

Arrange elements horizontally with spacing.

*Line: 126*

---

### GridLayout

Layout that arranges elements in a grid.

*Line: 134*

#### Methods

##### Method `__init__`

Initialize a grid layout.

Args:
    x (int): Starting X coordinate.
    y (int): Starting Y coordinate.
    cols (int): Number of columns in the grid.
    cell_width (int): Width of each cell.
    cell_height (int): Height of each cell.
    h_spacing (int): Horizontal spacing between cells.
    v_spacing (int): Vertical spacing between cells.

*Line: 137*

##### Method `_update_layout`

Arrange elements in a grid pattern.

*Line: 159*

---

### JustifiedLayout

Layout that justifies elements with equal spacing.

*Line: 170*

#### Methods

##### Method `__init__`

Initialize a justified layout.

Args:
    x (int): Starting X coordinate.
    y (int): Starting Y coordinate.
    justify_x (bool): Whether to justify horizontally.
    justify_y (bool): Whether to justify vertically.

*Line: 173*

##### Method `_update_layout`

Arrange elements with justified spacing.

*Line: 188*

---

### VerticalLayout

Layout that arranges elements vertically.

*Line: 88*

#### Methods

##### Method `__init__`

Initialize a vertical layout.

Args:
    x (int): Starting X coordinate.
    y (int): Starting Y coordinate.
    spacing (int): Space between elements in pixels.

*Line: 91*

##### Method `_update_layout`

Arrange elements vertically with spacing.

*Line: 103*

---

### UILayout

Base class for UI layout managers.

*Line: 47*

#### Methods

##### Method `remove_element`

Remove an element from the layout.

Args:
    element (UIElement): The UI element to remove from the layout.

*Line: 73*

##### Method `add_element`

Add an element to the layout.

Args:
    element (UIElement): The UI element to add to the layout.

*Line: 63*

##### Method `__init__`

Initialize a layout manager.

Args:
    x (int): Starting X coordinate for the layout.
    y (int): Starting Y coordinate for the layout.

*Line: 50*

##### Method `_update_layout`

Update element positions based on layout rules.

*Line: 84*

---

## Functions

### Function `__init__`

Initialize a justified layout.

Args:
    x (int): Starting X coordinate.
    y (int): Starting Y coordinate.
    justify_x (bool): Whether to justify horizontally.
    justify_y (bool): Whether to justify vertically.

*Line: 173*

### Function `add_element`

Add an element to the layout.

Args:
    element (UIElement): The UI element to add to the layout.

*Line: 63*

### Function `__init__`

Initialize a layout manager.

Args:
    x (int): Starting X coordinate for the layout.
    y (int): Starting Y coordinate for the layout.

*Line: 50*

### Function `__init__`

Initialize a vertical layout.

Args:
    x (int): Starting X coordinate.
    y (int): Starting Y coordinate.
    spacing (int): Space between elements in pixels.

*Line: 91*

### Function `_update_layout`

Arrange elements vertically with spacing.

*Line: 103*

### Function `_update_layout`

Arrange elements with justified spacing.

*Line: 188*

### Function `__init__`

Initialize a horizontal layout.

Args:
    x (int): Starting X coordinate.
    y (int): Starting Y coordinate.
    spacing (int): Space between elements in pixels.

*Line: 114*

### Function `__init__`

Initialize a grid layout.

Args:
    x (int): Starting X coordinate.
    y (int): Starting Y coordinate.
    cols (int): Number of columns in the grid.
    cell_width (int): Width of each cell.
    cell_height (int): Height of each cell.
    h_spacing (int): Horizontal spacing between cells.
    v_spacing (int): Vertical spacing between cells.

*Line: 137*

### Function `remove_element`

Remove an element from the layout.

Args:
    element (UIElement): The UI element to remove from the layout.

*Line: 73*

### Function `_update_layout`

Arrange elements horizontally with spacing.

*Line: 126*

### Function `_update_layout`

Arrange elements in a grid pattern.

*Line: 159*

### Function `_update_layout`

Update element positions based on layout rules.

*Line: 84*

