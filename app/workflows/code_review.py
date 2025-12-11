import asyncio
from app.engine.registry import registry
import random
from typing import Dict, Any

# node tools are async and accept the shared state, then return partial state updates

async def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    await asyncio.sleep(0.05)  # simulate IO
    code = state.get("code", "")
    # naive extraction (example)
    funcs = [f"func_{i}" for i, _ in enumerate(code.splitlines()) if "def " in _]
    return {"functions": funcs, "extracted": True}

async def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    await asyncio.sleep(0.05)
    # pretend complexity is random or proportional to num functions
    complexity = max(1, len(state.get("functions", [])) * random.randint(1, 5))
    return {"complexity": complexity}

async def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    await asyncio.sleep(0.05)
    issues = random.randint(0, 4)
    return {"issues": issues}

async def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    await asyncio.sleep(0.05)
    complexity = state.get("complexity", 5)
    issues = state.get("issues", 0)
    quality_score = max(0, 10 - (complexity + issues))
    # decide loop condition key 'quality_ok'
    threshold = state.get("quality_threshold", 7)
    return {"quality_score": quality_score, "quality_ok": quality_score >= threshold}

# register tools
registry.register("extract_functions", extract_functions)
registry.register("check_complexity", check_complexity)
registry.register("detect_issues", detect_issues)
registry.register("suggest_improvements", suggest_improvements)
