---
name: commit-message
description: Generate git commit messages from staged changes and optional user context. Use when asked to generate a commit message.
---

# Task

Generate a git commit message for the currently staged changes only.

The message MUST follow the Conventional Commits 1.0.0 specification and the project-specific conventions defined in this guide.

Inspect staged changes with `git diff --cached` or equivalent mechanisms. You may inspect nearby code, filenames, tests, documentation, and recent commits only to understand the staged changes.

DO NOT include unstaged or untracked changes unless they are explicitly staged.

If no staged changes exist, output exactly: No staged changes found.

Otherwise output ONLY the final commit message.

Do NOT include:
- explanations
- questions
- markdown fences
- comments
- additional surrounding text

You MUST NOT:
- modify files
- stage or unstage changes
- create commits
- amend commits
- rebase
- reset
- rewrite git history

# Source of Truth

The staged diff is the primary source of truth for WHAT changed.

Additional context MAY be provided alongside the staged changes.

This context is supplemental and SHOULD be used to improve the accuracy and quality of the generated commit message.

Additional context MAY:

- Clarify the intent of the change
- Explain WHY the change exists
- Suggest or explicitly specify the commit type
- Suggest or explicitly specify the scope
- Provide architectural or business context
- Describe behavioral or compatibility implications
- Provide issue references or footer metadata

The staged diff remains the primary source of truth for WHAT changed.

Additional context MUST NOT override the actual staged changes.

The generated commit message MUST:

- Accurately reflect the staged changes
- Incorporate relevant additional context when appropriate
- Avoid inventing motivations, metadata, or behavior not supported by either:
    - the staged changes
    - the provided additional context

If additional context conflicts with the staged changes, prioritize the staged changes.

# Commit Message Format Guide (Output Format)

This guide is based on Conventional Commits 1.0.0, with additional project-specific rules and conventions.


The commit message should be structured as follows:

```
<type>[optional scope][optional !]: <subject>

[optional body]

[optional footer(s)]
```

## Header Rules

Format: `<type>[optional scope][optional !]: <subject>`

The header `<subject>` contains a succinct description of the change:

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- NOT end with a period (.)
- Be written in English
- Be concise and specific
- Focus on WHAT changed
- Maximum recommended line length: 100 characters per line

### Type Selection

Use ONE of the following types:

- `fix`: Fixes a bug
- `feat`: Introduces a new feature
- `refactor`: Restructures code without changing external behavior
- `style`: Formatting or whitespace-only changes with no behavioral impact
- `perf`: Improves performance
- `test`: Adding missing tests or correcting existing tests
- `docs`: Documentation only changes
- `revert`: Reverts a previous commit
- `build`: Build system or dependency changes
- `ci`: CI/CD configuration changes
- `chore`: Maintenance or miscellaneous changes that do not fit other types and do not affect runtime behavior

Additional rules:

- Use `refactor` ONLY when behavior is intentionally unchanged
- Do NOT use `style` for UI or visual styling changes

### Scope Selection

Include a scope when:

- The change clearly affects a specific subsystem or component
- The affected area is identifiable from filenames or code structure
- The scope improves clarity
- The scope has been given as part of the additional context

Omit the scope when:

- The change affects many unrelated areas
- No single scope accurately represents the change
- The type and subject are sufficient to understand the change, the scope adds little value

Scopes SHOULD:

- Be short
- Use lowercase
- Use nouns or subsystem names
- Avoid overly generic names like misc or general

Examples:

```
fix(parser): handle trailing commas
feat(api): support batch requests
perf(sim): reduce allocation pressure
```

### Breaking Changes

Breaking changes MAY be indicated in either of the following ways:

1. Using `!` after `<type>[optional scope]` and before `:`

```
feat(api)!: remove legacy authentication flow
```

2. Using a footer

```
feat(api): redesign authentication flow

BREAKING CHANGE: legacy API tokens are no longer supported
```

Use breaking changes ONLY when the staged changes introduce intentional, backward-incompatible behavior or API changes.

## Body Rules

The body is OPTIONAL. Omit the body when the header alone is sufficiently clear.

The body MUST begin one blank line after the header.

The body SHOULD:

- Explain WHY the change exists
- Describe important behavioral changes or implementation context
- Focus on rationale and impact rather than repeating the diff
- Use factual, verifiable information only
- Be written in English

The body MUST NOT:

- Invent motivations or reasoning
- Speculate about intent
- Describe unstaged changes

Use short paragraphs by default. Use bullet points only for multiple parallel items, such as several related changes, dependency updates, or migration notes.

Example:

```
fix(feed): avoid duplicated reconnect attempts

Track active reconnect state to prevent concurrent reconnect loops.

Remove redundant retry scheduling logic that could trigger duplicate
connections under packet loss.
```

Example with bullets:

```
build(deps): update runtime dependencies

- update tokio from 1.44.0 to 1.45.1
- update reqwest from 0.11.27 to 0.12.5
```

Maximum recommended line length: 100 characters per line

## Footer Rules

Footers are OPTIONAL.

Format: `Token: value`

Footers MUST appear after one blank line following the body.

Supported footer tokens:

- `BREAKING CHANGE`: Describes significant changes that are not backward-compatible.
- `Fixes`: Indicates issues resolved by the commit
- `Refs`: References related issues or PRs
- `Reviewed-by`: Credits reviewers
- `Co-authored-by`: Credits additional contributors

Examples:

```
BREAKING CHANGE: The API endpoint `/users` has been removed and replaced with `/members`.
Fixes #123, #125
```

Additional rules:

- Use trailer-style formatting consistently
- Do NOT invent issue numbers, reviewers, or contributors
- Footer values MAY contain spaces
- Multiple footers MAY be included

# Special Cases

## Reverts

Revert commits SHOULD use the `revert` type.

Example:

```
revert: remove websocket retry backoff

Revert commit abc1234 due to reconnect instability.
```

Include the reverted commit hash in the body when available.

## Dependency Updates

For direct dependency updates:

- Mention updated direct dependencies in the body when relevant
- Include old and new versions when clearly available
- DO NOT list transitive-only dependency updates

## Large or Mixed Changes

When staged changes are large:

- Prioritize the most important behavioral or architectural changes
- Group related changes together
- Avoid file-by-file summaries
- Focus on the primary intent of the commit

When multiple areas are affected:

- Prefer a broader shared scope when appropriate
- Otherwise omit the scope entirely

