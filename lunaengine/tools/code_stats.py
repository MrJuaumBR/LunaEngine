#!/usr/bin/env python3
"""
LunaEngine Code Statistics Script
Counts lines of code, files, and provides detailed statistics
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class CodeStatistics:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.exclude_dirs = {'__pycache__', '.git', 'build', 'dist', 'venv', 'env', '.vscode', '.idea', 'themes'}
        self.exclude_files = {'*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll'}
        self.file_extensions = {'.py', '.txt', '.md', '.toml', '.cfg', '.ini','.json', '.vert', '.frag', '.comp', '.geom'}
        
    def get_some_stats(self) -> Dict:
        """
        Count the number of themes available in LunaEngine
        Returns: Dictionary with theme statistics
        """
        stats = {
            'total_themes': 0,
            'total_elements': 0,
            'themes_error': None,
            'elements_error': None
        }
        
        try:
            sys.path.append(str(self.root_dir))
            
            # Import the ThemeManager
            from lunaengine.ui.themes import ThemeManager
            
            # Get all themes and count them
            themes = ThemeManager.get_themes()
            stats['total_themes'] = len(themes)
                    
        except ImportError as e:
            stats['themes_error'] = f"Could not import ThemeManager: {e}"
        except Exception as e:
            stats['themes_error'] = f"Error counting themes: {e}"
        finally:
            # Remove the path we added
            if str(self.root_dir) in sys.path:
                sys.path.remove(str(self.root_dir))
        
        try:
            sys.path.append(str(self.root_dir))
            
            from lunaengine.ui.elements import UIElement, UiFrame
            
            total_elements_list = UIElement.__subclasses__().copy()
            total_elements_list.extend(UiFrame.__subclasses__())
            
            stats['total_elements'] = len(total_elements_list)
        except ImportError as e:
            stats['elements_error'] = f"Could not import UIElement: {e}"
        except Exception as e:
            stats['elements_error'] = f"Error counting elements: {e}"
        finally:
            # Remove the path we added
            if str(self.root_dir) in sys.path:
                sys.path.remove(str(self.root_dir))
        
        return stats
    
    def count_lines_in_file(self, file_path: Path) -> Tuple[int, int, int]:
        """
        Count lines in a file
        Returns: (total_lines, code_lines, comment_lines, blank_lines)
        """
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        in_multiline_comment = False
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    total_lines += 1
                    stripped_line = line.strip()
                    
                    # Check for blank lines
                    if not stripped_line:
                        blank_lines += 1
                        continue
                    
                    # Handle multiline comments
                    if in_multiline_comment:
                        comment_lines += 1
                        if '"""' in stripped_line or "'''" in stripped_line:
                            in_multiline_comment = False
                        continue
                    
                    # Check for multiline comment start
                    if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                        comment_lines += 1
                        if not (stripped_line.endswith('"""') and len(stripped_line) > 3) and \
                           not (stripped_line.endswith("'''") and len(stripped_line) > 3):
                            in_multiline_comment = True
                        continue
                    
                    # Check for single line comments
                    if stripped_line.startswith('#'):
                        comment_lines += 1
                    else:
                        code_lines += 1
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return total_lines, code_lines, comment_lines, blank_lines
    
    def get_all_files(self) -> List[Path]:
        """Get all relevant files in the project"""
        files = []
        
        for root, dirs, filenames in os.walk(self.root_dir):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # Check file extension
                if file_path.suffix in self.file_extensions:
                    files.append(file_path)
                    
        return files
    
    def get_project_structure(self) -> List[str]:
        """Get the complete project structure as a list of formatted lines"""
        lines = []
        
        def add_directory(path: Path, prefix: str = "", is_last: bool = True):
            """Recursively add directory structure to lines"""
            # Get all items in directory
            items = []
            for item in sorted(path.iterdir()):
                if item.name in self.exclude_dirs:
                    continue
                if item.is_dir() or item.suffix in self.file_extensions:
                    items.append(item)
            
            # Process each item
            for i, item in enumerate(items):
                is_last_item = (i == len(items) - 1)
                
                if item.is_dir():
                    # Directory
                    connector = "└── " if is_last_item else "├── "
                    lines.append(prefix + connector + "[DIR] " + item.name + "/")
                    
                    # Recursively process subdirectory
                    new_prefix = prefix + ("    " if is_last_item else "│   ")
                    add_directory(item, new_prefix, is_last_item)
                else:
                    # File
                    connector = "└── " if is_last_item else "├── "
                    ext = item.suffix.lower()
                    emoji = self.get_file_emoji(ext)
                    lines.append(prefix + connector + emoji + " " + item.name)
        
        # Start from root
        lines.append("[ROT] " + str(self.root_dir.name) + "/")
        add_directory(self.root_dir, "", True)
        
        return lines

    def format_structure_tree(self, structure_lines: List[str]) -> str:
        """Format the structure lines as a tree"""
        return "\n".join(structure_lines)
    
    def get_file_emoji(self, extension: str) -> str:
        """Get appropriate emoji for file type"""
        emoji_map = {
            '.py': '[PYT]',
            '.md': '[MDN]',
            '.txt': '[TXT]',
            '.toml': '[TML]',
            '.cfg': '[CFG]',
            '.ini': '[INI]',
            '.json': '[JSN]',
            '.yml': '[YML]',
            '.yaml': '[YAL]',
            '.vert': '[SHD]',
            '.frag': '[SHD]',
            '.comp': '[SHD]',
            '.geom': '[SHD]',
        }
        return emoji_map.get(extension, '[UNK]')
    
    def analyze_project(self) -> Dict:
        """Analyze the entire project and return statistics"""
        files = self.get_all_files()
        _stats = self.get_some_stats()
        stats = {
            'total_files': len(files),
            'files_by_extension': {},
            'files_by_directory': {},
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'files': [],
            'themes': {'total_themes':_stats['total_themes'], 'error': _stats['themes_error']},
            'elements': {'total_elements':_stats['total_elements'], 'error': _stats['elements_error']},
            'project_structure': self.get_project_structure()  # Now returns list of lines
        }
        
        for file_path in files:
            # Get file stats
            total, code, comment, blank = self.count_lines_in_file(file_path)
            
            # Update overall stats
            stats['total_lines'] += total
            stats['code_lines'] += code
            stats['comment_lines'] += comment
            stats['blank_lines'] += blank
            
            # Update extension stats
            ext = file_path.suffix
            stats['files_by_extension'][ext] = stats['files_by_extension'].get(ext, 0) + 1
            
            # Update directory stats
            rel_path = file_path.relative_to(self.root_dir)
            directory = str(rel_path.parent)
            if directory == '.':
                directory = 'root'
            stats['files_by_directory'][directory] = stats['files_by_directory'].get(directory, 0) + 1
            
            # Store individual file info
            stats['files'].append({
                'path': str(rel_path),
                'total_lines': total,
                'code_lines': code,
                'comment_lines': comment,
                'blank_lines': blank,
                'size_kb': file_path.stat().st_size / 1024
            })
        
        return stats
    
    def get_code_density(self, stats):
        # Code density
        return (stats['code_lines'] / max(1, stats['total_lines'])) * 100
    
    def print_statistics(self, stats: Dict):
        """Print formatted statistics"""
        print("=" * 60)
        print("LUNAENGINE CODE STATISTICS")
        print("=" * 60)
        
        # Overall statistics
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Files:     {stats['total_files']:>6}")
        print(f"   Total Lines:     {stats['total_lines']:>6}")
        print(f"   Code Lines:      {stats['code_lines']:>6} ({stats['code_lines']/max(1, stats['total_lines'])*100:.1f}%)")
        print(f"   Comment Lines:   {stats['comment_lines']:>6} ({stats['comment_lines']/max(1, stats['total_lines'])*100:.1f}%)")
        print(f"   Blank Lines:     {stats['blank_lines']:>6} ({stats['blank_lines']/max(1, stats['total_lines'])*100:.1f}%)")
        
        # Theme statistics
        print(f"\n🎨 THEME STATISTICS:")
        if stats['themes']['error']:
            print(f"   ❌ Error: {stats['themes']['error']}")
        else:
            print(f"   Total Themes:    {stats['themes']['total_themes']:>6}")
        
        # Files by extension
        print(f"\n📁 FILES BY EXTENSION:")
        for ext, count in sorted(stats['files_by_extension'].items()):
            percentage = (count / stats['total_files']) * 100
            print(f"   {ext or 'no ext':<8} {count:>4} files ({percentage:5.1f}%)")
        
        # Files by directory
        print(f"\n📂 FILES BY DIRECTORY:")
        for directory, count in sorted(stats['files_by_directory'].items()):
            percentage = (count / stats['total_files']) * 100
            print(f"   {directory:<25} {count:>3} files ({percentage:5.1f}%)")
        
        # Largest files
        print(f"\n📈 LARGEST FILES (by lines):")
        largest_files = sorted(stats['files'], key=lambda x: x['total_lines'], reverse=True)[:10]
        for i, file_info in enumerate(largest_files, 1):
            print(f"   {i:2}. {file_info['path'][:35]:<35} {file_info['total_lines']:>4} lines")
        
        # Most commented files
        print(f"\n💭 MOST COMMENTED FILES:")
        commented_files = sorted(stats['files'], 
                               key=lambda x: x['comment_lines']/max(1, x['total_lines']), 
                               reverse=True)[:10]
        for i, file_info in enumerate(commented_files, 1):
            comment_ratio = (file_info['comment_lines'] / max(1, file_info['total_lines'])) * 100
            print(f"   {i:2}. {file_info['path'][:35]:<35} {comment_ratio:5.1f}% comments")
        
        # Project structure
        print(f"\n🌳 PROJECT STRUCTURE:")
        structure_tree = self.format_structure_tree(stats['project_structure'])
        print(structure_tree)
        
        # Code density
        code_density = self.get_code_density(stats)
        print(f"\n📝 CODE DENSITY: {code_density:.1f}%")
        
        if code_density > 80:
            print("   🔥 High code density - consider adding more comments")
        elif code_density < 50:
            print("   📚 Well documented - good comment ratio")
        else:
            print("   ⚖️  Balanced code and comments")
        
        print("=" * 60)

