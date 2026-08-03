"""Convert a target IST time into an off-peak UTC cron line to paste into
.github/workflows/job-digest.yml.

GitHub Actions' `schedule:` trigger is read by GitHub's own scheduler from
the workflow YAML - it can't be computed at runtime by main.py, since
GitHub has to know the schedule before it ever runs your code. This script
just automates the IST->UTC conversion + the off-peak minute nudge, so you
never do the "-5:30, avoid :00/:30" math by hand; you still copy its output
into the workflow file yourself and push.

Usage:
    python3 ist_to_cron.py 9:00
    python3 ist_to_cron.py 09:00
    python3 ist_to_cron.py "6:30 PM"
"""
import sys
from datetime import datetime, timedelta

IST_OFFSET = timedelta(hours=5, minutes=30)
UNSAFE_MINUTES = {0, 15, 30, 45}
SAFE_NUDGE_MINUTES = 7  # push off :00/:15/:30/:45 by this many minutes


def parse_ist(text):
    text = text.strip()
    for fmt in ("%I:%M %p", "%I %p", "%H:%M", "%H"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"Couldn't parse {text!r} as a time. Try '9:00', '09:00', or '6:30 PM'.")


def ist_to_cron(ist_text):
    ist = parse_ist(ist_text)
    utc = ist - IST_OFFSET

    if utc.minute in UNSAFE_MINUTES:
        utc += timedelta(minutes=SAFE_NUDGE_MINUTES)

    actual_ist = utc + IST_OFFSET
    cron = f"{utc.minute} {utc.hour} * * *"
    return cron, actual_ist


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    ist_text = " ".join(sys.argv[1:])
    try:
        cron, actual_ist = ist_to_cron(ist_text)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    print(f'- cron: "{cron}"')
    print(f"# fires ~{actual_ist.strftime('%I:%M %p')} IST (UTC-only, off-peak minute)")


if __name__ == "__main__":
    main()
