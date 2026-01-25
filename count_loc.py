#!/usr/bin/env python3
"""
Lines of Code (LOC) Counter for RISKCAST Repository
Deterministic, reproducible LOC measurement with language breakdown.
"""

import os
import re
import json
import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# ============================================================================
# EXCLUSION RULES
# ============================================================================

# Directories to exclude
EXCLUDE_DIRS = {
    'node_modules', 'dist', 'build', '.next', '.nuxt', 'coverage',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', '.venv', 'venv', 'env',
    '__pycache__', 'logs', 'tmp', '.git', '.vscode', '.idea', '.cursor',
    'htmlcov', '.tox', '.hypothesis', '.cache', 'temp'
}

# File patterns to exclude
EXCLUDE_PATTERNS = [
    r'\.min\.js$',
    r'\.min\.css$',
    r'package-lock\.json$',
    r'yarn\.lock$',
    r'pnpm-lock\.yaml$',
    r'poetry\.lock$',
    r'pipfile\.lock$',
    r'uv\.lock$',
]

# Binary/asset extensions to exclude
EXCLUDE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz', '.7z',
    '.mp4', '.mov', '.avi', '.bin', '.so', '.pyc', '.pyo', '.pyd',
    '.map', '.css.map', '.js.map', '.db', '.sqlite', '.sqlite3',
    '.log', '.tmp', '.temp', '.swp', '.swo', '.DS_Store', '.key', '.pem'
}

# Language file extensions mapping
LANGUAGE_EXTENSIONS = {
    'Python': {'.py'},
    'TypeScript': {'.ts'},
    'TSX': {'.tsx'},
    'JavaScript': {'.js', '.mjs', '.cjs'},
    'Vue': {'.vue'},
    'HTML': {'.html', '.htm'},
    'CSS': {'.css', '.scss', '.sass', '.less'},
    'SQL': {'.sql'},
    'YAML': {'.yaml', '.yml'},
    'Markdown': {'.md', '.markdown'},
    'JSON': {'.json'},
    'Shell': {'.sh', '.bash', '.zsh', '.ps1'},
    'Dockerfile': {'Dockerfile', '.dockerfile'},
    'Makefile': {'Makefile', 'makefile'},
}

# Reverse mapping for quick lookup
EXT_TO_LANGUAGE = {}
for lang, exts in LANGUAGE_EXTENSIONS.items():
    for ext in exts:
        EXT_TO_LANGUAGE[ext] = lang

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class FileStats:
    """Statistics for a single file."""
    path: str
    language: str
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    total_lines: int = 0

@dataclass
class LanguageStats:
    """Aggregated statistics for a language."""
    language: str
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    files_count: int = 0

# ============================================================================
# COMMENT DETECTION
# ============================================================================

def is_python_comment(line: str) -> bool:
    """Check if line is a Python comment."""
    stripped = line.lstrip()
    return stripped.startswith('#')

def is_python_docstring(line: str, in_docstring: bool) -> Tuple[bool, bool]:
    """Detect Python docstrings (triple-quoted strings)."""
    stripped = line.strip()
    if '"""' in stripped or "'''" in stripped:
        # Count quotes
        triple_double = stripped.count('"""')
        triple_single = stripped.count("'''")
        if triple_double % 2 == 1 or triple_single % 2 == 1:
            return True, not in_docstring
    return in_docstring, in_docstring

def is_js_comment(line: str) -> bool:
    """Check if line is a JavaScript/TypeScript comment."""
    stripped = line.strip()
    return stripped.startswith('//') or '/*' in stripped or '*/' in stripped

def is_sql_comment(line: str) -> bool:
    """Check if line is a SQL comment."""
    stripped = line.strip()
    return stripped.startswith('--') or '/*' in stripped or '*/' in stripped

def is_yaml_comment(line: str) -> bool:
    """Check if line is a YAML comment."""
    stripped = line.lstrip()
    return stripped.startswith('#')

# ============================================================================
# FILE PROCESSING
# ============================================================================

def should_exclude_file(filepath: Path) -> bool:
    """Check if file should be excluded."""
    # Check directory exclusions
    parts = filepath.parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
    
    # Check extension exclusions
    if filepath.suffix in EXCLUDE_EXTENSIONS:
        return True
    
    # Check pattern exclusions
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, filepath_str, re.IGNORECASE):
            return True
    
    return False

def detect_language(filepath: Path) -> Optional[str]:
    """Detect language from file path."""
    # Check extension
    if filepath.suffix in EXT_TO_LANGUAGE:
        return EXT_TO_LANGUAGE[filepath.suffix]
    
    # Check special filenames
    filename = filepath.name
    if filename in EXT_TO_LANGUAGE:
        return EXT_TO_LANGUAGE[filename]
    
    return None

