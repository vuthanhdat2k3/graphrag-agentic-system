#!/usr/bin/env python3
"""Evaluate orchestrator on a JSONL file (`question` or `q` per line)."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from src.evaluation.runner import run_jsonl


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("jsonl", type=Path)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    results = await run_jsonl(args.jsonl, limit=args.limit)
    text = json.dumps(results, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    asyncio.run(main())
