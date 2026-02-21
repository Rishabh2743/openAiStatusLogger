from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from statusLogger import StatusMonitor

router = APIRouter()

monitor_instance: StatusMonitor = None


def set_monitor_instance(instance: StatusMonitor):
    global monitor_instance
    monitor_instance = instance


@router.get("/")
async def root():
    return {"message": "OpenAI Status Monitor is running"}


@router.get("/health")
async def health():
    return {"status": "healthy"}


@router.get("/events")
async def get_events():
    return {"events": monitor_instance.latest_events}


@router.get("/live", response_class=HTMLResponse)
async def live_view():
    return """
    <html>
        <head>
            <title>OpenAI Status Monitor</title>

            <style>
                body { font-family: Arial; margin: 40px; }
                .event {
                    margin-bottom: 15px;
                    padding: 10px;
                    border-left: 4px solid #007BFF;
                    background: #f4f6f8;
                    white-space: pre-line;
                }
            </style>

            <script>
                async function fetchEvents() {
                    const response = await fetch('/events');
                    const data = await response.json();

                    const container = document.getElementById("events");
                    container.innerHTML = "";

                    data.events.forEach(event => {
                        const div = document.createElement("div");
                        div.className = "event";
                        div.textContent = event;
                        container.appendChild(div);
                    });
                }

                // Poll every 5 seconds
                setInterval(fetchEvents, 5000);

                // Load immediately
                window.onload = fetchEvents;
            </script>
        </head>

        <body>
            <h2>OpenAI Status Monitor (Live)</h2>
            <div id="events">Loading...</div>
        </body>
    </html>
    """