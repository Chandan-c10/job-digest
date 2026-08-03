import datetime
import sys

import config
import experience
import notify
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
    pending = state.load_pending(config.PENDING_JOBS_FILE)
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
    # every run, frequent or official, so a job is only ever "new" once,
    # system-wide.
    seen.update(job["id"] for job in all_jobs)
    state.save_seen(config.STATE_FILE, seen)

    # Instant-mode subscribers get this run's finds right away; queue-mode
    # subscribers get an early heads-up now and the full entry later.
    _telegram_safe("deliver_instant", telegram_bot.deliver_instant, new_jobs)
    _telegram_safe("ping_queue", telegram_bot.ping_queue, new_jobs)

    # Accumulate for the next official run — this is what lets a frequent
    # discovery-only run exist without an official run ever missing a job
    # it already marked "seen".
    pending.extend(new_jobs)

    if not config.IS_OFFICIAL_RUN:
        state.save_pending(config.PENDING_JOBS_FILE, pending)
        print(f"Discovery run: {len(new_jobs)} new job(s) found, {len(pending)} pending for the next official digest.")
        return

    # Official run: flush everything accumulated since the last one to
    # scheduled/queue Telegram subscribers and to email.
    _telegram_safe("deliver_scheduled", telegram_bot.deliver_scheduled, pending)

    body = notify.format_digest(pending, errors)
    today = datetime.date.today().isoformat()
    subject = f"Job Digest {today}: {len(pending)} new match(es)"

    if not pending and not errors:
        print("No new matching jobs. Skipping email.")
        state.save_pending(config.PENDING_JOBS_FILE, [])
        return

    notify.send_email(subject, body)
    state.save_pending(config.PENDING_JOBS_FILE, [])
    print(f"Sent digest: {len(pending)} new job(s), {len(errors)} source error(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"job-digest failed: {exc}", file=sys.stderr)
        sys.exit(1)
