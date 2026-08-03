"""Telegram bot integration: sends the job digest to subscribers and lets
them pick job categories, custom skills, and a notification mode via chat
commands and inline buttons.

Polled once per script run (getUpdates with timeout=0, a non-blocking
"anything since last time?" check) rather than a persistent long-poll or
webhook — that fits the same GitHub Actions cron model as the email digest,
no always-on process required. A preference change sent to the bot takes
effect on the next run (scheduled, or a manual workflow_dispatch).

Three notification modes (schedule.telegram_due(), checked once per hourly
workflow run, decides when "scheduled" fires — see main.py):
  - scheduled (default): full digest only when schedule.telegram_due() is
    true (deliver_scheduled).
  - queue: an immediate lightweight ping per job (ping_queue), *plus* the
    full entry at the next scheduled fire, same as scheduled subscribers get.
  - instant: full entry immediately, on whichever run first finds it
    (deliver_instant) — never repeated at the next scheduled fire.
"""
import json
import os
import re
import urllib.request

import config

API_URL = "https://api.telegram.org/bot{token}/{method}"

DEFAULT_CATEGORIES = list(config.TELEGRAM_CATEGORY_LABELS)

MODE_LABELS = {"scheduled": "Scheduled", "queue": "Queue", "instant": "Instant"}

HELP_TEXT = (
    "<b>Job Digest Bot</b>\n\n"
    "/preferences – choose which job categories you want\n"
    "/skills – set custom skill keywords, e.g. /skills Rust, gRPC\n"
    "/scheduled – notify me only at the normal digest times (default)\n"
    "/queue – early heads-up ping now, full entry at the normal digest time\n"
    "/instant – notify me as soon as a match is found (~hourly checks)\n"
    "/status – show your current settings\n"
    "/pause – stop receiving digests\n"
    "/resume – start receiving digests again\n"
    "/help – show this message\n\n"
    "Note: categories and /skills both only filter jobs that already "
    "passed the bot's own DevOps/Cloud/AI skill match — they narrow that "
    "set, they don't widen it."
)


