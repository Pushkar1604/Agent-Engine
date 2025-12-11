"""
Simple in-memory store. Swap with DB later.
"""
from typing import Dict
from app.engine.models import GraphDef, RunState
import asyncio

GRAPHS: Dict[str, GraphDef] = {}
RUNS: Dict[str, RunState] = {}
# For WebSocket streaming: map run_id -> asyncio.Queue
RUN_LOG_QUEUES: Dict[str, "asyncio.Queue"] = {}
