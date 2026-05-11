# Step-back protocol

For ambiguous or multi-causal questions:

1. Infer the broader principle, domain context, or precedent behind the user question.
2. Run **one** `lightrag_query` with that broader frame (prefer `hybrid` or `global` if macro).
3. Re-issue a **specific** retrieval with the original entities/constraints, informed by that frame.

Example: revenue drop for company X → first retrieve industry/macro drivers, then entity-specific facts.
