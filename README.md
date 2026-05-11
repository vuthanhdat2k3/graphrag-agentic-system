# GraphRAG Agentic System

Production-oriented scaffold for **[LightRAG](https://github.com/HKUDS/LightRAG)** (vendored under `vendor/LightRAG`) with **plain-text ingestion** via `ainsert`, **LangGraph** orchestration (Plan → Route → Act → Verify → Stop), **CRAG**, and **Step-back / Query decomposition**. **RAG-Anything** (multimodal) is planned as a later plug-in.

Architecture source: `docs/GraphRAG_AgenticRAG_Architecture_Report.md` (v1.1).

External pattern references: [awesome-llm-apps `rag_tutorials`](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/rag_tutorials).

## LightRAG in this repo

- Expect **`vendor/LightRAG`** (clone or submodule):

  ```bash
  git clone --depth 1 https://github.com/HKUDS/LightRAG.git vendor/LightRAG
  ```

- Install installs **`lightrag-hku`** from that path (`pyproject.toml`). Set **`OPENAI_API_KEY`** (used by LightRAG’s default OpenAI embedding + LLM helpers).

- **Graph storage:** `LIGHTRAG_GRAPH_STORAGE=Neo4JStorage` with `NEO4J_*`, or **`NetworkXStorage`** for local dev without Neo4j.

## Quick start

```bash
cd graphrag-agentic-system
git clone --depth 1 https://github.com/HKUDS/LightRAG.git vendor/LightRAG   # if missing
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env: OPENAI_API_KEY; optional INGEST_ROOT, LIGHTRAG_GRAPH_STORAGE
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Plain-text ingestion

- **CLI:** `python scripts/ingest_bulk.py path/to/doc.md --type md`
- **HTTP:** `POST /v1/ingest/file` with `{"path": "doc.md", "file_type": "md", "dry_run": false}`  
  Set **`INGEST_ROOT`** so relative `path` is resolved under one directory and escapes are rejected.

Supported extensions for this build: **txt, md, markdown, csv** (UTF-8).

## Layout

- `config/` — settings, `lightrag_config.yaml`, prompts.
- `vendor/LightRAG` — upstream HKUDS LightRAG (clone locally; see Docker note).
- `src/core/` — LangGraph orchestrator.
- `src/retrieval/` — LightRAG query wrapper, Cypher, BM25, RRF helpers.
- `src/crag/` — CRAG middleware.
- `src/ingestion/` — `pipeline.py` (`ainsert`); `rag_anything.py` placeholder for later.
- `api/` — FastAPI.

## Docker

```bash
docker compose up --build
```

The **`Dockerfile` copies `vendor/LightRAG`** — ensure that directory exists before `docker build`. For Neo4j graph storage, add the `neo4j` driver to the image or use `pip install -e ".[neo4j]"`.
