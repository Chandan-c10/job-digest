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

1. `sources.py` fetches postings from 8 public sources (RemoteOK, We Work
   Remotely, Arbeitnow, Jobicy, Working Nomads, Himalayas, Internshala) —
   no login required for any of them.
2. `skills.py` matches each posting's text against the skill tiers in
   `config.py` (word-boundary matching, so short terms like "Git" don't
   false-positive on "Legit").
3. `experience.py` drops postings with senior/lead/staff/director-type
   titles, or that ask for a years-of-experience outside
   `config.MIN_YEARS`–`config.MAX_YEARS`.
4. `main.py` also applies `config.JOB_TYPES` and `config.LOCATIONS` if
   you've set them — both optional, both empty (no filtering) by default.
5. `state.py` remembers which postings you've already been shown
   (`seen_jobs.json`), so you're never re-notified.
6. `notify.py` emails you the digest via Gmail SMTP.

## Setup

Everything you configure lives in **`config.py`** — one file, nothing to
hunt for elsewhere:

1. Fork/clone this repo.
2. Edit `config.py`:
   - `PRIMARY_SKILLS` / `SECONDARY_SKILLS` / `AI_SKILLS` — your skills,
     and `MIN_SKILL_MATCHES` — how many hits a posting needs to count.
   - `MIN_YEARS` / `MAX_YEARS` — your experience range.
   - `JOB_TYPES` / `LOCATIONS` — optional; leave empty to skip. Useful for
     Internshala's on-site listings since most other sources are
     remote-only anyway.
   - `EMAIL_SCHEDULE_IST` / `TELEGRAM_INTERVAL_HOURS` (or
     `TELEGRAM_SCHEDULE_IST`) — when things fire, in IST. See "Timezone
     handling" below — you never need to touch the workflow file for this.
3. If you skip step 2 entirely (all skill lists left empty), the script
   fails loudly with a clear error instead of silently finding nothing —
   go back and fill in at least one skill list.
4. Create a Gmail App Password for whichever account will send the digest
   (Google Account → Security → 2-Step Verification → App Passwords).
