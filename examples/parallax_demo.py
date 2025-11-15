"""
parallax_demo.py - Parallax System Demonstration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pygame
from lunaengine.core import LunaEngine, Scene
from lunaengine.graphics.camera import Camera, CameraMode

class ParallaxDemo(Scene):
    """Demo scene to test the parallax background system"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Game state
        self.game_state = {
            'camera_speed': 200,
            'parallax_enabled': True,
            'debug_info': True
        }
        
        # World configuration
        self.world_size = (4000, 720)  # Wide world for horizontal movement
        
        # Player position (for camera control)
        self.player_x = 0
        
        # Load background image
        self.bg_image = self.load_background_image()
        
        # Setup camera and parallax
        self.setup_camera()
        self.setup_parallax()
        
        # Setup UI
        self.setup_ui()
        
        print("Parallax Demo Controls:")
        print("A/D or Left/Right Arrow - Move camera horizontally")
        print("W/S or Up/Down Arrow - Move camera vertically") 
        print("Mouse Wheel - Zoom in/out")
        print("P - Toggle parallax on/off")
        print("I - Toggle debug info")
        print("R - Reset camera position")

    def load_background_image(self):
        """Load the background image for parallax testing"""
        try:
            # Try to load from current directory first
            image_path = "background.jpg"
            if os.path.exists(image_path):
                image = pygame.image.load(image_path)
                print(f"Loaded background image: {image_path}")
                return image.convert_alpha()
            else:
                # Create a placeholder image if file not found
                print("Background image not found. Creating placeholder...")
                return self.create_placeholder_image()
        except Exception as e:
            print(f"Error loading background image: {e}")
            return self.create_placeholder_image()

    def create_placeholder_image(self):
        """Create a placeholder image with gradient and grid for testing"""
        surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
        
        # Create gradient background
        for y in range(720):
            # Sky gradient (blue to light blue)
            if y < 360:
                color = (100, 150, 255 - y // 3)
                pygame.draw.line(surface, color, (0, y), (1280, y))
            # Ground gradient (green to dark green)
            else:
                color = (50, 200 - (y - 360) // 2, 50)
                pygame.draw.line(surface, color, (0, y), (1280, y))
        
        # Add grid lines for better parallax effect visualization
        grid_color = (255, 255, 255, 50)
        for x in range(0, 1280, 100):
            pygame.draw.line(surface, grid_color, (x, 0), (x, 720), 2)
        for y in range(0, 720, 100):
            pygame.draw.line(surface, grid_color, (0, y), (1280, y), 2)
        
        # Add some landmarks
        landmark_color = (255, 200, 100, 200)
        
        # Mountains in background
        pygame.draw.polygon(surface, (150, 150, 200, 200), 
                           [(200, 360), (400, 200), (600, 360)])
        pygame.draw.polygon(surface, (120, 120, 180, 200), 
                           [(600, 360), (800, 150), (1000, 360)])
        
        # Trees in midground
        for x in [150, 450, 750, 1050]:
            # Trunk
            pygame.draw.rect(surface, (139, 69, 19, 255), (x, 360, 20, 60))
            # Leaves
            pygame.draw.circle(surface, (50, 150, 50, 255), (x + 10, 330), 40)
        
        # Foreground elements
        for x in [100, 300, 500, 700, 900, 1100]:
            pygame.draw.rect(surface, (100, 100, 100, 255), (x, 420, 10, 100))
        
        return surface

    def setup_camera(self):
        """Configure camera for parallax testing"""
        self.camera.position = pygame.math.Vector2(0, 0)
        self.camera.target_position = pygame.math.Vector2(0, 0)
        
        self.camera.mode = CameraMode.TOPDOWN
        self.camera.smooth_speed = 0.05
        self.camera.lead_factor = 0.0
        
        # Set zoom limits
        self.camera.zoom = 1.0
        self.camera.target_zoom = 1.0
        self.camera.min_zoom = 0.5
        self.camera.max_zoom = 2.0
        
        # Set camera bounds to world size
        world_rect = pygame.Rect(0, 0, self.world_size[0], self.world_size[1])
        self.camera.set_bounds(world_rect)

    def setup_parallax(self):
        """Setup parallax background with multiple layers"""
        # Clear any existing layers
        self.camera.clear_parallax_layers()
        
        # Create different parallax layers from the same image with different speeds
        # This simulates depth by having background elements move slower than foreground
        
        # Layer 1: Far background (mountains, sky) - moves very slowly
        far_bg = self.create_parallax_layer(self.bg_image, 0.1)
        self.camera.add_parallax_layer(far_bg, 0.2, tile_mode=True)
        
        # Layer 2: Mid background (distant trees) - moves slowly
        mid_bg = self.create_parallax_layer(self.bg_image, 0.3)
        self.camera.add_parallax_layer(mid_bg, 0.4, tile_mode=True)
        
        # Layer 3: Near background (close trees) - moves at medium speed
        near_bg = self.create_parallax_layer(self.bg_image, 0.6)
        self.camera.add_parallax_layer(near_bg, 0.7, tile_mode=True)
        
        # Layer 4: Foreground (grass, rocks) - moves almost with camera
        foreground = self.create_parallax_layer(self.bg_image, 0.9)
        self.camera.add_parallax_layer(foreground, 0.9, tile_mode=True)
        
        self.camera.enable_parallax(True)
        
        print("Parallax layers created:")
        print("- Far background (speed: 0.2)")
        print("- Mid background (speed: 0.4)") 
        print("- Near background (speed: 0.7)")
        print("- Foreground (speed: 0.9)")

    def create_parallax_layer(self, base_image, brightness_factor=1.0):
        """Create a modified version of the base image for parallax layers"""
        # Create a copy of the image
        layer = base_image.copy()
        
        # Adjust brightness to simulate depth (darker = further away)
        if brightness_factor != 1.0:
            # Fill with semi-transparent color to darken/brighten
            overlay = pygame.Surface(layer.get_size(), pygame.SRCALPHA)
            brightness_value = int(255 * (1 - brightness_factor))
            overlay.fill((brightness_value, brightness_value, brightness_value, 100))
            layer.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return layer

    def setup_ui(self):
        """Setup user interface for the demo"""
        from lunaengine.ui.elements import TextLabel, Button
        
        screen_width, screen_height = self.engine.width, self.engine.height
        
        # Debug info display
        self.debug_label = TextLabel(10, 10, "", 16, (255, 255, 255))
        self.add_ui_element(self.debug_label)
        
        # Toggle parallax button
        self.parallax_toggle = Button(screen_width - 150, 10, 140, 30, "Parallax: ON")
        self.parallax_toggle.set_on_click(self.toggle_parallax)
        self.add_ui_element(self.parallax_toggle)
        
        # Debug info toggle
        self.debug_toggle = Button(screen_width - 150, 50, 140, 30, "Debug Info: ON")
        self.debug_toggle.set_on_click(self.toggle_debug_info)
        self.add_ui_element(self.debug_toggle)
        
        # Reset camera button
        self.reset_button = Button(screen_width - 150, 90, 140, 30, "Reset Camera")
        self.reset_button.set_on_click(self.reset_camera)
        self.add_ui_element(self.reset_button)

    def toggle_parallax(self):
        """Toggle parallax effect on/off"""
        self.game_state['parallax_enabled'] = not self.game_state['parallax_enabled']
        self.camera.enable_parallax(self.game_state['parallax_enabled'])
        self.parallax_toggle.set_text(f"Parallax: {'ON' if self.game_state['parallax_enabled'] else 'OFF'}")

    def toggle_debug_info(self):
        """Toggle debug information display"""
        self.game_state['debug_info'] = not self.game_state['debug_info']
        self.debug_toggle.set_text(f"Debug Info: {'ON' if self.game_state['debug_info'] else 'OFF'}")

    def reset_camera(self):
        """Reset camera to starting position"""
        self.player_x = 0
        self.camera.position = pygame.math.Vector2(0, 0)
        self.camera.target_position = pygame.math.Vector2(0, 0)
        self.camera.set_zoom(1.0, smooth=False)

    def handle_key_press(self, event):
        """Handle key presses"""
        if event.key == pygame.K_p:
            self.toggle_parallax()
        elif event.key == pygame.K_i:
            self.toggle_debug_info()
        elif event.key == pygame.K_r:
            self.reset_camera()

    def update_player_movement(self, dt):
        """Update camera movement based on input"""
        keys = pygame.key.get_pressed()
        
        movement_x = 0
        movement_y = 0
        
        # Horizontal movement
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            movement_x = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            movement_x = 1
            
        # Vertical movement  
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            movement_y = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movement_y = 1
        
        # Apply movement
        self.player_x += movement_x * self.game_state['camera_speed'] * dt
        movement_y = movement_y * self.game_state['camera_speed'] * dt
        
        # Update camera target
        self.camera.target_position.x = self.player_x
        self.camera.target_position.y += movement_y
        
        # Mouse wheel zoom
        if self.engine.mouse_wheel != 0:
            zoom_speed = 0.1
            new_zoom = self.camera.zoom + (self.engine.mouse_wheel * zoom_speed)
            new_zoom = max(self.camera.min_zoom, min(self.camera.max_zoom, new_zoom))
            self.camera.set_zoom(new_zoom, smooth=True)

    def update_debug_info(self):
        """Update debug information display"""
        if self.game_state['debug_info']:
            info_text = (
                f"Camera Position: ({self.camera.position.x:.1f}, {self.camera.position.y:.1f})\n"
                f"Camera Zoom: {self.camera.zoom:.2f}\n"
                f"Player X: {self.player_x:.1f}\n"
                f"Parallax Layers: {self.camera.get_parallax_layer_count()}\n"
                f"World Size: {self.world_size[0]}x{self.world_size[1]}"
            )
            self.debug_label.set_text(info_text)
        else:
            self.debug_label.set_text("")

    def update(self, dt):
        """Update game logic"""
        # Update player movement
        self.update_player_movement(dt)
        
        # Update camera
        self.camera.update(dt)
        
        # Update debug info
        self.update_debug_info()

    def render(self, renderer):
        """Render the scene"""
        # Clear screen
        renderer.get_surface().fill((30, 30, 50))
        
        # Render parallax background
        if self.game_state['parallax_enabled']:
            self.camera.render_parallax(renderer)
        else:
            # Fallback: render static background when parallax is disabled
            bg_x = -self.camera.position.x * 0.5  # Simple parallax effect
            renderer.blit(self.bg_image, (bg_x % 1280 - 1280, 0))
            renderer.blit(self.bg_image, (bg_x % 1280, 0))
        
        # Render world boundaries for reference
        self.render_world_boundaries(renderer)
        
        # Render player position indicator
        self.render_player_indicator(renderer)

    def render_world_boundaries(self, renderer):
        """Render world boundaries for visual reference"""
        screen_width, screen_height = self.engine.width, self.engine.height
        
        # Convert world coordinates to screen coordinates
        left_pos = self.camera.world_to_screen((0, 0))
        right_pos = self.camera.world_to_screen((self.world_size[0], 0))
        
        # Draw boundary lines
        boundary_color = (255, 0, 0, 100)
        renderer.draw_line(left_pos.x, 0, left_pos.x, screen_height, boundary_color, 2)
        renderer.draw_line(right_pos.x, 0, right_pos.x, screen_height, boundary_color, 2)

    def render_player_indicator(self, renderer):
        """Render a simple indicator for player position"""
        player_screen_pos = self.camera.world_to_screen((self.player_x, self.world_size[1] // 2))
        
        # Draw player indicator
        indicator_color = (255, 255, 0)
        renderer.draw_circle(player_screen_pos.x, player_screen_pos.y, 10, indicator_color)
        
        # Draw direction indicator
        direction_length = 30
        renderer.draw_line(
            player_screen_pos.x, player_screen_pos.y,
            player_screen_pos.x + direction_length, player_screen_pos.y,
            indicator_color, 3
        )

def main():
    """Main function to run the parallax demo"""
    engine = LunaEngine("Parallax System Demo - Use A/D to move, P to toggle parallax", 1024, 576, use_opengl=True)
    engine.fps = 60
    
    # Register event handlers
    @engine.on_event(pygame.KEYDOWN)
    def on_key_press(event):
        if engine.current_scene and hasattr(engine.current_scene, 'handle_key_press'):
            engine.current_scene.handle_key_press(event)
    
    # Add and start the parallax demo scene
    engine.add_scene("parallax_demo", ParallaxDemo)
    engine.set_scene("parallax_demo")
    
    print("=== Parallax System Demo ===")
    print("This demo tests the parallax background system with horizontal movement.")
    print("The background image will be loaded from 'background.jpg' if available.")
    print("If no image is found, a placeholder will be generated automatically.")
    
    engine.run()

if __name__ == "__main__":
    main()