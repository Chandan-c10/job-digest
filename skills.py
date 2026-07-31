"""Shared skill-matching: word-boundary regex matching against job text,
used both for filtering the digest (main.py) and resume tailoring
(resume/tailor.py).
"""
import re

import config


def _terms_for(skill):
    """'Site Reliability Engineering (SRE)' -> ['site reliability engineering', 'sre']."""
    m = re.match(r"^(.*)\(([^)]+)\)\s*$", skill.strip())
    if m:
        return [m.group(1).strip().lower(), m.group(2).strip().lower()]
    return [skill.strip().lower()]


def _compile_patterns(skill_names):
    return {
        skill: [re.compile(r"\b" + re.escape(t) + r"\b") for t in _terms_for(skill)]
        for skill in skill_names
    }


ALL_SKILLS = config.PRIMARY_SKILLS + config.SECONDARY_SKILLS + config.AI_SKILLS
_PATTERNS = _compile_patterns(ALL_SKILLS)


def matched_skills(text):
    """Return the subset of config skill names that appear in `text`."""
    text = text.lower()
    return [
        skill for skill, patterns in _PATTERNS.items()
        if any(p.search(text) for p in patterns)
    ]


def skill_in_text(skill_name, text):
    """Loose word-boundary check for an arbitrary skill/tech token against text."""
    patterns = _PATTERNS.get(skill_name) or _compile_patterns([skill_name])[skill_name]
    return any(p.search(text.lower()) for p in patterns)
