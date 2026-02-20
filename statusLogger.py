import asyncio
import aiohttp
import feedparser
import re
import html
from datetime import datetime
from typing import Optional, List


# ==========================================
# Feed Client
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

            self.etag = response.headers.get("ETag")
            self.last_modified = response.headers.get("Last-Modified")

            return content


# ==========================================
# Feed Parser
# ==========================================

class FeedParser:
    def __init__(self):
        self.seen_entries = set()
        self.initialized = False

    def parse(self, raw_feed: str) -> List[dict]:
        events = []
        feed = feedparser.parse(raw_feed)

        for entry in feed.entries:
            entry_id = getattr(entry, "id", getattr(entry, "link", None))
            if not entry_id:
                continue

            # First run → print all
            if not self.initialized:
                self.seen_entries.add(entry_id)

            # After first run → only new
            elif entry_id in self.seen_entries:
                continue
            else:
                self.seen_entries.add(entry_id)

            timestamp = self._extract_timestamp(entry)
            raw_html = getattr(entry, "summary", "")

            components = self._extract_components(raw_html)
            status_message = self._extract_status_message(raw_html)

            product = f"OpenAI API - {components}"

            events.append({
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "product": product,
                "status": status_message
            })

        self.initialized = True
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
# Monitor Service
# ==========================================

class StatusMonitor:
    def __init__(self, feed_urls: List[str], concurrency_limit: int = 20):
        self.feed_urls = feed_urls
        self.clients = {url: FeedClient(url) for url in feed_urls}
        self.parser = FeedParser()
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.latest_events: List[str] = []

    async def _fetch_one(self, url: str, session: aiohttp.ClientSession):
        async with self.semaphore:
            return await self.clients[url].fetch(session)

    async def start(self, interval: int = 10):
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    tasks = [
                        self._fetch_one(url, session)
                        for url in self.feed_urls
                    ]

                    raw_results = await asyncio.gather(*tasks)

                    for raw_feed in raw_results:
                        if raw_feed:
                            events = self.parser.parse(raw_feed)
                            for event in events:
                                self._log(event)

                except Exception as e:
                    print("[ERROR]:", e)

                await asyncio.sleep(interval)

    def _log(self, event: dict):
        formatted = (
            f"[{event['timestamp']}] "
            f"Product: {event['product']}\n"
            f"Status: {event['status']}"
        )

        print(formatted + "\n")

        self.latest_events.insert(0, formatted)
        self.latest_events = self.latest_events[:50]