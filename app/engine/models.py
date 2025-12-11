from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List


class NodeDef(BaseModel):
    """Definition of a node in the graph."""
    name: str
    fn: str                             # registered tool name
    next: Optional[str] = None          # next node name (default linear)
    branches: Dict[str, str] = {}       # state-key -> node name (branching)
    loop_condition: Optional[str] = None  # state key name; loop while False


class GraphDef(BaseModel):
    start: str
    nodes: Dict[str, NodeDef]


class RunLogEntry(BaseModel):
    node: str
    result: Dict[str, Any]


class RunState(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any] = Field(default_factory=dict)
    logs: List[RunLogEntry] = Field(default_factory=list)
    done: bool = False
