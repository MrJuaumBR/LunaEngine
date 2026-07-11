"""
Storage Demo – Multi-Character Save/Load with Query System
Shows:
- Multiple characters (id, name, char_class, level, hp, max_hp, exp, inventory)
- Game settings (volume, resolution, fullscreen)
- Export/import to JSON for machine migration
- Query filters and search
"""

import sys
import os
import random
import json
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from lunaengine.core import Scene, LunaEngine
from lunaengine.ui import *
from lunaengine.ui.tween import Tween, EasingType
from lunaengine.storage import Savedata, Table, Query, load_savedata, save_savedata

# ------------------------------------------------------------
# Demo Scene
# ------------------------------------------------------------

class StorageDemoScene(Scene):
    def __init__(self, engine: LunaEngine):
        super().__init__(engine)
        self.engine = engine

        # Storage
        self.savedata = Savedata()
        self.characters_table = None
        self.settings_table = None
        self.load_or_create_data()

        # UI state
        self.selected_char_id = None
        self.current_view = "list"  # list, edit, new
        self.edit_data = {}  # temporary for new/edit

        # Flag to prevent recursive slider updates
        self._updating_settings = False

        # Build UI
        self.setup_ui()
        self.refresh_character_list()
        self.update_settings_display()

    # ------------------------------------------------------------
    # Data Management
    # ------------------------------------------------------------
    def load_or_create_data(self):
        """Try to load from file, or create default data."""
        filepath = Path("game_data.sav")
        if filepath.exists():
            try:
                self.savedata = load_savedata(filepath, encryption_key="my_secret_key")
                print("Loaded savedata from game_data.sav")
            except Exception as e:
                print(f"Error loading: {e}, creating fresh data")
                self.create_default_data()
        else:
            self.create_default_data()

        self.characters_table = self.savedata.table("characters")
        self.settings_table = self.savedata.table("settings")

    def create_default_data(self):
        """Create tables with default characters and settings."""
        self.savedata = Savedata()

        # Characters table – column name is 'char_class'
        chars = self.savedata.create_table("characters", 
                                           columns=["id", "name", "char_class", "level", "hp", "max_hp", "exp", "inventory"],
                                           primary_key="id")
        sample_inventory = ["Sword", "Shield", "Potion"]
        chars.insert(id=1, name="Aragorn", char_class="Warrior", level=5, hp=45, max_hp=50, exp=120, inventory=sample_inventory)
        chars.insert(id=2, name="Legolas", char_class="Archer", level=4, hp=30, max_hp=35, exp=95, inventory=["Bow", "Arrows"])
        chars.insert(id=3, name="Gandalf", char_class="Wizard", level=6, hp=40, max_hp=40, exp=210, inventory=["Staff", "Spellbook"])
        chars.insert(id=4, name="Frodo", char_class="Rogue", level=3, hp=25, max_hp=28, exp=70, inventory=["Ring", "Dagger"])

        # Settings table
        settings = self.savedata.create_table("settings", columns=["key", "value"], primary_key="key")
        settings.insert(key="master_volume", value=0.8)
        settings.insert(key="music_volume", value=0.6)
        settings.insert(key="sfx_volume", value=0.9)
        settings.insert(key="fullscreen", value=False)
        settings.insert(key="resolution", value="1920x1080")

        self.save_data()

    def save_data(self):
        """Save to encrypted file."""
        self.savedata.save("game_data.sav", encryption_key="my_secret_key", compress=True)
        print("Data saved.")

    def refresh_tables(self):
        """Re-fetch table references after load/create."""
        self.characters_table = self.savedata.table("characters")
        self.settings_table = self.savedata.table("settings")

    # ------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------
    def setup_ui(self):
        self.engine.set_global_theme(ThemeType.GRUVBOX)

        # Title
        title = TextLabel(512, 30, "Storage Demo – Character Manager", 36, pivot=(0.5, 0))
        self.add_ui_element(title)

        # Main tabs
        self.main_tabs = Tabination(25, 80, 980, 650, 20)
        self.main_tabs.add_tab("Characters")
        self.main_tabs.add_tab("Settings")
        self.main_tabs.add_tab("Migration")

        self.setup_characters_tab()
        self.setup_settings_tab()
        self.setup_migration_tab()

        self.add_ui_element(self.main_tabs)

        # FPS
        self.fps_label = TextLabel(self.engine.width - 10, 10, "FPS: --", 14, (100, 255, 100), pivot=(1, 0))
        self.add_ui_element(self.fps_label)

    # ---------- Characters Tab ----------
    def setup_characters_tab(self):
        tab = "Characters"
        y = 10

        # Buttons: New, Delete, Refresh, Save
        new_btn = Button(10, y, 100, 30, "New Character")
        new_btn.set_on_click(lambda: self.start_new_character())
        self.main_tabs.add_to_tab(tab, new_btn)

        delete_btn = Button(120, y, 100, 30, "Delete Selected")
        delete_btn.set_on_click(lambda: self.delete_selected_character())
        self.main_tabs.add_to_tab(tab, delete_btn)

        refresh_btn = Button(230, y, 100, 30, "Refresh")
        refresh_btn.set_on_click(lambda: self.refresh_character_list())
        self.main_tabs.add_to_tab(tab, refresh_btn)

        save_btn = Button(340, y, 100, 30, "Save")
        save_btn.set_on_click(lambda: self.save_data())
        self.main_tabs.add_to_tab(tab, save_btn)

        # Search bar
        self.main_tabs.add_to_tab(tab, TextLabel(460, y+5, "Search:", 16))
        self.search_input = TextBox(520, y, 150, 30, "")
        self.search_input.on_text_changed = lambda t: self.refresh_character_list(search_term=t)
        self.main_tabs.add_to_tab(tab, self.search_input)

        # Scrolling frame for character list
        self.char_list_frame = ScrollingFrame(10, y+50, 600, 500, 580, 800)
        self.main_tabs.add_to_tab(tab, self.char_list_frame)

        # Details panel
        detail_frame = UiFrame(630, y+50, 330, 500)
        detail_frame.set_background_color((40, 40, 60, 200))
        detail_frame.set_border((80, 80, 120), 2)
        detail_frame.set_corner_radius(8)
        self.main_tabs.add_to_tab(tab, detail_frame)

        self.detail_title = TextLabel(10, 10, "Character Details", 18, (255, 255, 0))
        detail_frame.add_child(self.detail_title)

        self.detail_labels = {}
        fields = ["name", "char_class", "level", "hp", "max_hp", "exp", "inventory"]
        display_names = ["Name", "Class", "Level", "HP", "Max HP", "EXP", "Inventory"]
        for i, (field, display) in enumerate(zip(fields, display_names)):
            lbl = TextLabel(10, 40 + i*25, f"{display}: --", 14, (200, 200, 200))
            detail_frame.add_child(lbl)
            self.detail_labels[field] = lbl

        self.detail_save_btn = Button(10, 240, 100, 30, "Save Changes")
        self.detail_save_btn.set_on_click(lambda: self.save_character_changes())
        detail_frame.add_child(self.detail_save_btn)

        self.detail_edit_btn = Button(120, 240, 100, 30, "Edit")
        self.detail_edit_btn.set_on_click(lambda: self.start_edit_character())
        detail_frame.add_child(self.detail_edit_btn)

        self.detail_edit_fields_frame = UiFrame(10, 280, 300, 200)
        detail_frame.add_child(self.detail_edit_fields_frame)
        self.detail_edit_fields_frame.visible = False

        self.edit_widgets = {}

    def refresh_character_list(self, search_term=None):
        """Populate the character list from the table, with optional search."""
        # Clear previous list
        for child in self.char_list_frame.children.copy():
            self.char_list_frame.remove_child(child)

        if self.characters_table is None:
            return

        # Build query
        query = self.characters_table.query()
        if search_term and search_term.strip():
            query.search(search_term.strip(), columns=["name", "char_class"], mode="contains", case_sensitive=False)

        # Execute and order by level descending
        rows = query.order_by("level", desc=True).execute()

        y = 10
        for row in rows:
            char_id = row["id"]
            name = row["name"]
            cls = row.get("char_class", "Unknown")
            level = row.get("level", 1)
            hp = row.get("hp", 0)
            max_hp = row.get("max_hp", 1)

            # Row frame
            row_frame = UiFrame(10, y, 560, 40)
            row_frame.set_background_color((50, 50, 70, 200) if y % 80 == 10 else (40, 40, 60, 200))
            row_frame.set_border((100, 100, 150), 1)
            row_frame.set_corner_radius(5)

            # Name + class + level
            name_lbl = TextLabel(10, 5, f"{name} ({cls})", 16, (255, 255, 255))
            row_frame.add_child(name_lbl)

            level_lbl = TextLabel(200, 5, f"Lv.{level}", 16, (200, 200, 255))
            row_frame.add_child(level_lbl)

            # HP bar
            hp_bar = ProgressBar(300, 10, 150, 20, 0, max_hp, hp, style='soundpad')
            row_frame.add_child(hp_bar)

            hp_text = TextLabel(460, 10, f"{hp}/{max_hp}", 12, (200, 200, 200))
            row_frame.add_child(hp_text)

            # Select button
            select_btn = Button(520, 5, 30, 30, "▶")
            select_btn.set_on_click(lambda cid=char_id: self.select_character(cid))
            row_frame.add_child(select_btn)

            self.char_list_frame.add_child(row_frame)
            y += 45

        self.char_list_frame.total_height = max(200, y + 20)

    def select_character(self, char_id):
        """Show character details."""
        self.selected_char_id = char_id
        row = self.characters_table.get_by_primary_key(char_id)
        if not row:
            return

        # Update detail labels
        for field, lbl in self.detail_labels.items():
            val = row.get(field, "--")
            if field == "inventory" and isinstance(val, list):
                val = ", ".join(val)
            # Update only the value part
            current_text = lbl.text
            if ':' in current_text:
                prefix = current_text.split(':')[0] + ':'
                lbl.set_text(f"{prefix} {val}")
            else:
                lbl.set_text(f"{field}: {val}")

        self.detail_edit_btn.enabled = True

    def start_new_character(self):
        """Switch to new character form."""
        self.current_view = "new"
        self.edit_data = {
            "name": "",
            "char_class": "Warrior",
            "level": 1,
            "hp": 30,
            "max_hp": 30,
            "exp": 0,
            "inventory": []
        }
        self.show_edit_form("Create New Character", save_callback=self.create_new_character)

    def start_edit_character(self):
        """Switch to edit mode for selected character."""
        if self.selected_char_id is None:
            return
        row = self.characters_table.get_by_primary_key(self.selected_char_id)
        if not row:
            return
        self.current_view = "edit"
        self.edit_data = row.copy()
        self.show_edit_form("Edit Character", save_callback=self.save_character_changes)

    def show_edit_form(self, title, save_callback):
        """Create/edit form overlay."""
        self.detail_edit_fields_frame.visible = True
        # Clear previous widgets
        for w in self.edit_widgets.values():
            self.detail_edit_fields_frame.remove_child(w)
        self.edit_widgets.clear()

        y = 10
        for field, value in self.edit_data.items():
            if field == "id":
                continue
            display_name = field.replace('_', ' ').title()
            lbl = TextLabel(10, y, f"{display_name}:", 14)
            self.detail_edit_fields_frame.add_child(lbl)

            if field == "inventory":
                inp = TextBox(120, y-5, 150, 25, ", ".join(value) if isinstance(value, list) else str(value))
                inp.on_text_changed = lambda t, f=field: self.update_edit_field(f, t)
            elif isinstance(value, (int, float)):
                inp = NumberSelector(120, y-5, 80, 25, 0, 999, int(value))
                inp.on_value_changed = lambda v, f=field: self.update_edit_field(f, v)
            else:
                inp = TextBox(120, y-5, 150, 25, str(value))
                inp.on_text_changed = lambda t, f=field: self.update_edit_field(f, t)

            self.detail_edit_fields_frame.add_child(inp)
            self.edit_widgets[field] = inp
            y += 30

        # Save button
        save_btn = Button(10, y+10, 100, 30, "Save")
        save_btn.set_on_click(save_callback)
        self.detail_edit_fields_frame.add_child(save_btn)

        cancel_btn = Button(120, y+10, 100, 30, "Cancel")
        cancel_btn.set_on_click(lambda: self.cancel_edit())
        self.detail_edit_fields_frame.add_child(cancel_btn)

        self.detail_edit_fields_frame.height = y + 50

    def update_edit_field(self, field, value):
        self.edit_data[field] = value

    def create_new_character(self):
        """Insert new character from edit_data."""
        if not self.edit_data.get("name"):
            self.engine.show_notification("Name is required!", NotificationType.WARNING)
            return
        max_id = 0
        for row in self.characters_table.rows:
            if row.get("id", 0) > max_id:
                max_id = row["id"]
        new_id = max_id + 1
        self.edit_data["id"] = new_id
        inv = self.edit_data.get("inventory", "")
        if isinstance(inv, str):
            inv = [item.strip() for item in inv.split(",") if item.strip()]
        self.edit_data["inventory"] = inv

        self.characters_table.insert(**self.edit_data)
        self.save_data()
        self.cancel_edit()
        self.refresh_character_list()
        self.engine.show_notification(f"Character '{self.edit_data['name']}' created!", NotificationType.SUCCESS)

    def save_character_changes(self):
        """Update selected character with edit_data."""
        if self.selected_char_id is None:
            return
        inv = self.edit_data.get("inventory", "")
        if isinstance(inv, str):
            inv = [item.strip() for item in inv.split(",") if item.strip()]
        self.edit_data["inventory"] = inv

        row = self.characters_table.get_by_primary_key(self.selected_char_id)
        if row:
            for key, val in self.edit_data.items():
                if key != "id":
                    row[key] = val
            self.save_data()
            self.cancel_edit()
            self.refresh_character_list()
            self.select_character(self.selected_char_id)
            self.engine.show_notification("Character updated!", NotificationType.SUCCESS)

    def cancel_edit(self):
        self.detail_edit_fields_frame.visible = False
        self.current_view = "list"

    def delete_selected_character(self):
        if self.selected_char_id is None:
            return
        row = self.characters_table.get_by_primary_key(self.selected_char_id)
        if row:
            name = row.get("name", "Unknown")
            self.characters_table.delete(lambda r: r["id"] == self.selected_char_id)
            self.save_data()
            self.selected_char_id = None
            self.detail_title.set_text("Character Details")
            for lbl in self.detail_labels.values():
                current_text = lbl.text
                if ':' in current_text:
                    prefix = current_text.split(':')[0] + ':'
                    lbl.set_text(f"{prefix} --")
                else:
                    lbl.set_text(f"{lbl.text.split(':')[0]}: --")
            self.refresh_character_list()
            self.engine.show_notification(f"Deleted '{name}'", NotificationType.INFO)

    # ---------- Settings Tab ----------
    def setup_settings_tab(self):
        tab = "Settings"
        y = 10

        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Game Settings", 24, (255, 255, 0)))

        # Master volume
        self.main_tabs.add_to_tab(tab, TextLabel(10, y+50, "Master Volume:", 16))
        self.master_vol_slider = Slider(160, y+45, 200, 20, 0, 1, 0.8)
        # Use a wrapper to prevent recursive loop
        self.master_vol_slider.on_value_changed = lambda v: self._on_setting_changed("master_volume", v)
        self.main_tabs.add_to_tab(tab, self.master_vol_slider)
        self.master_vol_label = TextLabel(370, y+50, "0.80", 14)
        self.main_tabs.add_to_tab(tab, self.master_vol_label)

        # Music volume
        self.main_tabs.add_to_tab(tab, TextLabel(10, y+80, "Music Volume:", 16))
        self.music_vol_slider = Slider(160, y+75, 200, 20, 0, 1, 0.6)
        self.music_vol_slider.on_value_changed = lambda v: self._on_setting_changed("music_volume", v)
        self.main_tabs.add_to_tab(tab, self.music_vol_slider)
        self.music_vol_label = TextLabel(370, y+80, "0.60", 14)
        self.main_tabs.add_to_tab(tab, self.music_vol_label)

        # SFX volume
        self.main_tabs.add_to_tab(tab, TextLabel(10, y+110, "SFX Volume:", 16))
        self.sfx_vol_slider = Slider(160, y+105, 200, 20, 0, 1, 0.9)
        self.sfx_vol_slider.on_value_changed = lambda v: self._on_setting_changed("sfx_volume", v)
        self.main_tabs.add_to_tab(tab, self.sfx_vol_slider)
        self.sfx_vol_label = TextLabel(370, y+110, "0.90", 14)
        self.main_tabs.add_to_tab(tab, self.sfx_vol_label)

        # Fullscreen switch
        self.main_tabs.add_to_tab(tab, TextLabel(10, y+140, "Fullscreen:", 16))
        self.fullscreen_switch = Switch(160, y+135, 60, 30, False)
        self.fullscreen_switch.set_on_toggle(lambda s: self._on_setting_changed("fullscreen", s))
        self.main_tabs.add_to_tab(tab, self.fullscreen_switch)

        # Resolution dropdown
        self.main_tabs.add_to_tab(tab, TextLabel(10, y+180, "Resolution:", 16))
        self.res_dropdown = Dropdown(160, y+175, 150, 30, ["1920x1080", "1280x720", "1024x768"])
        self.res_dropdown.set_on_selection_changed(lambda i, v: self._on_setting_changed("resolution", v))
        self.main_tabs.add_to_tab(tab, self.res_dropdown)

        # Save settings button
        save_sett_btn = Button(10, y+230, 150, 30, "Save Settings")
        save_sett_btn.set_on_click(lambda: self.save_data())
        self.main_tabs.add_to_tab(tab, save_sett_btn)

        # Load defaults button
        load_def_btn = Button(170, y+230, 150, 30, "Load Defaults")
        load_def_btn.set_on_click(lambda: self.reset_settings())
        self.main_tabs.add_to_tab(tab, load_def_btn)

    def _on_setting_changed(self, key, value):
        """Handle setting change without recursion."""
        if self._updating_settings:
            return
        self.update_setting(key, value)

    def update_setting(self, key, value):
        """Update a setting in the settings table."""
        if self.settings_table is None:
            return
        row = self.settings_table.get_by_primary_key(key)
        if row:
            row["value"] = value
        else:
            self.settings_table.insert(key=key, value=value)
        self.save_data()
        self.update_settings_display()

    def update_settings_display(self):
        """Refresh UI sliders and labels from current settings."""
        if self.settings_table is None:
            return
        self._updating_settings = True
        for row in self.settings_table.rows:
            key = row["key"]
            val = row["value"]
            if key == "master_volume":
                self.master_vol_slider.set_value(val)
                self.master_vol_label.set_text(f"{val:.2f}")
            elif key == "music_volume":
                self.music_vol_slider.set_value(val)
                self.music_vol_label.set_text(f"{val:.2f}")
            elif key == "sfx_volume":
                self.sfx_vol_slider.set_value(val)
                self.sfx_vol_label.set_text(f"{val:.2f}")
            elif key == "fullscreen":
                self.fullscreen_switch.set_value(val)
            elif key == "resolution":
                try:
                    idx = ["1920x1080", "1280x720", "1024x768"].index(val)
                    self.res_dropdown.set_selected_index(idx)
                except ValueError:
                    pass
        self._updating_settings = False

    def reset_settings(self):
        """Reset settings to defaults and save."""
        defaults = {
            "master_volume": 0.8,
            "music_volume": 0.6,
            "sfx_volume": 0.9,
            "fullscreen": False,
            "resolution": "1920x1080"
        }
        for key, val in defaults.items():
            row = self.settings_table.get_by_primary_key(key)
            if row:
                row["value"] = val
            else:
                self.settings_table.insert(key=key, value=val)
        self.save_data()
        self.update_settings_display()
        self.engine.show_notification("Settings reset to defaults", NotificationType.INFO)

    # ---------- Migration Tab ----------
    def setup_migration_tab(self):
        tab = "Migration"
        y = 10

        self.main_tabs.add_to_tab(tab, TextLabel(10, y, "Machine Migration (Export/Import)", 24, (255, 255, 0)))
        y += 50

        info = ("Export your data to a plain JSON file (no encryption). "
                "You can transfer this file to another machine and import it.")
        info_lbl = LongTextLabel(10, y, info, width=500, height=60, font_size=14)
        self.main_tabs.add_to_tab(tab, info_lbl)
        y += 80

        # Export button
        export_btn = Button(10, y, 150, 30, "Export to JSON")
        export_btn.set_on_click(lambda: self.export_data())
        self.main_tabs.add_to_tab(tab, export_btn)

        # Import button
        import_btn = Button(170, y, 150, 30, "Import from JSON")
        import_btn.set_on_click(lambda: self.import_data())
        self.main_tabs.add_to_tab(tab, import_btn)

        y += 50
        self.migration_status = TextLabel(10, y, "Ready", 14, (200, 200, 200))
        self.main_tabs.add_to_tab(tab, self.migration_status)

        # Additional info about encryption
        y += 40
        info2 = ("Note: The game saves encrypted with a key. "
                 "Exporting creates a plain file; import will load it and re-encrypt with current key.")
        info2_lbl = LongTextLabel(10, y, info2, width=500, height=60, font_size=12, color=(150, 150, 200))
        self.main_tabs.add_to_tab(tab, info2_lbl)

    def export_data(self):
        """Export all data to a JSON file."""
        try:
            self.savedata.export_to_json("export_data.json")
            self.migration_status.set_text("Exported to export_data.json")
            self.engine.show_notification("Data exported successfully!", NotificationType.SUCCESS)
        except Exception as e:
            self.migration_status.set_text(f"Export failed: {e}")
            self.engine.show_notification(f"Export error: {e}", NotificationType.ERROR)

    def import_data(self):
        """Import from JSON file and re-save with encryption."""
        try:
            self.savedata.import_from_json("export_data.json")
            # Re-save with encryption
            self.savedata.save("game_data.sav", encryption_key="my_secret_key", compress=True)
            self.refresh_tables()
            self.refresh_character_list()
            self.update_settings_display()
            self.migration_status.set_text("Imported from export_data.json and re-encrypted")
            self.engine.show_notification("Data imported successfully!", NotificationType.SUCCESS)
        except FileNotFoundError:
            self.migration_status.set_text("export_data.json not found!")
            self.engine.show_notification("File not found: export_data.json", NotificationType.ERROR)
        except Exception as e:
            self.migration_status.set_text(f"Import failed: {e}")
            self.engine.show_notification(f"Import error: {e}", NotificationType.ERROR)

    # ------------------------------------------------------------
    # Update & Render
    # ------------------------------------------------------------
    def update(self, dt):
        fps = self.engine.get_fps_stats()['current_fps']
        self.fps_label.set_text(f"FPS: {fps:.1f}")

    def render(self, renderer):
        renderer.fill_screen(ThemeManager.get_color('background'))
        renderer.draw_rect(0, 0, self.engine.width, 80, ThemeManager.get_color('background2'))

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    engine = LunaEngine("Storage Demo", 1024, 768, debug=True, show_splash=False)
    engine.fps = 60
    engine.add_scene("StorageDemo", StorageDemoScene)
    engine.set_scene("StorageDemo")
    engine.run()

if __name__ == "__main__":
    main()