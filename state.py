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
