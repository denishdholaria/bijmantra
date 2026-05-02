---
name: brapi-contract-review
description: 'Review BijMantra BrAPI contracts for response envelope shape, metadata and pagination consistency, *DbId field naming, router mounting, auth expectations, and test coverage. Use when editing BrAPI endpoints or auditing interoperability drift.'
argument-hint: 'BrAPI scope, endpoint group, or diff to review'
---

# BrAPI Contract Review

## When To Use

- A change touches BrAPI endpoints or BrAPI-adjacent schemas.
- You need to audit interoperability drift or response-envelope consistency.
- You want a standards-focused review before merging BrAPI work.

## Procedure

1. Limit the scope to BrAPI-owned files unless evidence shows a shared dependency is unavoidable.
2. Inspect router mounting, canonical BrAPI schema types, representative endpoint implementations, and BrAPI-focused tests.
3. Check for consistent `metadata` and `result` envelopes, pagination fields, and BrAPI-style `*DbId` names.
4. Distinguish official BrAPI endpoints from BijMantra extensions or convenience routes.
5. Add or update focused tests for any contract behavior that changes.

## Guardrails

- Prefer canonical shared BrAPI schemas over raw dictionary envelopes.
- Keep review findings grounded in repo evidence, not in a generic BrAPI summary.
- Do not widen the change into unrelated AI or product APIs unless there is a strict dependency.

## References

- [repo anchors](./references/repo-anchors.md)
