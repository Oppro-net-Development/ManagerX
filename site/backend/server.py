from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

# FastAPI-Doku deaktiviert, da eigene Docs
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# --- Basisverzeichnisse ---
BASE_DIR = Path(__file__).parent.parent           # site/
SITE_STATIC = BASE_DIR / "static"                 # site/static
DOCS_DIR = BASE_DIR.parent / "docs" / "_build" / "html"  # docs/_build/html

# --- Statische Dateien mounten ---
app.mount("/static", StaticFiles(directory=SITE_STATIC), name="site_static")
app.mount("/documentation", StaticFiles(directory=DOCS_DIR), name="docs_static")

# --- Website-Routen ---
@app.get("/", response_class=HTMLResponse)
async def read_index():
    html_file = SITE_STATIC / "html" / "index.html"
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))

@app.get("/features", response_class=HTMLResponse)
async def read_features():
    html_file = SITE_STATIC / "html" / "features.html"
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))

# --- Redirect /documentation auf index.html ---
@app.get("/documentation")
async def redirect_docs():
    return RedirectResponse(url="/documentation/index.html")

@app.get("/documentation/userguide/")
async def redirect_docs_index():
    return RedirectResponse(url="/documentation/user_guide/index.html")

# --- Server starten ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
