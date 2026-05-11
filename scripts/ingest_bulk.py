#!/usr/bin/env python3
"""Batch ingestion CLI — replace stubs with real LightRAG + RAG-Anything."""

from __future__ import annotations

import argparse
import asyncio

from src.ingestion.pipeline import ingest_file_stub


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--type", default="pdf")
    args = p.parse_args()
    for f in args.files:
        print(await ingest_file_stub(lightrag=object(), path=f, file_type=args.type))


if __name__ == "__main__":
    asyncio.run(main())
