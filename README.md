# Auto-Job-Hunting

A small daily job-alert bot. It polls RemoteOK and We Work Remotely, filters
postings against a skill list you define, drops roles above your experience
level, and emails you a digest of what's new. It never applies on your
behalf — you still click "Apply" yourself.

Deliberately excludes LinkedIn and any platform requiring a logged-in
session: scraping/bot-applying on those violates their Terms of Service and
risks account suspension. This only touches sources with public, ToS-friendly
access (a public JSON API or an RSS feed).

## How it works

1. `sources.py` fetches postings from RemoteOK's public API and We Work
   Remotely's public RSS feeds.
2. `skills.py` matches each posting's text against the skill tiers in
   `config.py` (word-boundary matching, so short terms like "Git" don't
   false-positive on "Legit").
3. `experience.py` drops postings with senior/lead/staff/director-type
   titles, or that explicitly ask for more years of experience than
   `experience.MAX_YEARS`.
4. `state.py` remembers which postings you've already been shown
   (`seen_jobs.json`), so you're never re-notified.
5. `notify.py` emails you the digest via Gmail SMTP.

## Setup

1. Fork/clone this repo.
2. Edit `config.py`: set `PRIMARY_SKILLS` / `SECONDARY_SKILLS` / `AI_SKILLS`
   to match what you're targeting, and adjust `MIN_SKILL_MATCHES`.
3. Edit `experience.py`'s `MAX_YEARS` to your experience level.
4. Create a Gmail App Password for whichever account will send the digest
   (Google Account → Security → 2-Step Verification → App Passwords).
5. Run it locally to test:

   ```bash
   export JOB_DIGEST_EMAIL="you@gmail.com"
   export JOB_DIGEST_APP_PASSWORD="your-16-char-app-password"
   export JOB_DIGEST_RECIPIENT="you@gmail.com"   # defaults to JOB_DIGEST_EMAIL's value if unset
   python3 main.py
   ```

## Running it daily via GitHub Actions

The workflow at `.github/workflows/job-digest.yml` ships with its schedule
commented out. To activate it on your fork:

1. Add repo secrets (Settings → Secrets and variables → Actions):
   - `JOB_DIGEST_EMAIL`
   - `JOB_DIGEST_APP_PASSWORD`
   - `JOB_DIGEST_RECIPIENT` (optional, defaults to `JOB_DIGEST_EMAIL`)

   Example:

   | Secret name | Example value |
   |---|---|
   | `JOB_DIGEST_EMAIL` | `you@gmail.com` |
   | `JOB_DIGEST_APP_PASSWORD` | `abcd efgh ijkl mnop` (16-char Gmail App Password, not your account password) |
   | `JOB_DIGEST_RECIPIENT` | `you@gmail.com` (optional — omit to just send to `JOB_DIGEST_EMAIL`) |

2. Uncomment the `schedule:` block in the workflow file.
3. Commit and push. It'll run on GitHub's infrastructure — no need for your
   own machine to be on.

> **No server needed — no external service at all.** GitHub Actions is a
> free tool (unlimited minutes on public repos): once the schedule is
> uncommented, GitHub itself wakes up a runner at `30 2 * * *` (08:00 IST /
> 02:30 UTC) every day, checks out the repo, runs `python3 main.py` exactly
> like the local test command above, and tears the runner down when it's
> done. There's no server to host or keep running, no cron provider to sign
> up for, and nothing to pay for.

State (`seen_jobs.json`) persists between runs via `actions/cache`, not by
committing it to the repo, so your job history doesn't clutter git log.

## Files

- `config.py` — skills, sources, email settings
- `sources.py` — per-source fetchers (RemoteOK API, We Work Remotely RSS)
- `skills.py` — shared word-boundary skill matching
- `experience.py` — seniority/years-of-experience filter
- `state.py` — seen-job id persistence
- `notify.py` — digest formatting + SMTP send
- `main.py` — entrypoint

## License

MIT — see [LICENSE](LICENSE).
