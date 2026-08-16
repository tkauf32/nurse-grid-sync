import sys

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} input.ics output.ics")
    sys.exit(1)

input_path = sys.argv[1]
output_path = sys.argv[2]

with open(input_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

out_lines = []
current_event = []
in_event = False
keep_event = False


def concise_event_title(summary: str) -> str:
    """Return the short event category shown in subscribed calendars."""
    normalized = summary.casefold()

    if "on call" in normalized:
        return "On Call"
    if "night" in normalized:
        return "Night Shift"
    if "evening" in normalized:
        return "Evening Shift"
    if "day" in normalized:
        return "Day Shift"
    return "Regular Shift"

for line in lines:
    # Detect start/end of events
    if line.startswith("BEGIN:VEVENT"):
        in_event = True
        keep_event = False
        current_event = [line]
        continue

    if in_event:
        current_event.append(line)

        # Check the SUMMARY line to decide whether to keep the event
        if line.startswith("SUMMARY:"):
            # Normalize whitespace and case just in case
            summary = line.strip()
            if ("Regular Shift" in summary) or ("On Call" in summary):
                keep_event = True
                line_ending = "\r\n" if line.endswith("\r\n") else "\n"
                current_event[-1] = f"SUMMARY:{concise_event_title(summary)}{line_ending}"

        if line.startswith("END:VEVENT"):
            # Event block is complete; decide to keep or drop
            if keep_event:
                out_lines.extend(current_event)
            # Reset for next event
            in_event = False
            current_event = []
            keep_event = False

        continue

    # Everything outside VEVENT (VCALENDAR header/footer, etc.)
    out_lines.append(line)

with open(output_path, "w", encoding="utf-8") as f:
    f.writelines(out_lines)
