import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import TextLabel, Button, Slider, Dropdown

class PerformanceDemoScene(Scene):
    
    def on_enter(self, previous_scene = None):
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.test_count = 100  # Number of test elements
        self.show_test_elements = False

        # Hardware Info Display
        hardware_info = self.engine.get_hardware_info()
        hardware_text = TextLabel(20, 50, f"System: {hardware_info.get('system', 'Unknown')} | CPU: {hardware_info.get('cpu_cores', '?')} cores | RAM: {hardware_info.get('memory_gb', 'Unknown')}", 
                                16, (200, 200, 255))
        self.ui_elements.append(hardware_text)
        
        # FPS Display
        self.ui_elements.append(TextLabel(20, 80, "Performance Statistics:", 24, (255, 255, 0)))
        
        self.fps_current = TextLabel(20, 110, "Current FPS: --", 18, (100, 255, 100))
        self.ui_elements.append(self.fps_current)
        
        self.fps_avg = TextLabel(20, 135, "Average FPS: --", 16, (200, 200, 255))
        self.ui_elements.append(self.fps_avg)
        
        self.fps_lows = TextLabel(20, 155, "1% Low: -- | 0.1% Low: --", 16, (255, 150, 100))
        self.ui_elements.append(self.fps_lows)
        
        self.frame_time = TextLabel(20, 175, "Frame Time: -- ms", 16, (200, 150, 255))
        self.ui_elements.append(self.frame_time)
        
        # Performance Controls
        self.toggle_btn = Button(20, 210, 200, 40, "Toggle Test Elements")
        self.toggle_btn.set_on_click(self.toggle_test_elements)
        self.ui_elements.append(self.toggle_btn)
        
        self.count_slider = Slider(20, 270, 200, 30, 10, 1000, 100)
        self.count_slider.on_value_changed = self.change_test_count
        self.ui_elements.append(self.count_slider)
        
        self.count_text = TextLabel(20, 325, f"Test Elements: {self.test_count}", 16, (150, 200, 150))
        self.ui_elements.append(self.count_text)
        
        # Instructions
        instructions = [
            "Performance Monitoring Features:",
            "• Optimized FPS tracking with minimal overhead",
            "• Hardware detection (Windows/Linux)",
            "• Automatic garbage collection", 
            "• 1% and 0.1% low FPS tracking",
            "• Toggle test elements to see performance impact"
        ]
        
        for i, instruction in enumerate(instructions):
            instruction_text = TextLabel(400, 80 + i * 25, instruction, 16, (150, 200, 150))
            self.ui_elements.append(instruction_text)
        
    def update(self, dt):
        self.update_ui()
        
    def update_ui(self):
        fps_stats = self.engine.get_fps_stats()
        
        self.fps_current.set_text(f"Current FPS: {fps_stats['current_fps']:.1f}")
        self.fps_avg.set_text(f"Average FPS: {fps_stats['average_fps']:.1f}")
        self.fps_lows.set_text(f"1% Low: {fps_stats['percentile_1']:.1f} | 0.1% Low: {fps_stats['percentile_01']:.1f}")
        self.frame_time.set_text(f"Frame Time: {fps_stats['frame_time_ms']:.2f} ms")
        self.count_text.set_text(f"Test Elements: {self.test_count}")
    
    def toggle_test_elements(self):
        self.show_test_elements = not self.show_test_elements
        print(f"Test elements: {'ON' if self.show_test_elements else 'OFF'}")
        
    def change_test_count(self, value):
        self.test_count = int(value)
        print(f"Test elements: {self.test_count}")
        
    def render(self, renderer):
        # Draw background
        renderer.draw_rect(0, 0, 800, 600, (20, 20, 40))
        
        # Draw header
        renderer.draw_rect(0, 0, 800, 40, (40, 40, 60))
        
        # Draw test elements if enabled (for performance testing)
        if self.show_test_elements:
            for i in range(self.test_count):
                x = (i * 10) % 700
                y = 400 + ((i * 15) // 700) * 20
                renderer.draw_rect(x, y, 8, 8, (100, 100, 200))

def main():
    engine = LunaEngine("LunaEngine - Performance Demo", 800, 600, True)
    engine.fps = 240
    
    
    engine.add_scene("main", PerformanceDemoScene)
    engine.set_scene("main")
    
    print("=== Performance Demo ===")
    print("Features:")
    print("✅ Fixed button click handling")
    print("✅ Optimized FPS tracking") 
    print("✅ Hardware detection")
    print("✅ Garbage collection")
    print("✅ Minimal performance overhead")
    print("\nStarting demo...")
    engine.run()

if __name__ == "__main__":
    main()