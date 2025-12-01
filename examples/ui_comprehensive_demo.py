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
            'dialog_active': False,
        }
        self.setup_ui()
        
    def on_enter(self, previous_scene: str = None):
        print("=== LunaEngine UI Demo ===")
        print("Explore all UI elements!")
        print("Controls:")
        print("- Click buttons to interact")
        print("- Use dropdowns and selects to choose options")
        print("- Drag the draggable element")
        print("- Type in the text box")
        print("- Change themes with the theme dropdown")
        print("- Hover over elements with tooltips")
        print("- Click to advance dialog boxes")
        
    def on_exit(self, next_scene: str = None):
        print("Exiting UI Demo scene")
        
    def setup_ui(self):
        title = TextLabel(512, 30, "LunaEngine - UI Demo", 36, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        section1_title = TextLabel(50, 120, "Interactive Elements", 20, (255, 255, 0))
        self.add_ui_element(section1_title)
        
        button1 = Button(50, 160, 150, 40, "Click Me")
        button1.set_on_click(lambda: self.update_state('button_clicks', self.demo_state['button_clicks'] + 1))
        button1.set_simple_tooltip("This button counts your clicks!")
        self.add_ui_element(button1)
        
        self.button_counter = TextLabel(220, 170, "Clicks: 0", 16)
        self.add_ui_element(self.button_counter)
        
        slider = Slider(50, 220, 200, 30, 0, 100, 50)
        slider.on_value_changed = lambda v: self.update_state('slider_value', v)
        slider.set_simple_tooltip("Drag to change the value")
        self.add_ui_element(slider)
        
        self.slider_display = TextLabel(260, 225, "Value: 50.0", 14)
        self.add_ui_element(self.slider_display)
        
        section2_title = TextLabel(50, 280, "Selection Elements", 20, (255, 255, 0))
        self.add_ui_element(section2_title)
        
        dropdown = Dropdown(50, 320, 200, 30, ["Option 1", "Option 2", "Option 3"])
        dropdown.set_on_selection_changed(lambda i, v: self.update_state('dropdown_selection', v))
        dropdown.set_simple_tooltip("Click to expand and select an option")
        self.add_ui_element(dropdown)
        
        theme_dropdown = Dropdown(50, 420, 150, 30, ThemeManager.get_theme_names(), font_size=19)
        theme_dropdown.set_on_selection_changed(lambda i, v: self.engine.set_global_theme(v))
        theme_dropdown.set_simple_tooltip("Change the global theme")
        self.add_ui_element(theme_dropdown)
        
        self.dropdown_display = TextLabel(260, 325, "Selected: Option 1", 14)
        self.add_ui_element(self.dropdown_display)
        
        switch = Switch(50, 370, 60, 30)
        switch.set_on_toggle(lambda s: self.update_state('switch_state', s))
        switch.set_simple_tooltip("Toggle switch on/off")
        self.add_ui_element(switch)
        
        self.switch_display = TextLabel(120, 375, "Switch: OFF", 14)
        self.add_ui_element(self.switch_display)
        
        section3_title = TextLabel(550, 120, "Visual Elements", 20, (255, 255, 0))
        self.add_ui_element(section3_title)
        
        self.progress_bar = ProgressBar(550, 160, 200, 20, 0, 100, 0)
        self.progress_bar.set_simple_tooltip("Shows progress from 0% to 100%")
        self.add_ui_element(self.progress_bar)
        
        progress_btn = Button(760, 160, 100, 20, "Add 10%")
        progress_btn.set_on_click(lambda: self.add_progress(10))
        self.add_ui_element(progress_btn)
        
        self.progress_display = TextLabel(550, 185, "Progress: 0%", 14)
        self.add_ui_element(self.progress_display)
        
        draggable = UIDraggable(550, 220, 100, 50)
        draggable.set_simple_tooltip("Drag me around the screen!")
        self.add_ui_element(draggable)
        
        gradient = UIGradient(550, 290, 200, 50, [(255, 0, 0), (200, 100, 0), (0, 255, 0), (0, 200, 100), (0, 0, 255)])
        gradient.set_simple_tooltip("Beautiful gradient with multiple colors")
        self.add_ui_element(gradient)
        
        section4_title = TextLabel(550, 360, "Advanced Elements", 20, (255, 255, 0))
        self.add_ui_element(section4_title)
        
        textbox = TextBox(550, 400, 200, 30, "Type here...")
        textbox.set_simple_tooltip("Click and type to enter text")
        self.add_ui_element(textbox)
        
        select = Select(550, 450, 200, 30, ["Choice A", "Choice B", "Choice C"])
        select.set_on_selection_changed(lambda i, v: self.update_state('select_index', i))
        select.set_simple_tooltip("Use arrows to cycle through options")
        self.add_ui_element(select)
        
        self.select_display = TextLabel(760, 455, "Choice: 1", 14)
        self.add_ui_element(self.select_display)
        
        scroll_frame = ScrollingFrame(550, 500, 300, 150, 280, 300)
        scroll_frame.set_simple_tooltip("Scrollable container with multiple items")
        self.add_ui_element(scroll_frame)
        
        for i in range(8):
            item_label = TextLabel(10, i * 25, f"Item {i + 1}", 14)
            scroll_frame.add_child(item_label)
        
        section5_title = TextLabel(50, 500, "New Elements", 20, (255, 255, 0))
        self.add_ui_element(section5_title)
        
        dialog_btn = Button(50, 540, 150, 40, "Show Dialog")
        dialog_btn.set_on_click(lambda: self.show_dialog())
        dialog_btn.set_simple_tooltip("Click to show an RPG-style dialog box")
        self.add_ui_element(dialog_btn)
        
        advanced_tooltip_btn = Button(220, 540, 180, 40, "Advanced Tooltip")
        advanced_tooltip_config = TooltipConfig(
            text="This is an advanced tooltip with custom styling! It has more padding, and a delay.",
            font_size=16,
            padding=12,
            offset_x=15,
            offset_y=15,
            show_delay=0.2,
            max_width=250,
        )
        advanced_tooltip = Tooltip(advanced_tooltip_config)
        advanced_tooltip_btn.set_tooltip(advanced_tooltip)
        self.add_ui_element(advanced_tooltip_btn)
        
        self.dialog_box = DialogBox(100, 300, 400, 150, style="modern")
        self.dialog_box.visible = False
        self.dialog_box.set_on_advance(lambda: self.hide_dialog())
        self.dialog_box.z_index = 100
        self.add_ui_element(self.dialog_box)
        
        self.fps_display = TextLabel(self.engine.width - 5, 20, "FPS: --", 16, (100, 255, 100), root_point=(1, 0))
        self.add_ui_element(self.fps_display)
    
    def update_state(self, key, value):
        self.demo_state[key] = value
        if key in ['dropdown_selection', 'switch_state']:
            print(f"{key}: {value}")
    
    def add_progress(self, amount):
        self.demo_state['progress_value'] = min(100, self.demo_state['progress_value'] + amount)
        self.progress_bar.set_value(self.demo_state['progress_value'])
    
    def show_dialog(self):
        self.dialog_box.visible = True
        self.dialog_box.set_text(
            "Welcome to LunaEngine! This is an RPG-style dialog box with typewriter animation. Click to continue...",
            "System",
            instant=False  # Change to True if you want instant display
        )
        self.demo_state['dialog_active'] = True
    
    def hide_dialog(self):
        self.dialog_box.visible = False
        self.demo_state['dialog_active'] = False
    
    def update_ui_displays(self):
        self.button_counter.set_text(f"Clicks: {self.demo_state['button_clicks']}")
        self.slider_display.set_text(f"Value: {self.demo_state['slider_value']:.1f}")
        self.dropdown_display.set_text(f"Selected: {self.demo_state['dropdown_selection']}")
        self.switch_display.set_text(f"Switch: {'ON' if self.demo_state['switch_state'] else 'OFF'}")
        self.progress_display.set_text(f"Progress: {self.demo_state['progress_value']}%")
        self.select_display.set_text(f"Choice: {self.demo_state['select_index'] + 1}")
        
        self.fps_display.set_text(f"FPS: {self.engine.get_fps_stats()['current_fps']:.1f}")
    
    def update(self, dt):
        self.update_ui_displays()
        
        if self.demo_state['progress_value'] < 100:
            self.demo_state['progress_value'] += dt * 2
            self.progress_bar.set_value(self.demo_state['progress_value'])
    
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        renderer.draw_rect(20, 100, 480, 500, ThemeManager.get_color('background2'))
        renderer.draw_rect(520, 100, 480, 600, ThemeManager.get_color('background2'))
        
        renderer.draw_rect(0, 0, self.engine.width, 90, ThemeManager.get_color('background2'))

def main():
    # Create engine
    engine = LunaEngine("LunaEngine - UI Demo", 1024, 768, use_opengl=True, fullscreen=True)
    
    # Configure the max FPS
    engine.fps = 60
    
    # Add and set the main scene
    engine.add_scene("main", ComprehensiveUIDemo)
    engine.set_scene("main")
    
    # Run the engine
    engine.run()

if __name__ == "__main__":
    main()