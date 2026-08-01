import json
import os


def load_seen(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r") as f:
        return set(json.load(f))


def save_seen(path, seen_ids):
    with open(path, "w") as f:
        json.dump(sorted(seen_ids), f, indent=2)


def load_pending(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def save_pending(path, jobs):
    with open(path, "w") as f:
        json.dump(jobs, f, indent=2)
