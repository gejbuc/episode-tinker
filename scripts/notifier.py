# scripts/notifier.py
"""
Notifier script that sends an ntfy.sh notification.
Can be run with workflow inputs or from command line.
"""
import os
import sys
import argparse
import yaml
import requests
from pathlib import Path

# Add repo root to Python path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONFIG_PATH = REPO_ROOT / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def run_notifier(config: dict, title: str, message: str, tags: str = "bell"):
    topic = get_ntfy_topic(config)
    print(f"[notifier] Sending to topic: {topic}")
    send_notification(topic, title, message, tags)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", help="Notification title", default="Episode Alert")
    parser.add_argument("--message", help="Notification message", default="New episode aired!")
    parser.add_argument("--tags", help="ntfy.sh tags", default="calendar,bell")
    # Also check for GitHub Actions workflow inputs in env vars
    args = parser.parse_args()

    config = load_config()

    # Prefer env vars (from workflow inputs) if available
    title = os.getenv("INPUT_TITLE", args.title)
    message = os.getenv("INPUT_MESSAGE", args.message)
    tags = os.getenv("INPUT_TAGS", args.tags)

    run_notifier(config, title, message, tags)
