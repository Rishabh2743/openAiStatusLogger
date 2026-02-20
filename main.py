import os
import asyncio
from fastapi import FastAPI
import uvicorn
from statusLogger import StatusMonitor
from api import router, set_monitor_instance


app = FastAPI()

PROVIDERS = ["https://status.openai.com/history.atom"]

monitor = StatusMonitor(PROVIDERS)

set_monitor_instance(monitor)

app.include_router(router)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor.start(interval=60))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)