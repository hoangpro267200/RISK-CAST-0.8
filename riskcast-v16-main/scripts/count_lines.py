#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to count lines of code in RISKCAST v16 project"""

import os
import sys
from pathlib import Path
from collections import defaultdict

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def count_lines_in_file(file_path):
    """Count lines in a file, handling encoding errors gracefully"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except Exception:
        return 0

def count_code_lines(root_dir='.'):
    """Count lines of code by file type"""
    root = Path(root_dir)
    excludes = {'venv', '.venv', '__pycache__', '.git', 'node_modules', 
                'dist', 'build', 'archive', '.pytest_cache', '.mypy_cache'}
    
    stats = defaultdict(lambda: {'files': 0, 'lines': 0})
    
    extensions = {
        '.py': 'Python',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript/TSX',
        '.js': 'JavaScript',
        '.vue': 'Vue',
        '.html': 'HTML',
        '.css': 'CSS',
        '.json': 'JSON',
        '.md': 'Markdown',
    }
    
    for ext, name in extensions.items():
        for file_path in root.rglob(f'*{ext}'):
            # Skip excluded directories
            if any(ex in str(file_path) for ex in excludes):
                continue
            
            if file_path.is_file():
                lines = count_lines_in_file(file_path)
                stats[name]['files'] += 1
                stats[name]['lines'] += lines
    
    return stats

def main():
    print("=" * 50)
    print("THỐNG KÊ DÒNG CODE RISKCAST v16")
    print("=" * 50)
    print()
    
    stats = count_code_lines()
    
    total_lines = 0
    total_files = 0
    
    for lang, data in sorted(stats.items()):
        files = data['files']
        lines = data['lines']
        total_lines += lines
        total_files += files
        print(f"{lang:20} {lines:>8,} dòng ({files:>4} files)")
    
    print()
    print("=" * 50)
    print(f"TỔNG: {total_lines:>8,} dòng code")
    print(f"Tổng số file: {total_files:>4} files")
    print("=" * 50)
    
    # Breakdown by category
    print()
    print("PHÂN LOẠI:")
    backend = stats.get('Python', {}).get('lines', 0)
    frontend_ts = stats.get('TypeScript/TSX', {}).get('lines', 0)
    frontend_js = stats.get('JavaScript', {}).get('lines', 0)
    frontend_vue = stats.get('Vue', {}).get('lines', 0)
    frontend_html = stats.get('HTML', {}).get('lines', 0)
    frontend_css = stats.get('CSS', {}).get('lines', 0)
    
    frontend_total = frontend_ts + frontend_js + frontend_vue + frontend_html + frontend_css
    
    print(f"Backend (Python):     {backend:>8,} dòng ({backend/total_lines*100:.1f}%)")
    print(f"Frontend (JS/TS/Vue): {frontend_total:>8,} dòng ({frontend_total/total_lines*100:.1f}%)")
    print(f"Markup (HTML/CSS):    {frontend_html + frontend_css:>8,} dòng ({(frontend_html + frontend_css)/total_lines*100:.1f}%)")

if __name__ == '__main__':
    main()

