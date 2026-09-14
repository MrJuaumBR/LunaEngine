"""
DEFINITIVE DOCUMENTATION GENERATOR - LUNAENGINE
"""

import os, ast, shutil, stat, html, re, json, sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

lessonsFldr = Path(os.path.dirname(__file__)) / 'lessons'
print(f"Lessons folder: {lessonsFldr}")

# ========== CONFIGURATION ==========

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_remove_folder(folder_path):
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path, onerror=remove_readonly)
            return True
        except Exception:
            return False
    return True

def format_docstring(docstring):
    if not docstring or docstring == 'No documentation':
        return 'No documentation'
    docstring = html.escape(docstring)
    docstring = docstring.replace('\n', '<br>')
    docstring = docstring.replace('  ', ' &nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
    return docstring

def extract_theme_colors(file_path):
    colors_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        theme_classes = re.findall(r'class\s+(\w+Theme).*?:', content)
        for theme_class in theme_classes:
            colors_data[theme_class] = {}
            named_colors = re.findall(r'(\w+)\s*=\s*\"(#(?:[0-9a-fA-F]{3}){1,2})\"', content)
            for color_name, color_hex in named_colors:
                colors_data[theme_class][color_name] = color_hex
        return colors_data
    except Exception as e:
        print(f"      [WARNING] Error extracting theme colors: {e}")
        return {}

# ========== LOAD CODE STATISTICS JSON ==========

def load_code_stats() -> Dict:
    stats_path = Path("docs/code_stats.json")
    if stats_path.exists():
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading code_stats.json: {e}")
    return {
        "total_files": 0,
        "total_lines": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "blank_lines": 0,
        "files_by_extension": {},
        "files": [],
        "version": "unknown",
        "version_status": "unknown",
        "themes": {"total_themes": 0, "themes_with_both_variants": 0, "total_variants": 0},
        "total_icons": 0,
        "elements": {"total_elements": 0}
    }

# ========== THEMES PREVIEW SUPPORT ==========
def load_all_themes() -> Dict[str, Dict[str, Any]]:
    themes = {}
    try:
        sys.path.insert(0, os.getcwd())
        from lunaengine.ui.themes import ThemeManager, ThemeType, CombinedTheme, UITheme
        ThemeManager.ensure_themes_loaded()
        for theme_type, theme_obj in ThemeManager.get_themes().items():
            theme_name = theme_type.value if isinstance(theme_type, ThemeType) else str(theme_type)
            if isinstance(theme_obj, CombinedTheme):
                themes[theme_name] = {
                    "dark": ui_theme_to_dict(theme_obj.dark),
                    "light": ui_theme_to_dict(theme_obj.light)
                }
            else:
                # fallback: treat as both
                theme_dict = ui_theme_to_dict(theme_obj)
                themes[theme_name] = {"dark": theme_dict, "light": theme_dict}
        print(f"Loaded {len(themes)} themes via ThemeManager")
        return themes
    except ImportError:
        print("ThemeManager not available, falling back to direct JSON loading")
    
    # Fallback: read from JSON files in assets/themes
    themes_dir = Path("lunaengine/assets/themes")
    if themes_dir.exists():
        for json_file in themes_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                theme_name = json_file.stem.lower()
                # Check for combined format (variants)
                if "variants" in data and isinstance(data["variants"], dict):
                    # Prefer dark variant, else light
                    if "dark" in data["variants"]:
                        theme_data = data["variants"]["dark"]
                    elif "light" in data["variants"]:
                        theme_data = data["variants"]["light"]
                    else:
                        theme_data = {}
                else:
                    # Legacy single-theme file
                    theme_data = data
                themes[theme_name] = theme_data
            except Exception as e:
                print(f"Error loading theme {json_file}: {e}")
    
    # If no themes loaded, try legacy themes.json
    if not themes:
        legacy_file = Path("lunaengine/ui/themes.json")
        if legacy_file.exists():
            try:
                with open(legacy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for name, theme_data in data.items():
                    themes[name.lower()] = theme_data
            except Exception as e:
                print(f"Error loading legacy themes: {e}")
    
    # Fallback to DEFAULT.json if present
    if not themes and Path("DEFAULT.json").exists():
        try:
            with open("DEFAULT.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                themes["default"] = data
        except Exception:
            pass
    
    return themes

def ui_theme_to_dict(ui_theme) -> Dict:
    """Convert UITheme object to serializable dict for preview."""
    result = {}
    for field in ui_theme.__dataclass_fields__:
        style = getattr(ui_theme, field, None)
        if style:
            result[field] = {
                "color": list(style.color),
                "alpha": style.alpha,
                "cornerRadius": style.corner_radius,
                "borderWidth": style.border_width,
                "blur": style.blur
            }
    return result

def generate_themes_preview_page(themes: Dict[str, Dict[str, Any]]):
    """
    Generate a standalone HTML page showcasing all available themes,
    with support for dark/light variants and live preview switching.
    themes structure: { theme_name: {"dark": theme_dict, "light": theme_dict} }
    """
    if not themes:
        print("No themes found, skipping themes preview page.")
        return

    # Helper to extract color from a style dict
    def get_color(style, default=(100,100,100)):
        color = style.get("color", default)
        if len(color) >= 3:
            return f"rgb({color[0]}, {color[1]}, {color[2]})"
        return f"rgb({default[0]}, {default[1]}, {default[2]})"

    def get_style(variant_data, key, fallback_key=None):
        style = variant_data.get(key)
        if not style and fallback_key:
            style = variant_data.get(fallback_key, {})
        return style

    # Build theme cards HTML
    themes_html = ""
    for theme_name, variants in sorted(themes.items()):
        dark = variants.get("dark", {})
        light = variants.get("light", {})
        default_variant = "dark" if dark else "light"
        default_data = dark if dark else light

        # Extract initial colors with fallbacks
        bg = get_color(get_style(default_data, "background"))
        primary = get_color(get_style(default_data, "text_primary"))
        secondary = get_color(get_style(default_data, "text_secondary"))
        btn_bg = get_color(get_style(default_data, "button_normal"))
        btn_text = get_color(get_style(default_data, "button_text"))
        accent = get_color(get_style(default_data, "accent1"))
        border = get_color(get_style(default_data, "border"))
        dropdown_bg = get_color(get_style(default_data, "dropdown_normal", "background"))
        dropdown_text = get_color(get_style(default_data, "dropdown_text", "text_primary"))
        dropdown_border = get_color(get_style(default_data, "dropdown_border", "border"))
        track_bg = get_color(get_style(default_data, "slider_track"))
        fill_bg = get_color(get_style(default_data, "slider_thumb_normal", "accent1"))

        # Contrast color for button text
        def contrast_color(rgb_str):
            match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', rgb_str)
            if match:
                r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                luminance = (0.299 * r + 0.587 * g + 0.114 * b)
                return "#000" if luminance > 186 else "#fff"
            return "#fff"

        button_text_color = contrast_color(btn_bg)

        # Card with variant toggles
        themes_html += f"""
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card theme-preview-card h-100 shadow-sm" style="border-top: 4px solid {accent};">
                <div class="card-header bg-light d-flex justify-content-between align-items-center">
                    <h5 class="card-title mb-0 card-header-title">{theme_name.replace('_', ' ').title()}</h5>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-secondary variant-toggle" data-theme-name="{theme_name}" data-variant="dark">Dark</button>
                        <button class="btn btn-outline-secondary variant-toggle" data-theme-name="{theme_name}" data-variant="light">Light</button>
                    </div>
                </div>
                <div class="card-body theme-preview-body" data-theme-name="{theme_name}" data-variant="{default_variant}" style="background-color: {bg} !important;">
                    <div class="preview-ui">
                        <span class="preview-label" style="color: {primary} !important;">Sample Text</span>
                        <span class="preview-label-secondary" style="color: {secondary} !important;">Secondary text</span>

                        <!-- Button -->
                        <div class="preview-button" style="background-color: {btn_bg} !important; color: {button_text_color} !important; padding: 0.25rem 0.75rem; border-radius: 4px; display: inline-block; margin: 0.5rem 0;">Button</div>

                        <!-- Dropdown -->
                        <div class="preview-dropdown" style="background-color: {dropdown_bg} !important; color: {dropdown_text} !important; border: 1px solid {dropdown_border} !important; border-radius: 4px; padding: 0.25rem 0.75rem; margin: 0.5rem 0; display: inline-block; cursor: default;">
                            <span>Option 1</span> <span style="float:right;">▼</span>
                        </div>

                        <!-- Text Input -->
                        <input type="text" class="preview-input" placeholder="Type here..." style="background-color: {dropdown_bg} !important; color: {primary} !important; border: 1px solid {border} !important; border-radius: 4px; padding: 0.25rem 0.5rem; margin: 0.5rem 0; width: 100%; display: block; box-sizing: border-box;">

                        <!-- Progress Bar -->
                        <div class="preview-progress" style="background-color: {track_bg} !important; border-radius: 4px; height: 8px; margin: 0.5rem 0; overflow: hidden;">
                            <div class="preview-progress-fill" style="width: 60%; height: 100%; background-color: {fill_bg} !important; border-radius: 4px;"></div>
                        </div>

                        <!-- Color Swatches -->
                        <div class="preview-swatch d-flex gap-2 mt-2">
                            <div style="background-color: {accent} !important; width: 30px; height: 30px; border-radius: 4px;"></div>
                            <div style="background-color: {btn_bg} !important; width: 30px; height: 30px; border-radius: 4px;"></div>
                            <div style="background-color: {border} !important; width: 30px; height: 30px; border-radius: 4px;"></div>
                        </div>
                    </div>
                </div>
                <div class="card-footer bg-transparent">
                    <button class="btn btn-sm btn-outline-primary apply-theme-preview" data-theme-name="{theme_name}" data-variant="dark">Preview Dark</button>
                    <button class="btn btn-sm btn-outline-primary apply-theme-preview" data-theme-name="{theme_name}" data-variant="light">Preview Light</button>
                </div>
            </div>
        </div>
        """

    # ==================== Full HTML page ====================
    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Themes Gallery - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="theme.css" rel="stylesheet">
    <style>
        [data-theme="dark"] .card-header-title {{
            color: #000 !important;
        }}
        .theme-preview-card {{
            transition: transform 0.2s;
        }}
        .theme-preview-card:hover {{
            transform: translateY(-5px);
        }}
        .preview-ui {{
            padding: 0.5rem;
            border-radius: 8px;
        }}
        .preview-label {{
            display: block;
            font-weight: bold;
            margin-bottom: 0.25rem;
        }}
        .preview-label-secondary {{
            display: block;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }}
        .preview-button, .preview-dropdown, .preview-input {{
            cursor: default;
        }}
        .theme-preview-modal .modal-body {{
            transition: all 0.2s;
        }}
        /* Override any !important from theme.css for preview elements */
        .theme-preview-body .preview-label,
        .theme-preview-body .preview-label-secondary,
        .theme-preview-body .preview-button,
        .theme-preview-body .preview-dropdown,
        .theme-preview-body .preview-input {{
            color: inherit !important; /* will be overridden by inline styles with !important */
        }}
    </style>
</head>
<body>
    {get_navbar_html()}
    <div class="container mt-5">
        {get_breadcrumbs([("Home", "index.html"), ("Themes Gallery", None)])}
        <h1 class="display-5 fw-bold mb-3"><i class="bi bi-palette me-3"></i>Themes Gallery</h1>
        <p class="lead">Explore all available UI themes with dark/light variants. Click "Preview Dark/Light" to see a live demo.</p>
        <hr>
        <div class="row" id="themesGrid">
            {themes_html}
        </div>
        <div class="text-center mt-4">
            <a href="index.html" class="btn btn-primary">
                <i class="bi bi-arrow-left me-2"></i>Back to Home
            </a>
        </div>
    </div>

    <!-- Modal for detailed preview -->
    <div class="modal fade theme-preview-modal" id="themePreviewModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Theme Preview: <span id="modalThemeName"></span> (<span id="modalVariantLabel">Dark</span>)</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body" id="modalPreviewBody">
                    <!-- Live preview will be injected -->
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    {get_footer_html()}
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // Theme data injected from Python
        const themeData = {json.dumps(themes, default=str)};

        // Helper: build box-shadow from shadow object
        function buildShadow(shadow) {{
            if (!shadow) return 'none';
            const color = shadow.color || [0,0,0];
            const alpha = shadow.alpha || 0.1;
            const dir = shadow.direction || [0, 2, 4, 0];
            const dx = dir[0] || 0;
            const dy = dir[1] || 2;
            const blur = dir[2] || 4;
            const spread = dir[3] || 0;
            return `${{dx}}px ${{dy}}px ${{blur}}px ${{spread}}px rgba(${{color[0]}},${{color[1]}},${{color[2]}},${{alpha}})`;
        }}

        // Helper: apply a style object to an element with !important
        function applyStyle(el, styleObj) {{
            if (!styleObj || !el) return;
            const color = styleObj.color;
            if (color) {{
                el.style.setProperty('background-color', `rgb(${{color[0]}},${{color[1]}},${{color[2]}})`, 'important');
            }}
            if (styleObj.cornerRadius !== undefined) {{
                el.style.setProperty('border-radius', styleObj.cornerRadius + 'px', 'important');
            }}
            if (styleObj.borderWidth !== undefined) {{
                el.style.setProperty('border-width', styleObj.borderWidth + 'px', 'important');
            }}
            if (styleObj.shadow) {{
                el.style.setProperty('box-shadow', buildShadow(styleObj.shadow), 'important');
            }}
        }}

        // Helper: set text color with !important
        function setTextColor(el, colorObj) {{
            if (el && colorObj && colorObj.color) {{
                el.style.setProperty('color', `rgb(${{colorObj.color[0]}},${{colorObj.color[1]}},${{colorObj.color[2]}})`, 'important');
            }}
        }}

        // Helper: set border color with !important
        function setBorderColor(el, colorObj) {{
            if (el && colorObj && colorObj.color) {{
                el.style.setProperty('border-color', `rgb(${{colorObj.color[0]}},${{colorObj.color[1]}},${{colorObj.color[2]}})`, 'important');
            }}
        }}

        // ---- Variant toggle on cards ----
        document.querySelectorAll('.variant-toggle').forEach(btn => {{
            btn.addEventListener('click', function(e) {{
                e.preventDefault();
                const themeName = this.getAttribute('data-theme-name');
                const variant = this.getAttribute('data-variant');
                const cardBody = this.closest('.card').querySelector('.theme-preview-body');
                const variantData = themeData[themeName]?.[variant];
                if (!variantData) return;

                // 1. Background
                const bgStyle = variantData.background;
                if (bgStyle) {{
                    cardBody.style.setProperty('background-color', `rgb(${{bgStyle.color[0]}},${{bgStyle.color[1]}},${{bgStyle.color[2]}})`, 'important');
                    applyStyle(cardBody, bgStyle);
                }}

                // 2. Labels
                const primary = variantData.text_primary;
                const secondary = variantData.text_secondary;
                const label = cardBody.querySelector('.preview-label');
                const labelSec = cardBody.querySelector('.preview-label-secondary');
                setTextColor(label, primary);
                setTextColor(labelSec, secondary);

                // 3. Button
                const btnEl = cardBody.querySelector('.preview-button');
                const btnStyle = variantData.button_normal;
                const btnTextStyle = variantData.button_text;
                if (btnStyle) applyStyle(btnEl, btnStyle);
                setTextColor(btnEl, btnTextStyle);

                // 4. Dropdown
                const dropdown = cardBody.querySelector('.preview-dropdown');
                const dropBg = variantData.dropdown_normal || variantData.background;
                const dropText = variantData.dropdown_text || variantData.text_primary;
                const dropBorder = variantData.dropdown_border || variantData.border;
                if (dropBg) applyStyle(dropdown, dropBg);
                setTextColor(dropdown, dropText);
                setBorderColor(dropdown, dropBorder);

                // 5. Text input
                const input = cardBody.querySelector('.preview-input');
                const inputBg = variantData.dropdown_normal || variantData.background;
                const inputText = variantData.text_primary;
                const inputBorder = variantData.border;
                if (inputBg) applyStyle(input, inputBg);
                setTextColor(input, inputText);
                setBorderColor(input, inputBorder);

                // 6. Progress bar
                const track = cardBody.querySelector('.preview-progress');
                const fill = cardBody.querySelector('.preview-progress-fill');
                const trackStyle = variantData.slider_track;
                const fillStyle = variantData.slider_thumb_normal || variantData.accent1;
                if (trackStyle) applyStyle(track, trackStyle);
                if (fillStyle) applyStyle(fill, fillStyle);

                // 7. Swatches
                const swatches = cardBody.querySelectorAll('.preview-swatch div');
                const accent = variantData.accent1;
                const btnBg = variantData.button_normal;
                const border = variantData.border;
                if (swatches.length >= 3) {{
                    if (accent) swatches[0].style.setProperty('background-color', `rgb(${{accent.color[0]}},${{accent.color[1]}},${{accent.color[2]}})`, 'important');
                    if (btnBg) swatches[1].style.setProperty('background-color', `rgb(${{btnBg.color[0]}},${{btnBg.color[1]}},${{btnBg.color[2]}})`, 'important');
                    if (border) swatches[2].style.setProperty('background-color', `rgb(${{border.color[0]}},${{border.color[1]}},${{border.color[2]}})`, 'important');
                }}

                // Update the "apply" buttons' data-variant
                const applyBtns = this.closest('.card').querySelectorAll('.apply-theme-preview');
                applyBtns.forEach(b => b.setAttribute('data-variant', variant));
            }});
        }});

        // ---- Apply preview (open modal) ----
        document.querySelectorAll('.apply-theme-preview').forEach(btn => {{
            btn.addEventListener('click', function(e) {{
                e.preventDefault();
                const themeName = this.getAttribute('data-theme-name');
                const variant = this.getAttribute('data-variant');
                const variantData = themeData[themeName]?.[variant];
                if (!variantData) return;

                const modal = new bootstrap.Modal(document.getElementById('themePreviewModal'));
                const modalBody = document.getElementById('modalPreviewBody');
                const modalTitle = document.getElementById('modalThemeName');
                const modalVariant = document.getElementById('modalVariantLabel');

                modalTitle.textContent = themeName.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                modalVariant.textContent = variant.charAt(0).toUpperCase() + variant.slice(1);

                // Build CSS variables for live preview
                let cssVars = '';
                const colorMap = {{
                    'button_normal': '--btn-bg',
                    'button_hover': '--btn-hover',
                    'button_text': '--btn-text',
                    'background': '--bg',
                    'text_primary': '--text-primary',
                    'text_secondary': '--text-secondary',
                    'accent1': '--accent',
                    'border': '--border-color',
                    'dropdown_normal': '--drop-bg',
                    'dropdown_text': '--drop-text',
                    'dropdown_border': '--drop-border',
                    'slider_track': '--track-bg',
                    'slider_thumb_normal': '--fill-bg'
                }};
                for (const [key, varName] of Object.entries(colorMap)) {{
                    const style = variantData[key];
                    if (style && style.color) {{
                        const rgb = style.color;
                        if (rgb.length >= 3) {{
                            cssVars += `${{varName}}: rgb(${{rgb[0]}}, ${{rgb[1]}}, ${{rgb[2]}});`;
                            if (style.cornerRadius !== undefined) {{
                                cssVars += `--${{varName}}-radius: ${{style.cornerRadius}}px;`;
                            }}
                            if (style.shadow) {{
                                const shadow = buildShadow(style.shadow);
                                cssVars += `--${{varName}}-shadow: ${{shadow}};`;
                            }}
                        }}
                    }}
                }}

                modalBody.innerHTML = `
                    <style>
                        .live-preview {{
                            background-color: var(--bg, #f8f9fa) !important;
                            padding: 2rem;
                            border-radius: 12px;
                            transition: all 0.2s;
                            box-shadow: var(--bg-shadow, none);
                        }}
                        .live-preview .sample-button {{
                            background-color: var(--btn-bg, #007bff) !important;
                            color: var(--btn-text, white) !important;
                            border: none;
                            padding: 0.5rem 1rem;
                            border-radius: var(--btn-bg-radius, 4px);
                            box-shadow: var(--btn-bg-shadow, none);
                            cursor: pointer;
                        }}
                        .live-preview .sample-button:hover {{
                            background-color: var(--btn-hover, #0056b3) !important;
                        }}
                        .live-preview p {{
                            color: var(--text-primary, #212529) !important;
                        }}
                        .live-preview small {{
                            color: var(--text-secondary, #6c757d) !important;
                        }}
                        .live-preview .accent-box {{
                            background-color: var(--accent, #6f42c1) !important;
                            width: 50px;
                            height: 50px;
                            border-radius: var(--accent-radius, 8px);
                            box-shadow: var(--accent-shadow, none);
                            margin-top: 1rem;
                        }}
                        .live-preview .border-demo {{
                            border: 1px solid var(--border-color, #dee2e6) !important;
                            padding: 0.5rem;
                            margin-top: 0.5rem;
                            border-radius: var(--border-radius, 4px);
                        }}
                        .live-preview .dropdown-demo {{
                            background-color: var(--drop-bg, #fff) !important;
                            color: var(--drop-text, #333) !important;
                            border: 1px solid var(--drop-border, #ccc) !important;
                            border-radius: var(--drop-bg-radius, 4px);
                            box-shadow: var(--drop-bg-shadow, none);
                            padding: 0.25rem 0.75rem;
                            display: inline-block;
                            margin-top: 0.5rem;
                        }}
                        .live-preview .input-demo {{
                            background-color: var(--drop-bg, #fff) !important;
                            color: var(--text-primary, #333) !important;
                            border: 1px solid var(--border-color, #ccc) !important;
                            border-radius: var(--drop-bg-radius, 4px);
                            box-shadow: var(--drop-bg-shadow, none);
                            padding: 0.25rem 0.5rem;
                            width: 100%;
                            box-sizing: border-box;
                            margin-top: 0.5rem;
                        }}
                        .live-preview .progress-demo {{
                            background-color: var(--track-bg, #e9ecef) !important;
                            border-radius: var(--track-bg-radius, 4px);
                            height: 8px;
                            margin-top: 0.5rem;
                            overflow: hidden;
                        }}
                        .live-preview .progress-demo .fill {{
                            width: 60%;
                            height: 100%;
                            background-color: var(--fill-bg, #007bff) !important;
                            border-radius: var(--fill-bg-radius, 4px);
                        }}
                    </style>
                    <div class="live-preview" style="${{cssVars}}">
                        <p>This is a live preview using the theme's colors.</p>
                        <small>Secondary text example</small>
                        <div><button class="sample-button mt-2">Sample Button</button></div>
                        <div class="dropdown-demo">Option 1 ▼</div>
                        <input class="input-demo" placeholder="Type here...">
                        <div class="progress-demo"><div class="fill"></div></div>
                        <div class="accent-box"></div>
                        <div class="border-demo">Bordered element</div>
                    </div>
                `;
                modal.show();
            }});
        }});
    }});
    </script>
    {get_search_script()}
