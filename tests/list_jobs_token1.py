# list_jobs_token1.py
import requests
import json

# Read token 1 from .env
with open(".env", "r") as f:
    lines = [line.strip() for line in f if line.strip()]
    cronjob_token = lines[0]

base_url = "https://api.cron-job.org"
headers = {
    "Authorization": f"Bearer {cronjob_token}",
    "Content-Type": "application/json"
}

print("Fetching jobs using token 1...")
resp = requests.get(f"{base_url}/jobs", headers=headers, timeout=10)

if resp.status_code == 200:
    jobs = resp.json().get("jobs", [])
    print(f"\nFound {len(jobs)} jobs:")
    for job in jobs:
        print(f"  - ID: {job['jobId']}, Title: {job.get('title')}, Enabled: {job.get('enabled')}")
else:
    print(f"Failed to get jobs: status {resp.status_code}")
    print(resp.text)
