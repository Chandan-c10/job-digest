import datetime
import sys

import config
import experience
import notify
import schedule
import skills
import sources
import state
import telegram_bot


def _telegram_safe(label, fn, *args):
    """Telegram is an optional second channel — a failure on its side (bad
    token, a subscriber blocking the bot, a Telegram API hiccup) must never
    take the email digest down with it."""
    try:
        fn(*args)
    except Exception as exc:  # noqa: BLE001
        print(f"Telegram: {label} failed ({exc}), continuing without it.")


def _matches_any(terms, text):
    """True if terms is empty (filter not in use) or text mentions at
    least one of them."""
    return not terms or any(skills.skill_in_text(t, text) for t in terms)


def main():
    if not (config.PRIMARY_SKILLS or config.SECONDARY_SKILLS or config.AI_SKILLS):
        raise RuntimeError(
            "No skills configured - PRIMARY_SKILLS, SECONDARY_SKILLS, and "
            "AI_SKILLS in config.py are all empty, so no job could ever "
            "match. Fill in at least one skill list before running (see "
            "README.md 'Setup')."
        )

    _telegram_safe("poll_commands", telegram_bot.poll_commands)

    seen = state.load_seen(config.STATE_FILE)
    pending_email = state.load_pending(config.PENDING_EMAIL_JOBS_FILE)
    pending_telegram = state.load_pending(config.PENDING_TELEGRAM_JOBS_FILE)
    all_jobs, errors = sources.fetch_all(config.SOURCES)

    new_jobs = []
    for job in all_jobs:
        if job["id"] in seen:
            continue
        if not experience.is_appropriate_level(job):
            continue
        if not _matches_any(config.JOB_TYPES, job["text_for_match"]):
            continue
        if not _matches_any(config.LOCATIONS, job["text_for_match"]):
            continue
        hits = skills.matched_skills(job["text_for_match"])
        if len(hits) >= config.MIN_SKILL_MATCHES:
            job["skills_matched"] = hits
            new_jobs.append(job)

    # Mark every fetched job as seen (not just matches) so a threshold/skill
    # tweak later doesn't resurface hundreds of old postings. This happens
    # every run so a job is only ever "new" once, system-wide.
    seen.update(job["id"] for job in all_jobs)
    state.save_seen(config.STATE_FILE, seen)

    # Instant-mode subscribers get this run's finds right away; queue-mode
    # subscribers get an early heads-up now and the full entry later.
    _telegram_safe("deliver_instant", telegram_bot.deliver_instant, new_jobs)
    _telegram_safe("ping_queue", telegram_bot.ping_queue, new_jobs)

    # Accumulate for whichever channel next fires - email and Telegram now
    # have fully independent schedules (see config.py / schedule.py), so
    # each gets its own accumulator rather than sharing one.
    pending_email.extend(new_jobs)
    pending_telegram.extend(new_jobs)

    email_due = schedule.email_due()
    telegram_due = schedule.telegram_due()

    if email_due:
        today = datetime.date.today().isoformat()
        subject = f"Job Digest {today}: {len(pending_email)} new match(es)"
        if pending_email or errors:
            notify.send_email(subject, notify.format_digest(pending_email, errors))
            print(f"Sent digest: {len(pending_email)} new job(s), {len(errors)} source error(s).")
        else:
            print("No new matching jobs. Skipping email.")
        pending_email = []

    if telegram_due:
        _telegram_safe("deliver_scheduled", telegram_bot.deliver_scheduled, pending_telegram)
        pending_telegram = []

    state.save_pending(config.PENDING_EMAIL_JOBS_FILE, pending_email)
    state.save_pending(config.PENDING_TELEGRAM_JOBS_FILE, pending_telegram)

    if not email_due and not telegram_due:
        print(
            f"Check-in run: {len(new_jobs)} new job(s) found, "
            f"{len(pending_email)} pending for email, "
            f"{len(pending_telegram)} pending for Telegram."
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"job-digest failed: {exc}", file=sys.stderr)
        sys.exit(1)
