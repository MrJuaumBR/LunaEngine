from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
import pygame as pg

class Main(Scene):
    def __init__(self, engine, *args, **kwargs):
        super().__init__(engine, *args, **kwargs)
        self.icon_test = pg.Surface((64, 64), pg.SRCALPHA)
        self.icon_test.fill((255, 255, 255, 255))
        pg.draw.rect(self.icon_test, (255, 0, 0), (8, 8, 48, 48))
        pg.draw.circle(self.icon_test, (0, 255, 0), (32, 32), 16)
        
        
        self.header_frame = UiFrame(50, 50, 320, 240, header_enabled=True, header_title='Header - Test', header_icon=self.icon_test, draggable=True)
        self.add_ui_element(self.header_frame)
        
        self.tabs1 = Tabination(0, 0, 300, 70, 24)
        self.tabs1.add_tab('Tab 1')
        self.tabs1.add_tab('Tab 2')
        self.add_ui_element(self.tabs1)
        
        self.tabs2 = Tabination(305, 0, 300, 70, 24)
        self.tabs2.add_tab('Tab A')
        self.tabs2.add_tab('Tab B')
        self.add_ui_element(self.tabs2)
        
        self.tabs3 = Tabination(self.header_frame.width//2, self.header_frame.header_height+3, 280, self.header_frame.height-self.header_frame.header_height, 24, root_point=(0.5, 0))
        self.tabs3.add_tab('Tab X')
        self.tabs3.add_tab('Tab Y')
        self.header_frame.add_child(self.tabs3)
        
if __name__ == '__main__':
    engine = LunaEngine()
    
    engine.add_scene('main', Main)
    engine.set_scene('main')
    
    engine.run()