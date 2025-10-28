import pygame
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.ui.elements import TextLabel, Button, Slider
from lunaengine.backend.pygame_backend import PygameRenderer

def working_ui_direct():
    """Test UI elements working directly without the engine"""
    print("=== Direct UI Test (No Engine) ===")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Direct UI Test")
    
    renderer = PygameRenderer(800, 600)
    renderer.initialize()
    
    # Create UI elements directly
    title = TextLabel(50, 50, "Direct UI Test - Should Work", 32, (255, 255, 0))
    button = Button(50, 100, 200, 50, "Direct Button")
    slider = Slider(50, 170, 200, 30)
    
    elements = [title, button, slider]
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update elements
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        for element in elements:
            element._update_with_mouse(mouse_pos, mouse_pressed, dt)
        
        # Render
        renderer.begin_frame()
        renderer.draw_rect(0, 0, 800, 600, (30, 30, 50))
        
        # Render elements
        for element in elements:
            element.render(renderer)
            
            # Draw debug borders
            renderer.draw_rect(element.x, element.y, element.width, element.height, (255, 0, 0), fill=False)
        
        # Draw to screen
        screen.blit(renderer.get_surface(), (0, 0))
        pygame.display.flip()
    
    pygame.quit()
    print("Direct UI test completed!")

if __name__ == "__main__":
    working_ui_direct()