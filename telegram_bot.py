"""Telegram bot integration: sends the job digest to subscribers and lets
them pick job categories via chat commands and inline buttons.

Polled once per script run (getUpdates with timeout=0, a non-blocking
"anything since last time?" check) rather than a persistent long-poll or
webhook — that fits the same GitHub Actions cron model as the email digest,
no always-on process required. A preference change sent to the bot takes
effect on the next run (scheduled, or a manual workflow_dispatch).
"""
import json
import os
import urllib.request

import config

API_URL = "https://api.telegram.org/bot{token}/{method}"

DEFAULT_CATEGORIES = list(config.TELEGRAM_CATEGORY_LABELS)

HELP_TEXT = (
    "<b>Job Digest Bot</b>\n\n"
    "/preferences – choose which job categories you want\n"
    "/status – show your current settings\n"
    "/pause – stop receiving digests\n"
    "/resume – start receiving digests again\n"
    "/help – show this message"
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
    return state["subscribers"].setdefault(
        str(chat_id), {"categories": list(DEFAULT_CATEGORIES), "enabled": True}
    )


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
    elif text.startswith("/status"):
        cats = ", ".join(config.TELEGRAM_CATEGORY_LABELS[c] for c in sub["categories"]) or "none selected"
        state_txt = "active" if sub["enabled"] else "paused"
        _send(chat_id, f"Status: <b>{state_txt}</b>\nCategories: {cats}")
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
        return
    state = load_state()
    result = _api("getUpdates", offset=state["update_offset"], timeout=0)
    if not result or not result.get("ok"):
        return
    for update in result["result"]:
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


def send_digest(jobs):
    """Send new matching jobs to every enabled subscriber, filtered to the
    categories each subscriber picked. No-op if the bot token isn't
    configured or there are no jobs to send."""
    if not config.TELEGRAM_BOT_TOKEN or not jobs:
        return
    state = load_state()
    for chat_id, sub in state["subscribers"].items():
        if not sub.get("enabled", True):
            continue
        allowed_skills = set()
        for cat in sub.get("categories", []):
            allowed_skills.update(config.TELEGRAM_CATEGORIES.get(cat, []))
        matched = [j for j in jobs if allowed_skills & set(j.get("skills_matched", []))] if allowed_skills else jobs
        if not matched:
            continue
        count_text = f"{len(matched)} new matching job{'s' if len(matched) != 1 else ''}"
        _send(chat_id, f"\U0001f680 <b>{count_text}</b>")
        for job in matched:
            _send(chat_id, _format_job(job), _apply_keyboard(job))
