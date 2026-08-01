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


def fetch_arbeitnow():
    raw = _get("https://www.arbeitnow.com/api/job-board-api")
    data = json.loads(raw)
    jobs = []
    for item in data.get("data", []):
        jobs.append({
            "id": f"arbeitnow-{item['slug']}",
            "title": item.get("title", "Untitled"),
            "company": item.get("company_name", "Unknown"),
            "url": item.get("url", ""),
            "source": "Arbeitnow",
            "posted": str(item.get("created_at", "")),
            "text_for_match": " ".join([
                item.get("title", ""),
                item.get("description", ""),
                " ".join(item.get("tags", [])),
                item.get("location", ""),
            ]),
        })
    return jobs


def fetch_jobicy():
    raw = _get("https://jobicy.com/api/v2/remote-jobs?count=50")
    data = json.loads(raw)
    jobs = []
    for item in data.get("jobs", []):
        jobs.append({
            "id": f"jobicy-{item['id']}",
            "title": item.get("jobTitle", "Untitled"),
            "company": item.get("companyName", "Unknown"),
            "url": item.get("url", ""),
            "source": "Jobicy",
            "posted": item.get("pubDate", ""),
            "text_for_match": " ".join([
                item.get("jobTitle", ""),
                item.get("jobExcerpt", ""),
                " ".join(item.get("jobIndustry", []) or []),
                " ".join(item.get("jobType", []) or []),
            ]),
        })
    return jobs


def fetch_working_nomads():
    raw = _get("https://www.workingnomads.com/api/exposed_jobs/")
    data = json.loads(raw)
    jobs = []
    for item in data:
        url = item.get("url", "")
        job_id = re.sub(r"\W+", "-", url.lower()).strip("-") or url
        jobs.append({
            "id": f"workingnomads-{job_id}",
            "title": item.get("title", "Untitled"),
            "company": item.get("company_name", "Unknown"),
            "url": url,
            "source": "Working Nomads",
            "posted": item.get("pub_date", ""),
            "text_for_match": " ".join([
                item.get("title", ""),
                item.get("description", ""),
                " ".join(item.get("tags", []) or []),
                item.get("category_name", ""),
            ]),
        })
    return jobs


def fetch_himalayas():
    raw = _get("https://himalayas.app/jobs/api")
    data = json.loads(raw)
    jobs = []
    for item in data.get("jobs", []):
        guid = item.get("guid", "")
        job_id = re.sub(r"\W+", "-", guid.lower()).strip("-") or guid
        jobs.append({
            "id": f"himalayas-{job_id}",
            "title": item.get("title", "Untitled"),
            "company": item.get("companyName", "Unknown"),
            "url": item.get("applicationLink") or guid,
            "source": "Himalayas",
            "posted": str(item.get("pubDate", "")),
            "text_for_match": " ".join([
                item.get("title", ""),
                item.get("excerpt", ""),
                item.get("description", ""),
                " ".join(item.get("categories", []) or []),
            ]),
        })
    return jobs


SOURCE_FUNCS = {
    "remoteok": fetch_remoteok,
    "wwr_devops": fetch_wwr_devops,
    "wwr_programming": fetch_wwr_programming,
    "arbeitnow": fetch_arbeitnow,
    "jobicy": fetch_jobicy,
    "working_nomads": fetch_working_nomads,
    "himalayas": fetch_himalayas,
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
