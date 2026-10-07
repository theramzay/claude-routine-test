#!/usr/bin/env python3
"""Collect posts and releases inside the lookback window for every technology in tech-stack.csv.

Reads feed and GitHub repo lists from feeds.json next to the skill, fetches each RSS/Atom feed
and each repo's releases, and prints the entries published inside the window, in UTC.
A source that fails or an entry with an unreadable date is reported, never fatal.

Usage: python3 fetch_feeds.py [--csv tech-stack.csv] [--hours 24] [--now 2026-10-07T07:00:00Z]
Exit codes: 0 = ran (check "Sources unavailable"), 2 = tech-stack.csv missing or empty.
"""
import argparse
import csv
import datetime as dt
import email.utils
import gzip
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
UTC = dt.timezone.utc
USER_AGENT = "tech-stack-news/1.0"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default="tech-stack.csv")
    p.add_argument("--feeds", default=str(SKILL_DIR / "feeds.json"))
    p.add_argument("--hours", type=float, default=24)
    p.add_argument("--now", help="window end as ISO 8601 (default: current UTC time)")
    p.add_argument("--summary-chars", type=int, default=800,
                   help="max characters of each entry's feed summary to print (0 = none)")
    return p.parse_args()


def read_stack(path):
    """Return [(company, technology), ...] in CSV order."""
    pairs = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            company = (row.get("company") or "").strip()
            for tech in (row.get("technologies") or "").split(";"):
                if company and tech.strip():
                    pairs.append((company, tech.strip()))
    return pairs


def parse_date(text):
    """Return (datetime in UTC, date_only) or (None, False) if the value can't be read."""
    text = (text or "").strip()
    if not text:
        return None, False
    try:
        d = email.utils.parsedate_to_datetime(text)  # RFC 822, used by RSS <pubDate>
    except (TypeError, ValueError, IndexError):
        d = None
    if d is None:
        iso = text.replace("Z", "+00:00").replace("z", "+00:00")
        try:
            d = dt.datetime.fromisoformat(iso)  # ISO 8601, used by Atom and <dc:date>
        except ValueError:
            return None, False
        if len(text) == 10:  # YYYY-MM-DD
            return d.replace(tzinfo=UTC), True
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC), False


def in_window(published, date_only, start, end):
    if date_only:
        return start.date() <= published.date() <= end.date()
    return start <= published <= end


