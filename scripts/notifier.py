# scripts/notifier.py
"""
Notifier script that sends an ntfy.sh notification.
Can be run with workflow inputs or from command line.
Uses state.json to track sent notifications.
"""
import os
import sys
import argparse
import yaml
import json
import requests
from pathlib import Path

# Add repo root to Python path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONFIG_PATH = REPO_ROOT / "config.yaml"
STATE_PATH = REPO_ROOT / "state.json"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH, encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"sent": []}
    return {"sent": []}


def save_state(state: dict):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_ntfy_topic(config: dict) -> str:
    return os.getenv("NTFY_TOPIC", config["notifications"]["ntfy_topic"])


def send_notification(topic: str, title: str, message: str, tags: str = "bell"):
    response = requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Tags": tags},
        timeout=10,
    )
    if response.status_code == 200:
        print(f"  ✓ Sent notification: {message}")
    else:
        print(f"  ✗ ntfy returned HTTP {response.status_code}")
    return response.status_code == 200


def run_notifier(config: dict, event_id: str, title: str, message: str, tags: str = "bell"):
    # Load state first to check if we already sent this notification
    state = load_state()
    if event_id and event_id in state.get("sent", []):
        print(f"[notifier] Already sent notification for event '{event_id}', skipping!")
        return

    topic = get_ntfy_topic(config)
    print(f"[notifier] Sending to topic: {topic}")
    success = send_notification(topic, title, message, tags)
    if success and event_id:
        state["sent"] = state.get("sent", []) + [event_id]
        save_state(state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-id", help="Unique event ID for duplicate tracking", default="")
    parser.add_argument("--title", help="Notification title", default="Episode Alert")
    parser.add_argument("--message", help="Notification message", default="New episode aired!")
    parser.add_argument("--tags", help="ntfy.sh tags", default="calendar,bell")
    # Also check for GitHub Actions workflow inputs in env vars
    args = parser.parse_args()

    config = load_config()

    # Prefer env vars (from workflow inputs) if available
    event_id = os.getenv("INPUT_EVENT_ID", args.event_id)
    title = os.getenv("INPUT_TITLE", args.title)
    message = os.getenv("INPUT_MESSAGE", args.message)
    tags = os.getenv("INPUT_TAGS", args.tags)

    run_notifier(config, event_id, title, message, tags)
