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
        self.exclude_dirs = {'__pycache__', '.git', 'build', 'dist', 'venv', 'env', '.vscode', '.idea'}
        self.exclude_files = {'*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll'}
        self.file_extensions = {'.py', '.txt', '.md', '.toml', '.cfg', '.ini'}
        
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
    
    def analyze_project(self) -> Dict:
        """Analyze the entire project and return statistics"""
        files = self.get_all_files()
        stats = {
            'total_files': len(files),
            'files_by_extension': {},
            'files_by_directory': {},
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'files': []
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
        
        # Code density
        code_density = (stats['code_lines'] / max(1, stats['total_lines'])) * 100
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
    save_detailed_report(stats, report_file)
    print(f"\n📄 Detailed report saved to: {report_file}")

def save_detailed_report(stats: Dict, report_file: Path):
    """Save a detailed markdown report"""
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# LunaEngine Code Statistics\n\n")
        
        f.write("## Overview\n\n")
        f.write(f"- **Total Files**: {stats['total_files']}\n")
        f.write(f"- **Total Lines**: {stats['total_lines']}\n")
        f.write(f"- **Code Lines**: {stats['code_lines']}\n")
        f.write(f"- **Comment Lines**: {stats['comment_lines']}\n")
        f.write(f"- **Blank Lines**: {stats['blank_lines']}\n")
        
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