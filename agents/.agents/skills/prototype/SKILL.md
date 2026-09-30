---
name: prototype
description: Build a throwaway prototype to answer a design question before committing to an implementation. Use when the user asks for a prototype, spike or sandbox to test whether a state model, data model or API shape holds up — or wants to explore what a UI should look like — or when resolving a wayfinder prototype ticket. Not for implementing or fixing real code.
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape; the code it will eventually feed decides the language.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / state model / data shape hold up?"** → [LOGIC.md](LOGIC.md). A pure module written in the destination language, driven by scripted scenarios that show the full state after every step — aimed at the cases that are hard to reason about on paper: races, out-of-order or duplicate events, partial outcomes, things that should be illegal.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

The two branches produce very different artifacts — getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module, library, service or data pipeline → logic; a page or component → UI) and state the assumption at the top of the prototype.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** Locate the prototype close to where it will actually be used, so context is obvious, and give it a `proto_` / `prototype` name so a casual reader can see it isn't production. Follow the project's existing conventions for where scratch code goes (a Rust crate's `examples/`, a Python package's neighbouring module or scratch folder, the app's routing convention for UI) rather than inventing a new top-level structure.
2. **Trivial to run.** One command, written at the top of the prototype: `cargo run --example proto_x`, `uv run proto_x.py`, `python proto_x.py`, `pnpm proto-x`, or "open this notebook / HTML file". No thinking required to start it.
3. **No persistence by default.** State lives in memory. Reading fixed input data (a fixture, a small data sample) is fine; writing is not. If the question explicitly involves storage, use a scratch DB or local file with a clear "PROTOTYPE — wipe me" name.
4. **Never touch production.** No live credentials, real accounts, real money or production endpoints. Use testnet, sandbox, paper, recorded fixtures or fakes. If the question can only be answered against a real system, stop and ask the human.
5. **Skip the polish.** No assertion suites, no error handling beyond what makes the prototype _runnable_, no abstractions, no new dependencies the question doesn't need. The point is to learn something fast.
6. **Surface the state.** After every step (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
7. **Capture it when done.** Fold any validated decision into the real code, then capture the prototype itself as a **primary source**: commit it to a throwaway branch, out of main, and leave a context pointer to that branch on the implementation issue. Capture the answer too — the verdict and the question it settled — in the issue or a commit. The main branch keeps only the validated decision.