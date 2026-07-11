from pathlib import Path
from enum import Enum
from typing import Dict, Optional, Union, List, Tuple, Callable
import os
import json
import zipfile
import zlib
import io
import time

class AtlasCategory(Enum):
    TEXTURE   = 'texture'
    FONT      = 'font'
    AUDIO     = 'audio'
    FOLDER    = 'folder'
    SRC       = 'src'
    DATASTORE = 'datastore'
    UNKNOWN   = 'unknown'

CATEGORY_EXTENSIONS = {
    AtlasCategory.TEXTURE:   ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tga', 'dds'],
    AtlasCategory.FONT:      ['ttf', 'otf', 'woff', 'woff2'],
    AtlasCategory.AUDIO:     ['mp3', 'wav', 'ogg', 'flac', 'aac'],
    AtlasCategory.SRC:       ['py', 'js', 'cpp', 'c', 'h', 'hpp', 'java', 'rs', 'go'],
    AtlasCategory.DATASTORE: ['json', 'db', 'sqlite', 'sqlite3', 'yaml', 'yml'],
}

class AtlasItem:
    def __init__(self, name: str, path: Path, category: AtlasCategory = AtlasCategory.UNKNOWN, *, validate: bool = True):
        self.name = name
        self.path = path
        self.category = category
        self._data: Optional[bytes] = None
        if validate and category not in (AtlasCategory.FOLDER, AtlasCategory.UNKNOWN):
            ext = path.suffix.lower().lstrip('.')
            allowed = CATEGORY_EXTENSIONS.get(category, [])
            if ext not in allowed:
                raise ValueError(
                    f"File '{path}' has extension '.{ext}' which is not allowed for category '{category.value}'. "
                    f"Allowed: {allowed or 'none'}"
                )

