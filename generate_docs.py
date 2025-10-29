#!/usr/bin/env python3
"""
DEFINITIVE DOCUMENTATION GENERATOR - LUNAENGINE
Complete code analysis + professional documentation (English)
"""

import os
import ast
import shutil
import stat
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

def analyze_project():
    """Analyzes the entire LunaEngine project"""
    
    print("🔍 Analyzing project structure...")
    
    project = {
        'modules': {},
        'total_files': 0,
        'total_classes': 0,
        'total_functions': 0
    }
    
    lunaengine_path = "lunaengine"
    if not os.path.exists(lunaengine_path):
        print("❌ lunaengine folder not found")
        return project
    
    # Expected modules
    expected_modules = ["core", "ui", "graphics", "utils", "backend", "tools"]
    
    for module in expected_modules:
        module_path = os.path.join(lunaengine_path, module)
        if os.path.exists(module_path):
            module_info = analyze_module(module_path, module)
            project['modules'][module] = module_info
            project['total_files'] += len(module_info['files'])
            project['total_classes'] += len(module_info['classes'])
            project['total_functions'] += len(module_info['functions'])
            print(f"   ✅ {module}: {len(module_info['files'])} files, {len(module_info['classes'])} classes")
        else:
            print(f"   ⚠️  {module}: not found")
    
    return project

def analyze_module(module_path, module_name):
    """Analyzes a specific module"""
    
    module_info = {
        'name': module_name,
        'description': get_module_description(module_name),
        'files': [],
        'classes': [],
        'functions': []
    }
    
    for file in os.listdir(module_path):
        if file.endswith('.py') and file != '__init__.py':
            file_path = os.path.join(module_path, file)
            file_info = analyze_python_file(file_path)
            
            module_info['files'].append({
                'name': file,
                'classes': file_info['classes'],
                'functions': file_info['functions'],
                'docstring': file_info['docstring']
            })
            
            module_info['classes'].extend(file_info['classes'])
            module_info['functions'].extend(file_info['functions'])
    
    return module_info

def analyze_python_file(file_path):
    """Analyzes a Python file in detail"""
    
    file_info = {
        'classes': [],
        'functions': [],
        'docstring': ''
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST analysis for detailed information
        try:
            tree = ast.parse(content)
            
            # Module docstring
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
                file_info['docstring'] = tree.body[0].value.s.strip()
            
            # Extract classes and functions
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_info = extract_class_info(node)
                    file_info['classes'].append(class_info)
                    
                elif isinstance(node, ast.FunctionDef):
                    function_info = extract_function_info(node)
                    file_info['functions'].append(function_info)
                    
        except SyntaxError:
            # Fallback to basic analysis
            extract_basic_info(content, file_info)
            
    except Exception as e:
        print(f"      ⚠️  Error analyzing {os.path.basename(file_path)}: {e}")
        extract_basic_info(content, file_info)
    
    return file_info

def extract_class_info(class_node):
    """Extracts detailed information from a class"""
    
    class_info = {
        'name': class_node.name,
        'docstring': ast.get_docstring(class_node) or 'No documentation',
        'methods': [],
        'bases': [ast.unparse(base) for base in class_node.bases]
    }
    
    # Class methods
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef):
            method_info = {
                'name': item.name,
                'docstring': ast.get_docstring(item) or 'No documentation',
                'args': extract_arguments(item.args)
            }
            class_info['methods'].append(method_info)
    
    return class_info

def extract_function_info(function_node):
    """Extracts information from a function"""
    
    return {
        'name': function_node.name,
        'docstring': ast.get_docstring(function_node) or 'No documentation',
        'args': extract_arguments(function_node.args)
    }

def extract_arguments(args_node):
    """Extracts function/method arguments"""
    
    arguments = []
    
    # Positional arguments
    for arg in args_node.args:
        arguments.append(arg.arg)
    
    # *args
    if args_node.vararg:
        arguments.append(f"*{args_node.vararg.arg}")
    
    # **kwargs
    if args_node.kwarg:
        arguments.append(f"**{args_node.kwarg.arg}")
    
    return arguments

def extract_basic_info(content, file_info):
    """Extracts basic information using regex (fallback)"""
    
    import re
    
    # Classes
    class_pattern = r'^class\s+(\w+)'
    classes = re.findall(class_pattern, content, re.MULTILINE)
    for cls in classes:
        file_info['classes'].append({
            'name': cls,
            'docstring': 'No documentation',
            'methods': [],
            'bases': []
        })
    
    # Functions
    func_pattern = r'^def\s+(\w+)'
    functions = re.findall(func_pattern, content, re.MULTILINE)
    for func in functions:
        file_info['functions'].append({
            'name': func,
            'docstring': 'No documentation',
            'args': []
        })