</body>
</html>"""

    # Write the file
    with open("docs/themes.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("[OK] Themes preview page generated: docs/themes.html")

# ========== LESSONS PROCESSING ==========

def generate_lessons():
    """Generate lessons index, individual lesson pages with sidebar, and lessons.md map."""
    if not lessonsFldr.exists():
        print("No lessons folder found. Skipping lessons generation.")
        return
    
    # Define desired category order
    category_order = {"basics": 0, "intermediate": 1, "advanced": 2}
    
    # Collect all categories and sort by order
    categories = []
    for cat_dir in sorted(lessonsFldr.iterdir(), key=lambda d: category_order.get(d.name.lower(), 99)):
        if cat_dir.is_dir():
            lessons = []
            for md_file in sorted(cat_dir.glob("*.md")):
                match = re.match(r'(\d+)-(.*)\.md', md_file.name)
                if match:
                    num = int(match.group(1))
                    title = match.group(2).replace('-', ' ').title()
                    lessons.append({
                        'num': num,
                        'title': title,
                        'filename': md_file.name,
                        'path': md_file,
                        'slug': md_file.name.replace('.md', '.html')
                    })
                else:
                    lessons.append({
                        'num': 999,
                        'title': md_file.stem.replace('-', ' ').title(),
                        'filename': md_file.name,
                        'path': md_file,
                        'slug': md_file.name.replace('.md', '.html')
                    })
            if lessons:
                categories.append({
                    'name': cat_dir.name,
                    'display_name': cat_dir.name.title(),
                    'lessons': sorted(lessons, key=lambda x: x['num'])
                })
    
    if not categories:
        return
    
    docs_lessons = Path("docs/lessons")
    docs_lessons.mkdir(exist_ok=True)
    
    # Generate lessons hub index
    index_html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lessons - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="../theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html("../", "Lessons")}
    <div class="container mt-5">
        {get_breadcrumbs([("Home", "../index.html"), ("Lessons", None)])}
        <h1 class="mb-4">📖 LunaEngine Lessons</h1>
        <p class="lead">Step‑by‑step tutorials to master the framework.</p>
        <hr>
"""
    for cat in categories:
        index_html += f"""
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h3 class="h5 mb-0"><i class="bi bi-folder-fill me-2"></i>{cat['display_name']}</h3>
            </div>
            <div class="card-body">
                <div class="row">
        """
        for lesson in cat['lessons']:
            index_html += f"""
                    <div class="col-md-6 mb-3">
                        <div class="card h-100">
                            <div class="card-body">
                                <h5 class="card-title">{lesson['num']}. {lesson['title']}</h5>
                                <a href="{cat['name']}/{lesson['slug']}" class="btn btn-sm btn-outline-primary">Read Lesson →</a>
                            </div>
                        </div>
                    </div>
            """
        index_html += """
                </div>
            </div>
        </div>
        """
    
    index_html += f"""
        <div class="text-center mt-4">
            <a href="../index.html" class="btn btn-primary">Back to Home</a>
        </div>
    </div>
    {get_footer_html("../")}
</body>
</html>"""
    with open(docs_lessons / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"[OK] Lessons hub generated with {len(categories)} categories")
    
    # Generate individual lesson pages with sidebar (course track)
    for cat in categories:
        cat_output_dir = docs_lessons / cat['name']
        cat_output_dir.mkdir(exist_ok=True)
        lessons_list = cat['lessons']
        for idx, lesson in enumerate(lessons_list):
            with open(lesson['path'], 'r', encoding='utf-8') as f:
                md_content = f.read()
            prev_lesson = lessons_list[idx-1] if idx > 0 else None
            next_lesson = lessons_list[idx+1] if idx+1 < len(lessons_list) else None
            
            # Build sidebar HTML with all categories and lessons
            sidebar_html = '<div class="list-group list-group-flush">'
            for s_cat in categories:
                sidebar_html += f'<div class="list-group-item bg-light fw-bold">{s_cat["display_name"]}</div>'
                for s_lesson in s_cat['lessons']:
                    is_active = (s_cat == cat and s_lesson == lesson)
                    active_class = ' active' if is_active else ''
                    sidebar_html += f'<a href="../{s_cat["name"]}/{s_lesson["slug"]}" class="list-group-item list-group-item-action{active_class}">{s_lesson["num"]}. {s_lesson["title"]}</a>'
                sidebar_html += '<div class="mb-2"></div>'
            sidebar_html += '</div>'
            
            lesson_html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{lesson['title']} - LunaEngine Lessons</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="../../theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html("../../", "Lessons")}
    <div class="container mt-5">
        {get_breadcrumbs([("Home", "../../index.html"), ("Lessons", "../index.html"), (cat['display_name'], None), (lesson['title'], None)])}
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 d-none d-md-block">
                <div class="card shadow-sm sticky-top" style="top: 6rem; max-height: 80vh; overflow-y: auto;">
                    <div class="card-header bg-secondary text-white">
                        <h5 class="mb-0"><i class="bi bi-map me-2"></i>Course Track</h5>
                    </div>
                    <div class="card-body p-0">
                        {sidebar_html}
                    </div>
                </div>
            </div>
            <!-- Main content -->
            <div class="col-md-9">
                <div class="card shadow-sm">
                    <div class="card-header bg-primary text-white">
                        <h1 class="h3 mb-0">{lesson['num']}. {lesson['title']}</h1>
                    </div>
                    <div class="card-body markdown-content">
                        {md_content}
                    </div>
                    <div class="card-footer bg-transparent">
                        <div class="d-flex justify-content-between">
                            {"<a href='"+prev_lesson['slug']+"' class='btn btn-outline-primary'><i class='bi bi-arrow-left me-2'></i>Previous: "+prev_lesson['title']+"</a>" if prev_lesson else '<span></span>'}
                            {"<a href='"+next_lesson['slug']+"' class='btn btn-outline-primary'>Next: "+next_lesson['title']+" <i class='bi bi-arrow-right ms-2'></i></a>" if next_lesson else '<span></span>'}
                        </div>
                    </div>
                </div>
                <div class="text-center mt-4">
                    <a href="../index.html" class="btn btn-secondary"><i class="bi bi-journal-bookmark me-2"></i>All Lessons</a>
                </div>
            </div>
        </div>
    </div>
    {get_footer_html("../")}
    <script src="../../theme.js"></script>
    <script>document.addEventListener('DOMContentLoaded', function() {{
        if (typeof initSimpleMarkdownParser === 'function') initSimpleMarkdownParser();
        else setTimeout(function() {{
            if (window.initSimpleMarkdownParser) window.initSimpleMarkdownParser();
        }}, 100);
    }});</script>
