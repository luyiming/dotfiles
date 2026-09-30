---
name: fix-rust-indexing-lints
description: Use when fixing clippy indexing_slicing or string_slice warnings, or rewriting Rust code to avoid panicking indexing and slicing.
---

## Goal

The goal of these lints is to make code panic-free by construction, not to silence warnings. Treat each warning as a question: "why does this code need an index at all?"

## Non-negotiable rules

- Do **not** replace `x[i]` with `x.get(i).unwrap()` or `.expect(...)`. It fails under the same condition and is usually harder to read.
- Do **not** suppress a warning at module or crate scope merely to make Clippy pass.
- Keep lint fixes focused. If you discover an unrelated bug or semantic issue, fix it separately or report it.

## Decision process

Before rewriting the code, determine what the failing case represents.

### Expected runtime absence

Examples: a dynamic index may be out of range, an optional value may be absent, or input may not contain a delimiter.

Handle it explicitly with APIs such as:

- `get`
- `first` / `last`
- `split_first` / `split_last`
- `split_once`
- `strip_prefix` / `strip_suffix`
- `?`
- `ok_or` / `ok_or_else`
- `let ... else`
- `match`

### Malformed external input

For network data, files, exchange data, protocol bytes, or other external input, prefer returning the function's existing error type rather than panicking.

### Local invariant

If the operation is safe because of a local invariant, first try to make that invariant visible through control flow, iterator structure, slice patterns, or types.

Use a lint expectation only when expressing the invariant structurally would clearly make the code worse.

## Rewrite patterns

### Iterate instead of indexing

Prefer iteration when the index exists only to traverse a collection.

```rust
// before
for i in 1..v.len() {
    if v[i].t < v[i - 1].t {
        return false;
    }
}

// after
v.array_windows().all(|[prev, curr]| prev.t <= curr.t)
```

Use APIs such as `for x in &mut v`, `iter`, `iter_mut`, `zip`, `array_windows`, `chunks_exact`, `enumerate`, `windows`.

### Destructure slices

Prefer slice patterns when the code needs a particular shape rather than arbitrary indexing.

```rust
let [first, rest @ ..] = items else {
    return Err(Error::Empty);
};

let &[a, b, c] = code else {
    return None;
};

let [b':', after @ ..] = input else {
    return Err(Error::BadInput);
};
```

Also consider `first`, `last`, `split_first`, and `split_last`.

### Keep state instead of reading it back

If code writes a value and immediately accesses it again through indexing like `v[i - 1]` or `last().expect(...)`, consider keeping that value in a local variable.

For example, keep a `previous`, `current`, or `pending` value directly and push it only once it is final.

### Use a slice as a cursor

For parsers and byte processing, prefer shrinking the remaining input instead of maintaining an integer cursor when practical.

```rust
let mut rest = input;

let Some(rest) = rest.strip_prefix(b":") else {
    return Err(Error::BadInput);
};
```

Useful operations include slice patterns, `strip_prefix`, `split_first`, `trim_ascii_start`, `split_at_checked`, and other operations that return the remaining slice.

### Use checked access when the index is inherently dynamic

If the index is part of the domain rather than an artifact of the implementation, `get` is often the clearest solution.

```rust
let item = items.get(index).ok_or(Error::BadIndex)?;
```

Handle `None` according to the surrounding API. Do not immediately convert it back into a panic.

For intentional clamping:

```rust
let truncated = body.get(..limit).unwrap_or(body);
```

is reasonable because failure means "use the whole body", not "this can never fail".

### Use fixed-size APIs for fixed-width binary data

When parsing a fixed number of bytes, prefer APIs that express the required width directly instead of indexing several positions manually.

```rust
// before
u32::from_le_bytes(buf[0..4].try_into().unwrap())

// after
let (head, rest) = buf
    .split_first_chunk::<4>()
    .ok_or(Error::Short)?;
let value = u32::from_le_bytes(*head);
```

For whole buffers, fixed-size chunk APIs like `as_chunks::<N>()` can similarly produce `&[[u8; N]]` plus a remainder.

### Borrow multiple elements safely

When two mutable elements must be accessed by dynamic indices, use an API that checks that the accesses are valid and non-overlapping instead of indexing twice.

```rust
let [a, b] = v.get_disjoint_mut([i, j])?;
```

### Use purpose-built APIs

Prefer an API that already expresses the operation over manual index arithmetic.

Examples include:

- `split_once` for delimiter-based parsing
- `read_exact` or buffered I/O APIs instead of manually tracking buffer offsets
- fixed-size chunk APIs for binary formats
- an existing byte-search utility such as `memchr` when it is already appropriate for the project

Do not introduce a new parser framework or dependency merely to remove a lint.

## Strings

String slicing uses byte offsets.

```rust
&s[..n]
```

panics if `n` is not a UTF-8 character boundary, even when `n <= s.len()`.

Do not assume external text is ASCII unless the API or validated input guarantees it.

When the requirement is "at most N bytes", round the byte limit to a valid UTF-8 boundary using an API such as `floor_char_boundary`.

Do not confuse byte limits with character or grapheme limits. If the requirement is expressed in characters or user-visible grapheme clusters, use an API matching that semantic.

Prefer delimiter APIs over finding an offset and slicing manually:

```rust
// before
let i = sym.find('-').unwrap();
let (base, quote) = (&sym[..i], &sym[i + 1..]);

// after
let (base, quote) = sym
    .split_once('-')
    .ok_or(Error::BadSymbol)?;
```

`rsplit_once`, `strip_prefix`, and `strip_suffix` belong to the same family.

## Encode structural invariants in types

If an invariant belongs to the data model rather than to one local operation, consider expressing it in the type.

If something is always exactly `N` items, prefer:

```rust
[T; N]
```

over a `Vec<T>` whose length must repeatedly be checked.

If a collection must never be empty, consider representing that directly:

```rust
struct NonEmpty<T> {
    first: T,
    rest: Vec<T>,
}
```

Do not introduce a new abstraction when a simple local control-flow rewrite is clearer.

## When a lint expectation is acceptable

As a last resort, keep the indexing or other operation and add a narrowly scoped lint expectation only when all of the following are true:

- the invariant is local and easy to verify;
- the operation improves readability or belongs to a measured hot path;
- expressing the invariant structurally would make the code worse;
- the expectation can be placed at the smallest practical scope;
- the reason explains the actual invariant.

For example:

```rust
#[expect(
    clippy::indexing_slicing,
    reason = "i is strictly less than len by construction of the loop bound"
)]
```

The reason must explain why the operation is safe, not why the lint is inconvenient.

Avoid module- or crate-wide expectations for these lints.

## Verification

Before finishing:

- The original Clippy warning no longer fires.
- No new `unwrap`, `expect`, or equivalent panic path was introduced merely to move the problem elsewhere.
- Behavior for valid inputs is unchanged.
- Empty input, singleton input, exact boundaries, and malformed or short external input retain the intended semantics where relevant.
- Existing relevant tests pass.
- Add or adjust a focused boundary test when the fix exposes a meaningful previously untested case.
- Every added `#[expect]` has a narrow scope and a reason stating a real invariant.
