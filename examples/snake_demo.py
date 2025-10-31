import sys
import os
import random
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine # Core Items
from lunaengine.ui.elements import * # UI Elements
from lunaengine.backend.pygame_backend import PygameRenderer # Pygame Renderer
import pygame

class MainMenuScene(Scene):
    CurrentTheme = ThemeType.EMERALD
    SnakeColor = (0, 255, 0)  # Default green snake
    
    def on_enter(self, previous_scene = None):
        super().on_enter(previous_scene)
        
    def on_exit(self, next_scene = None):
        super().on_exit(next_scene)
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Title
        Ui_TitleLabel = TextLabel(512, 80, "Snake Game Demo", 72, root_point=(0.5, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(Ui_TitleLabel)
        
        # Play button
        Ui_PlayButton = Button(512, 200, 200, 42, "[ Play ]", 40, root_point=(0.5, 0.5), theme=self.CurrentTheme)
        Ui_PlayButton.set_on_click(lambda: engine.set_scene("InGame"))
        self.ui_elements.append(Ui_PlayButton)
        
        # Exit button
        Ui_ExitButton = Button(512, 260, 200, 42, "[ Exit ]", 40, root_point=(0.5, 0.5), theme=self.CurrentTheme)
        Ui_ExitButton.set_on_click(lambda: setattr(engine, 'running', False))
        self.ui_elements.append(Ui_ExitButton)
        
        # Theme dropdown
        Ui_ThemeDropdown = Dropdown(512, 330, 200, 30, engine.get_theme_names(), root_point=(0.5, 0.5), theme=self.CurrentTheme)
        Ui_ThemeDropdown.set_on_selection_changed(lambda i, n: self.Ui_update_theme(n, engine))
        self.ui_elements.append(Ui_ThemeDropdown)
        
        # Snake Color Customization Section
        Ui_ColorLabel = TextLabel(512, 400, "Snake Color Customization", 28, root_point=(0.5, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(Ui_ColorLabel)
        
        # Red Slider
        Ui_RedLabel = TextLabel(400, 450, "Red:", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(Ui_RedLabel)
        
        self.Ui_RedSlider = Slider(450, 450, 150, 20, 0, 255, self.SnakeColor[0], root_point=(0, 0.5), theme=self.CurrentTheme)
        self.Ui_RedSlider.on_value_changed = lambda v: self.update_snake_color(0, int(v))
        self.ui_elements.append(self.Ui_RedSlider)
        
        # Green Slider
        Ui_GreenLabel = TextLabel(400, 490, "Green:", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(Ui_GreenLabel)
        
        self.Ui_GreenSlider = Slider(450, 490, 150, 20, 0, 255, self.SnakeColor[1], root_point=(0, 0.5), theme=self.CurrentTheme)
        self.Ui_GreenSlider.on_value_changed = lambda v: self.update_snake_color(1, int(v))
        self.ui_elements.append(self.Ui_GreenSlider)
        
        # Blue Slider
        Ui_BlueLabel = TextLabel(400, 530, "Blue:", 20, root_point=(0, 0.5), theme=self.CurrentTheme)
        self.ui_elements.append(Ui_BlueLabel)
        
        self.Ui_BlueSlider = Slider(450, 530, 150, 20, 0, 255, self.SnakeColor[2], root_point=(0, 0.5), theme=self.CurrentTheme)
        self.Ui_BlueSlider.on_value_changed = lambda v: self.update_snake_color(2, int(v))
        self.ui_elements.append(self.Ui_BlueSlider)
        
        
    def update_snake_color(self, channel: int, value: int):
        """Update snake color when sliders change"""
        new_color = list(self.SnakeColor)
        new_color[channel] = value
        self.SnakeColor = tuple(new_color)
        
    def Ui_update_theme(self, n, engine: LunaEngine):
        self.CurrentTheme = n
        engine.set_global_theme(n)
        
    def update(self, dt):
        pass
            
    def render(self, renderer: PygameRenderer):
        # Draw background
        renderer.draw_rect(0, 0, 1024, 720, ThemeManager.get_theme(ThemeManager.get_current_theme()).background)
        
        # Color preview box
        renderer.draw_rect(750, 450, 100, 100, self.SnakeColor)
        
        # Draw buttons
        for element in self.ui_elements:
            element.render(renderer)
            
class InGameScene(Scene):
    
    def on_enter(self, previous_scene = None):
        return super().on_enter(previous_scene)
    
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        
        # Get snake color from main menu
        self.snake_color = engine.scenes["MainMenu"].SnakeColor if "MainMenu" in engine.scenes else (0, 255, 0)
        
        # Game state
        self.reset_game()
        
        # UI elements
        self.Ui_ScoreLabel = TextLabel(10, 10, f"Score: {self.score}", 24, root_point=(0, 0))
        self.Ui_InfoLabel = TextLabel(10, 40, "WASD/Arrows to move | ESC to menu", 18, root_point=(0, 0))
        self.ui_elements.append(self.Ui_ScoreLabel)
        self.ui_elements.append(self.Ui_InfoLabel)
        
        # Register key events
        @engine.on_event(pygame.KEYDOWN)
        def on_key_press(event):
            self.handle_key_press(event.key)
    
    def reset_game(self):
        """Reset the game to initial state"""
        # Snake properties
        self.cell_size = 20
        self.grid_width = 1024 // self.cell_size
        self.grid_height = 720 // self.cell_size
        
        # Snake starts in the middle
        self.snake = [
            (self.grid_width // 2, self.grid_height // 2),
            (self.grid_width // 2 - 1, self.grid_height // 2),
            (self.grid_width // 2 - 2, self.grid_height // 2)
        ]
        self.direction = (1, 0)  # Start moving right
        self.next_direction = self.direction
        
        # Game state
        self.score = 0
        self.game_over = False
        self.base_speed = 6  # Reduced base speed (moves per second)
        self.speed = self.base_speed
        self.move_timer = 0
        
        # Spawn first apple
        self.spawn_apple()
    
    def spawn_apple(self):
        """Spawn an apple at a random position not occupied by the snake"""
        while True:
            apple_pos = (
                random.randint(0, self.grid_width - 1),
                random.randint(0, self.grid_height - 1)
            )
            if apple_pos not in self.snake:
                self.apple = apple_pos
                break
    
    def handle_key_press(self, key):
        """Handle keyboard input"""
        if key == pygame.K_ESCAPE:
            self.engine.set_scene("MainMenu")
            return
        
        if self.game_over:
            if key == pygame.K_SPACE:
                self.reset_game()
            return
        
        # Movement controls (WASD and Arrows)
        if key in [pygame.K_RIGHT, pygame.K_d] and self.direction != (-1, 0):
            self.next_direction = (1, 0)
        elif key in [pygame.K_LEFT, pygame.K_a] and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif key in [pygame.K_DOWN, pygame.K_s] and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif key in [pygame.K_UP, pygame.K_w] and self.direction != (0, 1):
            self.next_direction = (0, -1)
    
    def update_snake(self):
        """Update snake position and check collisions"""
        # Update direction
        self.direction = self.next_direction
        
        # Calculate new head position with wrap-around
        head_x, head_y = self.snake[0]
        new_head_x = (head_x + self.direction[0]) % self.grid_width
        new_head_y = (head_y + self.direction[1]) % self.grid_height
        new_head = (new_head_x, new_head_y)
        
        # Check collision with self
        if new_head in self.snake:
            self.game_over = True
            return
        
        # Move snake
        self.snake.insert(0, new_head)
        
        # Check if snake ate apple
        if new_head == self.apple:
            self.score += 10
            self.spawn_apple()
            # Increase speed slightly every 3 apples (slower progression)
            if self.score % 30 == 0:
                self.speed = min(12, self.speed + 1)  # Lower max speed
        else:
            # Remove tail if no apple eaten
            self.snake.pop()
    
    def update(self, dt):
        if self.game_over:
            return
            
        # Update movement timer with delay
        self.move_timer += dt
        move_interval = 0.65 / self.speed  # This creates the delay
        
        if self.move_timer >= move_interval:
            self.update_snake()
            self.move_timer = 0
        
        # Update UI
        self.Ui_ScoreLabel.set_text(f"Score: {self.score}")
        
        # Update snake color from main menu
        if "MainMenu" in self.engine.scenes:
            self.snake_color = self.engine.scenes["MainMenu"].SnakeColor
    
    def render(self, renderer: PygameRenderer):
        # Draw background
        current_theme = ThemeManager.get_theme(ThemeManager.get_current_theme())
        renderer.draw_rect(0, 0, 1024, 720, current_theme.background)
        
        # Draw grid (optional, for visual reference)
        grid_color = tuple(max(0, c - 20) for c in current_theme.background)
        for x in range(0, 1024, self.cell_size):
            renderer.draw_line(x, 0, x, 720, grid_color)
        for y in range(0, 720, self.cell_size):
            renderer.draw_line(0, y, 1024, y, grid_color)
        
        # Draw apple
        apple_x = self.apple[0] * self.cell_size
        apple_y = self.apple[1] * self.cell_size
        renderer.draw_rect(apple_x, apple_y, self.cell_size, self.cell_size, (255, 0, 0))
        
        # Draw snake with custom color
        for i, (x, y) in enumerate(self.snake):
            segment_x = x * self.cell_size
            segment_y = y * self.cell_size
            
            # Head is brighter, body is darker
            if i == 0:
                # Bright head
                head_color = tuple(min(255, c + 30) for c in self.snake_color)
                color = head_color
            else:
                # Gradient body color (darker towards tail)
                darken_factor = min(100, i * 8)
                color = tuple(max(0, c - darken_factor) for c in self.snake_color)
            
            renderer.draw_rect(segment_x, segment_y, self.cell_size, self.cell_size, color)
            
            # Draw border around segments
            border_color = tuple(max(0, c - 40) for c in color)
            renderer.draw_rect(segment_x, segment_y, self.cell_size, self.cell_size, border_color, fill=False)
        
        # Draw game over screen
        if self.game_over:
            # Semi-transparent overlay
            overlay = pygame.Surface((1024, 720), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            renderer.draw_surface(overlay, 0, 0)
            
            # Game over text
            font = pygame.font.Font(None, 72)
            game_over_text = font.render("GAME OVER", True, (255, 255, 255))
            score_text = font.render(f"Final Score: {self.score}", True, (255, 255, 255))
            restart_text = font.render("Press SPACE to restart", True, (255, 255, 255))
            
            renderer.draw_surface(game_over_text, 512 - game_over_text.get_width() // 2, 300)
            renderer.draw_surface(score_text, 512 - score_text.get_width() // 2, 380)
            renderer.draw_surface(restart_text, 512 - restart_text.get_width() // 2, 460)
        
        # Draw UI elements
        for element in self.ui_elements:
            element.render(renderer)
            
def main():
    engine = LunaEngine("LunaEngine - Snake Demo", 1024, 720)
    engine.fps = 60
    
    engine.add_scene("MainMenu", MainMenuScene)
    engine.add_scene("InGame", InGameScene)
    engine.set_scene("MainMenu")
    engine.run()
    
if __name__ == "__main__":
    main()