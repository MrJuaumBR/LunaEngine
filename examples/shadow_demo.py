"""
Shadow System Test Demo - LunaEngine
Updated to work with the new data‑only shadow system.
"""

import sys
import os
import math
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pygame
from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import *
from lunaengine.graphics.camera import Camera, CameraMode
from lunaengine.graphics.shadows import ShadowSystem, LightType

class ShadowTestScene(Scene):
    """Simple scene to test the shadow system"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Test objects
        self.test_objects = []
        self.lights = []
        self.shadow_casters = []
        
        # Camera setup
        self.camera.position = pygame.math.Vector2(400, 300)
        self.camera.target_position = pygame.math.Vector2(400, 300)
        self.camera.mode = CameraMode.TOPDOWN
        self.camera.zoom = 1.0
        self.camera.target_zoom = 1.0
        
        # Player for movement
        self.player = {
            'position': [400, 300],
            'velocity': [0, 0],
            'speed': 200,
            'size': 15
        }
        
        # Generate test objects
        self.generate_test_objects()
        
        # Setup UI
        self.setup_ui()
        
        # Debug info
        self.debug_info = {
            'mouse_world_pos': (0, 0),
            'camera_pos': (0, 0),
            'shadow_stats': {}
        }
        
        # Flag to toggle shadows (for demo, we just print)
        self.shadows_enabled = True

    def generate_test_objects(self):
        """Generate test objects for shadow casting"""
        
        # Create some rectangular objects
        rectangles = [
            (100, 100, 80, 40),    # x, y, width, height
            (600, 200, 60, 100),
            (300, 400, 120, 60),
            (200, 500, 70, 70),
            (500, 100, 50, 150)
        ]
        
        for x, y, w, h in rectangles:
            rect_data = {
                'type': 'rectangle',
                'position': [x, y],
                'size': [w, h],
                'color': (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
            }
            self.test_objects.append(rect_data)
            
            # Add as shadow caster using helper
            caster = self.shadow_system.add_rectangle_caster(x, y, w, h)
            self.shadow_casters.append(caster)
        
        # Create some circular objects
        circles = [
            (400, 200, 30),
            (150, 300, 40),
            (550, 350, 25),
            (250, 150, 35)
        ]
        
        for x, y, radius in circles:
            circle_data = {
                'type': 'circle',
                'position': [x, y],
                'radius': radius,
                'color': (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
            }
            self.test_objects.append(circle_data)
            
            # Add as shadow caster using helper
            caster = self.shadow_system.add_circle_caster(x, y, radius)
            self.shadow_casters.append(caster)
        
        # Create lights using helper methods
        # Main light (sun) – high range to simulate directional
        # Main light (directional)
        self.sun_light = self.shadow_system.add_directional_light(
            color=(1.0, 1.0, 0.8),
            intensity=0.8,
            range=600,
            shadow_map_size=1024
        )
        
        # Player light
        self.player_light = self.shadow_system.add_point_light(
            self.player['position'][0],
            self.player['position'][1],
            color=(1.0, 0.86, 0.7),  # normalized (255,220,180)
            intensity=0.6,
            range=150
        )
        self.lights.append(self.player_light)
        
        # Some static lights
        static_lights = [
            (200, 200, 120, (200, 150, 100), 0.7),
            (600, 400, 180, (200, 220, 255), 0.5),
            (100, 450, 100, (200, 255, 200), 0.6)
        ]
        
        for x, y, rng, col, intens in static_lights:
            norm_col = (col[0]/255.0, col[1]/255.0, col[2]/255.0)
            light = self.shadow_system.add_point_light(
                x, y,
                color=norm_col,
                intensity=intens,
                range=rng
            )
            self.lights.append(light)

    def setup_ui(self):
        """Setup user interface"""
        screen_width, screen_height = self.engine.width, self.engine.height
        
        # Control panel
        control_bg = UiFrame(10, 10, 300, 160)
        self.add_ui_element(control_bg)
        
        # Title
        title = TextLabel(20, 15, "Shadow System Test", 20, (255, 255, 255))
        self.add_ui_element(title)
        
        # Instructions
        instructions = [
            "WASD: Move camera",
            "Mouse Wheel: Zoom",
            "Click: Add light at mouse",
            "R: Reset lights",
            "C: Clear shadow casters",
            "T: Toggle shadows"
        ]
        
        for i, instruction in enumerate(instructions):
            label = TextLabel(20, 45 + i * 18, instruction, 14, (200, 200, 200))
            self.add_ui_element(label)
        
        self.darkness_slider = Slider(20, 200, 100, 20, 0.0, 1.0, self.shadow_system.darkness)
        self.add_ui_element(self.darkness_slider)
        self.darkness_slider.set_on_value_changed(lambda v: setattr(self.shadow_system, 'darkness', v))
        
        # Debug info display
        self.debug_label = TextLabel(10, screen_height - 100, "Debug Info", 14, (255, 255, 200))
        self.add_ui_element(self.debug_label)

    def handle_key_press(self, event):
        """Handle key presses"""
        if event.key == pygame.K_r:
            # Reset lights
            self.shadow_system.clear_lights()
            self.lights.clear()
            
            # Recreate player light
            self.player_light = self.shadow_system.add_point_light(
                self.player['position'][0],
                self.player['position'][1],
                color=(1.0, 0.86, 0.7),
                intensity=0.6,
                range=150
            )
            self.lights.append(self.player_light)
            print("Lights reset")
            
        elif event.key == pygame.K_c:
            # Clear shadow casters
            self.shadow_system.clear_casters()
            self.shadow_casters.clear()
            print("Shadow casters cleared")
            
        elif event.key == pygame.K_t:
            # Toggle shadows (just a flag for demo)
            self.shadows_enabled = not self.shadows_enabled
            self.shadow_system.enabled = self.shadows_enabled
            print(f"Shadows {'enabled' if self.shadows_enabled else 'disabled'}")
        elif event.key == pygame.K_1:
            self.handle_mouse_click(self.engine.input_state.mouse_pos)

    def handle_mouse_click(self, pos):
        """Handle mouse clicks to add lights"""
        world_pos = self.camera.screen_to_world(pos)
        
        # Random normalized color
        r = random.uniform(0.6, 1.0)
        g = random.uniform(0.6, 1.0)
        b = random.uniform(0.6, 1.0)
        color = (r, g, b)
        
        # Add a new point light at mouse position
        new_light = self.shadow_system.add_point_light(
            world_pos.x,
            world_pos.y,
            color=color,
            intensity=random.uniform(0.4, 0.8),
            range=random.randint(80, 200)
        )
        self.lights.append(new_light)
        print(f"Added light at ({world_pos.x:.1f}, {world_pos.y:.1f})")

    def update_player_movement(self, dt):
        """Update player/camera movement"""
        keys = pygame.key.get_pressed()
        
        # Reset velocity
        self.player['velocity'] = [0, 0]
        
        # Movement input
        if keys[pygame.K_w]:
            self.player['velocity'][1] = -1
        if keys[pygame.K_s]:
            self.player['velocity'][1] = 1
        if keys[pygame.K_a]:
            self.player['velocity'][0] = -1
        if keys[pygame.K_d]:
            self.player['velocity'][0] = 1
        
        # Mouse wheel zoom
        if self.engine.mouse_wheel != 0:
            zoom_speed = 0.1
            new_zoom = self.camera.zoom + (self.engine.mouse_wheel * zoom_speed)
            new_zoom = max(0.3, min(3.0, new_zoom))
            self.camera.set_zoom(new_zoom, smooth=True)
        
        # Normalize diagonal movement
        if self.player['velocity'][0] != 0 and self.player['velocity'][1] != 0:
            self.player['velocity'][0] *= 0.7071
            self.player['velocity'][1] *= 0.7071
        
        # Apply movement
        self.player['position'][0] += self.player['velocity'][0] * self.player['speed'] * dt
        self.player['position'][1] += self.player['velocity'][1] * self.player['speed'] * dt
        
        # Update camera to follow player
        self.camera.position.x = self.player['position'][0]
        self.camera.position.y = self.player['position'][1]
        self.camera.target_position.x = self.player['position'][0]
        self.camera.target_position.y = self.player['position'][1]
        
        # Update player light position
        self.player_light.position = (self.player['position'][0], self.player['position'][1])
        
        # Animate sun light – move in a large circle
        t = pygame.time.get_ticks() * 0.001
        self.sun_light.position = (
            400 + math.cos(t * 0.5) * 300,
            -100 + math.sin(t * 0.5) * 200
        )

    def update(self, dt):
        """Update game logic"""
        # Update player movement
        self.update_player_movement(dt)
        
        # Update camera
        self.camera.update(dt)
        
        # Update mouse world position for debug
        mouse_screen_pos = self.engine.mouse_pos
        mouse_world_pos = self.camera.screen_to_world(mouse_screen_pos)
        self.debug_info['mouse_world_pos'] = (mouse_world_pos.x, mouse_world_pos.y)
        self.debug_info['camera_pos'] = (self.camera.position.x, self.camera.position.y)
        
        # Get shadow system stats
        self.debug_info['shadow_stats'] = self.shadow_system.get_stats()
        
        # Update debug display
        self.update_debug_info()
        
    def update_debug_info(self):
        """Update debug information display"""
        stats = self.debug_info['shadow_stats']
        mouse_pos = self.debug_info['mouse_world_pos']
        camera_pos = self.debug_info['camera_pos']
        
        debug_text = f"Mouse World: ({mouse_pos[0]:.1f}, {mouse_pos[1]:.1f}), Camera: ({camera_pos[0]:.1f}, {camera_pos[1]:.1f}), Zoom: {self.camera.zoom:.2f}, Lights: {stats.get('lights', 0)} (visible: {stats.get('visible_lights', 0)}), Casters: {stats.get('casters', 0)} (visible: {stats.get('visible_casters', 0)})"
        
        self.debug_label.set_text(debug_text)

    def render(self, renderer):
        """Render the scene"""
        # Clear screen
        renderer.clear()
        renderer.fill_screen((40, 40, 50))  # dark background
        
        # Draw grid for reference
        self.draw_grid(renderer)
        
        # Draw test objects
        self.draw_objects(renderer)
        
        # Draw player
        self.draw_player(renderer)
        
        # Draw lights (for visualization)
        self.draw_lights_debug(renderer)
        
        if hasattr(self.sun_light, 'shadow_map') and self.sun_light.shadow_map:
            renderer.draw_texture(self.sun_light.shadow_map, 10, 10, 128, 128)
            # Optionally draw a label using renderer.draw_text (if you have a font)
            # You'd need a font surface; for simplicity, we can use pygame's font and blit via renderer.blit
            renderer.draw_text("Sun Shadow Map", 10, 140, (255, 255, 255), FontManager.get_font(None, 20))

    def draw_grid(self, renderer):
        """Draw a grid for spatial reference"""
        grid_size = 100
        grid_color = (60, 60, 80)
        
        # Get visible area
        visible_rect = self.camera.get_visible_rect()
        
        start_x = int(visible_rect.left // grid_size) * grid_size
        start_y = int(visible_rect.top // grid_size) * grid_size
        end_x = int(visible_rect.right) + grid_size
        end_y = int(visible_rect.bottom) + grid_size
        
        for x in range(start_x, end_x, grid_size):
            screen_pos = self.camera.world_to_screen((x, start_y))
            screen_end = self.camera.world_to_screen((x, end_y))
            renderer.draw_line(
                screen_pos.x, screen_pos.y,
                screen_end.x, screen_end.y,
                grid_color, 1
            )
        
        for y in range(start_y, end_y, grid_size):
            screen_pos = self.camera.world_to_screen((start_x, y))
            screen_end = self.camera.world_to_screen((end_x, y))
            renderer.draw_line(
                screen_pos.x, screen_pos.y,
                screen_end.x, screen_end.y,
                grid_color, 1
            )

    def draw_objects(self, renderer):
        """Draw all test objects"""
        for obj in self.test_objects:
            screen_pos = self.camera.world_to_screen(obj['position'])
            
            if obj['type'] == 'rectangle':
                width, height = obj['size']
                screen_width = width * self.camera.zoom
                screen_height = height * self.camera.zoom
                
                renderer.draw_rect(
                    screen_pos.x - screen_width / 2,
                    screen_pos.y - screen_height / 2,
                    screen_width,
                    screen_height,
                    obj['color'],
                    fill=True
                )
                
            elif obj['type'] == 'circle':
                radius = obj['radius'] * self.camera.zoom
                renderer.draw_circle(
                    screen_pos.x,
                    screen_pos.y,
                    radius,
                    obj['color'],
                    fill=True
                )

    def draw_player(self, renderer):
        """Draw the player"""
        screen_pos = self.camera.world_to_screen(self.player['position'])
        size = self.player['size'] * self.camera.zoom
        
        renderer.draw_circle(
            screen_pos.x,
            screen_pos.y,
            size,
            (255, 100, 100),
            fill=True
        )
        
        # Draw direction indicator
        if self.player['velocity'][0] != 0 or self.player['velocity'][1] != 0:
            end_x = screen_pos.x + self.player['velocity'][0] * size * 1.5
            end_y = screen_pos.y + self.player['velocity'][1] * size * 1.5
            renderer.draw_line(
                screen_pos.x, screen_pos.y,
                end_x, end_y,
                (255, 255, 255), 3
            )

    def draw_lights_debug(self, renderer):
        """Draw light positions for visualization"""
        for light in self.lights:
            screen_pos = self.camera.world_to_screen(light.position)
            radius = light.range * self.camera.zoom
            
            # Convert normalized color back to 0-255 for debug drawing
            r = int(light.color[0] * 255)
            g = int(light.color[1] * 255)
            b = int(light.color[2] * 255)
            debug_color = (r, g, b)
            
            # Draw light center
            renderer.draw_circle(
                screen_pos.x,
                screen_pos.y,
                5,
                debug_color,
                fill=True
            )
            
            # Draw light range (outline)
            renderer.draw_circle(
                screen_pos.x,
                screen_pos.y,
                radius,
                (*debug_color, 128),  # Semi-transparent
                fill=False,
                border_width=2
            )

def main():
    """Main function to run the shadow test demo"""
    engine = LunaEngine("Shadow System Test - LunaEngine", 1024, 768)
    engine.fps = 60
    
    # Register event handlers
    @engine.on_event(pygame.KEYDOWN)
    def on_key_press(event):
        if engine.current_scene and hasattr(engine.current_scene, 'handle_key_press'):
            engine.current_scene.handle_key_press(event)
    
    # Add and set the test scene
    engine.add_scene("shadow_test", ShadowTestScene)
    engine.set_scene("shadow_test")
    
    print("=== Shadow System Test Demo ===")
    print("Controls:")
    print("WASD - Move camera/player")
    print("Mouse Wheel - Zoom in/out")
    print("Click - Add light at mouse position")
    print("R - Reset lights")
    print("C - Clear shadow casters")
    print("T - Toggle shadows on/off")
    print("\nDebug information shown at bottom of screen")
    print("Note: Shadows are rendered via OpenGL depth maps, but")
    print("this demo only shows light positions. To see actual")
    print("shadows, you need a shader that samples the shadow maps.")
    
    engine.run()

if __name__ == "__main__":
    main()