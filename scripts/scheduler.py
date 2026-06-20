# scripts/scheduler.py
"""
Manages one-time cron-job.org jobs for episode alerts.

Called by the expander run after it finds upcoming episodes.
For each episode it creates cron-job.org jobs that trigger GitHub workflows:
  - episode alert at (air_time + 5 minutes)

Requires env vars:
  CRONJOB_TOKEN  — cron-job.org API bearer token
  GITHUB_TOKEN   — fine-grained PAT with actions:write on this repo
"""
import os
import time
import json
import requests
from datetime import datetime, timedelta

CRONJOB_API = "https://api.cron-job.org"
GITHUB_REPO = "gejbuc/episode-tinker"
EPISODE_ALERT_WORKFLOW_ID = "299252925"

# Tag prefix so we can find and clean up our jobs
EPISODE_JOB_TITLE_PREFIX = "episode-tinker-air"

# Delay between job creation calls to respect cron-job.org's PUT rate limit:
# PUT /jobs is capped at 5 requests per minute, so we need >=12s between each.
API_CALL_DELAY = 13  # seconds


def _headers(cronjob_token: str) -> dict:
    return {"Authorization": f"Bearer {cronjob_token}"}


def _patch_payload(github_token: str, dispatch_body: dict = None) -> dict:
    """Common PATCH body that attaches GitHub auth headers to a job."""
    body = dispatch_body or {"ref": "master"}
    return {
        "job": {
            "notification": {
                "onFailure": True,
                "onFailureCount": 1,
                "onSuccess": False,
                "onDisable": False,
            },
            "extendedData": {
                "headers": {
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {github_token}",
                    "User-Agent": "cron-job-org-trigger",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                "body": json.dumps(body),
            },
        }
    }


def _create_job(label: str, body: dict, github_token: str, cronjob_token: str, dispatch_body: dict = None) -> bool:
    """
    PUT a new job then PATCH its headers/body in a second request (API requires two steps).
    Sleeps after completion to respect cron-job.org burst rate limits.
    Returns True on full success, False on any failure.
    """
    resp = requests.put(
        f"{CRONJOB_API}/jobs",
        json=body,
        headers=_headers(cronjob_token),
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"  ✗ Failed to create job for '{label}': HTTP {resp.status_code} {resp.text}")
        time.sleep(API_CALL_DELAY)
        return False

    job_id = resp.json().get("jobId")
    fire_info = body["job"]["schedule"]
    print(f"  ⏰ Created job {job_id} for '{label}' at {fire_info['hours'][0]:02d}:{fire_info['minutes'][0]:02d} UTC")

    patch_resp = requests.patch(
        f"{CRONJOB_API}/jobs/{job_id}",
        json=_patch_payload(github_token, dispatch_body),
        headers=_headers(cronjob_token),
        timeout=10,
    )
    if patch_resp.status_code == 200:
        print(f"  ✓ Headers patched onto job {job_id}")
    else:
        print(f"  ✗ Header patch failed for job {job_id}: HTTP {patch_resp.status_code}")

    time.sleep(API_CALL_DELAY)
    return patch_resp.status_code == 200


def cleanup_stale_jobs(cronjob_token: str):
    """Delete any leftover episode alert jobs from previous runs."""
    resp = requests.get(f"{CRONJOB_API}/jobs", headers=_headers(cronjob_token), timeout=10)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    for job in jobs:
        title = job.get("title", "")
        if title.startswith(EPISODE_JOB_TITLE_PREFIX):
            job_id = job["jobId"]
            requests.delete(f"{CRONJOB_API}/jobs/{job_id}", headers=_headers(cronjob_token), timeout=10)
            print(f"  🗑 Deleted stale job {job_id}: {title}")
            time.sleep(API_CALL_DELAY)


def schedule_episode_alert(
    event_id: str,
    event_name: str,
    air_time: datetime,
    cronjob_token: str,
    github_token: str,
    alert_delay_minutes: int = 5,
    stagger_minutes: int = 0,
    dispatch_inputs: dict = None,
):
    """
    Create a one-time cron-job.org job that fires `alert_delay_minutes` after air_time.
    stagger_minutes shifts the fire time by +N minutes so simultaneous events don't
    collide on the same hour:minute slot.
    The job triggers the GitHub episode alert workflow via workflow_dispatch.
    """
    fire_time = air_time + timedelta(minutes=alert_delay_minutes) + timedelta(minutes=stagger_minutes)

    # Build dispatch body
    dispatch_body = {"ref": "master"}
    if dispatch_inputs:
        dispatch_body["inputs"] = dispatch_inputs

    # cron-job.org requires wildcard mdays/months so the job can fire on any day.
    # Jobs are deleted by cleanup_stale_jobs() on the next expander run before they repeat.
    body = {
        "job": {
            "title": f"{EPISODE_JOB_TITLE_PREFIX}:{event_id[:40]}",
            "url": f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{EPISODE_ALERT_WORKFLOW_ID}/dispatches",
            "enabled": True,
            "saveResponses": True,
            "requestMethod": 1,  # POST
            "requestTimeout": 30,
            "schedule": {
                "timezone": "UTC",
                "hours":   [fire_time.hour],
                "minutes": [fire_time.minute],
                "mdays":   [-1],
                "months":  [-1],
                "wdays":   [-1],
                "expiresAt": 0,
            },
        }
    }
    _create_job(event_name, body, github_token, cronjob_token, dispatch_body)
