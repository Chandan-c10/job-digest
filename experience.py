"""Filters out postings outside [config.MIN_YEARS, config.MAX_YEARS]:
senior/lead/staff-type titles, and postings that explicitly ask for a
years-of-experience range outside that window.
"""
import re

import config

SENIOR_TITLE_PATTERN = re.compile(
    r"\b(senior|sr\.?|staff|principal|lead|director|architect|head of|manager|vp|vice president)\b",
    re.IGNORECASE,
)

# Matches "3+ years", "3-5 years", "minimum 4 years", etc. Takes the lower
# bound of the range as the effective minimum requirement.
YEARS_PATTERN = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:-|to)\s*(\d{1,2})\s*\+?\s*years?|(\d{1,2})\s*\+?\s*years?",
    re.IGNORECASE,
)


def is_appropriate_level(job):
    if SENIOR_TITLE_PATTERN.search(job.get("title", "")):
        return False

    text = job.get("text_for_match", "")
    for m in YEARS_PATTERN.finditer(text):
        low = int(m.group(1) or m.group(3))
        if low > config.MAX_YEARS or low < config.MIN_YEARS:
            return False
    return True
