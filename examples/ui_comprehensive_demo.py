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
from lunaengine import LunaEngine
import pygame

class ComprehensiveUIDemo:
    def __init__(self, engine: LunaEngine):
        self.engine = engine
        self.ui_elements = []
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
    
    def setup_ui(self):
        """Setup all UI elements"""
        
        # Title Section
        title = TextLabel(512, 30, "LunaEngine - UI Demo", 36, root_point=(0.5, 0))
        self.ui_elements.append(title)
        
        # Section 1: Interactive Elements
        section1_title = TextLabel(50, 120, "Interactive Elements", 20, (255, 255, 0))
        self.ui_elements.append(section1_title)
        
        # Button with counter
        button1 = Button(50, 160, 150, 40, "Click Me")
        button1.set_on_click(lambda: self.update_state('button_clicks', self.demo_state['button_clicks'] + 1))
        self.ui_elements.append(button1)
        
        self.button_counter = TextLabel(220, 170, "Clicks: 0", 16)
        self.ui_elements.append(self.button_counter)
        
        # Slider
        slider = Slider(50, 220, 200, 30, 0, 100, 50)
        slider.on_value_changed = lambda v: self.update_state('slider_value', v)
        self.ui_elements.append(slider)
        
        self.slider_display = TextLabel(260, 225, "Value: 50.0", 14)
        self.ui_elements.append(self.slider_display)
        
        # Section 2: Selection Elements
        section2_title = TextLabel(50, 280, "Selection Elements", 20, (255, 255, 0))
        self.ui_elements.append(section2_title)
        
        # Dropdown
        dropdown = Dropdown(50, 320, 200, 30, ["Option 1", "Option 2", "Option 3"])
        dropdown.set_on_selection_changed(lambda i, v: self.update_state('dropdown_selection', v))
        self.ui_elements.append(dropdown)
        
        self.dropdown_display = TextLabel(260, 325, "Selected: Option 1", 14)
        self.ui_elements.append(self.dropdown_display)
        
        # Switch
        switch = Switch(50, 370, 60, 30)
        switch.set_on_toggle(lambda s: self.update_state('switch_state', s))
        self.ui_elements.append(switch)
        
        self.switch_display = TextLabel(120, 375, "Switch: OFF", 14)
        self.ui_elements.append(self.switch_display)
        
        # Section 3: Visual Elements
        section3_title = TextLabel(550, 120, "Visual Elements", 20, (255, 255, 0))
        self.ui_elements.append(section3_title)
        
        # Progress Bar
        self.progress_bar = ProgressBar(550, 160, 200, 20, 0, 100, 0)
        self.ui_elements.append(self.progress_bar)
        
        progress_btn = Button(760, 160, 100, 20, "Add 10%")
        progress_btn.set_on_click(lambda: self.add_progress(10))
        self.ui_elements.append(progress_btn)
        
        self.progress_display = TextLabel(550, 185, "Progress: 0%", 14)
        self.ui_elements.append(self.progress_display)
        
        # Draggable Element
        draggable = UIDraggable(550, 220, 100, 50)
        self.ui_elements.append(draggable)
        
        # Gradient
        gradient = UIGradient(550, 290, 200, 50, [(255, 0, 0), (0, 255, 0), (0, 0, 255)])
        self.ui_elements.append(gradient)
        
        # Section 4: Advanced Elements
        section4_title = TextLabel(550, 360, "Advanced Elements", 20, (255, 255, 0))
        self.ui_elements.append(section4_title)
        
        # Text Box
        textbox = TextBox(550, 400, 200, 30, "Type here...")
        self.ui_elements.append(textbox)
        
        # Select
        select = Select(550, 450, 200, 30, ["Choice A", "Choice B", "Choice C"])
        select.set_on_selection_changed(lambda i, v: self.update_state('select_index', i))
        self.ui_elements.append(select)
        
        self.select_display = TextLabel(760, 455, "Choice: 1", 14)
        self.ui_elements.append(self.select_display)
        
        # Scrolling Frame
        scroll_frame = ScrollingFrame(550, 500, 300, 150, 280, 300)
        self.ui_elements.append(scroll_frame)
        
        # Theme Label
        self.theme_label = TextLabel(50, 410, f"Current Theme: {str(ThemeManager.get_current_theme().name).capitalize()}", 16)
        self.ui_elements.append(self.theme_label)
        
        # Add items to scroll frame
        for i in range(8):
            item_label = TextLabel(10, i * 25, f"Item {i + 1}", 14)
            scroll_frame.add_child(item_label)
        
        # Theme Controls
        theme_dropdown = Dropdown(50, 450, 200, 30, self.engine.get_theme_names())
        theme_dropdown.set_on_selection_changed(lambda i, n: self.engine.set_global_theme(n))
        self.ui_elements.append(theme_dropdown)
        
        # FPS Display
        self.fps_display = TextLabel(900, 20, "FPS: --", 16, (100, 255, 100))
        self.ui_elements.append(self.fps_display)
    
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
        
        self.theme_label.set_text(f"Current Theme: {str(ThemeManager.get_current_theme().name).capitalize()}")
        
        # Update FPS
        fps_stats = self.engine.get_fps_stats()
        self.fps_display.set_text(f"FPS: {fps_stats['current']:.1f}")
    
    def update(self, dt):
        """Update scene logic"""
        self.update_ui_displays()
        
        # Auto-increment progress
        if self.demo_state['progress_value'] < 100:
            self.demo_state['progress_value'] += dt * 2  # 2% per second
            self.progress_bar.set_value(self.demo_state['progress_value'])
    
    def render(self, renderer):
        """Render scene background"""
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw section backgrounds
        renderer.draw_rect(20, 100, 480, 400, (40, 40, 60, 180), fill=True)
        renderer.draw_rect(520, 100, 480, 600, (40, 40, 60, 180), fill=True)
        
        # Draw header
        renderer.draw_rect(0, 0, 1024, 90, (30, 30, 50))

def main():
    """Main function"""
    engine = LunaEngine("LunaEngine - UI Demo", 1024, 720)
    engine.fps = 60
    
    demo_scene = ComprehensiveUIDemo(engine)
    engine.add_scene("main", demo_scene)
    engine.set_scene("main")
    
    print("=== LunaEngine UI Demo ===")
    print("Explore all UI elements!")
    
    engine.run()

if __name__ == "__main__":
    main()