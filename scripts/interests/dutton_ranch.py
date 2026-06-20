# scripts/interests/dutton_ranch.py
"""
Interest module for Dutton Ranch (IMDb tt34991493).
Fetches upcoming episodes from TVMaze API, with manually corrected airtime:
3:00 AM ET / 00:00 AM PT (07:00 UTC) every Friday!
"""
import requests
from datetime import datetime, timezone, timedelta


def get_events(config: dict) -> list:
    """Fetch upcoming episodes of Dutton Ranch from TVMaze."""
    # First get TVMaze show ID from IMDb ID tt34991493 for safety
    imdb_id = "tt34991493"
    lookup_url = f"https://api.tvmaze.com/lookup/shows?imdb={imdb_id}"
    lookup_response = requests.get(lookup_url, timeout=10)
    lookup_response.raise_for_status()
    show = lookup_response.json()
    show_id = show["id"]

    # Now fetch all episodes
    episodes_url = f"https://api.tvmaze.com/shows/{show_id}/episodes?specials=1"
    response = requests.get(episodes_url, timeout=10)
    response.raise_for_status()
    episodes = response.json()

    events = []
    for ep in episodes:
        # Skip episodes without airdate
        if not ep.get("airdate"):
            continue

        # Parse date, then set correct time: 07:00 UTC (3 AM ET / 00:00 PT)
        try:
            # Parse airdate into date object
            air_date = datetime.strptime(ep["airdate"], "%Y-%m-%d").date()
            # Combine with correct time: 07:00 UTC
            air_time = datetime.combine(
                air_date,
                datetime.min.time().replace(hour=7, minute=0, second=0),
                timezone.utc
            )
        except (ValueError, KeyError):
            continue

        # Build episode name and message
        season_num = ep.get("season", 0)
        ep_num = ep.get("number", 0)
        ep_name = ep.get("name", "Unknown")
        event_id = f"duttonranch-s{season_num:02d}e{ep_num:02d}"
        full_name = f"Dutton Ranch S{season_num:02d}E{ep_num:02d} - {ep_name}"
        message = f"New episode aired: {full_name}"

        events.append({
            "id": event_id,
            "name": full_name,
            "start_time": air_time,
            "title": "Dutton Ranch",
            "message": message
        })

    return events
