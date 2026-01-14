"""
filters_demo.py - Comprehensive Filter System Demo for LunaEngine

ENGINE PATH:
lunaengine -> examples -> filters_demo.py

DESCRIPTION:
This demo showcases all 19 available filters in the LunaEngine OpenGL renderer.
Users can:
1. Apply individual filters with configurable parameters
2. Combine multiple filters
3. Test different region types (fullscreen, rectangle, circle)
4. Adjust filter intensity and feather effects
5. Save/Load filter presets
6. View real-time performance impact

DEPENDENCIES:
- OpenGLRenderer with Filter system
- FilterType and FilterRegionType enums
- Filter class from backend.opengl

FEATURES DEMONSTRATED:
1. All 19 filter types with live preview
2. Real-time parameter adjustment
3. Region-based filtering (rectangle/circle regions)
4. Multiple filter stacking
5. Performance monitoring
6. Filter preset management
7. Visual feedback for active filters
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.backend.opengl import Filter, FilterType, FilterRegionType
from lunaengine.utils.performance import PerformanceMonitor
import pygame
import json
from typing import Dict, List, Tuple, Optional

class FilterDemoScene(Scene):
    """
    Comprehensive filter system demo scene.
    
    Shows all available filters in LunaEngine with real-time controls
    and visual feedback.
    """
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Demo state
        self.demo_state = {
            'active_filters': [],  # List of active Filter objects
            'selected_filter_type': FilterType.VIGNETTE,
            'selected_region_type': FilterRegionType.FULLSCREEN,
            'filter_intensity': 0.7,
            'filter_radius': 50.0,
            'filter_feather': 10.0,
            'region_x': 100,
            'region_y': 100,
            'region_width': 300,
            'region_height': 200,
            'show_grid': True,
            'show_region_outline': True,
            'performance_mode': False,
            'filter_presets': self.load_default_presets(),
            'current_preset': 'Default',
            'filter_count': 0,
            'animation_enabled': False,
            'animation_speed': 1.0,
        }
        
        # Animation state
        self.animation_time = 0.0
        
        # Initialize UI
        self.setup_ui()
        
        # Register key events
        @engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
    
    def on_enter(self, previous_scene: Optional[str] = None):
        """Called when scene becomes active."""
        super().on_enter(previous_scene)
        
        print("=" * 60)
        print("FILTER SYSTEM DEMO")
        print("=" * 60)
        print("\nAvailable Filters (19 total):")
        for i, filter_type in enumerate(FilterType, 1):
            print(f"  {i:2d}. {filter_type.value:20s} - {self.get_filter_description(filter_type)}")
        print("\nControls:")
        print("  SPACE     - Apply/Remove selected filter")
        print("  C         - Clear all filters")
        print("  R         - Reset to default view")
        print("  G         - Toggle grid display")
        print("  O         - Toggle region outline")
        print("  P         - Toggle performance mode")
        print("  A         - Toggle filter animation")
        print("  S         - Save current filter setup")
        print("  L         - Load saved preset")
        print("  ESC       - Return to main menu")
        print("  F1-F4     - Quick preset slots (1-4)")
        print("\nUse the UI controls to adjust filter parameters.")
        print("=" * 60)
        
        # Apply a default filter to start
        self.apply_quick_filter(FilterType.VIGNETTE, 0.5)
    
    def on_exit(self, next_scene: Optional[str] = None):
        """Called when scene is being exited."""
        super().on_exit(next_scene)
        
        # Clean up all filters
        self.clear_all_filters()
        print("Filter demo scene cleaned up.")
    
    def get_filter_description(self, filter_type: FilterType) -> str:
        """Get description for a filter type."""
        descriptions = {
            FilterType.NONE: "No effect",
            FilterType.VIGNETTE: "Darkens edges of screen",
            FilterType.BLUR: "Gaussian blur effect",
            FilterType.SEPIA: "Old photo/warm brown tone",
            FilterType.GRAYSCALE: "Black and white conversion",
            FilterType.INVERT: "Color inversion",
            FilterType.TEMPERATURE_WARM: "Warm orange/yellow tint",
            FilterType.TEMPERATURE_COLD: "Cool blue tint",
            FilterType.NIGHT_VISION: "Green monochrome with scanlines",
            FilterType.CRT: "Old CRT monitor effects",
            FilterType.PIXELATE: "Pixelation/low-res effect",
            FilterType.BLOOM: "Glow/light bleed effect",
            FilterType.EDGE_DETECT: "Edge detection (outlines)",
            FilterType.EMBOSS: "3D embossed texture",
            FilterType.SHARPEN: "Image sharpening",
            FilterType.POSTERIZE: "Reduces color palette",
            FilterType.NEON: "Neon glow around edges",
            FilterType.RADIAL_BLUR: "Zoom/motion blur from center",
            FilterType.FISHEYE: "Fish-eye lens distortion",
            FilterType.TWIRL: "Swirling vortex effect",
        }
        return descriptions.get(filter_type, "Unknown filter")
    
    def load_default_presets(self) -> Dict[str, List[Dict]]:
        """Load default filter presets."""
        return {
            'Default': [
                {'type': FilterType.VIGNETTE.value, 'intensity': 0.5, 'region': 'fullscreen'}
            ],
            'Old Film': [
                {'type': FilterType.SEPIA.value, 'intensity': 0.8, 'region': 'fullscreen'},
                {'type': FilterType.VIGNETTE.value, 'intensity': 0.3, 'region': 'fullscreen'}
            ],
            'Sci-Fi': [
                {'type': FilterType.NIGHT_VISION.value, 'intensity': 0.9, 'region': 'fullscreen'},
                {'type': FilterType.CRT.value, 'intensity': 0.4, 'region': 'fullscreen'}
            ],
            'Retro Game': [
                {'type': FilterType.PIXELATE.value, 'intensity': 0.6, 'region': 'fullscreen'},
                {'type': FilterType.CRT.value, 'intensity': 0.7, 'region': 'fullscreen'}
            ],
            'Dreamy': [
                {'type': FilterType.BLOOM.value, 'intensity': 0.5, 'region': 'fullscreen'},
                {'type': FilterType.BLUR.value, 'intensity': 0.3, 'region': 'fullscreen'}
            ],
            'Sketch': [
                {'type': FilterType.EDGE_DETECT.value, 'intensity': 0.8, 'region': 'fullscreen'},
                {'type': FilterType.GRAYSCALE.value, 'intensity': 1.0, 'region': 'fullscreen'}
            ],
            'Warm Sunset': [
                {'type': FilterType.TEMPERATURE_WARM.value, 'intensity': 0.7, 'region': 'fullscreen'},
                {'type': FilterType.VIGNETTE.value, 'intensity': 0.4, 'region': 'fullscreen'}
            ],
            'Cold Arctic': [
                {'type': FilterType.TEMPERATURE_COLD.value, 'intensity': 0.7, 'region': 'fullscreen'},
                {'type': FilterType.BLUR.value, 'intensity': 0.2, 'region': 'fullscreen'}
            ],
        }
    
    def setup_ui(self):
        """Setup comprehensive UI for filter controls."""
        
        # Set theme
        self.engine.set_global_theme(ThemeType.DEFAULT)
        
        # Title
        title = TextLabel(self.engine.width // 2, 20, 
                         "LunaEngine - Filter System Demo", 
                         36, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        subtitle = TextLabel(self.engine.width // 2, 60,
                           "19 Filters • Real-time Controls • Performance Monitoring",
                           18, (200, 200, 255), root_point=(0.5, 0))
        self.add_ui_element(subtitle)
        
        # Create main container with tabs
        self.main_tabs = Tabination(20, 100, self.engine.width - 40, self.engine.height - 120, 30)
        
        # Tab 1: Filter Selection & Control
        self.main_tabs.add_tab('Filters')
        self.setup_filters_tab()
        
        # Tab 2: Region Controls
        self.main_tabs.add_tab('Region')
        self.setup_region_tab()
        
        # Tab 3: Presets & Performance
        self.main_tabs.add_tab('Presets')
        self.setup_presets_tab()
        
        # Tab 4: Info & Help
        self.main_tabs.add_tab('Info')
        self.setup_info_tab()
        
        self.add_ui_element(self.main_tabs)
        
        # Active filters display (always visible)
        self.active_filters_label = TextLabel(self.engine.width - 10, 90,
                                            "Active: 0", 16, (100, 255, 100),
                                            root_point=(1, 0))
        self.add_ui_element(self.active_filters_label)
        
        # Performance display
        self.performance_label = TextLabel(self.engine.width - 10, self.engine.height - 10,
                                         "FPS: --", 16, (255, 200, 100),
                                         root_point=(1, 1))
        self.add_ui_element(self.performance_label)
        
        # Quick controls hint
        controls_hint = TextLabel(10, self.engine.height - 10,
                                 "SPACE: Apply/Remove | C: Clear | ESC: Menu",
                                 14, (150, 150, 200), root_point=(0, 1))
        self.add_ui_element(controls_hint)
    
    def setup_filters_tab(self):
        """Setup filter selection and controls tab."""
        
        # Filter type selection
        type_label = TextLabel(20, 20, "Filter Type:", 24, (255, 255, 0))
        self.main_tabs.add_to_tab('Filters', type_label)
        
        # Create dropdown with all filter types
        filter_names = [ft.value.replace('_', ' ').title() for ft in FilterType]
        self.filter_dropdown = Dropdown(150, 15, 250, 35, filter_names)
        self.filter_dropdown.set_on_selection_changed(self.on_filter_selected)
        self.main_tabs.add_to_tab('Filters', self.filter_dropdown)
        
        # Filter description
        self.filter_description = TextLabel(20, 65, "", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Filters', self.filter_description)
        
        # Intensity control
        intensity_label = TextLabel(20, 110, "Intensity:", 20, (200, 200, 255))
        self.main_tabs.add_to_tab('Filters',intensity_label)
        
        self.intensity_slider = Slider(120, 105, 200, 30, 0.0, 1.0, 0.7)
        self.intensity_slider.on_value_changed = self.on_intensity_changed
        self.main_tabs.add_to_tab('Filters', self.intensity_slider)
        
        self.intensity_value = TextLabel(330, 110, "0.70", 18)
        self.main_tabs.add_to_tab('Filters', self.intensity_value)
        
        # Feather control (for region edges)
        feather_label = TextLabel(20, 160, "Feather (edge softness):", 20, (200, 200, 255))
        self.main_tabs.add_to_tab('Filters', feather_label)
        
        self.feather_slider = Slider(220, 155, 200, 30, 0.0, 100.0, 10.0)
        self.feather_slider.on_value_changed = self.on_feather_changed
        self.main_tabs.add_to_tab('Filters', self.feather_slider)
        
        self.feather_value = TextLabel(430, 160, "10.0", 18)
        self.main_tabs.add_to_tab('Filters', self.feather_value)
        
        # Animation controls
        anim_label = TextLabel(20, 210, "Animation:", 20, (200, 200, 255))
        self.main_tabs.add_to_tab('Filters', anim_label)
        
        self.anim_toggle = Switch(120, 205, 60, 30, False)
        self.anim_toggle.set_on_toggle(self.on_animation_toggled)
        self.main_tabs.add_to_tab('Filters', self.anim_toggle)
        
        anim_state_label = TextLabel(190, 210, "OFF", 18, (200, 150, 150))
        self.main_tabs.add_to_tab('Filters', anim_state_label)
        self.anim_state_label = anim_state_label
        
        self.anim_speed_slider = Slider(250, 205, 150, 30, 0.1, 3.0, 1.0)
        self.anim_speed_slider.on_value_changed = self.on_animation_speed_changed
        self.main_tabs.add_to_tab('Filters', self.anim_speed_slider)
        
        self.anim_speed_value = TextLabel(410, 210, "1.0x", 18)
        self.main_tabs.add_to_tab('Filters', self.anim_speed_value)
        
        # Control buttons
        y_buttons = 270
        
        # Apply/Remove button
        self.apply_button = Button(20, y_buttons, 180, 40, "Apply Filter")
        self.apply_button.set_on_click(self.toggle_current_filter)
        self.main_tabs.add_to_tab('Filters', self.apply_button)
        
        # Clear all button
        clear_button = Button(210, y_buttons, 180, 40, "Clear All")
        clear_button.set_on_click(self.clear_all_filters)
        self.main_tabs.add_to_tab('Filters', clear_button)
        
        # Reset button
        reset_button = Button(400, y_buttons, 180, 40, "Reset View")
        reset_button.set_on_click(self.reset_view)
        self.main_tabs.add_to_tab('Filters', reset_button)
        
        # Active filters list
        list_label = TextLabel(20, 330, "Active Filters:", 22, (255, 255, 0))
        self.main_tabs.add_to_tab('Filters', list_label)
        
        # Scrollable list of active filters
        self.active_list_frame = ScrollingFrame(20, 360, 560, 200, 540, 300)
        self.main_tabs.add_to_tab('Filters', self.active_list_frame)
        
        # Update initial description
        self.update_filter_description()
    
    def setup_region_tab(self):
        """Setup region controls tab."""
        # Region type selection
        region_label = TextLabel(20, 20, "Region Type:", 24, (255, 255, 0))
        self.main_tabs.add_to_tab('Region', region_label)
        
        region_types = [rt.value.replace('_', ' ').title() for rt in FilterRegionType]
        self.region_dropdown = Dropdown(150, 15, 200, 35, region_types)
        self.region_dropdown.set_on_selection_changed(self.on_region_selected)
        self.main_tabs.add_to_tab('Region', self.region_dropdown)
        
        # Region position controls
        pos_label = TextLabel(20, 80, "Region Position & Size:", 22, (200, 200, 255))
        self.main_tabs.add_to_tab('Region', pos_label)
        
        # X position
        x_label = TextLabel(20, 120, "X:", 18)
        self.main_tabs.add_to_tab('Region', x_label)
        
        self.x_slider = Slider(50, 115, 200, 25, 0, self.engine.width, 100)
        self.x_slider.on_value_changed = self.on_region_x_changed
        self.main_tabs.add_to_tab('Region', self.x_slider)
        
        self.x_value = TextLabel(260, 120, "100", 16)
        self.main_tabs.add_to_tab('Region', self.x_value)
        
        # Y position
        y_label = TextLabel(20, 160, "Y:", 18)
        self.main_tabs.add_to_tab('Region', y_label)
        
        self.y_slider = Slider(50, 155, 200, 25, 0, self.engine.height, 100)
        self.y_slider.on_value_changed = self.on_region_y_changed
        self.main_tabs.add_to_tab('Region', self.y_slider)
        
        self.y_value = TextLabel(260, 160, "100", 16)
        self.main_tabs.add_to_tab('Region', self.y_value)
        
        # Width
        width_label = TextLabel(20, 200, "Width:", 18)
        self.main_tabs.add_to_tab('Region', width_label)
        
        self.width_slider = Slider(80, 195, 200, 25, 10, 500, 300)
        self.width_slider.on_value_changed = self.on_region_width_changed
        self.main_tabs.add_to_tab('Region', self.width_slider)
        
        self.width_value = TextLabel(290, 200, "300", 16)
        self.main_tabs.add_to_tab('Region', self.width_value)
        
        # Height
        height_label = TextLabel(20, 240, "Height:", 18)
        self.main_tabs.add_to_tab('Region', height_label)
        
        self.height_slider = Slider(80, 235, 200, 25, 10, 400, 200)
        self.height_slider.on_value_changed = self.on_region_height_changed
        self.main_tabs.add_to_tab('Region', self.height_slider)
        
        self.height_value = TextLabel(290, 240, "200", 16)
        self.main_tabs.add_to_tab('Region', self.height_value)
        
        # Radius control (for circular regions)
        radius_label = TextLabel(20, 280, "Radius (%):", 18)
        self.main_tabs.add_to_tab('Region', radius_label)
        
        self.radius_slider = Slider(120, 275, 200, 25, 10, 100, 50)
        self.radius_slider.on_value_changed = self.on_radius_changed
        self.main_tabs.add_to_tab('Region', self.radius_slider)
        
        self.radius_value = TextLabel(330, 280, "50%", 16)
        self.main_tabs.add_to_tab('Region', self.radius_value)
        
        # Visual feedback toggle
        visual_label = TextLabel(20, 320, "Visual Feedback:", 22, (200, 200, 255))
        self.main_tabs.add_to_tab('Region', visual_label)
        
        self.grid_toggle = Switch(20, 350, 60, 30, True)
        self.grid_toggle.set_on_toggle(lambda s: self.toggle_setting('show_grid', s))
        self.main_tabs.add_to_tab('Region', self.grid_toggle)
        
        grid_label = TextLabel(90, 355, "Show Grid", 18)
        self.main_tabs.add_to_tab('Region', grid_label)
        
        self.outline_toggle = Switch(20, 390, 60, 30, True)
        self.outline_toggle.set_on_toggle(lambda s: self.toggle_setting('show_region_outline', s))
        self.main_tabs.add_to_tab('Region', self.outline_toggle)
        
        outline_label = TextLabel(90, 395, "Show Region Outline", 18)
        self.main_tabs.add_to_tab('Region', outline_label)
        
        # Quick region buttons
        region_buttons_y = 440
        
        fullscreen_btn = Button(20, region_buttons_y, 120, 35, "Fullscreen")
        fullscreen_btn.set_on_click(lambda: self.set_region_type(FilterRegionType.FULLSCREEN))
        self.main_tabs.add_to_tab('Region', fullscreen_btn)
        
        center_btn = Button(150, region_buttons_y, 120, 35, "Center")
        center_btn.set_on_click(self.center_region)
        self.main_tabs.add_to_tab('Region', center_btn)
        
        quarter_btn = Button(280, region_buttons_y, 120, 35, "Quarter")
        quarter_btn.set_on_click(self.set_quarter_region)
        self.main_tabs.add_to_tab('Region', quarter_btn)
        
        # Update initial values
        self.update_region_controls()
    
    def setup_presets_tab(self):
        """Setup presets and performance tab."""
        # Preset selection
        preset_label = TextLabel(20, 20, "Filter Presets:", 24, (255, 255, 0))
        self.main_tabs.add_to_tab('Presets', preset_label)
        
        preset_names = list(self.demo_state['filter_presets'].keys())
        self.preset_dropdown = Dropdown(150, 15, 200, 35, preset_names)
        self.preset_dropdown.set_on_selection_changed(self.on_preset_selected)
        self.main_tabs.add_to_tab('Presets', self.preset_dropdown)
        
        # Load preset button
        load_btn = Button(360, 15, 100, 35, "Load")
        load_btn.set_on_click(self.load_selected_preset)
        self.main_tabs.add_to_tab('Presets', load_btn)
        
        # Save current button
        save_btn = Button(470, 15, 100, 35, "Save As...")
        save_btn.set_on_click(self.save_current_preset)
        self.main_tabs.add_to_tab('Presets', save_btn)
        
        # Preset description
        self.preset_description = TextLabel(20, 70, "", 16, (200, 200, 255))
        self.main_tabs.add_to_tab('Presets', self.preset_description)
        
        # Quick preset slots
        quick_label = TextLabel(20, 110, "Quick Slots (F1-F4):", 22, (200, 200, 255))
        self.main_tabs.add_to_tab('Presets', quick_label)
        
        quick_y = 140
        for i in range(4):
            slot_btn = Button(20 + (i * 150), quick_y, 140, 35, f"Slot {i+1}: Empty")
            slot_btn.set_on_click(lambda idx=i: self.load_quick_preset(idx))
            self.main_tabs.add_to_tab('Presets', slot_btn)
            # Store reference
            if not hasattr(self, 'quick_slot_buttons'):
                self.quick_slot_buttons = []
            self.quick_slot_buttons.append(slot_btn)
        
        # Performance section
        perf_label = TextLabel(20, 200, "Performance:", 24, (255, 255, 0))
        self.main_tabs.add_to_tab('Presets', perf_label)
        
        self.perf_toggle = Switch(20, 230, 60, 30, False)
        self.perf_toggle.set_on_toggle(self.on_performance_toggled)
        self.main_tabs.add_to_tab('Presets', self.perf_toggle)
        
        perf_state_label = TextLabel(90, 235, "Performance Mode: OFF", 18)
        self.main_tabs.add_to_tab('Presets', perf_state_label)
        self.perf_state_label = perf_state_label
        
        # Performance stats
        self.perf_stats = TextLabel(20, 280, "", 16, (200, 255, 200))
        self.main_tabs.add_to_tab('Presets', self.perf_stats)
        
        # Filter count impact
        self.filter_impact = TextLabel(20, 310, "", 16, (255, 200, 200))
        self.main_tabs.add_to_tab('Presets', self.filter_impact)
        
        # Update preset description
        self.update_preset_description()
    
    def setup_info_tab(self):
        """Setup information and help tab."""
        
        # Demo info
        info_lines = [
            "FILTER SYSTEM DEMO",
            "",
            "This demo showcases the 19 filters available",
            "in LunaEngine's OpenGL renderer.",
            "",
            "Key Features:",
            "• Real-time filter application & removal",
            "• Adjustable intensity and parameters",
            "• Region-based filtering (rectangle/circle)",
            "• Multiple filter stacking",
            "• Performance monitoring",
            "• Filter preset saving/loading",
            "• Visual feedback for active regions",
            "",
            "Filter Types:",
            "1. Vignette - Darkens screen edges",
            "2. Blur - Gaussian blur effect",
            "3. Sepia - Old photo/warm tone",
            "4. Grayscale - Black & white",
            "5. Invert - Color inversion",
            "6. Temperature Warm - Warm orange tint",
            "7. Temperature Cold - Cool blue tint",
            "8. Night Vision - Green with scanlines",
            "9. CRT - Old monitor effects",
            "10. Pixelate - Low-res pixelation",
            "11. Bloom - Glow/light bleed",
            "12. Edge Detect - Edge outlines",
            "13. Emboss - 3D textured effect",
            "14. Sharpen - Image sharpening",
            "15. Posterize - Reduced colors",
            "16. Neon - Neon glow on edges",
            "17. Radial Blur - Zoom/motion blur",
            "18. Fisheye - Lens distortion",
            "19. Twirl - Swirling vortex",
            "",
            "Performance Tips:",
            "• Fewer filters = better performance",
            "• Smaller regions = less GPU load",
            "• Complex filters (blur, bloom) are heavier",
            "• Enable Performance Mode to reduce overhead",
            "",
            "Use the UI controls or keyboard shortcuts!"
        ]
        
        y_pos = 20
        for line in info_lines:
            if line.startswith("FILTER SYSTEM") or line.startswith("Key Features") or line.startswith("Filter Types") or line.startswith("Performance Tips"):
                # Section headers
                label = TextLabel(20, y_pos, line, 20, (255, 255, 0))
                y_pos += 30
            elif line == "":
                # Empty line
                y_pos += 10
            elif line[0].isdigit() and ". " in line:
                # Numbered list item
                label = TextLabel(40, y_pos, line, 16, (200, 200, 255))
                y_pos += 25
            else:
                # Regular text
                label = TextLabel(20, y_pos, line, 16, (200, 200, 255))
                y_pos += 25
            
            self.main_tabs.add_to_tab('Info', label)
        
        # Keyboard shortcuts
        shortcuts = [
            "",
            "Keyboard Shortcuts:",
            "SPACE - Toggle selected filter",
            "C - Clear all filters",
            "R - Reset to default view",
            "G - Toggle grid display",
            "O - Toggle region outline",
            "P - Toggle performance mode",
            "A - Toggle filter animation",
            "S - Save current setup",
            "L - Load saved preset",
            "ESC - Return to menu",
            "F1-F4 - Quick preset slots",
        ]
        
        y_pos += 20
        for line in shortcuts:
            if line == "":
                y_pos += 10
            elif line == "Keyboard Shortcuts:":
                label = TextLabel(20, y_pos, line, 22, (255, 200, 100))
                y_pos += 30
            else:
                label = TextLabel(40, y_pos, line, 18, (200, 255, 200))
                y_pos += 28
            
            if line:
                self.main_tabs.add_to_tab('Info', label)
    
    # ============================================================================
    # FILTER MANAGEMENT METHODS
    # ============================================================================
    
    def create_filter_from_current_settings(self) -> Filter:
        """Create a Filter object from current UI settings."""
        filter_obj = Filter(
            filter_type=self.demo_state['selected_filter_type'],
            intensity=self.demo_state['filter_intensity'],
            region_type=self.demo_state['selected_region_type'],
            region_pos=(self.demo_state['region_x'], self.demo_state['region_y']),
            region_size=(self.demo_state['region_width'], self.demo_state['region_height']),
            radius=self.demo_state['filter_radius'],
            feather=self.demo_state['filter_feather'],
            blend_mode="normal"
        )
        return filter_obj
    
    def apply_filter(self, filter_obj: Filter):
        """Apply a filter to the renderer."""
        if self.engine.renderer and hasattr(self.engine.renderer, 'add_filter'):
            self.engine.renderer.add_filter(filter_obj)
            self.demo_state['active_filters'].append(filter_obj)
            self.demo_state['filter_count'] = len(self.demo_state['active_filters'])
            print(f"Applied filter: {filter_obj.filter_type.value}")
            self.update_active_filters_list()
            self.update_active_filters_label()
    
    def remove_filter(self, filter_obj: Filter):
        """Remove a filter from the renderer."""
        if self.engine.renderer and hasattr(self.engine.renderer, 'remove_filter'):
            self.engine.renderer.remove_filter(filter_obj)
            if filter_obj in self.demo_state['active_filters']:
                self.demo_state['active_filters'].remove(filter_obj)
                self.demo_state['filter_count'] = len(self.demo_state['active_filters'])
                print(f"Removed filter: {filter_obj.filter_type.value}")
                self.update_active_filters_list()
                self.update_active_filters_label()
    
    def clear_all_filters(self):
        """Remove all filters from the renderer."""
        if self.engine.renderer and hasattr(self.engine.renderer, 'clear_filters'):
            self.engine.renderer.clear_filters()
            self.demo_state['active_filters'].clear()
            self.demo_state['filter_count'] = 0
            print("Cleared all filters")
            self.update_active_filters_list()
            self.update_active_filters_label()
    
    def is_filter_active(self, filter_type: FilterType) -> bool:
        """Check if a filter type is currently active."""
        return any(f.filter_type == filter_type for f in self.demo_state['active_filters'])
    
    def toggle_current_filter(self):
        """Toggle the currently selected filter on/off."""
        filter_type = self.demo_state['selected_filter_type']
        
        # Check if this filter type is already active
        active_filters = [f for f in self.demo_state['active_filters'] 
                         if f.filter_type == filter_type]
        
        if active_filters:
            # Remove all instances of this filter type
            for filter_obj in active_filters[:]:  # Copy list for safe removal
                self.remove_filter(filter_obj)
            self.apply_button.set_text("Apply Filter")
        else:
            # Apply new filter
            filter_obj = self.create_filter_from_current_settings()
            self.apply_filter(filter_obj)
            self.apply_button.set_text("Remove Filter")
    
    def apply_quick_filter(self, filter_type: FilterType, intensity: float = 0.5):
        """Apply a filter with default settings."""
        # Clear existing filters of this type first
        existing = [f for f in self.demo_state['active_filters'] 
                   if f.filter_type == filter_type]
        for f in existing:
            self.remove_filter(f)
        
        # Create and apply new filter
        filter_obj = Filter(
            filter_type=filter_type,
            intensity=intensity,
            region_type=FilterRegionType.FULLSCREEN,
            region_pos=(0, 0),
            region_size=(self.engine.width, self.engine.height),
            radius=50.0,
            feather=10.0
        )
        self.apply_filter(filter_obj)
        
        # Update UI to match
        self.demo_state['selected_filter_type'] = filter_type
        self.demo_state['filter_intensity'] = intensity
        
        filter_index = list(FilterType).index(filter_type)
        self.filter_dropdown.set_selected_index(filter_index)
        self.intensity_slider.set_value(intensity)
        self.intensity_value.set_text(f"{intensity:.2f}")
        
        self.apply_button.set_text("Remove Filter")
        self.update_filter_description()
    
    # ============================================================================
    # REGION MANAGEMENT
    # ============================================================================
    
    def set_region_type(self, region_type: FilterRegionType):
        """Set the current region type."""
        self.demo_state['selected_region_type'] = region_type
        
        # Update dropdown
        region_index = list(FilterRegionType).index(region_type)
        self.region_dropdown.set_selected_index(region_index)
        
        # Update active filters with new region type
        self.update_active_filters_regions()
    
    def center_region(self):
        """Center the region on screen."""
        center_x = self.engine.width // 2 - self.demo_state['region_width'] // 2
        center_y = self.engine.height // 2 - self.demo_state['region_height'] // 2
        
        self.demo_state['region_x'] = center_x
        self.demo_state['region_y'] = center_y
        
        self.x_slider.set_value(center_x)
        self.y_slider.set_value(center_y)
        self.x_value.set_text(str(center_x))
        self.y_value.set_text(str(center_y))
        
        self.update_active_filters_regions()
    
    def set_quarter_region(self):
        """Set region to quarter of screen."""
        quarter_w = self.engine.width // 2
        quarter_h = self.engine.height // 2
        quarter_x = self.engine.width // 4
        quarter_y = self.engine.height // 4
        
        self.demo_state['region_width'] = quarter_w
        self.demo_state['region_height'] = quarter_h
        self.demo_state['region_x'] = quarter_x
        self.demo_state['region_y'] = quarter_y
        
        self.width_slider.set_value(quarter_w)
        self.height_slider.set_value(quarter_h)
        self.x_slider.set_value(quarter_x)
        self.y_slider.set_value(quarter_y)
        
        self.width_value.set_text(str(quarter_w))
        self.height_value.set_text(str(quarter_h))
        self.x_value.set_text(str(quarter_x))
        self.y_value.set_text(str(quarter_y))
        
        self.update_active_filters_regions()
    
    def update_active_filters_regions(self):
        """Update region settings for all active filters."""
        for filter_obj in self.demo_state['active_filters']:
            filter_obj.region_type = self.demo_state['selected_region_type']
            filter_obj.region_pos = (self.demo_state['region_x'], self.demo_state['region_y'])
            filter_obj.region_size = (self.demo_state['region_width'], self.demo_state['region_height'])
            filter_obj.radius = self.demo_state['filter_radius']
            filter_obj.feather = self.demo_state['filter_feather']
    
    # ============================================================================
    # PRESET MANAGEMENT
    # ============================================================================
    
    def load_selected_preset(self):
        """Load the selected preset."""
        preset_name = self.demo_state['current_preset']
        if preset_name in self.demo_state['filter_presets']:
            self.load_preset(preset_name)
    
    def load_preset(self, preset_name: str):
        """Load a specific preset."""
        print(f"Loading preset: {preset_name}")
        
        # Clear existing filters
        self.clear_all_filters()
        
        # Apply filters from preset
        if preset_name in self.demo_state['filter_presets']:
            preset_data = self.demo_state['filter_presets'][preset_name]
            
            for filter_data in preset_data:
                try:
                    filter_type = FilterType(filter_data['type'])
                    intensity = filter_data.get('intensity', 0.7)
                    region_type_str = filter_data.get('region', 'fullscreen')
                    
                    # Convert region string to enum
                    if region_type_str == 'fullscreen':
                        region_type = FilterRegionType.FULLSCREEN
                        region_pos = (0, 0)
                        region_size = (self.engine.width, self.engine.height)
                    elif region_type_str == 'rectangle':
                        region_type = FilterRegionType.RECTANGLE
                        region_pos = (100, 100)
                        region_size = (300, 200)
                    else:  # circle or default to fullscreen
                        region_type = FilterRegionType.FULLSCREEN
                        region_pos = (0, 0)
                        region_size = (self.engine.width, self.engine.height)
                    
                    filter_obj = Filter(
                        filter_type=filter_type,
                        intensity=intensity,
                        region_type=region_type,
                        region_pos=region_pos,
                        region_size=region_size,
                        radius=50.0,
                        feather=10.0
                    )
                    
                    self.apply_filter(filter_obj)
                    
                except (KeyError, ValueError) as e:
                    print(f"Error loading filter from preset: {e}")
        
        self.demo_state['current_preset'] = preset_name
        self.update_preset_description()
    
    def save_current_preset(self):
        """Save current filter setup as a new preset."""
        # In a real implementation, you'd prompt for a name
        # For this demo, we'll create an auto-named preset
        preset_count = len([k for k in self.demo_state['filter_presets'].keys() 
                           if k.startswith('Custom ')])
        preset_name = f"Custom {preset_count + 1}"
        
        # Convert current filters to preset data
        preset_data = []
        for filter_obj in self.demo_state['active_filters']:
            filter_data = {
                'type': filter_obj.filter_type.value,
                'intensity': filter_obj.intensity,
                'region': filter_obj.region_type.value,
                'radius': filter_obj.radius,
                'feather': filter_obj.feather
            }
            preset_data.append(filter_data)
        
        # Save the preset
        self.demo_state['filter_presets'][preset_name] = preset_data
        self.demo_state['current_preset'] = preset_name
        
        # Update UI
        preset_names = list(self.demo_state['filter_presets'].keys())
        self.preset_dropdown.set_options(preset_names)
        self.preset_dropdown.set_selected_index(preset_names.index(preset_name))
        
        self.update_preset_description()
        print(f"Saved preset: {preset_name} with {len(preset_data)} filters")
    
    def load_quick_preset(self, slot_index: int):
        """Load a quick preset from a slot."""
        # In a real implementation, you'd have actual slot storage
        # For this demo, we'll use some predefined quick presets
        quick_presets = {
            0: 'Old Film',
            1: 'Sci-Fi',
            2: 'Retro Game',
            3: 'Dreamy'
        }
        
        if slot_index in quick_presets:
            preset_name = quick_presets[slot_index]
            self.load_preset(preset_name)
            print(f"Loaded quick preset {slot_index + 1}: {preset_name}")
        else:
            print(f"No quick preset in slot {slot_index + 1}")
    
    # ============================================================================
    # UI UPDATE METHODS
    # ============================================================================
    
    def update_filter_description(self):
        """Update the filter description label."""
        filter_type = self.demo_state['selected_filter_type']
        description = self.get_filter_description(filter_type)
        is_active = self.is_filter_active(filter_type)
        
        status = " (ACTIVE)" if is_active else " (INACTIVE)"
        self.filter_description.set_text(f"{description}{status}")
    
    def update_preset_description(self):
        """Update the preset description label."""
        preset_name = self.demo_state['current_preset']
        if preset_name in self.demo_state['filter_presets']:
            filter_count = len(self.demo_state['filter_presets'][preset_name])
            self.preset_description.set_text(
                f"{preset_name}: {filter_count} filter{'s' if filter_count != 1 else ''}"
            )
        else:
            self.preset_description.set_text("No preset selected")
    
    def update_active_filters_list(self):
        """Update the scrollable list of active filters."""
        # Clear existing items
        self.active_list_frame.clear_children()
        
        # Add current active filters
        for i, filter_obj in enumerate(self.demo_state['active_filters']):
            y_pos = i * 30
            
            # Filter name and intensity
            filter_text = f"{i+1}. {filter_obj.filter_type.value}: {filter_obj.intensity:.2f}"
            filter_label = TextLabel(10, y_pos + 5, filter_text, 16)
            self.active_list_frame.add_child(filter_label)
            
            # Remove button
            remove_btn = Button(400, y_pos, 60, 25, "Remove")
            remove_btn.set_on_click(lambda f=filter_obj: self.remove_filter(f))
            self.active_list_frame.add_child(remove_btn)
            
            # Intensity slider for this filter
            intensity_slider = Slider(470, y_pos, 80, 25, 0.0, 1.0, filter_obj.intensity)
            intensity_slider.on_value_changed = lambda v, f=filter_obj: self.update_filter_intensity(f, v)
            self.active_list_frame.add_child(intensity_slider)
    
    def update_active_filters_label(self):
        """Update the active filters counter."""
        count = self.demo_state['filter_count']
        color = (100, 255, 100) if count <= 3 else (255, 200, 100) if count <= 6 else (255, 100, 100)
        self.active_filters_label.set_text(f"Active: {count}")
        self.active_filters_label.set_text_color(color)
    
    def update_region_controls(self):
        """Update region control values in UI."""
        self.x_value.set_text(str(self.demo_state['region_x']))
        self.y_value.set_text(str(self.demo_state['region_y']))
        self.width_value.set_text(str(self.demo_state['region_width']))
        self.height_value.set_text(str(self.demo_state['region_height']))
        self.radius_value.set_text(f"{self.demo_state['filter_radius']}%")
    
    def update_filter_intensity(self, filter_obj: Filter, intensity: float):
        """Update intensity of a specific filter."""
        filter_obj.intensity = max(0.0, min(1.0, intensity))
        print(f"Updated {filter_obj.filter_type.value} intensity to {intensity:.2f}")
    
    def update_performance_display(self):
        """Update performance statistics display."""
        if not self.demo_state['performance_mode']:
            self.perf_stats.set_text("Performance mode disabled")
            return
        
        # Get FPS stats
        fps_stats = self.engine.get_fps_stats()
        
        # Calculate filter performance impact
        filter_count = self.demo_state['filter_count']
        base_fps = 60  # Assuming 60 FPS baseline with no filters
        
        # Simple heuristic: each filter reduces FPS by 2-10% depending on type
        # This is just for demonstration
        performance_text = (
            f"FPS: {fps_stats['current_fps']:.1f} (Target: {self.engine.fps})\n"
            f"Frame Time: {fps_stats['frame_time_ms']:.2f} ms\n"
            f"Active Filters: {filter_count}\n"
            f"1% Low: {fps_stats['percentile_1']:.1f} FPS"
        )
        
        self.perf_stats.set_text(performance_text)
        
        # Update filter impact warning
        if filter_count == 0:
            self.filter_impact.set_text("No filters - Maximum performance")
            self.filter_impact.set_text_color((100, 255, 100))
        elif filter_count <= 3:
            self.filter_impact.set_text("Light filter load - Good performance")
            self.filter_impact.set_text_color((200, 255, 100))
        elif filter_count <= 6:
            self.filter_impact.set_text("Medium filter load - Acceptable performance")
            self.filter_impact.set_text_color((255, 200, 100))
        else:
            self.filter_impact.set_text("Heavy filter load - Reduced performance")
            self.filter_impact.set_text_color((255, 100, 100))
    
    def reset_view(self):
        """Reset to default view."""
        self.clear_all_filters()
        
        # Reset region to center
        self.center_region()
        
        # Reset selected filter to vignette
        self.demo_state['selected_filter_type'] = FilterType.VIGNETTE
        self.filter_dropdown.set_selected_index(0)
        
        # Reset intensity
        self.demo_state['filter_intensity'] = 0.5
        self.intensity_slider.set_value(0.5)
        self.intensity_value.set_text("0.50")
        
        # Update UI
        self.update_filter_description()
        self.apply_button.set_text("Apply Filter")
        
        print("View reset to default")
    
    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================
    
    def on_filter_selected(self, index: int, value: str):
        """Handle filter type selection."""
        # Convert string back to FilterType enum
        filter_name = value.lower().replace(' ', '_')
        try:
            filter_type = FilterType(filter_name)
            self.demo_state['selected_filter_type'] = filter_type
            
            # Update description and button text
            self.update_filter_description()
            
            # Update apply button text based on whether filter is active
            if self.is_filter_active(filter_type):
                self.apply_button.set_text("Remove Filter")
            else:
                self.apply_button.set_text("Apply Filter")
                
        except ValueError:
            print(f"Invalid filter type: {filter_name}")
    
    def on_region_selected(self, index: int, value: str):
        """Handle region type selection."""
        region_name = value.lower().replace(' ', '_')
        try:
            region_type = FilterRegionType(region_name)
            self.set_region_type(region_type)
        except ValueError:
            print(f"Invalid region type: {region_name}")
    
    def on_intensity_changed(self, value: float):
        """Handle intensity slider change."""
        self.demo_state['filter_intensity'] = value
        self.intensity_value.set_text(f"{value:.2f}")
        
        # Update intensity of all active filters of selected type
        filter_type = self.demo_state['selected_filter_type']
        for filter_obj in self.demo_state['active_filters']:
            if filter_obj.filter_type == filter_type:
                filter_obj.intensity = value
    
    def on_feather_changed(self, value: float):
        """Handle feather slider change."""
        self.demo_state['filter_feather'] = value
        self.feather_value.set_text(f"{value:.1f}")
        self.update_active_filters_regions()
    
    def on_region_x_changed(self, value: float):
        """Handle region X position change."""
        self.demo_state['region_x'] = int(value)
        self.x_value.set_text(str(int(value)))
        self.update_active_filters_regions()
    
    def on_region_y_changed(self, value: float):
        """Handle region Y position change."""
        self.demo_state['region_y'] = int(value)
        self.y_value.set_text(str(int(value)))
        self.update_active_filters_regions()
    
    def on_region_width_changed(self, value: float):
        """Handle region width change."""
        self.demo_state['region_width'] = int(value)
        self.width_value.set_text(str(int(value)))
        self.update_active_filters_regions()
    
    def on_region_height_changed(self, value: float):
        """Handle region height change."""
        self.demo_state['region_height'] = int(value)
        self.height_value.set_text(str(int(value)))
        self.update_active_filters_regions()
    
    def on_radius_changed(self, value: float):
        """Handle radius slider change."""
        self.demo_state['filter_radius'] = value
        self.radius_value.set_text(f"{value}%")
        self.update_active_filters_regions()
    
    def on_preset_selected(self, index: int, value: str):
        """Handle preset selection."""
        self.demo_state['current_preset'] = value
        self.update_preset_description()
    
    def on_performance_toggled(self, enabled: bool):
        """Handle performance mode toggle."""
        self.demo_state['performance_mode'] = enabled
        state_text = "Performance Mode: ON" if enabled else "Performance Mode: OFF"
        self.perf_state_label.set_text(state_text)
        
        if enabled:
            print("Performance mode enabled - showing stats")
        else:
            print("Performance mode disabled")
    
    def on_animation_toggled(self, enabled: bool):
        """Handle animation toggle."""
        self.demo_state['animation_enabled'] = enabled
        state_text = "ON" if enabled else "OFF"
        color = (100, 255, 100) if enabled else (200, 150, 150)
        self.anim_state_label.set_text(state_text)
        self.anim_state_label.set_text_color(color)
        
        if enabled:
            print("Filter animation enabled")
        else:
            print("Filter animation disabled")
    
    def on_animation_speed_changed(self, value: float):
        """Handle animation speed change."""
        self.demo_state['animation_speed'] = value
        self.anim_speed_value.set_text(f"{value:.1f}x")
    
    def toggle_setting(self, setting_name: str, value: bool):
        """Toggle a boolean setting."""
        self.demo_state[setting_name] = value
        print(f"{setting_name.replace('_', ' ').title()}: {'ON' if value else 'OFF'}")
    
    def handle_key_press(self, key):
        """Handle keyboard input."""
        if key == pygame.K_ESCAPE:
            # Return to main menu
            self.engine.set_scene("MainMenu")
            
        elif key == pygame.K_SPACE:
            # Toggle current filter
            self.toggle_current_filter()
            
        elif key == pygame.K_c:
            # Clear all filters
            self.clear_all_filters()
            
        elif key == pygame.K_r:
            # Reset view
            self.reset_view()
            
        elif key == pygame.K_g:
            # Toggle grid
            self.demo_state['show_grid'] = not self.demo_state['show_grid']
            self.grid_toggle.set_value(self.demo_state['show_grid'])
            print(f"Grid: {'ON' if self.demo_state['show_grid'] else 'OFF'}")
            
        elif key == pygame.K_o:
            # Toggle region outline
            self.demo_state['show_region_outline'] = not self.demo_state['show_region_outline']
            self.outline_toggle.set_value(self.demo_state['show_region_outline'])
            print(f"Region Outline: {'ON' if self.demo_state['show_region_outline'] else 'OFF'}")
            
        elif key == pygame.K_p:
            # Toggle performance mode
            self.demo_state['performance_mode'] = not self.demo_state['performance_mode']
            self.perf_toggle.set_value(self.demo_state['performance_mode'])
            self.on_performance_toggled(self.demo_state['performance_mode'])
            
        elif key == pygame.K_a:
            # Toggle animation
            self.demo_state['animation_enabled'] = not self.demo_state['animation_enabled']
            self.anim_toggle.set_value(self.demo_state['animation_enabled'])
            self.on_animation_toggled(self.demo_state['animation_enabled'])
            
        elif key == pygame.K_s:
            # Save preset
            self.save_current_preset()
            
        elif key == pygame.K_l:
            # Load preset
            self.load_selected_preset()
            
        elif pygame.K_F1 <= key <= pygame.K_F4:
            # Quick preset slots
            slot_index = key - pygame.K_F1
            self.load_quick_preset(slot_index)
    
    # ============================================================================
    # UPDATE & RENDER
    # ============================================================================
    
    def update(self, dt):
        """Update scene logic."""
        # Update animation time if enabled
        if self.demo_state['animation_enabled']:
            self.animation_time += dt * self.demo_state['animation_speed']
            
            # Animate filter intensities (sin wave between 0.3 and 0.8)
            for filter_obj in self.demo_state['active_filters']:
                # Different animation for each filter based on its type
                anim_offset = hash(filter_obj.filter_type.value) % 100 / 100.0
                intensity = 0.5 + 0.3 * math.sin(self.animation_time * 2 + anim_offset * 2 * math.pi)
                filter_obj.intensity = max(0.1, min(1.0, intensity))
        
        # Update performance display
        self.update_performance_display()
        
        # Update FPS display
        fps_stats = self.engine.get_fps_stats()
        self.performance_label.set_text(f"FPS: {fps_stats['current_fps']:.1f}")
    
    def render(self, renderer):
        """Render the scene."""
        # Get current theme colors
        theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        
        # Draw background with gradient
        renderer.fill_screen(theme.background)
        
        # Draw test pattern to see filter effects clearly
        self.draw_test_pattern(renderer)
        
        # Draw grid if enabled
        if self.demo_state['show_grid']:
            self.draw_grid(renderer)
        
        # Draw region outline if enabled and not fullscreen
        if (self.demo_state['show_region_outline'] and 
            self.demo_state['selected_region_type'] != FilterRegionType.FULLSCREEN):
            self.draw_region_outline(renderer)
        
        # Draw filter information overlay
        self.draw_filter_info(renderer)
    
    def draw_test_pattern(self, renderer):
        """Draw a test pattern to visualize filter effects."""
        # Color gradient background
        width, height = self.engine.width, self.engine.height
        
        # Draw color bands
        colors = [
            (255, 0, 0, 200),     # Red
            (255, 128, 0, 200),   # Orange
            (255, 255, 0, 200),   # Yellow
            (0, 255, 0, 200),     # Green
            (0, 255, 255, 200),   # Cyan
            (0, 0, 255, 200),     # Blue
            (128, 0, 255, 200),   # Purple
            (255, 0, 255, 200)    # Magenta
        ]
        
        band_width = width // len(colors)
        for i, color in enumerate(colors):
            x = i * band_width
            renderer.draw_rect(x, 0, band_width, height, color, fill=True)
        
        # Draw geometric shapes
        center_x, center_y = width // 2, height // 2
        
        # Circles
        circle_colors = [(255, 255, 255, 150), (0, 0, 0, 150)]
        for i, color in enumerate(circle_colors):
            radius = 50 + i * 30
            renderer.draw_circle(center_x, center_y, radius, color, fill=False, border_width=3)
        
        # Lines
        line_color = (255, 255, 255, 180)
        renderer.draw_line(0, center_y, width, center_y, line_color, 2)
        renderer.draw_line(center_x, 0, center_x, height, line_color, 2)
        
        # Diagonal lines
        renderer.draw_line(0, 0, width, height, line_color, 2)
        renderer.draw_line(width, 0, 0, height, line_color, 2)
        
        # Text labels for orientation
        font = pygame.font.Font(None, 24)
        labels = [
            ("TOP-LEFT", 50, 50),
            ("TOP-RIGHT", width - 100, 50),
            ("BOTTOM-LEFT", 50, height - 50),
            ("BOTTOM-RIGHT", width - 150, height - 50),
            ("CENTER", center_x - 40, center_y - 15)
        ]
        
        for text, x, y in labels:
            text_surface = font.render(text, True, (255, 255, 255))
            renderer.draw_surface(text_surface, x, y)
    
    def draw_grid(self, renderer):
        """Draw a grid overlay."""
        width, height = self.engine.width, self.engine.height
        grid_color = (100, 100, 100, 80)
        grid_size = 50
        
        # Vertical lines
        for x in range(0, width, grid_size):
            renderer.draw_line(x, 0, x, height, grid_color, 1)
        
        # Horizontal lines
        for y in range(0, height, grid_size):
            renderer.draw_line(0, y, width, y, grid_color, 1)
        
        # Center lines (thicker)
        center_color = (150, 150, 150, 120)
        renderer.draw_line(width // 2, 0, width // 2, height, center_color, 2)
        renderer.draw_line(0, height // 2, width, height // 2, center_color, 2)
    
    def draw_region_outline(self, renderer):
        """Draw outline of current filter region."""
        x, y = self.demo_state['region_x'], self.demo_state['region_y']
        width, height = self.demo_state['region_width'], self.demo_state['region_height']
        region_type = self.demo_state['selected_region_type']
        
        if region_type == FilterRegionType.RECTANGLE:
            # Rectangle outline
            outline_color = (255, 255, 0, 200)
            renderer.draw_rect(x, y, width, height, outline_color, fill=False, border_width=3)
            
            # Corner markers
            marker_color = (255, 200, 0, 255)
            marker_size = 10
            corners = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
            for cx, cy in corners:
                renderer.draw_rect(cx - marker_size//2, cy - marker_size//2, 
                                 marker_size, marker_size, marker_color, fill=True)
            
        elif region_type == FilterRegionType.CIRCLE:
            # Circle outline
            center_x = x + width // 2
            center_y = y + height // 2
            radius = min(width, height) // 2 * (self.demo_state['filter_radius'] / 100.0)
            
            outline_color = (0, 255, 255, 200)
            renderer.draw_circle(center_x, center_y, int(radius), outline_color, fill=False, border_width=3)
            
            # Center marker
            marker_color = (0, 200, 255, 255)
            renderer.draw_rect(center_x - 5, center_y - 5, 10, 10, marker_color, fill=True)
    
    def draw_filter_info(self, renderer):
        """Draw filter information overlay."""
        width, height = self.engine.width, self.engine.height
        
        # Active filters summary
        if self.demo_state['active_filters']:
            y_pos = height - 120
            
            # Background panel
            renderer.draw_rect(10, y_pos - 10, width - 20, 110, (0, 0, 0, 180), fill=True)
            
            # Title
            font_large = pygame.font.Font(None, 24)
            title_text = f"Active Filters: {len(self.demo_state['active_filters'])}"
            title_surface = font_large.render(title_text, True, (255, 255, 100))
            renderer.draw_surface(title_surface, 20, y_pos)
            
            # Filter list
            font = pygame.font.Font(None, 18)
            for i, filter_obj in enumerate(self.demo_state['active_filters']):
                if i < 5:  # Show only first 5 to avoid clutter
                    filter_text = f"{filter_obj.filter_type.value}: {filter_obj.intensity:.2f}"
                    if filter_obj.region_type != FilterRegionType.FULLSCREEN:
                        filter_text += f" ({filter_obj.region_type.value})"
                    
                    text_surface = font.render(filter_text, True, (200, 200, 255))
                    renderer.draw_surface(text_surface, 40, y_pos + 30 + i * 20)
            
            if len(self.demo_state['active_filters']) > 5:
                more_text = f"... and {len(self.demo_state['active_filters']) - 5} more"
                text_surface = font.render(more_text, True, (150, 150, 200))
                renderer.draw_surface(text_surface, 40, y_pos + 130)


class MainMenuScene(Scene):
    """
    Simple main menu for the filter demo.
    """
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Title
        title = TextLabel(self.engine.width // 2, 100, 
                         "LunaEngine Filter System", 
                         48, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        subtitle = TextLabel(self.engine.width // 2, 160,
                           "19 Post-Processing Filters • OpenGL Powered",
                           24, (200, 200, 255), root_point=(0.5, 0))
        self.add_ui_element(subtitle)
        
        # Demo button
        demo_btn = Button(self.engine.width // 2, 250, 300, 50, 
                         "Start Filter Demo", 32, root_point=(0.5, 0))
        demo_btn.set_on_click(lambda: engine.set_scene("FilterDemo"))
        self.add_ui_element(demo_btn)
        
        # Quick filter test buttons
        quick_label = TextLabel(self.engine.width // 2, 320,
                               "Quick Tests:", 28, (255, 255, 0), root_point=(0.5, 0))
        self.add_ui_element(quick_label)
        
        # Row 1
        vignette_btn = Button(self.engine.width // 2 - 160, 370, 150, 40, "Vignette")
        vignette_btn.set_on_click(lambda: self.quick_test(FilterType.VIGNETTE))
        self.add_ui_element(vignette_btn)
        
        blur_btn = Button(self.engine.width // 2, 370, 150, 40, "Blur")
        blur_btn.set_on_click(lambda: self.quick_test(FilterType.BLUR))
        self.add_ui_element(blur_btn)
        
        sepia_btn = Button(self.engine.width // 2 + 160, 370, 150, 40, "Sepia")
        sepia_btn.set_on_click(lambda: self.quick_test(FilterType.SEPIA))
        self.add_ui_element(sepia_btn)
        
        # Row 2
        crt_btn = Button(self.engine.width // 2 - 160, 420, 150, 40, "CRT")
        crt_btn.set_on_click(lambda: self.quick_test(FilterType.CRT))
        self.add_ui_element(crt_btn)
        
        neon_btn = Button(self.engine.width // 2, 420, 150, 40, "Neon")
        neon_btn.set_on_click(lambda: self.quick_test(FilterType.NEON))
        self.add_ui_element(neon_btn)
        
        bloom_btn = Button(self.engine.width // 2 + 160, 420, 150, 40, "Bloom")
        bloom_btn.set_on_click(lambda: self.quick_test(FilterType.BLOOM))
        self.add_ui_element(bloom_btn)
        
        # Exit button
        exit_btn = Button(self.engine.width // 2, 500, 200, 40, "Exit", 28, root_point=(0.5, 0))
        exit_btn.set_on_click(lambda: setattr(engine, 'running', False))
        self.add_ui_element(exit_btn)
        
        # Info text
        info_text = TextLabel(self.engine.width // 2, 560,
                             "Press SPACE in demo to toggle filters • ESC to return here",
                             16, (150, 200, 255), root_point=(0.5, 0))
        self.add_ui_element(info_text)
    
    def quick_test(self, filter_type: FilterType):
        """Quick test a specific filter."""
        # Switch to demo scene
        self.engine.set_scene("FilterDemo")
        
        # Apply the filter (with a small delay to ensure scene is loaded)
        import threading
        import time
        
        def apply_after_delay():
            time.sleep(0.1)  # Small delay for scene transition
            scene = self.engine.current_scene
            if isinstance(scene, FilterDemoScene):
                scene.apply_quick_filter(filter_type)
        
        thread = threading.Thread(target=apply_after_delay, daemon=True)
        thread.start()
    
    def on_enter(self, previous_scene: Optional[str] = None):
        super().on_enter(previous_scene)
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("Select 'Start Filter Demo' for full controls")
        print("Or try a quick filter test button!")
        print("="*60)
    
    def update(self, dt):
        pass
    
    def render(self, renderer):
        # Draw gradient background
        colors = [(20, 10, 40), (40, 20, 60), (30, 15, 50)]
        height = self.engine.height
        
        for i, color in enumerate(colors):
            segment_height = height // len(colors)
            y = i * segment_height
            renderer.draw_rect(0, y, self.engine.width, segment_height, color, fill=True)
        
        # Draw UI
        for element in self.ui_elements:
            element.render(renderer)


def main():
    """
    Main entry point for the filter system demo.
    
    Creates the engine, registers scenes, and starts the main loop.
    """
    # Initialize engine
    engine = LunaEngine(
        title="LunaEngine - Filter System Demo",
        width=1024,
        height=768,
        fullscreen=False
    )
    
    # Set target FPS
    engine.fps = 60
    
    # Register scenes
    engine.add_scene("MainMenu", MainMenuScene)
    engine.add_scene("FilterDemo", FilterDemoScene)
    
    # Start with main menu
    engine.set_scene("MainMenu")
    
    # Run the engine
    print("\n" + "="*60)
    print("Starting LunaEngine Filter System Demo")
    print("="*60)
    engine.run()


if __name__ == "__main__":
    # Add math import for animation
    import math
    
    # Run the demo
    main()