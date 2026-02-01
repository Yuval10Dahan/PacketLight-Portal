from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import datetime
import subprocess
import sys
import shutil
import tempfile
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Union, Optional
import os
import importlib.util


app = FastAPI(title="PacketLight Company Portal")



# ----------------------------
# URLs
# ----------------------------
LATENCY_URL = "https://latency-dashboard-file.streamlit.app/"
APS_URL = "https://aps-dashboard-file.streamlit.app/"

# ----------------------------
# Paths
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
REQUIREMENTS_DIR = BASE_DIR / "requirements_documents"

HW_TOOLS_RELEASE_DIR = Path(r"\\vs1\PacketLight\PacketLight Documentation Hub\GUI\Release")
HW_TOOLS_RELEASE_ZIP_NAME = "PacketLight_Documentation_Hub_Release.zip"
PACKETLIGHT_DOCUMENTATION_HUB_CREATOR = "Andrey Litvinenko"

LAB_NETWORKS = [
    "172.16.20.0",
    "172.16.30.0",
    "172.16.40.0",
]

# ----------------------------
# Mount static (portal)
# ----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ----------------------------
# Mount GUIQC frontend build (served by portal)
# You must copy GUIQC frontend build output into: static/guiqc/
# ----------------------------
app.mount(
    "/sw-test-progress/guiqc",
    StaticFiles(directory="static/guiqc", html=True),
    name="guiqc",
)



def _try_merge_guiqc_backend() -> None:
    """
    Merge GUIQC backend into Portal process safely (no 'main' name collisions).

    It loads GUIQC/backend/main.py by absolute path and then:
      - if it exposes `router` -> include_router(router)
      - elif it exposes `app`   -> copy its routes into portal
    """
    guiqc_backend_dir = BASE_DIR / "GUIQC" / "backend"
    backend_file = guiqc_backend_dir / "main.py"

    print(f"[GUIQC] backend dir = {guiqc_backend_dir}")

    if not backend_file.exists():
        print(f"[GUIQC] backend main.py not found: {backend_file}")
        return

    print("[GUIQC] importing GUIQC backend main.py ...")

    try:
        spec = importlib.util.spec_from_file_location("guiqc_backend_main", str(backend_file))
        if spec is None or spec.loader is None:
            print("[GUIQC] failed to create import spec")
            return

        guiqc_backend_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guiqc_backend_main)

        print("[GUIQC] import done ✅")
    except Exception as e:
        print(f"[GUIQC] failed to import GUIQC backend: {e}")
        return

    # Case 1: router exists
    router = getattr(guiqc_backend_main, "router", None)
    if router is not None:
        try:
            app.include_router(router)
            print("[GUIQC] backend merged via router ✅")
            return
        except Exception as e:
            print(f"[GUIQC] include_router failed: {e}")

    # Case 2: FastAPI app exists
    sub_app = getattr(guiqc_backend_main, "app", None)
    if sub_app is not None and hasattr(sub_app, "router"):
        try:
            for r in sub_app.router.routes:
                app.router.routes.append(r)
            print("[GUIQC] backend merged by copying routes ✅")
            return
        except Exception as e:
            print(f"[GUIQC] failed to copy backend routes: {e}")

    print("[GUIQC] backend merge failed (no router/app detected) ❌")



# Merge GUIQC backend routes into portal (non-blocking startup)
try:
    _try_merge_guiqc_backend()
except Exception as e:
    print(f"[GUIQC] merge failed: {e}")

# ============================================================
# IMPORTANT DESIGN DECISION:
# GUIQC expects its backend at /api/...
# Your portal also had /api/... endpoints.
#
# To avoid collisions:
#   - GUIQC keeps /api/...
#   - Portal APIs move to /portal-api/...
# ============================================================
PORTAL_API_PREFIX = "/portal-api"


# ----------------------------
# Requirements Docs (CONFIG)
# ----------------------------
FEATURE_VERSION_TRACKING_SELECT_VALUE = "__select__"

