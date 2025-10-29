import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine import LunaEngine
from lunaengine.ui import TextLabel, Button, Slider, Dropdown

class PerformanceDemoScene:
    def __init__(self):
        self.ui_elements = []
        self.test_count = 100  # Number of test elements
        self.show_test_elements = False
        
    def update(self, dt):
        pass
            
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
    engine = LunaEngine("LunaEngine - Performance Demo", 800, 600)
    engine.fps = 240
    scene = PerformanceDemoScene()
    
    def toggle_test_elements():
        scene.show_test_elements = not scene.show_test_elements
        print(f"Test elements: {'ON' if scene.show_test_elements else 'OFF'}")
    
    def change_test_count(value):
        scene.test_count = int(value)
        print(f"Test elements: {scene.test_count}")
    
    # Hardware Info Display
    hardware_info = engine.get_hardware_info()
    hardware_text = TextLabel(20, 50, f"System: {hardware_info.get('system', 'Unknown')} | CPU: {hardware_info.get('cpu_cores', '?')} cores | RAM: {hardware_info.get('memory_gb', 'Unknown')}", 
                            16, (200, 200, 255))
    scene.ui_elements.append(hardware_text)
    
    # FPS Display
    fps_title = TextLabel(20, 80, "Performance Statistics:", 24, (255, 255, 0))
    scene.ui_elements.append(fps_title)
    
    fps_current = TextLabel(20, 110, "Current FPS: --", 18, (100, 255, 100))
    scene.ui_elements.append(fps_current)
    
    fps_avg = TextLabel(20, 135, "Average FPS: --", 16, (200, 200, 255))
    scene.ui_elements.append(fps_avg)
    
    fps_lows = TextLabel(20, 155, "1% Low: -- | 0.1% Low: --", 16, (255, 150, 100))
    scene.ui_elements.append(fps_lows)
    
    frame_time = TextLabel(20, 175, "Frame Time: -- ms", 16, (200, 150, 255))
    scene.ui_elements.append(frame_time)
    
    # Performance Controls
    toggle_btn = Button(20, 210, 200, 40, "Toggle Test Elements")
    toggle_btn.set_on_click(toggle_test_elements)
    scene.ui_elements.append(toggle_btn)
    
    count_slider = Slider(20, 270, 200, 30, 10, 1000, 100)
    count_slider.on_value_changed = change_test_count
    scene.ui_elements.append(count_slider)
    
    count_text = TextLabel(20, 325, f"Test Elements: {scene.test_count}", 16, (150, 200, 150))
    scene.ui_elements.append(count_text)
    
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
        scene.ui_elements.append(instruction_text)
    
    # Real-time updates
    def update_ui():
        fps_stats = engine.get_fps_stats()
        
        fps_current.set_text(f"Current FPS: {fps_stats['current']:.1f}")
        fps_avg.set_text(f"Average FPS: {fps_stats['average']:.1f}")
        fps_lows.set_text(f"1% Low: {fps_stats['percentile_1']:.1f} | 0.1% Low: {fps_stats['percentile_01']:.1f}")
        frame_time.set_text(f"Frame Time: {fps_stats['frame_time_ms']:.2f} ms")
        count_text.set_text(f"Test Elements: {scene.test_count}")
    
    original_update = scene.update
    def new_update(dt):
        original_update(dt)
        update_ui()
    
    scene.update = new_update
    
    engine.add_scene("main", scene)
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