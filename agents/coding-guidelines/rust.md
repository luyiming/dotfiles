## Rust Coding Guidelines

### General Guidelines

- Avoid adding new `super::` imports except in inline `mod` blocks (e.g. `mod tests { ... }`) — prefer `crate::`-rooted paths. This makes imports consistent and easier to grep for.
- Use `<module>.rs` file layout instead of `<module>/mod.rs`.
  - For example, use `src/foo.rs` with `src/foo/bar.rs`, not `src/foo/mod.rs`.
- Prefer self-documenting APIs over ambiguous positional arguments such as `foo(false)` or `bar(None)`. Use enums, named methods, newtypes, or other idiomatic API shapes when the argument's meaning is not clear at the call site.
- Add doc comments to new traits that explain their purpose, intended usage, and implementation contract.
- For async trait methods, prefer native RPITIT with an explicit future contract over `#[async_trait]` or `#[allow(async_fn_in_trait)]`.
  - Example: `fn foo(&self, ...) -> impl Future<Output = T> + Send;`
  - Implementations may use `async fn` when they satisfy that contract.
- In tests, prefer whole-value equality assertions over field-by-field assertions when the entire value is expected to match.
- Do not add tests that merely restate statically defined constants or data without exercising behavior or an invariant.
- Prefer `#[tracing::instrument(...)]` when a span belongs to the callee itself; use `.instrument(...)` for caller-owned invocation or task context.
  - Avoid duplicate instrumentation of the same logical operation.
- Keep modules focused and reasonably sized:
  - Aim for Rust modules under ~500 LoC, excluding tests; treat this as a soft target rather than a hard limit.
  - Once a module approaches ~800 LoC, look for cohesive responsibilities that can be moved into a new module before adding substantial new functionality.
  - When extracting code, move closely related tests and documentation with it so invariants remain near their implementation.

### Errors, Logging, and Panics

#### Error and Log Message Style

- Start with lowercase.
- No trailing punctuation.
- Keep messages concise and descriptive; state what happened or what was invalid rather than using generic labels.
- Do not include severity prefixes such as `error:` or `INFO`.

#### Errors

- Include relevant context such as paths, fields, IDs, or expected and actual values when useful.
- Preserve the underlying error through error chaining (for example `#[source]`, `#[from]`, or `anyhow::Context`) rather than duplicating its message.

Examples:

- `failed to read "{path}"`
- `invalid value for "timeout": expected > 0, got 0`
- `missing required field "host"`

#### Logging (`tracing`)

- Keep event messages short and stable.
- Use spans to carry context across an operation, and events to record what happens within that context.
- Use `#[instrument]` when a function benefits from carrying the context. Use `skip(...)` / `skip_all` for large, sensitive, or noisy arguments, and `fields(...)` for explicit contextual fields.
- Prefer structured fields over string interpolation.
- Record values directly when supported; use `%` for concise, human-readable `Display` output and `?` for `Debug` output when additional diagnostic detail is useful.
- Avoid multiline logs and repetitive `info` events in tight loops.
- Do not log secrets, credentials, tokens, or sensitive payloads.
- Log errors where they are handled or suppressed; do not log an error and then return it unchanged.

Examples:

- `info!(port, "server started");`
- `info!(%method, %path, status = status.as_u16(), ?latency, "request completed");`
- `error!(path = %path.display(), error = %err, "failed to parse config");`
- `debug!(?response, "received unexpected response");`

#### Panics

- Panic only for bugs, violated invariants, or failed assumptions in tests; return `Result` for expected runtime failures such as I/O, network errors, invalid user input, or external API failures.
- When a panic is intentional, prefer `expect` over `unwrap`, with a message stating why the operation should succeed.

Examples:

- `.expect("config file should exist after initialization")`
- `.expect("channel should remain open while the worker is running")`
