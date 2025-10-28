import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine import LunaEngine, TextLabel, Button, Slider, Dropdown

class ComprehensiveDemoScene:
    def __init__(self):
        self.ui_elements = []
        self.click_count = 0
        self.slider_value = 50
        self.selected_option = "Option 1"
        self.counter = 0
        
    def update(self, dt):
        self.counter += dt
            
    def render(self, renderer):
        # Draw gradient background
        for y in range(0, 600, 20):
            color_val = 30 + (y // 600 * 20)
            renderer.draw_rect(0, y, 800, 20, (color_val, color_val, 60))
        
        # Draw header
        renderer.draw_rect(0, 0, 800, 60, (50, 50, 80, 200))

def main():
    engine = LunaEngine("LunaEngine - Comprehensive Demo", 800, 600)
    scene = ComprehensiveDemoScene()
    
    # Callbacks
    def on_button_click():
        scene.click_count += 1
        print(f"Button clicked! Total: {scene.click_count}")
    
    def on_slider_change(value):
        scene.slider_value = value
        print(f"Slider: {value:.1f}")
    
    def on_dropdown_change(index, option):
        scene.selected_option = option
        print(f"Dropdown selected: {option}")
    
    # UI Layout
    
    # Title
    title = TextLabel(20, 20, "LunaEngine UI System", 36, (255, 255, 0))
    scene.ui_elements.append(title)
    
    subtitle = TextLabel(20, 65, "All UI elements working together", 20, (200, 200, 255))
    scene.ui_elements.append(subtitle)
    
    # Button Section
    button_label = TextLabel(50, 120, "Buttons:", 24, (255, 200, 100))
    scene.ui_elements.append(button_label)
    
    button1 = Button(50, 150, 150, 40, "Click Me!")
    button1.set_on_click(on_button_click)
    scene.ui_elements.append(button1)
    
    button2 = Button(220, 150, 150, 40, "Another Button")
    button2.set_on_click(lambda: print("Second button clicked!"))
    scene.ui_elements.append(button2)
    
    # Slider Section  
    slider_label = TextLabel(50, 220, "Sliders:", 24, (100, 255, 200))
    scene.ui_elements.append(slider_label)
    
    slider1 = Slider(50, 250, 200, 30, 0, 100, 25)
    slider1.on_value_changed = on_slider_change
    scene.ui_elements.append(slider1)
    
    slider2 = Slider(50, 300, 200, 30, -50, 50, 0)
    slider2.on_value_changed = lambda v: print(f"Slider 2: {v:.1f}")
    scene.ui_elements.append(slider2)
    
    # Dropdown Section
    dropdown_label = TextLabel(400, 120, "Dropdowns:", 24, (200, 100, 255))
    scene.ui_elements.append(dropdown_label)
    
    dropdown1 = Dropdown(400, 150, 200, 30, 
                       ["Option 1", "Option 2", "Option 3", "Advanced Option", "Final Choice"])
    dropdown1.set_on_selection_changed(on_dropdown_change)
    scene.ui_elements.append(dropdown1)
    
    dropdown2 = Dropdown(400, 200, 200, 30, ["Red", "Green", "Blue", "Yellow", "Purple"])
    dropdown2.set_on_selection_changed(lambda i, o: print(f"Color: {o}"))
    scene.ui_elements.append(dropdown2)
    
    # Status Display
    status_text = TextLabel(50, 350, f"Clicks: {scene.click_count} | Slider: {scene.slider_value:.1f} | Selection: {scene.selected_option}", 
                          18, (255, 255, 255))
    scene.ui_elements.append(status_text)
    
    # Instructions
    instructions = [
        "Instructions:",
        "• Click buttons to increment counter",
        "• Drag sliders to change values", 
        "• Use dropdowns to select options",
        "• Hover over elements for feedback",
        "• Watch console for event output"
    ]
    
    for i, instruction in enumerate(instructions):
        instruction_text = TextLabel(400, 250 + i * 25, instruction, 16, (150, 200, 150))
        scene.ui_elements.append(instruction_text)
    
    # Real-time updates
    def update_ui():
        status_text.set_text(f"Clicks: {scene.click_count} | Slider: {scene.slider_value:.1f} | Selection: {scene.selected_option}")
    
    original_update = scene.update
    def new_update(dt):
        original_update(dt)
        update_ui()
    
    scene.update = new_update
    
    engine.add_scene("main", scene)
    engine.set_scene("main")
    
    print("=== LunaEngine Comprehensive Demo ===")
    print("All UI systems should be working:")
    print("✅ Buttons with click events")
    print("✅ Sliders with value changes") 
    print("✅ Dropdowns with selection")
    print("✅ Real-time status updates")
    print("✅ Hover effects")
    print("✅ Console logging")
    print("\nStarting demo...")
    engine.run()

if __name__ == "__main__":
    main()