# Auto-Job-Hunting

A small daily job-alert bot. It polls RemoteOK and We Work Remotely, filters
postings against a skill list you define, drops roles above your experience
level, and emails you a digest of what's new. It never applies on your
behalf — you still click "Apply" yourself.

Deliberately excludes LinkedIn and any platform requiring a logged-in
session: scraping/bot-applying on those violates their Terms of Service and
risks account suspension. This only touches sources with public,
ToS-friendly access (a public JSON API, RSS feed, or plain server-rendered
HTML) — each one verified live (real HTTP 200 + real job data) before being
wired in, not just assumed to work.

## How it works

1. `sources.py` fetches postings from eight sources: RemoteOK, We Work
   Remotely (2 RSS categories), Arbeitnow, Jobicy, Working Nomads,
   Himalayas — all public JSON APIs or RSS feeds, no login required — plus
   Internshala, which has no API/RSS but is server-rendered, so it's
   regex-parsed from the plain HTML instead. Several other well-known
   Indian/global portals were tested and rejected: see "Why not more
   sources?" below.
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
   Terraform / IaC, AI / GenAI, SRE, Backend, Python — edit
   `TELEGRAM_CATEGORIES` / `TELEGRAM_CATEGORY_LABELS` in `config.py` to
   change the options.
4. `/skills Rust, gRPC, Postgres` — add your own free-text keywords on top
   of the categories above. A job matches if it's in a selected category
   **or** mentions one of your custom keywords. `/skills` alone shows
   what's set; `/skills clear` resets it.
5. Other commands: `/preferences` (reopen the category picker), `/status`,
   `/pause`, `/resume`, `/help`.

### Notification modes

Each subscriber has exactly one active mode, switched anytime — setting a
new one replaces the old one:

| Command | Mode | Behavior |
|---|---|---|
| `/scheduled` (default) | Scheduled | Full digest only at the official run times. |
| `/queue` | Queue | An early "added to queue" ping the moment a job is found, **plus** the full entry at the next official run. |
| `/instant` | Instant | The full entry immediately, whenever a job is first found — never repeated later. |

`/status` shows the active mode along with categories, custom skills, and
pause state.

**How "instant" actually works — no server, so no true push.** Queue and
instant modes only do anything if you enable the optional hourly
`- cron: "0 * * * *"` trigger in the workflow file (commented out by
default alongside the rest of the schedule). That trigger fetches jobs and
pings instant/queue subscribers, but never sends email and never runs the
official digest — that's still only your official cron times. So
"instant" really means "within an hour" (or whatever interval you set that
trigger to), not real-time push. Scheduled-mode subscribers are completely
unaffected by it either way.

**Why an extra hourly run can't cause an official run to miss anything:**
a job is marked "seen" in `seen_jobs.json` the first time *any* run —
hourly or official — fetches it, so it only ever counts as "new" once,
system-wide. To stop that from meaning "an hourly run steals a job from
scheduled-mode subscribers," every newly-found job is *also* appended to
`pending_jobs.json` regardless of which run found it or who it's for. The
official run flushes and clears that whole accumulated list (to email, and
to scheduled/queue Telegram subscribers) rather than just its own run's
finds. Instant-mode delivery, by contrast, only ever uses that specific
run's own finds, so instant subscribers never see a repeat.

**Important limit:** categories and `/skills` both only *narrow* the
digest — they can't widen it. Every job still has to clear the global
`MIN_SKILL_MATCHES`-across-the-tiers filter in `main.py` first (that's
what builds the list Telegram ever sees). So a category or `/skills`
keyword surfaces a posting only if it also already scored high enough on
your `PRIMARY_SKILLS`/`SECONDARY_SKILLS`/`AI_SKILLS`. Making this fully
independent per subscriber would mean moving that filter to run
per-subscriber against every fetched job — a bigger change, not
implemented here.

**Timing:** same model as the email digest — no webhook, no always-on
server. `telegram_bot.poll_commands()` checks for new Telegram messages
once per run, so a `/preferences`, `/skills`, or mode change takes effect
on the next scheduled (or hourly, if enabled) run — or immediately if you
manually trigger the workflow right after messaging the bot.

Entirely optional: leave `TELEGRAM_BOT_TOKEN` unset and `telegram_bot.py`
no-ops everywhere it's called — the email digest works exactly as before.

## Why not more sources?

Every candidate below was actually tested live (real HTTP request, checked
the response) before being accepted or rejected — not assumed either way:

| Source | Result |
|---|---|
| LinkedIn | Excluded on principle, not tested — scraping/bot-applying violates its ToS and risks account suspension. |
| Naukri, Dice, Instahyre, CutShort, Foundit, TimesJobs | JS-rendered SPA — the plain HTML response has zero job data, only an empty app shell that fills in client-side after JavaScript runs. |
| Indeed, Glassdoor | `403 Forbidden` — actively blocked by Cloudflare/anti-bot protection. |
| Apna, Shine.com | Real job data does exist somewhere on the page, but embedded in a React-streaming payload or a separate internal API rather than plain HTML — technically scrapable, but too fragile (breaks silently on any frontend change) to be worth it. |
| jobseeker.com, talentanywhere.ai | Not actually job-listing aggregators — turned out to be a generic/parked-looking site and a staffing agency's marketing blog, respectively. |

Getting past the JS-rendered/blocked ones would require full
headless-browser automation (e.g. Playwright: load the page, run its JS,
wait for listings to render, scrape the DOM) — a materially heavier,
slower, and more fragile approach than the plain HTTP requests every
current source uses, and a poor fit for a script meant to run in a few
seconds on a free GitHub Actions runner. If you want to add one of these
anyway, or know of another source with a real public API/RSS/server-rendered
page, `sources.py`'s existing fetchers are the pattern to follow — see
`fetch_internshala()` for how to regex-parse an HTML-only source.

## Files

- `config.py` — skills, sources, email settings, Telegram categories
- `sources.py` — per-source fetchers (RemoteOK, We Work Remotely, Arbeitnow,
  Jobicy, Working Nomads, Himalayas, Internshala)
- `skills.py` — shared word-boundary skill matching
- `experience.py` — seniority/years-of-experience filter
- `state.py` — seen-job id persistence and the pending-jobs accumulator
  (`pending_jobs.json`) between official runs
- `notify.py` — digest formatting + SMTP send
- `telegram_bot.py` — optional Telegram channel: command polling, category
  picker, notification-mode handling, digest formatting + send (all no-ops
  if `TELEGRAM_BOT_TOKEN` unset)
- `main.py` — entrypoint

## License

MIT — see [LICENSE](LICENSE).
