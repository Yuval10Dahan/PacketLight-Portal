from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import datetime
import hashlib

app = FastAPI(title="PacketLight Company Portal")

# ----------------------------
# Configure these URLs
# ----------------------------
LATENCY_URL = "https://latency-dashboard-file.streamlit.app/"
APS_URL = "https://aps-dashboard-file.streamlit.app/"

# ----------------------------
# Paths
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CSS_PATH = STATIC_DIR / "portal.css"

DOWNLOADS_DIR = BASE_DIR / "downloads"
HW_TOOLS_EXE_NAME = "PacketLight_Documentation_Hub.exe"
HW_TOOLS_EXE_PATH = DOWNLOADS_DIR / HW_TOOLS_EXE_NAME
PACKETLIGHT_DOCUMENTATION_HUB_CREATOR = "Andrey Litvinenko"

# Your logo file (make sure it exists in: static/images/packetlight_logo.png)
LOGO_SRC = "/static/images/packetlight_logo.png"


# ----------------------------
# Static files with NO-CACHE headers (dev-friendly)
# ----------------------------
class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)

        # Disable caching so you don't need to hard-refresh while developing
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app.mount("/static", NoCacheStaticFiles(directory=str(STATIC_DIR)), name="static")


# ----------------------------
# Helpers
# ----------------------------
def static_version() -> str:
    """
    Cache-busting token based on portal.css last modified time.
    """
    try:
        return str(int(CSS_PATH.stat().st_mtime))
    except FileNotFoundError:
        return "1"


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for u in units:
        if size < 1024 or u == units[-1]:
            if u == "B":
                return f"{int(size)} {u}"
            return f"{size:.2f} {u}"
        size /= 1024.0
    return f"{num_bytes} B"


def file_build_id(path: Path) -> str:
    """
    Returns a short ID derived from the file contents.
    This is a reliable 'version-like' identifier without needing Windows EXE metadata libs.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:10].upper()


def page_html(title: str, body_html: str) -> HTMLResponse:
    v = static_version()
    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{title} - PacketLight Portal</title>
        <link rel="stylesheet" href="/static/portal.css?v={v}" />
      </head>
      <body>
        <!-- Floating logo on ALL internal pages -->
        <div class="portal-logo" aria-label="PacketLight">
          <img src="{LOGO_SRC}?v={v}" alt="PacketLight Logo" />
        </div>

        <div class="wrap">
          <header class="top">
            <a class="brand" href="/">PacketLight Portal</a>
          </header>

          <main class="card">
            <h1>{title}</h1>
            {body_html}

            <div class="actions" style="margin-top: 18px;">
              <a class="btn" href="/">← Back to Home</a>
            </div>
          </main>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def root():
    # Home page
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/go/latency")
def go_latency():
    return RedirectResponse(url=LATENCY_URL, status_code=302)


@app.get("/go/aps")
def go_aps():
    return RedirectResponse(url=APS_URL, status_code=302)


@app.get("/download/hw-tools")
def download_hw_tools():
    if not HW_TOOLS_EXE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"HW Tools installer not found: {HW_TOOLS_EXE_PATH}"
        )

    return FileResponse(
        path=str(HW_TOOLS_EXE_PATH),
        media_type="application/octet-stream",
        filename=HW_TOOLS_EXE_NAME,
    )


@app.get("/assembly")
def assembly_page():
    body = '<p class="muted">Placeholder page. Add your content here later.</p>'
    return page_html("Assembly", body)


@app.get("/requirements-docs")
def requirements_docs_page():
    body = '<p class="muted">Placeholder page. Add your content here later.</p>'
    return page_html("Requirements Documents", body)


@app.get("/ga-versions")
def ga_versions_page():
    body = '<p class="muted">Placeholder page. Add your content here later.</p>'
    return page_html("GA Versions", body)


@app.get("/sw-test-progress")
def sw_test_progress_page():
    body = '<p class="muted">Placeholder page. Add your content here later.</p>'
    return page_html("SW Test Progress", body)


@app.get("/products-lab")
def products_lab_page():
    body = '<p class="muted">Placeholder page. Add your content here later.</p>'
    return page_html("Products - LAB", body)


@app.get("/hw-tools")
def hw_tools_page():
    if HW_TOOLS_EXE_PATH.exists():
        st = HW_TOOLS_EXE_PATH.stat()
        size_str = human_size(st.st_size)

        updated = datetime.datetime.fromtimestamp(st.st_mtime)
        updated_str = updated.strftime("%Y-%m-%d %H:%M:%S")

        build_id = file_build_id(HW_TOOLS_EXE_PATH)

        body = f"""
          <div class="metaBox">
            <div class="metaRow"><b>File:</b> {HW_TOOLS_EXE_NAME}</div>
            <div class="metaRow"><b>Version:</b> {build_id}</div>
            <div class="metaRow"><b>Size:</b> {size_str}</div>
            <div class="metaRow"><b>Last updated:</b> {updated_str}</div>
            <div class="metaRow"><b>Creator:</b> {PACKETLIGHT_DOCUMENTATION_HUB_CREATOR}</div>
          </div>

          <div class="actions">
            <a class="btn" href="/download/hw-tools">⬇ Download PacketLight Documentation Hub</a>
          </div>

          <p class="muted" style="margin-top: 12px; font-size: 12px;">
            If Windows blocks the file: Right click → Properties → Unblock (if available).
          </p>
        """
    else:
        body = f"""
          <p class="muted">HW Tools installer was not found on the server.</p>
          <p class="muted" style="font-size: 13px;">
            Expected path: <code>{HW_TOOLS_EXE_PATH}</code>
          </p>
        """

    return page_html("HW Tools", body)
