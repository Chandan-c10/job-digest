import smtplib
from email.mime.text import MIMEText

import config


def format_digest(jobs, errors):
    if not jobs:
        body = "No new matching jobs today.\n"
    else:
        lines = [f"{len(jobs)} new matching job(s):\n"]
        for job in jobs:
            lines.append(f"- {job['title']} @ {job['company']} ({job['source']})")
            hits = job.get("skills_matched")
            if hits:
                lines.append(f"  Matched skills ({len(hits)}): {', '.join(hits)}")
            lines.append(f"  {job['url']}")
        body = "\n".join(lines)

    if errors:
        body += "\n\n---\nSource errors (non-fatal):\n"
        body += "\n".join(f"- {e}" for e in errors)

    return body


def send_email(subject, body):
    if not config.SENDER_APP_PASSWORD:
        raise RuntimeError(
            "JOB_DIGEST_APP_PASSWORD is not set. Export it before running "
            "(see README.md for how to generate a Gmail App Password)."
        )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.SENDER_EMAIL
    msg["To"] = config.RECIPIENT_EMAIL

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SENDER_EMAIL, config.SENDER_APP_PASSWORD)
        server.sendmail(config.SENDER_EMAIL, [config.RECIPIENT_EMAIL], msg.as_string())
