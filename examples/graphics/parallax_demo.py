import sys
import os
import random
import pygame
from pygame.math import Vector2

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import LunaEngine, Scene
from lunaengine.ui import *
from lunaengine.graphics.camera import ParallaxSprite, CameraMode


class Player:
    def __init__(self, x: float, y: float):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.velocity = Vector2(0, 0)
        self.on_ground = False
        self.speed = 300
        self.jump_power = -500
        self.gravity = 1000

    def update(self, dt: float, platforms):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity.x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity.x = self.speed

        self.velocity.y += self.gravity * dt
        self.rect.x += self.velocity.x * dt
        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.velocity.x > 0:
                    self.rect.right = plat.left
                elif self.velocity.x < 0:
                    self.rect.left = plat.right

        self.rect.y += self.velocity.y * dt
        self.on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat):
                if self.velocity.y > 0:
                    self.rect.bottom = plat.top
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0:
                    self.rect.top = plat.bottom
                    self.velocity.y = 0

        if self.on_ground and (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]):
            self.velocity.y = self.jump_power

        if self.rect.bottom > 800:
            self.rect.bottom = 800
            self.velocity.y = 0
            self.on_ground = True

    def draw(self, renderer, camera):
        center = camera.world_to_screen(self.rect.center)
        size = self.rect.width * camera.zoom
        bw = max(2, int(2 * camera.zoom))
        renderer.draw_rect(center.x - size/2 - bw, center.y - size/2 - bw,
                          size + bw*2, size + bw*2, (80,50,20), fill=True)
        renderer.draw_rect(center.x - size/2, center.y - size/2, size, size, (255,140,0), fill=True)
        eye_r = size * 0.1
        eye_off = size * 0.25
        eye_y = center.y - size * 0.2
        renderer.draw_circle(center.x - eye_off, eye_y, eye_r, (255,255,255), fill=True)
        renderer.draw_circle(center.x + eye_off, eye_y, eye_r, (255,255,255), fill=True)
        renderer.draw_circle(center.x - eye_off, eye_y, eye_r*0.5, (0,0,0), fill=True)
        renderer.draw_circle(center.x + eye_off, eye_y, eye_r*0.5, (0,0,0), fill=True)


class GameScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self._init_game()

    def _init_game(self):
        self.world_width = 3000
        self.world_height = 800

        self.platforms = [
            pygame.Rect(0, 750, 3000, 50),
            pygame.Rect(300, 700, 150, 20),
            pygame.Rect(600, 650, 150, 20),
            pygame.Rect(900, 550, 150, 20),
            pygame.Rect(1200, 450, 150, 20),
            pygame.Rect(1500, 450, 150, 20),
            pygame.Rect(1800, 400, 150, 20),
            pygame.Rect(2100, 500, 150, 20),
            pygame.Rect(2400, 600, 150, 20),
            pygame.Rect(2700, 700, 150, 20),
        ]

        self.coins = []
        coin_positions = [
            (350,685),(650,635),(950,535),(1250,435),(1550,435),
            (1850,385),(2150,485),(2450,585),(2750,685)
        ]
        for x,y in coin_positions:
            self.coins.append(pygame.Rect(x,y,20,20))
        self.score = 0

        self.player = Player(100, 718)
        self.player.update(0.016, self.platforms)

        self.camera.set_target(self.player, CameraMode.PLATFORMER)
        self.camera.deadzone = pygame.Rect(0,0,200,150)
        self.camera.deadzone.center = (self.engine.width//2, self.engine.height//2)
        self.camera.constraints.bounds = pygame.Rect(0,0,self.world_width,self.world_height)
        self.camera.set_zoom(1.0)
        self.camera.smooth_speed = 0.1
        self.camera.position = Vector2(self.player.rect.centerx, self.player.rect.centery)
        self.camera.target_position = self.camera.position.copy()
        self.camera.update(0)   # force viewport initialisation

        self.camera.parallax.clear()
        self._setup_parallax()

        self.ui_elements.clear()
        self.score_label = TextLabel(20,20, f"Score: {self.score}", 24, (255,255,0))
        self.add_ui_element(self.score_label)
        help_label = TextLabel(20,60, "L/R/A/D  |  Space/Up/W  |  R restart", 16, (200,200,200))
        self.add_ui_element(help_label)

    def _setup_parallax(self):
        # Sky (tiled)
        sky_surf = pygame.Surface((100,100))
        sky_surf.fill((135,206,235))
        sky_layer = self.camera.parallax.add_layer(speed=(0.0,0.0), repeat_x=True, repeat_y=True, z_index=0)
        sky_layer.set_tiled_texture(sky_surf)

        # Sun (single, drifts)
        sun_surf = pygame.Surface((80,80), pygame.SRCALPHA)
        pygame.draw.circle(sun_surf, (255,220,100), (40,40), 35)
        pygame.draw.circle(sun_surf, (255,255,180), (40,40), 25)
        sun_layer = self.camera.parallax.add_layer(speed=(0.05,0.0), z_index=1)
        sun_sprite = ParallaxSprite(
            surface=sun_surf,
            base_pos=Vector2(500, 200),
            scale=1.0, alpha=1.0, wind_movement=False
        )
        sun_layer.add_sprite(sun_sprite)

        # Clouds (6 sprites, no wind)
        cloud_surf = pygame.Surface((100,50), pygame.SRCALPHA)
        pygame.draw.ellipse(cloud_surf, (240,240,240,200), (0,10,40,30))
        pygame.draw.ellipse(cloud_surf, (240,240,240,200), (25,5,45,35))
        pygame.draw.ellipse(cloud_surf, (240,240,240,200), (55,15,40,30))
        cloud_layer = self.camera.parallax.add_layer(speed=(0.2,0.0), z_index=2)
        for x in range(200, self.world_width, 500):
            y = random.uniform(250, 350)
            sprite = ParallaxSprite(
                surface=cloud_surf,
                base_pos=Vector2(x, y),
                scale=1.0, alpha=1.0, wind_movement=False
            )
            cloud_layer.add_sprite(sprite)

        # Trees (15 sprites, static)
        tree_surf = pygame.Surface((40,70), pygame.SRCALPHA)
        pygame.draw.rect(tree_surf, (100,60,30), (15,40,10,30))
        pygame.draw.polygon(tree_surf, (50,130,50), [(20,5),(5,45),(35,45)])
        pygame.draw.polygon(tree_surf, (70,150,70), [(20,15),(10,45),(30,45)])
        tree_layer = self.camera.parallax.add_layer(speed=(0.7,0.0), z_index=3)
        for x in range(100, self.world_width, 180):   # every 180px
            scale = random.uniform(0.9, 1.1)
            tree_height = 70 * scale
            center_y = 750 - (tree_height / 2)
            sprite = ParallaxSprite(
                surface=tree_surf,
                base_pos=Vector2(x, center_y),
                scale=scale,
                alpha=1.0,
                wind_movement=False,
                oscillate_x=0, oscillate_y=0
            )
            tree_layer.add_sprite(sprite)

    def restart(self):
        self.engine.add_scene("game", GameScene)
        self.engine.set_scene("game")

    def update(self, dt: float):
        self.player.update(dt, self.platforms)
        self.camera.set_target(self.player, CameraMode.PLATFORMER)

        for coin in self.coins[:]:
            if self.player.rect.colliderect(coin):
                self.coins.remove(coin)
                self.score += 10
                self.score_label.set_text(f"Score: {self.score}")

        if pygame.key.get_pressed()[pygame.K_r]:
            self.restart()

    def render_world(self, renderer):
        for plat in self.platforms:
            tl = self.camera.world_to_screen((plat.left, plat.top))
            w = plat.width * self.camera.zoom
            h = plat.height * self.camera.zoom
            renderer.draw_rect(tl.x, tl.y, w, h, (101,67,33), fill=True)
            renderer.draw_rect(tl.x, tl.y, w, 3, (80,50,20), fill=True)
        for coin in self.coins:
            c = self.camera.world_to_screen(coin.center)
            r = (coin.width/2) * self.camera.zoom
            renderer.draw_circle(c.x, c.y, r, (255,215,0), fill=True)
            renderer.draw_circle(c.x-2, c.y-2, r*0.3, (255,255,150), fill=True)

    def render(self, renderer):
        self.camera.parallax.render(renderer)
        self.render_world(renderer)
        self.player.draw(renderer, self.camera)


def main():
    engine = LunaEngine("Platformer Demo", 1024, 768, debug=True)
    engine.fps = 60
    engine.add_scene("game", GameScene)
    engine.set_scene("game")
    engine.run()

if __name__ == "__main__":
    main()