def get_module_description(module_name):
    """Returns module description"""
    
    descriptions = {
        "core": "Core engine systems - Engine, Window, Renderer",
        "ui": "User interface components - Buttons, Layouts, Themes", 
        "graphics": "Graphics and rendering - Sprites, Lighting, Particles",
        "utils": "Utility functions - Performance, Math, Threading",
        "backend": "Renderer backends - OpenGL, Pygame",
        "tools": "Development tools - Documentation, Analysis"
    }
    
    return descriptions.get(module_name, f"{module_name} module")

# ========== DOCUMENTATION GENERATOR ==========

def generate_documentation():
    """Generates complete documentation"""
    
    print("\n🚀 Generating professional documentation...")
    
    # Clean previous docs
    safe_remove_folder("docs")
    os.makedirs("docs", exist_ok=True)
    
    # Analyze project
    project = analyze_project()
    
    # Generate theme files
    generate_theme_files()
    
    # Generate pages
    generate_main_page(project)
    generate_module_pages(project)
    generate_quick_start()
    
    print(f"\n🎉 DOCUMENTATION GENERATED SUCCESSFULLY!")
    print(f"📊 Project statistics:")
    print(f"   • Modules: {len(project['modules'])}")
    print(f"   • Files: {project['total_files']}")
    print(f"   • Classes: {project['total_classes']}")
    print(f"   • Functions: {project['total_functions']}")
    print(f"📁 Folder: {os.path.abspath('docs')}")

def generate_main_page(project):
    """Generates main page"""
    
    print("📄 Creating main page...")
    
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
                    <input type="text" id="moduleSearch" class="form-control" placeholder="Search modules...">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
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
                        <div class="d-flex justify-content-center gap-3">
                            <small class="text-white-50">{project['total_files']} files</small>
                            <small class="text-white-50">{project['total_classes']} classes</small>
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
                                <a href="quick-start.html" class="btn btn-light btn-sm">
                                    <i class="bi bi-play-circle me-1"></i>Quick Guide
                                </a>
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
    
    # Icons and colors for modules
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
            <div class="col-lg-4 col-md-6">
                <div class="module-card h-100">
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
    
    html += """
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

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="theme.js"></script>
</body>
</html>"""
    
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_module_pages(project):
    """Generates pages for each module"""
    
    print("📚 Generating module pages...")
    
    for module_name, module_info in project['modules'].items():
        print(f"   📦 {module_name}...")
        generate_single_module_page(module_name, module_info)

