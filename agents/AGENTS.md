# Natural Language Guidelines

## Scope and Precedence

- Language instructions apply only to the content they refer to. For example, requesting a particular language for a document or code comments does not change the conversational language or the language of unrelated artifacts.
- An explicit language instruction for specific content overrides the corresponding defaults below.

## Chat Responses

- Use the language in which the user's current request is primarily expressed for chat prose, including questions, plans, updates, explanations, warnings, and final responses.
- Infer that language from the user's own prose, not from embedded code, quotations, logs, error messages, or file contents.
- If the request mixes languages, use the language carrying the main intent. If the request is too short or ambiguous to determine this, continue in the established conversational language.

## Deliverables and Repository Content

- For standalone deliverables such as reports, analyses, research documents, and summaries, use the language explicitly requested or clearly implied by the intended audience. Otherwise, use the conversational language.
- For repository text, such as documentation, code comments, commit messages, developer-facing logs and diagnostics, assertion messages, and internal errors, follow the language of nearby existing text in the target file or its immediate context. If there is no clear local convention, use English by default. Do not search the broader repository solely to determine the language convention.
- For end-user-facing product text, such as UI or CLI copy and user-visible messages, follow explicit task, product, or locale requirements. Otherwise, follow nearby existing product text; if no convention is available, use English.
- When editing existing text, preserve its language unless translation is part of the task.

## Literal and Technical Content

- Preserve code, identifiers, commands, paths, API names, exact error messages, log excerpts, and quoted source text in their original form unless changing them is part of the task.
- Prefer established domain terminology when translation would reduce precision or clarity. Include the original term in parentheses when needed to avoid ambiguity.

# Programming Guidelines

Before modifying source code, tests, or configuration, use the `coding-guidelines` skill.
