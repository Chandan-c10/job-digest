import datetime
import sys

import config
import experience
import notify
import schedule_guard
import skills
import sources
import state


def main():
    if not schedule_guard.should_run():
        print(
            f"Not the target hour ({config.TARGET_HOUR}:00 {config.TIMEZONE}) "
            "or already ran today. Skipping."
        )
        return
    schedule_guard.mark_ran_today()

    seen = state.load_seen(config.STATE_FILE)
    all_jobs, errors = sources.fetch_all(config.SOURCES)

    new_jobs = []
    for job in all_jobs:
        if job["id"] in seen:
            continue
        if not experience.is_appropriate_level(job):
            continue
        hits = skills.matched_skills(job["text_for_match"])
        if len(hits) >= config.MIN_SKILL_MATCHES:
            job["skills_matched"] = hits
            new_jobs.append(job)

    # Mark every fetched job as seen (not just matches) so a threshold/skill
    # tweak later doesn't resurface hundreds of old postings.
    seen.update(job["id"] for job in all_jobs)
    state.save_seen(config.STATE_FILE, seen)

    body = notify.format_digest(new_jobs, errors)
    today = datetime.date.today().isoformat()
    subject = f"Job Digest {today}: {len(new_jobs)} new match(es)"

    if not new_jobs and not errors:
        print("No new matching jobs. Skipping email.")
        return

    notify.send_email(subject, body)
    print(f"Sent digest: {len(new_jobs)} new job(s), {len(errors)} source error(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"job-digest failed: {exc}", file=sys.stderr)
        sys.exit(1)
