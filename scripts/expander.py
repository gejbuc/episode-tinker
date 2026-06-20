# scripts/expander.py
"""
Expander script that:
1. Loads config and enabled interest modules
2. Gets upcoming episode events
3. Schedules one-time cron-job.org jobs for those episodes
"""
import os
import sys
import argparse
import yaml
import pytz
from pathlib import Path
from datetime import datetime, timedelta, timezone
from importlib import import_module

# Add repo root to Python path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONFIG_PATH = REPO_ROOT / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_interests(config: dict) -> list:
    interests = []
    for interest_key, interest_config in config.get("interests", {}).items():
        if not interest_config.get("enabled", False):
            continue
        try:
            module = import_module(f"interests.{interest_key}")
            interests.append((interest_key, module, interest_config))
        except Exception as e:
            print(f"⚠️  Skipping disabled or missing interest '{interest_key}': {e}")
    return interests


def get_existing_job_ids(cronjob_token: str) -> set:
    """Get all existing episode alert job titles to avoid duplicates."""
    from scripts.scheduler import CRONJOB_API, _headers, API_CALL_DELAY
    import time
    import requests

    existing_titles = set()
    resp = requests.get(f"{CRONJOB_API}/jobs", headers=_headers(cronjob_token), timeout=10)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    for job in jobs:
        title = job.get("title", "")
        existing_titles.add(title)
    return existing_titles


def run_expander(config: dict):
    from scripts.scheduler import (
        cleanup_stale_jobs,
        schedule_episode_alert,
        EPISODE_JOB_TITLE_PREFIX,
    )

    tz_name = config["notifications"].get("timezone", "UTC")
    tz = pytz.timezone(tz_name)
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(days=14)  # Look ahead 14 days
    print(f"[expander] Expanding episodes from now until {window_end.astimezone(tz).strftime('%Y-%m-%d %H:%M')} ({tz_name})")

    cronjob_token = os.getenv("CRONJOB_TOKEN")
    github_token = os.getenv("GITHUB_TOKEN")

    if not cronjob_token or not github_token:
        print("[expander] Missing CRONJOB_TOKEN or GITHUB_TOKEN, skipping job scheduling")
        return

    # Step 1: Clean up old jobs
    cleanup_stale_jobs(cronjob_token)

    # Step 2: Load existing jobs to avoid duplicates
    existing_titles = get_existing_job_ids(cronjob_token)

    # Step 3: Load interests and collect events
    interests = load_interests(config)
    events_by_id = {}
    scheduled_idx = 0

    for interest_key, module, interest_config in interests:
        print(f"\n[expander] Loading interest: {interest_key}")
        try:
            events = module.get_events(interest_config)
        except Exception as e:
            print(f"  ⚠️  Failed to get events for {interest_key}: {e}")
            continue

        for event in events:
            event_id = event.get("id")
            if not event_id:
                continue
            if event.get("start_time") is None:
                continue
            if event["start_time"] < now:
                continue
            if event["start_time"] > window_end:
                continue

            events_by_id[event_id] = event

    # Step 4: Schedule new jobs
    for event_id, event in sorted(events_by_id.items(), key=lambda x: x[1]["start_time"]):
        job_title = f"{EPISODE_JOB_TITLE_PREFIX}:{event_id[:40]}"
        if job_title in existing_titles:
            print(f"\n[expander] Skipping already scheduled event: {event['name']}")
            continue

        print(f"\n[expander] Scheduling event: {event['name']}")

        schedule_episode_alert(
            event_id=event_id,
            title=event.get("title", "Episode"),
            message=event.get("message", f"New episode aired: {event['name']}"),
            air_time=event["start_time"],
            cronjob_token=cronjob_token,
            github_token=github_token,
            stagger_minutes=scheduled_idx,
        )
        scheduled_idx += 1

    print(f"\n[expander] Done. Scheduled {scheduled_idx} new episode alerts.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to config file", default=str(CONFIG_PATH))
    args = parser.parse_args()
    config = load_config()
    run_expander(config)
