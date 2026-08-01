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
    "Infrastructure as Code (IaC)",
]

AI_SKILLS = [
    "GenAI", "RAG", "FastAPI", "OpenAI", "LLM",
]

MIN_SKILL_MATCHES = 4

# Sources to poll. Each must exist in sources.py's SOURCE_FUNCS.
SOURCES = ["remoteok", "wwr_devops", "wwr_programming"]

SENDER_EMAIL = os.environ.get("JOB_DIGEST_EMAIL", "you@example.com")
SENDER_APP_PASSWORD = os.environ.get("JOB_DIGEST_APP_PASSWORD")
RECIPIENT_EMAIL = os.environ.get("JOB_DIGEST_RECIPIENT", SENDER_EMAIL)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

STATE_FILE = os.path.join(os.path.dirname(__file__), "seen_jobs.json")

# GitHub Actions' cron trigger is UTC-only with no timezone setting, so the
# workflow fires every 15 min and main.py itself decides whether it's
# actually the target hour in TIMEZONE (schedule_guard.py) before doing any
# work. Change these to your own local time / timezone as needed.
TIMEZONE = "Asia/Kolkata"
TARGET_HOUR = 8  # 24-hour, in TIMEZONE
LAST_RUN_FILE = os.path.join(os.path.dirname(__file__), "last_run.json")
