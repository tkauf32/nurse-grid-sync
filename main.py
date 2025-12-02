from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
import os
import requests

app = FastAPI()

# Configure via environment variables
UPSTREAM_ICS_URL = "https://app.nursegrid.com/calendars/QbaGE1zikkrUNSB/ce7972d6-62ac-4ab8-b669-27c2bb1a6c27"  # original NurseGrid/Google ICS URL
ACCESS_TOKEN = "dOJehqtcqr9ZjmciLjewoHqE4xrhSkoDhF8AseWhtm8"     # long random string


def filter_ics(ics_text: str) -> str:
    """
    Keep only VEVENT blocks whose SUMMARY contains 'Regular Shift' or 'On Call'.
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
                if ("Regular Shift" in summary) or ("On Call" in summary):
                    keep_event = True

            if line.startswith("END:VEVENT"):
                if keep_event:
                    out_lines.extend(current_event)
                in_event = False
                current_event = []
                keep_event = False

            continue

        # Outside VEVENT: copy as-is (header/footer, etc.)
        out_lines.append(line)

    return "".join(out_lines)


@app.get("/nurse-schedule.ics")
async def get_filtered_ics(request: Request, token: str | None = None):
    # Simple token check in query string: ?token=...
    if ACCESS_TOKEN is None or UPSTREAM_ICS_URL is None:
        raise HTTPException(status_code=500, detail="Server not configured")

    if token != ACCESS_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        upstream = requests.get(UPSTREAM_ICS_URL, timeout=10)
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