def main():
    # Get the project root directory (parent of tools directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    if not project_root.exists():
        print(f"Error: Project root not found at {project_root}")
        sys.exit(1)
    
    print(f"Analyzing LunaEngine project at: {project_root}")
    
    # Analyze the project
    analyzer = CodeStatistics(project_root)
    stats = analyzer.analyze_project()
    
    # Print statistics
    analyzer.print_statistics(stats)
    
    # Save detailed report to file
    report_file = project_root / "CODE_STATISTICS.md"
    save_detailed_report(stats, report_file, analyzer)
    print(f"\n📄 Detailed report saved to: {report_file}")

def save_detailed_report(stats: Dict, report_file: Path, analyzer: CodeStatistics):
    """Save a detailed markdown report"""
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# LunaEngine Code Statistics\n\n")
        
        f.write("## Overview\n\n")
        f.write(f"- **Total Files**: {stats['total_files']}\n")
        f.write(f"- **Total Lines**: {stats['total_lines']}\n")
        f.write(f"- **Code Lines**: {stats['code_lines']}\n")
        f.write(f"- **Comment Lines**: {stats['comment_lines']}\n")
        f.write(f"- **Blank Lines**: {stats['blank_lines']}\n")
        
        # Add theme statistics to report
        f.write("\n## Statistics\n\n")
        if stats['themes']['error']:
            f.write(f"- Themes **Error**: {stats['themes']['error']}\n")
        else:
            f.write(f"- **Total Themes**: {stats['themes']['total_themes']}\n")
        
        if stats['elements']['error']:
            f.write(f"- Elements **Error**: {stats['elements']['error']}\n")
        else:
            f.write(f"- **Total Elements**: {stats['elements']['total_elements']}\n")
        
        f.write("\n## Code Density\n\n")
        code_density = (stats['code_lines'] / max(1, stats['total_lines'])) * 100
        f.write(f"- **Code Density**: {code_density:.1f}%\n")
        text = "High code density - consider adding more comments" if code_density > 80 else \
               "Well documented - good comment ratio" if code_density < 50 else \
               "Balanced code and comments"
        f.write(f"- {text}\n")
        
        f.write("\n## Project Structure\n\n")
        f.write("```bash\n")
        for line in stats['project_structure']:
            f.write(line + "\n")
        f.write("```\n")
        
        f.write("\n## Files by Extension\n\n")
        f.write("| Extension | Count | Percentage |\n")
        f.write("|-----------|-------|------------|\n")
        for ext, count in sorted(stats['files_by_extension'].items()):
            percentage = (count / stats['total_files']) * 100
            f.write(f"| `{ext or 'no ext'}` | {count} | {percentage:.1f}% |\n")
        
        f.write("\n## Files by Directory\n\n")
        f.write("| Directory | File Count |\n")
        f.write("|-----------|------------|\n")
        for directory, count in sorted(stats['files_by_directory'].items()):
            f.write(f"| `{directory}` | {count} |\n")
        
        f.write("\n## File Details\n\n")
        f.write("| File | Total Lines | Code | Comments | Blank | Size (KB) |\n")
        f.write("|------|------------|------|----------|-------|-----------|\n")
        
        for file_info in sorted(stats['files'], key=lambda x: x['total_lines'], reverse=True):
            f.write(f"| `{file_info['path']}` | {file_info['total_lines']} | {file_info['code_lines']} | {file_info['comment_lines']} | {file_info['blank_lines']} | {file_info['size_kb']:.1f} |\n")

if __name__ == "__main__":
    main()