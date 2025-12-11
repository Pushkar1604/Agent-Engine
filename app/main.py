from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
from app.utils.logging_config import configure_logging
from app.engine.models import GraphDef, NodeDef
from app.engine.core import Engine
from app.store.memory import GRAPHS, RUNS, RUN_LOG_QUEUES
import asyncio

configure_logging()
engine = Engine()
app = FastAPI(title="Minimal Agent Workflow Engine")

# request models
class CreateGraphRequest(BaseModel):
    graph_id: str | None = None
    start: str
    nodes: dict

class RunRequest(BaseModel):
    graph_id: str
    state: dict
    background: bool = False  # run async in background if True

@app.post("/graph/create")
async def create_graph(req: CreateGraphRequest):
    graph_id = req.graph_id or str(uuid.uuid4())
    # validate nodes -> build GraphDef
    nodes = {}
    for name, nd in req.nodes.items():
        nodes[name] = NodeDef(name=name, **nd)
    graph = GraphDef(start=req.start, nodes=nodes)
    engine.create_graph(graph_id, graph)
    return {"graph_id": graph_id}

@app.post("/graph/run")
async def run_graph(req: RunRequest, background: BackgroundTasks):
    if req.graph_id not in GRAPHS:
        raise HTTPException(status_code=404, detail="graph not found")

    if req.background:
        # start and return run_id immediately
        run_id = await engine.start_graph_background(req.graph_id, req.state)
        return {"run_id": run_id, "background": True}
    else:
        run = await engine.run_graph(req.graph_id, req.state)
        return JSONResponse(content=run.dict())

@app.get("/graph/state/{run_id}")
async def get_run_state(run_id: str):
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run.dict()

@app.websocket("/ws/logs/{run_id}")
async def ws_logs(websocket: WebSocket, run_id: str):
    await websocket.accept()
    queue = RUN_LOG_QUEUES.get(run_id)
    if queue is None:
        # if no queue yet, create a temporary one so WS can receive if run starts later
        queue = asyncio.Queue()
        RUN_LOG_QUEUES[run_id] = queue

    try:
        while True:
            message = await queue.get()
            await websocket.send_json(message)
            if isinstance(message, dict) and message.get("__done__"):
                break
    except WebSocketDisconnect:
        return
    finally:
        await websocket.close()