def generate_single_module_page(module_name, module_info):
    """Generates page for a specific module"""
    
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
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="../index.html">
                <i class="bi bi-moon-stars-fill me-2"></i>
                LunaEngine
            </a>
            <div class="d-flex align-items-center">
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
        
        if file_info['docstring']:
            html += f"""
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                {file_info['docstring']}
                            </div>
            """
        
        # Classes
        if file_info['classes']:
            html += '<h6>Classes:</h6>'
            for cls in file_info['classes']:
                html += f"""
                            <div class="class-item mb-3 p-3 border rounded">
                                <h6 class="text-success mb-2">
                                    <i class="bi bi-box me-2"></i>
                                    {cls['name']}
                                </h6>
                """
                
                if cls['docstring'] and cls['docstring'] != 'No documentation':
                    html += f'<p class="text-muted mb-2">{cls["docstring"]}</p>'
                
                if cls['bases']:
                    html += f'<small class="text-muted">Inherits from: {", ".join(cls["bases"])}</small>'
                
                # Methods
                if cls['methods']:
                    html += '<div class="mt-2"><strong>Methods:</strong>'
                    for method in cls['methods']:
                        args_str = ', '.join(method['args']) if method['args'] else ''
                        html += f"""
                                <div class="method-item ms-3 mt-1">
                                    <code>{method['name']}({args_str})</code>
                        """
                        if method['docstring'] and method['docstring'] != 'No documentation':
                            html += f'<br><small class="text-muted">{method["docstring"]}</small>'
                        html += '</div>'
                    html += '</div>'
                
                html += '</div>'
        
        # Functions
        if file_info['functions']:
            html += '<h6 class="mt-4">Functions:</h6>'
            for func in file_info['functions']:
                args_str = ', '.join(func['args']) if func['args'] else ''
                html += f"""
                        <div class="function-item mb-2 p-2 border rounded">
                            <code>{func['name']}({args_str})</code>
                """
                if func['docstring'] and func['docstring'] != 'No documentation':
                    html += f'<br><small class="text-muted">{func["docstring"]}</small>'
                html += '</div>'
        
        html += """
                        </div>
                    </div>
                </div>
        """
    
    html += """
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
</body>
</html>"""
    
    with open(f"{module_dir}/index.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_quick_start():
    """Generates quick start page"""
    
    print("🚀 Creating quick guide...")
    
    html = """<!DOCTYPE html>
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
            <button class="btn btn-outline-secondary theme-toggle">
                <span class="theme-icon">🌙</span>
            </button>
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
git clone https://github.com/your-username/LunaEngine.git
cd LunaEngine

# Install dependencies
pip install -r requirements.txt

# Run an example
python examples/basic_game.py</code></pre>
                    </div>
                </div>

                <div class="card mb-4">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0"><i class="bi bi-play-circle me-2"></i>First Game</h5>
                    </div>
                    <div class="card-body">
                        <pre><code>from lunaengine.core.engine import LunaEngine
from lunaengine.ui.elements import Button

class MyGame(LunaEngine):
    def __init__(self):
        super().__init__()
        self.button = Button("Click me!", (100, 100), (200, 50))
    
    def update(self):
        # Game logic here
        pass

# Run the game
game = MyGame()
game.initialize("My First Game", 800, 600)
game.run()</code></pre>
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
                        </ol>
                    </div>
                </div>

                <div class="text-center">
                    <a href="index.html" class="btn btn-primary">
                        <i class="bi bi-house me-2"></i>Back to Home
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="theme.js"></script>
</body>
</html>"""
    
    with open("docs/quick-start.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_theme_files():
    """Generates theme files"""
    
    css_content = """/* LunaEngine Documentation */
:root {
    --primary-color: #007bff;
    --bg-color: #ffffff;
    --text-color: #212529;
    --border-color: #dee2e6;
    --card-bg: #ffffff;
    --header-bg: #f8f9fa;
}

[data-theme="dark"] {
    --primary-color: #0d6efd;
    --bg-color: #1a1a1a;
    --text-color: #e9ecef;
    --border-color: #495057;
    --card-bg: #2d3748;
    --header-bg: #343a40;
}

body {
    background-color: var(--bg-color);
    color: var(--text-color);
    transition: all 0.3s ease;
}

.navbar {
    background-color: var(--header-bg) !important;
    border-bottom: 1px solid var(--border-color);
}

.theme-toggle {
    cursor: pointer;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

.theme-toggle:hover {
    background-color: var(--border-color);
}

.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 5rem 0;
}

.stats-card {
    background: rgba(255,255,255,0.1);
    padding: 2rem;
    border-radius: 1rem;
    backdrop-filter: blur(10px);
}

.module-card {
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    transition: all 0.3s ease;
    background-color: var(--card-bg);
}

.module-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}

.module-stats {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 1rem;
}

.file-card {
    transition: all 0.3s ease;
}

.file-card:hover {
    transform: translateX(5px);
}

.class-item, .function-item {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color) !important;
}

.method-item {
    border-left: 3px solid var(--success);
    padding-left: 1rem;
}

pre code {
    border-radius: 0.5rem;
    padding: 1rem !important;
    background: #f8f9fa !important;
}

[data-theme="dark"] pre code {
    background: #2d3748 !important;
    color: #e9ecef !important;
}
"""
    
    js_content = """// Theme management
$(document).ready(function() {
    const savedTheme = localStorage.getItem('lunaengine-theme') || 'light';
    setTheme(savedTheme);
    
    $('.theme-toggle').click(function() {
        const currentTheme = $('body').attr('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        localStorage.setItem('lunaengine-theme', newTheme);
    });
    
    $('#moduleSearch').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.module-card').each(function() {
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(searchTerm));
        });
    });
});

function setTheme(theme) {
    $('body').attr('data-theme', theme);
    $('.theme-icon').text(theme === 'dark' ? '☀️' : '🌙');
}
"""
    
    with open("docs/theme.css", "w", encoding="utf-8") as f:
        f.write(css_content)
    
    with open("docs/theme.js", "w", encoding="utf-8") as f:
        f.write(js_content)

def main():
    print("=" * 60)
    print("🚀 DEFINITIVE DOCUMENTATION GENERATOR - LUNAENGINE")
    print("=" * 60)
    
    generate_documentation()
    
    print(f"\n🌐 To view documentation:")
    print(f"   cd docs && python -m http.server 8000")
    print(f"   Open: http://localhost:8000")

if __name__ == "__main__":
    main()