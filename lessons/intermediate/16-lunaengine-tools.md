# Lesson 16 – LunaEngine Tools

LunaEngine comes with a suite of command‑line tools to help you manage themes, analyse your code, clear cache, and edit game databases. This lesson covers each tool in detail, including installation, usage, and common workflows. All tools now support `--help` to display available options.

---

## 1. Theme Tool (`theme_tool.py`)

The Theme Tool manages LunaEngine’s JSON theme files. It can **compile** individual theme JSONs into a single `themes.json`, **uncompile** back to separate files, and automatically **fix shadow properties** for dark/light variants.

### Location
```
lunaengine/tools/theme_tool.py
```

### Usage
```bash
python -m lunaengine.tools.theme_tool <command> [options]
```

### Commands

#### `compile` – Merge themes into one file
```bash
python -m lunaengine.tools.theme_tool compile [-i INPUT] [-o OUTPUT] [-c] [-v]
```
- `-i, --input` : folder containing individual theme JSONs (default: `lunaengine/assets/themes/`)
- `-o, --output`: output file path (default: `lunaengine/themes.json`)
- `-c, --compact`: produce minified JSON (no indentation)
- `-v, --verbose`: show detailed progress

**Example:**
```bash
python -m lunaengine.tools.theme_tool compile -c -v
```
> This compiles themes into a compact `themes.json` with verbose output.

#### `uncompile` – Split themes.json into separate files
```bash
python -m lunaengine.tools.theme_tool uncompile [-i INPUT] [-o OUTPUT] [-c] [-v]
```
- `-i, --input` : `themes.json` to split (default: `lunaengine/themes.json`)
- `-o, --output`: folder where individual theme JSONs will be written (default: `lunaengine/assets/themes/`)
- `-c, --compact`: produce compact JSON for each theme
- `-v, --verbose`: show each file being written

**Example:**
```bash
python -m lunaengine.tools.theme_tool uncompile -v
```
> This recreates all individual theme files in `assets/themes/` from the combined `themes.json` and lists each one.

#### `fix-shadows` – Add/update shadow properties
```bash
python -m lunaengine.tools.theme_tool fix-shadows [-i INPUT] [-o OUTPUT] [--overwrite] [-v]
```
- `-i, --input` : `themes.json` to modify (default: `lunaengine/themes.json`)
- `-o, --output`: output file (if not using `--overwrite`)
- `--overwrite` : overwrite the input file directly (instead of writing to a different output)
- `-v, --verbose`: show more details during processing

**Example:**
```bash
python -m lunaengine.tools.theme_tool fix-shadows -i themes.json --overwrite
```
> This updates the shadow properties in place.

### Workflow Example
1. Edit a theme JSON manually in `assets/themes/`.
2. Compile to update `themes.json`:
   ```bash
   python -m lunaengine.tools.theme_tool compile
   ```
3. (Optional) Fix shadows after changing colours:
   ```bash
   python -m lunaengine.tools.theme_tool fix-shadows --overwrite
   ```

---

## 2. Code Statistics (`code_stats.py`)

This script analyses your LunaEngine project and generates a detailed report on code lines, comments, file counts, and project structure. It also counts themes and UI elements automatically.

### Location
```
lunaengine/tools/code_stats.py
```

### Usage
```bash
python -m lunaengine.tools.code_stats [options]
```

### Options
- `--json` : output statistics as JSON instead of the formatted console report.
- `-o, --output FILE` : if `--json` is used, write JSON to this file (otherwise prints to stdout).
- `--no-structure` : exclude the project structure tree from the output (works with `--json`).
- `--no-markdown` : prevent generation of the `CODE_STATISTICS.md` report (default: generates it).

### Output Modes

#### Default (console + Markdown)
```bash
python -m lunaengine.tools.code_stats
```
Prints a summary and creates `CODE_STATISTICS.md` in the project root.

#### JSON Output
```bash
python -m lunaengine.tools.code_stats --json
```
Prints the complete statistics dictionary as JSON.

To save to a file:
```bash
python -m lunaengine.tools.code_stats --json --output stats.json
```

To omit the file tree:
```bash
python -m lunaengine.tools.code_stats --json --no-structure
```

### Sample Console Output (truncated)
```
============================================================
LUNAENGINE CODE STATISTICS
============================================================

📊 OVERALL STATISTICS:
   Total Files:        61
   Total Lines:     32050
   Code Lines:      22272 (69.5%)
   Comment Lines:    5167 (16.1%)
   Blank Lines:      4611 (14.4%)

🎨 THEME STATISTICS:
   Total Themes (base):         72
   Themes with both variants:   72
   Total variants (dark+light): 144

📁 FILES BY EXTENSION:
   .py      57 files (93.4%)
   .md       1 files ( 1.6%)
   ...

🌳 PROJECT STRUCTURE:
[ROT] LunaEngine/
├── [DIR] assets/
│   ├── [DIR] icons/
│   └── [DIR] shaders/
│       ├── [SHD] shaders.frag
...
```

