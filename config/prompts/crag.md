# CRAG judge prompts (short form)

## Relevance

Score each chunk 0.0–1.0 for usefulness to answer the user query. Return JSON array only.

## Consistency

Given chunks, report whether any contradict each other relative to the query. Return JSON:
`{"conflict": bool, "description": string | null}`.

## Authority ranking (on conflict)

Rank chunk indices by trustworthiness for this query (recency, primary source). Return JSON array of indices.
