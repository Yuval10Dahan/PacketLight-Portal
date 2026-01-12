from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import datetime
import hashlib

app = FastAPI(title="PacketLight Company Portal")

# ----------------------------
# Configure these URLs
# ----------------------------
LATENCY_URL = "https://latency-dashboard-file.streamlit.app/"
APS_URL = "https://aps-dashboard-file.streamlit.app/"

# Serve static files (HTML/CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ----------------------------
# Downloads config
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"

HW_TOOLS_EXE_NAME = "PacketLight_Documentation_Hub.exe"  
HW_TOOLS_EXE_PATH = DOWNLOADS_DIR / HW_TOOLS_EXE_NAME
PACKETLIGHT_DOCUMENTATION_HUB_CREATOR = "Andrey Litvinenko"


# ----------------------------
# Helpers
# ----------------------------
def human_size(num_bytes: int) -> str:
    # Simple human-readable formatting
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
    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{title} - PacketLight Portal</title>
        <link rel="stylesheet" href="/static/portal.css" />
      </head>
      <body>
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
    return FileResponse("static/index.html")


# External redirects
@app.get("/go/latency")
def go_latency():
    return RedirectResponse(url=LATENCY_URL, status_code=302)


@app.get("/go/aps")
def go_aps():
    return RedirectResponse(url=APS_URL, status_code=302)


# ✅ Download endpoint (forces download)
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
        filename="PacketLight_Documentation_Hub.exe",
    )


# Internal pages
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


# ✅ HW Tools page with download + auto meta
@app.get("/hw-tools")
def hw_tools_page():
    if HW_TOOLS_EXE_PATH.exists():
        st = HW_TOOLS_EXE_PATH.stat()
        size_str = human_size(st.st_size)

        # show local server time
        updated = datetime.datetime.fromtimestamp(st.st_mtime)
        updated_str = updated.strftime("%Y-%m-%d %H:%M:%S")

        build_id = file_build_id(HW_TOOLS_EXE_PATH)

        meta_html = f"""
        <div style="margin-top: 10px; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px;">
          <div class="muted" style="font-size: 13px; line-height: 1.6;">
            <div><b>File:</b> {HW_TOOLS_EXE_NAME}</div>
            <div><b>Size:</b> {size_str}</div>
            <div><b>Last updated:</b> {updated_str}</div>
            <div><b>Creator:</b> {PACKETLIGHT_DOCUMENTATION_HUB_CREATOR}</div>
          </div>
        </div>
        """
        download_html = """
        <div class="actions" style="margin-top: 14px;">
          <a class="btn" href="/download/hw-tools">⬇ Download PacketLight Documentation Hub</a>
        </div>
        <p class="muted" style="margin-top: 12px; font-size: 12px;">
          If Windows blocks the file: Right click → Properties → Unblock (if available).
        </p>
        """
        body = f"""
          {meta_html}
          {download_html}
        """
    else:
        body = f"""
          <p class="muted">HW Tools installer was not found on the server.</p>
          <p class="muted" style="font-size: 13px;">
            Expected path: <code>{HW_TOOLS_EXE_PATH}</code>
          </p>
        """

    return page_html("HW Tools", body)
