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
from lunaengine.ui.tween import Tween, EasingType, AnimationHandler
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
            # NEW STATES FOR NEW ELEMENTS
            'number_selector_value': 10,
            'checkbox_state': True,
        }
        self.animations = {}
        self.animation_handler = AnimationHandler(engine)
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
        print("- Use animation controls to pause/resume animations")
        
    def on_exit(self, next_scene: str = None):
        print("Exiting UI Demo scene")
        # Clean up animations
        self.animation_handler.cancel_all()
        
    def setup_ui(self):
        """Sets up all UI elements for the demo scene."""
        self.engine.set_global_theme(ThemeType.DEFAULT)
        
        # --- TITLE ---
        title = TextLabel(512, 30, "LunaEngine - UI Demo", 36, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        # --- SECTION 1: Interactive Elements ---
        section1_title = TextLabel(50, 100, "Interactive Elements", 20, (255, 255, 0))
        self.add_ui_element(section1_title)
        
        # Button Example
        button1 = Button(50, 130, 150, 40, "Click Me")
        button1.set_on_click(lambda: self.update_state('button_clicks', self.demo_state['button_clicks'] + 1))
        button1.set_simple_tooltip("This button counts your clicks!")
        self.add_ui_element(button1)
        
        self.button_counter = TextLabel(220, 140, "Clicks: 0", 16)
        self.add_ui_element(self.button_counter)
        
        # Slider Example
        slider = Slider(50, 175, 200, 30, 0, 100, 50)
        slider.on_value_changed = lambda v: self.update_state('slider_value', v)
        slider.set_simple_tooltip("Drag to change the value")
        self.add_ui_element(slider)
        
        self.slider_display = TextLabel(260, 180, "Value: 50.0", 14)
        self.add_ui_element(self.slider_display)
        
        # NEW: NumberSelector Example
        number_selector = NumberSelector(50, 215, 75, 25, 0, 99, self.demo_state['number_selector_value'], min_length=2)
        number_selector.on_value_changed = lambda v: self.update_state('number_selector_value', v)
        number_selector.set_simple_tooltip("Select a number from 00 to 99")
        self.add_ui_element(number_selector)

        self.number_selector_display = TextLabel(210, 220, "Number: 10", 14)
        self.add_ui_element(self.number_selector_display)
        
        # --- SECTION 2: Selection Elements (Shifted Down) ---
        section2_title = TextLabel(50, 260, "Selection Elements", 20, (255, 255, 0))
        self.add_ui_element(section2_title)
        
        # Dropdown Example
        dropdown = Dropdown(50, 290, 200, 30, ["Option 1", "Option 2", "Option 3"])
        dropdown.set_on_selection_changed(lambda i, v: self.update_state('dropdown_selection', v))
        dropdown.set_simple_tooltip("Click to expand and select an option")
        self.add_ui_element(dropdown)
        
        # Theme Dropdown Example
        theme_dropdown = Dropdown(50, 330, 150, 30, ThemeManager.get_theme_names(), font_size=19)
        theme_dropdown.set_on_selection_changed(lambda i, v: self.engine.set_global_theme(v))
        theme_dropdown.set_simple_tooltip("Change the global theme")
        self.add_ui_element(theme_dropdown)
        
        self.dropdown_display = TextLabel(260, 290, "Selected: Option 1", 14)
        self.add_ui_element(self.dropdown_display)
        
        # Switch Example
        switch = Switch(50, 370, 60, 30)
        switch.set_on_toggle(lambda s: self.update_state('switch_state', s))
        switch.set_simple_tooltip("Toggle switch on/off")
        self.add_ui_element(switch)
        
        self.switch_display = TextLabel(120, 380, "Switch: OFF", 14)
        self.add_ui_element(self.switch_display)
        
        checkbox = Checkbox(50, 410, 200, 25, self.demo_state['checkbox_state'], label="Enable Feature X")
        checkbox.set_on_toggle(lambda s: self.update_state('checkbox_state', s))
        checkbox.set_simple_tooltip("Toggle this feature on/off")
        self.add_ui_element(checkbox)
        
        self.checkbox_display = TextLabel(260, 415, "Feature X: ON", 14)
        self.add_ui_element(self.checkbox_display)

        # --- SECTION 3: Visual Elements ---
        section3_title = TextLabel(550, 100, "Visual Elements", 20, (255, 255, 0))
        self.add_ui_element(section3_title)
        
        self.progress_bar = ProgressBar(550, 120, 200, 20, 0, 100, 0)
        self.progress_bar.set_simple_tooltip("Shows progress from 0% to 100%")
        self.add_ui_element(self.progress_bar)
        
        progress_btn = Button(760, 120, 100, 20, "Add 10%")
        progress_btn.set_on_click(lambda: self.add_progress(10))
        self.add_ui_element(progress_btn)
        
        self.progress_display = TextLabel(550, 140, "Progress: 0%", 14)
        self.add_ui_element(self.progress_display)
        
        draggable = UIDraggable(550, 165, 100, 50)
        draggable.set_simple_tooltip("Drag me around the screen!")
        self.add_ui_element(draggable)
        
        gradient = UIGradient(550, 225, 200, 50, [(255, 0, 0), (200, 100, 0), (0, 255, 0), (0, 200, 100), (0, 0, 255)])
        gradient.set_simple_tooltip("Beautiful gradient with multiple colors")
        self.add_ui_element(gradient)
        
        # --- SECTION 4: Advanced Elements ---
        section4_title = TextLabel(550, 285, "Advanced Elements", 20, (255, 255, 0))
        self.add_ui_element(section4_title)
        
        textbox = TextBox(550, 320, 200, 30, "Type here...")
        textbox.set_simple_tooltip("Click and type to enter text")
        self.add_ui_element(textbox)
        
        select = Select(550, 355, 200, 30, ["Choice A", "Choice B", "Choice C"])
        select.set_on_selection_changed(lambda i, v: self.update_state('select_index', i))
        select.set_simple_tooltip("Use arrows to cycle through options")
        self.add_ui_element(select)
        
        self.select_display = TextLabel(760, 355, "Choice: 1", 14)
        self.add_ui_element(self.select_display)
        
        scroll_frame = ScrollingFrame(550, 400, 300, 150, 280, 300)
        scroll_frame.set_simple_tooltip("Scrollable container with multiple items")
        self.add_ui_element(scroll_frame)
        
        for i in range(8):
            item_label = TextLabel(10, i * 25, f"Item {i + 1}", 14)
            scroll_frame.add_child(item_label)
        
        # --- SECTION 5: Animation Examples (Shifted Down) ---
        section5_title = TextLabel(50, 450, "Animation Examples", 20, (255, 255, 0))
        self.add_ui_element(section5_title)
        
        # Animation controls
        animation_controls = TextLabel(50, 470, "Animation Controls:", 16, (200, 200, 255))
        self.add_ui_element(animation_controls)
        
        # Linear Animation Example
        linear_label = TextLabel(50, 490, "Linear Animation:", 14, (100, 255, 100))
        self.add_ui_element(linear_label)
        
        self.linear_box = UiFrame(50, 510, 15, 15)
        self.linear_box.set_background_color((100, 255, 100))
        self.add_ui_element(self.linear_box)
        
        # Bounce Animation Example
        bounce_label = TextLabel(50, 530, "Bounce Animation:", 14, (255, 200, 50))
        self.add_ui_element(bounce_label)
        
        self.bounce_box = UiFrame(50, 550, 15, 15)
        self.bounce_box.set_background_color((255, 200, 50))
        self.add_ui_element(self.bounce_box)
        
        # Back Animation Example
        back_label = TextLabel(50, 570, "Back Animation:", 14, (255, 100, 100))
        self.add_ui_element(back_label)
        
        self.back_box = UiFrame(50, 590, 15, 15)
        self.back_box.set_background_color((255, 100, 100))
        self.add_ui_element(self.back_box)
        
        # Animation path indicators
        self.linear_path = UiFrame(50, 515, 300, 5)
        self.linear_path.z_index = -1
        self.add_ui_element(self.linear_path)
        
        self.bounce_path = UiFrame(50, 555, 300, 5)
        self.bounce_path.z_index = -1
        self.add_ui_element(self.bounce_path)
        
        self.back_path = UiFrame(50, 595, 300, 5)
        self.back_path.z_index = -1
        self.add_ui_element(self.back_path)
        
        # Animation progress displays
        self.linear_progress = TextLabel(375, 515, "0%", 14, (100, 255, 100))
        self.add_ui_element(self.linear_progress)
        
        self.bounce_progress = TextLabel(375, 555, "0%", 14, (255, 200, 50))
        self.add_ui_element(self.bounce_progress)
        
        self.back_progress = TextLabel(375, 595, "0%", 14, (255, 100, 100))
        self.add_ui_element(self.back_progress)
        
        # Animation control buttons
        pause_btn = Button(50, 615, 80, 30, "Pause All")
        pause_btn.set_on_click(lambda: self.pause_animations())
        pause_btn.set_simple_tooltip("Pause all animations")
        self.add_ui_element(pause_btn)
        
        resume_btn = Button(140, 615, 80, 30, "Resume All")
        resume_btn.set_on_click(lambda: self.resume_animations())
        resume_btn.set_simple_tooltip("Resume all animations")
        self.add_ui_element(resume_btn)
        
        reset_btn = Button(230, 615, 80, 30, "Reset All")
        reset_btn.set_on_click(lambda: self.reset_animations())
        reset_btn.set_simple_tooltip("Reset all animations")
        self.add_ui_element(reset_btn)
        
        # Animation speed control
        speed_label = TextLabel(50, 655, "Speed:", 14, (200, 200, 255))
        self.add_ui_element(speed_label)
        
        self.speed_slider = Slider(100, 650, 100, 20, 0.5, 3.0, 1.0)
        self.speed_slider.on_value_changed = lambda v: self.update_animation_speed(v)
        self.speed_slider.set_simple_tooltip("Adjust animation speed (0.5x to 3.0x)")
        self.add_ui_element(self.speed_slider)
        
        self.speed_display = TextLabel(300, 655, "1.0x", 12)
        self.add_ui_element(self.speed_display)
        
        # Loop control buttons
        loop_btn = Button(50, 685, 80, 30, "3 Loops")
        loop_btn.set_on_click(lambda: self.set_animations_loops(3))
        loop_btn.set_simple_tooltip("Set all animations to loop 3 times")
        self.add_ui_element(loop_btn)

        infinite_loop_btn = Button(140, 685, 100, 30, "Infinite")
        infinite_loop_btn.set_on_click(lambda: self.set_animations_loops(-1))
        infinite_loop_btn.set_simple_tooltip("Set all animations to loop infinitely")
        self.add_ui_element(infinite_loop_btn)

        no_loop_btn = Button(250, 685, 80, 30, "No Loop")
        no_loop_btn.set_on_click(lambda: self.set_animations_loops(0))
        no_loop_btn.set_simple_tooltip("Disable looping for all animations")
        self.add_ui_element(no_loop_btn)
        
        # Loop count display
        self.loop_display = TextLabel(50, 725, "Loops: Infinite", 14, (200, 200, 255))
        self.add_ui_element(self.loop_display)
        
        # Dialog button
        dialog_btn = Button(725, 600, 150, 40, "Show Dialog")
        dialog_btn.set_on_click(lambda: self.show_dialog())
        dialog_btn.set_simple_tooltip("Click to show an RPG-style dialog box")
        self.add_ui_element(dialog_btn)
        
        advanced_tooltip_btn = Button(530, 600, 180, 40, "Advanced Tooltip")
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
        
        self.dialog_box = DialogBox(120, 300, 400, 150, style="modern")
        self.dialog_box.visible = False
        self.dialog_box.set_on_advance(lambda: self.hide_dialog())
        self.dialog_box.z_index = 100
        self.add_ui_element(self.dialog_box)
        
        self.fps_display = TextLabel(self.engine.width - 5, 20, "FPS: --", 16, (100, 255, 100), root_point=(1, 0))
        self.add_ui_element(self.fps_display)
        
        # Initialize animations
        self.setup_animations()
        
    def set_animations_loops(self, loops: int):
        """Set loop count for all animations"""
        yoyo = True  # Always use yoyo for this demo
        
        for anim_name, tween in self.animations.items():
            tween.set_loops(loops, yoyo=yoyo)
        
        if loops == -1:
            loop_text = "Loops: Infinite"
        elif loops == 0:
            loop_text = "Loops: No Loop"
        else:
            loop_text = f"Loops: {loops}"
        
        if yoyo:
            loop_text += " (Yoyo)"
        
        self.loop_display.set_text(loop_text)
        print(f"Set all animations to {loops if loops != -1 else 'infinite'} loops with yoyo={yoyo}")
    
    def setup_animations(self):
        """Set up the three animation examples using Tween system"""
        
        # 1. Linear Animation (smooth back and forth with yoyo)
        linear_tween = Tween.create(self.linear_box)
        linear_tween.to(
            x=350,  # Move 300 pixels to the right
            duration=2.0,
            easing=EasingType.LINEAR
        )
        linear_tween.set_loops(-1, yoyo=True)  # Infinite loops with yoyo
        linear_tween.set_callbacks(
            on_update=lambda tween, progress: self.update_animation_display('linear', linear_tween),
            on_loop=lambda loop_num: print(f"Linear animation: Loop #{loop_num}, Yoyo forward: {linear_tween.yoyo_forward}")
        )
        self.animation_handler.add('linear_animation', linear_tween, auto_play=True)
        
        # 2. Bounce Animation (bounces at the end with yoyo)
        bounce_tween = Tween.create(self.bounce_box)
        bounce_tween.to(
            x=350,  # Move 300 pixels to the right
            duration=2.0,
            easing=EasingType.BOUNCE_OUT
        )
        bounce_tween.set_loops(-1, yoyo=True)  # Infinite loops with yoyo
        bounce_tween.set_callbacks(
            on_update=lambda tween, progress: self.update_animation_display('bounce', bounce_tween),
            on_loop=lambda loop_num: print(f"Bounce animation: Loop #{loop_num}, Yoyo forward: {bounce_tween.yoyo_forward}")
        )
        self.animation_handler.add('bounce_animation', bounce_tween, auto_play=True)
        
        # 3. Back Animation (overshoots and comes back with yoyo)
        back_tween = Tween.create(self.back_box)
        back_tween.to(
            x=350,  # Move 300 pixels to the right
            duration=2.0,
            easing=EasingType.BACK_OUT
        )
        back_tween.set_loops(-1, yoyo=True)  # Infinite loops with yoyo
        back_tween.set_callbacks(
            on_update=lambda tween, progress: self.update_animation_display('back', back_tween),
            on_loop=lambda loop_num: print(f"Back animation: Loop #{loop_num}, Yoyo forward: {back_tween.yoyo_forward}")
        )
        self.animation_handler.add('back_animation', back_tween, auto_play=True)
        
        # Store animation objects for reference
        self.animations['linear'] = linear_tween
        self.animations['bounce'] = bounce_tween
        self.animations['back'] = back_tween
        
        print("Animations started with infinite yoyo loops")
    
    def update_animation_display(self, anim_type: str, tween: Tween):
        """Update animation progress display"""
        progress = tween.get_progress_percentage()
        current_loop = tween.current_loop
        yoyo_dir = "forward" if tween.yoyo_forward else "backward"
        
        if anim_type == 'linear':
            self.linear_progress.set_text(f"{progress:.0f}% L{current_loop} {yoyo_dir}")
        elif anim_type == 'bounce':
            self.bounce_progress.set_text(f"{progress:.0f}% L{current_loop} {yoyo_dir}")
        elif anim_type == 'back':
            self.back_progress.set_text(f"{progress:.0f}% L{current_loop} {yoyo_dir}")
    
    def update_animation_speed(self, speed: float):
        """Update animation speed by adjusting duration"""
        self.speed_display.set_text(f"{speed:.1f}x")
        
        # Update all animations' durations based on speed multiplier
        base_duration = 2.0  # Original duration
        new_duration = base_duration / speed
        
        for anim_name, tween in self.animations.items():
            # Use the new set_duration method
            tween.set_duration(new_duration)
            print(f"Updated {anim_name} animation duration to {new_duration:.2f}s")
    
    def pause_animations(self):
        """Pause all animations"""
        self.animation_handler.pause_all()
        print("All animations paused")
    
    def resume_animations(self):
        """Resume all animations"""
        self.animation_handler.resume_all()
        print("All animations resumed")
    
    def reset_animations(self):
        """Reset all animations to starting position"""
        print("Resetting animations...")
        
        # Cancel current animations
        self.animation_handler.cancel_all()
        
        # Reset box positions
        self.linear_box.x = 50
        self.bounce_box.x = 130
        self.back_box.x = 210
        
        # Reset progress displays
        self.linear_progress.set_text("0%")
        self.bounce_progress.set_text("0%")
        self.back_progress.set_text("0%")
        
        # Restart animations
        self.setup_animations()
        print("Animations reset and restarted")
    
    def update_state(self, key, value):
        """Updates the demo state and prints feedback for interactive elements."""
        self.demo_state[key] = value
        
        # Print for debug/console feedback
        if key in ['dropdown_selection', 'switch_state', 'number_selector_value', 'checkbox_state']:
            print(f"{key}: {value}")
    
    def add_progress(self, amount):
        """Increments the progress bar value."""
        self.demo_state['progress_value'] = min(100, self.demo_state['progress_value'] + amount)
        self.progress_bar.set_value(self.demo_state['progress_value'])
    
    def show_dialog(self):
        """Shows the RPG-style dialog box."""
        self.dialog_box.visible = True
        self.dialog_box.set_text(
            "Welcome to LunaEngine! This is an RPG-style dialog box with typewriter animation. Click to continue...",
            "System",
            instant=False  # Change to True if you want instant display
        )
        self.demo_state['dialog_active'] = True
    
    def hide_dialog(self):
        """Hides the RPG-style dialog box."""
        self.dialog_box.visible = False
        self.demo_state['dialog_active'] = False
    
    def update_ui_displays(self):
        """Updates all TextLabels that reflect current UI state."""
        self.button_counter.set_text(f"Clicks: {self.demo_state['button_clicks']}")
        self.slider_display.set_text(f"Value: {self.demo_state['slider_value']:.1f}")
        self.dropdown_display.set_text(f"Selected: {self.demo_state['dropdown_selection']}")
        self.switch_display.set_text(f"Switch: {'ON' if self.demo_state['switch_state'] else 'OFF'}")
        self.progress_display.set_text(f"Progress: {self.demo_state['progress_value']}%")
        self.select_display.set_text(f"Choice: {self.demo_state['select_index'] + 1}")
        
        # NEW ELEMENT DISPLAYS
        self.number_selector_display.set_text(f"Number: {self.demo_state['number_selector_value']:02d}")
        self.checkbox_display.set_text(f"Feature X: {'ON' if self.demo_state['checkbox_state'] else 'OFF'}")
        
        self.fps_display.set_text(f"FPS: {self.engine.get_fps_stats()['current_fps']:.1f}")
    
    def update(self, dt):
        # Update UI displays
        self.update_ui_displays()
        
        # Update progress bar animation
        if self.demo_state['progress_value'] < 100:
            self.demo_state['progress_value'] += dt * 2
            self.progress_bar.set_value(self.demo_state['progress_value'])
        
        # Update all animations through the handler
        self.animation_handler.update(dt)
    
    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        
        renderer.draw_rect(20, 90, 480, 650, ThemeManager.get_color('background2'))
        renderer.draw_rect(520, 90, 480, 650, ThemeManager.get_color('background2'))
        
        renderer.draw_rect(0, 0, self.engine.width, 90, ThemeManager.get_color('background2'))

def main():
    # Create engine
    engine = LunaEngine("LunaEngine - UI Demo", 1024, 768, use_opengl=True, fullscreen=False)
    
    # Configure the max FPS
    engine.fps = 60
    
    # Add and set the main scene
    engine.add_scene("main", ComprehensiveUIDemo)
    engine.set_scene("main")
    
    # Run the engine
    engine.run()

if __name__ == "__main__":
    main()