FEATURE_VERSION_TRACKING_HEADLINES = [
    "Change log",
    "Front Panel View",
    "Interoperability with other devices",
    "PL-4000G – PL-4000T Interoperability",
    "GA - Version Uplink supported",
    "GA - Client supported",
    "GA - Feature added",
    "Modern Version - Uplink supported",
    "Modern Version - Client supported",
    "Modern Version - Feature supported",
    "Future Version",
]

FEATURE_VERSION_TRACKING_DEVICES = [
    "PL-4000T",
]

FEATURE_VERSION_TRACKING_CONTENT: Dict[str, Dict[str, str]] = {
    "PL-4000T": {
        "Change log": """
            <div class="muted">
              Rev 1.0 (11 December 2025) – Initial release version
            </div>
        """,
        "Front Panel View": """
            <div class="muted">
              (placeholder) Add front panel summary here.
            </div>
        """,
        "Interoperability with other devices": """
            <div class="muted">
              (placeholder) Add interoperability summary here.
            </div>
        """,
        "PL-4000G – PL-4000T Interoperability": """
            <div class="muted">
              (placeholder) Add PL-4000G ↔ PL-4000T details here.
            </div>
        """,
        "GA - Version Uplink supported": "<div class='muted'>(placeholder)</div>",
        "GA - Client supported": "<div class='muted'>(placeholder)</div>",
        "GA - Feature added": "<div class='muted'>(placeholder)</div>",
        "Modern Version - Uplink supported": "<div class='muted'>(placeholder)</div>",
        "Modern Version - Client supported": "<div class='muted'>(placeholder)</div>",
        "Modern Version - Feature supported": "<div class='muted'>(placeholder)</div>",
        "Future Version": "<div class='muted'>(placeholder)</div>",
    }
}

REQ_SELECT_VALUE = "__select__"

REQ_DEVICES = [
    "PL-1000D",
    "PL-1000G IL",
    "PL-1000GR",
    "PL-1000IL",
    "PL-1000R",
    "PL-1000TN",
    "PL-2000FC",
    "PL-2000M",
    "PL-2000T",
    "PL-4000G",
    "PL-4000M",
    "PL-4000T",
    "PL-8000G",
    "PL-8000M",
    "PL-8000T",
]

REQ_URLS: Dict[str, Union[str, Path]] = {
    "PL-1000D":  r"\\vs1\PacketLight\System\PL-1000D",
    "PL-1000G IL": r"\\vs1\PacketLight\System\PL-1000G",
    "PL-1000GR": r"\\vs1\PacketLight\System\PL-1000GR",
    "PL-1000IL": r"\\vs1\PacketLight\System\PL-1000IL",
    "PL-1000R":  r"\\vs1\PacketLight\System\PL-1000R",
    "PL-1000TN": r"\\vs1\PacketLight\System\PL-1000TN",
    "PL-2000FC": r"\\vs1\PacketLight\System\PL-2000FC",
    "PL-2000M":  r"\\vs1\PacketLight\System\PL-2000M",
    "PL-2000T":  r"\\vs1\PacketLight\System\PL-2000T",
    "PL-4000G":  r"\\vs1\PacketLight\System\PL-4000G",
    "PL-4000M":  r"\\vs1\PacketLight\System\PL-4000M",
    "PL-4000T":  r"\\vs1\PacketLight\System\PL-4000T",
    "PL-8000G":  r"\\vs1\PacketLight\System\PL-8000G",
    "PL-8000M":  r"\\vs1\PacketLight\System\PL-8000M",
    "PL-8000T":  r"\\vs1\PacketLight\System\PL-8000T",
}

# ----------------------------
# Products-LAB cache (in-memory)
# ----------------------------
PRODUCTS_LAB_CACHE: Dict[str, Any] = {
    "data": {},          # Dict[str, List[str]]
    "scanned_at": None,  # datetime.datetime or None
    "error": None,       # str or None
}

