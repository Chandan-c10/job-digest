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

# Jobs accumulate here between official runs (see IS_OFFICIAL_RUN below) so
# a frequent discovery-only run never causes an official run to miss
# something an intervening run already marked "seen".
PENDING_JOBS_FILE = os.path.join(os.path.dirname(__file__), "pending_jobs.json")

# True on the normal scheduled/manual runs (email + full Telegram digest).
# False only on the extra frequent trigger added for Telegram instant/queue
# mode, which discovers jobs and pings instant/queue subscribers but never
# sends email or the official digest — see .github/workflows/job-digest.yml.
IS_OFFICIAL_RUN = os.environ.get("TELEGRAM_OFFICIAL_RUN", "true").lower() != "false"

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
