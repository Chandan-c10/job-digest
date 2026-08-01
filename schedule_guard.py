"""Makes the digest run at a specific local time even though GitHub Actions'
cron trigger is UTC-only with no timezone setting. The workflow's cron
fires frequently (e.g. every 15 min); this module decides whether *this*
particular firing is actually the target local hour, and whether today's
digest already went out, so only one real send happens per day regardless
of how often the workflow itself is triggered.
"""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import config


def _now():
    return datetime.now(ZoneInfo(config.TIMEZONE))


def is_target_hour(now=None):
    now = now or _now()
    return now.hour == config.TARGET_HOUR


def already_ran_today(now=None):
    now = now or _now()
    if not os.path.exists(config.LAST_RUN_FILE):
        return False
    with open(config.LAST_RUN_FILE) as f:
        last_date = json.load(f).get("date")
    return last_date == now.date().isoformat()


def mark_ran_today(now=None):
    now = now or _now()
    with open(config.LAST_RUN_FILE, "w") as f:
        json.dump({"date": now.date().isoformat()}, f)


def should_run(now=None):
    now = now or _now()
    return is_target_hour(now) and not already_ran_today(now)