> 📄 Detailed report also saved to: CODE_STATISTICS.md

---

## 3. Clear Pycache (`clear_pycache.py`)

This utility recursively removes all `__pycache__` directories and their contents from the project. Useful for cleaning up after refactoring or before packaging.

### Location
```
lunaengine/tools/clear_pycache.py
```

### Usage
```bash
python -m lunaengine.tools.clear_pycache [--path DIR] [--dry-run] [-v]
```

### Options
- `--path DIR` : root directory to start searching (default: the project root, i.e., parent of `tools/`).
- `--dry-run` : preview which directories would be removed without actually deleting them.
- `-v, --verbose` : show each removal (same as default behaviour; kept for consistency).

### Examples

**Clean the entire project:**
```bash
python -m lunaengine.tools.clear_pycache
```

**Test what would be removed in a subfolder:**
```bash
python -m lunaengine.tools.clear_pycache --path ./lunaengine --dry-run
```

**Output:**
```
[DRY RUN] Would remove .../LunaEngine/lunaengine/__pycache__
[DRY RUN] Would remove .../LunaEngine/lunaengine/backend/__pycache__
...
Total __pycache__ directories removed: 27
```

---

## 4. Database Editor (`database_editor.py`)

The Database Editor is a powerful tool to inspect and modify `.sav` (Savedata) files and Atlas bundles (`.res`). It can run in **CLI mode** or as a **web-based UI** using Flask.

### Location
```
lunaengine/tools/database_editor.py
```

### Prerequisites (optional)
- **Flask** – for the web UI (install with `pip install flask`). Without Flask, you can still use the CLI commands.

### Basic Usage
```bash
python -m lunaengine.tools.database_editor [--savedata FILE] [--atlas-bundle FILE] [--encryption-key KEY] [--no-ui] [--host HOST] [--port PORT] [--debug] [--no-browser] [COMMANDS]
```

### General Options
- `--savedata FILE` : path to the `.sav` file to load.
- `--atlas-bundle FILE` : path to an Atlas bundle (`.res`).
- `--atlas-root DIR` : root directory for file‑based Atlas (alternative to bundle).
- `--encryption-key KEY` : encryption key for savedata/atlas (if needed).
- `--no-ui` : run only CLI commands (no Flask server).
- `--host HOST` : bind address (default `127.0.0.1`).
- `--port PORT` : port for the web UI (default `5000`).
- `--debug` : enable Flask debug mode (auto‑reload on changes).
- `--no-browser` : prevent automatic opening of the browser when the UI starts.

### CLI Commands

| Command | Description |
|---------|-------------|
| `--list-tables` | List all tables in the Savedata |
| `--show-table NAME` | Display rows of a given table (first 20) |
| `--insert "table,col=val,..."` | Insert a new row |
| `--update "table,pk,col=val,..."` | Update a row by primary key |
| `--delete "table,pk"` | Delete a row by primary key |
| `--export-json FILE` | Export all tables to a JSON file |
| `--import-json FILE` | Import tables from a JSON file |
| `--list-resources` | List resources in the Atlas bundle |
| `--extract-resource NAME OUTPUT` | Extract a resource from the bundle to a file |

### Web UI (Flask)

If Flask is installed, running the editor without `--no-ui` launches a browser‑based interface:
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --atlas-bundle assets.res --debug
```
Then open `http://127.0.0.1:5000` (or it opens automatically unless `--no-browser` is used). The UI allows you to:
- Browse and edit tables (insert, update, delete rows)
- Upload a `.sav` file directly
- Export/import JSON
- View and download resources from the Atlas bundle

---

### Database Editor – Examples

#### List all tables
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --list-tables
```
Output:
```
Tables:
  players (columns: id, name, level, health, mana, rows: 3)
  inventory (columns: id, player_id, item, qty, rows: 12)
```

#### Show a table
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --show-table players
```
```
Table 'players' – 3 rows:
id | name   | level | health | mana
-------------------------------------
1  | Alice  | 5     | 120    | 80
2  | Bob    | 3     | 90     | 60
3  | Charlie| 7     | 150    | 100
```

#### Insert a new player
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --insert "players,name=Diana,level=4,health=110,mana=70"
```

#### Update a player’s level
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --update "players,1,level=8"
```

#### Delete a player
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --delete "players,2"
```

#### Export all data to JSON
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --export-json backup.json
```

