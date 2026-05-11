"""Raw Cypher execution (Neo4j driver) — stub."""

from __future__ import annotations

from typing import Any, Protocol


class CypherClient(Protocol):
    async def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict]: ...


class CypherStub:
    async def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict]:
        _ = params
        return [{"note": "stub", "cypher": cypher[:200]}]


cypher_stub: CypherClient = CypherStub()