def count_lines_python(content: str) -> Tuple[int, int, int]:
    """Count lines in Python file."""
    lines = content.split('\n')
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_docstring = False
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            blank_lines += 1
            continue
        
        # Check for docstring start/end
        in_docstring, docstring_toggled = is_python_docstring(line, in_docstring)
        
        if in_docstring:
            comment_lines += 1
        elif is_python_comment(line):
            comment_lines += 1
        else:
            code_lines += 1
    
    return code_lines, comment_lines, blank_lines

def count_lines_js_ts(content: str) -> Tuple[int, int, int]:
    """Count lines in JavaScript/TypeScript file."""
    lines = content.split('\n')
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_block_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            blank_lines += 1
            continue
        
        # Handle block comments
        if '/*' in line:
            in_block_comment = True
        if '*/' in line:
            in_block_comment = False
            comment_lines += 1
            continue
        
        if in_block_comment:
            comment_lines += 1
        elif stripped.startswith('//'):
            comment_lines += 1
        else:
            code_lines += 1
    
    return code_lines, comment_lines, blank_lines

def count_lines_vue(content: str) -> Tuple[int, int, int, int, int]:
    """Count lines in Vue SFC file (script, template, style separately)."""
    script_content = ''
    template_content = ''
    style_content = ''
    
    # Extract script section
    script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
    if script_match:
        script_content = script_match.group(1)
    
    # Extract template section
    template_match = re.search(r'<template[^>]*>(.*?)</template>', content, re.DOTALL | re.IGNORECASE)
    if template_match:
        template_content = template_match.group(1)
    
    # Extract style section
    style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL | re.IGNORECASE)
    if style_match:
        style_content = style_match.group(1)
    
    script_code, script_comment, script_blank = count_lines_js_ts(script_content)
    template_code, template_comment, template_blank = count_lines_html(template_content)
    style_code, style_comment, style_blank = count_lines_css(style_content)
    
    total_code = script_code + template_code + style_code
    total_comment = script_comment + template_comment + style_comment
    total_blank = script_blank + template_blank + style_blank
    
    return total_code, total_comment, total_blank

def count_lines_html(content: str) -> Tuple[int, int, int]:
    """Count lines in HTML file."""
    lines = content.split('\n')
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            blank_lines += 1
            continue
        
        if '<!--' in line and '-->' in line:
            comment_lines += 1
        elif '<!--' in line:
            comment_lines += 1
        elif '-->' in line:
            comment_lines += 1
        else:
            code_lines += 1
    
    return code_lines, comment_lines, blank_lines

def count_lines_css(content: str) -> Tuple[int, int, int]:
    """Count lines in CSS file."""
    lines = content.split('\n')
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_block_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            blank_lines += 1
            continue
        
        if '/*' in line:
            in_block_comment = True
        if '*/' in line:
            in_block_comment = False
            comment_lines += 1
            continue
        
        if in_block_comment:
            comment_lines += 1
        else:
            code_lines += 1
    
    return code_lines, comment_lines, blank_lines

def count_lines_sql(content: str) -> Tuple[int, int, int]:
    """Count lines in SQL file."""
    lines = content.split('\n')
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    in_block_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            blank_lines += 1
            continue
        
        if '/*' in line:
            in_block_comment = True
        if '*/' in line:
            in_block_comment = False
            comment_lines += 1
            continue
        
        if in_block_comment:
            comment_lines += 1
        elif stripped.startswith('--'):
            comment_lines += 1
        else:
            code_lines += 1
    
    return code_lines, comment_lines, blank_lines

def count_lines_yaml(content: str) -> Tuple[int, int, int]:
    """Count lines in YAML file."""
    lines = content.split('\n')
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    
    for line in lines:
        stripped = line.lstrip()
        
        if not line.strip():
            blank_lines += 1
            continue
        
        if is_yaml_comment(line):
            comment_lines += 1
        else:
            code_lines += 1
    
    return code_lines, comment_lines, blank_lines

def count_lines_markdown(content: str) -> Tuple[int, int, int]:
    """Count lines in Markdown file (all as code, no comment detection)."""
    lines = content.split('\n')
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    
    for line in lines:
        if not line.strip():
            blank_lines += 1
        else:
            code_lines += 1
    
    return code_lines, comment_lines, blank_lines

def count_lines_generic(content: str) -> Tuple[int, int, int]:
    """Generic line counter (no comment detection)."""
    lines = content.split('\n')
    code_lines = 0
    comment_lines = 0
    blank_lines = 0
    
    for line in lines:
        if not line.strip():
            blank_lines += 1
        else:
            code_lines += 1
    
    return code_lines, comment_lines, blank_lines

