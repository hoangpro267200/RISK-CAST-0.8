from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI(title="RISKCAST v35")


BASE_DIR = Path(__file__).resolve().parent
PRICING_UI_DIR = BASE_DIR / "ui" / "pricing"


@app.get("/ui/pricing", response_class=HTMLResponse)
def serve_pricing_ui():
    return FileResponse(PRICING_UI_DIR / "pricing_dashboard.html")


@app.get("/ui/pricing/pricing_dashboard.css")
def serve_pricing_css():
    return FileResponse(PRICING_UI_DIR / "pricing_dashboard.css")


@app.get("/ui/pricing/pricing_dashboard.js")
def serve_pricing_js():
    return FileResponse(PRICING_UI_DIR / "pricing_dashboard.js")