</body>
</html>"""
            with open(cat_output_dir / lesson['slug'], "w", encoding="utf-8") as f:
                f.write(lesson_html)
            print(f"   [OK] Lesson: {cat['name']}/{lesson['title']}")

    # Generate lessons.md map file in project root
    md_content = "# LunaEngine Lessons\n\n"
    for cat in categories:
        md_content += f"## {cat['display_name']}\n\n"
        for lesson in cat['lessons']:
            md_content += f"- [{lesson['num']:02d} {lesson['title']}](lessons/{cat['name']}/{lesson['filename']})\n"
        md_content += "\n"
    with open("lessons.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] lessons.md map created in project root")

# ========== PAGE GENERATORS ==========

def get_navbar_html(path_prefix="./", active_module=None):
    # Placeholder now includes (Ctrl+K) hint
    return f"""
    <nav class="navbar navbar-expand-lg navbar-light sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="{path_prefix}index.html" id="navbar-logo-link">
                <i class="bi bi-moon-stars-fill me-2"></i>
                LunaEngine
            </a>
            <div class="d-flex align-items-center">
                <div class="input-group me-3">
                    <input type="text" id="moduleSearch" class="form-control" placeholder="Search functions, classes, methods... (Ctrl+K)">
                    <span class="input-group-text" id="searchIcon"><i class="bi bi-search"></i></span>
                </div>
                {( '<span class="badge bg-primary me-3">' + active_module.title() + '</span>' if active_module else '')}
                <button class="btn btn-outline-secondary theme-toggle">
                    <span class="theme-icon">🌙</span>
                </button>
            </div>
        </div>
    </nav>
    """

def get_search_script():
    # Updated to compute relative path correctly
    return """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('moduleSearch');
        const searchIcon = document.querySelector('.input-group-text');
        if (searchInput && searchIcon) {
            const performSearch = () => {
                const searchTerm = searchInput.value.trim();
                if (searchTerm) {
                    // Compute relative path to root search.html
                    const path = window.location.pathname;
                    const parts = path.split('/').filter(p => p && p !== '');
                    // Remove file part if present
                    let dirParts = parts;
                    if (dirParts.length > 0 && dirParts[dirParts.length - 1].includes('.')) {
                        dirParts = dirParts.slice(0, -1);
                    }
                    // Number of levels to go up to reach the directory containing search.html
                    const levels = Math.max(0, dirParts.length - 1);
                    const searchPath = '../'.repeat(levels) + 'search.html';
                    window.location.href = `${searchPath}?q=${encodeURIComponent(searchTerm)}`;
                }
            };
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault(); 
                    e.stopPropagation();
                    performSearch();
                    return false;
                }
            });
            searchIcon.addEventListener('click', performSearch);
            const form = searchInput.closest('form');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    performSearch();
                    return false;
                });
            }
        }
    });
    </script>
    """
    
def get_footer_html(prefix="./"):
    return f"""
    <footer class="footer-section">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5><i class="bi bi-moon-stars-fill me-2"></i>LunaEngine</h5>
                    <p class="text-white-50">2D Game Framework for Python</p>
                </div>
                <div class="col-md-6 text-end">
                    <p class="text-white-50">
                        <i class="bi bi-lightning-charge me-1"></i>
                        Documentation generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}
                    </p>
                </div>
            </div>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="{prefix}theme.js"></script>
    {get_search_script()}
    """

def get_breadcrumbs(links):
    breadcrumb_html = '<nav aria-label="breadcrumb"><ol class="breadcrumb">'
    for text, url in links:
        if url:
            breadcrumb_html += f'<li class="breadcrumb-item"><a href="{url}">{text}</a></li>'
        else:
            breadcrumb_html += f'<li class="breadcrumb-item active">{text}</li>'
    breadcrumb_html += '</ol></nav>'
    return breadcrumb_html

def generate_file_page(module_name, file_info, module_docs_path):
    """
    module_docs_path: Path object for the module's documentation root (e.g., docs/ui)
    file_info contains 'output_subdir' (e.g., 'elements') and 'base_name'
    """
    out_dir = module_docs_path / file_info['output_subdir']
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{file_info['base_name']}.html"
    
    depth = len(file_info['output_subdir'].split('/')) if file_info['output_subdir'] else 0
    path_prefix = '../' * (depth + 1)
    
    def format_args(args_list):
        formatted = []
        for arg in args_list:
            if 'default' in arg:
                formatted.append(f"{arg['name']}: {arg['type']} = {arg['default']}")
            else:
                formatted.append(f"{arg['name']}: {arg['type']}")
        return ", ".join(formatted)
    
    classes_html = ""
    for cls in file_info['classes']:
        methods_html = ""
        for m in cls['methods']:
            args_formatted = format_args(m['args'])
            method_id = f"method-{str(cls['name']).lower()}-{str(m['name']).lower()}"
            methods_html += f"""
            <div class="method-item ms-3 mb-3 p-3 border-start border-3 border-success bg-light-subtle rounded-end" id="{method_id}">
                <code class="fs-6 fw-bold text-color-title">def {m['name']}({args_formatted}) -> {m['returns']}</code>
                <div class="mt-2 text-muted small">{m['docstring']}</div>
            </div>"""
        attributes_html = ""
        if cls.get('attributes'):
            attributes_html = '<div class="attributes-section mb-4"><h6 class="text-uppercase text-muted fw-bold small">Attributes</h6>'
            for attr in cls['attributes']:
                attributes_html += f"""
                <div class="attribute-item ms-3 mb-2">
                    <code>{attr['name']}: {attr['type']} = {attr.get('default', 'None')}</code>
                </div>"""
            attributes_html += '</div>'
        classes_html += f"""
        <div class="card mb-5 shadow-sm border-0 overflow-hidden" id="class-{str(cls['name']).lower()}">
            <div class="card-header bg-success text-white py-3">
                <h3 class="mb-0 h5"><i class="bi bi-box me-2"></i>class {cls['name']}</h3>
            </div>
            <div class="card-body">
                <div class="docstring-section mb-4">
                    <h6 class="text-uppercase text-muted fw-bold small">Description</h6>
                    <p class="lead fs-6">{cls['docstring']}</p>
                </div>
                {attributes_html}
                <div class="methods-section">
                    <h6 class="text-uppercase text-muted fw-bold small mb-3">Methods</h6>
                    {methods_html if methods_html else '<p class="text-muted italic">No methods defined.</p>'}
                </div>
            </div>
        </div>"""
    functions_html = ""
    if file_info['functions']:
        for func in file_info['functions']:
            args_formatted = format_args(func['args'])
            function_id = f"func-{str(func['name']).lower()}"
            functions_html += f"""
            <div class="card mb-3 border-start border-2 border-info shadow-sm" id="{function_id}">
                <div class="card-body">
                    <code class="fs-5 fw-bold text-color-title">def {func['name']}({args_formatted}) -> {func['returns']}</code>
                    <p class="mt-2 mb-0 text-muted">{func['docstring']}</p>
                </div>
            </div>"""
    up_levels = depth + 1
    home_rel = '../' * up_levels + 'index.html'
    module_index_rel = '../' * depth + 'index.html'
    
    html_page = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_info['name']} - LunaEngine Docs</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{path_prefix}theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html(path_prefix, module_name)}
    <div class="container mt-5">
        {get_breadcrumbs([
            ("Home", home_rel),
            (module_name.title(), module_index_rel),
            (file_info['name'], None)
        ])}
        <div class="header-section mb-5">
            <h1 class="display-5 fw-bold"><i class="bi bi-file-earmark-code text-primary me-3"></i>{file_info['name']}</h1>
            <div class="p-4 bg-light rounded-3 border-start border-2 border-primary mt-3">
                <i class="bi bi-info-circle-fill me-2 text-primary"></i>
                <span class="text-muted">{file_info['docstring']}</span>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                {classes_html}
                {f'<h2 class="mt-5 mb-4 border-bottom pb-2">Global Functions</h2>' if functions_html else ''}
                {functions_html}
            </div>
        </div>
        <div class="mt-5 mb-5 text-center">
            <a href="{module_index_rel}" class="btn btn-outline-primary">
                <i class="bi bi-arrow-left me-2"></i>Back to {module_name.title()} Module
            </a>
        </div>
    </div>
    {get_footer_html("../")}
</body>
</html>"""
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_page)
    shutil.copy("docs/theme.js", out_dir / "theme.js")

def generate_module_index(module_name, module_info):
    files_by_dir = {}
    for file in module_info['files']:
        subdir = file['output_subdir'] or "."
        files_by_dir.setdefault(subdir, []).append(file)
    
    file_list_html = ""
    for subdir, files in sorted(files_by_dir.items()):
        if subdir != ".":
            file_list_html += f'<h4 class="mt-4 mb-3"><i class="bi bi-folder-fill me-2"></i>{subdir}/</h4><div class="row">'
        else:
            file_list_html += '<div class="row">'
        for file in files:
            link_path = f"{file['output_subdir']}/{file['base_name']}.html" if file['output_subdir'] else f"{file['base_name']}.html"
            file_list_html += f"""
            <div class="col-md-4 mb-4">
                <div class="card h-100 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title"><i class="bi bi-file-earmark-code me-2"></i>{file['name']}</h5>
                        <p class="card-text small text-muted">Contains {len(file['classes'])} classes and {len(file['functions'])} functions.</p>
                        <a href="{link_path}" class="btn btn-sm btn-outline-primary">View Documentation</a>
                    </div>
                </div>
            </div>"""
        file_list_html += '</div>'
    
    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_name.title()} - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="../theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html("../", module_name)}
    <div class="container mt-5">
        {get_breadcrumbs([
            ("Home", "../index.html"),
            (module_name.title(), None)
        ])}
        <h1 class="display-4">{module_name.title()} Module</h1>
        <p class="lead">{module_info['description']}</p>
        <hr>
        {file_list_html}
        <div class="mt-5 mb-5 text-center">
            <a href="../index.html" class="btn btn-outline-primary">
                <i class="bi bi-arrow-left me-2"></i>Back to Home
            </a>
        </div>
    </div>
    {get_footer_html("../")}
