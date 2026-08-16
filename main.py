from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import Response, HTMLResponse
import os
import requests
from pathlib import Path

app = FastAPI()

ACCESS_TOKEN = os.getenv("ICS_ACCESS_TOKEN", "dOJehqtcqr9ZjmciLjewoHqE4xrhSkoDhF8AseWhtm8")  # use a long random string in prod
NURSEGRID_BASE = "https://app.nursegrid.com"

BASE_DIR = Path(__file__).parent
INDEX_PATH = BASE_DIR / "static" / "index.html"


def concise_event_title(summary: str) -> str | None:
    """Return a wanted event category, or None for events to exclude."""
    normalized = summary.casefold()

    if "on call" in normalized:
        return "On Call"
    if "night" in normalized:
        return "Night Shift"
    if "day" in normalized:
        return "Day Shift"
    if "regular shift" in normalized:
        return "Regular Shift"
    return None


def filter_ics(ics_text: str) -> str:
    """
    Keep only Regular Shift, Night Shift, Day Shift, and On Call VEVENT blocks.
    Replace kept event summaries with concise event-category titles.
    Preserve everything else (VCALENDAR header/footer).
    """
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
                summary = line.strip()
                title = concise_event_title(summary)
                if title:
                    keep_event = True
                    line_ending = "\r\n" if line.endswith("\r\n") else "\n"
                    current_event[-1] = f"SUMMARY:{title}{line_ending}"

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
