"""Decides whether "now" (IST) matches a schedule from config.py, with a
small state file guaranteeing each configured slot fires at most once a
day even if runs overlap its tolerance window.

This is what lets GitHub's own schedule: trigger be a single fixed
recurring check (see the workflow file) instead of encoding exact times -
config.py's EMAIL_SCHEDULE_IST / TELEGRAM_SCHEDULE_IST / TELEGRAM_INTERVAL_
HOURS are the only settings you ever need to edit to change when things
fire. A manual "Run workflow" always counts as due, for both channels,
without consuming a scheduled slot.
"""
import json
import os
from datetime import datetime, timedelta, timezone

import config

IST = timezone(timedelta(hours=5, minutes=30))


def _is_manual_trigger():
    return os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"


def _parse_ist_clock(text, on_date):
    text = text.strip()
    for fmt in ("%I:%M %p", "%I %p", "%H:%M", "%H"):
        try:
            t = datetime.strptime(text, fmt)
            return on_date.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
        except ValueError:
            continue
    raise ValueError(f"Couldn't parse schedule time {text!r} in config.py")


def _slots_for_today(schedule_times, interval_hours, today):
    """Return today's (slot_id, target_datetime) pairs. interval_hours
    (if set) takes priority over schedule_times."""
    if interval_hours:
        midnight = today.replace(hour=0, minute=0, second=0, microsecond=0)
        count = 24 // interval_hours
        return [
            (f"every-{interval_hours}h-{i}", midnight + timedelta(hours=i * interval_hours))
            for i in range(count)
        ]
    return [(t, _parse_ist_clock(t, today)) for t in (schedule_times or [])]


def _load_state():
    if not os.path.exists(config.SCHEDULE_STATE_FILE):
        return {"date": None, "fired": {}}
    with open(config.SCHEDULE_STATE_FILE) as f:
        return json.load(f)


def _save_state(state):
    with open(config.SCHEDULE_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _due_now(channel, schedule_times, interval_hours):
    if _is_manual_trigger():
        return True

    now = datetime.now(IST)
    today_key = now.strftime("%Y-%m-%d")

    state = _load_state()
    if state.get("date") != today_key:
        state = {"date": today_key, "fired": {}}

    fired = state["fired"].setdefault(channel, [])
    tolerance_seconds = config.SCHEDULE_TOLERANCE_MINUTES * 60

    for slot_id, target in _slots_for_today(schedule_times, interval_hours, now):
        if slot_id in fired:
            continue
        delta = (now - target).total_seconds()
        if 0 <= delta < tolerance_seconds:
            fired.append(slot_id)
            _save_state(state)
            return True
    return False


def email_due():
    return _due_now("email", config.EMAIL_SCHEDULE_IST, None)


def telegram_due():
    return _due_now("telegram", config.TELEGRAM_SCHEDULE_IST, config.TELEGRAM_INTERVAL_HOURS)
