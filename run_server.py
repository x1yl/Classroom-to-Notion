from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Query, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from main import main
import uvicorn
import asyncio
import aiohttp
import os
from typing import Optional, Annotated
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security setup
security = HTTPBearer()
API_SECRET = os.getenv("API_SECRET")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the API token"""
    if credentials.credentials != API_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(schedule_sync())
    yield


app = FastAPI(lifespan=lifespan)


async def run_sync(after_date: Optional[str] = None):
    print("Running Classroom to Notion sync...")
    if after_date:
        print(f"Using date filter: after:{after_date}")
    try:
        result = await asyncio.to_thread(main, after_date)
        print(result)
        return result
    except Exception as e:
        print(f"Error during sync: {str(e)}")
        return {"error": str(e)}


@app.post("/trigger-sync")
async def trigger_sync(
    background_tasks: BackgroundTasks, 
    after_date: Optional[str] = Query(None),
    token: str = Depends(verify_token)
):
    background_tasks.add_task(run_sync, after_date)
    message = "Sync task has been triggered and is running in the background. Check your Notion workspace for updates."
    if after_date:
        message += f" Using date filter: after:{after_date}"
    return {"message": message}


@app.post("/run-sync")
async def run_sync_endpoint(
    after_date: Optional[str] = Query(None),
    token: str = Depends(verify_token)
):
    result = await run_sync(after_date)
    return result


@app.get("/")
async def root():
    return {"message": "Classroom to Notion Sync Server is running"}


async def schedule_sync():
    async with aiohttp.ClientSession() as session:
        # Add authorization header for scheduled sync
        headers = {"Authorization": f"Bearer {API_SECRET}"}
        while True:
            await asyncio.sleep(180)  # Wait for 3 minutes
            try:
                async with session.post(
                    f"${{API_URL}}/trigger-sync",
                    headers=headers
                ) as response:
                    print(f"Scheduled sync triggered. Response: {response.status}")
            except Exception as e:
                print(f"Error triggering scheduled sync: {e}")


@app.post("/test")
async def test(
    after_date: Optional[str] = Query(None),
    token: str = Depends(verify_token)
):
    result = await run_sync(after_date)
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
