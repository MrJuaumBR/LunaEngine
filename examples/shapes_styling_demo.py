from lunaengine.core import LunaEngine, Scene
from lunaengine.backend import OpenGLRenderer
from lunaengine.ui import *
import random

class TestScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        but:Button = self.add_ui_element(Button(350, 100, 200, 100, 'Test', 32))
        self.add_ui_element(TextLabel(350, 250, 'Hello World', 32))
        self.style_using_gradient = True
        but.set_on_click(lambda: self.__setattr__('style_using_gradient', not self.style_using_gradient))
        # Random style for all shapes
        self.style = {
            'gradient': [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.uniform(0.5, 1.0)) 
                         for _ in range(random.randint(3, 5))],
            'border_color': (0, 255, 0),
            'border_width': 5
        }
        
        # Function to randomise the style from LiveInspector
        self.engine.add_function_to_live_inspector(
            'Random style', 
            lambda: self.__setattr__('style', {
                'gradient': [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.uniform(0.5, 1.0)) 
                             for _ in range(random.randint(3, 5))],
                'border_color': (0, 255, 0),
                'border_width': 5
            }),
            [], 'shapes_styling_demo'
        )
        
    def render(self, renderer: OpenGLRenderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        # ---- RECTANGLES (left column) ----
        renderer.draw_text('Rects', 100, 30, (255, 200, 200), FontManager.get_font(None, 24))
        
        renderer.draw_rect(100, 60, 200, 80, (255, 0, 0), fill=True,
                           border_color=(0, 255, 0), border_width=5)
        
        style_rect_gradient = {'gradient': [(255, 0, 0), (0, 255, 0), (0, 0, 255)], 
                               'border_color': (0, 255, 0), 'border_width': 5}
        style_rect_solid= {
            'border_color': (0, 0, 255), 'border_width': 5, 'color': (255, 255, 0)
        }
        renderer.draw_rect(100, 160, 200, 80, style=style_rect_gradient)
        
        renderer.draw_rect(100, 260, 200, 80, style=self.style)
        
        renderer.draw_rect(100, 360, 200, 80, (100, 100, 190), style={'shadow': ThemeManager.get_shadow('button_normal')})
        
        # ---- CIRCLE (right column, first row) ----
        renderer.draw_text('Circle', 620, 30, (255, 200, 200), FontManager.get_font(None, 24))
        renderer.draw_circle(700, 100, 50, style=self.style)
        
        # ---- POLYGON (right column, second row) ----
        renderer.draw_text('Polygon', 620, 170, (255, 200, 200), FontManager.get_font(None, 24))
        points = [(630, 220), (670, 180), (740, 200), (760, 250), (690, 270)]
        renderer.draw_polygon(points, color=(255, 255, 255) if not self.style_using_gradient else None, style= style_rect_gradient if self.style_using_gradient else style_rect_solid)
        
def main():
    engine = LunaEngine(width=1024, height=768, debug=True)
    engine.add_scene('test', TestScene)
    engine.set_scene('test')
    engine.run()

if __name__ == '__main__':
    main()