"""
RISKCAST Build Helper
Loads version.json and provides bundle paths for templates
"""

import json
from pathlib import Path
from typing import Dict, Optional

# Load version data
VERSION_FILE = Path(__file__).parent.parent.parent / "dist" / "version.json"
VERSION_DATA: Optional[Dict] = None
CDN_URL: str = "/dist"

def load_version_data():
    """Load version.json data"""
    global VERSION_DATA
    if VERSION_DATA is None and VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                VERSION_DATA = json.load(f)
                global CDN_URL
                if VERSION_DATA is not None:
                    CDN_URL = VERSION_DATA.get('cdn_url', '/dist')
        except Exception as e:
            print(f"⚠️  Could not load version.json: {e}")
            VERSION_DATA = {}
    return VERSION_DATA or {}

def get_js_bundle(bundle_name: str) -> str:
    """Get JS bundle path with hash"""
    version_data = load_version_data()
    js_bundles = version_data.get('js_bundles', {})
    
    if bundle_name in js_bundles:
        bundle_info = js_bundles[bundle_name]
        return f"{CDN_URL}/{bundle_info['path']}"
    
    # Fallback to development path
    return f"/static/js/{bundle_name}.js"

def get_css_bundle(bundle_name: str) -> str:
    """Get CSS bundle path with hash"""
    version_data = load_version_data()
    css_bundles = version_data.get('css_bundles', {})
    
    if bundle_name in css_bundles:
        bundle_info = css_bundles[bundle_name]
        return f"{CDN_URL}/{bundle_info['path']}"
    
    # Fallback to development path
    return f"/static/css/{bundle_name}.css"

def get_cdn_url() -> str:
    """Get CDN URL"""
    version_data = load_version_data()
    return version_data.get('cdn_url', '/dist')

def get_build_version() -> str:
    """Get build version"""
    version_data = load_version_data()
    return version_data.get('version', 'dev')