def count_file_lines(filepath: Path, language: str) -> FileStats:
    """Count lines in a file based on its language."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return FileStats(path=str(filepath), language=language)
    
    if language == 'Python':
        code, comment, blank = count_lines_python(content)
    elif language in ('JavaScript', 'TypeScript', 'TSX'):
        code, comment, blank = count_lines_js_ts(content)
    elif language == 'Vue':
        code, comment, blank = count_lines_vue(content)
    elif language == 'HTML':
        code, comment, blank = count_lines_html(content)
    elif language == 'CSS':
        code, comment, blank = count_lines_css(content)
    elif language == 'SQL':
        code, comment, blank = count_lines_sql(content)
    elif language == 'YAML':
        code, comment, blank = count_lines_yaml(content)
    elif language == 'Markdown':
        code, comment, blank = count_lines_markdown(content)
    else:
        code, comment, blank = count_lines_generic(content)
    
    return FileStats(
        path=str(filepath),
        language=language,
        code_lines=code,
        comment_lines=comment,
        blank_lines=blank,
        total_lines=code + comment + blank
    )

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def scan_repository(root: Path) -> Tuple[List[FileStats], Dict[str, LanguageStats]]:
    """Scan repository and count lines."""
    file_stats_list = []
    language_stats = defaultdict(lambda: LanguageStats(language='', code_lines=0, comment_lines=0, blank_lines=0, files_count=0))
    
    print("Scanning repository...")
    
    for filepath in root.rglob('*'):
        if not filepath.is_file():
            continue
        
        if should_exclude_file(filepath):
            continue
        
        language = detect_language(filepath)
        if not language:
            continue
        
        stats = count_file_lines(filepath, language)
        file_stats_list.append(stats)
        
        # Aggregate by language
        lang_stat = language_stats[language]
        lang_stat.language = language
        lang_stat.code_lines += stats.code_lines
        lang_stat.comment_lines += stats.comment_lines
        lang_stat.blank_lines += stats.blank_lines
        lang_stat.files_count += 1
    
    return file_stats_list, dict(language_stats)

# ============================================================================
# OUTPUT GENERATION
# ============================================================================

def generate_reports(file_stats_list: List[FileStats], language_stats: Dict[str, LanguageStats], root: Path):
    """Generate CSV and JSON reports."""
    artifacts_dir = root / 'artifacts'
    artifacts_dir.mkdir(exist_ok=True)
    
    # Prepare language stats for export
    lang_data = []
    for lang in sorted(language_stats.keys()):
        stat = language_stats[lang]
        lang_data.append({
            'language': stat.language,
            'code_lines': stat.code_lines,
            'comment_lines': stat.comment_lines,
            'blank_lines': stat.blank_lines,
            'total_lines': stat.code_lines + stat.comment_lines + stat.blank_lines,
            'files_count': stat.files_count
        })
    
    # Top 50 largest files
    top_files = sorted(file_stats_list, key=lambda x: x.code_lines, reverse=True)[:50]
    top_files_data = [
        {
            'path': f.path,
            'language': f.language,
            'code_lines': f.code_lines,
            'comment_lines': f.comment_lines,
            'blank_lines': f.blank_lines,
            'total_lines': f.total_lines
        }
        for f in top_files
    ]
    
    # Total stats
    total_code = sum(s.code_lines for s in file_stats_list)
    total_comment = sum(s.comment_lines for s in file_stats_list)
    total_blank = sum(s.blank_lines for s in file_stats_list)
    total_files = len(file_stats_list)
    
    # JSON export
    json_data = {
        'summary': {
            'total_code_lines': total_code,
            'total_comment_lines': total_comment,
            'total_blank_lines': total_blank,
            'total_lines': total_code + total_comment + total_blank,
            'total_files': total_files
        },
        'by_language': lang_data,
        'top_50_files': top_files_data
    }
    
    json_path = artifacts_dir / 'loc_report.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # CSV export
    csv_path = artifacts_dir / 'loc_report.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Language', 'Code Lines', 'Comment Lines', 'Blank Lines', 'Total Lines', 'Files Count'])
        for lang in lang_data:
            writer.writerow([
                lang['language'],
                lang['code_lines'],
                lang['comment_lines'],
                lang['blank_lines'],
                lang['total_lines'],
                lang['files_count']
            ])
        writer.writerow([])
        writer.writerow(['TOTAL', total_code, total_comment, total_blank, total_code + total_comment + total_blank, total_files])
        writer.writerow([])
        writer.writerow(['Top 50 Files by Code Lines'])
        writer.writerow(['Path', 'Language', 'Code Lines', 'Comment Lines', 'Blank Lines', 'Total Lines'])
        for file_data in top_files_data:
            writer.writerow([
                file_data['path'],
                file_data['language'],
                file_data['code_lines'],
                file_data['comment_lines'],
                file_data['blank_lines'],
                file_data['total_lines']
            ])
    
    return json_path, csv_path, json_data

def print_summary(json_data: dict):
    """Print summary table to terminal."""
    print("\n" + "="*80)
    print("LINES OF CODE REPORT")
    print("="*80)
    
    summary = json_data['summary']
    print(f"\nTOTAL SUMMARY:")
    print(f"  Code Lines:      {summary['total_code_lines']:>10,}")
    print(f"  Comment Lines:   {summary['total_comment_lines']:>10,}")
    print(f"  Blank Lines:     {summary['total_blank_lines']:>10,}")
    print(f"  Total Lines:     {summary['total_lines']:>10,}")
    print(f"  Files Count:     {summary['total_files']:>10,}")
    
    print(f"\n{'LANGUAGE':<20} {'CODE':>12} {'COMMENTS':>12} {'BLANKS':>12} {'TOTAL':>12} {'FILES':>10}")
    print("-" * 80)
    
    for lang in sorted(json_data['by_language'], key=lambda x: x['code_lines'], reverse=True):
        print(f"{lang['language']:<20} {lang['code_lines']:>12,} {lang['comment_lines']:>12,} "
              f"{lang['blank_lines']:>12,} {lang['total_lines']:>12,} {lang['files_count']:>10,}")
    
    print("\n" + "="*80)
    print("TOP 10 LARGEST FILES BY CODE LINES:")
    print("="*80)
    for i, file_data in enumerate(json_data['top_50_files'][:10], 1):
        print(f"{i:>2}. {file_data['path']:<60} ({file_data['language']:<10}) {file_data['code_lines']:>6,} lines")

# ============================================================================
# CROSS-VALIDATION
# ============================================================================

def try_cloc_validation(root: Path) -> Optional[dict]:
    """Try to validate using cloc if available."""
    import subprocess
    import shutil
    
    cloc_path = shutil.which('cloc')
    if not cloc_path:
        # Try to find scc as alternative
        scc_path = shutil.which('scc')
        if scc_path:
            try:
                result = subprocess.run(
                    [scc_path, '--by-file', '--format', 'json', str(root)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    return {'tool': 'scc', 'output': result.stdout}
            except Exception:
                pass
        return None
    
    try:
        # Build exclusion arguments
        exclude_dirs = ','.join(EXCLUDE_DIRS)
        result = subprocess.run(
            [cloc_path, '--exclude-dir', exclude_dirs, '--json', str(root)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return {'tool': 'cloc', 'output': result.stdout}
    except Exception as e:
        print(f"Warning: cloc validation failed: {e}")
    
    return None

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    root = Path(__file__).parent.resolve()
    
    print(f"Repository root: {root}")
    print("Starting LOC count...")
    
    # Scan repository
    file_stats_list, language_stats = scan_repository(root)
    
    # Generate reports
    json_path, csv_path, json_data = generate_reports(file_stats_list, language_stats, root)
    
    # Print summary
    print_summary(json_data)
    
    print(f"\n{'='*80}")
    print(f"Reports generated:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    print(f"{'='*80}")
    
    # Try cross-validation
    print("\nAttempting cross-validation with cloc/scc...")
    validation = try_cloc_validation(root)
    if validation:
        print(f"Cross-validation tool found: {validation['tool']}")
        try:
            if validation['tool'] == 'cloc':
                cloc_data = json.loads(validation['output'])
                cloc_total = cloc_data.get('SUM', {}).get('code', 0)
                our_total = json_data['summary']['total_code_lines']
                diff_pct = abs(cloc_total - our_total) / max(cloc_total, our_total) * 100 if max(cloc_total, our_total) > 0 else 0
                print(f"  cloc total: {cloc_total:,}")
                print(f"  Our total:  {our_total:,}")
                print(f"  Difference: {diff_pct:.2f}%")
                if diff_pct > 2:
                    print("  ⚠️  Difference > 2% - may be due to:")
                    print("     - Different comment detection rules")
                    print("     - Different file type classification")
                    print("     - Different exclusion patterns")
        except Exception as e:
            print(f"  Could not parse validation output: {e}")
    else:
        print("  No cross-validation tool found (cloc/scc not installed)")
        print("  Install cloc: brew install cloc (macOS) or apt-get install cloc (Linux)")

if __name__ == '__main__':
    main()
