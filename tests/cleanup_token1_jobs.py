# cleanup_token1_jobs.py
import requests
import time

# Read token 1 from .env
with open(".env", "r") as f:
    lines = [line.strip() for line in f if line.strip()]
    cronjob_token = lines[0]

base_url = "https://api.cron-job.org"
headers = {
    "Authorization": f"Bearer {cronjob_token}",
    "Content-Type": "application/json"
}

print("Getting jobs from token 1...")
resp = requests.get(f"{base_url}/jobs", headers=headers, timeout=10)
jobs = resp.json().get("jobs", [])

prefix = "episode-tinker-air"
for job in jobs:
    title = job.get("title", "")
    if title.startswith(prefix):
        job_id = job["jobId"]
        print(f"Deleting job {job_id}: {title}")
        requests.delete(f"{base_url}/jobs/{job_id}", headers=headers, timeout=10)
        time.sleep(13)  # Respect rate limits

print("Done cleaning up token 1 jobs!")