# ----------------------------
# Helpers
# ----------------------------
def page_html(title: str, body_html: str) -> HTMLResponse:
    return HTMLResponse(f"""
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
          <header class="top portal-header">
            <a class="brand" href="/">PacketLight Portal</a>
          </header>
          <main class="card">
            <h1>{title}</h1>
            {body_html}
            <div class="actions" style="margin-top:18px">
              <a class="btn" href="/">← Back to Home</a>
            </div>
          </main>
        </div>
      </body>
    </html>
    """)


# ----------------------------
# Requirements doc picker
# ----------------------------
REQ_KEYWORDS = ("system requirements", "requirements", "system")   # case-insensitive
DOC_EXTS = (".doc", ".docx", ".docm", ".ppt", ".pptx", ".pptm")

def device_name_variants(device: str) -> List[str]:
    d = device.strip().lower()
    no_dash = d.replace("-", "")
    no_space = d.replace(" ", "")
    no_dash_no_space = no_dash.replace(" ", "")
    dash_no_space = d.replace(" ", "")
    variants = [d, no_dash, no_space, no_dash_no_space, dash_no_space]
    out = []
    for v in variants:
        if v and v not in out:
            out.append(v)
    return out

def pick_newest_requirements_doc(folder: Path, device: str) -> Optional[Path]:
    if not folder.exists() or not folder.is_dir():
        return None

    keywords = [k.lower() for k in REQ_KEYWORDS]
    exts = {e.lower() for e in DOC_EXTS}
    variants = device_name_variants(device)

    candidates: List[Path] = []
    for p in folder.iterdir():
        if not p.is_file():
            continue
        if p.name.startswith("~$"):
            continue
        if p.suffix.lower() not in exts:
            continue

        name = p.name.lower()
        if not any(v in name for v in variants):
            continue
        if not any(k in name for k in keywords):
            continue
        candidates.append(p)

    if not candidates:
        return None

    return max(candidates, key=lambda x: x.stat().st_mtime)


