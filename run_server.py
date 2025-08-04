from fastapi import FastAPI, BackgroundTasks
from main import main
import uvicorn
import asyncio
import aiohttp

app = FastAPI()


async def run_sync():
    print("Running Classroom to Notion sync...")
    try:
        result = await asyncio.to_thread(main)
        print(result)
        return result
    except Exception as e:
        print(f"Error during sync: {str(e)}")
        return {"error": str(e)}


@app.post("/trigger-sync")
async def trigger_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_sync)
    return {
        "message": "Sync task has been triggered and is running in the background. Check your Notion workspace for updates."
    }


@app.post("/run-sync")
async def run_sync_endpoint():
    result = await run_sync()
    return result


@app.get("/")
async def root():
    return {"message": "Classroom to Notion Sync Server is running"}


async def schedule_sync():
    async with aiohttp.ClientSession() as session:
        while True:
            await asyncio.sleep(180)  # Wait for 3 minutes
            try:
                async with session.post(
                    "http://localhost:8888/trigger-sync"
                ) as response:
                    print(f"Scheduled sync triggered. Response: {response.status}")
            except Exception as e:
                print(f"Error triggering scheduled sync: {e}")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(schedule_sync())


@app.post("/test")
async def test():
    result = await run_sync()
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
