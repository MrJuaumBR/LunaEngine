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
from lunaengine.utils import distance
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
        self.setup_parallax()
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
        self.camera.smooth_speed = 0.1
        self.camera.lead_factor = 0.2
        
        # Set zoom limits to prevent extreme zoom
        self.camera.zoom = 1.0
        self.camera.target_zoom = 1.0
        self.camera.min_zoom = 0.5  # Add minimum zoom
        self.camera.max_zoom = 2.0  # Add maximum zoom
        
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
        
        grass_dark = (80, 160, 80)
        grass_light = (100, 180, 100)
        
        self.bg_surface = pygame.Surface((self.world_size[0], self.world_size[1]), pygame.SRCALPHA)
        # Generate world tiles
        for x in range(0, self.world_size[0], 100):
            for y in range(0, self.world_size[1], 100):
                grass_color = grass_dark if (x // 100 + y // 100) % 2 == 0 else grass_light
                pygame.draw.rect(self.bg_surface, grass_color, (x, y, 100, 100))
                # self.engine.renderer.draw_rect(x, y, 100, 100, grass_color, surface=self.bg_surface)
        
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
        
        # Place market and seed shop next to each other
        shop_y = self.world_size[1] // 2
        self.market_stall = {
            'position': [self.world_size[0] - 250, shop_y],  # Moved closer together
            'size': 80
        }
        
        self.seed_shop = {
            'position': [self.world_size[0] - 450, shop_y],  # Placed next to market
            'size': 80
        }

    
    def setup_parallax(self):
        """Setup optimized parallax background"""
        # Clear any existing layers
        self.camera.clear_parallax_layers()
        
        # Create optimized parallax surfaces
        sky_surface = self.create_sky_surface()
        far_mountains = self.create_far_mountains_surface()
        near_hills = self.create_near_hills_surface()
        
        # Add layers with optimized settings
        self.camera.add_parallax_layer(sky_surface, 0.05, tile_mode=True)
        self.camera.add_parallax_layer(far_mountains, 0.2, tile_mode=True)
        self.camera.add_parallax_layer(near_hills, 0.4, tile_mode=True)
        
        # Enable parallax
        self.camera.enable_parallax(True)

    def create_sky_surface(self):
        """Create sky background (very slow moving)"""
        surface = pygame.Surface((800, 600))
        # Gradient sky
        for y in range(600):
            # Blue gradient from dark to light
            blue_value = 100 + int(100 * (y / 600))
            color = (50, 50, blue_value)
            pygame.draw.line(surface, color, (0, y), (800, y))
        
        # Add some clouds
        cloud_color = (200, 200, 220, 180)
        pygame.draw.ellipse(surface, cloud_color, (100, 80, 200, 60))
        pygame.draw.ellipse(surface, cloud_color, (500, 120, 150, 50))
        pygame.draw.ellipse(surface, cloud_color, (300, 150, 180, 40))
        
        return surface

    def create_far_mountains_surface(self):
        """Create far mountains surface"""
        surface = pygame.Surface((1200, 400), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        
        # Draw distant mountains
        mountain_color = (60, 60, 90, 200)
        for i in range(4):
            x = i * 300
            height = 150 + (i % 2) * 50
            points = [
                (x, 400),
                (x + 150, 400 - height),
                (x + 300, 400)
            ]
            pygame.draw.polygon(surface, mountain_color, points)
        
        return surface

    def create_near_hills_surface(self):
        """Create near hills surface"""
        surface = pygame.Surface((800, 300), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        
        # Draw hills
        hill_color = (50, 80, 50, 220)
        for i in range(3):
            x = i * 250 - 50
            pygame.draw.ellipse(surface, hill_color, (x, 200, 400, 200))
        
        # Add some simple trees
        tree_color = (40, 70, 40, 240)
        for x in [100, 300, 500, 700]:
            # Tree trunk
            pygame.draw.rect(surface, tree_color, (x, 250, 8, 50))
            # Tree top
            pygame.draw.circle(surface, tree_color, (x + 4, 240), 20)
        
        return surface
    
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
        
        self.seed_shop_ui = self.create_seed_shop_ui()
        self.seed_shop_open = False
    
    def create_seed_shop_ui(self):
        """Create seed shop purchase UI"""
        # Create a modal background
        shop_background = UiFrame(200, 150, 600, 400)
        shop_background.visible = False
        
        # Title
        title = TextLabel(500, 170, "SEED SHOP", 28, (255, 255, 200), root_point=(0.5, 0))
        title.visible = False
        
        # Seed selection buttons
        wheat_btn = Button(300, 220, 200, 50, "Wheat Seeds - $10")
        wheat_btn.visible = False
        wheat_btn.set_on_click(lambda: self.purchase_seeds('wheat', 10))
        
        corn_btn = Button(300, 290, 200, 50, "Corn Seeds - $15") 
        corn_btn.visible = False
        corn_btn.set_on_click(lambda: self.purchase_seeds('corn', 15))
        
        # Quantity selection
        self.seed_quantity = 5
        quantity_label = TextLabel(300, 360, f"Quantity: {self.seed_quantity}", 20, (200, 230, 255))
        quantity_label.visible = False
        
        quantity_up = Button(450, 355, 40, 30, "+")
        quantity_up.visible = False
        quantity_up.set_on_click(lambda: self.change_seed_quantity(1, quantity_label))
        
        quantity_down = Button(500, 355, 40, 30, "-")
        quantity_down.visible = False
        quantity_down.set_on_click(lambda: self.change_seed_quantity(-1, quantity_label))
        
        # Close button
        close_btn = Button(400, 420, 150, 40, "Close Shop")
        close_btn.visible = False
        close_btn.set_on_click(self.close_seed_shop)
        
        # Store UI elements
        shop_elements = [
            shop_background, title, wheat_btn, corn_btn, 
            quantity_label, quantity_up, quantity_down, close_btn
        ]
        
        # Add to scene but keep hidden initially
        for element in shop_elements:
            self.add_ui_element(element)
        
        return shop_elements
    
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
    
    def get_interaction_distance(self):
        """Get maximum interaction distance based on zoom"""
        base_distance = 80  # Base interaction distance
        # Adjust distance based on zoom (closer zoom = smaller interaction area)
        zoom_factor = 1.0 / self.camera.zoom
        return base_distance * zoom_factor
    
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
        
        # Get Mouse wheel with controlled zoom
        if self.engine.mouse_wheel != 0:
            zoom_speed = 0.05  # Reduced zoom speed for smoother control
            new_zoom = self.camera.zoom + (self.engine.mouse_wheel * zoom_speed)
            # Clamp zoom between min and max values
            new_zoom = max(self.camera.min_zoom, min(self.camera.max_zoom, new_zoom))
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
    
    def handle_interaction(self):
        """Handle player interactions with world"""
        
        if self.engine._mouse_buttons.left:
            # Interact based on selected tool
            tool = self.game_state['selected_tool']
            ppos = self.player['position']
            mpos = self.camera.screen_to_world(self.engine.mouse_pos)
            
            if tool == 'axe':
                self.chop_tree(ppos, mpos)
            elif tool == 'pickaxe':
                self.mine_rock(ppos, mpos)
            elif tool == 'scythe':
                self.chop_grass(ppos, mpos)
            elif tool == 'seeds':
                self.plant_seed(ppos, mpos)
            
            # Shop interactions (regardless of tool)
            self.interact_with_market(ppos, mpos)
            self.interact_with_seed_shop(ppos, mpos)
    
    def chop_tree(self, position, mouse_pos):
        """Chop nearby tree with distance limit"""
        interaction_distance = self.get_interaction_distance()
        
        for tree in self.trees[:]:
            dis = distance(tree['position'], position)
            mdis = distance(tree['position'], mouse_pos)
            
            if dis < interaction_distance and mdis < tree['size'] + 20:
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

    
    def mine_rock(self, position, mouse_pos):
        """Mine nearby rock with distance limit"""
        interaction_distance = self.get_interaction_distance()
        
        for rock in self.rocks[:]:
            dis = distance(rock['position'], position)
            mdis = distance(rock['position'], mouse_pos)
            # Check if within interaction distance AND close enough to the rock
            if dis < interaction_distance and mdis < rock['size'] + 20:
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
    
    def plant_seed(self, position, mouse_pos):
        """Plant seed in empty plot with distance limit"""
        if self.game_state['seeds'][self.game_state['selected_seed']] <= 0:
            return
            
        interaction_distance = self.get_interaction_distance()
        
        for plot in self.farm_plots:
            dis = distance(plot['position'], position)
            mdis = distance(plot['position'], mouse_pos)
            # Check if within interaction distance AND close enough to the plot
            if dis < interaction_distance and mdis < plot['size']+20 and not plot['occupied']:
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

    
    def harvest_crop(self, position, mouse_pos):
        """Harvest mature crop with distance limit"""
        interaction_distance = self.get_interaction_distance()
        
        for plot in self.farm_plots:
            dis = distance(plot['position'], position)
            mdis = distance(plot['position'], mouse_pos)
            # Check if within interaction distance AND close enough to the plot
            if distance < interaction_distance and mdis < plot['size'] + 20 and plot['occupied'] and plot['growth_stage'] == 3:
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
                print(f"Sold all resources for ${total_sale}!")
    
    def show_seed_shop_ui(self):
        """Show seed shop UI"""
        self.seed_shop_open = True
        self.engine.visibility_change(self.seed_shop_ui, True)

    def close_seed_shop(self):
        """Close seed shop UI"""
        self.seed_shop_open = False
        self.engine.visibility_change(self.seed_shop_ui, False)

    def change_seed_quantity(self, change, label):
        """Change seed purchase quantity"""
        self.seed_quantity = max(1, min(20, self.seed_quantity + change))
        label.set_text(f"Quantity: {self.seed_quantity}")

    def purchase_seeds(self, seed_type, price_per_seed):
        """Purchase seeds of specified type"""
        total_cost = price_per_seed * self.seed_quantity
        
        if self.game_state['money'] >= total_cost:
            self.game_state['seeds'][seed_type] += self.seed_quantity
            self.game_state['money'] -= total_cost
            print(f"Purchased {self.seed_quantity} {seed_type} seeds for ${total_cost}!")
            self.close_seed_shop()
        else:
            print(f"Not enough money! Need ${total_cost}, but only have ${self.game_state['money']}.")

    def interact_with_seed_shop(self, position, mouse_pos):
        """Buy seeds at shop with UI"""
        if not self.seed_shop:
            return
            
        dis = distance(self.seed_shop['position'], position)
        mdis = distance(self.seed_shop['position'], mouse_pos)
        if (not self.seed_shop_open) and dis < self.get_interaction_distance() and mdis < self.seed_shop['size'] + 20:
            self.show_seed_shop_ui()
    
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
        """Apply camera offset to convert world coordinates to screen coordinates - FIXED"""
        if isinstance(position, (list, tuple)):
            screen_pos = self.camera.world_to_screen(position)
            return (screen_pos.x, screen_pos.y)
        elif hasattr(position, 'x') and hasattr(position, 'y'):
            screen_pos = self.camera.world_to_screen((position.x, position.y))
            return (screen_pos.x, screen_pos.y)
        return position
    
    def render(self, renderer):
        """Render the game with camera support"""
        
        self.camera.render_parallax(renderer)
        
        renderer.blit(pygame.transform.scale(self.bg_surface, self.camera.convert_size_zoom(self.world_size)), self.apply_camera_offset((0, 0)))
        
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
            
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, (80, 50, 20), fill=False)
            renderer.draw_rect(screen_x - size//2, screen_y - size//2, size, size, plot_color)
        
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
        size = self.camera.convert_size_zoom(self.player['size'])
        
        # Player color based on selected tool
        tool_colors = {
            'axe': (200, 100, 100),      # Red
            'pickaxe': (150, 150, 180),  # Blue-gray
            'scythe': (100, 180, 100),   # Green
            'seeds': (220, 200, 100)     # Yellow
        }
        
        renderer.draw_circle(screen_x, screen_y, size//2, (70, 130, 200))
        
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