</body>
</html>"""
    with open(f"docs/{module_name}/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_quick_start():
    print("Creating quick guide...")
    snake_code = ""
    snake_file_path = "examples/snake_demo.py"
    try:
        if os.path.exists(snake_file_path):
            with open(snake_file_path, 'r', encoding='utf-8') as f:
                snake_code = f.read()
            print(f"   [OK] Loaded snake game from {snake_file_path}")
        else:
            snake_code = "# Snake game file not found at examples/snake_demo.py"
            print(f"   [WARNING] Snake game file not found: {snake_file_path}")
    except Exception as e:
        snake_code = f"# Error reading snake game: {e}"
        print(f"   [WARNING] Error reading snake game: {e}")
    snake_code = html.escape(snake_code)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quick Start - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="theme.css" rel="stylesheet">
    <style>
        /* Chevron rotation animation */
        .chevron-rotate {{
            transition: transform 0.3s ease;
        }}
        .chevron-rotate.collapsed {{
            transform: rotate(-90deg);
        }}
    </style>
</head>
<body>
    {get_navbar_html()}
    <div class="container mt-5">
        {get_breadcrumbs([
            ("Home", "index.html"),
            ("Quick Start", None)
        ])}
        <h1 class="text-center mb-4">Quick Start Guide</h1>
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0"><i class="bi bi-lightning me-2"></i>Quick Installation</h5>
            </div>
            <div class="card-body">
                <pre><code># Clone the repository
git clone https://github.com/MrJuaumBR/LunaEngine.git
cd LunaEngine

# Install dependencies
pip install -r requirements.txt

# Run the Snake Game example
python examples/snake_demo.py</code></pre>
            </div>
        </div>
        
        <!-- SNAKE GAME EXAMPLE WITH COLLAPSE -->
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0"><i class="bi bi-play-circle me-2"></i>Snake Game Example</h5>
                <button class="btn btn-sm btn-light" type="button" 
                        data-bs-toggle="collapse" 
                        data-bs-target="#snakeCodeCollapse" 
                        aria-expanded="false" 
                        aria-controls="snakeCodeCollapse">
                    <i class="bi bi-chevron-down chevron-rotate collapsed" id="snakeToggleIcon"></i>
                </button>
            </div>
            <div class="collapse" id="snakeCodeCollapse">
                <div class="card-body">
                    <p class="text-muted mb-3">
                        <i class="bi bi-info-circle me-1"></i>
                        This is the actual code from <code>examples/snake_demo.py</code>
                    </p>
                    <pre><code>{snake_code}</code></pre>
                </div>
            </div>
        </div>
        
        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0"><i class="bi bi-book me-2"></i>Next Steps</h5>
            </div>
            <div class="card-body">
                <ol>
                    <li>Explore the <a href="examples/">examples hub</a> for more projects</li>
                    <li>Check out modules in the documentation</li>
                    <li>Visit our <a href="https://github.com/MrJuaumBR/LunaEngine-Games">games repository</a></li>
                    <li>Experiment with UI, graphics, and utilities</li>
                    <li>Join our <a href="contact.html">community</a> for help and support</li>
                </ol>
            </div>
        </div>
        <div class="text-center">
            <a href="index.html" class="btn btn-primary me-2">
                <i class="bi bi-house me-2"></i>Back to Home
            </a>
            <a href="examples/" class="btn btn-outline-primary me-2">
                <i class="bi bi-code-slash me-2"></i>View Examples
            </a>
            <a href="contact.html" class="btn btn-outline-primary">
                <i class="bi bi-people me-2"></i>Join Community
            </a>
        </div>
    </div>
    {get_footer_html()}
    <script>
        // Toggle chevron rotation when collapse is shown/hidden
        document.addEventListener('DOMContentLoaded', function() {{
            const collapseElement = document.getElementById('snakeCodeCollapse');
            const toggleIcon = document.getElementById('snakeToggleIcon');
            if (collapseElement && toggleIcon) {{
                collapseElement.addEventListener('show.bs.collapse', function () {{
                    toggleIcon.classList.remove('collapsed');
                }});
                collapseElement.addEventListener('hide.bs.collapse', function () {{
                    toggleIcon.classList.add('collapsed');
                }});
            }}
        }});
    </script>
</body>
</html>"""
    with open("docs/quick-start.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_examples_hub():
    print("Generating examples hub with subdirectories...")
    examples_dir = Path("examples")
    docs_examples_dir = Path("docs/examples")
    docs_examples_dir.mkdir(parents=True, exist_ok=True)

    # Walk all .py files
    examples_by_category = {}
    for py_file in examples_dir.rglob("*.py"):
        rel_path = py_file.relative_to(examples_dir)
        # Determine category: root files go to "General"
        if rel_path.parent == Path("."):
            category = "General"
        else:
            category = rel_path.parent.name.title()
        examples_by_category.setdefault(category, []).append(py_file)

    # Generate individual HTML pages for each example
    for category, files in examples_by_category.items():
        for py_file in files:
            rel_path = py_file.relative_to(examples_dir)
            # Output directory = docs/examples/ + relative parent
            out_dir = docs_examples_dir / rel_path.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{py_file.stem}.html"

            # Compute prefix for CSS/JS
            depth = len(out_dir.relative_to(Path("docs")).parts)  # e.g. ('examples','audio') -> 2
            prefix = "../" * depth

            # Read content and docstring
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                docstring_match = re.search(r'\"\"\"(.*?)\"\"\"', content, re.DOTALL)
                description = docstring_match.group(1).strip() if docstring_match else "No description"
                description = description.split('\n')[0] if '\n' in description else description

            html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{py_file.stem.replace('_', ' ').title()} - LunaEngine Examples</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{prefix}theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html(prefix)}
    <div class="container mt-5">
        {get_breadcrumbs([
            ("Home", f"{prefix}index.html"),
            ("Examples Hub", f"{prefix}examples/index.html"),
            (category, None),
            (py_file.stem.replace('_', ' ').title(), None)
        ])}
        <div class="row">
            <div class="col-lg-8">
                <h1 class="mb-3"><i class="bi bi-code-slash me-2"></i>{py_file.stem.replace('_', ' ').title()}</h1>
                <div class="card mb-4 shadow-sm">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="bi bi-file-earmark-code me-2"></i>{py_file.name}</h5>
                    </div>
                    <div class="card-body">
                        <pre><code class="language-python">{html.escape(content)}</code></pre>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card shadow-sm sticky-top" style="top: 20px;">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0"><i class="bi bi-info-circle me-2"></i>About</h5>
                    </div>
                    <div class="card-body">
                        <p>{description}</p>
                        <hr>
                        <div class="d-grid gap-2">
                            <a href="{py_file.name}" download class="btn btn-outline-primary">
                                <i class="bi bi-download me-2"></i>Download Python File
                            </a>
                            <a href="index.html" class="btn btn-outline-secondary">
                                <i class="bi bi-arrow-left me-2"></i>Back to Examples
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {get_footer_html(prefix)}
</body>
</html>"""
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            # Copy the .py file to the same location (preserving subdirs)
            shutil.copy2(py_file, out_dir / py_file.name)
            print(f"   [OK] Example: {rel_path}")

    # Generate the hub index with categories
    hub_html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Examples Hub - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="../theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html("../")}
    <div class="container mt-5">
        {get_breadcrumbs([
            ("Home", "../index.html"),
            ("Examples Hub", None)
        ])}
        <h1 class="mb-4"><i class="bi bi-code-slash me-2"></i>Examples Hub</h1>
        <p class="lead mb-4">Explore practical examples of LunaEngine in action.</p>
"""
    for category, files in sorted(examples_by_category.items()):
        hub_html += f"""
        <div class="card mb-4">
            <div class="card-header bg-secondary text-white">
                <h5 class="mb-0"><i class="bi bi-folder-fill me-2"></i>{category}</h5>
            </div>
            <div class="card-body">
                <div class="row">
        """
        for py_file in files:
            rel_path = py_file.relative_to(examples_dir)
            # Build link to the HTML page (preserving subdir)
            link = f"{rel_path.parent / py_file.stem}.html" if rel_path.parent != Path(".") else f"{py_file.stem}.html"
            hub_html += f"""
                    <div class="col-md-4 mb-3">
                        <div class="card h-100">
                            <div class="card-body">
                                <h6 class="card-title">{py_file.stem.replace('_', ' ').title()}</h6>
                                <p class="card-text small text-muted">{description[:100]}...</p>
                                <a href="{link}" class="btn btn-sm btn-outline-primary">View</a>
                            </div>
                        </div>
                    </div>
            """
        hub_html += """
                </div>
            </div>
        </div>
        """

    hub_html += f"""
        <div class="mt-4 text-center">
            <a href="../index.html" class="btn btn-primary">
                <i class="bi bi-arrow-left me-2"></i>Back to Home
            </a>
        </div>
    </div>
    {get_footer_html("../")}
</body>
</html>"""
    with open(docs_examples_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(hub_html)
    print("[OK] Examples hub generated with categories")

def generate_search_data(project):
    print("Generating global search data...")
    search_data = {
        "modules": [],
        "classes": [],
        "functions": [],
        "methods": [],
        "pages": [],
        "examples": [],
        "last_updated": datetime.now().isoformat()
    }
    for module_name, module_info in project['modules'].items():
        for file_info in module_info['files']:
            file_name = str(file_info['name']).split('.py')[0]
            if file_info['output_subdir']:
                link_prefix = f"{module_name}/{file_info['output_subdir']}/{file_name}.html"
            else:
                link_prefix = f"{module_name}/{file_name}.html"
            for class_info in file_info['classes']:
                class_id = f"class-{class_info['name'].lower()}"
                search_data["classes"].append({
                    "name": class_info['name'],
                    "module": module_name,
                    "file": file_info['name'],
                    "description": class_info['docstring'],
                    "link": f"{link_prefix}#{class_id}",
                    "methods_count": len(class_info['methods'])
                })
                for method_info in class_info['methods']:
                    method_id = f"method-{class_info['name'].lower()}-{method_info['name'].lower()}"
                    search_data["methods"].append({
                        "name": method_info['name'],
                        "class": class_info['name'],
                        "module": module_name,
                        "description": method_info['docstring'],
                        "link": f"{link_prefix}#{method_id}",
                        "is_method": True
                    })
            for function_info in file_info['functions']:
                function_id = f"func-{function_info['name'].lower()}"
                search_data["functions"].append({
                    "name": function_info['name'],
                    "module": module_name,
                    "file": file_info['name'],
                    "description": function_info['docstring'],
                    "link": f"{link_prefix}#{function_id}",
                    "is_method": False
                })
        search_data["modules"].append({
            "name": module_name,
            "title": module_name.title(),
            "description": module_info['description'],
            "link": f"{module_name}/index.html",
            "files_count": len(module_info['files']),
            "classes_count": len(module_info['classes']),
            "functions_count": len(module_info['functions'])
        })
    search_data["pages"].extend([
        {"name": "Quick Start", "description": "Get started quickly with LunaEngine", "link": "quick-start.html", "type": "guide"},
        {"name": "Examples Hub", "description": "Practical examples of LunaEngine in action", "link": "examples/", "type": "examples"},
        {"name": "Community & Contact", "description": "Join our community and get help", "link": "contact.html", "type": "community"},
        {"name": "Lessons", "description": "Step‑by‑step tutorials", "link": "lessons/", "type": "lessons"},
        {"name": "Themes Gallery", "description": "Browse and preview all UI themes", "link": "themes.html", "type": "themes"}
    ])
    examples_dir = "examples"
    if os.path.exists(examples_dir):
        for file in os.listdir(examples_dir):
            if file.endswith('.py'):
                search_data["examples"].append({
                    "name": file.replace('.py', '').replace('_', ' ').title(),
                    "file": file,
                    "link": f"examples/{file.replace('.py', '.html')}",
                    "type": "example"
                })
    with open("docs/search-data.json", "w", encoding="utf-8") as f:
        json.dump(search_data, f, indent=2)
    print(f"[OK] Global search data generated: {len(search_data['modules'])} modules, {len(search_data['classes'])} classes, {len(search_data['functions'])} functions, {len(search_data['methods'])} methods, {len(search_data['examples'])} examples")
    return search_data

def generate_search_page(project, search_data):
    print("Creating search page...")
    total_items = (len(search_data['modules']) + len(search_data['classes']) + len(search_data['functions']) + len(search_data['methods']) + len(search_data['pages']) + len(search_data.get('examples', [])))
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="theme.css" rel="stylesheet">
    <style>
    .search-highlight {{
        background-color: #ffeb3b;
        padding: 2px 4px;
        border-radius: 3px;
    }}
    .result-item {{
        border-left: 4px solid var(--primary-color);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }}
    .result-item:hover {{
        background-color: rgba(67, 97, 238, 0.05);
        transform: translateX(5px);
    }}
    .result-type-badge {{
        font-size: 0.7rem;
        padding: 0.2rem 0.5rem;
    }}
    /* Autocomplete dropdown styles */
    .suggestion-box {{
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: #fff;
        border: 1px solid #ced4da;
        border-radius: 0 0 0.375rem 0.375rem;
        max-height: 300px;
        overflow-y: auto;
        z-index: 1000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        display: none;
    }}
    .suggestion-item {{
        padding: 8px 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 1px solid #f0f0f0;
    }}
    .suggestion-item:hover,
    .suggestion-item.active {{
        background-color: #f0f7ff;
    }}
    .suggestion-item small {{
        margin-left: auto;
        color: #6c757d;
    }}
    .suggestion-item i {{
        font-size: 1.1rem;
    }}
    .search-group {{
        position: relative;
    }}
    </style>
</head>
<body>
    {get_navbar_html()}
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="index.html">Home</a></li>
                        <li class="breadcrumb-item active">Search Results</li>
                    </ol>
                </nav>
                <h1 class="mb-4"><i class="bi bi-search me-2"></i>Search Results</h1>
                <div id="searchInfo" class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    Global search across all LunaEngine documentation: <span id="totalIndexCount">0</span> items indexed
                </div>
                <div class="input-group mb-4 search-group">
                    <input type="text" id="globalSearch" class="form-control" placeholder="Search everything in LunaEngine... (Ctrl+K)">
                    <button class="btn btn-primary" type="button" id="searchButton">
                        <i class="bi bi-search"></i> Search
                    </button>
                    <div id="suggestionBox" class="suggestion-box"></div>
                </div>
                <div id="searchResults" class="search-results-container">
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Search functionality requires JavaScript. Please enable JavaScript to use search.
                    </div>
                </div>
                <div id="noResults" class="text-center py-5" style="display: none;">
                    <i class="bi bi-search display-1 text-muted mb-3"></i>
                    <h3 class="text-muted">No results found</h3>
                    <p class="text-muted">Try different keywords or browse the modules directly.</p>
                    <a href="index.html" class="btn btn-primary mt-3">
                        <i class="bi bi-house me-2"></i>Back to Home
                    </a>
                </div>
                <div id="searchStats" class="mt-4 text-center" style="display: none;">
                    <small class="text-muted" id="statsText"></small>
                </div>
                <div class="mt-5">
                    <h5>Quick Navigation</h5>
                    <div class="row">
                        <div class="col-md-3 mb-2">
                            <a href="index.html" class="btn btn-outline-primary w-100">
                                <i class="bi bi-house me-1"></i>Home
                            </a>
                        </div>
                        <div class="col-md-3 mb-2">
                            <a href="examples/" class="btn btn-outline-success w-100">
                                <i class="bi bi-code-slash me-1"></i>Examples
                            </a>
                        </div>
                        <div class="col-md-3 mb-2">
                            <a href="quick-start.html" class="btn btn-outline-info w-100">
                                <i class="bi bi-play-circle me-1"></i>Quick Start
                            </a>
                        </div>
                        <div class="col-md-3 mb-2">
                            <a href="contact.html" class="btn btn-outline-warning w-100">
                                <i class="bi bi-people me-1"></i>Community
                            </a>
                        </div>
                        <div class="col-md-3 mb-2">
                            <a href="themes.html" class="btn btn-outline-secondary w-100">
                                <i class="bi bi-palette me-1"></i>Themes
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="theme.js"></script>
    <script src="search.js"></script>
    <script>
    (function() {{
        'use strict';

        // --- Keyboard shortcut: Ctrl+K / Cmd+K to focus search ---
        document.addEventListener('keydown', function(e) {{
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {{
                e.preventDefault();
                const searchInput = document.getElementById('globalSearch') || document.getElementById('moduleSearch');
                if (searchInput) {{
                    searchInput.focus();
                    searchInput.select();
                }}
            }}
        }});

        // --- Autocomplete dropdown ---
        let searchData = null;
        let suggestionTimeout = null;
        const suggestionBox = document.getElementById('suggestionBox');
        const globalSearch = document.getElementById('globalSearch');

        // Listen for the custom event when search data is ready
        document.addEventListener('searchDataReady', function(e) {{
            searchData = e.detail;
            document.getElementById('totalIndexCount').textContent = 
                (searchData.modules?.length || 0) + 
                (searchData.classes?.length || 0) + 
                (searchData.functions?.length || 0) + 
                (searchData.methods?.length || 0) + 
                (searchData.pages?.length || 0) + 
                (searchData.examples?.length || 0);
        }});

        // Helper: highlight text
        function highlightText(text, term) {{
            if (!term) return text;
            const regex = new RegExp(`(${{term}})`, 'gi');
            return text.replace(regex, '<mark class="search-highlight">$1</mark>');
        }}

        function updateSuggestions(term) {{
            if (!searchData || !term || term.length < 2) {{
                suggestionBox.style.display = 'none';
                return;
            }}

            const lowerTerm = term.toLowerCase();
            const allItems = [];

            const types = [
                {{ data: searchData.modules, type: 'module', icon: 'bi-folder' }},
                {{ data: searchData.classes, type: 'class', icon: 'bi-box' }},
                {{ data: searchData.functions, type: 'function', icon: 'bi-gear' }},
                {{ data: searchData.methods, type: 'method', icon: 'bi-hammer' }},
                {{ data: searchData.pages, type: 'page', icon: 'bi-file-text' }},
                {{ data: searchData.examples, type: 'example', icon: 'bi-code-slash' }}
            ];

            types.forEach(({{ data, type, icon }}) => {{
                if (!data) return;
                data.forEach(item => {{
                    let name = item.name || item.title || '';
                    let description = item.description || '';
                    let module = item.module || '';
                    let score = 0;
                    const nameLower = name.toLowerCase();
                    const descLower = description.toLowerCase();
                    const moduleLower = module.toLowerCase();

                    if (nameLower.includes(lowerTerm)) {{
                        score += 10;
                        if (nameLower.startsWith(lowerTerm)) score += 5;
                    }}
                    if (descLower.includes(lowerTerm)) score += 3;
                    if (moduleLower.includes(lowerTerm)) score += 2;

                    if (score > 0) {{
                        allItems.push({{
                            name: name,
                            description: description,
                            link: item.link,
                            module: module,
                            type: type,
                            icon: icon,
                            score: score,
                            original: item
                        }});
                    }}
                }});
            }});

            allItems.sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
            const top = allItems.slice(0, 10);

            if (top.length === 0) {{
                suggestionBox.style.display = 'none';
                return;
            }}

            suggestionBox.innerHTML = top.map((item, idx) => `
                <div class="suggestion-item" data-index="${{idx}}" data-link="${{item.link}}">
                    <i class="bi ${{item.icon}} me-2"></i>
                    <span>${{highlightText(item.name, term)}}</span>
                    ${{item.module ? `<small>${{item.module}}</small>` : ''}}
                    <span class="badge bg-secondary ms-2">${{item.type}}</span>
                </div>
            `).join('');

            suggestionBox.style.display = 'block';

            // Click handler
            suggestionBox.querySelectorAll('.suggestion-item').forEach(el => {{
                el.addEventListener('click', function() {{
                    window.location.href = this.dataset.link;
                }});
            }});
        }}

        // Debounce
        function debounce(func, wait) {{
            let timeout;
            return function(...args) {{
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            }};
        }}

        if (globalSearch) {{
            globalSearch.addEventListener('input', debounce(function(e) {{
                const term = this.value.trim();
                updateSuggestions(term);
            }}, 150));

            globalSearch.addEventListener('blur', function() {{
                setTimeout(() => {{
                    suggestionBox.style.display = 'none';
                }}, 200);
            }});

            // Keyboard navigation
            let selectedIndex = -1;
            globalSearch.addEventListener('keydown', function(e) {{
                const items = suggestionBox.querySelectorAll('.suggestion-item');
                if (items.length === 0) return;

                if (e.key === 'ArrowDown') {{
                    e.preventDefault();
                    selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                    updateActive(items, selectedIndex);
                }} else if (e.key === 'ArrowUp') {{
                    e.preventDefault();
                    selectedIndex = Math.max(selectedIndex - 1, -1);
                    updateActive(items, selectedIndex);
                }} else if (e.key === 'Enter') {{
                    if (selectedIndex >= 0 && selectedIndex < items.length) {{
                        e.preventDefault();
                        const link = items[selectedIndex].dataset.link;
                        if (link) window.location.href = link;
                    }}
                }}
            }});

            function updateActive(items, index) {{
                items.forEach((el, i) => {{
                    el.classList.toggle('active', i === index);
                }});
                if (index >= 0 && index < items.length) {{
                    items[index].scrollIntoView({{ block: 'nearest' }});
                }}
            }}
        }}
    }})();
    </script>
    <!-- Navbar search script (same as in theme.js but ensures correct path) -->
    <script>
    (function() {{
        document.addEventListener('DOMContentLoaded', function() {{
            const searchInput = document.getElementById('moduleSearch');
            const searchIcon = document.querySelector('.input-group-text');
            if (searchInput && searchIcon) {{
                const performSearch = () => {{
                    const searchTerm = searchInput.value.trim();
                    if (searchTerm) {{
                        const path = window.location.pathname;
                        const parts = path.split('/').filter(p => p && p !== '');
                        let dirParts = parts;
                        if (dirParts.length > 0 && dirParts[dirParts.length - 1].includes('.')) {{
                            dirParts = dirParts.slice(0, -1);
                        }}
                        const levels = Math.max(0, dirParts.length - 1);
                        const searchPath = '../'.repeat(levels) + 'search.html';
                        window.location.href = `${{searchPath}}?q=${{encodeURIComponent(searchTerm)}}`;
                    }}
                }};
                searchInput.addEventListener('keydown', (e) => {{
                    if (e.key === 'Enter') {{
                        e.preventDefault(); 
                        e.stopPropagation();
                        performSearch();
                        return false;
                    }}
                }});
                searchIcon.addEventListener('click', performSearch);
                const form = searchInput.closest('form');
                if (form) {{
                    form.addEventListener('submit', (e) => {{
                        e.preventDefault();
                        performSearch();
                        return false;
                    }});
                }}
            }}
        }});
    }})();
    </script>
</body>
</html>"""
    with open("docs/search.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_theme_files():
    css_file = "docs/theme.css"
    js_file = "docs/theme.js"
    if not os.path.exists(css_file):
        print("Creating enhanced theme.css...")
        css_content = """/* LunaEngine Documentation - Standardized Theme */
:root {
    --primary-color: #4361ee;
    --secondary-color: #3a0ca3;
    --success-color: #4cc9f0;
    --info-color: #7209b7;
    --warning-color: #f72585;
    --danger-color: #b5179e;
    --light-color: #f8f9fa;
    --dark-color: #212529;
}
[data-theme="dark"] {
    --primary-color: #5a6fdb;
    --secondary-color: #4a1ca8;
    --dark-color: #f8f9fa;
    --light-color: #212529;
}
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: var(--light-color);
    color: var(--dark-color);
    transition: all 0.3s ease;
}
.navbar { background-color: var(--primary-color) !important; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.navbar-brand { font-size: 1.5rem; color: white !important; }
.hero-section {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    padding: 4rem 0;
    color: white;
    margin-bottom: 2rem;
}
.stats-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: transform 0.1s ease;
    transform-style: preserve-3d;
}
.tilt-card {
    transform-style: preserve-3d;
    perspective: 1000px;
}
.card {
    border: none;
    border-radius: 10px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    margin-bottom: 1.5rem;
}
.card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important; }
.card-header { border-radius: 10px 10px 0 0 !important; font-weight: 600; }
.module-card { border: 1px solid #e0e0e0; }
[data-theme="dark"] .module-card { border-color: #444; }
pre {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 1rem;
    border-left: 4px solid var(--primary-color);
}
[data-theme="dark"] pre { background-color: #2d3748; color: #e2e8f0; }
code {
    color: var(--primary-color);
    background-color: rgba(67, 97, 238, 0.1);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
}
.breadcrumb { background-color: transparent; padding: 0.75rem 0; }
.breadcrumb-item a { color: var(--primary-color); text-decoration: none; }
.breadcrumb-item.active { color: var(--dark-color); }
.footer-section {
    background-color: var(--dark-color);
    color: white;
    padding: 3rem 0;
    margin-top: 4rem;
}
.search-results-container .result-item {
    border-left: 4px solid var(--primary-color);
    transition: all 0.3s ease;
}
.search-results-container .result-item:hover {
    background-color: rgba(67, 97, 238, 0.05);
    transform: translateX(5px);
}
.color-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
}
.color-item {
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    color: white;
    font-weight: 500;
}
@media (max-width: 768px) {
    .hero-section { padding: 2rem 0; }
    .stats-card { margin-top: 2rem; }
    .color-grid { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.card, .module-card, .result-item { animation: fadeIn 0.5s ease-out; }
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: #f1f1f1; }
::-webkit-scrollbar-thumb { background: var(--primary-color); border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: var(--secondary-color); }
.code-stats-content { color: var(--text-color); line-height: 1.6; max-height: 400px; overflow-y: auto; }
.code-stats-content.preview { max-height: 150px; overflow: hidden; position: relative; }
.code-stats-content.preview::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 50px;
    background: linear-gradient(transparent, var(--card-bg));
    pointer-events: none;
}
/* Suggestion box (added) */
.suggestion-box {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #fff;
    border: 1px solid #ced4da;
    border-radius: 0 0 0.375rem 0.375rem;
    max-height: 300px;
    overflow-y: auto;
    z-index: 1000;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    display: none;
}
.suggestion-item {
    padding: 8px 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #f0f0f0;
}
.suggestion-item:hover,
.suggestion-item.active {
    background-color: #f0f7ff;
}
.suggestion-item small {
    margin-left: auto;
    color: #6c757d;
}
.suggestion-item i {
    font-size: 1.1rem;
}
.search-group {
    position: relative;
}
"""
        with open(css_file, "w", encoding="utf-8") as f:
            f.write(css_content)
    if not os.path.exists(js_file):
        print("Creating enhanced theme.js with tilt...")
        js_content = """// LunaEngine Theme Manager
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.querySelector('.theme-toggle');
    const themeIcon = document.querySelector('.theme-icon');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            if (themeIcon) themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
            this.innerHTML = `<span class="theme-icon">${newTheme === 'dark' ? '☀️' : '🌙'}</span>`;
        });
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        if (themeIcon) {
            themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
            themeToggle.innerHTML = `<span class="theme-icon">${savedTheme === 'dark' ? '☀️' : '🌙'}</span>`;
        }
    }
    // 3D Tilt effect for stats card
    const tiltCard = document.querySelector('.tilt-card');
    if (tiltCard) {
        tiltCard.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
        tiltCard.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
        });
    }
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    document.querySelectorAll('pre code').forEach(codeBlock => {
        const pre = codeBlock.parentElement;
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-outline-secondary copy-button';
        button.innerHTML = '<i class="bi bi-clipboard"></i>';
        button.style.position = 'absolute';
        button.style.top = '10px';
        button.style.right = '10px';
        button.style.opacity = '0.7';
        pre.style.position = 'relative';
        pre.appendChild(button);
        button.addEventListener('click', function() {
            const text = codeBlock.textContent;
            navigator.clipboard.writeText(text).then(() => {
                button.innerHTML = '<i class="bi bi-check"></i>';
                button.classList.replace('btn-outline-secondary', 'btn-success');
                setTimeout(() => {
                    button.innerHTML = '<i class="bi bi-clipboard"></i>';
                    button.classList.replace('btn-success', 'btn-outline-secondary');
                }, 2000);
            });
        });
    });
    const urlParams = new URLSearchParams(window.location.search);
    const searchTerm = urlParams.get('q');
    if (searchTerm) highlightSearchTerm(searchTerm);

    // Keyboard shortcut: Ctrl+K / Cmd+K to focus search
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('moduleSearch') || document.getElementById('globalSearch');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });
});

