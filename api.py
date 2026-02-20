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
    html_content = "<br><br>".join(monitor_instance.latest_events)
    return f"""
    <html>
        <head>
            <title>OpenAI Status Monitor</title>
            <meta http-equiv="refresh" content="5">
        </head>
        <body>
            <h2>OpenAI Status Monitor</h2>
            <p>{html_content}</p>
        </body>
    </html>
    """