def http_get(url, headers=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        **(headers or {}),
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
        encoding = resp.headers.get("Content-Encoding", "")
    if encoding == "gzip" or body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    elif encoding == "deflate":
        body = zlib.decompress(body)
    return body


def local(tag):
    return tag.rsplit("}", 1)[-1]


def child_text(el, *names):
    for c in el:
        if local(c.tag) in names and (c.text or "").strip():
            return c.text.strip()
    return ""


def entry_link(el):
    for c in el:
        if local(c.tag) != "link":
            continue
        if c.get("href") and c.get("rel", "alternate") == "alternate":
            return c.get("href")
        if (c.text or "").strip():
            return c.text.strip()
    for c in el:  # Atom entry with only non-alternate links
        if local(c.tag) == "link" and c.get("href"):
            return c.get("href")
    return ""


def parse_feed(body):
    """Return (entries, skipped) where entries are dicts and skipped counts undated entries."""
    root = ET.fromstring(body)
    entries, skipped = [], 0
    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        raw = child_text(el, "pubDate", "published", "date", "updated")
        published, date_only = parse_date(raw)
        if published is None:
            skipped += 1
            continue
        entries.append({
            "published": published,
            "date_only": date_only,
            "title": " ".join(child_text(el, "title").split()) or "(untitled)",
            "url": entry_link(el),
            "summary": plain_text(child_text(el, "description", "summary", "content", "encoded")),
        })
    return entries, skipped


def plain_text(markup):
    """Strip HTML tags and entities from a feed summary and collapse whitespace."""
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", markup or "", flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return " ".join(text.split())


def github_releases(repo):
    """Fetch releases with gh (uses the session's GitHub login), falling back to the REST API."""
    path = f"repos/{repo}/releases?per_page=20"
    errors = []
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return json.loads(r.stdout)
        errors.append(f"gh api: {(r.stderr or r.stdout).strip().splitlines()[-1:] or ['failed']}")
    else:
        errors.append("gh not installed")
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return json.loads(http_get(f"https://api.github.com/{path}", headers))
    except urllib.error.HTTPError as e:
        errors.append(f"REST API: HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        errors.append(f"REST API: {e}")
    raise RuntimeError("; ".join(errors))


def release_entries(releases):
    entries = []
    for rel in releases:
        if rel.get("draft"):
            continue
        published, date_only = parse_date(rel.get("published_at") or rel.get("created_at"))
        if published is None:
            continue
        title = rel.get("name") or rel.get("tag_name") or "(untitled)"
        if rel.get("prerelease"):
            title += " [prerelease]"
        entries.append({"published": published, "date_only": date_only,
                        "title": title, "url": rel.get("html_url", ""),
                        "summary": " ".join((rel.get("body") or "").split())})
    return entries


def main():
    args = parse_args()
    try:
        pairs = read_stack(args.csv)
    except FileNotFoundError:
        print(f"ERROR: {args.csv} not found", file=sys.stderr)
        return 2
    if not pairs:
        print(f"ERROR: {args.csv} has no companies or technologies", file=sys.stderr)
        return 2
    sources = json.loads(Path(args.feeds).read_text(encoding="utf-8"))

    end = parse_date(args.now)[0] if args.now else dt.datetime.now(UTC).replace(microsecond=0)
    if end is None:
        print(f"ERROR: --now {args.now!r} is not a valid date", file=sys.stderr)
        return 2
    start = end - dt.timedelta(hours=args.hours)

    cache, unavailable, warnings = {}, {}, {}

    def load(key, fetch):
        if key not in cache:
            try:
                cache[key] = fetch()
            except Exception as e:  # report every failure, never stop the run
                cache[key] = None
                unavailable[key] = f"{type(e).__name__}: {e}"
        return cache[key] or []

    def fetch_feed(url):
        entries, skipped = parse_feed(http_get(url))
        if skipped:
            warnings[url] = f"{skipped} entries skipped (missing or unreadable date)"
        return entries

    fmt = "%Y-%m-%d %H:%M"
    print(f"Window: {start.strftime(fmt)} to {end.strftime(fmt)} (UTC)")
    for company, tech in pairs:
        print(f"\n== {company} / {tech}")
        config = sources.get(tech)
        if not config:
            print("!! No feeds configured in feeds.json; research this technology with web search.")
            continue
        found = []
        for url in config.get("feeds", []):
            found += [dict(e, source=url) for e in load(url, lambda u=url: fetch_feed(u))]
        for repo in config.get("github", []):
            key = f"github.com/{repo}/releases"
            found += [dict(e, source=key)
                      for e in load(key, lambda r=repo: release_entries(github_releases(r)))]
        hits = sorted((e for e in found if in_window(e["published"], e["date_only"], start, end)),
                      key=lambda e: e["published"], reverse=True)
        if not hits:
            print("(nothing in window)")
        for e in hits:
            when = e["published"].strftime("%Y-%m-%d") + (" (date only)" if e["date_only"]
                                                          else e["published"].strftime(" %H:%M"))
            print(f"- [{when}] {e['title']} | {e['url']} | via {e['source']}")
            summary = e.get("summary", "")
            if args.summary_chars and summary:
                if len(summary) > args.summary_chars:
                    summary = summary[:args.summary_chars].rsplit(" ", 1)[0] + " …"
                print(f"    Summary: {summary}")

    print("\n== Sources unavailable")
    print("\n".join(f"- {k}: {v}" for k, v in unavailable.items()) or "(none)")
    print("\n== Warnings")
    print("\n".join(f"- {k}: {v}" for k, v in warnings.items()) or "(none)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
