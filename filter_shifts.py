import sys
import re

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
