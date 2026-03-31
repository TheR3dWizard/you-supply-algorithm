# bootstrap_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import json
import time
from typing import List
from pathlib import Path
from threading import Lock

app = FastAPI()

# ---------------- CONFIG ----------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

SYSTEM_LOG_FILE = LOG_DIR / "bootstrap_system_log.jsonl"
SNAPSHOT_HISTORY_FILE = LOG_DIR / "snapshot_history.jsonl"

ENABLE_IN_MEMORY_HISTORY = True
MAX_IN_MEMORY_SNAPSHOTS = None  # None = unlimited (RAM permitting)
# ---------------------------------------

# ---------------- STATE ----------------
REGISTRY: List[dict] = []
CURRENT_SNAPSHOT = {
    "nodes": {},
    "edges": [],
    "publisher": None,
    "timestamp": None
}

SNAPSHOT_HISTORY = []  # optional in-memory
WS_CLIENTS = set()

WS_LOCK = asyncio.Lock()
LOG_LOCK = Lock()
# --------------------------------------


# ---------------- LOGGING ----------------
def log_event(event_type: str, payload: dict):
    """
    Append a structured log entry to the system log file.
    """
    entry = {
        "event": event_type,
        "timestamp": time.time(),
        "payload": payload
    }
    with LOG_LOCK:
        with open(SYSTEM_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


def log_snapshot(snapshot: dict):
    """
    Log every snapshot in full (append-only).
    """
    entry = {
        "timestamp": time.time(),
        "snapshot": snapshot
    }
    with LOG_LOCK:
        with open(SNAPSHOT_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
# ----------------------------------------


# ---------------- REST API ----------------
@app.post("/register")
async def register_node(payload: dict):
    nid = payload.get("node_id")
    if not nid:
        return JSONResponse({"error": "node_id required"}, status_code=400)

    global REGISTRY
    REGISTRY = [p for p in REGISTRY if p.get("node_id") != nid]
    REGISTRY.append({
        "node_id": nid,
        "host": payload.get("host"),
        "port": payload.get("port"),
        "lat": payload.get("lat"),
        "lon": payload.get("lon"),
    })

    peers = [p for p in REGISTRY if p.get("node_id") != nid]

    log_event("REGISTER", {
        "node_id": nid,
        "host": payload.get("host"),
        "port": payload.get("port"),
        "lat": payload.get("lat"),
        "lon": payload.get("lon"),
        "peer_count": len(peers)
    })

    return {"peers": peers}


@app.post("/snapshot")
async def post_snapshot(payload: dict):
    """
    Receives snapshot from nodes and broadcasts it.
    """
    global CURRENT_SNAPSHOT, SNAPSHOT_HISTORY

    snapshot = {
        "publisher": payload.get("publisher"),
        "nodes": payload.get("nodes", {}),
        "edges": payload.get("edges", []),
        "timestamp": payload.get("timestamp", time.time())
    }

    CURRENT_SNAPSHOT = snapshot

    # log snapshot (full)
    log_snapshot(snapshot)

    # system log
    log_event("SNAPSHOT_RECEIVED", {
        "publisher": snapshot["publisher"],
        "node_count": len(snapshot["nodes"]),
        "edge_count": len(snapshot["edges"]),
        "timestamp": snapshot["timestamp"]
    })

    # optional in-memory history
    if ENABLE_IN_MEMORY_HISTORY:
        SNAPSHOT_HISTORY.append(snapshot)
        if MAX_IN_MEMORY_SNAPSHOTS and len(SNAPSHOT_HISTORY) > MAX_IN_MEMORY_SNAPSHOTS:
            SNAPSHOT_HISTORY.pop(0)

    # broadcast to WS clients
    asyncio.create_task(broadcast_snapshot(snapshot))

    return {"status": "ok"}


@app.get("/latest_snapshot")
async def latest_snapshot():
    return CURRENT_SNAPSHOT
# -----------------------------------------


# ---------------- WEBSOCKET ----------------
async def broadcast_snapshot(snapshot: dict):
    payload = json.dumps(snapshot)

    async with WS_LOCK:
        clients = list(WS_CLIENTS)

    dead = []
    for ws in clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)

    if dead:
        async with WS_LOCK:
            for d in dead:
                WS_CLIENTS.discard(d)


@app.websocket("/ws_snapshot")
async def websocket_snapshot_endpoint(websocket: WebSocket):
    await websocket.accept()

    async with WS_LOCK:
        WS_CLIENTS.add(websocket)

    log_event("WS_CONNECT", {
        "client": str(websocket.client),
        "active_clients": len(WS_CLIENTS)
    })

    try:
        # send current snapshot immediately
        await websocket.send_text(json.dumps(CURRENT_SNAPSHOT))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        async with WS_LOCK:
            WS_CLIENTS.discard(websocket)

        log_event("WS_DISCONNECT", {
            "client": str(websocket.client),
            "active_clients": len(WS_CLIENTS)
        })
# -------------------------------------------


# ---------------- RUN ----------------
if __name__ == "__main__":
    uvicorn.run("bootstrap_server:app", host="0.0.0.0", port=8000, reload=True)