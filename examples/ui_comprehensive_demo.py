"""
ui_comprehensive_demo.py - Comprehensive UI Elements Demo for LunaEngine

ENGINE PATH:
lunaengine -> examples -> ui_comprehensive_demo.py

DESCRIPTION:
This demo showcases all available UI elements in the LunaEngine system.
All elements are organized in tabs by functional sections.
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
            'number_selector_value': 10,
            'checkbox_state': True,
        }
        self.animations = {}
        self.animation_handler = AnimationHandler(engine)
        self.setup_ui()
        
    def on_enter(self, previous_scene: str = None):
        print("=== LunaEngine UI Demo ===")
        print("Explore all UI elements organized by section!")
        print("Use the tabs to navigate between different UI element categories.")
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
        """Sets up all UI elements organized in tabs by section."""
        self.engine.set_global_theme(ThemeType.DEFAULT)
        
        # --- TITLE ---
        title = TextLabel(512, 30, "LunaEngine - UI Demo", 36, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        # --- MAIN TAB CONTAINER ---
        self.main_tabs = Tabination(25, 90, 980, 650, 20)
        
        # --- SECTION 1: Interactive Elements ---
        self.main_tabs.add_tab('Interactive')
        self.setup_interactive_tab()
        
        # --- SECTION 2: Selection Elements ---
        self.main_tabs.add_tab('Selection')
        self.setup_selection_tab()
        
        # --- SECTION 3: Visual Elements ---
        self.main_tabs.add_tab('Visual')
        self.setup_visual_tab()
        
        # --- SECTION 4: Advanced Elements ---
        self.main_tabs.add_tab('Advanced')
        self.setup_advanced_tab()
        
        # --- SECTION 5: Animation Examples ---
        self.main_tabs.add_tab('Animation')
        self.setup_animation_tab()
        
        # Add the main tabs container to the scene
        self.add_ui_element(self.main_tabs)
        
        # --- GLOBAL ELEMENTS (outside tabs) ---
        self.dialog_box = DialogBox(120, 300, 400, 150, style="modern")
        self.dialog_box.visible = False
        self.dialog_box.set_on_advance(lambda: self.hide_dialog())
        self.dialog_box.z_index = 100
        self.add_ui_element(self.dialog_box)
        
        self.fps_display = TextLabel(self.engine.width - 5, 20, "FPS: --", 16, (100, 255, 100), root_point=(1, 0))
        self.add_ui_element(self.fps_display)
        
        # Initialize animations
        self.setup_animations()
    
    def setup_interactive_tab(self):
        """Sets up interactive elements tab."""
        # Tab title
        self.main_tabs.add_to_tab('Interactive', TextLabel(10, 10, "Interactive Elements", 24, (255, 255, 0)))
        
        # Button Example
        button1 = Button(20, 50, 150, 40, "Click Me")
        button1.set_on_click(lambda: self.update_state('button_clicks', self.demo_state['button_clicks'] + 1))
        button1.set_simple_tooltip("This button counts your clicks!")
        self.main_tabs.add_to_tab('Interactive', button1)
        
        self.button_counter = TextLabel(180, 70, "Clicks: 0", 16)
        self.main_tabs.add_to_tab('Interactive', self.button_counter)
        
        # Slider Example
        slider_label = TextLabel(20, 125, "Slider:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Interactive', slider_label)
        
        slider = Slider(100, 120, 200, 30, 0, 100, 50)
        slider.on_value_changed = lambda v: self.update_state('slider_value', v)
        slider.set_simple_tooltip("Drag to change the value")
        self.main_tabs.add_to_tab('Interactive', slider)
        
        self.slider_display = TextLabel(310, 125, "Value: 50.0", 14)
        self.main_tabs.add_to_tab('Interactive', self.slider_display)
        
        # Progress Bar Example
        progress_label = TextLabel(20, 175, "Progress Bar:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Interactive', progress_label)
        
        self.progress_bar = ProgressBar(150, 170, 200, 20, 0, 100, 0)
        self.progress_bar.set_simple_tooltip("Shows progress from 0% to 100%")
        self.main_tabs.add_to_tab('Interactive', self.progress_bar)
        
        progress_btn = Button(360, 170, 100, 20, "Add 10%")
        progress_btn.set_on_click(lambda: self.add_progress(10))
        self.main_tabs.add_to_tab('Interactive', progress_btn)
        
        self.progress_display = TextLabel(470, 175, "Progress: 0%", 14)
        self.main_tabs.add_to_tab('Interactive', self.progress_display)
        
        # Draggable Element
        draggable_label = TextLabel(20, 220, "Draggable Element:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Interactive', draggable_label)
        
        draggable = UIDraggable(160, 220, 100, 50)
        draggable.set_simple_tooltip("Drag me around within the tab!")
        self.main_tabs.add_to_tab('Interactive', draggable)
    
    def setup_selection_tab(self):
        """Sets up selection elements tab."""
        # Tab title
        self.main_tabs.add_to_tab('Selection', TextLabel(10, 10, "Selection Elements", 24, (255, 255, 0)))
        
        # Dropdown Example
        dropdown_label = TextLabel(20, 50, "Dropdown:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Selection', dropdown_label)
        
        dropdown = Dropdown(120, 40, 200, 30, ["Option 1", "Option 2", "Option 3"])
        dropdown.set_on_selection_changed(lambda i, v: self.update_state('dropdown_selection', v))
        dropdown.set_simple_tooltip("Click to expand and select an option")
        self.main_tabs.add_to_tab('Selection', dropdown)
        
        self.dropdown_display = TextLabel(330, 50, "Selected: Option 1", 14)
        self.main_tabs.add_to_tab('Selection', self.dropdown_display)
        
        # Theme Dropdown
        theme_label = TextLabel(20, 100, "Theme Selector:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Selection', theme_label)
        
        theme_dropdown = Dropdown(150, 90, 150, 30, ThemeManager.get_theme_names(), font_size=16)
        theme_dropdown.set_on_selection_changed(lambda i, v: self.engine.set_global_theme(v))
        theme_dropdown.set_simple_tooltip("Change the global theme")
        self.main_tabs.add_to_tab('Selection', theme_dropdown)
        
        # Switch Example
        switch_label = TextLabel(20, 160, "Switch:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Selection', switch_label)
        
        switch = Switch(100, 150, 60, 30)
        switch.set_on_toggle(lambda s: self.update_state('switch_state', s))
        switch.set_simple_tooltip("Toggle switch on/off")
        self.main_tabs.add_to_tab('Selection', switch)
        
        self.switch_display = TextLabel(170, 160, "Switch: OFF", 14)
        self.main_tabs.add_to_tab('Selection', self.switch_display)
        
        # Checkbox Example
        checkbox_label = TextLabel(20, 205, "Checkbox:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Selection', checkbox_label)
        
        checkbox = Checkbox(120, 200, 200, 25, self.demo_state['checkbox_state'], label="Enable Feature X")
        checkbox.set_on_toggle(lambda s: self.update_state('checkbox_state', s))
        checkbox.set_simple_tooltip("Toggle this feature on/off")
        self.main_tabs.add_to_tab('Selection', checkbox)
        
        self.checkbox_display = TextLabel(330, 205, "Feature X: ON", 14)
        self.main_tabs.add_to_tab('Selection', self.checkbox_display)
        
        # Number Selector Example
        number_label = TextLabel(20, 255, "Number Selector:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Selection', number_label)
        
        number_selector = NumberSelector(160, 250, 75, 25, 0, 99, self.demo_state['number_selector_value'], min_length=2)
        number_selector.on_value_changed = lambda v: self.update_state('number_selector_value', v)
        number_selector.set_simple_tooltip("Select a number from 00 to 99")
        self.main_tabs.add_to_tab('Selection', number_selector)

        self.number_selector_display = TextLabel(245, 255, "Number: 10", 14)
        self.main_tabs.add_to_tab('Selection', self.number_selector_display)
        
        # Select Example
        select_label = TextLabel(20, 295, "Select (Cycle):", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Selection', select_label)
        
        select = Select(150, 290, 200, 30, ["Choice A", "Choice B", "Choice C"])
        select.set_on_selection_changed(lambda i, v: self.update_state('select_index', i))
        select.set_simple_tooltip("Use arrows to cycle through options")
        self.main_tabs.add_to_tab('Selection', select)
        
        self.select_display = TextLabel(360, 295, "Choice: 1", 14)
        self.main_tabs.add_to_tab('Selection', self.select_display)
    
    def setup_visual_tab(self):
        """Sets up visual elements tab."""
        # Tab title
        self.main_tabs.add_to_tab('Visual', TextLabel(10, 10, "Visual Elements", 24, (255, 255, 0)))
        
        # Gradient Example
        gradient_label = TextLabel(20, 50, "Color Gradient:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Visual', gradient_label)
        
        gradient = UIGradient(40, 75, 300, 60, [(255, 0, 0), (200, 100, 0), (0, 255, 0), (0, 200, 100), (0, 0, 255)])
        gradient.set_simple_tooltip("Beautiful gradient with multiple colors")
        self.main_tabs.add_to_tab('Visual', gradient)
        
        # Text Label Examples
        labels_label = TextLabel(20, 175, "Text Labels:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Visual', labels_label)
        
        label1 = TextLabel(40, 195, "Regular Label", 18, (255, 255, 255))
        self.main_tabs.add_to_tab('Visual', label1)
        
        label2 = TextLabel(40, 225, "Colored Label", 22, (100, 255, 100))
        self.main_tabs.add_to_tab('Visual', label2)
        
        label3 = TextLabel(40, 255, "Large Label", 28, (255, 200, 50))
        self.main_tabs.add_to_tab('Visual', label3)
        
        # Frame Example
        frame_label = TextLabel(20, 280, "UI Frame:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Visual', frame_label)
        
        frame = UiFrame(40, 300, 200, 100)
        frame.set_background_color((50, 50, 100, 200))
        frame.set_border((100, 150, 255),2)
        self.main_tabs.add_to_tab('Visual', frame)
        
        # Frame with text
        inner_label = TextLabel(5,5, "This is a frame", 16, (255, 255, 255))
        frame.add_child(inner_label)
        
        # Separator line
        separator = TextLabel(20, 420, "Horizontal Separator:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Visual', separator)
        
        separator_line = UiFrame(20, 440, 400, 2)
        separator_line.set_background_color((100, 100, 100))
        self.main_tabs.add_to_tab('Visual', separator_line)
    
    def setup_advanced_tab(self):
        """Sets up advanced elements tab."""
        # Tab title
        self.main_tabs.add_to_tab('Advanced', TextLabel(10, 10, "Advanced Elements", 24, (255, 255, 0)))
        
        # TextBox Example
        textbox_label = TextLabel(20, 60, "TextBox:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', textbox_label)
        
        textbox = TextBox(100, 50, 250, 30, "Type here...")
        textbox.set_simple_tooltip("Click and type to enter text")
        self.main_tabs.add_to_tab('Advanced', textbox)
        
        # ScrollingFrame Example
        scroll_label = TextLabel(20, 100, "Scrolling Frame:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', scroll_label)
        
        scroll_frame = ScrollingFrame(20, 130, 350, 200, 330, 300)
        scroll_frame.set_simple_tooltip("Scrollable container with multiple items")
        self.main_tabs.add_to_tab('Advanced', scroll_frame)
        
        # Add items to scrolling frame
        for i in range(15):
            item_color = (100 + i * 10, 150, 200) if i % 2 == 0 else (200, 150, 100 + i * 10)
            item = TextLabel(10, i * 30, f"Scrollable Item {i + 1}", 14, item_color)
            scroll_frame.add_child(item)
        
        # Dialog Button
        dialog_label = TextLabel(390, 65, "Dialog Box:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', dialog_label)
        
        dialog_btn = Button(500, 50, 150, 40, "Show Dialog")
        dialog_btn.set_on_click(lambda: self.show_dialog())
        dialog_btn.set_simple_tooltip("Click to show an RPG-style dialog box")
        self.main_tabs.add_to_tab('Advanced', dialog_btn)
        
        # Advanced Tooltip Button
        tooltip_label = TextLabel(390, 115, "Advanced Tooltip:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', tooltip_label)
        
        advanced_tooltip_btn = Button(500, 100, 180, 40, "Hover for Tooltip")
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
        self.main_tabs.add_to_tab('Advanced', advanced_tooltip_btn)
    
    def setup_animation_tab(self):
        """Sets up animation examples tab."""
        # Tab title
        self.main_tabs.add_to_tab('Animation', TextLabel(10, 10, "Animation Examples", 24, (255, 255, 0)))
        
        # Animation controls label
        animation_controls = TextLabel(20, 50, "Animation Controls:", 20, (200, 200, 255))
        self.main_tabs.add_to_tab('Animation', animation_controls)
        
        # Linear Animation Example
        linear_label = TextLabel(20, 80, "Linear Animation:", 16, (100, 255, 100))
        self.main_tabs.add_to_tab('Animation', linear_label)
        
        self.linear_box = UiFrame(20, 105, 20, 20)
        self.linear_box.set_background_color((100, 255, 100))
        self.main_tabs.add_to_tab('Animation', self.linear_box)
        
        # Linear animation path
        self.linear_path = UiFrame(20, 115, 300, 3)
        self.linear_path.set_background_color((50, 150, 50, 100))
        self.linear_path.z_index = -1
        self.main_tabs.add_to_tab('Animation', self.linear_path)
        
        self.linear_progress = TextLabel(330, 110, "0%", 14, (100, 255, 100))
        self.main_tabs.add_to_tab('Animation', self.linear_progress)
        
        # Bounce Animation Example
        bounce_label = TextLabel(20, 140, "Bounce Animation:", 16, (255, 200, 50))
        self.main_tabs.add_to_tab('Animation', bounce_label)
        
        self.bounce_box = UiFrame(20, 165, 20, 20)
        self.bounce_box.set_background_color((255, 200, 50))
        self.main_tabs.add_to_tab('Animation', self.bounce_box)
        
        # Bounce animation path
        self.bounce_path = UiFrame(20, 175, 300, 3)
        self.bounce_path.set_background_color((200, 150, 50, 100))
        self.bounce_path.z_index = -1
        self.main_tabs.add_to_tab('Animation', self.bounce_path)
        
        self.bounce_progress = TextLabel(330, 170, "0%", 14, (255, 200, 50))
        self.main_tabs.add_to_tab('Animation', self.bounce_progress)
        
        # Back Animation Example
        back_label = TextLabel(20, 200, "Back Animation:", 16, (255, 100, 100))
        self.main_tabs.add_to_tab('Animation', back_label)
        
        self.back_box = UiFrame(20, 225, 20, 20)
        self.back_box.set_background_color((255, 100, 100))
        self.main_tabs.add_to_tab('Animation', self.back_box)
        
        # Back animation path
        self.back_path = UiFrame(20, 235, 300, 3)
        self.back_path.set_background_color((200, 50, 50, 100))
        self.back_path.z_index = -1
        self.main_tabs.add_to_tab('Animation', self.back_path)
        
        self.back_progress = TextLabel(330, 230, "0%", 14, (255, 100, 100))
        self.main_tabs.add_to_tab('Animation', self.back_progress)
        
        # Animation control buttons (horizontal layout)
        control_y = 270
        pause_btn = Button(20, control_y, 90, 30, "Pause All")
        pause_btn.set_on_click(lambda: self.pause_animations())
        pause_btn.set_simple_tooltip("Pause all animations")
        self.main_tabs.add_to_tab('Animation', pause_btn)
        
        resume_btn = Button(120, control_y, 90, 30, "Resume All")
        resume_btn.set_on_click(lambda: self.resume_animations())
        resume_btn.set_simple_tooltip("Resume all animations")
        self.main_tabs.add_to_tab('Animation', resume_btn)
        
        reset_btn = Button(220, control_y, 90, 30, "Reset All")
        reset_btn.set_on_click(lambda: self.reset_animations())
        reset_btn.set_simple_tooltip("Reset all animations")
        self.main_tabs.add_to_tab('Animation', reset_btn)
        
        # Animation speed control
        speed_label = TextLabel(20, 310, "Animation Speed:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Animation', speed_label)
        
        self.speed_slider = Slider(170, 310, 150, 20, 0.5, 3.0, 1.0)
        self.speed_slider.on_value_changed = lambda v: self.update_animation_speed(v)
        self.speed_slider.set_simple_tooltip("Adjust animation speed (0.5x to 3.0x)")
        self.main_tabs.add_to_tab('Animation', self.speed_slider)
        
        self.speed_display = TextLabel(330, 315, "1.0x", 14)
        self.main_tabs.add_to_tab('Animation', self.speed_display)
        
        # Loop control buttons
        loop_label = TextLabel(20, 350, "Loop Controls:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Animation', loop_label)
        
        loop_y = 380
        loop_btn = Button(20, loop_y, 100, 30, "3 Loops")
        loop_btn.set_on_click(lambda: self.set_animations_loops(3))
        loop_btn.set_simple_tooltip("Set all animations to loop 3 times")
        self.main_tabs.add_to_tab('Animation', loop_btn)

        infinite_loop_btn = Button(130, loop_y, 100, 30, "Infinite")
        infinite_loop_btn.set_on_click(lambda: self.set_animations_loops(-1))
        infinite_loop_btn.set_simple_tooltip("Set all animations to loop infinitely")
        self.main_tabs.add_to_tab('Animation', infinite_loop_btn)

        no_loop_btn = Button(240, loop_y, 100, 30, "No Loop")
        no_loop_btn.set_on_click(lambda: self.set_animations_loops(0))
        no_loop_btn.set_simple_tooltip("Disable looping for all animations")
        self.main_tabs.add_to_tab('Animation', no_loop_btn)
        
        # Loop count display
        self.loop_display = TextLabel(20, 420, "Loops: Infinite", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Animation', self.loop_display)
        
        # Animation description
        desc_text = "Animations use the Tween system with Yoyo effect (forward-backward motion)."
        desc_label = TextLabel(20, 460, desc_text, 14, (150, 200, 255))
        self.main_tabs.add_to_tab('Animation', desc_label)
    
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
            x=320,  # Move within the tab boundaries
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
            x=320,  # Move within the tab boundaries
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
            x=320,  # Move within the tab boundaries
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
        self.linear_box.x = 20
        self.bounce_box.x = 20
        self.back_box.x = 20
        
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
        
        # Header background
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