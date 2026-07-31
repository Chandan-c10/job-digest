"""Fetchers for each job source. Each returns a list of dicts with keys:
id, title, company, url, source, posted (str).
A network or parse failure in one source must never take down the others.
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = "Mozilla/5.0 (job-digest personal script)"


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_remoteok():
    raw = _get("https://remoteok.com/api")
    data = json.loads(raw)
    jobs = []
    for item in data:
        if "id" not in item:
            continue  # first element is the API legal notice, not a job
        jobs.append({
            "id": f"remoteok-{item['id']}",
            "title": item.get("position", "Untitled"),
            "company": item.get("company", "Unknown"),
            "url": item.get("url") or f"https://remoteok.com/remote-jobs/{item['id']}",
            "source": "RemoteOK",
            "posted": item.get("date", ""),
            "text_for_match": " ".join([
                item.get("position", ""),
                item.get("description", ""),
                " ".join(item.get("tags", [])),
            ]),
        })
    return jobs


def _fetch_wwr_category(slug, label):
    raw = _get(f"https://weworkremotely.com/categories/{slug}.rss")
    root = ET.fromstring(raw)
    jobs = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "")
        pub_date = (item.findtext("pubDate") or "").strip()
        # WWR titles are usually "Company: Job Title"
        company = title.split(":", 1)[0].strip() if ":" in title else "Unknown"
        job_id = re.sub(r"\W+", "-", link.lower()).strip("-") or link
        jobs.append({
            "id": f"wwr-{job_id}",
            "title": title,
            "company": company,
            "url": link,
            "source": f"We Work Remotely ({label})",
            "posted": pub_date,
            "text_for_match": title + " " + description,
        })
    return jobs


def fetch_wwr_devops():
    return _fetch_wwr_category("remote-devops-sysadmin-jobs", "DevOps/Sysadmin")


def fetch_wwr_programming():
    return _fetch_wwr_category("remote-programming-jobs", "Programming")


SOURCE_FUNCS = {
    "remoteok": fetch_remoteok,
    "wwr_devops": fetch_wwr_devops,
    "wwr_programming": fetch_wwr_programming,
}


def fetch_all(source_names):
    """Fetch every requested source, isolating failures per-source."""
    jobs = []
    errors = []
    for name in source_names:
        func = SOURCE_FUNCS.get(name)
        if func is None:
            errors.append(f"{name}: unknown source")
            continue
        try:
            jobs.extend(func())
        except Exception as exc:  # noqa: BLE001 - one bad source shouldn't kill the run
            errors.append(f"{name}: {exc}")
    return jobs, errors
