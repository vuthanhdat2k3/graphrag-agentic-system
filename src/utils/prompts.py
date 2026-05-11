"""Load markdown prompts from `config/prompts/`."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_PROMPTS = _ROOT / "config" / "prompts"


@lru_cache
def load_prompt(name: str) -> str:
    path = _PROMPTS / name
    return path.read_text(encoding="utf-8")
