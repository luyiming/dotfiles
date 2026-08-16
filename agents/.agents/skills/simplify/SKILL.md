---
name: simplify
description: Review code for simplification opportunities across reuse, quality, and efficiency, then rank findings without modifying code.
disable-model-invocation: true
---

# Simplify: Code Review

Review code for opportunities to reduce duplication, complexity, and unnecessary work. Report prioritized findings; do not modify code unless the user explicitly asks for changes.

## Phase 1: Determine Review Scope

Determine the review target in the following order:

1. **Use the user-specified scope if provided.**
   - This may be a code snippet, file, directory, module, package, commit, commit range, or other explicitly named scope.
   - For file/module/package scopes, review the current implementation of the specified scope.
   - For commit or diff scopes, focus findings on code introduced or changed by that range.

2. **Otherwise, review uncommitted changes.**
   - Run `git status --short` to identify changed and untracked files.
   - Use `git diff HEAD` to inspect tracked changes.
   - Include relevant untracked files in the review.

3. **If there are no uncommitted changes, report that there is nothing to review and ask the user to specify a scope.**

Agents may inspect surrounding code or the wider codebase for context, but findings must remain within the review target.

## Phase 2: Launch Three Review Agents in Parallel

Launch three sub-agents concurrently. Give each agent the complete review target and allow it to inspect the wider codebase for context.

Each agent should report only concrete simplification opportunities within the review target. Prefer meaningful improvements over stylistic nits or speculative refactors.

### Agent 1: Code Reuse Review

For each change or relevant implementation:

1. **Search for existing utilities and helpers** that could replace newly written code. Look for similar patterns elsewhere in the codebase — common locations are utility directories, shared modules, and files adjacent to the reviewed code. Prefer an existing utility only when its semantics and abstraction level genuinely match; do not force reuse merely because the implementations look similar.
2. **Flag new functions that duplicate existing functionality.** Identify the existing function or abstraction that should be used instead.
3. **Flag inline logic that could use an existing utility** — hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards, and similar patterns are common candidates.
4. **Flag newly introduced abstractions that duplicate an existing abstraction** even if their implementations differ slightly.

### Agent 2: Code Quality Review

Review the same target for unnecessary complexity and weak abstractions:

1. **Redundant state**: state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls
2. **Parameter sprawl**: functions accumulating loosely related parameters, repeated parameter groups, or flags that indicate the abstraction should be reconsidered
3. **Copy-paste with slight variation**: near-duplicate code blocks that should be unified with a shared abstraction
4. **Leaky abstractions**: exposing internal details that should be encapsulated, or breaking existing abstraction boundaries
5. **Weak domain representation**: raw strings or primitives used where an existing domain type already represents the concept, or where repeated misuse shows that a small domain type would materially simplify the code
6. **Unnecessary or speculative abstraction**: wrappers, helpers, extension points, parameters, or generalization that add indirection without serving a concrete current need
7. **Overly complex control flow**: deeply nested branches, duplicated conditions, or multi-step logic that can be expressed more directly
8. **Repeated branching on the same concept**: repeated `match`/`switch`/`if` cascades over the same enum, tag, or mode that duplicate knowledge across locations; consider centralizing the decision or moving behavior closer to the concept when that makes the code simpler

Do not recommend introducing an abstraction merely to eliminate superficial duplication; the resulting code should be simpler than what it replaces.

### Agent 3: Efficiency Review

Review the same target for unnecessary work:

1. **Redundant computations**: repeated calculations or transformations whose results could be reused
2. **Repeated I/O**: duplicate file reads, network/API calls, database queries, or N+1 patterns
3. **Missed concurrency**: independent operations run sequentially when they could safely run in parallel
4. **Hot-path bloat**: blocking or unnecessary work added to startup or per-request/per-render/per-item hot paths
5. **Redundant pre-checks**: check-then-act existence checks where the operation itself can determine success or failure
6. **Memory and lifecycle issues**: unbounded data structures, unnecessary copies, missing cleanup, or listener/resource leaks
7. **Overly broad operations**: reading entire files when only a portion is needed, loading all items when only a subset is required, or performing work before it is known to be necessary

## Phase 3: Validate and Rank Findings

Wait for all three agents to complete, then aggregate their findings.

Before reporting:

- Merge duplicate or overlapping findings.
- Verify each finding against the actual code and surrounding context.
- Discard false positives, speculative suggestions, and changes whose complexity outweighs their benefit.
- Prefer a small number of meaningful simplifications over an exhaustive list of minor cleanups.

Rank the remaining findings by expected value:

- **High**: clear simplification, removes meaningful duplication or complexity, or fixes significant unnecessary work with low behavioral risk
- **Medium**: worthwhile simplification with a smaller benefit or a somewhat broader change
- **Low**: minor cleanup that is correct but optional

Within the same priority, prefer findings with higher confidence and lower implementation risk.

For each finding, report:

- priority
- location
- what is unnecessarily complex, duplicated, or inefficient
- the suggested simplification
- why the change is worthwhile
- any meaningful implementation risk or tradeoff

## Phase 4: Report Only

Present the prioritized findings and stop.

Do not modify code as part of the review unless the user explicitly requested changes. The user can then choose which findings to apply.
