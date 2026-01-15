from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import datetime
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Any

app = fastapi_app = FastAPI(title="PacketLight Company Portal")

# ----------------------------
# URLs
# ----------------------------
LATENCY_URL = "https://latency-dashboard-file.streamlit.app/"
APS_URL = "https://aps-dashboard-file.streamlit.app/"

app.mount("/static", StaticFiles(directory="static"), name="static")

# ----------------------------
# Paths
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"

HW_TOOLS_EXE_NAME = "PacketLight_Documentation_Hub.exe"
HW_TOOLS_EXE_PATH = DOWNLOADS_DIR / HW_TOOLS_EXE_NAME
PACKETLIGHT_DOCUMENTATION_HUB_CREATOR = "Andrey Litvinenko"

LAB_NETWORKS = [
    "172.16.20.0",
    "172.16.30.0",
    "172.16.40.0",
]

# ----------------------------
# Requirements Docs (CONFIG)
# ----------------------------
REQ_SELECT_VALUE = "__select__"

REQ_HEADLINES = [
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

REQ_DEVICES = [
    "PL-4000T",
]

REQ_CONTENT: Dict[str, Dict[str, str]] = {
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

# ----------------------------
# Feature - Version Tracking (CONFIG) ✅ NEW
# ----------------------------
FEATURE_SELECT_VALUE = "__select__"

# For now: only PL-1000IL. Add more later.
FEATURE_TRACKING_DEVICES = [
    "PL-1000IL",
]

# You will replace each URL with your real document URL per device.
# NOTE: This route will redirect the browser to this URL (download handled by that URL).
FEATURE_TRACKING_DOC_URLS: Dict[str, str] = {
    "PL-1000IL": "https://example.com/replace-me/pl-1000il-feature-version-tracking.docx",
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
def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{int(size)} {u}" if u == "B" else f"{size:.2f} {u}"
        size /= 1024.0
    return f"{num_bytes} B"


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
          <header class="top">
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

# ----------------------------
# Products-LAB scanning logic
# ----------------------------
def perform_products_lab_scan() -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = defaultdict(list)

    for net in LAB_NETWORKS:
        for ip, product in run_snmp_scan(net):
            grouped[product].append(ip)

    for product in grouped:
        grouped[product].sort(key=lambda x: tuple(map(int, x.split("."))))

    return dict(grouped)

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


# ----------------------------
# REQUIREMENTS DOCUMENTS (UI)
# ----------------------------
@app.get("/requirements-docs")
def requirements_docs_page():
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
      const SELECT_VALUE = "{REQ_SELECT_VALUE}";

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

      fetch("/api/requirements/devices")
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
        fetch("/api/requirements/headlines?device=" + encodeURIComponent(dev))
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
        fetch("/api/requirements/content?device=" + encodeURIComponent(dev) + "&headline=" + encodeURIComponent(h))
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
    return page_html("Requirements Documents", body)


# ----------------------------
# REQUIREMENTS DOCUMENTS (API)
# ----------------------------
@app.get("/api/requirements/devices")
def req_devices():
    return JSONResponse(sorted(REQ_DEVICES))


@app.get("/api/requirements/headlines")
def req_headlines(device: str):
    if not device or device == REQ_SELECT_VALUE:
        return JSONResponse([])
    return JSONResponse(REQ_HEADLINES)


@app.get("/api/requirements/content")
def req_content(device: str, headline: str):
    if not device or device == REQ_SELECT_VALUE:
        return JSONResponse({"html": ""})
    if not headline or headline == REQ_SELECT_VALUE:
        return JSONResponse({"html": ""})

    html = REQ_CONTENT.get(device, {}).get(headline, "")
    return JSONResponse({"html": html})


@app.get("/ga-versions")
def ga_versions_page():
    return page_html("GA Versions", "<p class='muted'>Placeholder page.</p>")


@app.get("/sw-test-progress")
def sw_test_progress_page():
    return page_html("SW Test Progress", "<p class='muted'>Placeholder page.</p>")


# ----------------------------
# FEATURE - VERSION TRACKING (UI) ✅ NEW
# ----------------------------
@app.get("/feature-version-tracking")
def feature_version_tracking_page():
    body = f"""
      <p class="muted">
        Select a device to download its <b>Feature - Version Tracking</b> document.
      </p>

      <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end; margin-top:12px;">
        <div style="display:flex; flex-direction:column; gap:6px; min-width:260px;">
          <span class="muted" style="font-size:12px;">Device</span>
          <select id="fvtDevice" class="btn"></select>
        </div>

        <button id="downloadBtn" class="btn" type="button" style="cursor:pointer;" disabled>
          ⬇ Download
        </button>
      </div>

      <p class="muted" id="fvtStatus" style="margin-top:12px;"></p>

      <script>
        const SELECT_VALUE = "{FEATURE_SELECT_VALUE}";
        const deviceSel = document.getElementById("fvtDevice");
        const dlBtn = document.getElementById("downloadBtn");
        const status = document.getElementById("fvtStatus");

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

        fetch("/api/feature-version-tracking/devices")
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
          // This triggers a redirect to the device URL (browser will download/open it).
          window.location.href = "/api/feature-version-tracking/download?device=" + encodeURIComponent(dev);
        }});
      </script>
    """
    return page_html("Feature - Version Tracking", body)


# ----------------------------
# FEATURE - VERSION TRACKING (API) ✅ NEW
# ----------------------------
@app.get("/api/feature-version-tracking/devices")
def fvt_devices():
    return JSONResponse(sorted(FEATURE_TRACKING_DEVICES))


@app.get("/api/feature-version-tracking/download")
def fvt_download(device: str):
    if not device or device == FEATURE_SELECT_VALUE:
        raise HTTPException(400, "Missing device")

    url = FEATURE_TRACKING_DOC_URLS.get(device)
    if not url:
        raise HTTPException(404, f"No document URL configured for device: {device}")

    # Redirect the client to the document URL.
    return RedirectResponse(url)


# ----------------------------
# PRODUCTS - LAB PAGE (UI)
# ----------------------------
@app.get("/products-lab")
def products_lab_page():
    body = """
        <!-- Row 1: Refresh + Last scan (same line) -->
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
            <button id="refreshBtn" class="btn" type="button" style="cursor:pointer;">
            📡 Scan Devices
            </button>

            <span class="muted" id="meta" style="font-size:12px;"></span>
        </div>

        <!-- Row 2: Status text (Select product / Scanning / Errors) -->
        <p class="muted" id="status" style="margin-top:10px; margin-bottom:8px;">
            Loading last scan...
        </p>

        <!-- Row 3: Dropdown -->
        <select id="productSelect" class="btn" style="display:none; margin-bottom:12px;"></select>

        <!-- Drilldown list -->
        <ul id="ipList" style="margin-top:10px;"></ul>

        <script>
            const SELECT_PLACEHOLDER_VALUE = "__select__";

            function renderIPs(data) {
            const select = document.getElementById('productSelect');
            const list = document.getElementById('ipList');
            const chosen = select.value;

            list.innerHTML = '';
            if (chosen === SELECT_PLACEHOLDER_VALUE) return;

            (data[chosen] || []).forEach(ip => {
                const li = document.createElement('li');
                li.textContent = ip;
                list.appendChild(li);
            });
            }

            function populateProducts(data) {
            const status = document.getElementById('status');
            const select = document.getElementById('productSelect');

            select.innerHTML = "";

            const keys = Object.keys(data || {});
            if (!keys.length) {
                select.style.display = "none";
                document.getElementById('ipList').innerHTML = "";
                status.textContent = "No cached scans yet.";
                return;
            }

            status.textContent = "Select product:";
            select.style.display = "inline-block";

            const placeholder = document.createElement('option');
            placeholder.value = SELECT_PLACEHOLDER_VALUE;
            placeholder.textContent = 'Select';
            placeholder.selected = true;
            select.appendChild(placeholder);

            keys.sort().forEach(product => {
                const opt = document.createElement('option');
                opt.value = product;
                opt.textContent = product;
                select.appendChild(opt);
            });

            select.onchange = () => renderIPs(data);
            select.value = SELECT_PLACEHOLDER_VALUE;
            renderIPs(data);
            }

            function setMeta(scannedAt, err) {
            const meta = document.getElementById('meta');
            if (!scannedAt && !err) {
                meta.textContent = "";
                return;
            }

            let txt = scannedAt ? ("Last scan: " + scannedAt) : "";
            if (err) txt += (txt ? " • " : "") + ("Error: " + err);
            meta.textContent = txt;
            }

            function loadCached() {
            const status = document.getElementById('status');
            status.textContent = "Loading last scan...";
            setMeta("", "");

            fetch('/api/products-lab/cached')
                .then(r => r.json())
                .then(obj => {
                setMeta(obj.scanned_at, obj.error);

                if (obj.error) {
                    status.textContent = "Last scan had an error. You can Refresh.";
                }

                populateProducts(obj.data || {});
                })
                .catch(() => {
                status.textContent = "Failed to load cached scan.";
                setMeta("", "");
                });
            }

            function refreshScan() {
            const status = document.getElementById('status');
            const select = document.getElementById('productSelect');
            const list = document.getElementById('ipList');

            status.textContent = "Scanning Alpha Lab devices - Wait around 20 seconds...";

            select.style.display = "none";
            select.innerHTML = "";
            list.innerHTML = "";

            fetch('/api/products-lab/scan?force=1')
                .then(r => r.json())
                .then(obj => {
                setMeta(obj.scanned_at, obj.error);

                if (obj.error) {
                    status.textContent = "Scan failed. Showing last available cache (if exists).";
                }

                populateProducts(obj.data || {});
                })
                .catch(() => {
                status.textContent = "Scan failed.";
                });
            }

            document.getElementById('refreshBtn').addEventListener('click', refreshScan);

            // On page load
            loadCached();
        </script>
        """
    return page_html("Products - LAB", body)


# ----------------------------
# PRODUCTS - LAB API (Cached)
# ----------------------------
@app.get("/api/products-lab/cached")
def products_lab_cached():
    scanned_at = PRODUCTS_LAB_CACHE["scanned_at"]
    return JSONResponse({
        "data": PRODUCTS_LAB_CACHE["data"] or {},
        "scanned_at": scanned_at.isoformat(sep=" ", timespec="seconds") if scanned_at else None,
        "error": PRODUCTS_LAB_CACHE["error"],
    })


# ----------------------------
# PRODUCTS - LAB API (Scan)
# ----------------------------
@app.get("/api/products-lab/scan")
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
    if not HW_TOOLS_EXE_PATH.exists():
        raise HTTPException(404, "HW Tools installer not found")
    return FileResponse(HW_TOOLS_EXE_PATH, filename=HW_TOOLS_EXE_NAME)


@app.get("/hw-tools")
def hw_tools_page():
    if not HW_TOOLS_EXE_PATH.exists():
        return page_html("HW Tools", "<p class='muted'>Installer not found.</p>")

    st = HW_TOOLS_EXE_PATH.stat()
    return page_html("HW Tools", f"""
      <div class="muted">
        <div><b>File:</b> {HW_TOOLS_EXE_NAME}</div>
        <div><b>Size:</b> {human_size(st.st_size)}</div>
        <div><b>Updated:</b> {datetime.datetime.fromtimestamp(st.st_mtime)}</div>
        <div><b>Creator:</b> {PACKETLIGHT_DOCUMENTATION_HUB_CREATOR}</div>
      </div>
      <div class="actions" style="margin-top:14px">
        <a class="btn" href="/download/hw-tools">⬇ Download</a>
      </div>
    """)
