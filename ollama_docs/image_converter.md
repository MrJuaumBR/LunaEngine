# image_converter

## Overview

*File: `lunaengine\utils\image_converter.py`*
*Lines: 276*

## Classes

### ImageConverter

Converts images to Python code for embedding in games
Uses Pygame for image loading - NO PILLOW REQUIRED

*Line: 8*

#### Methods

##### Method `_resize_surface`

Resize surface while maintaining aspect ratio

*Line: 48*

##### Method `_to_compressed`

Convert to compressed base64 string

*Line: 135*

##### Method `image_to_python_code`

Convert an image to Python code

*Line: 15*

##### Method `_to_pixel_array`

Convert to Python pixel array code - FIXED COLOR BUG

*Line: 67*

##### Method `_to_base64`

Convert to base64 encoded string

*Line: 102*

##### Method `create_image_from_code`

Create a pygame Surface from converted image data

*Line: 169*

##### Method `_from_pixel_array`

Create surface from pixel array - FIXED COLOR BUG

*Line: 190*

##### Method `_from_encoded_data`

Create surface from encoded data

*Line: 211*

---

### EmbeddedImage

Helper class for working with embedded images

*Line: 246*

#### Methods

##### Method `__init__`

Private method.

*Line: 251*

##### Method `draw`

Draw the image using a renderer

*Line: 270*

##### Method `surface`

Get the pygame Surface (lazy loading)

*Line: 256*

##### Method `width`

```
Brief description:
Returns the width of the rectangle.

Parameters: None

Returns:
int: The width of the rectangle.
```

*Line: 263*

##### Method `height`

Brief Description:
This method returns the height of the current object.

Parameters: None

Returns:
int: The height of the current object.

*Line: 267*

---

## Functions

### Function `_to_base64`

Convert to base64 encoded string

*Line: 102*

### Function `surface`

Get the pygame Surface (lazy loading)

*Line: 256*

### Function `_to_compressed`

Convert to compressed base64 string

*Line: 135*

### Function `draw`

Draw the image using a renderer

*Line: 270*

### Function `_from_encoded_data`

Create surface from encoded data

*Line: 211*

### Function `create_image_from_code`

Create a pygame Surface from converted image data

*Line: 169*

### Function `_to_pixel_array`

Convert to Python pixel array code - FIXED COLOR BUG

*Line: 67*

### Function `_from_pixel_array`

Create surface from pixel array - FIXED COLOR BUG

*Line: 190*

### Function `__init__`

Private method.

*Line: 251*

### Function `_resize_surface`

Resize surface while maintaining aspect ratio

*Line: 48*

### Function `image_to_python_code`

Convert an image to Python code

*Line: 15*

### Function `height`

Brief Description:
Returns the height of the current node in a binary search tree.

Parameters: None

Returns:
int: The height of the current node.

*Line: 267*

### Function `width`

Brief Description:
Returns the width of the rectangle as an integer.

Parameters: None

Returns:
int: The width of the rectangle.

*Line: 263*

