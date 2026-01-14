"""
Particle System Demo - Fixed Version
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pygame
from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import *
from lunaengine.graphics.particles import *
from lunaengine.graphics.camera import Camera, CameraMode

class ParticleDemoScene(Scene):
    """Interactive particle system demo scene"""
    
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def on_enter(self, previous_scene: str = None):
        return super().on_enter(previous_scene)
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.demo_state = {
            'active_particles': 0,
            'fps': 0,
            'memory_usage': 0,
            'emission_rate': 50,
            'selected_particle': "dust",  # Uses string
            'selected_exit': "top",
            'selected_physics': "topdown", 
            'spread': 45.0,
            'auto_emit': True,
            'show_metrics': True,
        }
        self.emitter_positions = [
            (-200, -200), (-200, 200), (0, 50), (200, -200), (200, 200)
        ]
        self.setup_ui()
        
        # Register some custom particles
        self.setup_custom_particles()
        
        self.particle_system.get_physics_names()
        
    def setup_custom_particles(self):
        """Setup custom particle types for testing"""
        # Magic particles
        magic_config = ParticleConfig(
            color_start=(200, 0, 255),
            color_end=(100, 0, 200),
            size_start=6.0,
            size_end=10.0,
            lifetime=2.0,
            speed=120.0,
            gravity=-80.0,
            spread=90.0,
            fade_out=True,
            grow=True
        )
        self.particle_system.register_custom_particle("magic", magic_config)
        
        # Electric sparks
        electric_config = ParticleConfig(
            color_start=(0, 200, 255),
            color_end=(0, 100, 255),
            size_start=3.0,
            size_end=1.0,
            lifetime=0.8,
            speed=250.0,
            gravity=50.0,
            spread=15.0,
            fade_out=True
        )
        self.particle_system.register_custom_particle("electric", electric_config)

    def setup_ui(self):
        """Setup all UI controls and displays"""
        self.camera.mode = CameraMode.FIXED
        print(self.camera.viewport_width, self.camera.viewport_height)
        
        print(self.camera.world_to_screen((0,0)))
        print(self.camera.screen_to_world((0,0)))
        
        # Title
        title = TextLabel(512, 20, "LunaEngine - Particle System Demo", 32, root_point=(0.5, 0))
        self.add_ui_element(title)
        
        # FPS and Performance Display
        self.fps_display = TextLabel(20, 20, "FPS: --", 18, (100, 255, 100))
        self.add_ui_element(self.fps_display)
        
        self.particle_count_display = TextLabel(20, 45, "Particles: 0", 16, (200, 200, 255))
        self.add_ui_element(self.particle_count_display)
        
        self.memory_display = TextLabel(20, 70, "Memory: 0.0 MB", 16, (255, 200, 100))
        self.add_ui_element(self.memory_display)
        
        # Section 1: Particle Type Selection
        section1_title = TextLabel(20, 110, "Particle Type", 20, (255, 255, 0))
        self.add_ui_element(section1_title)
        
        # Particle type selector
        self.particle_dropdown = Dropdown(20, 140, 150, 30, self.particle_system.get_particles_names(True,True))
        self.particle_dropdown.set_on_selection_changed(
            lambda i, v: self.update_state('selected_particle', v)
        )
        self.add_ui_element(self.particle_dropdown)
        
        # Section 2: Emission Controls
        section2_title = TextLabel(20, 190, "Emission Controls", 20, (255, 255, 0))
        self.add_ui_element(section2_title)
        
        # Emission rate slider
        emission_label = TextLabel(20, 220, "Emission Rate:", 16)
        self.add_ui_element(emission_label)
        
        self.emission_slider = Slider(20, 240, 150, 20, 1, 500, 50)
        self.emission_slider.on_value_changed = lambda v: self.update_state('emission_rate', int(v))
        self.add_ui_element(self.emission_slider)
        
        self.emission_display = TextLabel(180, 240, "50 p/s", 14)
        self.add_ui_element(self.emission_display)
        
        # Spread control
        spread_label = TextLabel(20, 270, "Spread Angle:", 16)
        self.add_ui_element(spread_label)
        
        self.spread_slider = Slider(20, 290, 150, 20, 0, 360, 45)
        self.spread_slider.on_value_changed = lambda v: self.update_state('spread', v)
        self.add_ui_element(self.spread_slider)
        
        self.spread_display = TextLabel(180, 290, "45°", 14)
        self.add_ui_element(self.spread_display)
        
        # Section 3: Physics and Exit Points
        section3_title = TextLabel(20, 330, "Physics & Emission", 20, (255, 255, 0))
        self.add_ui_element(section3_title)
        
        exit_points = ["top", "bottom", "left", "right", "center", "circular"]
        self.exit_dropdown = Dropdown(20, 360, 150, 30, exit_points)
        self.exit_dropdown.set_on_selection_changed(
            lambda i, v: self.update_state('selected_exit', v)
        )
        self.add_ui_element(self.exit_dropdown)
        
        # Physics type selector
        self.physics_dropdown = Dropdown(20, 400, 150, 30, self.particle_system.get_physics_names(True, True))
        self.physics_dropdown.set_on_selection_changed(
            lambda i, v: self.update_state('selected_physics', v)
        )
        self.add_ui_element(self.physics_dropdown)
        
        # Section 4: Controls
        section4_title = TextLabel(20, 450, "Controls", 20, (255, 255, 0))
        self.add_ui_element(section4_title)
        
        # Auto emission toggle
        self.auto_emit_switch = Switch(20, 480, 60, 30, True)
        self.auto_emit_switch.set_on_toggle(lambda s: self.update_state('auto_emit', s))
        self.add_ui_element(self.auto_emit_switch)
        
        auto_emit_label = TextLabel(90, 485, "Auto Emission", 16)
        self.add_ui_element(auto_emit_label)
        
        # Burst mode button
        burst_button = Button(20, 520, 120, 30, "Burst Emission")
        burst_button.set_on_click(lambda: self.emit_burst())
        self.add_ui_element(burst_button)
        
        # Clear particles button
        clear_button = Button(150, 520, 120, 30, "Clear All")
        clear_button.set_on_click(lambda: self.particle_system.clear())
        self.add_ui_element(clear_button)
        
        # Manual emit button
        manual_button = Button(20, 560, 250, 30, "Click Here to Emit Manually")
        manual_button.set_on_click(lambda: self.emit_manual())
        self.add_ui_element(manual_button)

    def update_state(self, key, value):
        """Update demo state and refresh displays"""
        if key in ['particle_type', 'physics_type']: value = str(value).lower()
        self.demo_state[key] = value
        print(f"Updated {key} to {value}")  # DEBUG
        
        # Update UI displays
        self.emission_display.set_text(f"{self.demo_state['emission_rate']} p/s")
        self.spread_display.set_text(f"{self.demo_state['spread']:.0f}°")

    def emit_manual(self):
        """Emit particles manually from center"""
        particle_type = ParticleType[self.demo_state['selected_particle'].upper()]
        exit_point = ExitPoint[self.demo_state['selected_exit'].upper()]
        physics_type = PhysicsType[self.demo_state['selected_physics'].upper()]
        
        # Emit at world center (0,0)
        px,py = 0, 0
        print(self.camera.world_to_screen((px, py)))
        
        self.particle_system.emit(
            x=px, y=py,
            particle_type=particle_type,
            count=100,
            exit_point=exit_point,
            physics_type=physics_type,
            spread=self.demo_state['spread']
        )
        print(f"Emitted 100 {self.demo_state['selected_particle']} particles")

    def emit_burst(self):
        """Emit a burst of particles from all emitter positions"""
        particle_type = ParticleType[self.demo_state['selected_particle'].upper()]
        exit_point = ExitPoint[self.demo_state['selected_exit'].upper()]
        physics_type = PhysicsType[self.demo_state['selected_physics'].upper()]
        
        for x, y in self.emitter_positions:
            self.particle_system.emit(
                x=x, y=y,
                particle_type=particle_type,
                count=50,
                exit_point=exit_point,
                physics_type=physics_type,
                spread=self.demo_state['spread']
            )
        print(f"Emitted burst of {self.demo_state['selected_particle']} particles")

    def on_enter(self, previous_scene: str = None):
        """Called when scene becomes active"""
        print("=== Particle System Demo ===")
        print("Controls:")
        print("- Use dropdowns to select particle type, exit point, and physics")
        print("- Adjust sliders for emission rate and spread")
        print("- Click buttons to emit particles")
        print("- Toggle auto-emission on/off")

    def update(self, dt):
        """Update scene logic"""
        # Update particle system
        self.particle_system.update(dt)
        
        # Auto emission from fixed positions
        if self.demo_state['auto_emit']:
            particle_type = ParticleType[self.demo_state['selected_particle'].upper()]
            exit_point = ExitPoint[self.demo_state['selected_exit'].upper()]
            physics_type = PhysicsType[self.demo_state['selected_physics'].upper()]
            for x, y in self.emitter_positions:
                # print(f'X: {x} > {pos_x}, Y: {y} > {pos_y}')
                self.particle_system.emit(
                    x=x, y=y,
                    particle_type=particle_type,
                    count=int(self.demo_state['emission_rate'] * dt),
                    exit_point=exit_point,
                    physics_type=physics_type,
                    spread=self.demo_state['spread']
                )
        
        # Update performance displays
        stats = self.particle_system.get_stats()
        fps_stats = self.engine.get_fps_stats()
        
        self.demo_state['active_particles'] = stats['active_particles']
        self.demo_state['fps'] = fps_stats['current_fps']
        self.demo_state['memory_usage'] = stats['memory_usage_mb']
        
        # Update UI displays
        self.fps_display.set_text(f"FPS: {self.demo_state['fps']:.1f}")
        self.particle_count_display.set_text(f"Particles: {self.demo_state['active_particles']}")
        self.memory_display.set_text(f"Memory: {self.demo_state['memory_usage']:.2f} MB")

    def render(self, renderer):
        """Render scene"""
        # Draw background
        renderer.draw_rect(0, 0, 1024, 768, (20, 20, 30))
        
        # Draw emitter position markers (in world coordinates, so convert to screen)
        for x, y in self.emitter_positions:
            screen_pos = self.camera.world_to_screen((x,y))
            renderer.draw_rect(screen_pos.x-2, screen_pos.y-2, 4, 4, (255, 255, 255))
            renderer.draw_rect(screen_pos.x-1, screen_pos.y-1, 2, 2, (100, 200, 255))
        
        # Draw center marker (world (0,0) is the center)
        center_screen = self.camera.world_to_screen((0, 0))
        renderer.draw_rect(center_screen.x-2, center_screen.y-2, 4, 4, (255, 255, 0))

def main():
    """Main function"""
    # Test
    engine = LunaEngine("LunaEngine - Particle System Demo", 1024, 768)
    engine.fps = 144
    
    @engine.on_event(pygame.KEYDOWN)
    def handle_keydown(event):
        if event.key == pygame.K_r:
            print("Resetting particle system...")
            engine.scenes["main"].particle_system.clear()
        elif event.key == pygame.K_SPACE:
            engine.scenes["main"].emit_manual()
    
    engine.add_scene("main", ParticleDemoScene)
    engine.set_scene("main")
    engine.run()

if __name__ == "__main__":
    main()