5. Run it locally to test. `GITHUB_EVENT_NAME=workflow_dispatch` makes it
   send immediately regardless of the clock, same as a manual "Run
   workflow" on GitHub — without it, a local run only actually sends
   something if it happens to land within an hour of a time in
   `config.py`:

   ```bash
   export JOB_DIGEST_EMAIL="you@gmail.com"
   export JOB_DIGEST_APP_PASSWORD="your-16-char-app-password"
   export JOB_DIGEST_RECIPIENT="you@gmail.com"   # defaults to JOB_DIGEST_EMAIL's value if unset
   export GITHUB_EVENT_NAME="workflow_dispatch"
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

2. Uncomment the `schedule:` block in the workflow file — that's the
   *only* thing you ever touch there. Your actual send times go in
   `config.py` instead (next section).
3. Commit and push. It'll run on GitHub's infrastructure — no need for your
   own machine to be on.

> **No server needed.** GitHub itself runs `python3 main.py` on a fixed
> hourly check and throws the runner away when it's done — nothing to
> host, nothing to maintain. Free on public repos; on private repos it
> uses a small slice of GitHub's 2,000 free minutes/month (see below).

<details>
<summary>Exact free-tier minutes, if you're curious</summary>

Public repos get unlimited Actions minutes, $0. Private repos get 2,000
free minutes/month. Each run finishes in well under a minute, but Actions
bills a minimum of 1 minute per run regardless — the hourly check-in costs
~720 min/month (~36% of the budget). Comfortably inside the free
allowance with room to spare, running 24/7.

</details>

### Timezone handling

Set your actual send times in **`config.py`**, not the workflow file:

```python
EMAIL_SCHEDULE_IST = ["9:00 AM", "6:00 PM"]   # exact clock times
TELEGRAM_INTERVAL_HOURS = 2                    # or fixed times, see config.py
```

Every hourly check-in, `schedule.py` asks "is now within an hour of one of
these?" and only sends when a configured slot is due — each slot fires at
most once a day (tracked in `schedule_state.json`), no matter how many
times the hourly check-in runs past it. **Change a time by editing
`config.py` — no workflow file, no cron, no UTC math, ever.**

<details>
<summary>Why the workflow file still needs one cron line at all</summary>

GitHub's `schedule:` trigger is evaluated by GitHub's own scheduler
*before* `main.py` ever runs — it has to already know when to wake up a
runner, so it can't ask your Python code "what time should I run at?"
That's why one fixed, frequent check-in (hourly) stays in the workflow
file; `config.py` + `schedule.py` decide what that check-in actually
*does* each time, entirely in Python.

The hourly interval is deliberately off `:00`/`:30` — GitHub's scheduler
gets congested at those popular marks, which has been known to delay a
run by 3+ hours. If you want a *tighter* check interval (e.g. every 15
min, for closer-to-exact Telegram timing), edit the `cron:` line and keep
the new minute off `:00`/`:15`/`:30`/`:45` for the same reason —
`ist_to_cron.py` can help pick one.

</details>

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

Pick one with `/scheduled` (default), `/queue`, or `/instant`. `/status`
shows your current mode.

| Command | Mode | Behavior |
|---|---|---|
| `/scheduled` (default) | Scheduled | Full digest only when `TELEGRAM_INTERVAL_HOURS`/`TELEGRAM_SCHEDULE_IST` (in `config.py`) says it's due. |
| `/queue` | Queue | An early "added to queue" ping the moment a job is found, **plus** the full entry at the next scheduled fire. |
| `/instant` | Instant | The full entry immediately, whenever a job is first found — never repeated later. |

Entirely optional: leave `TELEGRAM_BOT_TOKEN` unset and `telegram_bot.py`
no-ops everywhere it's called — the email digest works exactly as before.

<details>
<summary>How "instant" actually works, and other details</summary>

**No true push.** Every hourly check-in fetches jobs and pings
instant/queue subscribers regardless of whether email or the scheduled
Telegram digest is due this run. So "instant" really means "within an
hour" (the check-in interval), not real-time push. Scheduled-mode
subscribers are completely unaffected by runs where their own schedule
isn't due.

**Why a check-in run can't cause a scheduled fire to miss anything:** a
job is marked "seen" in `seen_jobs.json` the first time *any* run fetches
it, so it only ever counts as "new" once, system-wide. Every newly-found
job is *also* appended to `pending_telegram_jobs.json` regardless of
whether Telegram's schedule is due this exact run. When it does become
due, that whole accumulated list gets flushed and cleared — so a
scheduled-mode subscriber still gets everything found since the last
fire, not just this run's own finds. Instant-mode delivery, by contrast,
only ever uses that specific run's own finds, so instant subscribers
never see a repeat. (Email works the same way, via its own separate
`pending_email_jobs.json` — the two schedules are fully independent.)

**Important limit:** categories and `/skills` both only *narrow* the
digest — they can't widen it. Every job still has to clear the global
`MIN_SKILL_MATCHES`-across-the-tiers filter in `main.py` first. So a
category or `/skills` keyword surfaces a posting only if it also already
scored high enough on your `PRIMARY_SKILLS`/`SECONDARY_SKILLS`/`AI_SKILLS`.

**Timing:** no webhook, no always-on server. `telegram_bot.poll_commands()`
checks for new Telegram messages once per run, so a `/preferences`,
`/skills`, or mode change takes effect on the next hourly check-in — or
immediately if you manually trigger the workflow right after messaging
the bot.

**State:** `telegram_state.json`, `pending_email_jobs.json`,
`pending_telegram_jobs.json`, and `schedule_state.json` (which configured
times have already fired today) persist between runs the same way
`seen_jobs.json` does — via `actions/cache`, gitignored, never committed.

</details>

## Why not more sources?

LinkedIn, Naukri, Indeed, Glassdoor, and a handful of others were tested
and rejected (blocked, JS-only, or too fragile to scrape reliably).

<details>
<summary>Full list of what was tried and why it didn't make the cut</summary>

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

</details>

## Files

- `config.py` — every setting you'd want to change: skills, experience
  range, job type/location filters, when things fire, sources, email
  settings, Telegram categories
- `schedule.py` — decides if "now" matches `config.py`'s
  `EMAIL_SCHEDULE_IST`/`TELEGRAM_INTERVAL_HOURS` (or `TELEGRAM_SCHEDULE_IST`),
  with per-day dedup so a slot fires at most once
- `ist_to_cron.py` — helper for changing the workflow's own check-in
  interval (rarely needed — see "Timezone handling")
- `sources.py` — per-source fetchers (RemoteOK, We Work Remotely, Arbeitnow,
  Jobicy, Working Nomads, Himalayas, Internshala)
- `skills.py` — shared word-boundary skill matching
- `experience.py` — seniority/years-of-experience filter (reads
  `config.MIN_YEARS`/`config.MAX_YEARS`)
- `state.py` — seen-job id persistence and the pending-jobs accumulators
  (`pending_email_jobs.json`, `pending_telegram_jobs.json`) between
  scheduled fires
- `notify.py` — digest formatting + SMTP send
- `telegram_bot.py` — optional Telegram channel: command polling, category
  picker, notification-mode handling, digest formatting + send (all no-ops
  if `TELEGRAM_BOT_TOKEN` unset)
- `main.py` — entrypoint

## License

MIT — see [LICENSE](LICENSE).
