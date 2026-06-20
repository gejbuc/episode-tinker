# episode-tinker

A lightweight TV episode notifier that sends alerts to your phone via [ntfy.sh](https://ntfy.sh) — no sign-ups, no API keys for the core functionality.

## How it works

Timing is handled entirely by [cron-job.org](https://cron-job.org) instead of GitHub's notoriously delayed scheduler.

```
12:00 EAT daily
  └─ cron-job.org triggers expander workflow
       ├─ loads upcoming episodes from interest modules
       ├─ cleans up old cron jobs
       └─ creates one-time cron-job.org jobs at (air_time + 5 minutes) for each episode

At each alert time
  └─ cron-job.org triggers episode alert workflow
       └─ sends ntfy.sh notification
```

## Project Structure

```
episode-tinker/
├── .github/
│   └── workflows/
│       ├── expand.yml       # Expander workflow (triggered daily by cron-job.org)
│       └── episode_alert.yml # Episode alert workflow (triggered per-episode)
├── scripts/
│   ├── notifier.py         # Sends ntfy.sh notifications
│   ├── expander.py         # Loads interests and schedules episode alerts
│   ├── scheduler.py        # Manages one-time cron-job.org jobs
│   └── interests/          # Interest modules (one per show/topic)
│       └── __init__.py
├── config.yaml             # All user-editable settings
├── requirements.txt
└── .gitignore
```

## Setup

1. Create a new GitHub repo for `episode-tinker` and push this code to it
2. Add secrets to your repo at `Settings > Secrets and variables > Actions`:
   - `NTFY_TOPIC`: Your ntfy.sh topic name
   - `CRONJOB_TOKEN`: cron-job.org API bearer token
   - `MORNING_GH_PAT`: GitHub fine-grained PAT with `actions:write` on this repo
3. Set up your first recurring cron-job.org job to trigger the `expand.yml` workflow daily
4. Customize `config.yaml` and add your real interest modules in `scripts/interests/`

## Adding Interests

To add a new show/interest:
1. Create a new Python module in `scripts/interests/`
2. Expose a `get_events(config)` function that returns upcoming episode events
3. Enable it in `config.yaml` under the `interests` section