def _api(method, **params):
    url = API_URL.format(token=config.TELEGRAM_BOT_TOKEN, method=method)
    data = json.dumps(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def load_state():
    if not os.path.exists(config.TELEGRAM_STATE_FILE):
        return {"update_offset": 0, "subscribers": {}}
    with open(config.TELEGRAM_STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(config.TELEGRAM_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _category_keyboard(selected):
    rows = [
        [{"text": f"{'✅' if key in selected else '⬜'} {label}", "callback_data": f"toggle:{key}"}]
        for key, label in config.TELEGRAM_CATEGORY_LABELS.items()
    ]
    rows.append([{"text": "Done", "callback_data": "done"}])
    return {"inline_keyboard": rows}


def _send(chat_id, text, keyboard=None):
    kwargs = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if keyboard:
        kwargs["reply_markup"] = keyboard
    _api("sendMessage", **kwargs)


def _get_subscriber(state, chat_id):
    sub = state["subscribers"].setdefault(
        str(chat_id),
        {
            "categories": list(DEFAULT_CATEGORIES),
            "enabled": True,
            "custom_skills": [],
            "notification_mode": "scheduled",
        },
    )
    sub.setdefault("custom_skills", [])
    sub.setdefault("notification_mode", "scheduled")
    return sub


def _handle_message(state, chat_id, text):
    sub = _get_subscriber(state, chat_id)
    text = (text or "").strip()

    if text.startswith("/start"):
        _send(
            chat_id,
            "Welcome! You're subscribed to the job digest. Pick which "
            "categories you want alerts for:",
            _category_keyboard(sub["categories"]),
        )
    elif text.startswith("/preferences"):
        _send(chat_id, "Your job categories:", _category_keyboard(sub["categories"]))
    elif text.startswith("/skills"):
        arg = text[len("/skills"):].strip()
        if not arg:
            current = ", ".join(sub["custom_skills"]) or "none set"
            _send(
                chat_id,
                f"Your custom skill keywords: {current}\n\n"
                "Set with: /skills Rust, gRPC, Postgres\n"
                "Clear with: /skills clear",
            )
        elif arg.lower() == "clear":
            sub["custom_skills"] = []
            _send(chat_id, "Cleared your custom skill keywords.")
        else:
            terms = [t.strip() for t in arg.split(",") if t.strip()]
            sub["custom_skills"] = terms
            _send(
                chat_id,
                "Custom skill keywords set: " + ", ".join(terms) + "\n\n"
                "You'll now also get jobs mentioning these, on top of your "
                "selected categories.",
            )
    elif text.startswith("/scheduled"):
        sub["notification_mode"] = "scheduled"
        _send(
            chat_id,
            "✅ Scheduled mode is enabled.\n\n"
            "You will receive job notifications according to the normal "
            "posting schedule.",
        )
    elif text.startswith("/queue"):
        sub["notification_mode"] = "queue"
        _send(
            chat_id,
            "✅ Queue mode is enabled.\n\n"
            "You'll receive jobs as soon as they enter the notification "
            "queue, before the scheduled notification is triggered.",
        )
    elif text.startswith("/instant"):
        sub["notification_mode"] = "instant"
        _send(
            chat_id,
            "✅ Instant mode is enabled.\n\n"
            "You'll receive matching job alerts as soon as new jobs become "
            "available.",
        )
    elif text.startswith("/status"):
        mode_label = MODE_LABELS.get(sub["notification_mode"], "Scheduled")
        state_txt = "Enabled ✅" if sub["enabled"] else "Paused ⏸"
        cat_lines = "\n".join(f"• {config.TELEGRAM_CATEGORY_LABELS[c]}" for c in sub["categories"]) or "• none selected"
        custom = ", ".join(sub["custom_skills"]) or "none"
        _send(
            chat_id,
            "\U0001f4ca <b>Your Settings</b>\n\n"
            f"Notification Mode:\n• {mode_label}\n\n"
            f"Notifications: {state_txt}\n\n"
            f"Selected Categories:\n{cat_lines}\n\n"
            f"Custom skills: {custom}",
        )
    elif text.startswith("/pause"):
        sub["enabled"] = False
        _send(chat_id, "Paused. Send /resume anytime to start getting digests again.")
    elif text.startswith("/resume"):
        sub["enabled"] = True
        _send(chat_id, "Resumed — you'll get the next digest that matches your categories.")
    elif text.startswith("/help"):
        _send(chat_id, HELP_TEXT)
    else:
        _send(chat_id, "Not sure what you mean.\n\n" + HELP_TEXT)


def _handle_callback(state, callback):
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback["data"]
    sub = _get_subscriber(state, chat_id)

    if data == "done":
        _api("answerCallbackQuery", callback_query_id=callback["id"], text="Saved")
        _send(chat_id, "Saved.\n\n" + HELP_TEXT)
        return

    if data.startswith("toggle:"):
        key = data.split(":", 1)[1]
        if key in sub["categories"]:
            sub["categories"].remove(key)
        else:
            sub["categories"].append(key)
        _api("answerCallbackQuery", callback_query_id=callback["id"])
        _api(
            "editMessageReplyMarkup",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=_category_keyboard(sub["categories"]),
        )


def poll_commands():
    """Apply any Telegram messages sent since the last run. No-op if the
    bot token isn't configured."""
    if not config.TELEGRAM_BOT_TOKEN:
        print("Telegram: TELEGRAM_BOT_TOKEN not set, skipping.")
        return
    state = load_state()
    result = _api("getUpdates", offset=state["update_offset"], timeout=0)
    if not result or not result.get("ok"):
        print(f"Telegram: getUpdates returned an unexpected response: {result}")
        return
    updates = result["result"]
    print(f"Telegram: {len(updates)} update(s) to process, {len(state['subscribers'])} known subscriber(s).")
    for update in updates:
        state["update_offset"] = update["update_id"] + 1
        if "message" in update:
            _handle_message(state, update["message"]["chat"]["id"], update["message"].get("text", ""))
        elif "callback_query" in update:
            _handle_callback(state, update["callback_query"])
    save_state(state)


def _escape(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_job(job):
    skills = ", ".join(job.get("skills_matched", []))
    return (
        f"\U0001f4bc <b>{_escape(job['title'])}</b>\n"
        f"\U0001f3e2 {_escape(job['company'])} · {_escape(job['source'])}\n"
        f"\U0001f9f0 {_escape(skills)}"
    )


def _apply_keyboard(job):
    return {"inline_keyboard": [[{"text": "\U0001f517 Apply", "url": job["url"]}]]}


def _format_queue_ping(job):
    return (
        "\U0001f4e5 <b>Job Added to Queue</b>\n\n"
        f"\U0001f3e2 Company: {_escape(job['company'])}\n"
        f"\U0001f4bc Role: {_escape(job['title'])}\n"
        "\U0001f4cd Remote\n\n"
        "Status: Waiting for scheduled notification\n\n"
        "This job is now in your queue."
    )


def _matches_custom_skills(custom_skills, text):
    text = (text or "").lower()
    return any(re.search(r"\b" + re.escape(term.lower()) + r"\b", text) for term in custom_skills)


def _matching_jobs(sub, jobs):
    allowed_skills = set()
    for cat in sub.get("categories", []):
        allowed_skills.update(config.TELEGRAM_CATEGORIES.get(cat, []))
    custom_skills = sub.get("custom_skills", [])

    if not allowed_skills and not custom_skills:
        return list(jobs)
    return [
        j for j in jobs
        if (allowed_skills & set(j.get("skills_matched", [])))
        or (custom_skills and _matches_custom_skills(custom_skills, j.get("text_for_match", "")))
    ]


def _send_job_cards(chat_id, jobs):
    count_text = f"{len(jobs)} new matching job{'s' if len(jobs) != 1 else ''}"
    _send(chat_id, f"\U0001f680 <b>{count_text}</b>")
    for job in jobs:
        _send(chat_id, _format_job(job), _apply_keyboard(job))


def deliver_instant(new_jobs):
    """Send this run's newly discovered jobs immediately to instant-mode
    subscribers. Safe to call on every run — each job only ever appears in
    new_jobs once, system-wide, so there's no risk of a double-send later
    at a scheduled fire."""
    if not config.TELEGRAM_BOT_TOKEN or not new_jobs:
        return
    state = load_state()
    for chat_id, sub in state["subscribers"].items():
        if not sub.get("enabled", True) or sub.get("notification_mode") != "instant":
            continue
        matched = _matching_jobs(sub, new_jobs)
        if matched:
            _send_job_cards(chat_id, matched)


def ping_queue(new_jobs):
    """Send a lightweight heads-up for this run's newly discovered jobs to
    queue-mode subscribers. The full entry follows later, at the next
    scheduled fire, via deliver_scheduled(). Safe to call on every run."""
    if not config.TELEGRAM_BOT_TOKEN or not new_jobs:
        return
    state = load_state()
    for chat_id, sub in state["subscribers"].items():
        if not sub.get("enabled", True) or sub.get("notification_mode") != "queue":
            continue
        for job in _matching_jobs(sub, new_jobs):
            _send(chat_id, _format_queue_ping(job))


def deliver_scheduled(pending_jobs):
    """Flush everything accumulated since the last scheduled fire to
    scheduled- and queue-mode subscribers. Call only when
    schedule.telegram_due() is true."""
    if not config.TELEGRAM_BOT_TOKEN or not pending_jobs:
        return
    state = load_state()
    for chat_id, sub in state["subscribers"].items():
        if not sub.get("enabled", True) or sub.get("notification_mode") not in ("scheduled", "queue"):
            continue
        matched = _matching_jobs(sub, pending_jobs)
        if matched:
            _send_job_cards(chat_id, matched)
