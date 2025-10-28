import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine import LunaEngine, TextLabel, Button, Slider

class GameScene:
    def __init__(self):
        self.ui_elements = []
        self.counter = 0
        self.click_count = 0
        self.slider_value = 50
        
    def update(self, dt):
        self.counter += dt
            
    def render(self, renderer):
        # Draw background FIRST (before UI elements)
        renderer.draw_rect(0, 0, 800, 600, (30, 30, 50))
        
        # Draw a header
        renderer.draw_rect(0, 0, 800, 40, (50, 50, 80))
        
        # UI elements are rendered by the engine AFTER the scene
        # So they appear on top of the background

def main():
    engine = LunaEngine("LunaEngine Demo - UI System Working!", 800, 600)
    
    scene = GameScene()
    
    def on_button_click():
        scene.click_count += 1
        print(f"Button clicked! Count: {scene.click_count}")
    
    def on_slider_change(value):
        scene.slider_value = value
        print(f"Slider changed to: {value:.1f}")
    
    # Create UI elements with better spacing
    title = TextLabel(20, 50, "Welcome to LunaEngine!", 32, (255, 255, 0))
    scene.ui_elements.append(title)
    
    button = Button(20, 100, 200, 40, "Click Me!")
    button.set_on_click(on_button_click)
    scene.ui_elements.append(button)
    
    slider = Slider(20, 160, 200, 30, 0, 100, 50)
    slider.on_value_changed = on_slider_change
    scene.ui_elements.append(slider)
    
    # Status display
    status_text = TextLabel(20, 210, f"Clicks: {scene.click_count} | Slider: {scene.slider_value:.1f}", 18, (200, 200, 255))
    scene.ui_elements.append(status_text)
    
    # Instructions
    instructions = [
        "Instructions:",
        "- Click the button to increment counter", 
        "- Drag the slider to change value",
        "- Hover over elements to see effects"
    ]
    
    for i, instruction in enumerate(instructions):
        instruction_text = TextLabel(20, 250 + i * 25, instruction, 16, (150, 200, 150))
        scene.ui_elements.append(instruction_text)
    
    # Update status text in real-time
    def update_ui():
        status_text.set_text(f"Clicks: {scene.click_count} | Slider: {scene.slider_value:.1f}")
    
    # Add update function to be called each frame
    original_update = scene.update
    def new_update(dt):
        original_update(dt)
        update_ui()
    
    scene.update = new_update
    
    engine.add_scene("main", scene)
    engine.set_scene("main")
    
    print("Starting LunaEngine...")
    print("Try clicking the button and moving the slider!")
    engine.run()

if __name__ == "__main__":
    main()