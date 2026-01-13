#!/usr/bin/env python3
"""
RISKCAST Production Build Script
Bundles and minifies JS/CSS for production deployment
"""

import os
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime

# Project root
ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "app" / "static"
DIST_DIR = ROOT / "dist"
BUILD_VERSION = datetime.now().strftime("%Y%m%d%H%M%S")

def get_file_hash(content):
    """Generate SHA256 hash of file content"""
    return hashlib.sha256(content.encode()).hexdigest()[:8]

def minify_js(content):
    """Basic JS minification (remove comments, extra whitespace)"""
    # Remove single-line comments
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'\s*{\s*', '{', content)
    content = re.sub(r'\s*}\s*', '}', content)
    content = re.sub(r'\s*;\s*', ';', content)
    return content.strip()

def minify_css(content):
    """Basic CSS minification"""
    # Remove comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'\s*{\s*', '{', content)
    content = re.sub(r'\s*}\s*', '}', content)
    content = re.sub(r'\s*;\s*', ';', content)
    content = re.sub(r'\s*:\s*', ':', content)
    content = re.sub(r'\s*,\s*', ',', content)
    return content.strip()

def bundle_files(file_list, output_path, minify_func=None):
    """Bundle multiple files into one"""
    bundled = []
    for file_path in file_list:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if file_path.exists():
            content = file_path.read_text(encoding='utf-8')
            bundled.append(f"\n/* === {file_path.name} === */\n{content}\n")
        else:
            print(f"⚠️  Warning: File not found: {file_path}")
    
    bundled_content = "\n".join(bundled)
    
    # Minify if function provided
    if minify_func:
        bundled_content = minify_func(bundled_content)
    
    # Write bundled file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(bundled_content, encoding='utf-8')
    
    # Generate hash
    file_hash = get_file_hash(bundled_content)
    hashed_path = output_path.parent / f"{output_path.stem}.{file_hash}{output_path.suffix}"
    hashed_path.write_text(bundled_content, encoding='utf-8')
    
    return file_hash, hashed_path

def build_js_bundles():
    """Build JavaScript bundles"""
    print("📦 Building JS bundles...")
    
    bundles = {}
    
    # Core bundle
    core_files = [
        STATIC_DIR / "js" / "core" / "riskcast_data_store.js",
        STATIC_DIR / "js" / "core" / "utils.js",
        STATIC_DIR / "js" / "core" / "translations.js",
        STATIC_DIR / "js" / "core" / "streaming.js"
    ]
    
    core_hash, core_path = bundle_files(
        core_files,
        DIST_DIR / "js" / "core.bundle.min.js",
        minify_js
    )
    bundles['core'] = {
        'hash': core_hash,
        'path': f"js/{core_path.name}",
        'size': core_path.stat().st_size
    }
    
    # Modules bundle
    module_files = [
        STATIC_DIR / "js" / "modules" / "progress_tracker.js",
        STATIC_DIR / "js" / "modules" / "ai_chat.js",
        STATIC_DIR / "js" / "modules" / "ai_adviser.js",
        STATIC_DIR / "js" / "modules" / "enterprise_input.js",
        STATIC_DIR / "js" / "modules" / "smart_input.js",
        STATIC_DIR / "js" / "modules" / "input_summary.js"
    ]
    
    modules_hash, modules_path = bundle_files(
        module_files,
        DIST_DIR / "js" / "modules.bundle.min.js",
        minify_js
    )
    bundles['modules'] = {
        'hash': modules_hash,
        'path': f"js/{modules_path.name}",
        'size': modules_path.stat().st_size
    }
    
    # Page bundles
    page_files_map = {
        'home': [STATIC_DIR / "js" / "pages" / "home.js"],
        'input': [STATIC_DIR / "js" / "pages" / "input.js"],
        'results': [STATIC_DIR / "js" / "pages" / "results.js"],
        'dashboard': [STATIC_DIR / "js" / "pages" / "dashboard.js"],
        'overview': [STATIC_DIR / "js" / "pages" / "overview.js"],
        'booking_summary': [STATIC_DIR / "js" / "pages" / "booking_summary.js"]
    }
    
    for page_name, files in page_files_map.items():
        if all(f.exists() for f in files):
            page_hash, page_path = bundle_files(
                files,
                DIST_DIR / "js" / f"{page_name}.bundle.min.js",
                minify_js
            )
            bundles[page_name] = {
                'hash': page_hash,
                'path': f"js/{page_path.name}",
                'size': page_path.stat().st_size
            }
    
    print(f"✅ Created {len(bundles)} JS bundles")
    return bundles

