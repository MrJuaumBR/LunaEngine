#!/usr/bin/env python3
"""
DEFINITIVE DOCUMENTATION GENERATOR - LUNAENGINE
Complete code analysis + professional documentation (English)
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
    """Formata docstring preservando quebras de linha e indentação"""
    if not docstring or docstring == 'No documentation':
        return 'No documentation'
    
    # Escapa caracteres HTML
    docstring = html.escape(docstring)
    
    # Preserva quebras de linha
    docstring = docstring.replace('\n', '<br>')
    
    # Preserva tabs e múltiplos espaços
    docstring = docstring.replace('  ', ' &nbsp;').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
    
    return docstring

def extract_theme_colors(file_path):
    """Extrai cores dos temas do arquivo themes.py"""
    colors_data = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Procura por classes de tema
        theme_classes = re.findall(r'class\s+(\w+Theme).*?:', content)
        
        for theme_class in theme_classes:
            colors_data[theme_class] = {}
            
            # Extrai cores hexadecimais
            hex_colors = re.findall(r'\"(#(?:[0-9a-fA-F]{3}){1,2})\"', content)
            named_colors = re.findall(r'(\w+)\s*=\s*\"(#(?:[0-9a-fA-F]{3}){1,2})\"', content)
            
            for color_name, color_hex in named_colors:
                colors_data[theme_class][color_name] = color_hex
            
            # Se não encontrou cores nomeadas, usa todas as cores hex encontradas
            if not colors_data[theme_class] and hex_colors:
                for i, color_hex in enumerate(hex_colors[:10]):  # Limita a 10 cores
                    colors_data[theme_class][f'color_{i+1}'] = color_hex
        
        return colors_data
        
    except Exception as e:
        print(f"      ⚠️  Error extracting theme colors: {e}")
        return {}

def analyze_project():
    """Analyzes the entire LunaEngine project"""
    
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
            project['total_methods'] += module_info['total_methods']
            print(f"   ✅ {module}: {len(module_info['files'])} files, {len(module_info['classes'])} classes, {len(module_info['functions'])} functions")
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
        'functions': [],
        'total_methods': 0
    }
    
    for file in os.listdir(module_path):
        if file.endswith('.py') and file != '__init__.py':
            file_path = os.path.join(module_path, file)
            file_info = analyze_python_file(file_path)
            
            # Extrai cores de temas se for o arquivo themes.py
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
    """Analyzes a Python file in detail"""
    
    file_info = {
        'classes': [],
        'functions': [],
        'docstring': '',
        'total_methods': 0
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST analysis for detailed information
        try:
            tree = ast.parse(content)
            
            # Module docstring
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
                file_info['docstring'] = format_docstring(tree.body[0].value.s.strip())
            elif tree.body and hasattr(ast, 'Constant') and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
                # Python 3.8+ usa ast.Constant para strings
                file_info['docstring'] = format_docstring(tree.body[0].value.value.strip())
            
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
        extract_basic_info(content, file_info)
    
    return file_info

def extract_class_info(class_node):
    """Extracts detailed information from a class"""
    
    class_info = {
        'name': class_node.name,
        'docstring': format_docstring(ast.get_docstring(class_node)) or 'No documentation',
        'methods': [],
        'bases': [ast.unparse(base) for base in class_node.bases],
        'attributes': extract_class_attributes(class_node)
    }
    
    # Class methods
    for item in class_node.body:
        if isinstance(item, ast.FunctionDef):
            method_info = extract_function_info(item, is_method=True)
            class_info['methods'].append(method_info)
    
    return class_info

def extract_class_attributes(class_node):
    """Extracts class attributes with type annotations"""
    attributes = []
    
    for item in class_node.body:
        if isinstance(item, ast.AnnAssign):
            # Typed attribute (e.g., name: str = "default")
            attr_name = item.target.id if isinstance(item.target, ast.Name) else 'unknown'
            attr_type = ast.unparse(item.annotation) if item.annotation else 'Any'
            default_value = ast.unparse(item.value) if item.value else 'None'
            attributes.append({
                'name': attr_name,
                'type': attr_type,
                'default': default_value
            })
        elif isinstance(item, ast.Assign):
            # Regular attribute (e.g., name = "default")
            for target in item.targets:
                if isinstance(target, ast.Name):
                    attr_name = target.id
                    default_value = ast.unparse(item.value) if item.value else 'None'
                    attributes.append({
                        'name': attr_name,
                        'type': 'Any',
                        'default': default_value
                    })
    
    return attributes

def extract_function_info(function_node, is_method=False):
    """Extracts information from a function with type annotations"""
    
    function_info = {
        'name': function_node.name,
        'docstring': format_docstring(ast.get_docstring(function_node)) or 'No documentation',
        'args': extract_arguments(function_node.args),
        'returns': extract_return_annotation(function_node),
        'is_method': is_method
    }
    
    return function_info

def extract_arguments(args_node):
    """Extracts function/method arguments with type annotations"""
    
    arguments = []
    
    # Positional arguments with type annotations
    for arg in args_node.args:
        arg_info = {
            'name': arg.arg,
            'type': ast.unparse(arg.annotation) if arg.annotation else 'Any'
        }
        arguments.append(arg_info)
    
    # *args
    if args_node.vararg:
        arg_info = {
            'name': f"*{args_node.vararg.arg}",
            'type': ast.unparse(args_node.vararg.annotation) if args_node.vararg.annotation else 'Any'
        }
        arguments.append(arg_info)
    
    # **kwargs
    if args_node.kwarg:
        arg_info = {
            'name': f"**{args_node.kwarg.arg}",
            'type': ast.unparse(args_node.kwarg.annotation) if args_node.kwarg.annotation else 'Any'
        }
        arguments.append(arg_info)
    
    return arguments

def extract_return_annotation(function_node):
    """Extracts return type annotation"""
    if function_node.returns:
        return ast.unparse(function_node.returns)
    return 'None'

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
            'bases': [],
            'attributes': []
        })
    
    # Functions
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
    generate_contact_page()
    
    print(f"\n🎉 DOCUMENTATION GENERATED SUCCESSFULLY!")
    print(f"📊 Project statistics:")
    print(f"   • Modules: {len(project['modules'])}")
    print(f"   • Files: {project['total_files']}")
    print(f"   • Classes: {project['total_classes']}")
    print(f"   • Functions: {project['total_functions']}")
    print(f"   • Methods: {project['total_methods']}")
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
        
        if file_info['docstring'] and file_info['docstring'] != 'No documentation':
            html += f"""
                            <div class="alert alert-info docstring-content">
                                <i class="bi bi-info-circle me-2"></i>
                                <div class="docstring-text">{file_info['docstring']}</div>
                            </div>
            """
        
        # Se for themes.py, mostra visualização das cores
        if file_info['name'] == 'themes.py' and file_info.get('theme_colors'):
            html += generate_theme_colors_section(file_info['theme_colors'])
        
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
                    html += f'<div class="docstring-content mb-2"><div class="docstring-text">{cls["docstring"]}</div></div>'
                
                if cls['bases']:
                    html += f'<small class="text-muted">Inherits from: {", ".join(cls["bases"])}</small>'
                
                # Class attributes
                if cls['attributes']:
                    html += '<div class="mt-3"><strong>Attributes:</strong>'
                    for attr in cls['attributes']:
                        html += f"""
                                <div class="attribute-item ms-3 mt-1">
                                    <code>{attr['name']}: {attr['type']} = {attr['default']}</code>
                                </div>
                        """
                    html += '</div>'
                
                # Methods
                if cls['methods']:
                    html += '<div class="mt-3"><strong>Methods:</strong>'
                    for method in cls['methods']:
                        args_str = ', '.join([f"{arg['name']}: {arg['type']}" for arg in method['args']])
                        html += f"""
                                <div class="method-item ms-3 mt-2 p-2 border-start border-3 border-success">
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
                args_str = ', '.join([f"{arg['name']}: {arg['type']}" for arg in func['args']])
                html += f"""
                        <div class="function-item mb-3 p-3 border rounded">
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

def generate_theme_colors_section(theme_colors):
    """Gera seção visual para cores dos temas"""
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
            # Determina cor do texto baseado no brilho da cor de fundo
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

def get_contrast_color(hex_color):
    """Determina se deve usar texto claro ou escuro baseado no brilho da cor"""
    # Remove o # se presente
    hex_color = hex_color.lstrip('#')
    
    # Converte para RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Calcula brilho (fórmula de luminância)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    
    return '#ffffff' if brightness < 128 else '#000000'

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
git clone https://github.com/MrJuaumBR/LunaEngine.git
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
</body>
</html>"""
    
    with open("docs/quick-start.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_contact_page():
    """Generates contact/community page"""
    
    print("📞 Creating contact page...")
    
    html = """<!DOCTYPE html>
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
            <button class="btn btn-outline-secondary theme-toggle">
                <span class="theme-icon">🌙</span>
            </button>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row">
            <div class="col-lg-8 mx-auto">
                <h1 class="text-center mb-4">👥 Community & Contact</h1>
                <p class="lead text-center text-muted mb-5">
                    Join our community to get help, share your projects, and contribute to LunaEngine!
                </p>

                <div class="row g-4">
                    <!-- GitHub -->
                    <div class="col-md-6">
                        <div class="card h-100 community-card">
                            <div class="card-body text-center p-4">
                                <div class="community-icon github mb-3">
                                    <i class="bi bi-github fs-1"></i>
                                </div>
                                <h4 class="card-title">GitHub</h4>
                                <p class="card-text text-muted">
                                    Star the repository, report issues, and contribute to the codebase.
                                </p>
                                <a href="https://github.com/MrJuaumBR/LunaEngine" target="_blank" class="btn btn-dark">
                                    <i class="bi bi-box-arrow-up-right me-2"></i>Visit GitHub
                                </a>
                            </div>
                        </div>
                    </div>

                    <!-- Discord -->
                    <div class="col-md-6">
                        <div class="card h-100 community-card">
                            <div class="card-body text-center p-4">
                                <div class="community-icon discord mb-3">
                                    <i class="bi bi-discord fs-1"></i>
                                </div>
                                <h4 class="card-title">Discord</h4>
                                <p class="card-text text-muted">
                                    Join our Discord server for real-time discussions and support.
                                </p>
                                <a href="https://discord.gg/fb84sHDX7R" target="_blank" class="btn btn-primary" style="background-color: #5865F2; border-color: #5865F2;">
                                    <i class="bi bi-box-arrow-up-right me-2"></i>Join Discord
                                </a>
                            </div>
                        </div>
                    </div>

                    <!-- YouTube -->
                    <div class="col-md-6">
                        <div class="card h-100 community-card">
                            <div class="card-body text-center p-4">
                                <div class="community-icon youtube mb-3">
                                    <i class="bi bi-youtube fs-1"></i>
                                </div>
                                <h4 class="card-title">YouTube</h4>
                                <p class="card-text text-muted">
                                    Watch tutorials, demos, and development updates on our channel.
                                </p>
                                <a href="https://www.youtube.com/@mrjuaumbr" target="_blank" class="btn btn-danger">
                                    <i class="bi bi-box-arrow-up-right me-2"></i>Visit YouTube
                                </a>
                            </div>
                        </div>
                    </div>

                    <!-- Documentation -->
                    <div class="col-md-6">
                        <div class="card h-100 community-card">
                            <div class="card-body text-center p-4">
                                <div class="community-icon docs mb-3">
                                    <i class="bi bi-book fs-1"></i>
                                </div>
                                <h4 class="card-title">Documentation</h4>
                                <p class="card-text text-muted">
                                    Explore the complete documentation and API reference.
                                </p>
                                <a href="index.html" class="btn btn-info text-white">
                                    <i class="bi bi-book me-2"></i>View Docs
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card mt-5">
                    <div class="card-header bg-warning text-dark">
                        <h5 class="mb-0"><i class="bi bi-lightbulb me-2"></i>Getting Help</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-unstyled">
                            <li class="mb-2"><i class="bi bi-check-circle text-success me-2"></i>Check the documentation first</li>
                            <li class="mb-2"><i class="bi bi-check-circle text-success me-2"></i>Search existing GitHub issues</li>
                            <li class="mb-2"><i class="bi bi-check-circle text-success me-2"></i>Ask in Discord for quick help</li>
                            <li class="mb-2"><i class="bi bi-check-circle text-success me-2"></i>Report bugs on GitHub</li>
                            <li><i class="bi bi-check-circle text-success me-2"></i>Share your projects with the community</li>
                        </ul>
                    </div>
                </div>

                <div class="text-center mt-5">
                    <a href="index.html" class="btn btn-primary me-2">
                        <i class="bi bi-house me-2"></i>Back to Home
                    </a>
                    <a href="quick-start.html" class="btn btn-outline-primary">
                        <i class="bi bi-rocket me-2"></i>Quick Start
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="theme.js"></script>
</body>
</html>"""
    
    with open("docs/contact.html", "w", encoding="utf-8") as f:
        f.write(html)

def generate_theme_files():
    """Generates CSS and JS theme files"""
    
    print("🎨 Creating theme files...")
    
    # CSS file
    css = """/* LunaEngine Documentation Theme */
:root {
    --primary-color: #6f42c1;
    --secondary-color: #6c757d;
    --success-color: #198754;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --light-color: #f8f9fa;
    --dark-color: #212529;
    --bg-color: #ffffff;
    --text-color: #212529;
    --border-color: #dee2e6;
    --card-bg: #ffffff;
    --header-bg: #ffffff;
    --footer-bg: #343a40;
    --code-bg: #f8f9fa;
    --link-color: #6f42c1;
}

[data-theme="dark"] {
    --primary-color: #8c68cd;
    --secondary-color: #a0aec0;
    --success-color: #48bb78;
    --warning-color: #ed8936;
    --danger-color: #f56565;
    --light-color: #4a5568;
    --dark-color: #e2e8f0;
    --bg-color: #1a202c;
    --text-color: #e2e8f0;
    --border-color: #4a5568;
    --card-bg: #2d3748;
    --header-bg: #2d3748;
    --footer-bg: #1a202c;
    --code-bg: #4a5568;
    --link-color: #90cdf4;
}

/* Base Styles */
body {
    background-color: var(--bg-color);
    color: var(--text-color);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    transition: all 0.3s ease;
}

/* Navigation */
.navbar {
    background-color: var(--header-bg) !important;
    border-bottom: 1px solid var(--border-color);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.navbar-brand {
    color: var(--primary-color) !important;
}

.navbar .form-control {
    background-color: var(--bg-color);
    border-color: var(--border-color);
    color: var(--text-color);
}

.navbar .input-group-text {
    background-color: var(--bg-color);
    border-color: var(--border-color);
    color: var(--text-color);
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, var(--primary-color), #8c68cd);
    padding: 4rem 0;
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
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    color: var(--text-color);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.module-card .card-header {
    border-bottom: 1px solid var(--border-color);
}

.module-stats .badge {
    margin: 0.1rem;
    font-size: 0.75rem;
}

/* Docstring Styling */
.docstring-content {
    background-color: var(--light-color);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    padding: 1rem;
    margin: 0.5rem 0;
}

.docstring-text {
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9rem;
    line-height: 1.5;
    white-space: pre-wrap;
    color: var(--text-color);
}

/* Theme Colors Preview */
.theme-colors-section {
    background: var(--light-color);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin: 1rem 0;
}

.color-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
}

.color-item {
    border-radius: 0.5rem;
    padding: 0.75rem;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: transform 0.2s ease;
    min-height: 80px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.color-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.color-swatch {
    width: 100%;
    height: 20px;
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
    border: 1px solid rgba(0,0,0,0.1);
}

.color-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.color-name {
    font-weight: 600;
    font-size: 0.8rem;
}

.color-hex {
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.75rem;
    opacity: 0.9;
}

.theme-preview {
    margin-bottom: 2rem;
}

.theme-preview:last-child {
    margin-bottom: 0;
}

/* Code Blocks */
pre {
    background-color: var(--code-bg);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    padding: 1rem;
    color: var(--text-color);
    overflow-x: auto;
}

code {
    color: var(--primary-color);
    background-color: var(--code-bg);
    padding: 0.2rem 0.4rem;
    border-radius: 0.25rem;
    font-family: 'Consolas', 'Monaco', monospace;
}

/* Community Cards */
.community-card {
    text-align: center;
    border: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.community-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
}

.community-icon.github {
    background-color: #333;
    color: white;
}

.community-icon.discord {
    background-color: #5865F2;
    color: white;
}

.community-icon.youtube {
    background-color: #FF0000;
    color: white;
}

.community-icon.docs {
    background-color: var(--primary-color);
    color: white;
}

/* Breadcrumb */
.breadcrumb {
    background-color: var(--bg-color);
}

.breadcrumb-item a {
    color: var(--primary-color);
    text-decoration: none;
}

.breadcrumb-item.active {
    color: var(--text-color);
}

/* Alerts */
.alert {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    color: var(--text-color);
}

.alert-info {
    border-left: 4px solid var(--info);
}

/* File Cards */
.file-card .card-header {
    background-color: var(--light-color);
    border-bottom: 1px solid var(--border-color);
}

.class-item, .function-item {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
}

.method-item {
    background-color: var(--bg-color);
}

.attribute-item code {
    font-size: 0.9em;
}

/* Theme Toggle */
.theme-toggle {
    border: 1px solid var(--border-color);
    color: var(--text-color);
}

.theme-toggle:hover {
    background-color: var(--light-color);
}

/* Responsive */
@media (max-width: 768px) {
    .hero-section {
        padding: 2rem 0;
    }
    
    .display-4 {
        font-size: 2rem;
    }
    
    .module-stats .badge {
        display: block;
        margin: 0.2rem 0;
    }
    
    .color-grid {
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }
}

/* Search */
#moduleSearch:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 0.2rem rgba(111, 66, 193, 0.25);
}

/* Links */
a {
    color: var(--link-color);
    text-decoration: none;
}

a:hover {
    color: var(--primary-color);
    text-decoration: underline;
}

/* Footer */
footer {
    background-color: var(--footer-bg) !important;
    color: var(--light-color);
}
"""
    
    with open("docs/theme.css", "w", encoding="utf-8") as f:
        f.write(css)
    
    # JavaScript file
    js = """// LunaEngine Documentation JavaScript

$(document).ready(function() {
    // Theme Toggle
    $('.theme-toggle').click(function() {
        const currentTheme = $('html').attr('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        $('html').attr('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update theme icon
        const themeIcon = $('.theme-icon');
        themeIcon.text(newTheme === 'light' ? '🌙' : '☀️');
    });
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    $('html').attr('data-theme', savedTheme);
    $('.theme-icon').text(savedTheme === 'light' ? '🌙' : '☀️');
    
    // Module Search
    $('#moduleSearch').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        
        $('.module-card').each(function() {
            const card = $(this);
            const cardText = card.text().toLowerCase();
            
            if (cardText.includes(searchTerm)) {
                card.show();
            } else {
                card.hide();
            }
        });
    });
    
    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(event) {
        event.preventDefault();
        const target = $($(this).attr('href'));
        
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 70
            }, 500);
        }
    });
    
    // Add copy to clipboard for code blocks
    $('pre').each(function() {
        const codeBlock = $(this);
        const copyButton = $('<button class="btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2">Copy</button>');
        
        codeBlock.css('position', 'relative').append(copyButton);
        
        copyButton.on('click', function() {
            const code = codeBlock.find('code').text() || codeBlock.text();
            navigator.clipboard.writeText(code).then(function() {
                copyButton.text('Copied!');
                setTimeout(() => copyButton.text('Copy'), 2000);
            });
        });
    });
});

// Utility functions
function formatCode(code) {
    return code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
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
"""
    
    with open("docs/theme.js", "w", encoding="utf-8") as f:
        f.write(js)

# ========== EXECUTION ==========

if __name__ == "__main__":
    print("🎯 LUNAENGINE - DEFINITIVE DOCUMENTATION GENERATOR")
    print("=" * 50)
    
    try:
        generate_documentation()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check if the lunaengine folder exists and try again.")