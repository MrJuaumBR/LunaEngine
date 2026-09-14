import os, sys

#sys.path.append(os.path.join(os.path.dirname(__file__ + '/../')))

from lunaengine.core import LunaEngine, Scene
from lunaengine.backend import OpenGLRenderer
import random

class TestScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)

        self.objects = []
        self.lights = []

        self.m_light = self.shadow_system.add_light(
            self.engine.mouse_pos,
            'point',
            [(200, 180, 50, 1.0), (180, 200, 50, 1.0)],
            brightness=16,
            distance=250,
        )

        self.generate_objects()

    def generate_objects(self):
        for i in range(random.randint(5, 10)):
            x = random.randint(0, self.engine.width)
            y = random.randint(0, self.engine.height)
            obj_shape = random.choice(['circle', 'rect'])
            if obj_shape == 'circle':
                size = random.randint(10, 30)
            else:  # rect
                size = (random.randint(10, 30), random.randint(10, 30))

            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 1.0)

            # Add shadow caster with custom depth/spread
            sx, sy = x, y
            if obj_shape == 'rect':
                sx += size[0] // 2
                sy += size[1] // 2
            self.shadow_system.add_shadow(
                (sx, sy),
                obj_shape,
                [(0, 0, 0, 1.0), color],
                size,
                alpha_factor=0.6,
                shadow_depth=1.5,    # longer shadows
                shadow_spread=1.2    # wider spread
            )
            self.objects.append(((x, y), obj_shape, size, color))

    def update(self, dt: float):
        self.m_light.x, self.m_light.y = self.engine.mouse_pos

    def render(self, renderer: OpenGLRenderer):
        # Draw the actual objects on top
        for (x, y), obj_shape, size, color in self.objects:
            if obj_shape == 'circle':
                renderer.draw_circle(x, y, size, color)
            elif obj_shape == 'rect':
                renderer.draw_rect(x, y, size[0], size[1], color)


def main():
    engine = LunaEngine(width=1024, height=768, debug=True)
    engine.add_scene('test', TestScene)
    engine.set_scene('test')
    engine.run()

if __name__ == '__main__':
    main()