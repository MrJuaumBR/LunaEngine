#!/usr/bin/env python3
"""
DEFINITIVE DOCUMENTATION GENERATOR - LUNAENGINE
Compact version with external CSS/JS files
"""

import os
import ast
import shutil
import stat
import html
import re
from pathlib import Path
from datetime import datetime

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
            
            if not colors_data[theme_class]:
                hex_colors = re.findall(r'\"(#(?:[0-9a-fA-F]{3}){1,2})\"', content)
                for i, color_hex in enumerate(hex_colors[:10]):
                    colors_data[theme_class][f'color_{i+1}'] = color_hex
        
        return colors_data
    except Exception as e:
        print(f"      ⚠️  Error extracting theme colors: {e}")
        return {}

def analyze_project():
    print("🔍 Analyzing project structure...")
    
    project = {
        'modules': {},
        'total_files': 0,
        'total_classes': 0,
        'total_functions': 0,
        'total_methods': 0
    }
    
    lunaengine_path = "lunaengine"
    if not os.path.exists(lunaengine_path):
        print("❌ lunaengine folder not found")
        return project
    
    expected_modules = ["core", "ui", "graphics", "utils", "backend", "tools"]
    
    for module in expected_modules:
        module_path = os.path.join(lunaengine_path, module)
        if os.path.exists(module_path):
            module_info = analyze_module(module_path, module)
            project['modules'][module] = module_info
            project['total_files'] += len(module_info['files'])
            project['total_classes'] += len(module_info['classes'])
            project['total_functions'] += len(module_info['functions'])
            project['total_methods'] += module_info['total_methods']
            print(f"   ✅ {module}: {len(module_info['files'])} files, {len(module_info['classes'])} classes, {len(module_info['functions'])} functions")
        else:
            print(f"   ⚠️  {module}: not found")
    
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
    
    for file in os.listdir(module_path):
        if file.endswith('.py') and file != '__init__.py':
            file_path = os.path.join(module_path, file)
            file_info = analyze_python_file(file_path)
            
            if file == 'themes.py':
                file_info['theme_colors'] = extract_theme_colors(file_path)
            
            module_info['files'].append({
                'name': file,
                'classes': file_info['classes'],
                'functions': file_info['functions'],
                'docstring': file_info['docstring'],
                'theme_colors': file_info.get('theme_colors', {})
            })
            
            module_info['classes'].extend(file_info['classes'])
            module_info['functions'].extend(file_info['functions'])
            module_info['total_methods'] += file_info['total_methods']
    
    return module_info

def analyze_python_file(file_path):
    file_info = {
        'classes': [],
        'functions': [],
        'docstring': '',
        'total_methods': 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            
            # Module docstring
            if tree.body and isinstance(tree.body[0], ast.Expr):
                if hasattr(ast, 'Constant') and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
                    file_info['docstring'] = format_docstring(tree.body[0].value.value.strip())
                elif isinstance(tree.body[0].value, ast.Str):
                    file_info['docstring'] = format_docstring(tree.body[0].value.s.strip())
            
            # Extract classes and functions
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_info = extract_class_info(node)
                    file_info['classes'].append(class_info)
                    file_info['total_methods'] += len(class_info['methods'])
                elif isinstance(node, ast.FunctionDef):
                    function_info = extract_function_info(node)
                    file_info['functions'].append(function_info)
                    
        except SyntaxError as e:
            print(f"      ⚠️  Syntax error in {os.path.basename(file_path)}: {e}")
            extract_basic_info(content, file_info)
            
    except Exception as e:
        print(f"      ⚠️  Error analyzing {os.path.basename(file_path)}: {e}")
    
    return file_info

def extract_class_info(class_node):
    class_info = {
        'name': class_node.name,
        'docstring': format_docstring(ast.get_docstring(class_node)) or 'No documentation',
        'methods': [],
        'bases': [ast.unparse(base) for base in class_node.bases],
        'attributes': extract_class_attributes(class_node)
    }
    
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef):
            method_info = extract_function_info(item, is_method=True)
            class_info['methods'].append(method_info)
    
    return class_info

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

