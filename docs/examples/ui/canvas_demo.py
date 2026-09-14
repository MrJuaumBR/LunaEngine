import math
import pygame
from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.backend import OpenGLRenderer
import pygame

class CanvasDemo(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)

        # Canvas with a background
        self.canvas = Canvas(
            50, 50, 400, 300,
            logical_width=600, logical_height=400,
            scale_mode='fit',
            background_color=(30, 30, 50),
            alpha=0.9
        )
        self.canvas.set_draw_callback(self.draw_canvas_content)
        self.add_ui_element(self.canvas)

        # Control button
        btn = Button(500, 50, 120, 30, "Toggle BG")
        btn.set_on_click(self.toggle_bg)
        self.add_ui_element(btn)

        self.angle = 0.0

    def draw_canvas_content(self, canvas: Canvas, renderer: OpenGLRenderer):
        w, h = canvas.logical_width, canvas.logical_height

        # Grid (background)
        for x in range(0, w, 40):
            renderer.draw_line(x, 0, x, h, (60, 60, 80), 1)
        for y in range(0, h, 40):
            renderer.draw_line(0, y, w, y, (60, 60, 80), 1)

        # Rect with gradient
        renderer.draw_rect(
            50, 50, 150, 100,
            style={
                'gradient': [(255, 0, 0), (0, 255, 0), (0, 0, 255)],
                'border_color': (255, 255, 255),
                'border_width': 2
            }
        )

        # Circle with border via style
        renderer.draw_circle(
            300, 150, 60, (100, 200, 255), fill=True,
            style={'border_color': (0, 0, 255), 'border_width': 3}
        )

        # Moving circle
        self.angle += 0.02
        cx = 300 + 120 * math.cos(self.angle)
        cy = 250 + 80 * math.sin(self.angle * 1.5)
        renderer.draw_circle(cx, cy, 25, (255, 100, 100), fill=True)

        # Text
        font = FontManager.get_font(None, 20)
        renderer.draw_text("Hello Canvas!", 50, 200, (255, 255, 200), font)

    def toggle_bg(self):
        if self.canvas.background_color:
            self.canvas.background_color = None
            self.canvas._surface = pygame.Surface(
                (self.canvas.logical_width, self.canvas.logical_height),
                pygame.SRCALPHA, 32
            )
        else:
            self.canvas.background_color = (30, 30, 50)
            self.canvas._surface = pygame.Surface(
                (self.canvas.logical_width, self.canvas.logical_height),
                0, 32
            )
            self.canvas._surface.fill((30, 30, 50))

def main():
    engine = LunaEngine("Canvas Fixed Demo", 700, 500, debug=True)
    engine.add_scene("demo", CanvasDemo)
    engine.set_scene("demo")
    engine.run()

if __name__ == "__main__":
    main()