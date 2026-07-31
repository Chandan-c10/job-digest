"""Filters out postings that don't fit a 1-2 year experience level:
senior/lead/staff-type titles, and postings that explicitly ask for more
years of experience than that.
"""
import re

MAX_YEARS = 1

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
        if low > MAX_YEARS:
            return False
    return True
