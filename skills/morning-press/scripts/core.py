"""Private profile storage and validation; no network or account access."""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator, FormatChecker

SKILL = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = next((p for p in SKILL.parents if (p / "plugin.json").is_file()), SKILL)
KINDS = ("news", "weather", "calendar", "economy", "events", "books", "screen", "learning", "positive", "language", "custom")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_schema(value, name):
    schema = read_json(SKILL / "assets" / f"{name}.schema.json")
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        e = errors[0]
        raise ValueError(f"{name}: {'.'.join(map(str, e.path)) or 'root'}: {e.message}")


def timezone(value):
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"Unknown IANA timezone: {value}") from exc


def public_url(value):
    """Only public-looking HTTPS destinations; private meeting/feed URLs stay local."""
    if not value:
        return
    import ipaddress
    u = urlsplit(value)
    host = (u.hostname or "").lower()
    if u.scheme != "https" or not host or u.username or u.password or u.query or u.fragment:
        raise ValueError("Use a public HTTPS article URL without credentials, query, or fragment")
    if host == "localhost" or "." not in host or host.endswith((".local", ".internal", ".localhost")):
        raise ValueError("Private link is not a public source")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Private IP address is not a public source")
    if any(host == d or host.endswith("." + d) for d in ("meet.google.com", "zoom.us", "teams.microsoft.com", "calendar.google.com")):
        raise ValueError("Meeting/calendar URLs cannot be printed or encoded as QR codes")


def validate_profile(profile, ready=False):
    validate_schema(profile, "profile")
    timezone(profile["publication"]["timezone"])
    ids = [s["id"] for s in profile["sections"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Section IDs must be unique")
    for section in profile["sections"]:
        for location in section["options"].get("locations", []):
            timezone(location["timezone"])
        if section["kind"] == "calendar":
            for provider in section["options"].get("providers", []):
                if provider["state"] == "connected" and provider["mode"] != "connector":
                    raise ValueError("Only a verified connector may be marked connected")
    if ready or profile["status"] == "ready":
        if profile["status"] != "ready":
            raise ValueError("Finish setup and confirm the profile before creating a real issue")
        if profile["delivery"]["schedule_requested"] and (not profile["delivery"]["time"] or not profile["delivery"]["weekdays"]):
            raise ValueError("A schedule preference needs a local time and at least one weekday")
        active = [s for s in profile["sections"] if s["enabled"]]
        if profile["publication"]["format"] == "markdown" and profile["publication"]["links"]["qr"]:
            raise ValueError("Printed QR codes require PDF or both output formats")
        if not active:
            raise ValueError("Enable at least one section")
        for s in active:
            opts = s["options"]
            if s["sources"]["mode"] == "allowlist" and not s["sources"]["domains"]:
                raise ValueError("An allowlist source policy needs at least one domain")
            if s["kind"] in ("news", "events", "positive") and not s["regions"]:
                raise ValueError(f"{s['id']}: select at least one region (or Worldwide)")
            if s["kind"] == "weather" and not opts.get("locations"):
                raise ValueError("Weather needs a location and its timezone")
            if s["kind"] == "calendar" and not opts.get("providers"):
                raise ValueError("Calendar needs a provider or manual import selection")
            if s["kind"] == "economy" and not opts.get("instruments") and not s["topics"]:
                raise ValueError("Economy needs instruments or economic topics")
            if s["kind"] == "screen" and not opts.get("country"):
                raise ValueError("Screen recommendations need a catalog country")
    return profile


def data_home(explicit=None):
    selected = explicit or os.environ.get("MORNING_PRESS_HOME")
    base = Path(selected).expanduser() if selected else Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "morning-press"
    base = base.resolve()
    if base == PUBLIC_ROOT or PUBLIC_ROOT in base.parents:
        raise ValueError("Private profiles and output must be stored outside the public package")
    return base


def profile_path(base, name):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", name):
        raise ValueError("Profile name must use 1-48 lowercase letters, digits, or hyphens")
    return base / "profiles" / name / "profile.json"


def private_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def save_profile(base, name, profile, replace=False):
    validate_profile(profile)
    target = profile_path(base, name)
    if target.exists() and not replace:
        raise ValueError("Profile exists; use --replace to update it explicitly")
    private_write(target, json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
    return target


def validate_issue(issue, profile):
    validate_profile(profile, ready=True)
    validate_schema(issue, "issue")
    active = {s["id"]: s for s in profile["sections"] if s["enabled"]}
    ids = [s["id"] for s in issue["sections"]]
    if len(ids) != len(set(ids)) or set(ids) != set(active):
        raise ValueError("Issue must contain each enabled section exactly once and no disabled sections")
    for section in issue["sections"]:
        pref = active[section["id"]]
        if section["status"] == "pending":
            raise ValueError("Research is still pending; a collection draft cannot be rendered")
        if section["status"] != "ready" and not section["note"].strip():
            raise ValueError("Unavailable/no_updates sections need an explanation")
        if len(section["items"]) > pref["max_items"]:
            raise ValueError(f"{pref['id']}: exceeds configured max_items")
        if (section["status"] == "ready") != bool(section["items"]):
            raise ValueError("Ready sections need items; unavailable/no_updates sections must have no items")
        for item in section["items"]:
            public_url(item["url"])
            src = item["source"]
            if pref["kind"] == "calendar" and item["url"]:
                raise ValueError("Calendar items must not contain printable URLs")
            if not issue["demo"] and pref["kind"] != "calendar" and not src:
                raise ValueError("Real editorial items require source provenance")
            if src:
                public_url(src["url"])
                if item["url"] and item["url"] != src["url"]:
                    raise ValueError("Title destination and source URL must match")
                checked = datetime.fromisoformat(src["checked_at"].replace("Z", "+00:00"))
                if checked.utcoffset() is None:
                    raise ValueError("Source checked_at needs an explicit timezone")
                if checked.astimezone(timezone(profile["publication"]["timezone"])).date() > date.fromisoformat(issue["date"]):
                    raise ValueError("Source checked_at falls after the issue date")
                policy = pref["sources"]
                host = urlsplit(src["url"]).hostname
                if policy["mode"] == "allowlist" and not any(host == d or host.endswith("." + d) for d in policy["domains"]):
                    raise ValueError(f"{pref['id']}: source is outside the allowed domains")
    return issue