def extract_function_info(function_node, is_method=False):
    full_code = ast.unparse(function_node) if hasattr(ast, 'unparse') else function_node.name
    docstring = ast.get_docstring(function_node) or ''
    
    return {
        'name': function_node.name,
        'docstring': format_docstring(docstring) or 'No documentation',
        'args': extract_arguments(function_node.args),
        'returns': extract_return_annotation(function_node),
        'is_method': is_method,
        'full_code': full_code,  
        'raw_docstring': docstring
    }

def extract_arguments(args_node):
    arguments = []
    
    for arg in args_node.args:
        arguments.append({
            'name': arg.arg,
            'type': ast.unparse(arg.annotation) if arg.annotation else 'Any'
        })
    
    if args_node.vararg:
        arguments.append({
            'name': f"*{args_node.vararg.arg}",
            'type': ast.unparse(args_node.vararg.annotation) if args_node.vararg.annotation else 'Any'
        })
    
    if args_node.kwarg:
        arguments.append({
            'name': f"**{args_node.kwarg.arg}",
            'type': ast.unparse(args_node.kwarg.annotation) if args_node.kwarg.annotation else 'Any'
        })
    
    return arguments

def extract_return_annotation(function_node):
    return ast.unparse(function_node.returns) if function_node.returns else 'None'

def extract_basic_info(content, file_info):
    import re
    class_pattern = r'^class\s+(\w+)'
    classes = re.findall(class_pattern, content, re.MULTILINE)
    for cls in classes:
        file_info['classes'].append({
            'name': cls,
            'docstring': 'No documentation',
            'methods': [],
            'bases': [],
            'attributes': []
        })
    
    func_pattern = r'^def\s+(\w+)'
    functions = re.findall(func_pattern, content, re.MULTILINE)
    for func in functions:
        file_info['functions'].append({
            'name': func,
            'docstring': 'No documentation',
            'args': [],
            'returns': 'None',
            'is_method': False
        })

