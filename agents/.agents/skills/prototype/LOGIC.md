# Logic Prototype

A **pure module** written in the language of the code it will feed, plus a **thin driver** that pushes it through scenarios and shows the full state after every step. Use this when the question is about **business logic, state transitions, data shape or API shape** — the kind of thing that looks reasonable on paper but only feels wrong once you push it through real cases.

## When this is the right shape

- "I'm not sure this state machine handles the case where X arrives, then Y, then a late X."
- "Does this data model actually let me represent the case where..."
- "What happens when events arrive duplicated, out of order, or after we've already given up?"
- "I want to feel out what the API should look like before writing it."
- Anything where someone wants to **feed in events and watch state change**.

If the question is "what should this look like" — wrong branch. Use [UI.md](UI.md).

## Process

### 1. State the question

Before writing code, write down what model you're prototyping, the question, and what answer would settle it — which scenarios, behaving how. One short paragraph, placed where whoever runs the prototype sees it first: the driver's printed header, the first notebook cell, or the HTML intro — not buried in a comment. A logic prototype that answers the wrong question is pure waste; making the question explicit lets it be checked later, whether the user is watching now or returning to it AFK.

### 2. Pick the language

Write the module in the **destination language** — the language of the code the validated logic will live in. Infer it from the surrounding code: a Rust crate means Rust, a Python package or research directory means Python, and so on. A prototype in a language the real code will never use can't be lifted.

The one exception: when the logic is being validated in one language and will be **reimplemented** in another (checked in Python research code, shipped in a Rust engine, say), write it in whichever language answers the question fastest, and say so in the question. What carries over is then the specification, not the code — see step 6.

### 3. Isolate the logic in a pure module

Put the logic that answers the question in its own file or module, separate from the driver (`examples/proto_x/model.rs` beside `examples/proto_x/main.rs`; `proto_x/model.py` beside `proto_x/run.py`). The driver is throwaway; this module isn't.

Pick whichever shape best fits the question, _not_ whichever is easiest to drive:

- **A pure reducer** — `apply(state, event) -> state`. Good when inputs are discrete events and state is a single value.
- **A state machine** — explicit states and transitions, returning a rejection for illegal ones. Good when "which events are even legal right now" is part of the question.
- **A small set of pure functions** over a plain data type. Good when there's no implicit current state — just transformations.
- **A type with a clear method surface** when the logic genuinely owns ongoing internal state.

Keep it pure: no I/O, no network, no printing, no reading the clock (pass timestamps in as part of the event), no unseeded randomness. The driver calls into the module; nothing flows the other direction. This is what keeps it deterministic — every scenario replays identically — and what lets it lift into the real code on its own once the question is answered.

### 4. Build the driver

Choose the shell by **who will react to it**, not by the language:

- **Script** (default) — a developer at a terminal. `cargo run --example proto_x`, `uv run proto_x/run.py`. Runs all scenarios, or one by name (`proto_x <scenario>`).
- **Notebook** — when the state is data worth tabulating or plotting over time. The module is imported, never defined in cells; one cell per scenario.
- **Single HTML file** — when a non-developer (designer, PM, domain expert) needs to drive it. Plain HTML/CSS/JS, everything inline, opens by double-click; the module is a `<script>` block kept free of DOM access. Labels in domain language, a readable state panel, free-play buttons (one per event), and guided scenarios in tabs where each step is a real button. Clean and restrained: one accent colour, no animations. Only choose this when the destination is JavaScript or reimplementation is already the plan (step 2).

Whatever the shell, the structure is the same:

1. **The question** from step 1, first thing shown.
2. **Scenarios** — each named, each starting from a known initial state, each with a one- or two-line description of the situation and what to watch for, followed by its ordered events. Cover the happy path, a tricky edge case, something that should be illegal, and the ordering cases — duplicate, out-of-order, late, partial.
3. **After every event**, show: the event, whether it was accepted or rejected (and why), the full relevant state, and what changed. Labelled fields or an aligned table, not a raw dump — a reader should see the change at a glance.
4. **Free play** — a way to try sequences the scenarios don't cover. For a script, adding a scenario is a few lines of data; for a notebook, a scratch cell; for HTML, the free-play buttons.

### 5. Run it and hand it over

If the user is around, give them the command (or the file) and let them run it. If you're working AFK, run every scenario yourself and put the output alongside the verdict. Either way, the interesting moments are "wait, that shouldn't be possible" or "huh, I assumed X would be different" — those are the bugs in the _idea_, which is the whole point. When new cases come up, add scenarios. Prototypes evolve.

### 6. Capture the answer and the prototype

Once the prototype has answered its question, capture the answer, then capture the prototype the way the [SKILL](SKILL.md) describes. The logic-specific mapping depends on step 2:

- **Same language as the destination:** the validated module lifts into the real code (the decision, absorbed); the driver rides along to the throwaway branch that keeps the prototype as a primary source.
- **Reimplementation planned:** nothing lifts. Record the validated logic precisely enough in the resolution that a reimplementation can check itself against it — the states and transitions, formulas and parameters, the behaviour in each edge case — and list the scenarios as acceptance cases the real implementation must reproduce. Module and driver both go to the throwaway branch.

## Anti-patterns

- **Don't write assertion suites.** A prototype that needs tests is no longer a prototype. Using a language's test harness purely as a runner (`cargo test proto_x -- --nocapture`) is fine; asserting and chasing coverage is not.
- **Don't wire it to real systems.** No real database, live API, real account or production credentials unless the question is specifically about that system — and then only testnet, sandbox or scratch copies.
- **Don't generalise.** No "what if we wanted to support X later." The prototype answers one question.
- **Don't blur the logic and the driver.** If the module prints, does I/O, reads the clock or knows about the shell, it's no longer liftable or deterministic.
- **Don't write it in a language the real code will never use** — unless reimplementation is the explicit plan and the capture records the spec.
- **Don't build infrastructure.** No framework, server, bundler or plugin system; keep the driver the thinnest thing that runs the scenarios.
- **Don't ship the driver.** It's optimised for being read and poked at. The module behind it is the part worth keeping.