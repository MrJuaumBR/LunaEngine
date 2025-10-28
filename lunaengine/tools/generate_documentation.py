#!/usr/bin/env python3
"""
Fast Ollama-powered documentation generator for LunaEngine
Multi-threaded with progress tracking
"""

import os
import ast
import subprocess
import concurrent.futures
import threading
from pathlib import Path
from typing import List, Dict, Any
import time

class FastDocumentationGenerator:
    def __init__(self, model: str = "codellama:7b"):
        self.model = model
        self._ollama_lock = threading.Lock()
        self._processed_count = 0
        self._total_count = 0
        self._start_time = None
    
    def _call_ollama(self, prompt: str) -> str:
        """Thread-safe Ollama call with optimized settings"""
        with self._ollama_lock:
            try:
                import ollama
                response = ollama.generate(
                    model=self.model,
                    prompt=prompt,
                    options={
                        'temperature': 0.2,      # More creative but consistent
                        'num_ctx': 16000,       # Larger context window
                        'num_predict': 512,     # Limit response length
                        'top_k': 40,
                        'top_p': 0.9,
                    }
                )
                return response['response'].strip()
            except Exception as e:
                print(f"❌ Ollama error: {e}")
                return '"""Auto-generated documentation."""'
    
    def _update_progress(self, item_type: str = "item"):
        """Update and display progress"""
        self._processed_count += 1
        if self._total_count > 0:
            percent = (self._processed_count / self._total_count) * 100
            elapsed = time.time() - self._start_time
            print(f"📊 Progress: {self._processed_count}/{self._total_count} ({percent:.1f}%) - {item_type}")
    
    def generate_docstring(self, simplified_code: str) -> str:
        """Fast prompt for docstring generation"""
        prompt = f"""Write a concise Google-style docstring for this Python code:

{simplified_code}

Include: 1) Brief description, 2) Parameters, 3) Returns. Keep it under 10 lines."""
        return self._call_ollama(prompt)

    def _extract_signature(self, func_node: ast.FunctionDef) -> str:
        """Extract function signature with types"""
        args = []
        
        # Regular arguments
        for arg in func_node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_type = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else 'Any'
                arg_str += f": {arg_type}"
            args.append(arg_str)
        
        # Return type
        return_type = ""
        if func_node.returns:
            return_type = f" -> {ast.unparse(func_node.returns)}" if hasattr(ast, 'unparse') else " -> Any"
        
        return f"{func_node.name}({', '.join(args)}){return_type}"

    def _extract_body_preview(self, func_node: ast.FunctionDef, source_code: str) -> List[str]:
        """Extract key lines from function body"""
        lines = source_code.split('\n')
        start_line = func_node.lineno
        
        # FIX: Use end_lineno instead of end_lineo
        end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else start_line + 10
        
        preview = []
        line_count = 0
        
        for i in range(start_line, min(end_line, start_line + 8)):  # First 8 lines
            if i >= len(lines):
                break
            line = lines[i].strip()
            if not line or line.startswith('def ') or line.startswith('"""'):
                continue
                
            # Skip simple returns/assignments, show control structures
            if any(keyword in line for keyword in ['if ', 'for ', 'while ', 'def ', 'class ', 'async ', 'await']):
                preview.append(line)
                line_count += 1
            
            if line_count >= 4:  # Max 4 preview lines
                break
                
        return preview

    def _simplify_code_for_ai(self, node: ast.AST, source_code: str) -> str:
        """Extract only essential parts for AI processing"""
        simplified = []
        
        if isinstance(node, ast.FunctionDef):
            signature = self._extract_signature(node)
            simplified.append(f"def {signature}:")
            
            docstring = ast.get_docstring(node)
            if docstring:
                simplified.append(f'    """{docstring}"""')
            
            body_preview = self._extract_body_preview(node, source_code)
            if body_preview:
                simplified.append("    # Code preview:")
                for line in body_preview:
                    simplified.append(f"    {line}")
                    
        elif isinstance(node, ast.ClassDef):
            simplified.append(f"class {node.name}:")
            docstring = ast.get_docstring(node)
            if docstring:
                simplified.append(f'    """{docstring}"""')
            
            # Show method signatures only
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_sig = self._extract_signature(item)
                    simplified.append(f"    def {method_sig}:")
                    method_doc = ast.get_docstring(item)
                    if method_doc:
                        simplified.append(f'        """{method_doc}"""')
        
        return "\n".join(simplified)

    def _analyze_function_parallel(self, func_node: ast.FunctionDef, source_code: str, is_method: bool = False) -> Dict[str, Any]:
        """Thread-safe function analysis"""
        # Skip private methods to save time
        if func_node.name.startswith('_'):
            return {
                'name': func_node.name,
                'docstring': ast.get_docstring(func_node) or "Private method.",
                'line_number': func_node.lineno,
                'is_method': is_method
            }
        
        simplified_code = self._simplify_code_for_ai(func_node, source_code)
        
        func_info = {
            'name': func_node.name,
            'docstring': ast.get_docstring(func_node),
            'line_number': func_node.lineno,
            'is_method': is_method
        }
        
        if not func_info['docstring']:
            context = "method" if is_method else "function"
            func_info['ai_docstring'] = self.generate_docstring(simplified_code)
            self._update_progress(f"{context} {func_node.name}")
        
        return func_info

    def _analyze_class_parallel(self, class_node: ast.ClassDef, source_code: str) -> Dict[str, Any]:
        """Thread-safe class analysis"""
        # Skip private classes
        if class_node.name.startswith('_'):
            return {
                'name': class_node.name,
                'docstring': ast.get_docstring(class_node) or "Private class.",
                'line_number': class_node.lineno,
                'methods': []
            }
        
        simplified_code = self._simplify_code_for_ai(class_node, source_code)
        
        class_info = {
            'name': class_node.name,
            'docstring': ast.get_docstring(class_node),
            'line_number': class_node.lineno,
            'methods': []
        }
        
        # Process methods in parallel
        methods_to_process = []
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                methods_to_process.append((node, source_code, True))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            method_futures = [
                executor.submit(self._analyze_function_parallel, node, src, is_method)
                for node, src, is_method in methods_to_process
            ]
            
            for future in concurrent.futures.as_completed(method_futures):
                class_info['methods'].append(future.result())
        
        if not class_info['docstring']:
            class_info['ai_docstring'] = self.generate_docstring(simplified_code)
            self._update_progress(f"class {class_node.name}")
        
        return class_info

    def analyze_module(self, module_path: Path) -> Dict[str, Any]:
        """Parallel analysis of a Python module"""
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception as e:
            print(f"❌ Error reading {module_path}: {e}")
            return {
                'module_name': module_path.stem,
                'file_path': str(module_path),
                'classes': [],
                'functions': [],
                'line_count': 0
            }
        
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            print(f"❌ Syntax error in {module_path}: {e}")
            return {
                'module_name': module_path.stem,
                'file_path': str(module_path),
                'classes': [],
                'functions': [],
                'line_count': len(source_code.splitlines())
            }
        
        analysis = {
            'module_name': module_path.stem,
            'file_path': str(module_path),
            'classes': [],
            'functions': [],
            'line_count': len(source_code.splitlines())
        }
        
        # Collect all functions and classes
        functions_to_process = []
        classes_to_process = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes_to_process.append((node, source_code))
            elif isinstance(node, ast.FunctionDef):
                parent_is_class = any(isinstance(parent, ast.ClassDef) for parent in ast.walk(node))
                if not parent_is_class:
                    functions_to_process.append((node, source_code, False))
        
        # Update total count for progress tracking
        self._total_count += len(functions_to_process) + len(classes_to_process)
        
        # Process in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all tasks
            function_futures = [
                executor.submit(self._analyze_function_parallel, node, src, is_method)
                for node, src, is_method in functions_to_process
            ]
            
            class_futures = [
                executor.submit(self._analyze_class_parallel, node, src)
                for node, src in classes_to_process
            ]
            
            # Collect results
            for future in concurrent.futures.as_completed(function_futures):
                analysis['functions'].append(future.result())
            
            for future in concurrent.futures.as_completed(class_futures):
                analysis['classes'].append(future.result())
        
        return analysis

    def generate_markdown_docs(self, module_path: Path) -> str:
        """Generate Markdown documentation for a module"""
        analysis = self.analyze_module(module_path)
        
        md = f"# {analysis['module_name']}\n\n"
        md += "## Overview\n\n"
        md += f"*File: `{analysis['file_path']}`*\n"
        md += f"*Lines: {analysis['line_count']}*\n\n"
        
        # Classes section
        if analysis['classes']:
            md += "## Classes\n\n"
            for class_info in analysis['classes']:
                md += self._format_class_docs(class_info)
        
        # Functions section
        if analysis['functions']:
            md += "## Functions\n\n"
            for func_info in analysis['functions']:
                md += self._format_function_docs(func_info)
        
        return md

    def _format_class_docs(self, class_info: Dict[str, Any]) -> str:
        """Format class documentation in Markdown"""
        md = f"### {class_info['name']}\n\n"
        
        docstring = class_info.get('ai_docstring') or class_info['docstring'] or "No documentation available."
        md += f"{docstring}\n\n"
        
        md += f"*Line: {class_info['line_number']}*\n\n"
        
        # Methods
        if class_info['methods']:
            md += "#### Methods\n\n"
            for method in class_info['methods']:
                md += self._format_function_docs(method, indent="##### ")
        
        md += "---\n\n"
        return md

    def _format_function_docs(self, func_info: Dict[str, Any], indent: str = "### ") -> str:
        """Format function documentation in Markdown"""
        prefix = "Method " if func_info['is_method'] else "Function "
        md = f"{indent}{prefix}`{func_info['name']}`\n\n"
        
        docstring = func_info.get('ai_docstring') or func_info['docstring'] or "No documentation available."
        md += f"{docstring}\n\n"
        
        md += f"*Line: {func_info['line_number']}*\n\n"
        return md

    def process_single_module(self, module_path: Path):
        """Process a single module and return markdown + output file path"""
        print(f"🔄 Processing {module_path}...")
        markdown_docs = self.generate_markdown_docs(module_path)
        output_file = Path("ollama_docs") / f"{module_path.stem}.md"
        return markdown_docs, output_file

    def generate_full_documentation(self):
        """Generate complete documentation using multi-threading"""
        print(f"🚀 Using Ollama model: {self.model}")
        print("⏳ Generating documentation with multi-threading...")
        
        self._start_time = time.time()
        self._processed_count = 0
        self._total_count = 0

        # Create documentation directory
        docs_dir = Path("ollama_docs")
        docs_dir.mkdir(exist_ok=True)

        modules = [
            "lunaengine/core/engine.py",
            "lunaengine/ui/elements.py",
            "lunaengine/utils/image_converter.py", 
            "lunaengine/graphics/lighting.py",
            "lunaengine/graphics/particles.py",
            "lunaengine/utils/performance.py"
        ]

        # First count total items for progress
        print("📋 Counting items to process...")
        for module_path in modules:
            path = Path(module_path)
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                                if not node.name.startswith('_'):
                                    self._total_count += 1
                except Exception as e:
                    print(f"⚠️  Could not count items in {path}: {e}")

        print(f"🎯 Total items to process: {self._total_count}")

        # Process modules in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_module = {
                executor.submit(self.process_single_module, Path(module_path)): module_path
                for module_path in modules if Path(module_path).exists()
            }
            
            for future in concurrent.futures.as_completed(future_to_module):
                module_path = future_to_module[future]
                try:
                    markdown_docs, output_file = future.result()
                    output_file.write_text(markdown_docs)
                    print(f"✅ Generated {output_file}")
                except Exception as e:
                    print(f"❌ Error processing {module_path}: {e}")

        # Create index
        index_content = """# LunaEngine Documentation

AI-generated documentation using Ollama with multi-threading.

## Modules
- [Core Engine](engine.md)
- [UI Elements](elements.md) 
- [Image Converter](image_converter.md)
- [Lighting System](lighting.md)
- [Particle System](particles.md)
- [Performance Tools](performance.md)

## About
This documentation was automatically generated using Ollama AI models with optimized parallel processing.
"""
        (docs_dir / "README.md").write_text(index_content)
        
        total_time = time.time() - self._start_time
        print(f"🎉 Documentation generation complete! Time: {total_time:.1f}s")
        print("📁 Open ollama_docs/README.md to browse the documentation")

def generate_full_documentation():
    """Generate complete documentation for LunaEngine"""
    generator = FastDocumentationGenerator()
    generator.generate_full_documentation()

if __name__ == "__main__":
    generate_full_documentation()