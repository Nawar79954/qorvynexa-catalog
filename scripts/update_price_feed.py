#!/usr/bin/env python3
"""Refresh a narrowly scoped official Disney+ Netherlands price adapter.

Only publishes a plan's first monthly amount when every matching occurrence on
the official page agrees. This intentionally chooses the regular price shown
immediately after the plan name, not the later six-month promotional amount.
On ambiguity or source changes, the feed is not written.
"""
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

FEED = Path("prices.json")
SOURCE_URL = "https://www.disneyplus.com/en-nl"
TARGETS = {
    "With ads": r"(?:Standard\s+With\s+Ads|Standaard\s+met\s+reclame)",
    "Premium": r"Premium",
}
HEADERS = {"User-Agent": "QorvynexaPriceFeed/1.0 (+https://github.com/Nawar79954/qorvynexa-catalog)"}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def fetch_text():
    request = Request(SOURCE_URL, headers=HEADERS)
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"official source returned HTTP {response.status}")
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            raise RuntimeError(f"unexpected content type: {content_type}")
        raw = response.read(3_000_001)
    if len(raw) > 3_000_000:
        raise RuntimeError("official source response exceeded size limit")
    parser = TextExtractor()
    parser.feed(raw.decode("utf-8", errors="strict"))
    return re.sub(r"\s+", " ", " ".join(parser.parts))


def parse_price(text, label_pattern, plan_name):
    # Capture only the amount immediately following the plan name. The source
    # currently lists regular monthly price first and any 6-month saver price
    # afterward; never select the latter by searching farther into the text.
    amount_pattern = r"€\s*([0-9]{1,3}(?:[.,][0-9]{2}))\s*(?:/\s*month|per month|/\s*maand|per maand)"
    pattern = re.compile(label_pattern + r"\s*\(\s*" + amount_pattern, re.IGNORECASE)
    matches = pattern.findall(text)
    if not matches:
        # Some page variants omit parentheses around the plan's price.
        pattern = re.compile(label_pattern + r"\s+" + amount_pattern, re.IGNORECASE)
        matches = pattern.findall(text)
    if not matches:
        raise RuntimeError(
            f"could not verify a regular monthly price for {plan_name!r}; feed was not changed"
        )
    normalized = {float(value.replace(",", ".")) for value in matches}
    if len(normalized) != 1:
        raise RuntimeError(
            f"official page has conflicting monthly prices for {plan_name!r}; feed was not changed"
        )
    amount = normalized.pop()
    if not 0 < amount < 1000:
        raise RuntimeError(f"implausible amount for {plan_name!r}; feed was not changed")
    return amount


def main():
    try:
        text = fetch_text()
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        fresh = [
            {
                "serviceId": "disney-plus",
                "planName": plan,
                "countryCode": "NL",
                "currency": "EUR",
                "amount": parse_price(text, pattern, plan),
                "sourceUrl": SOURCE_URL,
                "updatedAt": now,
            }
            for plan, pattern in TARGETS.items()
        ]
        feed = json.loads(FEED.read_text(encoding="utf-8"))
        managed = {(r["serviceId"], r["planName"], r["countryCode"], r["currency"]) for r in fresh}
        previous = feed.get("automaticPrices", [])
        feed["automaticPrices"] = [
            r for r in previous
            if (r.get("serviceId"), r.get("planName"), r.get("countryCode"), r.get("currency")) not in managed
        ] + fresh
        feed["updatedAt"] = now
        FEED.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Updated {len(fresh)} verified Disney+ Netherlands prices from the official page.")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
