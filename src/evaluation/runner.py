"""Run simple JSONL benchmarks (question / optional gold)."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.orchestrator import AgenticOrchestrator


async def run_jsonl(path: Path, *, limit: int | None = None) -> list[dict]:
    orch = AgenticOrchestrator()
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            q = str(obj.get("question") or obj.get("q") or "").strip()
            if not q:
                continue
            state = await orch.run(q)
            rows.append(
                {
                    "question": q,
                    "answer": state.get("final_answer", ""),
                    "trace": state.get("tool_trace", []),
                    "gold": obj.get("gold"),
                }
            )
    return rows
