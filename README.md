# OpenAI Status Monitor

A lightweight asynchronous Python application that automatically tracks and logs service updates from the OpenAI Status Page.

---

## 🚀 Overview

This project monitors the OpenAI status feed and automatically detects:

- New incidents
- Service outages
- Degraded performance
- Elevated error rates

Whenever a new update appears, it prints:

- The affected product/service
- The latest status message

Example console output:
[2026-01-08 02:30:50] Product: OpenAI API - Codex
Status: Elevated error rates detected

[2026-01-07 23:53:27] Product: OpenAI API - Responses
Status: Degraded performance

---

## 🧠 Design & Architecture

This solution follows clean architecture principles and separation of concerns.

### 🔹 Components

### 1️⃣ FeedClient
- Responsible for HTTP communication
- Uses `ETag` and `Last-Modified` headers
- Avoids unnecessary re-fetching
- Efficient conditional requests

### 2️⃣ FeedParser
- Parses Atom/RSS feed
- Extracts:
  - Timestamp
  - Affected components
  - Status message
- Prevents duplicate processing
- Sorts newest incidents first

### 3️⃣ StatusMonitor
- Orchestrates async feed monitoring
- Supports multiple providers
- Maintains in-memory event store
- Detects only new updates after first run

---

## ⚡ Efficiency & Scalability

This solution avoids inefficient polling by:

- Using HTTP conditional requests (ETag & If-Modified-Since)
- Only processing feed when content changes
- Leveraging asynchronous architecture
- Supporting concurrent monitoring of 100+ feeds

To scale to additional providers:

```python
PROVIDERS = [
    "https://status.openai.com/history.atom",
    "https://another-provider.com/status.atom"
]
```
```
git clone https://github.com/Rishabh2743/openAiStatusLogger.git
cd LogMonitor
pip install -r requirements.txt
http://localhost:8000/live
```
👨‍💻 Author

Rishabh Raj
