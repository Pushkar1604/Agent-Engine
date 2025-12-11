import asyncio
import uuid
import logging
from typing import Dict, Any, Optional
from app.engine.models import GraphDef, NodeDef, RunState, RunLogEntry
from app.store.memory import GRAPHS, RUNS, RUN_LOG_QUEUES
from app.engine.registry import registry

logger = logging.getLogger("engine.core")

class Engine:
    def create_graph(self, graph_id: str, graph_def: GraphDef):
        GRAPHS[graph_id] = graph_def

    def get_graph(self, graph_id: str) -> Optional[GraphDef]:
        return GRAPHS.get(graph_id)

    async def _execute_node(self, run: RunState, node_def: NodeDef):
        """Call node function, update run.state, push logs."""
        fn = registry.get(node_def.fn)
        if fn is None:
            raise RuntimeError(f"Tool '{node_def.fn}' not found")

        logger.info("Running node %s for run %s", node_def.name, run.run_id)
        result = await fn(run.state)
        # merge result into state
        run.state.update(result)
        run.logs.append(RunLogEntry(node=node_def.name, result=result))
        # push to websocket queue if present
        q = RUN_LOG_QUEUES.get(run.run_id)
        if q:
            await q.put({"node": node_def.name, "result": result})
        return result

    async def run_graph(self, graph_id: str, init_state: Dict[str, Any]) -> RunState:
        graph = self.get_graph(graph_id)
        if graph is None:
            raise KeyError("graph not found")

        run_id = str(uuid.uuid4())
        run = RunState(run_id=run_id, graph_id=graph_id, state=dict(init_state))
        RUNS[run_id] = run
        # create a queue for streaming logs
        RUN_LOG_QUEUES[run_id] = asyncio.Queue()

        # run in background task but awaited here so /graph/run returns final state.
        try:
            await self._run_loop(graph, run)
        finally:
            # mark done and cleanup queue if needed (keep logs available)
            run.done = True
            # put sentinel for any websocket listeners
            q = RUN_LOG_QUEUES.get(run_id)
            if q:
                await q.put({"__done__": True})
        return run

    async def start_graph_background(self, graph_id: str, init_state: Dict[str, Any]) -> str:
        """Start the run in a background task: returns run_id immediately."""
        graph = self.get_graph(graph_id)
        if graph is None:
            raise KeyError("graph not found")
        run_id = str(uuid.uuid4())
        run = RunState(run_id=run_id, graph_id=graph_id, state=dict(init_state))
        RUNS[run_id] = run
        RUN_LOG_QUEUES[run_id] = asyncio.Queue()
        # schedule task
        asyncio.create_task(self._run_loop(graph, run))
        return run_id

    async def _run_loop(self, graph: GraphDef, run: RunState):
        """
        Executes nodes starting from graph.start. Supports:
         - linear next
         - branches by checking state keys (truthy)
         - loop_condition: repeat node while state[loop_condition] is False or missing
        """
        current = graph.start
        visited = 0
        max_steps = 1000  # safety limit

        while current:
            if visited > max_steps:
                logger.error("Max steps exceeded for run %s", run.run_id)
                break
            visited += 1

            node_def = graph.nodes.get(current)
            if node_def is None:
                logger.error("Node %s not found in graph %s", current, graph)
                break

            result = await self._execute_node(run, node_def)

            # handle loop: if loop_condition present and state[cond] is falsy -> repeat same node
            if node_def.loop_condition:
                cond_val = run.state.get(node_def.loop_condition)
                if not cond_val:
                    logger.info("Looping on node %s for run %s (cond %s falsy)", current, run.run_id, node_def.loop_condition)
                    await asyncio.sleep(0)  # yield
                    continue  # repeat same node until condition becomes truthy

            # branching: branches is a mapping state_key -> next_node
            if node_def.branches:
                taken = False
                for k, nxt in node_def.branches.items():
                    if run.state.get(k):
                        current = nxt
                        taken = True
                        break
                if taken:
                    continue
                # if no branch matched, fallthrough to `next`
            current = node_def.next

        logger.info("Run %s completed", run.run_id)