#### Import from JSON
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --import-json backup.json
```

#### List resources in an Atlas bundle
```bash
python -m lunaengine.tools.database_editor --atlas-bundle assets.res --list-resources
```

#### Extract a resource
```bash
python -m lunaengine.tools.database_editor --atlas-bundle assets.res --extract-resource player_sprite.png player.png
```

---

## 5. File Tree Exporter (`file_tree.py`)

This tool generates a text‑based tree of the project’s file and folder structure, with sensible exclusions for development artefacts (cache, version control, compiled files). It’s designed to give LLMs, AI assistants, or documentation a clear, human‑readable snapshot of your repository layout.

### Location
```
lunaengine/tools/file_tree.py
```

### Usage
```bash
python -m lunaengine.tools.file_tree [options]
```

### Options
- `--path DIR` : root directory to start from (default: project root, i.e., parent of `tools/`).
- `--output FILE` : write the tree to a file instead of stdout.
- `--depth N` : limit traversal to `N` levels deep (`-1` means unlimited, default).
- `--ignore-dirs DIR1 DIR2 ...` : additional directory names to ignore (space separated). Defaults: `__pycache__ .git build dist venv env .vscode .idea`
- `--ignore-files PATTERN1 PATTERN2 ...` : additional file patterns (glob‑style) to ignore. Defaults: `*.pyc *.pyo *.pyd *.so *.dll`
- `--no-default-ignore` : disable the default ignore lists and only use custom ones.

### Examples

**Basic tree of the whole project:**
```bash
python -m lunaengine.tools.file_tree
```
Output (excerpt):
```
\LunaEngine\lunaengine/
├── assets/
│   ├── icons/
│   │   ├── ...
│   ├── shaders/
│   │   └── ...
│   ├── themes/
│   │   └── ...
│   └── lunaengine-icon.png
├── backend/
│   ├── __init__.py
│   ├── controller.py
│   ├── exceptions.py
│   ├── network.py
│   ├── openal.py
│   ├── opengl.py
│   └── types.py
├── core/
│   ├── __init__.py
│   ├── audio.py
│   ├── engine.py
│   ├── renderer.py
│   ├── scene.py
│   └── window.py
├── graphics/
│   ├── __init__.py
│   ├── camera.py
│   ├── paperdoll.py
│   ├── particles.py
│   ├── shadows.py
│   └── spritesheet.py
├── misc/
│   ├── __init__.py
│   ├── debug.py
│   └── icons.py
├── storage/
│   ├── __init__.py
│   ├── atlas.py
│   ├── encrypter.py
│   └── savedata.py
├── tools/
│   ├── __init__.py
│   ├── clear_pycache.py
│   ├── code_stats.py
│   ├── database_editor.py
│   ├── file_tree.py
│   └── theme_tool.py
├── ui/
│   ├── elements/
│   │   ├── ...
│   ├── __init__.py
│   ├── layer_manager.py
│   ├── layout.py
│   ├── notifications.py
│   ├── styles.py
│   ├── themes.py
│   ├── tooltips.py
│   └── tween.py
├── utils/
│   ├── __init__.py
│   ├── image_converter.py
│   ├── math_utils.py
│   ├── performance.py
│   ├── threading.py
│   └── timer.py
├── __init__.py
└── CODE_STATISTICS.md
```

**Limit depth and save to file:**
```bash
python -m lunaengine.tools.file_tree --depth 2 --output project_tree.txt
```

**Ignore additional folders (e.g., `docs/` and `tests/`):**
```bash
python -m lunaengine.tools.file_tree --ignore-dirs docs tests
```

**Use only custom ignores (no defaults):**
```bash
python -m lunaengine.tools.file_tree --no-default-ignore --ignore-dirs build
```

---

## Summary

| Tool | Purpose | Key New Options |
|------|---------|----------------|
| `theme_tool.py` | Manage themes (compile/uncompile/fix shadows) | `--verbose`, `--overwrite` |
| `code_stats.py` | Generate project code statistics | `--json`, `--output`, `--no-structure`, `--no-markdown` |
| `clear_pycache.py` | Remove Python cache files | `--path`, `--dry-run` |
| `database_editor.py` | Edit Savedata and Atlas bundles | `--debug`, `--no-browser` |
| `file_tree.py` | Export a text‑based file tree | `--depth`, `--output`, `--ignore-dirs`, `--ignore-files` |


All tools are located in the `lunaengine/tools/` directory and can be run with `python -m lunaengine.tools.<tool_name>`. Use `--help` with any tool to see the full list of options.

---

## Next Steps

Now that you know how to use these utilities, you can integrate them into your development workflow:
- Run `code_stats.py --json` to export metrics for automated analysis.
- Use `clear_pycache.py --dry-run` before cleaning to avoid surprises.
- Debug game saves with `database_editor.py --debug --no-browser` to keep the console clean.

In the next lesson, we’ll dive into [Advanced UI](../advanced/17-advanced-ui.md) – building complex interfaces with custom layouts and interactions.