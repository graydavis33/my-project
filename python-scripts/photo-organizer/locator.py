"""
Photo Organizer — Location Grouper
Clusters photos by GPS coordinates and reverse-geocodes cluster centers
to human-readable location names. Free — no API key needed.
"""

import json
import math
import os
import time

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from config import (
    CLUSTER_RADIUS_METERS,
    GEOCODE_USER_AGENT,
    GEOCODE_CACHE_FILE,
)

# ── Geocoding cache (saves API calls + speeds up reruns) ─────────────────────

def _load_cache(cache_path: str) -> dict:
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict, cache_path: str):
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


# ── Haversine distance ────────────────────────────────────────────────────────

def haversine_meters(lat1, lon1, lat2, lon2) -> float:
    """Return distance in meters between two GPS points."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── GPS clustering ────────────────────────────────────────────────────────────

def cluster_photos(photo_coords: dict[str, tuple[float, float]]) -> dict[str, list[str]]:
    """
    Group photo file paths into clusters based on GPS proximity.

    photo_coords: {filepath: (lat, lon)}
    Returns: {cluster_id_str: [filepath, ...]}
    """
    clusters: list[list[str]] = []       # list of filepath groups
    cluster_centers: list[tuple] = []    # (lat, lon) center of each cluster

    for filepath, (lat, lon) in photo_coords.items():
        placed = False
        for i, center in enumerate(cluster_centers):
            dist = haversine_meters(lat, lon, center[0], center[1])
            if dist <= CLUSTER_RADIUS_METERS:
                clusters[i].append(filepath)
                # Update center to average of all points in cluster
                n = len(clusters[i])
                new_lat = (center[0] * (n - 1) + lat) / n
                new_lon = (center[1] * (n - 1) + lon) / n
                cluster_centers[i] = (new_lat, new_lon)
                placed = True
                break
        if not placed:
            clusters.append([filepath])
            cluster_centers.append((lat, lon))

    # Return as dict keyed by cluster index
    return {str(i): paths for i, paths in enumerate(clusters)}, cluster_centers


# ── Reverse geocoding ─────────────────────────────────────────────────────────

def reverse_geocode(lat: float, lon: float, cache: dict, cache_path: str) -> str:
    """
    Convert lat/lon to a human-readable location name.
    Uses cache to avoid redundant API calls.
    Falls back gracefully on errors.
    """
    key = f"{round(lat, 3)},{round(lon, 3)}"   # Low precision key = better cache hits

    if key in cache:
        return cache[key]

    geolocator = Nominatim(user_agent=GEOCODE_USER_AGENT)
    try:
        time.sleep(1.1)   # Nominatim rate limit: 1 request/second
        location = geolocator.reverse((lat, lon), exactly_one=True, language="en", timeout=10)
        if location and location.raw.get("address"):
            addr = location.raw["address"]
            # Build a clean name: "City, State" or "City, Country"
            city    = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county", "")
            state   = addr.get("state", "")
            country = addr.get("country", "")
            if city and state:
                name = f"{city}, {state}"
            elif city and country:
                name = f"{city}, {country}"
            elif state and country:
                name = f"{state}, {country}"
            else:
                name = country or f"{round(lat,2)}N {round(lon,2)}E"
        else:
            name = f"{round(lat,2)}N {round(lon,2)}E"
    except (GeocoderTimedOut, GeocoderServiceError):
        name = f"{round(lat,2)}N {round(lon,2)}E"
    except Exception:
        name = "Unknown Location"

    cache[key] = name
    _save_cache(cache, cache_path)
    return name


def sanitize_folder_name(name: str) -> str:
    """Make a string safe to use as a folder name on Mac/Windows."""
    bad_chars = r'/\:*?"<>|'
    for ch in bad_chars:
        name = name.replace(ch, "-")
    return name.strip()


def build_location_groups(
    photo_coords: dict[str, tuple[float, float]],
    no_gps_photos: list[str],
    cache_path: str,
    progress_callback=None,
) -> dict[str, list[str]]:
    """
    Main function: takes photo paths with GPS and without GPS.
    Returns {location_name: [filepath, ...]}
    """
    cache = _load_cache(cache_path)
    groups: dict[str, list[str]] = {}

    if photo_coords:
        clusters, centers = cluster_photos(photo_coords)
        total = len(clusters)
        for i, (cluster_id, paths) in enumerate(clusters.items()):
            lat, lon = centers[int(cluster_id)]
            name = reverse_geocode(lat, lon, cache, cache_path)
            name = sanitize_folder_name(name)
            # Handle duplicate location names (two separate clusters same city)
            base_name = name
            suffix = 2
            while name in groups:
                name = f"{base_name} ({suffix})"
                suffix += 1
            groups[name] = paths
            if progress_callback:
                progress_callback(i + 1, total, f"Geocoded: {name}")

    if no_gps_photos:
        groups["No GPS Data"] = no_gps_photos

    return groups