# ----------------------------
# SNMP subprocess runner
# ----------------------------
def run_snmp_scan(network: str) -> List[Tuple[str, str]]:
    cmd = [
        sys.executable,
        "snmp_scan.py",
        "-n", network,
        "-v", "2c",
        "-c", "admin",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    rows = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("IP") or line.startswith("-"):
            continue
        parts = line.split()
        rows.append((parts[0], " ".join(parts[1:])))
    return rows

def perform_products_lab_scan() -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = defaultdict(list)

    for net in LAB_NETWORKS:
        for ip, product in run_snmp_scan(net):
            grouped[product].append(ip)

    for product in grouped:
        grouped[product].sort(key=lambda x: tuple(map(int, x.split("."))))

    return dict(grouped)


# ============================================================
# GUIQC BACKEND MERGE (Solution 1)
# - We import GUIQC backend module and "attach" its routes into this app.
# - After this, GUIQC /api/... endpoints are handled by the portal process.
# ============================================================



# ----------------------------
# ROUTES
# ----------------------------
@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.get("/go/latency")
def go_latency():
    return RedirectResponse(LATENCY_URL)


@app.get("/go/aps")
def go_aps():
    return RedirectResponse(APS_URL)


@app.get("/assembly")
def assembly_page():
    return page_html("Assembly", "<p class='muted'>Placeholder page.</p>")


@app.get("/ga-versions")
def ga_versions_page():
    return page_html("GA Versions", "<p class='muted'>Placeholder page.</p>")


@app.get("/sw-test-progress")
def sw_test_progress_page():
    # Production path (served by portal)
    body = """
    <div class="swtp-page">
      <div class="card swtp-wide" style="height:90vh; overflow:hidden; padding:0;">
        <iframe
          src="/sw-test-progress/guiqc/"
          style="width:100%; height:100%; border:0; display:block;"
          loading="lazy"
        ></iframe>
      </div>
    </div>
    """
    return page_html("SW Test Progress", body)


# ============================================================
# PORTAL APIs (moved to /portal-api to avoid collision with GUIQC /api)
# ============================================================

# ----------------------------
# Requirements Docs (UI)
# ----------------------------
@app.get("/requirements-docs")
def requirements_docs_page():
    body = f"""
      <p class="muted">
        Select a device to download its <b>Requirements Document</b> file.
      </p>

      <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end; margin-top:12px;">
        <div style="display:flex; flex-direction:column; gap:6px; min-width:260px;">
          <span class="muted" style="font-size:12px;">Device</span>
          <select id="reqDlDevice" class="btn"></select>
        </div>

        <button id="reqDlBtn" class="btn" type="button" style="cursor:pointer;" disabled>
          ⬇ Download
        </button>
      </div>

      <p class="muted" id="reqDlStatus" style="margin-top:12px;"></p>

      <script>
        const SELECT_VALUE = "{REQ_SELECT_VALUE}";
        const deviceSel = document.getElementById("reqDlDevice");
        const dlBtn = document.getElementById("reqDlBtn");
        const status = document.getElementById("reqDlStatus");

        function setStatus(txt) {{
          status.textContent = txt || "";
        }}

        function populateDevices(devices) {{
          deviceSel.innerHTML = "";

          const opt0 = document.createElement("option");
          opt0.value = SELECT_VALUE;
          opt0.textContent = "Select";
          deviceSel.appendChild(opt0);

          (devices || []).forEach(d => {{
            const opt = document.createElement("option");
            opt.value = d;
            opt.textContent = d;
            deviceSel.appendChild(opt);
          }});

          deviceSel.value = SELECT_VALUE;
          dlBtn.disabled = true;
          setStatus("Select a device.");
        }}

        fetch("{PORTAL_API_PREFIX}/requirements-docs/devices")
          .then(r => r.json())
          .then(devices => {{
            populateDevices(devices);
          }})
          .catch(() => {{
            setStatus("Failed to load devices.");
          }});

        deviceSel.addEventListener("change", () => {{
          const dev = deviceSel.value;
          if (dev === SELECT_VALUE) {{
            dlBtn.disabled = true;
            setStatus("Select a device.");
            return;
          }}
          dlBtn.disabled = false;
          setStatus("Ready to download: " + dev);
        }});

        dlBtn.addEventListener("click", () => {{
          const dev = deviceSel.value;
          if (!dev || dev === SELECT_VALUE) return;

          setStatus("Starting download for: " + dev);
          window.location.href = "{PORTAL_API_PREFIX}/requirements-docs/download?device=" + encodeURIComponent(dev);
        }});
      </script>
    """
    return page_html("Requirements", body)


@app.get(f"{PORTAL_API_PREFIX}/requirements-docs/devices")
def req_docs_devices():
    return JSONResponse(sorted(REQ_DEVICES))


@app.get(f"{PORTAL_API_PREFIX}/requirements-docs/download")
def req_docs_download(device: str):
    if not device or device == REQ_SELECT_VALUE:
        raise HTTPException(400, "Missing device")

    raw: Union[str, Path, None] = REQ_URLS.get(device)
    if not raw:
        raise HTTPException(404, f"No document configured for device: {device}")

    p = Path(raw)

    if p.exists() and p.is_dir():
        chosen = pick_newest_requirements_doc(p, device)
        if not chosen:
            raise HTTPException(
                404,
                f"No matching {DOC_EXTS} found containing {REQ_KEYWORDS} in: {p}"
            )
        p = chosen

    if not p.exists() or not p.is_file():
        raise HTTPException(404, f"File not found: {p}")

    return FileResponse(
        p,
        filename=p.name,
        media_type="application/octet-stream",
    )


# ----------------------------
# Feature - Version Tracking (UI)
# ----------------------------
@app.get("/feature-version-tracking")
def feature_version_tracking_page():
    body = f"""
    <p class="muted">Select a device and a headline to view the summarized content.</p>

    <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-top:12px;">
      <div style="display:flex; flex-direction:column; gap:6px;">
        <span class="muted" style="font-size:12px;">Device</span>
        <select id="reqDevice" class="btn"></select>
      </div>

      <div style="display:flex; flex-direction:column; gap:6px;">
        <span class="muted" style="font-size:12px;">Headline</span>
        <select id="reqHeadline" class="btn" disabled></select>
      </div>
    </div>

    <div id="reqContent"
         style="margin-top:14px; padding:14px; border-radius:14px;
                border:1px solid rgba(255,255,255,0.08); min-height:80px;">
      <div class="muted">No selection.</div>
    </div>

    <script>
      const SELECT_VALUE = "{FEATURE_VERSION_TRACKING_SELECT_VALUE}";

      const deviceSel = document.getElementById("reqDevice");
      const headSel   = document.getElementById("reqHeadline");
      const content   = document.getElementById("reqContent");

      function setContent(html) {{
        content.innerHTML = html || "<div class='muted'>No content.</div>";
      }}

      function resetHeadline() {{
        headSel.innerHTML = "";
        const opt = document.createElement("option");
        opt.value = SELECT_VALUE;
        opt.textContent = "Select";
        headSel.appendChild(opt);
        headSel.value = SELECT_VALUE;
        headSel.disabled = true;
      }}

      function resetAll() {{
        resetHeadline();
        setContent("<div class='muted'>No selection.</div>");
      }}

      function populateDevices(devices) {{
        deviceSel.innerHTML = "";
        const opt0 = document.createElement("option");
        opt0.value = SELECT_VALUE;
        opt0.textContent = "Select";
        deviceSel.appendChild(opt0);

        devices.forEach(d => {{
          const opt = document.createElement("option");
          opt.value = d;
          opt.textContent = d;
          deviceSel.appendChild(opt);
        }});

        deviceSel.value = SELECT_VALUE;
      }}

      function populateHeadlines(headlines) {{
        headSel.innerHTML = "";
        const opt0 = document.createElement("option");
        opt0.value = SELECT_VALUE;
        opt0.textContent = "Select";
        headSel.appendChild(opt0);

        headlines.forEach(h => {{
          const opt = document.createElement("option");
          opt.value = h;
          opt.textContent = h;
          headSel.appendChild(opt);
        }});

        headSel.value = SELECT_VALUE;
        headSel.disabled = false;
      }}

      fetch("{PORTAL_API_PREFIX}/feature-version-tracking/devices")
        .then(r => r.json())
        .then(devices => {{
          populateDevices(devices);
          resetAll();
        }})
        .catch(() => {{
          setContent("<div class='muted'>Failed to load devices.</div>");
        }});

      deviceSel.addEventListener("change", () => {{
        const dev = deviceSel.value;

        if (dev === SELECT_VALUE) {{
          resetAll();
          return;
        }}

        setContent("<div class='muted'>Select a headline.</div>");
        fetch("{PORTAL_API_PREFIX}/feature-version-tracking/headlines?device=" + encodeURIComponent(dev))
          .then(r => r.json())
          .then(headlines => {{
            populateHeadlines(headlines);
            setContent("<div class='muted'>Select a headline.</div>");
          }})
          .catch(() => {{
            resetAll();
            setContent("<div class='muted'>Failed to load headlines.</div>");
          }});
      }});

      headSel.addEventListener("change", () => {{
        const dev = deviceSel.value;
        const h = headSel.value;

        if (h === SELECT_VALUE) {{
          setContent("<div class='muted'>Select a headline.</div>");
          return;
        }}

        setContent("<div class='muted'>Loading...</div>");
        fetch("{PORTAL_API_PREFIX}/feature-version-tracking/content?device=" + encodeURIComponent(dev) + "&headline=" + encodeURIComponent(h))
          .then(r => r.json())
          .then(obj => {{
            setContent(obj.html || "<div class='muted'>No content.</div>");
          }})
          .catch(() => {{
            setContent("<div class='muted'>Failed to load content.</div>");
          }});
      }});
    </script>
    """
    return page_html("Feature - Version Tracking", body)


@app.get(f"{PORTAL_API_PREFIX}/feature-version-tracking/devices")
def fvt_devices():
    return JSONResponse(sorted(FEATURE_VERSION_TRACKING_DEVICES))


@app.get(f"{PORTAL_API_PREFIX}/feature-version-tracking/headlines")
def fvt_headlines(device: str):
    if not device or device == FEATURE_VERSION_TRACKING_SELECT_VALUE:
        return JSONResponse([])
    return JSONResponse(FEATURE_VERSION_TRACKING_HEADLINES)


@app.get(f"{PORTAL_API_PREFIX}/feature-version-tracking/content")
def fvt_content(device: str, headline: str):
    if not device or device == FEATURE_VERSION_TRACKING_SELECT_VALUE:
        return JSONResponse({"html": ""})
    if not headline or headline == FEATURE_VERSION_TRACKING_SELECT_VALUE:
        return JSONResponse({"html": ""})

    html = FEATURE_VERSION_TRACKING_CONTENT.get(device, {}).get(headline, "")
    return JSONResponse({"html": html})


# ----------------------------
# PRODUCTS - LAB PAGE (UI)
# ----------------------------
@app.get("/products-lab")
def products_lab_page():
    body = f"""
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
            <button id="refreshBtn" class="btn" type="button" style="cursor:pointer;">
            📡 Scan Devices
            </button>

            <span class="muted" id="meta" style="font-size:12px;"></span>
        </div>

        <p class="muted" id="status" style="margin-top:10px; margin-bottom:8px;">
            Loading last scan...
        </p>

        <select id="productSelect" class="btn" style="display:none; margin-bottom:12px;"></select>

        <ul id="ipList" style="margin-top:10px;"></ul>

        <script>
            const SELECT_PLACEHOLDER_VALUE = "__select__";

            function renderIPs(data) {{
              const select = document.getElementById('productSelect');
              const list = document.getElementById('ipList');
              const chosen = select.value;

              list.innerHTML = '';
              if (chosen === SELECT_PLACEHOLDER_VALUE) return;

              (data[chosen] || []).forEach(ip => {{
                  const li = document.createElement('li');
                  li.textContent = ip;
                  list.appendChild(li);
              }});
            }}

            function populateProducts(data) {{
              const status = document.getElementById('status');
              const select = document.getElementById('productSelect');

              select.innerHTML = "";

              const keys = Object.keys(data || {{}});
              if (!keys.length) {{
                  select.style.display = "none";
                  document.getElementById('ipList').innerHTML = "";
                  status.textContent = "No cached scans yet.";
                  return;
              }}

              status.textContent = "Select product:";
              select.style.display = "inline-block";

              const placeholder = document.createElement('option');
              placeholder.value = SELECT_PLACEHOLDER_VALUE;
              placeholder.textContent = 'Select';
              placeholder.selected = true;
              select.appendChild(placeholder);

              keys.sort().forEach(product => {{
                  const opt = document.createElement('option');
                  opt.value = product;
                  opt.textContent = product;
                  select.appendChild(opt);
              }});

              select.onchange = () => renderIPs(data);
              select.value = SELECT_PLACEHOLDER_VALUE;
              renderIPs(data);
            }}

            function setMeta(scannedAt, err) {{
              const meta = document.getElementById('meta');
              if (!scannedAt && !err) {{
                  meta.textContent = "";
                  return;
              }}

              let txt = scannedAt ? ("Last scan: " + scannedAt) : "";
              if (err) txt += (txt ? " • " : "") + ("Error: " + err);
              meta.textContent = txt;
            }}

            function loadCached() {{
              const status = document.getElementById('status');
              status.textContent = "Loading last scan...";
              setMeta("", "");

              fetch('{PORTAL_API_PREFIX}/products-lab/cached')
                  .then(r => r.json())
                  .then(obj => {{
                    setMeta(obj.scanned_at, obj.error);

                    if (obj.error) {{
                        status.textContent = "Last scan had an error. You can Refresh.";
                    }}

                    populateProducts(obj.data || {{}});
                  }})
                  .catch(() => {{
                    status.textContent = "Failed to load cached scan.";
                    setMeta("", "");
                  }});
            }}

            function refreshScan() {{
              const status = document.getElementById('status');
              const select = document.getElementById('productSelect');
              const list = document.getElementById('ipList');

              status.textContent = "Scanning Alpha Lab devices - Wait around 20 seconds...";

              select.style.display = "none";
              select.innerHTML = "";
              list.innerHTML = "";

              fetch('{PORTAL_API_PREFIX}/products-lab/scan?force=1')
                  .then(r => r.json())
                  .then(obj => {{
                    setMeta(obj.scanned_at, obj.error);

                    if (obj.error) {{
                        status.textContent = "Scan failed. Showing last available cache (if exists).";
                    }}

                    populateProducts(obj.data || {{}});
                  }})
                  .catch(() => {{
                    status.textContent = "Scan failed.";
                  }});
            }}

            document.getElementById('refreshBtn').addEventListener('click', refreshScan);

            loadCached();
        </script>
        """
    return page_html("Products - LAB", body)


@app.get(f"{PORTAL_API_PREFIX}/products-lab/cached")
def products_lab_cached():
    scanned_at = PRODUCTS_LAB_CACHE["scanned_at"]
    return JSONResponse({
        "data": PRODUCTS_LAB_CACHE["data"] or {},
        "scanned_at": scanned_at.isoformat(sep=" ", timespec="seconds") if scanned_at else None,
        "error": PRODUCTS_LAB_CACHE["error"],
    })


@app.get(f"{PORTAL_API_PREFIX}/products-lab/scan")
def products_lab_scan(force: int = 0):
    if not force:
        scanned_at = PRODUCTS_LAB_CACHE["scanned_at"]
        return JSONResponse({
            "data": PRODUCTS_LAB_CACHE["data"] or {},
            "scanned_at": scanned_at.isoformat(sep=" ", timespec="seconds") if scanned_at else None,
            "error": PRODUCTS_LAB_CACHE["error"],
        })

    try:
        data = perform_products_lab_scan()
        PRODUCTS_LAB_CACHE["data"] = data
        PRODUCTS_LAB_CACHE["scanned_at"] = datetime.datetime.now()
        PRODUCTS_LAB_CACHE["error"] = None
    except Exception as e:
        PRODUCTS_LAB_CACHE["error"] = str(e)

    scanned_at = PRODUCTS_LAB_CACHE["scanned_at"]
    return JSONResponse({
        "data": PRODUCTS_LAB_CACHE["data"] or {},
        "scanned_at": scanned_at.isoformat(sep=" ", timespec="seconds") if scanned_at else None,
        "error": PRODUCTS_LAB_CACHE["error"],
    })


# ----------------------------
# HW TOOLS
# ----------------------------
@app.get("/download/hw-tools")
def download_hw_tools():
    if not HW_TOOLS_RELEASE_DIR.exists() or not HW_TOOLS_RELEASE_DIR.is_dir():
        raise HTTPException(404, "HW Tools Release folder not found")

    tmp_dir = Path(tempfile.mkdtemp())
    zip_path = tmp_dir / HW_TOOLS_RELEASE_ZIP_NAME

    shutil.make_archive(
        base_name=str(zip_path.with_suffix("")),
        format="zip",
        root_dir=HW_TOOLS_RELEASE_DIR,
    )

    return FileResponse(
        zip_path,
        filename=HW_TOOLS_RELEASE_ZIP_NAME,
        media_type="application/zip",
    )


@app.get("/hw-tools")
def hw_tools_page():
    if not HW_TOOLS_RELEASE_DIR.exists():
        return page_html("HW Tools", "<p class='muted'>Release folder not found.</p>")

    return page_html("HW Tools", f"""
      <div class="muted">
        <div><b>Package:</b> PacketLight Documentation Hub Release</div>
        <div><b>Source:</b> \\\\vs1\\PacketLight\\PacketLight Documentation Hub\\GUI\\Release</div>
        <div><b>Creator:</b> {PACKETLIGHT_DOCUMENTATION_HUB_CREATOR}</div>
      </div>
      <div class="actions" style="margin-top:14px">
        <a class="btn" href="/download/hw-tools">⬇ Download Release (ZIP)</a>
      </div>
    """)
