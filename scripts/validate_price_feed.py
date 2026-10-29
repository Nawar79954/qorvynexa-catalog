#!/usr/bin/env python3
"""Validate Qorvynexa prices.json without fetching or inventing prices."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MAX_BODY_BYTES = 500_000
MAX_AMOUNT = 100_000
REQUIRED_RECORD_FIELDS = {
    "serviceId", "planName", "countryCode", "currency",
    "amount", "sourceUrl", "updatedAt",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_time(value, label: str):
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} is not a valid ISO-8601 timestamp")
    if parsed.tzinfo is None:
        fail(f"{label} must include a timezone")
    if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
        fail(f"{label} must not be in the future")
    return parsed


def valid_text(value, label: str, limit: int = 100) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        fail(f"{label} must be a non-empty string of at most {limit} characters")
    return value.strip()


def validate_record(record, section: str, index: int):
    label = f"{section}[{index}]"
    if not isinstance(record, dict):
        fail(f"{label} must be an object")
    missing = REQUIRED_RECORD_FIELDS - record.keys()
    if missing:
        fail(f"{label} missing fields: {', '.join(sorted(missing))}")

    service_id = valid_text(record["serviceId"], f"{label}.serviceId")
    plan_name = valid_text(record["planName"], f"{label}.planName")
    country = valid_text(record["countryCode"], f"{label}.countryCode", 2).upper()
    currency = valid_text(record["currency"], f"{label}.currency", 3).upper()
    if not re.fullmatch(r"[A-Z]{2}", country):
        fail(f"{label}.countryCode must be a two-letter ISO country code")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        fail(f"{label}.currency must be a three-letter currency code")

    amount = record["amount"]
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        fail(f"{label}.amount must be numeric")
    if not 0 < amount < MAX_AMOUNT:
        fail(f"{label}.amount must be greater than 0 and below {MAX_AMOUNT}")

    source = valid_text(record["sourceUrl"], f"{label}.sourceUrl", 2048)
    parsed_url = urlparse(source)
    if parsed_url.scheme != "https" or not parsed_url.hostname or parsed_url.username or parsed_url.password:
        fail(f"{label}.sourceUrl must be an HTTPS URL without embedded credentials")

    parse_time(record["updatedAt"], f"{label}.updatedAt")
    return (service_id, plan_name, country, currency)


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "prices.json")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")
    if len(raw) > MAX_BODY_BYTES:
        fail(f"{path} exceeds {MAX_BODY_BYTES} bytes")
    try:
        feed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON: {exc}")
    if not isinstance(feed, dict):
        fail("top-level JSON must be an object")
    if feed.get("schemaVersion") != 1:
        fail("schemaVersion must be 1")
    if not isinstance(feed.get("automaticPrices"), list):
        fail("automaticPrices must be a list")
    if not isinstance(feed.get("manualOverrides"), list):
        fail("manualOverrides must be a list")
    if "updatedAt" in feed and feed["updatedAt"] is not None:
        parse_time(feed["updatedAt"], "updatedAt")

    automatic_keys = set()
    for i, record in enumerate(feed["automaticPrices"]):
        key = validate_record(record, "automaticPrices", i)
        if key in automatic_keys:
            fail(f"duplicate automatic price key: {key}")
        automatic_keys.add(key)

    manual_keys = set()
    for i, record in enumerate(feed["manualOverrides"]):
        key = validate_record(record, "manualOverrides", i)
        if key in manual_keys:
            fail(f"duplicate manual override key: {key}")
        manual_keys.add(key)

    print(
        "Price feed valid: "
        f"{len(feed['automaticPrices'])} automatic prices, "
        f"{len(feed['manualOverrides'])} manual overrides. "
        "Manual overrides take precedence in the app."
    )
    if not feed["automaticPrices"] and not feed["manualOverrides"]:
        print("NOTICE: feed is empty; no prices will be added or inferred.")


if __name__ == "__main__":
    main()
