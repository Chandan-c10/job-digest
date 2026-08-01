import os

# Skill tiers, all matched (word-boundary, case-insensitive) against each
# job's title + tags + description. A job is only included if it hits at
# least MIN_SKILL_MATCHES skills total, counting across all three tiers.
PRIMARY_SKILLS = [
    "DevOps", "AWS", "Linux", "Docker", "Kubernetes", "Jenkins",
    "Terraform", "Git", "CI/CD", "Python", "Shell Scripting",
]

SECONDARY_SKILLS = [
    "DevSecOps", "Ansible", "Helm", "GitHub Actions", "SonarQube", "Trivy",
    "Cloud Engineering", "Site Reliability Engineering (SRE)",
    "Infrastructure as Code (IaC)", "Golang",
]

AI_SKILLS = [
    "GenAI", "RAG", "FastAPI", "OpenAI", "LLM",
]

MIN_SKILL_MATCHES = 4

# Sources to poll. Each must exist in sources.py's SOURCE_FUNCS.
SOURCES = [
    "remoteok", "wwr_devops", "wwr_programming",
    "arbeitnow", "jobicy", "working_nomads", "himalayas",
]

SENDER_EMAIL = os.environ.get("JOB_DIGEST_EMAIL", "you@example.com")
SENDER_APP_PASSWORD = os.environ.get("JOB_DIGEST_APP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("JOB_DIGEST_RECIPIENT", SENDER_EMAIL)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

STATE_FILE = os.path.join(os.path.dirname(__file__), "seen_jobs.json")

# Telegram bot: optional second delivery channel alongside email. Unset
# TELEGRAM_BOT_TOKEN and the whole thing is a no-op — telegram_bot.py checks
# it before making any API calls.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_STATE_FILE = os.path.join(os.path.dirname(__file__), "telegram_state.json")

# Categories a subscriber can pick from in the bot's /preferences menu, each
# mapped to the skill names (from the tiers above) that count as a match for
# that category. Keys are also what's stored in telegram_state.json.
TELEGRAM_CATEGORIES = {
    "devops": ["DevOps", "CI/CD", "Jenkins", "Git", "GitHub Actions", "Shell Scripting"],
    "cloud": ["AWS", "Cloud Engineering"],
    "k8s": ["Kubernetes", "Helm", "Docker"],
    "terraform": ["Terraform", "Infrastructure as Code (IaC)", "Ansible"],
    "ai": ["GenAI", "RAG", "FastAPI", "OpenAI", "LLM"],
    "sre": ["Site Reliability Engineering (SRE)", "DevSecOps"],
    "backend": ["Python", "Golang", "FastAPI"],
    "python": ["Python"],
    "golang": ["Golang"],
}

TELEGRAM_CATEGORY_LABELS = {
    "devops": "DevOps",
    "cloud": "Cloud",
    "k8s": "Kubernetes",
    "terraform": "Terraform / IaC",
    "ai": "AI / GenAI",
    "sre": "SRE",
    "backend": "Backend",
    "python": "Python",
    "golang": "Golang",
}
