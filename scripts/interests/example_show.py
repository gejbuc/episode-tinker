# scripts/interests/example_show.py
"""
Example interest module that returns some dummy test episodes.
Replace this with your real show modules!
"""
from datetime import datetime, timezone, timedelta


def get_events(config: dict) -> list:
    """
    Return a list of upcoming episode events.
    Each event should have:
      id: unique stable identifier
      name: human-readable name
      start_time: UTC-aware datetime
      title: notification title
      message: notification message
    """
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "example-s01e01",
            "name": "Example Show S01E01 - Pilot",
            "start_time": now + timedelta(minutes=30),
            "title": "Example Show",
            "message": "New episode aired: Example Show S01E01 - Pilot",
        },
    ]
