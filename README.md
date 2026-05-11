# GraphRAG Agentic System

Production-oriented scaffold for **RAG-Anything → LightRAG (Neo4j)** ingestion, **LangGraph** orchestration (Plan → Route → Act → Verify → Stop), standalone **CRAG** quality layer, and **Step-back / Query decomposition** prompts.

Architecture source: `docs/GraphRAG_AgenticRAG_Architecture_Report.md` (v1.1).

External pattern references: [awesome-llm-apps `rag_tutorials`](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/rag_tutorials) (agentic RAG, corrective RAG, hybrid search tutorials).

## Quick start

```bash
cd graphrag-agentic-system
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Layout

- `config/` — Pydantic settings, `lightrag_config.yaml`, markdown prompts.
- `src/core/` — LangGraph workflow and orchestrator loop.
- `src/retrieval/` — LightRAG wrapper, Cypher, BM25, hybrid (RRF).
- `src/crag/` — CRAG middleware (relevance + consistency); not provided by RAG-Anything/LightRAG.
- `src/ingestion/` — RAG-Anything → LightRAG pipeline hooks.
- `src/agents/` — Tool bindings and step-back helpers.
- `api/` — FastAPI (query / ingest / admin).

## Docker

```bash
docker compose up --build
```

Install optional extras (`lightrag`, `neo4j`) when wiring real LightRAG + Neo4j drivers.
