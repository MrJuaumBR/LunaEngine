"""
DEFINITIVE DOCUMENTATION GENERATOR - LUNAENGINE
"""

import os, ast, shutil, stat, html, re, json
from pathlib import Path
from datetime import datetime

# ========== CONFIGURATION ==========

def remove_readonly(func, path, excinfo):
    """Handle read-only files during deletion."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_remove_folder(folder_path):
    """Safely remove a folder and its contents."""
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path, onerror=remove_readonly)
            return True
        except Exception:
            return False
    return True

def format_docstring(docstring):
    """Format python docstrings into HTML-safe text."""
    if not docstring or docstring == 'No documentation':
        return 'No documentation'
    docstring = html.escape(docstring)
    docstring = docstring.replace('\n', '<br>')
    docstring = docstring.replace('  ', ' &nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
    return docstring

def extract_theme_colors(file_path):
    """Extract hex colors from themes.py for visual preview."""
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

def analyze_project():
    """Scan the project structure and extract metadata."""
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
    
    expected_modules = ["core", "ui", "graphics", "utils", "backend", "misc", "tools"]
    
    for module in expected_modules:
        module_path = os.path.join(lunaengine_path, module)
        if os.path.exists(module_path):
            module_info = analyze_module(module_path, module)
            project['modules'][module] = module_info
            project['total_files'] += len(module_info['files'])
            project['total_classes'] += len(module_info['classes'])
            project['total_functions'] += len(module_info['functions'])
            project['total_methods'] += module_info['total_methods']
            print(f"   [OK] {module}: {len(module_info['files'])} files found")
            
    return project

def analyze_module(module_path, module_name):
    """Analyze all python files within a specific module."""
    module_info = {
        'name': module_name,
        'description': get_module_description(module_name),
        'files': [],
        'classes': [],
        'functions': [],
        'total_methods': 0
    }
    
    for file in os.listdir(module_path):
        if file.endswith('.py') and file != '__init__.py':
            file_path = os.path.join(module_path, file)
            file_info = analyze_python_file(file_path)
            
            if file == 'themes.py':
                file_info['theme_colors'] = extract_theme_colors(file_path)
            
            file_data = {
                'name': file,
                'base_name': file.replace('.py', ''),
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
    """Parse a single python file using AST."""
    file_info = {'classes': [], 'functions': [], 'docstring': '', 'total_methods': 0}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            
            # Extract module docstring
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
    """Extract class metadata, methods, and attributes."""
    return {
        'name': class_node.name,
        'docstring': format_docstring(ast.get_docstring(class_node)),
        'methods': [extract_function_info(n, True) for n in class_node.body if isinstance(n, ast.FunctionDef)],
        'bases': [ast.unparse(base) for base in class_node.bases],
        'attributes': extract_class_attributes(class_node)
    }
    
def extract_function_info(node, is_method=False):
    """Extract function/method signature and docstrings with parameter types."""
    # Extract arguments with their types
    args = []
    for arg in node.args.args:
        arg_name = arg.arg
        arg_type = ast.unparse(arg.annotation) if arg.annotation else 'Any'
        args.append({'name': arg_name, 'type': arg_type})
    
    # Handle *args
    if node.args.vararg:
        args.append({'name': f"*{node.args.vararg.arg}", 'type': 'tuple'})
    
    # Handle **kwargs
    if node.args.kwarg:
        args.append({'name': f"**{node.args.kwarg.arg}", 'type': 'dict'})
    
    # Handle default values
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
    """Extract class attributes with their types and default values."""
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

def get_module_description(module_name):
    """Descriptions for the main module categories."""
    descriptions = {
        "core": "Core framework systems - Engine/LunaEngine, Window, Renderer",
        "ui": "User interface components - Buttons, Layouts, Themes", 
        "graphics": "Graphics and rendering - Sprites, Lighting, Particles",
        "utils": "Utility functions - Performance, Math, Threading",
        "backend": "Renderer backends - OpenGL, Pygame",
        "misc": "Miscellaneous functions - Bones, Icons",
        "tools": "Development tools - Documentation, Analysis"
    }
    return descriptions.get(module_name, f"{module_name} module")

def get_code_statistics():
    """Reads and returns the raw CODE_STATISTICS.md content with basic HTML escaping"""
    stats_path = "lunaengine/CODE_STATISTICS.md"
    if os.path.exists(stats_path):
        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic HTML escaping to prevent issues
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return content
        except Exception as e:
            print(f"Error reading CODE_STATISTICS.md: {e}")
            return "Statistics not available"
    return "Statistics file not found"

def get_about_md():
    """Reads and returns the raw about.md content with basic HTML escaping"""
    file_path = './about.md'
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic HTML escaping to prevent issues
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return content
        except Exception as e:
            print(f"Error reading about.md: {e}")
            return "About content not available"
    return "About file not found"

def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return '#ffffff' if brightness < 128 else '#000000'

# ========== DOCUMENTATION GENERATOR ==========

def get_navbar_html(path_prefix="./", active_module=None):
    """Standardized navbar for all pages."""
    return f"""
    <nav class="navbar navbar-expand-lg navbar-light sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="{path_prefix}index.html" id="navbar-logo-link">
                <i class="bi bi-moon-stars-fill me-2"></i>
                LunaEngine
            </a>
            <div class="d-flex align-items-center">
                <div class="input-group me-3">
                    <input type="text" id="moduleSearch" class="form-control" placeholder="Search functions, classes, methods...">
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
    return """
    <script>
    // Universal search handler
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('moduleSearch');
        const searchIcon = document.querySelector('.input-group-text');
        
        if (searchInput && searchIcon) {
            const performSearch = () => {
                const searchTerm = searchInput.value.trim();
                if (searchTerm) {
                    const currentPath = window.location.pathname;
                    let searchPath = 'search.html';
                    
                    // Adjust path based on current location
                    if (currentPath.split('/').filter(Boolean).length > 2) {
                        searchPath = '../search.html';
                    }
                    
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
    
def get_footer_html():
    """Standardized footer for all pages."""
    return f"""
    <!-- Footer -->
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
    <script src="theme.js"></script>
    {get_search_script()}
    """

def get_breadcrumbs(links):
    """Generate standardized breadcrumbs."""
    breadcrumb_html = '<nav aria-label="breadcrumb"><ol class="breadcrumb">'
    for text, url in links:
        if url:
            breadcrumb_html += f'<li class="breadcrumb-item"><a href="{url}">{text}</a></li>'
        else:
            breadcrumb_html += f'<li class="breadcrumb-item active">{text}</li>'
    breadcrumb_html += '</ol></nav>'
    return breadcrumb_html

def generate_documentation():
    """Main entry point for HTML generation."""
    print("\nGenerating professional documentation...")
    os.makedirs("docs", exist_ok=True)
    
    project = analyze_project()
    
    # Generate theme files
    generate_theme_files()
    
    # Generate main pages
    generate_main_page(project)
    search_data = generate_search_data(project)
    generate_search_page(project, search_data)
    generate_quick_start()
    generate_contact_page()
    generate_about_page(project)
    generate_examples_hub()
    
    # Process modules and their internal files
    for module_name, module_info in project['modules'].items():
        print(f"   Processing module: {module_name}...")
        os.makedirs(f"docs/{module_name}", exist_ok=True)
        generate_module_index(module_name, module_info)
        
        # Copy docs/theme.js to docs/{module_name}/theme.js
        shutil.copy("docs/theme.js", f"docs/{module_name}/theme.js")
        
        for file_info in module_info['files']:
            generate_file_page(module_name, file_info)
    
    print(f"\n[DONE] Files generated in: {os.path.abspath('docs')}")

def generate_main_page(project):
    """Generate main index page with standardized design."""
    print("Creating main page...")
    
    stats_content = get_code_statistics()
    
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LunaEngine - Documentation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html()}

    <!-- Hero Section -->
    <section class="hero-section">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-8">
                    <h1 class="display-4 fw-bold text-white mb-3">
                        <i class="bi bi-moon-stars-fill me-3"></i>
                        LunaEngine
                    </h1>
                    <p class="lead text-white mb-4">
                        A powerful and intuitive 2D game framework for Python
                    </p>
                    <div class="d-flex flex-wrap gap-2">
                        <span class="badge bg-light text-dark fs-6 p-2">
                            <i class="bi bi-lightning me-1"></i>High Performance
                        </span>
                        <span class="badge bg-light text-dark fs-6 p-2">
                            <i class="bi bi-palette me-1"></i>Modern UI
                        </span>
                        <span class="badge bg-light text-dark fs-6 p-2">
                            <i class="bi bi-code-slash me-1"></i>Pure Python
                        </span>
                    </div>
                </div>
                <div class="col-lg-4 text-center">
                    <div class="stats-card">
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

    <!-- Quick Navigation -->
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
                                <a href="quick-start.html" class="btn btn-light btn-sm me-2">
                                    <i class="bi bi-play-circle me-1"></i>Quick Guide
                                </a>
                                <a href="contact.html" class="btn btn-outline-light btn-sm me-2">
                                    <i class="bi bi-people me-1"></i>Community
                                </a>
                                <a href="about.html" class="btn btn-outline-light btn-sm me-2">
                                    <i class="bi bi-info-circle me-1"></i>About
                                </a>
                                <a href="examples/" class="btn btn-outline-light btn-sm me-2">
                                    <i class="bi bi-code-slash me-1"></i>Examples
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Code Statistics Section -->
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <div class="card shadow-sm">
                    <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="bi bi-graph-up me-2"></i>Code Statistics</h5>
                        <button class="btn btn-sm btn-light" type="button" data-bs-toggle="collapse" data-bs-target="#codeStatsCollapse" aria-expanded="false" aria-controls="codeStatsCollapse">
                            <i class="bi bi-chevron-down"></i>
                        </button>
                    </div>
                    <div class="collapse show" id="codeStatsCollapse">
                        <div class="card-body">
                            <div class="code-stats-content markdown-content">
                                {stats_content}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modules Grid -->
    <div class="container mt-5">
        <h2 class="mb-4">LunaEngine Modules</h2>
        <div class="row g-4">
"""
    
    module_styles = {
        "core": {"icon": "bi-cpu", "color": "primary", "name": "Core Systems"},
        "ui": {"icon": "bi-ui-radios", "color": "success", "name": "User Interface"},
        "graphics": {"icon": "bi-brightness-high", "color": "warning", "name": "Graphics & Rendering"},
        "utils": {"icon": "bi-tools", "color": "info", "name": "Utilities"},
        "backend": {"icon": "bi-hdd-stack", "color": "secondary", "name": "Renderer Backends"},
        "misc": {"icon": "bi-backpack", "color": "dark", "name": "Miscellaneous"},
        "tools": {"icon": "bi-wrench", "color": "danger", "name": "Development Tools"}
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
                            <span class="badge bg-light text-dark">
                                <i class="bi bi-file-text me-1"></i>{len(module_info['files'])} files
                            </span>
                            <span class="badge bg-light text-dark">
                                <i class="bi bi-box me-1"></i>{len(module_info['classes'])} classes
                            </span>
                            <span class="badge bg-light text-dark">
                                <i class="bi bi-gear me-1"></i>{len(module_info['functions'])} functions
                            </span>
                            <span class="badge bg-light text-dark">
                                <i class="bi bi-hammer me-1"></i>{module_info['total_methods']} methods
                            </span>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <a href="{module_name}/index.html" class="btn btn-{style['color']} w-100">
                            <i class="bi bi-book me-2"></i>View Documentation
                        </a>
                    </div>
                </div>
            </div>
"""
    
    html += f"""
        </div>
    </div>

    {get_footer_html()}
</body>
</html>"""
    
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_file_page(module_name, file_info):
    """Create a detailed documentation page for a single .py file with parameter types."""
    path_prefix = "../"
    
    # Format arguments with types
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
        
        # Class attributes
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
            ("Home", f"{path_prefix}index.html"),
            (module_name.title(), "index.html"),
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
            <a href="index.html" class="btn btn-outline-primary">
                <i class="bi bi-arrow-left me-2"></i>Back to {module_name.title()} Module
            </a>
        </div>
    </div>

    {get_footer_html()}
</body>
</html>"""

    with open(f"docs/{module_name}/{file_info['base_name']}.html", "w", encoding="utf-8") as f:
        f.write(html_page)

def generate_module_index(module_name, module_info):
    """Create an index.html for a specific module folder."""
    file_list_html = ""
    for file in module_info['files']:
        file_list_html += f"""
        <div class="col-md-4 mb-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <h5 class="card-title"><i class="bi bi-file-earmark-code me-2"></i>{file['name']}</h5>
                    <p class="card-text small text-muted">Contains {len(file['classes'])} classes and {len(file['functions'])} functions.</p>
                    <a href="{file['base_name']}.html" class="btn btn-sm btn-outline-primary">View Documentation</a>
                </div>
            </div>
        </div>"""

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
        <div class="row mt-4">{file_list_html}</div>
        <div class="mt-5 mb-5 text-center">
            <a href="../index.html" class="btn btn-outline-primary">
                <i class="bi bi-arrow-left me-2"></i>Back to Home
            </a>
        </div>
    </div>
    {get_footer_html()}
</body>
</html>"""
    
    with open(f"docs/{module_name}/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_quick_start():
    """Generate quick start guide."""
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

        <div class="card mb-4 shadow-sm">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0"><i class="bi bi-play-circle me-2"></i>Snake Game Example</h5>
            </div>
            <div class="card-body">
                <p class="text-muted mb-3">
                    <i class="bi bi-info-circle me-1"></i>
                    This is the actual code from <code>examples/snake_demo.py</code>
                </p>
                <pre><code>{snake_code}</code></pre>
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
</body>
</html>"""
    
    with open("docs/quick-start.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_examples_hub():
    """Generate examples hub page and individual example pages."""
    print("Generating examples hub...")
    
    examples_dir = "examples"
    docs_examples_dir = "docs/examples"
    os.makedirs(docs_examples_dir, exist_ok=True)
    
    # Scan examples directory
    examples = []
    if os.path.exists(examples_dir):
        for file in os.listdir(examples_dir):
            if file.endswith('.py'):
                example_path = os.path.join(examples_dir, file)
                try:
                    with open(example_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract docstring if present
                        docstring_match = re.search(r'\"\"\"(.*?)\"\"\"', content, re.DOTALL)
                        description = docstring_match.group(1).strip() if docstring_match else "No description provided"
                        description = description.split('\n')[0] if '\n' in description else description
                    
                    examples.append({
                        'name': file,
                        'title': file.replace('.py', '').replace('_', ' ').title(),
                        'description': description[:150] + "..." if len(description) > 150 else description,
                        'path': example_path,
                        'content': content
                    })
                    print(f"   [OK] Found example: {file}")
                except Exception as e:
                    print(f"   [WARNING] Error reading example {file}: {e}")
    else:
        print(f"   [WARNING] Examples directory not found: {examples_dir}")
    
    # Generate examples hub page
    examples_html = ""
    for example in examples:
        examples_html += f"""
        <div class="col-md-4 mb-4">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <h5 class="card-title"><i class="bi bi-code-slash me-2"></i>{example['title']}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">{example['name']}</h6>
                    <p class="card-text">{example['description']}</p>
                </div>
                <div class="card-footer bg-transparent">
                    <a href="{example['name'].replace('.py', '.html')}" class="btn btn-outline-primary btn-sm">
                        <i class="bi bi-eye me-1"></i>View Example
                    </a>
                    <a href="{example['name'].replace('.py', '.py')}" download class="btn btn-outline-secondary btn-sm">
                        <i class="bi bi-download me-1"></i>Download
                    </a>
                </div>
            </div>
        </div>"""
    
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
        <p class="lead mb-4">Explore practical examples of LunaEngine in action. Click on any example to view the source code and description.</p>
        
        <div class="row">
            {examples_html if examples else '<div class="col-12"><div class="alert alert-info">No examples found in the examples/ directory.</div></div>'}
        </div>
        
        <div class="mt-4 text-center">
            <a href="../index.html" class="btn btn-primary">
                <i class="bi bi-arrow-left me-2"></i>Back to Home
            </a>
        </div>
    </div>
    {get_footer_html()}
</body>
</html>"""
    
    with open(f"{docs_examples_dir}/index.html", "w", encoding="utf-8") as f:
        f.write(hub_html)
    
    # Generate individual example pages
    for example in examples:
        print(f"   Creating page for: {example['name']}")
        example_content = html.escape(example['content'])
        
        example_html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{example['title']} - LunaEngine Examples</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="../theme.css" rel="stylesheet">
</head>
<body>
    {get_navbar_html("../")}
    <div class="container mt-5">
        {get_breadcrumbs([
            ("Home", "../index.html"),
            ("Examples Hub", "index.html"),
            (example['title'], None)
        ])}
        
        <div class="row">
            <div class="col-lg-8">
                <h1 class="mb-3"><i class="bi bi-code-slash me-2"></i>{example['title']}</h1>
                <div class="card mb-4 shadow-sm">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="bi bi-file-earmark-code me-2"></i>{example['name']}</h5>
                    </div>
                    <div class="card-body">
                        <pre><code class="language-python">{example_content}</code></pre>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card shadow-sm sticky-top" style="top: 20px;">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0"><i class="bi bi-info-circle me-2"></i>About This Example</h5>
                    </div>
                    <div class="card-body">
                        <p>{example['description']}</p>
                        <hr>
                        <div class="d-grid gap-2">
                            <a href="{example['name']}" download class="btn btn-outline-primary">
                                <i class="bi bi-download me-2"></i>Download Python File
                            </a>
                            <a href="index.html" class="btn btn-outline-secondary">
                                <i class="bi bi-arrow-left me-2"></i>Back to Examples Hub
                            </a>
                            <a href="../quick-start.html" class="btn btn-outline-success">
                                <i class="bi bi-play-circle me-2"></i>Quick Start Guide
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {get_footer_html()}
</body>
</html>"""
        
        with open(f"{docs_examples_dir}/{example['name'].replace('.py', '.html')}", "w", encoding="utf-8") as f:
            f.write(example_html)
        
        # Also copy the actual .py file to docs/examples/
        try:
            shutil.copy2(example['path'], f"{docs_examples_dir}/{example['name']}")
        except Exception as e:
            print(f"   [WARNING] Failed to copy example file {example['name']}: {e}")

def generate_search_data(project):
    """Generate a global search data JSON file."""
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
    
    # Add modules
    for module_name, module_info in project['modules'].items():
        for file_info in module_info['files']:
            file_name = str(file_info['name']).split('.py')[0]
            
            # Classes
            for class_info in file_info['classes']:
                class_id = f"class-{class_info['name'].lower()}"
                search_data["classes"].append({
                    "name": class_info['name'],
                    "module": module_name,
                    "file": file_info['name'],
                    "description": class_info['docstring'],
                    "link": f"{module_name}/{file_name}.html#{class_id}",
                    "methods_count": len(class_info['methods'])
                })
                
                # Methods
                for method_info in class_info['methods']:
                    method_id = f"method-{class_info['name'].lower()}-{method_info['name'].lower()}"
                    search_data["methods"].append({
                        "name": method_info['name'],
                        "class": class_info['name'],
                        "module": module_name,
                        "description": method_info['docstring'],
                        "link": f"{module_name}/{file_name}.html#{method_id}",
                        "is_method": True
                    })
            
            # Functions
            for function_info in file_info['functions']:
                function_id = f"func-{function_info['name'].lower()}"
                search_data["functions"].append({
                    "name": function_info['name'],
                    "module": module_name,
                    "file": file_info['name'],
                    "description": function_info['docstring'],
                    "link": f"{module_name}/{file_name}.html#{function_id}",
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
    
    # Add general pages
    search_data["pages"].extend([
        {
            "name": "Quick Start",
            "description": "Get started quickly with LunaEngine",
            "link": "quick-start.html",
            "type": "guide"
        },
        {
            "name": "Examples Hub",
            "description": "Practical examples of LunaEngine in action",
            "link": "examples/",
            "type": "examples"
        },
        {
            "name": "Community & Contact",
            "description": "Join our community and get help",
            "link": "contact.html",
            "type": "community"
        }
    ])
    
    # Add examples
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
    
    # Write JSON file
    with open("docs/search-data.json", "w", encoding="utf-8") as f:
        json.dump(search_data, f, indent=2)
    
    print(f"[OK] Global search data generated: {len(search_data['modules'])} modules, "
          f"{len(search_data['classes'])} classes, {len(search_data['functions'])} functions, "
          f"{len(search_data['methods'])} methods, {len(search_data['examples'])} examples")
    
    return search_data

def generate_search_page(project, search_data):
    """Generate the search results page."""
    print("Creating search page...")
    
    total_items = (len(search_data['modules']) + len(search_data['classes']) + 
                   len(search_data['functions']) + len(search_data['methods']) + 
                   len(search_data['pages']) + len(search_data.get('examples', [])))
    
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
                    Global search across all LunaEngine documentation: {total_items} items indexed
                </div>
                
                <div class="input-group mb-4">
                    <input type="text" id="globalSearch" class="form-control" placeholder="Search everything in LunaEngine...">
                    <button class="btn btn-primary" type="button" id="searchButton">
                        <i class="bi bi-search"></i> Search
                    </button>
                </div>
                
                <div id="searchResults" class="search-results-container">
                    <!-- Results will be populated by JavaScript -->
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
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    // Search functionality
    document.addEventListener('DOMContentLoaded', function() {{
        const searchInput = document.getElementById('globalSearch');
        const searchButton = document.getElementById('searchButton');
        const searchResults = document.getElementById('searchResults');
        const noResults = document.getElementById('noResults');
        const searchStats = document.getElementById('searchStats');
        const statsText = document.getElementById('statsText');
        
        // Get search term from URL
        const urlParams = new URLSearchParams(window.location.search);
        const searchTerm = urlParams.get('q');
        
        if (searchTerm) {{
            searchInput.value = searchTerm;
            performSearch(searchTerm);
        }}
        
        // Search button click
        if (searchButton) {{
            searchButton.addEventListener('click', function() {{
                const term = searchInput.value.trim();
                if (term) {{
                    window.location.href = `search.html?q=${{encodeURIComponent(term)}}`;
                }}
            }});
        }}
        
        // Enter key in search input
        if (searchInput) {{
            searchInput.addEventListener('keydown', function(e) {{
                if (e.key === 'Enter') {{
                    const term = searchInput.value.trim();
                    if (term) {{
                        window.location.href = `search.html?q=${{encodeURIComponent(term)}}`;
                    }}
                }}
            }});
        }}
        
        function performSearch(term) {{
            fetch('search-data.json')
                .then(response => response.json())
                .then(data => {{
                    const results = searchData(data, term.toLowerCase());
                    displayResults(results, term);
                }})
                .catch(error => {{
                    console.error('Error loading search data:', error);
                    searchResults.innerHTML = '<div class="alert alert-danger">Error loading search data. Please try again later.</div>';
                }});
        }}
        
        function searchData(data, term) {{
            const results = [];
            
            // Search in modules
            data.modules.forEach(module => {{
                if (module.name.toLowerCase().includes(term) || 
                    module.title.toLowerCase().includes(term) || 
                    module.description.toLowerCase().includes(term)) {{
                    results.push({{...module, type: 'module'}});
                }}
            }});
            
            // Search in classes
            data.classes.forEach(cls => {{
                if (cls.name.toLowerCase().includes(term) || 
                    cls.description.toLowerCase().includes(term) ||
                    cls.module.toLowerCase().includes(term)) {{
                    results.push({{...cls, type: 'class'}});
                }}
            }});
            
            // Search in functions
            data.functions.forEach(func => {{
                if (func.name.toLowerCase().includes(term) || 
                    func.description.toLowerCase().includes(term) ||
                    func.module.toLowerCase().includes(term)) {{
                    results.push({{...func, type: 'function'}});
                }}
            }});
            
            // Search in methods
            data.methods.forEach(method => {{
                if (method.name.toLowerCase().includes(term) || 
                    method.description.toLowerCase().includes(term) ||
                    method.class.toLowerCase().includes(term) ||
                    method.module.toLowerCase().includes(term)) {{
                    results.push({{...method, type: 'method'}});
                }}
            }});
            
            // Search in pages
            data.pages.forEach(page => {{
                if (page.name.toLowerCase().includes(term) || 
                    page.description.toLowerCase().includes(term)) {{
                    results.push({{...page, type: 'page'}});
                }}
            }});
            
            // Search in examples
            if (data.examples) {{
                data.examples.forEach(example => {{
                    if (example.name.toLowerCase().includes(term) || 
                        example.file.toLowerCase().includes(term)) {{
                        results.push({{...example, type: 'example'}});
                    }}
                }});
            }}
            
            return results;
        }}
        
        function displayResults(results, term) {{
            if (results.length === 0) {{
                searchResults.style.display = 'none';
                noResults.style.display = 'block';
                searchStats.style.display = 'none';
                return;
            }}
            
            // Sort results by type priority
            const typePriority = {{
                'module': 1,
                'class': 2,
                'method': 3,
                'function': 4,
                'example': 5,
                'page': 6
            }};
            
            results.sort((a, b) => {{
                return typePriority[a.type] - typePriority[b.type] || a.name.localeCompare(b.name);
            }});
            
            let html = '<h5 class="mb-3">Found ' + results.length + ' results for "' + term + '"</h5>';
            
            results.forEach(result => {{
                const typeBadges = {{
                    'module': 'primary',
                    'class': 'success',
                    'method': 'info',
                    'function': 'warning',
                    'example': 'secondary',
                    'page': 'dark'
                }};
                
                const typeLabels = {{
                    'module': 'Module',
                    'class': 'Class',
                    'method': 'Method',
                    'function': 'Function',
                    'example': 'Example',
                    'page': 'Page'
                }};
                
                const badgeColor = typeBadges[result.type] || 'secondary';
                const typeLabel = typeLabels[result.type] || result.type;
                
                let description = result.description || 'No description available';
                if (description.length > 150) {{
                    description = description.substring(0, 150) + '...';
                }}
                
                // Highlight search term in description
                const regex = new RegExp(`(${{term}})`, 'gi');
                description = description.replace(regex, '<mark class="search-highlight">$1</mark>');
                
                html += `
                <div class="result-item p-3 rounded bg-light">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0">
                            <a href="${{result.link}}" class="text-decoration-none">
                                ${{result.name}}
                            </a>
                        </h6>
                        <span class="badge bg-${{badgeColor}} result-type-badge">${{typeLabel}}</span>
                    </div>
                    <p class="text-muted small mb-2">${{description}}</p>
                    <div class="text-muted small">
                        ${{result.type === 'method' ? `<i class="bi bi-box me-1"></i>Class: ${{result.class}} | ` : ''}}
                        ${{result.type === 'class' || result.type === 'function' || result.type === 'method' ? `<i class="bi bi-folder me-1"></i>Module: ${{result.module}} | ` : ''}}
                        ${{result.type === 'class' && result.methods_count ? `<i class="bi bi-hammer me-1"></i>${{result.methods_count}} methods | ` : ''}}
                        <a href="${{result.link}}" class="text-primary">
                            <i class="bi bi-arrow-right me-1"></i>View details
                        </a>
                    </div>
                </div>`;
            }});
            
            searchResults.innerHTML = html;
            searchResults.style.display = 'block';
            noResults.style.display = 'none';
            searchStats.style.display = 'block';
            statsText.textContent = `Found ${{results.length}} results for "${{term}}"`;
        }}
    }});
    </script>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="theme.js"></script>
    {get_search_script()}
</body>
</html>"""
    
    with open("docs/search.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_theme_files():
    """Generate CSS and JS files for standardized design."""
    css_file = "docs/theme.css"
    js_file = "docs/theme.js"
    
    # Enhanced CSS for standardized design
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

/* Navbar */
.navbar {
    background-color: var(--primary-color) !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.navbar-brand {
    font-size: 1.5rem;
    color: white !important;
}

/* Hero Section */
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
}

/* Cards */
.card {
    border: none;
    border-radius: 10px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    margin-bottom: 1.5rem;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
}

.card-header {
    border-radius: 10px 10px 0 0 !important;
    font-weight: 600;
}

.module-card {
    border: 1px solid #e0e0e0;
}

[data-theme="dark"] .module-card {
    border-color: #444;
}

/* Code blocks */
pre {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 1rem;
    border-left: 4px solid var(--primary-color);
}

[data-theme="dark"] pre {
    background-color: #2d3748;
    color: #e2e8f0;
}

code {
    color: var(--primary-color);
    background-color: rgba(67, 97, 238, 0.1);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
}

/* Breadcrumbs */
.breadcrumb {
    background-color: transparent;
    padding: 0.75rem 0;
}

.breadcrumb-item a {
    color: var(--primary-color);
    text-decoration: none;
}

.breadcrumb-item.active {
    color: var(--dark-color);
}

/* Footer */
.footer-section {
    background-color: var(--dark-color);
    color: white;
    padding: 3rem 0;
    margin-top: 4rem;
}

/* Search results */
.search-results-container .result-item {
    border-left: 4px solid var(--primary-color);
    transition: all 0.3s ease;
}

.search-results-container .result-item:hover {
    background-color: rgba(67, 97, 238, 0.05);
    transform: translateX(5px);
}

/* Examples hub */
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

/* Responsive */
@media (max-width: 768px) {
    .hero-section {
        padding: 2rem 0;
    }
    
    .stats-card {
        margin-top: 2rem;
    }
    
    .color-grid {
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.card, .module-card, .result-item {
    animation: fadeIn 0.5s ease-out;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
    background: var(--primary-color);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--secondary-color);
}"""
        
        with open(css_file, "w", encoding="utf-8") as f:
            f.write(css_content)
    
    # Enhanced JS for theme toggle
    if not os.path.exists(js_file):
        print("Creating enhanced theme.js...")
        js_content = """// LunaEngine Theme Manager
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.querySelector('.theme-toggle');
    const themeIcon = document.querySelector('.theme-icon');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update icon
            if (themeIcon) {
                themeIcon.textContent = newTheme === 'dark' ? '☀️' : '🌙';
            }
            
            // Update button text
            this.innerHTML = `<span class="theme-icon">${newTheme === 'dark' ? '☀️' : '🌙'}</span>`;
        });
        
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        if (themeIcon) {
            themeIcon.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
            themeToggle.innerHTML = `<span class="theme-icon">${savedTheme === 'dark' ? '☀️' : '🌙'}</span>`;
        }
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Add copy button to code blocks
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
    
    // Highlight search terms in URL
    const urlParams = new URLSearchParams(window.location.search);
    const searchTerm = urlParams.get('q');
    if (searchTerm) {
        highlightSearchTerm(searchTerm);
    }
});

function highlightSearchTerm(term) {
    const elements = document.querySelectorAll('.card-body, .docstring-content, p, li');
    const regex = new RegExp(`(${term})`, 'gi');
    
    elements.forEach(element => {
        const html = element.innerHTML;
        const highlighted = html.replace(regex, '<mark class="search-highlight">$1</mark>');
        element.innerHTML = highlighted;
    });
}"""
        
        with open(js_file, "w", encoding="utf-8") as f:
            f.write(js_content)

def generate_about_page(project_info):
    """Generate about page."""
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
        {get_breadcrumbs([
            ("Home", "index.html"),
            ("About", None)
        ])}
        <div class="card shadow-sm">
            <div class="card-header bg-info text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0"><i class="bi bi-info-circle-fill me-2"></i>About LunaEngine</h5>
                <button class="btn btn-sm btn-light" type="button" data-bs-toggle="collapse" data-bs-target="#aboutCollapse" aria-expanded="true" aria-controls="aboutCollapse">
                    <i class="bi bi-chevron-down"></i>
                </button>
            </div>
            <div class="collapse show" id="aboutCollapse">
                <div class="card-body">
                    <div class="markdown-content">
                        {about_content}
                    </div>
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
    """Generate contact page."""
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
        {get_breadcrumbs([
            ("Home", "index.html"),
            ("Community & Contact", None)
        ])}
        
        <h1 class="text-center mb-4">Community & Contact</h1>
        
        <div class="row g-4">
            <div class="col-md-6">
                <div class="card h-100 text-center shadow-sm">
                    <div class="card-body">
                        <i class="bi bi-github fs-1 text-primary mb-3"></i>
                        <h5>GitHub Repository</h5>
                        <p class="text-muted">Source code, issues, and contributions</p>
                        <a href="https://github.com/MrJuaumBR/LunaEngine" class="btn btn-outline-primary" target="_blank">
                            Visit GitHub
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card h-100 text-center shadow-sm">
                    <div class="card-body">
                        <i class="bi bi-discord fs-1 text-info mb-3"></i>
                        <h5>Discord Community</h5>
                        <p class="text-muted">Join our community for help and discussions</p>
                        <a href="https://discord.gg/fb84sHDX7R" class="btn btn-outline-info" target="_blank">
                            Join Discord
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card h-100 text-center shadow-sm">
                    <div class="card-body">
                        <i class="bi bi-youtube fs-1 text-danger mb-3"></i>
                        <h5>YouTube Channel</h5>
                        <p class="text-muted">Watch tutorials and demos</p>
                        <a href="https://youtube.com/@MrJuaumBR" class="btn btn-outline-danger" target="_blank">
                            Go to Channel
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card h-100 text-center shadow-sm">
                    <div class="card-body">
                        <i class="bi bi-code-slash fs-1 text-success mb-3"></i>
                        <h5>Examples Hub</h5>
                        <p class="text-muted">Browse practical examples</p>
                        <a href="examples/" class="btn btn-outline-success">
                            View Examples
                        </a>
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
    {get_footer_html()}
</body>
</html>"""
    
    with open("docs/contact.html", "w", encoding="utf-8") as f:
        f.write(html)

# ========== MAIN EXECUTION ==========

if __name__ == "__main__":
    print("ENHANCED DOCUMENTATION GENERATOR - LUNAENGINE")
    print("==============================================")
    print("Features:")
    print("  [OK] Parameter types preserved (e.g.: a:int, b:str)")
    print("  [OK] Examples hub with individual pages")
    print("  [OK] Standardized professional design")
    print("  [OK] Enhanced search functionality")
    print("  [OK] Theme switcher with persistence")
    print("  [OK] Copy code buttons")
    print("  [OK] Responsive design")
    print("==============================================")
    
    generate_documentation()