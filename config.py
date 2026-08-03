import os

# Your skills, split into 3 tiers. A job needs MIN_SKILL_MATCHES hits
# total (any tier) to count. Uncomment the examples below and edit them,
# or write your own the same way.
PRIMARY_SKILLS = [
    # "DevOps", "AWS", "Linux", "Docker", "Terraform", "Git", "CI/CD",
    # "Python", "Java", "JavaScript", "Node.js", "API",
]

SECONDARY_SKILLS = [
    # "Cloud Engineering", "Site Reliability Engineering (SRE)",
    # "Infrastructure as Code (IaC)", "SDE",
]

AI_SKILLS = [
    # "GenAI", "RAG", "FastAPI", "OpenAI", "LLM",
]

MIN_SKILL_MATCHES = 4

# Postings asking for more than MAX_YEARS or less than MIN_YEARS are
# skipped. Leave MIN_YEARS at 0 to allow any junior/fresher posting.
MIN_YEARS = 0
MAX_YEARS = 0

# Optional. If set, a posting must mention at least one entry from each
# non-empty list below (title/description). Leave a list empty to skip
# that filter entirely - e.g. most sources are remote-only, but Internshala
# includes on-site listings in specific cities, so LOCATIONS is useful there.
JOB_TYPES = [
    # "Full-time", "Internship", "Contract",
]

LOCATIONS = [
    # "Remote", "Bangalore", "Delhi",
]

# Sources to poll. Each must exist in sources.py's SOURCE_FUNCS.
SOURCES = [
    "remoteok", "wwr_devops", "wwr_programming",
    "arbeitnow", "jobicy", "working_nomads", "himalayas", "internshala",
]

SENDER_EMAIL = os.environ.get("JOB_DIGEST_EMAIL", "you@example.com")
SENDER_APP_PASSWORD = os.environ.get("JOB_DIGEST_APP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("JOB_DIGEST_RECIPIENT", SENDER_EMAIL)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

STATE_FILE = os.path.join(os.path.dirname(__file__), "seen_jobs.json")

# --- Schedule (see schedule.py) -------------------------------------------
# The workflow file's own cron just runs a fixed recurring check (e.g.
# hourly) - THIS is the only place you edit to change when things fire.
# No workflow/YAML edits needed for a time change.

# When to send the EMAIL digest (IST clock times). One entry per email/day.
EMAIL_SCHEDULE_IST = ["9:00 AM", "6:00 PM"]

# When to send the full TELEGRAM digest to scheduled/queue subscribers.
# Two ways to set this - use ONE:
#   - A simple recurring interval (this is what's active below): fires
#     every N hours starting from midnight IST. Must evenly divide 24
#     (1, 2, 3, 4, 6, 8, 12, 24). 2 -> 12 times/day; 1 -> 24 times/day.
#   - Fixed clock times, same style as email: set TELEGRAM_INTERVAL_HOURS
#     to None and fill in TELEGRAM_SCHEDULE_IST instead, e.g.
#     ["9:00 AM", "6:00 PM"].
TELEGRAM_INTERVAL_HOURS = 2
TELEGRAM_SCHEDULE_IST = []

# How close (minutes) "now" must be to a scheduled slot to count as due -
# keep this >= how often the workflow's own schedule: trigger actually
# runs, or a slot could be missed entirely between checks.
SCHEDULE_TOLERANCE_MINUTES = 60

SCHEDULE_STATE_FILE = os.path.join(os.path.dirname(__file__), "schedule_state.json")

# Jobs accumulate here between scheduled fires so a frequent check-in run
# never causes a scheduled send to miss something an intervening run
# already marked "seen". Separate files since email and Telegram now have
# independent schedules.
PENDING_EMAIL_JOBS_FILE = os.path.join(os.path.dirname(__file__), "pending_email_jobs.json")
PENDING_TELEGRAM_JOBS_FILE = os.path.join(os.path.dirname(__file__), "pending_telegram_jobs.json")

# Telegram bot: optional second delivery channel alongside email. Unset
# TELEGRAM_BOT_TOKEN and the whole thing is a no-op — telegram_bot.py checks
# it before making any API calls.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_STATE_FILE = os.path.join(os.path.dirname(__file__), "telegram_state.json")

# Categories subscribers pick from in the bot's /preferences menu. Each key
# maps to a list of skills (from the tiers above) that count as a match.
# Uncomment the examples below and edit them, or write your own the same way.
TELEGRAM_CATEGORIES = {
    # "devops": ["DevOps", "CI/CD", "Git"],
    # "cloud": ["AWS", "Cloud Engineering"],
    # "ai": ["GenAI", "RAG", "FastAPI", "OpenAI", "LLM"],
}

# One display label per key above, e.g. "devops" -> "DevOps".
TELEGRAM_CATEGORY_LABELS = {
    # "devops": "DevOps",
    # "cloud": "Cloud",
    # "ai": "AI / GenAI",
}