class Atlas:
    def __init__(self, root_path: Optional[Union[str, Path]] = None):
        self.root_path = Path(root_path).resolve() if root_path else Path(os.path.dirname(os.path.abspath(__file__)))
        self.atlas: Dict[str, AtlasItem] = {}
        # Bundle state
        self._bundle_path: Optional[Path] = None
        self._bundle_data: Dict[str, bytes] = {}
        self._use_bundle: bool = False
        self._bundle_manifest: Optional[dict] = None

    @staticmethod
    def guess_category_from_path(path: Path) -> AtlasCategory:
        if path.is_dir():
            return AtlasCategory.FOLDER
        ext = path.suffix.lower().lstrip('.')
        for cat, exts in CATEGORY_EXTENSIONS.items():
            if ext in exts:
                return cat
        return AtlasCategory.UNKNOWN

    def add_to_atlas(
        self,
        name: str,
        path: Union[str, Path],
        category: Optional[AtlasCategory] = None,
        *,
        auto_detect: bool = True,
        validate: bool = True
    ) -> AtlasItem:
        path = Path(path).resolve()
        if category is None:
            category = self.guess_category_from_path(path) if auto_detect else AtlasCategory.UNKNOWN
        item = AtlasItem(name, path, category, validate=validate)
        self.atlas[name] = item
        return item

    def get_item(self, name: str) -> Optional[AtlasItem]:
        return self.atlas.get(name)

    def get_bytes(self, name: str) -> Optional[bytes]:
        if self._use_bundle:
            return self._bundle_data.get(name)
        item = self.get_item(name)
        if item and item.path.exists():
            with open(item.path, 'rb') as f:
                return f.read()
        return None

    def add_texture(self, name: str, path: Union[str, Path]) -> AtlasItem:
        return self.add_to_atlas(name, path, AtlasCategory.TEXTURE)

    def add_font(self, name: str, path: Union[str, Path]) -> AtlasItem:
        return self.add_to_atlas(name, path, AtlasCategory.FONT)

    def add_audio(self, name: str, path: Union[str, Path]) -> AtlasItem:
        return self.add_to_atlas(name, path, AtlasCategory.AUDIO)

    def add_src(self, name: str, path: Union[str, Path]) -> AtlasItem:
        return self.add_to_atlas(name, path, AtlasCategory.SRC)

    def add_datastore(self, name: str, path: Union[str, Path]) -> AtlasItem:
        return self.add_to_atlas(name, path, AtlasCategory.DATASTORE)

    def add_folder(self, name: str, path: Union[str, Path]) -> AtlasItem:
        return self.add_to_atlas(name, path, AtlasCategory.FOLDER)

    # ----------------------------------------------------------------------
    # Bundle creation
    # ----------------------------------------------------------------------

    def create_bundle(self, output_path: Union[str, Path],
                      obfuscate: bool = False,
                      obfuscation_key: str = "LunaEngineDefaultKey") -> None:
        """
        Package all atlas resources into a single .res file (ZIP).
        """
        if obfuscate and not obfuscation_key:
            raise ValueError("Obfuscation key cannot be empty when obfuscate=True")

        output_path = Path(output_path)
        manifest = {
            "version": 1,
            "resources": {},
            "obfuscation": {
                "enabled": obfuscate,
                "key": obfuscation_key if obfuscate else None
            }
        }

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for name, item in self.atlas.items():
                if not item.path.exists():
                    print(f"Warning: {item.path} does not exist, skipping")
                    continue
                with open(item.path, 'rb') as f:
                    data = f.read()
                if obfuscate:
                    key_bytes = obfuscation_key.encode('utf-8')
                    data = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])
                if self.root_path:
                    try:
                        archive_path = str(item.path.relative_to(self.root_path))
                    except ValueError:
                        archive_path = item.path.name
                else:
                    archive_path = item.path.name

                zf.writestr(archive_path, data)

                # ---- Build manifest entry with safety ----
                # Ensure category is a string
                category_val = item.category
                if isinstance(category_val, Enum):
                    category_val = category_val.value
                elif not isinstance(category_val, str):
                    # If it's something else (like a method or class), convert to string
                    category_val = str(category_val)

                entry = {
                    "path": str(archive_path),
                    "category": category_val,
                    "size": int(len(data)),
                    "crc32": hex(zlib.crc32(data) & 0xffffffff)
                }
                manifest["resources"][name] = entry

            # Write manifest with detailed error handling
            try:
                manifest_json = json.dumps(manifest, indent=2)
                zf.writestr("manifest.json", manifest_json)
            except Exception as e:
                # Print the manifest to help debug
                print("\n=== Manifest structure (debug) ===")
                for key, value in manifest.items():
                    if key == "resources":
                        for res_name, res_info in value.items():
                            print(f"  {res_name}: {res_info}")
                    else:
                        print(f"{key}: {type(value)} = {value}")
                print("=====================================\n")
                raise RuntimeError(f"Failed to write manifest: {e}") from e

    # ----------------------------------------------------------------------
    # Bundle loading
    # ----------------------------------------------------------------------

    def load_from_bundle(self, bundle_path: Union[str, Path],
                         obfuscation_key: Optional[str] = None,
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """
        Load all resources from a .res bundle.
        If obfuscation was used, provide the same key.
        progress_callback is called with (current, total) for progress indication.
        """
        bundle_path = Path(bundle_path)
        if not bundle_path.exists():
            raise FileNotFoundError(f"Bundle not found: {bundle_path}")

        with zipfile.ZipFile(bundle_path, 'r') as zf:
            # Read manifest
            try:
                with zf.open("manifest.json") as f:
                    manifest = json.load(f)
            except KeyError:
                raise RuntimeError("Bundle is missing manifest.json – not a valid LunaEngine bundle")
            self._bundle_manifest = manifest

            obf_enabled = manifest["obfuscation"]["enabled"]
            key = manifest["obfuscation"].get("key")
            if obf_enabled and obfuscation_key is None:
                raise ValueError("This bundle is obfuscated; provide obfuscation_key")
            if obf_enabled and obfuscation_key != key:
                raise ValueError("Incorrect obfuscation key")

            resources = manifest["resources"]
            total = len(resources)
            for idx, (name, info) in enumerate(resources.items()):
                archive_path = info["path"]
                with zf.open(archive_path) as f:
                    data = f.read()
                if obf_enabled:
                    key_bytes = obfuscation_key.encode('utf-8')
                    data = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])
                self._bundle_data[name] = data
                # Ensure the item exists in the atlas (if not, create it)
                item = self.get_item(name)
                if item is None:
                    # Create a dummy item with a placeholder path
                    cat = info["category"]
                    # Convert to AtlasCategory if it's a string
                    if isinstance(cat, str):
                        try:
                            cat_enum = AtlasCategory(cat)
                        except ValueError:
                            cat_enum = AtlasCategory.UNKNOWN
                    else:
                        cat_enum = AtlasCategory.UNKNOWN
                    item = AtlasItem(name, Path(archive_path), cat_enum)
                    self.atlas[name] = item
                item._data = data
                if progress_callback:
                    progress_callback(idx + 1, total)

        self._bundle_path = bundle_path
        self._use_bundle = True
        print(f"Loaded {len(self._bundle_data)} resources from bundle: {bundle_path}")

    def is_bundle_loaded(self) -> bool:
        return self._use_bundle