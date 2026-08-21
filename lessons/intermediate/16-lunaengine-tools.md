# Lesson 16 – LunaEngine Tools

LunaEngine comes with a suite of command‑line tools to help you manage themes, analyse your code, clear cache, and edit game databases. This lesson covers each tool in detail, including installation, usage, and common workflows.

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
python -m lunaengine.tools.theme_tool compile [-i INPUT] [-o OUTPUT] [-c]
```
- `-i, --input` : folder containing individual theme JSONs (default: `lunaengine/assets/themes/`)
- `-o, --output`: output file path (default: `lunaengine/themes.json`)
- `-c, --compact`: produce minified JSON (no indentation)

**Example:**
```bash
python -m lunaengine.tools.theme_tool compile -c
```
> This creates a compact `themes.json` from all themes in `assets/themes/`.

#### `uncompile` – Split themes.json into separate files
```bash
python -m lunaengine.tools.theme_tool uncompile [-i INPUT] [-o OUTPUT] [-c]
```
- `-i, --input` : `themes.json` to split (default: `lunaengine/themes.json`)
- `-o, --output`: folder where individual theme JSONs will be written (default: `lunaengine/assets/themes/`)
- `-c, --compact`: produce compact JSON for each theme

**Example:**
```bash
python -m lunaengine.tools.theme_tool uncompile
```
> This recreates all individual theme files in `assets/themes/` from the combined `themes.json`.

#### `fix-shadows` – Add/update shadow properties
```bash
python -m lunaengine.tools.theme_tool fix-shadows [-i INPUT] [-o OUTPUT]
```
- `-i, --input` : `themes.json` to modify (default: `lunaengine/themes.json`)
- `-o, --output`: output file (if omitted, overwrites input)

**Example:**
```bash
python -m lunaengine.tools.theme_tool fix-shadows -i themes.json -o themes_fixed.json
```
> This walks through every style in every variant and adds a `shadow` object based on the theme’s mode (dark/light) and base colour.

### Workflow Example
1. Edit a theme JSON manually in `assets/themes/`.
2. Compile to update `themes.json`:
   ```bash
   python -m lunaengine.tools.theme_tool compile
   ```
3. (Optional) Fix shadows after changing colours:
   ```bash
   python -m lunaengine.tools.theme_tool fix-shadows
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
python -m lunaengine.tools.code_stats
```

No arguments needed – it automatically scans the parent directory of `tools/` (the project root).

### Output
- **Console** – prints a summary with:
  - Overall lines (total, code, comments, blank)
  - Theme statistics (number of themes, variants)
  - UI element count
  - Files by extension and directory
  - 10 largest files and most commented files
  - Project structure tree
  - Code density rating

- **Markdown report** – saved as `CODE_STATISTICS.md` in the project root, containing all statistics in a structured table format.

### Example
```bash
python -m lunaengine.tools.code_stats
```

**Sample console output:**
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
   .frag     1 files ( 1.6%)
   .geom     1 files ( 1.6%)
   .vert     1 files ( 1.6%)

🌳 PROJECT STRUCTURE:
[ROT] LunaEngine/
├── [DIR] assets/
│   ├── [DIR] icons/
│   └── [DIR] shaders/
│       ├── [SHD] shaders.frag
│       ├── [SHD] shaders.geom
│       └── [SHD] shaders.vert
...
```

> 📄 Detailed report saved to: CODE_STATISTICS.md

---

## 3. Clear Pycache (`clear_pycache.py`)

This utility recursively removes all `__pycache__` directories and their contents from the project. Useful for cleaning up after refactoring or before packaging.

### Location
```
lunaengine/tools/clear_pycache.py
```

### Usage
```bash
python -m lunaengine.tools.clear_pycache
```

It walks through every subdirectory of the project root and removes any folder named `__pycache__`.

**Example output:**
```
Removing ...\LunaEngine\lunaengine\__pycache__
Removing ...\LunaEngine\lunaengine\backend\__pycache__
...
Total items removed: 27
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
python -m lunaengine.tools.database_editor [--savedata FILE] [--atlas-bundle FILE] [--encryption-key KEY] [--no-ui] [--host HOST] [--port PORT] [COMMANDS]
```

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

If Flask is installed, running the editor without `--no-ui` launches a browser-based interface:
```bash
python -m lunaengine.tools.database_editor --savedata game.sav --atlas-bundle assets.res
```
Then open `http://127.0.0.1:5000`. The UI allows you to:
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

## Summary

| Tool | Purpose | Optional Dependencies |
|------|---------|-----------------------|
| `theme_tool.py` | Manage themes (compile/uncompile/fix shadows) | None |
| `code_stats.py` | Generate project code statistics | None |
| `clear_pycache.py` | Remove Python cache files | None |
| `database_editor.py` | Edit Savedata and Atlas bundles | Flask (for web UI) |

All tools are located in the `lunaengine/tools/` directory and can be run with `python -m lunaengine.tools.<tool_name>`.

---

## Next Steps

Now that you know how to use these utilities, you can integrate them into your development workflow:
- Run `code_stats.py` before commits to keep track of project growth.
- Use `theme_tool.py` to manage custom themes.
- Debug and manipulate game saves with `database_editor.py`.

In the next lesson, we’ll dive into [Advanced UI](../advanced/17-advanced-ui.md) – building complex interfaces with custom layouts and interactions.
```

---

Let me know if you want any adjustments, like renaming the other lesson files or renumbering. I've updated `lessons.md` accordingly.