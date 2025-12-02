from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import Response, HTMLResponse
import os
import re
import requests
from pathlib import Path

app = FastAPI()

ACCESS_TOKEN = os.getenv("ICS_ACCESS_TOKEN", "dOJehqtcqr9ZjmciLjewoHqE4xrhSkoDhF8AseWhtm8")  # use a long random string in prod
NURSEGRID_BASE = "https://app.nursegrid.com"

BASE_DIR = Path(__file__).parent
INDEX_PATH = BASE_DIR / "static" / "index.html"


def filter_ics(ics_text: str) -> str:
    lines = ics_text.splitlines(keepends=True)

    out_lines = []
    current_event = []
    in_event = False
    keep_event = False

    for line in lines:
        if line.startswith("BEGIN:VEVENT"):
            in_event = True
            keep_event = False
            current_event = [line]
            continue

        if in_event:
            current_event.append(line)

            if line.startswith("SUMMARY:"):
                m = re.match(r"(SUMMARY:.*?(Regular Shift|On Call))", line)
                if m:
                    current_event[-1] = m.group(1) + "\n"
                    keep_event = True

            if line.startswith("END:VEVENT"):
                if keep_event:
                    out_lines.extend(current_event)
                in_event = False
                current_event = []
                keep_event = False

            continue

        out_lines.append(line)

    return "".join(out_lines)


# 1) Root route: serve the index.html landing page
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if not INDEX_PATH.exists():
        # Basic fallback if you forget to deploy the file
        return HTMLResponse("<h1>NurseGrid Filter</h1><p>index.html not found.</p>", status_code=500)
    return HTMLResponse(INDEX_PATH.read_text(encoding="utf-8"))


# 2) Proxy route only for NurseGrid calendar paths
@app.get("/calendars/{full_path:path}")
async def proxy_calendar(
    full_path: str,
    request: Request,
    token: str | None = Query(None),
):
    # Require token
    if token != ACCESS_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    # (Optional) extra safety: ensure path is non-empty
    if not full_path:
        raise HTTPException(status_code=404, detail="Missing calendar path")

    upstream_url = f"{NURSEGRID_BASE}/calendars/{full_path}"

    try:
        upstream = requests.get(upstream_url, timeout=10)
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Upstream calendar fetch failed")

    if upstream.status_code != 200:
        raise HTTPException(status_code=502, detail="Upstream calendar returned error")

    filtered = filter_ics(upstream.text)

    return Response(
        content=filtered,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="nurse-schedule.ics"'
        },
    )
