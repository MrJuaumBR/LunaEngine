"""
topdown_farming_demo.py - Top-Down Farming Game Demo with Optimized Shadows

Updated for LunaEngine 0.2.0 Camera System:
- Unified world‑to‑screen conversion (camera.position = viewport centre)
- Constraints via CameraConstraints
- Compatible with legacy CameraMode / set_target
"""

import sys
import os
import random
import math
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import *
from lunaengine.graphics.camera import Camera, CameraMode
from lunaengine.graphics.particles import ParticleSystem, ParticleConfig, ExitPoint, PhysicsType
from lunaengine.graphics.shadows import ShadowSystem, Light, ShadowCaster
from lunaengine.utils import distance
import pygame

class TopDownFarmingGame(Scene):
    """Top-Down Farming and Collection Game with Optimized Shadows"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Game state
        self.game_state = {
            'money': 100,
            'inventory': {
                'wood': 0,
                'stone': 0,
                'wheat': 0,
                'corn': 0
            },
            'seeds': {
                'wheat': 5,
                'corn': 3
            },
            'selected_tool': 'axe',
            'selected_seed': 'wheat',
            'day_time': 0.25,  # Start in morning
            'day_count': 1
        }
        
        # World configuration
        self.world_size = (2000, 2000)
        self.cell_size = 40
        
        # Initialize game entities
        self.player = None
        self.trees = []
        self.rocks = []
        self.farm_plots = []
        self.crops = []
        self.market_stall = None
        self.seed_shop = None
        
        # Shadow system control
        self.shadows_enabled = True
        self.shadow_quality = "medium"  # low, medium, high
        
        # Generate world (BEFORE setting up camera)
        self.setup_parallax()
        self.generate_world()
        
        # Configure camera (AFTER generating world)
        self.setup_camera()
        
        # Setup shadow system (AFTER camera and world)
        self.setup_shadows()
        
        # Setup UI
        self.setup_ui()

    def setup_shadows(self):
        """Setup optimized shadow system"""
        # Configure shadow system based on quality
        if self.shadow_quality == "low":
            self.shadow_system.max_cache_size = 3
            self.shadow_update_frequency = 3  # Update every 3 frames
        elif self.shadow_quality == "medium":
            self.shadow_system.max_cache_size = 5
            self.shadow_update_frequency = 2  # Update every 2 frames
        else:  # high
            self.shadow_system.max_cache_size = 8
            self.shadow_update_frequency = 1  # Update every frame
        
        # Add only essential shadow casters for better performance
        self.add_essential_shadow_casters()
        
        # Setup lights
        self.setup_lights()

    def add_essential_shadow_casters(self):
        """Add only the most important shadow casters for performance"""
        # Clear existing shadow casters first
        self.shadow_system.clear_shadow_casters()
        
        # Add trees as shadow casters (most visible)
        for tree in self.trees[:15]:  # Limit to 15 trees for performance
            tree_caster = self.create_tree_shadow_caster(tree)
            self.shadow_system.shadow_casters.append(tree_caster)
            
        # Add rocks as shadow casters
        for rock in self.rocks[:15]:  # Limit to 15 rocks for performance
            rock_caster = self.create_rock_shadow_caster(rock)
            self.shadow_system.shadow_casters.append(rock_caster)
        
        # Add buildings as shadow casters
        if self.market_stall:
            market_caster = self.create_building_shadow_caster(self.market_stall)
            self.shadow_system.shadow_casters.append(market_caster)
        
        if self.seed_shop:
            shop_caster = self.create_building_shadow_caster(self.seed_shop)
            self.shadow_system.shadow_casters.append(shop_caster)

    def setup_lights(self):
        """Setup optimized lighting system"""
        # Main directional light (sun/moon)
        self.sun_light = self.shadow_system.add_light(
            self.world_size[0] // 2,
            -300,
            1200,
            (255, 255, 200),
            intensity=0.8
        )
        
        # Player light (simple, small radius for performance)
        self.player_light = self.shadow_system.add_light(
            self.player['position'][0],
            self.player['position'][1],
            150,  # Smaller radius for performance
            (255, 220, 180),
            intensity=0.6
        )
        
        # Add some static lights for better illumination
        static_lights = [
            (500, 500, 200, (255, 200, 150), 0.4),
            (1500, 500, 200, (200, 220, 255), 0.4),
            (500, 1500, 200, (200, 255, 200), 0.4),
            (1500, 1500, 200, (255, 200, 255), 0.4)
        ]
        
        for x, y, radius, color, intensity in static_lights:
            self.shadow_system.add_light(x, y, radius, color, intensity)

    def create_tree_shadow_caster(self, tree):
        """Create simplified shadow caster for a tree"""
        x, y = tree['position']  # World position
        size = tree['size']
        
        # Simple square shadow caster (better performance than circle)
        half_size = size * 0.3
        vertices = [
            (x - half_size, y - half_size),
            (x + half_size, y - half_size),
            (x + half_size, y + half_size),
            (x - half_size, y + half_size)
        ]
        
        return ShadowCaster(vertices)
    
    def create_rock_shadow_caster(self, rock):
        """Create simplified shadow caster for a rock"""
        x, y = rock['position']  # World position
        size = rock['size']
        
        # Simple square shadow caster (better performance than circle)
        half_size = size * 0.3
        vertices = [
            (x - half_size, y - half_size),
            (x + half_size, y - half_size),
            (x + half_size, y + half_size),
            (x - half_size, y + half_size)
        ]
        
        return ShadowCaster(vertices)

    def create_building_shadow_caster(self, building):
        """Create shadow caster for building"""
        x, y = building['position']  # World position
        size = building['size']
        
        half_size = size // 2
        vertices = [
            (x - half_size, y - half_size),
            (x + half_size, y - half_size),
            (x + half_size, y + half_size),
            (x - half_size, y + half_size)
        ]
        return ShadowCaster(vertices)

    def update_shadows(self):
        """Update shadow system with proper world coordinates"""
        # Update player light - use world position
        if hasattr(self, 'player') and self.player:
            self.player_light.position.x = self.player['position'][0]
            self.player_light.position.y = self.player['position'][1]
        
        # Update sun based on time of day - use world position
        sun_angle = self.game_state['day_time'] * 2 * math.pi
        sun_x = self.world_size[0] // 2 + math.cos(sun_angle) * 1000
        sun_y = self.world_size[1] // 2 + math.sin(sun_angle) * 400 - 400
        
        self.sun_light.position.x = sun_x
        self.sun_light.position.y = sun_y
        
        # Day/night cycle - adjust light properties
        if 0.25 <= self.game_state['day_time'] <= 0.75:
            # Daytime
            self.sun_light.color = (255, 255, 200)
            self.sun_light.intensity = 0.8
            self.player_light.intensity = 0.3  # Dim player light during day
        else:
            # Nighttime
            self.sun_light.color = (150, 180, 255)
            self.sun_light.intensity = 0.2
            self.player_light.intensity = 0.8  # Bright player light at night

    def setup_camera(self):
        """Configure camera for top-down mode (updated for new camera system)"""
        # Reset camera position to player position
        self.camera.position = pygame.math.Vector2(self.player['position'])
        self.camera.target_position = pygame.math.Vector2(self.player['position'])
        
        self.camera.smooth_speed = 0.1
        self.camera.lead_factor = 0.2
        
        # Zoom limits – now stored in CameraConstraints
        self.camera.constraints.min_zoom = 0.7
        self.camera.constraints.max_zoom = 2.0
        self.camera.zoom = 1.0
        self.camera.target_zoom = 1.0
        
        # Set camera bounds to world size
        world_rect = pygame.Rect(0, 0, self.world_size[0], self.world_size[1])
        self.camera.set_bounds(world_rect)
        
        # Set camera to follow player (dict with position + velocity for look‑ahead)
        self.camera.set_target({
            'position': self.player['position'],
            'velocity': self.player['velocity']
        }, CameraMode.TOPDOWN)

    def generate_world(self):
        """Generate optimized game world"""
        grass_dark = (80, 160, 80)
        grass_light = (100, 180, 100)
        
        self.bg_surface = pygame.Surface((self.world_size[0], self.world_size[1]))
        # Generate world tiles
        for x in range(0, self.world_size[0], 100):
            for y in range(0, self.world_size[1], 100):
                grass_color = grass_dark if (x // 100 + y // 100) % 2 == 0 else grass_light
                pygame.draw.rect(self.bg_surface, grass_color, (x, y, 100, 100))
        
        # Create player in center
        self.player = {
            'position': [self.world_size[0] // 2, self.world_size[1] // 2],
            'velocity': [0, 0],
            'speed': 200,
            'size': 20
        }
        
        # Generate trees (fewer for better performance)
        for _ in range(20):
            x = random.randint(100, self.world_size[0] - 100)
            y = random.randint(100, self.world_size[1] - 100)
            self.trees.append({
                'position': [x, y],
                'size': random.randint(30, 50),
                'health': 3,
                'type': 'tree'
            })
        
        # Generate rocks
        for _ in range(15):
            x = random.randint(100, self.world_size[0] - 100)
            y = random.randint(100, self.world_size[1] - 100)
            self.rocks.append({
                'position': [x, y],
                'size': random.randint(25, 40),
                'health': 4,
                'type': 'rock'
            })
        
        # Generate farm plots
        plot_start_x = 400
        plot_start_y = 400
        for row in range(4):  # Smaller farm for performance
            for col in range(4):
                x = plot_start_x + col * 80
                y = plot_start_y + row * 80
                self.farm_plots.append({
                    'position': [x, y],
                    'size': 60,
                    'occupied': False,
                    'crop_type': None,
                    'growth_stage': 0,
                    'growth_timer': 0
                })
        
        # Place market and seed shop
        shop_y = self.world_size[1] // 2
        self.market_stall = {
            'position': [self.world_size[0] - 250, shop_y],
            'size': 80
        }
        
        self.seed_shop = {
            'position': [self.world_size[0] - 450, shop_y],
            'size': 80
        }

    def setup_parallax(self):
        """Setup optimized parallax background"""
        self.camera.clear_parallax_layers()
        
        # Only use one parallax layer for performance
        sky_surface = self.create_sky_surface()
        self.camera.add_parallax_layer(sky_surface, 0.1, tile_mode=True)
        self.camera.enable_parallax(True)

    def create_sky_surface(self):
        """Create simple sky background"""
        surface = pygame.Surface((800, 600))
        # Simple solid color sky (better performance than gradient)
        surface.fill((70, 70, 120))
        return surface

    def setup_ui(self):
        """Setup user interface"""
        screen_width, screen_height = self.engine.width, self.engine.height
        toolbar_height = 100  # Smaller toolbar
        toolbar_y = screen_height - toolbar_height
        
        # Simple toolbar background
        toolbar_bg = UiFrame(0, toolbar_y, screen_width, toolbar_height)
        self.add_ui_element(toolbar_bg)
        
        # Money display
        self.money_display = TextLabel(20, toolbar_y + 15, f"Money: ${self.game_state['money']}", 20, (255, 215, 0))
        self.add_ui_element(self.money_display)
        
        # Inventory display (simplified)
        self.inventory_display = TextLabel(20, toolbar_y + 45, "Inventory: ", 16, (200, 230, 255))
        self.add_ui_element(self.inventory_display)
        
        # Time display
        self.time_display = TextLabel(screen_width - 200, toolbar_y + 15, f"Day {self.game_state['day_count']}", 16, (255, 200, 150))
        self.add_ui_element(self.time_display)
        
        # Shadow toggle button
        self.shadow_toggle = Button(screen_width - 200, toolbar_y + 45, 120, 30, "Shadows: ON")
        self.shadow_toggle.set_on_click(self.toggle_shadows)
        self.add_ui_element(self.shadow_toggle)
        
        # Update initial selection
        self.select_tool('axe')

    def toggle_shadows(self):
        """Toggle shadows on/off"""
        self.shadows_enabled = not self.shadows_enabled
        self.shadow_toggle.set_text(f"Shadows: {'ON' if self.shadows_enabled else 'OFF'}")
        print(f"Shadows {'enabled' if self.shadows_enabled else 'disabled'}")

    def select_tool(self, tool):
        """Select tool"""
        self.game_state['selected_tool'] = tool

    def handle_key_press(self, event):
        """Handle key presses"""
        if event.key == pygame.K_F1:
            self.toggle_shadows()
        elif event.key == pygame.K_1:
            self.select_tool('axe')
        elif event.key == pygame.K_2:
            self.select_tool('pickaxe')
        elif event.key == pygame.K_3:
            self.select_tool('scythe')
        elif event.key == pygame.K_4:
            self.select_tool('seeds')
        elif event.key == pygame.K_q and self.game_state['selected_tool'] == 'seeds':
            self.game_state['selected_seed'] = 'wheat'
        elif event.key == pygame.K_e and self.game_state['selected_tool'] == 'seeds':
            self.game_state['selected_seed'] = 'corn'

    def get_interaction_distance(self):
        """Get maximum interaction distance"""
        return 80

    def update_player_movement(self, dt):
        """Update player movement"""
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
        
        # Mouse wheel zoom (updated to use constraints)
        if self.engine.mouse_wheel != 0:
            zoom_speed = 0.05
            new_zoom = self.camera.zoom + (self.engine.mouse_wheel * zoom_speed)
            # Use constraints for min/max zoom
            new_zoom = max(self.camera.constraints.min_zoom, 
                          min(self.camera.constraints.max_zoom, new_zoom))
            self.camera.set_zoom(new_zoom, smooth=True)
        
        # Normalize diagonal movement
        if self.player['velocity'][0] != 0 and self.player['velocity'][1] != 0:
            self.player['velocity'][0] *= 0.7071
            self.player['velocity'][1] *= 0.7071
        
        # Apply movement
        self.player['position'][0] += self.player['velocity'][0] * self.player['speed'] * dt
        self.player['position'][1] += self.player['velocity'][1] * self.player['speed'] * dt
        
        # Keep player in bounds
        self.player['position'][0] = max(self.player['size'], min(self.world_size[0] - self.player['size'], self.player['position'][0]))
        self.player['position'][1] = max(self.player['size'], min(self.world_size[1] - self.player['size'], self.player['position'][1]))
        
        # Update camera target (look‑ahead works because we pass velocity)
        self.camera.set_target({
            'position': self.player['position'],
            'velocity': self.player['velocity']
        }, CameraMode.TOPDOWN)

    def handle_interaction(self):
        """Handle player interactions with world"""
        if self.engine.input_state.mouse_buttons_pressed.left:
            tool = self.game_state['selected_tool']
            ppos = self.player['position']
            mpos = self.camera.screen_to_world(self.engine.mouse_pos)
            
            if tool == 'axe':
                self.chop_tree(ppos, mpos)
            elif tool == 'pickaxe':
                self.mine_rock(ppos, mpos)
            elif tool == 'scythe':
                self.harvest_crop(ppos, mpos)
            elif tool == 'seeds':
                self.plant_seed(ppos, mpos)
            
            # Shop interactions
            self.interact_with_market(ppos, mpos)

    def chop_tree(self, position, mouse_pos):
        """Chop nearby tree"""
        interaction_distance = self.get_interaction_distance()
        
        for tree in self.trees[:]:
            dis = distance(tree['position'], position)
            mdis = distance(tree['position'], mouse_pos)
            
            if dis < interaction_distance and mdis < tree['size'] + 20:
                tree['health'] -= 1
                
                if tree['health'] <= 0:
                    self.trees.remove(tree)
                    self.game_state['inventory']['wood'] += 2
                    # Remove from shadow system and rebuild
                    self.add_essential_shadow_casters()
                
                break

    def mine_rock(self, position, mouse_pos):
        """Mine nearby rock"""
        interaction_distance = self.get_interaction_distance()
        
        for rock in self.rocks[:]:
            dis = distance(rock['position'], position)
            mdis = distance(rock['position'], mouse_pos)
            
            if dis < interaction_distance and mdis < rock['size'] + 20:
                rock['health'] -= 1
                
                if rock['health'] <= 0:
                    self.rocks.remove(rock)
                    self.game_state['inventory']['stone'] += 2
                
                break

    def plant_seed(self, position, mouse_pos):
        """Plant seed in empty plot"""
        if self.game_state['seeds'][self.game_state['selected_seed']] <= 0:
            return
            
        interaction_distance = self.get_interaction_distance()
        
        for plot in self.farm_plots:
            dis = distance(plot['position'], position)
            mdis = distance(plot['position'], mouse_pos)
            
            if dis < interaction_distance and mdis < plot['size'] + 20 and not plot['occupied']:
                plot['occupied'] = True
                plot['crop_type'] = self.game_state['selected_seed']
                plot['growth_stage'] = 1
                plot['growth_timer'] = 0
                
                self.game_state['seeds'][self.game_state['selected_seed']] -= 1
                break

    def harvest_crop(self, position, mouse_pos):
        """Harvest mature crop"""
        interaction_distance = self.get_interaction_distance()
        
        for plot in self.farm_plots:
            dis = distance(plot['position'], position)
            mdis = distance(plot['position'], mouse_pos)
            
            if dis < interaction_distance and mdis < plot['size'] + 20 and plot['occupied'] and plot['growth_stage'] == 3:
                crop_type = plot['crop_type']
                self.game_state['inventory'][crop_type] += 3
                
                # Reset plot
                plot['occupied'] = False
                plot['crop_type'] = None
                plot['growth_stage'] = 0
                plot['growth_timer'] = 0
                break

    def interact_with_market(self, position, mouse_pos):
        """Sell resources at market"""
        if not self.market_stall:
            return
        
        dis = distance(self.market_stall['position'], position)
        mdis = distance(self.market_stall['position'], mouse_pos)
        interaction_distance = self.get_interaction_distance()
        
        if dis < interaction_distance and mdis < self.market_stall['size'] + 20:
            # Selling prices
            prices = {
                'wood': 5,
                'stone': 8,
                'wheat': 12,
                'corn': 15
            }
            
            # Sell everything
            total_sale = 0
            for item, quantity in self.game_state['inventory'].items():
                if quantity > 0:
                    total_sale += quantity * prices[item]
                    self.game_state['inventory'][item] = 0
            
            if total_sale > 0:
                self.game_state['money'] += total_sale

    def update_crops(self, dt):
        """Update crop growth"""
        for plot in self.farm_plots:
            if plot['occupied']:
                plot['growth_timer'] += dt
                
                # Grow every 5 seconds
                if plot['growth_timer'] >= 5:
                    plot['growth_stage'] = min(3, plot['growth_stage'] + 1)
                    plot['growth_timer'] = 0

    def update_time(self, dt):
        """Update day/night cycle"""
        self.game_state['day_time'] += dt / 120  # 2 minutes per full day
        
        if self.game_state['day_time'] >= 1:
            self.game_state['day_time'] = 0
            self.game_state['day_count'] += 1

    def update_ui(self):
        """Update UI displays"""
        # Money
        self.money_display.set_text(f"Money: ${self.game_state['money']}")
        
        # Inventory
        inv_text = "Inventory: "
        for item, quantity in self.game_state['inventory'].items():
            if quantity > 0:
                inv_text += f"{item}:{quantity} "
        self.inventory_display.set_text(inv_text)
        
        # Time
        time_of_day = "Morning" if self.game_state['day_time'] < 0.25 else \
                     "Noon" if self.game_state['day_time'] < 0.5 else \
                     "Evening" if self.game_state['day_time'] < 0.75 else "Night"
        self.time_display.set_text(f"Day {self.game_state['day_count']} - {time_of_day}")

    def update(self, dt):
        """Update game logic"""
        # Update player movement
        self.update_player_movement(dt)
        
        # Update shadow system (less frequently for performance)
        static_frame_count = getattr(self, '_static_frame_count', 0)
        self._static_frame_count = static_frame_count + 1
        
        if self.shadows_enabled and static_frame_count % 2 == 0:  # Update every 2 frames
            self.update_shadows()
        
        # Update interactions
        self.handle_interaction()
        
        # Update crops
        self.update_crops(dt)
        
        # Update time
        self.update_time(dt)
        
        # Update UI
        self.update_ui()

    def apply_camera_offset(self, position):
        """Convert world coordinates to screen coordinates (uses new unified method)"""
        if isinstance(position, (list, tuple)):
            screen_pos = self.camera.world_to_screen(position)
            return (screen_pos.x, screen_pos.y)
        return position

    def get_ambient_color(self):
        """Get ambient color based on time"""
        time_of_day = self.game_state['day_time']
        if time_of_day < 0.25: return (120, 140, 180)
        elif time_of_day < 0.5: return (150, 170, 200)
        elif time_of_day < 0.75: return (180, 150, 140)
        else: return (80, 90, 120)

    def render_world(self, renderer):
        """Render the game world with proper coordinate conversion"""
        # Render parallax background
        self.camera.render_parallax(renderer)
        
        # Render base terrain
        screen_pos = self.apply_camera_offset((0, 0))
        renderer.blit(self.bg_surface, screen_pos)
        
        # Render farm plots
        for plot in self.farm_plots:
            screen_x, screen_y = self.apply_camera_offset(plot['position'])
            size = plot['size'] * self.camera.zoom
            
            # Plot color based on state
            if plot['occupied']:
                if plot['growth_stage'] == 1:
                    plot_color = (180, 160, 120)
                elif plot['growth_stage'] == 2:
                    plot_color = (140, 180, 100)
                else:
                    plot_color = (100, 160, 80)
            else:
                plot_color = (120, 80, 40)
            
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, (80, 50, 20), fill=False)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, plot_color)
        
        # Render trees
        for tree in self.trees:
            screen_x, screen_y = self.apply_camera_offset(tree['position'])
            size = tree['size'] * self.camera.zoom
            
            # Trunk
            trunk_color = (90, 60, 30)
            renderer.draw_rect(screen_x - 5, screen_y - size//2, 10, size//2, trunk_color)
            # Canopy
            canopy_color = (40, 120, 40)
            renderer.draw_circle(screen_x, screen_y - size//4, size//2, canopy_color)
        
        # Render rocks
        for rock in self.rocks:
            screen_x, screen_y = self.apply_camera_offset(rock['position'])
            size = rock['size'] * self.camera.zoom
            rock_color = (100, 100, 120)
            renderer.draw_circle(screen_x, screen_y, size//2, rock_color)
        
        # Render player
        screen_x, screen_y = self.apply_camera_offset(self.player['position'])
        size = self.player['size'] * self.camera.zoom
        
        renderer.draw_circle(screen_x, screen_y, size//2, (170, 150, 240))

    def render(self, renderer):
        """Render the game with optimized shadows"""
        
        # Apply ambient color based on time of day
        ambient_color = self.get_ambient_color()
        renderer.get_surface().fill(ambient_color)
        
        # Render World
        self.render_world(renderer)
        
        # Render market
        if self.market_stall:
            screen_x, screen_y = self.apply_camera_offset(self.market_stall['position'])
            size = self.market_stall['size'] * self.camera.zoom
            market_color = (200, 160, 60)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, market_color)
            renderer.draw_text("Market", screen_x - size//2, screen_y - size//2, (255, 255, 255), pygame.font.SysFont("Arial", 20))
        
        # Render seed shop
        if self.seed_shop:
            screen_x, screen_y = self.apply_camera_offset(self.seed_shop['position'])
            size = self.seed_shop['size'] * self.camera.zoom
            shop_color = (120, 180, 100)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, shop_color)
            renderer.draw_text("Seed Shop", screen_x - size//2, screen_y - size//2, (255, 255, 255), pygame.font.SysFont("Arial", 20))
        
        # Render shadows only if enabled
        if self.shadows_enabled:
            try:
                # Use camera base position (without shake) for shadow calculation
                shadow_surface = self.shadow_system.render(self.camera.base_position, renderer)
                if shadow_surface and isinstance(shadow_surface, pygame.Surface):
                    # Apply shadows with proper blending
                    renderer.blit(shadow_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            except Exception as e:
                # If shadows cause issues, disable them
                print(f"Shadow rendering error: {e}")
                import traceback
                traceback.print_exc()
                self.shadows_enabled = False
                self.shadow_toggle.set_text("Shadows: OFF")

def main():
    """Main function"""
    engine = LunaEngine("Top-Down Farming Game", 1024, 768)
    engine.fps = 60
    
    # Register event handlers
    @engine.on_event(pygame.KEYDOWN)
    def on_key_press(event):
        if engine.current_scene and hasattr(engine.current_scene, 'handle_key_press'):
            engine.current_scene.handle_key_press(event)
    
    engine.add_scene("game", TopDownFarmingGame)
    engine.set_scene("game")
    
    print("=== Top-Down Farming Game with Optimized Shadows ===")
    print("Controls:")
    print("WASD - Move player")
    print("Mouse Click - Interact with objects") 
    print("1-4 - Select tools")
    print("Q/E - Select seeds (when seeds tool is active)")
    print("F1 - Toggle shadows on/off")
    print("\nPress F1 to disable shadows if performance is poor")
    
    engine.run()

if __name__ == "__main__":
    main()