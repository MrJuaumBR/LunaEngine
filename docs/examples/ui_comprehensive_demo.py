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
from lunaengine.misc import icons  # Import the icons module
from lunaengine.backend import *


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
            'text_area_content': "This is a multi-line text area.\nYou can type here...\nIt supports line numbers and word wrapping.\nTry editing this text!",
            'file_finder_path': "C:/example.txt",
            'current_page': 1,
        }
        self.animations = {}
        
        self.last_controller_count = 0
        self.controller_dropdown = None
        self.controller_info_labels = {}
        self.left_stick_indicator = None
        self.right_stick_indicator = None
        self.dpad_indicator = None
        self.button_indicators = {}  # for some key buttons
        self.selected_controller_idx = None
        
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
        
        # --- SECTION 6: Icons Gallery ---
        self.main_tabs.add_tab('Icons')
        self.setup_icons_tab()
        
        # --- SECTION 7: Notifications ---
        self.main_tabs.add_tab('Notifications')
        self.setup_notification_tab()
        
        # --- SECTION 8: Charts ---
        self.main_tabs.add_tab('Charts')
        self.setup_charts_tab()
        
        # --- SECTION 9: Controller ---
        self.main_tabs.add_tab('Controller')
        self.setup_controller_tab()

        
        
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
        self.main_tabs.set_corner_radius((10, 10, 10, 10))

    def setup_icons_tab(self):
        """Sets up the icons gallery tab."""
        # Tab title
        self.main_tabs.add_to_tab('Icons', TextLabel(10, 10, "Icons Gallery", 24, (255, 255, 0)))
        
        # Description
        desc = TextLabel(10, 45, "All available icons in LunaEngine (from icons.py):", 14, (200, 200, 200))
        self.main_tabs.add_to_tab('Icons', desc)
        
        # Icon size selector
        size_label = TextLabel(10, 75, "Icon Size:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Icons', size_label)
        
        self.icon_size_selector = NumberSelector(100, 70, 80, 25, 16, 96, 32, step=8)
        self.icon_size_selector.on_value_changed = lambda v: self.update_icons_size(v)
        self.main_tabs.add_to_tab('Icons', self.icon_size_selector)
        
        size_text = TextLabel(190, 75, "pixels", 14, (150, 150, 150))
        self.main_tabs.add_to_tab('Icons', size_text)
        
        # Background color toggle
        bg_toggle = Checkbox(250, 70, 150, 25, True, "Show Background")
        bg_toggle.set_on_toggle(lambda s: self.toggle_icons_background(s))
        self.main_tabs.add_to_tab('Icons', bg_toggle)
        
        # Scrolling frame for icons
        self.icons_scroll = ScrollingFrame(10, 110, 960, 480, 950, 1500)
        self.icons_scroll.set_simple_tooltip("Scroll to see all available icons")
        self.main_tabs.add_to_tab('Icons', self.icons_scroll)
        
        # Get all icons
        self.all_icons = icons.get_all_icons(32)
        self.icon_elements = []
        
        # Add icons to the scrolling frame in a grid
        self.update_icons_display()
    
    def update_icons_display(self):
        """Updates the icons display with current size and settings."""
        # Clear existing icon elements
        for element in self.icon_elements:
            self.icons_scroll.remove_child(element)
        self.icon_elements.clear()
        
        # Get current icon size
        icon_size = self.icon_size_selector.value
        
        # Get updated icons with new size
        self.all_icons = icons.get_all_icons(icon_size)
        
        # Grid layout
        icons_per_row = 8
        spacing = 20
        icon_with_spacing = icon_size + spacing + 60  # Extra space for label
        
        x_offset = 20
        y_offset = 20
        
        # Add each icon with label
        for i, (icon_name, icon_surface) in enumerate(self.all_icons.items()):
            row = i // icons_per_row
            col = i % icons_per_row
            
            x = x_offset + col * icon_with_spacing
            y = y_offset + row * (icon_size + 40)  # Extra space for label
            
            
            frame_size = int(icon_size * 1.8)
            # Create container frame
            icon_frame = UiFrame(x, y, frame_size, frame_size)
            icon_frame.set_background_color((40, 40, 50, 150))
            icon_frame.set_border((80, 80, 100), 1)
            icon_frame.set_corner_radius(5)
            
            # Create ImageLabel element for the icon
            icon_img = ImageLabel(frame_size//2, frame_size//2 + 10, None, icon_size, icon_size, root_point=(0.5, 0.5))
            icon_img.set_image(icon_surface)
            
            # Create label for icon name
            label = TextLabel(frame_size//2, 5, 
                             icon_name, 12, (200, 200, 200), root_point=(0.5, 0))
            label.set_simple_tooltip(f"Icon: {icon_name}")
            
            # Add to scrolling frame
            icon_frame.add_child(icon_img)
            icon_frame.add_child(label)
            self.icons_scroll.add_child(icon_frame)
            
            # Store references
            self.icon_elements.extend([icon_frame, icon_img, label])
        
        # Update total count display
        count_label = TextLabel(10, 600, f"Total Icons: {len(self.all_icons)}", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Icons', count_label)
        
        # Add icon usage example
        usage_label = TextLabel(400, 600, "Usage: icons.get_icon('icon_name', size)", 14, (150, 200, 255))
        self.main_tabs.add_to_tab('Icons', usage_label)
        
        # Example buttons using icons
        example_frame = UiFrame(600, 590, 350, 60)
        example_frame.set_background_color((40, 40, 60, 180))
        example_frame.set_border((80, 100, 150), 1)
        example_frame.set_corner_radius(8)
        self.main_tabs.add_to_tab('Icons', example_frame)
        
        example_label = TextLabel(610, 595, "Icon Usage Examples:", 14, (220, 220, 255))
        self.main_tabs.add_to_tab('Icons', example_label)
        
        # Example 1: Button with icon
        btn1 = Button(610, 615, 100, 30, "Save")
        btn1_icon = ImageLabel(620, 620, None, 16, 16)
        btn1_icon.set_image(icons.get_icon('save', 16))
        self.main_tabs.add_to_tab('Icons', btn1)
        self.main_tabs.add_to_tab('Icons', btn1_icon)
        
        # Example 2: Button with icon
        btn2 = Button(720, 615, 100, 30, "Load")
        btn2_icon = ImageLabel(730, 620, None, 16, 16)
        btn2_icon.set_image(icons.get_icon('load', 16))
        self.main_tabs.add_to_tab('Icons', btn2)
        self.main_tabs.add_to_tab('Icons', btn2_icon)
        
        # Example 3: Button with icon
        btn3 = Button(830, 615, 100, 30, "Home")
        btn3_icon = ImageLabel(840, 620, None, 16, 16)
        btn3_icon.set_image(icons.get_icon('home', 16))
        self.main_tabs.add_to_tab('Icons', btn3)
        self.main_tabs.add_to_tab('Icons', btn3_icon)
    
    def update_icons_size(self, size: int):
        """Updates all icons to new size."""
        print(f"Updating icons to size: {size}")
        self.update_icons_display()
    
    def toggle_icons_background(self, show: bool):
        """Toggles the background for icon containers."""
        for element in self.icon_elements:
            if isinstance(element, UiFrame):
                if show:
                    element.set_background_color((40, 40, 50, 150))
                    element.set_border((80, 80, 100), 1)
                else:
                    element.set_background_color((0, 0, 0, 0))
                    element.set_border((0, 0, 0, 0), 0)

    def setup_notification_tab(self):
        self.main_tabs.add_to_tab('Notifications', TextLabel(10, 10, "Notifications", 24, (255, 255, 0)))
        
        self.notification_type = Dropdown(20, 50, 200, 35, ['Success', 'Info', 'Warning', 'Error'])
        self.main_tabs.add_to_tab('Notifications', self.notification_type)
        
        self.notification_position = Dropdown(235, 50, 200, 35, ['Top Left', 'Top Center', 'Top Right', 'Bottom Left', 'Bottom Center', 'Bottom Right'])
        self.main_tabs.add_to_tab('Notifications', self.notification_position)
        
        self.notification_duration = NumberSelector(20, 100, 200, 35, 1, 5, 5)
        self.main_tabs.add_to_tab('Notifications', self.notification_duration)
        
        self.show_close_button = Checkbox(20, 150, 80, 30, True, "Show Close Button")
        self.main_tabs.add_to_tab('Notifications', self.show_close_button)
        
        self.auto_close = Checkbox(220, 150, 80, 30, True, "Auto Close")
        self.main_tabs.add_to_tab('Notifications', self.auto_close)
        
        self.show_progress_bar = Checkbox(420, 150, 80, 30, True, "Show Progress Bar")
        self.main_tabs.add_to_tab('Notifications', self.show_progress_bar)
        
        self.notification_button = Button(20, 200, 200, 40, "Show Notification")
        self.notification_button.set_on_click(self.show_notification)
        self.main_tabs.add_to_tab('Notifications', self.notification_button)
        
    def setup_charts_tab(self):
        """Sets up the charts tab with various GraphicVisualizer examples."""
        # Tab title
        self.main_tabs.add_to_tab('Charts', TextLabel(10, 10, "Charts Gallery", 24, (255, 255, 0)))

        # Description
        desc = TextLabel(10, 45, "Various chart types using GraphicVisualizer:", 14, (200, 200, 200))
        self.main_tabs.add_to_tab('Charts', desc)

        # Store references to charts for randomisation
        self.charts = []

        # Bar chart
        bar_label = TextLabel(20, 75, "Bar Chart", 16, (100, 255, 100))
        self.main_tabs.add_to_tab('Charts', bar_label)
        bar_chart = ChartVisualizer(20, 100, 200, 150,
                                    data=[15, 30, 45, 25, 60, 35],
                                    labels=['Jan','Feb','Mar','Apr','May','Jun'],
                                    chart_type='bar',
                                    title='Monthly Sales',
                                    show_labels=True,
                                    show_legend=False,
                                    colors=[(54,162,235)])
        bar_chart.set_simple_tooltip("Bar chart showing monthly data")
        self.main_tabs.add_to_tab('Charts', bar_chart)
        self.charts.append(bar_chart)

        # Pie chart
        pie_label = TextLabel(250, 75, "Pie Chart", 16, (255, 200, 100))
        self.main_tabs.add_to_tab('Charts', pie_label)
        pie_chart = ChartVisualizer(250, 100, 200, 150,
                                    data=[30, 20, 25, 15, 10],
                                    labels=['A','B','C','D','E'],
                                    chart_type='pie',
                                    title='Distribution',
                                    show_labels=True,
                                    show_legend=True)
        pie_chart.set_simple_tooltip("Pie chart with legend")
        self.main_tabs.add_to_tab('Charts', pie_chart)
        self.charts.append(pie_chart)

        # Line chart
        line_label = TextLabel(20, 270, "Line Chart", 16, (100, 200, 255))
        self.main_tabs.add_to_tab('Charts', line_label)
        line_chart = ChartVisualizer(20, 295, 200, 150,
                                    data=[10, 25, 15, 30, 20, 35],
                                    labels=['Mon','Tue','Wed','Thu','Fri','Sat'],
                                    chart_type='line',
                                    title='Weekly Trend',
                                    show_labels=True,
                                    show_legend=False)
        line_chart.set_simple_tooltip("Line chart with points")
        self.main_tabs.add_to_tab('Charts', line_chart)
        self.charts.append(line_chart)

        # Scatter plot
        scatter_label = TextLabel(250, 270, "Scatter Plot", 16, (255, 100, 255))
        self.main_tabs.add_to_tab('Charts', scatter_label)
        scatter_chart = ChartVisualizer(250, 295, 200, 150,
                                        data=[5, 12, 9, 15, 7, 20],
                                        labels=['P1','P2','P3','P4','P5','P6'],
                                        chart_type='scatter',
                                        title='Data Points',
                                        show_labels=True,
                                        show_legend=False)
        scatter_chart.set_simple_tooltip("Scatter plot")
        self.main_tabs.add_to_tab('Charts', scatter_chart)
        self.charts.append(scatter_chart)

        # Additional note
        note = TextLabel(20, 470, "You can create custom charts with your own data and colors.", 14, (150, 200, 255))
        self.main_tabs.add_to_tab('Charts', note)

        # Randomize button
        randomize_btn = Button(20, 500, 150, 30, "Randomize Charts")
        randomize_btn.set_on_click(self.randomize_charts)
        randomize_btn.set_simple_tooltip("Click to randomize all chart data with smooth animation")
        self.main_tabs.add_to_tab('Charts', randomize_btn)
        
    def setup_controller_tab(self):
        """Build the UI elements for the Controller information tab."""
        tab = 'Controller'

        # Title
        self.main_tabs.add_to_tab(tab, TextLabel(10, 10, "Controller Status", 24, (255, 255, 0)))

        # Dropdown to select controller (if multiple)
        self.controller_dropdown = Dropdown(10, 50, 300, 30, ["No controller"])
        self.controller_dropdown.set_on_selection_changed(self.on_controller_selected)
        self.controller_dropdown.set_simple_tooltip("Choose which controller to display")
        self.main_tabs.add_to_tab(tab, self.controller_dropdown)

        # Info frame
        info_frame = UiFrame(10, 100, 460, 150)
        info_frame.set_background_color((30, 30, 40, 200))
        info_frame.set_border((80, 80, 100), 1)
        self.main_tabs.add_to_tab(tab, info_frame)

        # Info labels (will be updated dynamically)
        self.controller_info_labels['type'] = TextLabel(20, 10, "Type: --", 16, (200, 200, 200))
        info_frame.add_child(self.controller_info_labels['type'])
        self.controller_info_labels['connection'] = TextLabel(20, 30, "Connection: --", 16, (200, 200, 200))
        info_frame.add_child(self.controller_info_labels['connection'])
        self.controller_info_labels['touchpad'] = TextLabel(20, 50, "Touchpad: --", 16, (200, 200, 200))
        info_frame.add_child(self.controller_info_labels['touchpad'])
        self.controller_info_labels['gyro'] = TextLabel(20, 70, "Gyro: --", 16, (200, 200, 200))
        info_frame.add_child(self.controller_info_labels['gyro'])
        self.controller_info_labels['rumble'] = TextLabel(20, 90, "Rumble: --", 16, (200, 200, 200))
        info_frame.add_child(self.controller_info_labels['rumble'])

        # Right column of info
        self.controller_info_labels['axes'] = TextLabel(250, 10, "Axes: --", 16, (200, 200, 200))
        info_frame.add_child(self.controller_info_labels['axes'])
        self.controller_info_labels['buttons'] = TextLabel(250, 30, "Buttons: --", 16, (200, 200, 200))
        info_frame.add_child(self.controller_info_labels['buttons'])
        self.controller_info_labels['hats'] = TextLabel(250, 50, "Hats: --", 16, (200, 200, 200))
        info_frame.add_child(self.controller_info_labels['hats'])

        # Joystick visualizations
        joy_label = TextLabel(10, 270, "Joysticks:", 20, (200, 200, 255))
        self.main_tabs.add_to_tab(tab, joy_label)

        # Left stick
        left_frame = UiFrame(10, 310, 120, 120)
        left_frame.set_background_color((50, 50, 60))
        left_frame.set_border((100, 100, 150), 1)
        left_frame.set_corner_radius(5)
        self.main_tabs.add_to_tab(tab, left_frame)

        self.left_stick_indicator = UiFrame(60, 60, 10, 10, root_point=(0.5, 0.5))  # centered initially
        self.left_stick_indicator.set_background_color((255, 100, 100))
        self.left_stick_indicator.set_corner_radius(5)
        left_frame.add_child(self.left_stick_indicator)

        left_label = TextLabel(10, 435, "Left Stick", 14, (180, 180, 180))
        self.main_tabs.add_to_tab(tab, left_label)

        # Right stick
        right_frame = UiFrame(150, 310, 120, 120)
        right_frame.set_background_color((50, 50, 60))
        right_frame.set_border((100, 100, 150), 1)
        right_frame.set_corner_radius(5)
        self.main_tabs.add_to_tab(tab, right_frame)

        self.right_stick_indicator = UiFrame(60, 60, 10, 10, root_point=(0.5, 0.5))
        self.right_stick_indicator.set_background_color((100, 255, 100))
        self.right_stick_indicator.set_corner_radius(5)
        right_frame.add_child(self.right_stick_indicator)

        right_label = TextLabel(150, 435, "Right Stick", 14, (180, 180, 180))
        self.main_tabs.add_to_tab(tab, right_label)

        # D‑pad visual (simple cross)
        dpad_label = TextLabel(300, 270, "D-Pad:", 20, (200, 200, 255))
        self.main_tabs.add_to_tab(tab, dpad_label)

        dpad_frame = UiFrame(300, 310, 100, 100)
        dpad_frame.set_background_color((40, 40, 50))
        dpad_frame.set_border((100, 100, 150), 1)
        self.main_tabs.add_to_tab(tab, dpad_frame)

        self.dpad_indicator = UiFrame(50, 50, 10, 10, root_point=(0.5, 0.5))  # center
        self.dpad_indicator.set_background_color((200, 200, 0))
        self.dpad_indicator.set_corner_radius(5)
        dpad_frame.add_child(self.dpad_indicator)
        
        # R2, L2, LT, RT
        triggers_indicators = UiFrame(425, 310, 80, 100)
        triggers_indicators.set_background_color((40, 40, 50))
        
        self.right_trigger = ProgressBar(75, 50, 30, 90, min_val=-1, max_val=1, value=0, root_point=(1, 0.5), orientation='vertical')
        triggers_indicators.add_child(self.right_trigger)
        
        self.left_trigger = ProgressBar(5, 50, 30, 90,min_val=-1, max_val=1, value=0, root_point=(0, 0.5), orientation='vertical')
        triggers_indicators.add_child(self.left_trigger)
        self.main_tabs.add_to_tab(tab, triggers_indicators)

        # Button indicators (A, B, X, Y)
        btn_label = TextLabel(10, 470, "Buttons:", 20, (200, 200, 255))
        self.main_tabs.add_to_tab(tab, btn_label)

        btn_frame = UiFrame(10, 510, 400, 90)
        btn_frame.set_background_color((30, 30, 40, 200))
        btn_frame.set_border((80, 80, 100), 1)
        self.main_tabs.add_to_tab(tab, btn_frame)

        button_names = ['A', 'B', 'X', 'Y', 'LB', 'RB', 'Back', 'Start', 'RSC', 'LSC']
        x_pos = 10
        y_pos = 10
        for index, name in enumerate(button_names): # Frame can handle 7 per line
            # Create a small colored circle for each button
            circle = UiFrame(x_pos, y_pos, 45, 30)
            circle.set_background_color((80, 80, 80))  # default grey
            circle.set_corner_radius(20)
            btn_frame.add_child(circle)
            self.button_indicators[name] = circle

            # Label under circle
            lbl = TextLabel(22.5, 15, name, 18, (200, 200, 200), root_point=(0.5, 0.5))
            circle.add_child(lbl)

            x_pos += 55
            if index % 7 == 6:
                x_pos = 10
                y_pos += 40

        # Update the dropdown with currently connected controllers
        self.refresh_controller_dropdown()

    def refresh_controller_dropdown(self):
        """Update the dropdown list with current controllers."""
        controllers = self.engine.controller_manager.get_all_controllers()
        if controllers:
            names = [f"{c.name} (ID:{c.joystick_id})" for c in controllers]
            self.controller_dropdown.set_options(names)
            if self.selected_controller_idx is None or self.selected_controller_idx >= len(controllers):
                self.selected_controller_idx = 0
                self.controller_dropdown.selected_index = 0
        else:
            self.controller_dropdown.set_options(["No controller"])
            self.selected_controller_idx = None

    def on_controller_selected(self, index: int, value: str):
        """Handle selection of a controller from dropdown."""
        controllers = self.engine.controller_manager.get_all_controllers()
        if controllers and 0 <= index < len(controllers):
            self.selected_controller_idx = index

    def update_controller_display(self):
        """Update the UI elements with current data from the selected controller."""
        if self.selected_controller_idx is None:
            # No controller selected, set all indicators to default
            for label in self.controller_info_labels.values():
                label.set_text(label.text.split(':')[0] + ": --")
            # Reset joystick indicators to center
            self.left_stick_indicator.x = 60
            self.left_stick_indicator.y = 60
            self.right_stick_indicator.x = 60
            self.right_stick_indicator.y = 60
            self.dpad_indicator.x = 50
            self.dpad_indicator.y = 50
            for circle in self.button_indicators.values():
                circle.set_background_color((80, 80, 80))
            return

        controllers = self.engine.controller_manager.get_all_controllers()
        if not controllers or self.selected_controller_idx >= len(controllers):
            return

        ctrl = controllers[self.selected_controller_idx]

        # Update info labels
        self.controller_info_labels['type'].set_text(f"Type: {ctrl.type.name}")
        self.controller_info_labels['connection'].set_text(f"Connection: {ctrl.connection.name}")
        self.controller_info_labels['touchpad'].set_text(f"Touchpad: {'Yes' if ctrl._touch_joystick else 'No'}")
        self.controller_info_labels['gyro'].set_text(f"Gyro: {'Yes' if Axis.GYRO_X in ctrl._axis_map else 'No'}")
        self.controller_info_labels['rumble'].set_text(f"Rumble: {'Yes' if ctrl._has_rumble else 'No'}")
        self.controller_info_labels['axes'].set_text(f"Axes: {ctrl.num_axes}")
        self.controller_info_labels['buttons'].set_text(f"Buttons: {ctrl.num_buttons}")
        self.controller_info_labels['hats'].set_text(f"Hats: {ctrl.num_hats}")

        # Update joystick positions
        # Left stick: map axis values (-1..1) to frame coordinates (0..120) with offset
        lx = ctrl.get_axis(Axis.LEFT_X)
        ly = ctrl.get_axis(Axis.LEFT_Y)
        # Invert Y because screen Y increases downwards
        left_x = 60 + int(lx * 50)   # range -50..50 around center 55
        left_y = 60 + int(-ly * 50)  # negative ly moves up
        # Clamp to frame bounds
        left_x = max(5, min(115, left_x))
        left_y = max(5, min(115, left_y))
        self.left_stick_indicator.x = left_x
        self.left_stick_indicator.y = left_y

        rx = ctrl.get_axis(Axis.RIGHT_X)
        ry = ctrl.get_axis(Axis.RIGHT_Y)
        right_x = 60 + int(rx * 50)
        right_y = 60 + int(-ry * 50)
        right_x = max(5, min(115, right_x))
        right_y = max(5, min(115, right_y))
        self.right_stick_indicator.x = right_x
        self.right_stick_indicator.y = right_y

        # D‑pad
        hat_x = -1 if ctrl.get_button_pressed(JButton.DPAD_LEFT) else (1 if ctrl.get_button_pressed(JButton.DPAD_RIGHT) else 0)
        hat_y = 1 if ctrl.get_button_pressed(JButton.DPAD_UP) else (-1 if ctrl.get_button_pressed(JButton.DPAD_DOWN) else 0)
        dpad_x = 50 + int(hat_x * 40)   # max displacement 40
        dpad_y = 50 + int(-hat_y * 40)
        dpad_x = max(5, min(95, dpad_x))
        dpad_y = max(5, min(95, dpad_y))
        self.dpad_indicator.x = dpad_x
        self.dpad_indicator.y = dpad_y
        
        # (R2, L2), (LT, RT)
        self.right_trigger.set_value(ctrl.get_axis(Axis.RIGHT_TRIGGER))
        self.left_trigger.set_value(ctrl.get_axis(Axis.LEFT_TRIGGER))

        # Button indicators
        button_map = {
            'A': JButton.A,
            'B': JButton.B,
            'X': JButton.X,
            'Y': JButton.Y,
            'LB': JButton.LEFT_BUMPER,
            'RB': JButton.RIGHT_BUMPER,
            'Back': JButton.BACK,
            'Start': JButton.START,
            'RSC': JButton.RIGHT_STICK,
            'LSC': JButton.LEFT_STICK,
        }
        for name, btn in button_map.items():
            if ctrl.get_button_pressed(btn):
                self.button_indicators[name].set_background_color((0, 255, 0))  # green when pressed
            else:
                self.button_indicators[name].set_background_color((80, 80, 80))

    def randomize_charts(self):
        """Generate new random data for each chart and animate the change."""
        import random
        for chart in self.charts:
            n = len(chart.data)
            if chart.chart_type == 'pie':
                # Random values for pie
                new_data = [random.randint(5, 40) for _ in range(n)]
            else:
                new_data = [random.randint(5, 70) for _ in range(n)]

            # Animate the change over 0.8 seconds
            chart.set_data(new_data, animate=True, duration=0.8)

        print("Charts randomized with smooth transition!")
    
    def show_notification(self):
        notification_type = [NotificationType.SUCCESS, NotificationType.INFO, NotificationType.WARNING, NotificationType.ERROR][self.notification_type.selected_index]
        notification_position = [NotificationPosition.TOP_LEFT, NotificationPosition.TOP_CENTER, NotificationPosition.TOP_RIGHT, NotificationPosition.BOTTOM_LEFT, NotificationPosition.BOTTOM_CENTER, NotificationPosition.BOTTOM_RIGHT][self.notification_position.selected_index]
        self.engine.show_notification(text="Notification Example Text", notification_type=notification_type, duration=self.notification_duration.value, position=notification_position, show_close_button=self.show_close_button.value, auto_close=self.auto_close.value, show_progress_bar=self.show_progress_bar.value)
    
    def setup_interactive_tab(self):
        """Sets up interactive elements tab."""
        # Tab title
        self.main_tabs.add_to_tab('Interactive', TextLabel(10, 10, "Interactive Elements", 24, (255, 255, 0)))
        
        # Button Example
        button1 = Button(x=20, y=50, width=150, height=40, text="Click Me")
        button1.set_on_click(self.update_state, 'button_clicks', self.demo_state['button_clicks'] + 1)
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
        
        theme_dropdown = Dropdown(150, 90, 150, 30, ThemeManager.get_theme_names(), font_size=16, searchable=True)
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
        
        clock12hranalog = Clock(20, 460, 150, None, 16, True, True, '12hr', 'analog')
        clock12hrdigital = Clock(200, 460, 150, None, 16, True, True, '12hr', 'digital')
        clock24hranalog = Clock(380, 460, 150, None, 16, True, True, '24hr', 'analog')
        clock24hrdigital = Clock(560, 460, 150, None, 16, True, True, '24hr', 'digital')
        clock24hrboth = Clock(740, 460, 150, None, 16, True, True, '24hr', 'both')
        self.main_tabs.add_to_tab('Visual', clock12hranalog)
        self.main_tabs.add_to_tab('Visual', clock12hrdigital)
        self.main_tabs.add_to_tab('Visual', clock24hranalog)
        self.main_tabs.add_to_tab('Visual', clock24hrdigital)
        self.main_tabs.add_to_tab('Visual', clock24hrboth)
    
    def setup_advanced_tab(self):
        """Sets up advanced elements tab."""
        # Tab title
        self.main_tabs.add_to_tab('Advanced', TextLabel(10, 10, "Advanced Elements", 24, (255, 255, 0)))
        
        # TextBox Example
        textbox_label = TextLabel(20, 60, "TextBox (Single-line):", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', textbox_label)
        
        textbox = TextBox(150, 50, 250, 30, "Type here...")
        textbox.set_simple_tooltip("Click and type to enter text")
        self.main_tabs.add_to_tab('Advanced', textbox)
        
        # NEW: TextArea Example
        textarea_label = TextLabel(20, 100, "TextArea (Multi-line):", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', textarea_label)
        
        self.text_area = TextArea(20, 130, 350, 200, 
                                text=self.demo_state['text_area_content'],
                                font_size=14,
                                line_numbers=True,
                                word_wrap=True,
                                read_only=False,
                                tab_size=4)
        self.text_area.set_simple_tooltip("A multi-line text editor with line numbers and word wrap")
        self.main_tabs.add_to_tab('Advanced', self.text_area)
        
        # TextArea controls
        textarea_controls_y = 340
        textarea_clear_btn = Button(20, textarea_controls_y, 80, 25, "Clear")
        textarea_clear_btn.set_on_click(lambda: self.clear_text_area())
        self.main_tabs.add_to_tab('Advanced', textarea_clear_btn)
        
        textarea_undo_btn = Button(110, textarea_controls_y, 80, 25, "Undo")
        textarea_undo_btn.set_on_click(lambda: self.text_area.undo())
        self.main_tabs.add_to_tab('Advanced', textarea_undo_btn)
        
        textarea_redo_btn = Button(200, textarea_controls_y, 80, 25, "Redo")
        textarea_redo_btn.set_on_click(lambda: self.text_area.redo())
        self.main_tabs.add_to_tab('Advanced', textarea_redo_btn)
        
        textarea_select_all_btn = Button(290, textarea_controls_y, 80, 25, "Select All")
        textarea_select_all_btn.set_on_click(lambda: self.text_area.select_all())
        self.main_tabs.add_to_tab('Advanced', textarea_select_all_btn)
        
        # NEW: FileFinder Example
        filefinder_label = TextLabel(420, 60, "FileFinder:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', filefinder_label)
        
        self.file_finder = FileFinder(420, 90, 350, 40, 
                                    file_path=self.demo_state['file_finder_path'],
                                    file_filter=['.txt', '.py', '.json', '.png', '.jpg'],
                                    dialog_title="Select a file",
                                    button_text="Browse...",
                                    show_icon=True)
        self.file_finder.set_simple_tooltip("Select a file from your computer")
        self.file_finder.on_file_selected = lambda path: self.on_file_selected(path)
        self.main_tabs.add_to_tab('Advanced', self.file_finder)
        
        # FileFinder status display
        self.file_finder_status = TextLabel(420, 135, f"Selected: {self.demo_state['file_finder_path']}", 14, (200, 200, 200))
        self.main_tabs.add_to_tab('Advanced', self.file_finder_status)
        
        # NEW: Pagination Example
        pagination_label = TextLabel(420, 210, "Pagination:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', pagination_label)
        
        self.pagination = Pagination(420, 230, 350, 40, total_pages=10, current_page=self.demo_state['current_page'])
        self.pagination.set_on_page_change(lambda page, _: self.on_page_change(page))
        self.pagination.set_simple_tooltip("Navigate through pages")
        self.main_tabs.add_to_tab('Advanced', self.pagination)
        
        # Pagination controls
        pagination_controls_y = 290
        pagination_prev_btn = Button(420, pagination_controls_y, 80, 25, "Previous")
        pagination_prev_btn.set_on_click(lambda: self.pagination.previous_page())
        self.main_tabs.add_to_tab('Advanced', pagination_prev_btn)
        
        pagination_next_btn = Button(510, pagination_controls_y, 80, 25, "Next")
        pagination_next_btn.set_on_click(lambda: self.pagination.next_page())
        self.main_tabs.add_to_tab('Advanced', pagination_next_btn)
        
        pagination_goto_btn = Button(600, pagination_controls_y, 80, 25, "Go to 5")
        pagination_goto_btn.set_on_click(lambda: self.pagination.set_page(5))
        self.main_tabs.add_to_tab('Advanced', pagination_goto_btn)
        
        self.pagination_display = TextLabel(690, pagination_controls_y + 5, f"Page: {self.demo_state['current_page']}/10", 14)
        self.main_tabs.add_to_tab('Advanced', self.pagination_display)
        
        # ScrollingFrame Example (moved to make room)
        scroll_label = TextLabel(20, 380, "Scrolling Frame:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', scroll_label)
        
        scroll_frame = ScrollingFrame(20, 410, 350, 200, 330, 600)
        scroll_frame.set_simple_tooltip("Scrollable container with multiple items")
        self.main_tabs.add_to_tab('Advanced', scroll_frame)
        
        # Add items to scrolling frame
        for i in range(15):
            item_color = (100 + i * 10, 150, 200) if i % 2 == 0 else (200, 150, 100 + i * 10)
            if i % 2 == 0: # Even = TextLabel
                item = TextLabel(10, 15 + i * 30, f"Scrollable Item {i + 1}", 14, item_color)
            else: # Odd = Button
                item = Button(10, 15 + i * 30, 80, 20, f"Button {i + 1}")
                item.set_on_click(print, f"Button {i + 1} clicked!")
                
            scroll_frame.add_child(item)
        
        # Dialog Button (moved to right side)
        dialog_label = TextLabel(400, 360, "Dialog Box:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', dialog_label)
        
        dialog_btn = Button(500, 355, 150, 40, "Show Dialog")
        dialog_btn.set_on_click(lambda: self.show_dialog())
        dialog_btn.set_simple_tooltip("Click to show an RPG-style dialog box")
        self.main_tabs.add_to_tab('Advanced', dialog_btn)
        
        # Advanced Tooltip Button
        tooltip_label = TextLabel(400, 410, "Advanced Tooltip:", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Advanced', tooltip_label)
        
        advanced_tooltip_btn = Button(500, 405, 180, 40, "Hover for Tooltip")
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
        
    def clear_text_area(self):
        """Clear the text area content."""
        self.text_area.set_text("")
        self.demo_state['text_area_content'] = ""
        print("Text area cleared")

    def on_file_selected(self, file_path):
        """Handle file selection."""
        self.demo_state['file_finder_path'] = file_path
        self.file_finder_status.set_text(f"Selected: {file_path}")
        print(f"File selected: {file_path}")

    def on_page_change(self, page):
        """Handle pagination page change."""
        self.demo_state['current_page'] = page
        self.pagination_display.set_text(f"Page: {page}/10")
        print(f"Page changed to: {page}")
    
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
        self.animation_handler.add('linear_animation', linear_tween, auto_play=True)
        
        # 2. Bounce Animation (bounces at the end with yoyo)
        bounce_tween = Tween.create(self.bounce_box)
        bounce_tween.to(
            x=320,  # Move within the tab boundaries
            duration=2.0,
            easing=EasingType.BOUNCE_OUT
        )
        bounce_tween.set_loops(-1, yoyo=True)  # Infinite loops with yoyo
        self.animation_handler.add('bounce_animation', bounce_tween, auto_play=True)
        
        # 3. Back Animation (overshoots and comes back with yoyo)
        back_tween = Tween.create(self.back_box)
        back_tween.to(
            x=320,  # Move within the tab boundaries
            duration=2.0,
            easing=EasingType.BACK_OUT
        )
        back_tween.set_loops(-1, yoyo=True)  # Infinite loops with yoyo
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
        
        # Existing element displays
        self.number_selector_display.set_text(f"Number: {self.demo_state['number_selector_value']:02d}")
        self.checkbox_display.set_text(f"Feature X: {'ON' if self.demo_state['checkbox_state'] else 'OFF'}")
        
        self.fps_display.set_text(f"FPS: {self.engine.get_fps_stats()['current_fps']:.1f}")
        
        # Update text area content if it exists
        if hasattr(self, 'text_area'):
            current_text = self.text_area.get_text()
            if current_text != self.demo_state.get('text_area_content'):
                self.demo_state['text_area_content'] = current_text
    
    def on_controller_connected(self, controller):
        print(f"[Controller] Connected: {controller.name}")
        self.refresh_controller_dropdown()

    def on_controller_disconnected(self, controller):
        print(f"[Controller] Disconnected: {controller.name}")
        self.refresh_controller_dropdown()
    
    def update(self, dt):
        # Update UI displays
        self.update_ui_displays()
        self.update_controller_display()

        current_count = len(self.engine.controller_manager.get_all_controllers())
        if current_count != self.last_controller_count:
            self.refresh_controller_dropdown()
            self.last_controller_count = current_count
        
        # Update progress bar animation
        if self.demo_state['progress_value'] < 100:
            self.demo_state['progress_value'] += dt * 2
            self.progress_bar.set_value(self.demo_state['progress_value'])
    
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