# 08 - UI Layouts

When creating complex menus (like inventories or settings pages), manually calculating and updating the `x` and `y` coordinates of every single button can be a nightmare. 

**Layout Managers** (`lunaengine.ui.layout`) solve this by automatically organizing UI elements according to specified rules.

## Basic Layout Example

LunaEngine provides several layouts. The most common are `VerticalLayout` and `HorizontalLayout`.

```python
from lunaengine.ui.layout import VerticalLayout
from lunaengine.ui.elements import Button
from lunaengine.core import Scene

class MenuScene(Scene):
    def __init__(self, engine):
        super().__init__(engine)
        
        # 1. Create the Layout (start drawing at x=100, y=100 with 15px spacing)
        self.menu_layout = VerticalLayout(x=100, y=100, spacing=15)
        
        # 2. Create your buttons
        self.btn1 = Button(width=200, height=50, text="New Game")
        self.btn2 = Button(width=200, height=50, text="Load Game")
        self.btn3 = Button(width=200, height=50, text="Settings")
        
        # 3. Add them to the layout
        self.menu_layout.add_element(self.btn1)
        self.menu_layout.add_element(self.btn2)
        self.menu_layout.add_element(self.btn3)
        
        # 4. Remember to still add them to the scene so they render!
        self.add_ui_element(self.btn1)
        self.add_ui_element(self.btn2)
        self.add_ui_element(self.btn3)
```

By using the `VerticalLayout`, `btn2` is automatically placed below `btn1`, and `btn3` below `btn2`. If you add or remove elements later, the layout automatically recalculates their positions!

## Available Layouts

1. **VerticalLayout**: Arranges elements from top to bottom.
2. **HorizontalLayout**: Arranges elements from left to right.
3. **GridLayout**: Arranges elements in a grid pattern. Useful for inventories.
   - `GridLayout(x=0, y=0, cols=4, cell_width=50, cell_height=50)`
4. **JustifiedLayout**: Distributes elements so they evenly fill available space.

Layouts are essential for creating scalable, maintainable interfaces.