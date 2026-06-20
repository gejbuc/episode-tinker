# scripts/interests/house_of_the_dragon.py
"""
Interest module for House of the Dragon (IMDb tt11198330).
Fetches upcoming episodes from TVMaze API.
"""
import requests
from datetime import datetime, timezone


def get_events(config: dict) -> list:
    """Fetch upcoming episodes of House of the Dragon from TVMaze."""
    # First get TVMaze show ID from IMDb ID for safety
    imdb_id = "tt11198330"
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
        # Skip episodes without airdate/airstamp
        if not ep.get("airstamp"):
            continue

        # Parse airstamp into timezone-aware datetime
        try:
            air_time = datetime.fromisoformat(ep["airstamp"].replace("Z", "+00:00"))
        except (ValueError, KeyError):
            continue

        # Build episode name and message
        season_num = ep.get("season", 0)
        ep_num = ep.get("number", 0)
        ep_name = ep.get("name", "TBA")
        event_id = f"house_of_the_dragon-s{season_num:02d}e{ep_num:02d}"
        full_name = f"House of the Dragon S{season_num:02d}E{ep_num:02d} - {ep_name}"
        message = f"New episode aired: {full_name}"

        events.append({
            "id": event_id,
            "name": full_name,
            "start_time": air_time,
            "title": "House of the Dragon",
            "message": message
        })

    return events
