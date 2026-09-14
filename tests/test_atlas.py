from pathlib import Path

from lunaengine.storage.atlas import Atlas, AtlasCategory


def test_atlas_resolves_root_prefixed_resources(tmp_path: Path):
    asset = tmp_path / "assets" / "hero.png"
    asset.parent.mkdir()
    asset.write_bytes(b"test-image")

    atlas = Atlas(tmp_path)
    item = atlas.add_to_atlas("hero", "root/assets/hero.png", AtlasCategory.TEXTURE)

    assert item.path == asset.resolve()
    assert atlas.get_item("hero") is item
    assert atlas.get_bytes("hero") == b"test-image"


def test_atlas_folder_registration(tmp_path: Path):
    folder = tmp_path / "textures"
    folder.mkdir()

    atlas = Atlas(tmp_path)
    item = atlas.add_folder("textures", folder)

    assert item.category is AtlasCategory.FOLDER
    assert atlas.get_item("textures") is item
