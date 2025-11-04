"""
topdown_farming_demo.py - Top-Down Farming Game Demo with Camera (FIXED)
"""

import sys
import os
import random
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import *
from lunaengine.graphics.camera import Camera, CameraMode
from lunaengine.graphics.particles import ParticleSystem, ParticleConfig, ExitPoint, PhysicsType
import pygame

class TopDownFarmingGame(Scene):
    """Top-Down Farming and Collection Game"""
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.engine.set_global_theme(ThemeType.FOREST)
        
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
            'selected_tool': 'axe',  # axe, pickaxe, scythe, seeds
            'selected_seed': 'wheat',
            'day_time': 0,  # 0-1, where 0.5 is noon
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
        
        # Particle system
        self.particle_system = ParticleSystem(max_particles=1000)
        self.setup_particles()
        
        # Generate world (BEFORE setting up camera)
        self.generate_world()
        
        # Configure camera (AFTER generating world)
        self.setup_camera()
        
        # Setup UI
        self.setup_ui()
        
        # Register events
        @engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
    
    def setup_camera(self):
        """Configure camera for top-down mode"""
        # Reset camera position to player position
        self.camera.position = np.array(self.player['position'], dtype=float)
        self.camera.target_position = np.array(self.player['position'], dtype=float)
        
        self.camera.mode = CameraMode.TOPDOWN
        self.camera.smooth_speed = 0.1  # Reduced for more responsive camera
        self.camera.lead_factor = 0.2   # Reduced lead factor
        
        # Set camera to follow player
        self.camera.set_target(self.player, CameraMode.TOPDOWN)
    
    def setup_particles(self):
        """Setup particles for visual effects"""
        # Collection particles
        collect_config = ParticleConfig(
            color_start=(255, 255, 200),
            color_end=(255, 200, 100),
            size_start=3.0,
            size_end=1.0,
            lifetime=1.0,
            speed=50.0,
            gravity=0.0,
            spread=360.0,
            fade_out=True
        )
        self.particle_system.register_custom_particle("collect", collect_config)
        
        # Planting particles
        plant_config = ParticleConfig(
            color_start=(100, 255, 100),
            color_end=(50, 200, 50),
            size_start=4.0,
            size_end=2.0,
            lifetime=1.5,
            speed=30.0,
            gravity=0.0,
            spread=180.0,
            fade_out=True,
            grow=True
        )
        self.particle_system.register_custom_particle("plant", plant_config)
    
    def generate_world(self):
        """Generate game world with trees, rocks, farm plots, etc."""
        
        # Create player in center
        self.player = {
            'position': [self.world_size[0] // 2, self.world_size[1] // 2],
            'velocity': [0, 0],
            'speed': 200,
            'size': 20
        }
        
        # Generate trees (wood)
        for _ in range(30):
            x = random.randint(100, self.world_size[0] - 100)
            y = random.randint(100, self.world_size[1] - 100)
            self.trees.append({
                'position': [x, y],
                'size': random.randint(30, 50),
                'health': 3,
                'type': 'tree'
            })
        
        # Generate rocks (stone)
        for _ in range(25):
            x = random.randint(100, self.world_size[0] - 100)
            y = random.randint(100, self.world_size[1] - 100)
            self.rocks.append({
                'position': [x, y],
                'size': random.randint(25, 40),
                'health': 4,
                'type': 'rock'
            })
        
        # Generate farm plots
        plot_start_x = 300
        plot_start_y = 300
        for row in range(5):
            for col in range(5):
                x = plot_start_x + col * 80
                y = plot_start_y + row * 80
                self.farm_plots.append({
                    'position': [x, y],
                    'size': 60,
                    'occupied': False,
                    'crop_type': None,
                    'growth_stage': 0,  # 0-3 (0=empty, 3=ready to harvest)
                    'growth_timer': 0
                })
        
        # Generate market
        self.market_stall = {
            'position': [self.world_size[0] - 200, self.world_size[1] // 2],
            'size': 80
        }
        
        # Generate seed shop
        self.seed_shop = {
            'position': [200, self.world_size[1] - 200],
            'size': 80
        }
    
    def setup_ui(self):
        """Setup user interface as a toolbar at the bottom"""
        
        # Get screen dimensions
        screen_width, screen_height = self.engine.width, self.engine.height
        
        # Create toolbar background at the bottom
        toolbar_height = 120
        toolbar_y = screen_height - toolbar_height
        
        toolbar_bg = UiFrame(0, toolbar_y, screen_width, toolbar_height) #0, toolbar_y, screen_width, toolbar_height, (40, 40, 50, 220))
        self.add_ui_element(toolbar_bg)
        
        # Money display
        self.money_display = TextLabel(20, toolbar_y + 15, f"Money: ${self.game_state['money']}", 24, (255, 215, 0))
        self.add_ui_element(self.money_display)
        
        # Inventory display
        self.inventory_display = TextLabel(20, toolbar_y + 45, "Inventory: ", 18, (200, 230, 255))
        self.add_ui_element(self.inventory_display)
        
        # Seeds display
        self.seeds_display = TextLabel(20, toolbar_y + 70, "Seeds: ", 18, (200, 255, 220))
        self.add_ui_element(self.seeds_display)
        
        # Tools section
        tools_x = 250
        tools_title = TextLabel(tools_x, toolbar_y + 15, "Tools & Seeds:", 16, (255, 255, 200))
        self.add_ui_element(tools_title)
        
        # Tool buttons
        self.axe_btn = Button(tools_x, toolbar_y + 40, 100, 30, "Axe (1)")
        self.axe_btn.set_on_click(lambda: self.select_tool('axe'))
        self.add_ui_element(self.axe_btn)
        
        self.pickaxe_btn = Button(tools_x + 110, toolbar_y + 40, 100, 30, "Pickaxe (2)")
        self.pickaxe_btn.set_on_click(lambda: self.select_tool('pickaxe'))
        self.add_ui_element(self.pickaxe_btn)
        
        self.scythe_btn = Button(tools_x, toolbar_y + 80, 100, 30, "Scythe (3)")
        self.scythe_btn.set_on_click(lambda: self.select_tool('scythe'))
        self.add_ui_element(self.scythe_btn)
        
        self.seeds_btn = Button(tools_x + 110, toolbar_y + 80, 100, 30, "Seeds (4)")
        self.seeds_btn.set_on_click(lambda: self.select_tool('seeds'))
        self.add_ui_element(self.seeds_btn)
        
        # Seed selection (when seeds tool is selected)
        self.wheat_seed_btn = Button(tools_x + 220, toolbar_y + 40, 90, 25, "Wheat (Q)")
        self.wheat_seed_btn.set_on_click(lambda: self.select_seed('wheat'))
        self.add_ui_element(self.wheat_seed_btn)
        
        self.corn_seed_btn = Button(tools_x + 320, toolbar_y + 40, 90, 25, "Corn (E)")
        self.corn_seed_btn.set_on_click(lambda: self.select_seed('corn'))
        self.add_ui_element(self.corn_seed_btn)
        
        # Time display
        self.time_display = TextLabel(screen_width - 200, toolbar_y + 15, f"Day {self.game_state['day_count']} - Morning", 16, (255, 200, 150))
        self.add_ui_element(self.time_display)
        
        # Game information (smaller, at the very bottom)
        self.info_display = TextLabel(screen_width // 2, screen_height - 10, "WASD: Move | Mouse: Interact | 1-4: Tools | Q/E: Seeds", 12, (180, 180, 180), root_point=(0.5, 1.0))
        self.add_ui_element(self.info_display)
        
        # Update initial selection
        self.select_tool('axe')
    
    def select_tool(self, tool):
        """Select tool"""
        self.game_state['selected_tool'] = tool
        
        # Update button appearance
        self.axe_btn.enabled = (tool != 'axe')
        self.pickaxe_btn.enabled = (tool != 'pickaxe')
        self.scythe_btn.enabled = (tool != 'scythe')
        self.seeds_btn.enabled = (tool != 'seeds')
    
    def select_seed(self, seed_type):
        """Select seed type"""
        if self.game_state['selected_tool'] == 'seeds':
            self.game_state['selected_seed'] = seed_type
    
    def handle_key_press(self, key):
        """Handle key presses"""
        # Tools
        if key == pygame.K_1:
            self.select_tool('axe')
        elif key == pygame.K_2:
            self.select_tool('pickaxe')
        elif key == pygame.K_3:
            self.select_tool('scythe')
        elif key == pygame.K_4:
            self.select_tool('seeds')
        
        # Seeds (when seeds tool is active)
        if self.game_state['selected_tool'] == 'seeds':
            if key == pygame.K_q:
                self.select_seed('wheat')
            elif key == pygame.K_e:
                self.select_seed('corn')
    
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
    
    def handle_interaction(self):
        """Handle player interactions with world"""
        mouse_pos = pygame.mouse.get_pos()
        world_mouse_pos = self.camera.screen_to_world(mouse_pos)
        
        # Check mouse click
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        if mouse_pressed:
            # Interact based on selected tool
            tool = self.game_state['selected_tool']
            
            if tool == 'axe':
                self.chop_tree(world_mouse_pos)
            elif tool == 'pickaxe':
                self.mine_rock(world_mouse_pos)
            elif tool == 'scythe':
                self.harvest_crop(world_mouse_pos)
            elif tool == 'seeds':
                self.plant_seed(world_mouse_pos)
            
            # Shop interactions (regardless of tool)
            self.interact_with_market(world_mouse_pos)
            self.interact_with_seed_shop(world_mouse_pos)
    
    def chop_tree(self, position):
        """Chop nearby tree"""
        for tree in self.trees[:]:
            distance = math.sqrt((tree['position'][0] - position[0])**2 + (tree['position'][1] - position[1])**2)
            if distance < tree['size']:
                tree['health'] -= 1
                
                # Emit particles
                self.particle_system.emit(
                    x=tree['position'][0], y=tree['position'][1],
                    particle_type="collect",
                    count=5,
                    exit_point=ExitPoint.CIRCULAR,
                    physics_type=PhysicsType.TOPDOWN
                )
                
                if tree['health'] <= 0:
                    self.trees.remove(tree)
                    self.game_state['inventory']['wood'] += 2
                    print("Tree chopped! +2 Wood")
                
                break
    
    def mine_rock(self, position):
        """Mine nearby rock"""
        for rock in self.rocks[:]:
            distance = math.sqrt((rock['position'][0] - position[0])**2 + (rock['position'][1] - position[1])**2)
            if distance < rock['size']:
                rock['health'] -= 1
                
                # Emit particles
                self.particle_system.emit(
                    x=rock['position'][0], y=rock['position'][1],
                    particle_type="collect",
                    count=5,
                    exit_point=ExitPoint.CIRCULAR,
                    physics_type=PhysicsType.TOPDOWN
                )
                
                if rock['health'] <= 0:
                    self.rocks.remove(rock)
                    self.game_state['inventory']['stone'] += 2
                    print("Rock mined! +2 Stone")
                
                break
    
    def plant_seed(self, position):
        """Plant seed in empty plot"""
        if self.game_state['seeds'][self.game_state['selected_seed']] <= 0:
            return
            
        for plot in self.farm_plots:
            distance = math.sqrt((plot['position'][0] - position[0])**2 + (plot['position'][1] - position[1])**2)
            if distance < plot['size'] and not plot['occupied']:
                plot['occupied'] = True
                plot['crop_type'] = self.game_state['selected_seed']
                plot['growth_stage'] = 1
                plot['growth_timer'] = 0
                
                self.game_state['seeds'][self.game_state['selected_seed']] -= 1
                
                # Emit planting particles
                self.particle_system.emit(
                    x=plot['position'][0], y=plot['position'][1],
                    particle_type="plant",
                    count=8,
                    exit_point=ExitPoint.CIRCULAR,
                    physics_type=PhysicsType.TOPDOWN
                )
                
                print(f"Planted {self.game_state['selected_seed']} seed!")
                break
    
    def harvest_crop(self, position):
        """Harvest mature crop"""
        for plot in self.farm_plots:
            distance = math.sqrt((plot['position'][0] - position[0])**2 + (plot['position'][1] - position[1])**2)
            if distance < plot['size'] and plot['occupied'] and plot['growth_stage'] == 3:
                crop_type = plot['crop_type']
                self.game_state['inventory'][crop_type] += 3  # 3 units per harvest
                
                # Reset plot
                plot['occupied'] = False
                plot['crop_type'] = None
                plot['growth_stage'] = 0
                plot['growth_timer'] = 0
                
                # Emit harvest particles
                self.particle_system.emit(
                    x=plot['position'][0], y=plot['position'][1],
                    particle_type="collect",
                    count=10,
                    exit_point=ExitPoint.CIRCULAR,
                    physics_type=PhysicsType.TOPDOWN
                )
                
                print(f"Harvested {crop_type}! +3 {crop_type}")
                break
    
    def interact_with_market(self, position):
        """Sell resources at market"""
        if not self.market_stall:
            return
            
        distance = math.sqrt((self.market_stall['position'][0] - position[0])**2 + 
                           (self.market_stall['position'][1] - position[1])**2)
        
        if distance < self.market_stall['size']:
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
                print(f"Sold all resources for ${total_sale}!")
    
    def interact_with_seed_shop(self, position):
        """Buy seeds at shop"""
        if not self.seed_shop:
            return
            
        distance = math.sqrt((self.seed_shop['position'][0] - position[0])**2 + 
                           (self.seed_shop['position'][1] - position[1])**2)
        
        if distance < self.seed_shop['size']:
            # Buying prices
            prices = {
                'wheat': 10,
                'corn': 15
            }
            
            # Buy 5 seeds of each type if enough money
            for seed_type in ['wheat', 'corn']:
                if self.game_state['money'] >= prices[seed_type] * 5:
                    self.game_state['seeds'][seed_type] += 5
                    self.game_state['money'] -= prices[seed_type] * 5
                    print(f"Bought 5 {seed_type} seeds!")
    
    def update_crops(self, dt):
        """Update crop growth"""
        for plot in self.farm_plots:
            if plot['occupied']:
                plot['growth_timer'] += dt
                
                # Grow every 3 seconds
                if plot['growth_timer'] >= 3:
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
        
        # Seeds
        seeds_text = "Seeds: "
        for seed, quantity in self.game_state['seeds'].items():
            seeds_text += f"{seed}:{quantity} "
        self.seeds_display.set_text(seeds_text)
        
        # Time
        time_of_day = "Morning" if self.game_state['day_time'] < 0.25 else \
                     "Noon" if self.game_state['day_time'] < 0.5 else \
                     "Evening" if self.game_state['day_time'] < 0.75 else "Night"
        self.time_display.set_text(f"Day {self.game_state['day_count']} - {time_of_day}")
    
    def update(self, dt):
        """Update game logic"""
        # Update player movement
        self.update_player_movement(dt)
        
        # Update camera
        self.camera.update(dt)
        
        # Update interactions
        self.handle_interaction()
        
        # Update crops
        self.update_crops(dt)
        
        # Update time
        self.update_time(dt)
        
        # Update particles
        self.particle_system.update(dt)
        
        # Update UI
        self.update_ui()
    
    def apply_camera_offset(self, position):
        """Apply camera offset to convert world coordinates to screen coordinates"""
        if isinstance(position, (list, tuple)):
            return self.camera.world_to_screen(position).xy
        elif hasattr(position, 'x') and hasattr(position, 'y'):
            return self.camera.world_to_screen(position.x, position.y).xy
        return position
    
    def render(self, renderer):
        """Render the game with camera support"""
        # Background color based on time of day
        day_time = self.game_state['day_time']
        if day_time < 0.25:  # Morning
            bg_color = (100, 150, 200)  # Soft blue
        elif day_time < 0.5:  # Noon
            bg_color = (120, 180, 220)  # Bright blue
        elif day_time < 0.75:  # Evening
            bg_color = (220, 140, 80)   # Warm orange
        else:  # Night
            bg_color = (20, 30, 60)     # Deep blue
        
        # Draw world background (fixed to world coordinates)
        grass_dark = (80, 160, 80)
        grass_light = (100, 180, 100)
        
        for x in range(0, self.world_size[0], 100):
            for y in range(0, self.world_size[1], 100):
                grass_color = grass_dark if (x // 100 + y // 100) % 2 == 0 else grass_light
                screen_x, screen_y = self.apply_camera_offset((x, y))
                renderer.draw_rect(screen_x, screen_y, 100, 100, grass_color)
        
        # Render farm plots WITH CAMERA OFFSET
        for plot in self.farm_plots:
            world_x, world_y = plot['position']
            screen_x, screen_y = self.apply_camera_offset((world_x, world_y))
            size = plot['size']
            
            # Plot color based on state
            if plot['occupied']:
                if plot['growth_stage'] == 1:
                    plot_color = (180, 160, 120)  # Light brown - planted
                elif plot['growth_stage'] == 2:
                    plot_color = (140, 180, 100)  # Medium green - growing
                else:
                    plot_color = (100, 160, 80)   # Dark green - ready
            else:
                plot_color = (120, 80, 40)  # Rich brown - empty
            
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, plot_color)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, (80, 50, 20), fill=False)
        
        # Render trees WITH CAMERA OFFSET
        for tree in self.trees:
            world_x, world_y = tree['position']
            screen_x, screen_y = self.apply_camera_offset((world_x, world_y))
            size = tree['size']
            
            # Trunk
            trunk_color = (90, 60, 30)
            renderer.draw_rect(screen_x - 5, screen_y - size//2, 10, size//2, trunk_color)
            # Canopy
            canopy_color = (40, 120, 40)
            renderer.draw_circle(screen_x, screen_y - size//4, size//2, canopy_color)
        
        # Render rocks WITH CAMERA OFFSET
        for rock in self.rocks:
            world_x, world_y = rock['position']
            screen_x, screen_y = self.apply_camera_offset((world_x, world_y))
            size = rock['size']
            rock_color = (100, 100, 120)
            renderer.draw_circle(screen_x, screen_y, size//2, rock_color)
        
        # Render market WITH CAMERA OFFSET
        if self.market_stall:
            world_x, world_y = self.market_stall['position']
            screen_x, screen_y = self.apply_camera_offset((world_x, world_y))
            size = self.market_stall['size']
            market_color = (200, 160, 60)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, market_color)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, (160, 120, 40), fill=False)
            
            # Market text - UI element, render normally
            market_text = TextLabel(screen_x, screen_y - size, "MARKET", 16, (255, 255, 200), root_point=(0.5, 0.5))
            market_text.render(renderer)
        
        # Render seed shop WITH CAMERA OFFSET
        if self.seed_shop:
            world_x, world_y = self.seed_shop['position']
            screen_x, screen_y = self.apply_camera_offset((world_x, world_y))
            size = self.seed_shop['size']
            shop_color = (120, 180, 100)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, shop_color)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, (80, 140, 60), fill=False)
            
            # Shop text - UI element, render normally
            shop_text = TextLabel(screen_x, screen_y - size, "SEED SHOP", 16, (255, 255, 200), root_point=(0.5, 0.5))
            shop_text.render(renderer)
        
        # Render player
        screen_x, screen_y = self.apply_camera_offset(self.player['position'])
        size = self.player['size']
        
        # Player color based on selected tool
        tool_colors = {
            'axe': (200, 100, 100),      # Red
            'pickaxe': (150, 150, 180),  # Blue-gray
            'scythe': (100, 180, 100),   # Green
            'seeds': (220, 200, 100)     # Yellow
        }
        player_color = tool_colors.get(self.game_state['selected_tool'], (100, 150, 220))
        
        renderer.draw_circle(screen_x, screen_y, size//2, player_color)
        
        # Direction indicator
        if self.player['velocity'][0] != 0 or self.player['velocity'][1] != 0:
            dir_x = screen_x + self.player['velocity'][0] * size
            dir_y = screen_y + self.player['velocity'][1] * size
            renderer.draw_line(screen_x, screen_y, dir_x, dir_y, (255, 255, 255), 3)

def main():
    """Main function"""
    engine = LunaEngine("Top-Down Farming Game", 1024, 768, use_opengl=True)
    engine.fps = 60
    
    engine.add_scene("game", TopDownFarmingGame)
    engine.set_scene("game")
    
    print("=== Top-Down Farming Game ===")
    print("Controls:")
    print("WASD - Move player")
    print("Mouse Click - Interact with objects")
    print("1 - Axe (chop trees)")
    print("2 - Pickaxe (mine rocks)") 
    print("3 - Scythe (harvest crops)")
    print("4 - Seeds (plant crops)")
    print("Q/E - Select seed type (when seeds tool is active)")
    print("Click Market - Sell all resources")
    print("Click Seed Shop - Buy seeds")
    print("\nGameplay:")
    print("- Chop trees and mine rocks to get resources")
    print("- Sell resources at the market for money")
    print("- Buy seeds at the seed shop")
    print("- Plant seeds in empty farm plots")
    print("- Wait for crops to grow (3 stages)")
    print("- Harvest grown crops with scythe")
    print("- Sell crops for more money!")
    
    engine.run()

if __name__ == "__main__":
    main()