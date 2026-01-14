import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.ui import *
from lunaengine.core import LunaEngine, Scene

class MainScene(Scene):
    def on_enter(self, previous_scene = None):
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine, *args, **kwargs):
        super().__init__(engine, *args, **kwargs)
        self.setup_ui()
        
    def setup_ui(self):
        self.tabs = Tabination(30, 30, 300, 500, 20, None)
        self.tabs.add_tab('Tab 1')
        self.tabs.add_tab('Tab 2')
        
        self.textbox = TextBox(5, 5, 200, 30, "", 24, None)
        self.tabs.add_to_tab('Tab 1', self.textbox)
        
        self.scrolling = ScrollingFrame(5, 5, 200, 300, 200, 600)
        self.tabs.add_to_tab('Tab 2', self.scrolling)
        
        for i in range(0, 10):
            self.scrolling.add_child(TextLabel(5, i * 20 + 10, f'Line {i}', 16, (255, 255, 255)))            
        
        self.dropdown = Dropdown(5, 60, 200, 20, ['Option 1', 'Option 2', 'Option 3'])
        self.tabs.add_to_tab('Tab 1', self.dropdown)
        
        self.dropdown2 = Dropdown(5, 90, 200, 20, ['Option 1', 'Option 2', 'Option 3'])
        self.tabs.add_to_tab('Tab 1', self.dropdown2)
        
        self.add_ui_element(self.tabs)
    
def main():
    engine = LunaEngine("New Events - Demo", 800, 600)
    engine.add_scene('main', MainScene)
    
    engine.set_scene('main')
    engine.run()
    
if __name__ == '__main__':
    main()