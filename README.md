# Auto-Job-Hunting

A small daily job-alert bot. It polls RemoteOK and We Work Remotely, filters
postings against a skill list you define, drops roles above your experience
level, and emails you a digest of what's new. It never applies on your
behalf — you still click "Apply" yourself.

Deliberately excludes LinkedIn and any platform requiring a logged-in
session: scraping/bot-applying on those violates their Terms of Service and
risks account suspension. This only touches sources with public, ToS-friendly
access (a public JSON API or an RSS feed) — each one verified live (real
HTTP 200 + real job data) before being wired in, not just assumed to work.

## How it works

1. `sources.py` fetches postings from seven sources: RemoteOK, We Work
   Remotely (2 RSS categories), Arbeitnow, Jobicy, Working Nomads, and
   Himalayas — all public JSON APIs or RSS feeds, no login required.
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

2. Uncomment the `schedule:` block in the workflow file, and edit the
   `cron:` line(s) to your own target time(s) — see "Timezone handling"
   below.
3. Commit and push. It'll run on GitHub's infrastructure — no need for your
   own machine to be on.

> **No server needed — no external service at all.** GitHub Actions is a
> free tool. Once the schedule is uncommented, GitHub wakes up a runner at
> each cron time, checks out the repo, runs `python3 main.py` exactly like
> the local test command above, and tears the runner down when it's done.
> There's no server to host, no cron provider to sign up for, and (on public
> repos) nothing to pay for.

### Timezone handling

GitHub Actions' `schedule:` cron trigger is **UTC-only** — there's no
setting to make it fire at a local time directly, so you convert by hand:
subtract 5:30 from IST to get UTC (e.g. 9:00 AM IST → 03:30 UTC), or look
up the equivalent offset for your own timezone. Add one `- cron:` line per
trigger you want — the template ships with two as an example (9 AM and 6 PM
IST). Each fires independently, so N cron lines means N emails/day.

State (`seen_jobs.json`) persists between runs via `actions/cache`, not by
committing it to the repo, so your job history doesn't clutter git log.

## Telegram bot (optional second channel)

A Telegram bot can deliver the same digest as chat messages, with a
category picker so subscribers choose what they want without touching
`config.py`:

1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → follow the
   prompts → copy the bot token it gives you.
2. Add it as a repo secret: `TELEGRAM_BOT_TOKEN`.
3. Message your new bot `/start`. It replies with a category picker
   (buttons toggle ✅/⬜; tap "Done" when set): DevOps, Cloud, Kubernetes,
   Terraform / IaC, AI / GenAI, SRE — edit `TELEGRAM_CATEGORIES` /
   `TELEGRAM_CATEGORY_LABELS` in `config.py` to change the options.
4. Other commands: `/preferences` (reopen the picker), `/status`, `/pause`,
   `/resume`, `/help`.

**Timing:** same model as the email digest — no webhook, no always-on
server. `telegram_bot.poll_commands()` checks for new Telegram messages
once per run, so a `/preferences` change takes effect on the next
scheduled run (or immediately if you manually trigger the workflow right
after messaging the bot).

Entirely optional: leave `TELEGRAM_BOT_TOKEN` unset and `telegram_bot.py`
no-ops everywhere it's called — the email digest works exactly as before.

## Files

- `config.py` — skills, sources, email settings, Telegram categories
- `sources.py` — per-source fetchers (RemoteOK, We Work Remotely, Arbeitnow,
  Jobicy, Working Nomads, Himalayas)
- `skills.py` — shared word-boundary skill matching
- `experience.py` — seniority/years-of-experience filter
- `state.py` — seen-job id persistence
- `notify.py` — digest formatting + SMTP send
- `telegram_bot.py` — optional Telegram channel: command polling, category
  picker, digest formatting + send (all no-ops if `TELEGRAM_BOT_TOKEN` unset)
- `main.py` — entrypoint

## License

MIT — see [LICENSE](LICENSE).
