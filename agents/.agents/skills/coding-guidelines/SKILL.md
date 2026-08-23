---
name: coding-guidelines
description: Shared programming guidelines for modifying source code, tests, or configuration files, including language-specific rules for Rust, Python, and YAML.
---

# Coding Guidelines

Before modifying a file of a covered type, read its matching reference completely. Read each reference at most once per task.

- Rust source (`.rs`) — [references/rust.md](references/rust.md)
- Python source (`.py`) — [references/python.md](references/python.md)
- YAML documents (`.yaml`, `.yml`) — [references/yaml.md](references/yaml.md)

Apply the common guidelines below and every applicable language-specific guideline throughout the task.

Apply guidelines to the work being changed. Do not make unrelated changes solely to bring existing code into compliance.

Before completion, review all changed files against the applicable guidelines.

## Comments

- Preserve existing comments unless the code they describe is removed or the comment is clearly outdated or incorrect. A comment that seems unnecessary may encode a hidden constraint or a lesson from a past bug that is not obvious from the current code.
- Add comments sparingly. Prefer clear names and code structure over explanatory comments. Comment only when the rationale is non-obvious, such as a hidden constraint, subtle invariant, bug workaround, or surprising behavior.
- Keep comments concise and avoid restating what the code already makes clear.

## Defensive Programming

- Do not add fallback behavior, speculative defaults, compatibility paths, or recovery logic for cases outside the specified contract.
- Validate untrusted or external data at trust boundaries. Once validated, rely on established types and invariants internally instead of repeating the same checks throughout the call chain.
- Distinguish expected runtime failures from programmer errors and invariant violations: handle expected failures normally, but surface bugs explicitly rather than masking them with defaults, fallbacks, or silent recovery.
