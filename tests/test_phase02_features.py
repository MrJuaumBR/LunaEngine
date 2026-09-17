import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
import pytest
pygame.init()
pygame.display.set_mode((1, 1))

from lunaengine.graphics.image import Image
from lunaengine.graphics.spritesheet import SpriteSheet
from lunaengine.core.audio import AudioChannelGroup


def surface(size=(4, 4), color=(255, 0, 0, 255)):
    s = pygame.Surface(size, pygame.SRCALPHA)
    s.fill(color)
    return s


def test_image_scale_size_alpha_and_cache_invalidation():
    img = Image(surface((4, 2)), scale=0.5)
    assert img.get_surface().get_size() == (2, 1)
    first = img.get_surface()
    assert img.get_surface() is first
    img.set_size((8, 6)).set_alpha(0.5)
    assert img.get_surface().get_size() == (8, 6)
    assert img.get_surface().get_alpha() == 128


def test_image_filter_and_partial_mask_do_not_modify_source():
    src = surface((2, 1), (100, 50, 25, 255))
    mask = surface((2, 1), (255, 255, 255, 255))
    mask.set_at((1, 0), (255, 255, 255, 128))
    img = Image(src, mask=Image(mask)).set_filter('grayscale')
    result = img.get_surface()
    assert result.get_at((0, 0))[0] == result.get_at((0, 0))[1]
    assert result.get_at((1, 0))[3] in (127, 128)
    assert src.get_at((0, 0)) == (100, 50, 25, 255)


def test_spritesheet_image_compatibility(tmp_path):
    path = tmp_path / 'sheet.png'
    pygame.image.save(surface((4, 2)), str(path))
    sheet = SpriteSheet(path)
    assert isinstance(sheet.get_sprite_at_rect((0, 0, 2, 2)), pygame.Surface)
    image = sheet.get_image_at_rect((0, 0, 2, 2))
    assert isinstance(image, Image)
    assert image.get_surface().get_size() == (2, 2)


def test_image_ui_components_accept_image():
    from lunaengine.ui.elements.labels import ImageLabel
    from lunaengine.ui.elements.buttons import ImageButton
    image = Image(surface((3, 3)))
    label = ImageLabel(0, 0, image)
    button = ImageButton(0, 0, image)
    assert label.get_image().get_size() == (3, 3)
    assert button.get_image().get_size() == (3, 3)


def test_nested_audio_group_volume_and_mute():
    class Manager:
        master_volume = 1.0
    root = AudioChannelGroup('root', Manager(), volume=0.8)
    child = AudioChannelGroup('child', Manager(), parent=root, volume=0.5)
    assert child.get_effective_volume() == pytest.approx(0.4)
    child.set_mute(True)
    assert child.get_effective_volume() == 0.0


def test_pagination_large_page_count_has_bounded_visible_window():
    from lunaengine.ui.elements.containers import Pagination
    p = Pagination(0, 0, 420, 40, total_pages=1000, current_page=500, max_visible_pages=7)
    visible = p._calculate_visible_pages()
    assert len(visible) <= 9
    assert 1 in visible and 1000 in visible and 500 in visible
    p.set_area((10, 20, 300, 50))
    assert p.area == (10, 20, 300, 50)


def test_external_theme_loader_round_trip(tmp_path):
    import json
    from lunaengine.ui.themes import ThemeManager
    source = tmp_path / "theme.json"
    built_in = "lunaengine/assets/themes/DRACULA.json"
    with open(built_in, "r", encoding="utf-8") as handle:
        json.dump(json.load(handle), source.open("w", encoding="utf-8"))
    name = ThemeManager.load_custom_theme(source, "test_external_theme", overwrite=True)
    assert name == "test_external_theme"
    assert ThemeManager.has_theme(name)
    assert ThemeManager.unload_custom_theme(name)
