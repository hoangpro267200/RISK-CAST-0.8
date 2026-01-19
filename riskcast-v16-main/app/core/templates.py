# app/core/templates.py
# Shared Jinja2Templates instance for the entire application
from starlette.templating import Jinja2Templates
from pathlib import Path
from jinja2 import pass_context

# Setup templates - SINGLE INSTANCE for entire app
BASE_DIR = Path(__file__).resolve().parent.parent  # nằm trong /app
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Add url_for helper for static files (FastAPI's url_for doesn't work with StaticFiles mount)
original_url_for = templates.env.globals.get('url_for')

@pass_context
def url_for(context: dict, name: str, **path_params):
    """Custom url_for that handles static files - only override for 'static' endpoint"""
    if name == 'static':
        filename = path_params.get('filename', '')
        return f"/static/{filename}"
    # For all other routes, use FastAPI's native url_for
    if original_url_for:
        try:
            return original_url_for(context, name, **path_params)
        except Exception:
            # Fallback to simple path if url_for fails
            return f"/{name}"
    return f"/{name}"

templates.env.globals['url_for'] = url_for







