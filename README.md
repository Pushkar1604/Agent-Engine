# Minimal Agent Workflow Engine

> A clean, async, extensible workflow engine (FastAPI) implementing a small agent/workflow runner:
> node-based execution, shared state, branching, looping, tool registry, WebSocket logs, and Docker support.  
> (Built to satisfy the AI Engineering Internship assignment.) :contentReference[oaicite:0]{index=0}

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Design & Engine Details](#design--engine-details)
- [API Reference](#api-reference)
- [Example Graph JSON](#example-graph-json)
- [Running Locally](#running-locally)
- [Running with Docker](#running-with-docker)
- [Testing & Quick Run Script](#testing--quick-run-script)
- [How This Meets the Evaluation Criteria](#how-this-meets-the-evaluation-criteria)
- [Improvements & Future Work](#improvements--future-work)
- [Contact / Notes](#contact--notes)

---

## Overview

This repository contains a minimal but well-structured backend workflow engine that:

- Accepts graph definitions composed of nodes and edges.
- Executes nodes (async Python functions, called *tools*) that read and update a shared `state`.
- Supports branching and looping.
- Exposes a small set of clean FastAPI endpoints to create/run graphs and fetch run state.
- Streams per-node logs to clients via WebSocket for observability.
- Includes Docker + `docker-compose` to run the service easily for evaluation.

---

## Features

- **Node-based execution**: Nodes are async functions registered in a tool registry.
- **Shared state**: A dictionary flows between nodes and is updated incrementally.
- **Branching**: Conditional transitions using `branches: {state_key: node_name}`.
- **Looping**: `loop_condition` repeats a node until the provided state key becomes truthy.
- **Tool registry**: Simple pluggable registry for tools (functions).
- **FastAPI endpoints**: Create graph, run graph (foreground/background), get run state.
- **WebSocket logs**: Stream per-node execution results in real-time.
- **In-memory store**: Simple `GRAPHS`, `RUNS`, and `RUN_LOG_QUEUES` dictionaries (easy to swap for DB).
- **Docker-ready**: `Dockerfile` + `docker-compose.yml` included.

---

## Project Structure
```markdown

📦 agent-engine/
│
├── 📁 app/
│   ├── 🚀 main.py                  → FastAPI app, REST + WebSocket
│   │
│   ├── 🧠 engine/
│   │   ├── 📝 models.py            → NodeDef, GraphDef, RunState
│   │   ├── 🔧 registry.py          → Tool registry (async node functions)
│   │   └── ⚙️ core.py              → Workflow execution engine
│   │
│   ├── 🤖 workflows/
│   │   └── code_review.py         → Example Code Review Mini-Agent (Option A)
│   │
│   ├── 🗄 store/
│   │   └── memory.py              → In-memory storage for graphs + runs
│   │
│   └── 🛠 utils/
│       └── logging_config.py      → Structured logging setup
│
├── 🧪 tests/
│   └── quick_run.sh               → End-to-end test script
│
├── 🐳 Dockerfile                  → Container build
├── 🐙 docker-compose.yml          → Easy multi-service orchestration
├── 📜 requirements.txt            → Dependencies
└── 📘 README.md                   → Documentation



---

## Design & Engine Details

### Node definition (high level)
Each node definition supports:
- `fn` - the tool name (maps to a registered async function).
- `next` - the next node name for linear flow.
- `branches` - dict mapping `state_key -> node_name` to support conditional branching.
- `loop_condition` - state key name; if falsy, node repeats until it becomes truthy.

### Execution algorithm (core ideas)
1. Start at `graph.start`.
2. Execute the node's tool: `await tool(state)`.
3. Merge returned partial state into the run state.
4. Append a log entry and push it to the run's WebSocket queue (if any).
5. Decide next:
   - If `loop_condition` present and state[cond] is falsy → repeat same node.
   - Else if any `branches` conditions evaluate truthy → follow the first matching branch.
   - Else → move to `next`.
6. Terminate when no next node remains.

A safety `max_steps` guard prevents runaway loops.

---

## API Reference

### `POST /graph/create`
Register a graph. Request body: Graph JSON (see example). Returns:
```json
{ "graph_id": "<uuid>" }
POST /graph/run

Run a graph.
Request body:

{
  "graph_id": "<graph_id>",
  "state": { ... initial state ... },
  "background": false   // optional, if true returns run_id immediately and executes in background
}


Foreground: returns final RunState (state + logs + done flag).

Background: returns { "run_id": "<id>", "background": true }.

GET /graph/state/{run_id}

Returns the current RunState:

{
  "run_id": "...",
  "graph_id": "...",
  "state": { ... },
  "logs": [ {"node":"...","result":{...}}, ... ],
  "done": true|false
}

WS /ws/logs/{run_id}

Connect to get a stream of per-node log messages as JSON objects:

Each message: { "node": "<node_name>", "result": { ... } }

Final sentinel: { "__done__": true }

Example Graph JSON
{
  "start": "extract",
  "nodes": {
    "extract": {
      "fn": "extract_functions",
      "next": "complexity"
    },
    "complexity": {
      "fn": "check_complexity",
      "next": "issues"
    },
    "issues": {
      "fn": "detect_issues",
      "next": "improve"
    },
    "improve": {
      "fn": "suggest_improvements",
      "loop_condition": "quality_ok",
      "next": null
    }
  }
}


Note: Tools used in the example are defined in app/workflows/code_review.py. The suggest_improvements node writes quality_ok to state based on a quality_threshold provided in the initial state.

Running Locally

Create a virtualenv and install:

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


Start the server:

uvicorn app.main:app --reload --port 8000


Open docs:

http://localhost:8000/docs

Running with Docker

Build & run with Docker Compose (recommended for evaluation):

docker-compose up --build -d


FastAPI will be available at http://localhost:8000/docs.

To stop: docker-compose down.

Testing & Quick Run Script

A small tests/quick_run.sh script is provided to:

create an example graph,

run it (foreground),

print the run result.

Make it executable:

chmod +x tests/quick_run.sh
./tests/quick_run.sh