def get_module_description(module_name):
    descriptions = {
        "core": "Core engine systems - Engine, Window, Renderer",
        "ui": "User interface components - Buttons, Layouts, Themes", 
        "graphics": "Graphics and rendering - Sprites, Lighting, Particles",
        "utils": "Utility functions - Performance, Math, Threading",
        "backend": "Renderer backends - OpenGL, Pygame",
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
            print(f"⚠️  Error reading CODE_STATISTICS.md: {e}")
            return "Statistics not available"
    return "Statistics file not found"

def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return '#ffffff' if brightness < 128 else '#000000'

# ========== DOCUMENTATION GENERATOR ==========

def get_search_script():
    return """
    <script>
    // Universal search handler for GitHub Pages structure
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('moduleSearch');
        const searchIcon = document.querySelector('.input-group-text');
        
        if (searchInput && searchIcon) {
            const performSearch = () => {
                const searchTerm = searchInput.value.trim();
                if (searchTerm) {
                    // GitHub Pages structure: 
                    // - Root: https://mrjuaumbr.github.io/LunaEngine/
                    // - Modules: https://mrjuaumbr.github.io/LunaEngine/core/
                    // - Search: https://mrjuaumbr.github.io/LunaEngine/search.html
                    
                    const currentPath = window.location.pathname;
                    let searchPath = 'search.html';
                    
                    // If we're in a module subdirectory (/LunaEngine/core/)
                    if (currentPath.split('/').filter(Boolean).length > 2) {
                        // We're in a subdirectory like /LunaEngine/core/
                        searchPath = '../search.html';
                    }
                    // If we're in the root (/LunaEngine/)
                    else {
                        // We're in the root, search.html is at same level
                        searchPath = 'search.html';
                    }
                    
                    window.location.href = `${searchPath}?q=${encodeURIComponent(searchTerm)}`;
                }
            };
            
            // Handle Enter key - PREVENT DEFAULT FORM SUBMISSION
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault(); 
                    e.stopPropagation();
                    performSearch();
                    return false;
                }
            });
            
            // Handle click on search icon
            searchIcon.addEventListener('click', performSearch);
            
            // Also prevent form submission if the input is inside a form
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

def generate_documentation():
    print("\n🚀 Generating professional documentation...")
    
    # Create docs folder
    os.makedirs("docs", exist_ok=True)
    
    # Generate theme files (will not overwrite if exist)
    generate_theme_files()
    
    # Analyze project
    project = analyze_project()
    
    # Generate search data
    search_data = generate_search_data(project)
    
    # Generate pages
    generate_main_page(project)
    generate_module_pages(project)
    generate_quick_start()
    generate_contact_page()
    generate_search_page(project, search_data)
    
    print(f"\n🎉 DOCUMENTATION GENERATED SUCCESSFULLY!")
    print(f"📊 Project statistics:")
    print(f"   • Modules: {len(project['modules'])}")
    print(f"   • Files: {project['total_files']}")
    print(f"   • Classes: {project['total_classes']}")
    print(f"   • Functions: {project['total_functions']}")
    print(f"   • Methods: {project['total_methods']}")
    print(f"📁 Folder: {os.path.abspath('docs')}")

def generate_main_page(project):
    print("📄 Creating main page...")
    
    # Get code statistics
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
    <nav class="navbar navbar-expand-lg navbar-light sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="#">
                <i class="bi bi-moon-stars-fill me-2"></i>
                LunaEngine
            </a>
            <div class="d-flex align-items-center">
                <div class="input-group me-3">
                    <input type="text" id="moduleSearch" class="form-control" placeholder="Search functions, classes, methods... (e.g.: render(), .update())">
                    <span class="input-group-text" id="searchIcon"><i class="bi bi-search"></i></span>
                </div>
                <button class="btn btn-outline-secondary theme-toggle">
                    <span class="theme-icon">🌙</span>
                </button>
            </div>
        </div>
    </nav>

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
                        A powerful and intuitive 2D game engine for Python
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
                            <div class="col-md-8">
                                <h6 class="mb-0"><i class="bi bi-rocket me-2"></i>Get started quickly with LunaEngine</h6>
                            </div>
                            <div class="col-md-4 text-end">
                                <a href="quick-start.html" class="btn btn-light btn-sm me-2">
                                    <i class="bi bi-play-circle me-1"></i>Quick Guide
                                </a>
                                <a href="contact.html" class="btn btn-outline-light btn-sm">
                                    <i class="bi bi-people me-1"></i>Community
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
                <div class="card">
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
        "tools": {"icon": "bi-wrench", "color": "danger", "name": "Development Tools"}
    }
    
    for module_name, module_info in project['modules'].items():
        style = module_styles.get(module_name, {"icon": "bi-box", "color": "primary", "name": module_name.title()})
        
        html += f"""
            <div class="col-lg-4 col-md-6 rounded-top-18">
                <div class="module-card h-100">
                    <div class="card-header bg-{style['color']} text-white rounded-top-18">
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
                        <div class="module-stats">
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

    <!-- Footer -->
    <footer class="bg-dark text-white mt-5 py-5">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5><i class="bi bi-moon-stars-fill me-2"></i>LunaEngine</h5>
                    <p class="text-white-50">2D Game Engine for Python</p>
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
</body>
</html>"""
    
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_module_pages(project):
    print("📚 Generating module pages...")
    for module_name, module_info in project['modules'].items():
        print(f"   📦 {module_name}...")
        generate_single_module_page(module_name, module_info)

def generate_single_module_page(module_name, module_info):
    module_dir = f"docs/{module_name}"
    os.makedirs(module_dir, exist_ok=True)
    
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{module_name.title()} - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="../theme.css" rel="stylesheet">
    <style>
    .search-highlight {{
        background-color: #ffeb3b;
        padding: 2px 4px;
        border-radius: 3px;
        animation: highlight-pulse 2s ease-in-out;
    }}
    
    @keyframes highlight-pulse {{
        0% {{ background-color: #ffeb3b; }}
        50% {{ background-color: #ffff72; }}
        100% {{ background-color: #ffeb3b; }}
    }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="../index.html">
                <i class="bi bi-moon-stars-fill me-2"></i>
                LunaEngine
            </a>
            <div class="d-flex align-items-center">
                <div class="input-group me-3">
                    <input type="text" id="moduleSearch" class="form-control" placeholder="Search in {module_name}... (e.g.: def render(), .update())">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                </div>
                <span class="badge bg-primary me-3">{module_name.title()}</span>
                <button class="btn btn-outline-secondary theme-toggle">
                    <span class="theme-icon">🌙</span>
                </button>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Module Header -->
        <div class="row mb-5">
            <div class="col-12">
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb">
                        <li class="breadcrumb-item"><a href="../index.html">Home</a></li>
                        <li class="breadcrumb-item active">{module_name.title()}</li>
                    </ol>
                </nav>
                
                <div class="d-flex align-items-center mb-3">
                    <h1 class="mb-0">{module_name.title()}</h1>
                    <span class="badge bg-info ms-3">Code Analysis</span>
                </div>
                <p class="lead text-muted">{module_info['description']}</p>
            </div>
        </div>

        <!-- Module Files -->
        <div class="row">
            <div class="col-12">
"""
    
    for file_info in module_info['files']:
        html += f"""
                <div class="file-card mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">
                                <i class="bi bi-file-code me-2"></i>
                                {file_info['name']}
                            </h5>
                        </div>
                        <div class="card-body">
        """
        
        if file_info['docstring'] and file_info['docstring'] != 'No documentation':
            html += f"""
                            <div class="alert alert-info docstring-content">
                                <i class="bi bi-info-circle me-2"></i>
                                <div class="docstring-text">{file_info['docstring']}</div>
                            </div>
            """
        
        if file_info['name'] == 'themes.py' and file_info.get('theme_colors'):
            html += generate_theme_colors_section(file_info['theme_colors'])
        
        # Classes
        if file_info['classes']:
            html += '<h6>Classes:</h6>'
            for cls in file_info['classes']:
                class_id = f"class-{cls['name'].lower()}"
                html += f"""
                            <div class="class-item mb-3 p-3 border rounded" id="{class_id}">
                                <h6 class="text-success mb-2">
                                    <i class="bi bi-box me-2"></i>
                                    {cls['name']}
                                </h6>
                """
                
                if cls['docstring'] and cls['docstring'] != 'No documentation':
                    html += f'<div class="docstring-content mb-2"><div class="docstring-text">{cls["docstring"]}</div></div>'
                
                if cls['bases']:
                    html += f'<small class="text-muted">Inherits from: {", ".join(cls["bases"])}</small>'
                
                if cls['attributes']:
                    html += '<div class="mt-3"><strong>Attributes:</strong>'
                    for attr in cls['attributes']:
                        html += f"""
                                <div class="attribute-item ms-3 mt-1">
                                    <code>{attr['name']}: {attr['type']} = {attr['default']}</code>
                                </div>
                        """
                    html += '</div>'
                
                if cls['methods']:
                    html += '<div class="mt-3"><strong>Methods:</strong>'
                    for method in cls['methods']:
                        method_id = f"method-{cls['name'].lower()}-{method['name'].lower()}"
                        args_str = ', '.join([f"{arg['name']}: {arg['type']}" for arg in method['args']])
                        html += f"""
                                <div class="method-item ms-3 mt-2 p-2 border-start border-3 border-success" id="{method_id}">
                                    <code>def {method['name']}({args_str}) -> {method['returns']}</code>
                        """
                        if method['docstring'] and method['docstring'] != 'No documentation':
                            html += f'<div class="docstring-content mt-1"><div class="docstring-text">{method["docstring"]}</div></div>'
                        html += '</div>'
                    html += '</div>'
                
                html += '</div>'
        
        # Functions
        if file_info['functions']:
            html += '<h6 class="mt-4">Functions:</h6>'
            for func in file_info['functions']:
                function_id = f"func-{func['name'].lower()}"
                args_str = ', '.join([f"{arg['name']}: {arg['type']}" for arg in func['args']])
                html += f"""
                        <div class="function-item mb-3 p-3 border rounded" id="{function_id}">
                            <code>def {func['name']}({args_str}) -> {func['returns']}</code>
                """
                if func['docstring'] and func['docstring'] != 'No documentation':
                    html += f'<div class="docstring-content mt-2"><div class="docstring-text">{func["docstring"]}</div></div>'
                html += '</div>'
        
        html += """
                        </div>
                    </div>
                </div>
        """
    
    html += f"""
            </div>
        </div>

        <!-- Navigation -->
        <div class="row mt-4">
            <div class="col-12 text-center">
                <a href="../index.html" class="btn btn-primary">
                    <i class="bi bi-arrow-left me-2"></i>Back to Home
                </a>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="../theme.js"></script>
    {get_search_script()}
</body>
</html>"""
    
    with open(f"{module_dir}/index.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_theme_colors_section(theme_colors):
    if not theme_colors:
        return ""
    
    html = """
                            <div class="theme-colors-section mt-4">
                                <h6><i class="bi bi-palette me-2"></i>Theme Colors Preview</h6>
    """
    
    for theme_name, colors in theme_colors.items():
        html += f"""
                                <div class="theme-preview mb-4">
                                    <h6 class="text-primary">{theme_name}</h6>
                                    <div class="color-grid">
        """
        
        for color_name, color_hex in colors.items():
            text_color = get_contrast_color(color_hex)
            html += f"""
                                        <div class="color-item" style="background-color: {color_hex}; color: {text_color};">
                                            <div class="color-swatch"></div>
                                            <div class="color-info">
                                                <small class="color-name">{color_name}</small>
                                                <small class="color-hex">{color_hex}</small>
                                            </div>
                                        </div>
            """
        
        html += """
                                    </div>
                                </div>
        """
    
    html += """
                            </div>
    """
    
    return html

def generate_quick_start():
    print("🚀 Creating quick guide...")
    
    # Read the snake game example file
    snake_code = ""
    snake_file_path = "examples/snake_demo.py"
    
    try:
        if os.path.exists(snake_file_path):
            with open(snake_file_path, 'r', encoding='utf-8') as f:
                snake_code = f.read()
            print(f"   ✅ Loaded snake game from {snake_file_path}")
        else:
            snake_code = "# Snake game file not found at examples/snake_demo.py"
            print(f"   ⚠️  Snake game file not found: {snake_file_path}")
    except Exception as e:
        snake_code = f"# Error reading snake game: {e}"
        print(f"   ⚠️  Error reading snake game: {e}")
    
    # Escape HTML characters in the code
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
    <nav class="navbar navbar-expand-lg navbar-light sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="index.html">
                <i class="bi bi-moon-stars-fill me-2"></i>
                LunaEngine
            </a>
            <div class="d-flex align-items-center">
                <div class="input-group me-3">
                    <input type="text" id="moduleSearch" class="form-control" placeholder="Search documentation...">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                </div>
                <button class="btn btn-outline-secondary theme-toggle">
                    <span class="theme-icon">🌙</span>
                </button>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row">
            <div class="col-lg-8 mx-auto">
                <h1 class="text-center mb-4">🚀 Quick Start Guide</h1>
                
                <div class="card mb-4">
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

                <div class="card mb-4">
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

                <div class="card mb-4">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0"><i class="bi bi-book me-2"></i>Next Steps</h5>
                    </div>
                    <div class="card-body">
                        <ol>
                            <li>Explore the modules in the documentation</li>
                            <li>Check out examples in the <code>examples/</code> folder</li>
                            <li>Experiment with UI, graphics, and utilities</li>
                            <li>Consult specific module documentation</li>
                            <li>Join our <a href="contact.html">community</a> for help and support</li>
                        </ol>
                    </div>
                </div>

                <div class="text-center">
                    <a href="index.html" class="btn btn-primary me-2">
                        <i class="bi bi-house me-2"></i>Back to Home
                    </a>
                    <a href="contact.html" class="btn btn-outline-primary">
                        <i class="bi bi-people me-2"></i>Join Community
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="theme.js"></script>
    {get_search_script()}
</body>
</html>"""
    
    with open("docs/quick-start.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def generate_search_data(project):
    """Generate a global search data JSON file"""
    print("📊 Generating global search data...")
    
    search_data = {
        "modules": [],
        "classes": [],
        "functions": [],
        "methods": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Add modules
    for module_name, module_info in project['modules'].items():
        search_data["modules"].append({
            "name": module_name,
            "title": module_name.title(),
            "description": module_info['description'],
            "link": f"{module_name}/index.html",
            "files_count": len(module_info['files']),
            "classes_count": len(module_info['classes']),
            "functions_count": len(module_info['functions'])
        })
        
        # Add classes from this module
        for file_info in module_info['files']:
            for class_info in file_info['classes']:
                class_id = f"class-{class_info['name'].lower()}"
                search_data["classes"].append({
                    "name": class_info['name'],
                    "module": module_name,
                    "file": file_info['name'],
                    "description": class_info['docstring'],
                    "link": f"{module_name}/index.html#{class_id}",
                    "methods_count": len(class_info['methods']),
                    "element_id": class_id
                })
                
                # Add methods from this class
                for method_info in class_info['methods']:
                    method_id = f"method-{class_info['name'].lower()}-{method_info['name'].lower()}"
                    search_data["methods"].append({
                        "name": method_info['name'],
                        "class": class_info['name'],
                        "module": module_name,
                        "description": method_info['docstring'],
                        "link": f"{module_name}/index.html#{method_id}",
                        "is_method": True,
                        "element_id": method_id
                    })
            
            # Add standalone functions
            for function_info in file_info['functions']:
                function_id = f"func-{function_info['name'].lower()}"
                search_data["functions"].append({
                    "name": function_info['name'],
                    "module": module_name,
                    "file": file_info['name'],
                    "description": function_info['docstring'],
                    "link": f"{module_name}/index.html#{function_id}",
                    "is_method": False,
                    "element_id": function_id
                })
    
    # Add general pages
    search_data["pages"] = [
        {
            "name": "Quick Start",
            "description": "Get started quickly with LunaEngine",
            "link": "quick-start.html",
            "type": "guide"
        },
        {
            "name": "Community & Contact", 
            "description": "Join our community and get help",
            "link": "contact.html",
            "type": "community"
        }
    ]
    
    # Write JSON file
    import json
    with open("docs/search-data.json", "w", encoding="utf-8") as f:
        json.dump(search_data, f, indent=2)
    
    print(f"✅ Global search data generated: {len(search_data['modules'])} modules, "
          f"{len(search_data['classes'])} classes, {len(search_data['functions'])} functions, "
          f"{len(search_data['methods'])} methods")
    
    return search_data

def generate_search_page(project, search_data):
    print("🔍 Creating search page...")
    
    total_items = (len(search_data['modules']) + len(search_data['classes']) + 
                   len(search_data['functions']) + len(search_data['methods']) + 
                   len(search_data['pages']))
    
    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Results - LunaEngine</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="theme.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="index.html">
                <i class="bi bi-moon-stars-fill me-2"></i>
                LunaEngine
            </a>
            <div class="d-flex align-items-center">
                <div class="input-group me-3">
                    <input type="text" id="globalSearch" class="form-control" placeholder="Search everything in LunaEngine...">
                    <button class="btn btn-primary" type="button" id="searchButton">
                        <i class="bi bi-search"></i>
                    </button>
                </div>
                <button class="btn btn-outline-secondary theme-toggle">
                    <span class="theme-icon">🌙</span>
                </button>
            </div>
        </div>
    </nav>

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
                
                <div id="searchResults" class="search-results-container">
                    <!-- Results will be populated by JavaScript -->
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
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="search.js"></script>
    <script src="theme.js"></script>
</body>
</html>"""
    
    with open("docs/search.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_contact_page():
    print("📞 Creating contact page...")
    
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
    <nav class="navbar navbar-expand-lg navbar-light sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="index.html">
                <i class="bi bi-moon-stars-fill me-2"></i>
                LunaEngine
            </a>
            <div class="d-flex align-items-center">
                <div class="input-group me-3">
                    <input type="text" id="moduleSearch" class="form-control" placeholder="Search documentation...">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                </div>
                <button class="btn btn-outline-secondary theme-toggle">
                    <span class="theme-icon">🌙</span>
                </button>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row">
            <div class="col-lg-8 mx-auto">
                <h1 class="text-center mb-4">👥 Community & Contact</h1>
                
                <div class="row g-4">
                    <div class="col-md-6">
                        <div class="card h-100 text-center">
                            <div class="card-body">
                                <i class="bi bi-github fs-1 text-primary mb-3"></i>
                                <h5>GitHub Repository</h5>
                                <p class="text-muted">Source code, issues, and contributions</p>
                                <a href="https://github.com/MrJuaumBR/LunaEngine" class="btn btn-outline-primary">
                                    Visit GitHub
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card h-100 text-center">
                            <div class="card-body">
                                <i class="bi bi-discord fs-1 text-info mb-3"></i>
                                <h5>Discord Community</h5>
                                <p class="text-muted">Join our community for help and discussions</p>
                                <a href="https://discord.gg/fb84sHDX7R" class="btn btn-outline-info">
                                    Join Discord
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card h-100 text-center">
                            <div class="card-body">
                                <i class="bi bi-youtube fs-1 text-danger mb-3"></i>
                                <h5>YouTube Channel</h5>
                                <p class="text-muted">Watch some of our videos!</p>
                                <a href="https://youtube.com/@MrJuaumBR" class="btn btn-outline-danger">
                                    Go to Channel
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card h-100 text-center">
                            <div class="card-body">
                                <i class="bi bi-file-text fs-1 text-success mb-3"></i>
                                <h5>Documentation</h5>
                                <p class="text-muted">Browse the complete documentation</p>
                                <a href="index.html" class="btn btn-outline-success">
                                    View Docs
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-4">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0"><i class="bi bi-info-circle me-2"></i>Contributing</h5>
                    </div>
                    <div class="card-body">
                        <p>We welcome contributions! Here's how you can help:</p>
                        <ul>
                            <li>Report bugs and issues on GitHub</li>
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
                    <a href="quick-start.html" class="btn btn-outline-primary">
                        <i class="bi bi-play-circle me-2"></i>Quick Start
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="theme.js"></script>
    {get_search_script()}
</body>
</html>"""
    
    with open("docs/contact.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_theme_files():
    """Generate CSS and JS files only if they don't exist"""
    css_file = "docs/theme.css"
    js_file = "docs/theme.js"
    
    if not os.path.exists(css_file):
        print("🎨 Creating theme.css...")
        shutil.copy("theme.css", css_file)
    
    if not os.path.exists(js_file):
        print("⚡ Creating theme.js...")
        shutil.copy("theme.js", js_file)

# ========== MAIN EXECUTION ==========

if __name__ == "__main__":
    print("🎯 DEFINITIVE DOCUMENTATION GENERATOR - LUNAENGINE")
    print("==================================================")
    
    generate_documentation()