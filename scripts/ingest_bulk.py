#!/usr/bin/env python3
"""Batch plain-text ingestion into LightRAG (``ainsert``)."""

from __future__ import annotations

import argparse
import asyncio

from src.ingestion.pipeline import ingest_path


async def main() -> None:
    p = argparse.ArgumentParser(description="Ingest UTF-8 text files into LightRAG.")
    p.add_argument("files", nargs="+", help="Paths to .txt / .md / .csv files")
    p.add_argument(
        "--type",
        default="txt",
        help="File type hint (txt, md, markdown, csv)",
    )
    args = p.parse_args()
    for f in args.files:
        out = await ingest_path(f, args.type)
        print(out)


if __name__ == "__main__":
    asyncio.run(main())
