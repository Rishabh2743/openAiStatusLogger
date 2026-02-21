import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from statusLogger import StatusMonitor
from api import router, set_monitor_instance


PROVIDERS = ["https://status.openai.com/history.atom"]
monitor = StatusMonitor(PROVIDERS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting OpenAI Status Monitor...")

    task = asyncio.create_task(monitor.start())

    yield

    task.cancel()
    print("🛑 Shutting down monitor...")


app = FastAPI(lifespan=lifespan)

set_monitor_instance(monitor)
app.include_router(router)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)