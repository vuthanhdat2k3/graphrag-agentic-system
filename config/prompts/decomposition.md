# Query decomposition

Before routing:

1. List atomic sub-questions that must all be answered for a complete response.
2. Order them by dependency (facts before comparisons; entities before aggregates).
3. For each sub-question, pre-select a likely tool family:
   - entity/relationship → `lightrag_query(local)` or `cypher_query`
   - aggregate/trend → `lightrag_query(global)` or `hybrid`
   - wording/doctitle match → `bm25_search`
4. Merge observations only after `crag_verify` on combined chunks.
