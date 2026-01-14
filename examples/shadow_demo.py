"""
Shadow System Test Demo - LunaEngine
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
from lunaengine.graphics.shadows import ShadowSystem, Light, ShadowCaster

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
            
            # Add as shadow caster
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
            
            # Add as shadow caster
            caster = self.shadow_system.add_circle_caster(x, y, radius)
            self.shadow_casters.append(caster)
        
        # Create lights
        # Main light (sun)
        self.sun_light = self.shadow_system.add_light(400, -100, 600, (255, 255, 200), 0.8)
        self.lights.append(self.sun_light)
        
        # Player light
        self.player_light = self.shadow_system.add_light(
            self.player['position'][0],
            self.player['position'][1],
            150,
            (255, 220, 180),
            0.6
        )
        self.lights.append(self.player_light)
        
        # Some static lights
        static_lights = [
            (200, 200, 120, (255, 200, 150), 0.7),
            (600, 400, 180, (200, 220, 255), 0.5),
            (100, 450, 100, (200, 255, 200), 0.6)
        ]
        
        for x, y, radius, color, intensity in static_lights:
            light = self.shadow_system.add_light(x, y, radius, color, intensity)
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
            self.player_light = self.shadow_system.add_light(
                self.player['position'][0],
                self.player['position'][1],
                150,
                (255, 220, 180),
                0.6
            )
            self.lights.append(self.player_light)
            print("Lights reset")
            
        elif event.key == pygame.K_c:
            # Clear shadow casters
            self.shadow_system.clear_shadow_casters()
            self.shadow_casters.clear()
            print("Shadow casters cleared")
            
        elif event.key == pygame.K_t:
            # Toggle shadows
            self.engine.current_scene.shadows_enabled = not self.engine.current_scene.shadows_enabled
            print(f"Shadows {'enabled' if self.engine.current_scene.shadows_enabled else 'disabled'}")

    def handle_mouse_click(self, pos):
        """Handle mouse clicks to add lights"""
        world_pos = self.camera.screen_to_world(pos)
        
        # Add a new light at mouse position
        new_light = self.shadow_system.add_light(
            world_pos.x,
            world_pos.y,
            random.randint(80, 200),
            (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255)),
            random.uniform(0.4, 0.8)
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
        
        # Update player light
        self.player_light.position.x = self.player['position'][0]
        self.player_light.position.y = self.player['position'][1]
        
        # Animate sun light
        self.sun_light.position.x = 400 + math.cos(pygame.time.get_ticks() * 0.0005) * 300
        self.sun_light.position.y = -100 + math.sin(pygame.time.get_ticks() * 0.0005) * 200

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
        
        # Handle mouse clicks
        if self.engine.input_state.mouse_buttons_pressed.left:
            self.handle_mouse_click(mouse_screen_pos)
        
        # Update debug display
        self.update_debug_info()

    def update_debug_info(self):
        """Update debug information display"""
        stats = self.debug_info['shadow_stats']
        mouse_pos = self.debug_info['mouse_world_pos']
        camera_pos = self.debug_info['camera_pos']
        
        debug_text = f"Mouse World: ({mouse_pos[0]:.1f}, {mouse_pos[1]:.1f}), Camera: ({camera_pos[0]:.1f}, {camera_pos[1]:.1f}), Zoom: {self.camera.zoom:.2f}, Lights: {stats.get('total_lights', 0)} (visible: {stats.get('visible_lights', 0)}), Casters: {stats.get('total_casters', 0)} (visible: {stats.get('visible_casters', 0)}), Render Time: {stats.get('render_time_ms', 0):.1f}ms, FPS: {stats.get('current_fps', 0):.1f}"
        
        self.debug_label.set_text(debug_text)

    def render(self, renderer):
        """Render the scene"""
        # Clear screen
        renderer.get_surface().fill((30, 30, 50))
        
        # Draw grid for reference
        self.draw_grid(renderer)
        
        # Draw test objects
        self.draw_objects(renderer)
        
        # Draw player
        self.draw_player(renderer)
        
        # Draw lights (for visualization)
        self.draw_lights_debug(renderer)
        
        # Render shadows
        if hasattr(self, 'shadows_enabled') and self.shadows_enabled:
            try:
                shadow_surface = self.shadow_system.render(self.camera.position, renderer)
                if shadow_surface and isinstance(shadow_surface, pygame.Surface):
                    renderer.blit(shadow_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            except Exception as e:
                print(f"Shadow rendering error: {e}")
                import traceback
                traceback.print_exc()

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
            radius = light.radius * self.camera.zoom
            
            # Draw light center
            renderer.draw_circle(
                screen_pos.x,
                screen_pos.y,
                5,
                light.color,
                fill=True
            )
            
            # Draw light radius (outline)
            renderer.draw_circle(
                screen_pos.x,
                screen_pos.y,
                radius,
                (*light.color, 128),  # Semi-transparent
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
    
    # Enable shadows by default
    engine.current_scene.shadows_enabled = True
    
    print("=== Shadow System Test Demo ===")
    print("Controls:")
    print("WASD - Move camera/player")
    print("Mouse Wheel - Zoom in/out")
    print("Click - Add light at mouse position")
    print("R - Reset lights")
    print("C - Clear shadow casters")
    print("T - Toggle shadows on/off")
    print("\nDebug information shown at bottom of screen")
    
    engine.run()

if __name__ == "__main__":
    main()