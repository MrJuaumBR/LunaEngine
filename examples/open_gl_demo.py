# open_gl_demo.py - CORRECTED version
import os
import sys
import pygame
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.graphics.particles import *

class TestScene(Scene):
    def on_enter(self, previous_scene=None):
        print(f"Entering TestScene - OpenGL: {self.engine.use_opengl}")
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene=None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine):
        super().__init__(engine)
        self.particle_system = ParticleSystem(max_particles=1000)
        self.setup_ui()
        self.setup_test_data()
        self.emission_timer = 0
        self.debug_info = "Initialized"
    
    def setup_ui(self):
        """Setup UI elements for testing"""
        # Button to emit particles
        self.emit_button = Button(100, 50, 200, 40, "Emit Particles", 
                                theme=ThemeType.DEFAULT)
        self.emit_button.set_on_click(self.emit_particles)
        self.add_ui_element(self.emit_button)
        
        # Status label
        mode_text = "Mode: OpenGL" if self.engine.use_opengl else "Mode: Pygame"
        self.status_label = TextLabel(100, 100, mode_text, theme=ThemeType.DEFAULT)
        self.add_ui_element(self.status_label)
        
        # FPS label
        self.fps_label = TextLabel(100, 130, "FPS: 0", theme=ThemeType.DEFAULT)
        self.add_ui_element(self.fps_label)
        
        # Debug label
        self.debug_label = TextLabel(100, 160, "Debug: OK", theme=ThemeType.DEFAULT)
        self.add_ui_element(self.debug_label)
    
    def setup_test_data(self):
        """Setup test data for rendering"""
        self.test_objects = [
            {"x": 200, "y": 300, "width": 50, "height": 50, "color": (255, 0, 0)},
            {"x": 400, "y": 200, "width": 30, "height": 70, "color": (0, 255, 0)},
            {"x": 600, "y": 400, "width": 60, "height": 40, "color": (0, 0, 255)},
        ]
    
    def emit_particles(self):
        """Emit particles for testing"""
        self.particle_system.emit(
            x=400, y=300,
            particle_type=ParticleType.FIRE,
            count=50,
            exit_point=ExitPoint.CIRCULAR
        )
    
    def update(self, dt):
        """Update scene - FIXED VERSION"""
        super().update(dt)
        self.particle_system.update(dt)
        
        # Auto-emit particles occasionally
        self.emission_timer += dt
        if self.emission_timer > 1.5:  # Every 1.5 seconds
            self.emit_particles()
            self.emission_timer = 0
        
        # Update status labels
        try:
            fps_stats = self.engine.get_fps_stats()
            fps_value = fps_stats.get('current_fps', 0)
            particle_count = self.particle_system.active_particles
            
            self.status_label.set_text(f"Particles: {particle_count}")
            self.fps_label.set_text(f"FPS: {fps_value:.1f}")
            self.debug_label.set_text(f"Debug: {self.debug_info}")
            
        except Exception as e:
            self.debug_info = f"Update error: {e}"
    
    def render(self, renderer):
        """Render scene - CORRIGIDO"""
        # Clear background
        if not self.engine.use_opengl:
            renderer.get_surface().fill((30, 30, 50))
        
        # Render test objects
        for obj in self.test_objects:
            renderer.draw_rect(
                obj["x"], obj["y"], 
                obj["width"], obj["height"], 
                obj["color"]
            )

def main():
    """Test function to verify both rendering modes"""
    
    # Run interactive test with user choice
    print("\n=== Interactive Test ===")
    print("Choose rendering mode:")
    print("1. Pygame Mode (Software)")
    print("2. OpenGL Mode (Hardware Accelerated)")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            use_opengl = False
        elif choice == "2":
            use_opengl = True
        else:
            print("Invalid choice, defaulting to Pygame Mode")
            use_opengl = False
        
        engine = LunaEngine("Interactive Test", 800, 600, use_opengl=use_opengl)
        engine.add_scene("test", TestScene)
        engine.set_scene("test")
        
        print(f"Running in {'OpenGL' if use_opengl else 'Pygame'} mode...")
        print("Press ESC to exit")
        engine.run()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during interactive test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()