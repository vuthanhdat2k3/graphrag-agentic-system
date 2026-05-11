"""Extract JSON objects / arrays from LLM outputs."""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

T = TypeVar("T")


def parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"\{[\s\S]*\}", text)
    if fence:
        text = fence.group(0)
    return json.loads(text)


def parse_json_array(text: str) -> list[Any]:
    text = text.strip()
    fence = re.search(r"\[[\s\S]*\]", text)
    if fence:
        text = fence.group(0)
    return json.loads(text)