function highlightSearchTerm(term) {
    const elements = document.querySelectorAll('.card-body, .docstring-content, p, li');
    const regex = new RegExp(`(${term})`, 'gi');
    elements.forEach(element => {
        const html = element.innerHTML;
        const highlighted = html.replace(regex, '<mark class="search-highlight">$1</mark>');
        element.innerHTML = highlighted;
    });
}

// Simple markdown parser without external dependencies
function initSimpleMarkdownParser() {
    const elements = document.querySelectorAll('.markdown-content, .code-stats-content');
    
    console.log(`🔍 Found ${elements.length} markdown elements to render`);
    
    elements.forEach(element => {
        if (element.textContent && !element.classList.contains('rendered')) {
            let content = element.textContent;
            
            // Enhanced markdown parsing
            content = parseMarkdown(content);
            element.innerHTML = content;
            element.classList.add('rendered');
            
            addMarkdownStyles();
            initCopyButtons(); // Re-init copy buttons for new code blocks
            
            console.log('✅ Markdown content rendered');
        }
    });
}

function parseMarkdown(text) {
    if (!text) return '';
    
    // Process tables FIRST
    text = parseMarkdownTables(text);
    
    // Process code blocks
    text = text.replace(/```(\\w+)?\\n([\\s\\S]*?)```/g, function(match, lang, code) {
        return `<pre><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
    });
    
    // Headers
    text = text.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
    text = text.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
    text = text.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
    text = text.replace(/^#### (.*?)$/gm, '<h4>$1</h4>');
    text = text.replace(/^##### (.*?)$/gm, '<h5>$1</h5>');
    text = text.replace(/^###### (.*?)$/gm, '<h6>$1</h6>');
    
    // Bold
    text = text.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
    
    // Italic
    text = text.replace(/(^|\\s)\\*([^*\\s][^*]*[^*\\s]?)\\*($|\\s)/g, '$1<em>$2</em>$3');
    
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Links
    text = text.replace(/\\[(.*?)\\]\\((.*?)\\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Lists - unordered
    text = text.replace(/^\\s*[-*+] (.*?)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\\/li>)/gs, function(match) {
        if (match.includes('</li><li>')) {
            return '<ul>' + match + '</ul>';
        }
        return match;
    });
    
    // Lists - ordered
    text = text.replace(/^\\s*\\d+\\. (.*?)$/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\\/li>)/gs, function(match) {
        if (match.includes('</li><li>')) {
            return '<ol>' + match + '</ol>';
        }
        return match;
    });
    
    // Blockquotes
    text = text.replace(/^> (.*?)$/gm, '<blockquote>$1</blockquote>');
    
    // Horizontal rule
    text = text.replace(/^\\s*---\\s*$/gm, '<hr>');
    text = text.replace(/^\\s*\\*\\*\\*\\s*$/gm, '<hr>');
    
    // Paragraphs
    const blocks = text.split(/\\n\\s*\\n/);
    const processedBlocks = blocks.map(block => {
        if (block.trim().startsWith('<table') || 
            block.trim().startsWith('<pre') || 
            block.trim().startsWith('<ul') || 
            block.trim().startsWith('<ol') || 
            block.trim().startsWith('<blockquote') ||
            block.trim().startsWith('<h1') ||
            block.trim().startsWith('<h2') ||
            block.trim().startsWith('<h3') ||
            block.trim().startsWith('<h4') ||
            block.trim().startsWith('<h5') ||
            block.trim().startsWith('<h6')) {
            return block;
        }
        if (!block.trim()) return '';
        const withLineBreaks = block.replace(/\\n/g, '<br>');
        return `<p>${withLineBreaks}</p>`;
    });
    
    text = processedBlocks.filter(block => block !== '').join('\\n');
    
    return text;
}

function parseMarkdownTables(text) {
    const lines = text.split('\\n');
    let result = [];
    let i = 0;
    
    while (i < lines.length) {
        const line = lines[i];
        
        if (line.includes('|') && !line.includes('```') && line.trim()) {
            const tableRows = [];
            let j = i;
            while (j < lines.length && lines[j].includes('|') && !lines[j].includes('```') && lines[j].trim()) {
                tableRows.push(lines[j]);
                j++;
            }
            
            if (tableRows.length >= 2) {
                const separatorRow = tableRows[1];
                if (separatorRow.replace(/[^\\-|]/g, '').length > 0 && separatorRow.includes('-')) {
                    result.push(convertMarkdownTableToHTML(tableRows));
                    i = j;
                    continue;
                }
            }
        }
        
        result.push(line);
        i++;
    }
    
    return result.join('\\n');
}

