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

2. Set `TIMEZONE` and `TARGET_HOUR` in `config.py` to your own local time
   (e.g. `"America/New_York"`, `17` for 5 PM). No UTC math needed — see
   "Timezone handling" below for why.
3. Uncomment the `schedule:` block in the workflow file.
4. Commit and push. It'll run on GitHub's infrastructure — no need for your
   own machine to be on.

> **No server needed — no external service at all.** GitHub Actions is a
> free tool. Once the schedule is uncommented, GitHub wakes up a runner
> periodically, checks out the repo, runs `python3 main.py` exactly like the
> local test command above, and tears the runner down when it's done.
> There's no server to host, no cron provider to sign up for, and (on public
> repos) nothing to pay for.

### Timezone handling

GitHub Actions' `schedule:` cron trigger is **UTC-only** — there is no
setting to make it fire at a local time directly. Rather than requiring you
to convert your target time to UTC by hand (and redo that math every time
you change it), this repo moves the actual "is it time yet?" decision into
`schedule_guard.py`: the workflow's cron fires every 30 minutes (two
chances per target hour, in case GitHub delays a run under load — this is
a documented possibility), and the script checks the real current time in
`TIMEZONE` and only does real work if it matches `TARGET_HOUR` **and**
hasn't already run today (tracked via `last_run.json`, cached the same way
as `seen_jobs.json`, so a fresh runner VM still remembers). Only one actual
email goes out per day, regardless of how often the workflow itself fires.

**Actions-minutes note**: every firing costs a little runtime even when it
just skips (checkout + Python setup, roughly 20-30 seconds). Public repos
get unlimited Actions minutes; private repos get a monthly free quota
(2,000 min at the time of writing) — every-30-min firing costs roughly
500-950 min/month just from skip-runs, worth knowing if you fork this as
private.

State (`seen_jobs.json`, `last_run.json`) persists between runs via
`actions/cache`, not by committing them to the repo, so your job history
doesn't clutter git log.

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
