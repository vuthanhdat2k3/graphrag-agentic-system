# Báo Cáo Thiết Kế Kiến Trúc Hệ Thống
## Multi-Dimensional Knowledge Retrieval & Complex Reasoning
### GraphRAG + Agentic RAG + CRAG + Step-back Prompting

---

| Thuộc tính | Chi tiết |
|---|---|
| **Dự án** | Hệ thống Liên kết Dữ kiện Đa chiều & Suy luận Phức hợp |
| **Nền tảng RAG** | RAG-Anything → LightRAG (HKUDS) |
| **Graph Storage** | Neo4j (cấu hình qua LightRAG storage backend) |
| **Phiên bản** | v1.1 — Revised Architecture (đã cập nhật thực tế stack) |
| **Ngày lập** | Tháng 5, 2026 |
| **Phân loại** | Tài liệu kỹ thuật nội bộ |

---

## Mục Lục

1. [Tổng Quan & Làm Rõ Stack Thực Tế](#1-tổng-quan--làm-rõ-stack-thực-tế)
2. [Kiến Trúc 5 Lớp (Revised)](#2-kiến-trúc-5-lớp-revised)
3. [LightRAG — Graph Engine Thực Tế](#3-lightrag--graph-engine-thực-tế)
4. [CRAG — Phải Implement Riêng](#4-crag--phải-implement-riêng)
5. [Agentic Orchestrator & System Prompt](#5-agentic-orchestrator--system-prompt)
6. [Step-back Prompting & Query Decomposition](#6-step-back-prompting--query-decomposition)
7. [Local Traversal & Suy Luận Đa Bước](#7-local-traversal--suy-luận-đa-bước)
8. [Schema Neo4j](#8-schema-neo4j)
9. [Stack Công Nghệ & Cấu Hình](#9-stack-công-nghệ--cấu-hình)
10. [Hiệu Năng & SLA](#10-hiệu-năng--sla)
11. [Rủi Ro & Giảm Thiểu](#11-rủi-ro--giảm-thiểu)
12. [Lộ Trình Triển Khai](#12-lộ-trình-triển-khai)

---

## 1. Tổng Quan & Làm Rõ Stack Thực Tế

### 1.1 Hai Điểm Cần Làm Rõ Về RAG-Anything

Trước khi đi vào kiến trúc, cần xác nhận lại hai điểm kỹ thuật quan trọng ảnh hưởng trực tiếp đến thiết kế:

#### RAG-Anything có tích hợp Neo4j không?

**Không trực tiếp — nhưng gián tiếp qua LightRAG.**

RAG-Anything (HKUDS) là một **multimodal ingestion layer**. Chức năng cốt lõi là parse PDF, DOCX, bảng, hình ảnh, công thức rồi đẩy vào **LightRAG** để xử lý. LightRAG (cùng nhóm HKUDS) đã tích hợp Neo4j storage backend từ tháng 11/2024.

Stack thực tế:

```
RAG-Anything (parse & ingest)
    ↓
LightRAG (graph construction + retrieval)
    ↓
Neo4j (graph storage backend — cấu hình trong LightRAG)
```

Neo4j **có thể dùng được**, nhưng phải cấu hình ở tầng LightRAG, không phải RAG-Anything. RAG-Anything không expose Neo4j API trực tiếp.

#### RAG-Anything có phải là Corrective RAG (CRAG) không?

**Không.** Đây là hai thứ hoàn toàn khác nhau:

| Tiêu chí | RAG-Anything | CRAG (Corrective RAG) |
|---|---|---|
| Nguồn gốc | HKUDS — multimodal ingestion framework | Yan et al. 2024 — kỹ thuật riêng |
| Mục đích | Parse đa modal + đưa vào LightRAG | Đánh giá chất lượng retrieved docs |
| Có retrieval evaluator? | Không | Có |
| Có trigger web search fallback? | Không | Có |
| Có self-correction loop? | Không | Có |

> **Kết luận:** CRAG phải được **implement riêng** như một post-retrieval middleware, đặt sau LightRAG output và trước Orchestrator.

---

### 1.2 Mục Tiêu Thiết Kế

- Trả lời chính xác các câu hỏi phức tạp, đa chiều thông qua suy luận liên kết nhiều thực thể.
- Đảm bảo tính nhất quán thông tin — phát hiện và giải quyết xung đột dữ kiện nội tại.
- Tự chủ hoàn toàn trong chu trình retrieval: lên kế hoạch → định tuyến → hành động → xác minh → dừng.
- Tối ưu hiệu suất qua dynamic routing: chọn đúng công cụ cho từng loại truy vấn.
- Khả năng mở rộng vòng lặp truy xuất khi context ban đầu chưa đủ.

---

## 2. Kiến Trúc 5 Lớp (Revised)

```
┌─────────────────────────────────────────────────────────────┐
│  ① USER INTERFACE LAYER                                     │
│  Step-back Prompting → Query Decomposition → Sub-questions  │
└──────────────────────────────┬──────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│  ② AGENTIC ORCHESTRATOR                                     │
│  Plan → Route → Act → Verify → Stop                        │
│  [ System Prompt Engine — ReAct / CoT / Tool-calling ]     │
└──────────┬──────────────┬──────────────┬────────────────────┘
           ↓              ↓              ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────────────── ┐
│  Cypher      │  │  BM25        │  │  Vector Search           │
│  (LightRAG   │  │  Sparse      │  │  Dense Retrieval         │
│   + Neo4j)   │  │  Retrieval   │  │  (LightRAG built-in)     │
└──────┬───────┘  └──────┬───────┘  └──────────┬──────────────┘
       └──────────────── ↓ ─────────────────────┘
                         ↓  merged context
┌─────────────────────────────────────────────────────────────┐
│  ③ CRAG MODULE (implement riêng)                            │
│  Relevance scoring → Conflict detection → Self-correction   │
└──────────────────────────────┬──────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│  ④ KNOWLEDGE STORE                                          │
│  Neo4j Graph DB │ Vector Index │ BM25 Index │ Redis Cache   │
└──────────────────────────────┬──────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────┐
│  ⑤ DATA INGESTION — RAG-Anything + LightRAG Pipeline       │
│  Parse → Entity Extract → Graph Build → Dual Index         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. LightRAG — Graph Engine Thực Tế

RAG-Anything delegates toàn bộ graph construction và retrieval cho LightRAG. Đây là engine cần hiểu rõ nhất.

### 3.1 Dual-Level Retrieval của LightRAG

LightRAG không phải vanilla RAG — nó có **hai chế độ retrieval** hoạt động song song:

| Chế độ | Cơ chế | Phù hợp với |
|---|---|---|
| **Local retrieval** | Traverse từ entity anchor node, k-hop expansion | Câu hỏi về thực thể cụ thể, quan hệ trực tiếp |
| **Global retrieval** | Community-level reasoning, aggregate over clusters | Câu hỏi tổng hợp, xu hướng, pattern |

LightRAG tự động kết hợp cả hai qua **hybrid mode** — đây là điểm mạnh so với GraphRAG của Microsoft.

### 3.2 Cấu Hình Neo4j Storage trong LightRAG

```python
from lightrag import LightRAG
from lightrag.kg.neo4j_impl import Neo4JStorage

rag = LightRAG(
    working_dir="./rag_storage",
    graph_storage="Neo4JStorage",        # ← chỉ định Neo4j backend
    # LightRAG tự inject Neo4JStorage class
)

# Biến môi trường bắt buộc
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USERNAME=neo4j
# NEO4J_PASSWORD=your_password
```

### 3.3 Ingestion qua RAG-Anything

```python
from raganything import RAGAnything

# RAG-Anything parse multimodal → đẩy vào LightRAG
rag_anything = RAGAnything(lightrag_instance=rag)

await rag_anything.process_file(
    file_path="document.pdf",
    file_type="pdf"
)
# Internally: parse → extract entities → build graph → dual-index
```

### 3.4 Giới Hạn Cần Biết

- LightRAG dùng **internal graph schema** riêng khi lưu vào Neo4j — không hoàn toàn tự do define schema như Neo4j thuần.
- Muốn custom Cypher queries phức tạp, cần wrap LightRAG graph storage và query trực tiếp vào Neo4j qua `neo4j` Python driver.
- RAG-Anything **chưa expose API** để inject custom Neo4j queries — đây là phần phải implement thêm.

---

## 4. CRAG — Phải Implement Riêng

CRAG (Corrective RAG) là module **không có sẵn** trong RAG-Anything hay LightRAG. Cần xây dựng như một standalone middleware.

### 4.1 Kiến Trúc CRAG Module

```
Retrieved chunks (từ LightRAG)
         ↓
┌────────────────────────────┐
│  Step 1: Relevance Scorer  │  LLM-as-judge: score 0.0–1.0 mỗi chunk
│  threshold: 0.5            │
└─────────────┬──────────────┘
              ↓
    ┌─────────┴──────────┐
    │                    │
  HIGH               LOW / AMBIGUOUS
(score ≥ 0.5)       (score < 0.5)
    │                    │
    ↓                    ↓
Proceed           Web search fallback
                  + Knowledge refinement
              ↓
┌────────────────────────────┐
│  Step 2: Consistency Check │  Cross-check giữa các chunks
│  NLI model hoặc LLM-judge  │  Phát hiện contradictions
└─────────────┬──────────────┘
              ↓
    ┌─────────┴──────────┐
    │                    │
CONSISTENT          CONFLICT FOUND
    │                    │
    ↓                    ↓
Final context    Resolution strategy:
                 (a) Source authority ranking
                 (b) Re-retrieve với refined query
                 (c) Present both views + flag
```

### 4.2 Implementation CRAG

```python
from dataclasses import dataclass
from typing import List, Tuple
from enum import Enum

class RelevanceLevel(Enum):
    HIGH = "high"        # score >= 0.8
    MEDIUM = "medium"    # 0.5 <= score < 0.8
    LOW = "low"          # score < 0.5

@dataclass
class CRAGResult:
    verified_chunks: List[str]
    confidence_score: float
    has_conflict: bool
    conflict_description: str | None
    triggered_web_search: bool
    reasoning: str

class CRAGModule:
    def __init__(self, llm_client, web_search_fn=None, threshold=0.5):
        self.llm = llm_client
        self.web_search = web_search_fn
        self.threshold = threshold

    async def evaluate(
        self,
        query: str,
        retrieved_chunks: List[str]
    ) -> CRAGResult:
        # Step 1: Score relevance của từng chunk
        scores = await self._score_relevance(query, retrieved_chunks)

        high_chunks = [c for c, s in zip(retrieved_chunks, scores) if s >= self.threshold]
        low_chunks  = [c for c, s in zip(retrieved_chunks, scores) if s < self.threshold]

        # Step 2: Fallback nếu không đủ high-quality chunks
        web_triggered = False
        if len(high_chunks) < 2 and self.web_search:
            web_results = await self.web_search(query)
            high_chunks.extend(web_results)
            web_triggered = True

        # Step 3: Consistency check
        conflict, conflict_desc = await self._check_consistency(query, high_chunks)

        # Step 4: Resolution nếu có conflict
        if conflict:
            high_chunks = await self._resolve_conflict(query, high_chunks)

        overall_score = sum(scores) / len(scores) if scores else 0.0

        return CRAGResult(
            verified_chunks=high_chunks,
            confidence_score=overall_score,
            has_conflict=conflict,
            conflict_description=conflict_desc,
            triggered_web_search=web_triggered,
            reasoning=f"Evaluated {len(retrieved_chunks)} chunks, kept {len(high_chunks)}"
        )

    async def _score_relevance(self, query: str, chunks: List[str]) -> List[float]:
        prompt = f"""Score each chunk's relevance to the query (0.0 to 1.0).
Query: {query}
Return JSON array of scores only, e.g. [0.9, 0.3, 0.7]

Chunks:
{chr(10).join(f'[{i}] {c[:300]}' for i, c in enumerate(chunks))}"""
        response = await self.llm.complete(prompt)
        import json
        return json.loads(response)

    async def _check_consistency(
        self, query: str, chunks: List[str]
    ) -> Tuple[bool, str | None]:
        if len(chunks) < 2:
            return False, None
        prompt = f"""Do any of these chunks contradict each other regarding: "{query}"?
Answer JSON: {{"conflict": true/false, "description": "..." or null}}

Chunks:
{chr(10).join(f'[{i}] {c[:200]}' for i, c in enumerate(chunks))}"""
        response = await self.llm.complete(prompt)
        import json
        result = json.loads(response)
        return result["conflict"], result.get("description")

    async def _resolve_conflict(self, query: str, chunks: List[str]) -> List[str]:
        # Dùng LLM để rank chunks theo authority và recency
        prompt = f"""Rank these chunks by reliability for answering: "{query}"
Return indices of top chunks only (most reliable first), as JSON array.

{chr(10).join(f'[{i}] {c[:200]}' for i, c in enumerate(chunks))}"""
        response = await self.llm.complete(prompt)
        import json
        top_indices = json.loads(response)
        return [chunks[i] for i in top_indices[:3]]
```

### 4.3 CRAG Confidence Thresholds

| Mức độ | Score | Hành động |
|---|---|---|
| HIGH | ≥ 0.85 | Proceed to generation |
| MEDIUM | 0.60 – 0.84 | Expand retrieval loop (+1 iteration) |
| LOW | < 0.60 | Re-retrieve + web search fallback |

---

## 5. Agentic Orchestrator & System Prompt

### 5.1 Chu Trình 5 Bước

| Bước | Hành động | Output |
|---|---|---|
| **1. Plan** | Phân tích intent, decompose query, xác định loại câu hỏi | Query plan + sub-questions |
| **2. Route** | Classify truy vấn, chọn tool tối ưu | Routing decision: cypher / bm25 / vector |
| **3. Act** | Gọi LightRAG retrieval (local/global/hybrid), thực hiện traversal | Raw context chunks |
| **4. Verify** | Chạy CRAG module, score confidence | Verified context hoặc re-retrieve signal |
| **5. Stop** | Đánh giá độ đủ, quyết định dừng hoặc loop | Final context / expand loop |

### 5.2 System Prompt Đầy Đủ

```
SYSTEM PROMPT — Agentic RAG Orchestrator v1.1
==============================================

## IDENTITY
You are an autonomous multi-step retrieval agent operating over a Vietnamese
knowledge system backed by a LightRAG knowledge graph (Neo4j storage) and
multimodal document index (RAG-Anything).

Your sole purpose: answer user questions accurately by systematically
planning, retrieving, verifying, and synthesizing information.
You NEVER fabricate. You ALWAYS cite. You ALWAYS flag uncertainty.

---

## AVAILABLE TOOLS

### 1. lightrag_query(query: str, mode: str) → RetrievalResult
  Search the knowledge graph and vector index.
  mode options:
    - "local"  : entity-centric, k-hop graph traversal. Use for specific
                 entities, named relationships, direct facts.
    - "global" : community-level reasoning. Use for aggregate questions,
                 trends, patterns across many entities.
    - "hybrid" : combines local + global (default for complex queries).
    - "naive"  : vector-only, no graph. Use for abstract/conceptual queries.
  Returns: { chunks: List[str], entities: List[dict], relations: List[dict] }

### 2. cypher_query(cypher: str) → List[dict]
  Execute raw Cypher directly on Neo4j (via LightRAG storage layer).
  Use when lightrag_query returns insufficient relational detail.
  Example: MATCH (p:Person)-[:WORKS_AT]->(c:Company) RETURN p.name, c.name
  Returns: list of result rows as dicts.

### 3. bm25_search(query: str, top_k: int = 10) → List[Document]
  Keyword-based sparse retrieval.
  Use for: exact term matching, specific document names, static facts.
  Returns: { text, source, score }

### 4. crag_verify(query: str, chunks: List[str]) → CRAGResult
  Evaluate relevance and consistency of retrieved chunks.
  MUST be called after every retrieval before generating answer.
  Returns: { verified_chunks, confidence_score, has_conflict, reasoning }

### 5. web_search(query: str) → List[str]
  Search the web for supplementary information.
  Use ONLY when: crag_verify returns confidence < 0.6 AND internal
  knowledge is insufficient or conflicting.

---

## REASONING PROTOCOL (ReAct)

For every user question, follow this exact cycle:

```
THOUGHT: [Analyze the question. What type is it? What do I need to find?
          Are there multiple sub-questions? Which tool fits best?]

ACTION: [tool_name(params)]

OBSERVATION: [What did the tool return? Is it relevant? Sufficient?]

THOUGHT: [Do I have enough? Any conflicts? Should I verify? Loop again?]

ACTION: [crag_verify(...) or next tool or STOP]

... repeat up to MAX_LOOPS times ...

FINAL_ANSWER: [Synthesized answer with citations]
```

---

## CYCLE CONTROL

MAX_LOOPS: 5
STOP condition: crag_verify returns confidence_score >= 0.85
EXPAND condition: confidence_score < 0.85 → refine query, try different mode
ABORT condition: after 5 loops, generate best-effort answer with uncertainty flags

### Routing Logic:
- Entity + relationship questions → lightrag_query(mode="local") first
- Aggregate / trend questions → lightrag_query(mode="global")
- Abstract / conceptual → lightrag_query(mode="naive")
- Exact keyword / document name → bm25_search()
- Complex multi-hop → lightrag_query(mode="hybrid") + cypher_query()
- Insufficient internal context → web_search() as last resort

---

## STEP-BACK PROTOCOL

For complex or ambiguous questions, BEFORE routing, apply step-back:

1. Ask yourself: "What is the broader principle or context behind this question?"
2. Retrieve that broader context first (1 lightrag_query call).
3. Then retrieve the specific answer using that context as a frame.

Example:
  User: "Tại sao doanh thu Q3 của công ty X giảm?"
  Step-back: "Các yếu tố thường ảnh hưởng đến doanh thu trong ngành Y là gì?"
  → Retrieve macro context first, then drill into company X specifics.

---

## OUTPUT FORMAT

Always return a structured JSON response:

```json
{
  "reasoning_chain": [
    { "step": 1, "thought": "...", "action": "...", "observation": "..." }
  ],
  "retrieved_facts": [
    { "fact": "...", "source": "...", "confidence": 0.0-1.0 }
  ],
  "has_uncertainty": true/false,
  "uncertainty_notes": "...",
  "final_answer": "...",
  "sources": ["source1", "source2"]
}
```

---

## SAFETY CONSTRAINTS

- NEVER generate information not grounded in retrieved context.
- NEVER omit source attribution for any factual claim.
- Mark uncertain claims with [UNCERTAIN: reason].
- If two sources conflict and cannot be resolved, present both views explicitly.
- If MAX_LOOPS reached without sufficient context, state clearly:
  "Thông tin hiện có chưa đủ để trả lời chắc chắn. Dưới đây là những gì tìm được..."
```

---

## 6. Step-back Prompting & Query Decomposition

### 6.1 Step-back Prompting

Step-back prompting là kỹ thuật yêu cầu LLM **lùi một bước** để truy xuất nguyên lý tổng quát trước khi đi vào chi tiết, cải thiện đáng kể chất lượng suy luận trên câu hỏi phức tạp.

**Workflow:**

```
User query (specific)
        ↓
┌──────────────────────────────────┐
│  Step-back LLM call              │
│  "What is the broader principle  │
│   or domain behind this query?"  │
└─────────────────┬────────────────┘
                  ↓
       Abstract context retrieval
                  ↓
┌──────────────────────────────────┐
│  Original query + abstract       │
│  context → specific retrieval    │
└──────────────────────────────────┘
```

**Ví dụ:**

```
Original: "Năm 2023 BIDV cho vay bao nhiêu tỷ cho lĩnh vực bất động sản?"

Step-back: "Cơ cấu danh mục cho vay của các ngân hàng thương mại Việt Nam
            thường được phân bổ theo những lĩnh vực nào?"

→ LLM có context về ngành → retrieval chính xác hơn
```

### 6.2 Query Decomposition

Câu hỏi phức tạp được phân rã thành sub-questions độc lập:

```python
DECOMPOSITION_PROMPT = """
Phân tích câu hỏi sau và tách thành các sub-questions độc lập.
Mỗi sub-question phải có thể trả lời riêng lẻ.
Trả về JSON array.

Câu hỏi: {query}

Format:
[
  { "sub_question": "...", "retrieval_hint": "local|global|naive|bm25" },
  ...
]
"""
```

---

## 7. Local Traversal & Suy Luận Đa Bước

### 7.1 LightRAG Local Traversal

Khi gọi `lightrag_query(mode="local")`, LightRAG thực hiện:

```
1. Named Entity Recognition trên query
        ↓
2. Tìm anchor nodes trong Neo4j khớp với entities
        ↓
3. K-hop expansion (mặc định k=3)
   MATCH (anchor)-[*1..3]-(neighbor) RETURN neighbor
        ↓
4. Subgraph extraction — nodes + edges trong phạm vi k-hop
        ↓
5. Relevance pruning — loại bỏ nodes thấp liên quan
        ↓
6. Serialization → text context cho LLM
```

### 7.2 Custom Cypher cho Multi-hop Phức Tạp

Khi LightRAG local retrieval chưa đủ, dùng `cypher_query()` để viết Cypher tay:

```cypher
-- Tìm chuỗi quan hệ dài (multi-hop path)
MATCH path = (a:Entity {name: $anchor})
             -[*1..4]-
             (target:Entity)
WHERE target.type IN ['Organization', 'Person']
RETURN nodes(path) AS chain,
       relationships(path) AS links,
       length(path) AS depth
ORDER BY depth ASC
LIMIT 20

-- Tìm entities cùng community
MATCH (anchor:Entity {name: $anchor})<-[:IN_COMMUNITY]-(comm:Community)
MATCH (comm)-[:IN_COMMUNITY]->(related:Entity)
WHERE related.name <> $anchor
RETURN related.name, related.type, comm.title
LIMIT 30
```

### 7.3 Chiến Lược Traversal Theo Loại Truy Vấn

| Loại truy vấn | LightRAG mode | Cypher fallback | Depth |
|---|---|---|---|
| Entity lookup đơn giản | `local` | Không cần | k=1 |
| Chuỗi quan hệ | `local` | Path query | k=2–3 |
| Tổng hợp cộng đồng | `global` | Community query | Full |
| Khái niệm trừu tượng | `naive` | Không áp dụng | — |
| Multi-hop phức tạp | `hybrid` | Custom Cypher | k=4+ |

---

## 8. Schema Neo4j

LightRAG tạo schema sau trong Neo4j khi lưu trữ:

### 8.1 Node Labels

```
(:__Entity__)          # Tất cả entities (LightRAG default label)
  - id: string (unique)
  - entity_type: string  ["Person", "Organization", "Concept", "Location", ...]
  - description: string
  - source_id: string    # trỏ về chunk nguồn

(:__Community__)       # Community clusters (Louvain algorithm)
  - id: string
  - title: string
  - summary: string
  - level: int           # hierarchy level

(:__Chunk__)           # Document chunks
  - id: string
  - content: string
  - tokens: int
  - source: string
```

### 8.2 Relationship Types

```
(:__Entity__)-[:RELATED {
  weight: float,
  description: string,
  keywords: string,
  source_id: string
}]->(:__Entity__)

(:__Entity__)-[:IN_COMMUNITY]->(:__Community__)
(:__Chunk__)-[:MENTIONS]->(:__Entity__)
```

### 8.3 Custom Schema Extension (nếu cần)

Nếu muốn extend schema LightRAG với labels rõ ràng hơn:

```python
# Sau khi LightRAG insert, chạy Cypher migration:
"""
MATCH (e:__Entity__ {entity_type: 'Person'})
SET e:Person
RETURN count(e)
"""

"""
MATCH (e:__Entity__ {entity_type: 'Organization'})
SET e:Organization
RETURN count(e)
"""
```

### 8.4 Indexes Cần Tạo

```cypher
-- Full-text index cho BM25-style search
CREATE FULLTEXT INDEX entityDescriptions
FOR (e:__Entity__) ON EACH [e.description, e.id]

-- Vector index (nếu dùng Neo4j vector search)
CREATE VECTOR INDEX entityEmbeddings
FOR (e:__Entity__) ON (e.embedding)
OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } }

-- Composite index cho traversal
CREATE INDEX entityTypeId FOR (e:__Entity__) ON (e.entity_type, e.id)
```

---

## 9. Stack Công Nghệ & Cấu Hình

### 9.1 Stack Đầy Đủ

| Component | Technology | Version | Vai trò |
|---|---|---|---|
| **Multimodal Ingestion** | RAG-Anything | Latest | Parse PDF/DOCX/Image/Table/Formula |
| **Graph + Retrieval Engine** | LightRAG | Latest | Dual-level graph RAG, entity extraction |
| **Graph Storage** | Neo4j Enterprise | 5.x | Lưu entity graph, community clusters |
| **LLM — Orchestrator** | GPT-4o / Claude Sonnet 4.5 | Latest | Planning, routing, generation |
| **LLM — CRAG Evaluator** | GPT-4o-mini / Claude Haiku | Latest | Relevance scoring (cost-efficient) |
| **Embedding** | bge-m3 / text-embedding-3-large | Latest | Multilingual, Vietnamese support |
| **BM25 Engine** | Elasticsearch | 8.x | Sparse keyword index |
| **Cache** | Redis Cluster | 7.x | Query cache, TTL-based |
| **Agent Framework** | LangGraph | Latest | Agentic loop, state management |
| **API Layer** | FastAPI + WebSocket | 0.110+ | REST endpoints, streaming |
| **Observability** | Langfuse | Latest | Trace, eval, token tracking |

### 9.2 Cấu Hình Quan Trọng

```yaml
# config.yaml

lightrag:
  working_dir: "./rag_storage"
  graph_storage: "Neo4JStorage"
  embedding_model: "BAAI/bge-m3"
  llm_model: "gpt-4o"
  chunk_size: 1200          # tokens
  chunk_overlap: 100

neo4j:
  uri: "bolt://localhost:7687"
  database: "knowledge"

crag:
  relevance_threshold: 0.50     # loại chunk dưới ngưỡng này
  confidence_stop: 0.85         # dừng loop nếu đạt ngưỡng
  enable_web_fallback: true

orchestrator:
  max_loops: 5
  default_retrieval_mode: "hybrid"
  top_k_per_engine: 10
  enable_step_back: true        # bật step-back prompting
  enable_decomposition: true    # bật query decomposition

cache:
  query_ttl: 3600               # seconds
  result_ttl: 86400
```

---

## 10. Hiệu Năng & SLA

| Chỉ số | Target | Ghi chú |
|---|---|---|
| Latency P50 (simple query) | < 2s | Single retrieval, no loop |
| Latency P95 (complex multi-hop) | < 8s | Tối đa 3 retrieval loops |
| Throughput | > 50 QPS | Với horizontal scaling |
| CRAG Precision | > 92% | Tỷ lệ phát hiện đúng conflict |
| Answer Accuracy | > 88% | Đánh giá trên benchmark |
| LightRAG local query | < 300ms | k-hop traversal trên Neo4j |
| Vector search | < 50ms | ANN search |
| Cache hit rate | > 40% | Redis layer |
| Ingestion throughput | > 100 pages/min | RAG-Anything parallel |

---

## 11. Rủi Ro & Giảm Thiểu

| Rủi ro | Mức độ | Biện pháp |
|---|---|---|
| **LightRAG schema lock-in** | Cao | Document schema, viết migration scripts, test custom Cypher trước |
| Infinite retrieval loop | Cao | `MAX_LOOPS=5`, timeout per loop, circuit breaker |
| CRAG false positive conflict | Trung bình | Tune threshold, human feedback loop, A/B test |
| Neo4j query performance | Trung bình | Index on `entity_type + id`, query plan review, `EXPLAIN` |
| Knowledge Graph staleness | Trung bình | Incremental update pipeline, version tracking trên chunks |
| LLM hallucination bypass | Cao | CRAG mandatory trước generation, source citation enforced |
| Embedding model drift | Thấp | Re-embed on model update, version embedding model |
| RAG-Anything parser lỗi | Trung bình | Fallback parser (PyMuPDF), monitor parse error rate |

---

## 12. Lộ Trình Triển Khai

| Giai đoạn | Thời gian | Nội dung | Deliverable |
|---|---|---|---|
| **Phase 1 — Foundation** | Tuần 1–2 | Setup LightRAG + Neo4j, test schema, ingest domain data nhỏ | Graph DB populated, schema validated |
| **Phase 2 — RAG Core** | Tuần 3–4 | RAG-Anything ingestion pipeline, dual-index (graph + vector), BM25 | Working end-to-end retrieval |
| **Phase 3 — CRAG Module** | Tuần 5–6 | Implement CRAG middleware, relevance evaluator, web fallback | Verified retrieval quality |
| **Phase 4 — Agentic Loop** | Tuần 7–8 | Orchestrator + system prompt, LangGraph agent loop, routing logic | Full 5-step autonomous cycle |
| **Phase 5 — Step-back & Decompose** | Tuần 9** | Step-back prompting, query decomposition, sub-question aggregation | Complex query handling |
| **Phase 6 — Optimization** | Tuần 10–12 | Redis cache, Cypher index tuning, load testing, Langfuse observability | Production-ready |
| **Phase 7 — Go-live** | Tuần 13–14 | Staging, UAT, bug fixes, cutover | Live in production |

---

## Phụ Lục — Tóm Tắt Quan Hệ Giữa Các Component

```
RAG-Anything
  └── Chức năng: Parse multimodal documents
  └── Delegate tới: LightRAG (toàn bộ graph + retrieval)
  └── KHÔNG có: CRAG, Agentic loop, Neo4j API trực tiếp

LightRAG
  └── Chức năng: Graph construction + dual-level retrieval
  └── Storage backend: Neo4j (cấu hình qua env vars)
  └── Retrieval modes: local / global / hybrid / naive
  └── KHÔNG có: CRAG, Corrective mechanism, Agentic loop

CRAG Module
  └── Chức năng: Post-retrieval quality evaluation
  └── Input: chunks từ LightRAG
  └── PHẢI implement riêng (không có trong RAG-Anything/LightRAG)
  └── Tools: LLM-as-judge, web search fallback

Agentic Orchestrator (LangGraph)
  └── Chức năng: Plan → Route → Act → Verify → Stop
  └── Gọi: LightRAG, cypher_query, bm25_search, CRAG, web_search
  └── Điều khiển bởi: System Prompt (ReAct format)
```

---

*Hết tài liệu — v1.1 Revised*
