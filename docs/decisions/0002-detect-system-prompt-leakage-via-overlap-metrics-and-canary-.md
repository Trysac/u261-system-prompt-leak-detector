# Detect system prompt leakage via overlap metrics and canary tokens

Status: accepted (generated, pending human review)

## Context

LLM applications often protect system prompts containing business logic, tone rules, and instructions. These prompts leak when users ask the model to repeat them, often reformatted or base64 encoded. Teams need a lightweight, deterministic detector that can run in a gateway without network calls or an LLM.

## Decision

Implement a detector that compares outputs against the protected prompt using word n-gram overlap (after NFKC and casefold normalization), scans for a caller-provided canary token, and decodes base64 spans that may contain encoded copies. Return a score and a set of signals ('verbatim', 'canary', 'encoded') and provide an optional event callback that receives only metadata, never the prompt or output text.

## Consequences

The detector is transparent, fast, and safe to use in log pipelines because it avoids passing sensitive text to callbacks. It cannot detect paraphrases, translations, leaks shorter than the ngram size, or leaks split across responses, which are documented as limitations. The API is simple and extensible, but adding new detection heuristics will require extending the signal set and scoring logic.
