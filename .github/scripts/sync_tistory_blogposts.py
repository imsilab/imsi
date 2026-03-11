#!/usr/bin/env python3
import datetime as dt
import email.utils
import html
import json
import os
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET


RSS_URL = os.getenv("TISTORY_RSS_URL", "https://lambdacourse.tistory.com/rss")
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "3"))
OUTPUT_PATH = pathlib.Path(os.getenv("OUTPUT_PATH", "data/tistory-blogposts.json"))


def local_name(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def child_text(node, name):
    for child in list(node):
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def parse_pub_date(value):
    raw = (value or "").strip()
    if not raw:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
        if parsed is None:
            return ""
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        return ""


def clean_text(value):
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_excerpt(value, max_len=240):
    raw = clean_text(value)
    if not raw:
        return ""
    if len(raw) <= max_len:
        return raw
    cut = raw[:max_len]
    last_space = cut.rfind(" ")
    if last_space > 80:
        cut = cut[:last_space]
    return cut.rstrip(" .,;:!?") + "..."


def fetch_rss(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def extract_items(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = []

    for node in root.iter():
        if local_name(node.tag) != "item":
            continue

        title = child_text(node, "title")
        link = child_text(node, "link")
        pub_date = child_text(node, "pubDate")
        iso_date = parse_pub_date(pub_date)
        description = child_text(node, "description")
        excerpt = build_excerpt(description)

        if not title or not link:
            continue

        items.append(
            {
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "iso_date": iso_date,
                "excerpt": excerpt,
            }
        )

        if len(items) >= MAX_ITEMS:
            break

    return items


def main():
    xml_bytes = fetch_rss(RSS_URL)
    items = extract_items(xml_bytes)

    payload = {
        "source": "tistory_rss",
        "rss_url": RSS_URL,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(items),
        "items": items,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(items)} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
