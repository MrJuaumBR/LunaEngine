#!/usr/bin/env python3
"""
LunaEngine Database Editor – CLI + optional Flask UI with .sav upload.
"""

import argparse
import sys
import json
import os
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

# Import LunaEngine storage components
try:
    from ..storage import (
        Savedata, Table, Query, SavedataError,
        Atlas, AtlasItem, AtlasCategory,
        load_savedata, save_savedata
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from storage import (
        Savedata, Table, Query, SavedataError,
        Atlas, AtlasItem, AtlasCategory,
        load_savedata, save_savedata
    )

# ----------------------------------------------------------------------
# CLI actions (same as before)
# ----------------------------------------------------------------------

def cli_list_tables(savedata: Savedata) -> None:
    if not savedata.tables:
        print("No tables found.")
        return
    print("Tables:")
    for name in savedata.tables:
        table = savedata.table(name)
        print(f"  {name} (columns: {table.columns}, rows: {len(table)})")

def cli_show_table(savedata: Savedata, table_name: str, limit: int = 20) -> None:
    table = savedata.table(table_name)
    if not table:
        print(f"Table '{table_name}' not found.")
        return
    rows = table.select()
    print(f"Table '{table_name}' – {len(rows)} rows:")
    if not rows:
        return
    headers = table.columns
    print(" | ".join(headers))
    print("-" * 40)
    for row in rows[:limit]:
        print(" | ".join(str(row.get(h, "")) for h in headers))
    if len(rows) > limit:
        print(f"... and {len(rows) - limit} more rows.")

def cli_insert_row(savedata: Savedata, table_name: str, **kwargs) -> None:
    table = savedata.table(table_name)
    if not table:
        print(f"Table '{table_name}' not found.")
        return
    try:
        idx = table.insert(**kwargs)
        print(f"Inserted row at index {idx}.")
        savedata.save()
    except Exception as e:
        print(f"Insert failed: {e}")

def cli_update_row(savedata: Savedata, table_name: str, pk: Any, **kwargs) -> None:
    table = savedata.table(table_name)
    if not table:
        print(f"Table '{table_name}' not found.")
        return
    if not table.primary_key:
        print("Table has no primary key.")
        return
    count = table.update_by_primary_key(pk, **kwargs)
    if count:
        savedata.save()
        print(f"Updated row with {table.primary_key}={pk}.")
    else:
        print(f"No row found with {table.primary_key}={pk}.")

def cli_delete_row(savedata: Savedata, table_name: str, pk: Any) -> None:
    table = savedata.table(table_name)
    if not table:
        print(f"Table '{table_name}' not found.")
        return
    if not table.primary_key:
        print("Table has no primary key.")
        return
    count = table.delete_by_primary_key(pk)
    if count:
        savedata.save()
        print(f"Deleted row with {table.primary_key}={pk}.")
    else:
        print(f"No row found with {table.primary_key}={pk}.")

def cli_export_json(savedata: Savedata, output: str) -> None:
    savedata.export_to_json(output)
    print(f"Exported to {output}.")

def cli_import_json(savedata: Savedata, input_file: str) -> None:
    savedata.import_from_json(input_file)
    savedata.save()
    print(f"Imported from {input_file} and saved.")

def cli_list_resources(atlas: Atlas) -> None:
    if atlas.is_bundle_loaded():
        print("Resources in bundle:")
        for name in atlas._bundle_data:
            print(f"  {name}")
    else:
        print("Atlas items (files):")
        for name, item in atlas.atlas.items():
            print(f"  {name} -> {item.path} (category: {item.category.value})")

def cli_extract_resource(atlas: Atlas, name: str, output: str) -> None:
    data = atlas.get_bytes(name)
    if data is None:
        print(f"Resource '{name}' not found.")
        return
    out_path = Path(output)
    out_path.write_bytes(data)
    print(f"Extracted {name} to {output}.")

# ----------------------------------------------------------------------
# Flask UI (optional) – now with .sav upload
# ----------------------------------------------------------------------

try:
    from flask import Flask, request, render_template_string, jsonify, redirect, url_for
except ImportError:
    Flask = None

def create_flask_app(initial_savedata: Savedata, atlas: Optional[Atlas] = None):
    if Flask is None:
        raise RuntimeError("Flask is not installed. Please install Flask or use --no-ui.")

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'luna-engine-editor-secret'

    # Use a global-like variable stored in app.config to allow reloading
    app.config['savedata'] = initial_savedata
    app.config['atlas'] = atlas

    # HTML templates (embedded for simplicity)
    INDEX_TEMPLATE = """
    <!doctype html>
    <title>LunaEngine Database Editor</title>
    <h1>LunaEngine Database Editor</h1>
    <p><a href="{{ url_for('load_sav') }}">📁 Load a .sav file</a></p>
    <hr>
    <h2>Tables</h2>
    <ul>
    {% for name, table in tables.items() %}
        <li><a href="{{ url_for('view_table', table_name=name) }}">{{ name }}</a>
            ({{ table|length }} rows)
        </li>
    {% endfor %}
    </ul>
    {% if atlas and atlas.is_bundle_loaded() %}
    <h2>Atlas</h2>
    <ul>
    {% for name in atlas._bundle_data.keys() %}
        <li><a href="{{ url_for('view_resource', name=name) }}">{{ name }}</a></li>
    {% endfor %}
    </ul>
    {% endif %}
    <hr>
    <p><a href="{{ url_for('export_json') }}">📤 Export all tables to JSON</a></p>
    <p><a href="{{ url_for('import_json') }}">📥 Import tables from JSON</a></p>
    """

    TABLE_TEMPLATE = """
    <!doctype html>
    <title>Table: {{ table_name }}</title>
    <h1>Table: {{ table_name }}</h1>
    <p>Columns: {{ columns|join(', ') }}</p>
    <p>Primary key: {{ primary_key or 'None' }}</p>
    <p>Auto-increment: {{ auto_increment }}</p>
    <p><a href="{{ url_for('insert_row', table_name=table_name) }}">Insert new row</a></p>
    <p><a href="{{ url_for('index') }}">← Back</a></p>
    <table border="1">
        <tr>
            {% for col in columns %}
            <th>{{ col }}</th>
            {% endfor %}
            <th>Actions</th>
        </tr>
        {% for row in rows %}
        <tr>
            {% for col in columns %}
            <td>{{ row.get(col, '') }}</td>
            {% endfor %}
            <td>
                {% if primary_key %}
                <a href="{{ url_for('update_row', table_name=table_name, pk=row[primary_key]) }}">Edit</a>
                <a href="{{ url_for('delete_row', table_name=table_name, pk=row[primary_key]) }}"
                   onclick="return confirm('Delete this row?')">Delete</a>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    """

    INSERT_TEMPLATE = """
    <!doctype html>
    <title>Insert row – {{ table_name }}</title>
    <h1>Insert row into {{ table_name }}</h1>
    <form method="post">
        {% for col in columns %}
            <label>{{ col }}: <input type="text" name="{{ col }}" value=""></label><br>
        {% endfor %}
        <input type="submit" value="Insert">
    </form>
    <p><a href="{{ url_for('view_table', table_name=table_name) }}">← Back to table</a></p>
    """

    UPDATE_TEMPLATE = """
    <!doctype html>
    <title>Update row – {{ table_name }}</title>
    <h1>Update row ({{ primary_key }} = {{ pk }}) in {{ table_name }}</h1>
    <form method="post">
        {% for col in columns %}
            <label>{{ col }}:
                <input type="text" name="{{ col }}" value="{{ row.get(col, '') }}">
            </label><br>
        {% endfor %}
        <input type="submit" value="Update">
    </form>
    <p><a href="{{ url_for('view_table', table_name=table_name) }}">← Back to table</a></p>
    """

    LOAD_SAV_TEMPLATE = """
    <!doctype html>
    <title>Load .sav</title>
    <h1>Load a .sav file</h1>
    <form method="post" enctype="multipart/form-data">
        <label>Select .sav file: <input type="file" name="file" accept=".sav"></label><br>
        <label>Encryption key (optional): <input type="text" name="encryption_key"></label><br>
        <input type="submit" value="Load">
    </form>
    <p><a href="{{ url_for('index') }}">← Back</a></p>
    """

    @app.route('/')
    def index():
        savedata = app.config['savedata']
        atlas = app.config['atlas']
        return render_template_string(INDEX_TEMPLATE,
                                      tables=savedata.tables,
                                      atlas=atlas)

    @app.route('/load_sav', methods=['GET', 'POST'])
    def load_sav():
        if request.method == 'POST':
            file = request.files.get('file')
            if not file:
                return "No file uploaded.", 400
            key = request.form.get('encryption_key', '') or None
            temp_path = Path("temp_upload.sav")
            file.save(temp_path)
            try:
                new_savedata = load_savedata(temp_path, encryption_key=key)
                app.config['savedata'] = new_savedata
                return redirect(url_for('index'))
            except Exception as e:
                return f"Failed to load .sav: {e}", 400
            finally:
                temp_path.unlink(missing_ok=True)
        return render_template_string(LOAD_SAV_TEMPLATE)

    @app.route('/table/<table_name>')
    def view_table(table_name):
        savedata = app.config['savedata']
        table = savedata.table(table_name)
        if not table:
            return f"Table '{table_name}' not found.", 404
        rows = table.select()
        return render_template_string(TABLE_TEMPLATE,
                                      table_name=table_name,
                                      columns=table.columns,
                                      primary_key=table.primary_key,
                                      auto_increment=table.auto_increment,
                                      rows=rows)

    @app.route('/table/<table_name>/insert', methods=['GET', 'POST'])
    def insert_row(table_name):
        savedata = app.config['savedata']
        table = savedata.table(table_name)
        if not table:
            return f"Table '{table_name}' not found.", 404
        if request.method == 'POST':
            data = {k: request.form.get(k) for k in table.columns}
            for k, v in data.items():
                if v is None or v == '':
                    data[k] = None
                elif v.isdigit():
                    data[k] = int(v)
                else:
                    try:
                        data[k] = float(v)
                    except ValueError:
                        pass
            try:
                table.insert(**data)
                savedata.save()
                return redirect(url_for('view_table', table_name=table_name))
            except Exception as e:
                return f"Insert failed: {e}", 400
        return render_template_string(INSERT_TEMPLATE,
                                      table_name=table_name,
                                      columns=table.columns)

    @app.route('/table/<table_name>/update/<pk>', methods=['GET', 'POST'])
    def update_row(table_name, pk):
        savedata = app.config['savedata']
        table = savedata.table(table_name)
        if not table:
            return f"Table '{table_name}' not found.", 404
        if not table.primary_key:
            return "Table has no primary key.", 400
        row = table.get_by_primary_key(pk)
        if not row:
            return f"Row with {table.primary_key}={pk} not found.", 404
        if request.method == 'POST':
            data = {k: request.form.get(k) for k in table.columns}
            data.pop(table.primary_key, None)
            for k, v in data.items():
                if v is None or v == '':
                    data[k] = None
                elif v.isdigit():
                    data[k] = int(v)
                else:
                    try:
                        data[k] = float(v)
                    except ValueError:
                        pass
            try:
                table.update_by_primary_key(pk, **data)
                savedata.save()
                return redirect(url_for('view_table', table_name=table_name))
            except Exception as e:
                return f"Update failed: {e}", 400
        return render_template_string(UPDATE_TEMPLATE,
                                      table_name=table_name,
                                      columns=table.columns,
                                      primary_key=table.primary_key,
                                      pk=pk,
                                      row=row)

    @app.route('/table/<table_name>/delete/<pk>')
    def delete_row(table_name, pk):
        savedata = app.config['savedata']
        table = savedata.table(table_name)
        if not table:
            return f"Table '{table_name}' not found.", 404
        if not table.primary_key:
            return "Table has no primary key.", 400
        table.delete_by_primary_key(pk)
        savedata.save()
        return redirect(url_for('view_table', table_name=table_name))

    @app.route('/export')
    def export_json():
        savedata = app.config['savedata']
        savedata.export_to_json("export.json")
        return "Exported to export.json. <a href='/'>Back</a>"

    @app.route('/import', methods=['GET', 'POST'])
    def import_json():
        savedata = app.config['savedata']
        if request.method == 'POST':
            file = request.files.get('file')
            if not file:
                return "No file uploaded.", 400
            file.save("import.json")
            savedata.import_from_json("import.json")
            savedata.save()
            return redirect(url_for('index'))
        return '''
        <!doctype html>
        <title>Import JSON</title>
        <h1>Import JSON</h1>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".json">
            <input type="submit" value="Upload and import">
        </form>
        <p><a href="/">Back</a></p>
        '''

    @app.route('/resource/<name>')
    def view_resource(name):
        atlas = app.config['atlas']
        if not atlas or not atlas.is_bundle_loaded():
            return "No bundle loaded.", 404
        data = atlas.get_bytes(name)
        if data is None:
            return f"Resource '{name}' not found.", 404
        try:
            text = data.decode('utf-8')
            return f"<pre>{text}</pre>"
        except UnicodeDecodeError:
            return f"Binary resource – <a href='/resource/{name}/download'>Download</a>"

    @app.route('/resource/<name>/download')
    def download_resource(name):
        atlas = app.config['atlas']
        if not atlas or not atlas.is_bundle_loaded():
            return "No bundle loaded.", 404
        data = atlas.get_bytes(name)
        if data is None:
            return f"Resource '{name}' not found.", 404
        from flask import send_file
        import io
        return send_file(io.BytesIO(data), as_attachment=True, download_name=name)

    return app

# ----------------------------------------------------------------------
# Main entry point with argparse
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LunaEngine Database Editor",
        epilog="Example: %(prog)s --savedata game.sav --atlas-bundle resources.res --no-ui --list-tables"
    )
    parser.add_argument('--savedata', '-s', help="Path to Savedata file (.sav)", default=None)
    parser.add_argument('--atlas-bundle', '-b', help="Path to Atlas bundle (.res)", default=None)
    parser.add_argument('--atlas-root', help="Root directory for Atlas (if not using bundle)", default=None)
    parser.add_argument('--encryption-key', '-k', help="Encryption key for Savedata/Atlas", default=None)
    parser.add_argument('--no-ui', action='store_true', help="Disable Flask UI; run CLI commands only")
    parser.add_argument('--host', default='127.0.0.1', help="Flask host (default 127.0.0.1)")
    parser.add_argument('--port', type=int, default=5000, help="Flask port (default 5000)")
    parser.add_argument('--debug', action='store_true', help="Run Flask in debug mode")
    parser.add_argument('--no-browser', action='store_true', help="Do not open browser automatically")

    # CLI actions
    parser.add_argument('--list-tables', action='store_true', help="List all tables (CLI)")
    parser.add_argument('--show-table', help="Show rows of a table (CLI)")
    parser.add_argument('--insert', help="Insert row: table,col=val,... (CLI)")
    parser.add_argument('--update', help="Update row: table,pk,col=val,... (CLI)")
    parser.add_argument('--delete', help="Delete row: table,pk (CLI)")
    parser.add_argument('--export-json', help="Export all tables to JSON file (CLI)")
    parser.add_argument('--import-json', help="Import from JSON file (CLI)")
    parser.add_argument('--list-resources', action='store_true', help="List Atlas resources (CLI)")
    parser.add_argument('--extract-resource', nargs=2, metavar=('NAME', 'OUTPUT'),
                        help="Extract a resource from Atlas to file (CLI)")

    args = parser.parse_args()

    # Load initial Savedata
    if args.savedata:
        try:
            savedata = load_savedata(args.savedata, args.encryption_key)
            print(f"Loaded Savedata: {args.savedata}")
        except Exception as e:
            print(f"Failed to load Savedata: {e}")
            sys.exit(1)
    else:
        savedata = Savedata()

    # Load Atlas
    atlas = None
    if args.atlas_bundle:
        atlas = Atlas()
        try:
            atlas.load_from_bundle(args.atlas_bundle, args.encryption_key)
            print(f"Loaded Atlas bundle: {args.atlas_bundle}")
        except Exception as e:
            print(f"Failed to load Atlas bundle: {e}")
            sys.exit(1)
    elif args.atlas_root:
        atlas = Atlas(args.atlas_root)
        print(f"Atlas root set to: {args.atlas_root}")
    else:
        atlas = Atlas()

    # Execute CLI actions if requested
    if args.no_ui or any([args.list_tables, args.show_table, args.insert,
                         args.update, args.delete, args.export_json,
                         args.import_json, args.list_resources,
                         args.extract_resource]):

        if args.list_tables:
            cli_list_tables(savedata)

        if args.show_table:
            cli_show_table(savedata, args.show_table)

        if args.insert:
            parts = args.insert.split(',', 1)
            if len(parts) != 2:
                print("Invalid insert format. Use: table,col=val,col2=val2")
                sys.exit(1)
            table_name = parts[0]
            kv = parts[1].split(',')
            data = {}
            for item in kv:
                if '=' not in item:
                    print(f"Invalid key=value: {item}")
                    sys.exit(1)
                k, v = item.split('=', 1)
                if v.isdigit():
                    data[k] = int(v)
                else:
                    try:
                        data[k] = float(v)
                    except ValueError:
                        data[k] = v
            cli_insert_row(savedata, table_name, **data)

        if args.update:
            parts = args.update.split(',', 2)
            if len(parts) < 3:
                print("Invalid update format. Use: table,pk,col=val,col2=val2")
                sys.exit(1)
            table_name = parts[0]
            pk = parts[1]
            kv = parts[2].split(',')
            data = {}
            for item in kv:
                if '=' not in item:
                    print(f"Invalid key=value: {item}")
                    sys.exit(1)
                k, v = item.split('=', 1)
                if v.isdigit():
                    data[k] = int(v)
                else:
                    try:
                        data[k] = float(v)
                    except ValueError:
                        data[k] = v
            cli_update_row(savedata, table_name, pk, **data)

        if args.delete:
            parts = args.delete.split(',', 1)
            if len(parts) != 2:
                print("Invalid delete format. Use: table,pk")
                sys.exit(1)
            table_name, pk = parts[0], parts[1]
            cli_delete_row(savedata, table_name, pk)

        if args.export_json:
            cli_export_json(savedata, args.export_json)

        if args.import_json:
            cli_import_json(savedata, args.import_json)

        if args.list_resources:
            cli_list_resources(atlas)

        if args.extract_resource:
            name, output = args.extract_resource
            cli_extract_resource(atlas, name, output)

        if args.no_ui:
            return

    # Launch UI
    if Flask is None:
        print("Flask is not installed. Cannot start UI. Use --no-ui for CLI only.")
        sys.exit(1)

    app = create_flask_app(savedata, atlas)
    url = f"http://{args.host}:{args.port}"
    print(f"Starting LunaEngine Editor at {url}")
    if not args.no_browser:
        webbrowser.open(url)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()