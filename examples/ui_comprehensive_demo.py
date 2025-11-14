"""
ui_comprehensive_demo.py - Comprehensive UI Elements Demo for LunaEngine

ENGINE PATH:
lunaengine -> examples -> ui_comprehensive_demo.py

DESCRIPTION:
This demo showcases all available UI elements in the LunaEngine system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.ui import *
from lunaengine.core import LunaEngine, Scene
import pygame

class ComprehensiveUIDemo(Scene):
    """Comprehensive UI Demo Scene"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.demo_state = {
            'button_clicks': 0,
            'slider_value': 50,
            'dropdown_selection': 'Option 1',
            'text_input': 'Type here...',
            'progress_value': 0,
            'switch_state': False,
            'select_index': 0,
        }
        self.setup_ui()
        
    def on_enter(self, previous_scene: str = None):
        """
        Called when the scene becomes active.
        
        Args:
            previous_scene (str): Name of the previous scene
        """
        print("=== LunaEngine UI Demo ===")
        print("Explore all UI elements!")
        print("Controls:")
        print("- Click buttons to interact")
        print("- Use dropdowns and selects to choose options")
        print("- Drag the draggable element")
        print("- Type in the text box")
        print("- Change themes with the theme dropdown")
        
    def on_exit(self, next_scene: str = None):
        """
        Called when the scene is being replaced.
        
        Args:
            next_scene (str): Name of the next scene
        """
        print("Exiting UI Demo scene")
        
    def setup_ui(self):
        """Setup all UI elements"""
        
        # Title Section
        title = TextLabel(512, 30, "LunaEngine - UI Demo", 36, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        # Section 1: Interactive Elements
        section1_title = TextLabel(50, 120, "Interactive Elements", 20, (255, 255, 0))
        self.add_ui_element(section1_title)
        
        # Button with counter
        button1 = Button(50, 160, 150, 40, "Click Me")
        button1.set_on_click(lambda: self.update_state('button_clicks', self.demo_state['button_clicks'] + 1))
        self.add_ui_element(button1)
        
        self.button_counter = TextLabel(220, 170, "Clicks: 0", 16)
        self.add_ui_element(self.button_counter)
        
        # Slider
        slider = Slider(50, 220, 200, 30, 0, 100, 50)
        slider.on_value_changed = lambda v: self.update_state('slider_value', v)
        self.add_ui_element(slider)
        
        self.slider_display = TextLabel(260, 225, "Value: 50.0", 14)
        self.add_ui_element(self.slider_display)
        
        # Section 2: Selection Elements
        section2_title = TextLabel(50, 280, "Selection Elements", 20, (255, 255, 0))
        self.add_ui_element(section2_title)
        
        # Dropdown
        dropdown = Dropdown(50, 320, 200, 30, ["Option 1", "Option 2", "Option 3"])
        dropdown.set_on_selection_changed(lambda i, v: self.update_state('dropdown_selection', v))
        self.add_ui_element(dropdown)
        
        # Theme Dropdown
        theme_dropdown = Dropdown(50, 420, 150, 30, ThemeManager.get_theme_names(), font_size=19)
        theme_dropdown.set_on_selection_changed(lambda i, v: self.engine.set_global_theme(v))
        self.add_ui_element(theme_dropdown)
        
        self.dropdown_display = TextLabel(260, 325, "Selected: Option 1", 14)
        self.add_ui_element(self.dropdown_display)
        
        # Switch
        switch = Switch(50, 370, 60, 30)
        switch.set_on_toggle(lambda s: self.update_state('switch_state', s))
        self.add_ui_element(switch)
        
        self.switch_display = TextLabel(120, 375, "Switch: OFF", 14)
        self.add_ui_element(self.switch_display)
        
        # Section 3: Visual Elements
        section3_title = TextLabel(550, 120, "Visual Elements", 20, (255, 255, 0))
        self.add_ui_element(section3_title)
        
        # Progress Bar
        self.progress_bar = ProgressBar(550, 160, 200, 20, 0, 100, 0)
        self.add_ui_element(self.progress_bar)
        
        progress_btn = Button(760, 160, 100, 20, "Add 10%")
        progress_btn.set_on_click(lambda: self.add_progress(10))
        self.add_ui_element(progress_btn)
        
        self.progress_display = TextLabel(550, 185, "Progress: 0%", 14)
        self.add_ui_element(self.progress_display)
        
        # Draggable Element
        draggable = UIDraggable(550, 220, 100, 50)
        self.add_ui_element(draggable)
        
        # Gradient
        gradient = UIGradient(550, 290, 200, 50, [(255, 0, 0), (200, 100, 0), (0, 255, 0), (0, 200, 100), (0, 0, 255)])
        self.add_ui_element(gradient)
        
        # Section 4: Advanced Elements
        section4_title = TextLabel(550, 360, "Advanced Elements", 20, (255, 255, 0))
        self.add_ui_element(section4_title)
        
        # Text Box
        textbox = TextBox(550, 400, 200, 30, "Type here...")
        self.add_ui_element(textbox)
        
        # Select
        select = Select(550, 450, 200, 30, ["Choice A", "Choice B", "Choice C"])
        select.set_on_selection_changed(lambda i, v: self.update_state('select_index', i))
        self.add_ui_element(select)
        
        self.select_display = TextLabel(760, 455, "Choice: 1", 14)
        self.add_ui_element(self.select_display)
        
        # Scrolling Frame
        scroll_frame = ScrollingFrame(550, 500, 300, 150, 280, 300)
        self.add_ui_element(scroll_frame)
        
        # Add items to scroll frame
        for i in range(8):
            item_label = TextLabel(10, i * 25, f"Item {i + 1}", 14)
            scroll_frame.add_child(item_label)
        
        # FPS Display
        self.fps_display = TextLabel(900, 20, "FPS: --", 16, (100, 255, 100))
        self.add_ui_element(self.fps_display)
    
    def update_state(self, key, value):
        """Update demo state with minimal printing"""
        self.demo_state[key] = value
        # Only print for significant changes
        if key in ['dropdown_selection', 'switch_state']:
            print(f"{key}: {value}")
    
    def add_progress(self, amount):
        """Add progress to the progress bar"""
        self.demo_state['progress_value'] = min(100, self.demo_state['progress_value'] + amount)
        self.progress_bar.set_value(self.demo_state['progress_value'])
    
    def update_ui_displays(self):
        """Update all UI displays"""
        self.button_counter.set_text(f"Clicks: {self.demo_state['button_clicks']}")
        self.slider_display.set_text(f"Value: {self.demo_state['slider_value']:.1f}")
        self.dropdown_display.set_text(f"Selected: {self.demo_state['dropdown_selection']}")
        self.switch_display.set_text(f"Switch: {'ON' if self.demo_state['switch_state'] else 'OFF'}")
        self.progress_display.set_text(f"Progress: {self.demo_state['progress_value']}%")
        self.select_display.set_text(f"Choice: {self.demo_state['select_index'] + 1}")
        
        # Update FPS
        self.fps_display.set_text(f"FPS: {self.engine.get_fps_stats()['current_fps']:.1f}")
    
    def update(self, dt):
        """Update scene logic"""
        self.update_ui_displays()
        
        # Auto-increment progress
        if self.demo_state['progress_value'] < 100:
            self.demo_state['progress_value'] += dt * 2  # 2% per second
            self.progress_bar.set_value(self.demo_state['progress_value'])
    
    def render(self, renderer):
        """Render scene background"""
        
        renderer.draw_rect(0, 0, 1024, 720, ThemeManager.get_color('background'))
        
        # Draw section backgrounds
        renderer.draw_rect(20, 100, 480, 400, ThemeManager.get_color('background2'))
        renderer.draw_rect(520, 100, 480, 600, ThemeManager.get_color('background2'))
        
        # Draw header
        renderer.draw_rect(0, 0, 1024, 90, ThemeManager.get_color('background2'))

def main():
    """Main function"""
    engine = LunaEngine("LunaEngine - UI Demo", 1024, 720, use_opengl=True)
    engine.fps = 60
    
    engine.add_scene("main", ComprehensiveUIDemo)
    engine.set_scene("main")
    
    print("=== LunaEngine UI Demo ===")
    print("Explore all UI elements!")
    
    engine.run()

if __name__ == "__main__":
    main()