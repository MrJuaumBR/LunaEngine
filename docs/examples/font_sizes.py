from lunaengine.ui import *
from lunaengine.core import LunaEngine, Scene

class test(Scene):
    def __init__(self, engine:LunaEngine):
        super().__init__(engine)
        
        rows = 7          # number of rows
        cols = 3          # number of columns
        total = rows * cols

        start_x = 25
        start_y = 50
        col_spacing = 350
        row_spacing = 80

        max_font = 70
        min_font = 10

        for col in range(cols):
            for row in range(rows):
                i = col * rows + row                # global index (0..total-1)
                x = start_x + col * col_spacing
                y = start_y + row * row_spacing
                f_size = max_font - (max_font - min_font) * (i / (total - 1))
                self.add_ui_element(TextLabel(x, y, f"Hello World {i}", int(f_size)))
            
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color("background"))
        
engine = LunaEngine("Font Sizes", 1024, 720, debug=True)
engine.add_scene("test", test)
engine.set_scene("test")
engine.run()