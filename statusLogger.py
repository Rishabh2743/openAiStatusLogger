import asyncio
import aiohttp
import feedparser
import re
import html
from datetime import datetime
from typing import Optional, List
import os
import fastapi

# ==========================================
# Feed Client (Single Responsibility)
# ==========================================

class FeedClient:
    def __init__(self, feed_url: str):
        self.feed_url = feed_url
        self.etag: Optional[str] = None
        self.last_modified: Optional[str] = None

    async def fetch(self, session: aiohttp.ClientSession) -> Optional[str]:
        headers = {}

        if self.etag:
            headers["If-None-Match"] = self.etag
        if self.last_modified:
            headers["If-Modified-Since"] = self.last_modified

        async with session.get(self.feed_url, headers=headers) as response:
            if response.status == 304:
                return None

            response.raise_for_status()

            content = await response.text()

            # Update cache headers
            self.etag = response.headers.get("ETag")
            self.last_modified = response.headers.get("Last-Modified")

            return content


# ==========================================
# Feed Parser (Single Responsibility)
# ==========================================

class FeedParser:
    def __init__(self):
        self.seen_entries = set()

    def parse(self, raw_feed: str, first_run: bool) -> List[dict]:
        events = []
        feed = feedparser.parse(raw_feed)

        for entry in feed.entries:
            entry_id = getattr(entry, "id", getattr(entry, "link", None))
            if not entry_id:
                continue

            # After first run → skip already seen
            if not first_run and entry_id in self.seen_entries:
                continue

            self.seen_entries.add(entry_id)

            timestamp = self._extract_timestamp(entry)
            raw_html = getattr(entry, "summary", "")

            components = self._extract_components(raw_html)
            status_message = self._extract_status_message(raw_html)

            events.append({
                "timestamp": timestamp,  # store as datetime first
                "product": f"OpenAI API - {components}",
                "status": status_message
            })

        # Sort newest first
        events.sort(key=lambda x: x["timestamp"], reverse=False)

        # Convert timestamp to string format before returning
        for event in events:
            event["timestamp"] = event["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        return events

    def _extract_timestamp(self, entry):
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        return datetime.utcnow()

    def _extract_components(self, raw_html: str) -> str:
        components = re.findall(r"<li>(.*?)\s*\(", raw_html)
        return ", ".join(components) if components else "General"

    def _extract_status_message(self, raw_html: str) -> str:
        text = html.unescape(raw_html)
        text = re.sub(r"<.*?>", "", text)
        text = re.split(r"Affected components", text, flags=re.IGNORECASE)[0]
        text = text.replace("Status:", "").strip()
        text = re.sub(r"\s+", " ", text)
        text = re.split(r"All impacted services", text, flags=re.IGNORECASE)[0]
        return text.strip()

# ==========================================
# Status Monitor (Orchestrator)
# ==========================================

class StatusMonitor:
    def __init__(self, feed_urls: List[str], interval: int = 10):
        self.feed_urls = feed_urls
        self.clients = {url: FeedClient(url) for url in feed_urls}
        self.parser = FeedParser()
        self.interval = interval
        self.latest_events: List[str] = []
        self._first_run = True

    async def start(self):
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    for url in self.feed_urls:
                        raw_feed = await self.clients[url].fetch(session)

                        if raw_feed:
                            events = self.parser.parse(raw_feed, self._first_run)

                            for event in events:
                                self._add_event(event)

                            self._first_run = False

                except Exception as e:
                    print("[ERROR]:", e)

                await asyncio.sleep(self.interval)

    def _add_event(self, event: dict):
        formatted = (
            f"[{event['timestamp']}] "
            f"Product: {event['product']}\n"
            f"Status: {event['status']}"
        )

        print(formatted + "\n")

        # Insert at top
        self.latest_events.insert(0, formatted)

        # Keep only last 50
        self.latest_events = self.latest_events[:50]