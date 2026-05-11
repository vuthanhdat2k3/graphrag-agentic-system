"""Raw Cypher execution (Neo4j async driver) with stub fallback."""

from __future__ import annotations

from typing import Any, Protocol

from config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CypherClient(Protocol):
    async def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict]: ...


class CypherStub:
    async def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict]:
        _ = params
        return [{"note": "stub", "cypher": cypher[:200]}]


class Neo4jCypherClient:
    """Uses `neo4j` async driver when the optional extra is installed."""

    def __init__(self) -> None:
        self._driver = None

    async def run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict]:
        try:
            from neo4j import AsyncGraphDatabase
        except ImportError:
            return await CypherStub().run(cypher, params)

        if self._driver is None:
            s = get_settings()
            self._driver = AsyncGraphDatabase.driver(
                s.neo4j_uri,
                auth=(s.neo4j_username, s.neo4j_password),
            )
        try:
            async with self._driver.session() as session:
                result = await session.run(cypher, parameters=params or {})
                data = await result.data()
                return data
        except Exception as exc:  # noqa: BLE001
            logger.warning("cypher_run_failed: %s", exc)
            return [{"error": str(exc)[:500]}]


cypher_stub: CypherClient = CypherStub()


def make_cypher_client() -> CypherClient:
    try:
        import neo4j  # noqa: F401
    except ImportError:
        return cypher_stub
    return Neo4jCypherClient()
