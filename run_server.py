from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Query, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
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
    enable_scheduler = os.getenv("ENABLE_SCHEDULER", "false").lower() in ("1", "true", "yes")
    if enable_scheduler:
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


@app.get("/", response_class=HTMLResponse)
async def root():
        return """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Classroom → Notion Sync</title>
    <style>
        :root { color-scheme: light dark; }
        body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; padding: 24px; line-height: 1.5; }
        .container { max-width: 780px; margin: 0 auto; }
        h1 { margin: 0 0 8px; font-size: 1.6rem; }
        .card { border: 1px solid #ccc3; border-radius: 10px; padding: 16px; margin: 16px 0; }
        label { display: block; font-weight: 600; margin-top: 10px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ccc6; font-size: 0.95rem; }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 14px; }
        button { padding: 10px 14px; border-radius: 8px; border: 1px solid #8884; cursor: pointer; background: #2b7; color: #fff; font-weight: 600; }
        button.secondary { background: #09f; }
        button.ghost { background: transparent; color: inherit; border-color: #8886; }
        .small { font-size: 0.9rem; color: #888; }
        pre { background: #0000000c; padding: 12px; border-radius: 8px; overflow: auto; max-height: 360px; }
    </style>
    <script>
        function $(id){ return document.getElementById(id); }
        function setStatus(msg){ $("status").textContent = msg; }
        function savePrefs(){
            const prefs = { secret: $("secret").value, after_date: $("after_date").value };
            localStorage.setItem("ctn_prefs", JSON.stringify(prefs));
        }
        function loadPrefs(){
            try {
                const p = JSON.parse(localStorage.getItem("ctn_prefs") || "{}");
                if(p.secret) $("secret").value = p.secret;
                if(p.after_date) $("after_date").value = p.after_date;
            } catch(e) {}
        }
        function yesterdayStr(){
            const d = new Date(); d.setDate(d.getDate()-1);
            const y = d.getFullYear(); const m = d.getMonth()+1; const day = d.getDate();
            return `${y}/${m}/${day}`; // matches YYYY/M/D accepted by backend
        }
        async function callEndpoint(path){
            const base = location.origin;
            const secret = $("secret").value.trim();
            const after = $("after_date").value.trim();
            if(!secret){ alert("API Secret is required"); return; }
            const url = new URL(base + path);
            if(after) url.searchParams.set("after_date", after);
            setStatus("Calling " + url.pathname + "…");
            try {
                const res = await fetch(url, { method: "POST", headers: { Authorization: `Bearer ${secret}` } });
                const txt = await res.text();
                let out = txt;
                try { out = JSON.stringify(JSON.parse(txt), null, 2); } catch {}
                $("output").textContent = out;
                setStatus(`Response ${res.status} ${res.statusText}`);
            } catch (e) {
                $("output").textContent = String(e);
                setStatus("Request failed");
            }
            savePrefs();
        }
        async function health(){
            const res = await fetch("/health");
            const data = await res.json();
            $("output").textContent = JSON.stringify(data, null, 2);
            setStatus(`Health ${res.status}`);
        }
        window.addEventListener("DOMContentLoaded", () => {
            loadPrefs();
            if(!$("after_date").value){ $("after_date").value = yesterdayStr(); }
            health();
        });
    </script>
    </head>
    <body>
        <div class="container">
            <h1>Classroom → Notion Sync</h1>
            <div class="small">Use this page to run or trigger background syncs. Your secret is stored in your browser only.</div>

            <div class="card">
                <div class="row">
                    <div>
                        <label for="secret">API Secret (Bearer)</label>
                        <input id="secret" type="password" placeholder="Enter API secret" />
                    </div>
                    <div>
                        <label for="after_date">After Date (YYYY/MM/DD)</label>
                        <input id="after_date" type="text" placeholder="e.g. 2025/8/1" />
                    </div>
                </div>
                <div class="actions">
                    <button onclick="callEndpoint('/run-sync')">Run Sync (wait)</button>
                    <button class="secondary" onclick="callEndpoint('/trigger-sync')">Trigger Sync (background)</button>
                    <button class="ghost" onclick="document.getElementById('after_date').value = yesterdayStr(); savePrefs();">Set Yesterday</button>
                    <button class="ghost" onclick="health()">Health</button>
                </div>
                <div id="status" class="small" style="margin-top:8px;">Ready</div>
            </div>

            <div class="card">
                <div><strong>Response</strong></div>
                <pre id="output">(no response yet)</pre>
            </div>
        </div>
    </body>
</html>
"""


async def schedule_sync():
    async with aiohttp.ClientSession() as session:
        # Add authorization header for scheduled sync
        headers = {"Authorization": f"Bearer {API_SECRET}"}
        while True:
            await asyncio.sleep(180)  # Wait for 3 minutes
            try:
                base_url = os.getenv("API_URL", "http://localhost:8888").rstrip("/")
                async with session.post(f"{base_url}/trigger-sync", headers=headers) as response:
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