function convertMarkdownTableToHTML(tableRows) {
    if (tableRows.length < 2) return tableRows.join('\\n');
    
    let html = '<table>\\n';
    
    // Header row
    const headerCells = splitTableRow(tableRows[0]);
    html += '  <thead>\\n    <tr>\\n';
    headerCells.forEach(cell => {
        html += `      <th>${cell.trim()}</th>\\n`;
    });
    html += '    </tr>\\n  </thead>\\n';
    
    // Data rows
    html += '  <tbody>\\n';
    for (let i = 2; i < tableRows.length; i++) {
        const cells = splitTableRow(tableRows[i]);
        if (cells.length > 0) {
            html += '    <tr>\\n';
            cells.forEach(cell => {
                let cellContent = cell.trim();
                cellContent = cellContent.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
                cellContent = cellContent.replace(/\\*([^*]+)\\*/g, '<em>$1</em>');
                cellContent = cellContent.replace(/`([^`]+)`/g, '<code>$1</code>');
                html += `      <td>${cellContent}</td>\\n`;
            });
            html += '    </tr>\\n';
        }
    }
    html += '  </tbody>\\n</table>';
    
    return html;
}

function splitTableRow(row) {
    return row.split('|')
        .map(cell => cell.trim())
        .filter(cell => cell !== '' && !/^\\-+$/.test(cell));
}

function addMarkdownStyles() {
    if (!document.getElementById('markdown-styles')) {
        const styles = `
            <style id="markdown-styles">
            .markdown-content, .code-stats-content {
                line-height: 1.6;
            }
            .markdown-content table, .code-stats-content table {
                width: 100%;
                border-collapse: collapse;
                margin: 0.5rem 0 1rem 0;
                background: white;
                font-size: 0.9em;
            }
            .markdown-content th, .code-stats-content th,
            .markdown-content td, .code-stats-content td {
                padding: 0.5rem 0.75rem;
                border: 1px solid #dee2e6;
                text-align: left;
            }
            .markdown-content th, .code-stats-content th {
                background-color: #f8f9fa;
                font-weight: bold;
                color: #495057;
                font-size: 0.85em;
            }
            .markdown-content td, .code-stats-content td {
                font-size: 0.85em;
            }
            .markdown-content p, .code-stats-content p {
                margin: 0.5rem 0 1rem 0;
            }
            .markdown-content h1, .code-stats-content h1 { 
                font-size: 2rem; 
                margin: 1rem 0 0.5rem 0;
            }
            .markdown-content h2, .code-stats-content h2 { 
                font-size: 1.75rem; 
                margin: 0.75rem 0 0.5rem 0;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 0.25rem;
                color: #343a40;
            }
            .markdown-content h3, .code-stats-content h3 { 
                font-size: 1.5rem; 
                margin: 1rem 0 0.5rem 0; 
                color: #495057;
            }
            .markdown-content h4, .code-stats-content h4 { 
                font-size: 1.25rem; 
                margin: 0.75rem 0 0.5rem 0; 
                color: #6c757d;
            }
            .markdown-content h5, .code-stats-content h5 { 
                font-size: 1.1rem; 
                margin: 0.5rem 0; 
                color: #6c757d;
            }
            .markdown-content h6, .code-stats-content h6 { 
                font-size: 1rem; 
                margin: 0.5rem 0; 
                color: #6c757d;
            }
            .markdown-content hr, .code-stats-content hr {
                border: none;
                border-top: 2px solid #dee2e6;
                margin: 2rem 0;
            }
            .markdown-content a, .code-stats-content a {
                color: #007bff;
                text-decoration: none;
            }
            .markdown-content a:hover, .code-stats-content a:hover {
                text-decoration: underline;
            }
            
            [data-theme="dark"] .markdown-content,
            [data-theme="dark"] .code-stats-content {
                color: #e9ecef;
            }
            [data-theme="dark"] .markdown-content code,
            [data-theme="dark"] .code-stats-content code,
            [data-theme="dark"] .markdown-content pre,
            [data-theme="dark"] .code-stats-content pre {
                background-color: #2d3748;
                color: #e2e8f0;
            }
            [data-theme="dark"] .markdown-content th,
            [data-theme="dark"] .code-stats-content th {
                background-color: #4a5568;
                color: #e2e8f0;
                border-color: #718096;
            }
            [data-theme="dark"] .markdown-content table,
            [data-theme="dark"] .code-stats-content table {
                border-color: #718096;
                background-color: #2d3748;
            }
            [data-theme="dark"] .markdown-content td,
            [data-theme="dark"] .code-stats-content td {
                border-color: #718096;
                color: #e2e8f0;
            }
            [data-theme="dark"] .markdown-content blockquote,
            [data-theme="dark"] .code-stats-content blockquote {
                background-color: #2d3748;
                border-left-color: #63b3ed;
                color: #cbd5e0;
            }
            [data-theme="dark"] .markdown-content h1,
            [data-theme="dark"] .code-stats-content h1,
            [data-theme="dark"] .markdown-content h2,
            [data-theme="dark"] .code-stats-content h2,
            [data-theme="dark"] .markdown-content h3,
            [data-theme="dark"] .code-stats-content h3 {
                color: #f7fafc;
                border-color: #4a5568;
            }
            [data-theme="dark"] .markdown-content a,
            [data-theme="dark"] .code-stats-content a {
                color: #63b3ed;
            }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', styles);
    }
}

function initCopyButtons() {
    $('pre').each(function() {
        const $pre = $(this);
        if ($pre.find('.copy-btn').length === 0) {
            const $copyBtn = $('<button class="btn btn-sm btn-outline-secondary copy-btn">Copy</button>');
            $pre.css('position', 'relative').append($copyBtn);
            $copyBtn.on('click', function() {
                const code = $pre.find('code').text() || $pre.text();
                navigator.clipboard.writeText(code).then(() => {
                    $copyBtn.text('Copied!');
                    setTimeout(() => $copyBtn.text('Copy'), 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                    $copyBtn.text('Failed!');
                    setTimeout(() => $copyBtn.text('Copy'), 2000);
                });
            });
        }
    });
}

function initCodeStats() {
    const $collapse = $('#codeStatsCollapse');
    const $toggleBtn = $('[data-bs-target="#codeStatsCollapse"]');
    
    if ($collapse.length && $toggleBtn.length) {
        const statsCollapsed = localStorage.getItem('statsCollapsed') === 'true';
        
        if (statsCollapsed) {
            $collapse.removeClass('show');
            $toggleBtn.find('i').removeClass('bi-chevron-down').addClass('bi-chevron-right');
        }
        
        $toggleBtn.on('click', function() {
            setTimeout(() => {
                const isCollapsed = !$collapse.hasClass('show');
                localStorage.setItem('statsCollapsed', isCollapsed);
                $toggleBtn.find('i').toggleClass('bi-chevron-down bi-chevron-right', isCollapsed);
            }, 350);
        });
    }
}

function initSearchPage() {
    if (typeof window.LunaEngineSearch === 'undefined') {
        console.log('Loading search engine...');
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initSimpleMarkdownParser, 100);
});
"""
        with open(js_file, "w", encoding="utf-8") as f:
            f.write(js_content)

def generate_about_page(project_info):
    about_content = get_about_md()
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html()}
    <div class="container mt-5">
        {get_breadcrumbs([("Home", "index.html"), ("About", None)])}
        <div class="card shadow-sm">
            <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0"><i class="bi bi-info-circle-fill me-2"></i>About LunaEngine</h5>
                <button class="btn btn-sm btn-light" type="button" data-bs-toggle="collapse" data-bs-target="#aboutCollapse" aria-expanded="true" aria-controls="aboutCollapse">
                    <i class="bi bi-chevron-down"></i>
                </button>
            </div>
            <div class="collapse show" id="aboutCollapse">
                <div class="card-body markdown-content">
                    {about_content}
                </div>
            </div>
        </div>
        <div class="mt-4 text-center">
            <a href="index.html" class="btn btn-primary">
                <i class="bi bi-arrow-left me-2"></i>Back to Home
            </a>
        </div>
    </div>
    {get_footer_html()}
</body>
</html>"""
    with open("docs/about.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_contact_page():
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Community & Contact - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html()}
    <div class="container mt-5">
        {get_breadcrumbs([("Home", "index.html"), ("Community & Contact", None)])}
        <h1 class="text-center mb-4">Community & Contact</h1>
        <div class="row g-4">
            <div class="col-md-6">
                <div class="card h-100 text-center shadow-sm">
                    <div class="card-body">
                        <i class="bi bi-github fs-1 text-primary mb-3"></i>
                        <h5>GitHub Repository</h5>
                        <p class="text-muted">Source code, issues, and contributions</p>
                        <a href="https://github.com/MrJuaumBR/LunaEngine" class="btn btn-outline-primary" target="_blank">Visit GitHub</a>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card h-100 text-center shadow-sm">
                    <div class="card-body">
                        <i class="bi bi-discord fs-1 text-info mb-3"></i>
                        <h5>Discord Community</h5>
                        <p class="text-muted">Join our community for help and discussions</p>
                        <a href="https://discord.gg/fb84sHDX7R" class="btn btn-outline-info" target="_blank">Join Discord</a>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card h-100 text-center shadow-sm">
                    <div class="card-body">
                        <i class="bi bi-youtube fs-1 text-danger mb-3"></i>
                        <h5>YouTube Channel</h5>
                        <p class="text-muted">Watch tutorials and demos</p>
                        <a href="https://youtube.com/@MrJuaumBR" class="btn btn-outline-danger" target="_blank">Go to Channel</a>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card h-100 text-center shadow-sm">
                    <div class="card-body">
                        <i class="bi bi-code-slash fs-1 text-success mb-3"></i>
                        <h5>Examples Hub</h5>
                        <p class="text-muted">Browse practical examples</p>
                        <a href="examples/" class="btn btn-outline-success">View Examples</a>
                    </div>
                </div>
            </div>
        </div>
        <div class="card mt-4 shadow-sm">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0"><i class="bi bi-info-circle me-2"></i>Contributing</h5>
            </div>
            <div class="card-body">
                <p>We welcome contributions! Here's how you can help:</p>
                <ul>
                    <li>Report bugs and issues on GitHub/Discord</li>
                    <li>Suggest new features and improvements</li>
                    <li>Submit pull requests with bug fixes</li>
                    <li>Improve documentation and examples</li>
                    <li>Share your projects made with LunaEngine</li>
                </ul>
            </div>
        </div>
        <div class="text-center mt-4">
            <a href="index.html" class="btn btn-primary me-2">
                <i class="bi bi-house me-2"></i>Back to Home
            </a>
            <a href="quick-start.html" class="btn btn-outline-primary me-2">
                <i class="bi bi-play-circle me-2"></i>Quick Start
            </a>
            <a href="examples/" class="btn btn-outline-primary">
                <i class="bi bi-code-slash me-2"></i>Examples
            </a>
        </div>
    </div>
    {get_footer_html("./")}
</body>
</html>"""
    with open("docs/contact.html", "w", encoding="utf-8") as f:
        f.write(html)

def get_about_md():
    file_path = './about.md'
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return content
        except Exception as e:
            print(f"Error reading about.md: {e}")
            return "About content not available"
    return "About file not found"

def get_code_statistics():
    stats_path = "lunaengine/CODE_STATISTICS.md"
    if os.path.exists(stats_path):
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return content
        except Exception as e:
            print(f"Error reading CODE_STATISTICS.md: {e}")
            return "Statistics not available"
    return "Statistics file not found"

def get_module_description(module_name):
    descriptions = {
        "core": "Core framework systems - Engine/LunaEngine, Window, Renderer",
        "ui": "User interface components - Buttons, Layouts, Themes",
        "graphics": "Graphics and rendering - Sprites, Lighting, Particles",
        "utils": "Utility functions - Performance, Math, Threading",
        "backend": "Renderer backends - OpenGL, Pygame",
        "misc": "Miscellaneous functions - Bones, Icons",
        "tools": "Development tools - Documentation, Analysis",
        "storage": "Data storage and serialization - Atlas, Savedata, Encryption"
    }
    return descriptions.get(module_name, f"{module_name} module")

def analyze_project():
    print("Analyzing project structure...")
    project = {
        'modules': {},
        'total_files': 0,
        'total_classes': 0,
        'total_functions': 0,
        'total_methods': 0
    }
    lunaengine_path = "lunaengine"
    if not os.path.exists(lunaengine_path):
        print("[ERROR] lunaengine folder not found")
        return project
    expected_modules = ["core", "ui", "graphics", "utils", "backend", "misc", "tools", "storage"]
    for module in expected_modules:
        module_path = os.path.join(lunaengine_path, module)
        if os.path.exists(module_path):
            module_info = analyze_module(module_path, module)
            project['modules'][module] = module_info
            project['total_files'] += len(module_info['files'])
            project['total_classes'] += len(module_info['classes'])
            project['total_functions'] += len(module_info['functions'])
            project['total_methods'] += module_info['total_methods']
            print(f"   [OK] {module}: {len(module_info['files'])} files found (including nested)")
    return project

def analyze_module(module_path, module_name):
    module_info = {
        'name': module_name,
        'description': get_module_description(module_name),
        'files': [],
        'classes': [],
        'functions': [],
        'total_methods': 0
    }
    for root, dirs, files in os.walk(module_path):
        dirs[:] = [d for d in dirs if not d.startswith('__')]
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, module_path)
                subdir = os.path.dirname(rel_path)
                base_name = file.replace('.py', '')
                output_subdir = subdir.replace(os.sep, '/')
                file_info = analyze_python_file(file_path)
                if file == 'themes.py':
                    file_info['theme_colors'] = extract_theme_colors(file_path)
                file_data = {
                    'name': file,
                    'base_name': base_name,
                    'rel_path': rel_path,
                    'output_subdir': output_subdir,
                    'classes': file_info['classes'],
                    'functions': file_info['functions'],
                    'docstring': file_info['docstring'],
                    'theme_colors': file_info.get('theme_colors', {})
                }
                module_info['files'].append(file_data)
                module_info['classes'].extend(file_info['classes'])
                module_info['functions'].extend(file_info['functions'])
                module_info['total_methods'] += file_info['total_methods']
    return module_info

def analyze_python_file(file_path):
    file_info = {'classes': [], 'functions': [], 'docstring': '', 'total_methods': 0}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            file_info['docstring'] = format_docstring(ast.get_docstring(tree))
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_info = extract_class_info(node)
                    file_info['classes'].append(class_info)
                    file_info['total_methods'] += len(class_info['methods'])
                elif isinstance(node, ast.FunctionDef):
                    file_info['functions'].append(extract_function_info(node))
    except Exception as e:
        print(f"      [WARNING] Error parsing {os.path.basename(file_path)}: {e}")
    return file_info

def extract_class_info(class_node):
    return {
        'name': class_node.name,
        'docstring': format_docstring(ast.get_docstring(class_node)),
        'methods': [extract_function_info(n, True) for n in class_node.body if isinstance(n, ast.FunctionDef)],
        'bases': [ast.unparse(base) for base in class_node.bases],
        'attributes': extract_class_attributes(class_node)
    }

def extract_function_info(node, is_method=False):
    args = []
    for arg in node.args.args:
        arg_name = arg.arg
        arg_type = ast.unparse(arg.annotation) if arg.annotation else 'Any'
        args.append({'name': arg_name, 'type': arg_type})
    if node.args.vararg:
        args.append({'name': f"*{node.args.vararg.arg}", 'type': 'tuple'})
    if node.args.kwarg:
        args.append({'name': f"**{node.args.kwarg.arg}", 'type': 'dict'})
    defaults_offset = len(node.args.args) - len(node.args.defaults)
    for i, default in enumerate(node.args.defaults):
        if i + defaults_offset < len(args):
            args[i + defaults_offset]['default'] = ast.unparse(default)
    return {
        'name': node.name,
        'docstring': format_docstring(ast.get_docstring(node)),
        'args': args,
        'returns': ast.unparse(node.returns) if node.returns else 'Any',
        'is_method': is_method
    }

def extract_class_attributes(class_node):
    attributes = []
    for item in class_node.body:
        if isinstance(item, ast.AnnAssign):
            attr_name = item.target.id if isinstance(item.target, ast.Name) else 'unknown'
            attr_type = ast.unparse(item.annotation) if item.annotation else 'Any'
            default_value = ast.unparse(item.value) if item.value else 'None'
            attributes.append({'name': attr_name, 'type': attr_type, 'default': default_value})
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    attr_name = target.id
                    default_value = ast.unparse(item.value) if item.value else 'None'
                    attributes.append({'name': attr_name, 'type': 'Any', 'default': default_value})
    return attributes

def generate_main_page(project):
    print("Creating main page with code statistics dashboard...")
    stats = load_code_stats()
    
    # Top 10 files with relative size for progress bars
    top_files = sorted(stats.get('files', []), key=lambda x: x['total_lines'], reverse=True)[:10]
    max_lines = top_files[0]['total_lines'] if top_files else 1
    
    # Extensions data for simple bar list
    ext_data = stats.get('files_by_extension', {})
    ext_items = sorted(ext_data.items(), key=lambda x: x[1], reverse=True)
    max_ext_count = ext_items[0][1] if ext_items else 1
    
    # Theme and element stats
    theme_stats = stats.get('themes', {})
    total_themes = theme_stats.get('total_themes', 0)
    total_variants = theme_stats.get('total_variants', 0)
    total_icons = stats.get('total_icons', 0)
    total_elements = stats.get('elements', {}).get('total_elements', 0)
    
    # Build the HTML with embedded JSON for JavaScript
    stats_json = json.dumps(stats, default=str)
    
    # Generate file ranking HTML
    file_ranking_html = ""
    for idx, f in enumerate(top_files, 1):
        pct = (f['total_lines'] / max_lines) * 100
        file_ranking_html += f"""
        <div class="file-rank-item">
            <span class="rank-num">{idx}.</span>
            <span class="rank-name">{f['path'][:45]}</span>
            <span class="rank-lines">{f['total_lines']}</span>
            <div class="rank-bar"><div style="width: {pct:.1f}%;"></div></div>
        </div>
        """
    
    # Extension bars
    ext_bars_html = ""
    for ext, count in ext_items:
        pct = (count / max_ext_count) * 100
        ext_bars_html += f"""
        <div class="ext-bar-item">
            <span class="ext-name">{ext or 'no ext'}</span>
            <span class="ext-count">{count}</span>
            <div class="ext-bar"><div style="width: {pct:.1f}%;"></div></div>
        </div>
        """
    
    # Build the main HTML – escape double braces for JavaScript
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LunaEngine - Documentation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="theme.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* Dashboard specific styles are now in theme.css */
    </style>
</head>
<body>
    {get_navbar_html()}
    <!-- Hero Section -->
    <section class="hero-section">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-8">
                    <h1 class="display-4 fw-bold text-white mb-3">
                        <i class="bi bi-moon-stars-fill me-3"></i>LunaEngine
                    </h1>
                    <p class="lead text-white mb-4">A powerful and intuitive 2D game framework for Python</p>
                    <div class="d-flex flex-wrap gap-2">
                        <span class="badge bg-light text-dark fs-6 p-2"><i class="bi bi-lightning me-1"></i>High Performance</span>
                        <span class="badge bg-light text-dark fs-6 p-2"><i class="bi bi-palette me-1"></i>Modern UI</span>
                        <span class="badge bg-light text-dark fs-6 p-2"><i class="bi bi-code-slash me-1"></i>Pure Python</span>
                    </div>
                </div>
                <div class="col-lg-4 text-center">
                    <div class="stats-card tilt-card">
                        <h3 class="text-white mb-2">{len(project['modules'])}</h3>
                        <p class="text-white-50 mb-1">Modules</p>
                        <div class="d-flex justify-content-center gap-3 flex-wrap">
                            <small class="text-white-50">{project['total_files']} files</small>
                            <small class="text-white-50">{project['total_classes']} classes</small>
                            <small class="text-white-50">{project['total_functions']} functions</small>
                            <small class="text-white-50">{project['total_methods']} methods</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Quick links bar -->
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="card bg-primary text-white">
                    <div class="card-body py-3">
                        <div class="row align-items-center">
                            <div class="col-md-7">
                                <h6 class="mb-0"><i class="bi bi-rocket me-2"></i>Get started quickly with LunaEngine</h6>
                            </div>
                            <div class="col-md-5 text-end">
                                <a href="quick-start.html" class="btn btn-light btn-sm me-2"><i class="bi bi-play-circle me-1"></i>Quick Guide</a>
                                <a href="lessons/" class="btn btn-light btn-sm me-2"><i class="bi bi-journal-bookmark me-1"></i>Lessons</a>
                                <a href="contact.html" class="btn btn-outline-light btn-sm me-2"><i class="bi bi-people me-1"></i>Community</a>
                                <a href="about.html" class="btn btn-outline-light btn-sm me-2"><i class="bi bi-info-circle me-1"></i>About</a>
                                <a href="examples/" class="btn btn-outline-light btn-sm me-2"><i class="bi bi-code-slash me-1"></i>Examples</a>
                                <a href="themes.html" class="btn btn-outline-light btn-sm me-2"><i class="bi bi-palette me-1"></i>Themes</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Install card -->
    <div class="container mt-4">
        <div class="card shadow-sm border-0">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0"><i class="bi bi-download me-2"></i>Install LunaEngine</h5>
            </div>
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <div class="btn-group" role="group">
                            <input type="radio" class="btn-check" name="installOption" id="optWindows" value="windows" autocomplete="off" checked>
                            <label class="btn btn-outline-primary" for="optWindows">Windows</label>
                            <input type="radio" class="btn-check" name="installOption" id="optLinux" value="linux" autocomplete="off">
                            <label class="btn btn-outline-primary" for="optLinux">Linux</label>
                            <input type="radio" class="btn-check" name="installOption" id="optTestPyPi" value="testpypi" autocomplete="off">
                            <label class="btn btn-outline-primary" for="optTestPyPi">TestPyPi</label>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="input-group">
                            <code class="form-control bg-light" id="installCommand">pip install lunaengine</code>
                            <button class="btn btn-outline-secondary copy-install-btn" type="button" title="Copy to clipboard"><i class="bi bi-clipboard"></i></button>
                        </div>
                        <small class="text-muted">Click the copy button to copy the command.</small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ========== CODE STATISTICS DASHBOARD ========== -->
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <div class="glass-card">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h4 class="mb-0"><i class="bi bi-graph-up me-2"></i>Code Statistics Dashboard</h4>
                        <span class="badge bg-secondary">{stats.get('version', 'unknown')} - {stats.get('version_status', '')}</span>
                    </div>
                    <div class="row g-4">
                        <!-- Pie Chart -->
                        <div class="col-lg-3 col-md-6">
                            <div class="chart-container">
                                <canvas id="codePieChart"></canvas>
                            </div>
                            <p class="text-center text-muted small mt-2">Distribution of lines</p>
                        </div>
                        <!-- Summary Stats -->
                        <div class="col-lg-4 col-md-6">
                            <div class="stats-grid">
                                <div class="stat-item"><div class="stat-number">{stats.get('total_files', 0)}</div><div class="stat-label">Files</div></div>
                                <div class="stat-item"><div class="stat-number">{stats.get('total_lines', 0):,}</div><div class="stat-label">Total Lines</div></div>
                                <div class="stat-item"><div class="stat-number">{stats.get('code_lines', 0):,}</div><div class="stat-label">Code</div></div>
                                <div class="stat-item"><div class="stat-number">{stats.get('comment_lines', 0):,}</div><div class="stat-label">Comments</div></div>
                                <div class="stat-item"><div class="stat-number">{stats.get('blank_lines', 0):,}</div><div class="stat-label">Blank</div></div>
                                <div class="stat-item"><div class="stat-number">{total_themes}</div><div class="stat-label">Themes</div></div>
                                <div class="stat-item"><div class="stat-number">{total_variants}</div><div class="stat-label">Variants</div></div>
                                <div class="stat-item"><div class="stat-number">{total_icons}</div><div class="stat-label">Icons</div></div>
                                <div class="stat-item"><div class="stat-number">{total_elements}</div><div class="stat-label">UI Elements</div></div>
                            </div>
                        </div>
                        <!-- Top Files Ranking -->
                        <div class="col-lg-5 col-md-12">
                            <h6 class="mb-2"><i class="bi bi-trophy me-1"></i>Top Files (by lines)</h6>
                            <div class="file-rank-list">
                                {file_ranking_html}
                            </div>
                        </div>
                    </div>
                    <!-- Extensions bars -->
                    <div class="row mt-4">
                        <div class="col-12">
                            <h6 class="mb-2"><i class="bi bi-tags me-1"></i>Files by Extension</h6>
                            <div class="ext-bar-list">
                                {ext_bars_html}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ========== MODULES ========== -->
    <div class="container mt-5">
        <h2 class="mb-4">LunaEngine Modules</h2>
        <div class="row g-4" style="margin-bottom: 1vw;">
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
        const installRadios = document.querySelectorAll('input[name="installOption"]');
        const installCommandSpan = document.getElementById('installCommand');
        const copyBtn = document.querySelector('.copy-install-btn');
        
        function updateCommand() {{
            const selected = document.querySelector('input[name="installOption"]:checked').value;
            switch(selected) {{
                case 'windows': installCommandSpan.textContent = 'pip install lunaengine'; break;
                case 'linux': installCommandSpan.textContent = 'pip3 install lunaengine'; break;
                case 'testpypi': installCommandSpan.textContent = 'pip install -i https://test.pypi.org/simple/ lunaengine'; break;
            }}
        }}
        installRadios.forEach(radio => radio.addEventListener('change', updateCommand));
        copyBtn.addEventListener('click', function() {{
            const textToCopy = installCommandSpan.textContent;
            navigator.clipboard.writeText(textToCopy).then(() => {{
                const originalIcon = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="bi bi-check"></i>';
                copyBtn.classList.add('btn-success');
                copyBtn.classList.remove('btn-outline-secondary');
                setTimeout(() => {{
                    copyBtn.innerHTML = originalIcon;
                    copyBtn.classList.remove('btn-success');
                    copyBtn.classList.add('btn-outline-secondary');
                }}, 2000);
            }});
        }});
        
        // --- Pie Chart ---
        const stats = {stats_json};
        const pieCtx = document.getElementById('codePieChart').getContext('2d');
        const pieChart = new Chart(pieCtx, {{
            type: 'pie',
            data: {{
                labels: ['Code', 'Comments', 'Blank'],
                datasets: [{{
                    data: [stats.code_lines, stats.comment_lines, stats.blank_lines],
                    backgroundColor: ['#4caf50', '#ff9800', '#2196f3'],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            color: getComputedStyle(document.documentElement).getPropertyValue('--text-color').trim() || '#333',
                            font: {{ size: 10 }}
                        }}
                    }}
                }}
            }}
        }});
        window.lunaPieChart = pieChart;

        // Watch for theme changes and update legend color
        const observer = new MutationObserver(function(mutations) {{
            mutations.forEach(function(mutation) {{
                if (mutation.attributeName === 'data-theme') {{
                    const theme = document.documentElement.getAttribute('data-theme');
                    const color = theme === 'dark' ? '#e9ecef' : '#333';
                    if (window.lunaPieChart) {{
                        window.lunaPieChart.options.plugins.legend.labels.color = color;
                        window.lunaPieChart.update();
                    }}
                }}
            }});
        }});
        observer.observe(document.documentElement, {{ attributes: true }});
    }});
    </script>
    """
    
    # Add modules (unchanged – keep your existing module loop)
    module_styles = {
        "core": {"icon": "bi-cpu", "color": "primary", "name": "Core Systems"},
        "ui": {"icon": "bi-ui-radios", "color": "success", "name": "User Interface"},
        "graphics": {"icon": "bi-brightness-high", "color": "warning", "name": "Graphics & Rendering"},
        "utils": {"icon": "bi-tools", "color": "info", "name": "Utilities"},
        "backend": {"icon": "bi-hdd-stack", "color": "secondary", "name": "Renderer Backends"},
        "misc": {"icon": "bi-backpack", "color": "dark", "name": "Miscellaneous"},
        "tools": {"icon": "bi-wrench", "color": "danger", "name": "Development Tools"},
        "storage": {"icon": "bi-database", "color": "info", "name": "Storage"}
    }
    for module_name, module_info in project['modules'].items():
        style = module_styles.get(module_name, {"icon": "bi-box", "color": "primary", "name": module_name.title()})
        html += f"""
            <div class="col-lg-4 col-md-6">
                <div class="card module-card h-100 shadow-sm">
                    <div class="card-header bg-{style['color']} text-white">
                        <div class="d-flex align-items-center">
                            <i class="bi {style['icon']} fs-4 me-3"></i>
                            <div>
                                <h5 class="mb-0">{style['name']}</h5>
                                <small>{module_name}</small>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="text-muted">{module_info['description']}</p>
                        <div class="module-stats d-flex flex-wrap gap-2">
                            <span class="badge bg-light text-dark"><i class="bi bi-file-text me-1"></i>{len(module_info['files'])} files</span>
                            <span class="badge bg-light text-dark"><i class="bi bi-box me-1"></i>{len(module_info['classes'])} classes</span>
                            <span class="badge bg-light text-dark"><i class="bi bi-gear me-1"></i>{len(module_info['functions'])} functions</span>
                            <span class="badge bg-light text-dark"><i class="bi bi-hammer me-1"></i>{module_info['total_methods']} methods</span>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <a href="{module_name}/index.html" class="btn btn-{style['color']} w-100"><i class="bi bi-book me-2"></i>View Documentation</a>
                    </div>
                </div>
            </div>
    """
    html += f"""
        </div>
    </div>
    {get_footer_html("./")}
</body>
</html>"""
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_sitemap():
    """
    Generate sitemap.xml for the documentation site.
    Crawls all .html files in docs/ and creates a sitemap.
    """
    base_url = "https://mrjuaumbr.github.io/LunaEngine/"
    docs_dir = Path("docs")
    sitemap_path = docs_dir / "sitemap.xml"

    if not docs_dir.exists():
        print("docs folder not found, skipping sitemap generation.")
        return

    urls = []
    for html_file in docs_dir.rglob("*.html"):
        # Skip the search page if you want, or include it – it's fine to include
        rel_path = html_file.relative_to(docs_dir)
        loc = base_url + str(rel_path).replace("\\", "/")
        lastmod = datetime.now().date().isoformat()
        urls.append((loc, lastmod, rel_path))

    # Build XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for loc, lastmod, rel_path in urls:
        # Determine priority based on location
        if str(rel_path) == "index.html":
            priority = "1.0"
        elif str(rel_path).startswith("lessons") or str(rel_path).startswith("examples"):
            priority = "0.8"
        elif str(rel_path) in ["search.html", "themes.html", "quick-start.html", "contact.html", "about.html"]:
            priority = "0.7"
        else:
            # Module index or file pages
            if str(rel_path).endswith("index.html"):
                priority = "0.6"
            else:
                priority = "0.5"

        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{loc}</loc>")
        xml_lines.append(f"    <lastmod>{lastmod}</lastmod>")
        xml_lines.append("    <changefreq>monthly</changefreq>")
        xml_lines.append(f"    <priority>{priority}</priority>")
        xml_lines.append("  </url>")

    xml_lines.append("</urlset>")

    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))

    print(f"[OK] Sitemap generated with {len(urls)} URLs: {sitemap_path}")

def generate_documentation():
    print("\nGenerating professional documentation...")
    os.makedirs("docs", exist_ok=True)
    project = analyze_project()
    generate_theme_files()
    generate_main_page(project)
    search_data = generate_search_data(project)
    generate_search_page(project, search_data)
    generate_quick_start()
    generate_contact_page()
    generate_about_page(project)
    generate_examples_hub()
    generate_lessons()
    # Generate themes preview page
    themes = load_all_themes()
    generate_themes_preview_page(themes)
    
    generate_sitemap()
    
    for module_name, module_info in project['modules'].items():
        print(f"   Processing module: {module_name}...")
        module_docs_path = Path(f"docs/{module_name}")
        module_docs_path.mkdir(exist_ok=True)
        generate_module_index(module_name, module_info)
        shutil.copy("docs/theme.js", module_docs_path / "theme.js")
        for file_info in module_info['files']:
            generate_file_page(module_name, file_info, module_docs_path)
            
    print(f"\n[DONE] Files generated in: {os.path.abspath('docs')}")

if __name__ == "__main__":
    print("ENHANCED DOCUMENTATION GENERATOR - LUNAENGINE")
    print("==============================================")
    generate_documentation()