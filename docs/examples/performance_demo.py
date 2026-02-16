"""
LunaEngine Performance Profiling Demo

This thing isn't working properly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.ui.themes import ThemeManager, ThemeType
from lunaengine.backend import OpenGLRenderer

class PerformanceDemoScene(Scene):
    """
    Performance profiling demonstration scene.
    
    This scene showcases all performance monitoring features of LunaEngine
    with interactive controls to test different performance scenarios.
    """
    
    # =========================================================================
    # LAYOUT CONSTANTS
    # =========================================================================
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    
    # Control Panel
    CONTROL_PANEL_X = 10
    CONTROL_PANEL_Y = 10
    CONTROL_PANEL_WIDTH = 780
    CONTROL_PANEL_HEIGHT = 100
    
    # Stats Panel (left side)
    STATS_PANEL_X = 10
    STATS_PANEL_Y = 120
    STATS_PANEL_WIDTH = 380
    STATS_PANEL_HEIGHT = 450
    
    # Graph Panel (right side)
    GRAPH_PANEL_X = 400
    GRAPH_PANEL_Y = 120
    GRAPH_PANEL_WIDTH = 390
    GRAPH_PANEL_HEIGHT = 450
    
    # Graph Area within Graph Panel
    GRAPH_AREA_X = 10
    GRAPH_AREA_Y = 110
    GRAPH_AREA_WIDTH = 370
    GRAPH_AREA_HEIGHT = 300
    
    # Bar Graph Constants
    BAR_WIDTH = 40
    BAR_SPACING = 20
    
    # =========================================================================
    # SCENE LIFECYCLE
    # =========================================================================
    
    def on_enter(self, previous_scene=None):
        """Called when the scene becomes active."""
        super().on_enter(previous_scene)
        
        print("\n" + "="*60)
        print("LUNAENGINE PERFORMANCE PROFILING DEMO")
        print("="*60)
        print("FEATURES:")
        print("  ✓ Real-time FPS tracking with 1% and 0.1% lows")
        print("  ✓ Update time breakdown (scene, UI, animations, events)")
        print("  ✓ Render time breakdown (UI, particles, notifications)")
        print("  ✓ Individual UI element profiling")
        print("  ✓ Hardware information display")
        print("  ✓ Performance graph visualization")
        print("  ✓ Bottleneck detection")
        print("  ✓ Frame time history tracking")
        print("\nCONTROLS:")
        print("  • Toggle profiling on/off")
        print("  • Enable individual UI element profiling")
        print("  • Adjust test element count (10-2000)")
        print("  • Toggle test elements rendering")
        print("  • Toggle complex UI elements")
        print("="*60)
        print("\nStarting demo...")
    
    def on_exit(self, next_scene=None):
        """Called when the scene is being replaced."""
        print("\nPerformance demo exiting...")
        return super().on_exit(next_scene)
    
    def __init__(self, engine: LunaEngine):
        """Initialize the performance demo scene."""
        super().__init__(engine)
        
        # Performance tracking settings
        self.test_count = 100
        self.show_test_elements = False
        self.show_complex_elements = False
        self.profiling_enabled = True
        self.individual_ui_profiling = False
        
        # Performance data storage
        self.performance_data = {}
        self.frame_time_history = []
        self.history_size = 60  # 1 second at 60 FPS
        
        # Performance display elements
        self.fps_display = None
        self.update_displays = {}
        
        # Complex elements for testing
        self.complex_elements = []
        
        # Setup all UI components
        self.setup_control_panel()
        self.setup_performance_displays()
        self.setup_performance_graph()
        self.setup_hardware_info()
        self.setup_instructions()
        
        print("Performance demo initialized successfully!")
    
    # =========================================================================
    # UI SETUP METHODS
    # =========================================================================
    
    def setup_control_panel(self):
        """Setup the main control panel with all interactive controls."""
        # Control Panel Background
        control_panel = UiFrame(
            self.CONTROL_PANEL_X, self.CONTROL_PANEL_Y,
            self.CONTROL_PANEL_WIDTH, self.CONTROL_PANEL_HEIGHT
        )
        control_panel.set_background_color((30, 30, 40, 200))
        control_panel.set_border((80, 80, 100), 1)
        self.ui_elements.append(control_panel)
        
        # Title
        title = TextLabel(
            self.CONTROL_PANEL_X + 20, self.CONTROL_PANEL_Y + 15,
            "Performance Profiling Demo", 24, (255, 255, 0)
        )
        self.ui_elements.append(title)
        
        # Subtitle
        subtitle = TextLabel(
            self.CONTROL_PANEL_X + 20, self.CONTROL_PANEL_Y + 45,
            "Test and analyze LunaEngine performance in real-time", 12, (200, 200, 200)
        )
        self.ui_elements.append(subtitle)
        
        # Row 2: Buttons and Slider
        row2_y = self.CONTROL_PANEL_Y + 70
        
        # Test Elements Toggle Button
        self.toggle_test_btn = Button(
            self.CONTROL_PANEL_X + 440, row2_y,
            150, 30, "Test Elements"
        )
        self.toggle_test_btn.set_on_click(self.toggle_test_elements)
        self.ui_elements.append(self.toggle_test_btn)
        
        # Complex UI Toggle Button
        self.toggle_complex_btn = Button(
            self.CONTROL_PANEL_X + 600, row2_y,
            150, 30, "Complex UI"
        )
        self.toggle_complex_btn.set_on_click(self.toggle_complex_elements)
        self.ui_elements.append(self.toggle_complex_btn)
        
        # Element Count Control
        slider_x = self.CONTROL_PANEL_X + 20
        slider_y = self.CONTROL_PANEL_Y + 70
        
        # Slider Label
        slider_label = TextLabel(
            slider_x, slider_y - 20,
            "Element Count:", 12, (200, 200, 200)
        )
        self.ui_elements.append(slider_label)
        
        # Element Count Slider
        self.count_slider = Slider(
            slider_x, slider_y,
            180, 20, 10, 2000, self.test_count
        )
        self.count_slider.on_value_changed = self.change_test_count
        self.ui_elements.append(self.count_slider)
        
        # Element Count Display
        self.count_display = TextLabel(
            slider_x + 190, slider_y,
            f"{self.test_count} elements", 12, (150, 200, 150)
        )
        self.ui_elements.append(self.count_display)
    
    def setup_performance_displays(self):
        """Setup the performance statistics display area."""
        # Stats Panel Background
        stats_panel = UiFrame(
            self.STATS_PANEL_X, self.STATS_PANEL_Y,
            self.STATS_PANEL_WIDTH, self.STATS_PANEL_HEIGHT
        )
        stats_panel.set_background_color((30, 30, 40, 200))
        stats_panel.set_border((80, 80, 100), 1)
        self.ui_elements.append(stats_panel)
        
        # Panel Title
        panel_title = TextLabel(
            self.STATS_PANEL_X + 10, self.STATS_PANEL_Y + 10,
            "Performance Metrics", 20, (255, 255, 0)
        )
        self.ui_elements.append(panel_title)
        
        # Create all performance displays
        self.create_fps_displays()
        self.create_displays()
        
    
    def create_fps_displays(self):
        """Create FPS statistics displays."""
        y = self.STATS_PANEL_Y + 40
        spacing = 20
        
        # FPS Section Title
        fps_title = TextLabel(
            self.STATS_PANEL_X + 20, y,
            "Frame Rate", 16, (100, 200, 255)
        )
        self.ui_elements.append(fps_title)
        y += 25
        
        # Current FPS
        self.fps_current = TextLabel(
            self.STATS_PANEL_X + 30, y,
            "Current: --", 14, (100, 255, 100)
        )
        self.ui_elements.append(self.fps_current)
        y += spacing
        
        # Average FPS
        self.fps_avg = TextLabel(
            self.STATS_PANEL_X + 30, y,
            "Average: --", 14, (200, 200, 255)
        )
        self.ui_elements.append(self.fps_avg)
        y += spacing
        
        # 1% and 0.1% Lows
        self.fps_lows = TextLabel(
            self.STATS_PANEL_X + 30, y,
            "1% Low: -- | 0.1% Low: --", 14, (255, 150, 100)
        )
        self.ui_elements.append(self.fps_lows)
        y += spacing
        
        # Frame Time
        self.frame_time = TextLabel(
            self.STATS_PANEL_X + 30, y,
            "Frame Time: -- ms", 14, (200, 150, 255)
        )
        self.ui_elements.append(self.frame_time)
        y += spacing + 10
    
    def create_displays(self):
        """Create update timing displays (only for categories that exist)."""
        y = self.STATS_PANEL_Y + 160

        # Update Section Title
        update_title = TextLabel(
            self.STATS_PANEL_X + 20, y,
            "Update Times (ms)", 16, (100, 200, 255)
        )
        self.ui_elements.append(update_title)
        y += 25

        # Important categories we want to show
        categories_to_show = ["scene", "ui", "ui_total", "notifications", "particles", "frame"]
        for cat in categories_to_show:
            label = TextLabel(
                self.STATS_PANEL_X + 30, y,
                f"{cat.capitalize()}: --", 14, (200, 200, 255)
            )
            self.ui_elements.append(label)
            self.update_displays[cat] = label
            y += 18
    
    def setup_performance_graph(self):
        """Setup the performance graph panel."""
        # Graph Panel Background
        graph_panel = UiFrame(
            self.GRAPH_PANEL_X, self.GRAPH_PANEL_Y,
            self.GRAPH_PANEL_WIDTH, self.GRAPH_PANEL_HEIGHT
        )
        graph_panel.set_background_color((30, 30, 40, 200))
        graph_panel.set_border((80, 80, 100), 1)
        self.ui_elements.append(graph_panel)
        
        # Panel Title
        graph_title = TextLabel(
            self.GRAPH_PANEL_X + 10, self.GRAPH_PANEL_Y + 10,
            "Performance Visualization", 20, (255, 255, 0)
        )
        self.ui_elements.append(graph_title)
        
        # Graph Info
        info_y = self.GRAPH_PANEL_Y + 40
        info_lines = [
            ("Frame Time History (ms)", 14, (200, 200, 255)),
            ("Green: <16.7ms (60+ FPS)", 12, (100, 255, 100)),
            ("Yellow: <33.3ms (30-60 FPS)", 12, (255, 255, 100)),
            ("Red: >33.3ms (<30 FPS)", 12, (255, 100, 100))
        ]
        
        for text, size, color in info_lines:
            label = TextLabel(
                self.GRAPH_PANEL_X + 20, info_y,
                text, size, color
            )
            self.ui_elements.append(label)
            info_y += 18
        
        # Graph Area Background
        graph_area = UiFrame(
            self.GRAPH_PANEL_X + self.GRAPH_AREA_X,
            self.GRAPH_PANEL_Y + self.GRAPH_AREA_Y,
            self.GRAPH_AREA_WIDTH,
            self.GRAPH_AREA_HEIGHT
        )
        graph_area.set_background_color((20, 20, 30))
        graph_area.set_border((50, 50, 60), 1)
        self.ui_elements.append(graph_area)
        
        # Bottleneck Display
        self.bottleneck_display = TextLabel(
            self.GRAPH_PANEL_X + 20, self.GRAPH_PANEL_Y + self.GRAPH_PANEL_HEIGHT - 40,
            "Main Bottleneck: Analyzing...", 14, (255, 150, 100)
        )
        self.ui_elements.append(self.bottleneck_display)
        
        # Performance Summary
        self.performance_summary = TextLabel(
            self.GRAPH_PANEL_X + 20, self.GRAPH_PANEL_Y + self.GRAPH_PANEL_HEIGHT - 60,
            "Profiling: Enabled | Individual UI: Disabled", 12, (200, 200, 255)
        )
        self.ui_elements.append(self.performance_summary)
    
    def setup_hardware_info(self):
        """Display hardware information."""
        hardware_info = self.engine.get_hardware_info()
        
        # Format hardware info
        system_info = f"💻 {hardware_info.get('system', 'Unknown')} {hardware_info.get('release', '')}"
        cpu_info = f"⚡ CPU: {hardware_info.get('cpu_cores', '?')} cores @ {hardware_info.get('cpu_freq', '?')}"
        ram_info = f"🧠 RAM: {hardware_info.get('memory_total_gb', 'Unknown')}"
        
        # Create hardware info display
        hardware_text = TextLabel(
            self.STATS_PANEL_X, self.STATS_PANEL_Y + self.STATS_PANEL_HEIGHT + 5,
            f"{system_info} | {cpu_info} | {ram_info}", 
            11, (180, 180, 220)
        )
        self.ui_elements.append(hardware_text)
    
    def setup_instructions(self):
        """Setup instructions panel."""
        instructions = [
            "🎯 PERFORMANCE TESTING INSTRUCTIONS:",
            "1. Toggle profiling to enable/disable performance tracking",
            "2. Enable individual UI profiling to see per-element stats",
            "3. Adjust element count to test rendering performance",
            "4. Toggle test elements to see basic shape rendering impact",
            "5. Toggle complex UI to test interactive UI performance",
            "",
            "INTERPRETING RESULTS:",
            "• Frame time < 16.7ms = 60+ FPS (Good)",
            "• Frame time < 33.3ms = 30-60 FPS (Acceptable)",
            "• Frame time > 33.3ms = <30 FPS (Needs Optimization)",
            "",
            "💡 TIP: Watch for bottleneck detection to identify performance issues"
        ]
        
        start_y = self.GRAPH_PANEL_Y + self.GRAPH_PANEL_HEIGHT + 10
        
        for i, instruction in enumerate(instructions):
            color = (255, 255, 200) if i == 0 else (150, 200, 150)
            size = 12 if i == 0 else 10
            
            instruction_text = TextLabel(
                self.GRAPH_PANEL_X, start_y + i * 14,
                instruction, size, color
            )
            self.ui_elements.append(instruction_text)
    
    # =========================================================================
    # UPDATE METHODS
    # =========================================================================
    
    def update(self, dt):
        """Update scene logic."""
        self.update_performance_ui()
        self.update_performance_data()
        
        # Update frame time history
        fps_stats = self.engine.get_fps_stats()
        frame_time_ms = fps_stats.get('frame_time_ms', 0)
        self.frame_time_history.append(frame_time_ms)
        
        if len(self.frame_time_history) > self.history_size:
            self.frame_time_history.pop(0)
    
    def update_performance_ui(self):
        """Update UI elements with current performance data."""
        # Get FPS stats
        fps_stats = self.engine.get_fps_stats()
        
        # Update FPS displays
        self.fps_current.set_text(f"Current: {fps_stats['current_fps']:.1f}")
        self.fps_avg.set_text(f"Average: {fps_stats['average_fps']:.1f}")
        self.fps_lows.set_text(f"1% Low: {fps_stats['percentile_1']:.1f} | 0.1% Low: {fps_stats['percentile_01']:.1f}")
        self.frame_time.set_text(f"Frame Time: {fps_stats['frame_time_ms']:.2f} ms")
        
        # Update element count display
        test_status = "ON" if self.show_test_elements else "OFF"
        complex_status = "ON" if self.show_complex_elements else "OFF"
        self.count_display.set_text(f"{self.test_count} elements | Test: {test_status} | Complex: {complex_status}")
        
        # Update performance summary
        profiling_status = "Enabled" if self.profiling_enabled else "Disabled"
        ui_profiling_status = "Enabled" if self.individual_ui_profiling else "Disabled"
        self.performance_summary.set_text(f"Profiling: {profiling_status} | Individual UI: {ui_profiling_status}")
    
    def update_performance_data(self):
        """Update performance timing data displays."""
        if not self.profiling_enabled:
            self.clear_performance_displays()
            return

        try:
            # Get the timing breakdown from the LAST completed frame
            timings = self.engine.get_frame_timing_breakdown()
            self.update_timing_displays(timings)

            # Also get full stats for bottleneck detection
            perf_stats = self.engine.get_performance_stats()
            self.detect_bottleneck(perf_stats)

        except Exception as e:
            print(f"⚠️ Error updating performance data: {e}")
    
    def update_timing_displays(self, timings: dict[str, float]):
        """Update all timing labels with the given dict of category->ms."""
        for category, label in self.update_displays.items():
            duration = timings.get(category, 0.0)
            label.set_text(f"{category.capitalize()}: {duration:.2f} ms")
    
    def clear_performance_displays(self):
        """Clear all performance displays when profiling is disabled."""
        for display in list(self.update_displays.values()):
            display.set_text(f"{display.text.split(':')[0]}: --")
        
        self.bottleneck_display.set_text("Main Bottleneck: Profiling Disabled")
        self.bottleneck_display.color = (150, 150, 150)
    
    def detect_bottleneck(self, perf_stats):
        """Detect and display the main performance bottleneck."""
        # Use the frame timings from perf_stats (added in engine fix)
        timings = perf_stats.get("frame_timings", {})
        if not timings:
            self.bottleneck_display.set_text("Main Bottleneck: No data")
            return

        # Find slowest category
        slowest_cat = max(timings, key=timings.get)
        slowest_time = timings[slowest_cat]
        total_frame = perf_stats.get("frame_time_ms", 0)

        # Color coding
        if total_frame > 33.3:
            color = (255, 100, 100)
        elif total_frame > 16.7:
            color = (255, 255, 100)
        else:
            color = (100, 255, 100)

        self.bottleneck_display.set_text(
            f"Main Bottleneck: {slowest_cat} ({slowest_time:.1f} ms)"
        )
        self.bottleneck_display.color = color
    
    # =========================================================================
    # RENDERING METHODS
    # =========================================================================
    
    def render(self, renderer):
        """Render the scene."""
        # Draw background
        renderer.draw_rect(0, 0, self.WINDOW_WIDTH, self.WINDOW_HEIGHT, (15, 15, 25))
        
        # Draw header gradient
        renderer.draw_rect(0, 0, self.WINDOW_WIDTH, 120, (25, 25, 35))
        renderer.draw_rect(0, 100, self.WINDOW_WIDTH, 20, (30, 30, 40, 150))
        
        # Draw test elements if enabled
        if self.show_test_elements:
            self.draw_test_elements(renderer)
        
        # Draw complex UI elements if enabled
        if self.show_complex_elements:
            for element in self.complex_elements:
                element.render(renderer)
        
        # Draw performance graph
        self.draw_performance_graph(renderer)
    
    def draw_test_elements(self, renderer):
        """Draw test elements for performance testing."""
        for i in range(self.test_count):
            # Calculate position in a grid
            cols = 35  # Number of columns in the grid
            row = i // cols
            col = i % cols
            
            x = 50 + col * 20
            y = 120 + row * 20
            
            # Skip if outside visible area
            if y > 500:
                continue
            
            # Vary colors and sizes
            size = 8 + (i % 7)
            hue = (i * 137) % 360  # Golden ratio for distribution
            r = min(255, int(150 + 100 * (hue / 360)))
            g = min(255, int(150 + 100 * ((hue + 120) % 360) / 360))
            b = min(255, int(150 + 100 * ((hue + 240) % 360) / 360))
            
            # Draw element
            renderer.draw_rect(x, y, size, size, (r, g, b))
            
            # Add some variety
            if i % 4 == 0:
                renderer.draw_circle(x + size/2, y + size/2, size/2, (r, g, b, 180))
            elif i % 7 == 0:
                renderer.draw_circle(x + size/2, y + size/2, size/2, (r, g, b, 120), fill=False)
    
    def draw_performance_graph(self, renderer: OpenGLRenderer):
        """Draw the performance graph visualization."""
        if not self.frame_time_history:
            return
        
        # Graph area coordinates
        graph_x = self.GRAPH_PANEL_X + self.GRAPH_AREA_X
        graph_y = self.GRAPH_PANEL_Y + self.GRAPH_AREA_Y
        graph_width = self.GRAPH_AREA_WIDTH
        graph_height = self.GRAPH_AREA_HEIGHT
        
        # Draw graph background
        renderer.draw_rect(graph_x, graph_y, graph_width, graph_height, (20, 20, 30, 200))
        
        # Draw grid
        self.draw_graph_grid(renderer, graph_x, graph_y, graph_width, graph_height)
        
        # Draw FPS thresholds
        self.draw_fps_thresholds(renderer, graph_x, graph_y, graph_width, graph_height)
        
        # Draw frame time line graph
        self.draw_frame_time_graph(renderer, graph_x, graph_y, graph_width, graph_height)
        
        # Draw current frame time indicator
        if self.performance_data:
            self.draw_current_frame_indicator(renderer, graph_x, graph_y, graph_width, graph_height)
    
    def draw_graph_grid(self, renderer, x, y, width, height):
        """Draw graph grid lines."""
        grid_color = (40, 40, 50)
        
        # Vertical grid lines
        for i in range(0, 6):
            x_pos = x + (i * width / 5)
            renderer.draw_line(x_pos, y, x_pos, y + height, grid_color, 1)
        
        # Horizontal grid lines (every 10ms)
        max_time = 60.0
        for time_ms in [10, 20, 30, 40, 50, 60]:
            y_pos = y + height - (time_ms / max_time) * height
            renderer.draw_line(x, y_pos, x + width, y_pos, grid_color, 1)
    
    def draw_fps_thresholds(self, renderer, x, y, width, height):
        """Draw FPS threshold lines."""
        max_time = 60.0
        
        # 60 FPS line (16.7ms)
        fps60_y = y + height - (16.7 / max_time) * height
        renderer.draw_line(x, fps60_y, x + width, fps60_y, (100, 255, 100, 150), 2)
        
        # 30 FPS line (33.3ms)
        fps30_y = y + height - (33.3 / max_time) * height
        renderer.draw_line(x, fps30_y, x + width, fps30_y, (255, 255, 100, 150), 2)
        
        # Add labels
        renderer.draw_text("60 FPS", x + 5, fps60_y - 15, (100, 255, 100), FontManager.get_font(None, 10))
        renderer.draw_text("30 FPS", x + 5, fps30_y - 15, (255, 255, 100), FontManager.get_font(None, 10))
    
    def draw_frame_time_graph(self, renderer, x, y, width, height):
        """Draw line graph of frame time history."""
        if len(self.frame_time_history) < 2:
            return
        
        max_time = max(max(self.frame_time_history), 60.0)
        
        # Draw line segments
        for i in range(len(self.frame_time_history) - 1):
            x1 = x + (i / (len(self.frame_time_history) - 1)) * width
            y1 = y + height - (self.frame_time_history[i] / max_time) * height
            
            x2 = x + ((i + 1) / (len(self.frame_time_history) - 1)) * width
            y2 = y + height - (self.frame_time_history[i + 1] / max_time) * height
            
            # Color based on frame time
            avg_time = (self.frame_time_history[i] + self.frame_time_history[i + 1]) / 2
            if avg_time <= 16.7:
                color = (100, 255, 100)  # Green
            elif avg_time <= 33.3:
                color = (255, 255, 100)  # Yellow
            else:
                color = (255, 100, 100)  # Red
            
            renderer.draw_line(x1, y1, x2, y2, color, 2)
    
    def draw_current_frame_indicator(self, renderer, x, y, width, height):
        """Draw indicator for current frame time."""
        if not self.performance_data:
            return
        
        frame_time = self.performance_data.get('frame_time', 0)
        max_time = 60.0
        
        y_pos = y + height - (frame_time / max_time) * height
        
        # Draw indicator line
        renderer.draw_line(x, y_pos, x + width, y_pos, (255, 255, 255, 100), 1)
        
        # Draw value label
        if frame_time > 0:
            label_x = x + width - 80
            label_y = y_pos - 20 if y_pos > y + 30 else y_pos + 10
            
            color = (255, 255, 255)
            if frame_time > 33.3:
                color = (255, 100, 100)
            elif frame_time > 16.7:
                color = (255, 255, 100)
            else:
                color = (100, 255, 100)
            
            renderer.draw_text(f"{frame_time:.1f} ms", label_x, label_y, color, FontManager.get_font(None, 10))
    
    # =========================================================================
    # CONTROL METHODS
    # =========================================================================
    
    def toggle_profiling(self, enabled):
        """Toggle performance profiling on/off."""
        self.profiling_enabled = enabled
        self.engine.enable_performance_profiling(enabled)
        
        print(f"Performance profiling: {'ENABLED' if enabled else 'DISABLED'}")
        
        # Update UI profiling toggle state
        self.ui_profiling_toggle.checked = enabled and self.individual_ui_profiling
        self.ui_profiling_toggle.enabled = enabled
        
        if not enabled:
            self.clear_performance_displays()

    
    def toggle_test_elements(self):
        """Toggle test element rendering."""
        self.show_test_elements = not self.show_test_elements
        
        status = "ENABLED" if self.show_test_elements else "DISABLED"
        print(f"Test elements: {status} ({self.test_count} elements)")
        
        # Clear complex elements when disabling test elements
        if not self.show_test_elements:
            self.show_complex_elements = False
            self.clear_complex_elements()
    
    def toggle_complex_elements(self):
        """Toggle complex UI elements."""
        self.show_complex_elements = not self.show_complex_elements
        
        if self.show_complex_elements:
            self.create_complex_elements()
            print(f"🏗️ Complex UI elements: ENABLED ({len(self.complex_elements)} elements)")
        else:
            self.clear_complex_elements()
            print(f"🏗️ Complex UI elements: DISABLED")
    
    def create_complex_elements(self):
        """Create complex UI elements for performance testing."""
        self.clear_complex_elements()
        
        # Calculate grid dimensions
        cols = 8
        rows = min(6, (self.test_count + cols - 1) // cols)
        
        for i in range(min(self.test_count, cols * rows)):
            row = i // cols
            col = i % cols
            
            x = 50 + col * 90
            y = 120 + row * 70
            
            # Create a complex container with multiple children
            container = UiFrame(x, y, 80, 60)
            container.set_background_color((40, 40, 60, 200))
            container.set_border((80, 80, 100), 2)
            container.set_corner_radius(8)
            
            # Add child elements
            label = TextLabel(5, 5, f"#{i+1:03d}", 10, (200, 200, 200))
            container.add_child(label)
            
            # Add a mini progress bar
            progress = 0.3 + (i % 7) * 0.1
            progress_bar = UiFrame(10, 30, 60, 8)
            progress_bar.set_background_color((60, 60, 80))
            progress_bar.set_corner_radius(4)
            
            progress_fill = UiFrame(10, 30, int(60 * progress), 8)
            progress_fill.set_background_color((100, 150, 255))
            progress_fill.set_corner_radius(4)
            
            container.add_child(progress_bar)
            container.add_child(progress_fill)
            
            # Add hover effect
            original_color = container.background_color
            
            def make_hover_handler(cont, orig_color):
                def on_hover():
                    cont.set_background_color((60, 60, 80, 200))
                    cont.set_border((100, 100, 120), 2)
                
                def on_leave():
                    cont.set_background_color(orig_color)
                    cont.set_border((80, 80, 100), 2)
                
                return on_hover, on_leave
            
            hover_handler, leave_handler = make_hover_handler(container, original_color)
            container.on_hover = hover_handler
            container.on_hover_leave = leave_handler
            
            self.complex_elements.append(container)
    
    def clear_complex_elements(self):
        """Clear all complex UI elements."""
        self.complex_elements.clear()
    
    def change_test_count(self, value):
        """Change the number of test elements."""
        self.test_count = int(value)
        print(f"📦 Test elements count: {self.test_count}")
        
        # Update complex elements if they're visible
        if self.show_complex_elements:
            self.create_complex_elements()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for the performance profiling demo."""
    print("\n" + "="*60)
    print("🚀 LUNAENGINE PERFORMANCE PROFILING DEMO")
    print("="*60)
    print("Initializing engine with performance monitoring...")
    
    # Create engine with performance profiling enabled
    engine = LunaEngine(
        title="LunaEngine - Performance Profiling Demo",
        width=800,
        height=600,
        enable_performance_profiling=True,
        profile_individual_ui_elements=False
    )
    
    # Set high FPS for accurate performance measurements
    engine.fps = 240
    
    # Add and set the performance demo scene
    engine.add_scene("performance_demo", PerformanceDemoScene)
    engine.set_scene("performance_demo")
    
    print("\n✅ Engine initialized successfully!")
    print("Performance profiling is ACTIVE")
    print("🎮 Use the UI controls to test different scenarios")
    print("⏱️  Watch the performance metrics update in real-time")
    print("="*60)
    print("\nStarting main loop...")
    
    # Run the engine
    try:
        engine.run()
        print("\n👋 Performance demo completed successfully!")
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*60)


if __name__ == "__main__":
    main()