"""
LunaEngine Image Conversion Demo
With quality compression parameter
"""

import sys
import os
import math
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui.elements import *
from lunaengine.utils import EmbeddedImage, ImageConverter
import pygame

class ImageConversionDemoScene(Scene):
    def on_exit(self, next_scene = None):
        return super().on_exit(next_scene)
    
    def on_enter(self, previous_scene = None):
        return super().on_enter(previous_scene)
    def __init__(self, engine: LunaEngine = None):
        super().__init__(engine)
        self.embedded_images = []
        self.animation_time = 0
        self.converted_images = []
        self.selected_image_index = 0
        self.available_images = []
        self.status_message = "Click 'Find Images' to start"
        self.ui_elements_created = False
        self.quality = 1.0  # Default quality
        
    def on_enter(self, previous_scene = None):
        if not self.ui_elements_created:
            self._setup_ui()
            self.ui_elements_created = True
        return super().on_enter(previous_scene)
        
    def _setup_ui(self):
        """Setup all UI elements with proper layout"""
        self.ui_elements.clear()
        
        # Title and subtitle
        title = TextLabel(20, 20, "Image Conversion Demo", 32, (255, 255, 0))
        self.ui_elements.append(title)
        
        subtitle = TextLabel(20, 60, "PYGAME ONLY - NO PILLOW REQUIRED", 18, (100, 255, 100))
        self.ui_elements.append(subtitle)
        
        # Status display
        self.status_text = TextLabel(20, 90, self.status_message, 18, (255, 200, 100))
        self.ui_elements.append(self.status_text)
        
        # Control buttons
        find_btn = Button(20, 130, 150, 40, "Find Images")
        find_btn.set_on_click(self._find_images)
        self.ui_elements.append(find_btn)
        
        convert_all_btn = Button(180, 130, 150, 40, "Convert All Images")
        convert_all_btn.set_on_click(self._convert_all_images)
        self.ui_elements.append(convert_all_btn)
        
        view_btn = Button(340, 130, 180, 40, "View Converted Images")
        view_btn.set_on_click(self._view_converted_images)
        self.ui_elements.append(view_btn)
        
        # Quality slider
        quality_label = TextLabel(20, 190, "Quality/Size:", 16, (200, 200, 255))
        self.ui_elements.append(quality_label)
        
        self.quality_slider = Slider(120, 190, 200, 20, 0.1, 1.0, self.quality)
        self.quality_slider.on_value_changed = self._on_quality_changed
        self.ui_elements.append(self.quality_slider)
        
        self.quality_value = TextLabel(330, 190, f"{self.quality:.1f}", 16, (255, 255, 255))
        self.ui_elements.append(self.quality_value)
        
        # Statistics display
        self.stats_text = TextLabel(20, 220, "Images found: 0 | Converted: 0", 16, (100, 255, 100))
        self.ui_elements.append(self.stats_text)
        
        # Instructions
        instructions = [
            "How to use:",
            "1. Click 'Find Images' to discover images",
            "2. Adjust quality slider for size/quality tradeoff", 
            "3. Select an image from the dropdown",
            "4. Click 'Convert Selected Image' or 'Convert All Images'",
            "5. Click 'View Converted Images' to see results",
            "6. Use arrow keys to cycle through converted images",
            "",
            "Quality: 1.0 = original, 0.5 = half size, 0.25 = quarter size",
            "Supported formats: PNG, JPG, BMP, TGA, TIF"
        ]
        
        for i, instruction in enumerate(instructions):
            text = TextLabel(20, 500 + i * 25, instruction, 16, (200, 200, 255))
            self.ui_elements.append(text)
    
    def _on_quality_changed(self, value):
        """Handle quality slider change"""
        self.quality = value
        self.quality_value.set_text(f"{value:.1f}")
    
    def _find_images(self):
        """Find images in project directory"""
        self.status_message = "Searching for images..."
        self.status_text.set_text(self.status_message)
        
        project_root = Path(__file__).parent.parent
        self.available_images = self._find_image_files(project_root)
        
        if not self.available_images:
            self.status_message = "No images found! Add image files to project."
            self.status_text.set_text(self.status_message)
        else:
            self.status_message = f"Found {len(self.available_images)} images"
            self.status_text.set_text(self.status_message)
            
            # Remove existing dropdown if present
            if hasattr(self, 'image_dropdown'):
                self.ui_elements.remove(self.image_dropdown)
            
            # Create dropdown with unique image names
            image_names = [img.stem for img in self.available_images]
            self.image_dropdown = Dropdown(20, 250, 300, 30, image_names)
            self.ui_elements.append(self.image_dropdown)
            
            # Add Convert Selected button if not present
            if not hasattr(self, 'convert_btn') or self.convert_btn not in self.ui_elements:
                self.convert_btn = Button(20, 290, 200, 40, "Convert Selected Image")
                self.convert_btn.set_on_click(self._convert_selected)
                self.ui_elements.append(self.convert_btn)
    
    def _convert_selected(self):
        """Convert the currently selected image"""
        if self.available_images and hasattr(self, 'image_dropdown'):
            selected_index = self.image_dropdown.selected_index
            if selected_index < len(self.available_images):
                image_path = self.available_images[selected_index]
                converted = self._convert_image_file(image_path, self.quality)
                if converted:
                    self.converted_images.append(converted)
                    self.status_message = f"Converted: {image_path.name} (Quality: {self.quality})"
                    self.status_text.set_text(self.status_message)
    
    def _convert_all_images(self):
        """Convert all found images"""
        if not self.available_images:
            self.status_message = "No images to convert! Click 'Find Images' first."
            self.status_text.set_text(self.status_message)
            return
        
        self.status_message = f"Converting all images (Quality: {self.quality})..."
        self.status_text.set_text(self.status_message)
        
        converted_count = 0
        for image_file in self.available_images[:8]:  # Limit to 8 images
            converted = self._convert_image_file(image_file, self.quality)
            if converted:
                self.converted_images.append(converted)
                converted_count += 1
        
        self.status_message = f"Converted {converted_count} images (Quality: {self.quality})"
        self.status_text.set_text(self.status_message)
    
    def _view_converted_images(self):
        """Show converted images dropdown"""
        if not self.converted_images:
            self.status_message = "No converted images! Convert some images first."
            self.status_text.set_text(self.status_message)
            return
        
        # Remove existing dropdown if present
        if hasattr(self, 'converted_dropdown'):
            self.ui_elements.remove(self.converted_dropdown)
        
        # Create dropdown for converted images
        converted_names = [f"{img['name']} ({img['image'].width}x{img['image'].height})" 
                          for img in self.converted_images]
        self.converted_dropdown = Dropdown(20, 340, 300, 30, converted_names)
        self.converted_dropdown.set_on_selection_changed(
            lambda i, n: setattr(self, 'selected_image_index', i)
        )
        self.ui_elements.append(self.converted_dropdown)
        self.status_message = f"Viewing {len(self.converted_images)} converted images"
        self.status_text.set_text(self.status_message)
    
    def _find_image_files(self, directory: Path, max_depth: int = 3) -> list:
        """Find all image files using Pygame-supported formats"""
        image_files = []
        supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tga', '.tiff'}
        
        def search_path(current_path: Path, depth: int):
            if depth > max_depth:
                return
                
            try:
                for item in current_path.iterdir():
                    if item.is_file() and item.suffix.lower() in supported_extensions:
                        if item.stat().st_size < 10 * 1024 * 1024:  # Skip files >10MB
                            image_files.append(item)
                    elif item.is_dir() and not item.name.startswith('.'):
                        search_path(item, depth + 1)
            except (PermissionError, OSError):
                pass
        
        search_path(directory, 0)
        return image_files
    
    def _convert_image_file(self, image_path: Path, quality: float = 1.0) -> dict:
        """Convert an image file to embedded format with quality setting"""
        try:
            python_code = ImageConverter.image_to_python_code(
                str(image_path),
                output_var_name=f"embedded_{image_path.stem}",
                max_size=(256, 256),  # Max size constraint
                method='compressed',
                quality=quality
            )
            
            # Execute the code to get image data
            namespace = {}
            exec(python_code, namespace)
            image_data = namespace.get(f"embedded_{image_path.stem}")
            
            if not image_data:
                return None
            
            embedded_image = EmbeddedImage(image_data)
            
            # Save the converted code
            output_file = image_path.parent / f"{image_path.stem}_embedded.py"
            with open(output_file, 'w', encoding='utf-8') as f:
                header = [
                    '# Auto-generated by LunaEngine Image Conversion Tool',
                    f'# Source: {image_path.name}',
                    f'# Quality: {quality}',
                    '# Converted with: Pygame + base64 + zlib compression',
                    ''
                ]
                f.write('\n'.join(header) + python_code)
            
            return {
                'name': image_path.stem,
                'path': image_path,
                'image': embedded_image,
                'output_file': output_file,
                'quality': quality
            }
        
        except Exception:
            return None
    
    def _update_stats(self):
        """Update statistics display"""
        found_count = len(self.available_images)
        converted_count = len(self.converted_images)
        self.stats_text.set_text(f"Images found: {found_count} | Converted: {converted_count}")
    
    def update(self, dt):
        self.animation_time += dt
        for element in self.ui_elements:
            element.update(dt)
        self._update_stats()
            
    def render(self, renderer):
        # Draw background
        renderer.draw_rect(0, 0, 800, 600, (30, 30, 50))
        renderer.draw_rect(0, 0, 800, 60, (50, 50, 80))
        
        # Draw converted images in dedicated area
        if self.converted_images:
            current_image = self.converted_images[self.selected_image_index]
            x, y = 450, 150  # Fixed position away from UI
            
            # Draw with subtle animation
            offset_y = math.sin(self.animation_time * 2) * 5
            current_image['image'].draw(renderer, int(x), int(y + offset_y))
            
            # Draw border and info
            renderer.draw_rect(int(x), int(y + offset_y), 
                             current_image['image'].width, 
                             current_image['image'].height, 
                             (255, 255, 255), fill=False)
            
            # Draw image info
            font = pygame.font.Font(None, 20)
            info_text = f"{current_image['name']} - {current_image['image'].width}x{current_image['image'].height}"
            text_surface = font.render(info_text, True, (255, 255, 255))
            renderer.draw_surface(text_surface, x, y + current_image['image'].height + 15)
            
            # Draw quality info
            quality_text = f"Quality: {current_image.get('quality', 1.0):.1f}"
            quality_surface = font.render(quality_text, True, (200, 255, 200))
            renderer.draw_surface(quality_surface, x, y + current_image['image'].height + 35)

def main():
    engine = LunaEngine("Image Conversion Demo", 800, 600)
    
    @engine.on_event(pygame.KEYDOWN)
    def handle_key_event(event):
        if engine.current_scene and hasattr(engine.current_scene, 'converted_images'):
            scene = engine.current_scene
            if scene.converted_images:
                if event.key == pygame.K_RIGHT:
                    scene.selected_image_index = (scene.selected_image_index + 1) % len(scene.converted_images)
                elif event.key == pygame.K_LEFT:
                    scene.selected_image_index = (scene.selected_image_index - 1) % len(scene.converted_images)
    
    engine.add_scene("main", ImageConversionDemoScene)
    engine.set_scene("main")
    engine.run()

if __name__ == "__main__":
    main()