def build_css_bundles():
    """Build CSS bundles"""
    print("📦 Building CSS bundles...")
    
    bundles = {}
    
    # Core CSS bundle (base + layout + components)
    core_css_files = [
        STATIC_DIR / "css" / "base" / "variables.css",
        STATIC_DIR / "css" / "base" / "reset.css",
        STATIC_DIR / "css" / "base" / "typography.css",
        STATIC_DIR / "css" / "base" / "mixins.css",
        STATIC_DIR / "css" / "layout" / "grid.css",
        STATIC_DIR / "css" / "layout" / "navbar.css",
        STATIC_DIR / "css" / "layout" / "sidebar.css",
        STATIC_DIR / "css" / "layout" / "layout_frame.css",
        STATIC_DIR / "css" / "components" / "buttons.css",
        STATIC_DIR / "css" / "components" / "cards.css",
        STATIC_DIR / "css" / "components" / "chips.css",
        STATIC_DIR / "css" / "components" / "forms.css",
        STATIC_DIR / "css" / "components" / "stats_card.css",
        STATIC_DIR / "css" / "components" / "ai_panel.css",
        STATIC_DIR / "css" / "components" / "modals.css",
        STATIC_DIR / "css" / "components" / "progress_tracker.css"
    ]
    
    core_css_hash, core_css_path = bundle_files(
        core_css_files,
        DIST_DIR / "css" / "core.bundle.min.css",
        minify_css
    )
    bundles['core'] = {
        'hash': core_css_hash,
        'path': f"css/{core_css_path.name}",
        'size': core_css_path.stat().st_size
    }
    
    # Page-specific CSS bundles
    page_css_map = {
        'home': [STATIC_DIR / "css" / "home-optimized.css"],
        'input': [
            STATIC_DIR / "css" / "input.css",
            STATIC_DIR / "css" / "input_inline.css",
            STATIC_DIR / "css" / "transport_setup_refactor.css",
            STATIC_DIR / "css" / "smart_input_styles.css",
            STATIC_DIR / "css" / "enterprise_input_layout.css",
            STATIC_DIR / "css" / "packing_list.css",
            STATIC_DIR / "css" / "navigation.css"
        ],
        'results': [
            STATIC_DIR / "css" / "results.css",
            STATIC_DIR / "css" / "results_v16.css",
            STATIC_DIR / "css" / "booking_summary.css"
        ],
        'dashboard': [
            STATIC_DIR / "css" / "pages" / "dashboard.css",
            STATIC_DIR / "css" / "theme" / "particles.css"
        ],
        'overview': [STATIC_DIR / "css" / "overview.css"]
    }
    
    for page_name, files in page_css_map.items():
        existing_files = [f for f in files if f.exists()]
        if existing_files:
            page_hash, page_path = bundle_files(
                existing_files,
                DIST_DIR / "css" / f"{page_name}.bundle.min.css",
                minify_css
            )
            bundles[page_name] = {
                'hash': page_hash,
                'path': f"css/{page_path.name}",
                'size': page_path.stat().st_size
            }
    
    print(f"✅ Created {len(bundles)} CSS bundles")
    return bundles

def create_version_json(js_bundles, css_bundles):
    """Create version.json with all bundle info"""
    version_data = {
        'version': BUILD_VERSION,
        'build_date': datetime.now().isoformat(),
        'js_bundles': js_bundles,
        'css_bundles': css_bundles,
        'cdn_url': os.getenv('CDN_URL', '/dist')
    }
    
    version_path = DIST_DIR / "version.json"
    version_path.write_text(json.dumps(version_data, indent=2), encoding='utf-8')
    print(f"✅ Created version.json")
    return version_data

def main():
    """Main build process"""
    print("🚀 Starting RISKCAST Production Build...")
    print(f"📁 Build version: {BUILD_VERSION}\n")
    
    # Create dist directories
    (DIST_DIR / "js").mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "css").mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "images").mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "fonts").mkdir(parents=True, exist_ok=True)
    
    # Build bundles
    js_bundles = build_js_bundles()
    css_bundles = build_css_bundles()
    
    # Create version.json
    version_data = create_version_json(js_bundles, css_bundles)
    
    # Summary
    print("\n" + "="*60)
    print("✅ BUILD COMPLETE!")
    print("="*60)
    print(f"\n📦 JS Bundles: {len(js_bundles)}")
    print(f"📦 CSS Bundles: {len(css_bundles)}")
    print(f"📁 Output: {DIST_DIR}")
    print(f"\n📄 Version file: dist/version.json")
    print("\n✨ Ready for production deployment!")

if __name__ == "__main__":
    main()





















