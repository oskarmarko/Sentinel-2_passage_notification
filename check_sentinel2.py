#!/usr/bin/env python3
"""Check Copernicus Data Space for new Sentinel-2 images over Vojvodina and Slack-notify."""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

SEEN_FILE = os.path.join(os.path.dirname(__file__), "seen_products.json")
POLYGON = "POLYGON((18.8 44.6,21.3 44.6,21.3 46.2,18.8 46.2,18.8 44.6))"
PLATFORM_MAP = {"S2A": "Sentinel-2A", "S2B": "Sentinel-2B", "S2C": "Sentinel-2C"}


def build_url(since):
    filter_expr = (
        "Collection/Name eq 'SENTINEL-2' and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{POLYGON}') and "
        f"ContentDate/Start gt {since}T00:00:00.000Z"
    )
    params = {"$filter": filter_expr, "$orderby": "ContentDate/Start desc", "$top": "50"}
    return "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?" + urllib.parse.urlencode(params)


def fetch_products(since):
    url = build_url(since)
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.load(resp)
    return data.get("value", [])


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE) as f:
        return set(json.load(f))


def save_seen(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen_ids), f, indent=2)


def extract_metadata(name):
    orbit_m = re.search(r"_R(\d+)_", name)
    date_m = re.search(r"_(\d{4})(\d{2})(\d{2})T\d{6}_", name)
    platform_m = re.match(r"(S2[ABC])_", name)
    orbit = orbit_m.group(1) if orbit_m else "???"
    if date_m:
        y, mo, d = date_m.groups()
        date_str = f"{d}.{mo}.{y}"
    else:
        date_str = "???"
    platform = PLATFORM_MAP.get(platform_m.group(1), "Sentinel-2") if platform_m else "Sentinel-2"
    return platform, orbit, date_str


def send_slack_message(webhook_url, lines):
    text = (
        "\U0001f6f0️ New Sentinel-2 image(s) over Vojvodina available on Copernicus!\n\n"
        + "\n".join(lines)
        + "\n\nView & download: https://browser.dataspace.copernicus.eu"
    )
    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        webhook_url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def main():
    since = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
    products = fetch_products(since)

    seen = load_seen()
    new_products = [p for p in products if p["Id"] not in seen]

    if new_products:
        dedup = {}
        for p in new_products:
            key = extract_metadata(p["Name"])
            dedup.setdefault(key, key)
        lines = [f"• {plat} | Passage {orbit} | Acquired {date}" for plat, orbit, date in dedup]

        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("SLACK_WEBHOOK_URL not set, skipping Slack notification", file=sys.stderr)
        else:
            send_slack_message(webhook_url, lines)
        print(f"Notified about {len(new_products)} new product(s) ({len(dedup)} unique passage(s)).")
    else:
        print("No new products found.")

    seen.update(p["Id"] for p in products)
    save_seen(seen)


if __name__ == "__main__":
    main()
